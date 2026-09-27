import unicodedata
from typing import Generic, TypeVar

from pydantic import BaseModel, field_validator

T = TypeVar("T")


def nfc(value: str) -> str:
    """Chuẩn hóa Unicode NFC (D-06, Pitfall 2)."""
    return unicodedata.normalize("NFC", value)


class NFCModel(BaseModel):
    """Base cho mọi schema request: NFC-normalize mọi trường chuỗi tại điểm nhập liệu.

    Các trường mật khẩu (tên bắt đầu bằng ``mat_khau``) chỉ được NFC-normalize,
    không bao giờ strip khoảng trắng — một khoảng trắng ở đầu/cuối mật khẩu là
    một phần hợp lệ của mật khẩu.
    """

    @field_validator("*", mode="before")
    @classmethod
    def _normalize_nfc(cls, v, info):
        if not isinstance(v, str):
            return v
        normalized = nfc(v)
        field_name = info.field_name or ""
        if field_name.startswith("mat_khau"):
            return normalized
        return normalized.strip()


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
