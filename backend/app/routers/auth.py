from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import create_access_token, verify_password, verify_password_dummy
from app.models.tai_khoan import TaiKhoan
from app.schemas.auth import LoginRequest, NguoiDung, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_LOGIN_FAIL_DETAIL = "Sai thông tin đăng nhập hoặc tài khoản đã bị khóa"


def _to_nguoi_dung(settings, account: TaiKhoan) -> NguoiDung:
    ho_ten = settings.BO_MON_DISPLAY_NAME
    sinh_vien_id = None
    giang_vien_id = None
    if account.sinh_vien is not None:
        ho_ten = account.sinh_vien.ho_ten or ho_ten
        sinh_vien_id = account.sinh_vien.id
    elif account.giang_vien is not None:
        ho_ten = account.giang_vien.ho_ten or ho_ten
        giang_vien_id = account.giang_vien.id

    return NguoiDung(
        id=account.id,
        vai_tro=account.vai_tro,
        ma_dang_nhap=account.ma_dang_nhap,
        email=account.email,
        ho_ten=ho_ten,
        sinh_vien_id=sinh_vien_id,
        giang_vien_id=giang_vien_id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()

    account = db.execute(
        select(TaiKhoan).where(
            or_(
                TaiKhoan.ma_dang_nhap == payload.dang_nhap,
                TaiKhoan.email == payload.dang_nhap,
            )
        )
    ).scalar_one_or_none()

    if account is None:
        verify_password_dummy(payload.mat_khau)
        raise HTTPException(status_code=401, detail=_LOGIN_FAIL_DETAIL)

    if not verify_password(payload.mat_khau, account.mat_khau_bam) or account.bi_khoa:
        raise HTTPException(status_code=401, detail=_LOGIN_FAIL_DETAIL)

    access_token = create_access_token(account.id, account.vai_tro)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        nguoi_dung=_to_nguoi_dung(settings, account),
    )
