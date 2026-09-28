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
  # Cài đặt cũ: bổ sung các khóa MỚI có trong .env.example nhưng chưa có trong
  # .env (vd. AI_API_KEY/AI_DB_PASSWORD của Phase 4) — sinh __GENERATE__ giống
  # lần chạy đầu; KHÔNG bao giờ sửa giá trị một khóa đã có (T-04-22).
  added=()
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|'#'*) continue ;;
    esac
    [[ "$line" == *=* ]] || continue
    key="${line%%=*}"
    if ! grep -q "^${key}=" "${ENV_FILE}"; then
      if [[ "$line" == *"__GENERATE__"* ]]; then
        secret="$(openssl rand -hex 32)"
        line="${line//__GENERATE__/${secret}}"
      fi
      # .env có thể thiếu xuống dòng cuối — tránh dính khóa mới vào dòng trước.
      if [ -s "${ENV_FILE}" ] && [ -n "$(tail -c 1 "${ENV_FILE}")" ]; then
        printf '\n' >> "${ENV_FILE}"
      fi
      printf '%s\n' "$line" >> "${ENV_FILE}"
      added+=("$key")
    fi
  done < "${ENV_EXAMPLE}"
  chmod 600 "${ENV_FILE}"
  if [ "${#added[@]}" -gt 0 ]; then
    echo "${ENV_FILE} đã tồn tại — bổ sung khóa mới: ${added[*]}"
  else
    echo "${ENV_FILE} đã tồn tại — giữ nguyên."
  fi
fi

bash "${SCRIPT_DIR}/certs/gen-cert.sh"

echo ""
echo "Bước tiếp theo:"
echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml up -d --build --wait"
