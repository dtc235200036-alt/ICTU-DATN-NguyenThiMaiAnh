from datetime import date, time
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import UtcDateTime
from app.schemas.documents import CheckSummary
from app.schemas.progress import MilestoneOut, ProgressRowOut
from app.schemas.topics import CohortRef

# D-09/TOPC-04: mỗi vai trò một hình dạng riêng. Phase 2 dựng các widget đề
# tài; plan 03-07 bổ sung widget đề cương (OUTL-02), tiến độ (PROG-03) và bảo
# vệ (DEFN-04) của MH-02/03/04. Thông báo đọc qua /api/notifications.


class SvTopicOut(BaseModel):
    """MH-02: đề tài hiện tại (đang hoạt động) hoặc gần nhất của SV."""

    id: int
    ten_de_tai: str
    trang_thai: str
    giang_vien_huong_dan: str | None = None
    ly_do_tu_choi: str | None = None


class SvOutlineOut(BaseModel):
    """MH-02 "Đề cương": phiên bản mới nhất + kiểm tra trùng lặp của nó."""

    trang_thai: str
    phien_ban: int | None = None
    thoi_diem_nop: UtcDateTime | None = None
    kiem_tra: CheckSummary | None = None


class SvMilestoneStep(BaseModel):
    ten_moc: str
    han_nop: date | None = None
    trang_thai: str


class SvNextMilestone(BaseModel):
    ten_moc: str
    han_nop: date | None = None
    con_ngay: int | None = None


class SvDefenseOut(BaseModel):
    """MH-02 "Lịch và kết quả bảo vệ" — điểm CHỈ có sau khi Bộ môn chốt (T-03-40)."""

    ten_hoi_dong: str
    phong: str
    ngay_bao_ve: date
    gio_du_kien: str
    chu_tich: str | None = None
    diem_trung_binh: float | None = None


class SvDashboardOut(BaseModel):
    de_tai: SvTopicOut | None = None
    co_dot_dang_mo: bool
    de_cuong: SvOutlineOut | None = None
    tien_do: list[SvMilestoneStep] = []
    moc_tiep_theo: SvNextMilestone | None = None
    bao_ve: SvDefenseOut | None = None


class GvTopicItem(BaseModel):
    id: int
    ten_de_tai: str
    trang_thai: str
    sinh_vien: str | None = None


LoaiViec = Literal["DUYET_DE_CUONG", "NHAN_XET_TIEN_DO", "CHAM_DIEM"]


class GvTaskItem(BaseModel):
    """MH-03 "Việc cần xử lý": lien_ket là đường dẫn app do server sinh."""

    loai: LoaiViec
    sinh_vien: str | None = None
    ten_de_tai: str
    ghi_chu: str
    lien_ket: str


class GvDashboardOut(BaseModel):
    """MH-03: chỉ số + danh sách đề tài của chính GV gọi (own giang_vien_id)."""

    so_sinh_vien_huong_dan: int
    so_de_tai: int
    so_de_tai_cho_duyet: int
    de_tai: list[GvTopicItem]
    so_de_cuong_cho_duyet: int = 0
    so_bao_cao_cho_nhan_xet: int = 0
    so_hoi_dong_tham_gia: int = 0
    viec_can_xu_ly: list[GvTaskItem] = []


class BmPendingTopicRef(BaseModel):
    id: int
    ten_de_tai: str
    nguoi_de_xuat: str


class BmUpcomingCommittee(BaseModel):
    id: int
    ten_hoi_dong: str
    ngay_bao_ve: date
    gio_bao_ve: time
    phong: str
    so_sinh_vien: int


class BmProgressExcerpt(BaseModel):
    """MH-04 "Tiến độ Sinh viên (trích 5/{tong})" — 5 dòng đầu theo mã SV."""

    moc: list[MilestoneOut]
    items: list[ProgressRowOut]
    tong: int


class BmDashboardOut(BaseModel):
    """MH-04: tổng quan toàn khoa theo đợt (mặc định đợt đang mở mới nhất)."""

    dot_do_an: CohortRef | None = None
    de_tai_cho_duyet: int
    de_tai_da_phan_cong: int
    sv_chua_co_de_tai: int
    tong_sinh_vien: int
    cho_duyet_moi_nhat: list[BmPendingTopicRef]
    sv_tre_moc: int = 0
    tien_do_trich: BmProgressExcerpt | None = None
    moc_tien_do: list[MilestoneOut] = []
    so_hoi_dong_sap_toi: int = 0
    hoi_dong_sap_toi: list[BmUpcomingCommittee] = []
