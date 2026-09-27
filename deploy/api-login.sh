#!/usr/bin/env bash
# In ra access_token cho một tài khoản đăng nhập, dùng mật khẩu seed mặc định.
# Dùng: bash deploy/api-login.sh bomon
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DANG_NHAP="$1"

SEED_PW="$(docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api printenv SEED_DEFAULT_PASSWORD | tr -d '\r')"

BODY="$(curl -sk -X POST "https://localhost/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"${DANG_NHAP}\",\"mat_khau\":\"${SEED_PW}\"}")"

TOKEN="$(printf '%s' "$BODY" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])' 2>/dev/null)"

if [ -z "$TOKEN" ]; then
  echo "Không lấy được access_token cho '${DANG_NHAP}': ${BODY}" >&2
  exit 1
fi

printf '%s\n' "$TOKEN"
