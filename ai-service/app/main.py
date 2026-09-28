"""Ứng dụng FastAPI của dịch vụ AI (§3.3).

lifespan: đọc Settings, tạo engine thesis_ai, nạp mô hình MỘT lần (D-02),
dựng CorpusIndex từ thesis_ai qua pipeline.rebuild (không encode) rồi mới phục
vụ. Chạy đúng một worker uvicorn: chỉ mục nằm trong bộ nhớ tiến trình.
"""
import logging
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI, Request

from app import minhash, pipeline
from app.api import router
from app.core.body_limit import MaxBodySizeMiddleware
from app.core.config import get_settings
from app.db import make_engine, make_session_factory
from app.embedding import Encoder
from app.index import TAI_LIEU, TIEU_DE, CorpusIndex
from app.schemas import HealthResponse

logger = logging.getLogger("ai_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = make_engine(settings.DATABASE_URL)
    session_factory = make_session_factory(engine)
    encoder = Encoder(settings.AI_MODEL_PROFILE, settings.TORCH_THREADS)
    signer = partial(
        minhash.signature, k=settings.MINHASH_SHINGLE, num_perm=settings.MINHASH_NUM_PERM
    )
    index = CorpusIndex(encoder.dim, signer=signer)
    with session_factory() as session:
        stats = pipeline.rebuild(session, index, encoder)
    logger.info("Đã nạp %s và %s vector từ thesis_ai", encoder.name, stats.loaded)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.encoder = encoder
    app.state.index = index
    app.state.thieu_embedding = stats.thieu_embedding
    try:
        yield
    finally:
        engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    is_test = settings.APP_ENV == "test"
    app = FastAPI(
        title="NTMA AI service",
        lifespan=lifespan,
        docs_url="/docs" if is_test else None,
        redoc_url=None,
        openapi_url="/openapi.json" if is_test else None,
    )

    @app.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        state = request.app.state
        index = state.index
        tieu_de = index.size(TIEU_DE)
        tai_lieu = index.size(TAI_LIEU)
        try:
            with state.session_factory() as session:
                state.thieu_embedding = pipeline.count_missing(session, state.encoder)
        except Exception:  # DB tạm lỗi: giữ số đo gần nhất, không làm hỏng /health
            logger.warning("Không đếm được chunk thiếu embedding", exc_info=True)
        return HealthResponse(
            status="ok",
            model_loaded=state.encoder is not None,
            index_size=tieu_de + tai_lieu,
            index_size_tieu_de=tieu_de,
            index_size_tai_lieu=tai_lieu,
            ten_model=state.encoder.name,
            encode_calls=state.encoder.encode_calls,
            thieu_embedding=state.thieu_embedding,
        )

    app.include_router(router)
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=settings.MAX_BODY_BYTES)
    return app


app = create_app()
