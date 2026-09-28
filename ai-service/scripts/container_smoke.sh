#!/usr/bin/env bash
# Smoke container dịch vụ AI (D-02) — không chạm compose `ntma` hay MySQL chung.
#
#   bash ai-service/scripts/container_smoke.sh ntma-ai:test
#
# Chạy image với --memory=2g, cổng host tạm thời trên 127.0.0.1, SQLite trong
# container, profile bkai. Ưu tiên mount cache Hugging Face của host (chỉ đọc,
# HF_HUB_OFFLINE=1); nếu mô hình không nạp được từ đó thì chuyển sang named
# volume + tải trực tuyến và ghi lại đường đã dùng. Khóa API ngẫu nhiên, truyền
# qua --env-file (không lộ trong ps) và không bao giờ in ra stdout.
set -euo pipefail

IMAGE="${1:?Cách dùng: container_smoke.sh IMAGE}"
HF_CACHE="${HF_CACHE:-$HOME/.cache/huggingface}"
FALLBACK_VOLUME="${FALLBACK_VOLUME:-ntma-ai-smoke-models}"
NAME="ntma-ai-smoke-$$"
WORK="$(mktemp -d)"
KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

umask 077
cat >"$WORK/env" <<EOF
AI_API_KEY=$KEY
APP_ENV=production
AI_MODEL_PROFILE=bkai
DATABASE_URL=sqlite:////tmp/thesis_ai.db
TORCH_THREADS=4
EOF

start() {  # $1 = host-cache | named-volume
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  if [ "$1" = "host-cache" ]; then
    docker run -d --name "$NAME" --memory=2g --memory-swap=2g -p 127.0.0.1::8002 \
      --env-file "$WORK/env" -e HF_HUB_OFFLINE=1 \
      -v "$HF_CACHE:/models:ro" "$IMAGE" >/dev/null
  else
    docker run -d --name "$NAME" --memory=2g --memory-swap=2g -p 127.0.0.1::8002 \
      --env-file "$WORK/env" -v "$FALLBACK_VOLUME:/models" "$IMAGE" >/dev/null
  fi
}

wait_healthy() {  # trả 0 khi /health ok, 1 khi container dừng hoặc quá 600 s
  local deadline=$((SECONDS + 600))
  while [ $SECONDS -lt $deadline ]; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" != "true" ]; then
      return 1
    fi
    PORT="$(docker port "$NAME" 8002/tcp 2>/dev/null | head -1 | sed 's/.*://')"
    if [ -n "${PORT:-}" ] && curl -fsS "http://127.0.0.1:$PORT/health" 2>/dev/null \
        | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["status"]=="ok" else 1)' 2>/dev/null; then
      return 0
    fi
    sleep 3
  done
  return 1
}

CACHE_PATH="host-cache"
START_TS=$SECONDS
start "$CACHE_PATH"
if ! wait_healthy; then
  echo "Mô hình không nạp được từ cache host (read-only, offline) — chuyển sang named volume $FALLBACK_VOLUME"
  docker logs --tail 20 "$NAME" 2>&1 | grep -v -F "$KEY" || true
  CACHE_PATH="named-volume"
  START_TS=$SECONDS
  start "$CACHE_PATH"
  wait_healthy || { echo "FAIL: /health không đạt ok"; docker logs --tail 40 "$NAME" 2>&1 | grep -v -F "$KEY"; exit 1; }
fi
STARTUP_S=$((SECONDS - START_TS))
BASE="http://127.0.0.1:$PORT"
echo "model_cache_path=$CACHE_PATH startup_s=$STARTUP_S port=$PORT"

# Không phải root, đúng một worker.
UID_IN="$(docker exec "$NAME" id -u)"
[ "$UID_IN" = "10001" ] || { echo "FAIL: container chạy uid $UID_IN"; exit 1; }
WORKERS="$(docker exec "$NAME" sh -c 'cat /proc/1/cmdline | tr "\0" " "')"
echo "$WORKERS" | grep -q -- '--workers 1' || { echo "FAIL: uvicorn không chạy --workers 1"; exit 1; }

# 401 khi thiếu khóa.
CODE="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/check-title" \
  -H 'Content-Type: application/json' -d '{"text":"Quản lý thư viện"}')"
[ "$CODE" = "401" ] || { echo "FAIL: /check-title không khóa trả $CODE"; exit 1; }

# Dữ liệu tự soạn: hai tiêu đề ARCHIVE + một DOCUMENT ~300 câu, và truy vấn
# chép một phần (150 câu) + 150 câu mới.
python3 - "$WORK" <<'PY'
import itertools, json, sys
work = sys.argv[1]
subj = ["Hệ thống", "Mô-đun quản trị", "Ứng dụng di động", "Dịch vụ nền", "Cơ sở dữ liệu",
        "Giao diện người dùng", "Bộ phận kiểm thử", "Máy chủ ứng dụng", "Thuật toán gợi ý", "Tầng nghiệp vụ"]
verb = ["cho phép quản lý thông tin", "tự động tổng hợp báo cáo về", "ghi nhận và lưu trữ lịch sử của",
        "kiểm tra tính hợp lệ của", "gửi thông báo khi có thay đổi đối với", "phân quyền truy cập vào"]
obj = ["sinh viên và giảng viên hướng dẫn", "các đơn hàng trong ngày", "hồ sơ bệnh nhân tại phòng khám",
       "sách mượn trả của thư viện", "tiến độ thực hiện đồ án"]
ctx = ["nhằm giảm thời gian xử lý thủ công của cán bộ.", "trong môi trường mạng nội bộ của nhà trường.",
       "dựa trên kiến trúc hướng dịch vụ đã thiết kế ở chương trước.",
       "với dữ liệu được chuẩn hóa theo bảng mã Unicode.",
       "đáp ứng yêu cầu phi chức năng về thời gian phản hồi."]
sents = [f"{a} {b} {c} {d}" for a, b, c, d in itertools.product(subj, verb, obj, ctx)]
# Phần "mới" dùng bộ mảnh từ vựng khác hẳn → kỳ vọng ty_le_tong ≈ 50.
subj2 = ["Cảm biến độ ẩm", "Vườn rau thủy canh", "Bộ điều khiển trung tâm", "Mạch vi xử lý", "Trạm thời tiết"]
verb2 = ["đo đạc liên tục", "truyền tín hiệu vô tuyến về", "bật máy bơm tưới cho", "cảnh báo sớm hiện tượng", "tiết kiệm điện năng cho"]
obj2 = ["luống cải xanh ngoài trời", "nhà kính trồng dâu tây", "ao nuôi tôm thẻ chân trắng", "chuồng gà thả vườn", "đồi chè Tân Cương"]
ctx2 = ["vào mùa khô hanh kéo dài.", "suốt đêm mưa bão lớn.", "khi pin mặt trời sạc đầy.", "theo chu kỳ sinh trưởng tự nhiên.", "ở vùng trung du phía bắc.", "bằng sóng LoRa tầm xa."]
fresh = [f"{a} {b} {c} {d}" for a, b, c, d in itertools.product(subj2, verb2, obj2, ctx2)][:150]
corpus = sents[:300]
doc = "\n".join(" ".join(corpus[i:i + 3]) for i in range(0, 300, 3))
query = "\n".join(" ".join(corpus[i:i + 3]) for i in range(0, 150, 3))
query += "\n" + "\n".join(" ".join(fresh[i:i + 3]) for i in range(0, 150, 3))
json.dump({"id": 1, "type": "ARCHIVE", "text": "Xây dựng hệ thống quản lý thư viện cho trường trung học phổ thông"},
          open(f"{work}/t1.json", "w"), ensure_ascii=False)
json.dump({"id": 2, "type": "ARCHIVE", "text": "Ứng dụng học sâu nhận diện biển số xe máy tại bãi gửi xe"},
          open(f"{work}/t2.json", "w"), ensure_ascii=False)
json.dump({"id": 50, "type": "DOCUMENT", "text": doc}, open(f"{work}/doc.json", "w"), ensure_ascii=False)
json.dump({"text": "Phát triển phần mềm quản lý thư viện trường THPT", "top_k": 5},
          open(f"{work}/q.json", "w"), ensure_ascii=False)
json.dump({"ref_id": 0, "text": query, "top_k": 5, "nguong_doan": 90, "nguong_nguyen_van": 60},
          open(f"{work}/qd.json", "w"), ensure_ascii=False)
PY

post() {  # $1 path, $2 body file → stdout JSON
  curl -fsS -X POST "$BASE$1" -H 'Content-Type: application/json' \
    -H @"$WORK/hdr" --data-binary @"$2"
}
printf 'X-API-Key: %s\n' "$KEY" >"$WORK/hdr"

post /ingest "$WORK/t1.json" >/dev/null
post /ingest "$WORK/t2.json" >/dev/null
T0=$(date +%s.%N)
post /ingest "$WORK/doc.json" >"$WORK/ingest.out"
T1=$(date +%s.%N)
post /check-title "$WORK/q.json" >"$WORK/title.out"
T2=$(date +%s.%N)
post /check-document "$WORK/qd.json" >"$WORK/doc.out"
T3=$(date +%s.%N)

python3 - "$WORK" <<'PY'
import json, sys
w = sys.argv[1]
ingest = json.load(open(f"{w}/ingest.out"))
title = json.load(open(f"{w}/title.out"))
doc = json.load(open(f"{w}/doc.out"))
print("ingest_document:", ingest)
print("check_title_top:", title["matches"][:2])
print("check_document: ty_le_tong=%s so_doan=%s chi_tiet=%s do_an_trung=%s"
      % (doc["ty_le_tong"], doc["so_doan"], len(doc["chi_tiet"]), doc["do_an_trung"]))
assert ingest["chunk_count"] >= 290, "DOCUMENT phải có ~300 câu"
assert title["matches"] and title["matches"][0]["ref_id"] == 1, "tiêu đề diễn đạt lại không đứng đầu"
assert doc["ty_le_tong"] > 0, "bản chép một phần phải có ty_le_tong > 0"
PY

MEM_CUR="$(docker exec "$NAME" cat /sys/fs/cgroup/memory.current)"
MEM_PEAK="$(docker exec "$NAME" sh -c 'cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo 0')"
STATS="$(docker stats --no-stream --format '{{.MemUsage}}' "$NAME")"
OOM="$(docker inspect -f '{{.State.OOMKilled}}' "$NAME")"
SIZE="$(docker image inspect --format '{{.Size}}' "$IMAGE")"
LIMIT=$((2 * 1024 * 1024 * 1024))

python3 - <<PY
t0, t1, t2, t3 = $T0, $T1, $T2, $T3
print(f"ingest_document_300_s={t1 - t0:.2f} check_title_ms={(t2 - t1) * 1000:.0f} check_document_s={t3 - t2:.2f}")
PY
echo "docker_stats_mem=$STATS memory_current_mb=$((MEM_CUR / 1048576)) memory_peak_mb=$((MEM_PEAK / 1048576)) oom_killed=$OOM image_size_mb=$((SIZE / 1048576))"

[ "$OOM" = "false" ] || { echo "FAIL: OOMKilled"; exit 1; }
[ "$MEM_CUR" -lt "$LIMIT" ] || { echo "FAIL: bộ nhớ vượt 2 GiB"; exit 1; }
if docker logs "$NAME" 2>&1 | grep -q -F "$KEY"; then
  echo "FAIL: khóa API xuất hiện trong log container"; exit 1
fi
echo "CONTAINER SMOKE OK"
