from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import NFCModel
from app.schemas.documents import DocumentOut
from app.schemas.topics import PersonRef

_OPTIONAL_TEXT_FIELDS = ("ma_so_sinh_vien", "ho_ten_sinh_vien", "tu_khoa")


class ArchiveIn(NFCModel):
    """UC5.3: thêm/sửa một bản ghi kho (Bộ môn). Chuỗi đã NFC + strip bởi
    NFCModel; chuỗi rỗng ở trường tùy chọn được coi là không nhập (None)."""

    khoa: str = Field(min_length=1, max_length=20)
    ten_de_tai: str = Field(min_length=1, max_length=255)
    ma_so_sinh_vien: str | None = Field(default=None, max_length=20)
    ho_ten_sinh_vien: str | None = Field(default=None, max_length=150)
    giang_vien_id: int | None = None
    tu_khoa: str | None = Field(default=None, max_length=255)
    diem: Decimal | None = Field(default=None, ge=0, le=10, max_digits=4, decimal_places=2)

    @model_validator(mode="after")
    def _blank_to_none(self) -> "ArchiveIn":
        for name in _OPTIONAL_TEXT_FIELDS:
            if getattr(self, name) == "":
                setattr(self, name, None)
        return self


class ArchiveStudent(BaseModel):
    """Ảnh chụp danh tính SV lưu trong bản ghi kho (bản ghi import có thể
    không có tài khoản SV)."""

    ma: str | None = None
    ho_ten: str | None = None


class ArchiveListItem(BaseModel):
    """MH-13: một dòng của bảng kho đồ án."""

    id: int
    ten_de_tai: str
    khoa: str | None = None
    sinh_vien: ArchiveStudent | None = None
    giang_vien: PersonRef | None = None
    diem: float | None = None
    tu_khoa: str | None = None
    nguon: str
    trang_thai_index: str
    co_file: bool


class ArchiveDetail(ArchiveListItem):
    """MH-13 Drawer "Chi tiết bản ghi kho" — file = phiên bản BAO_CAO_CUOI mới
    nhất của đề tài (chỉ bản ghi lưu kho khi chốt bảo vệ mới có)."""

    de_tai_id: int | None = None
    sinh_vien_id: int | None = None
    file: DocumentOut | None = None


class ImportRowError(BaseModel):
    """UC5.4 E1: một dòng CSV bị bỏ qua — dong là số dòng vật lý (tiêu đề = 1)."""

    dong: int
    ly_do: str


class ImportResult(BaseModel):
    tong_dong: int
    thanh_cong: int
    loi: list[ImportRowError]
