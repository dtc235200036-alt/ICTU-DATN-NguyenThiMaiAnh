"""UC2 — Quản lý đề cương: SV nộp (CHUA_NOP->CHO_DUYET), GVHD duyệt
(GVHD_DA_DUYET) hoặc yêu cầu sửa (YEU_CAU_SUA), GVHD nộp lên Bộ môn
(CHO_BO_MON_DUYET), Lãnh đạo bộ môn phê duyệt kèm file đã ký số (DA_DUYET —
trạng thái cuối) hoặc trả lại (YEU_CAU_SUA); xem chi tiết/lịch sử."""
import io
import zipfile

from fastapi import HTTPException
from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.core.timeutil import now_utc
from app.models.de_cuong import (
    DC_CHO_BO_MON_DUYET,
    DC_CHO_DUYET,
    DC_CHUA_NOP,
    DC_DA_DUYET,
    DC_GVHD_DA_DUYET,
    DC_YEU_CAU_SUA,
    KET_QUA_DA_DUYET,
    KET_QUA_TRA_LAI,
    KET_QUA_YEU_CAU_SUA,
    LOAI_DE_CUONG,
    LOAI_DE_CUONG_KY_SO,
    PDF,
    DeCuong,
    LuotDuyetBoMon,
    LuotDuyetDeCuong,
    TaiLieuDoAn,
)
from app.models.de_tai import DA_PHAN_CONG, DeTai
from app.models.dot_do_an import DotDoAn
from app.models.tai_khoan import SinhVien, TaiKhoan
from app.models.thong_bao import (
    DE_CUONG_BO_MON_DUYET,
    DE_CUONG_BO_MON_TRA_LAI,
    DE_CUONG_DUYET,
    DE_CUONG_MOI,
    DE_CUONG_NOP_BO_MON,
    DE_CUONG_YEU_CAU_SUA,
)
from app.models.trung_lap import KetQuaKiemTraTrungLap
from app.schemas.common import Page, nfc
from app.schemas.outlines import (
    BoMonReviewOut,
    CheckItem,
    OutlineCounts,
    OutlineDetail,
    OutlineListItem,
    OutlineVersion,
    QuyenDeCuongOut,
    ReviewOut,
    ReviewRequest,
)
from app.schemas.topics import DinhHuongRef, PersonRef
from app.services import document_check, documents, notifications, outline_checks
from app.services.documents import ValidatedFile, to_document_out

_TOPIC_NOT_FOUND_DETAIL = "Không tìm thấy đề tài"
_OUTLINE_NOT_FOUND_DETAIL = "Không tìm thấy đề cương"
_SUBMIT_FORBIDDEN_DETAIL = "Bạn không có quyền nộp đề cương cho đề tài này"
_NOT_ASSIGNED_DETAIL = "Đề tài chưa được phân công GVHD — chưa thể nộp đề cương"
_ALREADY_PENDING_DETAIL = (
    "Đề cương đang chờ duyệt hoặc đã được duyệt — chưa thể nộp phiên bản mới"
)
_SUBMIT_RACE_DETAIL = "Đang có một lần nộp khác, vui lòng thử lại"
_VIEW_FORBIDDEN_DETAIL = "Bạn không có quyền xem đề cương này"
_REVIEW_FORBIDDEN_DETAIL = "Chỉ GVHD của đề tài mới được duyệt đề cương"
_STALE_VERSION_DETAIL = "Sinh viên vừa nộp phiên bản mới, vui lòng tải lại"
_NOT_PENDING_DETAIL = "Đề cương không còn ở trạng thái Chờ duyệt"
_NHAN_XET_REQUIRED_DETAIL = "Vui lòng nhập nhận xét khi yêu cầu sửa"
_FORWARD_FORBIDDEN_DETAIL = "Chỉ GVHD của đề tài mới được nộp đề cương lên Bộ môn"
_NOT_GVHD_APPROVED_DETAIL = "Đề cương chưa được GVHD duyệt hoặc đã nộp lên Bộ môn"
_NOT_AT_BO_MON_DETAIL = "Đề cương không ở trạng thái Chờ Bộ môn duyệt"
_SIGNED_NOT_PDF_DETAIL = "File phê duyệt phải là PDF đã ký số"
_NO_SIGNATURE_DETAIL = "File PDF chưa có chữ ký số — hãy ký số rồi tải lên lại"
_SIGNATURE_PARTIAL_DETAIL = (
    "Chữ ký số không phủ toàn bộ file (file đã bị sửa sau khi ký) — hãy ký lại"
)
_GHI_CHU_MAX = 2000
# Lọc tab "Từ chối" của Bộ môn: đề cương Bộ môn đã trả lại, đang chờ SV sửa.
BO_MON_TRA_LAI_FILTER = "BO_MON_TRA_LAI"


def _person_ref(entity, ma_attr: str) -> PersonRef | None:
    if entity is None:
        return None
    return PersonRef(id=entity.id, ho_ten=entity.ho_ten or "", ma=getattr(entity, ma_attr, None))


def _get_topic_locked_or_404(db: Session, de_tai_id: int) -> DeTai:
    topic = db.execute(
        select(DeTai).where(DeTai.id == de_tai_id).with_for_update()
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return topic


def _get_topic_or_404(db: Session, de_tai_id: int) -> DeTai:
    topic = db.execute(
        select(DeTai)
        .where(DeTai.id == de_tai_id)
        .options(
            selectinload(DeTai.sinh_vien),
            selectinload(DeTai.giang_vien),
            selectinload(DeTai.dinh_huong),
        )
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return topic


def _dinh_huong_ref(topic: DeTai) -> DinhHuongRef | None:
    if topic.dinh_huong is None:
        return None
    return DinhHuongRef(id=topic.dinh_huong.id, ma=topic.dinh_huong.ma, ten=topic.dinh_huong.ten)


def _notify_bo_mon(db: Session, loai: str, noi_dung: str, lien_ket: str) -> None:
    ids = db.execute(
        select(TaiKhoan.id)
        .where(TaiKhoan.vai_tro == VaiTro.BO_MON)
        .where(TaiKhoan.bi_khoa.is_(False))
    ).scalars().all()
    for tai_khoan_id in ids:
        notifications.create(db, tai_khoan_id, loai, noi_dung, lien_ket=lien_ket)


def _can_view_topic(user: CurrentUser, topic: DeTai) -> bool:
    """Cùng quy tắc xem như documents.can_view, nhưng ở mức đề tài (T-03-04)."""
    if user.vai_tro == VaiTro.BO_MON:
        return True
    if user.vai_tro == VaiTro.SINH_VIEN and user.sinh_vien_id is not None:
        return topic.sinh_vien_id == user.sinh_vien_id
    if user.vai_tro == VaiTro.GIANG_VIEN and user.giang_vien_id is not None:
        return topic.giang_vien_id == user.giang_vien_id
    return False


def submit(
    db: Session,
    user: CurrentUser,
    de_tai_id: int,
    vf: ValidatedFile,
    ghi_chu: str | None = None,
) -> tuple[OutlineDetail, int]:
    """UC2.1: khóa dòng de_tai (serialize lần nộp đầu tiên đồng thời), rồi
    conditional UPDATE de_cuong.trang_thai — chỉ CHUA_NOP/YEU_CAU_SUA mới nộp
    được (D-04, một commit cho toàn bộ: file + kiểm tra trùng + thông báo)."""
    topic = _get_topic_locked_or_404(db, de_tai_id)
    if user.sinh_vien_id is None or topic.sinh_vien_id != user.sinh_vien_id:
        raise HTTPException(status_code=403, detail=_SUBMIT_FORBIDDEN_DETAIL)
    if topic.trang_thai != DA_PHAN_CONG:
        raise HTTPException(status_code=409, detail=_NOT_ASSIGNED_DETAIL)

    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    if de_cuong is None:
        de_cuong = DeCuong(de_tai_id=de_tai_id, trang_thai=DC_CHUA_NOP)
        db.add(de_cuong)
        db.flush()

    now = now_utc()
    stmt = (
        update(DeCuong)
        .where(DeCuong.id == de_cuong.id)
        .where(DeCuong.trang_thai.in_([DC_CHUA_NOP, DC_YEU_CAU_SUA]))
        .values(
            trang_thai=DC_CHO_DUYET,
            ngay_nop_dau_tien=func.coalesce(DeCuong.ngay_nop_dau_tien, now),
            nop_bo_mon_luc=None,
            ket_qua_bo_mon=None,
        )
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_ALREADY_PENDING_DETAIL)

    doc = None
    ket_qua = None
    try:
        doc = documents.store(
            db, de_tai_id=de_tai_id, loai=LOAI_DE_CUONG, vf=vf, de_cuong_id=de_cuong.id
        )
        ghi_chu = nfc(ghi_chu or "").strip()
        doc.ghi_chu = ghi_chu[:_GHI_CHU_MAX] or None
        ket_qua = document_check.create_pending(db, doc)

        if topic.giang_vien is not None:
            ho_ten = (topic.sinh_vien.ho_ten if topic.sinh_vien is not None else None) or ""
            notifications.create(
                db,
                topic.giang_vien.tai_khoan_id,
                DE_CUONG_MOI,
                f"Sinh viên {ho_ten} đã nộp đề cương phiên bản {doc.so_phien_ban}: "
                f"{topic.ten_de_tai}",
                lien_ket=f"/duyet-de-cuong?de_tai_id={de_tai_id}",
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        if doc is not None:
            documents.remove_file_quietly(doc.ten_luu_tru)
        raise HTTPException(status_code=409, detail=_SUBMIT_RACE_DETAIL) from None
    except Exception:
        db.rollback()
        if doc is not None:
            documents.remove_file_quietly(doc.ten_luu_tru)
        raise

    return get_detail(db, user, de_tai_id), ket_qua.id


def get_detail(db: Session, user: CurrentUser, de_tai_id: int) -> OutlineDetail:
    topic = _get_topic_or_404(db, de_tai_id)
    if not _can_view_topic(user, topic):
        raise HTTPException(status_code=403, detail=_VIEW_FORBIDDEN_DETAIL)

    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()

    trang_thai = de_cuong.trang_thai if de_cuong is not None else DC_CHUA_NOP
    ngay_nop_dau_tien = de_cuong.ngay_nop_dau_tien if de_cuong is not None else None
    phien_ban: list[OutlineVersion] = []
    docs: list[TaiLieuDoAn] = []

    if de_cuong is not None:
        docs = (
            db.execute(
                select(TaiLieuDoAn)
                .where(TaiLieuDoAn.de_cuong_id == de_cuong.id)
                .where(TaiLieuDoAn.loai == LOAI_DE_CUONG)
                .order_by(TaiLieuDoAn.so_phien_ban.desc())
                .options(
                    selectinload(TaiLieuDoAn.ket_qua_kiem_tra).selectinload(
                        KetQuaKiemTraTrungLap.chi_tiet
                    ),
                    selectinload(TaiLieuDoAn.luot_duyet).selectinload(
                        LuotDuyetDeCuong.giang_vien
                    ),
                )
            )
            .scalars()
            .all()
        )
        for doc in docs:
            ket_qua = doc.ket_qua_kiem_tra
            if ket_qua is not None:
                document_check.expire_if_stale(db, ket_qua)
            kiem_tra = document_check.summary(ket_qua) if ket_qua is not None else None
            luot_duyet_out = None
            if doc.luot_duyet is not None:
                luot_duyet_out = ReviewOut(
                    ket_qua=doc.luot_duyet.ket_qua,
                    nhan_xet=doc.luot_duyet.nhan_xet,
                    thoi_diem=doc.luot_duyet.thoi_diem,
                    giang_vien=_person_ref(doc.luot_duyet.giang_vien, "ma_giang_vien"),
                )
            phien_ban.append(
                OutlineVersion(
                    tai_lieu=to_document_out(doc), kiem_tra=kiem_tra, luot_duyet=luot_duyet_out
                )
            )

    la_gvhd = user.giang_vien_id is not None and topic.giang_vien_id == user.giang_vien_id
    quyen = QuyenDeCuongOut(
        nop=(
            user.sinh_vien_id is not None
            and topic.sinh_vien_id == user.sinh_vien_id
            and topic.trang_thai == DA_PHAN_CONG
            and trang_thai in (DC_CHUA_NOP, DC_YEU_CAU_SUA)
        ),
        duyet=la_gvhd and trang_thai == DC_CHO_DUYET,
        nop_bo_mon=la_gvhd and trang_thai == DC_GVHD_DA_DUYET,
        duyet_bo_mon=user.vai_tro == VaiTro.BO_MON and trang_thai == DC_CHO_BO_MON_DUYET,
    )

    latest_doc = docs[0] if docs else None
    return OutlineDetail(
        de_tai_id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        sinh_vien=_person_ref(topic.sinh_vien, "ma_so_sinh_vien"),
        giang_vien=_person_ref(topic.giang_vien, "ma_giang_vien"),
        trang_thai=trang_thai,
        ngay_nop_dau_tien=ngay_nop_dau_tien,
        phien_ban=phien_ban,
        quyen=quyen,
        dinh_huong=_dinh_huong_ref(topic),
        lop=topic.sinh_vien.lop if topic.sinh_vien is not None else None,
        nop_bo_mon_luc=de_cuong.nop_bo_mon_luc if de_cuong is not None else None,
        ket_qua_bo_mon=de_cuong.ket_qua_bo_mon if de_cuong is not None else None,
        luot_duyet_bo_mon=_bo_mon_reviews(db, de_cuong.id) if de_cuong is not None else [],
        kiem_tra_nop=kiem_tra_nop(topic, latest_doc) if latest_doc is not None else [],
        ten_file_mau=outline_checks.ten_file_mau(
            topic.sinh_vien, topic.dinh_huong.ma if topic.dinh_huong is not None else None
        ),
    )


def kiem_tra_nop(topic: DeTai, doc: TaiLieuDoAn) -> list[CheckItem]:
    return [
        outline_checks.kiem_tra_ten_file(doc, topic),
        outline_checks.kiem_tra_dinh_huong(doc, topic),
        outline_checks.kiem_tra_noi_dung(doc),
    ]


def _bo_mon_reviews(db: Session, de_cuong_id: int) -> list[BoMonReviewOut]:
    rows = (
        db.execute(
            select(LuotDuyetBoMon)
            .where(LuotDuyetBoMon.de_cuong_id == de_cuong_id)
            .order_by(LuotDuyetBoMon.thoi_diem.desc(), LuotDuyetBoMon.id.desc())
            .options(
                selectinload(LuotDuyetBoMon.tai_lieu_ky_so),
                selectinload(LuotDuyetBoMon.tai_khoan),
            )
        )
        .scalars()
        .all()
    )
    return [
        BoMonReviewOut(
            ket_qua=r.ket_qua,
            nhan_xet=r.nhan_xet,
            thoi_diem=r.thoi_diem,
            nguoi_duyet=r.tai_khoan.ma_dang_nhap if r.tai_khoan is not None else "",
            tai_lieu_id=r.tai_lieu_do_an_id,
            tai_lieu_ky_so=to_document_out(r.tai_lieu_ky_so) if r.tai_lieu_ky_so else None,
            nguoi_ky=r.nguoi_ky,
            thoi_diem_ky=r.thoi_diem_ky,
        )
        for r in rows
    ]


def _scoped_outline_stmt(user: CurrentUser, dot_do_an_id: int | None, q: str | None):
    """Đề tài Đã phân công (+ đề cương nếu có) trong phạm vi vai trò gọi:
    SV/GV chỉ thấy đề tài của mình, Bộ môn thấy tất cả (T-03-04)."""
    stmt = (
        select(DeTai, DeCuong)
        .outerjoin(DeCuong, DeCuong.de_tai_id == DeTai.id)
        .where(DeTai.trang_thai == DA_PHAN_CONG)
    )
    # IN-03: tài khoản thiếu hồ sơ -> -1 (không khớp gì), không bao giờ `IS NULL`.
    if user.vai_tro == VaiTro.SINH_VIEN:
        stmt = stmt.where(DeTai.sinh_vien_id == (user.sinh_vien_id or -1))
    elif user.vai_tro == VaiTro.GIANG_VIEN:
        stmt = stmt.where(DeTai.giang_vien_id == (user.giang_vien_id or -1))
    if dot_do_an_id is not None:
        stmt = stmt.where(DeTai.dot_do_an_id == dot_do_an_id)
    if q:
        tu_khoa = nfc(q).strip()
        sv_khop = exists().where(
            (SinhVien.id == DeTai.sinh_vien_id)
            & or_(
                SinhVien.ho_ten.contains(tu_khoa, autoescape=True),
                SinhVien.ma_so_sinh_vien.contains(tu_khoa, autoescape=True),
            )
        )
        stmt = stmt.where(or_(DeTai.ten_de_tai.contains(tu_khoa, autoescape=True), sv_khop))
    return stmt


def list_outlines(
    db: Session,
    user: CurrentUser,
    trang_thai: str | None,
    dot_do_an_id: int | None,
    page: int,
    page_size: int,
    q: str | None = None,
) -> Page[OutlineListItem]:
    """UC2.3/MH-08/MH-09: chỉ đề tài Đã phân công; SV/GV chỉ thấy đề tài của
    mình, Bộ môn thấy tất cả (T-03-04); một truy vấn cho cả trang phiên bản
    mới nhất + kết quả kiểm tra (không N+1)."""
    stmt = _scoped_outline_stmt(user, dot_do_an_id, q)
    if trang_thai == BO_MON_TRA_LAI_FILTER:
        stmt = stmt.where(DeCuong.ket_qua_bo_mon == KET_QUA_TRA_LAI).where(
            DeCuong.trang_thai == DC_YEU_CAU_SUA
        )
    elif trang_thai is not None:
        stmt = stmt.where(func.coalesce(DeCuong.trang_thai, DC_CHUA_NOP) == trang_thai)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    paged = (
        stmt.order_by(DeTai.id.desc())
        .options(
            selectinload(DeTai.sinh_vien),
            selectinload(DeTai.giang_vien),
            selectinload(DeTai.dinh_huong),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(paged).all()

    de_cuong_ids = [dc.id for _topic, dc in rows if dc is not None]
    latest_by_de_cuong: dict[int, TaiLieuDoAn] = {}
    if de_cuong_ids:
        latest_sub = (
            select(
                TaiLieuDoAn.de_cuong_id,
                func.max(TaiLieuDoAn.so_phien_ban).label("max_ver"),
            )
            .where(TaiLieuDoAn.de_cuong_id.in_(de_cuong_ids))
            .where(TaiLieuDoAn.loai == LOAI_DE_CUONG)
            .group_by(TaiLieuDoAn.de_cuong_id)
            .subquery()
        )
        latest_docs = (
            db.execute(
                select(TaiLieuDoAn)
                .join(
                    latest_sub,
                    (TaiLieuDoAn.de_cuong_id == latest_sub.c.de_cuong_id)
                    & (TaiLieuDoAn.so_phien_ban == latest_sub.c.max_ver),
                )
                .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
            )
            .scalars()
            .all()
        )
        latest_by_de_cuong = {doc.de_cuong_id: doc for doc in latest_docs}

    items: list[OutlineListItem] = []
    for topic, de_cuong in rows:
        latest_doc = latest_by_de_cuong.get(de_cuong.id) if de_cuong is not None else None
        kiem_tra = None
        if latest_doc is not None and latest_doc.ket_qua_kiem_tra is not None:
            document_check.expire_if_stale(db, latest_doc.ket_qua_kiem_tra)
            kiem_tra = document_check.summary(latest_doc.ket_qua_kiem_tra)
        items.append(
            OutlineListItem(
                de_tai_id=topic.id,
                ten_de_tai=topic.ten_de_tai,
                sinh_vien=_person_ref(topic.sinh_vien, "ma_so_sinh_vien"),
                giang_vien=_person_ref(topic.giang_vien, "ma_giang_vien"),
                trang_thai=de_cuong.trang_thai if de_cuong is not None else DC_CHUA_NOP,
                phien_ban_moi_nhat=to_document_out(latest_doc) if latest_doc is not None else None,
                kiem_tra=kiem_tra,
                dinh_huong=_dinh_huong_ref(topic),
                nop_bo_mon_luc=de_cuong.nop_bo_mon_luc if de_cuong is not None else None,
                ket_qua_bo_mon=de_cuong.ket_qua_bo_mon if de_cuong is not None else None,
            )
        )

    return Page[OutlineListItem](items=items, total=total, page=page, page_size=page_size)


def count_outlines(
    db: Session, user: CurrentUser, dot_do_an_id: int | None, q: str | None = None
) -> OutlineCounts:
    """Số đề cương theo trạng thái cho các tab (cùng phạm vi với list_outlines)."""
    sub = (
        _scoped_outline_stmt(user, dot_do_an_id, q)
        .with_only_columns(
            func.coalesce(DeCuong.trang_thai, DC_CHUA_NOP).label("tt"),
            DeCuong.ket_qua_bo_mon.label("kq"),
        )
        .subquery()
    )
    rows = db.execute(select(sub.c.tt, func.count()).group_by(sub.c.tt)).all()
    theo_trang_thai = {str(tt): int(n) for tt, n in rows}
    tra_lai = db.execute(
        select(func.count())
        .select_from(sub)
        .where(sub.c.kq == KET_QUA_TRA_LAI)
        .where(sub.c.tt == DC_YEU_CAU_SUA)
    ).scalar_one()
    return OutlineCounts(
        tat_ca=sum(theo_trang_thai.values()),
        theo_trang_thai=theo_trang_thai,
        bo_mon_tra_lai=int(tra_lai),
    )


def _latest_version_or_none(db: Session, de_cuong_id: int) -> TaiLieuDoAn | None:
    return (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_cuong_id == de_cuong_id)
            .where(TaiLieuDoAn.loai == LOAI_DE_CUONG)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def review(
    db: Session, user: CurrentUser, de_tai_id: int, payload: ReviewRequest
) -> OutlineDetail:
    """UC2.2: GVHD duyệt hoặc yêu cầu sửa phiên bản MỚI NHẤT — Task 1 hiện
    thực nhánh DA_DUYET; nhánh YEU_CAU_SUA thuộc Task 2 (UC2.2 A1)."""
    topic = _get_topic_or_404(db, de_tai_id)
    if user.giang_vien_id is None or topic.giang_vien_id != user.giang_vien_id:
        raise HTTPException(status_code=403, detail=_REVIEW_FORBIDDEN_DETAIL)

    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    if de_cuong is None:
        raise HTTPException(status_code=404, detail=_OUTLINE_NOT_FOUND_DETAIL)

    latest_version = _latest_version_or_none(db, de_cuong.id)
    if latest_version is None or latest_version.id != payload.tai_lieu_do_an_id:
        raise HTTPException(status_code=409, detail=_STALE_VERSION_DETAIL)

    if payload.ket_qua == KET_QUA_YEU_CAU_SUA:
        return _review_yeu_cau_sua(db, user, topic, de_cuong, latest_version, payload)

    return _review_da_duyet(db, user, topic, de_cuong, latest_version, payload)


def _review_da_duyet(
    db: Session,
    user: CurrentUser,
    topic: DeTai,
    de_cuong: DeCuong,
    latest_version: TaiLieuDoAn,
    payload: ReviewRequest,
) -> OutlineDetail:
    stmt = (
        update(DeCuong)
        .where(DeCuong.id == de_cuong.id)
        .where(DeCuong.trang_thai == DC_CHO_DUYET)
        .values(trang_thai=DC_GVHD_DA_DUYET)
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL)

    try:
        db.add(
            LuotDuyetDeCuong(
                de_cuong_id=de_cuong.id,
                tai_lieu_do_an_id=latest_version.id,
                giang_vien_id=user.giang_vien_id,
                ket_qua=KET_QUA_DA_DUYET,
                nhan_xet=payload.nhan_xet,
                thoi_diem=now_utc(),
            )
        )
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL) from None

    if topic.sinh_vien is not None:
        notifications.create(
            db,
            topic.sinh_vien.tai_khoan_id,
            DE_CUONG_DUYET,
            f"GVHD đã duyệt đề cương của bạn, chờ nộp lên Bộ môn: {topic.ten_de_tai}",
            lien_ket="/de-cuong",
        )
    db.commit()

    return get_detail(db, user, topic.id)


def _review_yeu_cau_sua(
    db: Session,
    user: CurrentUser,
    topic: DeTai,
    de_cuong: DeCuong,
    latest_version: TaiLieuDoAn,
    payload: ReviewRequest,
) -> OutlineDetail:
    nhan_xet = (payload.nhan_xet or "").strip()
    if not nhan_xet:
        raise HTTPException(status_code=422, detail=_NHAN_XET_REQUIRED_DETAIL)

    stmt = (
        update(DeCuong)
        .where(DeCuong.id == de_cuong.id)
        .where(DeCuong.trang_thai == DC_CHO_DUYET)
        .values(trang_thai=DC_YEU_CAU_SUA)
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL)

    try:
        db.add(
            LuotDuyetDeCuong(
                de_cuong_id=de_cuong.id,
                tai_lieu_do_an_id=latest_version.id,
                giang_vien_id=user.giang_vien_id,
                ket_qua=KET_QUA_YEU_CAU_SUA,
                nhan_xet=nhan_xet,
                thoi_diem=now_utc(),
            )
        )
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL) from None

    if topic.sinh_vien is not None:
        notifications.create(
            db,
            topic.sinh_vien.tai_khoan_id,
            DE_CUONG_YEU_CAU_SUA,
            f"GVHD yêu cầu sửa đề cương: {nhan_xet[:150]}",
            lien_ket="/de-cuong",
        )
    db.commit()

    return get_detail(db, user, topic.id)


def forward_to_bo_mon(db: Session, user: CurrentUser, de_tai_id: int) -> OutlineDetail:
    """GVHD nộp đề cương đã duyệt lên Bộ môn. Chặn khi tên file sai quy tắc hoặc
    định hướng không khớp; kết quả trùng lặp chỉ để Bộ môn tham khảo."""
    topic = _get_topic_or_404(db, de_tai_id)
    if user.giang_vien_id is None or topic.giang_vien_id != user.giang_vien_id:
        raise HTTPException(status_code=403, detail=_FORWARD_FORBIDDEN_DETAIL)
    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    if de_cuong is None or de_cuong.trang_thai != DC_GVHD_DA_DUYET:
        raise HTTPException(status_code=409, detail=_NOT_GVHD_APPROVED_DETAIL)

    latest_version = db.execute(
        select(TaiLieuDoAn)
        .where(TaiLieuDoAn.de_cuong_id == de_cuong.id)
        .where(TaiLieuDoAn.loai == LOAI_DE_CUONG)
        .order_by(TaiLieuDoAn.so_phien_ban.desc())
        .limit(1)
        .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
    ).scalars().first()
    checks = kiem_tra_nop(topic, latest_version) if latest_version is not None else []
    loi = [c for c in checks if c.ma in ("TEN_FILE", "DINH_HUONG") and not c.dat]
    if latest_version is None or loi:
        chi_tiet = "; ".join(f"{c.ten}: {c.chi_tiet}" for c in loi) or "Chưa có file"
        raise HTTPException(
            status_code=409,
            detail=f"Chưa thể nộp lên Bộ môn — {chi_tiet}. Hãy yêu cầu sinh viên nộp lại.",
        )

    result = db.execute(
        update(DeCuong)
        .where(DeCuong.id == de_cuong.id)
        .where(DeCuong.trang_thai == DC_GVHD_DA_DUYET)
        .values(trang_thai=DC_CHO_BO_MON_DUYET, nop_bo_mon_luc=now_utc(), ket_qua_bo_mon=None)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_GVHD_APPROVED_DETAIL)

    ho_ten_sv = topic.sinh_vien.ho_ten if topic.sinh_vien is not None else ""
    ho_ten_gv = topic.giang_vien.ho_ten if topic.giang_vien is not None else ""
    _notify_bo_mon(
        db,
        DE_CUONG_NOP_BO_MON,
        f"GVHD {ho_ten_gv} đã nộp đề cương của {ho_ten_sv} lên Bộ môn: {topic.ten_de_tai}",
        lien_ket=f"/duyet-de-cuong?de_tai_id={de_tai_id}",
    )
    if topic.sinh_vien is not None:
        notifications.create(
            db,
            topic.sinh_vien.tai_khoan_id,
            DE_CUONG_NOP_BO_MON,
            f"GVHD đã nộp đề cương của bạn lên Bộ môn: {topic.ten_de_tai}",
            lien_ket="/de-cuong",
        )
    db.commit()
    return get_detail(db, user, de_tai_id)


def _de_cuong_at_bo_mon(db: Session, de_tai_id: int) -> DeCuong:
    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    if de_cuong is None or de_cuong.trang_thai != DC_CHO_BO_MON_DUYET:
        raise HTTPException(status_code=409, detail=_NOT_AT_BO_MON_DETAIL)
    return de_cuong


def bo_mon_approve(
    db: Session,
    user: CurrentUser,
    de_tai_id: int,
    vf: ValidatedFile,
    nhan_xet: str | None = None,
) -> OutlineDetail:
    """Lãnh đạo bộ môn phê duyệt: tải lên bản PDF đã ký số -> lưu vào thư mục đề
    cương của đợt (loai DE_CUONG_KY_SO) và chuyển đề cương sang DA_DUYET."""
    topic = _get_topic_or_404(db, de_tai_id)
    _de_cuong_at_bo_mon(db, de_tai_id)
    if vf.dinh_dang != PDF:
        raise HTTPException(status_code=422, detail=_SIGNED_NOT_PDF_DETAIL)
    chu_ky = outline_checks.doc_chu_ky_so(vf.content)
    if chu_ky is None:
        raise HTTPException(status_code=422, detail=_NO_SIGNATURE_DETAIL)
    if not chu_ky.phu_toan_bo_file:
        raise HTTPException(status_code=422, detail=_SIGNATURE_PARTIAL_DETAIL)

    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id).with_for_update()
    ).scalar_one()
    if de_cuong.trang_thai != DC_CHO_BO_MON_DUYET:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_AT_BO_MON_DETAIL)
    submitted = _latest_version_or_none(db, de_cuong.id)

    doc = None
    try:
        doc = documents.store(
            db, de_tai_id=de_tai_id, loai=LOAI_DE_CUONG_KY_SO, vf=vf, de_cuong_id=de_cuong.id
        )
        db.add(
            LuotDuyetBoMon(
                de_cuong_id=de_cuong.id,
                tai_lieu_do_an_id=submitted.id,
                tai_khoan_id=user.tai_khoan_id,
                ket_qua=KET_QUA_DA_DUYET,
                nhan_xet=(nhan_xet or "").strip() or None,
                thoi_diem=now_utc(),
                tai_lieu_ky_so_id=doc.id,
                nguoi_ky=(chu_ky.nguoi_ky or "")[:255] or None,
                thoi_diem_ky=chu_ky.thoi_diem_ky,
            )
        )
        de_cuong.trang_thai = DC_DA_DUYET
        de_cuong.ket_qua_bo_mon = KET_QUA_DA_DUYET

        noi_dung = f"Bộ môn đã phê duyệt đề cương (đã ký số): {topic.ten_de_tai}"
        if topic.sinh_vien is not None:
            notifications.create(
                db, topic.sinh_vien.tai_khoan_id, DE_CUONG_BO_MON_DUYET, noi_dung, lien_ket="/de-cuong"
            )
        if topic.giang_vien is not None:
            notifications.create(
                db,
                topic.giang_vien.tai_khoan_id,
                DE_CUONG_BO_MON_DUYET,
                noi_dung,
                lien_ket=f"/duyet-de-cuong?de_tai_id={de_tai_id}",
            )
        db.commit()
    except Exception:
        db.rollback()
        if doc is not None:
            documents.remove_file_quietly(doc.ten_luu_tru)
        raise
    return get_detail(db, user, de_tai_id)


def bo_mon_return(db: Session, user: CurrentUser, de_tai_id: int, nhan_xet: str) -> OutlineDetail:
    """Lãnh đạo bộ môn trả lại đề cương -> SV sửa và nộp lại (YEU_CAU_SUA)."""
    topic = _get_topic_or_404(db, de_tai_id)
    de_cuong = _de_cuong_at_bo_mon(db, de_tai_id)
    submitted = _latest_version_or_none(db, de_cuong.id)
    result = db.execute(
        update(DeCuong)
        .where(DeCuong.id == de_cuong.id)
        .where(DeCuong.trang_thai == DC_CHO_BO_MON_DUYET)
        .values(trang_thai=DC_YEU_CAU_SUA, ket_qua_bo_mon=KET_QUA_TRA_LAI)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_NOT_AT_BO_MON_DETAIL)
    db.add(
        LuotDuyetBoMon(
            de_cuong_id=de_cuong.id,
            tai_lieu_do_an_id=submitted.id,
            tai_khoan_id=user.tai_khoan_id,
            ket_qua=KET_QUA_TRA_LAI,
            nhan_xet=nhan_xet,
            thoi_diem=now_utc(),
        )
    )
    noi_dung = f"Bộ môn trả lại đề cương: {nhan_xet[:150]}"
    if topic.sinh_vien is not None:
        notifications.create(
            db, topic.sinh_vien.tai_khoan_id, DE_CUONG_BO_MON_TRA_LAI, noi_dung, lien_ket="/de-cuong"
        )
    if topic.giang_vien is not None:
        notifications.create(
            db,
            topic.giang_vien.tai_khoan_id,
            DE_CUONG_BO_MON_TRA_LAI,
            noi_dung,
            lien_ket=f"/duyet-de-cuong?de_tai_id={de_tai_id}",
        )
    db.commit()
    return get_detail(db, user, de_tai_id)


def export_signed_zip(db: Session, dot_do_an_id: int) -> tuple[str, bytes]:
    """Thư mục đề cương đã ký số của một đợt (bản ký số mới nhất mỗi đề tài),
    nén ZIP để nộp về khoa."""
    cohort = db.get(DotDoAn, dot_do_an_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đợt đồ án")
    latest = (
        select(LuotDuyetBoMon.de_cuong_id, func.max(LuotDuyetBoMon.id).label("max_id"))
        .where(LuotDuyetBoMon.ket_qua == KET_QUA_DA_DUYET)
        .where(LuotDuyetBoMon.tai_lieu_ky_so_id.is_not(None))
        .group_by(LuotDuyetBoMon.de_cuong_id)
        .subquery()
    )
    rows = (
        db.execute(
            select(LuotDuyetBoMon)
            .join(latest, LuotDuyetBoMon.id == latest.c.max_id)
            .join(DeCuong, DeCuong.id == LuotDuyetBoMon.de_cuong_id)
            .join(DeTai, DeTai.id == DeCuong.de_tai_id)
            .where(DeTai.dot_do_an_id == dot_do_an_id)
            .where(DeCuong.trang_thai == DC_DA_DUYET)
            .options(selectinload(LuotDuyetBoMon.tai_lieu_ky_so))
        )
        .scalars()
        .all()
    )
    buf = io.BytesIO()
    used: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for row in rows:
            doc = row.tai_lieu_ky_so
            path = documents.storage_path(doc.ten_luu_tru)
            if not path.exists():
                continue
            name = doc.ten_goc
            stem, dot, ext = name.rpartition(".")
            n = 2
            while name in used:
                name = f"{stem} ({n}){dot}{ext}" if dot else f"{name} ({n})"
                n += 1
            used.add(name)
            zf.write(path, arcname=name)
    ten_zip = f"de-cuong-ky-so-dot-{cohort.id}.zip"
    return ten_zip, buf.getvalue()
