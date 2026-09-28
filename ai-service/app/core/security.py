"""Khóa API nội bộ (AISV-01, §3.3.5, T-04-01/T-04-02).

Mọi endpoint trừ /health đi qua MỘT dependency cấp router. So sánh hằng thời
gian bằng hmac.compare_digest; giá trị nhận được không bao giờ được ghi log
hay trả lại trong phản hồi (detail là một câu cố định).
"""
import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_DETAIL = "Thiếu hoặc sai API key nội bộ"


def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    expected = get_settings().AI_API_KEY.get_secret_value().encode("utf-8")
    received = (api_key or "").encode("utf-8")
    if not api_key or not hmac.compare_digest(received, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_DETAIL)
