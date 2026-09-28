#!/usr/bin/env bash
# ROADMAP SC3/SC5: kịch bản UC1 đầy đủ qua Apache HTTPS — GV đề xuất, SV tự đề
# xuất, Bộ môn duyệt/phân công/từ chối, SV đăng ký, 403 cho sai vai trò, lọc
# danh sách theo đợt/trạng thái/GVHD. Dùng riêng một đợt khóa K99 và 3 tài
# khoản seed (GV030, DTC225200099, DTC225200100) — tự dọn dữ liệu của chính
# nó khi kết thúc, kể cả khi có bước lỗi giữa chừng (T-02-39).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${BASE_URL:-https://localhost}"

fail() {
  echo "FAIL: $1"
  exit 1
}

DOT_DO_AN_ID=""
START_UTC="$(date -u +%Y-%m-%dT%H:%M:%S)"

cleanup() {
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
    # NOTF-01 (plan 03-07): duyệt/từ chối đề tài giờ tạo thông báo — chỉ xóa
    # thông báo của 3 tài khoản dành riêng, phát sinh từ lúc script bắt đầu.
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM thong_bao WHERE tai_khoan_id IN (SELECT id FROM tai_khoan WHERE ma_dang_nhap IN ('GV030','DTC225200099','DTC225200100')) AND thoi_diem >= '${START_UTC}';" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE ct FROM chi_tiet_trung_lap ct JOIN ket_qua_kiem_tra_trung_lap kq ON kq.id = ct.ket_qua_id JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE kq FROM ket_qua_kiem_tra_trung_lap kq JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM dot_do_an WHERE id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

TOKEN_BOMON="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
TOKEN_GV="$(bash "${SCRIPT_DIR}/api-login.sh" GV030)"
TOKEN_SV_A="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200099)"
TOKEN_SV_B="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200100)"

# (a) Bộ môn tạo đợt kiểm thử K99
cohort_body="$(curl -sk -X POST "$BASE/api/cohorts" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d '{"ten_dot":"Đợt kiểm thử tự động","khoa":"K99","nam_hoc":"2026-2027","ngay_bat_dau":"2026-01-01"}')"
DOT_DO_AN_ID="$(printf '%s' "$cohort_body" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' 2>/dev/null)"
[ -n "$DOT_DO_AN_ID" ] || fail "Không tạo được đợt kiểm thử K99 (${cohort_body})"
echo "OK: Bộ môn tạo đợt kiểm thử K99 (id=${DOT_DO_AN_ID})"

# (b) GV030 đề xuất đề tài, gửi ngay -> Chờ duyệt, có kết quả kiểm tra tên
gv_topic_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_GV}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài do GV đề xuất\",\"linh_vuc\":\"Hệ thống thông tin\",\"gui\":true}")"
GV_TOPIC_ID="$(printf '%s' "$gv_topic_body" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' 2>/dev/null)"
gv_ok="$(printf '%s' "$gv_topic_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(1 if d.get("trang_thai") == "CHO_DUYET" and d.get("kiem_tra_ten") is not None else 0)')"
[ -n "$GV_TOPIC_ID" ] && [ "$gv_ok" = "1" ] || fail "Đề tài GV đề xuất không đúng trạng thái/kiểm tra tên (${gv_topic_body})"
echo "OK: GV030 đề xuất đề tài -> Chờ duyệt, có kiểm tra tên"

# (c) DTC225200099 tự đề xuất đề tài (self-proposal) -> Chờ duyệt
sv_topic_body="$(curl -sk -X POST "$BASE/api/topics" \
  -H "Authorization: Bearer ${TOKEN_SV_A}" -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E - Đề tài SV tự đề xuất\",\"linh_vuc\":\"Công nghệ phần mềm\",\"gui\":true}")"
SV_TOPIC_ID="$(printf '%s' "$sv_topic_body" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' 2>/dev/null)"
sv_trang_thai="$(printf '%s' "$sv_topic_body" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("trang_thai",""))' 2>/dev/null)"
[ -n "$SV_TOPIC_ID" ] && [ "$sv_trang_thai" = "CHO_DUYET" ] || fail "Đề tài SV tự đề xuất không ở Chờ duyệt (${sv_topic_body})"
echo "OK: DTC225200099 tự đề xuất đề tài -> Chờ duyệt"

# (d) Bộ môn xem danh sách chờ duyệt của đợt -> có cả hai đề tài
pending_body="$(curl -sk "$BASE/api/topic-approvals?dot_do_an_id=${DOT_DO_AN_ID}&page_size=50" \
  -H "Authorization: Bearer ${TOKEN_BOMON}")"
pending_ok="$(printf '%s' "$pending_body" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ids = {item['id'] for item in d['items']}
print(1 if {${GV_TOPIC_ID}, ${SV_TOPIC_ID}} <= ids else 0)
" 2>/dev/null)"
[ "$pending_ok" = "1" ] || fail "Danh sách chờ duyệt không có đủ 2 đề tài vừa tạo (${pending_body})"
echo "OK: Bộ môn thấy cả hai đề tài trong danh sách chờ duyệt"

# (e) Bộ môn duyệt đề tài GV (chưa có SV) -> Đã duyệt
approve_gv_body="$(curl -sk -X POST "$BASE/api/topic-approvals/${GV_TOPIC_ID}/approve" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' -d '{}')"
approve_gv_trang_thai="$(printf '%s' "$approve_gv_body" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("trang_thai",""))' 2>/dev/null)"
[ "$approve_gv_trang_thai" = "DA_DUYET" ] || fail "Duyệt đề tài GV không chuyển Đã duyệt (${approve_gv_body})"
echo "OK: Bộ môn duyệt đề tài GV -> Đã duyệt"

# (f) DTC225200100 đăng ký đề tài đã duyệt -> 200 Chờ duyệt; đăng ký lại -> 409
register_status="$(curl -sk -o /tmp/ntma-e2e-register.json -w '%{http_code}' -X POST \
  "$BASE/api/topics/${GV_TOPIC_ID}/register" -H "Authorization: Bearer ${TOKEN_SV_B}")"
[ "$register_status" = "200" ] || fail "SV đăng ký đề tài GV không trả 200 (nhận ${register_status})"
register_trang_thai="$(python3 -c 'import json; print(json.load(open("/tmp/ntma-e2e-register.json")).get("trang_thai",""))' 2>/dev/null)"
rm -f /tmp/ntma-e2e-register.json
[ "$register_trang_thai" = "CHO_DUYET" ] || fail "Sau đăng ký đề tài không ở Chờ duyệt (nhận ${register_trang_thai})"
echo "OK: DTC225200100 đăng ký đề tài GV đã duyệt -> Chờ duyệt"

second_register_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST \
  "$BASE/api/topics/${GV_TOPIC_ID}/register" -H "Authorization: Bearer ${TOKEN_SV_A}")"
[ "$second_register_status" = "409" ] || fail "Đăng ký đề tài đã có người không trả 409 (nhận ${second_register_status})"
echo "OK: đăng ký lần hai bị từ chối 409"

# (g) 403: DTC225200099 duyệt đề tài -> 403; GV030 sửa đề tài của SV khác -> 403
sv_approve_status="$(curl -sk -o /dev/null -w '%{http_code}' -X POST \
  "$BASE/api/topic-approvals/${GV_TOPIC_ID}/approve" -H "Authorization: Bearer ${TOKEN_SV_A}" \
  -H 'Content-Type: application/json' -d '{}')"
[ "$sv_approve_status" = "403" ] || fail "SV duyệt đề tài không trả 403 (nhận ${sv_approve_status})"
echo "OK: SV duyệt đề tài -> 403"

gv_edit_sv_topic_status="$(curl -sk -o /dev/null -w '%{http_code}' -X PUT \
  "$BASE/api/topics/${SV_TOPIC_ID}" -H "Authorization: Bearer ${TOKEN_GV}" \
  -H 'Content-Type: application/json' \
  -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"Sửa trái phép\",\"linh_vuc\":\"Hệ thống thông tin\"}")"
[ "$gv_edit_sv_topic_status" = "403" ] || fail "GV sửa đề tài của SV khác không trả 403 (nhận ${gv_edit_sv_topic_status})"
echo "OK: GV sửa đề tài của SV khác -> 403"

# (h) Bộ môn phân công GVHD (GV030) cho đề tài GV đã có SV -> Đã phân công
lecturers_body="$(curl -sk "$BASE/api/lecturers" -H "Authorization: Bearer ${TOKEN_BOMON}")"
GV030_ID="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV030"), ""))' 2>/dev/null)"
[ -n "$GV030_ID" ] || fail "Không tìm được id GV030 trong /api/lecturers"

assign_body="$(curl -sk -X POST "$BASE/api/topic-approvals/${GV_TOPIC_ID}/approve" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d "{\"giang_vien_id\":${GV030_ID}}")"
assign_trang_thai="$(printf '%s' "$assign_body" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("trang_thai",""))' 2>/dev/null)"
[ "$assign_trang_thai" = "DA_PHAN_CONG" ] || fail "Phân công GVHD không chuyển Đã phân công (${assign_body})"
echo "OK: Bộ môn phân công GVHD cho đề tài GV -> Đã phân công"

# (i) Bộ môn từ chối đề tài SV kèm lý do -> Từ chối; SV thấy đúng lý do
reject_body="$(curl -sk -X POST "$BASE/api/topic-approvals/${SV_TOPIC_ID}/reject" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" -H 'Content-Type: application/json' \
  -d '{"ly_do":"Kiểm thử tự động: trùng hướng"}')"
reject_trang_thai="$(printf '%s' "$reject_body" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("trang_thai",""))' 2>/dev/null)"
[ "$reject_trang_thai" = "TU_CHOI" ] || fail "Từ chối đề tài SV không chuyển Từ chối (${reject_body})"
echo "OK: Bộ môn từ chối đề tài SV với lý do"

sv_view_body="$(curl -sk "$BASE/api/topics/${SV_TOPIC_ID}" -H "Authorization: Bearer ${TOKEN_SV_A}")"
printf '%s' "$sv_view_body" | grep -q "Kiểm thử tự động: trùng hướng" || fail "SV không thấy lý do từ chối (${sv_view_body})"
echo "OK: SV thấy đúng lý do từ chối"

# (j) Bộ môn lọc danh sách theo đợt/trạng thái/GVHD -> đúng đề tài đã phân công
filtered_body="$(curl -sk "$BASE/api/topics?dot_do_an_id=${DOT_DO_AN_ID}&trang_thai=DA_PHAN_CONG&giang_vien_id=${GV030_ID}" \
  -H "Authorization: Bearer ${TOKEN_BOMON}")"
filtered_ok="$(printf '%s' "$filtered_body" | python3 -c "
import json, sys
d = json.load(sys.stdin)
ids = [item['id'] for item in d['items']]
print(1 if ids == [${GV_TOPIC_ID}] else 0)
" 2>/dev/null)"
[ "$filtered_ok" = "1" ] || fail "Lọc theo đợt/trạng thái/GVHD không trả đúng đề tài đã phân công (${filtered_body})"
echo "OK: lọc danh sách theo đợt/trạng thái/GVHD trả đúng đề tài đã phân công"

echo "OK: e2e UC1 hoàn tất — dữ liệu đợt K99 sẽ được dọn khi script kết thúc (trap)"
