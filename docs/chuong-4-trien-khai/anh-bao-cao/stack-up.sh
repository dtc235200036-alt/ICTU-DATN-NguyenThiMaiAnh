set -euo pipefail
source "$(dirname "$0")/stack-env.sh"
cd "$L"
t0=$(date +%s)
bash deploy/init.sh
C=(docker compose -f deploy/docker-compose.yml)
"${C[@]}" build ai
"${C[@]}" run --rm --no-deps -T -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 --entrypoint python ai -m app.download_model
echo "model ok $(( $(date +%s)-t0 )) s"
"${C[@]}" up -d --build --wait --wait-timeout 900
"${C[@]}" ps --format '{{.Service}}\t{{.Status}}'
echo "up ok $(( $(date +%s)-t0 )) s"
bash deploy/seed-ai.sh
echo "seed-ai ok $(( $(date +%s)-t0 )) s"
