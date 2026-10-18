from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# §3.1.3/trang-thai-de-cuong.puml: trạng thái đề cương — một chiều
# CHUA_NOP -> CHO_DUYET (chờ GVHD) -> GVHD_DA_DUYET -> CHO_BO_MON_DUYET
# -> DA_DUYET (Lãnh đạo bộ môn phê duyệt, file ký số đã nộp về khoa).
# GVHD hoặc Bộ môn trả lại -> YEU_CAU_SUA -> CHO_DUYET -> ...
# DA_DUYET luôn là trạng thái cuối — tiến độ/bảo vệ chỉ mở khi đã tới đây.
# Tiền tố DC_ tránh trùng với hằng số CHO_DUYET/DA_DUYET của de_tai.py.
DC_CHUA_NOP = "CHUA_NOP"
DC_CHO_DUYET = "CHO_DUYET"
DC_YEU_CAU_SUA = "YEU_CAU_SUA"
DC_GVHD_DA_DUYET = "GVHD_DA_DUYET"
DC_CHO_BO_MON_DUYET = "CHO_BO_MON_DUYET"
DC_DA_DUYET = "DA_DUYET"

# §3.1.3: loại tài liệu — dùng chung cho đề cương, báo cáo tiến độ, báo cáo
# cuối và bản ghi lưu kho (Phase 3 mở rộng theo từng plan).
LOAI_DE_CUONG = "DE_CUONG"
LOAI_BAO_CAO_TIEN_DO = "BAO_CAO_TIEN_DO"
LOAI_BAO_CAO_CUOI = "BAO_CAO_CUOI"
LOAI_KHO = "KHO"
# 0016: bản đề cương đã ký số do Lãnh đạo bộ môn nộp về khoa; file đính kèm
# GVHD gửi kèm khi giao đề tài.
LOAI_DE_CUONG_KY_SO = "DE_CUONG_KY_SO"
LOAI_DE_TAI = "DE_TAI"

DOCX = "DOCX"
PDF = "PDF"

# luot_duyet_de_cuong.ket_qua
KET_QUA_DA_DUYET = "DA_DUYET"
KET_QUA_YEU_CAU_SUA = "YEU_CAU_SUA"
# luot_duyet_bo_mon.ket_qua
KET_QUA_TRA_LAI = "TRA_LAI"


class DeCuong(Base):
    """UC2: đề cương của một đề tài — một de_tai có tối đa một de_cuong (§3.2.3)."""

    __tablename__ = "de_cuong"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_tai_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("de_tai.id", name="fk_de_cuong_de_tai"), nullable=False
    )
    trang_thai: Mapped[str] = mapped_column(String(20), nullable=False)
    ngay_nop_dau_tien: Mapped[datetime | None] = mapped_column(DateTime)
    # 0016: lần GVHD nộp lên Bộ môn gần nhất và kết quả Bộ môn gần nhất
    # (DA_DUYET/TRA_LAI; xóa khi SV nộp phiên bản mới).
    nop_bo_mon_luc: Mapped[datetime | None] = mapped_column(DateTime)
    ket_qua_bo_mon: Mapped[str | None] = mapped_column(String(20))

    de_tai = relationship("DeTai")
    phien_ban: Mapped[list["TaiLieuDoAn"]] = relationship(
        back_populates="de_cuong", order_by="TaiLieuDoAn.so_phien_ban.desc()"
    )
    luot_duyet: Mapped[list["LuotDuyetDeCuong"]] = relationship(back_populates="de_cuong")


class TaiLieuDoAn(Base):
    """UC2/UC3/UC4/UC5: một phiên bản tài liệu (đề cương, báo cáo tiến độ,
    báo cáo cuối hoặc bản ghi lưu kho) gắn với một đề tài (§3.2.3)."""

    __tablename__ = "tai_lieu_do_an"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_tai_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("de_tai.id", name="fk_tai_lieu_do_an_de_tai"), nullable=False
    )
    de_cuong_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("de_cuong.id", name="fk_tai_lieu_do_an_de_cuong")
    )
    loai: Mapped[str] = mapped_column(String(20), nullable=False)
    so_phien_ban: Mapped[int] = mapped_column(Integer, nullable=False)
    ten_goc: Mapped[str] = mapped_column(String(255), nullable=False)
    ten_luu_tru: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    kich_thuoc: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dinh_dang: Mapped[str] = mapped_column(String(10), nullable=False)
    thoi_diem_nop: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # D-03/Pitfall 3 (03-RESEARCH.md): cột bổ sung ngoài §3.2.3 gốc — đã ghi
    # ngược lại erd.puml/lop-thuc-the.puml/02-thiet-ke-csdl.md cùng migration 0006.
    noi_dung_trich_xuat: Mapped[str | None] = mapped_column(LONGTEXT)
    trich_xuat_loi: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    # WR-06 (04-REVIEW, 0014): lần ingest DOCUMENT thành công gần nhất vào chỉ
    # mục AI; NULL = chưa vào chỉ mục (được thử lại, đếm trên dashboard Bộ môn).
    da_index_luc: Mapped[datetime | None] = mapped_column(DateTime)
    # 0016: ghi chú người nộp kèm phiên bản (MH SV "Nộp đề cương").
    ghi_chu: Mapped[str | None] = mapped_column(Text)

    de_tai = relationship("DeTai")
    de_cuong = relationship("DeCuong", back_populates="phien_ban")
    ket_qua_kiem_tra = relationship(
        "KetQuaKiemTraTrungLap", uselist=False, viewonly=True,
        primaryjoin=(
            "TaiLieuDoAn.id == foreign(KetQuaKiemTraTrungLap.tai_lieu_do_an_id)"
        ),
    )
    luot_duyet: Mapped["LuotDuyetDeCuong | None"] = relationship(
        back_populates="tai_lieu", uselist=False
    )


class LuotDuyetDeCuong(Base):
    """UC2.2: một lượt duyệt (Đã duyệt/Yêu cầu sửa) của GVHD cho một phiên
    bản đề cương cụ thể — mỗi phiên bản có nhiều nhất một lượt duyệt (§3.2.3)."""

    __tablename__ = "luot_duyet_de_cuong"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_cuong_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("de_cuong.id", name="fk_luot_duyet_de_cuong_de_cuong"),
        nullable=False,
    )
    tai_lieu_do_an_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tai_lieu_do_an.id", name="fk_luot_duyet_de_cuong_tai_lieu"),
        nullable=False,
        unique=True,
    )
    giang_vien_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("giang_vien.id", name="fk_luot_duyet_de_cuong_giang_vien"),
        nullable=False,
    )
    ket_qua: Mapped[str] = mapped_column(String(20), nullable=False)
    nhan_xet: Mapped[str | None] = mapped_column(Text)
    thoi_diem: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    de_cuong = relationship("DeCuong", back_populates="luot_duyet")
    tai_lieu = relationship("TaiLieuDoAn", back_populates="luot_duyet")
    giang_vien = relationship("GiangVien")


class LuotDuyetBoMon(Base):
    """Lãnh đạo bộ môn phê duyệt (kèm file đề cương đã ký số) hoặc trả lại một
    phiên bản đề cương GVHD đã nộp lên — mỗi lần nộp lên có một lượt."""

    __tablename__ = "luot_duyet_bo_mon"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    de_cuong_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("de_cuong.id", name="fk_luot_duyet_bo_mon_de_cuong"),
        nullable=False,
    )
    tai_lieu_do_an_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tai_lieu_do_an.id", name="fk_luot_duyet_bo_mon_tai_lieu"),
        nullable=False,
    )
    tai_khoan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tai_khoan.id", name="fk_luot_duyet_bo_mon_tai_khoan"),
        nullable=False,
    )
    ket_qua: Mapped[str] = mapped_column(String(20), nullable=False)
    nhan_xet: Mapped[str | None] = mapped_column(Text)
    thoi_diem: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    tai_lieu_ky_so_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tai_lieu_do_an.id", name="fk_luot_duyet_bo_mon_ky_so")
    )
    nguoi_ky: Mapped[str | None] = mapped_column(String(255))
    thoi_diem_ky: Mapped[datetime | None] = mapped_column(DateTime)

    de_cuong = relationship("DeCuong")
    tai_lieu = relationship("TaiLieuDoAn", foreign_keys=[tai_lieu_do_an_id])
    tai_lieu_ky_so = relationship("TaiLieuDoAn", foreign_keys=[tai_lieu_ky_so_id])
    tai_khoan = relationship("TaiKhoan")
