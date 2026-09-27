from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.models.dot_do_an import DA_DONG, DANG_MO, DotDoAn
from app.schemas.cohorts import CohortCreate, CohortOut, CohortUpdate

# UC0.3/AUTH-04: GET mở cho mọi vai trò (bộ lọc/form đề tài dùng danh sách này);
# create/update/open/close chỉ Bộ môn — mỗi route khai báo require_role riêng vì
# router không thể dùng một dependency chung cho cả hai nhóm quyền (D-08).
router = APIRouter(prefix="/api/cohorts", tags=["cohorts"])

_NOT_FOUND_DETAIL = "Không tìm thấy đợt đồ án"


def _to_out(cohort: DotDoAn) -> CohortOut:
    return CohortOut(
        id=cohort.id,
        ten_dot=cohort.ten_dot,
        khoa=cohort.khoa,
        nam_hoc=cohort.nam_hoc,
        ngay_bat_dau=cohort.ngay_bat_dau,
        ngay_ket_thuc=cohort.ngay_ket_thuc,
        trang_thai=cohort.trang_thai,
    )


def _get_or_404(db: Session, cohort_id: int) -> DotDoAn:
    cohort = db.get(DotDoAn, cohort_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    return cohort


@router.get("", response_model=list[CohortOut])
def list_cohorts(
    trang_thai: str | None = Query(default=None),
    khoa: str | None = Query(default=None),
    _user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> list[CohortOut]:
    stmt = select(DotDoAn)
    if trang_thai is not None:
        stmt = stmt.where(DotDoAn.trang_thai == trang_thai)
    if khoa is not None:
        stmt = stmt.where(DotDoAn.khoa == khoa)
    stmt = stmt.order_by(DotDoAn.ngay_bat_dau.desc(), DotDoAn.id.desc())
    rows = db.execute(stmt).scalars().all()
    return [_to_out(row) for row in rows]


@router.post("", response_model=CohortOut, status_code=201)
def create_cohort(
    payload: CohortCreate,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CohortOut:
    cohort = DotDoAn(
        ten_dot=payload.ten_dot,
        khoa=payload.khoa,
        nam_hoc=payload.nam_hoc,
        ngay_bat_dau=payload.ngay_bat_dau,
        ngay_ket_thuc=payload.ngay_ket_thuc,
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return _to_out(cohort)


@router.put("/{cohort_id}", response_model=CohortOut)
def update_cohort(
    cohort_id: int,
    payload: CohortUpdate,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CohortOut:
    cohort = _get_or_404(db, cohort_id)
    cohort.ten_dot = payload.ten_dot
    cohort.khoa = payload.khoa
    cohort.nam_hoc = payload.nam_hoc
    cohort.ngay_bat_dau = payload.ngay_bat_dau
    cohort.ngay_ket_thuc = payload.ngay_ket_thuc
    db.commit()
    db.refresh(cohort)
    return _to_out(cohort)


@router.post("/{cohort_id}/open", response_model=CohortOut)
def open_cohort(
    cohort_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CohortOut:
    cohort = _get_or_404(db, cohort_id)
    cohort.trang_thai = DANG_MO
    db.commit()
    db.refresh(cohort)
    return _to_out(cohort)


@router.post("/{cohort_id}/close", response_model=CohortOut)
def close_cohort(
    cohort_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CohortOut:
    cohort = _get_or_404(db, cohort_id)
    cohort.trang_thai = DA_DONG
    db.commit()
    db.refresh(cohort)
    return _to_out(cohort)
