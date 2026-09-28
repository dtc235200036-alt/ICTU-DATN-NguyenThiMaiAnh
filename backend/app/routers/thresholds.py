from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import VaiTro
from app.schemas.thresholds import ThresholdOut, ThresholdUpdate
from app.services import thresholds as thresholds_service

# UC0.4/AISV-07 (T-04-29): chỉ Bộ môn đọc và sửa ngưỡng cảnh báo trùng lặp.
router = APIRouter(prefix="/api/thresholds", tags=["thresholds"])


@router.get("", response_model=list[ThresholdOut])
def get_thresholds(
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> list[ThresholdOut]:
    return thresholds_service.list_thresholds(db)


@router.put("", response_model=list[ThresholdOut])
def put_thresholds(
    payload: ThresholdUpdate,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> list[ThresholdOut]:
    return thresholds_service.update_thresholds(db, user, payload)
