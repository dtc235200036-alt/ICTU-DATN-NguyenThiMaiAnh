from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.roles import VaiTro
from app.core.security import InvalidToken, decode_token
from app.models.tai_khoan import TaiKhoan

_bearer_scheme = HTTPBearer(auto_error=False)

_INVALID_SESSION_DETAIL = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"

# Allow-list of (method, path) đôi không cần xác thực (AUTH-03).
# /api/docs và /api/openapi.json là tài liệu OpenAPI tự sinh bởi FastAPI (không
# chứa dữ liệu nghiệp vụ) — công khai theo mặc định của framework.
PUBLIC_ROUTES: set[tuple[str, str]] = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/logout"),
    ("GET", "/api/health"),
    ("GET", "/api/docs"),
    ("HEAD", "/api/docs"),
    ("GET", "/api/openapi.json"),
    ("HEAD", "/api/openapi.json"),
}


@dataclass(frozen=True)
class CurrentUser:
    tai_khoan_id: int
    vai_tro: VaiTro
    ma_dang_nhap: str
    email: str
    ho_ten: str
    sinh_vien_id: int | None
    giang_vien_id: int | None


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_INVALID_SESSION_DETAIL,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise _unauthorized()

    try:
        payload = decode_token(credentials.credentials, expected_typ="access")
    except InvalidToken:
        raise _unauthorized() from None

    try:
        tai_khoan_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise _unauthorized() from None

    # Đọc lại tai_khoan mỗi request — bi_khoa có hiệu lực ngay lập tức (AUTH-03).
    account = db.get(TaiKhoan, tai_khoan_id)
    if account is None or account.bi_khoa:
        raise _unauthorized()

    if str(account.vai_tro) != payload.get("vai_tro"):
        raise _unauthorized()

    # WR-04: token phát trước lần logout gần nhất (phien_ban_token đã tăng)
    # không còn khớp claim "tv" -> từ chối ngay, không chờ token hết hạn tự
    # nhiên.
    if payload.get("tv") != account.phien_ban_token:
        raise _unauthorized()

    ho_ten = account.email
    sinh_vien_id = None
    giang_vien_id = None
    if account.sinh_vien is not None:
        ho_ten = account.sinh_vien.ho_ten or ho_ten
        sinh_vien_id = account.sinh_vien.id
    elif account.giang_vien is not None:
        ho_ten = account.giang_vien.ho_ten or ho_ten
        giang_vien_id = account.giang_vien.id

    return CurrentUser(
        tai_khoan_id=account.id,
        vai_tro=account.vai_tro,
        ma_dang_nhap=account.ma_dang_nhap,
        email=account.email,
        ho_ten=ho_ten,
        sinh_vien_id=sinh_vien_id,
        giang_vien_id=giang_vien_id,
    )


def require_role(*roles: VaiTro) -> Callable[..., CurrentUser]:
    allowed = frozenset(roles)

    def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.vai_tro not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện thao tác này",
            )
        return user

    _dependency.allowed_roles = allowed
    return _dependency
