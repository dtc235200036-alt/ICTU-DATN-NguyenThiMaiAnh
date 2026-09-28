#!/usr/bin/env bash
# DATA-02 / D-05: nạp 300 đề tài kho khóa K18–K22 (seed-data/de-tai-kho.csv)
# qua ĐÚNG đường import thật của hệ thống — POST /api/archive/import qua Apache
# với vai trò Bộ môn — để mỗi bản ghi đi qua archive.run_ingest → /ingest của
# dịch vụ AI (type ARCHIVE, id = do_an_kho.id, chỉ tên đề tài) và lật sang
# DA_INDEX. Chạy lại an toàn (idempotent): mọi dòng đã có bị báo "Trùng bản
# ghi" và không có gì được chèn thêm.
#
# Dùng: bash deploy/seed-ai.sh   (sau `docker compose ... up -d --build --wait`)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BASE="${BASE_URL:-https://localhost}"
CSV="${REPO_ROOT}/seed-data/de-tai-kho.csv"
COMPOSE=(docker compose -f "${SCRIPT_DIR}/docker-compose.yml")
EXPECTED=300
KHOA_SEED="'K18','K19','K20','K21','K22'"

fail() {
  echo "FAIL: $1"
  exit 1
}

ok() {
  echo "OK: $1"
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

[ -f "$CSV" ] || fail "Không thấy ${CSV}"

# (1) Chờ dịch vụ AI sẵn sàng (lần đầu có thể phải tải trọng số mô hình) —
# gọi /health từ BÊN TRONG container api (cổng AI không mở ra host).
deadline=$((SECONDS + 600))
until "${COMPOSE[@]}" exec -T api python -c "
import json, sys, urllib.request
r = urllib.request.urlopen('http://ai:8002/health', timeout=4)
sys.exit(0 if json.load(r).get('status') == 'ok' else 1)
" >/dev/null 2>&1; do
  [ "$SECONDS" -lt "$deadline" ] || fail "Dịch vụ AI chưa sẵn sàng sau 600 s (docker compose logs ai)"
  sleep 5
done
ok "Dịch vụ AI sẵn sàng (/health status ok)"

# (2) Import CSV qua đường thật của Bộ môn (UC5.4).
TOKEN_BOMON="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
status="$(curl -sk -o "$TMP/import.json" -w '%{http_code}' -X POST "$BASE/api/archive/import" \
  -H "Authorization: Bearer ${TOKEN_BOMON}" \
  -F "file=@${CSV};type=text/csv")"
[ "$status" = "200" ] || fail "POST /api/archive/import trả ${status}: $(cat "$TMP/import.json")"

python3 - "$TMP/import.json" "$EXPECTED" <<'PY' || fail "Kết quả import không như kỳ vọng: $(cat "$TMP/import.json")"
import json, sys
d = json.load(open(sys.argv[1]))
expected = int(sys.argv[2])
bad = [e for e in d["loi"] if "Trùng bản ghi" not in e["ly_do"]]
if d["tong_dong"] != expected or bad:
    print(f"tong_dong={d['tong_dong']} (kỳ vọng {expected}); lỗi khác trùng: {bad[:5]}")
    sys.exit(1)
print(f"OK: import {d['tong_dong']} dòng — mới {d['thanh_cong']}, đã có từ trước {len(d['loi'])}")
PY

# (3) Chờ run_ingest nền đẩy từng bản ghi sang dịch vụ AI (DA_INDEX).
count_indexed() {
  bash "${SCRIPT_DIR}/sql.sh" "SELECT COUNT(*) FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN (${KHOA_SEED}) AND trang_thai_index='DA_INDEX'"
}

wait_indexed() {
  local limit="$1" n
  local until_ts=$((SECONDS + limit))
  while :; do
    n="$(count_indexed)"
    [ "$n" -ge "$EXPECTED" ] && return 0
    [ "$SECONDS" -lt "$until_ts" ] || return 1
    sleep 3
  done
}

if ! wait_indexed 300; then
  # UC5.3: bản ghi còn CHUA_INDEX (vd. dịch vụ AI lỗi giữa chừng) -> index lại
  # từng bản ghi một lần qua endpoint thật, rồi chờ tiếp.
  pending="$(bash "${SCRIPT_DIR}/sql.sh" "SELECT id FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN (${KHOA_SEED}) AND trang_thai_index='CHUA_INDEX'")"
  echo "Còn $(printf '%s\n' "$pending" | grep -c . || true) bản ghi CHUA_INDEX — index lại"
  for id in $pending; do
    code="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/archive/${id}/reindex" \
      -H "Authorization: Bearer ${TOKEN_BOMON}")"
    [ "$code" = "202" ] || fail "POST /api/archive/${id}/reindex trả ${code}"
  done
  wait_indexed 300 || fail "Chỉ $(count_indexed)/${EXPECTED} đề tài kho ở DA_INDEX sau khi index lại"
fi

ok "${EXPECTED} đề tài kho đã index"

# (4) DATA-03 (04-06): 25 tài liệu nguồn (A) thành đồ án khóa cũ có báo cáo
# cuối, liên kết với bản ghi kho vừa import, index DOCUMENT. Chạy lại không đổi gì.
"${COMPOSE[@]}" exec -T api python -m app.seed_ai_corpus --data /seed-data \
  || fail "seed_ai_corpus thất bại"

# (5) Backfill: index các đề tài hiện hành (không phải nháp, chưa vào kho) đã
# có từ demo Phase 2/3, tự chữa vector kho/tài liệu còn thiếu (vd. volume
# thesis_ai bị xóa) — văn bản không đổi là no-op phía dịch vụ AI.
"${COMPOSE[@]}" exec -T api python -m app.services.ai_index backfill --loai TOPIC ARCHIVE DOCUMENT \
  || fail "ai_index backfill thất bại"
ok "Backfill TOPIC + ARCHIVE + DOCUMENT xong"

# (6) Kiểm tra cuối: đúng 25 bản ghi kho nguồn đã liên kết đề tài có báo cáo,
# và chỉ mục tài liệu của dịch vụ AI không rỗng.
linked="$(bash "${SCRIPT_DIR}/sql.sh" "SELECT COUNT(*) FROM do_an_kho k JOIN tai_lieu_do_an t ON t.de_tai_id = k.de_tai_id AND t.loai = 'BAO_CAO_CUOI' WHERE k.nguon='IMPORT' AND k.khoa IN (${KHOA_SEED})")"
[ "$linked" = "25" ] || fail "Kỳ vọng 25 bản ghi kho nguồn có báo cáo cuối, nhận ${linked}"
size_tai_lieu="$("${COMPOSE[@]}" exec -T api python -c "
import json, urllib.request
print(json.load(urllib.request.urlopen('http://ai:8002/health', timeout=4))['index_size_tai_lieu'])
")"
[ "${size_tai_lieu:-0}" -gt 0 ] || fail "Chỉ mục tài liệu của dịch vụ AI rỗng (index_size_tai_lieu=${size_tai_lieu})"
ok "25 đồ án nguồn có báo cáo cuối; index_size_tai_lieu=${size_tai_lieu}"
