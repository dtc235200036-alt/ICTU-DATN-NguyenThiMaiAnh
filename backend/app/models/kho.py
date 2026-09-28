from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# §3.2.3/D-07: nguồn bản ghi kho — tự động khi chốt bảo vệ hoặc import khóa cũ.
HE_THONG = "HE_THONG"
IMPORT = "IMPORT"

# UC5.2 E1/MH-13: đã đẩy sang Dịch vụ AI để index hay chưa ("Đã index" /
# "Chưa index") — lỗi AI không bao giờ chặn lưu kho, Bộ môn index lại sau.
CHUA_INDEX = "CHUA_INDEX"
DA_INDEX = "DA_INDEX"


class DoAnKho(Base):
    """UC5/REPO-01..03: một đồ án trong kho của khoa — HE_THONG (tự chèn khi
    Bộ môn chốt kết quả bảo vệ) hoặc IMPORT (khóa cũ, không có de_tai_id).
    ma_so_sinh_vien/ho_ten_sinh_vien là ảnh chụp danh tính SV tại thời điểm
    lưu kho (bản ghi import không có tài khoản SV) — cột bổ sung Phase 3."""

    __tablename__ = "do_an_kho"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_tai_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("de_tai.id", name="fk_do_an_kho_de_tai"), unique=True
    )
    sinh_vien_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sinh_vien.id", name="fk_do_an_kho_sinh_vien")
    )
    giang_vien_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("giang_vien.id", name="fk_do_an_kho_giang_vien")
    )
    khoa: Mapped[str | None] = mapped_column(String(20))
    ten_de_tai: Mapped[str] = mapped_column(String(255), nullable=False)
    tu_khoa: Mapped[str | None] = mapped_column(String(255))
    diem: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    nguon: Mapped[str] = mapped_column(String(20), nullable=False)
    trang_thai_index: Mapped[str] = mapped_column(String(20), nullable=False)
    ma_so_sinh_vien: Mapped[str | None] = mapped_column(String(20))
    ho_ten_sinh_vien: Mapped[str | None] = mapped_column(String(150))

    de_tai = relationship("DeTai")
    sinh_vien = relationship("SinhVien")
    giang_vien = relationship("GiangVien")
