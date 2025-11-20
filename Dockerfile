# ---- Base Image ----
# Usamos a imagem oficial do Python na versão 3.9, que é compatível com a experta.
# A tag 'slim' é uma versão mais leve, ideal para produção.
FROM python:3.9-slim

# ---- Metadata ----
LABEL maintainer="Fernando Barcelos Rosito <fernando.rosito@gmail.com>"
LABEL description="API de Sistema Especialista de Vacinas em Flask com Experta."

# ---- Environment Variables ----
# Define o diretório de trabalho dentro do container.
WORKDIR /app

# Impede que o Python gere arquivos .pyc e os grave em disco.
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que a saída do Python seja enviada diretamente para o terminal (melhor para logs).
ENV PYTHONUNBUFFERED 1

# --- INSTALAÇÃO DE DEPENDÊNCIAS DO SISTEMA OPERACIONAL ---
# Atualiza a lista de pacotes e instala o netcat, que é necessário
# para o script de entrypoint testar a conexão com o banco de dados.
# A limpeza ao final ajuda a manter a imagem pequena.
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# ---- Install Dependencies ----
# Copia apenas o arquivo de requisitos primeiro para aproveitar o cache de camadas do Docker.
# O Docker só reinstalará as dependências se este arquivo mudar.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Application Code ----
# Copia todo o código do projeto para o diretório de trabalho no container.
COPY . .

# Copia o nosso novo script de entrypoint para dentro do container
COPY entrypoint.sh .

# ---- Expose Port ----
EXPOSE 5000

# ---- Define o Entrypoint ----
# Agora, o container sempre executará este script primeiro.
ENTRYPOINT ["/app/entrypoint.sh"]

# ---- Run Command ----
# Este comando agora será passado como argumento ("$@") para o entrypoint.sh
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]