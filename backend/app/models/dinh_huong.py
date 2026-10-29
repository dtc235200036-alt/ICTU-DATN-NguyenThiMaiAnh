from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# 0019: thư mục con dưới UPLOAD_DIR chứa file PDF mô tả định hướng.
THU_MUC_TEP_DINH_HUONG = "DINH_HUONG"


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
    # 0019: file PDF mô tả định hướng do Bộ môn tải lên (mỗi định hướng tối đa
    # một file, tải lên lại là thay). Không dùng tai_lieu_do_an vì bảng đó gắn
    # với một đề tài; NULL cả bốn cột khi chưa có file.
    tep_ten_goc: Mapped[str | None] = mapped_column(String(255))
    tep_ten_luu_tru: Mapped[str | None] = mapped_column(String(255), unique=True)
    tep_kich_thuoc: Mapped[int | None] = mapped_column(BigInteger)
    tep_cap_nhat_luc: Mapped[datetime | None] = mapped_column(DateTime)
