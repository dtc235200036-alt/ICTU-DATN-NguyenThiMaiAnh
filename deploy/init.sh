#!/usr/bin/env bash
# Sinh file deploy/.env (bí mật thật) từ deploy/.env.example và tạo chứng chỉ TLS tự ký.
# Không bao giờ ghi đè file .env đã tồn tại.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"

if [ ! -f "${ENV_FILE}" ]; then
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  # Thay từng giá trị __GENERATE__ bằng một chuỗi hex ngẫu nhiên riêng biệt.
  TMP_FILE="$(mktemp)"
  while IFS= read -r line || [ -n "$line" ]; do
    if [[ "$line" == *"__GENERATE__"* ]]; then
      secret="$(openssl rand -hex 32)"
      line="${line//__GENERATE__/${secret}}"
    fi
    printf '%s\n' "$line" >> "${TMP_FILE}"
  done < "${ENV_FILE}"
  mv "${TMP_FILE}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "Đã tạo ${ENV_FILE} với bí mật sinh tự động."
else
  echo "${ENV_FILE} đã tồn tại — giữ nguyên."
fi

bash "${SCRIPT_DIR}/certs/gen-cert.sh"

echo ""
echo "Bước tiếp theo:"
echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml up -d --build --wait"
