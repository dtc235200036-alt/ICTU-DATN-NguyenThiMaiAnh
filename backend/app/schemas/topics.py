from pydantic import BaseModel, Field

from app.schemas.common import NFCModel

# D-06: schema request kế thừa NFCModel (NFC-normalize + strip mọi trường).


class TopicCreate(NFCModel):
    """UC1.1: đề xuất đề tài mới — gui=False lưu nháp, gui=True gửi đề xuất ngay."""

    dot_do_an_id: int
    ten_de_tai: str = Field(min_length=5, max_length=255)
    mo_ta: str | None = Field(default=None, max_length=5000)
    linh_vuc: str | None = Field(default=None, max_length=100)
    gui: bool = False


class TopicUpdate(NFCModel):
    """UC1.1: sửa đề tài đang ở trạng thái Nháp (không đổi trang_thai — dùng /submit)."""

    dot_do_an_id: int
    ten_de_tai: str = Field(min_length=5, max_length=255)
    mo_ta: str | None = Field(default=None, max_length=5000)
    linh_vuc: str | None = Field(default=None, max_length=100)


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
