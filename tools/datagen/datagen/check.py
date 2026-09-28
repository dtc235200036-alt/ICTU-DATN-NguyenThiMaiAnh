"""Tự kiểm tra bộ dữ liệu (DATA-02, DATA-03).

- Kho đề tài: mô phỏng MỌI quy tắc import CSV kho đồ án đã tài liệu hóa (plan 03-05),
  truy vấn có nhãn, tính tất định (sinh lại → giống từng byte).
- Tài liệu: số lượng/phổ cặp/tập giữ lại, round-trip trích xuất ĐÚNG như Web API
  (backend/app/services/documents.py extract_text), thống kê trùng lặp 4-gram âm tiết,
  tính tất định.
"""

from __future__ import annotations

import collections
import csv
import hashlib
import io
import json
import re
import tempfile
import unicodedata
from pathlib import Path

from . import topics as T

MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_CSV_ROWS = 2000
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MA_SV_RE = re.compile(r"^DTC(18|19|20|21|22)5290\d{3}$")
KY_TU_CONG_THUC = ("=", "+", "-", "@")


class Ket:
    """Gom vi phạm và dòng OK."""

    def __init__(self) -> None:
        self.loi: list[str] = []

    def ok(self, cond: bool, msg_ok: str, msg_loi: str | list[str]) -> None:
        if cond:
            print(f"OK: {msg_ok}")
        else:
            if isinstance(msg_loi, list):
                self.loi.extend(msg_loi[:20])
                if len(msg_loi) > 20:
                    self.loi.append(f"... và {len(msg_loi) - 20} vi phạm khác")
            else:
                self.loi.append(msg_loi)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _doc_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    text = path.read_bytes().decode("utf-8-sig")  # UTF-8, cho phép BOM — như importer
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


# ---------------------------------------------------------------------------
# Kho đề tài + truy vấn
# ---------------------------------------------------------------------------
def check_topics(data: Path, seed: int, meta: dict) -> list[str]:
    k = Ket()
    csv_path = data / "de-tai-kho.csv"
    q_path = data / "truy-van-ten-de-tai.csv"
    m_path = data / "manifest.json"
    for p in (csv_path, q_path, m_path):
        if not p.exists():
            return [f"thiếu tệp {p}"]

    size = csv_path.stat().st_size
    k.ok(size <= MAX_CSV_BYTES, f"de-tai-kho.csv {size} byte ≤ 2 MB", f"CSV {size} byte > 2 MB")
    try:
        header, rows = _doc_csv(csv_path)
    except UnicodeDecodeError as e:
        return [f"CSV không phải UTF-8: {e}"]
    k.ok(header == T.CSV_HEADER, "header đúng định dạng import", f"header sai: {header}")
    k.ok(len(rows) == 300 and len(rows) <= MAX_CSV_ROWS, f"{len(rows)} dòng dữ liệu (≤ 2000)",
         f"số dòng {len(rows)} ≠ 300")
    dem = collections.Counter(r["khoa"] for r in rows)
    k.ok(all(dem[x] == 60 for x in T.KHOA) and len(dem) == 5, "60 đề tài mỗi khóa K18–K22",
         f"phân bố khóa sai: {dict(dem)}")

    vp: list[str] = []
    cap_khoa_ten: set[tuple[str, str]] = set()
    ten_da: set[str] = set()
    ma_sv_da: set[str] = set()
    for i, r in enumerate(rows, start=2):  # dòng vật lý, header = 1
        for col in T.CSV_HEADER:
            v = r.get(col) or ""
            if v != _nfc(v):
                vp.append(f"dòng {i}: cột {col} không ở dạng NFC")
            if v != v.strip():
                vp.append(f"dòng {i}: cột {col} có khoảng trắng thừa")
            if v.startswith(KY_TU_CONG_THUC):
                vp.append(f"dòng {i}: cột {col} bắt đầu bằng ký tự công thức (T-04-09)")
        khoa, ten = r["khoa"], r["ten_de_tai"]
        if not khoa:
            vp.append(f"dòng {i}: Thiếu khóa")
        elif len(khoa) > 20:
            vp.append(f"dòng {i}: Khóa quá 20 ký tự")
        if not ten:
            vp.append(f"dòng {i}: Thiếu tên đề tài")
        elif len(ten) > 255:
            vp.append(f"dòng {i}: tên đề tài > 255 ký tự")
        ma_sv = r["ma_so_sinh_vien"]
        if len(ma_sv) > 20 or not MA_SV_RE.match(ma_sv):
            vp.append(f"dòng {i}: mã SV {ma_sv!r} ngoài khối DTC{{yy}}5290nnn (có thể liên kết SV đang học)")
        if ma_sv in ma_sv_da:
            vp.append(f"dòng {i}: mã SV trùng {ma_sv}")
        ma_sv_da.add(ma_sv)
        if len(r["ho_ten_sinh_vien"]) > 150 or len(r["ho_ten_sinh_vien"].split()) < 2:
            vp.append(f"dòng {i}: họ tên SV không hợp lệ")
        if r["ma_giang_vien"] not in T.MA_GV_HOP_LE:
            vp.append(f"dòng {i}: Không tìm thấy giảng viên mã {r['ma_giang_vien']} (chỉ GV001–GV022)")
        if len(r["tu_khoa"]) > 255:
            vp.append(f"dòng {i}: từ khóa > 255 ký tự")
        try:
            d = float(r["diem"].replace(",", "."))
            if not 0 <= d <= 10:
                raise ValueError
        except ValueError:
            vp.append(f"dòng {i}: Điểm không hợp lệ (0–10)")
        if (khoa, ten) in cap_khoa_ten:
            vp.append(f"dòng {i}: Trùng bản ghi (khóa, tên đề tài)")
        cap_khoa_ten.add((khoa, ten))
        if ten.casefold() in ten_da:
            vp.append(f"dòng {i}: tên đề tài lặp lại ở khóa khác")
        ten_da.add(ten.casefold())
    k.ok(not vp, "mọi dòng qua quy tắc import (bắt buộc, độ dài, NFC, điểm, GV, mã SV, trùng lặp)", vp)

    # Manifest topics
    manifest = json.loads(m_path.read_text(encoding="utf-8"))
    mt = manifest.get("topics", [])
    k.ok(len(mt) == 300 and [x["ten_de_tai"] for x in mt] == [r["ten_de_tai"] for r in rows]
         and [x["stt"] for x in mt] == list(range(1, 301)),
         "manifest.topics khớp CSV theo thứ tự (stt, ma_doi_tuong)", "manifest.topics không khớp CSV")
    dt_kho = {x["ma_doi_tuong"] for x in mt}
    lap = collections.Counter(x["ma_doi_tuong"] for x in mt)
    k.ok(len(dt_kho) == 96 and all(2 <= c <= 4 for c in lap.values()),
         f"{len(dt_kho)} đối tượng kho, mỗi đối tượng lặp 2–4 lần qua các khóa",
         f"lặp đối tượng sai: min {min(lap.values())} max {max(lap.values())}")
    khoa_moi_dt: dict[str, set[str]] = collections.defaultdict(set)
    for x in mt:
        khoa_moi_dt[x["ma_doi_tuong"]].add(x["khoa"])
    k.ok(all(len(khoa_moi_dt[m]) == lap[m] for m in lap),
         "mỗi lần lặp của một đối tượng nằm ở một khóa khác", "đối tượng lặp trong cùng khóa")

    # Truy vấn
    qh, qs = _doc_csv(q_path)
    k.ok(qh == T.QUERY_HEADER, "header truy vấn đúng", f"header truy vấn sai: {qh}")
    loai = collections.Counter(q["loai"] for q in qs)
    k.ok(len(qs) == 80 and loai == {"DIEN_DAT_LAI": 40, "CUNG_LINH_VUC": 40},
         "80 truy vấn: 40 DIEN_DAT_LAI + 40 CUNG_LINH_VUC", f"phân bố truy vấn sai: {dict(loai)}")
    vq: list[str] = []
    for lo in ("DIEN_DAT_LAI", "CUNG_LINH_VUC"):
        tap = collections.Counter(q["tap"] for q in qs if q["loai"] == lo)
        if not (26 <= tap["HIEU_CHINH"] <= 30 and 10 <= tap["KIEM_CHUNG"] <= 14):
            vq.append(f"{lo}: tách tập sai {dict(tap)}")
    ten_csv = {r["ten_de_tai"] for r in rows}
    ten_csv_cf = {t.casefold() for t in ten_csv}
    for q in qs:
        if q["ten_truy_van"].casefold() in ten_csv_cf:
            vq.append(f"{q['ma_truy_van']}: truy vấn trùng nguyên văn tiêu đề kho")
        if q["ten_truy_van"] != _nfc(q["ten_truy_van"]):
            vq.append(f"{q['ma_truy_van']}: không NFC")
        if q["loai"] == "DIEN_DAT_LAI":
            if q["tieu_de_goc"] not in ten_csv:
                vq.append(f"{q['ma_truy_van']}: tieu_de_goc không có trong kho")
            if q["ky_vong_canh_bao"] != "1":
                vq.append(f"{q['ma_truy_van']}: DIEN_DAT_LAI phải kỳ vọng cảnh báo 1")
        else:
            if q["ma_doi_tuong"] in dt_kho:
                vq.append(f"{q['ma_truy_van']}: đối tượng {q['ma_doi_tuong']} có trong kho")
            if q["tieu_de_goc"] or q["ky_vong_canh_bao"] != "0":
                vq.append(f"{q['ma_truy_van']}: CUNG_LINH_VUC phải có tieu_de_goc rỗng, kỳ vọng 0")
    if len({q["ma_truy_van"] for q in qs}) != len(qs):
        vq.append("ma_truy_van trùng")
    k.ok(not vq, "truy vấn: tách tập 28/12 mỗi loại, không trùng tiêu đề kho, nguồn/đối tượng đúng", vq)

    # Tất định
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        T.write_topics(tdp, seed, meta)
        same_csv = (tdp / "de-tai-kho.csv").read_bytes() == csv_path.read_bytes()
        same_q = (tdp / "truy-van-ten-de-tai.csv").read_bytes() == q_path.read_bytes()
        m2 = json.loads((tdp / "manifest.json").read_text(encoding="utf-8"))
        same_m = m2["topics"] == mt
    k.ok(same_csv and same_q and same_m, f"sinh lại với hạt giống {seed}: CSV và manifest.topics giống từng byte",
         f"không tất định: csv={same_csv} truy_van={same_q} manifest={same_m}")
    return k.loi


# ---------------------------------------------------------------------------
# Tài liệu (DATA-03)
# ---------------------------------------------------------------------------
def extract_text(content: bytes, dinh_dang: str) -> str | None:
    """Bản sao logic backend/app/services/documents.py extract_text (không import backend):
    DOCX → "\\n".join(p.text for p in Document(...).paragraphs);
    PDF → "\\n".join(page.get_text() for page in fitz.open(...)); rồi NFC, bỏ \\x00."""
    import pymupdf as fitz
    from docx import Document

    try:
        if dinh_dang == "DOCX":
            document = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in document.paragraphs)
        elif dinh_dang == "PDF":
            with fitz.open(stream=content, filetype="pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
        else:
            return None
    except Exception:
        return None
    normalized = unicodedata.normalize("NFC", text).replace("\x00", "")
    return normalized if normalized.strip() else None


def _gon(s: str) -> str:
    return re.sub(r"\s+", " ", _nfc(s)).strip()


def tach_cau(doan: str) -> list[str]:
    return [c for c in re.split(r"(?<=\.)\s+", doan.strip()) if c]


def gram4(cau: str) -> frozenset:
    tok = re.findall(r"\w+", _nfc(cau).lower())
    if len(tok) < 4:
        return frozenset([tuple(tok)])
    return frozenset(tuple(tok[i:i + 4]) for i in range(len(tok) - 3))


def jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def _max_j(cau: str, nguon: list[frozenset]) -> float:
    g = gram4(cau)
    return max((jaccard(g, x) for x in nguon), default=0.0)


LOAI_DEM = {"CHEP_NGUYEN_VAN": 7, "DIEN_DAT_LAI": 7, "CUNG_LINH_VUC": 6, "KHONG_LIEN_QUAN": 5}


def check_documents(data: Path, seed: int, meta: dict) -> list[str]:
    from . import documents as D
    from . import vocab

    k = Ket()
    m_path = data / "manifest.json"
    thu_muc = data / "tai-lieu"
    if not m_path.exists() or not thu_muc.is_dir():
        return ["thiếu manifest.json hoặc tai-lieu/"]
    manifest = json.loads(m_path.read_text(encoding="utf-8"))
    caps = manifest.get("cap", [])

    # Số lượng, phổ, tập, định dạng
    tep_thuc = sorted(p.name for p in thu_muc.iterdir() if p.is_file())
    tep_mf = sorted(Path(c[x]["tep"]).name for c in caps for x in ("A", "B"))
    k.ok(len(tep_thuc) == 50 and tep_thuc == tep_mf, "đúng 50 tệp trong tai-lieu/, khớp manifest",
         f"tệp không khớp: {len(tep_thuc)} thực tế / {len(tep_mf)} manifest")
    dem = collections.Counter(c["loai"] for c in caps)
    kc = collections.Counter(c["loai"] for c in caps if c["tap"] == "KIEM_CHUNG")
    k.ok(len(caps) == 25 and dict(dem) == LOAI_DEM and sum(kc.values()) == 8 and all(kc[x] == 2 for x in LOAI_DEM),
         "25 cặp: CHEP 7 / DIEN 7 / CUNG 6 / KHONG 5; 8 KIEM_CHUNG (2 mỗi loại)",
         f"phổ/tập sai: {dict(dem)} kiểm chứng {dict(kc)}")
    chieu = collections.defaultdict(set)
    for c in caps:
        chieu[c["loai"]].add(f"{c['A']['dinh_dang']}->{c['B']['dinh_dang']}")
    k.ok(all(chieu[x] == {"DOCX->PDF", "PDF->DOCX"} for x in LOAI_DEM),
         "mọi loại có cả chiều DOCX→PDF và PDF→DOCX", f"thiếu chiều định dạng: {dict(chieu)}")
    ky_vong_sai = [c["ma_cap"] for c in caps if c["ky_vong_canh_bao"] != D.KY_VONG[c["loai"]]]
    k.ok(not ky_vong_sai, "kỳ vọng cảnh báo = 1 cho CHEP/DIEN, 0 cho CUNG/KHONG", f"kỳ vọng sai: {ky_vong_sai}")
    kho = {x["stt"]: x for x in manifest.get("topics", [])}
    a_sai = [c["ma_cap"] for c in caps if kho.get(c["A"]["stt_kho"], {}).get("ten_de_tai") != c["A"]["ten_de_tai"]]
    k.ok(not a_sai, "A của mọi cặp là một dòng trong kho 300 đề tài (stt_kho, ten_de_tai)", f"A không thuộc kho: {a_sai}")
    k.ok(len({c["A"]["ma_doi_tuong"] for c in caps}) == 25 and len({c["A"]["cum"] for c in caps}) == 8
         and len({c["A"]["khoa"] for c in caps}) == 5,
         "A: 25 đối tượng khác nhau, phủ 8 cụm và 5 khóa", "A trùng đối tượng hoặc chưa phủ cụm/khóa")

    # Round-trip trích xuất + băm + kích thước
    vr: list[str] = []
    trich: dict[str, str] = {}
    for c in caps:
        for x in ("A", "B"):
            tl = c[x]
            p = data / tl["tep"]
            if not p.exists():
                vr.append(f"{tl['tep']}: không tồn tại")
                continue
            raw = p.read_bytes()
            if len(raw) > MAX_UPLOAD_BYTES:
                vr.append(f"{tl['tep']}: vượt 20 MB")
            text = extract_text(raw, tl["dinh_dang"])
            if text is None:
                vr.append(f"{tl['tep']}: trích xuất rỗng/lỗi")
                continue
            trich[tl["tep"]] = text
            gon = _gon(text)
            doan = tl["doan"] if x == "A" else [d["text"] for d in tl["doan"]]
            mat = [i for i, d in enumerate(doan) if _gon(d) not in gon]
            if mat:
                vr.append(f"{tl['tep']}: {len(mat)} đoạn nội dung mất/biến dạng sau trích xuất (vd #{mat[0]})")
            if tl["dinh_dang"] == "PDF" and gon.count(vocab.DAU_TRANG) < 3:
                vr.append(f"{tl['tep']}: đầu trang lặp < 3 lần")
            bam = hashlib.sha256("\n".join(_nfc(d) for d in doan).encode("utf-8")).hexdigest()
            if bam != tl["bam_noi_dung"]:
                vr.append(f"{tl['tep']}: bam_noi_dung không khớp")
    k.ok(not vr, "mọi đoạn nội dung còn nguyên sau trích xuất của Web API (DOCX/PDF, NFC); PDF có đầu trang lặp ≥ 3; băm khớp; < 20 MB", vr)

    # Thống kê trùng lặp 4-gram âm tiết ở mức câu
    vo: list[str] = []
    bang: dict[str, dict] = {lo: {"cap": 0, "kc": 0, "d2p": 0, "p2d": 0, "cau_b": 0, "ty_le": [], "chi_so": [],
                                  "rieng": []} for lo in LOAI_DEM}
    for c in caps:
        lo = c["loai"]
        s = bang[lo]
        s["cap"] += 1
        s["kc"] += c["tap"] == "KIEM_CHUNG"
        s["d2p" if c["A"]["dinh_dang"] == "DOCX" else "p2d"] += 1
        a_doan = c["A"]["doan"]
        a_cau_g = [gram4(x) for d in a_doan for x in tach_cau(d)]
        b_doan = c["B"]["doan"]
        tong = sum(len(d["text"]) for d in b_doan)
        s["cau_b"] += sum(len(tach_cau(d["text"])) for d in b_doan)
        if lo in ("CHEP_NGUYEN_VAN", "DIEN_DAT_LAI"):
            lay = [d for d in b_doan if d["nguon"]]
            tl = sum(len(d["text"]) for d in lay) / tong
            s["ty_le"].append(tl)
            if not 0.40 <= tl <= 0.60:
                vo.append(f"{c['ma_cap']}: tỷ lệ chép/diễn đạt {tl:.2%} ngoài 40–60%")
            if abs(tl - c["ty_le_sao_chep"]) > 0.005:
                vo.append(f"{c['ma_cap']}: ty_le_sao_chep manifest lệch")
            js = []
            for d in lay:
                src = [gram4(x) for x in tach_cau(a_doan[d["nguon"]["chi_so"]])]
                js += [_max_j(x, src) for x in tach_cau(d["text"])]
            if lo == "CHEP_NGUYEN_VAN":
                if any(abs(j - 1.0) > 1e-9 for j in js):
                    vo.append(f"{c['ma_cap']}: có câu chép không trùng khớp 100% với nguồn")
                s["chi_so"].append(sum(j == 1.0 for j in js) / len(js))
            else:
                thap = sum(j < 0.5 for j in js) / len(js)
                s["chi_so"].append(thap)
                if thap < 0.70:
                    vo.append(f"{c['ma_cap']}: chỉ {thap:.0%} câu diễn đạt lại có Jaccard < 0,5 (cần ≥ 70%)")
            rieng = [x for d in b_doan if not d["nguon"] for x in tach_cau(d["text"])]
            tl_rieng = sum(_max_j(x, a_cau_g) >= 0.5 for x in rieng) / max(1, len(rieng))
            s["rieng"].append(tl_rieng)
            if tl_rieng >= 0.05:  # nhãn "không nguồn" của plan 04-04 phải sạch
                vo.append(f"{c['ma_cap']}: {tl_rieng:.1%} câu tự viết của B có Jaccard ≥ 0,5 với A (cần < 5%)")
        else:
            b_cau = [x for d in b_doan for x in tach_cau(d["text"])]
            if any(d["nguon"] for d in b_doan):
                vo.append(f"{c['ma_cap']}: {lo} không được có đoạn có nguồn A")
            gan = sum(_max_j(x, a_cau_g) >= 0.5 for x in b_cau) / len(b_cau)
            s["chi_so"].append(gan)
            s["ty_le"].append(0.0)
            if gan >= 0.05:
                vo.append(f"{c['ma_cap']}: {gan:.1%} câu B có Jaccard ≥ 0,5 với A (cần < 5%)")
    k.ok(not vo, "thống kê trùng lặp: CHEP 40–60% & câu chép = 1,0; DIEN ≥ 70% câu < 0,5; CUNG/KHONG < 5% câu ≥ 0,5", vo)

    print("\nThống kê theo loại (Jaccard 4-gram âm tiết, mức câu):")
    print("| Loại | Cặp | KIEM_CHUNG | DOCX→PDF | PDF→DOCX | Câu B | Tỷ lệ chép/diễn đạt | Chỉ số chính | Câu tự viết ≥ 0,5 |")
    print("|------|-----|-----------|----------|----------|-------|---------------------|--------------|-------------------|")
    ten_cs = {"CHEP_NGUYEN_VAN": "câu chép J=1,0", "DIEN_DAT_LAI": "câu diễn đạt J<0,5",
              "CUNG_LINH_VUC": "câu B J≥0,5", "KHONG_LIEN_QUAN": "câu B J≥0,5"}
    for lo, s in bang.items():
        tl = f"{min(s['ty_le']):.1%}–{max(s['ty_le']):.1%}" if lo in ("CHEP_NGUYEN_VAN", "DIEN_DAT_LAI") else "0%"
        cs = f"{ten_cs[lo]}: {min(s['chi_so']):.1%}–{max(s['chi_so']):.1%}"
        rg = f"{max(s['rieng']):.1%} (max)" if s["rieng"] else "—"
        print(f"| {lo} | {s['cap']} | {s['kc']} | {s['d2p']} | {s['p2d']} | {s['cau_b']} | {tl} | {cs} | {rg} |")
    # Thông tin thêm cho plan 04-06 (mọi A được index cùng lúc): câu B không nguồn so với TẤT CẢ A.
    tat_ca_a = [gram4(x) for c in caps for d in c["A"]["doan"] for x in tach_cau(d)]
    b_khong_nguon = [x for c in caps for d in c["B"]["doan"] if not d["nguon"] for x in tach_cau(d["text"])]
    gan_ca_kho = sum(_max_j(x, tat_ca_a) >= 0.5 for x in b_khong_nguon)
    print(f"Câu B không nguồn có Jaccard ≥ 0,5 với BẤT KỲ tài liệu A nào: {gan_ca_kho}/{len(b_khong_nguon)} "
          f"({gan_ca_kho / len(b_khong_nguon):.1%})")
    k.ok(gan_ca_kho / len(b_khong_nguon) < 0.05,
         "câu B không nguồn gần như không trùng câu của mọi tài liệu A khác (< 5%)",
         f"{gan_ca_kho} câu B không nguồn trùng gần với tài liệu A khác (≥ 5%)")
    print()

    # Tất định: sinh lại toàn bộ vào thư mục tạm
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        T.write_topics(tdp, seed, meta)
        D.write_documents(tdp, seed, meta)
        same_m = (tdp / "manifest.json").read_bytes() == m_path.read_bytes()
        khac_text, giong_byte = [], 0
        for c in caps:
            for x in ("A", "B"):
                tl = c[x]
                raw2 = (tdp / tl["tep"]).read_bytes()
                giong_byte += raw2 == (data / tl["tep"]).read_bytes()
                if extract_text(raw2, tl["dinh_dang"]) != trich.get(tl["tep"]):
                    khac_text.append(tl["tep"])
    k.ok(same_m and not khac_text,
         f"sinh lại với hạt giống {seed}: manifest.json giống từng byte, văn bản trích xuất giống hệt "
         f"({giong_byte}/50 tệp giống từng byte)",
         f"không tất định: manifest={same_m}, văn bản khác ở {khac_text[:5]}")
    return k.loi
