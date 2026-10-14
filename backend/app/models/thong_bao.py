from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# §3.1/D-08: loại thông báo in-app cho toàn Phase 3 (mỗi UC dùng một tập con).
DE_TAI_DUYET = "DE_TAI_DUYET"
DE_TAI_PHAN_CONG = "DE_TAI_PHAN_CONG"
DE_TAI_TU_CHOI = "DE_TAI_TU_CHOI"
# UC0.8/UC1.3 (0015): Bộ môn gán SV cho GVHD; SV gửi đề tài tới GVHD duyệt.
PHAN_CONG_GVHD = "PHAN_CONG_GVHD"
DE_TAI_CHO_DUYET = "DE_TAI_CHO_DUYET"
DE_CUONG_MOI = "DE_CUONG_MOI"
DE_CUONG_DUYET = "DE_CUONG_DUYET"
DE_CUONG_YEU_CAU_SUA = "DE_CUONG_YEU_CAU_SUA"
TIEN_DO_NHAN_XET = "TIEN_DO_NHAN_XET"
HOI_DONG_PHAN_CONG = "HOI_DONG_PHAN_CONG"
LICH_BAO_VE = "LICH_BAO_VE"
KET_QUA_BAO_VE = "KET_QUA_BAO_VE"


class ThongBao(Base):
    """UC0.5/D-08: thông báo in-app — tạo trong CÙNG transaction với thay đổi
    trạng thái kích hoạt nó, không bao giờ commit riêng (§3.2.3)."""

    __tablename__ = "thong_bao"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tai_khoan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tai_khoan.id", name="fk_thong_bao_tai_khoan"), nullable=False
    )
    loai: Mapped[str] = mapped_column(String(30), nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    lien_ket: Mapped[str | None] = mapped_column(String(255))
    da_doc: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    thoi_diem: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    tai_khoan = relationship("TaiKhoan")
