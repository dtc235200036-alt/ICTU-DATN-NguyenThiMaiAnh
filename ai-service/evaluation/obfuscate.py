"""Các kiểu biến đổi (che giấu) đoạn đạo văn cho bộ đánh giá kiểu PAN.

Phân loại theo ReParaphrased (Zhou và cộng sự, 2024) và obfuscation của PAN.
Mỗi kiểu là một hàm thuần (text, rng) -> str chỉ dùng rng được truyền vào, nên
kết quả tất định theo seed. Kiểu `llm` không có hàm: văn bản diễn đạt lại lấy
từ dien-dat-lai-llm.jsonl (evaluation/tao_bo.py).
Câu được tách bằng đúng bộ chia câu production (app/nlp/chunking.py).
"""
import random
import re
import unicodedata
from pathlib import Path

from app.nlp.chunking import sentences
from app.nlp.normalize import syllables

# Hư từ có thể bỏ mà câu vẫn đúng ngữ pháp (sửa nhẹ).
_HU_TU = {"các", "những", "thì", "đã", "sẽ", "rất", "cũng", "đều", "việc", "sự"}
_NOI_CAU = (", đồng thời", " và", "; bên cạnh đó,", "; ngoài ra,")


def _doc_tu_dien() -> dict[str, list[str]]:
    """tu-dong-nghia.tsv: cột 1 = cụm (chữ thường) được thay, cột 2 = cụm thay thế."""
    tu_dien: dict[str, list[str]] = {}
    tep = Path(__file__).with_name("tu-dong-nghia.tsv")
    for dong in tep.read_text(encoding="utf-8").splitlines():
        if dong.strip():
            cum, thay = unicodedata.normalize("NFC", dong).split("\t")
            tu_dien.setdefault(cum, []).append(thay)
    return tu_dien


_TU_DONG_NGHIA = _doc_tu_dien()
# re thử các nhánh theo thứ tự → xếp cụm dài trước để khớp cụm dài nhất tại mỗi vị trí.
_TU_RE = re.compile(
    r"(?<!\w)(?:"
    + "|".join(map(re.escape, sorted(_TU_DONG_NGHIA, key=len, reverse=True)))
    + r")(?!\w)",
    re.IGNORECASE,
)


def nguyen_van(text: str, rng: random.Random) -> str:
    """Chép nguyên văn."""
    return text


def sua_nhe(text: str, rng: random.Random) -> str:
    """Sửa nhẹ: thay ~15–25 % số cụm có trong từ điển đồng nghĩa, bỏ vài hư từ,
    bỏ/đổi một hai dấu phẩy, chấm phẩy; phần lớn văn bản giữ nguyên."""
    khop = list(_TU_RE.finditer(text))
    so_thay = max(1, round(len(khop) * rng.uniform(0.15, 0.25))) if khop else 0
    phan, cuoi = [], 0
    for k in sorted(rng.sample(range(len(khop)), so_thay)):
        m = khop[k]
        thay = rng.choice(_TU_DONG_NGHIA[m.group(0).lower()])
        if m.group(0)[0].isupper():
            thay = thay[0].upper() + thay[1:]
        phan += [text[cuoi : m.start()], thay]
        cuoi = m.end()
    phan.append(text[cuoi:])

    tu = "".join(phan).split(" ")
    dau = [i for i, t in enumerate(tu[:-1]) if t.endswith((",", ";"))]
    for i in rng.sample(dau, min(len(dau), rng.randint(1, 2))):
        tu[i] = tu[i][:-1] + ("," if tu[i].endswith(";") else "")
    hu_tu = [i for i, t in enumerate(tu) if t in _HU_TU]
    bo = set(rng.sample(hu_tu, min(len(hu_tu), rng.randint(1, 3))))
    return " ".join(t for i, t in enumerate(tu) if i not in bo)


def dao_cau(text: str, rng: random.Random) -> str:
    """Đảo thứ tự câu; từ 2 câu trở lên thì thứ tự chắc chắn khác bản gốc."""
    cau = sentences([text])
    thu_tu = list(range(len(cau)))
    while len(cau) > 1 and thu_tu == sorted(thu_tu):
        rng.shuffle(thu_tu)
    return " ".join(cau[i] for i in thu_tu)


def gop_cau(text: str, rng: random.Random) -> str:
    """Gộp từng cặp câu liên tiếp bằng một từ nối."""
    cau = sentences([text])
    ket_qua = []
    for k in range(0, len(cau) - 1, 2):
        dau, sau = cau[k], cau[k + 1]
        tu = sau.split(" ")
        # Giữ chữ hoa cho từ viết tắt (≥ 2 chữ hoa) và tên riêng nhiều âm tiết (từ kế cũng viết hoa).
        if sum(c.isupper() for c in tu[0]) < 2 and not (len(tu) > 1 and tu[1][:1].isupper()):
            sau = sau[0].lower() + sau[1:]
        # Câu sau mở đầu bằng trạng ngữ ngắn ("Tuy nhiên,", "Ngoài ra,") → nối bằng "; " cho tự nhiên.
        noi = ";" if re.match(r"(?:\w+ ){0,2}\w+,", sau) else rng.choice(_NOI_CAU)
        ket_qua.append(dau.rstrip(".!?…") + noi + " " + sau)
    if len(cau) % 2:
        ket_qua.append(cau[-1])
    return " ".join(ket_qua)


def tach_cau(text: str, rng: random.Random) -> str:
    """Tách câu dài hơn 25 âm tiết tại dấu phẩy gần giữa câu nhất (mỗi nửa ≥ 6 âm tiết)."""
    ket_qua = []
    for c in sentences([text]):
        phay = [
            m.start()
            for m in re.finditer(", ", c)
            if len(syllables(c[: m.start()])) >= 6 and len(syllables(c[m.end() :])) >= 6
        ]
        if len(syllables(c)) > 25 and phay:
            i = min(phay, key=lambda i: abs(i - len(c) / 2))
            c = c[:i] + ". " + c[i + 2].upper() + c[i + 3 :]
        ket_qua.append(c)
    return " ".join(ket_qua)


def xao_tron(text: str, rng: random.Random) -> str:
    """Random obfuscation của PAN: xáo từ trong ~30 % cửa sổ 3–4 từ, rồi xóa ~5 %
    và chèn ~5 % từ (từ chèn lấy ngẫu nhiên trong chính đoạn)."""
    tu = text.split()
    xao, i = [], 0
    while i < len(tu):
        cua_so = tu[i : i + rng.choice((3, 4))]
        if rng.random() < 0.3:
            rng.shuffle(cua_so)
        xao += cua_so
        i += len(cua_so)
    ket_qua = []
    for t in xao:
        r = rng.random()
        if r >= 0.05:
            ket_qua.append(t)
        if r >= 0.95:
            ket_qua.append(rng.choice(tu))
    return " ".join(ket_qua)


BIEN_DOI = {
    "nguyen_van": nguyen_van,
    "sua_nhe": sua_nhe,
    "dao_cau": dao_cau,
    "gop_cau": gop_cau,
    "tach_cau": tach_cau,
    "xao_tron": xao_tron,
}
