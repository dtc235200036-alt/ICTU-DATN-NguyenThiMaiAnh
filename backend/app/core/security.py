import time
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.roles import VaiTro

settings = get_settings()

# Hash bcrypt cố định dùng để so sánh khi tài khoản không tồn tại (đồng đều thời gian
# xử lý giữa "sai mật khẩu" và "không tồn tại tài khoản" — T-02-02).
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-for-timing-safety", bcrypt.gensalt(rounds=12))


class InvalidToken(Exception):
    """Token JWT thiếu, sai định dạng, hết hạn hoặc sai loại (typ)."""


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Mật khẩu vượt quá 72 byte")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Trả về False khi mật khẩu sai hoặc hash không hợp lệ — không bao giờ raise."""
    try:
        target = (password_hash or "").encode("utf-8") or _DUMMY_HASH
        return bcrypt.checkpw(password.encode("utf-8"), target)
    except ValueError:
        return False


def verify_password_dummy(password: str) -> None:
    """Chạy verify với hash giả khi tài khoản không tồn tại, giữ thời gian xử lý đồng đều."""
    try:
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
    except ValueError:
        pass


def create_access_token(tai_khoan_id: int, vai_tro: VaiTro) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": str(tai_khoan_id),
        "vai_tro": str(vai_tro),
        "typ": "access",
        "iat": now,
        "exp": now + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(tai_khoan_id: int) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": str(tai_khoan_id),
        "typ": "refresh",
        "iat": now,
        "exp": now + settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_typ: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "typ"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidToken(str(exc)) from exc

    if payload.get("typ") != expected_typ:
        raise InvalidToken(f"Loại token không hợp lệ: mong đợi {expected_typ}")

    return payload
