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
# IN-09 (03-REVIEW): chỉ dọn bản ghi kho IMPORT K98 do CHÍNH lần chạy này tạo
# (id lớn hơn id lớn nhất lúc bắt đầu) — không xóa dữ liệu K98 có sẵn.
KHO_MAX_ID_START="$(DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" "SELECT COALESCE(MAX(id), 0) FROM do_an_kho;" 2>/dev/null || echo "")"
case "${KHO_MAX_ID_START}" in
  ''|*[!0-9]*) echo "FAIL: không đọc được MAX(do_an_kho.id) trước khi chạy"; exit 1 ;;
esac
DOT_DO_AN_ID=""
HOI_DONG_IDS=""
# Bản ghi kho do script tự xóa qua API (UC5.3) — vẫn phải purge khỏi chỉ mục AI
# khi dọn dẹp vì xóa kho chưa gỡ vector (giới hạn đã ghi nhận, 04-05).
DELETED_KHO_IDS=""

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
    # Phase 4 (04-05): gỡ vector đề tài K98 (TOPIC) và bản ghi kho K98/của các
    # đề tài đó (ARCHIVE) khỏi chỉ mục AI TRƯỚC khi xóa hàng — chạy lại test
    # không để lại vector mồ côi (chỉ có tác dụng khi AI_CLIENT=http).
    local purge_topic_ids purge_kho_ids
    purge_topic_ids="$(DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" 2>/dev/null | paste -sd, - || true)"
    purge_kho_ids="$(DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "SELECT id FROM do_an_kho WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}) OR (khoa='K98' AND nguon='IMPORT' AND id > ${KHO_MAX_ID_START});" 2>/dev/null | paste -sd, - || true)"
    purge_kho_ids="$(printf '%s,%s' "${purge_kho_ids}" "${DELETED_KHO_IDS}" | tr ',' '\n' | grep -E '^[0-9]+$' | sort -un | paste -sd, - || true)"
    if [ -n "${purge_topic_ids}" ]; then
      docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api \
        python -m app.services.ai_index purge --loai TOPIC --ids "${purge_topic_ids}" >/dev/null 2>&1 || true
    fi
    if [ -n "${purge_kho_ids}" ]; then
      docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api \
        python -m app.services.ai_index purge --loai ARCHIVE --ids "${purge_kho_ids}" >/dev/null 2>&1 || true
    fi
    # 04-06: đề cương/báo cáo cuối đã kiểm tra xong được ingest DOCUMENT — gỡ luôn.
    local purge_doc_ids
    purge_doc_ids="$(DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" \
      "SELECT id FROM tai_lieu_do_an WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID});" 2>/dev/null | paste -sd, - || true)"
    if [ -n "${purge_doc_ids}" ]; then
      docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api \
        python -m app.services.ai_index purge --loai DOCUMENT --ids "${purge_doc_ids}" >/dev/null 2>&1 || true
    fi
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
      "DELETE FROM do_an_kho WHERE de_tai_id IN (SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}) OR (khoa='K98' AND nguon='IMPORT' AND id > ${KHO_MAX_ID_START});" >/dev/null 2>&1 || true
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
        docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T api rm -f "/data/uploads/${ten}" </dev/null >/dev/null 2>&1 || true
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
TOKEN_GV026=""
TOKEN_GV027=""
TOKEN_GV028=""
TOKEN_GV029=""
TOKEN_SV097=""
TOKEN_SV098=""
DE_TAI_ID=""
# uc4_defense (plan 03-04) đặt; uc5_archive (plan 03-05) dùng lại.
LICH_BAO_VE_ID=""
DO_AN_KHO_ID=""

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

  # GV029 yêu cầu sửa v1 kèm nhận xét (UC2.2 A1)
  status="$(call POST "/api/outlines/${DE_TAI_ID}/review" "${TOKEN_GV029}" \
    -H 'Content-Type: application/json' \
    -d "{\"tai_lieu_do_an_id\":${doc_id},\"ket_qua\":\"YEU_CAU_SUA\",\"nhan_xet\":\"Vui lòng bổ sung mục tiêu cụ thể hơn\"}")"
  [ "$status" = "200" ] || fail "GV029 yêu cầu sửa không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  trang="$(jget "d.get('trang_thai','')")"
  [ "$trang" = "YEU_CAU_SUA" ] || fail "Đề cương không chuyển Yêu cầu sửa (nhận ${trang})"
  ok "GV029 yêu cầu sửa đề cương kèm nhận xét -> Yêu cầu sửa"

  status="$(call GET /api/notifications "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không lấy được thông báo (mã ${status})"
  local has_yeu_cau_sua_notif
  has_yeu_cau_sua_notif="$(jget "1 if any(i['loai'] == 'DE_CUONG_YEU_CAU_SUA' for i in d['items']) else 0")"
  [ "$has_yeu_cau_sua_notif" = "1" ] || fail "DTC225200098 không có thông báo Yêu cầu sửa đề cương"
  ok "DTC225200098 có thông báo Yêu cầu sửa đề cương (NOTF-01)"

  # DTC225200098 nộp lại phiên bản 2 dạng PDF
  local pdf_path="$TMP/de-cuong-v2.pdf"
  uv --directory "${SCRIPT_DIR}/../backend" run python - "$pdf_path" <<'PYEOF'
import sys
import pymupdf

path = sys.argv[1]
doc = pymupdf.open()
page = doc.new_page()
page.insert_text((72, 72), "Outline version 2 - revised after GVHD feedback")
page.insert_text((72, 96), "This paragraph adds more detail about the research scope and methodology")
doc.save(path)
doc.close()
PYEOF
  [ -s "$pdf_path" ] || fail "Không sinh được file PDF kiểm thử"

  local doc_id_v2
  status="$(call POST "/api/outlines/${DE_TAI_ID}/submit" "${TOKEN_SV098}" \
    -F "file=@${pdf_path};type=application/pdf")"
  [ "$status" = "202" ] || fail "Nộp đề cương v2 (PDF) không trả 202 (mã ${status}, $(cat "$TMP/body"))"
  doc_id_v2="$(jget "d['phien_ban'][0]['tai_lieu']['id']")"
  [ -n "$doc_id_v2" ] || fail "Không đọc được id tài liệu v2 vừa nộp"
  ok "DTC225200098 nộp đề cương v2 (PDF) -> 202 (tai_lieu_do_an_id=${doc_id_v2})"

  trang=""
  for attempt in $(seq 1 20); do
    status="$(call GET "/api/documents/${doc_id_v2}/check" "${TOKEN_SV098}")"
    [ "$status" = "200" ] || fail "GET check tài liệu v2 lỗi (mã ${status})"
    trang="$(jget "d.get('trang_thai','')")"
    [ "$trang" != "DANG_KIEM_TRA" ] && break
    sleep 0.5
  done
  [ "$trang" = "HOAN_TAT" ] || fail "Kiểm tra trùng lặp v2 không đạt Hoàn tất (trạng thái cuối: ${trang})"
  ok "Kiểm tra trùng lặp tài liệu v2 hoàn tất (HOAN_TAT)"

  status="$(call POST "/api/outlines/${DE_TAI_ID}/review" "${TOKEN_GV029}" \
    -H 'Content-Type: application/json' \
    -d "{\"tai_lieu_do_an_id\":${doc_id_v2},\"ket_qua\":\"DA_DUYET\"}")"
  [ "$status" = "200" ] || fail "GV029 duyệt đề cương v2 không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  trang="$(jget "d.get('trang_thai','')")"
  [ "$trang" = "DA_DUYET" ] || fail "Đề cương không chuyển Đã duyệt (nhận ${trang})"
  ok "GV029 duyệt đề cương v2 -> Đã duyệt"

  status="$(call GET /api/notifications "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không lấy được thông báo (mã ${status})"
  local has_notification
  has_notification="$(jget "1 if any(i['loai'] == 'DE_CUONG_DUYET' for i in d['items']) else 0")"
  [ "$has_notification" = "1" ] || fail "DTC225200098 không có thông báo Đề cương được duyệt"
  ok "DTC225200098 có thông báo Đề cương được duyệt (NOTF-01)"

  # ZIP đổi tên .docx -> 422 (kiểm tra theo nội dung nhị phân, không theo đuôi file)
  local fake_docx="$TMP/fake.docx"
  python3 -c "
import zipfile
with zipfile.ZipFile('$fake_docx', 'w') as zf:
    zf.writestr('not-a-document.txt', 'hello')
"
  status="$(call POST "/api/outlines/${DE_TAI_ID}/submit" "${TOKEN_SV098}" \
    -F "file=@${fake_docx};type=application/vnd.openxmlformats-officedocument.wordprocessingml.document")"
  [ "$status" = "422" ] || fail "ZIP đổi tên .docx không bị từ chối 422 (mã ${status})"
  ok "ZIP đổi tên .docx bị từ chối 422 (kiểm tra theo nội dung nhị phân)"

  # DTC225200097 (SV khác) -> 403
  status="$(call GET "/api/outlines/${DE_TAI_ID}" "${TOKEN_SV097}")"
  [ "$status" = "403" ] || fail "DTC225200097 xem chi tiết đề cương không bị từ chối 403 (mã ${status})"
  status="$(call GET "/api/documents/${doc_id}/download" "${TOKEN_SV097}")"
  [ "$status" = "403" ] || fail "DTC225200097 tải tài liệu không bị từ chối 403 (mã ${status})"
  ok "DTC225200097 (SV khác) bị từ chối 403 trên xem chi tiết + tải tài liệu"

  # GV025 (GV không liên quan) -> 403 khi duyệt
  status="$(call POST "/api/outlines/${DE_TAI_ID}/review" "${TOKEN_GV025}" \
    -H 'Content-Type: application/json' \
    -d "{\"tai_lieu_do_an_id\":${doc_id_v2},\"ket_qua\":\"DA_DUYET\"}")"
  [ "$status" = "403" ] || fail "GV025 duyệt đề cương không bị từ chối 403 (mã ${status})"
  ok "GV025 (GV không liên quan) bị từ chối 403 khi duyệt"

  # DTC225200098 tải lại v1 -> byte giống hệt file đã nộp
  local downloaded_path="$TMP/downloaded-v1"
  curl -sk -o "$downloaded_path" -X GET "$BASE/api/documents/${doc_id}/download" \
    -H "Authorization: Bearer ${TOKEN_SV098}"
  local original_sha downloaded_sha
  original_sha="$(sha256sum "$docx_path" | awk '{print $1}')"
  downloaded_sha="$(sha256sum "$downloaded_path" | awk '{print $1}')"
  [ "$original_sha" = "$downloaded_sha" ] || fail "Bytes tải về của v1 không khớp file đã nộp"
  ok "DTC225200098 tải lại v1 -> bytes khớp sha256 với file gốc"

  if docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T apache test -e /data/uploads 2>/dev/null; then
    fail "/data/uploads có thể truy cập được từ container apache (vi phạm D-02)"
  fi
  ok "/data/uploads không tồn tại/không lộ trong container apache (D-02)"
}

uc3_progress() {
  # UC3.1-UC3.4 (plan 03-06): mốc do Bộ môn đặt, SV nộp theo mốc (tệp tùy
  # chọn), GVHD nhận xét + thông báo, dashboard toàn khoa với cờ trễ mốc.
  local yesterday next_week status m2
  yesterday="$(TZ=Asia/Ho_Chi_Minh date -d yesterday +%F)"
  next_week="$(TZ=Asia/Ho_Chi_Minh date -d '+7 days' +%F)"

  status="$(call POST /api/progress/milestones "${TOKEN_BOMON}" -H 'Content-Type: application/json' \
    -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_moc\":\"Mốc 1 (E2E)\",\"han_nop\":\"${yesterday}\"}")"
  [ "$status" = "201" ] || fail "Bộ môn không tạo được Mốc 1 (mã ${status}, $(cat "$TMP/body"))"
  status="$(call POST /api/progress/milestones "${TOKEN_BOMON}" -H 'Content-Type: application/json' \
    -d "{\"dot_do_an_id\":${DOT_DO_AN_ID},\"ten_moc\":\"Mốc 2 (E2E)\",\"han_nop\":\"${next_week}\"}")"
  [ "$status" = "201" ] || fail "Bộ môn không tạo được Mốc 2 (mã ${status}, $(cat "$TMP/body"))"
  m2="$(jget "d['id']")"
  ok "Bộ môn thiết lập 2 mốc tiến độ cho đợt K98 (hạn ${yesterday} và ${next_week})"

  local pdf_path="$TMP/tien-do-moc-2.pdf"
  uv --directory "${SCRIPT_DIR}/../backend" run python - "$pdf_path" <<'PYEOF'
import sys
import pymupdf

doc = pymupdf.open()
page = doc.new_page()
page.insert_text((72, 72), "Progress report for milestone 2 - end-to-end test")
doc.save(sys.argv[1])
doc.close()
PYEOF
  [ -s "$pdf_path" ] || fail "Không sinh được file PDF báo cáo tiến độ kiểm thử"

  status="$(call POST "/api/progress/reports/${m2}" "${TOKEN_SV098}" \
    -F "noi_dung=Đã hoàn thành thiết kế CSDL và API (E2E)" -F "file=@${pdf_path};type=application/pdf")"
  [ "$status" = "200" ] || fail "DTC225200098 không nộp được báo cáo Mốc 2 (mã ${status}, $(cat "$TMP/body"))"
  ok "DTC225200098 nộp báo cáo Mốc 2 kèm PDF"

  status="$(call GET /api/progress/me "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "GET /api/progress/me lỗi (mã ${status})"
  local states
  states="$(jget "'|'.join(m['trang_thai'] + ':' + ('file' if (m['bao_cao'] or {}).get('tep') else '-') for m in d['de_tai']['moc'])")"
  [ "$states" = "TRE_MOC:-|DUNG_HAN:file" ] || fail "Trạng thái mốc sai (nhận '${states}', mong đợi 'TRE_MOC:-|DUNG_HAN:file')"
  ok "SV thấy Mốc 1 Trễ mốc, Mốc 2 Đúng hạn có tệp đính kèm (D-05)"

  status="$(call GET /api/progress/students "${TOKEN_GV029}")"
  [ "$status" = "200" ] || fail "GV029 không lấy được danh sách SV (mã ${status})"
  local cho
  cho="$(jget "next((str(i['so_cho_nhan_xet']) + '|' + str(i['tre_moc']) for i in d if i['de_tai_id'] == ${DE_TAI_ID}), '')")"
  [ "$cho" = "1|True" ] || fail "GV029 không thấy SV với 1 báo cáo chờ nhận xét + trễ mốc (nhận '${cho}')"
  ok "GV029 thấy DTC225200098: 1 báo cáo chờ nhận xét, cờ trễ mốc"

  local bao_cao_id
  status="$(call GET "/api/progress/topics/${DE_TAI_ID}" "${TOKEN_GV029}")"
  [ "$status" = "200" ] || fail "GV029 không xem được tiến độ đề tài (mã ${status})"
  bao_cao_id="$(jget "next(m['bao_cao']['id'] for m in d['moc'] if m['id'] == ${m2})")"
  [ -n "$bao_cao_id" ] || fail "Không đọc được id báo cáo Mốc 2"

  status="$(call POST "/api/progress/reports/${bao_cao_id}/review" "${TOKEN_GV025}" \
    -H 'Content-Type: application/json' -d '{"nhan_xet":"Không phải GVHD","danh_gia":"DAT"}')"
  [ "$status" = "403" ] || fail "GV025 (không phải GVHD) nhận xét không bị từ chối 403 (mã ${status})"
  ok "GV025 (không phải GVHD) bị từ chối 403 khi nhận xét"

  status="$(call POST "/api/progress/reports/${bao_cao_id}/review" "${TOKEN_GV029}" \
    -H 'Content-Type: application/json' -d '{"nhan_xet":"Đúng kế hoạch, tiếp tục (E2E)","danh_gia":"DAT"}')"
  [ "$status" = "200" ] || fail "GV029 nhận xét không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  ok "GV029 nhận xét Mốc 2: Đạt"

  status="$(call GET /api/notifications "${TOKEN_SV098}")"
  [ "$(jget "1 if any(i['loai'] == 'TIEN_DO_NHAN_XET' for i in d['items']) else 0")" = "1" ] \
    || fail "DTC225200098 không có thông báo TIEN_DO_NHAN_XET"
  ok "DTC225200098 có thông báo nhận xét tiến độ (NOTF-01)"

  status="$(call POST "/api/progress/reports/${m2}" "${TOKEN_SV098}" -F "noi_dung=Nộp lại sau nhận xét")"
  [ "$status" = "409" ] || fail "Nộp lại sau khi GVHD nhận xét không bị từ chối 409 (mã ${status})"
  ok "Nộp lại Mốc 2 sau khi GVHD nhận xét bị từ chối 409"

  status="$(call GET "/api/progress/dashboard?dot_do_an_id=${DOT_DO_AN_ID}&chi_tre_moc=true" "${TOKEN_BOMON}")"
  [ "$status" = "200" ] || fail "Bộ môn không xem được tiến độ toàn khoa (mã ${status})"
  local flagged
  flagged="$(jget "str(any(r['de_tai']['id'] == ${DE_TAI_ID} and r['tre_moc'] for r in d['items'])) + '|' + str(d['so_sv_tre_moc'])")"
  [ "$flagged" = "True|1" ] || fail "Dashboard toàn khoa không đánh dấu SV trễ mốc (nhận '${flagged}')"
  ok "Bộ môn thấy DTC225200098 bị đánh dấu Trễ mốc trên tiến độ toàn khoa"

  status="$(call GET /api/progress/dashboard "${TOKEN_SV097}")"
  [ "$status" = "403" ] || fail "DTC225200097 xem tiến độ toàn khoa không bị từ chối 403 (mã ${status})"
  ok "DTC225200097 bị từ chối 403 trên tiến độ toàn khoa"
}

uc4_defense() {
  local pdf_path="$TMP/bao-cao-cuoi.pdf"
  uv --directory "${SCRIPT_DIR}/../backend" run python - "$pdf_path" <<'PYEOF'
import sys
import pymupdf

path = sys.argv[1]
doc = pymupdf.open()
page = doc.new_page()
page.insert_text((72, 72), "Final report end-to-end test content for defense flow")
page.insert_text((72, 96), "Second line describing methodology and results summary")
doc.save(path)
doc.close()
PYEOF
  [ -s "$pdf_path" ] || fail "Không sinh được file PDF báo cáo cuối kiểm thử"

  TOKEN_GV026="$(bash "${SCRIPT_DIR}/api-login.sh" GV026)"
  TOKEN_GV027="$(bash "${SCRIPT_DIR}/api-login.sh" GV027)"
  TOKEN_GV028="$(bash "${SCRIPT_DIR}/api-login.sh" GV028)"

  local lecturers_body
  lecturers_body="$(curl -sk "$BASE/api/lecturers" -H "Authorization: Bearer ${TOKEN_BOMON}")"
  local gv025_id gv026_id gv027_id gv028_id gv029_id
  gv025_id="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV025"), ""))' 2>/dev/null)"
  gv026_id="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV026"), ""))' 2>/dev/null)"
  gv027_id="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV027"), ""))' 2>/dev/null)"
  gv028_id="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV028"), ""))' 2>/dev/null)"
  gv029_id="$(printf '%s' "$lecturers_body" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(next((gv["id"] for gv in d if gv.get("ma_giang_vien") == "GV029"), ""))' 2>/dev/null)"
  [ -n "$gv025_id" ] && [ -n "$gv026_id" ] && [ -n "$gv027_id" ] && [ -n "$gv028_id" ] && [ -n "$gv029_id" ] \
    || fail "Không tìm đủ id GV025/026/027/028/029 trong /api/lecturers"

  local status
  status="$(call POST "/api/defense/final-reports/${DE_TAI_ID}" "${TOKEN_SV098}" \
    -F "file=@${pdf_path};type=application/pdf")"
  [ "$status" = "202" ] || fail "Nộp báo cáo cuối không trả 202 (mã ${status}, $(cat "$TMP/body"))"
  local report_doc_id
  report_doc_id="$(jget "d['phien_ban'][0]['tai_lieu']['id']")"
  [ -n "$report_doc_id" ] || fail "Không đọc được id báo cáo cuối vừa nộp"
  ok "DTC225200098 nộp báo cáo cuối -> 202 (tai_lieu_do_an_id=${report_doc_id})"

  local trang attempt
  trang=""
  for attempt in $(seq 1 20); do
    status="$(call GET "/api/documents/${report_doc_id}/check" "${TOKEN_SV098}")"
    [ "$status" = "200" ] || fail "GET check báo cáo cuối lỗi (mã ${status})"
    trang="$(jget "d.get('trang_thai','')")"
    [ "$trang" != "DANG_KIEM_TRA" ] && break
    sleep 0.5
  done
  [ "$trang" = "HOAN_TAT" ] || fail "Kiểm tra trùng lặp báo cáo cuối không đạt Hoàn tất (trạng thái cuối: ${trang})"
  ok "Kiểm tra trùng lặp báo cáo cuối hoàn tất (HOAN_TAT)"

  status="$(call GET "/api/defense/final-reports/${DE_TAI_ID}" "${TOKEN_GV029}")"
  [ "$status" = "200" ] || fail "GV029 (GVHD) không xem được báo cáo cuối (mã ${status})"
  ok "GV029 (GVHD) xem được báo cáo cuối -> 200"

  status="$(call GET "/api/defense/final-reports/${DE_TAI_ID}" "${TOKEN_SV097}")"
  [ "$status" = "403" ] || fail "DTC225200097 xem báo cáo cuối không bị từ chối 403 (mã ${status})"
  ok "DTC225200097 (SV khác) bị từ chối 403 trên xem báo cáo cuối"

  status="$(call GET /api/defense/eligible-students "${TOKEN_BOMON}")"
  [ "$status" = "200" ] || fail "Bộ môn không lấy được danh sách SV đủ điều kiện bảo vệ (mã ${status})"
  local has_eligible
  has_eligible="$(jget "1 if any(i['de_tai_id'] == ${DE_TAI_ID} for i in d) else 0")"
  [ "$has_eligible" = "1" ] || fail "Danh sách SV đủ điều kiện bảo vệ không có đề tài kiểm thử"
  ok "Bộ môn thấy đề tài trong danh sách SV đủ điều kiện bảo vệ"

  local today
  today="$(TZ=Asia/Ho_Chi_Minh date +%F)"

  status="$(call POST /api/defense/committees "${TOKEN_BOMON}" -H 'Content-Type: application/json' \
    -d "{\"ten_hoi_dong\":\"Hội đồng E2E K98\",\"ngay_bao_ve\":\"${today}\",\"gio_bao_ve\":\"08:00\",\"phong\":\"E2E-302\",\"thanh_vien\":[{\"giang_vien_id\":${gv026_id},\"vai_tro\":\"CHU_TICH\"},{\"giang_vien_id\":${gv027_id},\"vai_tro\":\"THU_KY\"},{\"giang_vien_id\":${gv028_id},\"vai_tro\":\"UY_VIEN\"}]}")"
  [ "$status" = "201" ] || fail "Bộ môn tạo hội đồng A không trả 201 (mã ${status}, $(cat "$TMP/body"))"
  local hoi_dong_a_id
  hoi_dong_a_id="$(jget "d['id']")"
  [ -n "$hoi_dong_a_id" ] || fail "Không đọc được id hội đồng A vừa tạo"
  HOI_DONG_IDS="${HOI_DONG_IDS:+$HOI_DONG_IDS,}${hoi_dong_a_id}"
  ok "Bộ môn tạo hội đồng A (GV026/027/028) -> 201 (id=${hoi_dong_a_id})"

  status="$(call POST /api/defense/committees "${TOKEN_BOMON}" -H 'Content-Type: application/json' \
    -d "{\"ten_hoi_dong\":\"Hội đồng E2E K98 - B\",\"ngay_bao_ve\":\"${today}\",\"gio_bao_ve\":\"09:00\",\"phong\":\"E2E-303\",\"thanh_vien\":[{\"giang_vien_id\":${gv029_id},\"vai_tro\":\"CHU_TICH\"},{\"giang_vien_id\":${gv025_id},\"vai_tro\":\"UY_VIEN\"},{\"giang_vien_id\":${gv027_id},\"vai_tro\":\"UY_VIEN\"}]}")"
  [ "$status" = "201" ] || fail "Bộ môn tạo hội đồng B không trả 201 (mã ${status}, $(cat "$TMP/body"))"
  local hoi_dong_b_id
  hoi_dong_b_id="$(jget "d['id']")"
  [ -n "$hoi_dong_b_id" ] || fail "Không đọc được id hội đồng B vừa tạo"
  HOI_DONG_IDS="${HOI_DONG_IDS:+$HOI_DONG_IDS,}${hoi_dong_b_id}"
  ok "Bộ môn tạo hội đồng B (chứa GVHD GV029) -> 201 (id=${hoi_dong_b_id})"

  status="$(call POST "/api/defense/committees/${hoi_dong_b_id}/schedules" "${TOKEN_BOMON}" \
    -H 'Content-Type: application/json' -d "{\"de_tai_id\":${DE_TAI_ID}}")"
  [ "$status" = "409" ] || fail "Xếp lịch vào hội đồng chứa GVHD không bị từ chối 409 (mã ${status})"
  ok "Xếp lịch vào hội đồng B (chứa GVHD GV029) bị từ chối 409 (D-06)"

  status="$(call POST "/api/defense/committees/${hoi_dong_a_id}/schedules" "${TOKEN_BOMON}" \
    -H 'Content-Type: application/json' -d "{\"de_tai_id\":${DE_TAI_ID}}")"
  [ "$status" = "201" ] || fail "Xếp lịch vào hội đồng A không trả 201 (mã ${status}, $(cat "$TMP/body"))"
  ok "Bộ môn xếp lịch đề tài vào hội đồng A -> 201"

  status="$(call GET /api/notifications "${TOKEN_GV026}")"
  [ "$status" = "200" ] || fail "GV026 không lấy được thông báo (mã ${status})"
  local has_phan_cong
  has_phan_cong="$(jget "1 if any(i['loai'] == 'HOI_DONG_PHAN_CONG' for i in d['items']) else 0")"
  [ "$has_phan_cong" = "1" ] || fail "GV026 không có thông báo phân công hội đồng"
  ok "GV026 có thông báo phân công hội đồng (HOI_DONG_PHAN_CONG)"

  status="$(call GET /api/notifications "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không lấy được thông báo (mã ${status})"
  local has_lich_bao_ve
  has_lich_bao_ve="$(jget "1 if any(i['loai'] == 'LICH_BAO_VE' for i in d['items']) else 0")"
  [ "$has_lich_bao_ve" = "1" ] || fail "DTC225200098 không có thông báo lịch bảo vệ"
  ok "DTC225200098 có thông báo lịch bảo vệ (LICH_BAO_VE)"

  status="$(call POST /api/defense/committees "${TOKEN_SV098}" -H 'Content-Type: application/json' \
    -d "{\"ten_hoi_dong\":\"x\",\"ngay_bao_ve\":\"${today}\",\"gio_bao_ve\":\"08:00\",\"phong\":\"x\",\"thanh_vien\":[]}")"
  [ "$status" = "403" ] || fail "DTC225200098 tạo hội đồng không bị từ chối 403 (mã ${status})"
  ok "DTC225200098 (SV) bị từ chối 403 khi tạo hội đồng"

  status="$(call POST "/api/defense/final-reports/${DE_TAI_ID}" "${TOKEN_SV098}" \
    -F "file=@${pdf_path};type=application/pdf")"
  [ "$status" = "409" ] || fail "Nộp lại báo cáo cuối sau khi đã xếp lịch không bị từ chối 409 (mã ${status})"
  ok "DTC225200098 nộp lại báo cáo cuối sau khi đã xếp lịch bị từ chối 409"

  status="$(call DELETE "/api/defense/committees/${hoi_dong_b_id}" "${TOKEN_BOMON}")"
  [ "$status" = "204" ] || fail "Bộ môn xóa hội đồng B (chưa có SV) không trả 204 (mã ${status})"
  ok "Bộ môn xóa hội đồng B (chưa có SV) -> 204"

  # --- UC4.3–4.5 + UC5.2 (plan 03-04): chấm điểm, chốt, lưu kho ---
  status="$(call GET "/api/defense/committees/${hoi_dong_a_id}" "${TOKEN_BOMON}")"
  [ "$status" = "200" ] || fail "Bộ môn không đọc được hội đồng A (mã ${status})"
  LICH_BAO_VE_ID="$(jget "next(r['id'] for r in d['lich'] if r['de_tai_id'] == ${DE_TAI_ID})")"
  [ -n "$LICH_BAO_VE_ID" ] || fail "Không tìm được lich_bao_ve của đề tài trong hội đồng A"

  status="$(call GET "/api/defense/schedules/${LICH_BAO_VE_ID}" "${TOKEN_GV025}")"
  [ "$status" = "403" ] || fail "GV025 (ngoài hội đồng) xem lịch chấm điểm không bị từ chối 403 (mã ${status})"
  status="$(call GET "/api/documents/${report_doc_id}/download" "${TOKEN_GV025}")"
  [ "$status" = "403" ] || fail "GV025 (ngoài hội đồng) tải báo cáo cuối không bị từ chối 403 (mã ${status})"
  ok "GV025 (ngoài hội đồng) bị từ chối 403 trên lịch chấm điểm + tải báo cáo cuối (UC4.3 E1)"

  status="$(call GET /api/defense/my-committees "${TOKEN_GV026}")"
  [ "$status" = "200" ] || fail "GV026 không lấy được danh sách hội đồng của tôi (mã ${status})"
  local in_mine
  in_mine="$(jget "1 if any(r['id'] == ${LICH_BAO_VE_ID} for h in d for r in h['lich']) else 0")"
  [ "$in_mine" = "1" ] || fail "Hội đồng của GV026 không có SV đã xếp lịch"
  status="$(call GET "/api/documents/${report_doc_id}/download" "${TOKEN_GV026}")"
  [ "$status" = "200" ] || fail "GV026 (thành viên hội đồng) không tải được báo cáo cuối (mã ${status})"
  ok "GV026 thấy SV trong hội đồng của mình và tải được báo cáo cuối -> 200"

  status="$(call PUT "/api/defense/schedules/${LICH_BAO_VE_ID}/score" "${TOKEN_GV026}" \
    -H 'Content-Type: application/json' -d '{"diem":8.0,"nhan_xet":"Trình bày rõ ràng"}')"
  [ "$status" = "200" ] || fail "GV026 chấm 8.0 không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  status="$(call PUT "/api/defense/schedules/${LICH_BAO_VE_ID}/score" "${TOKEN_GV027}" \
    -H 'Content-Type: application/json' -d '{"diem":8.5,"nhan_xet":"Cần bổ sung phần so sánh"}')"
  [ "$status" = "200" ] || fail "GV027 chấm 8.5 không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  ok "GV026 chấm 8.0, GV027 chấm 8.5 (kèm nhận xét) -> 200"

  status="$(call POST "/api/defense/schedules/${LICH_BAO_VE_ID}/finalize" "${TOKEN_BOMON}")"
  [ "$status" = "409" ] || fail "Chốt khi mới 2/3 thành viên chấm không bị từ chối 409 (mã ${status})"
  ok "Bộ môn chốt khi mới 2/3 thành viên chấm -> 409 ($(jget "d['detail']"))"

  status="$(call PUT "/api/defense/schedules/${LICH_BAO_VE_ID}/score" "${TOKEN_GV028}" \
    -H 'Content-Type: application/json' -d '{"diem":9.0}')"
  [ "$status" = "200" ] || fail "GV028 chấm 9.0 không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  ok "GV028 chấm 9.0 -> 200"

  status="$(call POST "/api/defense/schedules/${LICH_BAO_VE_ID}/finalize" "${TOKEN_BOMON}")"
  [ "$status" = "200" ] || fail "Bộ môn chốt kết quả không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  local diem_tb
  diem_tb="$(jget "d['lich']['diem_trung_binh']")"
  [ "$diem_tb" = "8.5" ] || fail "Điểm trung bình sau chốt không phải 8.5 (nhận ${diem_tb})"
  DO_AN_KHO_ID="$(jget "d['do_an_kho_id']")"
  [ -n "$DO_AN_KHO_ID" ] || fail "Không đọc được do_an_kho_id sau khi chốt"
  ok "Bộ môn chốt kết quả -> 200, điểm TB 8.5, lưu kho (do_an_kho_id=${DO_AN_KHO_ID})"

  status="$(call GET /api/defense/me "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không lấy được lịch/kết quả bảo vệ (mã ${status})"
  diem_tb="$(jget "(d.get('ket_qua') or {}).get('diem_trung_binh')")"
  [ "$diem_tb" = "8.5" ] || fail "DTC225200098 không thấy điểm 8.5 sau chốt (nhận ${diem_tb})"
  status="$(call GET /api/notifications "${TOKEN_SV098}")"
  local has_ket_qua
  has_ket_qua="$(jget "1 if any(i['loai'] == 'KET_QUA_BAO_VE' for i in d['items']) else 0")"
  [ "$has_ket_qua" = "1" ] || fail "DTC225200098 không có thông báo kết quả bảo vệ"
  ok "DTC225200098 thấy điểm 8.5 + thông báo KET_QUA_BAO_VE (UC4.5, NOTF-01)"

  status="$(call PUT "/api/defense/schedules/${LICH_BAO_VE_ID}/score" "${TOKEN_GV026}" \
    -H 'Content-Type: application/json' -d '{"diem":9.5}')"
  [ "$status" = "409" ] || fail "GV026 sửa điểm sau chốt không bị từ chối 409 (mã ${status})"
  ok "GV026 sửa điểm sau chốt bị từ chối 409"

  local kho_row attempt
  kho_row=""
  for attempt in $(seq 1 20); do
    kho_row="$(bash "${SCRIPT_DIR}/sql.sh" "SELECT CONCAT(nguon,'|',trang_thai_index) FROM do_an_kho WHERE id=${DO_AN_KHO_ID} AND de_tai_id=${DE_TAI_ID}")"
    [ "$kho_row" = "HE_THONG|DA_INDEX" ] && break
    sleep 0.5
  done
  [ "$kho_row" = "HE_THONG|DA_INDEX" ] || fail "Bản ghi kho không ở HE_THONG|DA_INDEX (nhận ${kho_row})"
  ok "do_an_kho id=${DO_AN_KHO_ID}: nguồn HE_THONG, đã index (DA_INDEX)"
}

uc5_archive() {
  # --- UC5.1/5.3/5.4 (plan 03-05): tra cứu, tải báo cáo đã lưu kho, sửa +
  # index lại, import CSV khóa cũ (thành công một phần), RBAC ghi ---
  [ -n "$DO_AN_KHO_ID" ] || fail "uc5_archive cần DO_AN_KHO_ID từ uc4_defense"
  local status found
  status="$(call GET "/api/archive?khoa=K98" "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không tra cứu được kho (mã ${status})"
  found="$(jget "next((f\"{i['diem']}|{i['co_file']}\" for i in d['items'] if i['id'] == ${DO_AN_KHO_ID}), '')")"
  [ "$found" = "8.5|True" ] || fail "Kho K98 không có đồ án vừa chốt với điểm 8.5 + file (nhận '${found}')"
  ok "DTC225200098 tra cứu kho K98 thấy đồ án vừa chốt của mình (điểm 8.5, có file)"
  # WR-10 (03-REVIEW): sinh viên khác thấy đồ án + file nhưng không thấy điểm
  status="$(call GET "/api/archive?khoa=K98" "${TOKEN_SV097}")"
  [ "$status" = "200" ] || fail "DTC225200097 không tra cứu được kho (mã ${status})"
  found="$(jget "next((f\"{i['diem']}|{i['co_file']}\" for i in d['items'] if i['id'] == ${DO_AN_KHO_ID}), '')")"
  [ "$found" = "None|True" ] || fail "DTC225200097 (SV khác) phải thấy đồ án có file nhưng không thấy điểm (nhận '${found}')"
  ok "DTC225200097 tra cứu kho K98 thấy đồ án vừa chốt nhưng không thấy điểm của SV khác (WR-10)"

  local archived_path="$TMP/kho-bao-cao.pdf"
  status="$(curl -sk -o "$archived_path" -w '%{http_code}' "$BASE/api/archive/${DO_AN_KHO_ID}/file" \
    -H "Authorization: Bearer ${TOKEN_SV097}")"
  [ "$status" = "200" ] || fail "DTC225200097 không tải được báo cáo đã lưu kho (mã ${status})"
  [ "$(sha256sum "$archived_path" | awk '{print $1}')" = "$(sha256sum "$TMP/bao-cao-cuoi.pdf" | awk '{print $1}')" ] \
    || fail "Báo cáo tải từ kho không khớp sha256 với báo cáo cuối đã nộp"
  ok "DTC225200097 tải báo cáo cuối từ kho -> bytes khớp sha256 với file đã nộp"

  local put_body
  status="$(call GET "/api/archive/${DO_AN_KHO_ID}" "${TOKEN_BOMON}")"
  [ "$status" = "200" ] || fail "Bộ môn không đọc được chi tiết bản ghi kho (mã ${status})"
  put_body="$(jget "json.dumps({'khoa': d['khoa'], 'ten_de_tai': d['ten_de_tai'], 'ma_so_sinh_vien': d['sinh_vien']['ma'], 'ho_ten_sinh_vien': d['sinh_vien']['ho_ten'], 'giang_vien_id': (d['giang_vien'] or {}).get('id'), 'tu_khoa': 'kiểm thử, tự động', 'diem': d['diem']}, ensure_ascii=False)")"
  [ -n "$put_body" ] || fail "Không dựng được payload sửa bản ghi kho"
  status="$(call PUT "/api/archive/${DO_AN_KHO_ID}" "${TOKEN_BOMON}" -H 'Content-Type: application/json' -d "$put_body")"
  [ "$status" = "200" ] || fail "Bộ môn sửa từ khóa bản ghi kho không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  local idx attempt
  idx=""
  for attempt in $(seq 1 20); do
    call GET "/api/archive/${DO_AN_KHO_ID}" "${TOKEN_BOMON}" >/dev/null
    idx="$(jget "d['trang_thai_index'] + '|' + (d['tu_khoa'] or '')")"
    [ "$idx" = "DA_INDEX|kiểm thử, tự động" ] && break
    sleep 0.5
  done
  [ "$idx" = "DA_INDEX|kiểm thử, tự động" ] || fail "Bản ghi kho sau khi sửa không về DA_INDEX (nhận ${idx})"
  ok "Bộ môn sửa từ khóa 'kiểm thử, tự động' -> index lại nền -> DA_INDEX"

  local csv_path="$TMP/kho-khoa-cu.csv"
  cat >"$csv_path" <<'CSVEOF'
khoa,ten_de_tai,ma_so_sinh_vien,ho_ten_sinh_vien,ma_giang_vien,tu_khoa,diem
K98,E2E kho - Nhận diện biển số xe bằng học sâu,,Người Kiểm Thử,GV029,"học sâu, biển số",8.25
K98,E2E kho - Quản lý ký túc xá trực tuyến,,,,,"7,5"
K98,,,,,,
CSVEOF
  status="$(call POST /api/archive/import "${TOKEN_BOMON}" -F "file=@${csv_path};type=text/csv")"
  [ "$status" = "200" ] || fail "Bộ môn import CSV không trả 200 (mã ${status}, $(cat "$TMP/body"))"
  local imp
  imp="$(jget "f\"{d['tong_dong']}|{d['thanh_cong']}|\" + ','.join(str(e['dong']) + ':' + e['ly_do'] for e in d['loi'])")"
  [ "$imp" = "3|2|4:Thiếu tên đề tài" ] || fail "Kết quả import CSV sai (nhận ${imp})"
  ok "Bộ môn import CSV 3 dòng -> 2 thành công, dòng 4 bị bỏ qua (Thiếu tên đề tài)"

  status="$(call GET /api/archive "${TOKEN_GV025}" --get --data-urlencode "q=biển số" --data-urlencode "khoa=K98")"
  [ "$status" = "200" ] || fail "GV025 tìm kiếm kho theo từ khóa không trả 200 (mã ${status})"
  local imported_id
  imported_id="$(jget "d['items'][0]['id'] if d['total'] == 1 and d['items'][0]['nguon'] == 'IMPORT' else ''")"
  [ -n "$imported_id" ] || fail "Tìm 'biển số' không ra đúng một bản ghi import ($(cat "$TMP/body"))"
  ok "GV025 tìm 'biển số' trong kho -> đúng bản ghi vừa import (id=${imported_id})"

  status="$(call POST /api/archive "${TOKEN_SV097}" -H 'Content-Type: application/json' \
    -d '{"khoa":"K98","ten_de_tai":"SV thêm trái phép"}')"
  [ "$status" = "403" ] || fail "DTC225200097 thêm bản ghi kho không bị từ chối 403 (mã ${status})"
  status="$(call POST /api/archive/import "${TOKEN_GV025}" -F "file=@${csv_path};type=text/csv")"
  [ "$status" = "403" ] || fail "GV025 import CSV không bị từ chối 403 (mã ${status})"
  ok "DTC225200097 thêm bản ghi + GV025 import CSV đều bị từ chối 403"

  DELETED_KHO_IDS="${imported_id}"
  status="$(call DELETE "/api/archive/${imported_id}" "${TOKEN_BOMON}")"
  [ "$status" = "204" ] || fail "Bộ môn xóa bản ghi import không trả 204 (mã ${status})"
  status="$(call GET "/api/archive/${imported_id}" "${TOKEN_BOMON}")"
  [ "$status" = "404" ] || fail "Bản ghi đã xóa vẫn đọc được (mã ${status})"
  ok "Bộ môn xóa một bản ghi import -> 204, đọc lại -> 404"
}

uc0_notifications() {
  # --- UC0.5/NOTF-01 (plan 03-07): đếm chưa đọc, riêng tư (404), đánh dấu tất cả ---
  local status unread note_id phan_cong
  status="$(call GET /api/notifications/unread-count "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không đọc được số thông báo chưa đọc (mã ${status})"
  unread="$(jget "d['chua_doc']")"
  [ "${unread:-0}" -gt 0 ] || fail "DTC225200098 không có thông báo chưa đọc sau cả chuỗi UC2-5 (nhận ${unread})"

  status="$(call GET "/api/notifications?page_size=50" "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không đọc được danh sách thông báo (mã ${status})"
  phan_cong="$(jget "sum(1 for i in d['items'] if i['loai'] == 'DE_TAI_PHAN_CONG' and i['lien_ket'] == '/de-tai/${DE_TAI_ID}')")"
  [ "$phan_cong" = "1" ] || fail "DTC225200098 không có đúng một thông báo DE_TAI_PHAN_CONG cho đề tài ${DE_TAI_ID} (nhận ${phan_cong})"
  note_id="$(jget "d['items'][0]['id']")"
  ok "DTC225200098 có ${unread} thông báo chưa đọc, gồm DE_TAI_PHAN_CONG từ quyết định duyệt đề tài (NOTF-01)"

  status="$(call POST "/api/notifications/${note_id}/read" "${TOKEN_SV097}")"
  [ "$status" = "404" ] || fail "DTC225200097 đánh dấu thông báo của DTC225200098 không bị 404 (mã ${status})"
  call GET /api/notifications/unread-count "${TOKEN_SV098}" >/dev/null
  [ "$(jget "d['chua_doc']")" = "$unread" ] || fail "Số chưa đọc của DTC225200098 bị đổi bởi người khác"
  ok "DTC225200097 đánh dấu thông báo của DTC225200098 -> 404, số chưa đọc không đổi"

  status="$(call POST /api/notifications/read-all "${TOKEN_SV098}")"
  [ "$status" = "204" ] || fail "DTC225200098 đánh dấu tất cả đã đọc không trả 204 (mã ${status})"
  call GET /api/notifications/unread-count "${TOKEN_SV098}" >/dev/null
  [ "$(jget "d['chua_doc']")" = "0" ] || fail "Sau read-all số chưa đọc của DTC225200098 khác 0"
  ok "DTC225200098 đánh dấu tất cả đã đọc -> 204, số chưa đọc = 0"
}

uc0_dashboards() {
  # --- MH-02/03/04 (plan 03-07): widget Phase 3 trên dashboard từng vai trò ---
  local status got
  status="$(call GET /api/dashboard/sinh-vien "${TOKEN_SV098}")"
  [ "$status" = "200" ] || fail "DTC225200098 không xem được dashboard (mã ${status})"
  got="$(jget "f\"{d['de_cuong']['trang_thai']}|{d['bao_ve']['diem_trung_binh']}|{len(d['tien_do'])}|{bool(d['bao_ve']['chu_tich'])}\"")"
  [ "$got" = "DA_DUYET|8.5|2|True" ] || fail "Dashboard SV sai (đề cương|điểm|số mốc|chủ tịch = ${got})"
  ok "Dashboard DTC225200098: đề cương Đã duyệt, 2 mốc tiến độ, lịch bảo vệ có Chủ tịch, điểm 8.5 (MH-02)"

  status="$(call GET /api/dashboard/giang-vien "${TOKEN_GV029}")"
  [ "$status" = "200" ] || fail "GV029 không xem được dashboard (mã ${status})"
  got="$(jget "all(k in d for k in ('so_de_cuong_cho_duyet','so_bao_cao_cho_nhan_xet','so_hoi_dong_tham_gia','viec_can_xu_ly'))")"
  [ "$got" = "True" ] || fail "Dashboard GV029 thiếu bộ đếm Phase 3 ($(cat "$TMP/body"))"
  ok "Dashboard GV029 có Đề cương chờ duyệt / Báo cáo chờ nhận xét / Hội đồng tham gia / Việc cần xử lý (MH-03)"

  status="$(call GET "/api/dashboard/bo-mon?dot_do_an_id=${DOT_DO_AN_ID}" "${TOKEN_BOMON}")"
  [ "$status" = "200" ] || fail "Bộ môn không xem được dashboard đợt K98 (mã ${status})"
  got="$(jget "f\"{d['sv_tre_moc']}|{d['tien_do_trich']['tong']}|{len(d['moc_tien_do'])}\"")"
  [ "${got%%|*}" -ge 1 ] || fail "Dashboard Bộ môn K98 không thấy SV trễ mốc (sv_tre_moc|tong|so_moc = ${got})"
  ok "Dashboard Bộ môn đợt K98: SV trễ mốc|tổng SV|số mốc = ${got} (MH-04)"

  status="$(call GET /api/dashboard/bo-mon "${TOKEN_SV098}")"
  [ "$status" = "403" ] || fail "DTC225200098 xem dashboard Bộ môn không bị 403 (mã ${status})"
  ok "DTC225200098 xem dashboard Bộ môn -> 403"
}

setup_assigned_topic
uc2_outline
uc3_progress
uc4_defense
uc5_archive
uc0_notifications
uc0_dashboards

echo "OK: e2e UC2-5 (đề cương -> tiến độ -> bảo vệ -> lưu kho -> tra cứu/quản lý kho -> thông báo -> dashboard) hoàn tất — dữ liệu đợt K98 sẽ được dọn khi script kết thúc (trap)"
