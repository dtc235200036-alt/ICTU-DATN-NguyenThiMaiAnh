#!/usr/bin/env bash
# Chạy một câu SQL bên trong container mysql của stack compose.
# Dùng: bash deploy/sql.sh "SELECT 1" ; DB=thesis_core_test bash deploy/sql.sh "..."
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
Q="$1"
DB_NAME="${DB:-thesis_core}"

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T \
  -e Q="${Q}" -e DB="${DB_NAME}" mysql sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" mysql -N -B -u"$MYSQL_USER" "$DB" -e "$Q"'
