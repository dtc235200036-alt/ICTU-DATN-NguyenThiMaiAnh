"""Chuẩn hóa văn bản (AISV-02): mọi văn bản vào pipeline đều qua nfc()."""
import re
import unicodedata

_SPACES_RE = re.compile(r"[ \t  -​　]+")
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def nfc(text: str) -> str:
    """NFC, bỏ NUL, CRLF/CR → LF, gộp khoảng trắng trong từng dòng, strip dòng."""
    text = unicodedata.normalize("NFC", text).replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(_SPACES_RE.sub(" ", line).strip() for line in text.split("\n"))


def one_line(text: str) -> str:
    """nfc() rồi gộp toàn bộ thành một dòng (tiêu đề đề tài)."""
    return " ".join(part for part in nfc(text).split("\n") if part).strip()


def syllables(text: str) -> list[str]:
    """Các âm tiết (token \\w+) của văn bản NFC đã casefold."""
    return _WORD_RE.findall(unicodedata.normalize("NFC", text).casefold())
