from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import VaiTro
from app.schemas.documents import UploadCheckDetail, UploadCheckSummary
from app.services import document_check, documents

# 0020: GV/Bộ môn tải một tệp PDF/DOCX bất kỳ lên để kiểm tra trùng lặp với kho.
# Tệp chỉ nằm trong bộ nhớ: không lưu đĩa, không vào chỉ mục AI.
router = APIRouter(prefix="/api/upload-checks", tags=["upload-checks"])

_ROLES = (VaiTro.GIANG_VIEN, VaiTro.BO_MON)
_NO_TEXT_DETAIL = (
    "Không trích xuất được nội dung file (có thể là PDF dạng ảnh quét) — hãy chọn file khác"
)


@router.post("", response_model=UploadCheckSummary, status_code=202)
def create_upload_check(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role(*_ROLES)),
    db: Session = Depends(get_db),
) -> UploadCheckSummary:
    document_check.ensure_upload_quota(db, user.tai_khoan_id)
    vf = documents.read_and_validate(file)
    if not vf.text:
        raise HTTPException(status_code=422, detail=_NO_TEXT_DETAIL)
    if documents.too_long_for_check(vf.text):
        raise HTTPException(status_code=422, detail=documents.too_long_detail(vf.text))
    ket_qua = document_check.create_upload_pending(db, user.tai_khoan_id, vf.ten_goc)
    db.commit()
    db.refresh(ket_qua)
    background_tasks.add_task(document_check.run, ket_qua.id, vf.text)
    return document_check.upload_summary(ket_qua)


@router.get("", response_model=list[UploadCheckSummary])
def list_upload_checks(
    user: CurrentUser = Depends(require_role(*_ROLES)),
    db: Session = Depends(get_db),
) -> list[UploadCheckSummary]:
    return [
        document_check.upload_summary(k)
        for k in document_check.list_uploads(db, user.tai_khoan_id)
    ]


@router.get("/{ket_qua_id}", response_model=UploadCheckDetail)
def get_upload_check(
    ket_qua_id: int,
    user: CurrentUser = Depends(require_role(*_ROLES)),
    db: Session = Depends(get_db),
) -> UploadCheckDetail:
    return document_check.upload_detail(document_check.get_upload_or_404(db, user, ket_qua_id))
