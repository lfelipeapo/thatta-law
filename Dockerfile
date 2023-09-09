# Imagem base
FROM python:3.9

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos de código-fonte para o diretório de trabalho
COPY . /app

# Atualiza o pip
RUN pip install --upgrade pip

# Instala as dependências do projeto
RUN pip install -r requirements.txt

# Expõe a porta 5001 para acessar a API
EXPOSE 5001