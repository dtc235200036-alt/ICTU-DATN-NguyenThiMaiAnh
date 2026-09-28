#!/usr/bin/env bash
# Phase 5 (05-04, D-01/D-02): cài đặt / nâng cấp TOÀN BỘ hệ thống bằng một lệnh
# từ một bản `git clone` sạch trên máy Linux có Docker:
#   0. kiểm tra điều kiện (docker, compose v2, openssl, curl, python3, dung lượng
#      trống, cổng 80/443)
#   1. deploy/init.sh — sinh deploy/.env (bí mật ngẫu nhiên, chmod 600) và chứng
#      chỉ TLS tự ký; tùy chọn --server-name / --random-seed-password
#   2. tải trước trọng số mô hình AI vào volume ai-models (D-02) — lúc chạy
#      service ai đặt HF_HUB_OFFLINE=1, không bao giờ gọi Hugging Face
#   3. docker compose up -d --build --wait (mysql / api / apache HTTPS / ai nội bộ)
#   4. kiểm tra migration (alembic_version = revision mới nhất) + ai /health
#   5. kiểm tra dữ liệu seed DATA-01 (100 SV, 30 GV, Bộ môn)
#   6. deploy/seed-ai.sh — 300 đề tài kho qua đường import thật + 25 đồ án
#      nguồn có báo cáo (DATA-02, DATA-03); idempotent
#   7. tóm tắt: URL, tài khoản, nguồn mật khẩu, thời gian từng bước
#
# Chạy lại an toàn: KHÔNG xóa dữ liệu trừ khi có `--fresh --yes`.
#
# Dùng: bash deploy/install.sh [--fresh [--yes]] [--server-name TEN]
#                              [--random-seed-password] [--skip-seed-ai]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

COMPOSE_FILE="deploy/docker-compose.yml"
COMPOSE=(docker compose -f "${COMPOSE_FILE}")
PROJECT="${COMPOSE_PROJECT_NAME:-ntma}"
ENV_FILE="deploy/.env"
CERT_DIR="deploy/certs"
DEV_DEFAULT_PW="DoAn@2026"
MIN_FREE_GB=10

FRESH=0
YES=0
SERVER_NAME_ARG=""
RANDOM_PW=0
SKIP_SEED_AI=0

usage() {
  cat <<'EOF'
Dùng: bash deploy/install.sh [tùy chọn]

  --fresh                  Cài lại sạch: `docker compose down -v` (XÓA CSDL, file
                           đã nộp và cache mô hình) trước khi cài. Cần --yes hoặc
                           gõ XOA để xác nhận; không có TTY thì bắt buộc --yes.
  --yes                    Xác nhận --fresh không cần hỏi.
  --server-name TEN        Tên máy chủ (DNS hoặc IP) — ghi SERVER_NAME vào
                           deploy/.env và sinh lại chứng chỉ tự ký cho tên đó
                           (chứng chỉ của CA thật được giữ nguyên).
  --random-seed-password   Sinh mật khẩu seed ngẫu nhiên vào deploy/.env (chỉ khi
                           còn trống / là mật khẩu dev mặc định và CSDL chưa có).
  --skip-seed-ai           Bỏ qua bước nạp kho dịch vụ AI (deploy/seed-ai.sh).
  -h, --help               In hướng dẫn này.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --fresh) FRESH=1; shift ;;
    --yes|-y) YES=1; shift ;;
    --server-name)
      [ $# -ge 2 ] || { echo "FAIL: --server-name cần một giá trị" >&2; exit 2; }
      SERVER_NAME_ARG="$2"; shift 2 ;;
    --server-name=*) SERVER_NAME_ARG="${1#*=}"; shift ;;
    --random-seed-password) RANDOM_PW=1; shift ;;
    --skip-seed-ai) SKIP_SEED_AI=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "FAIL: tùy chọn không hợp lệ: $1" >&2; usage >&2; exit 2 ;;
  esac
done

ok() { echo "OK: $1"; }
info() { echo "... $1"; }
warn() { echo "CẢNH BÁO: $1"; }
fail() {
  echo "FAIL: $1"
  exit 1
}

# --- Đo thời gian từng bước ---------------------------------------------------
STEP_NAMES=()
STEP_SECS=()
STEP_T0=0
INSTALL_T0=$(date +%s)
CURRENT_STEP=""

step_begin() {
  CURRENT_STEP="$1"
  STEP_T0=$(date +%s)
  echo ""
  echo "=== Bước ${CURRENT_STEP}"
}

step_end() {
  local d=$(( $(date +%s) - STEP_T0 ))
  STEP_NAMES+=("${CURRENT_STEP}")
  STEP_SECS+=("$d")
  echo "THOI_GIAN_BUOC: ${CURRENT_STEP} = ${d} s"
}

env_get() {
  # In giá trị của một khóa trong deploy/.env (rỗng nếu không có). Không in ra log.
  [ -f "${ENV_FILE}" ] || return 0
  grep -m1 "^$1=" "${ENV_FILE}" 2>/dev/null | cut -d= -f2- || true
}

env_set() {
  # Ghi KEY=VALUE vào deploy/.env (thay dòng cũ hoặc thêm mới), giữ chmod 600.
  python3 - "${ENV_FILE}" "$1" "$2" <<'PY'
import sys
path, key, value = sys.argv[1:4]
lines = open(path, encoding="utf-8").read().splitlines()
out, done = [], False
for line in lines:
    if line.startswith(key + "="):
        if not done:
            out.append(f"{key}={value}")
            done = True
        continue
    out.append(line)
if not done:
    out.append(f"{key}={value}")
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
PY
  chmod 600 "${ENV_FILE}"
}

volume_exists() {
  docker volume inspect "${PROJECT}_$1" >/dev/null 2>&1
}

# --- Xác nhận thao tác phá hủy (T-05-12) — kiểm tra TRƯỚC mọi thao tác khác -----
if [ "${FRESH}" = "1" ] && [ "${YES}" != "1" ]; then
  if [ -t 0 ]; then
    echo "--fresh sẽ XÓA toàn bộ dữ liệu của project ${PROJECT}: CSDL (mysql-data), file đã nộp (uploads-data) và cache mô hình (ai-models)."
    printf 'Gõ XOA để xác nhận: '
    read -r answer
    [ "${answer}" = "XOA" ] || fail "Không xác nhận — không xóa gì."
  else
    fail "--fresh cần --yes khi không có TTY (không xóa gì)."
  fi
fi

echo "Cài đặt hệ thống quản lý đồ án (project ${PROJECT}) — commit $(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo '?')"

# --- Bước 0: điều kiện --------------------------------------------------------
step_begin "0 — Kiểm tra điều kiện"
for cmd in docker openssl curl python3; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Thiếu lệnh '$cmd' trên PATH"
done
docker info >/dev/null 2>&1 || fail "Không kết nối được Docker daemon (đã chạy dịch vụ docker và có quyền với /var/run/docker.sock?)"
compose_ver="$(docker compose version --short 2>/dev/null || true)"
[ -n "${compose_ver}" ] || fail "Thiếu Docker Compose v2 (lệnh 'docker compose')"
[ "${compose_ver%%.*}" -ge 2 ] 2>/dev/null || fail "Cần Docker Compose v2 trở lên (đang có ${compose_ver})"
ok "docker $(docker version --format '{{.Server.Version}}' 2>/dev/null), compose ${compose_ver}, openssl, curl, python3"

docker_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo /)"
free_kb="$(df -Pk "${docker_root}" 2>/dev/null | awk 'NR==2{print $4}')"
[ -n "${free_kb}" ] || free_kb="$(df -Pk / | awk 'NR==2{print $4}')"
free_gb=$(( free_kb / 1024 / 1024 ))
[ "${free_gb}" -ge "${MIN_FREE_GB}" ] || fail "Chỉ còn ${free_gb} GB trống trên ${docker_root} (cần >= ${MIN_FREE_GB} GB cho image + mô hình + dữ liệu)"
ok "Dung lượng trống trên ${docker_root}: ${free_gb} GB"

http_port="$(env_get HTTP_PORT)"; http_port="${http_port:-80}"
https_port="$(env_get HTTPS_PORT)"; https_port="${https_port:-443}"
apache_running=""
if "${COMPOSE[@]}" ps --status running -q apache >/dev/null 2>&1; then
  apache_running="$("${COMPOSE[@]}" ps --status running -q apache 2>/dev/null || true)"
fi
port_busy() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltnH "sport = :$1" 2>/dev/null | grep -q .
  else
    (exec 3<>"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
  fi
}
for p in "${http_port}" "${https_port}"; do
  if port_busy "$p"; then
    [ -n "${apache_running}" ] || fail "Cổng $p đang bị chương trình khác chiếm (không phải apache của project ${PROJECT}) — giải phóng cổng hoặc đổi HTTP_PORT/HTTPS_PORT trong deploy/.env"
  fi
done
ok "Cổng ${http_port}/${https_port} trống hoặc do apache của project ${PROJECT} giữ"

if [ "${FRESH}" = "1" ]; then
  info "--fresh: docker compose down -v --remove-orphans (project ${PROJECT})"
  if [ -f "${ENV_FILE}" ]; then
    "${COMPOSE[@]}" down -v --remove-orphans
  else
    # Chưa có .env thì compose không nội suy được biến bắt buộc — xóa theo tên.
    docker ps -aq --filter "label=com.docker.compose.project=${PROJECT}" | xargs -r docker rm -f >/dev/null
    for v in mysql-data uploads-data ai-models; do
      docker volume rm "${PROJECT}_$v" >/dev/null 2>&1 || true
    done
  fi
  ok "Đã xóa container và volume của project ${PROJECT}"
fi
step_end

# --- Bước 1: bí mật + chứng chỉ -------------------------------------------------
step_begin "1 — Sinh deploy/.env và chứng chỉ TLS"
bash deploy/init.sh | sed '/^Bước tiếp theo:/,$d'

if [ -n "${SERVER_NAME_ARG}" ]; then
  [[ "${SERVER_NAME_ARG}" =~ ^[A-Za-z0-9.-]+$ ]] || fail "--server-name chỉ gồm chữ, số, dấu chấm, gạch ngang"
  env_set SERVER_NAME "${SERVER_NAME_ARG}"
  ok "SERVER_NAME=${SERVER_NAME_ARG} ghi vào deploy/.env"
fi
SERVER_NAME="$(env_get SERVER_NAME)"
SERVER_NAME="${SERVER_NAME:-localhost}"

# Chứng chỉ tự ký phải khớp SERVER_NAME; chứng chỉ do CA cấp (issuer khác
# subject) KHÔNG bao giờ bị ghi đè (4.3 — thay bằng tay deploy/certs/server.*).
if [ "${SERVER_NAME}" != "localhost" ]; then
  subj="$(openssl x509 -in "${CERT_DIR}/server.crt" -noout -subject -nameopt RFC2253 2>/dev/null || true)"
  iss="$(openssl x509 -in "${CERT_DIR}/server.crt" -noout -issuer -nameopt RFC2253 2>/dev/null || true)"
  if openssl x509 -in "${CERT_DIR}/server.crt" -noout -checkhost "${SERVER_NAME}" 2>/dev/null | grep -q 'does match' \
     || openssl x509 -in "${CERT_DIR}/server.crt" -noout -checkip "${SERVER_NAME}" 2>/dev/null | grep -q 'does match'; then
    ok "Chứng chỉ TLS đã khớp ${SERVER_NAME}"
  elif [ "${subj#subject=}" != "${iss#issuer=}" ]; then
    warn "Chứng chỉ trong ${CERT_DIR} do CA cấp nhưng không khớp ${SERVER_NAME} — giữ nguyên, hãy thay bằng chứng chỉ đúng tên"
  else
    if [[ "${SERVER_NAME}" =~ ^[0-9.]+$ ]]; then san="IP:${SERVER_NAME}"; else san="DNS:${SERVER_NAME}"; fi
    openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 825 \
      -keyout "${CERT_DIR}/server.key" -out "${CERT_DIR}/server.crt" \
      -subj "/CN=${SERVER_NAME}" -addext "subjectAltName=${san}" >/dev/null 2>&1 \
      || fail "Không sinh được chứng chỉ tự ký cho ${SERVER_NAME}"
    chmod 600 "${CERT_DIR}/server.key"
    chmod 644 "${CERT_DIR}/server.crt"
    ok "Sinh lại chứng chỉ tự ký cho ${SERVER_NAME} (${san})"
  fi
fi

if [ "${RANDOM_PW}" = "1" ]; then
  cur_pw="$(env_get SEED_DEFAULT_PASSWORD)"
  if [ -n "${cur_pw}" ] && [ "${cur_pw}" != "${DEV_DEFAULT_PW}" ]; then
    ok "SEED_DEFAULT_PASSWORD đã được đặt riêng trong deploy/.env — giữ nguyên"
  elif volume_exists mysql-data; then
    warn "CSDL đã có tài khoản seed — đổi SEED_DEFAULT_PASSWORD bây giờ không đổi mật khẩu các tài khoản đã tạo; bỏ qua --random-seed-password (dùng cùng --fresh --yes khi cài mới)"
  else
    env_set SEED_DEFAULT_PASSWORD "Ntma@$(openssl rand -hex 8)"
    ok "Đã ghi SEED_DEFAULT_PASSWORD ngẫu nhiên vào deploy/.env (xem giá trị trong file đó)"
  fi
fi
[ -n "$(env_get SEED_DEFAULT_PASSWORD)" ] || fail "SEED_DEFAULT_PASSWORD trống trong deploy/.env — app.seed không tạo được tài khoản (dùng --random-seed-password)"
step_end

# --- Bước 2: tải trước mô hình (D-02) -----------------------------------------
step_begin "2 — Build image AI và tải trước mô hình"
"${COMPOSE[@]}" build ai
model_t0=$(date +%s)
# ENTRYPOINT của image là docker-entrypoint.sh (migrate + uvicorn) nên phải đổi
# entrypoint; bật mạng cho riêng lần tải này (service ai chạy với OFFLINE=1).
# Idempotent: mô hình đã có trong volume thì chỉ mất vài giây để kiểm tra.
if ! "${COMPOSE[@]}" run --rm --no-deps -T \
    -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 \
    --entrypoint python ai -m app.download_model; then
  fail "Không tải được trọng số mô hình vào volume ${PROJECT}_ai-models. Máy cần Internet (huggingface.co) trong lúc cài đặt; máy chủ không có Internet: làm nóng volume ở nơi có mạng rồi sao chép sang (deploy/README.md)."
fi
MODEL_SECS=$(( $(date +%s) - model_t0 ))
model_mb="$("${COMPOSE[@]}" run --rm --no-deps -T --entrypoint du ai -sm /models 2>/dev/null | awk '{print $1}' | tail -1 || true)"
echo "MO_HINH: tai_giay=${MODEL_SECS} dung_luong_mib=${model_mb:-?}"
ok "Mô hình sẵn sàng trong volume ${PROJECT}_ai-models (${model_mb:-?} MiB, ${MODEL_SECS} s)"
step_end

# --- Bước 3: dựng stack --------------------------------------------------------
step_begin "3 — docker compose up -d --build --wait"
"${COMPOSE[@]}" up -d --build --wait --wait-timeout 900 \
  || fail "Stack chưa healthy — xem: docker compose -f ${COMPOSE_FILE} ps && docker compose -f ${COMPOSE_FILE} logs"
"${COMPOSE[@]}" ps --format '{{.Service}}\t{{.Status}}'
[ "$("${COMPOSE[@]}" exec -T ai printenv HF_HUB_OFFLINE | tr -d '\r')" = "1" ] || fail "Service ai không chạy với HF_HUB_OFFLINE=1 (D-02)"
ok "Stack ${PROJECT} chạy (ai: HF_HUB_OFFLINE=1)"
step_end

# --- Bước 4: migration + dịch vụ AI --------------------------------------------
step_begin "4 — Kiểm tra migration và dịch vụ AI"
head_rev="$(python3 - backend/alembic/versions <<'PY'
import pathlib, re, sys
revs, downs = set(), set()
for f in pathlib.Path(sys.argv[1]).glob("*.py"):
    t = f.read_text(encoding="utf-8")
    m = re.search(r'^revision\s*(?::\s*str\s*)?=\s*["\']([^"\']+)', t, re.M)
    if m:
        revs.add(m.group(1))
    for d in re.findall(r'^down_revision\s*(?::[^=]+)?=\s*["\']([^"\']+)', t, re.M):
        downs.add(d)
heads = sorted(revs - downs)
print(heads[0] if len(heads) == 1 else "?")
PY
)"
db_rev="$(bash deploy/sql.sh "SELECT version_num FROM alembic_version" | tr -d '\r')"
[ "${db_rev}" = "${head_rev}" ] || fail "alembic_version=${db_rev}, revision mới nhất trong backend/alembic/versions=${head_rev}"
ok "thesis_core ở revision mới nhất (${db_rev})"
ai_health="$("${COMPOSE[@]}" exec -T api python -c "
import json, urllib.request
h = json.load(urllib.request.urlopen('http://ai:8002/health', timeout=10))
print(h.get('status'), h.get('ten_model'))
" 2>/dev/null || true)"
[ "${ai_health%% *}" = "ok" ] || fail "Dịch vụ AI /health (từ container api) không ok: ${ai_health}"
ok "Dịch vụ AI /health ok — ${ai_health#* }"
step_end

# --- Bước 5: DATA-01 -------------------------------------------------------------
step_begin "5 — Kiểm tra tài khoản seed (DATA-01)"
counts="$(bash deploy/sql.sh "SELECT SUM(vai_tro='SINH_VIEN'), SUM(vai_tro='GIANG_VIEN'), SUM(vai_tro='BO_MON') FROM tai_khoan" | tr -d '\r')"
read -r n_sv n_gv n_bm <<<"${counts}"
[ "${n_sv}" = "100" ] && [ "${n_gv}" = "30" ] && [ "${n_bm:-0}" -ge 1 ] \
  || fail "Tài khoản seed: ${n_sv} SV / ${n_gv} GV / ${n_bm} Bộ môn (kỳ vọng 100 / 30 / >= 1)"
ok "Tài khoản seed: ${n_sv} sinh viên, ${n_gv} giảng viên, ${n_bm} Bộ môn"
step_end

# --- Bước 6: kho dịch vụ AI (DATA-02, DATA-03) ----------------------------------
# Các script deploy/*.sh gọi https://localhost:${HTTPS_PORT} (Apache có thể không ở 443).
export HTTPS_PORT="$(env_get HTTPS_PORT)"; HTTPS_PORT="${HTTPS_PORT:-443}"
export HTTP_PORT="$(env_get HTTP_PORT)"; HTTP_PORT="${HTTP_PORT:-80}"
if [ "${SKIP_SEED_AI}" = "1" ]; then
  info "Bỏ qua deploy/seed-ai.sh (--skip-seed-ai)"
else
  step_begin "6 — Nạp kho dịch vụ AI (seed-ai.sh)"
  bash deploy/seed-ai.sh
  step_end
fi

# --- Bước 7: tóm tắt ---------------------------------------------------------------
TOTAL=$(( $(date +%s) - INSTALL_T0 ))
pw_now="$(env_get SEED_DEFAULT_PASSWORD)"
echo ""
echo "=== Tóm tắt"
echo "Địa chỉ:     https://${SERVER_NAME}$([ "${https_port}" = "443" ] || echo ":${https_port}")/"
echo "Tài khoản:   bomon (Bộ môn), GV001–GV030 (giảng viên), DTC225200001–DTC225200100 (sinh viên); đăng nhập bằng mã hoặc email"
if [ "${pw_now}" = "${DEV_DEFAULT_PW}" ]; then
  echo "Mật khẩu:    mật khẩu dev mặc định (deploy/README.md, mục Tài khoản demo) — SEED_DEFAULT_PASSWORD trong deploy/.env"
  if [ "${SERVER_NAME}" != "localhost" ]; then
    warn "SERVER_NAME=${SERVER_NAME} nhưng vẫn dùng mật khẩu dev mặc định — cài máy chủ thật với --random-seed-password (cùng --fresh --yes nếu CSDL đã có)"
  fi
else
  echo "Mật khẩu:    SEED_DEFAULT_PASSWORD trong deploy/.env (chmod 600)"
fi
echo "Thời gian từng bước:"
for i in "${!STEP_NAMES[@]}"; do
  echo "  ${STEP_NAMES[$i]}: ${STEP_SECS[$i]} s"
done
echo "THOI_GIAN_TONG: ${TOTAL} s"
echo "Tiếp theo:   bash deploy/verify-all.sh --quick   (đầy đủ: bash deploy/verify-all.sh)"
ok "Cài đặt hoàn tất"
