from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.models.de_tai import CHO_DUYET, DA_DUYET, DA_PHAN_CONG, DeTai, TU_CHOI
from app.models.tai_khoan import GiangVien, TaiKhoan
from app.models.trung_lap import HOAN_TAT, TEN_DE_TAI, KetQuaKiemTraTrungLap
from app.schemas.common import Page
from app.schemas.topic_approval import PendingTopicItem, TitleCheckSummary
from app.schemas.topics import CohortRef, TopicOut
from app.services import topics as topics_service
from app.services.topics import _person_refs

# UC1.3/D-08: Bộ môn duyệt (kèm phân công GVHD) hoặc từ chối (kèm lý do) một
# đề tài đang Chờ duyệt — mọi thay đổi trạng thái là MỘT UPDATE có điều kiện
# trên trang_thai = 'CHO_DUYET' (T-02-36), không đọc rồi ghi cho quyết định
# chấp nhận/từ chối; đọc lại chỉ để chọn đúng thông điệp lỗi khi rowcount=0.
_TOPIC_NOT_FOUND_DETAIL = "Không tìm thấy đề tài"
_NOT_PENDING_DETAIL = "Đề tài không còn ở trạng thái Chờ duyệt"
_GV_REQUIRED_DETAIL = "Vui lòng chọn giảng viên hướng dẫn"
_GV_INVALID_DETAIL = "Giảng viên không tồn tại hoặc đã bị khóa"


def _title_check_summary(ket_qua: KetQuaKiemTraTrungLap | None) -> TitleCheckSummary:
    if ket_qua is None or ket_qua.trang_thai != HOAN_TAT:
        return TitleCheckSummary(trang_thai="CHUA_KIEM_TRA", so_tuong_tu=0)
    if not ket_qua.chi_tiet:
        return TitleCheckSummary(trang_thai="KHONG_TRUNG", so_tuong_tu=0)
    return TitleCheckSummary(trang_thai="CO_TUONG_TU", so_tuong_tu=len(ket_qua.chi_tiet))


def _pending_item_out(topic: DeTai, ket_qua: KetQuaKiemTraTrungLap | None) -> PendingTopicItem:
    nguoi_de_xuat, giang_vien, sinh_vien = _person_refs(topic)
    return PendingTopicItem(
        id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        linh_vuc=topic.linh_vuc,
        dot_do_an=CohortRef(
            id=topic.dot_do_an.id,
            ten_dot=topic.dot_do_an.ten_dot,
            khoa=topic.dot_do_an.khoa,
            trang_thai=topic.dot_do_an.trang_thai,
        ),
        loai_nguoi_de_xuat=topic.loai_nguoi_de_xuat,
        nguoi_de_xuat=nguoi_de_xuat,
        sinh_vien=sinh_vien,
        giang_vien=giang_vien,
        ngay_de_xuat=ket_qua.thoi_diem if ket_qua is not None else None,
        kiem_tra_ten=_title_check_summary(ket_qua),
    )


def list_pending(
    db: Session, dot_do_an_id: int | None, page: int, page_size: int
) -> Page[PendingTopicItem]:
    """UC1.3/MH-07: mọi đề tài Chờ duyệt (lọc theo đợt nếu có), cũ nhất trước."""
    stmt = select(DeTai).where(DeTai.trang_thai == CHO_DUYET)
    if dot_do_an_id is not None:
        stmt = stmt.where(DeTai.dot_do_an_id == dot_do_an_id)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    paged = (
        stmt.order_by(DeTai.id.asc())
        .options(
            selectinload(DeTai.dot_do_an),
            selectinload(DeTai.giang_vien),
            selectinload(DeTai.sinh_vien),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(paged).scalars().all()

    ids = [row.id for row in rows]
    latest_by_topic: dict[int, KetQuaKiemTraTrungLap] = {}
    if ids:
        # Một truy vấn cho cả trang (không phải mỗi dòng) — giữ dòng mới nhất
        # theo thoi_diem cho mỗi đề tài nhờ thứ tự ORDER BY + lấy dòng đầu.
        kq_rows = (
            db.execute(
                select(KetQuaKiemTraTrungLap)
                .where(KetQuaKiemTraTrungLap.de_tai_id.in_(ids))
                .where(KetQuaKiemTraTrungLap.loai_kiem_tra == TEN_DE_TAI)
                .options(selectinload(KetQuaKiemTraTrungLap.chi_tiet))
                .order_by(
                    KetQuaKiemTraTrungLap.de_tai_id,
                    KetQuaKiemTraTrungLap.thoi_diem.desc(),
                    KetQuaKiemTraTrungLap.id.desc(),
                )
            )
            .scalars()
            .all()
        )
        for kq in kq_rows:
            if kq.de_tai_id is not None and kq.de_tai_id not in latest_by_topic:
                latest_by_topic[kq.de_tai_id] = kq

    items = [_pending_item_out(row, latest_by_topic.get(row.id)) for row in rows]
    return Page[PendingTopicItem](items=items, total=total, page=page, page_size=page_size)


def approve(
    db: Session, user: CurrentUser, topic_id: int, giang_vien_id: int | None
) -> TopicOut:
    """UC1.3: GV-proposed chưa có SV -> Đã duyệt (mở đăng ký); đã có SV (tự đề
    xuất hoặc đã đăng ký) -> Đã phân công, BẮT BUỘC chọn GVHD thủ công (E1,
    không bao giờ tự động gán kể cả khi GV đề xuất là lựa chọn duy nhất)."""
    topic = db.get(DeTai, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)

    if topic.sinh_vien_id is None:
        stmt = (
            update(DeTai)
            .where(DeTai.id == topic_id)
            .where(DeTai.trang_thai == CHO_DUYET)
            .where(DeTai.sinh_vien_id.is_(None))
            .values(trang_thai=DA_DUYET)
        )
    else:
        if giang_vien_id is None:
            raise HTTPException(status_code=422, detail=_GV_REQUIRED_DETAIL)
        gv = db.execute(
            select(GiangVien)
            .join(TaiKhoan, TaiKhoan.id == GiangVien.tai_khoan_id)
            .where(GiangVien.id == giang_vien_id)
            .where(TaiKhoan.bi_khoa.is_(False))
        ).scalar_one_or_none()
        if gv is None:
            raise HTTPException(status_code=422, detail=_GV_INVALID_DETAIL)

        sv_seen = topic.sinh_vien_id
        stmt = (
            update(DeTai)
            .where(DeTai.id == topic_id)
            .where(DeTai.trang_thai == CHO_DUYET)
            .where(DeTai.sinh_vien_id == sv_seen)
            .values(trang_thai=DA_PHAN_CONG, giang_vien_id=giang_vien_id)
        )

    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        # Không phải check-then-act: UPDATE đã tự quyết định thất bại (đề tài
        # đã bị người khác duyệt/từ chối hoặc SV vừa đổi) — đọc lại chỉ để
        # chọn đúng thông điệp (T-02-36).
        db.expire_all()
        fresh = db.get(DeTai, topic_id)
        if fresh is None:
            raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
        raise HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL)

    return topics_service.get_topic(db, user, topic_id)


def reject(db: Session, user: CurrentUser, topic_id: int, ly_do: str) -> TopicOut:
    """UC1.3/A1: lý do bắt buộc, lưu vào de_tai.ly_do_tu_choi; cột sinh
    sinh_vien_id_dang_hoat_dong tự giải phóng SV ngay khi trang_thai=TU_CHOI."""
    stmt = (
        update(DeTai)
        .where(DeTai.id == topic_id)
        .where(DeTai.trang_thai == CHO_DUYET)
        .values(trang_thai=TU_CHOI, ly_do_tu_choi=ly_do)
    )
    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        db.expire_all()
        fresh = db.get(DeTai, topic_id)
        if fresh is None:
            raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
        raise HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL)

    return topics_service.get_topic(db, user, topic_id)
