#!/usr/bin/env bash
# Chạy một lần bởi entrypoint chính thức của image mysql khi khởi tạo dữ liệu lần đầu.
# Tạo thêm schema thesis_core_test dùng cho pytest, cùng collation tiếng Việt.
set -euo pipefail

mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL
  CREATE DATABASE IF NOT EXISTS thesis_core_test
    CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci;
  GRANT ALL PRIVILEGES ON thesis_core_test.* TO '${MYSQL_USER}'@'%';
  FLUSH PRIVILEGES;
EOSQL
