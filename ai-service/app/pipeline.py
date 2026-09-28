"""Pipeline kiểm tra trùng lặp (AISV-02..05) — các hàm plan 04-04 gọi trực tiếp.

- ingest / ingest_many : REPLACE theo (loai, ma_nguon), một lần encode cho cả lô
- check_title          : tìm tiêu đề gần nghĩa trong phân vùng tieu_de
- rebuild              : dựng lại chỉ mục bộ nhớ từ thesis_ai, KHÔNG encode
"""
import hashlib
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.embedding import Encoder
from app.index import TIEU_DE, ChunkRow, CorpusIndex, partition_of
from app.models import (
    LOAI_ARCHIVE,
    LOAI_TOPIC,
    Chunk,
    Embedding,
    IndexMetadata,
)
from app.nlp.normalize import one_line

logger = logging.getLogger("ai_service.pipeline")

# Các thao tác ghi (ingest/reindex) được tuần tự hóa: tránh hai lần thay thế
# cùng một nguồn chen nhau giữa DB và bộ nhớ. Tìm kiếm không cần khóa này.
_WRITE_LOCK = threading.Lock()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def chunk_texts(loai: str, text: str) -> list[str]:
    """Văn bản → danh sách chunk (đã NFC)."""
    if loai in (LOAI_TOPIC, LOAI_ARCHIVE):
        title = one_line(text)
        return [title] if title else []
    raise ValueError(f"loai_nguon không hỗ trợ: {loai}")


@dataclass(frozen=True)
class IngestItem:
    loai: str
    ma_nguon: int
    text: str


def _is_unchanged(session: Session, encoder: Encoder, loai: str, ma_nguon: int, hashes: list[str]) -> bool:
    stored = session.execute(
        select(Chunk.id, Chunk.bam_noi_dung)
        .where(Chunk.loai_nguon == loai, Chunk.ma_nguon == ma_nguon)
        .order_by(Chunk.thu_tu)
    ).all()
    if [h for _, h in stored] != hashes:
        return False
    if not stored:
        return True
    with_embedding = session.scalar(
        select(func.count(Embedding.id)).where(
            Embedding.chunk_id.in_([cid for cid, _ in stored]),
            Embedding.ten_model == encoder.name,
        )
    )
    return with_embedding == len(stored)


def _upsert_index_metadata(session: Session, ten_model: str) -> None:
    so_vector = session.scalar(
        select(func.count(Embedding.id)).where(Embedding.ten_model == ten_model)
    )
    meta = session.scalar(select(IndexMetadata).where(IndexMetadata.ten_model == ten_model))
    if meta is None:
        session.add(IndexMetadata(ten_model=ten_model, so_vector=so_vector, cap_nhat_luc=_utcnow()))
    else:
        meta.so_vector = so_vector
        meta.cap_nhat_luc = _utcnow()


def ingest_many(
    session: Session, index: CorpusIndex, encoder: Encoder, items: list[IngestItem]
) -> list[int]:
    """Ingest cả lô với MỘT lần encode; trả số chunk của từng mục.

    Ngữ nghĩa REPLACE theo (loai, ma_nguon): mọi chunk cũ của nguồn bị thay;
    văn bản không sinh chunk nào để lại nguồn rỗng. Nguồn không đổi (cùng
    chuỗi băm + đã có embedding của mô hình hiện tại) → không encode.
    """
    with _WRITE_LOCK:
        planned: list[tuple[IngestItem, list[str]]] = []
        counts: list[int] = []
        # Mục cuối cùng thắng khi một lô lặp lại cùng nguồn.
        last_of: dict[tuple[str, int], int] = {}
        for pos, item in enumerate(items):
            last_of[(item.loai, item.ma_nguon)] = pos
        for pos, item in enumerate(items):
            texts = chunk_texts(item.loai, item.text)
            counts.append(len(texts))
            if last_of[(item.loai, item.ma_nguon)] != pos:
                continue
            hashes = [_sha256(t) for t in texts]
            if _is_unchanged(session, encoder, item.loai, item.ma_nguon, hashes):
                continue
            planned.append((item, texts))

        if not planned:
            return counts

        all_texts = [t for _, texts in planned for t in texts]
        vectors = encoder.encode(all_texts)

        new_rows: list[tuple[IngestItem, list[ChunkRow], np.ndarray]] = []
        offset = 0
        try:
            for item, texts in planned:
                old_ids = select(Chunk.id).where(
                    Chunk.loai_nguon == item.loai, Chunk.ma_nguon == item.ma_nguon
                )
                # Xóa tường minh embedding trước (không phụ thuộc PRAGMA
                # foreign_keys của SQLite); MySQL còn có ON DELETE CASCADE.
                session.execute(delete(Embedding).where(Embedding.chunk_id.in_(old_ids)))
                session.execute(
                    delete(Chunk).where(
                        Chunk.loai_nguon == item.loai, Chunk.ma_nguon == item.ma_nguon
                    )
                )
                chunks = [
                    Chunk(
                        loai_nguon=item.loai,
                        ma_nguon=item.ma_nguon,
                        thu_tu=i,
                        noi_dung=t,
                        bam_noi_dung=_sha256(t),
                    )
                    for i, t in enumerate(texts, start=1)
                ]
                session.add_all(chunks)
                session.flush()
                item_vectors = vectors[offset : offset + len(texts)]
                offset += len(texts)
                session.add_all(
                    Embedding(
                        chunk_id=c.id,
                        ten_model=encoder.name,
                        so_chieu=encoder.dim,
                        vector=v.astype("<f4").tobytes(),
                    )
                    for c, v in zip(chunks, item_vectors)
                )
                rows = [ChunkRow(c.id, c.loai_nguon, c.ma_nguon, c.thu_tu, c.noi_dung) for c in chunks]
                new_rows.append((item, rows, item_vectors))
            session.flush()
            _upsert_index_metadata(session, encoder.name)
            session.commit()
        except Exception:
            session.rollback()
            raise

        with index.lock:
            for item, rows, item_vectors in new_rows:
                index.remove_source(item.loai, item.ma_nguon)
                index.add(partition_of(item.loai), rows, item_vectors)
        return counts


def ingest(
    session: Session, index: CorpusIndex, encoder: Encoder, loai: str, ma_nguon: int, text: str
) -> int:
    """Ingest một nguồn (REPLACE); trả số chunk. Đúng một encode khi có thay đổi."""
    return ingest_many(session, index, encoder, [IngestItem(loai, ma_nguon, text)])[0]


def _ty_le(score: float) -> float:
    return round(min(max(float(score), 0.0), 1.0) * 100, 2)


def check_title(
    index: CorpusIndex, encoder: Encoder, text: str, top_k: int, nguong: float | None
) -> list[dict]:
    """Top-k đề tài/đồ án gần nghĩa: [{ref_id, loai, ty_le}] với ty_le = cosine×100."""
    query = one_line(text)
    if not query or index.size(TIEU_DE) == 0:
        return []
    vector = encoder.encode([query])
    scores, ids = index.search(TIEU_DE, vector, top_k * 3)
    best: dict[tuple[str, int], float] = {}
    for score, chunk_id in zip(scores[0], ids[0]):
        if chunk_id < 0:
            continue
        row = index.row(TIEU_DE, int(chunk_id))
        if row is None:
            continue
        key = (row.loai, row.ma_nguon)
        ty_le = _ty_le(score)
        if ty_le > best.get(key, -1.0):
            best[key] = ty_le
    matches = [
        {"ref_id": ma_nguon, "loai": loai, "ty_le": ty_le}
        for (loai, ma_nguon), ty_le in best.items()
        if nguong is None or ty_le >= nguong
    ]
    matches.sort(key=lambda m: (-m["ty_le"], m["ref_id"], m["loai"]))
    return matches[:top_k]


@dataclass(frozen=True)
class RebuildStats:
    loaded: int
    thieu_embedding: int


def rebuild(session: Session, index: CorpusIndex, encoder: Encoder) -> RebuildStats:
    """Dựng lại chỉ mục bộ nhớ từ thesis_ai — KHÔNG gọi encode (D-02).

    Chunk chưa có embedding cho mô hình hiện tại được đếm (thieu_embedding) để
    /reindex bù; index_metadata lệch với số vector nạp được → ghi cảnh báo.
    """
    rows = session.execute(
        select(
            Chunk.id,
            Chunk.loai_nguon,
            Chunk.ma_nguon,
            Chunk.thu_tu,
            Chunk.noi_dung,
            Embedding.so_chieu,
            Embedding.vector,
        )
        .join(Embedding, Embedding.chunk_id == Chunk.id)
        .where(Embedding.ten_model == encoder.name)
        .order_by(Chunk.id)
    ).all()
    total_chunks = session.scalar(select(func.count(Chunk.id))) or 0

    grouped: dict[str, tuple[list[ChunkRow], list[np.ndarray]]] = {}
    loaded = 0
    for cid, loai, ma_nguon, thu_tu, noi_dung, so_chieu, blob in rows:
        if so_chieu != encoder.dim:
            continue
        part_rows, part_vecs = grouped.setdefault(partition_of(loai), ([], []))
        part_rows.append(ChunkRow(cid, loai, ma_nguon, thu_tu, noi_dung))
        part_vecs.append(np.frombuffer(blob, dtype="<f4"))
        loaded += 1

    with index.lock:
        index.clear()
        for part, (part_rows, part_vecs) in grouped.items():
            index.add(part, part_rows, np.vstack(part_vecs))

    meta = session.scalar(select(IndexMetadata).where(IndexMetadata.ten_model == encoder.name))
    if meta is not None and meta.so_vector != loaded:
        logger.warning(
            "index_metadata lệch: so_vector=%s nhưng nạp được %s vector cho %s",
            meta.so_vector,
            loaded,
            encoder.name,
        )
    thieu = int(total_chunks) - loaded
    if thieu:
        logger.warning("%s chunk chưa có embedding cho %s (dùng /reindex)", thieu, encoder.name)
    return RebuildStats(loaded=loaded, thieu_embedding=thieu)
