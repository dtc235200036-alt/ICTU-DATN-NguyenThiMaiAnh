from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.models.de_tai import (
    CHO_DUYET,
    DA_DUYET,
    DeTai,
    GIANG_VIEN,
    NHAP,
    SINH_VIEN,
)
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.trung_lap import KetQuaKiemTraTrungLap
from app.schemas.topics import (
    CohortRef,
    PersonRef,
    QuyenOut,
    SavedChiTietTrungLap,
    SavedTitleCheck,
    TopicCreate,
    TopicOut,
    TopicUpdate,
)
from app.services import title_check

# T-02-25 (D-05): mọi thao tác ghi có thể vi phạm uk_de_tai_sv_hoat_dong (1 SV chỉ
# có tối đa 1 đề tài đang hoạt động) đều bắt IntegrityError -> 409, không kiểm tra
# rồi ghi (check-then-act) vì race condition giữa hai request đồng thời.
_DUPLICATE_ACTIVE_TOPIC_DETAIL = (
    "Bạn đã có một đề tài đang hoạt động (chờ duyệt, đã duyệt hoặc đã phân công)"
)
_COHORT_CLOSED_DETAIL = "Đợt đồ án đã đóng"
_COHORT_NOT_FOUND_DETAIL = "Không tìm thấy đợt đồ án"
_TOPIC_NOT_FOUND_DETAIL = "Không tìm thấy đề tài"
_FORBIDDEN_EDIT_DETAIL = "Bạn không có quyền chỉnh sửa đề tài này"
_FORBIDDEN_VIEW_DETAIL = "Bạn không có quyền xem đề tài này"
_NOT_DRAFT_DETAIL = "Chỉ sửa được đề tài ở trạng thái Nháp"
_SUBMIT_NOT_DRAFT_DETAIL = "Đề tài không ở trạng thái Nháp"


def is_owner(user: CurrentUser, topic: DeTai) -> bool:
    """D-08: chủ sở hữu đề tài là người đứng tên đề xuất (GV hoặc SV), không phải
    bất kỳ ai cùng vai trò và cũng không phải Bộ môn."""
    if topic.loai_nguoi_de_xuat == SINH_VIEN:
        return user.sinh_vien_id is not None and topic.sinh_vien_id == user.sinh_vien_id
    return user.giang_vien_id is not None and topic.giang_vien_id == user.giang_vien_id


def can_view(user: CurrentUser, topic: DeTai) -> bool:
    """T-02-23: Bộ môn luôn xem được; SV/GV chỉ xem đề tài của chính mình; đề tài
    đã duyệt và còn trống (chưa có SV) thì ai cũng xem được (chuẩn bị cho UC1.2)."""
    if user.vai_tro == VaiTro.BO_MON:
        return True
    if user.vai_tro == VaiTro.SINH_VIEN and user.sinh_vien_id is not None:
        if topic.sinh_vien_id == user.sinh_vien_id:
            return True
    if user.vai_tro == VaiTro.GIANG_VIEN and user.giang_vien_id is not None:
        if topic.giang_vien_id == user.giang_vien_id:
            return True
    return topic.trang_thai == DA_DUYET and topic.sinh_vien_id is None


def _get_or_404(db: Session, topic_id: int) -> DeTai:
    topic = db.execute(
        select(DeTai)
        .where(DeTai.id == topic_id)
        .options(
            joinedload(DeTai.dot_do_an),
            joinedload(DeTai.giang_vien),
            joinedload(DeTai.sinh_vien),
        )
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return topic


def _get_open_cohort_or_error(db: Session, dot_do_an_id: int) -> DotDoAn:
    cohort = db.get(DotDoAn, dot_do_an_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail=_COHORT_NOT_FOUND_DETAIL)
    if cohort.trang_thai != DANG_MO:
        raise HTTPException(status_code=409, detail=_COHORT_CLOSED_DETAIL)
    return cohort


def _person_ref(entity, ma_attr: str) -> PersonRef:
    return PersonRef(id=entity.id, ho_ten=entity.ho_ten or "", ma=getattr(entity, ma_attr))


def _saved_title_check_out(ket_qua: KetQuaKiemTraTrungLap | None) -> SavedTitleCheck | None:
    if ket_qua is None:
        return None
    return SavedTitleCheck(
        trang_thai=ket_qua.trang_thai,
        ty_le_tong=float(ket_qua.ty_le_tong) if ket_qua.ty_le_tong is not None else None,
        nguong_ap_dung=float(ket_qua.nguong_ap_dung),
        thoi_diem=ket_qua.thoi_diem,
        chi_tiet=[
            SavedChiTietTrungLap(doi_tuong_trung=ct.doi_tuong_trung, ty_le=float(ct.ty_le))
            for ct in ket_qua.chi_tiet
        ],
    )


def _to_out(db: Session, user: CurrentUser, topic: DeTai) -> TopicOut:
    if topic.loai_nguoi_de_xuat == SINH_VIEN and topic.sinh_vien is not None:
        nguoi_de_xuat = _person_ref(topic.sinh_vien, "ma_so_sinh_vien")
    elif topic.giang_vien is not None:
        nguoi_de_xuat = _person_ref(topic.giang_vien, "ma_giang_vien")
    else:
        nguoi_de_xuat = PersonRef(id=0, ho_ten="")

    giang_vien_huong_dan = (
        _person_ref(topic.giang_vien, "ma_giang_vien") if topic.giang_vien is not None else None
    )
    sinh_vien = (
        _person_ref(topic.sinh_vien, "ma_so_sinh_vien") if topic.sinh_vien is not None else None
    )

    owner = is_owner(user, topic)
    la_nhap = topic.trang_thai == NHAP
    quyen = QuyenOut(sua=owner and la_nhap, gui=owner and la_nhap)

    saved_check = _saved_title_check_out(title_check.latest_title_check(db, topic.id))

    return TopicOut(
        id=topic.id,
        dot_do_an=CohortRef(
            id=topic.dot_do_an.id,
            ten_dot=topic.dot_do_an.ten_dot,
            khoa=topic.dot_do_an.khoa,
            trang_thai=topic.dot_do_an.trang_thai,
        ),
        ten_de_tai=topic.ten_de_tai,
        mo_ta=topic.mo_ta,
        linh_vuc=topic.linh_vuc,
        trang_thai=topic.trang_thai,
        loai_nguoi_de_xuat=topic.loai_nguoi_de_xuat,
        nguoi_de_xuat=nguoi_de_xuat,
        giang_vien_huong_dan=giang_vien_huong_dan,
        sinh_vien=sinh_vien,
        ly_do_tu_choi=topic.ly_do_tu_choi,
        quyen=quyen,
        kiem_tra_ten=saved_check,
    )


def create_topic(db: Session, user: CurrentUser, payload: TopicCreate) -> TopicOut:
    _get_open_cohort_or_error(db, payload.dot_do_an_id)

    if user.vai_tro == VaiTro.SINH_VIEN:
        loai = SINH_VIEN
        sinh_vien_id = user.sinh_vien_id
        giang_vien_id = None
    else:
        loai = GIANG_VIEN
        giang_vien_id = user.giang_vien_id
        sinh_vien_id = None

    # UC1.1/D-10: tính kiểm tra trùng tên TRƯỚC khi mở transaction ghi (lời gọi
    # AI có thể mất vài giây ở Phase 4) — chỉ khi gửi đề xuất ngay (gui=True).
    check_result = title_check.kiem_tra_ten(db, payload.ten_de_tai) if payload.gui else None

    topic = DeTai(
        dot_do_an_id=payload.dot_do_an_id,
        giang_vien_id=giang_vien_id,
        sinh_vien_id=sinh_vien_id,
        ten_de_tai=payload.ten_de_tai,
        mo_ta=payload.mo_ta,
        linh_vuc=payload.linh_vuc,
        trang_thai=CHO_DUYET if payload.gui else NHAP,
        loai_nguoi_de_xuat=loai,
    )
    db.add(topic)
    try:
        db.flush()
        if check_result is not None:
            title_check.luu_ket_qua(db, topic.id, payload.ten_de_tai, check_result)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_DUPLICATE_ACTIVE_TOPIC_DETAIL) from None

    return _to_out(db, user, _get_or_404(db, topic.id))


def update_topic(db: Session, user: CurrentUser, topic_id: int, payload: TopicUpdate) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    if not is_owner(user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN_EDIT_DETAIL)
    if topic.trang_thai != NHAP:
        raise HTTPException(status_code=409, detail=_NOT_DRAFT_DETAIL)
    _get_open_cohort_or_error(db, payload.dot_do_an_id)

    topic.dot_do_an_id = payload.dot_do_an_id
    topic.ten_de_tai = payload.ten_de_tai
    topic.mo_ta = payload.mo_ta
    topic.linh_vuc = payload.linh_vuc
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_DUPLICATE_ACTIVE_TOPIC_DETAIL) from None

    return _to_out(db, user, _get_or_404(db, topic_id))


def submit_topic(db: Session, user: CurrentUser, topic_id: int) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    if not is_owner(user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN_EDIT_DETAIL)

    # UC1.1/D-10: tính trước khi UPDATE trạng thái; chỉ lưu kết quả nếu UPDATE
    # thực sự đổi được trạng thái (persist cùng transaction với status change).
    check_result = title_check.kiem_tra_ten(db, topic.ten_de_tai, exclude_id=topic.id)
    ten_de_tai = topic.ten_de_tai

    # Điều kiện đợt đang mở nằm ngay trong UPDATE (không kiểm tra rồi ghi) — nếu
    # đợt vừa đóng giữa lúc kiểm tra và ghi, UPDATE này vẫn từ chối đúng (§3.2.5-b).
    stmt = (
        update(DeTai)
        .where(DeTai.id == topic_id)
        .where(DeTai.trang_thai == NHAP)
        .where(DeTai.dot_do_an_id.in_(select(DotDoAn.id).where(DotDoAn.trang_thai == DANG_MO)))
        .values(trang_thai=CHO_DUYET)
    )
    try:
        result = db.execute(stmt)
        if result.rowcount > 0:
            title_check.luu_ket_qua(db, topic_id, ten_de_tai, check_result)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_DUPLICATE_ACTIVE_TOPIC_DETAIL) from None

    if result.rowcount == 0:
        db.expire_all()
        fresh = _get_or_404(db, topic_id)
        if fresh.trang_thai != NHAP:
            raise HTTPException(status_code=409, detail=_SUBMIT_NOT_DRAFT_DETAIL)
        raise HTTPException(status_code=409, detail=_COHORT_CLOSED_DETAIL)

    return _to_out(db, user, _get_or_404(db, topic_id))


def get_topic(db: Session, user: CurrentUser, topic_id: int) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    if not can_view(user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN_VIEW_DETAIL)
    return _to_out(db, user, topic)
