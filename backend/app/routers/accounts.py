from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.core.roles import VaiTro
from app.schemas.accounts import AccountCreate, AccountOut, AccountUpdate
from app.schemas.common import Page
from app.services import accounts as accounts_service

# D-08/UC0.2: toàn bộ router chỉ Bộ môn được gọi — mọi route thừa hưởng
# require_role(BO_MON) từ đây, không cần khai báo lại từng route.
router = APIRouter(
    prefix="/api/accounts",
    tags=["accounts"],
    dependencies=[Depends(require_role(VaiTro.BO_MON))],
)


@router.get("", response_model=Page[AccountOut])
def list_accounts(
    vai_tro: VaiTro = Query(...),
    q: str | None = Query(default=None),
    bi_khoa: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[AccountOut]:
    return accounts_service.list_accounts(db, vai_tro, q, bi_khoa, page, page_size)


@router.post("", response_model=AccountOut, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountOut:
    return accounts_service.create_account(db, payload)


@router.put("/{tai_khoan_id}", response_model=AccountOut)
def update_account(
    tai_khoan_id: int, payload: AccountUpdate, db: Session = Depends(get_db)
) -> AccountOut:
    return accounts_service.update_account(db, tai_khoan_id, payload)


@router.post("/{tai_khoan_id}/lock", response_model=AccountOut)
def lock_account(tai_khoan_id: int, db: Session = Depends(get_db)) -> AccountOut:
    return accounts_service.set_locked(db, tai_khoan_id, True)


@router.post("/{tai_khoan_id}/unlock", response_model=AccountOut)
def unlock_account(tai_khoan_id: int, db: Session = Depends(get_db)) -> AccountOut:
    return accounts_service.set_locked(db, tai_khoan_id, False)
