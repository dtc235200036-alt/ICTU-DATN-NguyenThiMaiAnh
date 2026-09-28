"""Hợp đồng HTTP §3.3.5 (+ các trường bổ sung ghi trong README)."""
from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import get_settings

_MAX_TEXT = get_settings().MAX_TEXT_CHARS


class IngestRequest(BaseModel):
    id: int = Field(ge=1)
    type: Literal["TOPIC", "ARCHIVE"]
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


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    index_size: int
    index_size_tieu_de: int
    index_size_tai_lieu: int
    ten_model: str
    encode_calls: int
    thieu_embedding: int
