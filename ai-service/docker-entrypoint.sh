#!/bin/sh
set -e

# thesis_ai có lịch sử migration riêng (§3.2.1, DEPL-01).
alembic upgrade head

# Đúng MỘT worker: chỉ mục FAISS và ma trận MinHash nằm trong bộ nhớ tiến
# trình và /ingest sửa chúng tại chỗ — worker thứ hai sẽ phục vụ chỉ mục cũ.
# 0.0.0.0 chỉ là bên trong container; plan 04-05 không publish cổng nào ra
# host (mạng nội bộ compose, không có route Apache — AISV-01).
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8002 \
  --workers 1 \
  --no-server-header
