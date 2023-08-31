# Use a imagem oficial do Python
FROM python:3.9

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos necessários para o container
COPY requirements.txt .
COPY app.py .

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta que o app usa
EXPOSE 5001

# Comando para rodar o aplicativo
CMD ["python", "app.py"]
