#!/bin/bash
set -euo pipefail
# Password is generated as hex in the private runtime, never a shell argument.
identity_password="$(cat /etc/identity/keycloak-password)"
[[ "$identity_password" =~ ^[a-f0-9]{64}$ ]] || exit 1
psql --username "$POSTGRES_USER" --dbname postgres --set ON_ERROR_STOP=1 <<SQL
CREATE ROLE keycloak LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '$identity_password';
CREATE DATABASE keycloak OWNER keycloak;
SQL
unset identity_password
