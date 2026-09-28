#!/usr/bin/env bash
# Phase 5 (05-05, D-08): đưa hệ thống về TRẠNG THÁI DEMO đã biết trên stack
# đã seed — chạy trước mỗi buổi demo/tập dượt và sau mỗi lần chạy kịch bản.
#
#   bash deploy/demo-state.sh             # xóa trạng thái demo cũ + dựng lại
#   bash deploy/demo-state.sh --chi-xoa   # chỉ xóa (đợt K22 trống cho 5 SV demo)
#   bash deploy/demo-state.sh --dem       # chỉ ĐỌC: in chữ ký (số hàng + md5 cột trạng
#                                         # thái) của mọi hàng demo — verify-all so trước/sau
#
# Tài khoản demo DÀNH RIÊNG (không bộ kiểm thử tự động nào dùng; tự động dùng
# K95–K99, DTC225200094–100, GV023, GV025–GV030; smoke-test chỉ ĐỌC với
# DTC225200001/GV001):
#   SV  DTC225200011  chưa có đề tài — demo trực tiếp: đề xuất tên diễn đạt lại
#                     đề tài kho -> cảnh báo AI -> gửi; Bộ môn duyệt + phân
#                     công GV011; nộp đề cương chép nguyên văn -> "Đang kiểm tra"
#                     -> "Hoàn tất – x%"
#   SV  DTC225200012  đề tài đã phân công GV011; đề cương v1 = tệp B của một cặp
#                     CHEP_NGUYEN_VAN, kiểm tra xong (liệt kê đồ án nguồn trong
#                     kho), CHỜ GV011 duyệt (MH-09 / MH-14 đoạn tô sáng)
#   SV  DTC225200013  đề cương đã duyệt (tệp B cặp KHONG_LIEN_QUAN), 2 báo cáo
#                     tiến độ: mốc 1 đã được GV011 nhận xét, mốc 2 chờ nhận xét
#   SV  DTC225200014  báo cáo cuối đã kiểm tra, xếp lịch "Hội đồng demo K22",
#                     GV012 + GV013 đã chấm, GV014 CHƯA chấm (demo: GV014 chấm,
#                     Bộ môn chốt điểm -> tự lưu kho)
#   SV  DTC225200015  như 014 nhưng đủ 3 điểm, đã chốt và đã nằm trong Kho đồ án
#   GV  GV011 (GVHD), GV012 (chủ tịch), GV013 (thư ký), GV014 (ủy viên); Bộ môn `bomon`
#   Đợt: "Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)" (đợt K22 đang mở của seed)
#
# Tệp nộp lấy từ seed-data/ theo seed-data/manifest.json +
# ai-service/calibration/ket-qua-chi-tiet.json (chỉ các cặp đã hiệu chỉnh Đạt),
# CỐ Ý bỏ qua cặp CHEP_NGUYEN_VAN/KHONG_LIEN_QUAN đầu tiên — e2e-ai.sh dùng
# chúng và kỳ vọng đồ án nguồn đứng đầu là A của cặp; nếu cùng tệp B nằm sẵn
# trong chỉ mục (của SV demo) thì kết quả của e2e-ai sẽ bị lệch.
#
# An toàn (T-05-19): chỉ chọn hàng của 5 SV demo trong đợt K22 và hội đồng tên
# "Hội đồng demo K22"; DỪNG trước khi xóa nếu hội đồng đó có lịch/thành viên
# không thuộc tài khoản demo. Mốc tiến độ của đợt được get-or-create (không
# bao giờ xóa), chỉ đặt lại hạn nộp tương đối theo ngày chạy.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BASE="${BASE_URL:-https://localhost}"
COMPOSE=(docker compose -f "${SCRIPT_DIR}/docker-compose.yml")

DEMO_SV=(DTC225200011 DTC225200012 DTC225200013 DTC225200014 DTC225200015)
DEMO_GV=(GV011 GV012 GV013 GV014)
DOT_TEN="Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)"
HOI_DONG_TEN="Hội đồng demo K22"
DEMO_IN="'$(IFS=,; echo "${DEMO_SV[*]}" | sed "s/,/','/g")'"
DEMO_ALL_IN="'$(IFS=,; echo "${DEMO_SV[*]},${DEMO_GV[*]}" | sed "s/,/','/g")'"

CHI_XOA=0
DEM=0
case "${1:-}" in
  --chi-xoa) CHI_XOA=1 ;;
  --dem) DEM=1 ;;
  "") ;;
  -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
  *) echo "Dùng: bash deploy/demo-state.sh [--chi-xoa | --dem]" >&2; exit 2 ;;
esac

ok() { echo "OK: $1"; }
fail() { echo "FAIL: $1"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
T_BAT_DAU=$SECONDS

# sql Q — chạy trong container mysql với utf8mb4 (câu lệnh có chữ tiếng Việt).
sql() {
  "${COMPOSE[@]}" exec -T -e Q="$1" mysql sh -c \
    'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -N -B -u"$MYSQL_USER" thesis_core -e "$Q"' \
    </dev/null | tr -d '\r'
}
csv() { paste -sd, - | sed 's/^,*//; s/,*$//'; }

# call METHOD PATH TOKEN [curl args...] — thân vào $TMP/body, in mã HTTP.
call() {
  local method="$1" path="$2" token="$3"
  shift 3
  curl -sk -o "$TMP/body" -w '%{http_code}' -X "$method" "$BASE$path" \
    -H "Authorization: Bearer ${token}" "$@"
}
jget() {
  python3 -c "
import json
d = json.load(open('$TMP/body', encoding='utf-8'))
print($1)
" 2>/dev/null
}
# json_post TOKEN PATH PYDICT EXPECT — POST JSON dựng bằng Python (giữ tiếng Việt).
json_req() {
  local method="$1" token="$2" path="$3" pyexpr="$4" expect="$5" code
  python3 -c "import json; print(json.dumps($pyexpr, ensure_ascii=False))" > "$TMP/req.json"
  code="$(call "$method" "$path" "$token" -H 'Content-Type: application/json' --data-binary "@$TMP/req.json")"
  [ "$code" = "$expect" ] || fail "${method} ${path} trả ${code} (mong đợi ${expect}): $(head -c 400 "$TMP/body")"
}

# ------------------------------------------------------------------ định danh
SV_ROWS="$(sql "SELECT tk.ma_dang_nhap, sv.id, tk.id FROM tai_khoan tk JOIN sinh_vien sv ON sv.tai_khoan_id = tk.id WHERE tk.ma_dang_nhap IN (${DEMO_IN}) ORDER BY tk.ma_dang_nhap")"
[ "$(printf '%s\n' "$SV_ROWS" | grep -c .)" = "5" ] || fail "Không tìm đủ 5 SV demo (${DEMO_SV[*]}) — đã seed DATA-01 chưa?"
SV_IDS="$(printf '%s\n' "$SV_ROWS" | cut -f2 | csv)"
TK_DEMO_IDS="$(sql "SELECT id FROM tai_khoan WHERE ma_dang_nhap IN (${DEMO_ALL_IN})" | csv)"
[ "$(printf '%s' "$TK_DEMO_IDS" | tr ',' '\n' | grep -c .)" = "9" ] || fail "Không tìm đủ 9 tài khoản demo (5 SV + 4 GV)"
GV_DEMO_IDS="$(sql "SELECT gv.id FROM giang_vien gv JOIN tai_khoan tk ON tk.id = gv.tai_khoan_id WHERE tk.ma_dang_nhap IN (${DEMO_ALL_IN})" | csv)"
DOT_ID="$(sql "SELECT id FROM dot_do_an WHERE ten_dot = '${DOT_TEN}' AND khoa = 'K22' AND trang_thai = 'DANG_MO'")"
[ "$(printf '%s\n' "$DOT_ID" | grep -c .)" = "1" ] || fail "Không tìm thấy đúng một đợt đang mở '${DOT_TEN}' (nhận '${DOT_ID}')"

if [ "$DEM" = "1" ]; then
  # Chữ ký hàng demo: số hàng + md5 các cột trạng thái/điểm (phát hiện cả hàng bị SỬA).
  T_SEL="SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_ID} AND sinh_vien_id IN (${SV_IDS})"
  L_SEL="SELECT l.id FROM lich_bao_ve l JOIN hoi_dong h ON h.id = l.hoi_dong_id WHERE h.ten_hoi_dong = '${HOI_DONG_TEN}' OR l.de_tai_id IN (${T_SEL})"
  sql "SELECT 'de_tai', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, trang_thai, IFNULL(giang_vien_id, '-'), ten_de_tai) ORDER BY id)), '-') FROM de_tai WHERE id IN (${T_SEL})
UNION ALL SELECT 'tai_lieu_do_an', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, loai, so_phien_ban, ten_luu_tru) ORDER BY id)), '-') FROM tai_lieu_do_an WHERE de_tai_id IN (${T_SEL})
UNION ALL SELECT 'de_cuong', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, trang_thai) ORDER BY id)), '-') FROM de_cuong WHERE de_tai_id IN (${T_SEL})
UNION ALL SELECT 'ket_qua_kiem_tra', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, trang_thai, IFNULL(ty_le_tong, '-')) ORDER BY id)), '-') FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (${T_SEL})
UNION ALL SELECT 'bao_cao_tien_do', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, IFNULL(danh_gia, '-'), IFNULL(nhan_xet, '-')) ORDER BY id)), '-') FROM bao_cao_tien_do WHERE de_tai_id IN (${T_SEL})
UNION ALL SELECT 'hoi_dong', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, ngay_bao_ve, gio_bao_ve, phong) ORDER BY id)), '-') FROM hoi_dong WHERE ten_hoi_dong = '${HOI_DONG_TEN}'
UNION ALL SELECT 'lich_bao_ve', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, da_chot, IFNULL(diem_trung_binh, '-')) ORDER BY id)), '-') FROM lich_bao_ve WHERE id IN (SELECT id FROM (${L_SEL}) x)
UNION ALL SELECT 'diem_bao_ve', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, diem) ORDER BY id)), '-') FROM diem_bao_ve WHERE lich_bao_ve_id IN (SELECT id FROM (${L_SEL}) x)
UNION ALL SELECT 'do_an_kho', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, trang_thai_index, IFNULL(diem, '-'), IFNULL(tu_khoa, '-')) ORDER BY id)), '-') FROM do_an_kho WHERE de_tai_id IN (${T_SEL})
UNION ALL SELECT 'thong_bao', COUNT(*), IFNULL(MD5(GROUP_CONCAT(CONCAT_WS(':', id, da_doc) ORDER BY id)), '-') FROM thong_bao WHERE tai_khoan_id IN (${TK_DEMO_IDS})"
  exit 0
fi
ok "5 SV demo (sinh_vien.id ${SV_IDS}), 4 GV demo, đợt K22 id=${DOT_ID}"

# ------------------------------------------------------------------ xóa
TOPIC_IDS="$(sql "SELECT id FROM de_tai WHERE dot_do_an_id = ${DOT_ID} AND sinh_vien_id IN (${SV_IDS})" | csv)"
HD_IDS="$(sql "SELECT id FROM hoi_dong WHERE ten_hoi_dong = '${HOI_DONG_TEN}'" | csv)"
T_IN="${TOPIC_IDS:-0}"
HD_IN="${HD_IDS:-0}"

# An toàn: hội đồng demo chỉ được chứa lịch của đề tài demo và thành viên demo.
LA_LICH="$(sql "SELECT COUNT(*) FROM lich_bao_ve WHERE hoi_dong_id IN (${HD_IN}) AND de_tai_id NOT IN (${T_IN})")"
LA_TV="$(sql "SELECT COUNT(*) FROM thanh_vien_hoi_dong WHERE hoi_dong_id IN (${HD_IN}) AND giang_vien_id NOT IN (${GV_DEMO_IDS:-0})")"
LA_KHO="$(sql "SELECT COUNT(*) FROM do_an_kho WHERE de_tai_id IN (${T_IN}) AND (sinh_vien_id IS NULL OR sinh_vien_id NOT IN (${SV_IDS}))")"
LA_LICH_DT="$(sql "SELECT COUNT(*) FROM lich_bao_ve WHERE de_tai_id IN (${T_IN}) AND hoi_dong_id NOT IN (${HD_IN})")"
if [ "$LA_LICH" != "0" ] || [ "$LA_TV" != "0" ] || [ "$LA_KHO" != "0" ] || [ "$LA_LICH_DT" != "0" ]; then
  fail "Dừng, KHÔNG xóa gì: hàng được chọn dính tài khoản ngoài demo (lịch lạ ${LA_LICH}, thành viên lạ ${LA_TV}, kho lạ ${LA_KHO}, lịch đề tài demo ở hội đồng khác ${LA_LICH_DT})"
fi

DOC_IDS="$(sql "SELECT id FROM tai_lieu_do_an WHERE de_tai_id IN (${T_IN})" | csv)"
KHO_IDS="$(sql "SELECT id FROM do_an_kho WHERE de_tai_id IN (${T_IN})" | csv)"
DEM="$(sql "SELECT CONCAT_WS(' ',
  (SELECT COUNT(*) FROM de_tai WHERE id IN (${T_IN})),
  (SELECT COUNT(*) FROM tai_lieu_do_an WHERE de_tai_id IN (${T_IN})),
  (SELECT COUNT(*) FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (${T_IN})),
  (SELECT COUNT(*) FROM bao_cao_tien_do WHERE de_tai_id IN (${T_IN})),
  (SELECT COUNT(*) FROM hoi_dong WHERE id IN (${HD_IN})),
  (SELECT COUNT(*) FROM lich_bao_ve WHERE hoi_dong_id IN (${HD_IN}) OR de_tai_id IN (${T_IN})),
  (SELECT COUNT(*) FROM diem_bao_ve WHERE lich_bao_ve_id IN (SELECT id FROM lich_bao_ve WHERE hoi_dong_id IN (${HD_IN}) OR de_tai_id IN (${T_IN}))),
  (SELECT COUNT(*) FROM do_an_kho WHERE de_tai_id IN (${T_IN})),
  (SELECT COUNT(*) FROM thong_bao WHERE tai_khoan_id IN (${TK_DEMO_IDS})))")"
read -r n_dt n_tl n_kq n_bc n_hd n_lich n_diem n_kho n_tb <<<"$DEM"
ok "Trạng thái demo cũ: ${n_dt} đề tài, ${n_tl} tài liệu, ${n_kq} kết quả kiểm tra, ${n_bc} báo cáo tiến độ, ${n_hd} hội đồng demo, ${n_lich} lịch, ${n_diem} điểm, ${n_kho} bản ghi kho, ${n_tb} thông báo"

purge() {
  [ -n "$2" ] || return 0
  "${COMPOSE[@]}" exec -T api python -m app.services.ai_index purge --loai "$1" --ids "$2" </dev/null >/dev/null \
    || fail "Không gỡ được ${1} ${2} khỏi chỉ mục AI (python -m app.services.ai_index purge)"
}
purge TOPIC "${TOPIC_IDS}"
purge DOCUMENT "${DOC_IDS}"
purge ARCHIVE "${KHO_IDS}"
[ -z "${TOPIC_IDS}${DOC_IDS}${KHO_IDS}" ] || ok "Đã gỡ khỏi chỉ mục AI: TOPIC [${TOPIC_IDS}] DOCUMENT [${DOC_IDS}] ARCHIVE [${KHO_IDS}]"

FILES="$(sql "SELECT ten_luu_tru FROM tai_lieu_do_an WHERE de_tai_id IN (${T_IN})")"
while IFS= read -r ten; do
  [ -z "$ten" ] && continue
  case "$ten" in /*|*..*) fail "Tên lưu trữ bất thường: ${ten}" ;; esac
  "${COMPOSE[@]}" exec -T api rm -f "/data/uploads/${ten}" </dev/null >/dev/null
done <<<"${FILES}"

LICH_SEL="SELECT id FROM lich_bao_ve WHERE hoi_dong_id IN (${HD_IN}) OR de_tai_id IN (${T_IN})"
sql "DELETE FROM thong_bao WHERE tai_khoan_id IN (${TK_DEMO_IDS});
DELETE FROM diem_bao_ve WHERE lich_bao_ve_id IN (SELECT id FROM (${LICH_SEL}) x);
DELETE FROM lich_bao_ve WHERE hoi_dong_id IN (${HD_IN}) OR de_tai_id IN (${T_IN});
DELETE FROM thanh_vien_hoi_dong WHERE hoi_dong_id IN (${HD_IN});
DELETE FROM hoi_dong WHERE id IN (${HD_IN});
DELETE FROM do_an_kho WHERE de_tai_id IN (${T_IN});
DELETE FROM bao_cao_tien_do WHERE de_tai_id IN (${T_IN});
DELETE FROM luot_duyet_de_cuong WHERE de_cuong_id IN (SELECT id FROM de_cuong WHERE de_tai_id IN (${T_IN}));
DELETE FROM chi_tiet_trung_lap WHERE ket_qua_id IN (SELECT id FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (${T_IN}));
DELETE FROM ket_qua_kiem_tra_trung_lap WHERE de_tai_id IN (${T_IN});
DELETE FROM tai_lieu_do_an WHERE de_tai_id IN (${T_IN});
DELETE FROM de_cuong WHERE de_tai_id IN (${T_IN});
DELETE FROM de_tai WHERE id IN (${T_IN});" >/dev/null

CON="$(sql "SELECT (SELECT COUNT(*) FROM de_tai WHERE dot_do_an_id = ${DOT_ID} AND sinh_vien_id IN (${SV_IDS})) + (SELECT COUNT(*) FROM hoi_dong WHERE ten_hoi_dong = '${HOI_DONG_TEN}')")"
[ "$CON" = "0" ] || fail "Sau khi xóa vẫn còn ${CON} đề tài/hội đồng demo"
N011="$(sql "SELECT COUNT(*) FROM de_tai dt JOIN sinh_vien sv ON sv.id = dt.sinh_vien_id JOIN tai_khoan tk ON tk.id = sv.tai_khoan_id WHERE tk.ma_dang_nhap = 'DTC225200011'")"
[ "$N011" = "0" ] || fail "DTC225200011 vẫn còn ${N011} đề tài"
ok "Đã xóa trạng thái demo (DTC225200011 không còn đề tài nào) sau $((SECONDS - T_BAT_DAU)) s"

if [ "$CHI_XOA" = "1" ]; then
  ok "--chi-xoa: dừng sau bước xóa ($((SECONDS - T_BAT_DAU)) s)"
  exit 0
fi

# ------------------------------------------------------------------ dựng lại
T_DUNG=$SECONDS
python3 - "$REPO_ROOT" > "$TMP/tep.tsv" <<'PY'
import json, sys
root = sys.argv[1]
manifest = json.load(open(f"{root}/seed-data/manifest.json", encoding="utf-8"))
dat = {c["ma_cap"] for c in json.load(open(f"{root}/ai-service/calibration/ket-qua-chi-tiet.json", encoding="utf-8"))["cap"] if c["dat"]}
def cac(loai):
    return [c for c in manifest["cap"] if c["loai"] == loai and c["ma_cap"] in dat]
chep, khac, cung = cac("CHEP_NGUYEN_VAN"), cac("KHONG_LIEN_QUAN"), cac("CUNG_LINH_VUC")
# [0] của CHEP/KHONG_LIEN_QUAN thuộc về e2e-ai.sh; chep[2] để SV 011 nộp trực tiếp khi demo.
chon = {
    "DC012": chep[1], "DC013": khac[1], "DC014": cung[1], "DC015": cung[2],
    "BC014": khac[2], "BC015": khac[3],
}
for k, c in chon.items():
    print("\t".join([k, c["ma_cap"], f"{root}/seed-data/{c['B']['tep']}", f"{c['A']['ten_de_tai']} ({c['A']['khoa']})"]))
PY
tep() { grep "^$1	" "$TMP/tep.tsv" | cut -f3; }
nhan() { grep "^$1	" "$TMP/tep.tsv" | cut -f2; }
for k in DC012 DC013 DC014 DC015 BC014 BC015; do
  [ -f "$(tep $k)" ] || fail "Không thấy tệp seed cho ${k}: $(tep $k)"
done
CHEP012_NGUON="$(grep '^DC012	' "$TMP/tep.tsv" | cut -f4)"

declare -A TOKEN
for ma in bomon "${DEMO_SV[@]:1}" "${DEMO_GV[@]}"; do
  TOKEN[$ma]="$(bash "${SCRIPT_DIR}/api-login.sh" "$ma")" || fail "Không đăng nhập được ${ma}"
done
curl -sk "$BASE/api/lecturers" -H "Authorization: Bearer ${TOKEN[bomon]}" > "$TMP/gv.json"
gv_id() {
  python3 -c "import json,sys; print(next(g['id'] for g in json.load(open('$TMP/gv.json')) if g.get('ma_giang_vien') == sys.argv[1]))" "$1" \
    || fail "Không tìm được id ${1} trong /api/lecturers"
}
GV011="$(gv_id GV011)"; GV012="$(gv_id GV012)"; GV013="$(gv_id GV013)"; GV014="$(gv_id GV014)"

# Mốc tiến độ của đợt (get-or-create, hạn tương đối theo ngày chạy, kẹp trong đợt).
HOM_NAY="$(TZ=Asia/Ho_Chi_Minh date +%F)"
DOT_KT="$(sql "SELECT IFNULL(ngay_ket_thuc, '2099-12-31') FROM dot_do_an WHERE id = ${DOT_ID}")"
han() { local d; d="$(TZ=Asia/Ho_Chi_Minh date -d "+$1 days" +%F)"; [[ "$d" > "$DOT_KT" ]] && d="$DOT_KT"; echo "$d"; }
call GET "/api/progress/milestones?dot_do_an_id=${DOT_ID}" "${TOKEN[bomon]}" >/dev/null
declare -A MOC
for spec in "1|Mốc 1 – Phân tích và thiết kế hệ thống|3" "2|Mốc 2 – Cài đặt các chức năng chính|17" "3|Mốc 3 – Kiểm thử và hoàn thiện báo cáo|45"; do
  IFS='|' read -r so ten ngay <<<"$spec"
  call GET "/api/progress/milestones?dot_do_an_id=${DOT_ID}" "${TOKEN[bomon]}" >/dev/null
  id="$(python3 -c "import json,sys; print(next((m['id'] for m in json.load(open('$TMP/body', encoding='utf-8')) if m['ten_moc'] == sys.argv[1]), ''))" "$ten")"
  if [ -z "$id" ]; then
    json_req POST "${TOKEN[bomon]}" /api/progress/milestones "{'dot_do_an_id': ${DOT_ID}, 'ten_moc': '''${ten}''', 'han_nop': '$(han "$ngay")'}" 201
    id="$(jget "d['id']")"
  else
    json_req PUT "${TOKEN[bomon]}" "/api/progress/milestones/${id}" "{'dot_do_an_id': ${DOT_ID}, 'ten_moc': '''${ten}''', 'han_nop': '$(han "$ngay")'}" 200
  fi
  MOC[$so]="$id"
done
ok "Mốc tiến độ đợt K22: ${MOC[1]}, ${MOC[2]}, ${MOC[3]} (hạn +3/+17/+45 ngày, tối đa ${DOT_KT})"

declare -A DE_TAI
de_xuat() {  # ma ten linh_vuc
  json_req POST "${TOKEN[$1]}" /api/topics "{'dot_do_an_id': ${DOT_ID}, 'ten_de_tai': '''$2''', 'linh_vuc': '''$3''', 'gui': True}" 201
  DE_TAI[$1]="$(jget "d['id']")"
  json_req POST "${TOKEN[bomon]}" "/api/topic-approvals/${DE_TAI[$1]}/approve" "{'giang_vien_id': ${GV011}}" 200
  [ "$(jget "d['trang_thai']")" = "DA_PHAN_CONG" ] || fail "Đề tài của $1 không Đã phân công"
}
de_xuat DTC225200012 "Xây dựng hệ thống quản lý thiết bị phòng máy thực hành cho Khoa Công nghệ thông tin" "Hệ thống thông tin"
de_xuat DTC225200013 "Phát triển ứng dụng hỗ trợ sinh viên tìm nhà trọ quanh Đại học Thái Nguyên" "Công nghệ phần mềm"
de_xuat DTC225200014 "Xây dựng hệ thống quản lý câu lạc bộ sinh viên Trường Đại học Công nghệ Thông tin và Truyền thông" "Hệ thống thông tin"
de_xuat DTC225200015 "Phát triển ứng dụng di động theo dõi lịch tiêm chủng cho trẻ em tại trạm y tế phường Tân Thịnh" "Công nghệ phần mềm"
ok "4 đề tài tự đề xuất (012..015) đã được Bộ môn duyệt, phân công GV011: ${DE_TAI[DTC225200012]}, ${DE_TAI[DTC225200013]}, ${DE_TAI[DTC225200014]}, ${DE_TAI[DTC225200015]}"

# nop PATH_API TOKEN FILE -> id tài liệu; cho_kiem_tra TOKEN DOC_ID -> "ty_le|so_doan"
nop() {
  local ct="application/pdf" code
  case "$3" in *.docx) ct="application/vnd.openxmlformats-officedocument.wordprocessingml.document" ;; esac
  code="$(call POST "$1" "$2" -F "file=@$3;type=${ct}")"
  [ "$code" = "202" ] || fail "POST $1 ($(basename "$3")) trả ${code}: $(head -c 300 "$TMP/body")"
  jget "d['phien_ban'][0]['tai_lieu']['id']"
}
cho_kiem_tra() {
  local han=$((SECONDS + 90)) trang
  while :; do
    call GET "/api/documents/$2/check" "$1" >/dev/null
    trang="$(jget "d['trang_thai']")"
    [ "$trang" = "HOAN_TAT" ] && break
    [ "$trang" = "LOI" ] && fail "Kiểm tra tài liệu $2 kết thúc LOI"
    [ "$SECONDS" -lt "$han" ] || fail "Kiểm tra tài liệu $2 chưa HOAN_TAT sau 90 s (${trang})"
    sleep 0.5
  done
  cp "$TMP/body" "$TMP/check-$2.json"
  jget "f\"{d['ty_le_tong']}%\""
}
duyet_de_cuong() {  # ma doc_id
  json_req POST "${TOKEN[GV011]}" "/api/outlines/${DE_TAI[$1]}/review" "{'tai_lieu_do_an_id': $2, 'ket_qua': 'DA_DUYET', 'nhan_xet': 'Đề cương rõ ràng, đồng ý cho thực hiện.'}" 200
  [ "$(jget "d['trang_thai']")" = "DA_DUYET" ] || fail "Đề cương của $1 không Đã duyệt"
}

declare -A DOC
for ma in DTC225200012 DTC225200013 DTC225200014 DTC225200015; do
  k="DC${ma: -3}"
  DOC[$k]="$(nop "/api/outlines/${DE_TAI[$ma]}/submit" "${TOKEN[$ma]}" "$(tep "$k")")"
done
declare -A TL
for ma in DTC225200012 DTC225200013 DTC225200014 DTC225200015; do
  k="DC${ma: -3}"
  TL[$k]="$(cho_kiem_tra "${TOKEN[$ma]}" "${DOC[$k]}")"
done
python3 - "$TMP/check-${DOC[DC012]}.json" "$CHEP012_NGUON" <<'PY' || fail "Đề cương 012 không liệt kê đúng đồ án nguồn chép nguyên văn"
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
assert d["vuot_nguong"] is True, d["vuot_nguong"]
assert d["do_an_trung"] and d["do_an_trung"][0]["doi_tuong_trung"] == sys.argv[2], [m["doi_tuong_trung"] for m in d["do_an_trung"]]
assert any("nguyên văn" in (s["vi_tri"] or "") for s in d["chi_tiet"])
PY
ok "Đề cương 012 ($(nhan DC012)-B) Hoàn tất ${TL[DC012]}, vượt ngưỡng, đồ án nguồn '${CHEP012_NGUON}' — CHỜ GV011 duyệt"
for ma in DTC225200013 DTC225200014 DTC225200015; do duyet_de_cuong "$ma" "${DOC[DC${ma: -3}]}"; done
ok "Đề cương 013/014/015 ($(nhan DC013)/$(nhan DC014)/$(nhan DC015)-B, ${TL[DC013]}/${TL[DC014]}/${TL[DC015]}) — GV011 đã duyệt"

# UC3: 013 nộp mốc 1 + mốc 2; GV011 nhận xét mốc 1.
for spec in "1|Đã hoàn thành khảo sát nhu cầu thuê trọ của 120 sinh viên, đặc tả 14 use case và thiết kế CSDL (9 bảng)." \
            "2|Đã cài đặt tìm kiếm phòng trọ theo bản đồ, lọc theo giá/khoảng cách và đăng tin cho chủ trọ; đang tích hợp đánh giá phòng."; do
  IFS='|' read -r so nd <<<"$spec"
  code="$(call POST "/api/progress/reports/${MOC[$so]}" "${TOKEN[DTC225200013]}" --form-string "noi_dung=${nd}")"
  [ "$code" = "200" ] || fail "013 nộp báo cáo mốc ${so} trả ${code}: $(head -c 300 "$TMP/body")"
done
call GET "/api/progress/topics/${DE_TAI[DTC225200013]}" "${TOKEN[GV011]}" >/dev/null
BC1="$(jget "next(m['bao_cao']['id'] for m in d['moc'] if m['id'] == ${MOC[1]})")"
json_req POST "${TOKEN[GV011]}" "/api/progress/reports/${BC1}/review" "{'nhan_xet': 'Phân tích đầy đủ, thiết kế CSDL hợp lý. Bổ sung sơ đồ tuần tự cho chức năng đăng tin.', 'danh_gia': 'DAT'}" 200
ok "013: 2 báo cáo tiến độ (mốc 1 GV011 đã nhận xét Đạt, mốc 2 chờ nhận xét)"

# UC4: báo cáo cuối 014/015 -> hội đồng demo -> điểm.
for ma in DTC225200014 DTC225200015; do
  k="BC${ma: -3}"
  DOC[$k]="$(nop "/api/defense/final-reports/${DE_TAI[$ma]}" "${TOKEN[$ma]}" "$(tep "$k")")"
done
for ma in DTC225200014 DTC225200015; do
  k="BC${ma: -3}"
  TL[$k]="$(cho_kiem_tra "${TOKEN[$ma]}" "${DOC[$k]}")"
done
ok "Báo cáo cuối 014/015 ($(nhan BC014)/$(nhan BC015)-B) Hoàn tất ${TL[BC014]}/${TL[BC015]}"

json_req POST "${TOKEN[bomon]}" /api/defense/committees "{'ten_hoi_dong': '''${HOI_DONG_TEN}''', 'ngay_bao_ve': '${HOM_NAY}', 'gio_bao_ve': '08:00', 'phong': 'C2-301', 'thanh_vien': [{'giang_vien_id': ${GV012}, 'vai_tro': 'CHU_TICH'}, {'giang_vien_id': ${GV013}, 'vai_tro': 'THU_KY'}, {'giang_vien_id': ${GV014}, 'vai_tro': 'UY_VIEN'}]}" 201
HD="$(jget "d['id']")"
for ma in DTC225200015 DTC225200014; do
  json_req POST "${TOKEN[bomon]}" "/api/defense/committees/${HD}/schedules" "{'de_tai_id': ${DE_TAI[$ma]}}" 201
done
call GET "/api/defense/committees/${HD}" "${TOKEN[bomon]}" >/dev/null
LICH015="$(jget "next(r['id'] for r in d['lich'] if r['de_tai_id'] == ${DE_TAI[DTC225200015]})")"
LICH014="$(jget "next(r['id'] for r in d['lich'] if r['de_tai_id'] == ${DE_TAI[DTC225200014]})")"
cham() {  # gv lich diem nhan_xet
  json_req PUT "${TOKEN[$1]}" "/api/defense/schedules/$2/score" "{'diem': $3, 'nhan_xet': '''$4'''}" 200
}
cham GV012 "$LICH015" 8.5 "Ứng dụng hoàn chỉnh, trình bày rõ ràng; cần đánh giá thêm trên thiết bị thật."
cham GV013 "$LICH015" 9.0 "Kiến trúc hợp lý, kiểm thử đầy đủ."
cham GV014 "$LICH015" 8.0 "Phần thông báo nhắc lịch còn đơn giản."
code="$(call POST "/api/defense/schedules/${LICH015}/finalize" "${TOKEN[bomon]}")"
[ "$code" = "200" ] || fail "Bộ môn chốt điểm 015 trả ${code}: $(head -c 300 "$TMP/body")"
KHO015="$(jget "d['do_an_kho_id']")"
DTB015="$(jget "d['lich']['diem_trung_binh']")"
cham GV012 "$LICH014" 8.0 "Chức năng quản lý thành viên và sự kiện đầy đủ; giao diện cần thống nhất hơn."
cham GV013 "$LICH014" 8.5 "Báo cáo trình bày tốt, có số liệu thử nghiệm."
han_kho=$((SECONDS + 30))
until [ "$(sql "SELECT CONCAT(nguon,'|',trang_thai_index) FROM do_an_kho WHERE id = ${KHO015}")" = "HE_THONG|DA_INDEX" ]; do
  [ "$SECONDS" -lt "$han_kho" ] || fail "Bản ghi kho ${KHO015} của 015 chưa DA_INDEX sau 30 s"
  sleep 0.5
done
ok "Hội đồng demo K22 (id=${HD}, ${HOM_NAY} 08:00, C2-301: GV012 chủ tịch, GV013 thư ký, GV014 ủy viên): 015 đủ 3 điểm, đã chốt TB ${DTB015}, lưu kho id=${KHO015} (DA_INDEX); 014 có 2/3 điểm (GV014 chưa chấm)"

echo
echo "=== Trạng thái demo (đợt K22 id=${DOT_ID})"
printf '%-14s %-9s %s\n' "DTC225200011" "—" "chưa có đề tài (demo trực tiếp: đề xuất -> cảnh báo AI -> gửi -> duyệt -> nộp $(python3 - "$REPO_ROOT" <<'PY'
import json, sys
root = sys.argv[1]
m = json.load(open(f"{root}/seed-data/manifest.json", encoding="utf-8"))
dat = {c["ma_cap"] for c in json.load(open(f"{root}/ai-service/calibration/ket-qua-chi-tiet.json", encoding="utf-8"))["cap"] if c["dat"]}
print([c for c in m["cap"] if c["loai"] == "CHEP_NGUYEN_VAN" and c["ma_cap"] in dat][2]["B"]["tep"])
PY
))"
printf '%-14s %-9s %s\n' "DTC225200012" "${DE_TAI[DTC225200012]}" "đề cương v1 $(nhan DC012)-B, Hoàn tất ${TL[DC012]}, chờ GV011 duyệt"
printf '%-14s %-9s %s\n' "DTC225200013" "${DE_TAI[DTC225200013]}" "đề cương đã duyệt; tiến độ: mốc 1 đã nhận xét, mốc 2 chờ nhận xét"
printf '%-14s %-9s %s\n' "DTC225200014" "${DE_TAI[DTC225200014]}" "báo cáo cuối ${TL[BC014]}; Hội đồng demo K22: 2/3 điểm (GV014 chưa chấm)"
printf '%-14s %-9s %s\n' "DTC225200015" "${DE_TAI[DTC225200015]}" "đã chốt TB ${DTB015}, trong Kho đồ án (id ${KHO015})"
ok "Dựng trạng thái demo xong: dựng $((SECONDS - T_DUNG)) s, tổng $((SECONDS - T_BAT_DAU)) s"
