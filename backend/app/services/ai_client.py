import logging
import re
import unicodedata
from collections import deque
from collections.abc import Callable, Iterable
from typing import Protocol

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, LOAI_DE_CUONG, TaiLieuDoAn
from app.models.de_tai import NHAP, DeTai

_logger = logging.getLogger(__name__)

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
    def check_title(self, text: str, top_k: int = 5, nguong: float | None = None) -> dict:
        """§3.3.5 /check-title: {matches: [{ref_id, loai: TOPIC|ARCHIVE, ty_le}]}
        — `nguong` là ngưỡng hiện hành do Web API gửi theo từng request (D-04)."""
        ...

    def check_document(
        self,
        ref_id: int,
        text: str,
        top_k: int = 5,
        nguong_doan: float | None = None,
        loai_tru: Iterable[int] | None = None,
    ) -> dict:
        """§3.3.5 /check-document: {ty_le_tong, do_an_trung: [...], chi_tiet: [...]}
        — `loai_tru` = id tài liệu không bao giờ được so khớp (vd. các phiên bản
        trước của cùng đề tài)."""
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

    def check_title(self, text: str, top_k: int = 5, nguong: float | None = None) -> dict:
        # `nguong` được nhận để cùng chữ ký với AiClientHttp; bộ giả lập không
        # lọc theo nó (thang Jaccard khác thang cosine) — title_check lọc sau.
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
        return {
            "matches": [
                {"ref_id": ref_id, "loai": "TOPIC", "ty_le": ty_le} for ty_le, ref_id in top
            ]
        }

    def check_document(
        self,
        ref_id: int,
        text: str,
        top_k: int = 5,
        nguong_doan: float | None = None,
        loai_tru: Iterable[int] | None = None,
    ) -> dict:
        excluded = set(loai_tru or ())
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
                if doc_id == ref_id or doc_id in excluded:
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


class AiClientHttp:
    """D-07: client HTTP tới dịch vụ AI nội bộ (§3.3.5) — cùng chữ ký với
    AiClientStub nên không caller nào phải đổi. Mỗi lời gọi một httpx.Client
    (không chia sẻ trạng thái giữa request/background task), header
    X-API-Key, timeout connect 2 s + read/write theo từng loại lời gọi.

    MỌI lỗi (kết nối, timeout, HTTP không 2xx, thân trả về sai hợp đồng) đều
    thành AiServiceError với thông điệp chỉ gồm endpoint + trạng thái — không
    bao giờ chứa header hay khóa (T-04-16). Caller suy biến theo UC1.1 E2 /
    UC0.7 E1 (không bao giờ chặn nghiệp vụ)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        title_timeout: float,
        document_timeout: float,
        ingest_timeout: float,
        document_timeout_per_1k_chars: float = 0.0,
        document_timeout_max: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._title_timeout = title_timeout
        self._document_timeout = document_timeout
        self._ingest_timeout = ingest_timeout
        self._per_1k = document_timeout_per_1k_chars
        self._timeout_max = document_timeout_max
        self._transport = transport

    def _scaled(self, base: float, text: str) -> float:
        """CR-02: timeout theo độ dài văn bản (base + hệ số × nghìn ký tự),
        không vượt trần; văn bản ngắn giữ đúng base."""
        timeout = max(base, self._document_timeout + self._per_1k * len(text) / 1000)
        if self._timeout_max is not None:
            timeout = min(timeout, max(base, self._timeout_max))
        return timeout

    def _fail(self, message: str) -> AiServiceError:
        _logger.warning(message)
        return AiServiceError(message)

    def _post(self, path: str, payload: dict, read_timeout: float, required: tuple[str, ...]) -> dict:
        timeout = httpx.Timeout(read_timeout, connect=2.0)
        try:
            with httpx.Client(
                base_url=self._base_url,
                headers={"X-API-Key": self._api_key},
                timeout=timeout,
                transport=self._transport,
            ) as client:
                response = client.post(path, json=payload)
        except httpx.HTTPError as exc:
            # Chỉ tên lớp lỗi — không dùng str(exc)/repr(request) (có thể kèm header).
            raise self._fail(
                f"Dịch vụ AI không phản hồi khi gọi {path} ({type(exc).__name__})"
            ) from None

        if not 200 <= response.status_code < 300:
            raise self._fail(f"Dịch vụ AI trả lỗi khi gọi {path} (HTTP {response.status_code})")
        try:
            body = response.json()
        except ValueError:
            raise self._fail(f"Dịch vụ AI trả dữ liệu không hợp lệ khi gọi {path}") from None
        if not isinstance(body, dict) or any(key not in body for key in required):
            raise self._fail(f"Dịch vụ AI trả dữ liệu sai hợp đồng khi gọi {path}")
        return body

    def check_title(self, text: str, top_k: int = 5, nguong: float | None = None) -> dict:
        body = self._post(
            "/check-title",
            {"text": text, "top_k": top_k, "nguong": nguong},
            self._title_timeout,
            ("matches",),
        )
        matches = body["matches"]
        if not isinstance(matches, list) or not all(
            isinstance(m, dict) and {"ref_id", "loai", "ty_le"} <= m.keys() for m in matches
        ):
            raise self._fail("Dịch vụ AI trả dữ liệu sai hợp đồng khi gọi /check-title")
        return body

    def check_document(
        self,
        ref_id: int,
        text: str,
        top_k: int = 5,
        nguong_doan: float | None = None,
        loai_tru: Iterable[int] | None = None,
    ) -> dict:
        # nguong_nguyen_van cố ý bỏ trống — dịch vụ AI dùng giá trị hiệu chỉnh.
        payload = {
            "ref_id": ref_id,
            "text": text,
            "top_k": top_k,
            "nguong_doan": nguong_doan,
            "loai_tru": sorted(set(loai_tru or ())),
        }
        return self._post(
            "/check-document",
            payload,
            self._scaled(self._document_timeout, text),
            ("ty_le_tong", "do_an_trung", "chi_tiet"),
        )

    def ingest(self, ref_id: int, loai: str, text: str) -> dict:
        return self._post(
            "/ingest",
            {"id": ref_id, "type": loai, "text": text},
            self._scaled(self._ingest_timeout, text) if loai == "DOCUMENT" else self._ingest_timeout,
            ("chunk_count", "indexed"),
        )


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
    if settings.AI_CLIENT == "http":
        # D-07: dịch vụ AI thật trên mạng nội bộ (Settings đã bắt buộc URL + khóa).
        return AiClientHttp(
            settings.AI_SERVICE_URL or "",
            settings.AI_API_KEY or "",
            title_timeout=settings.AI_TITLE_TIMEOUT_SECONDS,
            document_timeout=settings.AI_DOCUMENT_TIMEOUT_SECONDS,
            ingest_timeout=settings.AI_INGEST_TIMEOUT_SECONDS,
            document_timeout_per_1k_chars=settings.AI_DOCUMENT_TIMEOUT_PER_1K_CHARS,
            document_timeout_max=settings.AI_DOCUMENT_TIMEOUT_MAX_SECONDS,
        )
    # Phương án dự phòng (AI_CLIENT=stub): bộ giả lập Phase 2/3.
    return AiClientStub(
        _corpus_provider_factory(db),
        mode=settings.AI_STUB_MODE,
        document_corpus_provider=_document_corpus_provider_factory(db),
    )
