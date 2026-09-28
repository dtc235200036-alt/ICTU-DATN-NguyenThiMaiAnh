from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import VaiTro
from app.schemas.common import Page
from app.schemas.topic_approval import ApproveRequest, PendingTopicItem, RejectRequest
from app.schemas.topics import TopicOut
from app.services import topic_approval as topic_approval_service

# UC1.3/T-02-34: toàn bộ router chỉ Bộ môn được gọi — SV/GV (kể cả GV đề xuất
# chính đề tài đó) luôn nhận 403, trạng thái đề tài không đổi.
router = APIRouter(
    prefix="/api/topic-approvals",
    tags=["topic-approvals"],
    dependencies=[Depends(require_role(VaiTro.BO_MON))],
)


@router.get("", response_model=Page[PendingTopicItem])
def list_pending(
    dot_do_an_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[PendingTopicItem]:
    return topic_approval_service.list_pending(db, dot_do_an_id, page, page_size)


@router.post("/{topic_id}/approve", response_model=TopicOut)
def approve_topic(
    topic_id: int,
    payload: ApproveRequest,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topic_approval_service.approve(db, user, topic_id, payload.giang_vien_id)


@router.post("/{topic_id}/reject", response_model=TopicOut)
def reject_topic(
    topic_id: int,
    payload: RejectRequest,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topic_approval_service.reject(db, user, topic_id, payload.ly_do)
