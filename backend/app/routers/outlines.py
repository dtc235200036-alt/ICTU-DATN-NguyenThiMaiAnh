from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.common import Page
from app.schemas.outlines import (
    BoMonReturnRequest,
    OutlineCounts,
    OutlineDetail,
    OutlineListItem,
    ReviewRequest,
)
from app.services import document_check, documents
from app.services import outlines as outlines_service

# UC2/OUTL-01..03: nộp/duyệt/xem đề cương — mọi route khai báo require_role
# riêng (T-02-style route-coverage test bao trùm cả router này).
router = APIRouter(prefix="/api/outlines", tags=["outlines"])


@router.get("", response_model=Page[OutlineListItem])
def list_outlines(
    trang_thai: str | None = Query(default=None),
    dot_do_an_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> Page[OutlineListItem]:
    return outlines_service.list_outlines(
        db, user, trang_thai, dot_do_an_id, page, page_size, q
    )


@router.get("/counts", response_model=OutlineCounts)
def count_outlines(
    dot_do_an_id: int | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> OutlineCounts:
    return outlines_service.count_outlines(db, user, dot_do_an_id, q)


@router.get("/export-signed")
def export_signed_outlines(
    dot_do_an_id: int = Query(...),
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> Response:
    """Thư mục đề cương đã ký số của đợt (ZIP) để nộp về khoa."""
    ten_zip, data = outlines_service.export_signed_zip(db, dot_do_an_id)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{ten_zip}"'},
    )


@router.get("/{de_tai_id}", response_model=OutlineDetail)
def get_outline(
    de_tai_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    return outlines_service.get_detail(db, user, de_tai_id)


@router.post("/{de_tai_id}/submit", response_model=OutlineDetail, status_code=202)
def submit_outline(
    de_tai_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ghi_chu: str | None = Form(default=None, max_length=2000),
    user: CurrentUser = Depends(require_role(VaiTro.SINH_VIEN)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    """UC2.1: 202 ngay sau khi lưu + tạo bản ghi kiểm tra (D-04) — kiểm tra
    thật chạy nền SAU response, chỉ nhận ket_qua_id (int), không bao giờ
    truyền session/UploadFile vào add_task (Pattern 4, 03-RESEARCH.md)."""
    vf = documents.read_and_validate(file)
    detail, ket_qua_id = outlines_service.submit(db, user, de_tai_id, vf, ghi_chu)
    background_tasks.add_task(document_check.run, ket_qua_id)
    return detail


@router.post("/{de_tai_id}/review", response_model=OutlineDetail)
def review_outline(
    de_tai_id: int,
    payload: ReviewRequest,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    return outlines_service.review(db, user, de_tai_id, payload)


@router.post("/{de_tai_id}/forward", response_model=OutlineDetail)
def forward_outline(
    de_tai_id: int,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    """GVHD nộp đề cương đã duyệt lên Bộ môn (kiểm tra tên file + định hướng)."""
    return outlines_service.forward_to_bo_mon(db, user, de_tai_id)


@router.post("/{de_tai_id}/rename-file", response_model=OutlineDetail)
def rename_outline_file(
    de_tai_id: int,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    """GVHD đổi tên file đề cương đã duyệt theo mẫu (chỉ khi chỉ sai tên file)."""
    return outlines_service.rename_to_template(db, user, de_tai_id)


@router.post("/{de_tai_id}/bo-mon/approve", response_model=OutlineDetail)
def bo_mon_approve_outline(
    de_tai_id: int,
    file: UploadFile = File(...),
    nhan_xet: str | None = Form(default=None, max_length=5000),
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    """Lãnh đạo bộ môn phê duyệt kèm bản PDF đã ký số."""
    vf = documents.read_and_validate(file)
    return outlines_service.bo_mon_approve(db, user, de_tai_id, vf, nhan_xet)


@router.post("/{de_tai_id}/bo-mon/return", response_model=OutlineDetail)
def bo_mon_return_outline(
    de_tai_id: int,
    payload: BoMonReturnRequest,
    user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> OutlineDetail:
    return outlines_service.bo_mon_return(db, user, de_tai_id, payload.nhan_xet)
