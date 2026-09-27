from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import NFCModel

# D-06: schema request kế thừa NFCModel (NFC-normalize + strip mọi trường).
_KHOA_PATTERN = r"^K\d{2}$"
_NAM_HOC_PATTERN = r"^\d{4}-\d{4}$"

_DATE_ORDER_DETAIL = "Ngày kết thúc phải sau ngày bắt đầu"


class _CohortFields(NFCModel):
    ten_dot: str = Field(min_length=1, max_length=100)
    khoa: str = Field(pattern=_KHOA_PATTERN)
    nam_hoc: str | None = Field(default=None, pattern=_NAM_HOC_PATTERN)
    ngay_bat_dau: date
    ngay_ket_thuc: date | None = None

    @model_validator(mode="after")
    def _check_date_order(self) -> "_CohortFields":
        if self.ngay_ket_thuc is not None and self.ngay_ket_thuc < self.ngay_bat_dau:
            raise ValueError(_DATE_ORDER_DETAIL)
        return self


class CohortCreate(_CohortFields):
    """UC0.3: mở đợt đồ án mới — trang_thai luôn khởi tạo DANG_MO ở service layer."""


class CohortUpdate(_CohortFields):
    """UC0.3: sửa thông tin đợt đồ án (không đổi trang_thai — dùng /open, /close)."""


class CohortOut(BaseModel):
    id: int
    ten_dot: str
    khoa: str
    nam_hoc: str | None = None
    ngay_bat_dau: date
    ngay_ket_thuc: date | None = None
    trang_thai: str
