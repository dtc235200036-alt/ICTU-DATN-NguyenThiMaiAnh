#!/usr/bin/env bash
# Kiểm tra DOM đã render (headless Chrome) chứa một chuỗi văn bản mong đợi.
# Dùng: bash deploy/dom-check.sh /dang-nhap 'Mã SV/GV hoặc email'
set -euo pipefail

PATH_ARG="$1"
EXPECTED_TEXT="$2"
CHROME="${CHROME:-/usr/bin/google-chrome}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

DOM_FILE="${TMP_DIR}/dom.html"

"${CHROME}" --headless=new --disable-gpu --ignore-certificate-errors \
  --no-first-run --no-default-browser-check \
  --user-data-dir="${TMP_DIR}/profile" \
  --virtual-time-budget=10000 \
  --dump-dom "https://localhost${PATH_ARG}" > "${DOM_FILE}" 2>/dev/null

if grep -qF "${EXPECTED_TEXT}" "${DOM_FILE}"; then
  echo "OK: DOM tại ${PATH_ARG} chứa \"${EXPECTED_TEXT}\""
  exit 0
else
  echo "FAIL: DOM tại ${PATH_ARG} không chứa \"${EXPECTED_TEXT}\""
  head -n 40 "${DOM_FILE}"
  exit 1
fi
