"""Kiểm tra trùng lặp tài liệu bất đồng bộ (D-04, UC0.7, §3.3.7) — Pattern 4
(03-RESEARCH.md): hàm `run` chạy trong FastAPI BackgroundTasks, PHẢI mở
SessionLocal RIÊNG (không bao giờ dùng session của request) và PHẢI luôn kết
thúc ở HOAN_TAT hoặc LOI — không bao giờ để lại DANG_KIEM_TRA
(trang-thai-kiem-tra-trung-lap.puml)."""
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.core.timeutil import now_utc
from app.models.cau_hinh_nguong import NGUONG_TAI_LIEU, CauHinhNguong
from app.models.de_cuong import TaiLieuDoAn
from app.models.de_tai import DeTai
from app.models.kho import DoAnKho
from app.models.trung_lap import (
    DANG_KIEM_TRA,
    HOAN_TAT,
    LOI,
    NGUON_ARCHIVE,
    NGUON_DOCUMENT,
    TAI_LIEU,
    ChiTietTrungLap,
    KetQuaKiemTraTrungLap,
)
from app.schemas.documents import CheckDetail, CheckMatch, CheckSegment, CheckSummary
from app.schemas.topics import PersonRef
from app.services.ai_client import get_ai_client
from app.services.documents import to_document_out

_logger = logging.getLogger(__name__)

# WR-02-tương tự: chỉ dùng để LƯU VẾT khi cau_hinh_nguong thiếu dòng
# NGUONG_TAI_LIEU — khớp giá trị seed ở migration 0004.
_FALLBACK_NGUONG_TAI_LIEU = 30.00
_RECHECK_NOT_LOI_DETAIL = "Chỉ kiểm tra lại được khi kết quả đang ở trạng thái Lỗi"


def _get_threshold(db: Session) -> float:
    try:
        gia_tri = db.execute(
            select(CauHinhNguong.gia_tri).where(CauHinhNguong.loai == NGUONG_TAI_LIEU)
        ).scalar_one()
        return float(gia_tri)
    except NoResultFound:
        return _FALLBACK_NGUONG_TAI_LIEU


def create_pending(db: Session, doc: TaiLieuDoAn) -> KetQuaKiemTraTrungLap:
    """D-04: một dòng ket_qua_kiem_tra_trung_lap (DANG_KIEM_TRA) trong CÙNG
    transaction với submit — caller commit, KHÔNG commit ở đây."""
    nguong = _get_threshold(db)
    doi_tuong = f"{doc.loai} v{doc.so_phien_ban} - {doc.ten_goc}"[:255]
    ket_qua = KetQuaKiemTraTrungLap(
        de_tai_id=doc.de_tai_id,
        tai_lieu_do_an_id=doc.id,
        loai_kiem_tra=TAI_LIEU,
        trang_thai=DANG_KIEM_TRA,
        nguong_ap_dung=nguong,
        doi_tuong_duoc_kiem_tra=doi_tuong,
        thoi_diem=now_utc(),
    )
    db.add(ket_qua)
    db.flush()
    return ket_qua


def _label_for(db: Session, loai: str, ref_id: int) -> str:
    """WR-06: tra nhãn THEO KHÔNG GIAN id — ARCHIVE là do_an_kho.id, DOCUMENT
    là tai_lieu_do_an.id; không bao giờ đọc một id kho như id tài liệu."""
    if loai == NGUON_ARCHIVE:
        kho = db.get(DoAnKho, ref_id)
        if kho is None:
            return f"Đồ án kho #{ref_id}"
        label = f"{kho.ten_de_tai} ({kho.khoa})" if kho.khoa else kho.ten_de_tai
        return label[:255]
    doc = db.get(TaiLieuDoAn, ref_id)
    if doc is None:
        return f"Tài liệu #{ref_id}"
    topic = db.get(DeTai, doc.de_tai_id)
    if topic is None:
        return f"Tài liệu #{ref_id}"
    khoa = topic.dot_do_an.khoa if topic.dot_do_an is not None else ""
    label = f"{topic.ten_de_tai} ({khoa})" if khoa else topic.ten_de_tai
    return label[:255]


def _mark_loi(task_db: Session, ket_qua_id: int, stamp: datetime | None = None) -> None:
    """`stamp` (WR-05): chỉ lật LOI nếu bản ghi vẫn thuộc về lần chạy này —
    một lần chạy cũ thất bại muộn không được đè lên lần kiểm tra lại mới."""
    stmt = (
        update(KetQuaKiemTraTrungLap)
        .where(KetQuaKiemTraTrungLap.id == ket_qua_id)
        .where(KetQuaKiemTraTrungLap.trang_thai == DANG_KIEM_TRA)
    )
    if stamp is not None:
        stmt = stmt.where(KetQuaKiemTraTrungLap.thoi_diem == stamp)
    task_db.execute(stmt.values(trang_thai=LOI))
    task_db.commit()


def run(ket_qua_id: int) -> None:
    """Chạy nền sau response 202 — mở SessionLocal riêng, broad except cố ý:
    BẤT KỲ lỗi gì cũng phải chuyển bản ghi sang LOI, không bao giờ để lại
    DANG_KIEM_TRA (Pitfall 1, 03-RESEARCH.md).

    WR-05 — dấu sở hữu: `thoi_diem` đọc từ DB lúc bắt đầu là dấu của lần chạy
    (create_pending/request_recheck đặt mới mỗi lần). Kết quả chỉ được ghi
    khi UPDATE có điều kiện (DANG_KIEM_TRA + đúng dấu) khớp đúng 1 dòng; nếu
    không (lần chạy đã hết hạn -> LOI, hoặc đã bị một lần kiểm tra lại thay
    thế) thì rollback — xóa/chèn chi tiết nằm CÙNG transaction ngắn đó, nên
    không bao giờ còn chi tiết trên bản ghi LOI hay chi tiết đan xen giữa hai
    lần chạy. Lời gọi AI nằm ngoài transaction ghi."""
    task_db = SessionLocal()
    stamp: datetime | None = None
    try:
        ket_qua = task_db.get(KetQuaKiemTraTrungLap, ket_qua_id)
        if ket_qua is None or ket_qua.tai_lieu_do_an_id is None:
            return
        if ket_qua.trang_thai != DANG_KIEM_TRA:
            return
        stamp = ket_qua.thoi_diem
        doc = task_db.get(TaiLieuDoAn, ket_qua.tai_lieu_do_an_id)
        if doc is None or doc.trich_xuat_loi or not doc.noi_dung_trich_xuat:
            _mark_loi(task_db, ket_qua_id, stamp)
            return
        doc_id, text = doc.id, doc.noi_dung_trich_xuat
        # Kết thúc transaction đọc trước lời gọi AI (có thể tới hàng chục giây).
        task_db.commit()

        raw = get_ai_client(task_db).check_document(doc_id, text)

        # Xóa chi tiết cũ rồi chèn lại trong CÙNG transaction với UPDATE có
        # điều kiện bên dưới (WR-05).
        task_db.execute(
            ChiTietTrungLap.__table__.delete().where(
                ChiTietTrungLap.ket_qua_id == ket_qua_id
            )
        )
        for item in raw.get("chi_tiet", []):
            # /check-document so khớp trong không gian DOCUMENT (§3.3.5); một
            # item mang "loai" tường minh (ARCHIVE) được tôn trọng (WR-06).
            loai = item.get("loai") or NGUON_DOCUMENT
            if loai not in (NGUON_DOCUMENT, NGUON_ARCHIVE):
                loai = NGUON_DOCUMENT
            ref_id = int(item["ref_id"])
            task_db.add(
                ChiTietTrungLap(
                    ket_qua_id=ket_qua_id,
                    doi_tuong_trung=_label_for(task_db, loai, ref_id),
                    ty_le=item["ty_le"],
                    doan_nguon=item.get("doan_nguon"),
                    doan_trung=item.get("doan_trung"),
                    vi_tri=item.get("vi_tri"),
                    loai_nguon=loai,
                    nguon_id=ref_id,
                )
            )

        stmt = (
            update(KetQuaKiemTraTrungLap)
            .where(KetQuaKiemTraTrungLap.id == ket_qua_id)
            .where(KetQuaKiemTraTrungLap.trang_thai == DANG_KIEM_TRA)
            .where(KetQuaKiemTraTrungLap.thoi_diem == stamp)
            .values(trang_thai=HOAN_TAT, ty_le_tong=raw.get("ty_le_tong", 0.0))
        )
        if task_db.execute(stmt).rowcount != 1:
            # Lần chạy đã hết hạn (LOI) hoặc bị kiểm tra lại thay thế — bỏ kết quả.
            task_db.rollback()
            _logger.warning(
                "document_check.run bỏ kết quả cũ cho ket_qua_id=%s (đã hết hạn/bị thay thế)",
                ket_qua_id,
            )
            return
        task_db.commit()
    except Exception:
        task_db.rollback()
        try:
            _mark_loi(task_db, ket_qua_id, stamp)
        except Exception:
            task_db.rollback()
        _logger.exception("document_check.run thất bại cho ket_qua_id=%s", ket_qua_id)
    finally:
        task_db.close()


def expire_if_stale(db: Session, ket_qua: KetQuaKiemTraTrungLap) -> None:
    """Bất biến bắt buộc (trang-thai-kiem-tra-trung-lap.puml): một bản ghi
    không bao giờ ở mãi DANG_KIEM_TRA — kể cả khi tiến trình api bị khởi động
    lại giữa lúc chạy nền. Gọi trước mọi lần đọc kết quả kiểm tra."""
    if ket_qua.trang_thai != DANG_KIEM_TRA:
        return
    settings = get_settings()
    if now_utc() - ket_qua.thoi_diem < timedelta(
        seconds=settings.DOCUMENT_CHECK_TIMEOUT_SECONDS
    ):
        return
    stmt = (
        update(KetQuaKiemTraTrungLap)
        .where(KetQuaKiemTraTrungLap.id == ket_qua.id)
        .where(KetQuaKiemTraTrungLap.trang_thai == DANG_KIEM_TRA)
        .values(trang_thai=LOI)
    )
    db.execute(stmt)
    db.commit()
    db.refresh(ket_qua)


def get_check_for_doc(db: Session, doc: TaiLieuDoAn) -> KetQuaKiemTraTrungLap | None:
    return db.execute(
        select(KetQuaKiemTraTrungLap)
        .where(KetQuaKiemTraTrungLap.tai_lieu_do_an_id == doc.id)
        .options(selectinload(KetQuaKiemTraTrungLap.chi_tiet))
    ).scalar_one_or_none()


def summary(ket_qua: KetQuaKiemTraTrungLap) -> CheckSummary:
    return CheckSummary(
        id=ket_qua.id,
        trang_thai=ket_qua.trang_thai,
        ty_le_tong=float(ket_qua.ty_le_tong) if ket_qua.ty_le_tong is not None else None,
        nguong_ap_dung=float(ket_qua.nguong_ap_dung),
        thoi_diem=ket_qua.thoi_diem,
    )


def _published_sources(db: Session, rows: list[ChiTietTrungLap]) -> set[tuple[str, int]]:
    """WR-07: nguồn nào là đồ án ĐÃ CÔNG BỐ trong kho — một bản ghi ARCHIVE,
    hoặc một tài liệu (DOCUMENT) của đề tài đã có dòng do_an_kho (đồ án khóa
    trước được nạp vào hệ thống, hoặc đồ án đã chốt bảo vệ)."""
    visible = {
        (NGUON_ARCHIVE, row.nguon_id)
        for row in rows
        if row.loai_nguon == NGUON_ARCHIVE and row.nguon_id is not None
    }
    doc_ids = {
        row.nguon_id
        for row in rows
        if row.loai_nguon == NGUON_DOCUMENT and row.nguon_id is not None
    }
    if doc_ids:
        archived = db.execute(
            select(TaiLieuDoAn.id)
            .join(DoAnKho, DoAnKho.de_tai_id == TaiLieuDoAn.de_tai_id)
            .where(TaiLieuDoAn.id.in_(doc_ids))
        ).scalars()
        visible |= {(NGUON_DOCUMENT, doc_id) for doc_id in archived}
    return visible


def detail(db: Session, doc: TaiLieuDoAn, user: CurrentUser) -> CheckDetail:
    """Router đã gọi expire_if_stale + kiểm tra tồn tại (404) trước khi gọi
    hàm này — vẫn phòng thủ khi ket_qua vắng mặt để hàm luôn trả được kết quả.

    WR-07: với SINH_VIEN, `doan_trung` (văn bản của tài liệu nguồn) chỉ được
    trả khi nguồn là đồ án đã vào kho; nguồn là đề cương/báo cáo chưa công bố
    của sinh viên khác chỉ lộ tên đề tài, khóa và tỷ lệ. GV/Bộ môn thấy đủ."""
    ket_qua = get_check_for_doc(db, doc)
    topic = db.get(DeTai, doc.de_tai_id)
    ten_de_tai = topic.ten_de_tai if topic is not None else ""
    sinh_vien = None
    if topic is not None and topic.sinh_vien is not None:
        sinh_vien = PersonRef(
            id=topic.sinh_vien.id,
            ho_ten=topic.sinh_vien.ho_ten or "",
            ma=topic.sinh_vien.ma_so_sinh_vien,
        )

    chi_tiet_rows = list(ket_qua.chi_tiet) if ket_qua is not None else []
    redact = user.vai_tro == VaiTro.SINH_VIEN
    published = _published_sources(db, chi_tiet_rows) if redact else set()

    def _hidden(row: ChiTietTrungLap) -> bool:
        if not redact or row.doan_trung is None:
            return False
        return (row.loai_nguon, row.nguon_id) not in published

    chi_tiet = [
        CheckSegment(
            doi_tuong_trung=row.doi_tuong_trung,
            doan_nguon=row.doan_nguon,
            doan_trung=None if hidden else row.doan_trung,
            vi_tri=row.vi_tri,
            ty_le=float(row.ty_le),
            doan_trung_an=hidden,
        )
        for row in chi_tiet_rows
        for hidden in [_hidden(row)]
    ]

    grouped: dict[str, float] = {}
    for row in chi_tiet_rows:
        ty_le = float(row.ty_le)
        if row.doi_tuong_trung not in grouped or ty_le > grouped[row.doi_tuong_trung]:
            grouped[row.doi_tuong_trung] = ty_le
    do_an_trung = sorted(
        (CheckMatch(doi_tuong_trung=k, ty_le=v) for k, v in grouped.items()),
        key=lambda m: -m.ty_le,
    )

    return CheckDetail(
        id=ket_qua.id if ket_qua is not None else 0,
        trang_thai=ket_qua.trang_thai if ket_qua is not None else DANG_KIEM_TRA,
        ty_le_tong=(
            float(ket_qua.ty_le_tong)
            if ket_qua is not None and ket_qua.ty_le_tong is not None
            else None
        ),
        nguong_ap_dung=float(ket_qua.nguong_ap_dung) if ket_qua is not None else 0.0,
        thoi_diem=ket_qua.thoi_diem if ket_qua is not None else now_utc(),
        tai_lieu=to_document_out(doc),
        de_tai_id=doc.de_tai_id,
        ten_de_tai=ten_de_tai,
        sinh_vien=sinh_vien,
        do_an_trung=do_an_trung,
        chi_tiet=chi_tiet,
    )


def request_recheck(db: Session, ket_qua: KetQuaKiemTraTrungLap) -> None:
    """Task 2 (POST /recheck): chỉ cho phép khi đang LOI — conditional UPDATE
    (rowcount 0 -> 409); xóa chi tiết cũ, commit, router mới schedule `run`."""
    stmt = (
        update(KetQuaKiemTraTrungLap)
        .where(KetQuaKiemTraTrungLap.id == ket_qua.id)
        .where(KetQuaKiemTraTrungLap.trang_thai == LOI)
        .values(trang_thai=DANG_KIEM_TRA, thoi_diem=now_utc())
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_RECHECK_NOT_LOI_DETAIL)
    db.execute(
        ChiTietTrungLap.__table__.delete().where(ChiTietTrungLap.ket_qua_id == ket_qua.id)
    )
    db.commit()
    db.refresh(ket_qua)
