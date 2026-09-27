import re
import unicodedata
from collections.abc import Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.de_tai import NHAP, DeTai

_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


class AiServiceError(Exception):
    """Dịch vụ AI không phản hồi hoặc lỗi (UC1.1 – E2). Không bao giờ chặn nghiệp vụ."""


class AiClient(Protocol):
    def check_title(self, text: str, top_k: int = 5) -> dict:
        """§3.3.5 /check-title: {matches: [{ref_id, ty_le}]}."""
        ...


def _tokenize(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return set(_WORD_RE.findall(normalized))


def _jaccard_percent(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return round((intersection / union) * 100, 2)


class AiClientStub:
    """D-10: giả lập ngữ nghĩa bằng Jaccard trên tập âm tiết — cùng hợp đồng
    `{matches: [{ref_id, ty_le}]}` mà Phase 4 sẽ thay bằng dịch vụ AI thật, nên
    không caller nào phải đổi khi seam này được swap.

    `corpus_provider` được gọi lại ở mỗi lần check_title (không cache) để luôn
    thấy đề tài mới nhất; Phase 4 thay bằng một httpx client cùng chữ ký.
    """

    def __init__(
        self, corpus_provider: Callable[[], list[tuple[int, str]]], mode: str = "normal"
    ) -> None:
        self._corpus_provider = corpus_provider
        self._mode = mode

    def check_title(self, text: str, top_k: int = 5) -> dict:
        if self._mode == "loi":
            raise AiServiceError("Dịch vụ AI không phản hồi (mô phỏng AI_STUB_MODE=loi)")

        query_tokens = _tokenize(text)
        scored: list[tuple[float, int]] = []
        for ref_id, ref_title in self._corpus_provider():
            ty_le = _jaccard_percent(query_tokens, _tokenize(ref_title))
            if ty_le > 0:
                scored.append((ty_le, ref_id))

        scored.sort(key=lambda item: (-item[0], item[1]))
        top = scored[:top_k]
        return {"matches": [{"ref_id": ref_id, "ty_le": ty_le} for ty_le, ref_id in top]}


def _corpus_provider_factory(db: Session) -> Callable[[], list[tuple[int, str]]]:
    def _provider() -> list[tuple[int, str]]:
        rows = db.execute(
            select(DeTai.id, DeTai.ten_de_tai).where(DeTai.trang_thai != NHAP)
        ).all()
        return [(row.id, row.ten_de_tai) for row in rows]

    return _provider


def get_ai_client(db: Session) -> AiClient:
    settings = get_settings()
    # Phase 2 chỉ hỗ trợ "stub"; Phase 4 thêm nhánh AI_CLIENT="http" ở đây.
    return AiClientStub(_corpus_provider_factory(db), mode=settings.AI_STUB_MODE)
