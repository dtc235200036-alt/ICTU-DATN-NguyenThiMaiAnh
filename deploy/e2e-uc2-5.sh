#!/usr/bin/env bash
# UC2-5: kịch bản demo chain "outline -> tiến độ -> bảo vệ -> lưu kho" qua
# Apache HTTPS (D-09). Plan này (03-01) chỉ dựng khung dùng chung (helpers,
# setup_assigned_topic, cleanup) + section UC2 (đề cương). Các plan sau bổ
# sung uc3_progress/uc4_defense/uc5_archive — mỗi câu lệnh dọn dẹp có `|| true`
# để không lỗi khi bảng của phần đó chưa tồn tại/chưa có dữ liệu.
#
# Tài khoản dành riêng cho script này (không dùng chung với e2e-uc1.sh):
# GV025 (GV không liên quan), GV026/GV027/GV028 (hội đồng, plan 03-03),
# GV029 (GVHD), DTC225200097 (SV khác), DTC225200098 (SV chính). Đợt kiểm thử
# dùng khoa K98 (e2e-uc1.sh dùng K99).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${BASE_URL:-https://localhost}"

fail() {
  echo "FAIL: $1"
  exit 1
}

ok() {
  echo "OK: $1"
}

TMP="$(mktemp -d)"
START_UTC="$(date -u +%Y-%m-%dT%H:%M:%S)"
DOT_DO_AN_ID=""
HOI_DONG_IDS=""

# call METHOD PATH TOKEN [curl args...] — thân trả về ghi vào $TMP/body, in
# ra mã HTTP.
call() {
  local method="$1" path="$2" token="$3"
  shift 3
  curl -sk -o "$TMP/body" -w '%{http_code}' -X "$method" "$BASE$path" \
    -H "Authorization: Bearer ${token}" "$@"
}

# jget PYEXPR — parse $TMP/body làm JSON vào biến `d`, in ra PYEXPR.
jget() {
  python3 -c "
import json
d = json.load(open('$TMP/body'))
print($1)
" 2>/dev/null
}

cleanup() {
  if [ -n "${DOT_DO_AN_ID}" ]; then
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM thong_bao WHERE tai_khoan_id IN (SELECT id FROM tai_khoan WHERE ma_dang_nhap IN ('GV025','GV026','GV027','GV028','GV029','DTC225200097','DTC225200098')) AND thoi_diem >= '${START_UTC}';" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM diem_bao_ve WHERE lich_bao_ve_id IN (SELECT id FROM lich_bao_ve WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}));" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM lich_bao_ve WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" >/dev/null 2>&1 || true
    if [ -n "${HOI_DONG_IDS}" ]; then
      DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
        "DELETE FROM thanh_vien_hoi_dong WHERE hoi_dong_id IN (${HOI_DONG_IDS});" >/dev/null 2>&1 || true
      DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
        "DELETE FROM hoi_dong WHERE id IN (${HOI_DONG_IDS});" >/dev/null 2>&1 || true
    fi
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM do_an_kho WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}) OR (khoa='K98' AND nguon='IMPORT');" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM bao_cao_tien_do WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM moc_tien_do WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM luot_duyet_de_cuong WHERE de_cuong_id IN (SELECT id FROM de_cuong WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}));" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM chi_tiet_trung_lap WHERE ket_qua_id IN (SELECT id FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}));" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" >/dev/null 2>&1 || true

    # Xóa file vật lý trước khi xóa hàng tai_lieu_do_an (cần ten_luu_tru).
    TEN_LUU_TRU_LIST="$(DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "SELECT ten_luu_tru FROM tai_lieu_do_an WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" 2>/dev/null || true)"
    if [ -n "${TEN_LUU_TRU_LIST}" ]; then
      while IFS= read -r ten; do
        [ -z "$ten" ] && continue
        docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api rm -f "/data/uploads/${ten}" >/dev/null 2>&1 || true
      done <<<"${TEN_LUU_TRU_LIST}"
    fi
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM tai_lieu_do_an WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM de_cuong WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "DELETE FROM dot_do_an WHERE id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT

TOKEN_BOMON=""
TOKEN_GV025=""
TOKEN_GV029=""
TOKEN_SV097=""
TOKEN_SV098=""
DE_TAI_ID=""

setup_assigned_topic() {
  TOKEN_BOMON="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
  TOKEN_GV025="$(bash "${SCRIPT_DIR}/api-login.sh" GV025)"
  TOKEN_GV029="$(bash "${SCRIPT_DIR}/api-login.sh" GV029)"
  TOKEN_SV097="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200097)"
  TOKEN_SV098="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200098)"

  local status has_active
  status="$(call GET /api/dashboard/sinh-vien "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "Không lấy được dashboard SV DTC225200098 (mã ${status})"
  has_active="$(jget "1 if d.get('de_tai') else 0")"
  [ "$has_active" = "0" ] || fail "DTC225200098 đã có đề tài đang hoạt động — dọn dữ liệu cũ rồi chạy lại"

  status="$(call POST /api/cohorts "${TOKEN_BOMON}" -H 'Content-Type: application/json' \
    -d '{"ten_dot":"Đợt kiểm thử tự động UC2-5","khoa":"K98","nam_hoc":"2026-2027","ngay_bat_dau":"2026-01-01"}')"
  [ "$status" = "201" ] || fail "Không tạo được đợt kiểm thử K98 (mã ${status}, $(cat "$TMP/body"))"
  DOT_DO_AN_ID="$(jget "d['id']")"
  [ -n "$DOT_DO_AN_ID" ] || fail "Không đọc được id đợt K98 vừa tạo"
  ok "Bộ môn tạo đợt kiểm thử K98 (id=${DOT_DO_AN_ID})"

  status="$(call POST /api/topics "${TOKEN_SV098}" -H 'Content-Type: application/json' \
    -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_de_tai\":\"E2E UC2-5 - Đề tài tự đề xuất\",\"linh_vuc\":\"Hệ thống thông tin\",\"gui\":true}")"
  [ "$status" = "201" ] || fail "DTC225200098 không tự đề xuất được đề tài (mã ${status}, $(cat "$TMP/body"))"
  DE_TAI_ID="$(jget "d['id']")"
  [ -n "$DE_TAI_ID" ] || fail "Không đọc được id đề tài vừa tự đề xuất"
  ok "DTC225200098 tự đề xuất đề tài (id=${DE_TAI_ID})"

  local lecturers_body gv029_id
  lecturers_body="$(curl -sk "$BASE/api/lecturers" -H "Authorization: Bearer ${TOKEN_BOMON}")"
  gv029_id="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV029"), ""))' 2>/dev/null)"
  [ -n "$gv029_id" ] || fail "Không tìm được id GV029 trong /api/lecturers"

  status="$(call POST "/api/topic-approvals/${DE_TAI_ID}/approve" "${TOKEN_BOMON}" \
    -H 'Content-Type: application/json' -d "{\"giang_vien_id\":${gv029_id}}")"
  [ "$status" = "200" ] || fail "Bộ môn không phân công GVHD được cho đề tài (mã ${status}, $(cat "$TMP/body"))"
  local trang_thai
  trang_thai="$(jget "d.get('trang_thai','')")"
  [ "$trang_thai" = "DA_PHAN_CONG" ] || fail "Đề tài không chuyển Đã phân công (nhận ${trang_thai})"
  ok "Bộ môn phân công GV029 làm GVHD cho đề tài -> Đã phân công"
}

uc2_outline() {
  local docx_path="$TMP/de-cuong-v1.docx"
  uv --directory "${SCRIPT_DIR}/../backend" run python - "$docx_path" <<'PYEOF'
import sys
from docx import Document

path = sys.argv[1]
doc = Document()
doc.add_paragraph(
    "Đề cương này trình bày hệ thống quản lý đồ án sinh viên khoa Công nghệ "
    "thông tin, tập trung vào quy trình đăng ký đề tài và nộp đề cương trực "
    "tuyến cho sinh viên và giảng viên hướng dẫn."
)
doc.add_paragraph(
    "Chương một mô tả cơ sở lý thuyết về kiến trúc hướng dịch vụ, các thành "
    "phần Web API, ứng dụng khách và dịch vụ trí tuệ nhân tạo kiểm tra trùng "
    "lặp nội dung tài liệu nộp lên hệ thống."
)
doc.add_paragraph(
    "Chương hai khảo sát quy trình nghiệp vụ thực tế tại bộ môn, xác định các "
    "yêu cầu chức năng và phi chức năng, cùng các trường hợp sử dụng chính "
    "của toàn bộ hệ thống quản lý đồ án tốt nghiệp."
)
doc.save(path)
PYEOF
  [ -s "$docx_path" ] || fail "Không sinh được file DOCX kiểm thử"

  local status doc_id trang attempt
  status="$(call POST "/api/outlines/${DE_TAI_ID}/submit" "${TOKEN_SV098}" \
    -F "file=@${docx_path};type=application/vnd.openxmlformats-officedocument.wordprocessingml.document")"
  [ "$status" = "202" ] || fail "Nộp đề cương v1 không trả 202 (mã ${status}, $(cat "$TMP/body"))"
  doc_id="$(jget "d['phien_ban'][0]['tai_lieu']['id']")"
  [ -n "$doc_id" ] || fail "Không đọc được id tài liệu v1 vừa nộp"
  ok "DTC225200098 nộp đề cương v1 -> 202 (tai_lieu_do_an_id=${doc_id})"

  trang=""
  for attempt in $(seq 1 20); do
    status="$(call GET "/api/documents/${doc_id}/check" "${TOKEN_SV098}")"
    [ "$status" = "200" ] || fail "GET check tài liệu v1 lỗi (mã ${status})"
    trang="$(jget "d.get('trang_thai','')")"
    [ "$trang" != "DANG_KIEM_TRA" ] && break
    sleep 0.5
  done
  [ "$trang" = "HOAN_TAT" ] || fail "Kiểm tra trùng lặp không đạt Hoàn tất sau khi chờ (trạng thái cuối: ${trang})"
  ok "Kiểm tra trùng lặp tài liệu v1 hoàn tất (HOAN_TAT)"

  status="$(call GET "/api/outlines?dot_do_an_id=${DOT_DO_AN_ID}" "${TOKEN_GV029}")"
  [ "$status" = "200" ] || fail "GV029 không lấy được danh sách đề cương (mã ${status})"
  local has_topic
  has_topic="$(jget "1 if any(i['de_tai_id'] == ${DE_TAI_ID} and i['trang_thai'] == 'CHO_DUYET' for i in d['items']) else 0")"
  [ "$has_topic" = "1" ] || fail "Danh sách đề cương của GV029 không có đề tài kiểm thử ở Chờ duyệt"
  ok "GV029 thấy đề tài trong danh sách đề cương (Chờ duyệt)"

  status="$(call GET "/api/outlines/${DE_TAI_ID}" "${TOKEN_GV029}")"
  [ "$status" = "200" ] || fail "GV029 không xem được chi tiết đề cương (mã ${status})"
  local tom_tat_len kiem_tra_trang
  tom_tat_len="$(jget "len((d['phien_ban'][0]['tai_lieu'].get('tom_tat') or ''))")"
  [ "${tom_tat_len:-0}" -gt 0 ] || fail "Tóm tắt trích xuất rỗng (D-03)"
  kiem_tra_trang="$(jget "d['phien_ban'][0]['kiem_tra']['trang_thai']")"
  [ "$kiem_tra_trang" = "HOAN_TAT" ] || fail "GV029 không thấy kiểm tra Hoàn tất (nhận ${kiem_tra_trang})"
  ok "GV029 thấy tóm tắt trích xuất (D-03) + kiểm tra Hoàn tất trên màn duyệt"

  status="$(call POST "/api/outlines/${DE_TAI_ID}/review" "${TOKEN_GV029}" \
    -H 'Content-Type: application/json' \
    -d "{\"tai_lieu_do_an_id\":${doc_id},\"ket_qua\":\"DA_DUYET\"}")"
  [ "$status" = "200" ] || fail "GV029 duyệt đề cương không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  trang="$(jget "d.get('trang_thai','')")"
  [ "$trang" = "DA_DUYET" ] || fail "Đề cương không chuyển Đã duyệt (nhận ${trang})"
  ok "GV029 duyệt đề cương -> Đã duyệt"

  status="$(call GET /api/notifications "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không lấy được thông báo (mã ${status})"
  local has_notification
  has_notification="$(jget "1 if any(i['loai'] == 'DE_CUONG_DUYET' for i in d['items']) else 0")"
  [ "$has_notification" = "1" ] || fail "DTC225200098 không có thông báo Đề cương được duyệt"
  ok "DTC225200098 có thông báo Đề cương được duyệt (NOTF-01)"

  if docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T apache test -e /data/uploads 2>/dev/null; then
    fail "/data/uploads có thể truy cập được từ container apache (vi phạm D-02)"
  fi
  ok "/data/uploads không tồn tại/không lộ trong container apache (D-02)"
}

setup_assigned_topic
uc2_outline

echo "OK: e2e UC2 hoàn tất — dữ liệu đợt K98 sẽ được dọn khi script kết thúc (trap)"
