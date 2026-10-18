from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DinhHuong(Base):
    """Danh mục định hướng đề tài của Bộ môn (H01, H02, ...) — thay cho trường
    lĩnh vực tự do; mã định hướng là phần đầu tên file đề cương
    (<Mã định hướng>.<MSSV>.<Họ tên>.<Lớp>)."""

    __tablename__ = "dinh_huong"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ma: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    ten: Mapped[str] = mapped_column(String(255), nullable=False)
    mo_ta: Mapped[str | None] = mapped_column(Text)
    hoat_dong: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
