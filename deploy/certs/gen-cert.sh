#!/usr/bin/env bash
# Sinh chứng chỉ TLS tự ký cho localhost (mkcert nếu có, ngược lại dùng openssl).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_FILE="${SCRIPT_DIR}/server.crt"
KEY_FILE="${SCRIPT_DIR}/server.key"

if [ -f "${CERT_FILE}" ] && [ -f "${KEY_FILE}" ]; then
  echo "Chứng chỉ đã tồn tại tại ${SCRIPT_DIR} — bỏ qua."
  exit 0
fi

if command -v mkcert >/dev/null 2>&1; then
  ( cd "${SCRIPT_DIR}" && mkcert -cert-file server.crt -key-file server.key localhost 127.0.0.1 )
else
  openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 825 \
    -keyout "${KEY_FILE}" -out "${CERT_FILE}" \
    -subj /CN=localhost \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
fi

chmod 600 "${KEY_FILE}"
chmod 644 "${CERT_FILE}"
echo "Đã tạo chứng chỉ TLS tại ${SCRIPT_DIR}."
