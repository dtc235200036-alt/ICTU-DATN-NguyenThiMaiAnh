"""Dịch vụ tải lên / lưu trữ / trích xuất tài liệu dùng CHUNG cho đề cương
(plan này), báo cáo tiến độ và báo cáo cuối (các plan sau — Pattern 1,
03-RESEARCH.md). Đây là MỘT nơi duy nhất kiểm tra định dạng/dung lượng file
và ghi xuống đĩa — không được fork ba bản riêng cho từng UC."""
import os
import unicodedata
import uuid
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pymupdf as fitz
from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.core.timeutil import now_utc
from app.models.bao_ve import LichBaoVe, ThanhVienHoiDong
from app.models.de_cuong import DOCX as DINH_DANG_DOCX
from app.models.de_cuong import PDF as DINH_DANG_PDF
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, TaiLieuDoAn
from app.models.de_tai import DeTai
from app.schemas.documents import DocumentOut

_TOM_TAT_MAX_CHARS = 600

_PDF_MAGIC = b"%PDF-"
_DOCX_MARKER = "word/document.xml"
# CR-01 (03-REVIEW): trần giải nén thấp + parse luồng (không dựng DOM) —
# XML nén ~1000:1 nên một DOCX ~1 MB có thể chứa hàng trăm MB XML; DOM của
# python-docx/lxml tốn gấp nhiều lần kích thước XML.
_MAX_DOCX_UNCOMPRESSED_BYTES = 25 * 1024 * 1024  # tổng giải nén mọi phần
_MAX_DOCX_XML_BYTES = 15 * 1024 * 1024  # riêng word/document.xml
_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_W_P = _W_NS + "p"
_W_T = _W_NS + "t"
_W_TAB = _W_NS + "tab"
_W_BR = _W_NS + "br"
_W_CR = _W_NS + "cr"

_FILE_TOO_LARGE_DETAIL = "File vượt quá dung lượng tối đa 20 MB (NFR-06)"
_FILE_EMPTY_DETAIL = "File rỗng, vui lòng chọn file khác"
_FILE_BAD_FORMAT_DETAIL = (
    "File không đúng định dạng DOCX hoặc PDF (hệ thống kiểm tra theo nội dung"
    " file, không theo đuôi file)"
)
_DOC_NOT_FOUND_DETAIL = "Không tìm thấy tài liệu"
_DOC_FORBIDDEN_DETAIL = "Bạn không có quyền xem tài liệu này"
_PATH_INVALID_DETAIL = "Đường dẫn tệp không hợp lệ"


@dataclass
class ValidatedFile:
    content: bytes
    dinh_dang: str
    ext: str
    ten_goc: str
    # CR-01: văn bản trích xuất NGAY khi validate (trước mọi khóa hàng) —
    # store() dùng lại, không parse trong transaction đang giữ FOR UPDATE.
    text: str | None = None
    text_extracted: bool = False


def _safe_basename(filename: str) -> str:
    """NFC-normalize và loại bỏ mọi phần đường dẫn (T-03-01/T-03-02) — tên
    file client gửi không bao giờ được dùng để dựng đường dẫn thật."""
    normalized = unicodedata.normalize("NFC", filename)
    base = normalized.replace("\\", "/").rsplit("/", 1)[-1]
    if len(base) <= 255:
        return base
    # IN-02: cắt phần tên, GIỮ đuôi file — đuôi quyết định định dạng được kiểm.
    suffix = Path(base).suffix
    if len(suffix) >= 255:
        return base[:255]
    return base[: 255 - len(suffix)] + suffix


def read_and_validate(upload: UploadFile) -> ValidatedFile:
    """D-01/T-03-01: đọc tối đa MAX_UPLOAD_BYTES + 1 byte; đuôi file VÀ magic
    bytes phải khớp nhau — không bao giờ tin `upload.content_type` (client
    tự khai, có thể giả mạo)."""
    settings = get_settings()
    content = upload.file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail=_FILE_TOO_LARGE_DETAIL)
    if len(content) == 0:
        raise HTTPException(status_code=422, detail=_FILE_EMPTY_DETAIL)

    ten_goc = _safe_basename(upload.filename or "")
    ext = Path(ten_goc).suffix.lower()

    if ext == ".pdf":
        if not content.startswith(_PDF_MAGIC):
            raise HTTPException(status_code=422, detail=_FILE_BAD_FORMAT_DETAIL)
        dinh_dang = DINH_DANG_PDF
    elif ext == ".docx":
        try:
            with zipfile.ZipFile(BytesIO(content)) as zf:
                if _DOCX_MARKER not in zf.namelist():
                    raise HTTPException(status_code=422, detail=_FILE_BAD_FORMAT_DETAIL)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=422, detail=_FILE_BAD_FORMAT_DETAIL) from None
        dinh_dang = DINH_DANG_DOCX
    else:
        raise HTTPException(status_code=422, detail=_FILE_BAD_FORMAT_DETAIL)

    return ValidatedFile(
        content=content,
        dinh_dang=dinh_dang,
        ext=ext.lstrip("."),
        ten_goc=ten_goc,
        text=extract_text(content, dinh_dang),
        text_extracted=True,
    )


def _extract_docx_text(content: bytes) -> str | None:
    """CR-01: đọc word/document.xml theo luồng (iterparse, expat — không tải
    DTD/thực thể ngoài) và xóa từng phần tử ngay khi xong, nên bộ nhớ chỉ tỉ
    lệ với độ sâu cây, không với kích thước XML. Ngữ nghĩa như python-docx
    `paragraph.text`: w:t nối liền, w:tab -> tab, w:br/w:cr -> xuống dòng."""
    with zipfile.ZipFile(BytesIO(content)) as zf:
        info = zf.getinfo(_DOCX_MARKER)
        total = sum(i.file_size for i in zf.infolist())
        if info.file_size > _MAX_DOCX_XML_BYTES or total > _MAX_DOCX_UNCOMPRESSED_BYTES:
            return None
        paragraphs: list[str] = []
        buf: list[str] = []
        stack: list[ET.Element] = []
        # ZipExtFile giới hạn đầu ra ở file_size đã khai báo (đã kiểm ở trên).
        with zf.open(info) as fh:
            for event, el in ET.iterparse(fh, events=("start", "end")):
                if event == "start":
                    stack.append(el)
                    continue
                stack.pop()
                tag = el.tag
                if tag == _W_T:
                    buf.append(el.text or "")
                elif tag == _W_TAB:
                    buf.append("\t")
                elif tag in (_W_BR, _W_CR):
                    buf.append("\n")
                elif tag == _W_P:
                    paragraphs.append("".join(buf))
                    buf.clear()
                # Mọi phần tử con đã xử lý xong trước "end" của cha -> gỡ khỏi
                # cha ngay (luôn là con cuối nên remove là O(1) thực tế).
                if stack:
                    stack[-1].remove(el)
                el.clear()
    return "\n".join(paragraphs)


def extract_text(content: bytes, dinh_dang: str) -> str | None:
    """D-03: trích xuất tốt nhất có thể (best-effort) — KHÔNG BAO GIỜ chặn
    việc nộp; mọi lỗi/kết quả rỗng trả về None (caller đánh dấu trich_xuat_loi)."""
    try:
        if dinh_dang == DINH_DANG_DOCX:
            text = _extract_docx_text(content)
            if text is None:
                return None
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


def storage_path(ten_luu_tru: str) -> Path:
    """Giải mã đường dẫn tuyệt đối dưới UPLOAD_DIR — từ chối nếu vượt ra
    ngoài (T-03-02, dù ten_luu_tru luôn do server sinh)."""
    settings = get_settings()
    base = Path(settings.UPLOAD_DIR).resolve()
    resolved = (base / ten_luu_tru).resolve()
    if not (resolved == base or base in resolved.parents):
        raise HTTPException(status_code=400, detail=_PATH_INVALID_DETAIL)
    return resolved


def remove_file_quietly(ten_luu_tru: str) -> None:
    """Bù trừ (compensation) khi commit của caller thất bại sau khi file đã
    được ghi xuống đĩa — không bao giờ ném lỗi."""
    try:
        storage_path(ten_luu_tru).unlink(missing_ok=True)
    except Exception:
        pass


def store(
    db: Session,
    *,
    de_tai_id: int,
    loai: str,
    vf: ValidatedFile,
    de_cuong_id: int | None = None,
) -> TaiLieuDoAn:
    """D-02: so_phien_ban tăng dần theo (de_tai_id, loai); tên lưu trữ luôn
    do server sinh (`{loai}/{uuid4}.{ext}`) — không bao giờ dùng tên gốc.
    `db.add` + `db.flush` — caller commit; nếu caller rollback, PHẢI gọi
    `remove_file_quietly(doc.ten_luu_tru)` để dọn file mồ côi."""
    settings = get_settings()
    max_version = db.execute(
        select(func.coalesce(func.max(TaiLieuDoAn.so_phien_ban), 0))
        .where(TaiLieuDoAn.de_tai_id == de_tai_id)
        .where(TaiLieuDoAn.loai == loai)
    ).scalar_one()
    so_phien_ban = int(max_version) + 1

    ten_luu_tru = f"{loai}/{uuid.uuid4().hex}.{vf.ext}"
    dir_path = Path(settings.UPLOAD_DIR) / loai
    dir_path.mkdir(parents=True, exist_ok=True)
    final_path = storage_path(ten_luu_tru)
    tmp_path = dir_path / f".tmp-{uuid.uuid4().hex}"
    tmp_path.write_bytes(vf.content)
    os.replace(tmp_path, final_path)

    text = vf.text if vf.text_extracted else extract_text(vf.content, vf.dinh_dang)

    doc = TaiLieuDoAn(
        de_tai_id=de_tai_id,
        de_cuong_id=de_cuong_id,
        loai=loai,
        so_phien_ban=so_phien_ban,
        ten_goc=vf.ten_goc,
        ten_luu_tru=ten_luu_tru,
        kich_thuoc=len(vf.content),
        dinh_dang=vf.dinh_dang,
        thoi_diem_nop=now_utc(),
        noi_dung_trich_xuat=text,
        trich_xuat_loi=text is None,
    )
    db.add(doc)
    db.flush()
    return doc


def is_committee_member_for_topic(db: Session, giang_vien_id: int, de_tai_id: int) -> bool:
    """DEFN-03/UC4.3 E1: GV là thành viên (thanh_vien_hoi_dong) của hội đồng
    đang giữ lich_bao_ve của đề tài này."""
    count = db.execute(
        select(func.count())
        .select_from(ThanhVienHoiDong)
        .join(LichBaoVe, LichBaoVe.hoi_dong_id == ThanhVienHoiDong.hoi_dong_id)
        .where(LichBaoVe.de_tai_id == de_tai_id)
        .where(ThanhVienHoiDong.giang_vien_id == giang_vien_id)
    ).scalar_one()
    return count > 0


def can_view(db: Session, user: CurrentUser, doc: TaiLieuDoAn) -> bool:
    """T-03-04: Bộ môn luôn xem được; SV chủ đề tài; GV là GVHD của đề tài;
    T-03-20 (plan 03-04): thành viên hội đồng bảo vệ của đề tài — CHỈ với báo
    cáo cuối (BAO_CAO_CUOI), không bao giờ với đề cương/báo cáo tiến độ."""
    if user.vai_tro == VaiTro.BO_MON:
        return True
    topic = db.get(DeTai, doc.de_tai_id)
    if topic is None:
        return False
    if user.vai_tro == VaiTro.SINH_VIEN and user.sinh_vien_id is not None:
        return topic.sinh_vien_id == user.sinh_vien_id
    if user.vai_tro == VaiTro.GIANG_VIEN and user.giang_vien_id is not None:
        if topic.giang_vien_id == user.giang_vien_id:
            return True
        return doc.loai == LOAI_BAO_CAO_CUOI and is_committee_member_for_topic(
            db, user.giang_vien_id, topic.id
        )
    return False


def get_viewable_or_error(db: Session, user: CurrentUser, doc_id: int) -> TaiLieuDoAn:
    doc = db.get(TaiLieuDoAn, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=_DOC_NOT_FOUND_DETAIL)
    if not can_view(db, user, doc):
        raise HTTPException(status_code=403, detail=_DOC_FORBIDDEN_DETAIL)
    return doc


def to_document_out(doc: TaiLieuDoAn) -> DocumentOut:
    tom_tat = doc.noi_dung_trich_xuat[:_TOM_TAT_MAX_CHARS] if doc.noi_dung_trich_xuat else None
    return DocumentOut(
        id=doc.id,
        loai=doc.loai,
        so_phien_ban=doc.so_phien_ban,
        ten_goc=doc.ten_goc,
        kich_thuoc=doc.kich_thuoc,
        dinh_dang=doc.dinh_dang,
        thoi_diem_nop=doc.thoi_diem_nop,
        trich_xuat_loi=doc.trich_xuat_loi,
        tom_tat=tom_tat,
    )
