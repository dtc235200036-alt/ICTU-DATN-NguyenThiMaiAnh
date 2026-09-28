#!/usr/bin/env bash
# Phase 4 (04-05): e2e dịch vụ AI qua stack compose thật.
#   ai_security — NFR-07/AISV-01: cổng AI không mở ra host, không có route
#                 Apache, thiếu/sai X-API-Key -> 401, tài khoản DB thesis_ai
#                 không đọc được thesis_core.
#   ai_title    — ROADMAP SC1/AISV-03: SV kiểm tra một tên diễn đạt lại của đề
#                 tài kho đã seed -> kết quả đầu tiên là đồ án kho đúng đối
#                 tượng, <= 5 s; NFC và NFD cho kết quả giống hệt; tên cùng
#                 lĩnh vực không bị cảnh báo trùng kho.
#   ai_index    — ROADMAP SC5/AISV-02/NFR-11: bản ghi kho mới và đề tài vừa gửi
#                 duyệt được index ngay (push-on-write), đúng một lần encode,
#                 và lần kiểm tra tên kế tiếp đã thấy chúng.
#   ai_document — ROADMAP SC2/AISV-04..06 (04-06): SV nộp tài liệu B của một
#                 cặp chép nguyên văn -> HOAN_TAT, tỷ lệ >= NGUONG_TAI_LIEU,
#                 đồ án trùng "{tên A} ({khóa})", đoạn nộp cạnh đoạn nguồn,
#                 không đoạn khuôn mẫu; B của cặp không liên quan dưới ngưỡng;
#                 GVHD thấy cùng kết quả; nộp lại không khớp chính đề tài mình.
# Dọn dẹp (trap, kể cả khi lỗi giữa chừng): purge vector TOPIC/ARCHIVE/DOCUMENT
# đã tạo khỏi chỉ mục AI, xóa file đã nộp rồi xóa dữ liệu K97 theo thứ tự khóa
# ngoại.
#
# Tài khoản dành riêng (không script nào khác dùng): bomon, DTC225200095,
# DTC225200096 (SV), GV023 (GVHD); khóa kiểm thử K97 (e2e-uc1 dùng K99,
# e2e-uc2-5 dùng K98, ai-nfr dùng K96). Cần chạy `bash deploy/seed-ai.sh` trước.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BASE="${BASE_URL:-https://localhost}"
COMPOSE=(docker compose -f "${SCRIPT_DIR}/docker-compose.yml")

fail() {
  echo "FAIL: $1"
  exit 1
}

ok() {
  echo "OK: $1"
}

TMP="$(mktemp -d)"
START_UTC="$(date -u +%Y-%m-%dT%H:%M:%S)"

# call METHOD PATH TOKEN [curl args...] — thân trả về ghi vào $TMP/body, in
# ra "mã_HTTP thời_gian_giây".
call() {
  local method="$1" path="$2" token="$3"
  shift 3
  curl -sk -o "$TMP/body" -w '%{http_code} %{time_total}' -X "$method" "$BASE$path" \
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

DOT_DO_AN_ID=""
KHO_IDS=""
# Đề tài K97 do DTC225200095 tự đề xuất trong ai_index — ai_document dùng lại
# (một SV chỉ được giữ một đề tài đang hoạt động).
TOPIC_SV_A_ID=""

sql() {
  DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" "$1"
}

cleanup() {
  local topic_ids kho_ids
  if [ -n "${DOT_DO_AN_ID}" ] || [ -n "${KHO_IDS}" ]; then
    topic_ids=""
    if [ -n "${DOT_DO_AN_ID}" ]; then
      topic_ids="$(sql "SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}" 2>/dev/null | paste -sd, - || true)"
    fi
    kho_ids="$(sql "SELECT id FROM do_an_kho WHERE khoa = 'K97'" 2>/dev/null | paste -sd, - || true)"
    kho_ids="$(printf '%s,%s' "${KHO_IDS}" "${kho_ids}" | tr ',' '\n' | grep -E '^[0-9]+$' | sort -un | paste -sd, - || true)"
    # Không để lại vector mồ côi trong chỉ mục AI (T-04-21).
    if [ -n "${topic_ids}" ]; then
      "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai TOPIC --ids "${topic_ids}" >/dev/null 2>&1 || true
    fi
    if [ -n "${kho_ids}" ]; then
      "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai ARCHIVE --ids "${kho_ids}" >/dev/null 2>&1 || true
    fi
    sql "DELETE FROM thong_bao WHERE tai_khoan_id IN (SELECT id FROM tai_khoan WHERE ma_dang_nhap IN ('DTC225200095','DTC225200096','GV023')) AND thoi_diem >= '${START_UTC}';" >/dev/null 2>&1 || true
    if [ -n "${DOT_DO_AN_ID}" ]; then
      local doc_ids files ten
      doc_ids="$(sql "SELECT t.id FROM tai_lieu_do_an t JOIN de_tai dt ON dt.id = t.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID}" 2>/dev/null | paste -sd, - || true)"
      if [ -n "${doc_ids}" ]; then
        "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai DOCUMENT --ids "${doc_ids}" >/dev/null 2>&1 || true
      fi
      files="$(sql "SELECT t.ten_luu_tru FROM tai_lieu_do_an t JOIN de_tai dt ON dt.id = t.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID}" 2>/dev/null || true)"
      while IFS= read -r ten; do
        [ -z "$ten" ] && continue
        "${COMPOSE[@]}" exec -T api rm -f "/data/uploads/${ten}" </dev/null >/dev/null 2>&1 || true
      done <<<"${files}"
      sql "DELETE ct FROM chi_tiet_trung_lap ct JOIN ket_qua_kiem_tra_trung_lap kq ON kq.id = ct.ket_qua_id JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
      sql "DELETE kq FROM ket_qua_kiem_tra_trung_lap kq JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
      sql "DELETE l FROM luot_duyet_de_cuong l JOIN de_cuong dc ON dc.id = l.de_cuong_id JOIN de_tai dt ON dt.id = dc.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
      sql "DELETE t FROM tai_lieu_do_an t JOIN de_tai dt ON dt.id = t.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
      sql "DELETE dc FROM de_cuong dc JOIN de_tai dt ON dt.id = dc.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
      sql "DELETE FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    fi
    if [ -n "${kho_ids}" ]; then
      sql "DELETE FROM do_an_kho WHERE id IN (${kho_ids});" >/dev/null 2>&1 || true
    fi
    if [ -n "${DOT_DO_AN_ID}" ]; then
      sql "DELETE FROM dot_do_an WHERE id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    fi
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT

# encode_calls của dịch vụ AI (/health không cần khóa, gọi từ trong container api).
encode_calls() {
  "${COMPOSE[@]}" exec -T api python -c "
import json, urllib.request
print(json.load(urllib.request.urlopen('http://ai:8002/health', timeout=4))['encode_calls'])
"
}

# check_title TOKEN TEN — POST /api/topics/check-title, thân ở $TMP/body.
check_title() {
  python3 -c 'import json,sys; print(json.dumps({"ten_de_tai": sys.argv[1]}, ensure_ascii=False))' "$2" > "$TMP/req.json"
  call POST /api/topics/check-title "$1" -H 'Content-Type: application/json' --data-binary "@$TMP/req.json"
}

require_seeds() {
  local n
  n="$(bash "${SCRIPT_DIR}/sql.sh" "SELECT COUNT(*) FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN ('K18','K19','K20','K21','K22') AND trang_thai_index='DA_INDEX'")"
  [ "$n" -ge 300 ] || fail "Chưa seed — chạy bash deploy/seed-ai.sh (mới có ${n}/300 đề tài kho DA_INDEX)"
  ok "Kho đã seed: ${n} đề tài kho DA_INDEX"
}

# --- ai_security (NFR-07, AISV-01, T-04-15/T-04-17) --------------------------
ai_security() {
  # (1) Từ host: cổng 8002 không được publish.
  if curl -s -m 3 -o /dev/null "http://127.0.0.1:8002/health"; then
    fail "Cổng dịch vụ AI 8002 truy cập được từ host"
  fi
  ok "Host không kết nối được tới 127.0.0.1:8002 (không publish cổng AI)"

  # (2) Trong mạng nội bộ: thiếu/sai khóa -> 401, đúng khóa -> 200. Khóa đọc
  # BÊN TRONG container api, không bao giờ in ra.
  local codes
  codes="$("${COMPOSE[@]}" exec -T api python -c "
import json, os, urllib.error, urllib.request
def post(headers):
    req = urllib.request.Request('http://ai:8002/check-title', data=json.dumps({'text': 'Xây dựng hệ thống quản lý thư viện'}).encode(), headers={'Content-Type': 'application/json', **headers}, method='POST')
    try:
        return urllib.request.urlopen(req, timeout=10).status
    except urllib.error.HTTPError as e:
        return e.code
print(post({}), post({'X-API-Key': 'sai-khoa-' + 'x' * 40}), post({'X-API-Key': os.environ['AI_API_KEY']}))
")"
  [ "$codes" = "401 401 200" ] || fail "X-API-Key: kỳ vọng '401 401 200' (thiếu/sai/đúng), nhận '${codes}'"
  ok "Trong mạng nội bộ: thiếu khóa 401, sai khóa 401, đúng khóa 200"

  # (3) Apache không có route nào tới dịch vụ AI.
  if grep -Eq '8002|//ai[:/]' "${SCRIPT_DIR}/apache/ntma.conf"; then
    fail "deploy/apache/ntma.conf có route tới dịch vụ AI"
  fi
  local code
  code="$(curl -sk -o "$TMP/apache-ai" -w '%{http_code}' -X POST "$BASE/check-title" \
    -H 'Content-Type: application/json' -d '{"text":"Xây dựng hệ thống quản lý thư viện"}')"
  if grep -q '"matches"\|API key nội bộ' "$TMP/apache-ai"; then
    fail "POST ${BASE}/check-title qua Apache trả về thân JSON của dịch vụ AI (HTTP ${code})"
  fi
  ok "Apache không có route tới dịch vụ AI (POST /check-title -> HTTP ${code}, không phải AI)"

  # (4) T-04-17: tài khoản DB thesis_ai không đọc được thesis_core.
  local db_probe
  db_probe="$("${COMPOSE[@]}" exec -T ai python -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    conn.execute(text('SELECT COUNT(*) FROM thesis_ai.chunk')).scalar()
    try:
        conn.execute(text('SELECT COUNT(*) FROM thesis_core.tai_khoan')).scalar()
        print('ALLOWED')
    except Exception:
        print('DENIED')
" 2>/dev/null | tail -1)"
  [ "$db_probe" = "DENIED" ] || fail "Tài khoản DB thesis_ai đọc được thesis_core (nhận '${db_probe}')"
  ok "Tài khoản DB thesis_ai chỉ có quyền trên thesis_ai (thesis_core bị từ chối)"
}

# --- ai_title (SC1, AISV-03, AISV-02 NFC=NFD) --------------------------------
ai_title() {
  local token_sv
  token_sv="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200095)"

  # Truy vấn đã được hiệu chỉnh đánh giá đúng (04-04): 3 DIEN_DAT_LAI bị cảnh
  # báo + đúng top-1 và 1 CUNG_LINH_VUC đúng là không cảnh báo.
  python3 - "$REPO_ROOT" > "$TMP/queries.tsv" <<'PY'
import csv, json, sys
root = sys.argv[1]
ket_qua = json.load(open(f"{root}/ai-service/calibration/ket-qua-chi-tiet.json"))
rows = {r["ma_truy_van"]: r for r in csv.DictReader(open(f"{root}/seed-data/truy-van-ten-de-tai.csv", encoding="utf-8-sig"))}
pos = [q for q in ket_qua["truy_van"] if q["loai"] == "DIEN_DAT_LAI" and q["dat"] and q["bi_canh_bao"] and q["top1_dung_doi_tuong"]][:3]
neg = [q for q in ket_qua["truy_van"] if q["loai"] == "CUNG_LINH_VUC" and q["dat"]][:1]
for kind, qs in (("POS", pos), ("NEG", neg)):
    for q in qs:
        r = rows[q["ma_truy_van"]]
        print("\t".join([kind, r["ma_truy_van"], r["ma_doi_tuong"], r["ten_truy_van"]]))
PY
  [ "$(grep -c '^POS' "$TMP/queries.tsv")" = "3" ] && [ "$(grep -c '^NEG' "$TMP/queries.tsv")" = "1" ] \
    || fail "Không chọn được 3 truy vấn dương + 1 âm từ ket-qua-chi-tiet.json"

  local kind ma doi_tuong ten res code secs body_nfc body_nfd top
  while IFS=$'\t' read -r kind ma doi_tuong ten; do
    python3 -c 'import json,sys; print(json.dumps({"ten_de_tai": sys.argv[1]}, ensure_ascii=False))' "$ten" > "$TMP/req-nfc.json"
    python3 -c 'import json,sys,unicodedata; print(json.dumps({"ten_de_tai": unicodedata.normalize("NFD", sys.argv[1])}, ensure_ascii=False))' "$ten" > "$TMP/req-nfd.json"
    cmp -s "$TMP/req-nfc.json" "$TMP/req-nfd.json" && fail "${ma}: dạng NFD trùng NFC — truy vấn không có dấu?"

    res="$(call POST /api/topics/check-title "$token_sv" -H 'Content-Type: application/json' --data-binary "@$TMP/req-nfc.json")"
    code="${res%% *}"; secs="${res#* }"
    [ "$code" = "200" ] || fail "${ma}: check-title trả ${code}: $(cat "$TMP/body")"
    [ "$(jget 'd["trang_thai"]')" = "HOAN_TAT" ] || fail "${ma}: trạng thái kiểm tra không HOAN_TAT: $(cat "$TMP/body")"
    python3 -c "import sys; sys.exit(0 if float('$secs') <= 5.0 else 1)" || fail "${ma}: check-title mất ${secs}s (> 5 s)"
    body_nfc="$(jget 'json.dumps([(m["nguon"], m["de_tai_id"] or m["do_an_kho_id"], m["ty_le"]) for m in d["matches"]])')"
    cp "$TMP/body" "$TMP/body-nfc"

    res="$(call POST /api/topics/check-title "$token_sv" -H 'Content-Type: application/json' --data-binary "@$TMP/req-nfd.json")"
    [ "${res%% *}" = "200" ] || fail "${ma}: check-title (NFD) trả ${res%% *}"
    body_nfd="$(jget 'json.dumps([(m["nguon"], m["de_tai_id"] or m["do_an_kho_id"], m["ty_le"]) for m in d["matches"]])')"
    [ "$body_nfc" = "$body_nfd" ] || fail "${ma}: NFC và NFD cho kết quả khác nhau (${body_nfc} vs ${body_nfd})"

    if [ "$kind" = "POS" ]; then
      top="$(python3 - "$TMP/body-nfc" "$REPO_ROOT/seed-data/manifest.json" "$doi_tuong" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
manifest = json.load(open(sys.argv[2]))
if not d["matches"]:
    print("KHÔNG CÓ KẾT QUẢ"); sys.exit(1)
m = d["matches"][0]
objs = {t["ma_doi_tuong"] for t in manifest["topics"] if t["ten_de_tai"] == m["ten_de_tai"]}
if m["nguon"] != "KHO" or sys.argv[3] not in objs:
    print(f"top-1 = {m['nguon']} '{m['ten_de_tai']}' ({sorted(objs)}), kỳ vọng KHO thuộc {sys.argv[3]}"); sys.exit(1)
print(f"{m['ty_le']}% — {m['ten_de_tai']} ({m['khoa']}, GVHD {m['giang_vien']})")
PY
)" || fail "${ma}: ${top}"
      ok "${ma} (diễn đạt lại, ${secs}s, NFC=NFD): top-1 Kho đồ án ${top}"
    else
      [ "$(jget 'sum(1 for m in d["matches"] if m["nguon"] == "KHO")')" = "0" ] \
        || fail "${ma} (cùng lĩnh vực): bị cảnh báo trùng kho: $(cat "$TMP/body-nfc")"
      ok "${ma} (cùng lĩnh vực, ${secs}s, NFC=NFD): không có kết quả Kho đồ án vượt ngưỡng"
    fi
  done < "$TMP/queries.tsv"
}

# --- ai_index (SC5, AISV-02, NFR-11) -----------------------------------------
ai_index() {
  local token_bomon token_sv_a token_sv_b res before after kho_id topic_id deadline hit

  token_bomon="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
  token_sv_a="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200095)"
  token_sv_b="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200096)"

  res="$(call POST /api/cohorts "$token_bomon" -H 'Content-Type: application/json' \
    -d '{"ten_dot":"Đợt kiểm thử tự động AI","khoa":"K97","nam_hoc":"2026-2027","ngay_bat_dau":"2026-01-01"}')"
  [ "${res%% *}" = "201" ] || [ "${res%% *}" = "200" ] || fail "Không tạo được đợt K97 (${res%% *}): $(cat "$TMP/body")"
  DOT_DO_AN_ID="$(jget 'd["id"]')"
  [ -n "$DOT_DO_AN_ID" ] || fail "Không đọc được id đợt K97"
  ok "Bộ môn tạo đợt kiểm thử K97 (id=${DOT_DO_AN_ID})"

  # (a) Bản ghi kho mới -> DA_INDEX trong <= 30 s, đúng MỘT lần encode.
  before="$(encode_calls)"
  res="$(call POST /api/archive "$token_bomon" -H 'Content-Type: application/json' \
    -d '{"khoa":"K97","ten_de_tai":"Xây dựng hệ thống quản lý phòng thí nghiệm hóa học cho trường cao đẳng y tế"}')"
  [ "${res%% *}" = "201" ] || fail "Bộ môn thêm bản ghi kho K97 trả ${res%% *}: $(cat "$TMP/body")"
  kho_id="$(jget 'd["id"]')"
  KHO_IDS="${kho_id}"
  deadline=$((SECONDS + 30))
  while :; do
    call GET "/api/archive/${kho_id}" "$token_bomon" >/dev/null
    [ "$(jget 'd["trang_thai_index"]')" = "DA_INDEX" ] && break
    [ "$SECONDS" -lt "$deadline" ] || fail "Bản ghi kho ${kho_id} chưa DA_INDEX sau 30 s"
    sleep 1
  done
  after="$(encode_calls)"
  [ "$((after - before))" = "1" ] || fail "Index bản ghi kho mới tốn $((after - before)) lần encode (kỳ vọng 1 — NFR-11)"
  ok "Bản ghi kho K97 (id=${kho_id}) DA_INDEX, encode_calls ${before} -> ${after} (+1, không tính lại corpus)"

  res="$(check_title "$token_sv_b" "Phát triển phần mềm quản lý phòng thí nghiệm hóa học tại trường cao đẳng y tế")"
  [ "${res%% *}" = "200" ] || fail "check-title trả ${res%% *}"
  hit="$(jget "next((m['ty_le'] for m in d['matches'] if m['nguon'] == 'KHO' and m['do_an_kho_id'] == ${kho_id}), '')")"
  [ -n "$hit" ] || fail "Lần kiểm tra kế tiếp không thấy bản ghi kho vừa thêm: $(cat "$TMP/body")"
  ok "DTC225200096 kiểm tra tên diễn đạt lại -> thấy ngay bản ghi kho mới (${hit}%)"

  # (b) Đề tài SV tự đề xuất, gửi duyệt ngay -> index sau commit.
  before="$(encode_calls)"
  python3 -c 'import json,sys; print(json.dumps({"dot_do_an_id": int(sys.argv[1]), "ten_de_tai": "Ứng dụng di động theo dõi lịch tiêm chủng cho trẻ em tại trạm y tế xã", "linh_vuc": "Công nghệ phần mềm", "gui": True}, ensure_ascii=False))' "$DOT_DO_AN_ID" > "$TMP/topic.json"
  res="$(call POST /api/topics "$token_sv_a" -H 'Content-Type: application/json' --data-binary "@$TMP/topic.json")"
  [ "${res%% *}" = "201" ] || fail "DTC225200095 tự đề xuất đề tài trả ${res%% *}: $(cat "$TMP/body")"
  topic_id="$(jget 'd["id"]')"
  TOPIC_SV_A_ID="${topic_id}"
  [ "$(jget 'd["trang_thai"]')" = "CHO_DUYET" ] || fail "Đề tài mới không ở CHO_DUYET"
  # +2 = 1 encode truy vấn (kiểm tra tên lưu lúc gửi) + 1 encode ingest TOPIC.
  deadline=$((SECONDS + 10))
  while :; do
    after="$(encode_calls)"
    [ "$((after - before))" -ge 2 ] && break
    [ "$SECONDS" -lt "$deadline" ] || fail "Đề tài ${topic_id} chưa được index sau 10 s (encode_calls +$((after - before)))"
    sleep 1
  done
  [ "$((after - before))" = "2" ] || fail "Gửi đề tài tốn $((after - before)) lần encode (kỳ vọng 2 = 1 kiểm tra tên + 1 ingest)"
  ok "DTC225200095 gửi đề tài K97 (id=${topic_id}) -> CHO_DUYET, index nền (encode_calls +2 = kiểm tra tên + ingest)"

  res="$(check_title "$token_sv_b" "Xây dựng ứng dụng di động quản lý lịch tiêm chủng trẻ em cho trạm y tế xã")"
  [ "${res%% *}" = "200" ] || fail "check-title trả ${res%% *}"
  hit="$(jget "next((m['ty_le'] for m in d['matches'] if m['nguon'] == 'DE_TAI' and m['de_tai_id'] == ${topic_id}), '')")"
  [ -n "$hit" ] || fail "Lần kiểm tra kế tiếp không thấy đề tài vừa gửi: $(cat "$TMP/body")"
  ok "DTC225200096 kiểm tra tên diễn đạt lại -> thấy ngay đề tài hiện hành vừa gửi (${hit}%)"
}

# --- ai_document (SC2, AISV-04/05/06, D-03/D-04) ------------------------------
DOCX_CT="application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# submit_outline TOKEN DE_TAI_ID FILE — nộp đề cương, in ra tai_lieu_do_an id.
submit_outline() {
  local ct="application/pdf" res
  case "$3" in *.docx) ct="$DOCX_CT" ;; esac
  res="$(call POST "/api/outlines/$2/submit" "$1" -F "file=@$3;type=${ct}")"
  [ "${res%% *}" = "202" ] || fail "Nộp đề cương $(basename "$3") trả ${res%% *}: $(cat "$TMP/body")" >&2
  echo "OK: nộp $(basename "$3") cho đề tài $2 -> 202 trong ${res#* }s" >&2
  jget 'd["phien_ban"][0]["tai_lieu"]["id"]'
}

# wait_check TOKEN DOC_ID OUT — chờ tối đa 30 s tới HOAN_TAT, chép thân vào OUT.
wait_check() {
  local deadline=$((SECONDS + 30)) trang
  while :; do
    call GET "/api/documents/$2/check" "$1" >/dev/null
    trang="$(jget 'd["trang_thai"]')"
    [ "$trang" = "HOAN_TAT" ] && break
    [ "$trang" = "LOI" ] && fail "Kiểm tra tài liệu $2 kết thúc LOI"
    [ "$SECONDS" -lt "$deadline" ] || fail "Kiểm tra tài liệu $2 chưa HOAN_TAT sau 30 s (${trang})"
    sleep 0.5
  done
  cp "$TMP/body" "$3"
}

# review_changes TOKEN_GV DE_TAI_ID DOC_ID — GVHD yêu cầu sửa (để nộp phiên bản mới).
review_changes() {
  local res
  res="$(call POST "/api/outlines/$2/review" "$1" -H 'Content-Type: application/json' \
    -d "{\"tai_lieu_do_an_id\":$3,\"ket_qua\":\"YEU_CAU_SUA\",\"nhan_xet\":\"Kiểm thử tự động: nộp lại\"}")"
  [ "${res%% *}" = "200" ] || fail "GVHD yêu cầu sửa đề cương đề tài $2 trả ${res%% *}: $(cat "$TMP/body")"
}

ai_document() {
  local token_bomon token_sv_a token_sv_b token_gv gv_id topic_b res nguong t
  token_bomon="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
  token_sv_a="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200095)"
  token_sv_b="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200096)"
  token_gv="$(bash "${SCRIPT_DIR}/api-login.sh" GV023)"
  [ -n "${TOPIC_SV_A_ID}" ] || fail "ai_document cần đề tài K97 của DTC225200095 từ ai_index"

  call GET /api/lecturers "$token_bomon" >/dev/null
  gv_id="$(jget 'next((g["id"] for g in d if g.get("ma_giang_vien") == "GV023"), "")')"
  [ -n "$gv_id" ] || fail "Không tìm được id GV023"

  python3 -c 'import json,sys; print(json.dumps({"dot_do_an_id": int(sys.argv[1]), "ten_de_tai": "Hệ thống đặt lịch sân bóng mini trực tuyến cho câu lạc bộ thể thao phường", "linh_vuc": "Công nghệ phần mềm", "gui": True}, ensure_ascii=False))' "$DOT_DO_AN_ID" > "$TMP/topic-b.json"
  res="$(call POST /api/topics "$token_sv_b" -H 'Content-Type: application/json' --data-binary "@$TMP/topic-b.json")"
  [ "${res%% *}" = "201" ] || fail "DTC225200096 tự đề xuất đề tài trả ${res%% *}: $(cat "$TMP/body")"
  topic_b="$(jget 'd["id"]')"

  for t in "${TOPIC_SV_A_ID}" "${topic_b}"; do
    res="$(call POST "/api/topic-approvals/${t}/approve" "$token_bomon" -H 'Content-Type: application/json' -d "{\"giang_vien_id\":${gv_id}}")"
    [ "${res%% *}" = "200" ] || fail "Bộ môn duyệt đề tài ${t} trả ${res%% *}: $(cat "$TMP/body")"
    [ "$(jget 'd["trang_thai"]')" = "DA_PHAN_CONG" ] || fail "Đề tài ${t} không DA_PHAN_CONG"
  done
  ok "Bộ môn duyệt 2 đề tài K97 (${TOPIC_SV_A_ID}, ${topic_b}) với GVHD GV023 -> DA_PHAN_CONG"

  # Cặp chép nguyên văn và cặp không liên quan đầu tiên mà hiệu chỉnh (04-04) đánh giá đạt.
  python3 - "$REPO_ROOT" > "$TMP/pairs.tsv" <<'PY'
import json, sys
root = sys.argv[1]
manifest = json.load(open(f"{root}/seed-data/manifest.json", encoding="utf-8"))
dat = {c["ma_cap"] for c in json.load(open(f"{root}/ai-service/calibration/ket-qua-chi-tiet.json", encoding="utf-8"))["cap"] if c["dat"]}
for loai in ("CHEP_NGUYEN_VAN", "KHONG_LIEN_QUAN"):
    cap = next(c for c in manifest["cap"] if c["loai"] == loai and c["ma_cap"] in dat)
    print("\t".join([loai, cap["ma_cap"], f"{root}/seed-data/{cap['B']['tep']}", f"{cap['A']['ten_de_tai']} ({cap['A']['khoa']})"]))
PY
  local chep_ma chep_file chep_label khac_ma khac_file
  IFS=$'\t' read -r _ chep_ma chep_file chep_label < <(grep '^CHEP_NGUYEN_VAN' "$TMP/pairs.tsv")
  IFS=$'\t' read -r _ khac_ma khac_file _ < <(grep '^KHONG_LIEN_QUAN' "$TMP/pairs.tsv")
  [ -f "$chep_file" ] && [ -f "$khac_file" ] || fail "Không thấy tệp B của cặp ${chep_ma}/${khac_ma}"
  nguong="$(sql "SELECT gia_tri FROM cau_hinh_nguong WHERE loai='NGUONG_TAI_LIEU'")"

  # (1) Bài chép nguyên văn -> cảnh báo, đúng đồ án nguồn, đoạn nộp cạnh đoạn nguồn.
  local doc_a t0 own_label summary_a
  t0=$SECONDS
  doc_a="$(submit_outline "$token_sv_a" "${TOPIC_SV_A_ID}" "$chep_file")"
  wait_check "$token_sv_a" "$doc_a" "$TMP/check-a.json"
  own_label="$(sql "SELECT CONCAT(ten_de_tai, ' (K97)') FROM de_tai WHERE id = ${TOPIC_SV_A_ID}")"
  summary_a="$(python3 - "$TMP/check-a.json" "$nguong" "$chep_label" "$own_label" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
nguong, label, own = float(sys.argv[2]), sys.argv[3], sys.argv[4]
boiler = ("LỜI CAM ĐOAN", "MỤC LỤC", "TÀI LIỆU THAM KHẢO", "Đồ án tốt nghiệp - Khoa Công nghệ thông tin")
errs = []
if d["ty_le_tong"] is None or d["ty_le_tong"] < nguong:
    errs.append(f"ty_le_tong {d['ty_le_tong']} < {nguong}")
if not d["do_an_trung"] or d["do_an_trung"][0]["doi_tuong_trung"] != label:
    errs.append(f"đồ án trùng {[m['doi_tuong_trung'] for m in d['do_an_trung']]} != {label!r}")
segs = d["chi_tiet"]
if not any(s["doi_tuong_trung"] == label for s in segs):
    errs.append("không đoạn nào gắn nhãn đồ án nguồn")
if not any("trùng nguyên văn" in (s["vi_tri"] or "") for s in segs):
    errs.append("không đoạn nào 'trùng nguyên văn'")
if not all(s["doan_nguon"] and s["doan_trung"] and not s["doan_trung_an"] for s in segs):
    errs.append("có đoạn thiếu văn bản nộp/văn bản nguồn")
for s in segs:
    for b in boiler:
        if b in (s["doan_nguon"] or "") or b in (s["doan_trung"] or ""):
            errs.append(f"đoạn {s['vi_tri']} chứa khuôn mẫu {b!r}")
if any(s["doi_tuong_trung"] == own for s in segs):
    errs.append("khớp với chính đề tài của mình")
if errs:
    print("; ".join(errs)); sys.exit(1)
nv = sum(1 for s in segs if "nguyên văn" in (s["vi_tri"] or ""))
print(f"{d['ty_le_tong']}% >= {nguong}%, {len(segs)} đoạn ({nv} nguyên văn), đồ án trùng '{label}' {d['do_an_trung'][0]['ty_le']}%")
PY
)" || fail "${chep_ma}-B: kết quả kiểm tra không đạt SC2: ${summary_a}"
  ok "${chep_ma}-B (chép nguyên văn) HOAN_TAT sau $((SECONDS - t0))s: ${summary_a}; đoạn nộp cạnh đoạn nguồn, không đoạn khuôn mẫu"

  # (2) GVHD thấy cùng kết quả trên màn duyệt đề cương và trang chi tiết.
  res="$(call GET "/api/outlines/${TOPIC_SV_A_ID}" "$token_gv")"
  [ "${res%% *}" = "200" ] || fail "GV023 xem đề cương trả ${res%% *}"
  python3 - "$TMP/body" "$TMP/check-a.json" "$doc_a" <<'PY' || fail "GV023 không thấy cùng kết quả kiểm tra trên màn duyệt"
import json, sys
o = json.load(open(sys.argv[1], encoding="utf-8")); a = json.load(open(sys.argv[2], encoding="utf-8"))
v = next(p for p in o["phien_ban"] if p["tai_lieu"]["id"] == int(sys.argv[3]))
k = v["kiem_tra"]
sys.exit(0 if k["trang_thai"] == "HOAN_TAT" and k["ty_le_tong"] == a["ty_le_tong"] else 1)
PY
  res="$(call GET "/api/documents/${doc_a}/check" "$token_gv")"
  [ "${res%% *}" = "200" ] || fail "GV023 xem chi tiết kiểm tra trả ${res%% *}"
  python3 - "$TMP/body" "$TMP/check-a.json" <<'PY' || fail "GV023 thấy chi tiết khác SV"
import json, sys
g = json.load(open(sys.argv[1], encoding="utf-8")); a = json.load(open(sys.argv[2], encoding="utf-8"))
key = lambda d: (d["ty_le_tong"], [(m["doi_tuong_trung"], m["ty_le"]) for m in d["do_an_trung"]], [(s["vi_tri"], s["doan_nguon"], s["doan_trung"]) for s in d["chi_tiet"]])
sys.exit(0 if key(g) == key(a) else 1)
PY
  ok "GV023 thấy cùng tỷ lệ, đồ án trùng và đoạn trùng trên màn duyệt đề cương + chi tiết"

  # (3) Bài không liên quan -> dưới ngưỡng.
  local doc_b ty_b
  doc_b="$(submit_outline "$token_sv_b" "${topic_b}" "$khac_file")"
  wait_check "$token_sv_b" "$doc_b" "$TMP/check-b.json"
  ty_b="$(python3 -c "import json;print(json.load(open('$TMP/check-b.json'))['ty_le_tong'])")"
  python3 -c "import sys; sys.exit(0 if float('$ty_b') < float('$nguong') else 1)" \
    || fail "${khac_ma}-B (không liên quan) bị cảnh báo: ${ty_b}% >= ${nguong}%"
  ok "${khac_ma}-B (không liên quan) HOAN_TAT: ${ty_b}% < ${nguong}%"

  # (4) Nộp lại cùng file sau Yêu cầu sửa -> không khớp phiên bản trước của mình (loai_tru).
  local doc_a2 ty_a2
  review_changes "$token_gv" "${TOPIC_SV_A_ID}" "$doc_a"
  doc_a2="$(submit_outline "$token_sv_a" "${TOPIC_SV_A_ID}" "$chep_file")"
  wait_check "$token_gv" "$doc_a2" "$TMP/check-a2.json"
  ty_a2="$(python3 - "$TMP/check-a2.json" "$own_label" "$chep_label" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
labels = {s["doi_tuong_trung"] for s in d["chi_tiet"]} | {m["doi_tuong_trung"] for m in d["do_an_trung"]}
if sys.argv[2] in labels or not d["do_an_trung"] or d["do_an_trung"][0]["doi_tuong_trung"] != sys.argv[3]:
    print(sorted(labels)); sys.exit(1)
print(d["ty_le_tong"])
PY
)" || fail "Nộp lại khớp với phiên bản trước của chính đề tài: ${ty_a2}"
  ok "Nộp lại cùng file (v2) HOAN_TAT: ${ty_a2}%, không nhãn của chính đề tài, nguồn vẫn '${chep_label}'"
}

require_seeds
ai_security
ai_title
ai_index
ai_document

echo "OK: e2e dịch vụ AI hoàn tất (bắt đầu ${START_UTC} UTC)"
