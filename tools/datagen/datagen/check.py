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
