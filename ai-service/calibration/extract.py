"""Trích xuất văn bản DOCX/PDF — BẢN SAO của hàm Web API.

Nguồn: backend/app/services/documents.py::extract_text (Phase 3, D-03).
Hiệu chỉnh ngưỡng phải chạy trên ĐÚNG văn bản mà Web API gửi sang dịch vụ AI
khi sinh viên nộp file; nếu hai hàm lệch nhau, số liệu ở chương 4 (mục hiệu
chỉnh ngưỡng) không còn đúng với production. Sửa hàm Web API ⇒ sửa ở đây rồi
chạy lại `calibration/calibrate.py tune` và `evaluate`.

Giữ nguyên từng bước: DOCX = "\\n".join(p.text for p in Document(...).paragraphs)
(kèm trần dung lượng giải nén 150 MiB), PDF = "\\n".join(page.get_text() for
page in fitz.open(stream=..., filetype="pdf")), rồi NFC + bỏ NUL; lỗi hoặc rỗng
→ None.
"""
import unicodedata
import zipfile
from io import BytesIO

import pymupdf as fitz
from docx import Document

DINH_DANG_DOCX = "DOCX"
DINH_DANG_PDF = "PDF"
_MAX_DOCX_UNCOMPRESSED_BYTES = 150 * 1024 * 1024


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
                text = "\n".join(page.get_text() for page in pdf)
        else:
            return None
    except Exception:
        return None

    normalized = unicodedata.normalize("NFC", text).replace("\x00", "")
    if not normalized.strip():
        return None
    return normalized
