from fastapi import HTTPException
from sqlalchemy import distinct, exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.core.timeutil import to_vn_date, today_vn
from app.models.bao_ve import CHU_TICH, DiemBaoVe, HoiDong, LichBaoVe, ThanhVienHoiDong
from app.models.de_cuong import DC_CHO_DUYET, DC_CHUA_NOP, LOAI_DE_CUONG, DeCuong, TaiLieuDoAn
from app.models.de_tai import DA_PHAN_CONG, NHAP, DeTai
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.phan_cong import PhanCongHuongDan
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan
from app.models.tien_do import CHUA_DEN_HAN, BaoCaoTienDo, MocTienDo
from app.models.trung_lap import DANG_KIEM_TRA, HOAN_TAT, KetQuaKiemTraTrungLap
from app.schemas.dashboard import (
    BmAssignedTopicRef,
    BmDashboardOut,
    BmProgressExcerpt,
    BmUpcomingCommittee,
    GvDashboardOut,
    GvTaskItem,
    GvTopicItem,
    SvDashboardOut,
    SvDefenseOut,
    SvMilestoneStep,
    SvNextMilestone,
    SvOutlineOut,
    SvTopicOut,
)
from app.schemas.topics import CohortRef
from app.services import ai_index, defense, document_check, progress

_VIEC_MAX = 10
_TIEN_DO_TRICH = 5
_HOI_DONG_SAP_TOI = 5

# D-08/T-02-38: một endpoint mỗi vai trò (require_role ở router); mọi truy
# vấn SV/GV chỉ đọc trong phạm vi own sinh_vien_id/giang_vien_id — không có
# tham số cho phép xem đề tài của người khác.


# IN-03: tài khoản chưa có hồ sơ SV/GV -> id không tồn tại, để bộ lọc phạm vi
# không bao giờ biên dịch thành `IS NULL` (lộ đề tài chưa có SV/GVHD).
_NO_PROFILE_ID = -1


def get_sv_dashboard(db: Session, user: CurrentUser) -> SvDashboardOut:
    sv_id = user.sinh_vien_id if user.sinh_vien_id is not None else _NO_PROFILE_ID

    topic = (
        db.execute(
            select(DeTai)
            .where(DeTai.sinh_vien_id_dang_hoat_dong == sv_id)
            .options(selectinload(DeTai.giang_vien))
        )
        .scalars()
        .first()
    )
    if topic is None:
        topic = (
            db.execute(
                select(DeTai)
                .where(DeTai.sinh_vien_id == sv_id)
                .where(DeTai.trang_thai != NHAP)  # bản nháp GV đang soạn: SV không thấy
                .options(selectinload(DeTai.giang_vien))
                .order_by(DeTai.id.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

    de_tai_out = None
    if topic is not None:
        de_tai_out = SvTopicOut(
            id=topic.id,
            ten_de_tai=topic.ten_de_tai,
            trang_thai=topic.trang_thai,
            giang_vien_huong_dan=topic.giang_vien.ho_ten if topic.giang_vien is not None else None,
            ly_do_tu_choi=topic.ly_do_tu_choi,
        )

    co_dot_dang_mo = (
        db.execute(select(DotDoAn.id).where(DotDoAn.trang_thai == DANG_MO).limit(1)).first()
        is not None
    )

    tien_do: list[SvMilestoneStep] = []
    moc_tiep_theo: SvNextMilestone | None = None
    my = progress.my_progress(db, user).de_tai
    if my is not None:
        today = today_vn()
        tien_do = [
            SvMilestoneStep(ten_moc=m.ten_moc, han_nop=m.han_nop, trang_thai=m.trang_thai)
            for m in my.moc
        ]
        nxt = next((m for m in my.moc if m.trang_thai == CHUA_DEN_HAN), None)
        if nxt is not None:
            moc_tiep_theo = SvNextMilestone(
                ten_moc=nxt.ten_moc,
                han_nop=nxt.han_nop,
                con_ngay=(nxt.han_nop - today).days if nxt.han_nop is not None else None,
            )

    # UC0.8: GVHD của SV trong đợt đang mở mới nhất (SV chỉ làm việc với GVHD).
    gvhd = db.execute(
        select(GiangVien)
        .join(PhanCongHuongDan, PhanCongHuongDan.giang_vien_id == GiangVien.id)
        .join(DotDoAn, DotDoAn.id == PhanCongHuongDan.dot_do_an_id)
        .where(PhanCongHuongDan.sinh_vien_id == sv_id)
        .where(DotDoAn.trang_thai == DANG_MO)
        .order_by(DotDoAn.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    return SvDashboardOut(
        de_tai=de_tai_out,
        giang_vien_huong_dan=(
            " ".join(p for p in (gvhd.hoc_vi, gvhd.ho_ten) if p) if gvhd is not None else None
        ),
        co_dot_dang_mo=co_dot_dang_mo,
        de_cuong=_sv_outline(db, topic),
        tien_do=tien_do,
        moc_tiep_theo=moc_tiep_theo,
        bao_ve=_sv_defense(db, user),
    )


def _sv_outline(db: Session, topic: DeTai | None) -> SvOutlineOut | None:
    """OUTL-02/MH-02: chỉ khi đề tài đã phân công GVHD (điểm vào UC2)."""
    if topic is None or topic.trang_thai != DA_PHAN_CONG:
        return None
    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == topic.id)
    ).scalar_one_or_none()
    if de_cuong is None:
        return SvOutlineOut(trang_thai=DC_CHUA_NOP)
    doc = (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_cuong_id == de_cuong.id)
            .where(TaiLieuDoAn.loai == LOAI_DE_CUONG)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if doc is None:
        return SvOutlineOut(trang_thai=de_cuong.trang_thai)
    ket_qua = document_check.get_check_for_doc(db, doc)
    kiem_tra = None
    if ket_qua is not None:
        document_check.expire_if_stale(db, ket_qua)
        kiem_tra = document_check.summary(ket_qua)
    return SvOutlineOut(
        trang_thai=de_cuong.trang_thai,
        phien_ban=doc.so_phien_ban,
        thoi_diem_nop=doc.thoi_diem_nop,
        kiem_tra=kiem_tra,
    )


def _sv_defense(db: Session, user: CurrentUser) -> SvDefenseOut | None:
    """DEFN-04/T-03-40: dùng lại defense.my_defense — điểm chỉ có sau khi chốt."""
    mine = defense.my_defense(db, user)
    if mine.lich is None:
        return None
    chu_tich = next((m for m in mine.lich.thanh_vien if m.vai_tro == CHU_TICH), None)
    return SvDefenseOut(
        ten_hoi_dong=mine.lich.ten_hoi_dong,
        phong=mine.lich.phong,
        ngay_bao_ve=mine.lich.ngay_bao_ve,
        gio_du_kien=mine.lich.gio_du_kien,
        chu_tich=(
            " ".join(p for p in (chu_tich.hoc_vi, chu_tich.ho_ten) if p)
            if chu_tich is not None
            else None
        ),
        diem_trung_binh=mine.ket_qua.diem_trung_binh if mine.ket_qua is not None else None,
    )


def _gv_unassigned_students(db: Session, gv_id: int) -> int:
    """Số SV trong lớp hướng dẫn (đợt đang mở) của GV chưa có đề tài đang hoạt
    động — việc "Giao đề tài" còn lại. Một truy vấn đếm, không lặp Python."""
    return db.execute(
        select(func.count())
        .select_from(PhanCongHuongDan)
        .join(DotDoAn, DotDoAn.id == PhanCongHuongDan.dot_do_an_id)
        .where(PhanCongHuongDan.giang_vien_id == gv_id)
        .where(DotDoAn.trang_thai == DANG_MO)
        .where(
            ~exists(
                select(DeTai.id).where(
                    DeTai.sinh_vien_id_dang_hoat_dong == PhanCongHuongDan.sinh_vien_id
                )
            )
        )
    ).scalar_one()


def get_gv_dashboard(db: Session, user: CurrentUser) -> GvDashboardOut:
    gv_id = user.giang_vien_id if user.giang_vien_id is not None else _NO_PROFILE_ID

    so_sinh_vien_huong_dan = db.execute(
        select(func.count())
        .select_from(DeTai)
        .where(DeTai.giang_vien_id == gv_id)
        .where(DeTai.trang_thai == DA_PHAN_CONG)
    ).scalar_one()

    so_de_tai = db.execute(
        select(func.count()).select_from(DeTai).where(DeTai.giang_vien_id == gv_id)
    ).scalar_one()

    # UC0.8: sĩ số lớp hướng dẫn trong các đợt đang mở (Bộ môn phân công).
    so_sinh_vien_lop = db.execute(
        select(func.count())
        .select_from(PhanCongHuongDan)
        .join(DotDoAn, DotDoAn.id == PhanCongHuongDan.dot_do_an_id)
        .where(PhanCongHuongDan.giang_vien_id == gv_id)
        .where(DotDoAn.trang_thai == DANG_MO)
    ).scalar_one()

    so_sinh_vien_chua_giao_de_tai = _gv_unassigned_students(db, gv_id)

    rows = (
        db.execute(
            select(DeTai)
            .where(DeTai.giang_vien_id == gv_id)
            .options(selectinload(DeTai.sinh_vien))
            .order_by(DeTai.id.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    de_tai = [
        GvTopicItem(
            id=row.id,
            ten_de_tai=row.ten_de_tai,
            trang_thai=row.trang_thai,
            sinh_vien=row.sinh_vien.ho_ten if row.sinh_vien is not None else None,
        )
        for row in rows
    ]

    own_assigned = (DeTai.giang_vien_id == gv_id, DeTai.trang_thai == DA_PHAN_CONG)
    so_de_cuong_cho_duyet = db.execute(
        select(func.count())
        .select_from(DeCuong)
        .join(DeTai, DeTai.id == DeCuong.de_tai_id)
        .where(*own_assigned)
        .where(DeCuong.trang_thai == DC_CHO_DUYET)
    ).scalar_one()
    so_bao_cao_cho_nhan_xet = db.execute(
        select(func.count())
        .select_from(BaoCaoTienDo)
        .join(DeTai, DeTai.id == BaoCaoTienDo.de_tai_id)
        .where(*own_assigned)
        .where(BaoCaoTienDo.nhan_xet.is_(None))
    ).scalar_one()
    so_hoi_dong_tham_gia = db.execute(
        select(func.count(distinct(ThanhVienHoiDong.hoi_dong_id))).where(
            ThanhVienHoiDong.giang_vien_id == gv_id
        )
    ).scalar_one()

    return GvDashboardOut(
        so_sinh_vien_huong_dan=so_sinh_vien_huong_dan,
        so_sinh_vien_lop=so_sinh_vien_lop,
        so_de_tai=so_de_tai,
        so_sinh_vien_chua_giao_de_tai=so_sinh_vien_chua_giao_de_tai,
        de_tai=de_tai,
        so_de_cuong_cho_duyet=so_de_cuong_cho_duyet,
        so_bao_cao_cho_nhan_xet=so_bao_cao_cho_nhan_xet,
        so_hoi_dong_tham_gia=so_hoi_dong_tham_gia,
        viec_can_xu_ly=_gv_tasks(db, gv_id),
    )


def _check_note(ket_qua: KetQuaKiemTraTrungLap | None) -> str:
    if ket_qua is None:
        return "Kiểm tra trùng lặp: Chưa kiểm tra"
    if ket_qua.trang_thai == HOAN_TAT:
        ty_le = float(ket_qua.ty_le_tong or 0)
        pct = f"{ty_le:.1f}".rstrip("0").rstrip(".")
        return f"Kiểm tra trùng lặp: Hoàn tất ({pct}%)"
    if ket_qua.trang_thai == DANG_KIEM_TRA:
        return "Kiểm tra trùng lặp: Đang kiểm tra"
    return "Kiểm tra trùng lặp: Lỗi"


def _gv_tasks(db: Session, gv_id: int | None) -> list[GvTaskItem]:
    """MH-03 "Việc cần xử lý" (≤ 10): SV chưa được giao đề tài (một việc gộp), đề cương chờ duyệt, báo cáo tiến độ chờ
    nhận xét của đề tài mình hướng dẫn, và lịch bảo vệ (chưa chốt) ở hội đồng
    mình ngồi mà mình chưa chấm. Mỗi loại một truy vấn, không N+1."""
    if gv_id is None:
        return []
    tasks: list[GvTaskItem] = []

    # Góp ý GVHD mục 1: việc gộp "Giao đề tài" đứng đầu danh sách khi lớp còn SV
    # chưa được giao đề tài (aggregate, không lặp theo từng SV).
    chua_giao = _gv_unassigned_students(db, gv_id)
    if chua_giao > 0:
        tasks.append(
            GvTaskItem(
                loai="GIAO_DE_TAI",
                sinh_vien=None,
                ten_de_tai=None,
                ghi_chu=f"{chua_giao} sinh viên trong lớp hướng dẫn chưa được giao đề tài",
                lien_ket="/sinh-vien-huong-dan",
            )
        )

    outlines = db.execute(
        select(DeCuong.id, DeTai.id, DeTai.ten_de_tai, SinhVien.ho_ten)
        .join(DeTai, DeTai.id == DeCuong.de_tai_id)
        .outerjoin(SinhVien, SinhVien.id == DeTai.sinh_vien_id)
        .where(DeTai.giang_vien_id == gv_id)
        .where(DeTai.trang_thai == DA_PHAN_CONG)
        .where(DeCuong.trang_thai == DC_CHO_DUYET)
        .order_by(DeCuong.id)
        .limit(_VIEC_MAX)
    ).all()
    latest_doc: dict[int, TaiLieuDoAn] = {}
    if outlines:
        docs = (
            db.execute(
                select(TaiLieuDoAn)
                .where(TaiLieuDoAn.de_cuong_id.in_([row[0] for row in outlines]))
                .where(TaiLieuDoAn.loai == LOAI_DE_CUONG)
                .options(selectinload(TaiLieuDoAn.ket_qua_kiem_tra))
                .order_by(TaiLieuDoAn.de_cuong_id, TaiLieuDoAn.so_phien_ban.desc())
            )
            .scalars()
            .all()
        )
        for doc in docs:
            latest_doc.setdefault(doc.de_cuong_id, doc)
    for de_cuong_id, de_tai_id, ten, sv_ten in outlines:
        doc = latest_doc.get(de_cuong_id)
        tasks.append(
            GvTaskItem(
                loai="DUYET_DE_CUONG",
                sinh_vien=sv_ten,
                ten_de_tai=ten,
                ghi_chu=_check_note(doc.ket_qua_kiem_tra if doc is not None else None),
                lien_ket=f"/duyet-de-cuong?de_tai_id={de_tai_id}",
            )
        )

    reports = db.execute(
        select(BaoCaoTienDo.thoi_diem_nop, MocTienDo.ten_moc, DeTai.id, DeTai.ten_de_tai, SinhVien.ho_ten)
        .join(DeTai, DeTai.id == BaoCaoTienDo.de_tai_id)
        .join(MocTienDo, MocTienDo.id == BaoCaoTienDo.moc_tien_do_id)
        .outerjoin(SinhVien, SinhVien.id == DeTai.sinh_vien_id)
        .where(DeTai.giang_vien_id == gv_id)
        .where(DeTai.trang_thai == DA_PHAN_CONG)
        .where(BaoCaoTienDo.nhan_xet.is_(None))
        .order_by(BaoCaoTienDo.thoi_diem_nop, BaoCaoTienDo.id)
        .limit(_VIEC_MAX)
    ).all()
    for thoi_diem_nop, ten_moc, de_tai_id, ten, sv_ten in reports:
        tasks.append(
            GvTaskItem(
                loai="NHAN_XET_TIEN_DO",
                sinh_vien=sv_ten,
                ten_de_tai=ten,
                ghi_chu=f"{ten_moc} - nộp {to_vn_date(thoi_diem_nop).strftime('%d/%m/%Y')}",
                lien_ket=f"/nhan-xet-tien-do?de_tai_id={de_tai_id}",
            )
        )

    my_score = (
        select(DiemBaoVe.id)
        .where(DiemBaoVe.lich_bao_ve_id == LichBaoVe.id)
        .where(DiemBaoVe.giang_vien_id == gv_id)
    )
    to_score = db.execute(
        select(LichBaoVe.id, HoiDong.id, HoiDong.ten_hoi_dong, HoiDong.ngay_bao_ve, DeTai.ten_de_tai, SinhVien.ho_ten)
        .join(HoiDong, HoiDong.id == LichBaoVe.hoi_dong_id)
        .join(
            ThanhVienHoiDong,
            (ThanhVienHoiDong.hoi_dong_id == HoiDong.id) & (ThanhVienHoiDong.giang_vien_id == gv_id),
        )
        .join(DeTai, DeTai.id == LichBaoVe.de_tai_id)
        .outerjoin(SinhVien, SinhVien.id == LichBaoVe.sinh_vien_id)
        .where(LichBaoVe.da_chot.is_(False))
        .where(~exists(my_score))
        .order_by(HoiDong.ngay_bao_ve, HoiDong.gio_bao_ve, LichBaoVe.thu_tu, LichBaoVe.id)
        .limit(_VIEC_MAX)
    ).all()
    for lich_id, hoi_dong_id, ten_hd, ngay, ten, sv_ten in to_score:
        tasks.append(
            GvTaskItem(
                loai="CHAM_DIEM",
                sinh_vien=sv_ten,
                ten_de_tai=ten,
                ghi_chu=f"{ten_hd} - {ngay.strftime('%d/%m/%Y')}",
                lien_ket=f"/cham-diem?hoi_dong_id={hoi_dong_id}&lich_id={lich_id}",
            )
        )
    return tasks[:_VIEC_MAX]


def _default_cohort(db: Session) -> DotDoAn | None:
    cohort = (
        db.execute(
            select(DotDoAn).where(DotDoAn.trang_thai == DANG_MO).order_by(DotDoAn.id.desc()).limit(1)
        )
        .scalars()
        .first()
    )
    if cohort is not None:
        return cohort
    return db.execute(select(DotDoAn).order_by(DotDoAn.id.desc()).limit(1)).scalars().first()


def get_bo_mon_dashboard(db: Session, dot_do_an_id: int | None) -> BmDashboardOut:
    cohort = db.get(DotDoAn, dot_do_an_id) if dot_do_an_id is not None else _default_cohort(db)
    if dot_do_an_id is not None and cohort is None:
        # IN-10: id đợt không tồn tại -> 404, không trả bảng điều khiển toàn số 0.
        raise HTTPException(status_code=404, detail="Không tìm thấy đợt đồ án")

    sv_chua_giao_de_tai = 0
    de_tai_da_phan_cong = 0
    de_tai_moi_giao: list[BmAssignedTopicRef] = []

    if cohort is not None:
        # SV đã được phân công GVHD trong đợt nhưng chưa có đề tài đang hoạt động.
        sv_chua_giao_de_tai = db.execute(
            select(func.count())
            .select_from(PhanCongHuongDan)
            .where(PhanCongHuongDan.dot_do_an_id == cohort.id)
            .where(
                ~exists(
                    select(DeTai.id).where(
                        DeTai.sinh_vien_id_dang_hoat_dong == PhanCongHuongDan.sinh_vien_id
                    )
                )
            )
        ).scalar_one()

        de_tai_da_phan_cong = db.execute(
            select(func.count())
            .select_from(DeTai)
            .where(DeTai.dot_do_an_id == cohort.id)
            .where(DeTai.trang_thai == DA_PHAN_CONG)
        ).scalar_one()

        rows = (
            db.execute(
                select(DeTai)
                .where(DeTai.dot_do_an_id == cohort.id)
                .where(DeTai.trang_thai == DA_PHAN_CONG)
                .options(selectinload(DeTai.giang_vien), selectinload(DeTai.sinh_vien))
                .order_by(DeTai.id.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )
        for row in rows:
            de_tai_moi_giao.append(
                BmAssignedTopicRef(
                    id=row.id,
                    ten_de_tai=row.ten_de_tai,
                    giang_vien=(row.giang_vien.ho_ten if row.giang_vien is not None else "") or "",
                    sinh_vien=(row.sinh_vien.ho_ten if row.sinh_vien is not None else "") or "",
                )
            )

    sv_chua_co_de_tai = db.execute(
        select(func.count())
        .select_from(SinhVien)
        .join(TaiKhoan, TaiKhoan.id == SinhVien.tai_khoan_id)
        .where(TaiKhoan.bi_khoa.is_(False))
        .where(
            ~exists(
                select(DeTai.id).where(DeTai.sinh_vien_id_dang_hoat_dong == SinhVien.id)
            )
        )
    ).scalar_one()

    tong_sinh_vien = db.execute(
        select(func.count())
        .select_from(SinhVien)
        .join(TaiKhoan, TaiKhoan.id == SinhVien.tai_khoan_id)
        .where(TaiKhoan.bi_khoa.is_(False))
    ).scalar_one()

    sv_chua_phan_cong = 0
    if cohort is not None:
        sv_chua_phan_cong = db.execute(
            select(func.count())
            .select_from(SinhVien)
            .join(TaiKhoan, TaiKhoan.id == SinhVien.tai_khoan_id)
            .where(TaiKhoan.bi_khoa.is_(False))
            .where(
                ~exists(
                    select(PhanCongHuongDan.id)
                    .where(PhanCongHuongDan.sinh_vien_id == SinhVien.id)
                    .where(PhanCongHuongDan.dot_do_an_id == cohort.id)
                )
            )
        ).scalar_one()

    sv_tre_moc = 0
    tien_do_trich = None
    moc_tien_do = []
    if cohort is not None:
        # PROG-03/D-05: cùng một hàm tính cờ trễ như /tien-do-toan-khoa.
        milestones, rows = progress.compute_cohort_progress(db, cohort.id)
        counts = progress._report_counts(db, [m.id for m in milestones])
        moc_tien_do = [progress._milestone_out(m, counts.get(m.id, 0)) for m in milestones]
        sv_tre_moc = sum(1 for r in rows if r.tre_moc)
        tien_do_trich = BmProgressExcerpt(
            moc=moc_tien_do,
            items=[progress.row_out(r) for r in rows[:_TIEN_DO_TRICH]],
            tong=len(rows),
        )

    today = today_vn()
    so_hoi_dong_sap_toi = db.execute(
        select(func.count()).select_from(HoiDong).where(HoiDong.ngay_bao_ve >= today)
    ).scalar_one()
    so_sv_lich = (
        select(func.count(LichBaoVe.id))
        .where(LichBaoVe.hoi_dong_id == HoiDong.id)
        .correlate(HoiDong)
        .scalar_subquery()
    )
    hoi_dong_sap_toi = [
        BmUpcomingCommittee(
            id=hd.id,
            ten_hoi_dong=hd.ten_hoi_dong,
            ngay_bao_ve=hd.ngay_bao_ve,
            gio_bao_ve=hd.gio_bao_ve,
            phong=hd.phong,
            so_sinh_vien=n,
        )
        for hd, n in db.execute(
            select(HoiDong, so_sv_lich)
            .where(HoiDong.ngay_bao_ve >= today)
            .order_by(HoiDong.ngay_bao_ve, HoiDong.gio_bao_ve, HoiDong.id)
            .limit(_HOI_DONG_SAP_TOI)
        ).all()
    ]

    return BmDashboardOut(
        tai_lieu_chua_index=ai_index.count_pending_documents(db),
        sv_tre_moc=sv_tre_moc,
        tien_do_trich=tien_do_trich,
        moc_tien_do=moc_tien_do,
        so_hoi_dong_sap_toi=so_hoi_dong_sap_toi,
        hoi_dong_sap_toi=hoi_dong_sap_toi,
        dot_do_an=(
            CohortRef(
                id=cohort.id, ten_dot=cohort.ten_dot, khoa=cohort.khoa, trang_thai=cohort.trang_thai
            )
            if cohort is not None
            else None
        ),
        sv_chua_giao_de_tai=sv_chua_giao_de_tai,
        de_tai_da_phan_cong=de_tai_da_phan_cong,
        sv_chua_co_de_tai=sv_chua_co_de_tai,
        sv_chua_phan_cong=sv_chua_phan_cong,
        tong_sinh_vien=tong_sinh_vien,
        de_tai_moi_giao=de_tai_moi_giao,
    )
