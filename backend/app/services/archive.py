"""UC5 — Kho đồ án (D-07). Phần này (plan 03-04): tự lưu kho khi Bộ môn chốt
kết quả bảo vệ (UC5.2) và đẩy bản ghi sang Dịch vụ AI để index qua seam
`ai_client` sau commit. Plan 03-05 bổ sung tìm kiếm/CRUD/import CSV.

Quy tắc payload /ingest (§3.3.5 `{id, type, text}`, Phase 4 — 04-05): mọi
bản ghi kho gửi `("ARCHIVE", tên đề tài NFC)` với id = do_an_kho.id — không
gian id ARCHIVE riêng, không đụng TOPIC (de_tai.id) hay DOCUMENT
(tai_lieu_do_an.id). Báo cáo cuối của đồ án được index dưới id tài liệu của
chính nó (plan 04-06).

Plan 03-05 (UC5.1/UC5.3/UC5.4): tra cứu, chi tiết + tải báo cáo cuối, CRUD của
Bộ môn, index lại và import CSV khóa cũ (thành công một phần, báo lỗi theo
dòng). Xóa bản ghi chỉ xóa khỏi thesis_core — hợp đồng §3.3.5 chưa có
/delete phía AI (Phase 4)."""
import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.db import SessionLocal
from app.models.bao_ve import LichBaoVe
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, TaiLieuDoAn
from app.models.de_tai import DeTai
from app.models.kho import CHUA_INDEX, DA_INDEX, HE_THONG, IMPORT, DoAnKho
from app.models.tai_khoan import GiangVien, SinhVien
from app.schemas.archive import (
    ArchiveDetail,
    ArchiveIn,
    ArchiveListItem,
    ArchiveStudent,
    ImportResult,
    ImportRowError,
)
from app.schemas.common import Page, nfc
from app.schemas.topics import PersonRef
from app.services import documents
from app.services.ai_client import get_ai_client

_logger = logging.getLogger(__name__)

INGEST_ARCHIVE = "ARCHIVE"


def insert_from_defense(db: Session, lich: LichBaoVe) -> DoAnKho:
    """UC5.2/REPO-01: một bản ghi kho HE_THONG cho SV vừa được chốt điểm —
    add + flush, KHÔNG commit (caller — defense.finalize — commit cùng lúc với
    da_chot và thông báo). UNIQUE(de_tai_id) chặn chèn trùng khi đua nhau."""
    topic = db.get(DeTai, lich.de_tai_id)
    sv = db.get(SinhVien, lich.sinh_vien_id)
    khoa = topic.dot_do_an.khoa if topic is not None and topic.dot_do_an is not None else None
    kho = DoAnKho(
        de_tai_id=lich.de_tai_id,
        sinh_vien_id=lich.sinh_vien_id,
        giang_vien_id=topic.giang_vien_id if topic is not None else None,
        khoa=khoa,
        ten_de_tai=topic.ten_de_tai if topic is not None else "",
        tu_khoa=None,
        diem=lich.diem_trung_binh,
        nguon=HE_THONG,
        trang_thai_index=CHUA_INDEX,
        ma_so_sinh_vien=sv.ma_so_sinh_vien if sv is not None else None,
        ho_ten_sinh_vien=sv.ho_ten if sv is not None else None,
    )
    db.add(kho)
    db.flush()
    return kho


def latest_final_report(db: Session, de_tai_id: int | None) -> TaiLieuDoAn | None:
    """"File" của bản ghi kho = phiên bản BAO_CAO_CUOI mới nhất của đề tài
    (không có cột riêng — D-07)."""
    if de_tai_id is None:
        return None
    return (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == de_tai_id)
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def ingest_payload(db: Session, kho: DoAnKho) -> tuple[str, str]:
    """04-05: không gian ARCHIVE (id = do_an_kho.id), CHỈ tên đề tài — cùng
    dạng văn bản với TOPIC nên /check-title so sánh tên với tên."""
    return INGEST_ARCHIVE, nfc(kho.ten_de_tai)


def run_ingest(do_an_kho_ids: list[int]) -> None:
    """Chạy nền SAU commit (BackgroundTasks) — mở SessionLocal RIÊNG; mỗi id
    một try/except độc lập: lỗi AI để nguyên CHUA_INDEX, ghi log và sang id
    kế tiếp (UC5.2 E1 — không bao giờ chặn lưu kho; Bộ môn index lại sau)."""
    task_db = SessionLocal()
    try:
        for kho_id in do_an_kho_ids:
            try:
                kho = task_db.get(DoAnKho, kho_id)
                if kho is None:
                    continue
                loai, text = ingest_payload(task_db, kho)
                get_ai_client(task_db).ingest(kho.id, loai, text)
                task_db.execute(
                    update(DoAnKho).where(DoAnKho.id == kho_id).values(trang_thai_index=DA_INDEX)
                )
                task_db.commit()
            except Exception:
                task_db.rollback()
                try:
                    task_db.execute(
                        update(DoAnKho)
                        .where(DoAnKho.id == kho_id)
                        .values(trang_thai_index=CHUA_INDEX)
                    )
                    task_db.commit()
                except Exception:
                    task_db.rollback()
                _logger.exception("archive.run_ingest thất bại cho do_an_kho_id=%s", kho_id)
    finally:
        task_db.close()


# --- UC5.1: tra cứu / chi tiết / tải báo cáo cuối (mọi vai trò) -------------

_NOT_FOUND_DETAIL = "Không tìm thấy bản ghi kho"
_NO_FILE_DETAIL = "Bản ghi kho không có file báo cáo"
_DUPLICATE_DETAIL = "Đã có bản ghi cùng khóa và tên đề tài"
_GV_NOT_FOUND_DETAIL = "Không tìm thấy giảng viên hướng dẫn"

_MEDIA_TYPES = {
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "PDF": "application/pdf",
}


def _get_or_404(db: Session, kho_id: int) -> DoAnKho:
    kho = db.execute(
        select(DoAnKho).where(DoAnKho.id == kho_id).options(selectinload(DoAnKho.giang_vien))
    ).scalar_one_or_none()
    if kho is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    return kho


def _item_fields(kho: DoAnKho, co_file: bool) -> dict:
    sinh_vien = (
        ArchiveStudent(ma=kho.ma_so_sinh_vien, ho_ten=kho.ho_ten_sinh_vien)
        if kho.ma_so_sinh_vien or kho.ho_ten_sinh_vien
        else None
    )
    gv = kho.giang_vien
    return dict(
        id=kho.id,
        ten_de_tai=kho.ten_de_tai,
        khoa=kho.khoa,
        sinh_vien=sinh_vien,
        giang_vien=(
            PersonRef(id=gv.id, ho_ten=gv.ho_ten or "", ma=gv.ma_giang_vien) if gv is not None else None
        ),
        diem=float(kho.diem) if kho.diem is not None else None,
        tu_khoa=kho.tu_khoa,
        nguon=kho.nguon,
        trang_thai_index=kho.trang_thai_index,
        co_file=co_file,
    )


def list_archive(
    db: Session,
    khoa: str | None,
    giang_vien_id: int | None,
    q: str | None,
    page: int,
    page_size: int,
) -> Page[ArchiveListItem]:
    """UC5.1/REPO-02: lọc AND theo khóa, GVHD, từ khóa (contains trên tên đề
    tài HOẶC từ khóa; autoescape=True — "%"/"_" là ký tự thường, T-03-27);
    so sánh theo collation utf8mb4_vietnamese_ci của bảng."""
    stmt = select(DoAnKho)
    if khoa:
        stmt = stmt.where(DoAnKho.khoa == nfc(khoa).strip())
    if giang_vien_id is not None:
        stmt = stmt.where(DoAnKho.giang_vien_id == giang_vien_id)
    term = nfc(q).strip() if q else ""
    if term:
        stmt = stmt.where(
            or_(
                DoAnKho.ten_de_tai.contains(term, autoescape=True),
                DoAnKho.tu_khoa.contains(term, autoescape=True),
            )
        )
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = (
        db.execute(
            stmt.options(selectinload(DoAnKho.giang_vien))
            .order_by(DoAnKho.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    # co_file: MỘT truy vấn cho cả trang (không N+1).
    de_tai_ids = {r.de_tai_id for r in rows if r.de_tai_id is not None}
    with_file: set[int] = set()
    if de_tai_ids:
        with_file = set(
            db.execute(
                select(TaiLieuDoAn.de_tai_id)
                .where(TaiLieuDoAn.de_tai_id.in_(de_tai_ids))
                .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
                .distinct()
            )
            .scalars()
            .all()
        )
    items = [ArchiveListItem(**_item_fields(r, r.de_tai_id in with_file)) for r in rows]
    return Page[ArchiveListItem](items=items, total=total, page=page, page_size=page_size)


def khoa_options(db: Session) -> list[str]:
    return list(
        db.execute(
            select(DoAnKho.khoa).where(DoAnKho.khoa.is_not(None)).distinct().order_by(DoAnKho.khoa.desc())
        )
        .scalars()
        .all()
    )


def _detail_out(db: Session, kho: DoAnKho) -> ArchiveDetail:
    doc = latest_final_report(db, kho.de_tai_id)
    return ArchiveDetail(
        **_item_fields(kho, doc is not None),
        de_tai_id=kho.de_tai_id,
        sinh_vien_id=kho.sinh_vien_id,
        file=documents.to_document_out(doc) if doc is not None else None,
    )


def get_detail(db: Session, kho_id: int) -> ArchiveDetail:
    return _detail_out(db, _get_or_404(db, kho_id))


def file_path_or_404(db: Session, kho_id: int) -> tuple[Path, str, str]:
    """UC5.1: mọi vai trò đã đăng nhập tải được báo cáo cuối ĐÃ LƯU KHO (chỉ
    BAO_CAO_CUOI của đề tài gắn với bản ghi — T-03-30); tài liệu khác vẫn
    nằm sau documents.can_view."""
    kho = _get_or_404(db, kho_id)
    doc = latest_final_report(db, kho.de_tai_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=_NO_FILE_DETAIL)
    path = documents.storage_path(doc.ten_luu_tru)
    if not path.exists():
        raise HTTPException(status_code=404, detail=_NO_FILE_DETAIL)
    return path, doc.ten_goc, _MEDIA_TYPES.get(doc.dinh_dang, "application/octet-stream")


# --- UC5.3: thêm / sửa / xóa / index lại (Bộ môn) ---------------------------


def _find_sv_by_ma(db: Session, ma: str | None) -> SinhVien | None:
    if not ma:
        return None
    return db.execute(select(SinhVien).where(SinhVien.ma_so_sinh_vien == ma)).scalar_one_or_none()


def _validate_payload(db: Session, payload: ArchiveIn, exclude_id: int | None) -> SinhVien | None:
    if payload.giang_vien_id is not None and db.get(GiangVien, payload.giang_vien_id) is None:
        raise HTTPException(status_code=422, detail=_GV_NOT_FOUND_DETAIL)
    dup = select(DoAnKho.id).where(DoAnKho.khoa == payload.khoa).where(
        DoAnKho.ten_de_tai == payload.ten_de_tai
    )
    if exclude_id is not None:
        dup = dup.where(DoAnKho.id != exclude_id)
    if db.execute(dup.limit(1)).first() is not None:
        raise HTTPException(status_code=409, detail=_DUPLICATE_DETAIL)
    return _find_sv_by_ma(db, payload.ma_so_sinh_vien)


def _apply(kho: DoAnKho, payload: ArchiveIn, sv: SinhVien | None) -> None:
    kho.khoa = payload.khoa
    kho.ten_de_tai = payload.ten_de_tai
    kho.ma_so_sinh_vien = payload.ma_so_sinh_vien
    kho.ho_ten_sinh_vien = payload.ho_ten_sinh_vien or (sv.ho_ten if sv is not None else None)
    kho.sinh_vien_id = sv.id if sv is not None else None
    kho.giang_vien_id = payload.giang_vien_id
    kho.tu_khoa = payload.tu_khoa
    kho.diem = payload.diem
    # Nội dung đổi -> phải index lại (run_ingest nền sẽ lật sang DA_INDEX).
    kho.trang_thai_index = CHUA_INDEX


def create(db: Session, payload: ArchiveIn) -> int:
    """UC5.3 A1: bản ghi thêm tay (không qua bảo vệ) — nguồn IMPORT, không file."""
    sv = _validate_payload(db, payload, None)
    kho = DoAnKho(nguon=IMPORT, trang_thai_index=CHUA_INDEX, ten_de_tai=payload.ten_de_tai)
    _apply(kho, payload, sv)
    db.add(kho)
    db.commit()
    return kho.id


def update_record(db: Session, kho_id: int, payload: ArchiveIn) -> None:
    """UC5.3: sửa metadata — nguon và de_tai_id không bao giờ đổi."""
    kho = _get_or_404(db, kho_id)
    sv = _validate_payload(db, payload, kho_id)
    _apply(kho, payload, sv)
    db.commit()


def delete(db: Session, kho_id: int) -> None:
    """UC5.3 E1: chỉ xóa hàng do_an_kho — chi_tiet_trung_lap lưu doi_tuong_trung
    dạng văn bản (không FK) nên lịch sử kiểm tra trùng lặp giữ nguyên."""
    kho = _get_or_404(db, kho_id)
    db.delete(kho)
    db.commit()


def mark_for_reindex(db: Session, kho_id: int) -> None:
    _get_or_404(db, kho_id)
    db.execute(update(DoAnKho).where(DoAnKho.id == kho_id).values(trang_thai_index=CHUA_INDEX))
    db.commit()


# --- UC5.4: import CSV khóa cũ (Bộ môn) --------------------------------------

CSV_MAX_BYTES = 2 * 1024 * 1024
CSV_MAX_ROWS = 2000
CSV_REQUIRED_COLUMNS = ("khoa", "ten_de_tai")
_CSV_COLUMNS = (
    "khoa",
    "ten_de_tai",
    "ma_so_sinh_vien",
    "ho_ten_sinh_vien",
    "ma_giang_vien",
    "tu_khoa",
    "diem",
)
_DIEM_INVALID = "Điểm không hợp lệ (0–10)"
_DIEM_STEP = Decimal("0.01")


def _parse_diem(raw: str) -> Decimal | None:
    """ "8.5" hoặc "8,5" -> Decimal; ngoài [0, 10] hoặc quá 2 chữ số thập phân
    -> ValueError. Chỉ phân tích số — nội dung ô không bao giờ được đánh giá."""
    try:
        value = Decimal(raw.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError from exc
    if not value.is_finite() or value < 0 or value > 10 or value != value.quantize(_DIEM_STEP):
        raise ValueError
    return value.quantize(_DIEM_STEP)


def _key(khoa: str, ten: str) -> tuple[str, str]:
    # Khớp hành vi so sánh không phân biệt hoa/thường của utf8mb4_vietnamese_ci.
    return khoa.casefold(), ten.casefold()


def _decode_csv(upload: UploadFile) -> str:
    content = upload.file.read(CSV_MAX_BYTES + 1)
    if len(content) > CSV_MAX_BYTES:
        raise HTTPException(status_code=422, detail="File CSV tối đa 2 MB")
    if not content.strip():
        raise HTTPException(status_code=422, detail="File CSV rỗng")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="File CSV phải mã hóa UTF-8") from exc


def import_csv(db: Session, upload: UploadFile) -> tuple[ImportResult, list[int]]:
    """UC5.4 + E1: dòng lỗi bị bỏ qua và liệt kê (số dòng vật lý, tiêu đề = 1,
    kèm lý do); các dòng hợp lệ được chèn trong MỘT giao dịch (nguồn IMPORT,
    CHUA_INDEX), NFC hóa từng ô. Trả (kết quả, id mới) — router xếp run_ingest."""
    text = _decode_csv(upload)
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if ";" in first_line and "," not in first_line else ","
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    header = [nfc(h or "").strip().casefold() for h in (reader.fieldnames or [])]
    missing = [c for c in CSV_REQUIRED_COLUMNS if c not in header]
    if missing:
        raise HTTPException(
            status_code=422, detail=f"File CSV thiếu cột bắt buộc: {', '.join(missing)}"
        )
    reader.fieldnames = header

    parsed: list[tuple[int, dict[str, str]]] = []
    try:
        for raw in reader:
            cells = {
                col: nfc(raw.get(col) or "").strip() if isinstance(raw.get(col), str) else ""
                for col in _CSV_COLUMNS
            }
            if not any(cells.values()) and not any(
                isinstance(v, str) and v.strip() for v in raw.values()
            ):
                continue  # dòng trống hoàn toàn (thường ở cuối file xuất từ bảng tính)
            parsed.append((reader.line_num, cells))
            if len(parsed) > CSV_MAX_ROWS:
                raise HTTPException(
                    status_code=422, detail=f"File CSV tối đa {CSV_MAX_ROWS} dòng dữ liệu"
                )
    except csv.Error as exc:
        # WR-08: ô vượt field_size_limit, dấu ngoặc kép hỏng... -> 422 có số dòng
        # thay vì 500 (không đưa nội dung ô vào thông điệp).
        raise HTTPException(
            status_code=422,
            detail=f"File CSV không hợp lệ gần dòng {reader.line_num + 1}: {type(exc).__name__}"
            f" ({str(exc)[:120]})",
        ) from None

    # Tra cứu gộp (không N+1): GV theo mã, SV theo mã, bản ghi kho sẵn có theo khóa.
    ma_gv = {c["ma_giang_vien"] for _, c in parsed if c["ma_giang_vien"]}
    gv_by_ma: dict[str, GiangVien] = {}
    if ma_gv:
        for gv in db.execute(select(GiangVien).where(GiangVien.ma_giang_vien.in_(ma_gv))).scalars():
            gv_by_ma[(gv.ma_giang_vien or "").casefold()] = gv
    ma_sv = {c["ma_so_sinh_vien"] for _, c in parsed if c["ma_so_sinh_vien"]}
    sv_by_ma: dict[str, SinhVien] = {}
    if ma_sv:
        for sv in db.execute(select(SinhVien).where(SinhVien.ma_so_sinh_vien.in_(ma_sv))).scalars():
            sv_by_ma[(sv.ma_so_sinh_vien or "").casefold()] = sv
    khoas = {c["khoa"] for _, c in parsed if c["khoa"]}
    seen: set[tuple[str, str]] = set()
    if khoas:
        for k, t in db.execute(
            select(DoAnKho.khoa, DoAnKho.ten_de_tai).where(DoAnKho.khoa.in_(khoas))
        ).all():
            seen.add(_key(k or "", t))

    errors: list[ImportRowError] = []
    new_rows: list[DoAnKho] = []
    for dong, c in parsed:
        reasons: list[str] = []
        if not c["khoa"]:
            reasons.append("Thiếu khóa")
        elif len(c["khoa"]) > 20:
            reasons.append("Khóa quá 20 ký tự")
        if not c["ten_de_tai"]:
            reasons.append("Thiếu tên đề tài")
        elif len(c["ten_de_tai"]) > 255:
            reasons.append("Tên đề tài quá 255 ký tự")
        if len(c["ma_so_sinh_vien"]) > 20:
            reasons.append("Mã sinh viên quá 20 ký tự")
        if len(c["ho_ten_sinh_vien"]) > 150:
            reasons.append("Họ tên sinh viên quá 150 ký tự")
        if len(c["tu_khoa"]) > 255:
            reasons.append("Từ khóa quá 255 ký tự")
        diem = None
        if c["diem"]:
            try:
                diem = _parse_diem(c["diem"])
            except ValueError:
                reasons.append(_DIEM_INVALID)
        gv = None
        if c["ma_giang_vien"]:
            gv = gv_by_ma.get(c["ma_giang_vien"].casefold())
            if gv is None:
                reasons.append(f"Không tìm thấy giảng viên mã {c['ma_giang_vien']}")
        if c["khoa"] and c["ten_de_tai"] and _key(c["khoa"], c["ten_de_tai"]) in seen:
            reasons.append("Trùng bản ghi (khóa, tên đề tài)")
        if reasons:
            errors.append(ImportRowError(dong=dong, ly_do="; ".join(reasons)))
            continue

        seen.add(_key(c["khoa"], c["ten_de_tai"]))
        sv = sv_by_ma.get(c["ma_so_sinh_vien"].casefold()) if c["ma_so_sinh_vien"] else None
        new_rows.append(
            DoAnKho(
                khoa=c["khoa"],
                ten_de_tai=c["ten_de_tai"],
                ma_so_sinh_vien=c["ma_so_sinh_vien"] or None,
                ho_ten_sinh_vien=c["ho_ten_sinh_vien"] or (sv.ho_ten if sv is not None else None),
                sinh_vien_id=sv.id if sv is not None else None,
                giang_vien_id=gv.id if gv is not None else None,
                tu_khoa=c["tu_khoa"] or None,
                diem=diem,
                nguon=IMPORT,
                trang_thai_index=CHUA_INDEX,
            )
        )

    if new_rows:
        try:
            db.add_all(new_rows)
            db.commit()
        except (IntegrityError, DataError):
            # WR-08: ràng buộc mà bước kiểm tra trước bỏ sót (vd. import đồng
            # thời trùng khóa + tên) -> 409, không phải 500.
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Không lưu được dữ liệu import — vui lòng kiểm tra lại file",
            ) from None
    result = ImportResult(tong_dong=len(parsed), thanh_cong=len(new_rows), loi=errors)
    return result, [r.id for r in new_rows]
