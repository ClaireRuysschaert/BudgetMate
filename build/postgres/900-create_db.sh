#!/bin/bash
set -e

echo $(env)

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER "$POSTGRES_APP_USER" PASSWORD '$POSTGRES_APP_PASSWORD';
    CREATE DATABASE "$POSTGRES_APP_DB";
    GRANT ALL PRIVILEGES ON DATABASE "$POSTGRES_APP_DB" TO "$POSTGRES_APP_USER";
    ALTER USER "$POSTGRES_APP_USER" CREATEDB;
EOSQL
