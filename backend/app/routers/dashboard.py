from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import VaiTro
from app.schemas.dashboard import BmDashboardOut, GvDashboardOut, SvDashboardOut
from app.services import dashboard as dashboard_service

# D-09/T-02-38: mỗi vai trò một route riêng, mỗi route chỉ vai trò đó gọi
# được — không có route dùng chung nhiều vai trò cho dashboard.
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/sinh-vien", response_model=SvDashboardOut)
def sv_dashboard(
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN)),
    db: Session = Depends(get_db),
) -> SvDashboardOut:
    return dashboard_service.get_sv_dashboard(db, user)


@router.get("/giang-vien", response_model=GvDashboardOut)
def gv_dashboard(
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> GvDashboardOut:
    return dashboard_service.get_gv_dashboard(db, user)


@router.get("/bo-mon", response_model=BmDashboardOut)
def bo_mon_dashboard(
    dot_do_an_id: int | None = Query(default=None),
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> BmDashboardOut:
    return dashboard_service.get_bo_mon_dashboard(db, dot_do_an_id)
