from pydantic import BaseModel

from app.schemas.common import UtcDateTime
from app.schemas.topics import PersonRef


class DocumentOut(BaseModel):
    """UC2/UC3/UC4/UC5: một phiên bản tài liệu đã nộp."""

    id: int
    loai: str
    so_phien_ban: int
    ten_goc: str
    kich_thuoc: int
    dinh_dang: str
    thoi_diem_nop: UtcDateTime
    trich_xuat_loi: bool
    tom_tat: str | None = None
    # WR-05: văn bản trích xuất vượt AI_DOCUMENT_MAX_CHARS — không kiểm tra
    # trùng lặp tự động được, "Kiểm tra lại" không có tác dụng.
    qua_dai_kiem_tra: bool = False
    # 0016: ghi chú người nộp kèm phiên bản.
    ghi_chu: str | None = None


class CheckSummary(BaseModel):
    """UC0.7: trạng thái tóm tắt của một kết quả kiểm tra trùng lặp tài liệu.

    CR-01 (04-REVIEW): `vuot_nguong` do Web API tính MỘT lần theo đúng quy tắc
    đã hiệu chỉnh — tỷ lệ trùng với một đồ án nguồn cao nhất
    (`ty_le_nguon_cao_nhat`) >= `nguong_ap_dung`; `ty_le_tong` chỉ để hiển thị.
    None khi chưa HOAN_TAT."""

    id: int
    trang_thai: str
    ty_le_tong: float | None = None
    ty_le_nguon_cao_nhat: float | None = None
    vuot_nguong: bool | None = None
    nguong_ap_dung: float
    thoi_diem: UtcDateTime
    # CR-04: phạm vi được kiểm tra; loai_tru_nhieu = hơn một nửa ký tự bị loại
    # như phần mẫu chung (GVHD nên xem trực tiếp tài liệu).
    so_doan: int | None = None
    so_doan_loai_tru: int | None = None
    ty_le_loai_tru: float | None = None
    loai_tru_nhieu: bool = False


class CheckMatch(BaseModel):
    doi_tuong_trung: str
    ty_le: float


class CheckSegment(BaseModel):
    doi_tuong_trung: str
    doan_nguon: str | None = None
    doan_trung: str | None = None
    vi_tri: str | None = None
    ty_le: float
    # WR-07: True khi doan_trung bị ẩn với người xem (SV) vì nguồn là tài liệu
    # chưa công bố của sinh viên khác (không phải đồ án đã vào kho).
    doan_trung_an: bool = False


class CheckDetail(BaseModel):
    """UC0.7/MH-09/MH-14: chi tiết đầy đủ một kết quả kiểm tra tài liệu."""

    id: int
    trang_thai: str
    ty_le_tong: float | None = None
    ty_le_nguon_cao_nhat: float | None = None
    vuot_nguong: bool | None = None
    nguong_ap_dung: float
    thoi_diem: UtcDateTime
    so_doan: int | None = None
    so_doan_loai_tru: int | None = None
    ty_le_loai_tru: float | None = None
    loai_tru_nhieu: bool = False
    tai_lieu: DocumentOut
    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef | None = None
    do_an_trung: list[CheckMatch]
    chi_tiet: list[CheckSegment]
