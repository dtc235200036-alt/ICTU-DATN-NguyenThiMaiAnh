from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NFCModel, UtcDateTime
from app.schemas.documents import CheckSummary, DocumentOut
from app.schemas.topics import PersonRef


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


class QuyenDeCuongOut(BaseModel):
    nop: bool
    duyet: bool


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


class OutlineListItem(BaseModel):
    """MH-08/MH-09: một dòng trong danh sách đề cương (SV/GV/Bộ môn)."""

    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef | None = None
    giang_vien: PersonRef | None = None
    trang_thai: str
    phien_ban_moi_nhat: DocumentOut | None = None
    kiem_tra: CheckSummary | None = None


class ReviewRequest(NFCModel):
    """UC2.2: duyệt hoặc yêu cầu sửa một phiên bản đề cương cụ thể."""

    tai_lieu_do_an_id: int
    ket_qua: Literal["DA_DUYET", "YEU_CAU_SUA"]
    nhan_xet: str | None = Field(default=None, max_length=5000)
