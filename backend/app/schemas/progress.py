from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NFCModel, UtcDateTime
from app.schemas.documents import DocumentOut
from app.schemas.topics import CohortRef, PersonRef


class MilestoneIn(NFCModel):
    dot_do_an_id: int
    ten_moc: str = Field(min_length=1, max_length=100)
    han_nop: date


class MilestoneUpdate(NFCModel):
    ten_moc: str = Field(min_length=1, max_length=100)
    han_nop: date


class MilestoneOut(BaseModel):
    id: int
    dot_do_an_id: int
    ten_moc: str
    thu_tu: int
    han_nop: date | None
    so_bao_cao: int = 0


class ReportOut(BaseModel):
    id: int
    noi_dung: str | None
    thoi_diem_nop: UtcDateTime
    nhan_xet: str | None
    danh_gia: str | None
    tep: DocumentOut | None = None


class MilestoneStatus(BaseModel):
    """Một mốc nhìn từ một đề tài — trang_thai tính theo D-05, không lưu DB."""

    id: int
    ten_moc: str
    thu_tu: int
    han_nop: date | None
    trang_thai: str
    # Số ngày trễ so với hạn (NOP_TRE: ngày nộp - hạn; TRE_MOC: hôm nay - hạn).
    so_ngay_tre: int | None = None
    bao_cao: ReportOut | None = None


class TopicProgressOut(BaseModel):
    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef | None
    giang_vien: PersonRef | None
    dot_do_an: CohortRef | None
    trang_thai_de_cuong: str
    moc: list[MilestoneStatus]
    tre_moc: bool
    co_the_nop: bool
    ly_do: str | None = None
    co_the_nhan_xet: bool


class MyProgressOut(BaseModel):
    de_tai: TopicProgressOut | None


class StudentProgressItem(BaseModel):
    de_tai_id: int
    ten_de_tai: str
    sinh_vien: PersonRef | None
    so_cho_nhan_xet: int
    tre_moc: bool


class ReviewIn(NFCModel):
    nhan_xet: str = Field(min_length=1, max_length=5000)
    danh_gia: Literal["DAT", "CAN_CAI_THIEN", "CHUA_DAT"]


class ProgressCellOut(BaseModel):
    moc_id: int
    trang_thai: str
    bao_cao_id: int | None = None


class TopicRef(BaseModel):
    id: int
    ten_de_tai: str


class ProgressRowOut(BaseModel):
    sinh_vien: PersonRef | None
    giang_vien: PersonRef | None
    de_tai: TopicRef
    o: list[ProgressCellOut]
    tre_moc: bool


class ProgressDashboardOut(BaseModel):
    dot_do_an: CohortRef | None
    moc: list[MilestoneOut]
    items: list[ProgressRowOut]
    total: int
    page: int
    page_size: int
    so_sv_tre_moc: int
