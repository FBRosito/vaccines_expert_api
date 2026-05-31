#!/bin/sh

set -e

# POSTGRES_HOST is injected from .env via docker-compose.
DB_HOST=$POSTGRES_HOST
DB_PORT=$POSTGRES_PORT

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

# netcat probes whether the port is open; loop until the connection succeeds.
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Database ready. Running migrations..."
flask db upgrade

echo "Migrations complete. Starting application..."
exec "$@"
