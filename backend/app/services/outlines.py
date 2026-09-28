"""UC2 — Quản lý đề cương: nộp (một-chiều CHUA_NOP->CHO_DUYET->(DA_DUYET |
YEU_CAU_SUA->CHO_DUYET->...)), xem chi tiết/lịch sử, duyệt/yêu cầu sửa."""
from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.core.timeutil import now_utc
from app.models.de_cuong import (
    DC_CHO_DUYET,
    DC_CHUA_NOP,
    DC_DA_DUYET,
    DC_YEU_CAU_SUA,
    KET_QUA_DA_DUYET,
    KET_QUA_YEU_CAU_SUA,
    LOAI_DE_CUONG,
    DeCuong,
    LuotDuyetDeCuong,
    TaiLieuDoAn,
)
from app.models.de_tai import DA_PHAN_CONG, DeTai
from app.models.thong_bao import DE_CUONG_DUYET, DE_CUONG_MOI, DE_CUONG_YEU_CAU_SUA
from app.models.trung_lap import KetQuaKiemTraTrungLap
from app.schemas.common import Page
from app.schemas.outlines import (
    OutlineDetail,
    OutlineListItem,
    OutlineVersion,
    QuyenDeCuongOut,
    ReviewOut,
    ReviewRequest,
)
from app.schemas.topics import PersonRef
from app.services import document_check, documents, notifications
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
        )
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return topic


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
    db: Session, user: CurrentUser, de_tai_id: int, vf: ValidatedFile
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

    quyen = QuyenDeCuongOut(
        nop=(
            user.sinh_vien_id is not None
            and topic.sinh_vien_id == user.sinh_vien_id
            and topic.trang_thai == DA_PHAN_CONG
            and trang_thai in (DC_CHUA_NOP, DC_YEU_CAU_SUA)
        ),
        duyet=(
            user.giang_vien_id is not None
            and topic.giang_vien_id == user.giang_vien_id
            and trang_thai == DC_CHO_DUYET
        ),
    )

    return OutlineDetail(
        de_tai_id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        sinh_vien=_person_ref(topic.sinh_vien, "ma_so_sinh_vien"),
        giang_vien=_person_ref(topic.giang_vien, "ma_giang_vien"),
        trang_thai=trang_thai,
        ngay_nop_dau_tien=ngay_nop_dau_tien,
        phien_ban=phien_ban,
        quyen=quyen,
    )


def list_outlines(
    db: Session,
    user: CurrentUser,
    trang_thai: str | None,
    dot_do_an_id: int | None,
    page: int,
    page_size: int,
) -> Page[OutlineListItem]:
    """UC2.3/MH-08/MH-09: chỉ đề tài Đã phân công; SV/GV chỉ thấy đề tài của
    mình, Bộ môn thấy tất cả (T-03-04); một truy vấn cho cả trang phiên bản
    mới nhất + kết quả kiểm tra (không N+1)."""
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
    if trang_thai is not None:
        stmt = stmt.where(func.coalesce(DeCuong.trang_thai, DC_CHUA_NOP) == trang_thai)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    paged = (
        stmt.order_by(DeTai.id.desc())
        .options(selectinload(DeTai.sinh_vien), selectinload(DeTai.giang_vien))
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
            )
        )

    return Page[OutlineListItem](items=items, total=total, page=page, page_size=page_size)


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
        .values(trang_thai=DC_DA_DUYET)
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
            f"Đề cương của bạn đã được duyệt: {topic.ten_de_tai}",
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
