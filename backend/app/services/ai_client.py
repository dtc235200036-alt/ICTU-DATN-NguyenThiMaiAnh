import re
import unicodedata
from collections import deque
from collections.abc import Callable
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, LOAI_DE_CUONG, TaiLieuDoAn
from app.models.de_tai import NHAP, DeTai

_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)

# D-10 (Phase 2) + Pattern 2 (03-RESEARCH.md): đoạn văn hợp lệ để so khớp khi
# kiểm tra tài liệu (UC0.7) — dòng không rỗng có >= 8 âm tiết sau NFC.
_PARAGRAPH_MIN_TOKENS = 8
_MATCH_THRESHOLD = 50.0

# Stub ingest (D-07/UC5.3): "đẩy" vào corpus giả lập — chỉ ghi log, không có
# chỉ mục vector thật (Phase 4 thay bằng dịch vụ AI thật cùng chữ ký).
INGEST_LOG: deque = deque(maxlen=1000)


class AiServiceError(Exception):
    """Dịch vụ AI không phản hồi hoặc lỗi (UC1.1 – E2, UC0.7 – E1/E2). Không
    bao giờ chặn nghiệp vụ."""


class AiClient(Protocol):
    def check_title(self, text: str, top_k: int = 5) -> dict:
        """§3.3.5 /check-title: {matches: [{ref_id, ty_le}]}."""
        ...

    def check_document(self, ref_id: int, text: str, top_k: int = 5) -> dict:
        """§3.3.5 /check-document: {ty_le_tong, do_an_trung: [...], chi_tiet: [...]}."""
        ...

    def ingest(self, ref_id: int, loai: str, text: str) -> dict:
        """§3.3.5 /ingest: {chunk_count, indexed: true}."""
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


def _paragraphs(text: str) -> list[str]:
    """Tách văn bản thành các đoạn hợp lệ (Pattern 2, 03-RESEARCH.md): mỗi
    dòng không rỗng có >= 8 âm tiết sau NFC-casefold được coi là một đoạn."""
    normalized = unicodedata.normalize("NFC", text)
    paragraphs = []
    for line in normalized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if len(_WORD_RE.findall(stripped.casefold())) >= _PARAGRAPH_MIN_TOKENS:
            paragraphs.append(stripped)
    return paragraphs


class AiClientStub:
    """D-10: giả lập ngữ nghĩa bằng Jaccard trên tập âm tiết — cùng hợp đồng
    `{matches: [{ref_id, ty_le}]}` / `{ty_le_tong, do_an_trung, chi_tiet}` /
    `{chunk_count, indexed}` mà Phase 4 sẽ thay bằng dịch vụ AI thật, nên
    không caller nào phải đổi khi seam này được swap.

    `corpus_provider`/`document_corpus_provider` được gọi lại ở mỗi lần kiểm
    tra (không cache) để luôn thấy dữ liệu mới nhất; Phase 4 thay bằng một
    httpx client cùng chữ ký.
    """

    def __init__(
        self,
        corpus_provider: Callable[[], list[tuple[int, str]]],
        mode: str = "normal",
        document_corpus_provider: Callable[[], list[tuple[int, int, str]]] | None = None,
    ) -> None:
        self._corpus_provider = corpus_provider
        self._mode = mode
        self._document_corpus_provider = document_corpus_provider

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

    def check_document(self, ref_id: int, text: str, top_k: int = 5) -> dict:
        if self._mode == "loi":
            raise AiServiceError("Dịch vụ AI không phản hồi (mô phỏng AI_STUB_MODE=loi)")

        query_paragraphs = _paragraphs(text)
        total = len(query_paragraphs)
        if total == 0 or self._document_corpus_provider is None:
            return {"ty_le_tong": 0.0, "do_an_trung": [], "chi_tiet": []}

        corpus = self._document_corpus_provider()
        # Không so khớp với chính đề tài của phiên bản đang kiểm tra (các
        # phiên bản trước của cùng một đề tài không tính là "trùng").
        own_de_tai_id: int | None = None
        for doc_id, de_tai_id, _entry_text in corpus:
            if doc_id == ref_id:
                own_de_tai_id = de_tai_id
                break

        entry_paragraphs_cache: dict[int, list[str]] = {}
        flagged_count = 0
        entry_match_counts: dict[int, int] = {}
        chi_tiet: list[dict] = []

        for idx, query_paragraph in enumerate(query_paragraphs, start=1):
            query_token_set = _tokenize(query_paragraph)
            best_score = 0.0
            best_doc_id: int | None = None
            best_entry_paragraph: str | None = None

            for doc_id, de_tai_id, entry_text in corpus:
                if doc_id == ref_id:
                    continue
                if own_de_tai_id is not None and de_tai_id == own_de_tai_id:
                    continue
                if doc_id not in entry_paragraphs_cache:
                    entry_paragraphs_cache[doc_id] = _paragraphs(entry_text)
                for entry_paragraph in entry_paragraphs_cache[doc_id]:
                    score = _jaccard_percent(query_token_set, _tokenize(entry_paragraph))
                    if score > best_score:
                        best_score = score
                        best_doc_id = doc_id
                        best_entry_paragraph = entry_paragraph

            if best_doc_id is not None and best_score >= _MATCH_THRESHOLD:
                flagged_count += 1
                entry_match_counts[best_doc_id] = entry_match_counts.get(best_doc_id, 0) + 1
                chi_tiet.append(
                    {
                        "ref_id": best_doc_id,
                        "doan_nguon": query_paragraph,
                        "doan_trung": best_entry_paragraph,
                        "vi_tri": f"Đoạn {idx}",
                        "ty_le": best_score,
                    }
                )

        chi_tiet.sort(key=lambda item: -item["ty_le"])
        chi_tiet = chi_tiet[:50]

        do_an_trung = [
            {"ref_id": doc_id, "ty_le": round(100 * count / total, 2)}
            for doc_id, count in entry_match_counts.items()
        ]
        do_an_trung.sort(key=lambda item: -item["ty_le"])
        do_an_trung = do_an_trung[:top_k]

        ty_le_tong = round(100 * flagged_count / total, 2) if total else 0.0

        return {"ty_le_tong": ty_le_tong, "do_an_trung": do_an_trung, "chi_tiet": chi_tiet}

    def ingest(self, ref_id: int, loai: str, text: str) -> dict:
        if self._mode == "loi":
            raise AiServiceError("Dịch vụ AI không phản hồi (mô phỏng AI_STUB_MODE=loi)")

        chunk_count = len(_paragraphs(text))
        INGEST_LOG.append({"ref_id": ref_id, "loai": loai, "text_len": len(text)})
        return {"chunk_count": chunk_count, "indexed": True}


def _corpus_provider_factory(db: Session) -> Callable[[], list[tuple[int, str]]]:
    def _provider() -> list[tuple[int, str]]:
        rows = db.execute(
            select(DeTai.id, DeTai.ten_de_tai).where(DeTai.trang_thai != NHAP)
        ).all()
        return [(row.id, row.ten_de_tai) for row in rows]

    return _provider


def _document_corpus_provider_factory(
    db: Session,
) -> Callable[[], list[tuple[int, int, str]]]:
    """Phiên bản mới nhất theo (de_tai_id, loai) trong {DE_CUONG, BAO_CAO_CUOI}
    có văn bản trích xuất hợp lệ — dùng làm corpus cho check_document."""

    def _provider() -> list[tuple[int, int, str]]:
        latest = (
            select(
                TaiLieuDoAn.de_tai_id,
                TaiLieuDoAn.loai,
                func.max(TaiLieuDoAn.so_phien_ban).label("max_ver"),
            )
            .where(TaiLieuDoAn.loai.in_([LOAI_DE_CUONG, LOAI_BAO_CAO_CUOI]))
            .where(TaiLieuDoAn.trich_xuat_loi.is_(False))
            .where(TaiLieuDoAn.noi_dung_trich_xuat.is_not(None))
            .group_by(TaiLieuDoAn.de_tai_id, TaiLieuDoAn.loai)
            .subquery()
        )
        rows = db.execute(
            select(
                TaiLieuDoAn.id, TaiLieuDoAn.de_tai_id, TaiLieuDoAn.noi_dung_trich_xuat
            ).join(
                latest,
                (TaiLieuDoAn.de_tai_id == latest.c.de_tai_id)
                & (TaiLieuDoAn.loai == latest.c.loai)
                & (TaiLieuDoAn.so_phien_ban == latest.c.max_ver),
            )
        ).all()
        return [(row.id, row.de_tai_id, row.noi_dung_trich_xuat) for row in rows]

    return _provider


def get_ai_client(db: Session) -> AiClient:
    settings = get_settings()
    # Phase 2/3 chỉ hỗ trợ "stub"; Phase 4 thêm nhánh AI_CLIENT="http" ở đây.
    return AiClientStub(
        _corpus_provider_factory(db),
        mode=settings.AI_STUB_MODE,
        document_corpus_provider=_document_corpus_provider_factory(db),
    )
