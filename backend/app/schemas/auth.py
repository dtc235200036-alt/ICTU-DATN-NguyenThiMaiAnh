from pydantic import BaseModel, Field, field_validator

from app.core.roles import VaiTro
from app.schemas.common import NFCModel


class LoginRequest(NFCModel):
    dang_nhap: str = Field(min_length=1, max_length=150)
    mat_khau: str = Field(min_length=1, max_length=128)

    @field_validator("mat_khau")
    @classmethod
    def _mat_khau_byte_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu vượt quá 72 byte")
        return v


class NguoiDung(BaseModel):
    id: int
    vai_tro: VaiTro
    ma_dang_nhap: str
    email: str
    ho_ten: str
    sinh_vien_id: int | None = None
    giang_vien_id: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    nguoi_dung: NguoiDung
