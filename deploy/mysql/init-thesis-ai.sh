#!/usr/bin/env bash
# D-07 / §3.2.1: dịch vụ AI sở hữu schema riêng `thesis_ai` với tài khoản DB
# riêng CHỈ có quyền trên schema đó (không đọc thesis_core — T-04-17).
# Chạy bởi service one-shot `ai-db-init` (image mysql:8.4) mỗi lần
# `docker compose up`: idempotent (IF NOT EXISTS + ALTER USER giữ mật khẩu
# đồng bộ với deploy/.env). Mật khẩu root chỉ đi qua biến MYSQL_PWD, mật khẩu
# các tài khoản thesis_ai chỉ đi qua stdin của mysql — không nằm trên dòng lệnh.
#
# WR-03 (04-REVIEW) — đặc quyền tối thiểu, hai tài khoản, chỉ từ subnet compose:
# - thesis_ai          : SELECT/INSERT/UPDATE/DELETE trên thesis_ai.* — tiến
#                        trình phục vụ request (xử lý văn bản không tin cậy)
#                        không có DDL/DROP;
# - thesis_ai_migrate  : mọi quyền trên thesis_ai.* — CHỈ service one-shot
#                        `ai-migrate` dùng để chạy `alembic upgrade head`.
# Tài khoản cũ 'thesis_ai'@'%' (ALL PRIVILEGES, mọi host) bị xóa.
set -eu

: "${MYSQL_ROOT_PASSWORD:?thiếu MYSQL_ROOT_PASSWORD}"
: "${AI_DB_PASSWORD:?thiếu AI_DB_PASSWORD}"
: "${AI_DB_MIGRATE_PASSWORD:?thiếu AI_DB_MIGRATE_PASSWORD}"
MYSQL_HOST="${MYSQL_HOST:-mysql}"
# Phải khớp subnet của mạng ntma-internal trong docker-compose.yml.
AI_DB_CLIENT_HOST="${AI_DB_CLIENT_HOST:-172.28.238.%}"

# Thoát dấu ' và \ để chuỗi an toàn trong literal SQL.
esc() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e "s/'/''/g"
}
AI_PW_SQL="$(esc "${AI_DB_PASSWORD}")"
MIGRATE_PW_SQL="$(esc "${AI_DB_MIGRATE_PASSWORD}")"
HOST_SQL="$(esc "${AI_DB_CLIENT_HOST}")"

export MYSQL_PWD="${MYSQL_ROOT_PASSWORD}"
mysql --protocol=TCP -h "${MYSQL_HOST}" -u root --default-character-set=utf8mb4 <<EOSQL
CREATE DATABASE IF NOT EXISTS thesis_ai
  CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci;
DROP USER IF EXISTS 'thesis_ai'@'%';

CREATE USER IF NOT EXISTS 'thesis_ai'@'${HOST_SQL}' IDENTIFIED BY '${AI_PW_SQL}';
ALTER USER 'thesis_ai'@'${HOST_SQL}' IDENTIFIED BY '${AI_PW_SQL}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'thesis_ai'@'${HOST_SQL}';
GRANT SELECT, INSERT, UPDATE, DELETE ON thesis_ai.* TO 'thesis_ai'@'${HOST_SQL}';

CREATE USER IF NOT EXISTS 'thesis_ai_migrate'@'${HOST_SQL}' IDENTIFIED BY '${MIGRATE_PW_SQL}';
ALTER USER 'thesis_ai_migrate'@'${HOST_SQL}' IDENTIFIED BY '${MIGRATE_PW_SQL}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'thesis_ai_migrate'@'${HOST_SQL}';
GRANT ALL PRIVILEGES ON thesis_ai.* TO 'thesis_ai_migrate'@'${HOST_SQL}';
FLUSH PRIVILEGES;
EOSQL

echo "ai-db-init: schema thesis_ai; thesis_ai (DML) + thesis_ai_migrate (DDL) chỉ trên thesis_ai.*, host ${AI_DB_CLIENT_HOST}"
