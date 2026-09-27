#!/usr/bin/env bash
# tools/render-diagrams.sh - one-command render for PlantUML (*.puml), draw.io
# BPMN (*.drawio) and static HTML mockup screens (mockup/mh-NN.html).
#
# Usage: tools/render-diagrams.sh [--check] [--force] [PATH ...]
#   --check   Validate sources only (PlantUML -checkonly, drawio XML well-formedness).
#             Mockup screens are skipped entirely in --check mode.
#   --force   Re-render even when outputs are newer than their source.
#   PATH      File or directory (scanned recursively). Default: docs
#
# Works without Graphviz (falls back to -Playout=smetana) and without Figma.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)"
PLANTUML_CFG="$SCRIPT_DIR/plantuml.cfg"

PINNED_PLANTUML_URL="https://github.com/plantuml/plantuml/releases/download/v1.2026.8/plantuml-1.2026.8.jar"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/ntma-tools"
CACHE_JAR="$CACHE_DIR/plantuml-1.2026.8.jar"
FALLBACK_JAR="$HOME/.vscode/extensions/jebbs.plantuml-2.18.1/plantuml.jar"
DRAWIO_DOCKER_IMAGE="rlespinasse/drawio-desktop-headless:v1.72.0"
CACHED_APPIMAGE="$CACHE_DIR/drawio-x86_64-v31.5.3.AppImage"

CHECK_MODE=false
FORCE=false
PATHS=()

for arg in "$@"; do
  case "$arg" in
    --check) CHECK_MODE=true ;;
    --force) FORCE=true ;;
    *) PATHS+=("$arg") ;;
  esac
done
if [ ${#PATHS[@]} -eq 0 ]; then
  PATHS=("docs")
fi

RENDERED=0
SKIPPED=0
HAD_ERROR=0

log() { printf '%s\n' "$*" >&2; }

LAYOUT_FLAG=()
if ! command -v dot >/dev/null 2>&1; then
  LAYOUT_FLAG=(-Playout=smetana)
fi

# ---------------------------------------------------------------------------
# PlantUML jar resolution
# ---------------------------------------------------------------------------
resolve_plantuml_jar() {
  if [ -n "${PLANTUML_JAR:-}" ] && [ -f "$PLANTUML_JAR" ]; then
    printf '%s' "$PLANTUML_JAR"
    return 0
  fi
  if [ -f "$CACHE_JAR" ]; then
    printf '%s' "$CACHE_JAR"
    return 0
  fi
  mkdir -p "$CACHE_DIR"
  if curl -fsSL -o "$CACHE_JAR" "$PINNED_PLANTUML_URL" 2>/tmp/ntma-plantuml-dl.log; then
    log "Da tai PlantUML jar ve: $CACHE_JAR"
    log "sha256: $(sha256sum "$CACHE_JAR" | awk '{print $1}')"
    printf '%s' "$CACHE_JAR"
    return 0
  fi
  rm -f "$CACHE_JAR"
  if [ -f "$FALLBACK_JAR" ]; then
    log "CANH BAO: khong tai duoc PlantUML jar da pin, dung ban du phong: $FALLBACK_JAR"
    printf '%s' "$FALLBACK_JAR"
    return 0
  fi
  log "LOI: khong co PlantUML jar nao kha dung (tai that bai, khong co ban du phong)"
  return 1
}

# ---------------------------------------------------------------------------
# PlantUML (*.puml) rendering
# ---------------------------------------------------------------------------
render_puml() {
  local src="$1"
  local dir base png svg
  dir="$(dirname "$src")"
  base="$(basename "$src" .puml)"
  png="$dir/$base.png"
  svg="$dir/$base.svg"

  if $CHECK_MODE; then
    local out
    if out=$(java -jar "$JAR" -charset UTF-8 -config "$PLANTUML_CFG" "${LAYOUT_FLAG[@]}" -checkonly "$src" 2>&1); then
      RENDERED=$((RENDERED + 1))
    else
      log "$src: PlantUML -checkonly that bai:"
      log "$out"
      HAD_ERROR=1
    fi
    return 0
  fi

  if ! $FORCE && [ -f "$png" ] && [ -f "$svg" ] && [ "$png" -nt "$src" ] && [ "$svg" -nt "$src" ]; then
    SKIPPED=$((SKIPPED + 1))
    return 0
  fi

  local out1 out2
  if ! out1=$(java -jar "$JAR" -charset UTF-8 -config "$PLANTUML_CFG" "${LAYOUT_FLAG[@]}" -tpng "$src" 2>&1); then
    log "$src: render PNG that bai:"
    log "$out1"
    HAD_ERROR=1
    return 0
  fi
  if printf '%s' "$out1" | grep -qE 'Error line|Cannot run program|Some diagram description contains errors'; then
    log "$src: PlantUML bao loi khi render PNG:"
    log "$out1"
    HAD_ERROR=1
    return 0
  fi

  if ! out2=$(java -jar "$JAR" -charset UTF-8 -config "$PLANTUML_CFG" "${LAYOUT_FLAG[@]}" -tsvg "$src" 2>&1); then
    log "$src: render SVG that bai:"
    log "$out2"
    HAD_ERROR=1
    return 0
  fi
  if printf '%s' "$out2" | grep -qE 'Error line|Cannot run program|Some diagram description contains errors'; then
    log "$src: PlantUML bao loi khi render SVG:"
    log "$out2"
    HAD_ERROR=1
    return 0
  fi

  RENDERED=$((RENDERED + 1))
}

# ---------------------------------------------------------------------------
# draw.io (*.drawio) rendering
# ---------------------------------------------------------------------------
drawio_page_names() {
  python3 - "$1" <<'PYEOF'
import sys
import xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
root = tree.getroot()
for d in root.findall('.//diagram'):
    print(d.get('name') or d.get('id') or '')
PYEOF
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

export_drawio_page() {
  # $1=src(file path) $2=1-based page index $3=output png path
  local src="$1" idx="$2" out="$3"
  local abs_src abs_out_dir abs_out
  abs_src="$(cd "$(dirname "$src")" && pwd)/$(basename "$src")"
  abs_out_dir="$(cd "$(dirname "$out")" && pwd)"
  abs_out="$abs_out_dir/$(basename "$out")"

  if command -v drawio >/dev/null 2>&1; then
    if drawio -x -f png --scale 2 --page-index "$idx" -o "$abs_out" "$abs_src" >/tmp/ntma-drawio-export.log 2>&1 \
       && [ -s "$abs_out" ]; then
      return 0
    fi
    log "$src (trang $idx): drawio CLI xuat that bai (xem /tmp/ntma-drawio-export.log)"
  fi

  if command -v docker >/dev/null 2>&1; then
    if docker run --rm --shm-size=1g --user "$(id -u):$(id -g)" -e HOME=/tmp \
         -v "$REPO_ROOT:/data" -w /data "$DRAWIO_DOCKER_IMAGE" \
         -x -f png --scale 2 --page-index "$idx" \
         -o "${abs_out#"$REPO_ROOT"/}" "${abs_src#"$REPO_ROOT"/}" \
         >/tmp/ntma-drawio-export.log 2>&1 \
       && [ -s "$abs_out" ]; then
      return 0
    fi
    log "$src (trang $idx): docker drawio-desktop-headless xuat that bai (xem /tmp/ntma-drawio-export.log)"
  fi

  local appimage="${DRAWIO_APPIMAGE:-$CACHED_APPIMAGE}"
  if [ -f "$appimage" ]; then
    if "$appimage" --no-sandbox -x -f png --scale 2 --page-index "$idx" -o "$abs_out" "$abs_src" \
         >/tmp/ntma-drawio-export.log 2>&1 \
       && [ -s "$abs_out" ]; then
      return 0
    fi
    log "$src (trang $idx): AppImage drawio xuat that bai (xem /tmp/ntma-drawio-export.log)"
  fi

  log "$src (trang $idx): KHONG co cong cu xuat draw.io nao dung duoc. Hay mo https://app.diagrams.net/, mo file nay va xuat thu cong trang tuong ung thanh: $out"
  return 1
}

render_drawio() {
  local src="$1"
  local dir base
  dir="$(dirname "$src")"
  base="$(basename "$src" .drawio)"

  if $CHECK_MODE; then
    if python3 -c "import xml.etree.ElementTree as ET, sys; ET.parse(sys.argv[1])" "$src" 2>/tmp/ntma-drawio-check.log; then
      RENDERED=$((RENDERED + 1))
    else
      log "$src: khong phai XML hop le:"
      cat /tmp/ntma-drawio-check.log >&2
      HAD_ERROR=1
    fi
    return 0
  fi

  local pages
  if ! pages=$(drawio_page_names "$src"); then
    log "$src: khong doc duoc danh sach trang"
    HAD_ERROR=1
    return 0
  fi

  local idx=0
  while IFS= read -r pagename; do
    idx=$((idx + 1))
    [ -z "$pagename" ] && continue
    local slug out_png
    slug=$(slugify "$pagename")
    out_png="$dir/${base}-${slug}.png"

    if ! $FORCE && [ -s "$out_png" ] && [ "$out_png" -nt "$src" ]; then
      SKIPPED=$((SKIPPED + 1))
      continue
    fi

    if export_drawio_page "$src" "$idx" "$out_png"; then
      RENDERED=$((RENDERED + 1))
    else
      HAD_ERROR=1
    fi
  done <<<"$pages"
}

# ---------------------------------------------------------------------------
# Mockup screens: mockup/mh-NN.html -> mockup/mh-NN.png via headless Chrome
# ---------------------------------------------------------------------------
render_mockup() {
  local src="$1"
  local dir base
  dir="$(dirname "$src")"
  base="$(basename "$src" .html)"

  case "$(basename "$dir")" in
    mockup) ;;
    *) return 0 ;;
  esac
  case "$base" in
    mh-[0-9][0-9]) ;;
    *) return 0 ;;
  esac

  local png="$dir/$base.png"
  local css="$dir/antd-admin.css"

  local size w h
  size=$(grep -oE '<meta[^>]*name="mockup-size"[^>]*content="[0-9]+x[0-9]+"' "$src" \
         | grep -oE 'content="[0-9]+x[0-9]+"' | grep -oE '[0-9]+x[0-9]+' | head -1 || true)
  if [ -n "$size" ]; then
    w="${size%x*}"
    h="${size#*x}"
  else
    w=1440
    h=900
  fi
  if [ "$w" != "1440" ]; then
    log "$src: meta mockup-size phai co chieu rong 1440, hien tai la $w"
    HAD_ERROR=1
    return 0
  fi

  if ! $FORCE && [ -s "$png" ] && [ "$png" -nt "$src" ] && { [ ! -f "$css" ] || [ "$png" -nt "$css" ]; }; then
    SKIPPED=$((SKIPPED + 1))
    return 0
  fi

  local chrome="${CHROME:-/usr/bin/google-chrome}"
  if [ ! -x "$chrome" ] && ! command -v "$chrome" >/dev/null 2>&1; then
    log "$src: khong tim thay Chrome tai '$chrome'. Cai Google Chrome hoac dat bien CHROME."
    HAD_ERROR=1
    return 0
  fi

  local tmpdir abs_src abs_png
  tmpdir="$(mktemp -d)"
  abs_src="$(cd "$dir" && pwd)/$(basename "$src")"
  abs_png="$(cd "$dir" && pwd)/$(basename "$png")"

  set +e
  "$chrome" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
    --user-data-dir="$tmpdir" --window-size="${w},${h}" \
    --screenshot="$abs_png" "file://$abs_src" >/tmp/ntma-chrome-export.log 2>&1
  set -e
  rm -rf "$tmpdir"

  if [ ! -s "$abs_png" ]; then
    log "$src: Chrome khong tao duoc anh chup man hinh. Xem /tmp/ntma-chrome-export.log"
    cat /tmp/ntma-chrome-export.log >&2
    HAD_ERROR=1
    return 0
  fi
  RENDERED=$((RENDERED + 1))
}

# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------
collect_files() {
  local ext="$1"
  shift
  local p
  for p in "$@"; do
    if [ -f "$p" ]; then
      case "$p" in
        *".$ext") printf '%s\n' "$p" ;;
      esac
    elif [ -d "$p" ]; then
      find "$p" -type f -name "*.$ext" | sort
    fi
  done
}

JAR=""
if ! JAR=$(resolve_plantuml_jar); then
  exit 1
fi

mapfile -t PUML_FILES < <(collect_files puml "${PATHS[@]}")
mapfile -t DRAWIO_FILES < <(collect_files drawio "${PATHS[@]}")
mapfile -t HTML_FILES < <(collect_files html "${PATHS[@]}")

for f in "${PUML_FILES[@]:-}"; do
  [ -n "$f" ] || continue
  render_puml "$f" || true
done

for f in "${DRAWIO_FILES[@]:-}"; do
  [ -n "$f" ] || continue
  render_drawio "$f" || true
done

if ! $CHECK_MODE; then
  for f in "${HTML_FILES[@]:-}"; do
    [ -n "$f" ] || continue
    render_mockup "$f" || true
  done
fi

echo "rendered $RENDERED, skipped $SKIPPED"

if [ "$HAD_ERROR" -ne 0 ]; then
  exit 1
fi
exit 0
