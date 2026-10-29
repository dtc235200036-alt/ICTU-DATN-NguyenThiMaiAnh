from pydantic import BaseModel, Field

from app.schemas.common import NFCModel, UtcDateTime


class TepDinhHuongOut(BaseModel):
    """0019: file PDF mô tả định hướng — xem/tải qua GET /api/dinh-huong/{id}/tep."""

    ten_goc: str
    kich_thuoc: int
    cap_nhat_luc: UtcDateTime


class DinhHuongOut(BaseModel):
    id: int
    ma: str
    ten: str
    mo_ta: str | None = None
    hoat_dong: bool
    so_de_tai: int = 0
    tep: TepDinhHuongOut | None = None


class DinhHuongIn(NFCModel):
    """Bộ môn thêm/sửa một định hướng — mã dạng H + 2 chữ số (H01, H02, ...)."""

    ma: str = Field(pattern=r"^[Hh]\d{2}$")
    ten: str = Field(min_length=2, max_length=255)
    mo_ta: str | None = Field(default=None, max_length=2000)
    hoat_dong: bool = True
