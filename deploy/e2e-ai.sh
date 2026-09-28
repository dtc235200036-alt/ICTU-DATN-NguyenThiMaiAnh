#!/usr/bin/env bash
# Phase 4 (04-05): e2e dịch vụ AI qua stack compose thật.
#   ai_security — NFR-07/AISV-01: cổng AI không mở ra host, không có route
#                 Apache, thiếu/sai X-API-Key -> 401, tài khoản DB thesis_ai
#                 không đọc được thesis_core.
#   ai_title    — ROADMAP SC1/AISV-03: SV kiểm tra một tên diễn đạt lại của đề
#                 tài kho đã seed -> kết quả đầu tiên là đồ án kho đúng đối
#                 tượng, <= 5 s; NFC và NFD cho kết quả giống hệt; tên cùng
#                 lĩnh vực không bị cảnh báo trùng kho.
#
# Tài khoản dành riêng (không script nào khác dùng): bomon, DTC225200095,
# DTC225200096 (SV), GV023 (GVHD, dự phòng); khóa kiểm thử K97 (e2e-uc1 dùng
# K99, e2e-uc2-5 dùng K98). Cần chạy `bash deploy/seed-ai.sh` trước.
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

cleanup() {
  rm -rf "$TMP"
}
trap cleanup EXIT

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

require_seeds
ai_security
ai_title

echo "OK: e2e dịch vụ AI hoàn tất (bắt đầu ${START_UTC} UTC)"
