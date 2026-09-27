from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.roles import VaiTro
from app.core.security import hash_password
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan
from app.schemas.accounts import AccountCreate, AccountOut, AccountUpdate
from app.schemas.common import Page

_CONFLICT_DETAIL = "Mã hoặc email đã tồn tại"
_NOT_FOUND_DETAIL = "Không tìm thấy tài khoản"

_PROFILE_MODEL_BY_ROLE = {
    VaiTro.SINH_VIEN: SinhVien,
    VaiTro.GIANG_VIEN: GiangVien,
}


def _to_account_out(account: TaiKhoan, profile: SinhVien | GiangVien) -> AccountOut:
    is_sv = isinstance(profile, SinhVien)
    return AccountOut(
        tai_khoan_id=account.id,
        vai_tro=account.vai_tro,
        ma_dang_nhap=account.ma_dang_nhap,
        email=account.email,
        bi_khoa=account.bi_khoa,
        profile_id=profile.id,
        ho_ten=profile.ho_ten or "",
        lop=profile.lop if is_sv else None,
        khoa=profile.khoa if is_sv else None,
        hoc_vi=None if is_sv else profile.hoc_vi,
    )


def list_accounts(
    db: Session,
    vai_tro: VaiTro,
    q: str | None,
    bi_khoa: bool | None,
    page: int,
    page_size: int,
) -> Page[AccountOut]:
    profile_model = _PROFILE_MODEL_BY_ROLE.get(vai_tro)
    if profile_model is None:
        raise HTTPException(status_code=422, detail="vai_tro phải là SINH_VIEN hoặc GIANG_VIEN")

    base = (
        select(TaiKhoan, profile_model)
        .join(profile_model, profile_model.tai_khoan_id == TaiKhoan.id)
        .where(TaiKhoan.vai_tro == vai_tro)
    )

    if bi_khoa is not None:
        base = base.where(TaiKhoan.bi_khoa == bi_khoa)

    if q:
        base = base.where(
            or_(
                TaiKhoan.ma_dang_nhap.contains(q, autoescape=True),
                TaiKhoan.email.contains(q, autoescape=True),
                profile_model.ho_ten.contains(q, autoescape=True),
            )
        )

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar_one()

    # D-06: sắp xếp theo ho_ten (collation utf8mb4_vietnamese_ci ở cấp cột/bảng).
    paged = (
        base.order_by(profile_model.ho_ten.asc(), TaiKhoan.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(paged).all()
    items = [_to_account_out(account, profile) for account, profile in rows]

    return Page[AccountOut](items=items, total=total, page=page, page_size=page_size)


def create_account(db: Session, payload: AccountCreate) -> AccountOut:
    account = TaiKhoan(
        ma_dang_nhap=payload.ma,
        email=payload.email,
        mat_khau_bam=hash_password(payload.mat_khau),
        vai_tro=VaiTro(payload.vai_tro),
        bi_khoa=False,
    )
    db.add(account)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_CONFLICT_DETAIL) from None

    if payload.vai_tro == "SINH_VIEN":
        profile: SinhVien | GiangVien = SinhVien(
            tai_khoan_id=account.id,
            ma_so_sinh_vien=payload.ma,
            ho_ten=payload.ho_ten,
            email=payload.email,
            lop=payload.lop,
            khoa=payload.khoa,
        )
    else:
        profile = GiangVien(
            tai_khoan_id=account.id,
            ma_giang_vien=payload.ma,
            ho_ten=payload.ho_ten,
            email=payload.email,
            hoc_vi=payload.hoc_vi,
        )
    db.add(profile)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_CONFLICT_DETAIL) from None

    db.commit()
    db.refresh(account)
    db.refresh(profile)
    return _to_account_out(account, profile)


def _load_manageable_account(db: Session, tai_khoan_id: int) -> tuple[TaiKhoan, SinhVien | GiangVien]:
    """404 khi không tồn tại HOẶC là BO_MON — BO_MON không thể sửa/khóa qua API (T-02-13)."""
    account = db.get(TaiKhoan, tai_khoan_id)
    if account is None or account.vai_tro == VaiTro.BO_MON:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)

    profile = account.sinh_vien or account.giang_vien
    if profile is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)

    return account, profile


def update_account(db: Session, tai_khoan_id: int, payload: AccountUpdate) -> AccountOut:
    account, profile = _load_manageable_account(db, tai_khoan_id)
    is_sv = isinstance(profile, SinhVien)

    if payload.email is not None:
        account.email = payload.email
        profile.email = payload.email
    if payload.ho_ten is not None:
        profile.ho_ten = payload.ho_ten
    if payload.mat_khau is not None:
        account.mat_khau_bam = hash_password(payload.mat_khau)

    if is_sv:
        if payload.lop is not None:
            profile.lop = payload.lop
        if payload.khoa is not None:
            profile.khoa = payload.khoa
    else:
        if payload.hoc_vi is not None:
            profile.hoc_vi = payload.hoc_vi

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_CONFLICT_DETAIL) from None

    db.commit()
    db.refresh(account)
    db.refresh(profile)
    return _to_account_out(account, profile)


def set_locked(db: Session, tai_khoan_id: int, locked: bool) -> AccountOut:
    account, profile = _load_manageable_account(db, tai_khoan_id)
    account.bi_khoa = locked
    db.commit()
    db.refresh(account)
    db.refresh(profile)
    return _to_account_out(account, profile)
