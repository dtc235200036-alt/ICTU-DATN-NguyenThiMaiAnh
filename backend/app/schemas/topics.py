from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_serializer

from app.schemas.common import NFCModel

# D-06: schema request kế thừa NFCModel (NFC-normalize + strip mọi trường).


class TopicCreate(NFCModel):
    """UC1.1: GVHD tạo đề tài và giao cho `sinh_vien_id` (bắt buộc, thuộc lớp
    hướng dẫn của GV trong đợt) — gui=False lưu nháp, gui=True giao ngay (Đã
    phân công)."""

    dot_do_an_id: int
    ten_de_tai: str = Field(min_length=5, max_length=255)
    mo_ta: str | None = Field(default=None, max_length=5000)
    linh_vuc: str | None = Field(default=None, max_length=100)
    sinh_vien_id: int
    gui: bool = False


class TopicUpdate(NFCModel):
    """UC1.1: GVHD sửa đề tài Nháp (không đổi trang_thai — dùng /submit)."""

    dot_do_an_id: int
    ten_de_tai: str = Field(min_length=5, max_length=255)
    mo_ta: str | None = Field(default=None, max_length=5000)
    linh_vuc: str | None = Field(default=None, max_length=100)
    sinh_vien_id: int


class PersonRef(BaseModel):
    id: int
    ho_ten: str
    ma: str | None = None


class CohortRef(BaseModel):
    id: int
    ten_dot: str
    khoa: str
    trang_thai: str


class QuyenOut(BaseModel):
    sua: bool
    gui: bool


class TitleCheckRequest(NFCModel):
    """UC0.6: kiểm tra trùng tên tức thời (không lưu kết quả) — dùng khi rời ô Tên đề tài."""

    ten_de_tai: str = Field(min_length=5, max_length=255)


class TitleMatch(BaseModel):
    """AISV-03: nguon DE_TAI = đề tài hiện hành (de_tai_id), KHO = đồ án
    trong kho các khóa trước (do_an_kho_id; de_tai_id khi bản ghi kho liên kết
    một đề tài của hệ thống)."""

    nguon: Literal["DE_TAI", "KHO"] = "DE_TAI"
    de_tai_id: int | None = None
    do_an_kho_id: int | None = None
    ten_de_tai: str
    khoa: str
    giang_vien: str | None = None
    ty_le: float


class TitleCheckResult(BaseModel):
    """§3.3.5 hình dạng /check-title sau khi Web API lọc theo cau_hinh_nguong."""

    trang_thai: str
    nguong: float
    matches: list[TitleMatch]


class SavedChiTietTrungLap(BaseModel):
    doi_tuong_trung: str
    ty_le: float


class SavedTitleCheck(BaseModel):
    """UC1.1/A2, MH-07: kết quả kiểm tra trùng tên đã lưu tại thời điểm GVHD giao đề tài."""

    trang_thai: str
    ty_le_tong: float | None = None
    nguong_ap_dung: float
    thoi_diem: datetime
    chi_tiet: list[SavedChiTietTrungLap]

    @field_serializer("thoi_diem")
    def _serialize_utc(self, value: datetime) -> str:
        # D-06/NFR-14 tương tự: thoi_diem lưu là UTC naive — gắn lại tzinfo=UTC
        # trước khi xuất ISO-8601 để frontend quy đổi đúng sang Asia/Ho_Chi_Minh.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class TopicOut(BaseModel):
    id: int
    dot_do_an: CohortRef
    ten_de_tai: str
    mo_ta: str | None = None
    linh_vuc: str | None = None
    trang_thai: str
    loai_nguoi_de_xuat: str
    nguoi_de_xuat: PersonRef
    giang_vien_huong_dan: PersonRef | None = None
    sinh_vien: PersonRef | None = None
    ly_do_tu_choi: str | None = None
    quyen: QuyenOut
    kiem_tra_ten: SavedTitleCheck | None = None


class TopicListItem(BaseModel):
    """UC1.2/MH-05: một dòng trong danh sách đề tài — chỉ các trường bảng cần."""

    id: int
    ten_de_tai: str
    linh_vuc: str | None = None
    trang_thai: str
    dot_do_an: CohortRef
    nguoi_de_xuat: PersonRef
    giang_vien_huong_dan: PersonRef | None = None
    sinh_vien: PersonRef | None = None


@dataclass
class TopicListParams:
    """Tham số truy vấn GET /api/topics — đã được FastAPI Query() validate/ép
    kiểu (enum trang_thai/pham_vi/sap_xep) trước khi tới đây (T-02-33)."""

    dot_do_an_id: int | None = None
    trang_thai: str | None = None
    giang_vien_id: int | None = None
    linh_vuc: str | None = None
    q: str | None = None
    pham_vi: str = "tat_ca"
    sap_xep: str = "moi_nhat"
    page: int = 1
    page_size: int = 10
