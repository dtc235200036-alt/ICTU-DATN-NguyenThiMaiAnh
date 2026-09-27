import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.roles import VaiTro
from app.schemas.common import NFCModel

# D-06: schema request kế thừa NFCModel (NFC-normalize + strip mọi trường trước
# khi các validator dưới đây chạy).
_MA_PATTERN = r"^[A-Za-z0-9._-]{3,20}$"
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_email_format(v: str) -> str:
    if not _EMAIL_PATTERN.match(v):
        raise ValueError("Email không hợp lệ")
    return v


def _check_mat_khau_byte_length(v: str) -> str:
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Mật khẩu vượt quá 72 byte")
    return v


class AccountCreate(NFCModel):
    """UC0.2: tạo tài khoản SV/GV. BO_MON không thể được tạo qua API (T-02-13)."""

    vai_tro: Literal["SINH_VIEN", "GIANG_VIEN"]
    ma: str = Field(pattern=_MA_PATTERN)
    email: str = Field(max_length=150)
    ho_ten: str = Field(min_length=1, max_length=150)
    lop: str | None = Field(default=None, max_length=50)
    khoa: str | None = Field(default=None, max_length=100)
    hoc_vi: str | None = Field(default=None, max_length=50)
    mat_khau: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _email_valid(cls, v: str) -> str:
        return _check_email_format(v)

    @field_validator("mat_khau")
    @classmethod
    def _mat_khau_valid(cls, v: str) -> str:
        return _check_mat_khau_byte_length(v)


class AccountUpdate(NFCModel):
    """UC0.2: sửa tài khoản SV/GV. mã bất biến sau khi tạo (không có trong đây)."""

    email: str | None = Field(default=None, max_length=150)
    ho_ten: str | None = Field(default=None, min_length=1, max_length=150)
    lop: str | None = Field(default=None, max_length=50)
    khoa: str | None = Field(default=None, max_length=100)
    hoc_vi: str | None = Field(default=None, max_length=50)
    mat_khau: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _email_valid(cls, v: str | None) -> str | None:
        return _check_email_format(v) if v is not None else v

    @field_validator("mat_khau")
    @classmethod
    def _mat_khau_valid(cls, v: str | None) -> str | None:
        return _check_mat_khau_byte_length(v) if v is not None else v


class AccountOut(BaseModel):
    """Không bao giờ chứa mat_khau_bam (T-02-14)."""

    tai_khoan_id: int
    vai_tro: VaiTro
    ma_dang_nhap: str
    email: str
    bi_khoa: bool
    profile_id: int
    ho_ten: str
    lop: str | None = None
    khoa: str | None = None
    hoc_vi: str | None = None


class LecturerOut(BaseModel):
    """T-02-17: chỉ id/mã/họ tên/học vị — không email/tài khoản."""

    id: int
    ma_giang_vien: str | None = None
    ho_ten: str | None = None
    hoc_vi: str | None = None
