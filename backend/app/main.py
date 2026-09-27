from fastapi import FastAPI

from app.core.body_limit import MaxBodySizeMiddleware
from app.routers import discover_routers

app = FastAPI(
    title="NTMA Web API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.add_middleware(MaxBodySizeMiddleware)

for router in discover_routers():
    app.include_router(router)
