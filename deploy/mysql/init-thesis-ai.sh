#!/usr/bin/env bash
# D-07 / §3.2.1: dịch vụ AI sở hữu schema riêng `thesis_ai` với tài khoản DB
# riêng CHỈ có quyền trên schema đó (không đọc thesis_core — T-04-17).
# Chạy bởi service one-shot `ai-db-init` (image mysql:8.4) mỗi lần
# `docker compose up`: idempotent (IF NOT EXISTS + ALTER USER giữ mật khẩu
# đồng bộ với deploy/.env). Mật khẩu root chỉ đi qua biến MYSQL_PWD, mật khẩu
# thesis_ai chỉ đi qua stdin của mysql — không bao giờ nằm trên dòng lệnh.
set -eu

: "${MYSQL_ROOT_PASSWORD:?thiếu MYSQL_ROOT_PASSWORD}"
: "${AI_DB_PASSWORD:?thiếu AI_DB_PASSWORD}"
MYSQL_HOST="${MYSQL_HOST:-mysql}"

# Thoát dấu ' và \ để chuỗi mật khẩu an toàn trong literal SQL.
esc() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e "s/'/''/g"
}
AI_PW_SQL="$(esc "${AI_DB_PASSWORD}")"

export MYSQL_PWD="${MYSQL_ROOT_PASSWORD}"
mysql --protocol=TCP -h "${MYSQL_HOST}" -u root --default-character-set=utf8mb4 <<EOSQL
CREATE DATABASE IF NOT EXISTS thesis_ai
  CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci;
CREATE USER IF NOT EXISTS 'thesis_ai'@'%' IDENTIFIED BY '${AI_PW_SQL}';
ALTER USER 'thesis_ai'@'%' IDENTIFIED BY '${AI_PW_SQL}';
GRANT ALL PRIVILEGES ON thesis_ai.* TO 'thesis_ai'@'%';
FLUSH PRIVILEGES;
EOSQL

echo "ai-db-init: schema thesis_ai + tài khoản thesis_ai sẵn sàng (chỉ quyền trên thesis_ai.*)"
