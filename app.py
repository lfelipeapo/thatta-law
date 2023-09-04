import requests
from flask_cors import CORS
from flask import redirect, request, __name__, jsonify
from requests_html import HTMLSession

from flask_openapi3 import OpenAPI, Info, Tag
from schema import DocumentSchema, DocumentListagemSchema, MensagemResposta

info = Info(title="Thatta Law API", version='1.0.0')
app = OpenAPI(__name__, info=info)
CORS(app)

# Configurações
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'America/Sao_Paulo'

# Definir tags
home_tag = Tag(name="Documentação",
               description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
scrape_tag = Tag(name="Leis",
               description="Rota para captura de dados de leis brasileiras")
# Rotas

@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')


@app.get('/scrape', tags=[scrape_tag], responses={"200": DocumentListagemSchema, "400": MensagemResposta, "500": MensagemResposta})
def obter_leis():
    """Obtém uma listagem do códice brasileiro (conjunto legal brasileiro).
    Retorna uma lista de documentos ou leis brasileiros.
    """
    keyword = request.args.get('keyword')
    tipoDocumento = request.args.get('tipoDocumento', '')
    sort = request.args.get('sort', '')

    if not keyword:
        return jsonify({"mensagem": "O parâmetro 'keyword' é obrigatório."}), 400

    results = []
    startDoc = 1
    session = HTMLSession()

    while True:
        url = f"https://www.lexml.gov.br/busca/search?sort={sort}&keyword={keyword}&f1-tipoDocumento={tipoDocumento}&startDoc={startDoc}"

        response = session.get(url, timeout=10)

        if response.status_code != 200:
            return jsonify({"mensagem": "Erro ao acessar o site solicitado."}), 500

        docHits = response.html.find('td.docHit')
        if not docHits:
            break

        for docHit in docHits:
            main_divs = docHit.find('div[id^="main_"]')
            for main_div in main_divs:
                document = {}
                for row in main_div.find('tr'):
                    cols = row.find('td')
                    if len(cols) == 4:
                        key = cols[1].text.strip()
                        value = cols[2].text.strip()
                        if key:
                            document[key] = value
                            if key == "Título":
                                link = cols[2].find('a', first=True).attrs['href']
                                document["Link"] = f"https://www.lexml.gov.br{link}"
                                detail_response = session.get(document["Link"])
                                if detail_response.status_code == 200:
                                    mais_detalhes_link = detail_response.html.find('div.row div.col-xs-12.col-sm-12.col-md-10.col-lg-10.text-left a.noprint', first=True).attrs['href']
                                    document["MaisDetalhes"] = mais_detalhes_link
                results.append(document)

        startDoc += 20

    return jsonify({"documentos": results}), 200

if __name__ == '__main__':
    app.run(debug=True)