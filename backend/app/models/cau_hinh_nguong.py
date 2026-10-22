from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# UC0.4/D-10: mỗi loại ngưỡng đúng 1 dòng hiện hành (UNIQUE loai).
NGUONG_TEN_DE_TAI = "NGUONG_TEN_DE_TAI"
NGUONG_TAI_LIEU = "NGUONG_TAI_LIEU"
# D-04 (Phase 4, Alembic 0010): ngưỡng ngữ nghĩa từng đoạn/câu (cosine×100)
# gửi sang /check-document dưới tên nguong_doan.
NGUONG_DOAN_TRUNG = "NGUONG_DOAN_TRUNG"
# Alembic 0017: tỷ lệ tổng mọi nguồn (ty_le_tong) từ giá trị này trở lên cũng là
# "Vượt ngưỡng cảnh báo" — bài ghép từ nhiều đồ án, mỗi đồ án dưới NGUONG_TAI_LIEU.
NGUONG_TONG_TAI_LIEU = "NGUONG_TONG_TAI_LIEU"


class CauHinhNguong(Base):
    """UC0.4: ngưỡng cảnh báo trùng lặp do Bộ môn cấu hình (§3.2.3)."""

    __tablename__ = "cau_hinh_nguong"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    loai: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    gia_tri: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tai_khoan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tai_khoan.id", name="fk_cau_hinh_nguong_tai_khoan")
    )
    thoi_diem_cap_nhat: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    tai_khoan = relationship("TaiKhoan")
