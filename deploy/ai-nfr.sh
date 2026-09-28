#!/usr/bin/env bash
# Phase 4 (04-06): đo NFR-07..NFR-11 của dịch vụ AI trên stack compose ĐANG CHẠY
# (docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md):
#   NFR-07 — cổng AI không mở ra host, không có route Apache, thiếu/sai khóa
#            -> 401, tài khoản DB thesis_ai không đọc được thesis_core.
#   NFR-08 — 20 lời gọi trực tiếp POST /check-title (trong mạng nội bộ, kèm khóa)
#            với kho 300 đề tài đã ingest: P95 <= 5 s.
#   NFR-09 — nộp lần lượt 20 file B khác nhau của seed-data qua Apache; thời gian
#            nộp -> HOAN_TAT (thăm dò mỗi 0,25 s): P95 <= 30 s, không có LOI.
#   NFR-10 — thời gian phản hồi của API nộp (202): lớn nhất <= 2 s.
#   NFR-11 — thêm 1 bản ghi kho -> encode_calls của dịch vụ AI tăng đúng 1.
#   Bộ nhớ — container ai: đỉnh cgroup < 2048 MiB và không bị OOM-kill.
# Dùng: bash deploy/ai-nfr.sh [--report docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md]
# (sau `bash deploy/seed-ai.sh`). Phase 5 chạy lại đúng lệnh này trên server.
#
# Tài khoản dành riêng: bomon, DTC225200095 (SV), GV023 (GVHD) — dùng chung với
# e2e-ai (K97) nên KHÔNG chạy song song hai script; khóa kiểm thử K96. Dọn dẹp
# (trap, kể cả khi lỗi): purge vector DOCUMENT/TOPIC/ARCHIVE đã tạo, xóa file đã
# nộp, xóa dữ liệu K96 theo thứ tự khóa ngoại.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BASE="${BASE_URL:-https://localhost}"
COMPOSE=(docker compose -f "${SCRIPT_DIR}/docker-compose.yml")
REPORT=""
N_TITLE=20
N_FILES=20

while [ $# -gt 0 ]; do
  case "$1" in
    --report) REPORT="$2"; shift 2 ;;
    *) echo "Dùng: bash deploy/ai-nfr.sh [--report PATH]" >&2; exit 2 ;;
  esac
done

fail() {
  echo "FAIL: $1"
  exit 1
}

ok() {
  echo "OK: $1"
}

TMP="$(mktemp -d)"
START_UTC="$(date -u +%Y-%m-%dT%H:%M:%S)"
KQ="$TMP/kq.env"          # key=value — kết quả đo, đọc lại khi viết báo cáo
: > "$KQ"
DOT_DO_AN_ID=""
KHO_ID=""

record() {
  printf '%s=%s\n' "$1" "$2" >> "$KQ"
}

sql() {
  DB=thesis_core bash "${SCRIPT_DIR}/sql.sh" "$1"
}

call() {
  local method="$1" path="$2" token="$3"
  shift 3
  curl -sk -o "$TMP/body" -w '%{http_code}' -X "$method" "$BASE$path" \
    -H "Authorization: Bearer ${token}" "$@"
}

jget() {
  python3 -c "
import json
d = json.load(open('$TMP/body'))
print($1)
" 2>/dev/null
}

cleanup() {
  if [ -n "${DOT_DO_AN_ID}" ]; then
    local topic_ids doc_ids files ten
    topic_ids="$(sql "SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID}" 2>/dev/null | paste -sd, - || true)"
    doc_ids="$(sql "SELECT t.id FROM tai_lieu_do_an t JOIN de_tai dt ON dt.id = t.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID}" 2>/dev/null | paste -sd, - || true)"
    # T-04-27: không để lại vector mồ côi trong chỉ mục AI.
    if [ -n "${doc_ids}" ]; then
      "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai DOCUMENT --ids "${doc_ids}" >/dev/null 2>&1 || true
    fi
    if [ -n "${topic_ids}" ]; then
      "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai TOPIC --ids "${topic_ids}" >/dev/null 2>&1 || true
    fi
    files="$(sql "SELECT t.ten_luu_tru FROM tai_lieu_do_an t JOIN de_tai dt ON dt.id = t.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID}" 2>/dev/null || true)"
    while IFS= read -r ten; do
      [ -z "$ten" ] && continue
      "${COMPOSE[@]}" exec -T api rm -f "/data/uploads/${ten}" </dev/null >/dev/null 2>&1 || true
    done <<<"${files}"
  fi
  if [ -n "${KHO_ID}" ]; then
    "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai ARCHIVE --ids "${KHO_ID}" >/dev/null 2>&1 || true
    sql "DELETE FROM do_an_kho WHERE id = ${KHO_ID};" >/dev/null 2>&1 || true
  fi
  sql "DELETE FROM thong_bao WHERE tai_khoan_id IN (SELECT id FROM tai_khoan WHERE ma_dang_nhap IN ('DTC225200095','GV023')) AND thoi_diem >= '${START_UTC}';" >/dev/null 2>&1 || true
  if [ -n "${DOT_DO_AN_ID}" ]; then
    sql "DELETE ct FROM chi_tiet_trung_lap ct JOIN ket_qua_kiem_tra_trung_lap kq ON kq.id = ct.ket_qua_id JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    sql "DELETE kq FROM ket_qua_kiem_tra_trung_lap kq JOIN de_tai dt ON dt.id = kq.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    sql "DELETE l FROM luot_duyet_de_cuong l JOIN de_cuong dc ON dc.id = l.de_cuong_id JOIN de_tai dt ON dt.id = dc.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    sql "DELETE t FROM tai_lieu_do_an t JOIN de_tai dt ON dt.id = t.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    sql "DELETE dc FROM de_cuong dc JOIN de_tai dt ON dt.id = dc.de_tai_id WHERE dt.dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    sql "DELETE FROM de_tai WHERE dot_do_an_id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
    sql "DELETE FROM dot_do_an WHERE id = ${DOT_DO_AN_ID};" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT

health() {
  "${COMPOSE[@]}" exec -T api python -c "
import json, urllib.request
h = json.load(urllib.request.urlopen('http://ai:8002/health', timeout=4))
print($1)
"
}

AI_CID="$("${COMPOSE[@]}" ps -q ai)"
[ -n "$AI_CID" ] || fail "Container ai không chạy"

# --- Môi trường đo -------------------------------------------------------------
[ "$(health 'h["status"]')" = "ok" ] || fail "Dịch vụ AI chưa sẵn sàng"
n_kho="$(sql "SELECT COUNT(*) FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN ('K18','K19','K20','K21','K22') AND trang_thai_index='DA_INDEX'")"
[ "$n_kho" -ge 300 ] || fail "Chưa seed — chạy bash deploy/seed-ai.sh (mới có ${n_kho}/300 đề tài kho DA_INDEX)"
record so_cpu "$(nproc)"
record ram_mib "$(free -m | awk 'NR==2{print $2}')"
record cpu_model "$(awk -F': ' '/model name/{print $2; exit}' /proc/cpuinfo)"
record ten_model "$(health 'h["ten_model"]')"
record profile "$(docker exec "$AI_CID" printenv AI_MODEL_PROFILE)"
record torch_threads "$(docker exec "$AI_CID" printenv TORCH_THREADS)"
record index_size_tieu_de "$(health 'h["index_size_tieu_de"]')"
record index_size_tai_lieu "$(health 'h["index_size_tai_lieu"]')"
record ngay "$(date +%Y-%m-%d)"
ok "Môi trường: $(nproc) CPU, $(free -m | awk 'NR==2{print $2}') MiB RAM, kho $(health 'h["index_size_tieu_de"]') tiêu đề / $(health 'h["index_size_tai_lieu"]') câu tài liệu"

# --- NFR-07 (AISV-01) ---------------------------------------------------------
nfr07_ok=1
if curl -s -m 3 -o /dev/null "http://127.0.0.1:8002/health"; then nfr07_ok=0; echo "FAIL: cổng 8002 truy cập được từ host"; fi
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
[ "$codes" = "401 401 200" ] || { nfr07_ok=0; echo "FAIL: X-API-Key thiếu/sai/đúng -> ${codes}"; }
apache_route=0
grep -Eq '8002|//ai[:/]' "${SCRIPT_DIR}/apache/ntma.conf" && apache_route=1
apache_code="$(curl -sk -o "$TMP/apache-ai" -w '%{http_code}' -X POST "$BASE/check-title" -H 'Content-Type: application/json' -d '{"text":"x"}')"
grep -q '"matches"\|API key nội bộ' "$TMP/apache-ai" && apache_route=1
[ "$apache_route" = "0" ] || { nfr07_ok=0; echo "FAIL: Apache có route tới dịch vụ AI"; }
db_probe="$("${COMPOSE[@]}" exec -T ai python -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    try:
        conn.execute(text('SELECT COUNT(*) FROM thesis_core.tai_khoan')).scalar()
        print('ALLOWED')
    except Exception:
        print('DENIED')
" 2>/dev/null | tail -1)"
[ "$db_probe" = "DENIED" ] || { nfr07_ok=0; echo "FAIL: tài khoản DB thesis_ai đọc được thesis_core"; }
record nfr07_ok "$nfr07_ok"
record nfr07_codes "$codes"
record nfr07_apache_code "$apache_code"
record nfr07_db "$db_probe"
[ "$nfr07_ok" = "1" ] && ok "NFR-07: host không tới được 8002; thiếu/sai/đúng khóa = ${codes}; Apache không route (POST /check-title -> ${apache_code} SPA); thesis_ai DB user ${db_probe} trên thesis_core"

# --- NFR-08 (AISV-03) ---------------------------------------------------------
nguong_ten="$(sql "SELECT gia_tri FROM cau_hinh_nguong WHERE loai='NGUONG_TEN_DE_TAI'")"
title_ms="$("${COMPOSE[@]}" exec -T -e N="${N_TITLE}" -e NGUONG="${nguong_ten}" api python - <<'PY'
import csv, json, os, time, urllib.request
rows = list(csv.DictReader(open("/seed-data/truy-van-ten-de-tai.csv", encoding="utf-8-sig")))[: int(os.environ["N"])]
key = os.environ["AI_API_KEY"]
out = []
for r in rows:
    body = json.dumps({"text": r["ten_truy_van"], "top_k": 5, "nguong": float(os.environ["NGUONG"])}).encode()
    req = urllib.request.Request("http://ai:8002/check-title", data=body, headers={"Content-Type": "application/json", "X-API-Key": key}, method="POST")
    t = time.perf_counter()
    urllib.request.urlopen(req, timeout=10).read()
    out.append(round((time.perf_counter() - t) * 1000, 1))
print(json.dumps(out))
PY
)"
record nfr08_ms "$title_ms"

# --- NFR-09 / NFR-10 (AISV-04, AISV-06) ---------------------------------------
TOKEN_BOMON="$(bash "${SCRIPT_DIR}/api-login.sh" bomon)"
TOKEN_SV="$(bash "${SCRIPT_DIR}/api-login.sh" DTC225200095)"
TOKEN_GV="$(bash "${SCRIPT_DIR}/api-login.sh" GV023)"

[ "$(call GET /api/dashboard/sinh-vien "$TOKEN_SV")" = "200" ] || fail "Không đọc được dashboard DTC225200095"
[ "$(jget '1 if d.get("de_tai") else 0')" = "0" ] || fail "DTC225200095 đang có đề tài hoạt động (e2e-ai đang chạy?) — dọn rồi chạy lại"

[ "$(call POST /api/cohorts "$TOKEN_BOMON" -H 'Content-Type: application/json' \
  -d '{"ten_dot":"Đợt đo hiệu năng AI","khoa":"K96","nam_hoc":"2026-2027","ngay_bat_dau":"2026-01-01"}')" = "201" ] \
  || fail "Không tạo được đợt K96: $(cat "$TMP/body")"
DOT_DO_AN_ID="$(jget 'd["id"]')"
python3 -c 'import json,sys; print(json.dumps({"dot_do_an_id": int(sys.argv[1]), "ten_de_tai": "Đo hiệu năng kiểm tra trùng lặp tài liệu của hệ thống quản lý đồ án", "linh_vuc": "Công nghệ phần mềm", "gui": True}, ensure_ascii=False))' "$DOT_DO_AN_ID" > "$TMP/topic.json"
[ "$(call POST /api/topics "$TOKEN_SV" -H 'Content-Type: application/json' --data-binary "@$TMP/topic.json")" = "201" ] \
  || fail "DTC225200095 không tạo được đề tài K96: $(cat "$TMP/body")"
TOPIC_ID="$(jget 'd["id"]')"
call GET /api/lecturers "$TOKEN_BOMON" >/dev/null
GV_ID="$(jget 'next((g["id"] for g in d if g.get("ma_giang_vien") == "GV023"), "")')"
[ "$(call POST "/api/topic-approvals/${TOPIC_ID}/approve" "$TOKEN_BOMON" -H 'Content-Type: application/json' -d "{\"giang_vien_id\":${GV_ID}}")" = "200" ] \
  || fail "Bộ môn không duyệt được đề tài K96: $(cat "$TMP/body")"
ok "Đợt K96 (id=${DOT_DO_AN_ID}), đề tài ${TOPIC_ID} của DTC225200095, GVHD GV023"

mem_before="$(docker stats --no-stream --format '{{.MemUsage}}' "$AI_CID" | awk '{print $1}')"
python3 - "$BASE" "$TOKEN_SV" "$TOKEN_GV" "$TOPIC_ID" "$REPO_ROOT" "$N_FILES" "$TMP/nfr09.tsv" <<'PY' || fail "Vòng đo NFR-09/NFR-10 lỗi"
import json, os, ssl, sys, time, urllib.error, urllib.request, uuid
base, tok_sv, tok_gv, topic, root, n, out = sys.argv[1:8]
ctx = ssl._create_unverified_context()
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

def req(method, path, token, body=None, ctype=None):
    headers = {"Authorization": f"Bearer {token}"}
    if ctype:
        headers["Content-Type"] = ctype
    r = urllib.request.Request(base + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=ctx, timeout=60) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

manifest = json.load(open(f"{root}/seed-data/manifest.json", encoding="utf-8"))
files = [f"{root}/seed-data/{c['B']['tep']}" for c in manifest["cap"]][: int(n)]
rows = []
for i, path in enumerate(files, 1):
    name = os.path.basename(path)
    boundary = uuid.uuid4().hex
    ct = DOCX if name.endswith(".docx") else "application/pdf"
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: {ct}\r\n\r\n").encode() + open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    t0 = time.perf_counter()
    status, data = req("POST", f"/api/outlines/{topic}/submit", tok_sv, body, f"multipart/form-data; boundary={boundary}")
    t_resp = time.perf_counter() - t0
    if status != 202:
        print(f"{name}: nộp trả {status}: {data}", file=sys.stderr); sys.exit(1)
    doc_id = data["phien_ban"][0]["tai_lieu"]["id"]
    trang = "DANG_KIEM_TRA"
    while time.perf_counter() - t0 < 60:
        status, d = req("GET", f"/api/documents/{doc_id}/check", tok_sv)
        trang = d["trang_thai"] if status == 200 else f"HTTP{status}"
        if trang in ("HOAN_TAT", "LOI"):
            break
        time.sleep(0.25)
    t_done = time.perf_counter() - t0
    rows.append([str(i), name, f"{t_resp:.3f}", f"{t_done:.2f}", trang, str(d.get("ty_le_tong")), str(len(d.get("chi_tiet") or []))])
    print(f"  {i:2d}. {name}: nộp {t_resp:.3f}s, HOAN_TAT sau {t_done:.2f}s ({trang}, {d.get('ty_le_tong')}%)", file=sys.stderr)
    if trang not in ("HOAN_TAT", "LOI"):
        break
    status, data = req("POST", f"/api/outlines/{topic}/review", tok_gv,
                       json.dumps({"tai_lieu_do_an_id": doc_id, "ket_qua": "YEU_CAU_SUA", "nhan_xet": "Đo hiệu năng: nộp phiên bản kế tiếp"}).encode(),
                       "application/json")
    if status != 200:
        print(f"{name}: GVHD yêu cầu sửa trả {status}: {data}", file=sys.stderr); sys.exit(1)
with open(out, "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write("\t".join(r) + "\n")
PY
mem_after="$(docker stats --no-stream --format '{{.MemUsage}}' "$AI_CID" | awk '{print $1}')"

# --- NFR-11 (AISV-02) ---------------------------------------------------------
before="$(health 'h["encode_calls"]')"
[ "$(call POST /api/archive "$TOKEN_BOMON" -H 'Content-Type: application/json' \
  -d '{"khoa":"K96","ten_de_tai":"Xây dựng hệ thống quản lý kho vật tư y tế cho bệnh viện đa khoa tuyến huyện"}')" = "201" ] \
  || fail "Bộ môn không thêm được bản ghi kho K96: $(cat "$TMP/body")"
KHO_ID="$(jget 'd["id"]')"
deadline=$((SECONDS + 30))
until [ "$(call GET "/api/archive/${KHO_ID}" "$TOKEN_BOMON" >/dev/null; jget 'd["trang_thai_index"]')" = "DA_INDEX" ]; do
  [ "$SECONDS" -lt "$deadline" ] || fail "Bản ghi kho ${KHO_ID} chưa DA_INDEX sau 30 s"
  sleep 1
done
after="$(health 'h["encode_calls"]')"
record nfr11_before "$before"
record nfr11_after "$after"

# --- Bộ nhớ container ai ------------------------------------------------------
record mem_before "$mem_before"
record mem_after "$mem_after"
record mem_peak_bytes "$(docker exec "$AI_CID" cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo 0)"
record mem_limit_bytes "$(docker inspect -f '{{.HostConfig.Memory}}' "$AI_CID")"
record oom_killed "$(docker inspect -f '{{.State.OOMKilled}}' "$AI_CID")"
record restart_count "$(docker inspect -f '{{.RestartCount}}' "$AI_CID")"

# --- Tổng hợp + báo cáo -------------------------------------------------------
python3 - "$KQ" "$TMP/nfr09.tsv" "${REPORT}" "$N_FILES" <<'PY'
import json, math, sys
kq = {}
for line in open(sys.argv[1], encoding="utf-8"):
    k, _, v = line.rstrip("\n").partition("=")
    kq[k] = v
rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[2], encoding="utf-8") if l.strip()]
report, n_files = sys.argv[3], int(sys.argv[4])

def p95(xs):
    s = sorted(xs)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)]

def mib(v):
    v = v.strip()
    for unit, f in (("GiB", 1024), ("MiB", 1), ("KiB", 1 / 1024)):
        if v.endswith(unit):
            return float(v[: -len(unit)]) * f
    return float(v) / 1048576

title = json.loads(kq["nfr08_ms"])
submit = [float(r[2]) for r in rows]
done = [float(r[3]) for r in rows]
states = [r[4] for r in rows]
peak = int(kq["mem_peak_bytes"] or 0) / 1048576
limit = int(kq["mem_limit_bytes"]) / 1048576
delta11 = int(kq["nfr11_after"]) - int(kq["nfr11_before"])
res = {
    "NFR-07": kq["nfr07_ok"] == "1",
    "NFR-08": len(title) == 20 and p95(title) <= 5000,
    "NFR-09": len(rows) == n_files and all(s == "HOAN_TAT" for s in states) and p95(done) <= 30,
    "NFR-10": len(rows) == n_files and max(submit) <= 2,
    "NFR-11": delta11 == 1,
    "MEM": 0 < peak < 2048 and kq["oom_killed"] == "false",
}
dat = lambda b: "Đạt" if b else "**Không đạt**"
lines = [
    ("NFR-07", "Dịch vụ AI không có đường public; thiếu khóa -> 401",
     "Host gọi 127.0.0.1:8002; trong mạng nội bộ gọi /check-title thiếu / sai / đúng X-API-Key; tìm route trong ntma.conf và POST https://localhost/check-title; tài khoản DB thesis_ai đọc thesis_core",
     f"Host không kết nối được; mã {kq['nfr07_codes']}; không có route (Apache trả {kq['nfr07_apache_code']} là trang SPA); thesis_core: {kq['nfr07_db']}"),
    ("NFR-08", "P95 kiểm tra tên đề tài ≤ 5 s",
     f"{len(title)} lời gọi trực tiếp POST /check-title (trong container api, kèm khóa), kho {kq['index_size_tieu_de']} tiêu đề",
     f"P50 {sorted(title)[len(title)//2]:.0f} ms, **P95 {p95(title):.0f} ms**, max {max(title):.0f} ms"),
    ("NFR-09", "P95 nộp -> Hoàn tất ≤ 30 s",
     f"Nộp lần lượt {len(rows)} file B khác nhau qua Apache, thăm dò GET /api/documents/{{id}}/check mỗi 0,25 s",
     f"P50 {sorted(done)[len(done)//2]:.2f} s, **P95 {p95(done):.2f} s**, max {max(done):.2f} s; {states.count('HOAN_TAT')}/{len(rows)} HOAN_TAT, {states.count('LOI')} LOI"),
    ("NFR-10", "API nộp trả phản hồi ≤ 2 s",
     "Thời gian phản hồi 202 của POST /api/outlines/{id}/submit (cùng 20 lần nộp)",
     f"P95 {p95(submit):.3f} s, **max {max(submit):.3f} s**"),
    ("NFR-11", "Ingest 1 bản ghi = 1 lần encode",
     "encode_calls (/health) trước và sau khi Bộ môn thêm 1 bản ghi kho (chờ DA_INDEX)",
     f"{kq['nfr11_before']} -> {kq['nfr11_after']} (**+{delta11}**)"),
    ("Bộ nhớ", f"Container ai < {limit:.0f} MiB, không OOM",
     "docker stats trước/sau vòng NFR-09; đỉnh cgroup memory.peak; State.OOMKilled",
     f"{kq['mem_before']} -> {kq['mem_after']}; **đỉnh {peak:.0f} MiB**; OOMKilled={kq['oom_killed']}"),
]
print()
print(f"{'NFR':8} {'Kết quả':70} Đạt?")
for (nfr, _, _, kqua), key in zip(lines, res):
    print(f"{nfr:8} {kqua.replace('**', '')[:70]:70} {'Đạt' if res[key] else 'KHÔNG ĐẠT'}")

if report:
    md = [
        "## 4.x.4 Hiệu năng và bảo mật của dịch vụ kiểm tra trùng lặp",
        "",
        "> **Mã PI:** 3.4, 4.1 — **Yêu cầu:** AISV-01, AISV-02, AISV-03, AISV-06 (NFR-07..NFR-11)",
        "",
        f"> Số liệu trong trang này do `bash deploy/ai-nfr.sh --report {report}` đo và ghi tự động ngày {kq['ngay']} — không sửa tay.",
        "",
        "### Mục tiêu",
        "",
        "Kiểm chứng các yêu cầu phi chức năng NFR-07..NFR-11 (mục 2.4, `docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md`) của dịch vụ AI trên stack triển khai thật (Apache → Web API → dịch vụ AI, MySQL), với kho dữ liệu thử nghiệm đã seed đủ (DATA-02, DATA-03).",
        "",
        "### Môi trường đo",
        "",
        "| Thành phần | Giá trị |",
        "|---|---|",
        f"| Máy | Máy phát triển dùng chung (không phải server triển khai) — {kq['so_cpu']} CPU logic ({kq['cpu_model']}), RAM {int(kq['ram_mib']) / 1024:.1f} GiB, chạy đồng thời các ứng dụng khác |",
        f"| Dịch vụ AI | Container `ai` (CPU, `TORCH_THREADS={kq['torch_threads']}`, trần bộ nhớ {limit:.0f} MiB), hồ sơ mô hình `{kq['profile']}` — `{kq['ten_model']}` |",
        f"| Kho đã index | {kq['index_size_tieu_de']} tiêu đề (300 đề tài kho K18–K22) · {kq['index_size_tai_lieu']} câu tài liệu (25 đồ án nguồn có báo cáo cuối) |",
        "| Đường đi của request | NFR-08: gọi thẳng dịch vụ AI trong mạng nội bộ (không tính độ trễ mạng client, đúng phương pháp của NFR-08); NFR-09/10: qua Apache HTTPS → Web API → BackgroundTasks → dịch vụ AI |",
        "",
        "### Kết quả",
        "",
        "| NFR | Chỉ tiêu | Cách đo | Kết quả đo | Đạt? |",
        "|---|---|---|---|---|",
    ]
    for (nfr, chi_tieu, cach, kqua), key in zip(lines, res):
        md.append(f"| {nfr} | {chi_tieu} | {cach} | {kqua} | {dat(res[key])} |")
    md += [
        "",
        "### Chi tiết NFR-09 / NFR-10 theo từng file",
        "",
        "Mỗi file là một phiên bản đề cương mới của cùng một đề tài (GVHD yêu cầu sửa giữa hai lần nộp); các phiên bản trước của đề tài nằm trong danh sách loại trừ nên không bao giờ khớp với nhau. Tỷ lệ là tỷ lệ tương đồng tổng hợp do dịch vụ AI trả về (so với 25 đồ án nguồn và các tài liệu đã nộp trước đó).",
        "",
        "| # | File | Phản hồi nộp (s) | Nộp → Hoàn tất (s) | Trạng thái | Tỷ lệ (%) | Số đoạn trùng |",
        "|---:|---|---:|---:|---|---:|---:|",
    ]
    for r in rows:
        md.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |")
    md += [
        "",
        f"Thời gian NFR-08 từng lời gọi (ms): {', '.join(f'{x:.0f}' for x in title)}.",
        "",
        "### Nhận xét",
        "",
        "- Kiểm tra tài liệu chạy nền: API nộp trả 202 ngay sau khi lưu file và trích xuất văn bản, nên thời gian phản hồi (NFR-10) không phụ thuộc thời gian suy luận của mô hình.",
        "- Thời gian nộp → Hoàn tất gồm độ phân giải thăm dò 0,25 s; phần lớn còn lại là thời gian mã hóa các câu của tài liệu nộp trên CPU (tài liệu dài — báo cáo cuối — tốn nhiều hơn đề cương).",
        "- Embedding của kho được tính một lần lúc ingest và giữ trong chỉ mục FAISS trong bộ nhớ; thêm một bản ghi chỉ mã hóa đúng bản ghi đó (NFR-11).",
        "- Chất lượng phát hiện (tỷ lệ cảnh báo đúng/sai trên các cặp có chủ đích) được trình bày ở mục 4.x.3 — [03-hieu-chinh-nguong.md](03-hieu-chinh-nguong.md).",
        "",
        "### Chạy lại",
        "",
        "```bash",
        "bash deploy/seed-ai.sh          # nếu kho chưa seed",
        f"bash deploy/ai-nfr.sh --report {report}",
        "```",
        "",
        "Phase 5 chạy lại đúng lệnh này trên server triển khai (Apache + HTTPS) và thay các số liệu ở trên bằng số đo trên server.",
        "",
    ]
    with open(report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    print(f"\nĐã ghi {report}")

sys.exit(0 if all(res.values()) else 1)
PY
echo "OK: đo NFR-07..NFR-11 hoàn tất (bắt đầu ${START_UTC} UTC)"
