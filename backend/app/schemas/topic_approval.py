from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_serializer

from app.schemas.common import NFCModel
from app.schemas.topics import CohortRef, PersonRef

# UC1.3/MH-07: 3 trạng thái hiển thị cho Bộ môn khi duyệt — khác với
# trang_thai lưu trong ket_qua_kiem_tra_trung_lap (HOAN_TAT/LOI); đây là kết
# quả đã được diễn giải lại cho màn hình (Không trùng / N đề tài tương tự /
# Chưa kiểm tra).


class TitleCheckSummary(BaseModel):
    trang_thai: str  # "KHONG_TRUNG" | "CO_TUONG_TU" | "CHUA_KIEM_TRA"
    so_tuong_tu: int = 0


class PendingTopicItem(BaseModel):
    """UC1.3/MH-07: một dòng trong bảng 'Đề tài chờ duyệt'."""

    id: int
    ten_de_tai: str
    linh_vuc: str | None = None
    dot_do_an: CohortRef
    loai_nguoi_de_xuat: str
    nguoi_de_xuat: PersonRef
    sinh_vien: PersonRef | None = None
    giang_vien: PersonRef | None = None
    ngay_de_xuat: datetime | None = None
    kiem_tra_ten: TitleCheckSummary

    @field_serializer("ngay_de_xuat")
    def _serialize_utc(self, value: datetime | None) -> str | None:
        # ngay_de_xuat = thoi_diem của kết quả kiểm tra tên đã lưu (UTC naive
        # trong DB) — gắn lại tzinfo=UTC trước khi xuất ISO-8601.
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class ApproveRequest(NFCModel):
    """UC1.3: giang_vien_id bắt buộc khi đề tài đã có SV (đăng ký hoặc tự đề
    xuất); bỏ trống khi đề tài do GV đề xuất và chưa có SV (UC1.3 E1: không
    bao giờ tự động gán GVHD)."""

    giang_vien_id: int | None = None


class RejectRequest(NFCModel):
    """UC1.3/A1: lý do từ chối bắt buộc (không được để trống sau khi strip)."""

    ly_do: str = Field(min_length=1, max_length=2000)
