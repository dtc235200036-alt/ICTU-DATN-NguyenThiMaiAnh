#!/usr/bin/env bash
# Phase 5 (05-04, D-03): đo các yêu cầu phi chức năng MỨC HỆ THỐNG trên bản
# triển khai đã seed, qua đường thật Apache HTTPS
# (docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md):
#   NFR-01 http:// -> 301 sang https://
#   NFR-02 mọi mật khẩu là bcrypt cost >= 12; mật khẩu seed không có trong log
#   NFR-03 JWT_SECRET từ môi trường; token hết hạn (ký bằng chính helper của
#          app, exp trong quá khứ) -> 401, token còn hạn cùng tài khoản -> 200
#   NFR-04 SV gọi route của Bộ môn -> 403 (bổ sung cho smoke/e2e)
#   NFR-05 Bộ môn khóa tài khoản -> đăng nhập đúng mật khẩu bị từ chối; mở khóa
#          -> đăng nhập lại được
#   NFR-08 20 x POST /api/topics/check-title qua Apache (SV), P95 curl <= 5 s
#   NFR-12 20 x tra cứu kho (từ khóa + khóa) và 20 x danh sách đề tài có bộ lọc
#          qua Apache (Bộ môn), mỗi loại P95 <= 1 s
#   NFR-13 information_schema: mọi bảng/cột văn bản của thesis_core và
#          thesis_ai là utf8mb4_vietnamese_ci; alembic_version = revision mới nhất
#   NFR-14 cùng một tên ở dạng NFC và NFD qua HTTPS -> cùng (nguon, id, ty_le)
#   NFR-15 ProxyTimeout > 30, / là SPA tĩnh do Apache phục vụ, /api qua proxy
#   NFR-17/18/19 số liệu seed (DATA-01/02/03) + 4 loại trùng + bảng kiểm chứng
# NFR-06 do smoke-test + pytest chứng minh, NFR-07/09/10/11 do ai-nfr.sh,
# NFR-16 do plan 05-05 (verify-all.sh ghép lại).
#
# Tài khoản dành riêng: DTC235210073 (SV) + bomon; khóa K95 dành riêng (script
# không tạo đợt nào). Dọn dẹp (trap, kể cả khi lỗi): mở khóa DTC235210073, xóa
# thông báo của nó phát sinh từ lúc bắt đầu, xóa đề tài/đợt K95 nếu có.
#
# Dùng: bash deploy/nfr-he-thong.sh [--json PATH]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BASE="${BASE_URL:-https://localhost:${HTTPS_PORT:-443}}"
HTTP_BASE="${HTTP_BASE_URL:-http://localhost:${HTTP_PORT:-80}}"
COMPOSE=(docker compose -f "${SCRIPT_DIR}/docker-compose.yml")
SV_MA="DTC235210073"
KHOA_RIENG="K95"
N=20
JSON_OUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --json) JSON_OUT="$2"; shift 2 ;;
    *) echo "Dùng: bash deploy/nfr-he-thong.sh [--json PATH]" >&2; exit 2 ;;
  esac
done

TMP="$(mktemp -d)"
START_UTC="$(date -u +%Y-%m-%d\ %H:%M:%S)"
KQ="$TMP/kq.jsonl"
: > "$KQ"
FAILS=0

sql() {
  bash "${SCRIPT_DIR}/sql.sh" "$1" | tr -d '\r'
}

sql_root() {
  "${COMPOSE[@]}" exec -T -e Q="$1" mysql sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -N -B -uroot -e "$Q"' | tr -d '\r'
}

cleanup() {
  local rc=$?
  sql "UPDATE tai_khoan SET bi_khoa = 0 WHERE ma_dang_nhap = '${SV_MA}';" >/dev/null 2>&1 || true
  sql "DELETE FROM thong_bao WHERE tai_khoan_id IN (SELECT id FROM tai_khoan WHERE ma_dang_nhap = '${SV_MA}') AND thoi_diem >= '${START_UTC}';" >/dev/null 2>&1 || true
  local dot_ids topic_ids
  dot_ids="$(sql "SELECT id FROM dot_do_an WHERE khoa = '${KHOA_RIENG}'" 2>/dev/null | paste -sd, - || true)"
  if [ -n "${dot_ids}" ]; then
    topic_ids="$(sql "SELECT id FROM de_tai WHERE dot_do_an_id IN (${dot_ids})" 2>/dev/null | paste -sd, - || true)"
    if [ -n "${topic_ids}" ]; then
      "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai TOPIC --ids "${topic_ids}" >/dev/null 2>&1 || true
      sql "DELETE ct FROM chi_tiet_trung_lap ct JOIN ket_qua_kiem_tra_trung_lap kq ON kq.id = ct.ket_qua_id WHERE kq.de_tai_id IN (${topic_ids});" >/dev/null 2>&1 || true
      sql "DELETE FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (${topic_ids});" >/dev/null 2>&1 || true
      sql "DELETE FROM de_tai WHERE id IN (${topic_ids});" >/dev/null 2>&1 || true
    fi
    # 0015: phân công GVHD trỏ tới đợt (FK không cascade) — xóa trước đợt.
    sql "DELETE FROM phan_cong_huong_dan WHERE dot_do_an_id IN (${dot_ids});" >/dev/null 2>&1 || true
    sql "DELETE FROM dot_do_an WHERE id IN (${dot_ids});" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  exit "$rc"
}
trap cleanup EXIT

# ghi_kq MA DAT(true/false) "cách đo" "kết quả"
ghi_kq() {
  python3 - "$KQ" "$1" "$2" "$3" "$4" <<'PY'
import json, sys
path, ma, dat, cach, kq = sys.argv[1:6]
with open(path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"ma": ma, "dat": dat == "true", "cach_do": cach, "ket_qua": kq}, ensure_ascii=False) + "\n")
PY
  if [ "$2" = "true" ]; then
    echo "OK: $1 — $4"
  else
    echo "FAIL: $1 — $4"
    FAILS=$((FAILS + 1))
  fi
}

p95_of() {
  # stdin: một số mỗi dòng -> "p50 p95 max" (P95 = giá trị hạng ceil(0.95 n))
  python3 -c "
import math, sys
xs = sorted(float(l) for l in sys.stdin if l.strip())
p = lambda q: xs[max(0, math.ceil(q * len(xs)) - 1)]
print(f'{p(0.5):.3f} {p(0.95):.3f} {xs[-1]:.3f} {len(xs)}')
"
}

login() {
  bash "${SCRIPT_DIR}/api-login.sh" "$1"
}

# --- Điều kiện --------------------------------------------------------------------
n_sv="$(sql "SELECT COUNT(*) FROM tai_khoan WHERE ma_dang_nhap = '${SV_MA}' AND vai_tro = 'SINH_VIEN'")"
[ "$n_sv" = "1" ] || { echo "FAIL: không có tài khoản ${SV_MA}"; exit 1; }
TOKEN_BOMON="$(login bomon)"
TOKEN_SV="$(login "${SV_MA}")"
SV_TK_ID="$(sql "SELECT id FROM tai_khoan WHERE ma_dang_nhap = '${SV_MA}'")"

# --- NFR-01 ----------------------------------------------------------------------
code01="$(curl -s -o /dev/null -m 10 -w '%{http_code}' "${HTTP_BASE}/")"
loc01="$(curl -s -o /dev/null -m 10 -w '%{redirect_url}' "${HTTP_BASE}/tong-quan")"
if [ "$code01" = "301" ] && [[ "$loc01" == https://* ]]; then d=true; else d=false; fi
ghi_kq NFR-01 "$d" "curl ${HTTP_BASE}/ và /tong-quan (cổng 80), đọc mã trạng thái và Location" \
  "HTTP ${code01}, Location ${loc01%%/tong-quan*}/… (https)"

# --- NFR-02 ----------------------------------------------------------------------
hash_rows="$(sql "SELECT LEFT(mat_khau_bam, 7), COUNT(*) FROM tai_khoan GROUP BY LEFT(mat_khau_bam, 7)")"
seed_pw="$("${COMPOSE[@]}" exec -T api printenv SEED_DEFAULT_PASSWORD | tr -d '\r')"
log_hits="$("${COMPOSE[@]}" logs --no-color api apache 2>/dev/null | grep -cF -- "${seed_pw}" || true)"
res02="$(python3 - "$hash_rows" <<'PY'
import re, sys
tong, xau = 0, 0
for line in sys.argv[1].splitlines():
    if not line.strip():
        continue
    pre, n = line.rsplit("\t", 1)
    tong += int(n)
    m = re.fullmatch(r"\$2[aby]\$(\d\d)\$", pre)
    if not m or int(m.group(1)) < 12:
        xau += int(n)
kinds = sorted({l.split("\t")[0] for l in sys.argv[1].splitlines() if l.strip()})
print(tong, xau, ",".join(kinds))
PY
)"
read -r tk_tong tk_xau tk_kieu <<<"$res02"
if [ "$tk_xau" = "0" ] && [ "$tk_tong" -gt 0 ] && [ "$log_hits" = "0" ]; then d=true; else d=false; fi
ghi_kq NFR-02 "$d" "Đọc tiền tố cột tai_khoan.mat_khau_bam của mọi tài khoản; tìm mật khẩu seed trong log container api/apache" \
  "${tk_tong} tài khoản, tiền tố ${tk_kieu} (bcrypt cost 12), ${tk_xau} tài khoản không đạt; mật khẩu seed xuất hiện ${log_hits} lần trong log"

# --- NFR-03 ----------------------------------------------------------------------
secret_len="$("${COMPOSE[@]}" exec -T api sh -c 'printf %s "$JWT_SECRET" | wc -c' | tr -d '\r ')"
tv="$(sql "SELECT phien_ban_token FROM tai_khoan WHERE id = ${SV_TK_ID}")"
tokens="$("${COMPOSE[@]}" exec -T -e TK_ID="${SV_TK_ID}" -e TV="${tv}" api python - <<'PY'
import os, time
from app.core import security
settings = security.settings
from app.core.roles import VaiTro
real = time.time
lui = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 3600
time.time = lambda: real() - lui  # helper của app, đồng hồ lùi -> exp trong quá khứ
het_han = security.create_access_token(int(os.environ["TK_ID"]), VaiTro.SINH_VIEN, int(os.environ["TV"]))
time.time = real
con_han = security.create_access_token(int(os.environ["TK_ID"]), VaiTro.SINH_VIEN, int(os.environ["TV"]))
print(het_han)
print(con_han)
PY
)"
tok_het="$(printf '%s\n' "$tokens" | sed -n 1p | tr -d '\r')"
tok_con="$(printf '%s\n' "$tokens" | sed -n 2p | tr -d '\r')"
c_het="$(curl -sk -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${tok_het}" "$BASE/api/auth/me")"
c_con="$(curl -sk -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${tok_con}" "$BASE/api/auth/me")"
c_none="$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api/auth/me")"
unset tokens tok_het tok_con
if [ "$c_het" = "401" ] && [ "$c_con" = "200" ] && [ "$c_none" = "401" ] && [ "${secret_len:-0}" -ge 32 ]; then d=true; else d=false; fi
ghi_kq NFR-03 "$d" "JWT_SECRET đọc từ biến môi trường của container api (độ dài); ký token bằng security.create_access_token của app với exp trong quá khứ và còn hạn, gọi GET /api/auth/me qua Apache" \
  "JWT_SECRET ${secret_len} ký tự từ môi trường; token hết hạn -> ${c_het}, token còn hạn -> ${c_con}, không token -> ${c_none}"

# --- NFR-04 (phép đo HTTPS bổ sung) ------------------------------------------------
c4a="$(curl -sk -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${TOKEN_SV}" "$BASE/api/accounts")"
c4b="$(curl -sk -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${TOKEN_SV}" "$BASE/api/dashboard/bo-mon")"
c4c="$(curl -sk -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer ${TOKEN_SV}" -F "file=@${REPO_ROOT}/seed-data/de-tai-kho.csv;type=text/csv" "$BASE/api/archive/import")"
if [ "$c4a" = "403" ] && [ "$c4b" = "403" ] && [ "$c4c" = "403" ]; then d=true; else d=false; fi
ghi_kq NFR-04 "$d" "SV ${SV_MA} gọi GET /api/accounts, GET /api/dashboard/bo-mon, POST /api/archive/import qua Apache" \
  "mã ${c4a} / ${c4b} / ${c4c}"

# --- NFR-05 ----------------------------------------------------------------------
c_lock="$(curl -sk -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer ${TOKEN_BOMON}" "$BASE/api/accounts/${SV_TK_ID}/lock")"
c_login_khoa="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"${SV_MA}\",\"mat_khau\":\"${seed_pw}\"}")"
c_me_khoa="$(curl -sk -o /dev/null -w '%{http_code}' -H "Authorization: Bearer ${TOKEN_SV}" "$BASE/api/auth/me")"
c_unlock="$(curl -sk -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer ${TOKEN_BOMON}" "$BASE/api/accounts/${SV_TK_ID}/unlock")"
c_login_mo="$(curl -sk -o /dev/null -w '%{http_code}' -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"dang_nhap\":\"${SV_MA}\",\"mat_khau\":\"${seed_pw}\"}")"
unset seed_pw
if [ "$c_lock" = "200" ] && { [ "$c_login_khoa" = "401" ] || [ "$c_login_khoa" = "403" ]; } && [ "$c_unlock" = "200" ] && [ "$c_login_mo" = "200" ]; then d=true; else d=false; fi
ghi_kq NFR-05 "$d" "Bộ môn khóa ${SV_MA} (POST /api/accounts/{id}/lock), đăng nhập đúng mật khẩu, gọi API bằng token cũ, mở khóa rồi đăng nhập lại — qua Apache" \
  "khóa ${c_lock}; đăng nhập khi bị khóa -> ${c_login_khoa}; token cũ -> ${c_me_khoa}; mở khóa ${c_unlock}; đăng nhập lại -> ${c_login_mo}"
TOKEN_SV="$(login "${SV_MA}")"

# --- NFR-08 qua HTTPS --------------------------------------------------------------
python3 - "${REPO_ROOT}/seed-data/truy-van-ten-de-tai.csv" "$N" > "$TMP/titles.txt" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))[: int(sys.argv[2])]
for r in rows:
    print(r["ten_truy_van"])
PY
: > "$TMP/t08"
bad08=0
while IFS= read -r ten; do
  python3 -c 'import json,sys; print(json.dumps({"ten_de_tai": sys.argv[1]}, ensure_ascii=False))' "$ten" > "$TMP/body08.json"
  out="$(curl -sk -o "$TMP/r08.json" -w '%{http_code} %{time_total}' -X POST "$BASE/api/topics/check-title" \
    -H "Authorization: Bearer ${TOKEN_SV}" -H 'Content-Type: application/json' --data-binary "@$TMP/body08.json")"
  [ "${out%% *}" = "200" ] || bad08=$((bad08 + 1))
  grep -q '"trang_thai":"HOAN_TAT"' "$TMP/r08.json" || bad08=$((bad08 + 1))
  echo "${out#* }" >> "$TMP/t08"
done < "$TMP/titles.txt"
read -r p50 p95 pmax n08 < <(p95_of < "$TMP/t08")
if [ "$bad08" = "0" ] && [ "$n08" = "$N" ] && python3 -c "import sys; sys.exit(0 if $p95 <= 5 else 1)"; then d=true; else d=false; fi
ghi_kq NFR-08 "$d" "${n08} lời gọi POST /api/topics/check-title qua Apache HTTPS (Apache -> Web API -> dịch vụ AI) bằng SV, tên từ seed-data/truy-van-ten-de-tai.csv, đo curl time_total" \
  "qua HTTPS: P50 ${p50} s, P95 ${p95} s, max ${pmax} s; ${bad08} lỗi"

# --- NFR-12 ------------------------------------------------------------------------
KW=("quản lý" "hệ thống" "website" "ứng dụng" "bán hàng" "thư viện" "nhân sự" "khách sạn" "học tập" "kế toán")
KH=("K18" "K19" "K20" "K21" "K22")
: > "$TMP/t12a"
: > "$TMP/t12b"
bad12=0
urlenc() { python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1"; }
for i in $(seq 0 $((N - 1))); do
  q="$(urlenc "${KW[$((i % ${#KW[@]}))]}")"
  k="${KH[$((i % ${#KH[@]}))]}"
  out="$(curl -sk -o "$TMP/r12.json" -w '%{http_code} %{time_total}' -H "Authorization: Bearer ${TOKEN_BOMON}" \
    "$BASE/api/archive?q=${q}&khoa=${k}&page=1&page_size=10")"
  [ "${out%% *}" = "200" ] || bad12=$((bad12 + 1))
  echo "${out#* }" >> "$TMP/t12a"
done
DOT_IDS=($(sql "SELECT id FROM dot_do_an ORDER BY id"))
TT=("CHO_DUYET" "DA_DUYET" "DA_PHAN_CONG" "TU_CHOI")
for i in $(seq 0 $((N - 1))); do
  q="$(urlenc "${KW[$((i % ${#KW[@]}))]}")"
  case $((i % 4)) in
    0) params="dot_do_an_id=${DOT_IDS[$((i % ${#DOT_IDS[@]}))]}&sap_xep=moi_nhat" ;;
    1) params="q=${q}" ;;
    2) params="trang_thai=${TT[$((i % ${#TT[@]}))]}" ;;
    3) params="dot_do_an_id=${DOT_IDS[$((i % ${#DOT_IDS[@]}))]}&q=${q}" ;;
  esac
  out="$(curl -sk -o "$TMP/r12.json" -w '%{http_code} %{time_total}' -H "Authorization: Bearer ${TOKEN_BOMON}" \
    "$BASE/api/topics?${params}&page=1&page_size=10")"
  [ "${out%% *}" = "200" ] || { bad12=$((bad12 + 1)); echo "  /api/topics?${params} -> ${out%% *}: $(head -c 200 "$TMP/r12.json")"; }
  echo "${out#* }" >> "$TMP/t12b"
done
read -r a50 a95 amax na < <(p95_of < "$TMP/t12a")
read -r b50 b95 bmax nb < <(p95_of < "$TMP/t12b")
n_kho_all="$(sql "SELECT COUNT(*) FROM do_an_kho")"
if [ "$bad12" = "0" ] && python3 -c "import sys; sys.exit(0 if $a95 <= 1 and $b95 <= 1 else 1)"; then d=true; else d=false; fi
ghi_kq NFR-12 "$d" "${na} lần GET /api/archive?q=…&khoa=… (kho ${n_kho_all} bản ghi) và ${nb} lần GET /api/topics với bộ lọc đợt/từ khóa/trạng thái, qua Apache HTTPS bằng Bộ môn, đo curl time_total" \
  "tra cứu kho P95 ${a95} s (max ${amax}); danh sách đề tài P95 ${b95} s (max ${bmax}); ${bad12} lỗi"

# --- NFR-13 ------------------------------------------------------------------------
col_bad="$(sql_root "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema IN ('thesis_core','thesis_ai') AND collation_name IS NOT NULL AND collation_name <> 'utf8mb4_vietnamese_ci'")"
tbl_bad="$(sql_root "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('thesis_core','thesis_ai') AND table_type = 'BASE TABLE' AND table_collation <> 'utf8mb4_vietnamese_ci'")"
col_tong="$(sql_root "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema IN ('thesis_core','thesis_ai') AND collation_name IS NOT NULL")"
tbl_tong="$(sql_root "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('thesis_core','thesis_ai') AND table_type = 'BASE TABLE'")"
bad_list="$(sql_root "SELECT CONCAT(table_schema,'.',table_name,'.',column_name,'=',collation_name) FROM information_schema.columns WHERE table_schema IN ('thesis_core','thesis_ai') AND collation_name IS NOT NULL AND collation_name <> 'utf8mb4_vietnamese_ci' LIMIT 5" | paste -sd' ' -)"
head_core="$(python3 - "${REPO_ROOT}/backend/alembic/versions" <<'PY'
import pathlib, re, sys
revs, downs = set(), set()
for f in pathlib.Path(sys.argv[1]).glob("*.py"):
    t = f.read_text(encoding="utf-8")
    m = re.search(r'^revision\s*(?::\s*str\s*)?=\s*["\']([^"\']+)', t, re.M)
    if m:
        revs.add(m.group(1))
    downs.update(re.findall(r'^down_revision\s*(?::[^=]+)?=\s*["\']([^"\']+)', t, re.M))
h = sorted(revs - downs)
print(h[0] if len(h) == 1 else "?")
PY
)"
head_ai="$(python3 - "${REPO_ROOT}/ai-service/alembic/versions" <<'PY'
import pathlib, re, sys
revs, downs = set(), set()
for f in pathlib.Path(sys.argv[1]).glob("*.py"):
    t = f.read_text(encoding="utf-8")
    m = re.search(r'^revision\s*(?::\s*str\s*)?=\s*["\']([^"\']+)', t, re.M)
    if m:
        revs.add(m.group(1))
    downs.update(re.findall(r'^down_revision\s*(?::[^=]+)?=\s*["\']([^"\']+)', t, re.M))
h = sorted(revs - downs)
print(h[0] if len(h) == 1 else "?")
PY
)"
db_core="$(sql_root "SELECT version_num FROM thesis_core.alembic_version")"
db_ai="$(sql_root "SELECT version_num FROM thesis_ai.alembic_version")"
if [ "$col_bad" = "0" ] && [ "$tbl_bad" = "0" ] && [ "$db_core" = "$head_core" ] && [ "$db_ai" = "$head_ai" ]; then d=true; else d=false; fi
ghi_kq NFR-13 "$d" "information_schema.columns/tables của thesis_core và thesis_ai (collation khác utf8mb4_vietnamese_ci); alembic_version của hai schema so với revision mới nhất trong mã nguồn" \
  "${col_tong} cột văn bản / ${tbl_tong} bảng, ${col_bad} cột và ${tbl_bad} bảng sai collation${bad_list:+ (${bad_list})}; thesis_core ${db_core} (mới nhất ${head_core}), thesis_ai ${db_ai} (mới nhất ${head_ai})"

# --- NFR-14 ------------------------------------------------------------------------
TEN14="$(sed -n 1p "$TMP/titles.txt")"
for form in NFC NFD; do
  python3 -c 'import json,sys,unicodedata; print(json.dumps({"ten_de_tai": unicodedata.normalize(sys.argv[2], sys.argv[1])}, ensure_ascii=False))' "$TEN14" "$form" > "$TMP/b14-$form.json"
  curl -sk -o "$TMP/r14-$form.json" -X POST "$BASE/api/topics/check-title" \
    -H "Authorization: Bearer ${TOKEN_SV}" -H 'Content-Type: application/json' --data-binary "@$TMP/b14-$form.json"
done
res14="$(python3 - "$TMP/r14-NFC.json" "$TMP/r14-NFD.json" "$TMP/b14-NFC.json" "$TMP/b14-NFD.json" <<'PY'
import json, sys
def trip(p):
    d = json.load(open(p, encoding="utf-8"))
    return d.get("trang_thai"), sorted((m["nguon"], m.get("do_an_kho_id") or m.get("de_tai_id"), m["ty_le"]) for m in d.get("matches", []))
a, b = trip(sys.argv[1]), trip(sys.argv[2])
khac = open(sys.argv[3], "rb").read() != open(sys.argv[4], "rb").read()
same = a == b and len(a[1]) > 0 and khac
print("true" if same else "false", len(a[1]), a[1][0][2] if a[1] else "-", a[0])
PY
)"
read -r d14 n14 top14 tt14 <<<"$res14"
ghi_kq NFR-14 "$d14" "Cùng một tên đề tài (truy vấn TV001) gửi dạng NFC và dạng NFD (byte khác nhau) tới POST /api/topics/check-title qua HTTPS, so sánh các bộ (nguồn, id, tỷ lệ)" \
  "${n14} kết quả giống hệt nhau ở hai dạng (trạng thái ${tt14}, tỷ lệ cao nhất ${top14} %)"

# --- NFR-15 ------------------------------------------------------------------------
conf="${SCRIPT_DIR}/apache/ntma.conf"
pt="$(awk '/^[[:space:]]*ProxyTimeout/{print $2; exit}' "$conf")"
docroot="$(grep -c '^[[:space:]]*DocumentRoot /usr/local/apache2/htdocs' "$conf" || true)"
api_proxy="$(grep -c '^[[:space:]]*ProxyPass /api/ http://api:8001/api/' "$conf" || true)"
curl -sk -D "$TMP/h15" -o "$TMP/root.html" "$BASE/"
asset="$(grep -o 'src="/assets/[^"]*\.js"' "$TMP/root.html" | head -1 | sed 's/^src="//; s/"$//')"
asset_ct="$(curl -sk -o /dev/null -w '%{http_code} %{content_type}' "$BASE${asset:-/assets/none.js}")"
api15="$(curl -sk "$BASE/api/health")"
if [ "${pt:-0}" -gt 30 ] && [ "$docroot" -ge 1 ] && [ "$api_proxy" -ge 1 ] && grep -q 'id="root"' "$TMP/root.html" \
   && [[ "$asset_ct" == 200*javascript* ]] && printf '%s' "$api15" | grep -q '"status":"ok"'; then d=true; else d=false; fi
ghi_kq NFR-15 "$d" "Đọc deploy/apache/ntma.conf (ProxyTimeout, DocumentRoot, ProxyPass /api/); GET / và một tệp /assets/*.js do Apache phục vụ; GET /api/health qua proxy" \
  "ProxyTimeout ${pt} s; DocumentRoot htdocs (bản build Vite); / trả SPA (id=\"root\"), ${asset:-?} -> ${asset_ct}; /api/health qua proxy: status ok"

# --- NFR-17 / 18 / 19 ----------------------------------------------------------------
read -r n_sv n_gv <<<"$(sql "SELECT SUM(vai_tro='SINH_VIEN'), SUM(vai_tro='GIANG_VIEN') FROM tai_khoan")"
if [ "$n_sv" = "580" ] && [ "$n_gv" = "70" ]; then d=true; else d=false; fi
ghi_kq NFR-17 "$d" "Đếm tai_khoan theo vai_tro sau khi seed" "${n_sv} sinh viên, ${n_gv} giảng viên"

read -r k_n k_idx k_khoa <<<"$(sql "SELECT COUNT(*), SUM(trang_thai_index='DA_INDEX'), COUNT(DISTINCT khoa) FROM do_an_kho WHERE nguon='IMPORT' AND khoa IN ('K18','K19','K20','K21','K22')")"
h18="$("${COMPOSE[@]}" exec -T api python -c "
import json, urllib.request
h = json.load(urllib.request.urlopen('http://ai:8002/health', timeout=10))
print(h['index_size_tieu_de'], h['thieu_embedding'])
" | tr -d '\r')"
read -r idx_td thieu <<<"$h18"
if [ "$k_n" = "300" ] && [ "$k_idx" = "300" ] && [ "$k_khoa" -ge 2 ] && [ "$idx_td" -ge 300 ] && [ "$thieu" = "0" ]; then d=true; else d=false; fi
ghi_kq NFR-18 "$d" "Đếm do_an_kho (IMPORT K18–K22) và trạng thái DA_INDEX; /health của dịch vụ AI (index_size_tieu_de, thieu_embedding)" \
  "${k_n} đề tài thuộc ${k_khoa} khóa, ${k_idx} DA_INDEX; chỉ mục tiêu đề ${idx_td} vector, thiếu embedding ${thieu}"

res19="$(python3 - "${REPO_ROOT}/seed-data" "${REPO_ROOT}/docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md" <<'PY'
import collections, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
files = [p for p in (root / "tai-lieu").iterdir() if p.suffix in (".docx", ".pdf")]
m = json.load(open(root / "manifest.json", encoding="utf-8"))
loai = collections.Counter(c["loai"] for c in m["cap"])
page = pathlib.Path(sys.argv[2])
bang = page.exists() and all(k in page.read_text(encoding="utf-8") for k in ("P01", "P25"))
ok = len(files) == 50 and len(m["cap"]) == 25 and len(loai) == 4 and bang
print("true" if ok else "false")
print(f"{len(files)} tệp ({sum(p.suffix == '.docx' for p in files)} DOCX, {sum(p.suffix == '.pdf' for p in files)} PDF), {len(m['cap'])} cặp A/B, 4 loại: " + ", ".join(f"{k} {v}" for k, v in sorted(loai.items())) + ("; bảng kiểm chứng P01–P25 ở thu-nghiem-ai/03-hieu-chinh-nguong.md" if bang else "; THIẾU bảng kiểm chứng"))
PY
)"
d19="$(printf '%s\n' "$res19" | sed -n 1p)"
kq19="$(printf '%s\n' "$res19" | sed -n 2p)"
linked="$(sql "SELECT COUNT(*) FROM do_an_kho k JOIN tai_lieu_do_an t ON t.de_tai_id = k.de_tai_id AND t.loai = 'BAO_CAO_CUOI' WHERE k.nguon='IMPORT'")"
[ "$linked" = "25" ] || d19=false
ghi_kq NFR-19 "$d19" "Đếm tệp seed-data/tai-lieu, cặp và loại trùng trong seed-data/manifest.json; kiểm tra bảng kiểm chứng; đếm đồ án nguồn có báo cáo cuối trong CSDL" \
  "${kq19}; ${linked} đồ án nguồn có báo cáo cuối đã nạp"

# --- Kết quả ---------------------------------------------------------------------------
if [ -n "$JSON_OUT" ]; then
  python3 - "$KQ" "$JSON_OUT" "$START_UTC" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
out = {"bat_dau_utc": sys.argv[3], "nfr": {r["ma"]: {k: r[k] for k in ("dat", "cach_do", "ket_qua")} for r in rows}}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
  echo "Đã ghi ${JSON_OUT}"
fi
if [ "$FAILS" -gt 0 ]; then
  echo "FAIL: ${FAILS} NFR không đạt"
  exit 1
fi
echo "OK: đo NFR hệ thống hoàn tất (bắt đầu ${START_UTC} UTC)"
