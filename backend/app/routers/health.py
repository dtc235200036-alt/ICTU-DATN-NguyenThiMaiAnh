from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.db import SessionLocal

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(response: Response) -> dict:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "db": "error"}
