from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import VaiTro
from app.schemas.common import Page
from app.schemas.topic_approval import PendingTopicItem, RejectRequest
from app.schemas.topics import TopicOut
from app.services import topic_approval as topic_approval_service

# UC1.3/T-02-34 (0015): toàn bộ router chỉ GV được gọi, và service chỉ cho GVHD
# của chính đề tài đó (403 với GV khác) — SV/Bộ môn luôn nhận 403.
router = APIRouter(
    prefix="/api/topic-approvals",
    tags=["topic-approvals"],
    dependencies=[Depends(require_role(VaiTro.GIANG_VIEN))],
)


@router.get("", response_model=Page[PendingTopicItem])
def list_pending(
    dot_do_an_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> Page[PendingTopicItem]:
    return topic_approval_service.list_pending(db, user, dot_do_an_id, page, page_size)


@router.post("/{topic_id}/approve", response_model=TopicOut)
def approve_topic(
    topic_id: int,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topic_approval_service.approve(db, user, topic_id)


@router.post("/{topic_id}/reject", response_model=TopicOut)
def reject_topic(
    topic_id: int,
    payload: RejectRequest,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topic_approval_service.reject(db, user, topic_id, payload.ly_do)
