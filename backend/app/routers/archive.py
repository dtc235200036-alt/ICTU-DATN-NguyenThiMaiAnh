from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.archive import ArchiveDetail, ArchiveIn, ArchiveListItem, ImportResult
from app.schemas.common import Page
from app.services import archive

# UC5.1 (mọi vai trò đọc) + UC5.3/UC5.4 (chỉ Bộ môn ghi, T-03-26) — mỗi route
# khai báo require_role riêng. Mọi bản ghi mới/sửa/import/index lại được đẩy
# sang seam AI bằng BackgroundTasks SAU commit (D-07, UC5.2 E1: lỗi AI chỉ để
# lại CHUA_INDEX). "/khoa" và "/import" khai báo trước các route "/{kho_id}".
router = APIRouter(prefix="/api/archive", tags=["archive"])


@router.get("", response_model=Page[ArchiveListItem])
def list_archive(
    khoa: str | None = Query(default=None, max_length=20),
    giang_vien_id: int | None = Query(default=None),
    q: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> Page[ArchiveListItem]:
    # WR-10: SV không thấy điểm của sinh viên khác.
    return archive.list_archive(db, khoa, giang_vien_id, q, page, page_size, viewer=user)


@router.get("/khoa", response_model=list[str])
def khoa_options(
    _user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> list[str]:
    return archive.khoa_options(db)


@router.post("/import", response_model=ImportResult)
def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> ImportResult:
    result, new_ids = archive.import_csv(db, file)
    if new_ids:
        background_tasks.add_task(archive.run_ingest, new_ids)
    return result


@router.post("", response_model=ArchiveDetail, status_code=201)
def create_record(
    payload: ArchiveIn,
    background_tasks: BackgroundTasks,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> ArchiveDetail:
    kho_id = archive.create(db, payload)
    background_tasks.add_task(archive.run_ingest, [kho_id])
    return archive.get_detail(db, kho_id)


@router.get("/{kho_id}", response_model=ArchiveDetail)
def get_record(
    kho_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> ArchiveDetail:
    return archive.get_detail(db, kho_id, viewer=user)


@router.get("/{kho_id}/file")
def download_file(
    kho_id: int,
    _user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> FileResponse:
    path, ten_goc, media_type = archive.file_path_or_404(db, kho_id)
    return FileResponse(path, filename=ten_goc, media_type=media_type)


@router.put("/{kho_id}", response_model=ArchiveDetail)
def update_record(
    kho_id: int,
    payload: ArchiveIn,
    background_tasks: BackgroundTasks,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> ArchiveDetail:
    archive.update_record(db, kho_id, payload)
    background_tasks.add_task(archive.run_ingest, [kho_id])
    return archive.get_detail(db, kho_id)


@router.delete("/{kho_id}", status_code=204)
def delete_record(
    kho_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> None:
    archive.delete(db, kho_id)


@router.post("/{kho_id}/reindex", response_model=ArchiveDetail, status_code=202)
def reindex_record(
    kho_id: int,
    background_tasks: BackgroundTasks,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> ArchiveDetail:
    archive.mark_for_reindex(db, kho_id)
    background_tasks.add_task(archive.run_ingest, [kho_id])
    return archive.get_detail(db, kho_id)
