"""Các endpoint nghiệp vụ — tất cả sau MỘT dependency require_api_key cấp
router (AISV-01, T-04-01). Endpoint là `def` thường: FastAPI chạy trong
threadpool nên suy luận mô hình không bao giờ chặn event loop."""
from fastapi import APIRouter, Depends, Request

from app import pipeline
from app.core.security import require_api_key
from app.schemas import (
    CheckDocumentRequest,
    CheckDocumentResponse,
    CheckTitleRequest,
    CheckTitleResponse,
    IngestRequest,
    IngestResponse,
    ReindexRequest,
    ReindexResponse,
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


@router.post("/check-document", response_model=CheckDocumentResponse)
def check_document(body: CheckDocumentRequest, request: Request) -> dict:
    state = request.app.state
    settings = state.settings
    exclude = {body.ref_id, *body.loai_tru}
    scores = pipeline.score_document(
        state.index,
        state.encoder,
        body.text,
        exclude,
        shingle=settings.MINHASH_SHINGLE,
        num_perm=settings.MINHASH_NUM_PERM,
    )
    return pipeline.check_document(
        scores,
        body.nguong_doan if body.nguong_doan is not None else settings.NGUONG_DOAN_MAC_DINH,
        body.nguong_nguyen_van
        if body.nguong_nguyen_van is not None
        else settings.NGUONG_NGUYEN_VAN_MAC_DINH,
        body.top_k,
        settings.CHI_TIET_TOI_DA,
    )


@router.post("/reindex", response_model=ReindexResponse)
def reindex(request: Request, body: ReindexRequest | None = None) -> ReindexResponse:
    state = request.app.state
    with state.session_factory() as session:
        if body is not None and body.items:
            items = [pipeline.IngestItem(i.type, i.id, i.text) for i in body.items]
            pipeline.ingest_many(session, state.index, state.encoder, items)
            return ReindexResponse(indexed_count=len(items))
        stats = pipeline.reembed_missing(session, state.index, state.encoder)
    return ReindexResponse(indexed_count=stats.loaded)
