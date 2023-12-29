#!/bin/sh

# Parse and extract values
DB_HOST=$(awk '/^database:/,/^$/' config.yaml | awk '/^ *hostname:/ {print $2}')
DB_PORT=$(awk '/^database:/,/^$/' config.yaml | awk '/^ *port:/ {print $2}')
DB_DATABASE=$(awk '/^database:/,/^$/' config.yaml | awk '/^ *database:/ {printf "%s", $2}')

if [ "$DB_DATABASE" = "postgres" ]; then
    echo "INFO - Waiting for PostgreSQL DB"

    while ! nc -z "$DB_HOST" "$DB_PORT"; do
      sleep 0.1
    done

    echo "INFO - PostgreSQL DB started"
fi

python -u src/app.py

exec "$@"
