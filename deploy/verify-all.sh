#!/usr/bin/env bash
# Phase 5 (05-04, D-03): kiểm chứng TOÀN HỆ THỐNG trên bản triển khai đã seed
# bằng một lệnh — chạy tuần tự mọi bộ kiểm thử, đo thời gian từng bước, in
# bảng kết quả và (với --report) ghi kết quả máy đọc được vào
# docs/chuong-4-trien-khai/ket-qua-kiem-thu/ (đã che bí mật).
#
#   --quick   : tình trạng stack + dữ liệu DATA-01/02/03 + smoke-test.sh
#   (mặc định): như --quick, thêm pytest backend, pytest ai-service, e2e-uc1,
#               e2e-uc2-5, e2e-ai, ai-nfr (--json), nfr-he-thong (--json),
#               tools/check-erd-db.py và kiểm tra dữ liệu kiểm thử còn sót
#   --report  : ghi tong-hop.json + nhat-ky-verify-all.log và trang số liệu
#               AI thu-nghiem-ai/04-hieu-nang-va-bao-mat.md (ai-nfr.sh --report)
#   (05-05) mọi chế độ: chữ ký hàng của tài khoản demo (deploy/demo-state.sh --dem)
#               được ghi TRƯỚC các bộ kiểm thử và so lại ở bước cuối "trạng thái
#               demo" — lệch là FAIL. Chế độ đầy đủ đo thêm NFR-16: chạy kịch bản
#               ảnh tools/demo/kich-ban-anh.json --chi-doc qua Chrome headless 1440 px.
#
# Mọi nội dung ghi ra đĩa và in ra màn hình đi qua hàm che: mọi giá trị dài
# >= 8 ký tự của deploy/.env và mọi chuỗi dạng JWT (eyJ….….…) bị thay (T-05-10).
# Thoát khác 0 nếu có bước lỗi; luôn in bảng các bước.
#
# Dùng: bash deploy/verify-all.sh [--quick] [--report]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

COMPOSE=(docker compose -f "${SCRIPT_DIR}/docker-compose.yml")
ENV_FILE="${SCRIPT_DIR}/.env"
OUT_DIR="${REPO_ROOT}/docs/chuong-4-trien-khai/ket-qua-kiem-thu"
AI_REPORT="docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md"
KHOA_SEED="'K18','K19','K20','K21','K22'"
KHOA_KIEM_THU="'K95','K96','K97','K98','K99'"

MODE=full
REPORT=0
BUOC=""

usage() {
  echo "Dùng: bash deploy/verify-all.sh [--quick] [--report]" >&2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --quick) MODE=quick; shift ;;
    --report) REPORT=1; shift ;;
    # Bước nội bộ (được chính script gọi trong bước con, cũng chạy tay được).
    --buoc) BUOC="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

sql() {
  bash "${SCRIPT_DIR}/sql.sh" "$1" | tr -d '\r'
}

ai_health_json() {
  "${COMPOSE[@]}" exec -T api python -c "
import json, urllib.request
print(json.dumps(json.load(urllib.request.urlopen('http://ai:8002/health', timeout=10))))
"
}

# =============================================================================
# Bước nội bộ: tình trạng stack
# =============================================================================
buoc_stack() {
  local ps_json
  ps_json="$("${COMPOSE[@]}" ps -a --format json)" || { echo "FAIL: docker compose ps lỗi"; return 1; }
  python3 - "$ps_json" <<'PY' || return 1
import json, sys
raw = sys.argv[1].strip()
items = json.loads(raw) if raw.startswith("[") else [json.loads(l) for l in raw.splitlines() if l.strip()]
by = {}
for c in items:
    by.setdefault(c["Service"], []).append(c)
bad = []
for svc in ("mysql", "api", "ai"):
    cs = by.get(svc, [])
    if not cs or any(c.get("State") != "running" or c.get("Health") != "healthy" for c in cs):
        bad.append(f"{svc}: {[(c.get('State'), c.get('Health')) for c in cs] or 'không có'}")
    else:
        print(f"OK: {svc} running, healthy")
cs = by.get("apache", [])
if not cs or any(c.get("State") != "running" for c in cs):
    bad.append(f"apache: {[c.get('State') for c in cs] or 'không có'}")
else:
    print("OK: apache running")
for svc in ("ai-db-init", "ai-migrate"):
    cs = by.get(svc, [])
    if not cs or any(c.get("State") != "exited" or int(c.get("ExitCode", 1)) != 0 for c in cs):
        bad.append(f"{svc}: {[(c.get('State'), c.get('ExitCode')) for c in cs] or 'không có'}")
    else:
        print(f"OK: {svc} đã chạy xong (exit 0)")
for b in bad:
    print(f"FAIL: {b}")
sys.exit(1 if bad else 0)
PY
  local offline
  offline="$("${COMPOSE[@]}" exec -T ai printenv HF_HUB_OFFLINE | tr -d '\r')"
  [ "$offline" = "1" ] || { echo "FAIL: service ai không có HF_HUB_OFFLINE=1 (D-02)"; return 1; }
  echo "OK: service ai chạy với HF_HUB_OFFLINE=1 (mô hình tải trước lúc cài đặt)"
  "${COMPOSE[@]}" config --format json | python3 -c "
import json, sys
s = json.load(sys.stdin)['services']['ai']
sys.exit(1 if s.get('ports') else 0)" || { echo "FAIL: service ai publish cổng ra host"; return 1; }
  echo "OK: service ai không publish cổng ra host"
  local h
  h="$(curl -sk -m 10 https://localhost/api/health)"
  printf '%s' "$h" | grep -q '"status":"ok"' || { echo "FAIL: https://localhost/api/health: $h"; return 1; }
  echo "OK: https://localhost/api/health qua Apache: status ok"
}

# =============================================================================
# Bước nội bộ: dữ liệu thử nghiệm DATA-01/02/03 (ghi JSON nếu có DU_LIEU_JSON)
# =============================================================================
buoc_du_lieu() {
  local tk kho khoa_rows health linked n_files
  tk="$(sql "SELECT SUM(vai_tro='SINH_VIEN'), SUM(vai_tro='GIANG_VIEN'), SUM(vai_tro='BO_MON') FROM tai_khoan")" || return 1
  kho="$(sql "SELECT COUNT(*), COALESCE(SUM(trang_thai_index='DA_INDEX'),0), COUNT(DISTINCT khoa) FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN (${KHOA_SEED})")" || return 1
  khoa_rows="$(sql "SELECT khoa, COUNT(*) FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN (${KHOA_SEED}) GROUP BY khoa ORDER BY khoa")" || return 1
  linked="$(sql "SELECT COUNT(*) FROM do_an_kho k JOIN tai_lieu_do_an t ON t.de_tai_id = k.de_tai_id AND t.loai = 'BAO_CAO_CUOI' WHERE k.nguon='IMPORT' AND k.khoa IN (${KHOA_SEED})")" || return 1
  health="$(ai_health_json)" || { echo "FAIL: không đọc được /health của dịch vụ AI"; return 1; }
  n_files="$(find "${REPO_ROOT}/seed-data/tai-lieu" -maxdepth 1 -type f \( -name '*.docx' -o -name '*.pdf' \) | wc -l)"
  python3 - "$tk" "$kho" "$khoa_rows" "$linked" "$health" "$n_files" "${REPO_ROOT}/seed-data/manifest.json" "${DU_LIEU_JSON:-}" <<'PY'
import collections, json, sys
tk, kho, khoa_rows, linked, health, n_files, manifest_path, out = sys.argv[1:9]
n_files = int(n_files)
sv, gv, bm = (int(x or 0) for x in tk.split())
kho_n, kho_idx, kho_khoa = (int(x or 0) for x in kho.split())
theo_khoa = {l.split("\t")[0]: int(l.split("\t")[1]) for l in khoa_rows.splitlines() if l.strip()}
h = json.loads(health)
m = json.load(open(manifest_path, encoding="utf-8"))
cap = m["cap"]
d = {
    "sinh_vien": sv,
    "giang_vien": gv,
    "bo_mon": bm,
    "kho_de_tai": kho_n,
    "kho_da_index": kho_idx,
    "kho_so_khoa": kho_khoa,
    "index_tieu_de": int(h.get("index_size_tieu_de", 0)),
    "index_tai_lieu": int(h.get("index_size_tai_lieu", 0)),
    "thieu_embedding": int(h.get("thieu_embedding", 0)),
    "tep_thu_nghiem": int(n_files),
    "cap_trung_lap": len(cap),
    "do_an_nguon_co_bao_cao": int(linked),
    "kho_theo_khoa": theo_khoa,
    "cap_theo_loai": dict(collections.Counter(c["loai"] for c in cap)),
    "cap_theo_tap": dict(collections.Counter(c["tap"] for c in cap)),
    "ten_model": h.get("ten_model"),
}
checks = [
    ("DATA-01", sv == 580 and gv == 70 and bm >= 1, f"{sv} sinh viên, {gv} giảng viên, {bm} Bộ môn (kỳ vọng 580 / 70 / >= 1)"),
    ("DATA-02", kho_n == 300 and kho_idx == 300 and kho_khoa >= 2 and d["index_tieu_de"] >= 300 and d["thieu_embedding"] == 0,
     f"{kho_n} đề tài kho IMPORT K18–K22 ({kho_khoa} khóa), {kho_idx} DA_INDEX; /health index_size_tieu_de={d['index_tieu_de']}, thieu_embedding={d['thieu_embedding']}"),
    ("DATA-03", n_files == 50 and len(cap) == 25 and int(linked) == 25 and d["index_tai_lieu"] > 0 and len(d["cap_theo_loai"]) == 4,
     f"{n_files} tệp trong seed-data/tai-lieu, {len(cap)} cặp thuộc {len(d['cap_theo_loai'])} loại trùng, {linked} đồ án nguồn có báo cáo cuối, index_size_tai_lieu={d['index_tai_lieu']}"),
]
bad = 0
for ma, ok, msg in checks:
    print(("OK: " if ok else "FAIL: ") + f"{ma} — {msg}")
    bad += not ok
if out:
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
sys.exit(1 if bad else 0)
PY
}

# =============================================================================
# Bước nội bộ (05-05): trạng thái demo không bị các bộ kiểm thử làm thay đổi
# =============================================================================
buoc_trang_thai_demo() {
  if [ ! -f "${SCRIPT_DIR}/demo-state.sh" ]; then
    echo "OK: bỏ qua — không có deploy/demo-state.sh"
    return 0
  fi
  [ -s "${TRUOC:-}" ] || { echo "FAIL: không có chữ ký trạng thái demo trước khi chạy (${TRUOC:-chưa đặt TRUOC})"; return 1; }
  local sau
  sau="$(bash "${SCRIPT_DIR}/demo-state.sh" --dem)" || { echo "FAIL: demo-state.sh --dem lỗi"; return 1; }
  python3 - "$TRUOC" "$sau" <<'PY'
import sys
truoc = [l.split("\t") for l in open(sys.argv[1], encoding="utf-8").read().splitlines() if l.strip()]
sau = [l.split("\t") for l in sys.argv[2].splitlines() if l.strip()]
t, s = {r[0]: r[1:] for r in truoc}, {r[0]: r[1:] for r in sau}
lech = [k for k in sorted(set(t) | set(s)) if t.get(k) != s.get(k)]
print("OK: hàng demo trước = sau: " + ", ".join(f"{k} {t[k][0]}" for k in t if k not in lech))
for k in lech:
    print(f"FAIL: hàng demo '{k}' đã đổi: trước {t.get(k)} -> sau {s.get(k)}")
sys.exit(1 if lech else 0)
PY
}

# =============================================================================
# Bước nội bộ (05-05): NFR-16 — màn hình chính ở 1440 px, không lỗi, không tràn
# =============================================================================
buoc_nfr16() {
  local n out j
  if [ ! -f "${SCRIPT_DIR}/demo-state.sh" ] || [ ! -f "${REPO_ROOT}/tools/demo/kich-ban-anh.json" ]; then
    echo "OK: bỏ qua đo trực tiếp — thiếu deploy/demo-state.sh hoặc tools/demo/kich-ban-anh.json"
    return 0
  fi
  n="$(bash "${SCRIPT_DIR}/demo-state.sh" --dem | awk -F'\t' '$1=="de_tai"{print $2}')"
  if [ "${n:-0}" -lt 4 ]; then
    echo "OK: bỏ qua đo trực tiếp — chưa có trạng thái demo (bash deploy/demo-state.sh); NFR-16 lấy từ ket-qua-kiem-thu/anh-chup.json đã commit"
    return 0
  fi
  out="$(mktemp -d)"
  j="${NFR16_JSON:-$out/nfr16.json}"
  if ! python3 "${REPO_ROOT}/tools/demo/chay-kich-ban.py" "${REPO_ROOT}/tools/demo/kich-ban-anh.json" --chi-doc \
      --out-dir "$out" --json "$j"; then
    rm -rf "$out"
    echo "FAIL: kịch bản ảnh (chỉ đọc) lỗi"
    return 1
  fi
  python3 - "$j" <<'PY' || { rm -rf "$out"; return 1; }
import json, struct, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
sizes = {struct.unpack(">II", open(b["anh"], "rb").read()[16:24]) for b in d["buoc"] if b["anh"]}
rong = max(b["do_rong"] or 0 for b in d["buoc"])
bad = [b["id"] for b in d["buoc"] if b["ket_qua"] != "OK"]
ok = not bad and rong <= 1440 and sizes == {(1440, 900)}
print(f"{'OK' if ok else 'FAIL'}: NFR-16 {len(d['buoc'])} màn hình, ảnh {sorted(sizes)}, scrollWidth max {rong} px, lỗi {bad or 'không'}")
sys.exit(0 if ok else 1)
PY
  rm -rf "$out"
  if pgrep -f '[c]hrome.*remote-debugging-port=0' >/dev/null; then
    echo "FAIL: còn tiến trình Chrome debug sau khi chạy"
    return 1
  fi
}

# =============================================================================
# Bước nội bộ: không còn dữ liệu của các bộ kiểm thử tự động
# =============================================================================
buoc_con_sot() {
  local n
  n="$(sql "SELECT COUNT(*) FROM dot_do_an WHERE khoa IN (${KHOA_KIEM_THU})")" || return 1
  [ "$n" = "0" ] || { echo "FAIL: còn ${n} đợt đồ án kiểm thử (K95–K99)"; return 1; }
  echo "OK: không còn đợt đồ án kiểm thử K95–K99"
  n="$(sql "SELECT COUNT(*) FROM do_an_kho WHERE khoa IN (${KHOA_KIEM_THU})")" || return 1
  [ "$n" = "0" ] || { echo "FAIL: còn ${n} bản ghi kho khóa kiểm thử (K95–K99)"; return 1; }
  echo "OK: không còn bản ghi kho khóa kiểm thử K95–K99"
  n="$(sql "SELECT COUNT(*) FROM tai_khoan WHERE bi_khoa = 1")" || return 1
  [ "$n" = "0" ] || { echo "FAIL: còn ${n} tài khoản đang bị khóa"; return 1; }
  echo "OK: không có tài khoản nào bị khóa"
}

case "${BUOC}" in
  "") ;;
  stack) buoc_stack; exit $? ;;
  du-lieu) buoc_du_lieu; exit $? ;;
  con-sot) buoc_con_sot; exit $? ;;
  trang-thai-demo) buoc_trang_thai_demo; exit $? ;;
  nfr-16) buoc_nfr16; exit $? ;;
  *) echo "Bước không hợp lệ: ${BUOC}" >&2; exit 2 ;;
esac

# =============================================================================
# Chạy các bước
# =============================================================================
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
STEPS_TSV="$WORK/buoc.tsv"
: > "$STEPS_TSV"
RUN_T0=$(date +%s)
THOI_DIEM_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Hàm che bí mật (T-05-10): giá trị .env dài >= 8 ký tự -> *** (khóa bí mật)
# hoặc <TEN_KHOA> (khóa không bí mật, vd. SERVER_NAME); chuỗi dạng JWT -> ***.
cat > "$WORK/che.py" <<'PY'
import re, sys
env_path = sys.argv[1]
rep = []
try:
    for line in open(env_path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if len(v) >= 8:
            secret = re.search(r"PASSWORD|SECRET|KEY|TOKEN", k)
            rep.append((v, "***" if secret else f"<{k}>"))
except FileNotFoundError:
    pass
rep.sort(key=lambda kv: -len(kv[0]))
jwt = re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")
for line in sys.stdin:
    for v, r in rep:
        line = line.replace(v, r)
    sys.stdout.write(jwt.sub("***", line))
PY
che() {
  python3 "$WORK/che.py" "$ENV_FILE"
}

# 05-05: chữ ký hàng demo TRƯỚC mọi bộ kiểm thử (so lại ở bước cuối).
if [ -f "${SCRIPT_DIR}/demo-state.sh" ]; then
  bash "${SCRIPT_DIR}/demo-state.sh" --dem > "$WORK/demo-truoc.tsv" 2>&1 || true
fi

FAILED=0
run_step() {
  local ma="$1" ten="$2" to="$3" lenh="$4"
  local i log t0 t1 rc secs status
  i=$(( $(wc -l < "$STEPS_TSV") + 1 ))
  log="$WORK/buoc-$(printf '%02d' "$i")-${ma}.log"
  echo ""
  echo "=== [$i] ${ten}: ${lenh}"
  t0=$(date +%s.%N)
  ( cd "${REPO_ROOT}" && timeout --kill-after=30 "$to" bash -c "$lenh" ) > "$log" 2>&1 < /dev/null
  rc=$?
  t1=$(date +%s.%N)
  secs="$(python3 -c "print(round($t1 - $t0, 1))")"
  if [ "$rc" = "0" ]; then
    status=OK
  else
    status=FAIL
    FAILED=$((FAILED + 1))
    [ "$rc" = "124" ] && echo "(quá thời gian ${to} s)" >> "$log"
  fi
  tail -n 20 "$log" | che | sed 's/^/    /'
  echo "--> ${status} (${secs} s, mã thoát ${rc})"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$i" "$ma" "$ten" "$lenh" "$status" "$secs" "$log" >> "$STEPS_TSV"
}

run_step stack "Tình trạng stack (mysql/api/ai healthy, apache, one-shot exit 0, AI offline)" 120 \
  "bash deploy/verify-all.sh --buoc stack"
run_step du-lieu "Dữ liệu thử nghiệm DATA-01/02/03" 120 \
  "DU_LIEU_JSON='$WORK/du-lieu.json' bash deploy/verify-all.sh --buoc du-lieu"
run_step smoke "Smoke test qua Apache HTTPS" 300 "bash deploy/smoke-test.sh"

if [ "$MODE" = "full" ]; then
  run_step pytest-backend "Pytest Web API (backend)" 1800 "uv --directory backend run pytest -q"
  run_step pytest-ai "Pytest dịch vụ AI (ai-service)" 1800 "uv --directory ai-service run pytest -q"
  run_step e2e-uc1 "E2E UC1 — phân công GVHD, đề xuất/đăng ký/GVHD duyệt đề tài" 600 "bash deploy/e2e-uc1.sh"
  run_step e2e-uc2-5 "E2E UC2–UC5 — đề cương, tiến độ, bảo vệ, lưu kho" 900 "bash deploy/e2e-uc2-5.sh"
  run_step e2e-ai "E2E dịch vụ AI thật (SC1–SC5)" 1200 "bash deploy/e2e-ai.sh"
  if [ "$REPORT" = "1" ]; then
    run_step ai-nfr "Đo NFR-07..NFR-11 dịch vụ AI (kho đầy đủ)" 1800 \
      "bash deploy/ai-nfr.sh --json '$WORK/ai-nfr.json' --report ${AI_REPORT}"
  else
    run_step ai-nfr "Đo NFR-07..NFR-11 dịch vụ AI (kho đầy đủ)" 1800 \
      "bash deploy/ai-nfr.sh --json '$WORK/ai-nfr.json'"
  fi
  run_step nfr-he-thong "Đo NFR hệ thống qua HTTPS (NFR-01..05, 08, 12..15, 17..19)" 900 \
    "bash deploy/nfr-he-thong.sh --json '$WORK/nfr-he-thong.json'"
  run_step erd-db "Đối chiếu ERD với schema thesis_core" 120 "python3 tools/check-erd-db.py"
  run_step con-sot "Không còn dữ liệu kiểm thử (K95–K99, tài khoản khóa)" 120 \
    "bash deploy/verify-all.sh --buoc con-sot"
  run_step nfr-16 "NFR-16 — màn hình chính ở 1440 px qua Chrome headless (chỉ đọc)" 600 \
    "NFR16_JSON='$WORK/nfr16.json' bash deploy/verify-all.sh --buoc nfr-16"
fi
run_step trang-thai-demo "Kiểm tra trạng thái demo không đổi (hàng của tài khoản demo trước/sau)" 120 \
  "TRUOC='$WORK/demo-truoc.tsv' bash deploy/verify-all.sh --buoc trang-thai-demo"

TOTAL=$(( $(date +%s) - RUN_T0 ))

echo ""
echo "=== Kết quả (${MODE}, ${TOTAL} s)"
python3 - "$STEPS_TSV" <<'PY'
import sys
print(f"{'#':3} {'Bước':62} {'KQ':6} {'Giây':>8}")
for row in open(sys.argv[1], encoding="utf-8"):
    i, ma, ten, lenh, st, secs, log = row.rstrip("\n").split("\t")
    print(f"{i:3} {ten[:62]:62} {st:6} {secs:>8}")
PY

if [ "$REPORT" = "1" ]; then
  mkdir -p "$OUT_DIR"
  COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo '?')"
  DIRTY="$(git -C "$REPO_ROOT" status --porcelain -- backend frontend ai-service deploy seed-data 2>/dev/null | wc -l)"
  # Nhật ký đầy đủ (đã che).
  {
    echo "# Nhật ký bash deploy/verify-all.sh --report"
    echo "# commit: ${COMMIT}$([ "$DIRTY" = "0" ] || echo " (+${DIRTY} tệp sản phẩm chưa commit)")"
    echo "# bắt đầu (UTC): ${THOI_DIEM_UTC}; tổng thời gian: ${TOTAL} s"
    echo "# máy: $(nproc) CPU, $(free -g | awk 'NR==2{print $2}') GiB RAM, $(uname -sr)"
    while IFS=$'\t' read -r i ma ten lenh status secs log; do
      echo ""
      echo "================================================================"
      echo "[$i] ${ten}"
      echo "lệnh: ${lenh//$WORK/\$TMP}"
      echo "kết quả: ${status} (${secs} s)"
      echo "----------------------------------------------------------------"
      cat "$log"
    done < "$STEPS_TSV"
  } | che > "$OUT_DIR/nhat-ky-verify-all.log"

  python3 - "$STEPS_TSV" "$WORK" "$OUT_DIR/tong-hop.json" "$COMMIT" "$THOI_DIEM_UTC" "$TOTAL" "$MODE" "$DIRTY" <<'PY'
import json, os, platform, re, sys
steps_tsv, work, out, commit, t_utc, total, mode, dirty = sys.argv[1:9]

def load(name):
    p = os.path.join(work, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

def tom_tat(ma, log):
    lines = [l.rstrip() for l in open(log, encoding="utf-8", errors="replace") if l.strip()]
    if ma.startswith("pytest"):
        for l in reversed(lines):
            if re.search(r"\d+ (passed|failed|error)", l):
                return l.strip("= ").strip()
    oks = sum(1 for l in lines if l.startswith("OK"))
    fails = [l for l in lines if l.startswith("FAIL")]
    if fails:
        return f"{oks} kiểm tra OK; lỗi: {fails[0][:200]}"
    return f"{oks} kiểm tra OK" + (f"; {lines[-1][:160]}" if lines and not lines[-1].startswith("OK") else "")

buoc, status_of = [], {}
for row in open(steps_tsv, encoding="utf-8"):
    i, ma, ten, lenh, st, secs, log = row.rstrip("\n").split("\t")
    lenh = lenh.replace(work, "$TMP")
    buoc.append({"ma": ma, "ten": ten, "lenh": lenh, "trang_thai": st, "giay": float(secs), "tom_tat": tom_tat(ma, log)})
    status_of[ma] = st

pytest_counts = {}
for b in buoc:
    if b["ma"].startswith("pytest"):
        c = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|errors?|deselected)", b["tom_tat"])}
        pytest_counts[b["ma"]] = c
        b["so_test"] = c

du_lieu = load("du-lieu.json") or {}
he_thong = load("nfr-he-thong.json") or {}
ai = load("ai-nfr.json") or {}

def suites_ok(*mas):
    if any(m not in status_of for m in mas):
        return None
    return all(status_of[m] == "OK" for m in mas)

CHI_TIEU = {
    "NFR-01": "HTTP cổng 80 chuyển hướng sang HTTPS 443",
    "NFR-02": "Mật khẩu băm bcrypt cost >= 12, không lộ trong log",
    "NFR-03": "JWT ký bằng khóa từ biến môi trường; token hết hạn -> 401",
    "NFR-04": "Kiểm tra vai trò/quyền sở hữu phía server; sai vai trò -> 403",
    "NFR-05": "Tài khoản bị khóa không đăng nhập được",
    "NFR-06": "Kiểm tra file theo magic bytes; tối đa 20 MB (Apache + Web API)",
    "NFR-07": "Dịch vụ AI không có đường public; thiếu khóa -> 401",
    "NFR-08": "P95 kiểm tra tên đề tài <= 5 s (kho 300 đề tài)",
    "NFR-09": "P95 nộp -> Hoàn tất <= 30 s (20 file)",
    "NFR-10": "API nộp trả phản hồi <= 2 s",
    "NFR-11": "Ingest 1 bản ghi = 1 lần encode",
    "NFR-12": "P95 tra cứu kho / danh sách đề tài <= 1 s",
    "NFR-13": "utf8mb4_vietnamese_ci cho mọi bảng/cột văn bản; schema qua Alembic",
    "NFR-14": "NFC và NFD cho cùng kết quả so sánh",
    "NFR-15": "Client tĩnh, Apache proxy /api, ProxyTimeout > 30 s",
    "NFR-16": "Chrome/Edge desktop, khung 1440 px",
    "NFR-17": "580 tài khoản SV + 70 tài khoản GV",
    "NFR-18": "300 đề tài nhiều khóa, 100% đã ingest vào dịch vụ AI",
    "NFR-19": "50 file thử nghiệm, đủ 4 loại trùng + bảng kiểm chứng",
}

nfr = {}
# (1) NFR đo trực tiếp bởi nfr-he-thong.sh
for ma, v in (he_thong.get("nfr") or {}).items():
    nfr[ma] = {"ma": ma, "chi_tieu": CHI_TIEU.get(ma, v.get("chi_tieu", "")), "cach_do": v["cach_do"],
               "ket_qua": v["ket_qua"], "dat": v["dat"], "nguon": "deploy/nfr-he-thong.sh"}

# (2) NFR do các bộ kiểm thử chứng minh (+ phép đo HTTPS của nfr-he-thong nếu có)
def ghep(ma, mas, cach, kq_suite):
    s = suites_ok(*mas)
    base = nfr.get(ma)
    dat = s if base is None else (None if s is None else (s and base["dat"] is True))
    if base is not None and base["dat"] is False:
        dat = False
    nguon = ", ".join(mas) + (" + deploy/nfr-he-thong.sh" if base else "")
    nfr[ma] = {"ma": ma, "chi_tieu": CHI_TIEU[ma],
               "cach_do": cach + ("; " + base["cach_do"] if base else ""),
               "ket_qua": kq_suite + ("; " + base["ket_qua"] if base else ""),
               "dat": dat, "nguon": nguon}

ok_txt = lambda mas: "; ".join(f"{m}: {status_of.get(m, 'không chạy')}" for m in mas)
ghep("NFR-04", ["pytest-backend", "smoke", "e2e-uc1", "e2e-uc2-5"],
     "403 chéo vai trò trên mọi nhóm route (smoke-test), SV/Bộ môn/GV không phải GVHD duyệt đề tài, SV lớp khác xem/đăng ký đề tài (e2e-uc1 bước g, h), SV/GV khác gọi route không thuộc quyền (e2e-uc2-5), pytest RBAC/ownership",
     ok_txt(["pytest-backend", "smoke", "e2e-uc1", "e2e-uc2-5"]))
ghep("NFR-05", ["pytest-backend"],
     "pytest test_auth::test_locked_account_cannot_login_or_refresh, test_accounts_rbac::test_bomon_lock_blocks_login_and_unlock_restores_it",
     ok_txt(["pytest-backend"]))
ghep("NFR-06", ["pytest-backend", "smoke"],
     "Body 30 MB qua Apache -> 413, 21 MB lọt (smoke-test h); pytest test_outline_flow::test_upload_rejected_before_any_version (sai magic bytes/đuôi giả), test_body_limit",
     ok_txt(["pytest-backend", "smoke"]))

# (3) NFR dịch vụ AI (ai-nfr.sh --json), NFR-07 thêm e2e-ai ai_security
if ai:
    n7 = ai["nfr_07"]
    s7 = suites_ok("e2e-ai")
    nfr["NFR-07"] = {"ma": "NFR-07", "chi_tieu": CHI_TIEU["NFR-07"],
                     "cach_do": "Host gọi 127.0.0.1:8002; /check-title thiếu/sai/đúng X-API-Key trong mạng nội bộ; tìm route AI trong ntma.conf và qua https://localhost; tài khoản DB thesis_ai đọc thesis_core; e2e-ai ai_security",
                     "ket_qua": f"host không tới được 8002; mã {n7['codes']}; Apache trả {n7['apache_code']} (SPA, không route); thesis_ai DB {n7['db']}; e2e-ai: {status_of.get('e2e-ai', 'không chạy')}",
                     "dat": bool(n7["dat"]) and s7 is not False, "nguon": "deploy/ai-nfr.sh, e2e-ai"}
    n8 = ai["nfr_08"]
    trong = f"{n8['n']} lời gọi trực tiếp POST /check-title trong mạng nội bộ, kho {ai.get('index_size_tieu_de')} tiêu đề"
    kq8 = f"P95 {n8['p95_s']:.3f} s (trực tiếp)"
    base8 = nfr.get("NFR-08")
    nfr["NFR-08"] = {"ma": "NFR-08", "chi_tieu": CHI_TIEU["NFR-08"],
                     "cach_do": trong + ("; " + base8["cach_do"] if base8 else ""),
                     "ket_qua": kq8 + ("; " + base8["ket_qua"] if base8 else ""),
                     "dat": bool(n8["dat"]) and (base8 is None or base8["dat"] is True),
                     "nguon": "deploy/ai-nfr.sh" + (" + deploy/nfr-he-thong.sh" if base8 else "")}
    n9 = ai["nfr_09"]
    nfr["NFR-09"] = {"ma": "NFR-09", "chi_tieu": CHI_TIEU["NFR-09"],
                     "cach_do": f"Nộp lần lượt {n9['n']} file B khác nhau qua Apache HTTPS, thăm dò trạng thái mỗi 0,25 s",
                     "ket_qua": f"P95 {n9['p95_s']:.2f} s, max {n9['max_s']:.2f} s; {n9['hoan_tat']}/{n9['n']} Hoàn tất, {n9['loi']} lỗi",
                     "dat": bool(n9["dat"]), "nguon": "deploy/ai-nfr.sh"}
    n10 = ai["nfr_10"]
    nfr["NFR-10"] = {"ma": "NFR-10", "chi_tieu": CHI_TIEU["NFR-10"],
                     "cach_do": "Thời gian phản hồi 202 của POST /api/outlines/{id}/submit (cùng 20 lần nộp)",
                     "ket_qua": f"max {n10['max_s']:.3f} s, P95 {n10['p95_s']:.3f} s",
                     "dat": bool(n10["dat"]), "nguon": "deploy/ai-nfr.sh"}
    n11 = ai["nfr_11"]
    nfr["NFR-11"] = {"ma": "NFR-11", "chi_tieu": CHI_TIEU["NFR-11"],
                     "cach_do": "encode_calls (/health) trước và sau khi Bộ môn thêm 1 bản ghi kho (chờ DA_INDEX)",
                     "ket_qua": f"+{n11['encode_calls_delta']} lần encode",
                     "dat": bool(n11["dat"]), "nguon": "deploy/ai-nfr.sh"}
# NFR-16 (05-05): số đo trực tiếp của bước nfr-16 nếu có, không thì ảnh chụp đã commit.
n16 = load("nfr16.json")
nguon16 = "verify-all bước nfr-16 (tools/demo/chay-kich-ban.py --chi-doc)"
if n16 is None:
    p16 = os.path.join(os.path.dirname(out), "anh-chup.json")
    if os.path.exists(p16):
        n16 = json.load(open(p16, encoding="utf-8"))
        nguon16 = "docs/chuong-4-trien-khai/ket-qua-kiem-thu/anh-chup.json (tools/demo/chay-kich-ban.py)"
if n16:
    b16 = n16["buoc"]
    rong16 = max((b["do_rong"] or 0) for b in b16) if b16 else 0
    loi16 = [b["id"] for b in b16 if b["ket_qua"] != "OK"]
    uc16 = sorted({b["id"].split("-")[0] for b in b16})
    vt16 = sorted({("SV" if (b["vai_tro"] or "").startswith("DTC") else "GV" if (b["vai_tro"] or "").startswith("GV") else "Bộ môn" if b["vai_tro"] else "khách") for b in b16})
    nfr["NFR-16"] = {"ma": "NFR-16", "chi_tieu": CHI_TIEU["NFR-16"],
                     "cach_do": f"Chrome headless (CDP) khung 1440×900 qua Apache HTTPS, {len(b16)} màn hình ({', '.join(uc16)}; vai trò {', '.join(vt16)}); mỗi màn hình đo document.documentElement.scrollWidth, bắt exception JS, lỗi console, HTTP >= 400 ngoài dự kiến",
                     "ket_qua": f"{len(b16) - len(loi16)}/{len(b16)} màn hình OK, scrollWidth max {rong16} px, lỗi: {', '.join(loi16) or 'không'} (đo lúc {n16.get('thoi_diem_utc')})",
                     "dat": (not loi16) and rong16 <= 1440 and len(b16) >= 20, "nguon": nguon16}
else:
    nfr["NFR-16"] = {"ma": "NFR-16", "chi_tieu": CHI_TIEU["NFR-16"],
                     "cach_do": "Chụp các màn hình chính bằng Chrome headless ở 1440 px (tools/demo/chay-kich-ban.py)",
                     "ket_qua": "Chưa đo", "dat": None, "nguon": "plan 05-05"}
for i in range(1, 20):
    ma = "NFR-%02d" % i
    nfr.setdefault(ma, {"ma": ma, "chi_tieu": CHI_TIEU[ma], "cach_do": "", "ket_qua": "Chưa đo (bước đo không chạy)", "dat": None, "nguon": ""})

mem_total = 0
try:
    mem_total = int(open("/proc/meminfo").read().split()[1]) / 1048576
except Exception:
    pass
os_name = platform.platform()
try:
    for l in open("/etc/os-release", encoding="utf-8"):
        if l.startswith("PRETTY_NAME="):
            os_name = l.split("=", 1)[1].strip().strip('"') + f" (kernel {platform.release()})"
except Exception:
    pass
res = {
    "lenh": "bash deploy/verify-all.sh --report" if mode == "full" else "bash deploy/verify-all.sh --quick --report",
    "che_do": mode,
    "commit": commit,
    "tep_san_pham_chua_commit": int(dirty),
    "thoi_diem_utc": t_utc,
    "tong_giay": int(total),
    "may": {"nproc": os.cpu_count(), "ram_gb": round(mem_total, 1), "os": os_name,
            "cpu": next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "")},
    "buoc": buoc,
    "pytest": pytest_counts,
    "du_lieu": du_lieu,
    "nfr": [nfr["NFR-%02d" % i] for i in range(1, 20)],
    "ai_nfr_chi_tiet": ai or None,
}
json.dump(res, open(out + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Đã ghi {out}")
PY
  che < "$OUT_DIR/tong-hop.json.tmp" > "$OUT_DIR/tong-hop.json"
  rm -f "$OUT_DIR/tong-hop.json.tmp"
  echo "Kết quả: docs/chuong-4-trien-khai/ket-qua-kiem-thu/{tong-hop.json,nhat-ky-verify-all.log}"
  python3 - "$OUT_DIR/tong-hop.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print()
print(f"{'NFR':7} {'Đạt?':10} Kết quả")
for n in d["nfr"]:
    dat = {True: "Đạt", False: "KHÔNG ĐẠT", None: "Chưa đo"}[n["dat"]]
    print(f"{n['ma']:7} {dat:10} {n['ket_qua'][:110]}")
PY
fi

if [ "$FAILED" -gt 0 ]; then
  echo "FAIL: ${FAILED} bước lỗi"
  exit 1
fi
echo "OK: mọi bước đạt (${MODE}, ${TOTAL} s)"
