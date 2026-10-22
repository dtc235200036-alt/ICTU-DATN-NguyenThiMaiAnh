"""Chia câu (đơn vị phát hiện, D-03).

Dòng còn lại sau lọc mẫu chung được nối thành MỘT dòng chảy (cách nhau bởi
khoảng trắng) nên đoạn bị PDF bẻ dòng được nối lại, rồi tách câu. DOCX (một
dòng mỗi đoạn) và PDF (nhiều dòng mỗi đoạn) vì thế cho cùng các câu — điều
kiện để vân tay bắt được bản chép nguyên văn giữa hai định dạng.
Không chồng lấn giữa các câu → phép tính tỷ lệ theo ký tự là chính xác.

CR-03 (04-REVIEW): văn bản do sinh viên kiểm soát → mọi bước phải TUYẾN TÍNH
theo độ dài: đếm âm tiết cộng dồn (không đếm lại chuỗi đang lớn dần), không
sao chép tiền tố của dòng chảy ở mỗi ranh giới câu, và mỗi mảnh bị chặn cả
theo âm tiết (MAX_SYLLABLES) lẫn theo ký tự (MAX_CHARS) — mảnh không có âm
tiết (vd. "- , - , …") không còn lớn vô hạn.
"""
import re

from app.nlp.normalize import syllables

MIN_SYLLABLES = 6
MAX_SYLLABLES = 120
# Trần ký tự của một câu/mảnh: câu 120 âm tiết tiếng Việt ≈ 500–700 ký tự.
MAX_CHARS = 2000

_BOUNDARY_RE = re.compile(r"[.!?…]+[\"”’')\]]*\s+")
_ABBREVIATIONS = {"ts", "ths", "pgs", "gs", "tp", "v.v", "tr", "nxb", "vd", "tt"}
_OPENERS = "\"“‘'([«"


def _starts_sentence(ch: str) -> bool:
    return ch.isupper() or ch.isdigit() or ch in _OPENERS


def _is_abbreviation(stream: str, punct_start: int) -> bool:
    # Chỉ cắt đúng token đứng trước dấu câu (không sao chép cả tiền tố).
    token = stream[stream.rfind(" ", 0, punct_start) + 1 : punct_start].casefold()
    return token in _ABBREVIATIONS


def _split_stream(stream: str) -> list[str]:
    out: list[str] = []
    start = 0
    for m in _BOUNDARY_RE.finditer(stream):
        end = m.end()
        if end >= len(stream) or not _starts_sentence(stream[end]):
            continue
        if stream[m.start()] == "." and _is_abbreviation(stream, m.start()):
            continue
        piece = stream[start:end].strip()
        if piece:
            out.append(piece)
        start = end
    tail = stream[start:].strip()
    if tail:
        out.append(tail)
    return out


def _n(text: str) -> int:
    return len(syllables(text))


def _pack(parts: list[str], sep: str) -> list[str]:
    """Gộp tham lam các phần (đã tách bởi sep) thành mảnh ≤ MAX_SYLLABLES và
    ≤ MAX_CHARS. sep không chứa ký tự chữ nên số âm tiết của mảnh = tổng số
    âm tiết của các phần — đếm mỗi phần đúng một lần (tuyến tính)."""
    pieces: list[str] = []
    current: list[str] = []
    cur_n = cur_len = 0
    for part in parts:
        n, length = _n(part), len(part)
        if current and (
            cur_n + n > MAX_SYLLABLES or cur_len + len(sep) + length > MAX_CHARS
        ):
            pieces.append(sep.join(current))
            current, cur_n, cur_len = [], 0, 0
        cur_len += (len(sep) if current else 0) + length
        current.append(part)
        cur_n += n
    if current:
        pieces.append(sep.join(current))
    return pieces


def _hard_split(text: str) -> list[str]:
    """Cắt theo từ khi đủ MAX_SYLLABLES âm tiết hoặc MAX_CHARS ký tự; từ đơn
    dài hơn MAX_CHARS (không có dấu cách) bị cắt theo ký tự."""
    pieces: list[str] = []
    current: list[str] = []
    cur_n = cur_len = 0
    for word in text.split(" "):
        for i in range(0, max(len(word), 1), MAX_CHARS):
            chunk = word[i : i + MAX_CHARS]
            current.append(chunk)
            cur_n += _n(chunk)
            cur_len += len(chunk) + 1
            if cur_n >= MAX_SYLLABLES or cur_len >= MAX_CHARS:
                pieces.append(" ".join(current))
                current, cur_n, cur_len = [], 0, 0
    if current:
        pieces.append(" ".join(current))
    return pieces


def _fits(text: str) -> bool:
    return len(text) <= MAX_CHARS and _n(text) <= MAX_SYLLABLES


def _limit(sentence: str) -> list[str]:
    if _fits(sentence):
        return [sentence]
    out: list[str] = []
    for piece in _pack(sentence.split("; "), "; "):
        if _fits(piece):
            out.append(piece)
            continue
        for sub in _pack(piece.split(", "), ", "):
            out.extend([sub] if _fits(sub) else _hard_split(sub))
    return out


def sentences(lines: list[str]) -> list[str]:
    stream = " ".join(line.strip() for line in lines if line.strip())
    stream = re.sub(r"\s+", " ", stream)
    result: list[str] = []
    for sentence in _split_stream(stream):
        for piece in _limit(sentence):
            if _n(piece) >= MIN_SYLLABLES:
                result.append(piece)
    return result
