from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import VaiTro
from app.schemas.assignments import (
    AssignmentFilter,
    AssignmentImport,
    AssignmentPage,
    AssignmentResult,
    AssignmentUpdate,
    MyAdvisorOut,
    MyStudentsOut,
)
from app.services import assignments as assignments_service

# UC0.8: gán/import phân công chỉ Bộ môn; GV xem lớp của mình; SV xem GVHD của
# mình — mỗi route khai báo require_role riêng (route-coverage test).
router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.get("", response_model=AssignmentPage)
def list_assignments(
    dot_do_an_id: int = Query(),
    q: str | None = Query(default=None),
    giang_vien_id: int | None = Query(default=None),
    loc: AssignmentFilter = Query(default="tat_ca"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> AssignmentPage:
    return assignments_service.list_for_cohort(
        db, dot_do_an_id, q, giang_vien_id, loc, page, page_size
    )


@router.put("", response_model=AssignmentResult)
def update_assignments(
    payload: AssignmentUpdate,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> AssignmentResult:
    return assignments_service.update(db, payload.dot_do_an_id, payload.items)


@router.post("/import", response_model=AssignmentResult)
def import_assignments(
    payload: AssignmentImport,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> AssignmentResult:
    return assignments_service.import_csv(db, payload.dot_do_an_id, payload.noi_dung)


@router.get("/my-students", response_model=list[MyStudentsOut])
def my_students(
    dot_do_an_id: int | None = Query(default=None),
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> list[MyStudentsOut]:
    return assignments_service.my_students(db, user, dot_do_an_id)


@router.get("/my-advisor", response_model=list[MyAdvisorOut])
def my_advisor(
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN)),
    db: Session = Depends(get_db),
) -> list[MyAdvisorOut]:
    return assignments_service.my_advisors(db, user)
