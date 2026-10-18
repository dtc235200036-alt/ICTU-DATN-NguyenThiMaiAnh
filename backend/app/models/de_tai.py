from sqlalchemy import BigInteger, Computed, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# §3.1.2 / FR-DT-07: 5 trạng thái đề tài.
NHAP = "NHAP"
CHO_DUYET = "CHO_DUYET"
DA_DUYET = "DA_DUYET"
TU_CHOI = "TU_CHOI"
DA_PHAN_CONG = "DA_PHAN_CONG"

TRANG_THAI_HOAT_DONG = (CHO_DUYET, DA_DUYET, DA_PHAN_CONG)

# Người đề xuất là GV hoặc SV (D-04).
GIANG_VIEN = "GIANG_VIEN"
SINH_VIEN = "SINH_VIEN"


class DeTai(Base):
    """UC1.1: đề tài đề xuất/đăng ký — cổng nghiệp vụ chính của quy trình đồ án (§3.2.3)."""

    __tablename__ = "de_tai"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dot_do_an_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dot_do_an.id", name="fk_de_tai_dot_do_an"), nullable=False
    )
    giang_vien_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("giang_vien.id", name="fk_de_tai_giang_vien")
    )
    sinh_vien_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sinh_vien.id", name="fk_de_tai_sinh_vien")
    )
    # Cột sinh (D-05, §3.2.5) — ORM không bao giờ tự ghi cột này, chỉ đọc lại.
    sinh_vien_id_dang_hoat_dong: Mapped[int | None] = mapped_column(
        BigInteger,
        Computed(
            "CASE WHEN trang_thai IN ('CHO_DUYET','DA_DUYET','DA_PHAN_CONG')"
            " THEN sinh_vien_id END",
            persisted=True,
        ),
    )
    ten_de_tai: Mapped[str] = mapped_column(String(255), nullable=False)
    mo_ta: Mapped[str | None] = mapped_column(Text)
    linh_vuc: Mapped[str | None] = mapped_column(String(100))
    # 0016: định hướng (H01, H02, ...) thay cho lĩnh vực; NULL ở đề tài cũ.
    dinh_huong_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("dinh_huong.id", name="fk_de_tai_dinh_huong")
    )
    trang_thai: Mapped[str] = mapped_column(String(20), nullable=False)
    loai_nguoi_de_xuat: Mapped[str] = mapped_column(String(10), nullable=False)
    ly_do_tu_choi: Mapped[str | None] = mapped_column(Text)

    dot_do_an = relationship("DotDoAn")
    giang_vien = relationship("GiangVien")
    sinh_vien = relationship("SinhVien")
    dinh_huong = relationship("DinhHuong")
