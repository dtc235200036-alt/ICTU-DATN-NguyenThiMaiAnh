from datetime import date

from sqlalchemy import BigInteger, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# FR-TK-05: trạng thái đợt đồ án — mở đăng ký/đề xuất hay đã khóa.
DANG_MO = "DANG_MO"
DA_DONG = "DA_DONG"


class DotDoAn(Base):
    """UC0.3: đợt đồ án theo khóa — cổng cho mọi thao tác đề tài (§3.2.3)."""

    __tablename__ = "dot_do_an"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ten_dot: Mapped[str] = mapped_column(String(100), nullable=False)
    khoa: Mapped[str] = mapped_column(String(20), nullable=False)
    nam_hoc: Mapped[str | None] = mapped_column(String(20))
    ngay_bat_dau: Mapped[date] = mapped_column(Date, nullable=False)
    ngay_ket_thuc: Mapped[date | None] = mapped_column(Date)
    trang_thai: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=DANG_MO
    )
