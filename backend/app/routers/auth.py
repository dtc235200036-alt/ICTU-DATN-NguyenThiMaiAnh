from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE
from app.core.security import (
    InvalidToken,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    verify_password_dummy,
)
from app.core.throttle import login_throttle
from app.models.tai_khoan import TaiKhoan
from app.schemas.auth import LoginRequest, NguoiDung, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_LOGIN_FAIL_DETAIL = "Sai thông tin đăng nhập hoặc tài khoản đã bị khóa"
_TOO_MANY_ATTEMPTS_DETAIL = "Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 15 phút."
_REFRESH_COOKIE_NAME = "refresh_token"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


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


def _set_refresh_cookie(
    response: Response, settings, account_id: int, token_version: int
) -> None:
    refresh_token = create_refresh_token(account_id, token_version)
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/api/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    )


def _delete_refresh_cookie(response: Response, settings) -> None:
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        path="/api/auth",
        secure=settings.COOKIE_SECURE,
        samesite="strict",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    ip = _client_ip(request)

    if login_throttle.is_blocked(ip, payload.dang_nhap):
        raise HTTPException(status_code=429, detail=_TOO_MANY_ATTEMPTS_DETAIL)

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
        login_throttle.record_failure(ip, payload.dang_nhap)
        raise HTTPException(status_code=401, detail=_LOGIN_FAIL_DETAIL)

    if not verify_password(payload.mat_khau, account.mat_khau_bam) or account.bi_khoa:
        login_throttle.record_failure(ip, payload.dang_nhap)
        raise HTTPException(status_code=401, detail=_LOGIN_FAIL_DETAIL)

    login_throttle.reset(ip, payload.dang_nhap)

    access_token = create_access_token(account.id, account.vai_tro, account.phien_ban_token)
    _set_refresh_cookie(response, settings, account.id, account.phien_ban_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        nguoi_dung=_to_nguoi_dung(settings, account),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    cookie_value = request.cookies.get(_REFRESH_COOKIE_NAME)

    def _reject() -> HTTPException:
        _delete_refresh_cookie(response, settings)
        return HTTPException(status_code=401, detail=_LOGIN_FAIL_DETAIL)

    if not cookie_value:
        raise _reject()

    try:
        payload = decode_token(cookie_value, expected_typ="refresh")
    except InvalidToken:
        raise _reject() from None

    try:
        account_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise _reject() from None

    account = db.get(TaiKhoan, account_id)
    if account is None or account.bi_khoa:
        raise _reject()

    # WR-04: refresh token phát trước lần logout gần nhất không còn khớp
    # phien_ban_token hiện tại -> từ chối thay vì cấp access token mới.
    if payload.get("tv") != account.phien_ban_token:
        raise _reject()

    access_token = create_access_token(account.id, account.vai_tro, account.phien_ban_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        nguoi_dung=_to_nguoi_dung(settings, account),
    )


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    """WR-04: tăng phien_ban_token của tài khoản khi logout — mọi access và
    refresh token đã phát ra trước đó (kể cả bản sao bị rò rỉ ngoài phiên
    hiện tại) hết hiệu lực ngay lập tức, thay vì chỉ xóa cookie phía client
    và chờ token hết hạn tự nhiên (tối đa REFRESH_TOKEN_EXPIRE_MINUTES)."""
    settings = get_settings()
    cookie_value = request.cookies.get(_REFRESH_COOKIE_NAME)
    if cookie_value:
        try:
            payload = decode_token(cookie_value, expected_typ="refresh")
            account_id = int(payload["sub"])
        except (InvalidToken, KeyError, ValueError):
            account_id = None
        if account_id is not None:
            db.execute(
                update(TaiKhoan)
                .where(TaiKhoan.id == account_id)
                .values(phien_ban_token=TaiKhoan.phien_ban_token + 1)
            )
            db.commit()
    _delete_refresh_cookie(response, settings)


@router.get("/me", response_model=NguoiDung)
def me(
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> NguoiDung:
    settings = get_settings()
    account = db.get(TaiKhoan, user.tai_khoan_id)
    if account is None:
        raise HTTPException(status_code=401, detail=_LOGIN_FAIL_DETAIL)
    return _to_nguoi_dung(settings, account)
