#!/bin/sh
set -e

# thesis_ai có lịch sử migration riêng (§3.2.1, DEPL-01).
# WR-03 (04-REVIEW): trong compose, migration chạy ở service one-shot
# `ai-migrate` (`docker-entrypoint.sh migrate`, tài khoản thesis_ai_migrate có
# DDL); service `ai` đặt AI_MIGRATE_ON_START=0 và phục vụ bằng tài khoản chỉ có
# DML. Chạy image đơn lẻ (container_smoke, SQLite) giữ mặc định: migrate rồi phục vụ.
if [ "${1:-serve}" = "migrate" ]; then
  exec alembic upgrade head
fi
if [ "${AI_MIGRATE_ON_START:-1}" = "1" ]; then
  alembic upgrade head
fi

# Đúng MỘT worker: chỉ mục FAISS và ma trận MinHash nằm trong bộ nhớ tiến
# trình và /ingest sửa chúng tại chỗ — worker thứ hai sẽ phục vụ chỉ mục cũ.
# 0.0.0.0 chỉ là bên trong container; plan 04-05 không publish cổng nào ra
# host (mạng nội bộ compose, không có route Apache — AISV-01).
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8002 \
  --workers 1 \
  --no-server-header
