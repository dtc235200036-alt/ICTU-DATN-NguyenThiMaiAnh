#!/usr/bin/env bash
# ROADMAP SC3/SC5: kịch bản UC1 đầy đủ qua Apache HTTPS theo luồng phân công
# GVHD (0015) — Bộ môn gán SV cho GVHD đầu đợt (UC0.8: gán từng SV + import
# CSV, xem danh sách), SV chưa có GVHD không đề xuất được, SV tự đề xuất -> GVHD
# duyệt/từ chối, GV mở đề tài cho lớp -> SV trong lớp đăng ký là Đã phân công
# ngay, GV giao thẳng đề tài cho SV trong lớp, không đổi GVHD khi đã có đề tài
# Đã phân công, SV lớp khác không thấy/không đăng ký được, 403 cho sai vai trò
# (SV, Bộ môn, GV không phải GVHD), lọc danh sách theo đợt/trạng thái/GVHD.
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
    # NOTF-01 (plan 03-07) + 0015: duyệt/từ chối/gửi đề tài và phân công GVHD
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

# (b) SV chưa được phân công GVHD trong đợt -> không đề xuất được (409)
unassigned_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề xuất khi chưa có GVHD\",\"linh_vuc\":\"Công nghệ phần mềm\",\"gui\":true}")"
[ "$unassigned_status" = "409" ] || fail "SV chưa có GVHD đề xuất đề tài không trả 409 (nhận ${unassigned_status}: $(cat /tmp/ntma-e2e-uc1.json))"
grep -q "chưa được Bộ môn phân công" /tmp/ntma-e2e-uc1.json || fail "Thông báo 409 khi chưa có GVHD không đúng ($(cat /tmp/ntma-e2e-uc1.json))"
echo "OK: SV chưa được phân công GVHD đề xuất đề tài -> 409"

# (c) Bộ môn phân công GVHD: gán hàng loạt (PUT) DTC235210040, DTC235210045 ->
# GV030; import CSV DTC235210023 -> GV024 (lớp khác)
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

# (d) GV030 mở đề tài cho lớp (gửi, không chọn SV) -> Đã duyệt, có kiểm tra tên
gv_topic_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài do GV đề xuất\",\"linh_vuc\":\"Hệ thống thông tin\",\"gui\":true}")"
GV_TOPIC_ID="$(jfield "$gv_topic_body" 'd["id"]')"
gv_ok="$(jfield "$gv_topic_body" '1 if d.get("trang_thai") == "DA_DUYET" and d.get("sinh_vien") is None and d.get("kiem_tra_ten") is not None else 0')"
[ -n "$GV_TOPIC_ID" ] && [ "$gv_ok" = "1" ] || fail "Đề tài GV mở cho lớp không đúng trạng thái/kiểm tra tên (${gv_topic_body})"
echo "OK: GV030 mở đề tài cho lớp -> Đã duyệt (chờ SV trong lớp đăng ký), có kiểm tra tên"

# (e) DTC235210040 tự đề xuất đề tài -> Chờ duyệt, GVHD = GV030
sv_topic_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài SV tự đề xuất\",\"linh_vuc\":\"Công nghệ phần mềm\",\"gui\":true}")"
SV_TOPIC_ID="$(jfield "$sv_topic_body" 'd["id"]')"
sv_ok="$(jfield "$sv_topic_body" '1 if d.get("trang_thai") == "CHO_DUYET" and (d.get("giang_vien_huong_dan") or {}).get("ma") == "GV030" else 0')"
[ -n "$SV_TOPIC_ID" ] && [ "$sv_ok" = "1" ] || fail "Đề tài SV tự đề xuất không ở Chờ duyệt với GVHD GV030 (${sv_topic_body})"
echo "OK: DTC235210040 tự đề xuất đề tài -> Chờ duyệt, gửi tới GVHD GV030"

# (f) GV030 thấy đề tài trong danh sách chờ duyệt của mình; GV024 thì không
pending_body="$(curl -sk "$BASE/api/topic-approvals?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" \
  -H "Authorization: Bearer ${TOKEN_GV}")"
[ "$(jfield "$pending_body" "1 if [i['id'] for i in d['items']] == [${SV_TOPIC_ID}] else 0")" = "1" ] \
  || fail "Danh sách chờ duyệt của GV030 không đúng chỉ đề tài SV vừa gửi (${pending_body})"
pending_other="$(curl -sk "$BASE/api/topic-approvals?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" \
  -H "Authorization: Bearer ${TOKEN_GV_KHAC}")"
[ "$(jfield "$pending_other" "1 if not d['items'] else 0")" = "1" ] \
  || fail "GV024 (không phải GVHD) vẫn thấy đề tài chờ duyệt của lớp GV030 (${pending_other})"
echo "OK: GV030 thấy đề tài SV trong danh sách chờ duyệt; GV024 không thấy"

# (g) 403: SV duyệt, Bộ môn duyệt, GV không phải GVHD duyệt/từ chối; GV030 sửa
# đề tài do SV đề xuất -> 403
for spec in "SV_A|SV duyệt đề tài" "BOMON|Bộ môn duyệt đề tài (0015: chỉ GVHD duyệt)" "GV_KHAC|GV024 (không phải GVHD) duyệt đề tài"; do
  who="${spec%%|*}"; label="${spec#*|}"
  tok_var="TOKEN_${who}"
  status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST \
    "$BASE/api/topic-approvals/${SV_TOPIC_ID}/approve" -H "Authorization: Bearer ${!tok_var}")"
  [ "$status" = "403" ] || fail "${label} không trả 403 (nhận ${status})"
done
for who in BOMON GV_KHAC; do
  tok_var="TOKEN_${who}"
  status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST \
    "$BASE/api/topic-approvals/${SV_TOPIC_ID}/reject" -H "Authorization: Bearer ${!tok_var}" \
    -H 'Content-Type: application/json' -d '{"ly_do":"Từ chối trái phép"}')"
  [ "$status" = "403" ] || fail "${who} từ chối đề tài không phải lớp mình không trả 403 (nhận ${status})"
done
still_body="$(curl -sk "$BASE/api/topics/${SV_TOPIC_ID}" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$(jfield "$still_body" 'd["trang_thai"]')" = "CHO_DUYET" ] || fail "Đề tài SV đổi trạng thái sau các lần duyệt/từ chối bị 403 (${still_body})"
echo "OK: SV, Bộ môn, GV024 duyệt/từ chối -> 403, đề tài vẫn Chờ duyệt"

gv_edit_sv_topic_status="$(curl -sk -o /dev/null -w '%{http_code}' -X PUT \
  "$BASE/api/topics/${SV_TOPIC_ID}" -H "Authorization: Bearer ${TOKEN_GV}" \
  -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"Sửa trái phép\",\"linh_vuc\":\"Hệ thống thông tin\"}")"
[ "$gv_edit_sv_topic_status" = "403" ] || fail "GV sửa đề tài do SV đề xuất không trả 403 (nhận ${gv_edit_sv_topic_status})"
echo "OK: GV sửa đề tài do SV đề xuất -> 403"

# (h) SV lớp khác (DTC235210023, GVHD GV024) không thấy, không đăng ký được đề
# tài GV030 mở cho lớp
other_view_status="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/topics/${GV_TOPIC_ID}" \
  -H "Authorization: Bearer ${TOKEN_SV_C}")"
[ "$other_view_status" = "403" ] || fail "SV lớp khác xem đề tài GV030 mở cho lớp không trả 403 (nhận ${other_view_status})"
other_list="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" -H "Authorization: Bearer ${TOKEN_SV_C}")"
[ "$(jfield "$other_list" "1 if all(i['id'] != ${GV_TOPIC_ID} for i in d['items']) else 0")" = "1" ] \
  || fail "SV lớp khác thấy đề tài GV030 mở cho lớp trong danh sách (${other_list})"
other_register_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST \
  "$BASE/api/topics/${GV_TOPIC_ID}/register" -H "Authorization: Bearer ${TOKEN_SV_C}")"
[ "$other_register_status" = "403" ] || fail "SV lớp khác đăng ký đề tài GV030 không trả 403 (nhận ${other_register_status})"
own_list="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" -H "Authorization: Bearer ${TOKEN_SV_B}")"
[ "$(jfield "$own_list" "1 if any(i['id'] == ${GV_TOPIC_ID} and i['co_the_dang_ky'] for i in d['items']) else 0")" = "1" ] \
  || fail "SV lớp GV030 không thấy đề tài mở cho lớp (co_the_dang_ky) (${own_list})"
echo "OK: SV lớp khác xem/đăng ký đề tài GV030 mở -> 403, không có trong danh sách; SV lớp GV030 thấy và đăng ký được"

# (i) DTC235210045 (lớp GV030) đăng ký đề tài mở -> 200 Đã phân công ngay;
# đăng ký lại -> 409
register_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X POST \
  "$BASE/api/topics/${GV_TOPIC_ID}/register" -H "Authorization: Bearer ${TOKEN_SV_B}")"
[ "$register_status" = "200" ] || fail "SV đăng ký đề tài GV không trả 200 (nhận ${register_status}: $(cat /tmp/ntma-e2e-uc1.json))"
register_trang_thai="$(python3 -c 'import json; print(json.load(open("/tmp/ntma-e2e-uc1.json")).get("trang_thai",""))' 2>/dev/null || true)"
[ "$register_trang_thai" = "DA_PHAN_CONG" ] || fail "Sau đăng ký đề tài không ở Đã phân công (nhận ${register_trang_thai})"
echo "OK: DTC235210045 đăng ký đề tài GV030 mở cho lớp -> Đã phân công (không qua Bộ môn)"

second_register_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST \
  "$BASE/api/topics/${GV_TOPIC_ID}/register" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$second_register_status" = "409" ] || fail "Đăng ký đề tài đã có người không trả 409 (nhận ${second_register_status})"
echo "OK: đăng ký lần hai bị từ chối 409"

# (j) Đổi GVHD của SV đã có đề tài Đã phân công -> 409, phân công giữ nguyên
change_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X PUT "$BASE/api/assignments" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"items\":[{\"sinh_vien_id\":${SV_B_ID},\"giang_vien_id\":${GV024_ID}}]}")"
[ "$change_status" = "409" ] || fail "Đổi GVHD của SV đã có đề tài Đã phân công không trả 409 (nhận ${change_status}: $(cat /tmp/ntma-e2e-uc1.json))"
kept_body="$(curl -sk "$BASE/api/assignments?dot_do_an_id=${DOT_DO_AN_ID}&q=DTC235210045" -H "Authorization: Bearer ${TOKEN_BOMON}")"
[ "$(jfield "$kept_body" "next(r['giang_vien']['ma'] for r in d['items'] if r['sinh_vien']['ma'] == 'DTC235210045')")" = "GV030" ] \
  || fail "GVHD của DTC235210045 bị đổi dù đã có đề tài Đã phân công (${kept_body})"
echo "OK: đổi GVHD của SV đã có đề tài Đã phân công -> 409, vẫn là GV030"

# (k) GVHD GV030 từ chối đề tài SV kèm lý do -> Từ chối; SV thấy đúng lý do
reject_body="$(curl -sk -X POST "$BASE/api/topic-approvals/${SV_TOPIC_ID}/reject" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d '{"ly_do":"Kiểm thử tự động: trùng hướng"}')"
[ "$(jfield "$reject_body" 'd.get("trang_thai", "")')" = "TU_CHOI" ] || fail "GVHD từ chối đề tài SV không chuyển Từ chối (${reject_body})"
echo "OK: GVHD GV030 từ chối đề tài SV với lý do"

sv_view_body="$(curl -sk "$BASE/api/topics/${SV_TOPIC_ID}" -H "Authorization: Bearer ${TOKEN_SV_A}")"
printf '%s' "$sv_view_body" | grep -q "Kiểm thử tự động: trùng hướng" || fail "SV không thấy lý do từ chối (${sv_view_body})"
echo "OK: SV thấy đúng lý do từ chối"

# (l) SV đề xuất lại -> GVHD GV030 duyệt (không gửi thân) -> Đã phân công
sv_topic2_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài SV đề xuất lại\",\"linh_vuc\":\"Công nghệ phần mềm\",\"gui\":true}")"
SV_TOPIC2_ID="$(jfield "$sv_topic2_body" 'd["id"]')"
[ -n "$SV_TOPIC2_ID" ] && [ "$(jfield "$sv_topic2_body" 'd["trang_thai"]')" = "CHO_DUYET" ] \
  || fail "SV đề xuất lại sau khi bị từ chối không ở Chờ duyệt (${sv_topic2_body})"
approve_body="$(curl -sk -X POST "$BASE/api/topic-approvals/${SV_TOPIC2_ID}/approve" -H "Authorization: Bearer ${TOKEN_GV}")"
approve_ok="$(jfield "$approve_body" '1 if d.get("trang_thai") == "DA_PHAN_CONG" and (d.get("giang_vien_huong_dan") or {}).get("ma") == "GV030" else 0')"
[ "$approve_ok" = "1" ] || fail "GVHD duyệt đề tài SV không chuyển Đã phân công (${approve_body})"
echo "OK: SV đề xuất lại -> GVHD GV030 duyệt -> Đã phân công"

# (m) GV giao thẳng đề tài (sinh_vien_id): cho SV lớp khác -> 409; cho SV trong
# lớp đã có đề tài đang hoạt động -> 409.
direct_other_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Giao cho SV lớp khác\",\"linh_vuc\":\"Hệ thống thông tin\",\"sinh_vien_id\":${SV_C_ID},\"gui\":true}")"
[ "$direct_other_status" = "409" ] || fail "GV giao đề tài cho SV lớp khác không trả 409 (nhận ${direct_other_status}: $(cat /tmp/ntma-e2e-uc1.json))"
grep -q "không thuộc lớp hướng dẫn" /tmp/ntma-e2e-uc1.json || fail "Thông báo 409 khi giao cho SV lớp khác không đúng ($(cat /tmp/ntma-e2e-uc1.json))"
direct_busy_status="$(curl -sk -o /tmp/ntma-e2e-uc1.json -w '%{http_code}' -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Giao cho SV đã có đề tài\",\"linh_vuc\":\"Hệ thống thông tin\",\"sinh_vien_id\":${SV_B_ID},\"gui\":true}")"
[ "$direct_busy_status" = "409" ] || fail "GV giao đề tài cho SV đã có đề tài đang hoạt động không trả 409 (nhận ${direct_busy_status}: $(cat /tmp/ntma-e2e-uc1.json))"
echo "OK: GV030 giao đề tài cho SV lớp khác -> 409; cho SV đã có đề tài đang hoạt động -> 409"

# Giao thẳng thành công: Bộ môn chuyển DTC235210023 (chưa có đề tài) sang lớp
# GV030 rồi GV030 giao đề tài kèm sinh_vien_id -> Đã phân công ngay.
move_body="$(curl -sk -X PUT "$BASE/api/assignments" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"items\":[{\"sinh_vien_id\":${SV_C_ID},\"giang_vien_id\":${GV030_ID}}]}")"
[ "$(jfield "$move_body" 'd["cap_nhat"]')" = "1" ] || fail "Bộ môn đổi GVHD của SV chưa có đề tài không thành công (${move_body})"
direct_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài GV giao thẳng\",\"linh_vuc\":\"Hệ thống thông tin\",\"sinh_vien_id\":${SV_C_ID},\"gui\":true}")"
DIRECT_TOPIC_ID="$(jfield "$direct_body" 'd["id"]')"
direct_ok="$(jfield "$direct_body" '1 if d.get("trang_thai") == "DA_PHAN_CONG" and (d.get("sinh_vien") or {}).get("ma") == "DTC235210023" else 0')"
[ -n "$DIRECT_TOPIC_ID" ] && [ "$direct_ok" = "1" ] || fail "GV giao thẳng đề tài cho SV trong lớp không Đã phân công ngay (${direct_body})"
echo "OK: Bộ môn đổi GVHD của SV chưa có đề tài (GV024 -> GV030); GV030 giao thẳng đề tài -> Đã phân công ngay"

# (n) Bộ môn lọc danh sách theo đợt/trạng thái/GVHD -> đúng 3 đề tài đã phân công
filtered_body="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&trang_thai=DA_PHAN_CONG&giang_vien_id=${GV030_ID}" \
  -H "Authorization: Bearer ${TOKEN_BOMON}")"
filtered_ok="$(jfield "$filtered_body" "1 if sorted(i['id'] for i in d['items']) == sorted([${GV_TOPIC_ID}, ${SV_TOPIC2_ID}, ${DIRECT_TOPIC_ID}]) else 0")"
[ "$filtered_ok" = "1" ] || fail "Lọc theo đợt/trạng thái/GVHD không trả đúng các đề tài đã phân công (${filtered_body})"
echo "OK: lọc danh sách theo đợt/trạng thái/GVHD trả đúng 3 đề tài đã phân công"

echo "OK: e2e UC1 hoàn tất — dữ liệu đợt K99 (đề tài, phân công GVHD) sẽ được dọn khi script kết thúc (trap)"
