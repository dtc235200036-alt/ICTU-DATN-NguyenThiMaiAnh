"""Xuất DOCX (python-docx) và PDF (reportlab) từ CÙNG một danh sách khối có thứ tự.

Không dùng LibreOffice (04-RESEARCH): hai định dạng mang cùng văn bản từng đoạn.
PDF dùng TrueType DejaVuSans (có đủ glyph tiếng Việt, lớp văn bản có ToUnicode) và vẽ
đầu trang "Đồ án tốt nghiệp - Khoa Công nghệ thông tin" + số trang trên MỌI trang — đúng
kiểu rò rỉ đầu/chân trang mà bộ lọc dòng lặp của dịch vụ AI phải loại bỏ.
Cả hai định dạng được ghi tất định (PDF invariant, DOCX cố định thời gian trong zip/core).
"""

from __future__ import annotations

import datetime as _dt
import io
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from . import vocab

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
THOI_DIEM = _dt.datetime(2026, 9, 28, 8, 0, 0)
ZIP_TIME = (2026, 9, 28, 8, 0, 0)
TAC_GIA = "ntma-datagen"
_font_ok = False


def _dang_ky_font() -> None:
    global _font_ok
    if not _font_ok:
        pdfmetrics.registerFont(TTFont(FONT, str(FONT_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, str(FONT_DIR / "DejaVuSans-Bold.ttf")))
        _font_ok = True


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------
def _field_page(paragraph) -> None:
    run = paragraph.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    run._r.addnext(fld)


def _font(style, size: float, bold: bool = False) -> None:
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), "Times New Roman")


def _docx_bytes(khoi: list[tuple[str, str, str]], tieu_de: str) -> bytes:
    doc = Document()
    _font(doc.styles["Normal"], 13)
    _font(doc.styles["Heading 1"], 14, bold=True)
    _font(doc.styles["Heading 2"], 13, bold=True)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    hp = sec.header.paragraphs[0]
    hp.text = vocab.DAU_TRANG
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _field_page(fp)
    rong = sec.page_width - sec.left_margin - sec.right_margin

    for loai, text, phu in khoi:
        if loai in ("bia", "bia_lon", "bia_trong"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if text:
                run = p.add_run(text)
                run.bold = True
                if loai == "bia_lon":
                    run.font.size = Pt(18)
        elif loai == "tieu_de_1":
            h = doc.add_heading(text, level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            h.paragraph_format.page_break_before = True
        elif loai == "tieu_de_2":
            doc.add_heading(text, level=2)
        elif loai in ("doan", "van_ban"):
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1)
        elif loai == "phai":
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif loai == "muc_luc":
            p = doc.add_paragraph(f"{text}\t{phu}")
            p.paragraph_format.tab_stops.add_tab_stop(rong, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        elif loai == "chu_thich":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(text).italic = True
        elif loai == "tltk":
            doc.add_paragraph(text)
        else:
            raise ValueError(loai)

    cp = doc.core_properties
    cp.title = tieu_de
    cp.author = TAC_GIA
    cp.last_modified_by = TAC_GIA
    cp.created = THOI_DIEM
    cp.modified = THOI_DIEM
    cp.revision = 1
    buf = io.BytesIO()
    doc.save(buf)
    # Chuẩn hóa zip để tệp giống từng byte giữa các lần sinh.
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as zin, \
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=ZIP_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = info.external_attr
            zout.writestr(zi, zin.read(info.filename))
    return out.getvalue()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def _styles() -> dict[str, ParagraphStyle]:
    return {
        "bia": ParagraphStyle("bia", fontName=FONT_BOLD, fontSize=12, leading=19, alignment=TA_CENTER, spaceAfter=6),
        "bia_lon": ParagraphStyle("bia_lon", fontName=FONT_BOLD, fontSize=18, leading=26, alignment=TA_CENTER,
                                  spaceBefore=24, spaceAfter=18),
        "tieu_de_1": ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=14, leading=20, alignment=TA_CENTER,
                                    spaceAfter=14),
        "tieu_de_2": ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=12, leading=18, alignment=TA_LEFT,
                                    spaceBefore=8, spaceAfter=6),
        "doan": ParagraphStyle("doan", fontName=FONT, fontSize=11.5, leading=17, alignment=TA_JUSTIFY,
                               firstLineIndent=1 * cm, spaceAfter=6),
        "phai": ParagraphStyle("phai", fontName=FONT, fontSize=11.5, leading=17, alignment=TA_RIGHT),
        "muc_luc": ParagraphStyle("muc_luc", fontName=FONT, fontSize=11.5, leading=18, alignment=TA_LEFT),
        "chu_thich": ParagraphStyle("chu_thich", fontName=FONT, fontSize=10.5, leading=15, alignment=TA_CENTER,
                                    spaceBefore=4, spaceAfter=10),
        "tltk": ParagraphStyle("tltk", fontName=FONT, fontSize=11, leading=16, alignment=TA_LEFT, spaceAfter=4),
    }


def _dong_muc_luc(text: str, trang: str, rong: float, style: ParagraphStyle) -> str:
    """Dòng mục lục có chấm dẫn (dot leader) lấp đầy chiều rộng khung — như PDF xuất từ Word."""
    w = lambda s: pdfmetrics.stringWidth(s, style.fontName, style.fontSize)  # noqa: E731
    # chừa lề vài chấm để Paragraph không ngắt dòng chuỗi chấm dẫn
    so_cham = max(3, int((rong - w(text) - w(trang) - 2 * w(" ")) / w(".")) - 6)
    return f"{text} {'.' * so_cham} {trang}"


def _pdf_bytes(khoi: list[tuple[str, str, str]], tieu_de: str) -> bytes:
    _dang_ky_font()
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=3 * cm, rightMargin=2 * cm, topMargin=2.5 * cm,
                            bottomMargin=2.2 * cm, title=tieu_de, author=TAC_GIA, creator=TAC_GIA,
                            subject="Tài liệu thử nghiệm tổng hợp (DATA-03)", invariant=1, allowSplitting=0)
    rong = A4[0] - 5 * cm

    def trang(canvas, d) -> None:
        canvas.saveState()
        canvas.setFont(FONT, 9)
        canvas.drawCentredString(A4[0] / 2, A4[1] - 1.4 * cm, vocab.DAU_TRANG)
        canvas.setLineWidth(0.4)
        canvas.line(3 * cm, A4[1] - 1.6 * cm, A4[0] - 2 * cm, A4[1] - 1.6 * cm)
        canvas.drawCentredString(A4[0] / 2, 1.2 * cm, str(d.page))
        canvas.restoreState()

    story = []
    for loai, text, phu in khoi:
        if loai == "bia_trong":
            story.append(Spacer(1, 1.2 * cm))
        elif loai == "tieu_de_1":
            story += [PageBreak(), Paragraph(escape(text), st["tieu_de_1"])]
        elif loai in ("doan", "van_ban"):
            story.append(Paragraph(escape(text), st["doan"]))
        elif loai == "muc_luc":
            story.append(Paragraph(escape(_dong_muc_luc(text, phu, rong, st["muc_luc"])), st["muc_luc"]))
        elif loai in st:
            story.append(Paragraph(escape(text), st[loai]))
        else:
            raise ValueError(loai)
    doc.build(story, onFirstPage=trang, onLaterPages=trang)
    return buf.getvalue()


def ve(path: Path, dinh_dang: str, khoi: list[tuple[str, str, str]], *, tieu_de: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _docx_bytes(khoi, tieu_de) if dinh_dang == "DOCX" else _pdf_bytes(khoi, tieu_de)
    path.write_bytes(data)
