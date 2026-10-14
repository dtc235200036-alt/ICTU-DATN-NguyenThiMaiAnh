#!/usr/bin/env bash
# Smoke test qua Apache HTTPS — bộ kiểm tra dùng lại cho mọi kế hoạch sau.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${BASE_URL:-https://localhost:${HTTPS_PORT:-443}}"

fail() {
  echo "FAIL: $1"
  exit 1
}

# (a) http:// redirect 301 -> https://
redirect_url="$(curl -sk -o /dev/null -w '%{redirect_url}' -D - "http://localhost:${HTTP_PORT:-80}/" 2>/dev/null | tr -d '\r' | grep -i '^location:' | awk '{print $2}' | tail -1)"
status_a="$(curl -sk -o /dev/null -w '%{http_code}' "http://localhost:${HTTP_PORT:-80}/")"
[ "$status_a" = "301" ] || fail "http://localhost/ không trả 301 (nhận $status_a)"
echo "OK: http://localhost:${HTTP_PORT:-80}/ trả 301"

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

# (i) Set-Cookie của refresh_token có đủ HttpOnly, Secure, SameSite=Strict, Path=/api/auth
login_headers="$(curl -sk -D - -o /tmp/ntma-login-body.json -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d "{\"dang_nhap\":\"bomon\",\"mat_khau\":\"${SEED_PW}\"}")"
echo "$login_headers" | grep -qi 'set-cookie:.*refresh_token' || fail "Không thấy Set-Cookie refresh_token"
echo "$login_headers" | grep -qi 'HttpOnly' || fail "Cookie refresh_token thiếu HttpOnly"
echo "$login_headers" | grep -qi 'Secure' || fail "Cookie refresh_token thiếu Secure"
echo "$login_headers" | grep -qi 'SameSite=Strict' || fail "Cookie refresh_token thiếu SameSite=Strict"
echo "$login_headers" | grep -qi 'Path=/api/auth' || fail "Cookie refresh_token thiếu Path=/api/auth"
rm -f /tmp/ntma-login-body.json
echo "OK: Set-Cookie refresh_token có đủ HttpOnly, Secure, SameSite=Strict, Path=/api/auth"

# (j) POST /api/auth/refresh dùng cookie jar -> 200 + access_token
COOKIE_JAR="$(mktemp)"
trap 'rm -f "${COOKIE_JAR}"' EXIT

curl -sk -c "${COOKIE_JAR}" -o /dev/null -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d "{\"dang_nhap\":\"bomon\",\"mat_khau\":\"${SEED_PW}\"}"
refresh_body="$(curl -sk -b "${COOKIE_JAR}" -c "${COOKIE_JAR}" -X POST "$BASE/api/auth/refresh")"
echo "$refresh_body" | grep -q '"access_token"' || fail "POST /api/auth/refresh không trả access_token ($refresh_body)"
echo "OK: POST /api/auth/refresh trả access_token"

# (k) GET /api/auth/me với token -> 200; không token -> 401
ACCESS_TOKEN="$(echo "$refresh_body" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
me_status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/auth/me" -H "Authorization: Bearer ${ACCESS_TOKEN}")"
[ "$me_status" = "200" ] || fail "GET /api/auth/me với token hợp lệ không trả 200 (nhận $me_status)"
me_status_no_token="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/auth/me")"
[ "$me_status_no_token" = "401" ] || fail "GET /api/auth/me không token không trả 401 (nhận $me_status_no_token)"
echo "OK: GET /api/auth/me trả 200 có token, 401 không token"

# (l) POST /api/auth/logout -> 204 và xóa cookie; refresh sau đó -> 401
logout_status="$(curl -sk -b "${COOKIE_JAR}" -c "${COOKIE_JAR}" -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/logout")"
[ "$logout_status" = "204" ] || fail "POST /api/auth/logout không trả 204 (nhận $logout_status)"
after_logout_status="$(curl -sk -b "${COOKIE_JAR}" -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/refresh")"
[ "$after_logout_status" = "401" ] || fail "refresh sau logout không trả 401 (nhận $after_logout_status)"
echo "OK: logout trả 204 và xóa cookie refresh (refresh sau đó trả 401)"

# (m) 6 lần đăng nhập sai liên tiếp cho một mã đăng nhập ngẫu nhiên -> lần thứ 6 trả 429
RAND_LOGIN="khong-ton-tai-$(date +%s%N)"
for i in 1 2 3 4 5; do
  curl -sk -o /dev/null -X POST "$BASE/api/auth/login" \
    -H 'Content-Type: application/json' -d "{\"dang_nhap\":\"${RAND_LOGIN}\",\"mat_khau\":\"sai\"}"
done
sixth_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d "{\"dang_nhap\":\"${RAND_LOGIN}\",\"mat_khau\":\"sai\"}")"
[ "$sixth_status" = "429" ] || fail "Lần đăng nhập sai thứ 6 không trả 429 (nhận $sixth_status)"
echo "OK: lần đăng nhập sai thứ 6 trả 429"

# (n) Dashboard theo vai trò: mỗi vai trò tự xem được /api/dashboard/* của
# chính mình (D-09); vai trò khác luôn bị 403 (T-02-38).
TOKEN_BOMON="$(curl -sk -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"bomon\",\"mat_khau\":\"${SEED_PW}\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
TOKEN_GV001="$(curl -sk -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"GV001\",\"mat_khau\":\"${SEED_PW}\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
TOKEN_SV001="$(curl -sk -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"DTC235200016\",\"mat_khau\":\"${SEED_PW}\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"

status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/dashboard/bo-mon" -H "Authorization: Bearer ${TOKEN_BOMON}")"
[ "$status" = "200" ] || fail "bomon xem /api/dashboard/bo-mon không trả 200 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/dashboard/giang-vien" -H "Authorization: Bearer ${TOKEN_GV001}")"
[ "$status" = "200" ] || fail "GV001 xem /api/dashboard/giang-vien không trả 200 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/dashboard/sinh-vien" -H "Authorization: Bearer ${TOKEN_SV001}")"
[ "$status" = "200" ] || fail "DTC235200016 xem /api/dashboard/sinh-vien không trả 200 (nhận $status)"
echo "OK: mỗi vai trò xem được dashboard của chính mình"

# UC0.8 (0015): dashboard có trường phân công GVHD mới của từng vai trò.
for spec in "bo-mon BOMON sv_chua_phan_cong" "giang-vien GV001 so_sinh_vien_lop" "sinh-vien SV001 giang_vien_huong_dan"; do
  read -r dash who field <<<"$spec"
  tok_var="TOKEN_${who}"
  curl -sk "$BASE/api/dashboard/${dash}" -H "Authorization: Bearer ${!tok_var}" \
    | python3 -c 'import json,sys; sys.exit(0 if sys.argv[1] in json.load(sys.stdin) else 1)' "$field" 2>/dev/null \
    || fail "/api/dashboard/${dash} thiếu trường ${field}"
done
echo "OK: dashboard có sv_chua_phan_cong (bo-mon), so_sinh_vien_lop (giang-vien), giang_vien_huong_dan (sinh-vien)"

status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/dashboard/bo-mon" -H "Authorization: Bearer ${TOKEN_SV001}")"
[ "$status" = "403" ] || fail "DTC235200016 xem /api/dashboard/bo-mon không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/dashboard/sinh-vien" -H "Authorization: Bearer ${TOKEN_GV001}")"
[ "$status" = "403" ] || fail "GV001 xem /api/dashboard/sinh-vien không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/dashboard/giang-vien" -H "Authorization: Bearer ${TOKEN_BOMON}")"
[ "$status" = "403" ] || fail "bomon xem /api/dashboard/giang-vien không trả 403 (nhận $status)"
echo "OK: dashboard của vai trò khác bị từ chối 403"

status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/accounts?vai_tro=SINH_VIEN" -H "Authorization: Bearer ${TOKEN_SV001}")"
[ "$status" = "403" ] || fail "DTC235200016 xem /api/accounts không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/cohorts" -H "Authorization: Bearer ${TOKEN_SV001}" -H 'Content-Type: application/json' -d '{}')"
[ "$status" = "403" ] || fail "DTC235200016 tạo đợt đồ án không trả 403 (nhận $status)"
echo "OK: DTC235200016 bị 403 trên accounts/cohorts"

# Góp ý GVHD mục 1 (quick 261014-u0j): chỉ GVHD tạo/giao đề tài và kiểm tra
# trùng tên (SV, Bộ môn 403); route đăng ký đề tài và router duyệt đề tài đã gỡ (404).
status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/topics" -H "Authorization: Bearer ${TOKEN_SV001}" -H 'Content-Type: application/json' -d '{"dot_do_an_id":1,"ten_de_tai":"Smoke - SV tự đề xuất","sinh_vien_id":1,"gui":false}')"
[ "$status" = "403" ] || fail "DTC235200016 tạo đề tài không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/topics/check-title" -H "Authorization: Bearer ${TOKEN_SV001}" -H 'Content-Type: application/json' -d '{"ten_de_tai":"Smoke - kiểm tra tên"}')"
[ "$status" = "403" ] || fail "DTC235200016 kiểm tra trùng tên không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/topics/1/register" -H "Authorization: Bearer ${TOKEN_SV001}")"
[ "$status" = "404" ] || fail "Route đăng ký đề tài đã gỡ nhưng không trả 404 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topic-approvals" -H "Authorization: Bearer ${TOKEN_GV001}")"
[ "$status" = "404" ] || fail "Router duyệt đề tài đã gỡ nhưng GV001 không nhận 404 (nhận $status)"
echo "OK: SV tạo đề tài / kiểm tra trùng tên -> 403; route đăng ký và duyệt đề tài đã gỡ -> 404"

# UC0.8 (0015): phân công GVHD — Bộ môn gán/import, GV xem lớp của mình, SV
# xem GVHD của mình; seed gán DTC235200016 -> GV001 trong đợt demo.
for who in GV001 SV001; do
  tok_var="TOKEN_${who}"
  status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/assignments?dot_do_an_id=1" -H "Authorization: Bearer ${!tok_var}")"
  [ "$status" = "403" ] || fail "${who} xem /api/assignments không trả 403 (nhận $status)"
  for spec in "PUT /api/assignments" "POST /api/assignments/import"; do
    read -r method path <<<"$spec"
    status="$(curl -sk -o /dev/null -w '%{http_code}' -X "$method" "$BASE$path" \
      -H "Authorization: Bearer ${!tok_var}" -H 'Content-Type: application/json' -d '{}')"
    [ "$status" = "403" ] || fail "${who} ${method} ${path} không trả 403 (nhận $status)"
  done
done
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/assignments/my-students" -H "Authorization: Bearer ${TOKEN_BOMON}")"
[ "$status" = "403" ] || fail "bomon xem /api/assignments/my-students không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/assignments/my-advisor" -H "Authorization: Bearer ${TOKEN_GV001}")"
[ "$status" = "403" ] || fail "GV001 xem /api/assignments/my-advisor không trả 403 (nhận $status)"
status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/assignments/my-students" -H "Authorization: Bearer ${TOKEN_GV001}")"
[ "$status" = "200" ] || fail "GV001 xem /api/assignments/my-students không trả 200 (nhận $status)"
advisor_body="$(curl -sk "$BASE/api/assignments/my-advisor" -H "Authorization: Bearer ${TOKEN_SV001}")"
advisor_ok="$(printf '%s' "$advisor_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(1 if any(r["giang_vien"]["ma"] == "GV001" for r in d) else 0)' 2>/dev/null || true)"
[ "$advisor_ok" = "1" ] || fail "DTC235200016 xem /api/assignments/my-advisor không thấy GVHD GV001 (seed mặc định) (${advisor_body})"
echo "OK: /api/assignments — gán/import/xem chỉ bomon (GV001, DTC235200016 bị 403); my-students chỉ GV, my-advisor chỉ SV; DTC235200016 có GVHD GV001"

status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topics" -H "Authorization: Bearer ${TOKEN_SV001}")"
[ "$status" = "200" ] || fail "DTC235200016 xem /api/topics không trả 200 (nhận $status)"
echo "OK: DTC235200016 xem /api/topics -> 200"

# --- Phase 3 (plan 03-07): mỗi nhóm route mới chỉ đúng vai trò gọi được ---
# expect_status CODE METHOD PATH TOKEN MÔ_TẢ — gửi thân JSON rỗng cho POST/PUT;
# require_role chặn trước khi kiểm tra thân/đối tượng nên không cần id thật.
expect_status() {
  local want="$1" method="$2" path="$3" token="$4" label="$5" got
  if [ "$method" = "GET" ]; then
    got="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE$path" -H "Authorization: Bearer ${token}")"
  else
    got="$(curl -sk -o /dev/null -w '%{http_code}' -X "$method" "$BASE$path" \
      -H "Authorization: Bearer ${token}" -H 'Content-Type: application/json' -d '{}')"
  fi
  [ "$got" = "$want" ] || fail "${label}: ${method} ${path} không trả ${want} (nhận ${got})"
}

expect_status 403 POST /api/defense/committees "${TOKEN_SV001}" DTC235200016
expect_status 403 POST /api/archive "${TOKEN_SV001}" DTC235200016
expect_status 403 POST /api/archive/import "${TOKEN_SV001}" DTC235200016
expect_status 403 POST /api/progress/milestones "${TOKEN_SV001}" DTC235200016
expect_status 403 GET /api/progress/dashboard "${TOKEN_SV001}" DTC235200016
expect_status 403 POST /api/outlines/1/review "${TOKEN_SV001}" DTC235200016
echo "OK: DTC235200016 bị 403 trên defense/committees, archive (thêm, import), progress (mốc, dashboard), outlines review"

expect_status 403 POST /api/outlines/1/submit "${TOKEN_GV001}" GV001
expect_status 403 POST /api/defense/schedules/1/finalize "${TOKEN_GV001}" GV001
expect_status 403 POST /api/progress/reports/1 "${TOKEN_GV001}" GV001
echo "OK: GV001 bị 403 trên outlines submit, defense finalize, progress reports"

expect_status 403 POST /api/outlines/1/review "${TOKEN_BOMON}" bomon
expect_status 403 PUT /api/defense/schedules/1/score "${TOKEN_BOMON}" bomon
echo "OK: bomon bị 403 trên outlines review, defense score"

for who in BOMON GV001 SV001; do
  tok_var="TOKEN_${who}"
  expect_status 200 GET /api/notifications "${!tok_var}" "$who"
  expect_status 200 GET /api/notifications/unread-count "${!tok_var}" "$who"
  expect_status 200 GET /api/archive "${!tok_var}" "$who"
done
echo "OK: cả ba vai trò đọc được notifications, notifications/unread-count, archive -> 200"

# UC0.4/AISV-07 (04-07, T-04-29): chỉ Bộ môn đọc/sửa ngưỡng trùng lặp.
for who in GV001 SV001; do
  tok_var="TOKEN_${who}"
  expect_status 403 GET /api/thresholds "${!tok_var}" "$who"
  expect_status 403 PUT /api/thresholds "${!tok_var}" "$who"
done
expect_status 200 GET /api/thresholds "${TOKEN_BOMON}" bomon
echo "OK: /api/thresholds — DTC235200016 và GV001 bị 403 (GET/PUT), bomon GET 200"

echo "SMOKE TEST: tất cả kiểm tra đã qua."
