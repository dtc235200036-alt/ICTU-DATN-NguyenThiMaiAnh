"""Các endpoint nghiệp vụ — tất cả sau MỘT dependency require_api_key cấp
router (AISV-01, T-04-01). Endpoint là `def` thường: FastAPI chạy trong
threadpool nên suy luận mô hình không bao giờ chặn event loop."""
from fastapi import APIRouter, Depends, Request

from app import pipeline
from app.core.security import require_api_key
from app.schemas import (
    CheckTitleRequest,
    CheckTitleResponse,
    IngestRequest,
    IngestResponse,
)

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/ingest", response_model=IngestResponse)
def ingest(body: IngestRequest, request: Request) -> IngestResponse:
    state = request.app.state
    with state.session_factory() as session:
        count = pipeline.ingest(session, state.index, state.encoder, body.type, body.id, body.text)
    return IngestResponse(chunk_count=count, indexed=True)


@router.post("/check-title", response_model=CheckTitleResponse)
def check_title(body: CheckTitleRequest, request: Request) -> CheckTitleResponse:
    state = request.app.state
    matches = pipeline.check_title(state.index, state.encoder, body.text, body.top_k, body.nguong)
    return CheckTitleResponse(matches=matches)
