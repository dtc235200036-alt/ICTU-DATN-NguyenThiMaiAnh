from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# §3.1.4 / D-10: loại kiểm tra và trạng thái kết quả kiểm tra trùng lặp.
TEN_DE_TAI = "TEN_DE_TAI"
TAI_LIEU = "TAI_LIEU"

# WR-06: không gian id của nguồn trùng (khớp dịch vụ AI, §3.3.5).
NGUON_TOPIC = "TOPIC"  # de_tai.id
NGUON_ARCHIVE = "ARCHIVE"  # do_an_kho.id
NGUON_DOCUMENT = "DOCUMENT"  # tai_lieu_do_an.id

DANG_KIEM_TRA = "DANG_KIEM_TRA"
HOAN_TAT = "HOAN_TAT"
LOI = "LOI"


class KetQuaKiemTraTrungLap(Base):
    """UC0.6: kết quả kiểm tra trùng lặp đã lưu (tên đề tài hoặc tài liệu, §3.2.3)."""

    __tablename__ = "ket_qua_kiem_tra_trung_lap"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_tai_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("de_tai.id", name="fk_ket_qua_kttl_de_tai")
    )
    tai_lieu_do_an_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tai_lieu_do_an.id", name="fk_ket_qua_kttl_tai_lieu_do_an"),
    )
    loai_kiem_tra: Mapped[str] = mapped_column(String(20), nullable=False)
    trang_thai: Mapped[str] = mapped_column(String(20), nullable=False)
    ty_le_tong: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    # CR-01 (04-REVIEW, 0012): tỷ lệ trùng với MỘT đồ án nguồn cao nhất — đúng
    # thống kê NGUONG_TAI_LIEU được hiệu chỉnh; ty_le_tong chỉ để hiển thị.
    ty_le_nguon_cao_nhat: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    nguong_ap_dung: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    doi_tuong_duoc_kiem_tra: Mapped[str | None] = mapped_column(String(255))
    thoi_diem: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    de_tai = relationship("DeTai")
    chi_tiet: Mapped[list["ChiTietTrungLap"]] = relationship(
        back_populates="ket_qua", order_by="ChiTietTrungLap.ty_le.desc()"
    )


class ChiTietTrungLap(Base):
    """UC0.6: một dòng chi tiết (đề tài/đồ án trùng) trong một kết quả kiểm tra."""

    __tablename__ = "chi_tiet_trung_lap"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ket_qua_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ket_qua_kiem_tra_trung_lap.id", name="fk_chi_tiet_trung_lap_ket_qua"),
        nullable=False,
    )
    doi_tuong_trung: Mapped[str] = mapped_column(String(255), nullable=False)
    ty_le: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    doan_nguon: Mapped[str | None] = mapped_column(Text)
    doan_trung: Mapped[str | None] = mapped_column(Text)
    vi_tri: Mapped[str | None] = mapped_column(String(50))
    # WR-06 (0011): nguồn của đoạn trùng — không gian id AI + id trong không
    # gian đó; không FK (tham chiếu đa hình, nguồn có thể bị xóa sau này).
    loai_nguon: Mapped[str | None] = mapped_column(String(20))
    nguon_id: Mapped[int | None] = mapped_column(BigInteger)
    # CR-01 (0012): tỷ lệ theo nguồn (do_an_trung của AI) của nguồn chứa đoạn.
    ty_le_nguon: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    ket_qua: Mapped[KetQuaKiemTraTrungLap] = relationship(back_populates="chi_tiet")
