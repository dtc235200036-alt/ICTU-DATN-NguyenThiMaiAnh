from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NFCModel, UtcDateTime
from app.schemas.topics import CohortRef, PersonRef

# UC0.8: Bộ môn gán SV -> GVHD theo đợt; GV xem lớp hướng dẫn của mình; SV xem
# GVHD của mình. Mỗi SV có tối đa một GVHD trong một đợt (uk_phan_cong_sv_dot).


class AssignmentRow(BaseModel):
    """MH-15: một dòng bảng phân công — SV, GVHD hiện tại (nếu có) và đề tài
    đang hoạt động của SV trong đợt (để Bộ môn biết dòng nào còn đổi được)."""

    sinh_vien: PersonRef
    lop: str | None = None
    giang_vien: PersonRef | None = None
    de_tai_id: int | None = None
    ten_de_tai: str | None = None
    trang_thai_de_tai: str | None = None
    doi_duoc: bool = True


class LecturerLoad(BaseModel):
    giang_vien: PersonRef
    hoc_vi: str | None = None
    so_sinh_vien: int


class AssignmentPage(BaseModel):
    items: list[AssignmentRow]
    total: int
    page: int
    page_size: int
    tong_sinh_vien: int
    da_phan_cong: int
    tai_giang_vien: list[LecturerLoad]


class AssignmentItem(NFCModel):
    sinh_vien_id: int
    # null = gỡ phân công (chỉ được khi SV chưa có đề tài Đã phân công).
    giang_vien_id: int | None = None


class AssignmentUpdate(NFCModel):
    dot_do_an_id: int
    items: list[AssignmentItem] = Field(min_length=1, max_length=500)


class AssignmentImport(NFCModel):
    """Nội dung CSV (UTF-8) mỗi dòng `ma_so_sinh_vien,ma_giang_vien`; dòng tiêu
    đề và dòng trống được bỏ qua."""

    dot_do_an_id: int
    noi_dung: str = Field(min_length=1, max_length=200_000)


class AssignmentResult(BaseModel):
    cap_nhat: int
    loi: list[str] = []


class MyStudentItem(BaseModel):
    """MH-16 "Sinh viên của tôi": SV trong lớp hướng dẫn + đề tài hiện tại."""

    sinh_vien: PersonRef
    lop: str | None = None
    email: str | None = None
    de_tai_id: int | None = None
    ten_de_tai: str | None = None
    trang_thai_de_tai: str | None = None


class MyStudentsOut(BaseModel):
    dot_do_an: CohortRef
    items: list[MyStudentItem]


class MyAdvisorOut(BaseModel):
    dot_do_an: CohortRef
    giang_vien: PersonRef
    hoc_vi: str | None = None
    email: str | None = None
    thoi_diem: UtcDateTime


AssignmentFilter = Literal["tat_ca", "da_phan_cong", "chua_phan_cong"]
