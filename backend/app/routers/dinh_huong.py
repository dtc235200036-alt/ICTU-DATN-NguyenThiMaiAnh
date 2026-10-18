from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.models.de_tai import DeTai
from app.models.dinh_huong import DinhHuong
from app.schemas.dinh_huong import DinhHuongIn, DinhHuongOut

# Danh mục định hướng đề tài: mọi vai trò đọc (form giao đề tài, bộ lọc, kiểm
# tra tên file đề cương); chỉ Bộ môn thêm/sửa.
router = APIRouter(prefix="/api/dinh-huong", tags=["dinh-huong"])

_NOT_FOUND_DETAIL = "Không tìm thấy định hướng"
_DUPLICATE_DETAIL = "Mã định hướng đã tồn tại"


def _to_out(item: DinhHuong, so_de_tai: int = 0) -> DinhHuongOut:
    return DinhHuongOut(
        id=item.id,
        ma=item.ma,
        ten=item.ten,
        mo_ta=item.mo_ta,
        hoat_dong=item.hoat_dong,
        so_de_tai=so_de_tai,
    )


@router.get("", response_model=list[DinhHuongOut])
def list_dinh_huong(
    chi_hoat_dong: bool = Query(default=False),
    _user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> list[DinhHuongOut]:
    so_de_tai = (
        select(DeTai.dinh_huong_id, func.count().label("n"))
        .where(DeTai.dinh_huong_id.is_not(None))
        .group_by(DeTai.dinh_huong_id)
        .subquery()
    )
    stmt = (
        select(DinhHuong, func.coalesce(so_de_tai.c.n, 0))
        .outerjoin(so_de_tai, so_de_tai.c.dinh_huong_id == DinhHuong.id)
        .order_by(DinhHuong.ma)
    )
    if chi_hoat_dong:
        stmt = stmt.where(DinhHuong.hoat_dong.is_(True))
    return [_to_out(item, int(n)) for item, n in db.execute(stmt).all()]


@router.post("", response_model=DinhHuongOut, status_code=201)
def create_dinh_huong(
    payload: DinhHuongIn,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> DinhHuongOut:
    item = DinhHuong(
        ma=payload.ma.upper(), ten=payload.ten, mo_ta=payload.mo_ta, hoat_dong=payload.hoat_dong
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_DUPLICATE_DETAIL) from None
    db.refresh(item)
    return _to_out(item)


@router.put("/{dinh_huong_id}", response_model=DinhHuongOut)
def update_dinh_huong(
    dinh_huong_id: int,
    payload: DinhHuongIn,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> DinhHuongOut:
    item = db.get(DinhHuong, dinh_huong_id)
    if item is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    item.ma = payload.ma.upper()
    item.ten = payload.ten
    item.mo_ta = payload.mo_ta
    item.hoat_dong = payload.hoat_dong
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=_DUPLICATE_DETAIL) from None
    db.refresh(item)
    return _to_out(item)
