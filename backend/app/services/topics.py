from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.models.bao_ve import LichBaoVe
from app.models.de_cuong import LOAI_DE_TAI, DeCuong, TaiLieuDoAn
from app.models.de_tai import (
    DA_PHAN_CONG,
    DeTai,
    GIANG_VIEN,
    NHAP,
    SINH_VIEN,
)
from app.models.dinh_huong import DinhHuong
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.kho import DoAnKho
from app.models.tai_khoan import GiangVien, SinhVien
from app.models.tien_do import BaoCaoTienDo
from app.models.thong_bao import DE_TAI_PHAN_CONG
from app.models.trung_lap import KetQuaKiemTraTrungLap
from app.schemas.common import Page, nfc
from app.schemas.topics import (
    CohortRef,
    DinhHuongRef,
    PersonRef,
    QuyenOut,
    SavedChiTietTrungLap,
    SavedTitleCheck,
    TepDinhKem,
    TopicCreate,
    TopicListItem,
    TopicListParams,
    TopicOut,
    TopicUpdate,
)
from app.services import assignments, documents, notifications, title_check
from app.services.documents import ValidatedFile

# Góp ý GVHD mục 1 (quick 261014-u0j): chỉ GVHD tạo và giao đề tài cho SV trong
# lớp hướng dẫn (UC1.1) — SV không tự đề xuất/đăng ký, không còn bước duyệt. Các
# giá trị enum/cột cũ (CHO_DUYET, DA_DUYET, TU_CHOI, ly_do_tu_choi) giữ trong
# CSDL để tương thích dữ liệu nhưng không còn được tạo ra (D-03).
#
# T-02-25 (D-05): mọi thao tác ghi có thể vi phạm uk_de_tai_sv_hoat_dong (1 SV chỉ
# có tối đa 1 đề tài đang hoạt động) đều bắt IntegrityError -> 409, không kiểm tra
# rồi ghi (check-then-act) vì race condition giữa hai request đồng thời.
_COHORT_CLOSED_DETAIL = "Đợt đồ án đã đóng"
_COHORT_NOT_FOUND_DETAIL = "Không tìm thấy đợt đồ án"
_TOPIC_NOT_FOUND_DETAIL = "Không tìm thấy đề tài"
_FORBIDDEN_EDIT_DETAIL = "Bạn không có quyền chỉnh sửa đề tài này"
_FORBIDDEN_VIEW_DETAIL = "Bạn không có quyền xem đề tài này"
_NOT_DRAFT_DETAIL = "Chỉ sửa được đề tài ở trạng thái Nháp"
_SUBMIT_NOT_DRAFT_DETAIL = "Đề tài không ở trạng thái Nháp"
_SV_HAS_ACTIVE_TOPIC_DETAIL = "Sinh viên này đã có một đề tài đang hoạt động"
_NOT_MY_STUDENT_DETAIL = "Sinh viên không thuộc lớp hướng dẫn của bạn trong đợt này"
_DINH_HUONG_INVALID_DETAIL = "Định hướng không tồn tại hoặc đã ngừng sử dụng"
_WITHDRAW_FORBIDDEN_DETAIL = "Chỉ GVHD của đề tài hoặc Bộ môn mới được thu hồi đề tài"
_WITHDRAW_NOT_ASSIGNED_DETAIL = "Chỉ thu hồi được đề tài Đã phân công"
# Thứ tự kiểm tra: việc SV đã làm trên đề tài -> lý do không thu hồi được.
_WITHDRAW_BLOCKERS = (
    (DeCuong, "Sinh viên đã nộp đề cương cho đề tài này — không thu hồi được"),
    (BaoCaoTienDo, "Sinh viên đã nộp báo cáo tiến độ cho đề tài này — không thu hồi được"),
    (LichBaoVe, "Đề tài đã được xếp lịch bảo vệ — không thu hồi được"),
    (DoAnKho, "Đề tài đã được lưu vào kho đồ án — không thu hồi được"),
)
_ATTACH_FORBIDDEN_DETAIL = "Chỉ GVHD của đề tài mới được đính kèm file"
_NO_STUDENT_ON_DRAFT_DETAIL = (
    "Đề tài nháp chưa chọn sinh viên được giao — hãy sửa và chọn sinh viên trước khi gửi"
)


def is_owner(user: CurrentUser, topic: DeTai) -> bool:
    """D-08: chủ sở hữu đề tài là GVHD đứng tên tạo đề tài, không phải GV khác và
    cũng không phải SV/Bộ môn (hàng cũ do SV đề xuất không còn chủ sở hữu)."""
    return (
        topic.loai_nguoi_de_xuat == GIANG_VIEN
        and user.giang_vien_id is not None
        and topic.giang_vien_id == user.giang_vien_id
    )


def _is_hidden_draft(user: CurrentUser, topic: DeTai) -> bool:
    """Nháp chỉ người soạn thấy: nháp GV định giao cho SV ẩn với SV; (hàng cũ) nháp
    SV chưa gửi ẩn với GV."""
    if topic.trang_thai != NHAP:
        return False
    if user.vai_tro == VaiTro.SINH_VIEN:
        return topic.loai_nguoi_de_xuat == GIANG_VIEN
    return topic.loai_nguoi_de_xuat == SINH_VIEN


def can_view(db: Session, user: CurrentUser, topic: DeTai) -> bool:
    """T-02-23/UC0.8: Bộ môn luôn xem được; GV xem đề tài mình hướng dẫn; SV chỉ
    xem đề tài được giao cho chính mình (không thấy bản nháp GV đang soạn)."""
    if user.vai_tro == VaiTro.BO_MON:
        return True
    if user.vai_tro == VaiTro.SINH_VIEN and user.sinh_vien_id is not None:
        return topic.sinh_vien_id == user.sinh_vien_id and not _is_hidden_draft(user, topic)
    if user.vai_tro == VaiTro.GIANG_VIEN and user.giang_vien_id is not None:
        if topic.giang_vien_id == user.giang_vien_id:
            return not _is_hidden_draft(user, topic)
    return False


def _get_or_404(db: Session, topic_id: int) -> DeTai:
    topic = db.execute(
        select(DeTai)
        .where(DeTai.id == topic_id)
        .options(
            joinedload(DeTai.dot_do_an),
            joinedload(DeTai.giang_vien),
            joinedload(DeTai.sinh_vien),
            joinedload(DeTai.dinh_huong),
        )
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return topic


def _check_dinh_huong(db: Session, dinh_huong_id: int | None, current_id: int | None = None) -> None:
    """Định hướng phải còn hoạt động — trừ khi giữ nguyên định hướng hiện có của
    đề tài (Bộ môn ngừng một định hướng không làm hỏng đề tài cũ)."""
    if dinh_huong_id is None or dinh_huong_id == current_id:
        return
    item = db.get(DinhHuong, dinh_huong_id)
    if item is None or not item.hoat_dong:
        raise HTTPException(status_code=422, detail=_DINH_HUONG_INVALID_DETAIL)


def _dinh_huong_ref(topic: DeTai) -> DinhHuongRef | None:
    item = topic.dinh_huong
    if item is None:
        return None
    return DinhHuongRef(id=item.id, ma=item.ma, ten=item.ten)


def latest_attachment(db: Session, topic_id: int) -> TaiLieuDoAn | None:
    return (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == topic_id)
            .where(TaiLieuDoAn.loai == LOAI_DE_TAI)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def _get_open_cohort_or_error(db: Session, dot_do_an_id: int) -> DotDoAn:
    cohort = db.get(DotDoAn, dot_do_an_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail=_COHORT_NOT_FOUND_DETAIL)
    if cohort.trang_thai != DANG_MO:
        raise HTTPException(status_code=409, detail=_COHORT_CLOSED_DETAIL)
    return cohort


def _lock_open_cohort_or_error(db: Session, dot_do_an_id: int) -> DotDoAn:
    """WR-01: giống _get_open_cohort_or_error nhưng khóa hàng đợt (SELECT ...
    FOR UPDATE) ngay trước khi ghi đề tài. create_topic/update_topic gọi
    _get_open_cohort_or_error TRƯỚC (early 404/409, không giữ khóa qua bước
    kiểm tra trùng tên có thể chậm — UC1.1/D-10), rồi gọi hàm này NGAY TRƯỚC
    db.add()/commit() để đóng cửa sổ TOCTOU: nếu một request khác đang đóng
    đợt (cohorts.close_cohort cũng ghi vào cùng hàng dot_do_an), một trong
    hai giao dịch phải chờ giao dịch kia commit trước khi đọc/ghi tiếp —
    không còn khoảng hở giữa đọc trạng thái và ghi đề tài, giống cách
    submit_topic/register_topic tự bảo vệ bằng UPDATE có điều kiện."""
    cohort = db.execute(
        select(DotDoAn).where(DotDoAn.id == dot_do_an_id).with_for_update()
    ).scalar_one_or_none()
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


def _person_refs(
    topic: DeTai,
) -> tuple[PersonRef, PersonRef | None, PersonRef | None]:
    """Trả (người đề xuất, GVHD, sinh viên) — dùng chung cho get_topic (TopicOut)
    và list_topics (TopicListItem), tránh N+1 vì các quan hệ đã được eager-load.
    Góp ý GVHD: người đề xuất luôn là GVHD (kể cả đề tài cũ do SV đề xuất)."""
    if topic.giang_vien is not None:
        nguoi_de_xuat = _person_ref(topic.giang_vien, "ma_giang_vien")
    else:
        nguoi_de_xuat = PersonRef(id=0, ho_ten="")

    giang_vien_huong_dan = (
        _person_ref(topic.giang_vien, "ma_giang_vien") if topic.giang_vien is not None else None
    )
    sinh_vien = (
        _person_ref(topic.sinh_vien, "ma_so_sinh_vien") if topic.sinh_vien is not None else None
    )
    return nguoi_de_xuat, giang_vien_huong_dan, sinh_vien


def _to_out(db: Session, user: CurrentUser, topic: DeTai) -> TopicOut:
    nguoi_de_xuat, giang_vien_huong_dan, sinh_vien = _person_refs(topic)

    owner = is_owner(user, topic)
    la_nhap = topic.trang_thai == NHAP
    quyen = QuyenOut(
        sua=owner and la_nhap,
        gui=owner and la_nhap,
        thu_hoi=(owner or user.vai_tro == VaiTro.BO_MON)
        and topic.trang_thai == DA_PHAN_CONG
        and topic.dot_do_an.trang_thai == DANG_MO,
    )

    saved_check = _saved_title_check_out(title_check.latest_title_check(db, topic.id))
    attachment = latest_attachment(db, topic.id)

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
        dinh_huong=_dinh_huong_ref(topic),
        tep_dinh_kem=(
            TepDinhKem(
                id=attachment.id,
                ten_goc=attachment.ten_goc,
                kich_thuoc=attachment.kich_thuoc,
                dinh_dang=attachment.dinh_dang,
                thoi_diem_nop=attachment.thoi_diem_nop,
            )
            if attachment is not None
            else None
        ),
        # Lần kiểm tra trùng tên được lưu đúng lúc GVHD giao đề tài.
        ngay_giao=(
            saved_check.thoi_diem
            if saved_check is not None and topic.trang_thai == DA_PHAN_CONG
            else None
        ),
        trang_thai=topic.trang_thai,
        loai_nguoi_de_xuat=topic.loai_nguoi_de_xuat,
        nguoi_de_xuat=nguoi_de_xuat,
        giang_vien_huong_dan=giang_vien_huong_dan,
        sinh_vien=sinh_vien,
        ly_do_tu_choi=topic.ly_do_tu_choi,
        quyen=quyen,
        kiem_tra_ten=saved_check,
    )


def _gv_label(gv: GiangVien | None) -> str:
    if gv is None:
        return ""
    return " ".join(part for part in (gv.hoc_vi, gv.ho_ten) if part)


def _require_my_student(db: Session, user: CurrentUser, dot_do_an_id: int, sinh_vien_id: int) -> None:
    """UC0.8: GV chỉ giao đề tài cho SV trong lớp hướng dẫn của mình ở đợt đó."""
    if not assignments.is_advisor_of(db, user.giang_vien_id, dot_do_an_id, sinh_vien_id):
        raise HTTPException(status_code=409, detail=_NOT_MY_STUDENT_DETAIL)


def _notify_after_send(db: Session, topic: DeTai) -> None:
    """Thông báo cùng transaction với lần giao đề tài (D-05/D-08): GVHD giao ->
    SV được báo đề tài + GVHD."""
    ten = topic.ten_de_tai
    if topic.trang_thai == DA_PHAN_CONG and topic.sinh_vien_id is not None:
        sv = db.get(SinhVien, topic.sinh_vien_id)
        gv = db.get(GiangVien, topic.giang_vien_id)
        notifications.create(
            db,
            sv.tai_khoan_id,
            DE_TAI_PHAN_CONG,
            f"GVHD {_gv_label(gv)} đã giao cho bạn đề tài '{ten}'",
            lien_ket=f"/de-tai/{topic.id}",
        )


def create_topic(db: Session, user: CurrentUser, payload: TopicCreate) -> TopicOut:
    _get_open_cohort_or_error(db, payload.dot_do_an_id)

    # UC0.8/D-07: chỉ GVHD được Bộ môn phân công cho SV trong đợt này mới tạo và
    # giao đề tài cho SV đó; giao thẳng -> Đã phân công.
    giang_vien_id = user.giang_vien_id
    sinh_vien_id = payload.sinh_vien_id
    _require_my_student(db, user, payload.dot_do_an_id, sinh_vien_id)
    _check_dinh_huong(db, payload.dinh_huong_id)

    # UC1.1/D-10: tính kiểm tra trùng tên TRƯỚC khi mở transaction ghi (lời gọi
    # AI có thể mất vài giây ở Phase 4) — chỉ khi giao ngay (gui=True).
    check_result = title_check.kiem_tra_ten(db, payload.ten_de_tai) if payload.gui else None

    topic = DeTai(
        dot_do_an_id=payload.dot_do_an_id,
        giang_vien_id=giang_vien_id,
        sinh_vien_id=sinh_vien_id,
        ten_de_tai=payload.ten_de_tai,
        mo_ta=payload.mo_ta,
        linh_vuc=payload.linh_vuc,
        dinh_huong_id=payload.dinh_huong_id,
        trang_thai=DA_PHAN_CONG if payload.gui else NHAP,
        loai_nguoi_de_xuat=GIANG_VIEN,
    )
    try:
        # WR-01: khóa lại đợt ngay trước khi ghi để đóng cửa sổ TOCTOU giữa
        # lần kiểm tra ở trên và INSERT thật sự (khoảng cách này có thể vài
        # giây khi payload.gui=True gọi AI).
        _lock_open_cohort_or_error(db, payload.dot_do_an_id)
        db.add(topic)
        db.flush()
        if check_result is not None:
            title_check.luu_ket_qua(db, topic.id, payload.ten_de_tai, check_result)
            _notify_after_send(db, topic)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_SV_HAS_ACTIVE_TOPIC_DETAIL) from None
    except HTTPException:
        db.rollback()
        raise

    return _to_out(db, user, _get_or_404(db, topic.id))


def update_topic(db: Session, user: CurrentUser, topic_id: int, payload: TopicUpdate) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    if not is_owner(user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN_EDIT_DETAIL)
    if topic.trang_thai != NHAP:
        raise HTTPException(status_code=409, detail=_NOT_DRAFT_DETAIL)
    _get_open_cohort_or_error(db, payload.dot_do_an_id)

    _require_my_student(db, user, payload.dot_do_an_id, payload.sinh_vien_id)
    topic.sinh_vien_id = payload.sinh_vien_id

    topic.dot_do_an_id = payload.dot_do_an_id
    topic.ten_de_tai = payload.ten_de_tai
    topic.mo_ta = payload.mo_ta
    topic.linh_vuc = payload.linh_vuc
    _check_dinh_huong(db, payload.dinh_huong_id, topic.dinh_huong_id)
    topic.dinh_huong_id = payload.dinh_huong_id
    try:
        # WR-01: khóa lại đợt ngay trước khi ghi để đóng cửa sổ TOCTOU giữa
        # _get_open_cohort_or_error ở trên và UPDATE thật sự.
        _lock_open_cohort_or_error(db, payload.dot_do_an_id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_SV_HAS_ACTIVE_TOPIC_DETAIL) from None
    except HTTPException:
        db.rollback()
        raise

    return _to_out(db, user, _get_or_404(db, topic_id))


def submit_topic(db: Session, user: CurrentUser, topic_id: int) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    if not is_owner(user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN_EDIT_DETAIL)

    if topic.sinh_vien_id is None:
        # Bộ môn đổi GVHD đã gỡ SV khỏi nháp (assignments.reassign) — phải chọn lại.
        raise HTTPException(status_code=409, detail=_NO_STUDENT_ON_DRAFT_DETAIL)
    # GVHD đọc lại lúc gửi (Bộ môn có thể vừa đổi phân công).
    _require_my_student(db, user, topic.dot_do_an_id, topic.sinh_vien_id)
    values = {"trang_thai": DA_PHAN_CONG}
    sv_guard = DeTai.sinh_vien_id == topic.sinh_vien_id

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
        .where(sv_guard)
        .where(DeTai.dot_do_an_id.in_(select(DotDoAn.id).where(DotDoAn.trang_thai == DANG_MO)))
        .values(**values)
    )
    try:
        result = db.execute(stmt)
        if result.rowcount > 0:
            title_check.luu_ket_qua(db, topic_id, ten_de_tai, check_result)
            db.expire_all()
            _notify_after_send(db, db.get(DeTai, topic_id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_SV_HAS_ACTIVE_TOPIC_DETAIL) from None

    if result.rowcount == 0:
        db.expire_all()
        fresh = _get_or_404(db, topic_id)
        if fresh.trang_thai != NHAP:
            raise HTTPException(status_code=409, detail=_SUBMIT_NOT_DRAFT_DETAIL)
        raise HTTPException(status_code=409, detail=_COHORT_CLOSED_DETAIL)

    return _to_out(db, user, _get_or_404(db, topic_id))


def withdraw_topic(db: Session, user: CurrentUser, topic_id: int, ly_do: str | None) -> TopicOut:
    """Thu hồi đề tài Đã phân công về Nháp (giữ nguyên SV) để GVHD sửa rồi giao
    lại; SV mất đề tài đang hoạt động nên GVHD cũng có thể giao đề tài khác."""
    topic = _get_or_404(db, topic_id)
    if not (is_owner(user, topic) or user.vai_tro == VaiTro.BO_MON):
        raise HTTPException(status_code=403, detail=_WITHDRAW_FORBIDDEN_DETAIL)
    try:
        _lock_open_cohort_or_error(db, topic.dot_do_an_id)
        # Khóa hàng đề tài: hai lượt thu hồi/giao đồng thời không cùng đọc trạng thái cũ.
        # shortcut: nộp đề cương không khóa hàng đề tài nên còn khe rất nhỏ nếu SV nộp
        # đúng lúc thu hồi; thêm with_for_update ở outlines nếu cần chặt hơn.
        topic = db.execute(
            select(DeTai).where(DeTai.id == topic_id).with_for_update().execution_options(populate_existing=True)
        ).scalar_one()
        if topic.trang_thai != DA_PHAN_CONG:
            raise HTTPException(status_code=409, detail=_WITHDRAW_NOT_ASSIGNED_DETAIL)
        for model, detail in _WITHDRAW_BLOCKERS:
            if db.scalar(select(model.id).where(model.de_tai_id == topic_id).limit(1)) is not None:
                raise HTTPException(status_code=409, detail=detail)

        topic.trang_thai = NHAP
        nguoi = "Bộ môn" if user.vai_tro == VaiTro.BO_MON else f"GVHD {_gv_label(topic.giang_vien)}"
        noi_dung = f"{nguoi} đã thu hồi đề tài '{topic.ten_de_tai}'" + (f". Lý do: {ly_do}" if ly_do else "")
        nguoi_nhan = [topic.sinh_vien.tai_khoan_id]
        if user.vai_tro == VaiTro.BO_MON and topic.giang_vien is not None:
            nguoi_nhan.append(topic.giang_vien.tai_khoan_id)
        for tai_khoan_id in nguoi_nhan:
            notifications.create(db, tai_khoan_id, DE_TAI_PHAN_CONG, noi_dung)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    return _to_out(db, user, _get_or_404(db, topic_id))


def get_topic(db: Session, user: CurrentUser, topic_id: int) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    if not can_view(db, user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN_VIEW_DETAIL)
    return _to_out(db, user, topic)


def _scope_predicate(user: CurrentUser, pham_vi: str):
    """T-02-29/UC1.2 A1/D-08: dựng điều kiện phạm vi TRƯỚC, rồi mọi filter khác
    chỉ được AND vào — không bao giờ mở rộng phạm vi (pham_vi không còn mở rộng
    phạm vi của ai). Bộ môn không giới hạn. GV chỉ thấy đề tài mình hướng dẫn
    (trừ nháp SV cũ chưa gửi); SV chỉ thấy đề tài được giao cho mình, không thấy
    nháp GV đang soạn."""
    if user.vai_tro == VaiTro.BO_MON:
        return None

    if user.vai_tro == VaiTro.SINH_VIEN:
        return (DeTai.sinh_vien_id == user.sinh_vien_id) & ~(
            (DeTai.loai_nguoi_de_xuat == GIANG_VIEN) & (DeTai.trang_thai == NHAP)
        )

    # GIANG_VIEN — GV không thấy đề tài GV khác.
    return (DeTai.giang_vien_id == user.giang_vien_id) & ~(
        (DeTai.loai_nguoi_de_xuat == SINH_VIEN) & (DeTai.trang_thai == NHAP)
    )


def _list_item_out(topic: DeTai) -> TopicListItem:
    nguoi_de_xuat, giang_vien_huong_dan, sinh_vien = _person_refs(topic)
    return TopicListItem(
        id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        linh_vuc=topic.linh_vuc,
        dinh_huong=_dinh_huong_ref(topic),
        trang_thai=topic.trang_thai,
        dot_do_an=CohortRef(
            id=topic.dot_do_an.id,
            ten_dot=topic.dot_do_an.ten_dot,
            khoa=topic.dot_do_an.khoa,
            trang_thai=topic.dot_do_an.trang_thai,
        ),
        nguoi_de_xuat=nguoi_de_xuat,
        giang_vien_huong_dan=giang_vien_huong_dan,
        sinh_vien=sinh_vien,
    )


def list_topics(db: Session, user: CurrentUser, params: TopicListParams) -> Page[TopicListItem]:
    """UC1.2/TOPC-04/NFR-12: danh sách đề tài lọc theo trạng thái/đợt/GVHD/lĩnh
    vực/từ khóa, luôn trong phạm vi server-side của vai trò gọi (T-02-29)."""
    stmt = select(DeTai)

    scope = _scope_predicate(user, params.pham_vi)
    if scope is not None:
        stmt = stmt.where(scope)

    if params.dot_do_an_id is not None:
        stmt = stmt.where(DeTai.dot_do_an_id == params.dot_do_an_id)
    if params.trang_thai is not None:
        stmt = stmt.where(DeTai.trang_thai == params.trang_thai)
    if params.giang_vien_id is not None:
        stmt = stmt.where(DeTai.giang_vien_id == params.giang_vien_id)
    if params.linh_vuc is not None:
        stmt = stmt.where(DeTai.linh_vuc == params.linh_vuc)
    if params.dinh_huong_id is not None:
        stmt = stmt.where(DeTai.dinh_huong_id == params.dinh_huong_id)
    if params.q:
        # T-02-32/T-02-33: autoescape=True chống LIKE-injection qua % và _.
        stmt = stmt.where(DeTai.ten_de_tai.contains(nfc(params.q), autoescape=True))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    if params.sap_xep == "ten":
        stmt = stmt.order_by(DeTai.ten_de_tai.asc())
    else:
        stmt = stmt.order_by(DeTai.id.desc())

    paged = (
        stmt.options(
            selectinload(DeTai.dot_do_an),
            selectinload(DeTai.giang_vien),
            selectinload(DeTai.sinh_vien),
            selectinload(DeTai.dinh_huong),
        )
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    rows = db.execute(paged).scalars().all()

    items = [_list_item_out(row) for row in rows]

    return Page[TopicListItem](
        items=items, total=total, page=params.page, page_size=params.page_size
    )


def attach_file(db: Session, user: CurrentUser, topic_id: int, vf: ValidatedFile) -> TopicOut:
    """GVHD đính kèm file mô tả đề tài (mỗi lần tải lên là một phiên bản mới)."""
    topic = _get_or_404(db, topic_id)
    if user.giang_vien_id is None or topic.giang_vien_id != user.giang_vien_id:
        raise HTTPException(status_code=403, detail=_ATTACH_FORBIDDEN_DETAIL)
    doc = documents.store(db, de_tai_id=topic.id, loai=LOAI_DE_TAI, vf=vf)
    try:
        db.commit()
    except Exception:
        db.rollback()
        documents.remove_file_quietly(doc.ten_luu_tru)
        raise
    return _to_out(db, user, _get_or_404(db, topic.id))
