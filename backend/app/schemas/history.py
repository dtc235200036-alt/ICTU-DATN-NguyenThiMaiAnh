from datetime import date

from pydantic import BaseModel

from app.schemas.common import UtcDateTime


class TopicEvent(BaseModel):
    """Một dòng "Lịch sử đề tài": ngày cập nhật, nội dung, người thực hiện."""

    thoi_diem: UtcDateTime
    noi_dung: str
    nguoi_thuc_hien: str


class SubmissionRow(BaseModel):
    """Một dòng "Lịch sử nộp" của SV (đề tài, đề cương, báo cáo tiến độ, báo cáo cuối)."""

    loai: str
    noi_dung: str
    thoi_diem_nop: UtcDateTime | None = None
    han_cuoi: date | None = None
    trang_thai: str
    trang_thai_label: str
    tai_lieu_id: int | None = None
