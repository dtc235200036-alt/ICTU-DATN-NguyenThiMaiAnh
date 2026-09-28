from pydantic import BaseModel

from app.schemas.common import UtcDateTime


class NotificationOut(BaseModel):
    id: int
    loai: str
    noi_dung: str
    lien_ket: str | None = None
    da_doc: bool
    thoi_diem: UtcDateTime


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int
    chua_doc: int


class UnreadCountOut(BaseModel):
    chua_doc: int
