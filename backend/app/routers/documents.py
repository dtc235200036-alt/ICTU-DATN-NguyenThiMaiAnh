from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE
from app.schemas.documents import CheckDetail
from app.services import document_check, documents

router = APIRouter(prefix="/api/documents", tags=["documents"])

_NO_CHECK_DETAIL = "Chưa có kết quả kiểm tra"


@router.get("/{tai_lieu_do_an_id}/check", response_model=CheckDetail)
def get_check(
    tai_lieu_do_an_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> CheckDetail:
    doc = documents.get_viewable_or_error(db, user, tai_lieu_do_an_id)
    ket_qua = document_check.get_check_for_doc(db, doc)
    if ket_qua is None:
        raise HTTPException(status_code=404, detail=_NO_CHECK_DETAIL)
    document_check.expire_if_stale(db, ket_qua)
    return document_check.detail(db, doc)
