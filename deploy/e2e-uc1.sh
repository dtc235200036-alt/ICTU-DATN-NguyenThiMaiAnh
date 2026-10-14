#!/usr/bin/env bash
# ROADMAP SC3/SC5: kịch bản UC1 đầy đủ qua Apache HTTPS theo luồng GVHD giao
# đề tài (góp ý GVHD mục 1, quick 261014-u0j) — Bộ môn gán SV cho GVHD đầu đợt
# (UC0.8: gán từng SV + import CSV, xem danh sách); SV KHÔNG tự đề xuất/đăng ký
# đề tài; chỉ GVHD được Bộ môn phân công kiểm tra trùng tên (UC0.6) và tạo/giao
# đề tài cho SV trong lớp mình -> Đã phân công ngay, SV nhận thông báo và chỉ
# thấy đề tài của chính mình; lưu nháp rồi gửi; 1 SV : 1 đề tài đang hoạt động;
# GV không phải GVHD / SV lớp khác bị từ chối; SV và Bộ môn gọi chức năng tạo/
# sửa/gửi/kiểm tra tên -> 403, route đăng ký và duyệt đã gỡ -> 404; không đổi
# GVHD khi đã có đề tài Đã phân công; lọc danh sách theo đợt/trạng thái/GVHD.
# Dùng riêng một đợt khóa K99 và 5 tài khoản seed (GV030 + DTC235210040,
# DTC235210045 lớp GV030; GV024 + DTC235210023 lớp khác) — tự dọn dữ liệu của
# chính nó khi kết thúc, kể cả khi có bước lỗi giữa chừng (T-02-39).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${BASE_URL:-https://localhost:${HTTPS_PORT:-443}}"

fail() {
  echo "FAIL: $1"
  exit 1
}

DOT_DO_AN_ID=""
START_UTC="$(date -u +%Y-%m-%dT%H:%M:%S)"
RESERVED_IN="'GV030','GV024','DTC235210040','DTC235210045','DTC235210023'"

cleanup() {
  rm -f /tmp/ntma-e2e-uc1.json
  if [ -n "${DOT_DO_AN_ID}" ]; then
    # Phase 4 (04-05): gỡ vector các đề tài K99 (TOPIC) khỏi chỉ mục AI TRƯỚC
    # khi xóa hàng — chạy lại test không để lại vector mồ côi.
    local purge_topic_ids
    purge_topic_ids="$(DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" 2>/dev/null | paste -sd, - || true)"
    if [ -n "${purge_topic_ids}" ]; then
      docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api \
        python -m app.services.ai_index purge --loai TOPIC --ids "${purge_topic_ids}" >/dev/null 2>&1 || true
    fi
    # NOTF-01 (plan 03-07) + 0015: giao đề tài và phân công GVHD
    # tạo thông báo — chỉ xóa thông báo của các tài khoản dành riêng, phát sinh
    # từ lúc script bắt đầu.
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM thong_bao WHERE tai_khoan_id IN (SELECT id FROM tai_khoan WHERE ma_dang_nhap IN (${RESERVED_IN})) AND thoi_diem >= '${START_UTC}';" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE ct FROM chi_tiet_trung_lap ct JOIN ket_qua_kiem_tra_trung_lap kq ON kq.id = ct.ket_qua_id JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE kq FROM ket_qua_kiem_tra_trung_lap kq JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    # 0015: phân công GVHD trỏ tới đợt (FK không cascade) — xóa trước đợt.
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM phan_cong_huong_dan WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM dot_do_an WHERE id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# jfield JSON EXPR — in giá trị biểu thức Python trên `d` (rỗng nếu lỗi).
jfield() {
  printf '%s' "$1" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print($2)
" 2>/dev/null || true
}

TOKEN_BOMON="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
TOKEN_GV="$(bash "${SCRIPT_DIR}/api-login.sh" GV030)"
TOKEN_GV_KHAC="$(bash "${SCRIPT_DIR}/api-login.sh" GV024)"
TOKEN_SV_A="$(bash "${SCRIPT_DIR}/api-login.sh" DTC235210040)"
TOKEN_SV_B="$(bash "${SCRIPT_DIR}/api-login.sh" DTC235210045)"
TOKEN_SV_C="$(bash "${SCRIPT_DIR}/api-login.sh" DTC235210023)"

# (a) Bộ môn tạo đợt kiểm thử K99
cohort_body="$(curl -sk -X POST "$BASE/api/cohorts" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d '{"ten_dot":"Đợt kiểm thử tự động","khoa":"K99","nam_hoc":"2026-2027","ngay_bat_dau":"2026-01-01"}')"
DOT_DO_AN_ID="$(jfield "$cohort_body" 'd["id"]')"
[ -n "$DOT_DO_AN_ID" ] || fail "Không tạo được đợt kiểm thử K99 (${cohort_body})"
echo "OK: Bộ môn tạo đợt kiểm thử K99 (id=${DOT_DO_AN_ID})"

# (c0) Tìm id GV/SV (qua Bộ môn) để dùng ở các bước sau
lecturers_body="$(curl -sk "$BASE/api/lecturers" -H "Authorization: Bearer ${TOKEN_BOMON}")"
GV030_ID="$(jfield "$lecturers_body" 'next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV030"), "")')"
GV024_ID="$(jfield "$lecturers_body" 'next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV024"), "")')"
[ -n "$GV030_ID" ] && [ -n "$GV024_ID" ] || fail "Không tìm được id GV030/GV024 trong /api/lecturers"

# sv_id MA — sinh_vien.id qua danh sách phân công của đợt (tìm theo mã).
sv_id() {
  local body
  body="$(curl -sk "$BASE/api/assignments?dot_do_an_id=${DOT_DO_AN_ID}&q=$1" -H "Authorization: Bearer ${TOKEN_BOMON}")"
  jfield "$body" "next((r['sinh_vien']['id'] for r in d['items'] if r['sinh_vien']['ma'] == '$1'), '')"
}
SV_A_ID="$(sv_id DTC235210040)"
SV_B_ID="$(sv_id DTC235210045)"
SV_C_ID="$(sv_id DTC235210023)"
[ -n "$SV_A_ID" ] && [ -n "$SV_B_ID" ] && [ -n "$SV_C_ID" ] || fail "Không tìm được id SV trong /api/assignments (A=${SV_A_ID} B=${SV_B_ID} C=${SV_C_ID})"

# (b) GV030 chưa là GVHD của DTC235210040 trong đợt -> không giao được (409)
unassigned_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Giao đề tài khi chưa phân công\",\"linh_vuc\":\"Công nghệ phần mềm\",\"sinh_vien_id\":${SV_A_ID},\"gui\":true}")"
[ "$unassigned_status" = "409" ] || fail "GV giao đề tài cho SV chưa được phân công không trả 409 (nhận ${unassigned_status}: $(cat /tmp/ntma-e2e-uc1.json))"
grep -q "không thuộc lớp hướng dẫn" /tmp/ntma-e2e-uc1.json || fail "Thông báo 409 khi chưa phân công không đúng ($(cat /tmp/ntma-e2e-uc1.json))"
echo "OK: GV030 giao đề tài cho SV chưa được Bộ môn phân công -> 409 (không thuộc lớp hướng dẫn)"

# (c) Bộ môn phân công GVHD: gán hàng loạt (PUT) DTC235210040, DTC235210045 ->
# GV030; import CSV DTC235210023 -> GV024 (lớp khác)
assign_body="$(curl -sk -X PUT "$BASE/api/assignments" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"items\":[{\"sinh_vien_id\":${SV_A_ID},\"giang_vien_id\":${GV030_ID}},{\"sinh_vien_id\":${SV_B_ID},\"giang_vien_id\":${GV030_ID}}]}")"
[ "$(jfield "$assign_body" 'd["cap_nhat"]')" = "2" ] || fail "Bộ môn gán GVHD hàng loạt không cập nhật đúng 2 SV (${assign_body})"
import_body="$(curl -sk -X POST "$BASE/api/assignments/import" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"noi_dung\":\"ma_so_sinh_vien,ma_giang_vien\nDTC235210023,GV024\nKHONG_TON_TAI,GV024\n\"}")"
import_ok="$(jfield "$import_body" '1 if d["cap_nhat"] == 1 and len(d["loi"]) == 1 and "KHONG_TON_TAI" in d["loi"][0] else 0')"
[ "$import_ok" = "1" ] || fail "Import CSV phân công không cập nhật 1 dòng + báo 1 lỗi mã lạ (${import_body})"
echo "OK: Bộ môn gán DTC235210040, DTC235210045 -> GV030 (PUT) và import DTC235210023 -> GV024 (dòng mã lạ báo lỗi)"

list_body="$(curl -sk "$BASE/api/assignments?dot_do_an_id=${DOT_DO_AN_ID}&giang_vien_id=${GV030_ID}&loc=da_phan_cong&page_size=50" \
  -H "Authorization: Bearer ${TOKEN_BOMON}")"
list_ok="$(jfield "$list_body" "1 if sorted(r['sinh_vien']['ma'] for r in d['items']) == ['DTC235210040', 'DTC235210045'] and all(r['giang_vien']['ma'] == 'GV030' for r in d['items']) and d['da_phan_cong'] == 3 and next(t['so_sinh_vien'] for t in d['tai_giang_vien'] if t['giang_vien']['ma'] == 'GV030') == 2 else 0")"
[ "$list_ok" = "1" ] || fail "Danh sách phân công lọc theo GV030 không đúng (${list_body})"
echo "OK: danh sách phân công đợt K99 lọc theo GV030 có đúng 2 SV, đợt có 3 SV đã phân công, tải GV030 = 2"

advisor_body="$(curl -sk "$BASE/api/assignments/my-advisor" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$(jfield "$advisor_body" "next((r['giang_vien']['ma'] for r in d if r['dot_do_an']['id'] == ${DOT_DO_AN_ID}), '')")" = "GV030" ] \
  || fail "DTC235210040 không thấy GVHD GV030 trong đợt K99 (${advisor_body})"
students_body="$(curl -sk "$BASE/api/assignments/my-students?dot_do_an_id=${DOT_DO_AN_ID}" -H "Authorization: Bearer ${TOKEN_GV}")"
[ "$(jfield "$students_body" "sorted(i['sinh_vien']['ma'] for i in d[0]['items'])")" = "['DTC235210040', 'DTC235210045']" ] \
  || fail "GV030 không thấy đúng 2 SV trong lớp hướng dẫn K99 (${students_body})"
echo "OK: SV thấy GVHD của mình (my-advisor), GV030 thấy lớp hướng dẫn 2 SV (my-students)"

# (d) UC0.6: GV030 kiểm tra trùng tên -> 200; SV kiểm tra tên -> 403
check_gv_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/topics/check-title" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d '{"ten_de_tai":"E2E - Đề tài do GVHD giao"}')"
[ "$check_gv_status" = "200" ] || fail "GVHD kiểm tra trùng tên không trả 200 (nhận ${check_gv_status})"
check_sv_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/topics/check-title" \
  -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d '{"ten_de_tai":"E2E - Đề tài do GVHD giao"}')"
[ "$check_sv_status" = "403" ] || fail "SV kiểm tra trùng tên không trả 403 (nhận ${check_sv_status})"
echo "OK: GV030 kiểm tra trùng tên -> 200; SV kiểm tra trùng tên -> 403"

# (e) GV030 tạo và giao đề tài cho DTC235210040 -> Đã phân công, có kiểm tra tên;
# SV nhận thông báo
topic_a_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài do GVHD giao\",\"linh_vuc\":\"Hệ thống thông tin\",\"sinh_vien_id\":${SV_A_ID},\"gui\":true}")"
TOPIC_A_ID="$(jfield "$topic_a_body" 'd["id"]')"
topic_a_ok="$(jfield "$topic_a_body" '1 if d.get("trang_thai") == "DA_PHAN_CONG" and (d.get("sinh_vien") or {}).get("ma") == "DTC235210040" and (d.get("giang_vien_huong_dan") or {}).get("ma") == "GV030" and d.get("kiem_tra_ten") is not None else 0')"
[ -n "$TOPIC_A_ID" ] && [ "$topic_a_ok" = "1" ] || fail "GVHD giao đề tài không ở Đã phân công / thiếu kiểm tra tên (${topic_a_body})"
notif_body="$(curl -sk "$BASE/api/notifications" -H "Authorization: Bearer ${TOKEN_SV_A}")"
printf '%s' "$notif_body" | grep -q "E2E - Đề tài do GVHD giao" || fail "SV không nhận thông báo giao đề tài (${notif_body})"
echo "OK: GV030 giao đề tài cho DTC235210040 -> Đã phân công ngay, có kiểm tra tên; SV nhận thông báo"

# (f) SV chỉ thấy đề tài của mình; SV lớp khác (DTC235210023) không xem được
own_view_status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topics/${TOPIC_A_ID}" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$own_view_status" = "200" ] || fail "SV được giao không xem được đề tài của mình (nhận ${own_view_status})"
own_list="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$(jfield "$own_list" "1 if [i['id'] for i in d['items']] == [${TOPIC_A_ID}] else 0")" = "1" ] \
  || fail "SV được giao không thấy đúng đề tài của mình trong danh sách (${own_list})"
other_view_status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topics/${TOPIC_A_ID}" -H "Authorization: Bearer ${TOKEN_SV_C}")"
[ "$other_view_status" = "403" ] || fail "SV lớp khác xem đề tài không trả 403 (nhận ${other_view_status})"
other_list="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" -H "Authorization: Bearer ${TOKEN_SV_C}")"
[ "$(jfield "$other_list" "1 if all(i['id'] != ${TOPIC_A_ID} for i in d['items']) else 0")" = "1" ] \
  || fail "SV lớp khác thấy đề tài của SV khác trong danh sách (${other_list})"
echo "OK: DTC235210040 thấy đúng đề tài được giao; SV lớp khác xem -> 403 và không có trong danh sách"

# (g) GV030 lưu nháp cho DTC235210045 -> Nháp, SV chưa thấy; GV030 gửi -> Đã phân công
draft_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Bản nháp GVHD soạn\",\"linh_vuc\":\"Công nghệ phần mềm\",\"sinh_vien_id\":${SV_B_ID},\"gui\":false}")"
TOPIC_B_ID="$(jfield "$draft_body" 'd["id"]')"
[ -n "$TOPIC_B_ID" ] && [ "$(jfield "$draft_body" 'd["trang_thai"]')" = "NHAP" ] || fail "GVHD lưu nháp không ở trạng thái Nháp (${draft_body})"
draft_view_status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topics/${TOPIC_B_ID}" -H "Authorization: Bearer ${TOKEN_SV_B}")"
[ "$draft_view_status" = "403" ] || fail "SV xem được bản nháp GV đang soạn (nhận ${draft_view_status})"
draft_list="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" -H "Authorization: Bearer ${TOKEN_SV_B}")"
[ "$(jfield "$draft_list" "1 if all(i['id'] != ${TOPIC_B_ID} for i in d['items']) else 0")" = "1" ] \
  || fail "SV thấy bản nháp GV đang soạn trong danh sách (${draft_list})"
submit_body="$(curl -sk -X POST "$BASE/api/topics/${TOPIC_B_ID}/submit" -H "Authorization: Bearer ${TOKEN_GV}")"
[ "$(jfield "$submit_body" 'd.get("trang_thai", "")')" = "DA_PHAN_CONG" ] || fail "GVHD gửi bản nháp không chuyển Đã phân công (${submit_body})"
sv_b_view_status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topics/${TOPIC_B_ID}" -H "Authorization: Bearer ${TOKEN_SV_B}")"
[ "$sv_b_view_status" = "200" ] || fail "SV không xem được đề tài sau khi GVHD gửi nháp (nhận ${sv_b_view_status})"
echo "OK: GV030 lưu nháp cho DTC235210045 (SV không thấy) rồi gửi -> Đã phân công, SV xem được"

# (h) RBAC: 403 cho SV/Bộ môn ở các route chỉ GV; 404 cho route đã gỡ; 409/422
# cho các ca nghiệp vụ
status_of() { curl -sk -o /dev/null -w '%{http_code}' "$@"; }
t="$(status_of -X POST "$BASE/api/topics" -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - SV tự đề xuất\",\"sinh_vien_id\":${SV_A_ID},\"gui\":true}")"
[ "$t" = "403" ] || fail "SV tạo đề tài không trả 403 (nhận ${t})"
t="$(status_of -X PUT "$BASE/api/topics/${TOPIC_A_ID}" -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"Sửa trái phép\",\"sinh_vien_id\":${SV_A_ID}}")"
[ "$t" = "403" ] || fail "SV sửa đề tài không trả 403 (nhận ${t})"
t="$(status_of -X POST "$BASE/api/topics/${TOPIC_A_ID}/submit" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$t" = "403" ] || fail "SV gửi đề tài không trả 403 (nhận ${t})"
t="$(status_of -X POST "$BASE/api/topics" -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Bộ môn tạo đề tài\",\"sinh_vien_id\":${SV_A_ID},\"gui\":true}")"
[ "$t" = "403" ] || fail "Bộ môn tạo đề tài không trả 403 (nhận ${t})"
t="$(status_of -X POST "$BASE/api/topics/${TOPIC_A_ID}/register" -H "Authorization: Bearer ${TOKEN_SV_C}")"
[ "$t" = "404" ] || fail "Route đăng ký đề tài đã gỡ nhưng không trả 404 (nhận ${t})"
t="$(status_of "$BASE/api/topic-approvals?dot_do_an_id=${DOT_DO_AN_ID}" -H "Authorization: Bearer ${TOKEN_GV}")"
[ "$t" = "404" ] || fail "Route duyệt đề tài đã gỡ nhưng không trả 404 (nhận ${t})"
echo "OK: SV tạo/sửa/gửi đề tài và Bộ môn tạo đề tài -> 403; route đăng ký và duyệt đề tài đã gỡ -> 404"

t="$(status_of -X POST "$BASE/api/topics" -H "Authorization: Bearer ${TOKEN_GV_KHAC}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - GV khác giao đề tài\",\"sinh_vien_id\":${SV_A_ID},\"gui\":true}")"
[ "$t" = "409" ] || fail "GV024 (không phải GVHD) giao đề tài không trả 409 (nhận ${t})"
t="$(status_of "$BASE/api/topics/${TOPIC_A_ID}" -H "Authorization: Bearer ${TOKEN_GV_KHAC}")"
[ "$t" = "403" ] || fail "GV024 xem đề tài của GV030 không trả 403 (nhận ${t})"
busy_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Giao thêm cho SV đã có đề tài\",\"sinh_vien_id\":${SV_A_ID},\"gui\":true}")"
[ "$busy_status" = "409" ] || fail "Giao thêm đề tài cho SV đã có đề tài đang hoạt động không trả 409 (nhận ${busy_status}: $(cat /tmp/ntma-e2e-uc1.json))"
grep -q "đã có một đề tài đang hoạt động" /tmp/ntma-e2e-uc1.json || fail "Thông báo 409 SV đã có đề tài không đúng ($(cat /tmp/ntma-e2e-uc1.json))"
t="$(status_of -X POST "$BASE/api/topics" -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Thiếu sinh viên được giao\",\"gui\":true}")"
[ "$t" = "422" ] || fail "GV tạo đề tài không có sinh_vien_id không trả 422 (nhận ${t})"
echo "OK: GV024 giao đề tài -> 409, xem đề tài GV030 -> 403; giao thêm cho SV đã có đề tài -> 409; thiếu sinh_vien_id -> 422"

# (i) Đổi GVHD của SV đã có đề tài Đã phân công -> 409, phân công giữ nguyên
change_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X PUT "$BASE/api/assignments" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"items\":[{\"sinh_vien_id\":${SV_B_ID},\"giang_vien_id\":${GV024_ID}}]}")"
[ "$change_status" = "409" ] || fail "Đổi GVHD của SV đã có đề tài Đã phân công không trả 409 (nhận ${change_status}: $(cat /tmp/ntma-e2e-uc1.json))"
kept_body="$(curl -sk "$BASE/api/assignments?dot_do_an_id=${DOT_DO_AN_ID}&q=DTC235210045" -H "Authorization: Bearer ${TOKEN_BOMON}")"
[ "$(jfield "$kept_body" "next(r['giang_vien']['ma'] for r in d['items'] if r['sinh_vien']['ma'] == 'DTC235210045')")" = "GV030" ] \
  || fail "GVHD của DTC235210045 bị đổi dù đã có đề tài Đã phân công (${kept_body})"
echo "OK: đổi GVHD của SV đã có đề tài Đã phân công -> 409, vẫn là GV030"

# (j) Bộ môn chuyển DTC235210023 (chưa có đề tài) sang lớp GV030 rồi GV030 giao đề tài
move_body="$(curl -sk -X PUT "$BASE/api/assignments" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"items\":[{\"sinh_vien_id\":${SV_C_ID},\"giang_vien_id\":${GV030_ID}}]}")"
[ "$(jfield "$move_body" 'd["cap_nhat"]')" = "1" ] || fail "Bộ môn đổi GVHD của SV chưa có đề tài không thành công (${move_body})"
topic_c_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài GV giao sau khi đổi lớp\",\"linh_vuc\":\"Hệ thống thông tin\",\"sinh_vien_id\":${SV_C_ID},\"gui\":true}")"
TOPIC_C_ID="$(jfield "$topic_c_body" 'd["id"]')"
topic_c_ok="$(jfield "$topic_c_body" '1 if d.get("trang_thai") == "DA_PHAN_CONG" and (d.get("sinh_vien") or {}).get("ma") == "DTC235210023" else 0')"
[ -n "$TOPIC_C_ID" ] && [ "$topic_c_ok" = "1" ] || fail "GV030 giao đề tài cho SV vừa chuyển lớp không Đã phân công (${topic_c_body})"
echo "OK: Bộ môn đổi GVHD của SV chưa có đề tài (GV024 -> GV030); GV030 giao đề tài -> Đã phân công ngay"

# (k) Bộ môn lọc danh sách theo đợt/trạng thái/GVHD -> đúng 3 đề tài đã phân công
filtered_body="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&trang_thai=DA_PHAN_CONG&giang_vien_id=${GV030_ID}" \
  -H "Authorization: Bearer ${TOKEN_BOMON}")"
filtered_ok="$(jfield "$filtered_body" "1 if sorted(i['id'] for i in d['items']) == sorted([${TOPIC_A_ID}, ${TOPIC_B_ID}, ${TOPIC_C_ID}]) else 0")"
[ "$filtered_ok" = "1" ] || fail "Lọc theo đợt/trạng thái/GVHD không trả đúng các đề tài đã phân công (${filtered_body})"
echo "OK: lọc danh sách theo đợt/trạng thái/GVHD trả đúng 3 đề tài đã phân công"

echo "OK: e2e UC1 hoàn tất — dữ liệu đợt K99 (đề tài, phân công GVHD) sẽ được dọn khi script kết thúc (trap)"
