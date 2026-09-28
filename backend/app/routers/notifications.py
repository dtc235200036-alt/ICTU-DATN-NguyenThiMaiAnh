from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE
from app.schemas.notifications import NotificationPage, UnreadCountOut
from app.services import notifications as notifications_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationPage)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> NotificationPage:
    return notifications_service.list_for_user(db, user, page, page_size)


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> UnreadCountOut:
    return notifications_service.unread_count(db, user)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> Response:
    notifications_service.mark_all_read(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{thong_bao_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    thong_bao_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> Response:
    notifications_service.mark_read(db, user, thong_bao_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
