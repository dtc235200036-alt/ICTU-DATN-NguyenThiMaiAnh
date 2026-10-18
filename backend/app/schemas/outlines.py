from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NFCModel, UtcDateTime
from app.schemas.documents import CheckSummary, DocumentOut
from app.schemas.topics import DinhHuongRef, PersonRef


class ReviewOut(BaseModel):
    """UC2.2: một lượt duyệt đã lưu, gắn với đúng một phiên bản đề cương."""

    ket_qua: str
    nhan_xet: str | None = None
    thoi_diem: UtcDateTime
    giang_vien: PersonRef


class OutlineVersion(BaseModel):
    """UC2.3: một phiên bản trong lịch sử — tài liệu + kiểm tra + lượt duyệt riêng."""

    tai_lieu: DocumentOut
    kiem_tra: CheckSummary | None = None
    luot_duyet: ReviewOut | None = None


class BoMonReviewOut(BaseModel):
    """Một lượt Lãnh đạo bộ môn phê duyệt (kèm file ký số) hoặc trả lại."""

    ket_qua: str
    nhan_xet: str | None = None
    thoi_diem: UtcDateTime
    nguoi_duyet: str
    tai_lieu_id: int
    tai_lieu_ky_so: DocumentOut | None = None
    nguoi_ky: str | None = None
    thoi_diem_ky: UtcDateTime | None = None


class CheckItem(BaseModel):
    """Một mục kiểm tra tự động trước khi nộp lên/phê duyệt (TEN_FILE,
    DINH_HUONG, NOI_DUNG)."""

    ma: str
    ten: str
    dat: bool
    chi_tiet: str | None = None


class QuyenDeCuongOut(BaseModel):
    nop: bool
    duyet: bool
    # 0016: GVHD nộp lên Bộ môn; Lãnh đạo bộ môn phê duyệt/trả lại.
    nop_bo_mon: bool = False
    duyet_bo_mon: bool = False


class OutlineDetail(BaseModel):
    """MH-08/MH-09: chi tiết đề cương của một đề tài — mọi phiên bản mới nhất trước."""

    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef | None = None
    giang_vien: PersonRef | None = None
    trang_thai: str
    ngay_nop_dau_tien: UtcDateTime | None = None
    phien_ban: list[OutlineVersion]
    quyen: QuyenDeCuongOut
    dinh_huong: DinhHuongRef | None = None
    lop: str | None = None
    nop_bo_mon_luc: UtcDateTime | None = None
    ket_qua_bo_mon: str | None = None
    luot_duyet_bo_mon: list[BoMonReviewOut] = []
    # Kiểm tra tự động trên phiên bản mới nhất + tên file mẫu cho SV.
    kiem_tra_nop: list[CheckItem] = []
    ten_file_mau: str | None = None


class OutlineListItem(BaseModel):
    """MH-08/MH-09: một dòng trong danh sách đề cương (SV/GV/Bộ môn)."""

    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef | None = None
    giang_vien: PersonRef | None = None
    trang_thai: str
    phien_ban_moi_nhat: DocumentOut | None = None
    kiem_tra: CheckSummary | None = None
    dinh_huong: DinhHuongRef | None = None
    nop_bo_mon_luc: UtcDateTime | None = None
    ket_qua_bo_mon: str | None = None


class OutlineCounts(BaseModel):
    """Số đề cương theo tab (Bộ môn: Tất cả/Chờ duyệt/Đã duyệt/Từ chối)."""

    tat_ca: int
    theo_trang_thai: dict[str, int]
    bo_mon_tra_lai: int


class BoMonReturnRequest(NFCModel):
    nhan_xet: str = Field(min_length=1, max_length=5000)


class ReviewRequest(NFCModel):
    """UC2.2: duyệt hoặc yêu cầu sửa một phiên bản đề cương cụ thể."""

    tai_lieu_do_an_id: int
    ket_qua: Literal["DA_DUYET", "YEU_CAU_SUA"]
    nhan_xet: str | None = Field(default=None, max_length=5000)
