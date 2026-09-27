from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE
from app.models.tai_khoan import GiangVien, TaiKhoan
from app.schemas.accounts import LecturerOut

# T-02-17: mọi vai trò được gọi (bộ lọc đề tài + gán GVHD ở các plan sau).
router = APIRouter(prefix="/api/lecturers", tags=["lecturers"])


@router.get("", response_model=list[LecturerOut])
def list_lecturers(
    _user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> list[LecturerOut]:
    rows = (
        db.execute(
            select(GiangVien)
            .join(TaiKhoan, TaiKhoan.id == GiangVien.tai_khoan_id)
            .where(TaiKhoan.bi_khoa.is_(False))
            .order_by(GiangVien.ho_ten.asc())
        )
        .scalars()
        .all()
    )
    return [
        LecturerOut(id=gv.id, ma_giang_vien=gv.ma_giang_vien, ho_ten=gv.ho_ten, hoc_vi=gv.hoc_vi)
        for gv in rows
    ]
