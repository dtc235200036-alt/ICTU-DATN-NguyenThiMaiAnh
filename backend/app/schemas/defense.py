from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NFCModel
from app.schemas.documents import CheckSummary, DocumentOut
from app.schemas.topics import PersonRef

VaiTroThanhVien = Literal["CHU_TICH", "THU_KY", "UY_VIEN"]


class MemberIn(NFCModel):
    """UC4.2: một dòng thành viên hội đồng trong payload tạo/sửa."""

    giang_vien_id: int
    vai_tro: VaiTroThanhVien


class CommitteeIn(NFCModel):
    """UC4.2: tạo hoặc sửa một hội đồng — 3-5 thành viên, kiểm tra thêm ở
    services/defense.py (đúng 1 Chủ tịch, tối đa 1 Thư ký, GV tồn tại/chưa khóa)."""

    ten_hoi_dong: str = Field(min_length=1, max_length=150)
    ngay_bao_ve: date
    gio_bao_ve: time
    phong: str = Field(min_length=1, max_length=50)
    thanh_vien: list[MemberIn] = Field(min_length=3, max_length=5)


class MemberOut(BaseModel):
    giang_vien: PersonRef
    hoc_vi: str | None = None
    vai_tro: VaiTroThanhVien


class ScheduleRow(BaseModel):
    """MH-11: một dòng SV trong bảng "Sinh viên bảo vệ" của một hội đồng."""

    id: int
    thu_tu: int | None = None
    gio_du_kien: str
    sinh_vien: PersonRef
    de_tai_id: int
    ten_de_tai: str
    giang_vien_huong_dan: PersonRef | None = None
    so_da_cham: int
    so_thanh_vien: int
    diem_tam_tinh: float | None = None
    diem_trung_binh: float | None = None
    da_chot: bool
    bao_cao_cuoi: DocumentOut | None = None
    kiem_tra: CheckSummary | None = None


class CommitteeOut(BaseModel):
    id: int
    ten_hoi_dong: str
    ngay_bao_ve: date
    gio_bao_ve: time
    phong: str
    thanh_vien: list[MemberOut]
    lich: list[ScheduleRow]


class CommitteeListItem(BaseModel):
    id: int
    ten_hoi_dong: str
    ngay_bao_ve: date
    gio_bao_ve: time
    phong: str
    chu_tich: PersonRef | None = None
    so_thanh_vien: int
    so_sinh_vien: int


class EligibleStudent(BaseModel):
    """UC4.2: một đề tài đủ điều kiện xếp lịch bảo vệ (đã nộp báo cáo cuối,
    chưa xếp lịch)."""

    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef
    giang_vien_huong_dan: PersonRef | None = None
    giang_vien_id: int | None = None
    bao_cao_cuoi: DocumentOut
    kiem_tra: CheckSummary | None = None


class ScheduleIn(NFCModel):
    de_tai_id: int


class FinalReportVersion(BaseModel):
    tai_lieu: DocumentOut
    kiem_tra: CheckSummary | None = None


class QuyenBaoCaoCuoiOut(BaseModel):
    nop: bool


class FinalReportDetail(BaseModel):
    """MH-08 (tab "Báo cáo cuối"): UC4.1 — không có vòng lặp sửa như đề
    cương, mọi phiên bản mới nhất trước."""

    de_tai_id: int
    ten_de_tai: str
    trang_thai_de_cuong: str
    da_xep_lich: bool
    phien_ban: list[FinalReportVersion]
    quyen: QuyenBaoCaoCuoiOut
