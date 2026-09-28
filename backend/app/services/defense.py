"""UC4 — Bảo vệ: nộp báo cáo cuối (UC4.1), lập hội đồng + xếp lịch (UC4.2,
D-06), chấm điểm (UC4.3), chốt kết quả + tự lưu kho (UC4.4/UC5.2) và SV xem
lịch/kết quả (UC4.5). GVHD của một SV không bao giờ được ngồi hội đồng của
chính SV đó — chặn ở server (409), không chỉ cảnh báo UI; chỉ thành viên hội
đồng mới xem/chấm SV của hội đồng mình (UC4.3 E1, 403)."""
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.core.timeutil import today_vn
from app.models.bao_ve import CHU_TICH, SLOT_MINUTES, THU_KY, DiemBaoVe, HoiDong, LichBaoVe, ThanhVienHoiDong
from app.models.de_cuong import DC_CHUA_NOP, DC_DA_DUYET, LOAI_BAO_CAO_CUOI, DeCuong, TaiLieuDoAn
from app.models.de_tai import DA_PHAN_CONG, DeTai
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan
from app.models.thong_bao import HOI_DONG_PHAN_CONG, KET_QUA_BAO_VE, LICH_BAO_VE
from app.schemas.defense import (
    CommitteeIn,
    CommitteeListItem,
    CommitteeOut,
    EligibleStudent,
    FinalizeOut,
    FinalReportDetail,
    FinalReportVersion,
    MemberIn,
    MemberOut,
    MyCommittee,
    MyCommitteeRow,
    MyDefenseMember,
    MyDefenseOut,
    MyDefenseResult,
    MyDefenseSchedule,
    MyScore,
    QuyenBaoCaoCuoiOut,
    ScheduleRow,
    ScoreRequest,
    ScoringDetail,
)
from app.schemas.topics import PersonRef
from app.services import archive, document_check, documents, notifications
from app.services.documents import ValidatedFile, to_document_out

_TOPIC_NOT_FOUND_DETAIL = "Không tìm thấy đề tài"
_SUBMIT_FORBIDDEN_DETAIL = "Bạn không có quyền nộp báo cáo cuối cho đề tài này"
_NOT_ASSIGNED_DETAIL = "Đề tài chưa được phân công GVHD"
_OUTLINE_NOT_APPROVED_DETAIL = "Đề cương chưa được duyệt — chưa thể nộp báo cáo cuối (UC4.1)"
_ALREADY_SCHEDULED_SELF_DETAIL = "Bạn đã được xếp lịch bảo vệ — không thể nộp lại báo cáo cuối"
_SUBMIT_RACE_DETAIL = "Đang có một lần nộp khác, vui lòng thử lại"
_VIEW_FORBIDDEN_DETAIL = "Bạn không có quyền xem báo cáo cuối này"

_MEMBER_COUNT_DETAIL = "Hội đồng phải có từ 3 đến 5 thành viên"
_MEMBER_DUPLICATE_DETAIL = "Một giảng viên không được xuất hiện hai lần trong cùng hội đồng"
_CHU_TICH_REQUIRED_DETAIL = "Hội đồng phải có đúng một Chủ tịch"
_THU_KY_MAX_DETAIL = "Hội đồng chỉ có tối đa một Thư ký"
_GV_INVALID_DETAIL = "Giảng viên không tồn tại hoặc đã bị khóa"

_COMMITTEE_NOT_FOUND_DETAIL = "Không tìm thấy hội đồng"
_COMMITTEE_HAS_SCORES_DETAIL = "Hội đồng đã có điểm — không thể sửa thành viên hoặc lịch"
_COMMITTEE_HAS_SCORES_SCHEDULE_DETAIL = (
    "Hội đồng đã có điểm — không thể đổi ngày, giờ hoặc phòng bảo vệ"
)
_COMMITTEE_HAS_STUDENTS_DETAIL = "Hội đồng đã có sinh viên — gỡ sinh viên trước khi xóa"

_SCHEDULE_NOT_FOUND_DETAIL = "Không tìm thấy lịch bảo vệ"
_NOT_ELIGIBLE_NO_REPORT_DETAIL = "Sinh viên chưa nộp báo cáo cuối"
_ALREADY_SCHEDULED_ELSEWHERE_DETAIL = "Sinh viên đã được xếp vào một hội đồng khác"
_SCHEDULE_LOCKED_DETAIL = "Lịch bảo vệ đã có điểm hoặc đã chốt kết quả — không thể gỡ khỏi lịch"

_NOT_MEMBER_DETAIL = "Bạn không thuộc hội đồng của sinh viên này (UC4.3 - E1)"
_SCORE_FINALIZED_DETAIL = "Kết quả đã được chốt — không thể sửa điểm"
_FINALIZED_DETAIL = "Kết quả đã được chốt"
_FINALIZED_REASON = "Kết quả đã chốt"
_BO_MON_NO_SCORE_REASON = "Chỉ thành viên hội đồng được chấm điểm"
_ARCHIVE_DUPLICATE_DETAIL = "Đề tài đã có trong kho đồ án"


def _not_yet_detail(ngay: date) -> str:
    return f"Chưa đến ngày bảo vệ ({ngay.strftime('%d/%m/%Y')})"


def _member_scored_detail(names: list[str]) -> str:
    return (
        f"Không thể thay {', '.join(names)}: giảng viên đã chấm điểm trong hội đồng này"
        " — chỉ thay được thành viên chưa chấm"
    )


def _not_enough_scores_detail(n: int, m: int) -> str:
    return f"Chưa đủ thành viên hội đồng chấm điểm ({n}/{m})"


def _person_ref(entity, ma_attr: str) -> PersonRef | None:
    if entity is None:
        return None
    return PersonRef(id=entity.id, ho_ten=entity.ho_ten or "", ma=getattr(entity, ma_attr, None))


def _gvhd_exclusion_detail(sv: SinhVien | None) -> str:
    ho_ten = sv.ho_ten if sv is not None else ""
    ma = sv.ma_so_sinh_vien if sv is not None else ""
    return (
        f"GVHD của sinh viên {ho_ten} ({ma}) không được ngồi hội đồng của sinh viên mình hướng dẫn (D-06)"
    )


def _format_dt(ngay: date, gio: time) -> str:
    return f"{ngay.strftime('%d/%m/%Y')} {gio.strftime('%H:%M')}"


def _compute_slot_time(gio_bao_ve: time, thu_tu: int | None) -> str:
    base = datetime.combine(date(2000, 1, 1), gio_bao_ve)
    offset_minutes = SLOT_MINUTES * ((thu_tu or 1) - 1)
    slot = base + timedelta(minutes=offset_minutes)
    return slot.strftime("%H:%M")


# ---------------------------------------------------------------------------
# UC4.1 — báo cáo cuối
# ---------------------------------------------------------------------------


def _can_view_final_report(db: Session, user: CurrentUser, topic: DeTai) -> bool:
    """T-03-17/T-03-20: SV chủ đề tài, GVHD, Bộ môn hoặc thành viên hội đồng
    đang giữ lịch bảo vệ của đề tài (cùng quy tắc documents.can_view cho
    BAO_CAO_CUOI — DEFN-03)."""
    if user.vai_tro == VaiTro.BO_MON:
        return True
    if user.vai_tro == VaiTro.SINH_VIEN and user.sinh_vien_id is not None:
        return topic.sinh_vien_id == user.sinh_vien_id
    if user.vai_tro == VaiTro.GIANG_VIEN and user.giang_vien_id is not None:
        if topic.giang_vien_id == user.giang_vien_id:
            return True
        return documents.is_committee_member_for_topic(db, user.giang_vien_id, topic.id)
    return False


def _get_topic_locked_or_404(db: Session, de_tai_id: int) -> DeTai:
    topic = db.execute(
        select(DeTai).where(DeTai.id == de_tai_id).with_for_update()
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    return topic


def submit_final_report(
    db: Session, user: CurrentUser, de_tai_id: int, vf: ValidatedFile
) -> tuple[FinalReportDetail, int]:
    """UC4.1/D-01..D-04: khóa dòng de_tai; chỉ SV chủ đề tài có GVHD và đề
    cương Đã duyệt mới nộp được; một khi đã xếp lịch bảo vệ, không nộp lại
    được nữa (D-02: mỗi lần nộp vẫn là một phiên bản mới, không đè)."""
    topic = _get_topic_locked_or_404(db, de_tai_id)
    if user.sinh_vien_id is None or topic.sinh_vien_id != user.sinh_vien_id:
        raise HTTPException(status_code=403, detail=_SUBMIT_FORBIDDEN_DETAIL)
    if topic.giang_vien_id is None:
        raise HTTPException(status_code=409, detail=_NOT_ASSIGNED_DETAIL)

    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    if de_cuong is None or de_cuong.trang_thai != DC_DA_DUYET:
        raise HTTPException(status_code=409, detail=_OUTLINE_NOT_APPROVED_DETAIL)

    already_scheduled = db.execute(
        select(func.count()).select_from(LichBaoVe).where(LichBaoVe.sinh_vien_id == user.sinh_vien_id)
    ).scalar_one()
    if already_scheduled > 0:
        raise HTTPException(status_code=409, detail=_ALREADY_SCHEDULED_SELF_DETAIL)

    doc = None
    ket_qua = None
    try:
        doc = documents.store(db, de_tai_id=de_tai_id, loai=LOAI_BAO_CAO_CUOI, vf=vf)
        ket_qua = document_check.create_pending(db, doc)
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

    return get_final_report(db, user, de_tai_id), ket_qua.id


def get_final_report(db: Session, user: CurrentUser, de_tai_id: int) -> FinalReportDetail:
    topic = db.execute(
        select(DeTai)
        .where(DeTai.id == de_tai_id)
        .options(selectinload(DeTai.sinh_vien), selectinload(DeTai.giang_vien))
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    if not _can_view_final_report(db, user, topic):
        raise HTTPException(status_code=403, detail=_VIEW_FORBIDDEN_DETAIL)

    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    trang_thai_de_cuong = de_cuong.trang_thai if de_cuong is not None else DC_CHUA_NOP

    docs = (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == de_tai_id)
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
        )
        .scalars()
        .all()
    )

    phien_ban: list[FinalReportVersion] = []
    for doc in docs:
        ket_qua = doc.ket_qua_kiem_tra
        if ket_qua is not None:
            document_check.expire_if_stale(db, ket_qua)
        kiem_tra = document_check.summary(ket_qua) if ket_qua is not None else None
        phien_ban.append(FinalReportVersion(tai_lieu=to_document_out(doc), kiem_tra=kiem_tra))

    da_xep_lich = (
        db.execute(
            select(func.count()).select_from(LichBaoVe).where(LichBaoVe.de_tai_id == de_tai_id)
        ).scalar_one()
        > 0
    )

    nop = (
        user.sinh_vien_id is not None
        and topic.sinh_vien_id == user.sinh_vien_id
        and topic.giang_vien_id is not None
        and trang_thai_de_cuong == DC_DA_DUYET
        and not da_xep_lich
    )

    return FinalReportDetail(
        de_tai_id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        trang_thai_de_cuong=trang_thai_de_cuong,
        da_xep_lich=da_xep_lich,
        phien_ban=phien_ban,
        quyen=QuyenBaoCaoCuoiOut(nop=nop),
    )


# ---------------------------------------------------------------------------
# UC4.2 — hội đồng & lịch bảo vệ
# ---------------------------------------------------------------------------


def _validate_members(
    db: Session, thanh_vien: list[MemberIn], keep_ids: frozenset[int] = frozenset()
) -> None:
    """`keep_ids`: thành viên ĐANG có trong hội đồng (khi sửa) — vẫn được giữ
    nếu tài khoản đã bị khóa sau khi phân công (WR-01: điểm họ đã chấm vẫn
    hợp lệ); GV MỚI thêm vào luôn phải còn hoạt động."""
    if not (3 <= len(thanh_vien) <= 5):
        raise HTTPException(status_code=422, detail=_MEMBER_COUNT_DETAIL)

    gv_ids = [m.giang_vien_id for m in thanh_vien]
    if len(set(gv_ids)) != len(gv_ids):
        raise HTTPException(status_code=422, detail=_MEMBER_DUPLICATE_DETAIL)

    chu_tich_count = sum(1 for m in thanh_vien if m.vai_tro == CHU_TICH)
    if chu_tich_count != 1:
        raise HTTPException(status_code=422, detail=_CHU_TICH_REQUIRED_DETAIL)

    thu_ky_count = sum(1 for m in thanh_vien if m.vai_tro == THU_KY)
    if thu_ky_count > 1:
        raise HTTPException(status_code=422, detail=_THU_KY_MAX_DETAIL)

    valid_ids = set(
        db.execute(
            select(GiangVien.id)
            .join(TaiKhoan, TaiKhoan.id == GiangVien.tai_khoan_id)
            .where(GiangVien.id.in_(gv_ids))
            .where(TaiKhoan.bi_khoa.is_(False) | GiangVien.id.in_(keep_ids))
        )
        .scalars()
        .all()
    )
    if valid_ids != set(gv_ids):
        raise HTTPException(status_code=422, detail=_GV_INVALID_DETAIL)


def _scheduled_rows_with_topic_sv(db: Session, hoi_dong_id: int):
    return db.execute(
        select(LichBaoVe, DeTai, SinhVien)
        .join(DeTai, DeTai.id == LichBaoVe.de_tai_id)
        .join(SinhVien, SinhVien.id == LichBaoVe.sinh_vien_id)
        .where(LichBaoVe.hoi_dong_id == hoi_dong_id)
    ).all()


def create_committee(db: Session, payload: CommitteeIn) -> CommitteeOut:
    _validate_members(db, payload.thanh_vien)

    hoi_dong = HoiDong(
        ten_hoi_dong=payload.ten_hoi_dong,
        ngay_bao_ve=payload.ngay_bao_ve,
        gio_bao_ve=payload.gio_bao_ve,
        phong=payload.phong,
    )
    db.add(hoi_dong)
    db.flush()

    for m in payload.thanh_vien:
        db.add(
            ThanhVienHoiDong(
                hoi_dong_id=hoi_dong.id, giang_vien_id=m.giang_vien_id, vai_tro=m.vai_tro
            )
        )
    db.flush()

    when = _format_dt(hoi_dong.ngay_bao_ve, hoi_dong.gio_bao_ve)
    for m in payload.thanh_vien:
        gv = db.get(GiangVien, m.giang_vien_id)
        if gv is not None:
            notifications.create(
                db,
                gv.tai_khoan_id,
                HOI_DONG_PHAN_CONG,
                f"Bạn được phân vào {hoi_dong.ten_hoi_dong} — {when}, phòng {hoi_dong.phong}",
                lien_ket="/cham-diem",
            )
    db.commit()
    return get_committee(db, hoi_dong.id)


def update_committee(db: Session, hoi_dong_id: int, payload: CommitteeIn) -> CommitteeOut:
    """Khóa dòng hội đồng (score() giữ khóa CHIA SẺ trên cùng dòng — WR-02).
    WR-01: khi hội đồng ĐÃ có điểm vẫn cho Bộ môn thay thành viên CHƯA chấm
    (vd. GV bị khóa/vắng mặt — nếu không, finalize kẹt vĩnh viễn ở "chưa đủ
    điểm"); thành viên đã chấm không gỡ được, ngày/giờ/phòng không đổi được."""
    hoi_dong = db.execute(
        select(HoiDong).where(HoiDong.id == hoi_dong_id).with_for_update()
    ).scalar_one_or_none()
    if hoi_dong is None:
        raise HTTPException(status_code=404, detail=_COMMITTEE_NOT_FOUND_DETAIL)

    # Đọc có khóa (đọc bản commit mới nhất, không phải snapshot đầu request).
    existing_members = (
        db.execute(
            select(ThanhVienHoiDong)
            .where(ThanhVienHoiDong.hoi_dong_id == hoi_dong_id)
            .with_for_update()
        )
        .scalars()
        .all()
    )
    existing_by_gv = {m.giang_vien_id: m for m in existing_members}

    _validate_members(db, payload.thanh_vien, keep_ids=frozenset(existing_by_gv))

    new_gv_ids = {m.giang_vien_id for m in payload.thanh_vien}
    scheduled = _scheduled_rows_with_topic_sv(db, hoi_dong_id)
    for _lich, de_tai, sv in scheduled:
        if de_tai.giang_vien_id is not None and de_tai.giang_vien_id in new_gv_ids:
            raise HTTPException(status_code=409, detail=_gvhd_exclusion_detail(sv))

    schedule_changed = (
        hoi_dong.ngay_bao_ve != payload.ngay_bao_ve
        or hoi_dong.gio_bao_ve != payload.gio_bao_ve
        or hoi_dong.phong != payload.phong
    )

    scorer_ids = set(
        db.execute(
            select(DiemBaoVe.giang_vien_id)
            .join(LichBaoVe, LichBaoVe.id == DiemBaoVe.lich_bao_ve_id)
            .where(LichBaoVe.hoi_dong_id == hoi_dong_id)
            .with_for_update(read=True)
        )
        .scalars()
        .all()
    )
    if scorer_ids:
        if schedule_changed:
            raise HTTPException(status_code=409, detail=_COMMITTEE_HAS_SCORES_SCHEDULE_DETAIL)
        scored_removed = sorted((existing_by_gv.keys() - new_gv_ids) & scorer_ids)
        if scored_removed:
            names = [
                (gv.ho_ten if gv is not None and gv.ho_ten else f"GV #{gv_id}")
                for gv_id in scored_removed
                for gv in [db.get(GiangVien, gv_id)]
            ]
            raise HTTPException(status_code=409, detail=_member_scored_detail(names))

    hoi_dong.ten_hoi_dong = payload.ten_hoi_dong
    hoi_dong.ngay_bao_ve = payload.ngay_bao_ve
    hoi_dong.gio_bao_ve = payload.gio_bao_ve
    hoi_dong.phong = payload.phong

    added_gv_ids = new_gv_ids - existing_by_gv.keys()
    removed_gv_ids = existing_by_gv.keys() - new_gv_ids

    for gv_id in removed_gv_ids:
        db.delete(existing_by_gv[gv_id])
    for m in payload.thanh_vien:
        if m.giang_vien_id in existing_by_gv:
            existing_by_gv[m.giang_vien_id].vai_tro = m.vai_tro
        else:
            db.add(
                ThanhVienHoiDong(
                    hoi_dong_id=hoi_dong_id, giang_vien_id=m.giang_vien_id, vai_tro=m.vai_tro
                )
            )
    db.flush()

    when = _format_dt(hoi_dong.ngay_bao_ve, hoi_dong.gio_bao_ve)
    for gv_id in added_gv_ids:
        gv = db.get(GiangVien, gv_id)
        if gv is not None:
            notifications.create(
                db,
                gv.tai_khoan_id,
                HOI_DONG_PHAN_CONG,
                f"Bạn được phân vào {hoi_dong.ten_hoi_dong} — {when}, phòng {hoi_dong.phong}",
                lien_ket="/cham-diem",
            )

    if schedule_changed:
        for m in payload.thanh_vien:
            gv = db.get(GiangVien, m.giang_vien_id)
            if gv is not None:
                notifications.create(
                    db,
                    gv.tai_khoan_id,
                    LICH_BAO_VE,
                    f"Lịch bảo vệ thay đổi: {hoi_dong.ten_hoi_dong} — {when}, phòng {hoi_dong.phong}",
                    lien_ket="/cham-diem",
                )
        for lich, _de_tai, sv in scheduled:
            gio_du_kien = _compute_slot_time(hoi_dong.gio_bao_ve, lich.thu_tu)
            notifications.create(
                db,
                sv.tai_khoan_id,
                LICH_BAO_VE,
                (
                    f"Lịch bảo vệ thay đổi: {hoi_dong.ten_hoi_dong} — "
                    f"{hoi_dong.ngay_bao_ve.strftime('%d/%m/%Y')} {gio_du_kien}, phòng {hoi_dong.phong}"
                ),
                lien_ket="/bao-ve",
            )

    db.commit()
    return get_committee(db, hoi_dong_id)


def delete_committee(db: Session, hoi_dong_id: int) -> None:
    hoi_dong = db.get(HoiDong, hoi_dong_id)
    if hoi_dong is None:
        raise HTTPException(status_code=404, detail=_COMMITTEE_NOT_FOUND_DETAIL)

    has_students = db.execute(
        select(func.count()).select_from(LichBaoVe).where(LichBaoVe.hoi_dong_id == hoi_dong_id)
    ).scalar_one()
    if has_students > 0:
        raise HTTPException(status_code=409, detail=_COMMITTEE_HAS_STUDENTS_DETAIL)

    for member in list(hoi_dong.thanh_vien):
        db.delete(member)
    db.delete(hoi_dong)
    db.commit()


def list_committees(db: Session) -> list[CommitteeListItem]:
    rows = (
        db.execute(
            select(HoiDong)
            .order_by(HoiDong.ngay_bao_ve, HoiDong.gio_bao_ve)
            .options(selectinload(HoiDong.thanh_vien).selectinload(ThanhVienHoiDong.giang_vien))
        )
        .scalars()
        .all()
    )

    ids = [h.id for h in rows]
    student_counts: dict[int, int] = {}
    if ids:
        count_rows = db.execute(
            select(LichBaoVe.hoi_dong_id, func.count())
            .where(LichBaoVe.hoi_dong_id.in_(ids))
            .group_by(LichBaoVe.hoi_dong_id)
        ).all()
        student_counts = {hoi_dong_id: count for hoi_dong_id, count in count_rows}

    items: list[CommitteeListItem] = []
    for h in rows:
        chu_tich_member = next((m for m in h.thanh_vien if m.vai_tro == CHU_TICH), None)
        items.append(
            CommitteeListItem(
                id=h.id,
                ten_hoi_dong=h.ten_hoi_dong,
                ngay_bao_ve=h.ngay_bao_ve,
                gio_bao_ve=h.gio_bao_ve,
                phong=h.phong,
                chu_tich=(
                    _person_ref(chu_tich_member.giang_vien, "ma_giang_vien")
                    if chu_tich_member is not None
                    else None
                ),
                so_thanh_vien=len(h.thanh_vien),
                so_sinh_vien=student_counts.get(h.id, 0),
            )
        )
    return items


def _latest_final_report_or_none(db: Session, de_tai_id: int) -> TaiLieuDoAn | None:
    return (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == de_tai_id)
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .limit(1)
            .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
        )
        .scalars()
        .first()
    )


def get_committee(db: Session, hoi_dong_id: int) -> CommitteeOut:
    """Không N+1: selectinload thành viên/lịch, một truy vấn cho số điểm đã
    chấm mỗi lịch, một truy vấn cho phiên bản báo cáo cuối mới nhất mỗi đề tài."""
    hoi_dong = db.execute(
        select(HoiDong)
        .where(HoiDong.id == hoi_dong_id)
        .options(
            selectinload(HoiDong.thanh_vien).selectinload(ThanhVienHoiDong.giang_vien),
            selectinload(HoiDong.lich).selectinload(LichBaoVe.sinh_vien),
            selectinload(HoiDong.lich).selectinload(LichBaoVe.de_tai).selectinload(DeTai.giang_vien),
        )
    ).scalar_one_or_none()
    if hoi_dong is None:
        raise HTTPException(status_code=404, detail=_COMMITTEE_NOT_FOUND_DETAIL)

    so_thanh_vien = len(hoi_dong.thanh_vien)
    lich_ids = [l.id for l in hoi_dong.lich]
    de_tai_ids = [l.de_tai_id for l in hoi_dong.lich]

    score_by_lich: dict[int, tuple[int, float | None]] = {}
    if lich_ids:
        score_rows = db.execute(
            select(DiemBaoVe.lich_bao_ve_id, func.count(), func.avg(DiemBaoVe.diem))
            .where(DiemBaoVe.lich_bao_ve_id.in_(lich_ids))
            .group_by(DiemBaoVe.lich_bao_ve_id)
        ).all()
        score_by_lich = {
            lich_id: (count, float(avg) if avg is not None else None)
            for lich_id, count, avg in score_rows
        }

    latest_docs: dict[int, TaiLieuDoAn] = {}
    if de_tai_ids:
        latest_sub = (
            select(TaiLieuDoAn.de_tai_id, func.max(TaiLieuDoAn.so_phien_ban).label("max_ver"))
            .where(TaiLieuDoAn.de_tai_id.in_(de_tai_ids))
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
            .group_by(TaiLieuDoAn.de_tai_id)
            .subquery()
        )
        docs = (
            db.execute(
                select(TaiLieuDoAn)
                .join(
                    latest_sub,
                    (TaiLieuDoAn.de_tai_id == latest_sub.c.de_tai_id)
                    & (TaiLieuDoAn.so_phien_ban == latest_sub.c.max_ver),
                )
                .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
            )
            .scalars()
            .all()
        )
        latest_docs = {d.de_tai_id: d for d in docs}

    lich_out: list[ScheduleRow] = []
    for l in hoi_dong.lich:
        so_da_cham, diem_tb = score_by_lich.get(l.id, (0, None))
        diem_tam_tinh = (
            diem_tb if so_da_cham == so_thanh_vien and so_thanh_vien > 0 and diem_tb is not None else None
        )
        doc = latest_docs.get(l.de_tai_id)
        kiem_tra = None
        if doc is not None and doc.ket_qua_kiem_tra is not None:
            document_check.expire_if_stale(db, doc.ket_qua_kiem_tra)
            kiem_tra = document_check.summary(doc.ket_qua_kiem_tra)
        lich_out.append(
            ScheduleRow(
                id=l.id,
                thu_tu=l.thu_tu,
                gio_du_kien=_compute_slot_time(hoi_dong.gio_bao_ve, l.thu_tu),
                sinh_vien=_person_ref(l.sinh_vien, "ma_so_sinh_vien"),
                de_tai_id=l.de_tai_id,
                ten_de_tai=l.de_tai.ten_de_tai,
                giang_vien_huong_dan=_person_ref(l.de_tai.giang_vien, "ma_giang_vien"),
                so_da_cham=so_da_cham,
                so_thanh_vien=so_thanh_vien,
                diem_tam_tinh=diem_tam_tinh,
                diem_trung_binh=float(l.diem_trung_binh) if l.diem_trung_binh is not None else None,
                da_chot=l.da_chot,
                bao_cao_cuoi=to_document_out(doc) if doc is not None else None,
                kiem_tra=kiem_tra,
            )
        )

    members_out = [
        MemberOut(
            giang_vien=_person_ref(m.giang_vien, "ma_giang_vien"),
            hoc_vi=m.giang_vien.hoc_vi if m.giang_vien is not None else None,
            vai_tro=m.vai_tro,
        )
        for m in hoi_dong.thanh_vien
    ]

    return CommitteeOut(
        id=hoi_dong.id,
        ten_hoi_dong=hoi_dong.ten_hoi_dong,
        ngay_bao_ve=hoi_dong.ngay_bao_ve,
        gio_bao_ve=hoi_dong.gio_bao_ve,
        phong=hoi_dong.phong,
        thanh_vien=members_out,
        lich=lich_out,
    )


def eligible_students(db: Session) -> list[EligibleStudent]:
    """UC4.2: đề tài Đã phân công, SV chưa được xếp lịch, đã có ít nhất một
    phiên bản báo cáo cuối."""
    scheduled_sv_ids = select(LichBaoVe.sinh_vien_id)
    topics = (
        db.execute(
            select(DeTai)
            .where(DeTai.trang_thai == DA_PHAN_CONG)
            .where(DeTai.sinh_vien_id.is_not(None))
            .where(~DeTai.sinh_vien_id.in_(scheduled_sv_ids))
            .order_by(DeTai.id)
            .options(selectinload(DeTai.sinh_vien), selectinload(DeTai.giang_vien))
        )
        .scalars()
        .all()
    )

    de_tai_ids = [t.id for t in topics]
    latest_docs: dict[int, TaiLieuDoAn] = {}
    if de_tai_ids:
        latest_sub = (
            select(TaiLieuDoAn.de_tai_id, func.max(TaiLieuDoAn.so_phien_ban).label("max_ver"))
            .where(TaiLieuDoAn.de_tai_id.in_(de_tai_ids))
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
            .group_by(TaiLieuDoAn.de_tai_id)
            .subquery()
        )
        docs = (
            db.execute(
                select(TaiLieuDoAn)
                .join(
                    latest_sub,
                    (TaiLieuDoAn.de_tai_id == latest_sub.c.de_tai_id)
                    & (TaiLieuDoAn.so_phien_ban == latest_sub.c.max_ver),
                )
                .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
            )
            .scalars()
            .all()
        )
        latest_docs = {d.de_tai_id: d for d in docs}

    items: list[EligibleStudent] = []
    for t in topics:
        doc = latest_docs.get(t.id)
        if doc is None:
            continue
        kiem_tra = None
        if doc.ket_qua_kiem_tra is not None:
            document_check.expire_if_stale(db, doc.ket_qua_kiem_tra)
            kiem_tra = document_check.summary(doc.ket_qua_kiem_tra)
        items.append(
            EligibleStudent(
                de_tai_id=t.id,
                ten_de_tai=t.ten_de_tai,
                sinh_vien=_person_ref(t.sinh_vien, "ma_so_sinh_vien"),
                giang_vien_huong_dan=_person_ref(t.giang_vien, "ma_giang_vien"),
                giang_vien_id=t.giang_vien_id,
                bao_cao_cuoi=to_document_out(doc),
                kiem_tra=kiem_tra,
            )
        )
    return items


def _build_schedule_row(db: Session, lich_id: int) -> ScheduleRow:
    lich = db.execute(
        select(LichBaoVe)
        .where(LichBaoVe.id == lich_id)
        .options(
            selectinload(LichBaoVe.hoi_dong),
            selectinload(LichBaoVe.sinh_vien),
            selectinload(LichBaoVe.de_tai).selectinload(DeTai.giang_vien),
        )
    ).scalar_one()

    so_thanh_vien = db.execute(
        select(func.count())
        .select_from(ThanhVienHoiDong)
        .where(ThanhVienHoiDong.hoi_dong_id == lich.hoi_dong_id)
    ).scalar_one()
    so_da_cham, diem_tb = db.execute(
        select(func.count(), func.avg(DiemBaoVe.diem)).where(DiemBaoVe.lich_bao_ve_id == lich_id)
    ).one()
    diem_tam_tinh = (
        float(diem_tb)
        if so_da_cham == so_thanh_vien and so_thanh_vien > 0 and diem_tb is not None
        else None
    )

    doc = _latest_final_report_or_none(db, lich.de_tai_id)
    kiem_tra = None
    if doc is not None and doc.ket_qua_kiem_tra is not None:
        document_check.expire_if_stale(db, doc.ket_qua_kiem_tra)
        kiem_tra = document_check.summary(doc.ket_qua_kiem_tra)

    return ScheduleRow(
        id=lich.id,
        thu_tu=lich.thu_tu,
        gio_du_kien=_compute_slot_time(lich.hoi_dong.gio_bao_ve, lich.thu_tu),
        sinh_vien=_person_ref(lich.sinh_vien, "ma_so_sinh_vien"),
        de_tai_id=lich.de_tai_id,
        ten_de_tai=lich.de_tai.ten_de_tai,
        giang_vien_huong_dan=_person_ref(lich.de_tai.giang_vien, "ma_giang_vien"),
        so_da_cham=so_da_cham,
        so_thanh_vien=so_thanh_vien,
        diem_tam_tinh=diem_tam_tinh,
        diem_trung_binh=float(lich.diem_trung_binh) if lich.diem_trung_binh is not None else None,
        da_chot=lich.da_chot,
        bao_cao_cuoi=to_document_out(doc) if doc is not None else None,
        kiem_tra=kiem_tra,
    )


def add_schedule(db: Session, hoi_dong_id: int, de_tai_id: int) -> ScheduleRow:
    """UC4.2/D-06: khóa dòng hội đồng (serialize với sửa thành viên); từ
    chối khi đề tài chưa đủ điều kiện, khi GVHD của SV đã là thành viên hội
    đồng này, hoặc khi hội đồng đã có điểm; UNIQUE(sinh_vien_id) là tuyến
    phòng thủ cuối cùng khi hai lần xếp lịch đua nhau (§3.2.5.c)."""
    hoi_dong = db.execute(
        select(HoiDong).where(HoiDong.id == hoi_dong_id).with_for_update()
    ).scalar_one_or_none()
    if hoi_dong is None:
        raise HTTPException(status_code=404, detail=_COMMITTEE_NOT_FOUND_DETAIL)

    topic = db.execute(
        select(DeTai).where(DeTai.id == de_tai_id).options(selectinload(DeTai.sinh_vien))
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND_DETAIL)
    if topic.giang_vien_id is None:
        raise HTTPException(status_code=409, detail=_NOT_ASSIGNED_DETAIL)

    has_report = db.execute(
        select(func.count())
        .select_from(TaiLieuDoAn)
        .where(TaiLieuDoAn.de_tai_id == de_tai_id)
        .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
    ).scalar_one()
    if has_report == 0:
        raise HTTPException(status_code=409, detail=_NOT_ELIGIBLE_NO_REPORT_DETAIL)

    is_gvhd_member = db.execute(
        select(func.count())
        .select_from(ThanhVienHoiDong)
        .where(ThanhVienHoiDong.hoi_dong_id == hoi_dong_id)
        .where(ThanhVienHoiDong.giang_vien_id == topic.giang_vien_id)
    ).scalar_one()
    if is_gvhd_member > 0:
        raise HTTPException(status_code=409, detail=_gvhd_exclusion_detail(topic.sinh_vien))

    has_scores = db.execute(
        select(func.count())
        .select_from(DiemBaoVe)
        .join(LichBaoVe, LichBaoVe.id == DiemBaoVe.lich_bao_ve_id)
        .where(LichBaoVe.hoi_dong_id == hoi_dong_id)
    ).scalar_one()
    if has_scores > 0:
        raise HTTPException(status_code=409, detail=_COMMITTEE_HAS_SCORES_DETAIL)

    max_thu_tu = db.execute(
        select(func.coalesce(func.max(LichBaoVe.thu_tu), 0)).where(
            LichBaoVe.hoi_dong_id == hoi_dong_id
        )
    ).scalar_one()

    lich = LichBaoVe(
        hoi_dong_id=hoi_dong_id,
        de_tai_id=de_tai_id,
        sinh_vien_id=topic.sinh_vien_id,
        thu_tu=int(max_thu_tu) + 1,
    )
    db.add(lich)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_ALREADY_SCHEDULED_ELSEWHERE_DETAIL) from None

    if topic.sinh_vien is not None:
        gio_du_kien = _compute_slot_time(hoi_dong.gio_bao_ve, lich.thu_tu)
        notifications.create(
            db,
            topic.sinh_vien.tai_khoan_id,
            LICH_BAO_VE,
            (
                f"Bạn đã được xếp lịch bảo vệ: {hoi_dong.ten_hoi_dong} — "
                f"{hoi_dong.ngay_bao_ve.strftime('%d/%m/%Y')} {gio_du_kien}, phòng {hoi_dong.phong}"
            ),
            lien_ket="/bao-ve",
        )

    db.commit()
    return _build_schedule_row(db, lich.id)


def remove_schedule(db: Session, lich_bao_ve_id: int) -> None:
    lich = db.execute(
        select(LichBaoVe).where(LichBaoVe.id == lich_bao_ve_id).with_for_update()
    ).scalar_one_or_none()
    if lich is None:
        raise HTTPException(status_code=404, detail=_SCHEDULE_NOT_FOUND_DETAIL)

    has_score = db.execute(
        select(func.count()).select_from(DiemBaoVe).where(DiemBaoVe.lich_bao_ve_id == lich_bao_ve_id)
    ).scalar_one()
    if has_score > 0 or lich.da_chot:
        raise HTTPException(status_code=409, detail=_SCHEDULE_LOCKED_DETAIL)

    hoi_dong_id = lich.hoi_dong_id
    sinh_vien = db.get(SinhVien, lich.sinh_vien_id)
    db.delete(lich)
    db.flush()

    remaining = (
        db.execute(
            select(LichBaoVe).where(LichBaoVe.hoi_dong_id == hoi_dong_id).order_by(LichBaoVe.thu_tu)
        )
        .scalars()
        .all()
    )
    for idx, row in enumerate(remaining, start=1):
        row.thu_tu = idx
    db.flush()

    if sinh_vien is not None:
        notifications.create(
            db,
            sinh_vien.tai_khoan_id,
            LICH_BAO_VE,
            "Lịch bảo vệ của bạn đã bị hủy — chờ Bộ môn xếp lại",
            lien_ket="/bao-ve",
        )
    db.commit()


# ---------------------------------------------------------------------------
# UC4.3 — chấm điểm (DEFN-03, D-06)
# ---------------------------------------------------------------------------

_VAI_TRO_ORDER = {CHU_TICH: 0, THU_KY: 1}


def _is_member(db: Session, hoi_dong_id: int, giang_vien_id: int | None) -> bool:
    if giang_vien_id is None:
        return False
    count = db.execute(
        select(func.count())
        .select_from(ThanhVienHoiDong)
        .where(ThanhVienHoiDong.hoi_dong_id == hoi_dong_id)
        .where(ThanhVienHoiDong.giang_vien_id == giang_vien_id)
    ).scalar_one()
    return count > 0


def my_committees(db: Session, user: CurrentUser) -> list[MyCommittee]:
    """MH-12 "Hội đồng của tôi": chỉ hội đồng người gọi là thành viên; mỗi SV
    kèm CHỈ điểm của chính người gọi (không bao giờ điểm thành viên khác)."""
    if user.giang_vien_id is None:
        return []
    memberships = (
        db.execute(
            select(ThanhVienHoiDong)
            .join(HoiDong, HoiDong.id == ThanhVienHoiDong.hoi_dong_id)
            .where(ThanhVienHoiDong.giang_vien_id == user.giang_vien_id)
            .order_by(HoiDong.ngay_bao_ve, HoiDong.gio_bao_ve, HoiDong.id)
            .options(
                selectinload(ThanhVienHoiDong.hoi_dong)
                .selectinload(HoiDong.lich)
                .selectinload(LichBaoVe.sinh_vien),
                selectinload(ThanhVienHoiDong.hoi_dong)
                .selectinload(HoiDong.lich)
                .selectinload(LichBaoVe.de_tai),
            )
        )
        .scalars()
        .all()
    )

    lich_ids = [l.id for m in memberships for l in m.hoi_dong.lich]
    my_scores: dict[int, Decimal] = {}
    if lich_ids:
        rows = db.execute(
            select(DiemBaoVe.lich_bao_ve_id, DiemBaoVe.diem)
            .where(DiemBaoVe.lich_bao_ve_id.in_(lich_ids))
            .where(DiemBaoVe.giang_vien_id == user.giang_vien_id)
        ).all()
        my_scores = {lich_id: diem for lich_id, diem in rows}

    result: list[MyCommittee] = []
    for m in memberships:
        hd = m.hoi_dong
        result.append(
            MyCommittee(
                id=hd.id,
                ten_hoi_dong=hd.ten_hoi_dong,
                ngay_bao_ve=hd.ngay_bao_ve,
                gio_bao_ve=hd.gio_bao_ve,
                phong=hd.phong,
                vai_tro_cua_toi=m.vai_tro,
                lich=[
                    MyCommitteeRow(
                        id=l.id,
                        thu_tu=l.thu_tu,
                        gio_du_kien=_compute_slot_time(hd.gio_bao_ve, l.thu_tu),
                        sinh_vien=_person_ref(l.sinh_vien, "ma_so_sinh_vien"),
                        ten_de_tai=l.de_tai.ten_de_tai,
                        diem_cua_toi=float(my_scores[l.id]) if l.id in my_scores else None,
                        da_chot=l.da_chot,
                    )
                    for l in hd.lich
                ],
            )
        )
    return result


def get_schedule_for_scoring(db: Session, user: CurrentUser, lich_id: int) -> ScoringDetail:
    """MH-12 "Chấm điểm - {SV}": GV phải là thành viên hội đồng của lịch này
    (403 UC4.3 E1); Bộ môn xem được nhưng không chấm."""
    lich = db.execute(
        select(LichBaoVe)
        .where(LichBaoVe.id == lich_id)
        .options(
            selectinload(LichBaoVe.hoi_dong),
            selectinload(LichBaoVe.sinh_vien),
            selectinload(LichBaoVe.de_tai),
        )
    ).scalar_one_or_none()
    if lich is None:
        raise HTTPException(status_code=404, detail=_SCHEDULE_NOT_FOUND_DETAIL)

    is_gv = user.vai_tro == VaiTro.GIANG_VIEN
    if is_gv and not _is_member(db, lich.hoi_dong_id, user.giang_vien_id):
        raise HTTPException(status_code=403, detail=_NOT_MEMBER_DETAIL)
    if not is_gv and user.vai_tro != VaiTro.BO_MON:
        raise HTTPException(status_code=403, detail=_NOT_MEMBER_DETAIL)

    hd = lich.hoi_dong
    doc = _latest_final_report_or_none(db, lich.de_tai_id)
    kiem_tra = None
    if doc is not None and doc.ket_qua_kiem_tra is not None:
        document_check.expire_if_stale(db, doc.ket_qua_kiem_tra)
        kiem_tra = document_check.summary(doc.ket_qua_kiem_tra)

    diem_cua_toi = None
    if is_gv:
        mine = db.execute(
            select(DiemBaoVe)
            .where(DiemBaoVe.lich_bao_ve_id == lich.id)
            .where(DiemBaoVe.giang_vien_id == user.giang_vien_id)
        ).scalar_one_or_none()
        if mine is not None:
            diem_cua_toi = MyScore(diem=float(mine.diem), nhan_xet=mine.nhan_xet)

    ly_do: str | None = None
    if not is_gv:
        ly_do = _BO_MON_NO_SCORE_REASON
    elif lich.da_chot:
        ly_do = _FINALIZED_REASON
    elif hd.ngay_bao_ve > today_vn():
        ly_do = _not_yet_detail(hd.ngay_bao_ve)

    return ScoringDetail(
        id=lich.id,
        hoi_dong_id=hd.id,
        ten_hoi_dong=hd.ten_hoi_dong,
        ngay_bao_ve=hd.ngay_bao_ve,
        phong=hd.phong,
        gio_du_kien=_compute_slot_time(hd.gio_bao_ve, lich.thu_tu),
        sinh_vien=_person_ref(lich.sinh_vien, "ma_so_sinh_vien"),
        de_tai_id=lich.de_tai_id,
        ten_de_tai=lich.de_tai.ten_de_tai,
        bao_cao_cuoi=to_document_out(doc) if doc is not None else None,
        kiem_tra=kiem_tra,
        diem_cua_toi=diem_cua_toi,
        da_chot=lich.da_chot,
        co_the_cham=ly_do is None,
        ly_do_khong_cham=ly_do,
    )


def score(db: Session, user: CurrentUser, lich_id: int, payload: ScoreRequest) -> ScoringDetail:
    """UC4.3/T-03-21: khóa dòng lich_bao_ve (serialize với finalize) — thành
    viên (403), chưa chốt (409), đã đến ngày bảo vệ (409); upsert điểm của
    chính người gọi (UNIQUE(lich_bao_ve_id, giang_vien_id))."""
    lich = db.execute(
        select(LichBaoVe).where(LichBaoVe.id == lich_id).with_for_update()
    ).scalar_one_or_none()
    if lich is None:
        raise HTTPException(status_code=404, detail=_SCHEDULE_NOT_FOUND_DETAIL)
    if not _is_member(db, lich.hoi_dong_id, user.giang_vien_id):
        db.rollback()
        raise HTTPException(status_code=403, detail=_NOT_MEMBER_DETAIL)
    if lich.da_chot:
        db.rollback()
        raise HTTPException(status_code=409, detail=_SCORE_FINALIZED_DETAIL)
    hd = db.get(HoiDong, lich.hoi_dong_id)
    if hd.ngay_bao_ve > today_vn():
        db.rollback()
        raise HTTPException(status_code=409, detail=_not_yet_detail(hd.ngay_bao_ve))

    existing = db.execute(
        select(DiemBaoVe)
        .where(DiemBaoVe.lich_bao_ve_id == lich_id)
        .where(DiemBaoVe.giang_vien_id == user.giang_vien_id)
    ).scalar_one_or_none()
    if existing is not None:
        existing.diem = payload.diem
        existing.nhan_xet = payload.nhan_xet
    else:
        db.add(
            DiemBaoVe(
                lich_bao_ve_id=lich_id,
                giang_vien_id=user.giang_vien_id,
                diem=payload.diem,
                nhan_xet=payload.nhan_xet,
            )
        )
    db.commit()
    return get_schedule_for_scoring(db, user, lich_id)


# ---------------------------------------------------------------------------
# UC4.4 — chốt kết quả (DEFN-04, §3.2.5 d) + UC5.2 tự lưu kho (REPO-01)
# ---------------------------------------------------------------------------


def finalize(db: Session, lich_id: int) -> tuple[FinalizeOut, int]:
    """T-03-22: khóa dòng lich_bao_ve; chỉ chốt khi số dòng diem_bao_ve bằng
    số thành viên hội đồng; điểm TB = trung bình cộng làm tròn 2 chữ số
    (ROUND_HALF_UP); da_chot lật bằng MỘT conditional UPDATE; cùng
    transaction chèn do_an_kho + thông báo KET_QUA_BAO_VE. Router đẩy
    archive.run_ingest vào BackgroundTasks SAU commit."""
    lich = db.execute(
        select(LichBaoVe).where(LichBaoVe.id == lich_id).with_for_update()
    ).scalar_one_or_none()
    if lich is None:
        raise HTTPException(status_code=404, detail=_SCHEDULE_NOT_FOUND_DETAIL)
    if lich.da_chot:
        db.rollback()
        raise HTTPException(status_code=409, detail=_FINALIZED_DETAIL)

    n_members = db.execute(
        select(func.count())
        .select_from(ThanhVienHoiDong)
        .where(ThanhVienHoiDong.hoi_dong_id == lich.hoi_dong_id)
    ).scalar_one()
    scores = (
        db.execute(select(DiemBaoVe.diem).where(DiemBaoVe.lich_bao_ve_id == lich_id))
        .scalars()
        .all()
    )
    if n_members == 0 or len(scores) != n_members:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=_not_enough_scores_detail(len(scores), n_members)
        )

    avg = (sum((Decimal(d) for d in scores), Decimal("0")) / Decimal(len(scores))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    result = db.execute(
        update(LichBaoVe)
        .where(LichBaoVe.id == lich_id)
        .where(LichBaoVe.da_chot.is_(False))
        .values(da_chot=True, diem_trung_binh=avg)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_FINALIZED_DETAIL)
    db.refresh(lich)

    try:
        kho = archive.insert_from_defense(db, lich)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_ARCHIVE_DUPLICATE_DETAIL) from None

    sv = db.get(SinhVien, lich.sinh_vien_id)
    if sv is not None:
        notifications.create(
            db,
            sv.tai_khoan_id,
            KET_QUA_BAO_VE,
            f"Kết quả bảo vệ của bạn đã được chốt: {avg}",
            lien_ket="/bao-ve",
        )
    kho_id = kho.id
    db.commit()
    return FinalizeOut(lich=_build_schedule_row(db, lich_id), do_an_kho_id=kho_id), kho_id


# ---------------------------------------------------------------------------
# UC4.5 — SV xem lịch và kết quả bảo vệ
# ---------------------------------------------------------------------------


def my_defense(db: Session, user: CurrentUser) -> MyDefenseOut:
    """T-03-23: lịch (hội đồng, ngày, giờ, phòng, thành viên) luôn trả khi đã
    xếp; ket_qua CHỈ khi da_chot — không bao giờ lộ điểm tạm tính/từng thành viên."""
    if user.sinh_vien_id is None:
        return MyDefenseOut()
    lich = db.execute(
        select(LichBaoVe)
        .where(LichBaoVe.sinh_vien_id == user.sinh_vien_id)
        .options(
            selectinload(LichBaoVe.hoi_dong)
            .selectinload(HoiDong.thanh_vien)
            .selectinload(ThanhVienHoiDong.giang_vien)
        )
    ).scalar_one_or_none()
    if lich is None:
        return MyDefenseOut()

    hd = lich.hoi_dong
    members = sorted(hd.thanh_vien, key=lambda m: (_VAI_TRO_ORDER.get(m.vai_tro, 2), m.id))
    schedule = MyDefenseSchedule(
        ten_hoi_dong=hd.ten_hoi_dong,
        ngay_bao_ve=hd.ngay_bao_ve,
        gio_du_kien=_compute_slot_time(hd.gio_bao_ve, lich.thu_tu),
        phong=hd.phong,
        thu_tu=lich.thu_tu,
        thanh_vien=[
            MyDefenseMember(
                ho_ten=m.giang_vien.ho_ten if m.giang_vien is not None else "",
                hoc_vi=m.giang_vien.hoc_vi if m.giang_vien is not None else None,
                vai_tro=m.vai_tro,
            )
            for m in members
        ],
    )
    ket_qua = None
    if lich.da_chot and lich.diem_trung_binh is not None:
        ket_qua = MyDefenseResult(diem_trung_binh=float(lich.diem_trung_binh))
    return MyDefenseOut(lich=schedule, ket_qua=ket_qua)
