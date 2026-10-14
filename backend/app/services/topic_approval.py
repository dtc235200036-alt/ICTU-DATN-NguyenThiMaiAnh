from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.models.de_tai import CHO_DUYET, DA_PHAN_CONG, SINH_VIEN, DeTai, TU_CHOI
from app.models.tai_khoan import GiangVien
from app.models.thong_bao import DE_TAI_PHAN_CONG, DE_TAI_TU_CHOI
from app.models.trung_lap import HOAN_TAT, TEN_DE_TAI, KetQuaKiemTraTrungLap
from app.schemas.common import Page
from app.schemas.topic_approval import PendingTopicItem, TitleCheckSummary
from app.schemas.topics import CohortRef, TopicOut
from app.services import notifications
from app.services import topics as topics_service
from app.services.topics import _person_refs

# UC1.3/D-08 (đổi ở 0015): GVHD của SV duyệt hoặc từ chối (kèm lý do) đề tài SV
# đề xuất đang Chờ duyệt — Bộ môn không còn duyệt đề tài; GVHD đã được Bộ môn
# phân công từ đầu đợt (UC0.8). Mọi thay đổi trạng thái là MỘT UPDATE có điều
# kiện trên trang_thai = 'CHO_DUYET' và giang_vien_id = người gọi (T-02-36),
# không đọc rồi ghi; đọc lại chỉ để chọn đúng thông điệp lỗi khi rowcount=0.
_TOPIC_NOT_FOUND_DETAIL = "Không tìm thấy đề tài"
_NOT_PENDING_DETAIL = "Đề tài không còn ở trạng thái Chờ duyệt"
_NOT_ADVISOR_DETAIL = "Bạn không phải giảng viên hướng dẫn của đề tài này"
_LY_DO_MAX = 200


def _lien_ket(topic_id: int) -> str:
    return f"/de-tai/{topic_id}"


def _gv_label(gv: GiangVien) -> str:
    return " ".join(part for part in (gv.hoc_vi, gv.ho_ten) if part)


def _refused(db: Session, topic_id: int) -> HTTPException:
    """rowcount=0: UPDATE đã tự quyết định thất bại (đề tài đã bị người khác
    duyệt/từ chối hoặc SV vừa đổi) — rollback để KHÔNG tạo thông báo nào, rồi
    đọc lại chỉ để chọn đúng thông điệp (T-02-36, T-03-39)."""
    db.rollback()
    db.expire_all()
    fresh = db.get(DeTai, topic_id)
    if fresh is None:
        return HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return HTTPException(status_code=409, detail=_NOT_PENDING_DETAIL)


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
    db: Session, user: CurrentUser, dot_do_an_id: int | None, page: int, page_size: int
) -> Page[PendingTopicItem]:
    """UC1.3/MH-07: đề tài SV trong lớp mình gửi đang Chờ duyệt (lọc theo đợt
    nếu có), cũ nhất trước."""
    stmt = (
        select(DeTai)
        .where(DeTai.trang_thai == CHO_DUYET)
        .where(DeTai.giang_vien_id == user.giang_vien_id)
    )
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


def _own_topic_or_error(db: Session, user: CurrentUser, topic_id: int) -> DeTai:
    topic = db.get(DeTai, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    if user.giang_vien_id is None or topic.giang_vien_id != user.giang_vien_id:
        raise HTTPException(status_code=403, detail=_NOT_ADVISOR_DETAIL)
    return topic


def approve(db: Session, user: CurrentUser, topic_id: int) -> TopicOut:
    """UC1.3: GVHD duyệt đề tài SV trong lớp mình đề xuất -> Đã phân công."""
    topic = _own_topic_or_error(db, user, topic_id)
    ten = topic.ten_de_tai
    sv_seen = topic.sinh_vien_id
    sv = topic.sinh_vien
    gv = db.get(GiangVien, user.giang_vien_id)

    stmt = (
        update(DeTai)
        .where(DeTai.id == topic_id)
        .where(DeTai.trang_thai == CHO_DUYET)
        .where(DeTai.giang_vien_id == user.giang_vien_id)
        .where(DeTai.loai_nguoi_de_xuat == SINH_VIEN)
        .where(DeTai.sinh_vien_id == sv_seen)
        .values(trang_thai=DA_PHAN_CONG)
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        raise _refused(db, topic_id)

    # D-08/T-03-39: thông báo và thay đổi trạng thái chung MỘT commit.
    if sv is not None:
        notifications.create(
            db,
            sv.tai_khoan_id,
            DE_TAI_PHAN_CONG,
            f"Đề tài '{ten}' đã được GVHD {_gv_label(gv)} duyệt",
            lien_ket=_lien_ket(topic_id),
        )
    db.commit()

    return topics_service.get_topic(db, user, topic_id)


def reject(db: Session, user: CurrentUser, topic_id: int, ly_do: str) -> TopicOut:
    """UC1.3/A1: lý do bắt buộc, lưu vào de_tai.ly_do_tu_choi; cột sinh
    sinh_vien_id_dang_hoat_dong tự giải phóng SV ngay khi trang_thai=TU_CHOI —
    SV đề xuất đề tài khác (vẫn gửi tới cùng GVHD)."""
    topic = _own_topic_or_error(db, user, topic_id)
    ten = topic.ten_de_tai
    sv = topic.sinh_vien

    stmt = (
        update(DeTai)
        .where(DeTai.id == topic_id)
        .where(DeTai.trang_thai == CHO_DUYET)
        .where(DeTai.giang_vien_id == user.giang_vien_id)
        .values(trang_thai=TU_CHOI, ly_do_tu_choi=ly_do)
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        raise _refused(db, topic_id)

    if sv is not None:
        notifications.create(
            db,
            sv.tai_khoan_id,
            DE_TAI_TU_CHOI,
            f"Đề tài '{ten}' bị GVHD từ chối: {ly_do[:_LY_DO_MAX]}",
            lien_ket=_lien_ket(topic_id),
        )
    db.commit()

    return topics_service.get_topic(db, user, topic_id)
