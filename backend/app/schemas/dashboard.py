from pydantic import BaseModel

from app.schemas.topics import CohortRef

# D-09/TOPC-04: mỗi vai trò một hình dạng riêng — chỉ các widget có dữ liệu
# thật ở Phase 2 (MH-02/03/04 subset); widget đề cương/tiến độ/hội đồng/thông
# báo thuộc Phase 3, không có trường rỗng giả ở đây.


class SvTopicOut(BaseModel):
    """MH-02: đề tài hiện tại (đang hoạt động) hoặc gần nhất của SV."""

    id: int
    ten_de_tai: str
    trang_thai: str
    giang_vien_huong_dan: str | None = None
    ly_do_tu_choi: str | None = None


class SvDashboardOut(BaseModel):
    de_tai: SvTopicOut | None = None
    co_dot_dang_mo: bool


class GvTopicItem(BaseModel):
    id: int
    ten_de_tai: str
    trang_thai: str
    sinh_vien: str | None = None


class GvDashboardOut(BaseModel):
    """MH-03: chỉ số + danh sách đề tài của chính GV gọi (own giang_vien_id)."""

    so_sinh_vien_huong_dan: int
    so_de_tai: int
    so_de_tai_cho_duyet: int
    de_tai: list[GvTopicItem]


class BmPendingTopicRef(BaseModel):
    id: int
    ten_de_tai: str
    nguoi_de_xuat: str


class BmDashboardOut(BaseModel):
    """MH-04: tổng quan toàn khoa theo đợt (mặc định đợt đang mở mới nhất)."""

    dot_do_an: CohortRef | None = None
    de_tai_cho_duyet: int
    de_tai_da_phan_cong: int
    sv_chua_co_de_tai: int
    tong_sinh_vien: int
    cho_duyet_moi_nhat: list[BmPendingTopicRef]
