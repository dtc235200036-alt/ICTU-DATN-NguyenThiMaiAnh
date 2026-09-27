#!/usr/bin/env bash
# Smoke test qua Apache HTTPS — bộ kiểm tra dùng lại cho mọi kế hoạch sau.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${BASE_URL:-https://localhost}"

fail() {
  echo "FAIL: $1"
  exit 1
}

# (a) http:// redirect 301 -> https://
redirect_url="$(curl -sk -o /dev/null -w '%{redirect_url}' -D - "http://localhost/" 2>/dev/null | tr -d '\r' | grep -i '^location:' | awk '{print $2}' | tail -1)"
status_a="$(curl -sk -o /dev/null -w '%{http_code}' "http://localhost/")"
[ "$status_a" = "301" ] || fail "http://localhost/ không trả 301 (nhận $status_a)"
echo "OK: http://localhost/ trả 301"

# (b) /api/health -> 200, status ok, db ok
health_body="$(curl -sk "$BASE/api/health")"
echo "$health_body" | grep -q '"status":"ok"' || fail "GET /api/health không có status ok ($health_body)"
echo "$health_body" | grep -q '"db":"ok"' || fail "GET /api/health không có db ok ($health_body)"
echo "OK: GET /api/health trả status ok, db ok"

# (c) GET / -> 200 chứa id="root"
root_body="$(curl -sk "$BASE/")"
echo "$root_body" | grep -q 'id="root"' || fail "GET / không chứa id=\"root\""
echo "OK: GET / chứa id=\"root\""

# (d) GET /tong-quan -> 200 chứa id="root" (SPA fallback)
tq_body="$(curl -sk "$BASE/tong-quan")"
echo "$tq_body" | grep -q 'id="root"' || fail "GET /tong-quan không chứa id=\"root\" (SPA fallback)"
echo "OK: GET /tong-quan trả SPA fallback"

# (e) headers CSP + nosniff
headers="$(curl -sk -D - -o /dev/null "$BASE/")"
echo "$headers" | grep -qi '^content-security-policy:' || fail "Thiếu header Content-Security-Policy"
echo "$headers" | grep -qi '^x-content-type-options: *nosniff' || fail "Thiếu header X-Content-Type-Options: nosniff"
echo "OK: header CSP và X-Content-Type-Options có mặt"

# (f) login bomon -> 200, access_token + vai_tro BO_MON
SEED_PW="$(docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api printenv SEED_DEFAULT_PASSWORD | tr -d '\r')"
login_body="$(curl -sk -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"bomon\",\"mat_khau\":\"${SEED_PW}\"}")"
echo "$login_body" | grep -q '"access_token"' || fail "Đăng nhập bomon không trả access_token ($login_body)"
echo "$login_body" | grep -q '"vai_tro":"BO_MON"' || fail "Đăng nhập bomon không trả vai_tro BO_MON ($login_body)"
echo "OK: đăng nhập bomon thành công"

# (g) login sai mật khẩu -> 401 generic detail
wrong_status="$(curl -sk -o /tmp/ntma-wrong-login.json -w '%{http_code}' -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d '{"dang_nhap":"bomon","mat_khau":"sai-mat-khau"}')"
[ "$wrong_status" = "401" ] || fail "Đăng nhập sai mật khẩu không trả 401 (nhận $wrong_status)"
grep -q "Sai thông tin đăng nhập" /tmp/ntma-wrong-login.json || fail "Thông báo lỗi đăng nhập không đúng nội dung chung"
rm -f /tmp/ntma-wrong-login.json
echo "OK: đăng nhập sai mật khẩu trả 401 với thông báo chung"

# (h) 21MB body không bị từ chối; 30MB body bị 413 (D-12/NFR-06).
# -H "Expect:" tắt "Expect: 100-continue" của curl cho body lớn: mod_proxy_http
# của Apache không xử lý đúng bắt tay 100-continue khi backend trả lời sớm,
# gây 500 giả — không liên quan tới việc kiểm tra giới hạn kích thước ở đây.
status_21mb="$(head -c 21000000 /dev/zero | curl -sk -H "Expect:" -o /dev/null -w '%{http_code}' -X POST "$BASE/api/health" --data-binary @-)"
[ "$status_21mb" != "413" ] || fail "Body 21MB bị từ chối (413) — giới hạn quá nhỏ"
echo "OK: body 21MB không bị từ chối (status $status_21mb)"

status_30mb="$(head -c 30000000 /dev/zero | curl -sk -H "Expect:" -o /dev/null -w '%{http_code}' -X POST "$BASE/api/health" --data-binary @-)"
[ "$status_30mb" = "413" ] || fail "Body 30MB không bị từ chối 413 (nhận $status_30mb)"
echo "OK: body 30MB bị từ chối 413"

echo "SMOKE TEST: tất cả kiểm tra đã qua."
