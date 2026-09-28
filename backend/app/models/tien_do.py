from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# UC3.3: mức đánh giá của GVHD cho một báo cáo tiến độ.
DAT = "DAT"
CAN_CAI_THIEN = "CAN_CAI_THIEN"
CHUA_DAT = "CHUA_DAT"
DANH_GIA_LABELS = {DAT: "Đạt", CAN_CAI_THIEN: "Cần cải thiện", CHUA_DAT: "Chưa đạt"}

# D-05: trạng thái của một (đề tài, mốc) — LUÔN tính từ ngày, không lưu DB.
DUNG_HAN = "DUNG_HAN"
NOP_TRE = "NOP_TRE"
TRE_MOC = "TRE_MOC"
CHUA_DEN_HAN = "CHUA_DEN_HAN"


class MocTienDo(Base):
    """UC3.1: một mốc tiến độ (tên + hạn nộp) do Bộ môn đặt cho một đợt (§3.2.3)."""

    __tablename__ = "moc_tien_do"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dot_do_an_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dot_do_an.id", name="fk_moc_tien_do_dot_do_an"), nullable=False
    )
    ten_moc: Mapped[str] = mapped_column(String(100), nullable=False)
    thu_tu: Mapped[int] = mapped_column(Integer, nullable=False)
    han_nop: Mapped[date | None] = mapped_column(Date)

    dot_do_an = relationship("DotDoAn")


class BaoCaoTienDo(Base):
    """UC3.2/UC3.3: một báo cáo cho mỗi (đề tài, mốc) — nộp lại trước khi GVHD
    nhận xét thì ghi đè cùng dòng; tai_lieu_do_an_id (cột bổ sung Phase 3)
    trỏ tới phiên bản tệp đính kèm mới nhất (tùy chọn)."""

    __tablename__ = "bao_cao_tien_do"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_tai_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("de_tai.id", name="fk_bao_cao_tien_do_de_tai"), nullable=False
    )
    moc_tien_do_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("moc_tien_do.id", name="fk_bao_cao_tien_do_moc"), nullable=False
    )
    noi_dung: Mapped[str | None] = mapped_column(Text)
    thoi_diem_nop: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    nhan_xet: Mapped[str | None] = mapped_column(Text)
    danh_gia: Mapped[str | None] = mapped_column(String(20))
    tai_lieu_do_an_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tai_lieu_do_an.id", name="fk_bao_cao_tien_do_tai_lieu")
    )

    de_tai = relationship("DeTai")
    moc = relationship("MocTienDo")
    tai_lieu = relationship("TaiLieuDoAn")
