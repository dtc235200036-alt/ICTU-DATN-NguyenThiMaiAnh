"""Chia câu (đơn vị phát hiện, D-03).

Dòng còn lại sau lọc mẫu chung được nối thành MỘT dòng chảy (cách nhau bởi
khoảng trắng) nên đoạn bị PDF bẻ dòng được nối lại, rồi tách câu. DOCX (một
dòng mỗi đoạn) và PDF (nhiều dòng mỗi đoạn) vì thế cho cùng các câu — điều
kiện để MinHash bắt được bản chép nguyên văn giữa hai định dạng.
Không chồng lấn giữa các câu → phép tính tỷ lệ theo ký tự là chính xác.
"""
import re

from app.nlp.normalize import syllables

MIN_SYLLABLES = 6
MAX_SYLLABLES = 120

_BOUNDARY_RE = re.compile(r"[.!?…]+[\"”’')\]]*\s+")
_ABBREVIATIONS = {"ts", "ths", "pgs", "gs", "tp", "v.v", "tr", "nxb", "vd", "tt"}
_OPENERS = "\"“‘'([«"


def _starts_sentence(ch: str) -> bool:
    return ch.isupper() or ch.isdigit() or ch in _OPENERS


def _is_abbreviation(stream: str, punct_start: int) -> bool:
    before = stream[:punct_start]
    token = before.rsplit(" ", 1)[-1].casefold()
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
    """Gộp tham lam các phần (đã tách bởi sep) thành mảnh ≤ MAX_SYLLABLES."""
    pieces: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current}{sep}{part}" if current else part
        if current and _n(candidate) > MAX_SYLLABLES:
            pieces.append(current)
            current = part
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def _hard_split(text: str) -> list[str]:
    words = text.split(" ")
    pieces, current = [], []
    for word in words:
        current.append(word)
        if _n(" ".join(current)) >= MAX_SYLLABLES:
            pieces.append(" ".join(current))
            current = []
    if current:
        pieces.append(" ".join(current))
    return pieces


def _limit(sentence: str) -> list[str]:
    if _n(sentence) <= MAX_SYLLABLES:
        return [sentence]
    out: list[str] = []
    for piece in _pack(sentence.split("; "), "; "):
        if _n(piece) <= MAX_SYLLABLES:
            out.append(piece)
            continue
        for sub in _pack(piece.split(", "), ", "):
            out.extend([sub] if _n(sub) <= MAX_SYLLABLES else _hard_split(sub))
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
