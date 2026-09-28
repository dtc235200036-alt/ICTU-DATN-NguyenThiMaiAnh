#!/bin/sh
set -e

alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  python -m app.seed
fi

# WR-03: '*' làm uvicorn tin X-Forwarded-For từ BẤT KỲ peer nào mở được kết
# nối TCP tới api:8001 (mọi container trên cùng mạng compose, không chỉ
# apache) — cho phép giả mạo IP để né login throttle (T-02-xx). Mặc định an
# toàn (chỉ localhost) khi FORWARDED_ALLOW_IPS không được truyền; compose
# truyền đúng IP tĩnh của container apache (xem deploy/docker-compose.yml).
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8001 \
  --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
  --no-server-header
