from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.topics import TopicCreate, TopicOut, TopicUpdate
from app.services import topics as topics_service

# UC1.1/AUTH-03: đề xuất/sửa/gửi chỉ GV và SV (Bộ môn không đề xuất đề tài);
# xem chi tiết mở cho mọi vai trò đã xác thực, quyền xem thực sự do can_view
# (T-02-23) quyết định ở tầng service, không phải ở require_role.
router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(
    payload: TopicCreate,
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topics_service.create_topic(db, user, payload)


@router.put("/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topics_service.update_topic(db, user, topic_id, payload)


@router.post("/{topic_id}/submit", response_model=TopicOut)
def submit_topic(
    topic_id: int,
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topics_service.submit_topic(db, user, topic_id)


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(
    topic_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topics_service.get_topic(db, user, topic_id)
