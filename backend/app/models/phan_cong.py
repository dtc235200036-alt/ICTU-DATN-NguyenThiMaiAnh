from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PhanCongHuongDan(Base):
    """UC0.8: Bộ môn gán mỗi SV cho đúng MỘT GVHD trong một đợt đồ án — "lớp"
    hướng dẫn của GV. SV chỉ làm việc với GVHD của mình: đề xuất đề tài gửi tới
    GVHD duyệt, chỉ thấy/đăng ký đề tài GVHD của mình mở cho lớp."""

    __tablename__ = "phan_cong_huong_dan"
    __table_args__ = (
        UniqueConstraint("dot_do_an_id", "sinh_vien_id", name="uk_phan_cong_sv_dot"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dot_do_an_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dot_do_an.id", name="fk_phan_cong_dot_do_an"),
        nullable=False,
    )
    sinh_vien_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sinh_vien.id", name="fk_phan_cong_sinh_vien"),
        nullable=False,
    )
    giang_vien_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("giang_vien.id", name="fk_phan_cong_giang_vien"),
        nullable=False,
    )
    thoi_diem: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    dot_do_an = relationship("DotDoAn")
    sinh_vien = relationship("SinhVien")
    giang_vien = relationship("GiangVien")
