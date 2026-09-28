"""Hợp đồng HTTP §3.3.5 (+ các trường bổ sung ghi trong README)."""
from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import get_settings

_SETTINGS = get_settings()
_MAX_TEXT = _SETTINGS.MAX_TEXT_CHARS


class IngestRequest(BaseModel):
    """TOPIC = de_tai.id, ARCHIVE = do_an_kho.id (chỉ tiêu đề),
    DOCUMENT = tai_lieu_do_an.id (văn bản đã trích xuất)."""

    id: int = Field(ge=1)
    type: Literal["TOPIC", "ARCHIVE", "DOCUMENT"]
    # Rỗng hợp lệ: ngữ nghĩa REPLACE — nguồn còn lại không chunk nào.
    text: str = Field(max_length=_MAX_TEXT)


class IngestResponse(BaseModel):
    chunk_count: int
    indexed: bool = True


class CheckTitleRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    nguong: float | None = Field(default=None, ge=0, le=100)


class TitleMatch(BaseModel):
    ref_id: int
    loai: Literal["TOPIC", "ARCHIVE"]
    ty_le: float


class CheckTitleResponse(BaseModel):
    matches: list[TitleMatch]


class CheckDocumentRequest(BaseModel):
    # 0 = tài liệu chưa nằm trong kho; tập loại trừ = {ref_id} ∪ loai_tru.
    ref_id: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=_MAX_TEXT)
    top_k: int = Field(default=_SETTINGS.TOP_K_MAC_DINH, ge=1, le=20)
    # None → giá trị mặc định của dịch vụ; Web API thường gửi ngưỡng riêng (D-04).
    nguong_doan: float | None = Field(default=None, ge=0, le=100)
    nguong_nguyen_van: float | None = Field(default=None, ge=0, le=100)
    loai_tru: list[int] = Field(default_factory=list, max_length=2000)


class DocumentMatch(BaseModel):
    ref_id: int
    ty_le: float


class PassageDetail(BaseModel):
    ref_id: int
    doan_nguon: str
    doan_trung: str
    vi_tri: str
    ty_le: float
    tin_hieu: Literal["NGUYEN_VAN", "NGU_NGHIA"]
    diem_ngu_nghia: float
    diem_nguyen_van: float


class CheckDocumentResponse(BaseModel):
    ty_le_tong: float
    do_an_trung: list[DocumentMatch]
    chi_tiet: list[PassageDetail]
    so_doan: int
    so_doan_loai_tru: int
    # CR-04: % ký tự của văn bản bị loại như phần mẫu chung (không kiểm tra).
    ty_le_loai_tru: float = 0.0


class ReindexRequest(BaseModel):
    items: list[IngestRequest] | None = Field(default=None, max_length=500)


class ReindexResponse(BaseModel):
    indexed_count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    index_size: int
    index_size_tieu_de: int
    index_size_tai_lieu: int
    ten_model: str
    encode_calls: int
    thieu_embedding: int
