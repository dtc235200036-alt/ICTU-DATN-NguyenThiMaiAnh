from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.roles import VaiTro
from app.models.base import Base


class TaiKhoan(Base):
    __tablename__ = "tai_khoan"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ma_dang_nhap: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    mat_khau_bam: Mapped[str] = mapped_column(String(255), nullable=False)
    vai_tro: Mapped[VaiTro] = mapped_column(
        Enum(VaiTro, values_callable=lambda enum_cls: [e.value for e in enum_cls], native_enum=True),
        nullable=False,
    )
    bi_khoa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    sinh_vien: Mapped["SinhVien | None"] = relationship(
        back_populates="tai_khoan", uselist=False
    )
    giang_vien: Mapped["GiangVien | None"] = relationship(
        back_populates="tai_khoan", uselist=False
    )


class SinhVien(Base):
    __tablename__ = "sinh_vien"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tai_khoan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tai_khoan.id"), unique=True, nullable=False
    )
    ma_so_sinh_vien: Mapped[str | None] = mapped_column(String(20), unique=True)
    ho_ten: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(150))
    lop: Mapped[str | None] = mapped_column(String(50))
    khoa: Mapped[str | None] = mapped_column(String(100))

    tai_khoan: Mapped["TaiKhoan"] = relationship(back_populates="sinh_vien")


class GiangVien(Base):
    __tablename__ = "giang_vien"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tai_khoan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tai_khoan.id"), unique=True, nullable=False
    )
    ma_giang_vien: Mapped[str | None] = mapped_column(String(20), unique=True)
    ho_ten: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(150))
    hoc_vi: Mapped[str | None] = mapped_column(String(50))

    tai_khoan: Mapped["TaiKhoan"] = relationship(back_populates="giang_vien")
