import requests
from flask_cors import CORS
from flask import redirect, request, __name__, jsonify
from requests_html import HTMLSession
from concurrent.futures import ThreadPoolExecutor
from flask_caching import Cache
from flask_openapi3 import OpenAPI, Info, Tag
from schema import DocumentListagemSchema, MensagemResposta

info = Info(title="Thatta Law API", version='1.0.0')
app = OpenAPI(__name__, info=info)
CORS(app)

# Configurações
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'America/Sao_Paulo'
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = 'redis://redis:6379/0'
cache = Cache(app)

# Definir tags
home_tag = Tag(name="Documentação",
               description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
scrape_tag = Tag(name="Leis",
                 description="Rota para captura de dados de leis brasileiras")

MAX_STARTDOC = 1000

def cache_key():
    return request.url

@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação."""
    return redirect('/openapi')

@app.get('/scrape', tags=[scrape_tag], responses={"200": DocumentListagemSchema, "400": MensagemResposta, "500": MensagemResposta})
@cache.cached(timeout=200, key_prefix=cache_key)
def obter_leis():
    """Obtém uma listagem do códice brasileiro (conjunto legal brasileiro).
    Retorna uma lista de documentos ou leis brasileiros."""
    keyword = request.args.get('keyword')
    tipoDocumento = request.args.get('tipoDocumento', '')
    sort = request.args.get('sort', '')

    if not keyword:
        return jsonify({"mensagem": "O parâmetro 'keyword' é obrigatório."}), 400

    results = []
    startDoc = 1
    session = HTMLSession()

    with ThreadPoolExecutor(max_workers=30) as executor:
        while startDoc <= MAX_STARTDOC:
            url = f"https://www.lexml.gov.br/busca/search?sort={sort}&keyword={keyword}&f1-tipoDocumento={tipoDocumento}&startDoc={startDoc}"
            response = session.get(url, timeout=10)

            if response.status_code != 200:
                return jsonify({"mensagem": "Erro ao acessar o site solicitado."}), 500

            docHits = response.html.find('td.docHit')
            if not docHits:
                break

            tasks = []
            documents = []
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
                                    tasks.append(executor.submit(fetch_details, session, document["Link"]))
                    documents.append(document)

            for task, doc in zip(tasks, documents):
                detail_link = task.result()
                if detail_link:
                    doc["MaisDetalhes"] = detail_link
                    results.append(doc)

            startDoc += 20

        return jsonify({"documentos": results}), 200

def fetch_details(session, link):
    try:
        detail_response = session.get(link)
    except requests.exceptions.ConnectionError as error:
        return jsonify({'message': 'error' + str(error)})
    if detail_response.status_code == 200:
        mais_detalhes_element = detail_response.html.find('div.row div.col-xs-12.col-sm-12.col-md-10.col-lg-10.text-left a.noprint', first=True)
        if mais_detalhes_element:
            return mais_detalhes_element.attrs['href']
        else:
            return None

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
