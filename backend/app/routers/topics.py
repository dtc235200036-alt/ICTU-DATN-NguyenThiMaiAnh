from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import CurrentUser, require_role
from app.core.roles import ANY_ROLE, VaiTro
from app.schemas.common import Page
from app.schemas.topics import (
    TitleCheckRequest,
    TitleCheckResult,
    TitleMatch,
    TopicCreate,
    TopicListItem,
    TopicListParams,
    TopicOut,
    TopicUpdate,
)
from app.schemas.history import TopicEvent
from app.services import ai_index, documents, student_history
from app.services import title_check as title_check_service
from app.services import topics as topics_service

# UC1.1/AUTH-03 (góp ý GVHD mục 1): chỉ GVHD tạo/sửa/gửi đề tài và kiểm tra
# trùng tên (SV, Bộ môn nhận 403); SV không tự đề xuất/đăng ký và không còn
# route duyệt đề tài. Xem chi tiết/danh sách mở cho mọi vai trò đã xác thực
# (UC1.2), quyền xem/phạm vi thực sự do can_view/list_topics
# (T-02-23/T-02-29) quyết định ở tầng service.
router = APIRouter(prefix="/api/topics", tags=["topics"])

_TrangThaiFilter = Literal["NHAP", "DA_PHAN_CONG"]
_PhamViFilter = Literal["tat_ca", "cua_toi"]
_SapXepFilter = Literal["moi_nhat", "ten"]


@router.get("", response_model=Page[TopicListItem])
def list_topics(
    dot_do_an_id: int | None = Query(default=None),
    trang_thai: _TrangThaiFilter | None = Query(default=None),
    giang_vien_id: int | None = Query(default=None),
    linh_vuc: str | None = Query(default=None),
    dinh_huong_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    pham_vi: _PhamViFilter = Query(default="tat_ca"),
    sap_xep: _SapXepFilter = Query(default="moi_nhat"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> Page[TopicListItem]:
    params = TopicListParams(
        dot_do_an_id=dot_do_an_id,
        trang_thai=trang_thai,
        giang_vien_id=giang_vien_id,
        linh_vuc=linh_vuc,
        dinh_huong_id=dinh_huong_id,
        q=q,
        pham_vi=pham_vi,
        sap_xep=sap_xep,
        page=page,
        page_size=page_size,
    )
    return topics_service.list_topics(db, user, params)


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(
    payload: TopicCreate,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    out = topics_service.create_topic(db, user, payload)
    if payload.gui:
        # AISV-02 push-on-write: đề tài vừa giao SV (Đã phân công) được index sau
        # commit (một lần encode) — lần kiểm tra tên kế tiếp đã thấy nó.
        background_tasks.add_task(ai_index.run_ingest_topic, out.id)
    return out


@router.put("/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topics_service.update_topic(db, user, topic_id, payload)


@router.post("/{topic_id}/submit", response_model=TopicOut)
def submit_topic(
    topic_id: int,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    out = topics_service.submit_topic(db, user, topic_id)
    # AISV-02 push-on-write: bản nháp vừa giao SV được index sau commit.
    background_tasks.add_task(ai_index.run_ingest_topic, out.id)
    return out


@router.post("/check-title", response_model=TitleCheckResult)
def check_title(
    payload: TitleCheckRequest,
    _user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TitleCheckResult:
    """UC0.6 (chỉ GVHD, UC1.1): kiểm tra tức thời, KHÔNG lưu kết quả (bản lưu chỉ
    xảy ra khi GVHD giao đề tài thật sự — xem topics_service.create_topic/
    submit_topic)."""
    result = title_check_service.kiem_tra_ten(db, payload.ten_de_tai)
    return TitleCheckResult(
        trang_thai=result.trang_thai,
        nguong=result.nguong,
        matches=[
            TitleMatch(
                nguon=m.nguon,
                de_tai_id=m.de_tai_id,
                do_an_kho_id=m.do_an_kho_id,
                ten_de_tai=m.ten_de_tai,
                khoa=m.khoa,
                giang_vien=m.giang_vien,
                ty_le=m.ty_le,
            )
            for m in result.matches
        ],
    )


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(
    topic_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> TopicOut:
    return topics_service.get_topic(db, user, topic_id)



@router.post("/{topic_id}/attachment", response_model=TopicOut)
def attach_topic_file(
    topic_id: int,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role(VaiTro.GIANG_VIEN)),
    db: Session = Depends(get_db),
) -> TopicOut:
    """GVHD đính kèm file mô tả đề tài (DOCX/PDF, cùng kiểm tra định dạng/dung
    lượng như đề cương); tải về qua /api/documents/{id}/download."""
    vf = documents.read_and_validate(file)
    return topics_service.attach_file(db, user, topic_id, vf)


@router.get("/{topic_id}/history", response_model=list[TopicEvent])
def topic_history(
    topic_id: int,
    user: CurrentUser = Depends(require_role(*ANY_ROLE)),
    db: Session = Depends(get_db),
) -> list[TopicEvent]:
    """Lịch sử đề tài: giao đề tài, nộp/duyệt đề cương, Bộ môn phê duyệt, báo cáo."""
    return student_history.topic_history(db, user, topic_id)
