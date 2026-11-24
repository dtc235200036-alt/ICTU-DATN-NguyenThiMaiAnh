"""Trích xuất văn bản DOCX/PDF — BẢN SAO của hàm Web API.

Nguồn: backend/app/services/documents.py::extract_text (Phase 3, D-03).
Hiệu chỉnh ngưỡng phải chạy trên ĐÚNG văn bản mà Web API gửi sang dịch vụ AI
khi sinh viên nộp file; nếu hai hàm lệch nhau, số liệu ở chương 4 (mục hiệu
chỉnh ngưỡng) không còn đúng với production. Sửa hàm Web API ⇒ sửa ở đây rồi
chạy lại `calibration/calibrate.py tune` và `evaluate`.

Giữ nguyên từng bước: DOCX = "\\n".join(p.text for p in Document(...).paragraphs)
(kèm trần dung lượng giải nén 150 MiB), PDF = "\\n".join(_pdf_page_text(page)
for page in fitz.open(stream=..., filetype="pdf")) (dựng lại dấu cách bị thiếu
từ rawdict — hằng số và hàm phụ giống hệt bên Web API), rồi NFC + bỏ NUL; lỗi
hoặc rỗng → None.
"""
import unicodedata
import zipfile
from io import BytesIO

import pymupdf as fitz
from docx import Document

DINH_DANG_DOCX = "DOCX"
DINH_DANG_PDF = "PDF"
_MAX_DOCX_UNCOMPRESSED_BYTES = 150 * 1024 * 1024


# Khoảng hở tối thiểu (tỉ lệ cỡ chữ) để coi là dấu cách bị thiếu; trên 104 PDF
# kho thật 0,08/0,10/0,12 cho kết quả như nhau -> lấy giữa.
_PDF_KHOANG_HO_TI_LE = 0.10


def _pdf_page_text(page: fitz.Page) -> str:
    """MuPDF không tự chèn dấu cách sau chữ khối U+1E00–U+1EFF (ệ, ử, ế…) khi
    PDF không có ký tự dấu cách thật — khoảng cách giữa hai từ chỉ là vị trí
    đặt chữ (LaTeX vntex, một số bản xuất từ Word) -> "Hệthống", "sửdụng".
    Dựng lại từng dòng từ rawdict (cùng cờ, cùng thứ tự khối/dòng như
    get_text()), chèn " " khi khoảng hở ngang vượt ngưỡng."""
    out: list[str] = []
    for block in page.get_text("rawdict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]:
        for line in block.get("lines", []):
            buf: list[str] = []
            x_max = float("-inf")
            for span in line["spans"]:
                nguong = _PDF_KHOANG_HO_TI_LE * span["size"]
                for ch in span["chars"]:
                    c, x0, x1 = ch["c"], ch["bbox"][0], ch["bbox"][2]
                    # So với mép phải xa nhất đã gặp (không chỉ ký tự liền trước)
                    # để dấu vẽ rời/glyph chồng nhau không bao giờ sinh dấu cách.
                    if buf and x0 - x_max > nguong and not c.isspace() and not buf[-1].isspace():
                        buf.append(" ")
                    buf.append(c)
                    x_max = max(x_max, x1)
            if buf:
                out.append("".join(buf) + "\n")
    return "".join(out)


def extract_text(content: bytes, dinh_dang: str) -> str | None:
    try:
        if dinh_dang == DINH_DANG_DOCX:
            total_uncompressed = 0
            with zipfile.ZipFile(BytesIO(content)) as zf:
                for info in zf.infolist():
                    total_uncompressed += info.file_size
            if total_uncompressed > _MAX_DOCX_UNCOMPRESSED_BYTES:
                return None
            document = Document(BytesIO(content))
            text = "\n".join(p.text for p in document.paragraphs)
        elif dinh_dang == DINH_DANG_PDF:
            with fitz.open(stream=content, filetype="pdf") as pdf:
                text = "\n".join(_pdf_page_text(page) for page in pdf)
        else:
            return None
    except Exception:
        return None

    normalized = unicodedata.normalize("NFC", text).replace("\x00", "")
    if not normalized.strip():
        return None
    return normalized
