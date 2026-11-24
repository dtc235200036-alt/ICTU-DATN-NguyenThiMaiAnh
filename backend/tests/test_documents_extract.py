"""Trích xuất PDF: dựng lại dấu cách MuPDF bỏ sót sau chữ U+1E00–U+1EFF
(PDF LaTeX vntex trong kho đồ án cũ ra "Hệthống", "sửdụng")."""
import pymupdf as fitz

from app.models.de_cuong import PDF
from app.services.documents import _pdf_page_text, extract_text

# Helvetica WinAnsi: ê ô ò ù (EA F4 F2 F9) ánh xạ ToUnicode sang ệ ố ử ụ —
# khối U+1E00–U+1EFF như font vntex, không cần nhúng font tiếng Việt.
_TO_UNICODE = b"""/CIDInit /ProcSet findresource begin 12 dict begin begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /Adobe-Identity-UCS def /CMapType 2 def
1 begincodespacerange <00> <FF> endcodespacerange
4 beginbfchar <EA> <1EC7> <F4> <1ED1> <F2> <1EED> <F9> <1EE5> endbfchar
endcmap CMapName currentdict /CMap defineresource pop end end"""


def _pdf_dinh_chu() -> bytes:
    """Mỗi từ là một lần vẽ riêng trên cùng đường cơ sở, cách nhau 0,25 em,
    KHÔNG có ký tự dấu cách — giống cách pdfTeX đặt khoảng cách giữa từ."""
    doc = fitz.open()
    page = doc.new_page()
    helv = fitz.Font("helv")
    x = 72.0
    for tu in ["Hê", "thông", "sò", "dùng"]:
        page.insert_text((x, 100), tu, fontname="helv", fontsize=12)
        x += helv.text_length(tu, fontsize=12) + 0.25 * 12
    cmap = doc.get_new_xref()
    doc.update_object(cmap, "<<>>")
    doc.update_stream(cmap, _TO_UNICODE)
    doc.xref_set_key(page.get_fonts()[0][0], "ToUnicode", f"{cmap} 0 R")
    data = doc.tobytes()
    doc.close()
    return data


def test_pdf_extraction_restores_missing_spaces():
    data = _pdf_dinh_chu()
    with fitz.open(stream=data, filetype="pdf") as pdf:
        # Tiền đề: nếu MuPDF đã tự chèn dấu cách thì xem lại _pdf_page_text.
        assert pdf[0].get_text() == "Hệthống sửdụng\n"
    assert extract_text(data, PDF) == "Hệ thống sử dụng\n"


class _Trang:
    def __init__(self, blocks):
        self.blocks = blocks

    def get_text(self, *_args, **_kwargs):
        return {"blocks": self.blocks}


def _kt(c, x0, x1):
    return {"c": c, "bbox": (x0, 0, x1, 10)}


def test_pdf_line_rebuild_edge_cases():
    # Cỡ chữ 10 -> ngưỡng 1,0.
    dong = [
        _kt("e", 0, 5),
        _kt("̂", 1, 4),  # dấu vẽ rời, nằm trong "e"
        _kt("m", 5.5, 11),  # hở 0,5 so với mép "e" (1,5 so với dấu) -> liền
        _kt("A", 13, 19),  # hở 2 -> thêm dấu cách
        _kt("V", 18, 24),  # chồng (kerning âm) -> liền
        _kt(" ", 26, 28),  # dấu cách sẵn có -> không nhân đôi
        _kt("x", 30, 35),
    ]
    blocks = [
        {"type": 1},  # khối ảnh: không có "lines"
        {"lines": [{"spans": [{"size": 10, "chars": dong}]}, {"spans": []}]},
        {"lines": [{"spans": [{"size": 10, "chars": [_kt("b", 0, 5)]}]}]},
    ]
    assert _pdf_page_text(_Trang(blocks)) == "êm AV x\nb\n"
