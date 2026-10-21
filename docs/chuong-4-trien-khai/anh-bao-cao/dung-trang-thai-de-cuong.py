"""Dựng trạng thái cho ảnh chụp luồng đề cương hai cấp trên stack cô lập (dữ liệu hư cấu).

4 SV trong lớp hướng dẫn của GV011 (không thuộc 5 SV demo):
  A: tên file đúng mẫu, GVHD đã duyệt -> chờ GVHD nộp lên Bộ môn
  B: tên file sai họ tên (không dấu), GVHD đã duyệt -> chưa nộp được, có nút đổi tên
  C: GVHD đã nộp lên Bộ môn -> chờ Bộ môn phê duyệt (tải PDF ký số)
  D: Bộ môn đã phê duyệt kèm PDF ký số -> DA_DUYET
Mật khẩu đọc từ container api, không in ra."""
import json, os, ssl, subprocess, sys, time, uuid, urllib.request, urllib.error
L = os.environ["L"]
BASE = f"https://localhost:{os.environ['HTTPS_PORT']}"
CTX = ssl._create_unverified_context()
sys.path.insert(0, f"{L}/backend/tests")
from pdf_sign_helper import sign_pdf  # noqa: E402

PW = subprocess.run(["docker", "compose", "-f", f"{L}/deploy/docker-compose.yml", "exec", "-T", "api",
                     "printenv", "SEED_DEFAULT_PASSWORD"], capture_output=True, text=True, cwd=L).stdout.strip()

def req(method, path, token=None, body=None, files=None, fields=None):
    headers = {}
    data = None
    if token: headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode(); headers["Content-Type"] = "application/json"
    if files:
        b = uuid.uuid4().hex; parts = []
        for k, v in (fields or {}).items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        for k, (fn, content, ctype) in files.items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{fn}"\r\nContent-Type: {ctype}\r\n\r\n'.encode() + content + b"\r\n")
        parts.append(f"--{b}--\r\n".encode()); data = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={b}"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=120) as resp:
            t = resp.read(); return resp.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e:
        t = e.read(); return e.code, (json.loads(t) if t else None)

def login(u):
    s, d = req("POST", "/api/auth/login", body={"dang_nhap": u, "mat_khau": PW})
    assert s == 200, (u, s, d); return d["access_token"]

gv, bm = login("GV011"), login("bomon")
s, ms = req("GET", "/api/assignments/my-students", gv); assert s == 200, (s, ms)
ms = ms[0] if isinstance(ms, list) else ms; print("dot:", ms["dot_do_an"]); dot = ms["dot_do_an"]["id"]
demo = {"DTC235200139", "DTC235200258", "DTC235200325", "DTC235200340", "DTC235270078"}
free = [i for i in ms["items"] if i["sinh_vien"]["ma"] not in demo and not i["de_tai_id"]]
print("SV tu do cua GV011:", len(free))
s, dh = req("GET", "/api/dinh-huong", bm); dh = {d["ma"]: d["id"] for d in (dh if isinstance(dh, list) else dh["items"])}
print("dinh huong:", sorted(dh))
plan = [
    ("A", "Xây dựng ứng dụng đặt lịch sử dụng phòng thực hành có nhắc lịch tự động", "H01", "P18-B.docx", "dung"),
    ("B", "Phát triển hệ thống gợi ý tài liệu học tập theo lịch sử truy cập của sinh viên", "H02", "P25-B.pdf", "khong-dau"),
    ("C", "Xây dựng cổng thông tin việc làm thực tập cho sinh viên Khoa Công nghệ thông tin", "H01", "P20-B.docx", "dung"),
    ("D", "Ứng dụng nhận dạng biển số xe ra vào bãi đỗ của trường bằng học sâu", "H02", "P15-B.pdf", "dung"),
]
import unicodedata
def bo_dau(s):
    s = s.replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
out = {}
for (key, ten, ma_dh, tep, kieu), sv in zip(plan, free):
    s, t = req("POST", "/api/topics", gv, body={"dot_do_an_id": dot, "ten_de_tai": ten, "mo_ta": "Đề tài hư cấu dùng cho ảnh chụp báo cáo.",
                                              "dinh_huong_id": dh[ma_dh], "sinh_vien_id": sv["sinh_vien"]["id"], "gui": True})
    print(key, "tao de tai", s, (t or {}).get("trang_thai") if isinstance(t, dict) else t)
    if s not in (200, 201): continue
    tid = t["id"]; ma, ho_ten, lop = sv["sinh_vien"]["ma"], sv["sinh_vien"]["ho_ten"], sv["lop"]
    duoi = tep.rsplit(".", 1)[1]
    ten_file = f"{ma_dh}.{ma}.{ho_ten if kieu == 'dung' else bo_dau(ho_ten)}.{lop}.{duoi}"
    content = open(f"{L}/seed-data/tai-lieu/{tep}", "rb").read()
    ctype = "application/pdf" if duoi == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    tsv = login(ma)
    s, d = req("POST", f"/api/outlines/{tid}/submit", tsv, files={"file": (ten_file, content, ctype)}, fields={"ghi_chu": "Em gửi đề cương lần 1."})
    print(key, "nop", s)
    for _ in range(120):
        s, d = req("GET", f"/api/outlines/{tid}", gv)
        v = d["phien_ban"][-1] if d.get("phien_ban") else None
        if v and v.get("kiem_tra") and v["kiem_tra"].get("trang_thai") in ("HOAN_TAT", "LOI"): break
        time.sleep(1)
    tl = v["tai_lieu"]["id"]
    print(key, "kiem tra", v["kiem_tra"].get("trang_thai"), v["kiem_tra"].get("ty_le_nguon_cao_nhat"))
    s, d = req("POST", f"/api/outlines/{tid}/review", gv, body={"tai_lieu_do_an_id": tl, "ket_qua": "DA_DUYET", "nhan_xet": "Đề cương đạt yêu cầu."})
    print(key, "GVHD duyet", s, d.get("trang_thai") if isinstance(d, dict) else d)
    if key in ("C", "D"):
        s, d = req("POST", f"/api/outlines/{tid}/forward", gv); print(key, "nop Bo mon", s, (d or {}).get("detail") if s != 200 else "")
    if key == "D":
        base = content
        signed = sign_pdf(base, "Lãnh đạo Bộ môn (chứng thư thử nghiệm)")
        s, d = req("POST", f"/api/outlines/{tid}/bo-mon/approve", bm, files={"file": (ten_file.rsplit('.', 1)[0] + ".pdf", signed, "application/pdf")}, fields={"nhan_xet": "Đồng ý phê duyệt."})
        print(key, "Bo mon phe duyet", s, (d or {}).get("detail") if s != 200 else "")
    out[key] = {"de_tai_id": tid, "ma_sv": ma}
json.dump(out, open(os.environ.get("OUT", "/dev/stdout"), "w"), ensure_ascii=False, indent=1)
