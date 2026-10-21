"""Sinh danh sách SV/GV hư cấu cho stack chụp ảnh: giữ thứ tự dòng (phân công GVHD
mặc định phụ thuộc thứ tự), giữ mã SV mà các script deploy/tools tham chiếu, thay mọi
họ tên, email và các mã SV còn lại bằng giá trị hư cấu. Không in dữ liệu thật."""
import csv, random, re, subprocess, sys, unicodedata
repo, out = sys.argv[1], sys.argv[2]
rng = random.Random(20261021)
ho = ["Nguyễn","Trần","Lê","Phạm","Hoàng","Vũ","Đặng","Bùi","Đỗ","Hồ","Ngô","Dương","Lý","Đinh","Phan","Tạ","Lương","Mai","Cao","Triệu"]
dem_nam = ["Văn","Đức","Minh","Quang","Hữu","Thành","Gia","Tuấn","Ngọc","Xuân"]
dem_nu = ["Thị","Thu","Ngọc","Thanh","Phương","Bảo","Khánh","Hồng","Minh","Diệu"]
ten_nam = ["An","Bình","Cường","Dũng","Hải","Hiếu","Hưng","Khoa","Kiên","Long","Nam","Phong","Quân","Sơn","Tài","Thắng","Trung","Tùng","Việt","Vinh"]
ten_nu = ["Anh","Chi","Dung","Giang","Hà","Hạnh","Hoa","Hương","Lan","Linh","Mai","Ngân","Nhung","Oanh","Phương","Quỳnh","Thảo","Trang","Uyên","Yến"]
def ten():
    if rng.random() < 0.5:
        return f"{rng.choice(ho)} {rng.choice(dem_nam)} {rng.choice(ten_nam)}"
    return f"{rng.choice(ho)} {rng.choice(dem_nu)} {rng.choice(ten_nu)}"
ref = set(subprocess.run(
    "grep -rhoE 'DTC[0-9]{9}' deploy tools backend/tests frontend/src || true",
    shell=True, cwd=repo, capture_output=True, text=True).stdout.split())
nfc = lambda s: unicodedata.normalize("NFC", s)
with open(f"{repo}/backend/app/seed_data/sinh_vien.csv", encoding="utf-8-sig") as f:
    sv = list(csv.DictReader(f))
kept = 0
with open(f"{out}/sinh_vien.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["ma_so_sinh_vien","ho_ten","lop"])
    for i, r in enumerate(sv, 1):
        ma = r["ma_so_sinh_vien"].strip()
        if ma in ref: kept += 1
        else: ma = f"DTC22529{i:04d}"
        w.writerow([ma, nfc(ten()), r["lop"].strip()])
with open(f"{repo}/backend/app/seed_data/giang_vien.csv", encoding="utf-8-sig") as f:
    gv = list(csv.DictReader(f))
with open(f"{out}/giang_vien.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["ma_giang_vien","ho_ten","hoc_vi","email","bo_mon"])
    for r in gv:
        ma = r["ma_giang_vien"].strip()
        w.writerow([ma, nfc(ten()), r["hoc_vi"].strip(), f"{ma.lower()}@ntma-demo.edu.vn", r["bo_mon"].strip()])
print(f"SV: {len(sv)} dòng, giữ {kept} mã được script tham chiếu; GV: {len(gv)} dòng")
