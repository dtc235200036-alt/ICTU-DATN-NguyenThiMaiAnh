# syntax=docker/dockerfile:1
# Dịch vụ AI (D-02): CPU-only (torch lấy từ index whl/cpu qua uv.lock), một
# worker uvicorn, chạy bằng người dùng không phải root, trọng số mô hình cache
# dưới /models (named volume hoặc mount cache HF có sẵn).
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /uvx /usr/local/bin/

# Tạo appuser TRƯỚC và cài venv bằng chính appuser thay vì `chown -R` sau
# cùng: chown đệ quy nhân đôi lớp venv (~1.3 GB torch CPU). /models thuộc
# appuser để named volume mount lần đầu kế thừa quyền sở hữu.
# IN-07 (04-REVIEW): mã nguồn (/app, /app/app, …) thuộc root — tiến trình
# appuser chỉ ghi được /app/.venv (lúc build) và /models; compose còn chạy
# container với read_only + tmpfs /tmp.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser \
 && mkdir -p /app/.venv /models \
 && chown appuser:appuser /app/.venv /models

ENV PATH="/app/.venv/bin:${PATH}" \
    HF_HOME=/models \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/uv-cache \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY pyproject.toml uv.lock ./
USER appuser
RUN uv sync --frozen --no-dev --no-install-project --no-cache

USER root
COPY . .
USER appuser
RUN uv sync --frozen --no-dev --no-cache

# Làm nóng underthesea một lần lúc build để tài nguyên nó cần (nếu có) nằm
# sẵn trong image, không phải tải khi container khởi động.
RUN python -c "from underthesea import word_tokenize; print(word_tokenize('Xây dựng hệ thống quản lý', format='text'))"

EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --start-period=180s --retries=5 \
  CMD ["python", "-c", "import json, urllib.request; r = urllib.request.urlopen('http://127.0.0.1:8002/health', timeout=4); raise SystemExit(0 if json.load(r).get('status') == 'ok' else 1)"]

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
