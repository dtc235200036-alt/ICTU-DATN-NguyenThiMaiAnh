from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.progress import (
    MilestoneIn,
    MilestoneOut,
    MilestoneUpdate,
    MyProgressOut,
    ProgressDashboardOut,
    ReviewIn,
    StudentProgressItem,
    TopicProgressOut,
)
from app.services import documents
from app.services import progress as progress_service

# UC3/PROG-01..03: mốc tiến độ, báo cáo theo mốc, nhận xét GVHD, tiến độ toàn
# khoa — mọi route khai báo require_role riêng (route-coverage test).
router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/milestones", response_model=list[MilestoneOut])
def list_milestones(
    dot_do_an_id: int | None = Query(default=None),
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> list[MilestoneOut]:
    return progress_service.list_milestones(db, dot_do_an_id)


@router.post("/milestones", response_model=MilestoneOut, status_code=201)
def create_milestone(
    payload: MilestoneIn,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> MilestoneOut:
    return progress_service.create_milestone(db, payload)


@router.put("/milestones/{moc_id}", response_model=MilestoneOut)
def update_milestone(
    moc_id: int,
    payload: MilestoneUpdate,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> MilestoneOut:
    return progress_service.update_milestone(db, moc_id, payload)


@router.delete("/milestones/{moc_id}", status_code=204)
def delete_milestone(
    moc_id: int,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> Response:
    progress_service.delete_milestone(db, moc_id)
    return Response(status_code=204)


@router.get("/me", response_model=MyProgressOut)
def my_progress(
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN)),
    db: Session = Depends(get_db),
) -> MyProgressOut:
    return progress_service.my_progress(db, user)


@router.post("/reports/{moc_id}", response_model=MyProgressOut)
def submit_report(
    moc_id: int,
    noi_dung: str = Form(...),
    file: UploadFile | None = File(None),
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN)),
    db: Session = Depends(get_db),
) -> MyProgressOut:
    """UC3.2: tệp đính kèm tùy chọn — một phần `file` rỗng (không tên) được
    coi như không đính kèm; có tệp thì kiểm tra y hệt đề cương (D-01)."""
    vf = None
    if file is not None and file.filename:
        vf = documents.read_and_validate(file)
    return progress_service.submit_report(db, user, moc_id, noi_dung, vf)


@router.get("/students", response_model=list[StudentProgressItem])
def list_students(
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> list[StudentProgressItem]:
    return progress_service.list_students(db, user)


@router.get("/topics/{de_tai_id}", response_model=TopicProgressOut)
def topic_progress(
    de_tai_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> TopicProgressOut:
    return progress_service.topic_progress(db, user, de_tai_id)


@router.post("/reports/{bao_cao_id}/review", response_model=TopicProgressOut)
def review_report(
    bao_cao_id: int,
    payload: ReviewIn,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicProgressOut:
    return progress_service.review_report(db, user, bao_cao_id, payload)


@router.get("/dashboard", response_model=ProgressDashboardOut)
def dashboard(
    dot_do_an_id: int | None = Query(default=None),
    chi_tre_moc: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
    loc_de_cuong: Literal["DA_NOP", "CHO_DUYET", "CHUA_NOP"] | None = Query(default=None),
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> ProgressDashboardOut:
    return progress_service.dashboard(
        db, dot_do_an_id, chi_tre_moc, page, page_size, q, loc_de_cuong
    )
