#!/bin/sh

set -e

# A variável de ambiente POSTGRES_HOST vem do nosso .env, que o docker-compose injeta.
DB_HOST=$POSTGRES_HOST
DB_PORT=$POSTGRES_PORT

echo "Aguardando o banco de dados PostgreSQL iniciar em $DB_HOST:$DB_PORT..."

# O comando 'nc' (netcat) testa se a porta está aberta.
# O loop continua enquanto a conexão falhar.
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Banco de dados pronto. Executando migrações..."
flask db upgrade

echo "Migrações concluídas. Iniciando a aplicação..."
exec "$@"