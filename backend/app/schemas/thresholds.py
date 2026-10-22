from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.common import NFCModel, UtcDateTime

_E1 = "Ngưỡng phải nằm trong khoảng 0–100% (UC0.4 - E1)"


class ThresholdOut(BaseModel):
    """UC0.4: một dòng cau_hinh_nguong kèm nhãn, giải thích và giá trị đề xuất
    sau hiệu chỉnh (04-04)."""

    loai: str
    nhan: str
    mo_ta: str
    gia_tri: float
    gia_tri_de_xuat: float
    # IN-02: None khi CSDL chưa có dòng (form vẫn hiện giá trị đề xuất để lưu).
    thoi_diem_cap_nhat: UtcDateTime | None = None
    nguoi_cap_nhat: str | None = None


class ThresholdUpdate(NFCModel):
    """UC0.4 (D-04): Bộ môn gửi đủ bốn ngưỡng một lần. T-04-30: 0–100, tối đa 2
    chữ số thập phân (cột DECIMAL(5,2) + CHECK 0–100 ở DB là lớp chặn thứ hai)."""

    NGUONG_TEN_DE_TAI: Decimal
    NGUONG_TAI_LIEU: Decimal
    NGUONG_TONG_TAI_LIEU: Decimal
    NGUONG_DOAN_TRUNG: Decimal

    @field_validator("NGUONG_TEN_DE_TAI", "NGUONG_TAI_LIEU", "NGUONG_TONG_TAI_LIEU", "NGUONG_DOAN_TRUNG")
    @classmethod
    def _range(cls, v: Decimal) -> Decimal:
        if not v.is_finite() or v < 0 or v > 100:
            raise ValueError(_E1)
        if v != v.quantize(Decimal("0.01")):
            raise ValueError("Ngưỡng chỉ được có tối đa 2 chữ số thập phân (UC0.4 - E1)")
        return v.quantize(Decimal("0.01"))
