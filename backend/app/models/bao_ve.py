from datetime import date, time
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# §3.1.5/D-06: vai trò thành viên hội đồng bảo vệ.
CHU_TICH = "CHU_TICH"
THU_KY = "THU_KY"
UY_VIEN = "UY_VIEN"

# UC4.2/MH-11: mỗi SV kế tiếp trong cùng hội đồng bảo vệ cách nhau 30 phút,
# tính từ hoi_dong.gio_bao_ve theo thu_tu (giờ hiển thị là suy ra, không lưu).
SLOT_MINUTES = 30


class HoiDong(Base):
    """UC4.2: một hội đồng bảo vệ do Bộ môn lập — tên, ngày/giờ/phòng, thành
    viên và các SV được xếp lịch bảo vệ trong buổi đó (§3.2.3)."""

    __tablename__ = "hoi_dong"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ten_hoi_dong: Mapped[str] = mapped_column(String(150), nullable=False)
    ngay_bao_ve: Mapped[date] = mapped_column(Date, nullable=False)
    gio_bao_ve: Mapped[time] = mapped_column(Time, nullable=False)
    phong: Mapped[str] = mapped_column(String(50), nullable=False)

    thanh_vien: Mapped[list["ThanhVienHoiDong"]] = relationship(
        back_populates="hoi_dong", cascade="all, delete-orphan"
    )
    lich: Mapped[list["LichBaoVe"]] = relationship(
        back_populates="hoi_dong", order_by="LichBaoVe.thu_tu"
    )


class ThanhVienHoiDong(Base):
    """UC4.2: một thành viên (GV) của một hội đồng, đúng một vai trò
    CHU_TICH/THU_KY/UY_VIEN — không lặp lại GV trong cùng hội đồng (§3.2.3)."""

    __tablename__ = "thanh_vien_hoi_dong"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hoi_dong_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("hoi_dong.id", name="fk_thanh_vien_hoi_dong_hoi_dong"),
        nullable=False,
    )
    giang_vien_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("giang_vien.id", name="fk_thanh_vien_hoi_dong_giang_vien"),
        nullable=False,
    )
    vai_tro: Mapped[str] = mapped_column(String(20), nullable=False)

    hoi_dong = relationship("HoiDong", back_populates="thanh_vien")
    giang_vien = relationship("GiangVien")


class LichBaoVe(Base):
    """UC4.2/D-06: một SV được xếp vào một hội đồng — UNIQUE(sinh_vien_id)
    đảm bảo mỗi SV chỉ có đúng một lịch bảo vệ dù xếp đồng thời (§3.2.5.c)."""

    __tablename__ = "lich_bao_ve"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hoi_dong_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hoi_dong.id", name="fk_lich_bao_ve_hoi_dong"), nullable=False
    )
    de_tai_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("de_tai.id", name="fk_lich_bao_ve_de_tai"), nullable=False
    )
    sinh_vien_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sinh_vien.id", name="fk_lich_bao_ve_sinh_vien"),
        unique=True,
        nullable=False,
    )
    thu_tu: Mapped[int | None] = mapped_column(Integer)
    diem_trung_binh: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    da_chot: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    hoi_dong = relationship("HoiDong", back_populates="lich")
    de_tai = relationship("DeTai")
    sinh_vien = relationship("SinhVien")
    diem: Mapped[list["DiemBaoVe"]] = relationship(back_populates="lich_bao_ve")


class DiemBaoVe(Base):
    """UC4.3 (plan 03-04): điểm một thành viên hội đồng chấm cho một SV đã
    xếp lịch — đúng một điểm mỗi (lich_bao_ve, giang_vien) (§3.2.5.c)."""

    __tablename__ = "diem_bao_ve"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lich_bao_ve_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("lich_bao_ve.id", name="fk_diem_bao_ve_lich_bao_ve"),
        nullable=False,
    )
    giang_vien_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("giang_vien.id", name="fk_diem_bao_ve_giang_vien"), nullable=False
    )
    diem: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    nhan_xet: Mapped[str | None] = mapped_column(Text)

    lich_bao_ve = relationship("LichBaoVe", back_populates="diem")
    giang_vien = relationship("GiangVien")
