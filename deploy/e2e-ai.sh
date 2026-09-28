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
# Dọn dẹp (trap, kể cả khi lỗi giữa chừng): purge vector TOPIC/ARCHIVE đã tạo
# khỏi chỉ mục AI rồi xóa dữ liệu K97 theo thứ tự khóa ngoại.
#
# Tài khoản dành riêng (không script nào khác dùng): bomon, DTC225200095,
# DTC225200096 (SV), GV023 (GVHD, dự phòng — chưa dùng); khóa kiểm thử K97
# (e2e-uc1 dùng K99, e2e-uc2-5 dùng K98). Cần chạy `bash deploy/seed-ai.sh` trước.
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
      sql "DELETE ct FROM chi_tiet_trung_lap ct JOIN ket_qua_kiem_tra_trung_lap kq ON kq.id = ct.ket_qua_id JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
      sql "DELETE kq FROM ket_qua_kiem_tra_trung_lap kq JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
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

require_seeds
ai_security
ai_title
ai_index

echo "OK: e2e dịch vụ AI hoàn tất (bắt đầu ${START_UTC} UTC)"
