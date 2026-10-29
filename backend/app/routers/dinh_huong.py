from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.core.timeutil import now_utc
from app.models.de_tai import DeTai
from app.models.dinh_huong import THU_MUC_TEP_DINH_HUONG, DinhHuong
from app.schemas.dinh_huong import DinhHuongIn, DinhHuongOut, TepDinhHuongOut
from app.services import documents

# Danh mục định hướng đề tài: mọi vai trò đọc (form giao đề tài, bộ lọc, kiểm
# tra tên file đề cương) và xem file PDF mô tả định hướng; chỉ Bộ môn thêm/sửa
# và tải lên/thay/gỡ file mô tả (0019).
router = APIRouter(prefix="/api/dinh-huong", tags=["dinh-huong"])

_NOT_FOUND_DETAIL = "Không tìm thấy định hướng"
_DUPLICATE_DETAIL = "Mã định hướng đã tồn tại"
_NOT_PDF_DETAIL = "File mô tả định hướng phải là PDF"
_NO_FILE_DETAIL = "Định hướng chưa có file mô tả"
_FILE_MISSING_DETAIL = "Không tìm thấy file"


def _to_out(item: DinhHuong, so_de_tai: int = 0) -> DinhHuongOut:
    tep = None
    if item.tep_ten_luu_tru is not None:
        tep = TepDinhHuongOut(
            ten_goc=item.tep_ten_goc,
            kich_thuoc=item.tep_kich_thuoc,
            cap_nhat_luc=item.tep_cap_nhat_luc,
        )
    return DinhHuongOut(
        id=item.id,
        ma=item.ma,
        ten=item.ten,
        mo_ta=item.mo_ta,
        hoat_dong=item.hoat_dong,
        so_de_tai=so_de_tai,
        tep=tep,
    )


def _get_for_update_or_404(db: Session, dinh_huong_id: int) -> DinhHuong:
    """Khóa hàng tới khi commit: hai lượt thay file đồng thời không cùng đọc
    một tên file cũ (file của lượt trước sẽ thành file mồ côi trên đĩa)."""
    item = db.execute(
        select(DinhHuong)
        .where(DinhHuong.id == dinh_huong_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    return item


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


@router.get("/{dinh_huong_id}/tep")
def download_tep_mo_ta(
    dinh_huong_id: int,
    _user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> FileResponse:
    """File PDF mô tả định hướng (client xem trong khung PDF hoặc tải về). Như
    GET /api/dinh-huong, định hướng đã ngừng sử dụng vẫn xem được — đề tài cũ
    còn gắn với nó."""
    item = db.get(DinhHuong, dinh_huong_id)
    if item is None:
        raise HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)
    if item.tep_ten_luu_tru is None:
        raise HTTPException(status_code=404, detail=_NO_FILE_DETAIL)
    path = documents.storage_path(item.tep_ten_luu_tru)
    if not path.exists():
        raise HTTPException(status_code=404, detail=_FILE_MISSING_DETAIL)
    # Cùng URL nhưng nội dung đổi khi Bộ môn thay file — trình duyệt phải hỏi
    # lại server (ETag) thay vì dùng bản cũ trong cache.
    return FileResponse(
        path,
        filename=item.tep_ten_goc,
        media_type="application/pdf",
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/{dinh_huong_id}/tep", response_model=DinhHuongOut)
def upload_tep_mo_ta(
    dinh_huong_id: int,
    file: UploadFile = File(...),
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> DinhHuongOut:
    """Bộ môn tải lên hoặc thay file PDF mô tả định hướng (cùng kiểm tra dung
    lượng/magic bytes như đề cương). File cũ chỉ bị xóa sau khi commit thành
    công; commit lỗi thì xóa file mới vừa ghi."""
    # Xét đuôi trước khi đọc: DOCX bị từ chối ngay với thông báo "phải là PDF"
    # thay vì được đọc và trích xuất văn bản vô ích.
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(status_code=422, detail=_NOT_PDF_DETAIL)
    vf = documents.read_and_validate(file)

    item = _get_for_update_or_404(db, dinh_huong_id)
    ten_luu_tru_cu = item.tep_ten_luu_tru
    ten_luu_tru = documents.write_file(THU_MUC_TEP_DINH_HUONG, vf)
    try:
        item.tep_ten_goc = vf.ten_goc
        item.tep_ten_luu_tru = ten_luu_tru
        item.tep_kich_thuoc = len(vf.content)
        item.tep_cap_nhat_luc = now_utc()
        db.commit()
    except Exception:
        db.rollback()
        documents.remove_file_quietly(ten_luu_tru)
        raise
    if ten_luu_tru_cu is not None:
        documents.remove_file_quietly(ten_luu_tru_cu)
    db.refresh(item)
    return _to_out(item)


@router.delete("/{dinh_huong_id}/tep", status_code=204)
def delete_tep_mo_ta(
    dinh_huong_id: int,
    _user: CurrentUser = Depends(require_role(VaiTro.BO_MON)),
    db: Session = Depends(get_db),
) -> None:
    """Bộ môn gỡ file mô tả; file trên đĩa chỉ bị xóa sau khi commit."""
    item = _get_for_update_or_404(db, dinh_huong_id)
    ten_luu_tru = item.tep_ten_luu_tru
    if ten_luu_tru is None:
        raise HTTPException(status_code=404, detail=_NO_FILE_DETAIL)
    item.tep_ten_goc = None
    item.tep_ten_luu_tru = None
    item.tep_kich_thuoc = None
    item.tep_cap_nhat_luc = None
    db.commit()
    documents.remove_file_quietly(ten_luu_tru)
