from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.documents import CheckDetail, CheckSummary
from app.services import document_check, documents

router = APIRouter(prefix="/api/documents", tags=["documents"])

_NO_CHECK_DETAIL = "Chưa có kết quả kiểm tra"
_FILE_MISSING_DETAIL = "Không tìm thấy file"

_MEDIA_TYPES = {
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "PDF": "application/pdf",
}


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


@router.get("/{tai_lieu_do_an_id}/download")
def download_document(
    tai_lieu_do_an_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> FileResponse:
    """D-02/§3.3.3: đường dẫn duy nhất tới bytes tệp — Starlette tự mã hóa
    filename tiếng Việt đúng chuẩn (RFC 5987), không tự dựng header thủ công."""
    doc = documents.get_viewable_or_error(db, user, tai_lieu_do_an_id)
    path = documents.storage_path(doc.ten_luu_tru)
    if not path.exists():
        raise HTTPException(status_code=404, detail=_FILE_MISSING_DETAIL)
    return FileResponse(
        path,
        filename=doc.ten_goc,
        media_type=_MEDIA_TYPES.get(doc.dinh_dang, "application/octet-stream"),
    )


@router.post("/{tai_lieu_do_an_id}/recheck", response_model=CheckSummary, status_code=202)
def recheck_document(
    tai_lieu_do_an_id: int,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN, VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> CheckSummary:
    """UC0.7/trang-thai-kiem-tra-trung-lap.puml: chỉ kiểm tra lại được khi
    đang LOI (conditional UPDATE trong document_check.request_recheck).
    get_viewable_or_error đã tự giới hạn GV chỉ là GVHD của đề tài (T-03-06)."""
    doc = documents.get_viewable_or_error(db, user, tai_lieu_do_an_id)
    ket_qua = document_check.get_check_for_doc(db, doc)
    if ket_qua is None:
        raise HTTPException(status_code=404, detail=_NO_CHECK_DETAIL)
    document_check.request_recheck(db, ket_qua)
    background_tasks.add_task(document_check.run, ket_qua.id)
    return document_check.summary(ket_qua)
