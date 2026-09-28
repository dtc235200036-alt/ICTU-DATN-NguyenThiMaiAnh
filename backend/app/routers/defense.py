from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.defense import (
    CommitteeIn,
    CommitteeListItem,
    CommitteeOut,
    EligibleStudent,
    FinalReportDetail,
    ScheduleIn,
    ScheduleRow,
)
from app.services import defense as defense_service
from app.services import document_check, documents

# UC4/DEFN-01..02: nộp báo cáo cuối (SV) + hội đồng/lịch bảo vệ (Bộ môn) —
# mỗi route khai báo require_role riêng (route-coverage test bao trùm cả
# router này, giống outlines.py/documents.py).
router = APIRouter(prefix="/api/defense", tags=["defense"])


@router.post("/final-reports/{de_tai_id}", response_model=FinalReportDetail, status_code=202)
def submit_final_report(
    de_tai_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN)),
    db: Session = Depends(get_db),
) -> FinalReportDetail:
    vf = documents.read_and_validate(file)
    detail, ket_qua_id = defense_service.submit_final_report(db, user, de_tai_id, vf)
    background_tasks.add_task(document_check.run, ket_qua_id)
    return detail


@router.get("/final-reports/{de_tai_id}", response_model=FinalReportDetail)
def get_final_report(
    de_tai_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> FinalReportDetail:
    return defense_service.get_final_report(db, user, de_tai_id)


@router.get("/committees", response_model=list[CommitteeListItem])
def list_committees(
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> list[CommitteeListItem]:
    return defense_service.list_committees(db)


@router.post("/committees", response_model=CommitteeOut, status_code=201)
def create_committee(
    payload: CommitteeIn,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CommitteeOut:
    return defense_service.create_committee(db, payload)


@router.get("/eligible-students", response_model=list[EligibleStudent])
def eligible_students(
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> list[EligibleStudent]:
    return defense_service.eligible_students(db)


@router.get("/committees/{hoi_dong_id}", response_model=CommitteeOut)
def get_committee(
    hoi_dong_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CommitteeOut:
    return defense_service.get_committee(db, hoi_dong_id)


@router.put("/committees/{hoi_dong_id}", response_model=CommitteeOut)
def update_committee(
    hoi_dong_id: int,
    payload: CommitteeIn,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CommitteeOut:
    return defense_service.update_committee(db, hoi_dong_id, payload)


@router.delete("/committees/{hoi_dong_id}", status_code=204)
def delete_committee(
    hoi_dong_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> None:
    defense_service.delete_committee(db, hoi_dong_id)


@router.post("/committees/{hoi_dong_id}/schedules", response_model=ScheduleRow, status_code=201)
def add_schedule(
    hoi_dong_id: int,
    payload: ScheduleIn,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> ScheduleRow:
    return defense_service.add_schedule(db, hoi_dong_id, payload.de_tai_id)


@router.delete("/schedules/{lich_bao_ve_id}", status_code=204)
def remove_schedule(
    lich_bao_ve_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> None:
    defense_service.remove_schedule(db, lich_bao_ve_id)
