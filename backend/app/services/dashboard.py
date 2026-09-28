from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.models.de_tai import CHO_DUYET, DA_PHAN_CONG, DeTai, SINH_VIEN
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.tai_khoan import SinhVien, TaiKhoan
from app.schemas.dashboard import (
    BmDashboardOut,
    BmPendingTopicRef,
    GvDashboardOut,
    GvTopicItem,
    SvDashboardOut,
    SvTopicOut,
)
from app.schemas.topics import CohortRef

# D-08/T-02-38: một endpoint mỗi vai trò (require_role ở router); mọi truy
# vấn SV/GV chỉ đọc trong phạm vi own sinh_vien_id/giang_vien_id — không có
# tham số cho phép xem đề tài của người khác.


def get_sv_dashboard(db: Session, user: CurrentUser) -> SvDashboardOut:
    sv_id = user.sinh_vien_id

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

    return SvDashboardOut(de_tai=de_tai_out, co_dot_dang_mo=co_dot_dang_mo)


def get_gv_dashboard(db: Session, user: CurrentUser) -> GvDashboardOut:
    gv_id = user.giang_vien_id

    so_sinh_vien_huong_dan = db.execute(
        select(func.count())
        .select_from(DeTai)
        .where(DeTai.giang_vien_id == gv_id)
        .where(DeTai.trang_thai == DA_PHAN_CONG)
    ).scalar_one()

    so_de_tai = db.execute(
        select(func.count()).select_from(DeTai).where(DeTai.giang_vien_id == gv_id)
    ).scalar_one()

    so_de_tai_cho_duyet = db.execute(
        select(func.count())
        .select_from(DeTai)
        .where(DeTai.giang_vien_id == gv_id)
        .where(DeTai.trang_thai == CHO_DUYET)
    ).scalar_one()

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

    return GvDashboardOut(
        so_sinh_vien_huong_dan=so_sinh_vien_huong_dan,
        so_de_tai=so_de_tai,
        so_de_tai_cho_duyet=so_de_tai_cho_duyet,
        de_tai=de_tai,
    )


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

    de_tai_cho_duyet = 0
    de_tai_da_phan_cong = 0
    cho_duyet_moi_nhat: list[BmPendingTopicRef] = []

    if cohort is not None:
        de_tai_cho_duyet = db.execute(
            select(func.count())
            .select_from(DeTai)
            .where(DeTai.dot_do_an_id == cohort.id)
            .where(DeTai.trang_thai == CHO_DUYET)
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
                .where(DeTai.trang_thai == CHO_DUYET)
                .options(selectinload(DeTai.giang_vien), selectinload(DeTai.sinh_vien))
                .order_by(DeTai.id.desc())
                .limit(5)
            )
            .scalars()
            .all()
        )
        for row in rows:
            if row.loai_nguoi_de_xuat == SINH_VIEN and row.sinh_vien is not None:
                nguoi_de_xuat = row.sinh_vien.ho_ten or ""
            elif row.giang_vien is not None:
                nguoi_de_xuat = row.giang_vien.ho_ten or ""
            else:
                nguoi_de_xuat = ""
            cho_duyet_moi_nhat.append(
                BmPendingTopicRef(id=row.id, ten_de_tai=row.ten_de_tai, nguoi_de_xuat=nguoi_de_xuat)
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

    return BmDashboardOut(
        dot_do_an=(
            CohortRef(
                id=cohort.id, ten_dot=cohort.ten_dot, khoa=cohort.khoa, trang_thai=cohort.trang_thai
            )
            if cohort is not None
            else None
        ),
        de_tai_cho_duyet=de_tai_cho_duyet,
        de_tai_da_phan_cong=de_tai_da_phan_cong,
        sv_chua_co_de_tai=sv_chua_co_de_tai,
        tong_sinh_vien=tong_sinh_vien,
        cho_duyet_moi_nhat=cho_duyet_moi_nhat,
    )
