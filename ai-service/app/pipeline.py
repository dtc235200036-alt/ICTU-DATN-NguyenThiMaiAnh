"""Pipeline kiểm tra trùng lặp (AISV-02..05) — các hàm plan 04-04 gọi trực tiếp.

- ingest / ingest_many : REPLACE theo (loai, ma_nguon), một lần encode cho cả lô
- check_title          : tìm tiêu đề gần nghĩa trong phân vùng tieu_de
- score_document       : điểm ngữ nghĩa + nguyên văn tốt nhất của từng câu
- check_document       : áp ngưỡng (theo request, D-04) → tỷ lệ, đồ án, đoạn trùng
- reembed_missing      : encode (một lần) các chunk thiếu embedding cho mô hình hiện tại
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
from app import minhash
from app.index import TAI_LIEU, TIEU_DE, ChunkRow, CorpusIndex, partition_of
from app.models import (
    LOAI_ARCHIVE,
    LOAI_DOCUMENT,
    LOAI_TOPIC,
    Chunk,
    Embedding,
    IndexMetadata,
)
from app.nlp.boilerplate import strip_boilerplate
from app.nlp.chunking import sentences
from app.nlp.normalize import nfc, one_line

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
    if loai == LOAI_DOCUMENT:
        return sentences(strip_boilerplate(text).lines)
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


# ---------------------------------------------------------------------------
# Kiểm tra tài liệu (AISV-04, AISV-05, D-03)
# ---------------------------------------------------------------------------

NGUYEN_VAN = "NGUYEN_VAN"
NGU_NGHIA = "NGU_NGHIA"
MAX_PASSAGE_SENTENCES = 6


@dataclass(frozen=True)
class ChunkScore:
    vi_tri: int  # thứ tự câu trong tài liệu được kiểm tra (từ 1)
    text: str
    n_chars: int
    sem_ref: int | None
    sem_text: str | None
    sem_thu_tu: int | None
    sem_score: float
    verb_ref: int | None
    verb_text: str | None
    verb_thu_tu: int | None
    verb_score: float


@dataclass(frozen=True)
class DocumentScores:
    chunks: list[ChunkScore]
    removed: int


def score_document(
    index: CorpusIndex,
    encoder: Encoder,
    text: str,
    exclude_refs: set[int] | frozenset[int],
    strip: bool = True,
    shingle: int = 4,
    num_perm: int = 128,
) -> DocumentScores:
    """Điểm tốt nhất của từng câu so với kho DOCUMENT (không phụ thuộc ngưỡng).

    strip=False chỉ dành cho ablation của plan 04-04. Một lần encode cho mọi
    câu; nguồn thuộc exclude_refs không bao giờ được so khớp. shingle/num_perm
    phải trùng với signer của CorpusIndex (main.py truyền cùng Settings).
    """
    if strip:
        stripped = strip_boilerplate(text)
        lines, removed = stripped.lines, stripped.removed
    else:
        lines, removed = [line for line in nfc(text).split("\n") if line], 0
    sents = sentences(lines)
    if not sents:
        return DocumentScores([], removed)

    vectors = encoder.encode(sents)
    signatures = [minhash.signature(s, shingle, num_perm) for s in sents]
    excluded = frozenset(int(r) for r in exclude_refs)
    excluded_arr = np.fromiter(excluded, dtype=np.int64, count=len(excluded))

    out: list[ChunkScore] = []
    with index.lock:
        part = index.partition(TAI_LIEU)
        n_excluded = sum(len(part.by_source.get((LOAI_DOCUMENT, r), [])) for r in excluded)
        k = min(index.size(TAI_LIEU), n_excluded + 10)
        scores, ids = index.search(TAI_LIEU, vectors, k)

        matrix, mh_ids = None, None
        if part.mh_matrix is not None and len(part.mh_ids) > 0:
            allowed = ~np.isin(part.mh_refs, excluded_arr)
            if allowed.any():
                matrix, mh_ids = part.mh_matrix[allowed], part.mh_ids[allowed]

        for pos, sent in enumerate(sents):
            sem_row, sem_score = None, 0.0
            for score, cid in zip(scores[pos], ids[pos]):
                if cid < 0:
                    continue
                row = part.rows.get(int(cid))
                if row is not None and row.ma_nguon not in excluded:
                    sem_row, sem_score = row, float(score)
                    break
            verb_row, verb_score = None, 0.0
            if matrix is not None:
                jac = minhash.jaccard_many(signatures[pos], matrix)
                best = int(np.argmax(jac))
                verb_row, verb_score = part.rows.get(int(mh_ids[best])), float(jac[best])
            out.append(
                ChunkScore(
                    vi_tri=pos + 1,
                    text=sent,
                    n_chars=len(sent),
                    sem_ref=sem_row.ma_nguon if sem_row else None,
                    sem_text=sem_row.noi_dung if sem_row else None,
                    sem_thu_tu=sem_row.thu_tu if sem_row else None,
                    sem_score=sem_score,
                    verb_ref=verb_row.ma_nguon if verb_row else None,
                    verb_text=verb_row.noi_dung if verb_row else None,
                    verb_thu_tu=verb_row.thu_tu if verb_row else None,
                    verb_score=verb_score,
                )
            )
    return DocumentScores(out, removed)


def _weighted(values: list[tuple[float, int]]) -> float:
    total = sum(w for _, w in values)
    if total == 0:
        return 0.0
    return round(100 * sum(v * w for v, w in values) / total, 2)


def check_document(
    scores: DocumentScores,
    nguong_doan: float,
    nguong_nguyen_van: float,
    top_k: int,
    chi_tiet_toi_da: int,
) -> dict:
    """Áp ngưỡng lên điểm từng câu → phản hồi /check-document.

    Câu bị gắn cờ NGUYEN_VAN khi Jaccard×100 ≥ nguong_nguyen_van (bằng chứng
    mạnh hơn nên thắng), ngược lại NGU_NGHIA khi cosine×100 ≥ nguong_doan.
    ty_le_tong = tỷ lệ ký tự bị gắn cờ; đoạn trùng = chuỗi câu liên tiếp gắn
    cờ cùng một nguồn (tối đa 6 câu).
    """
    chunks = scores.chunks
    total_chars = sum(c.n_chars for c in chunks)
    # (chunk, tín hiệu, ref, (thu_tu, câu nguồn), điểm kích hoạt)
    flags: list[tuple[ChunkScore, str, int, tuple[int, str], float] | None] = []
    for c in chunks:
        if c.verb_ref is not None and c.verb_score * 100 >= nguong_nguyen_van:
            flags.append((c, NGUYEN_VAN, c.verb_ref, (c.verb_thu_tu, c.verb_text), c.verb_score))
        elif c.sem_ref is not None and c.sem_score * 100 >= nguong_doan:
            flags.append((c, NGU_NGHIA, c.sem_ref, (c.sem_thu_tu, c.sem_text), c.sem_score))
        else:
            flags.append(None)

    flagged_chars = sum(f[0].n_chars for f in flags if f)
    per_ref: dict[int, int] = {}
    for f in flags:
        if f:
            per_ref[f[2]] = per_ref.get(f[2], 0) + f[0].n_chars
    do_an_trung = sorted(
        ({"ref_id": ref, "ty_le": round(100 * n / total_chars, 2)} for ref, n in per_ref.items()),
        key=lambda d: (-d["ty_le"], d["ref_id"]),
    )[:top_k]

    runs: list[list[tuple]] = []
    prev = None
    for f in flags:
        if f is None:
            prev = None
            continue
        if prev is not None and prev[2] == f[2] and len(runs[-1]) < MAX_PASSAGE_SENTENCES:
            runs[-1].append(f)
        else:
            runs.append([f])
        prev = f

    chi_tiet = []
    for run in runs:
        first, last = run[0][0].vi_tri, run[-1][0].vi_tri
        sources = sorted({src for _, _, _, src, _ in run}, key=lambda s: s[0])
        run_chars = sum(c.n_chars for c, *_ in run)
        verbatim_chars = sum(c.n_chars for c, sig, *_ in run if sig == NGUYEN_VAN)
        chi_tiet.append(
            {
                "ref_id": run[0][2],
                "doan_nguon": " ".join(c.text for c, *_ in run),
                "doan_trung": " ".join(text for _, text in sources),
                "vi_tri": f"Câu {first}" if first == last else f"Câu {first}–{last}",
                "ty_le": _weighted([(trig, c.n_chars) for c, _, _, _, trig in run]),
                "tin_hieu": NGUYEN_VAN if 2 * verbatim_chars >= run_chars else NGU_NGHIA,
                "diem_ngu_nghia": _weighted([(max(c.sem_score, 0.0), c.n_chars) for c, *_ in run]),
                "diem_nguyen_van": _weighted([(c.verb_score, c.n_chars) for c, *_ in run]),
                "_first": first,
            }
        )
    chi_tiet.sort(key=lambda d: (-d["ty_le"], d["_first"]))
    for d in chi_tiet:
        del d["_first"]

    return {
        "ty_le_tong": round(100 * flagged_chars / total_chars, 2) if total_chars else 0.0,
        "do_an_trung": do_an_trung,
        "chi_tiet": chi_tiet[:chi_tiet_toi_da],
        "so_doan": len(chunks),
        "so_doan_loai_tru": scores.removed,
    }


def count_missing(session: Session, encoder: Encoder) -> int:
    """Số chunk chưa có embedding cho mô hình hiện tại."""
    has = select(Embedding.chunk_id).where(Embedding.ten_model == encoder.name)
    return int(session.scalar(select(func.count(Chunk.id)).where(Chunk.id.not_in(has))) or 0)


def reembed_missing(session: Session, index: CorpusIndex, encoder: Encoder) -> RebuildStats:
    """/reindex không kèm items: encode (MỘT lần) các chunk thiếu embedding
    cho mô hình hiện tại, rồi dựng lại bộ nhớ từ thesis_ai."""
    with _WRITE_LOCK:
        has = select(Embedding.chunk_id).where(Embedding.ten_model == encoder.name)
        missing = session.execute(
            select(Chunk.id, Chunk.noi_dung).where(Chunk.id.not_in(has)).order_by(Chunk.id)
        ).all()
        if missing:
            vectors = encoder.encode([t for _, t in missing])
            try:
                session.add_all(
                    Embedding(
                        chunk_id=cid,
                        ten_model=encoder.name,
                        so_chieu=encoder.dim,
                        vector=v.astype("<f4").tobytes(),
                    )
                    for (cid, _), v in zip(missing, vectors)
                )
                session.flush()
                _upsert_index_metadata(session, encoder.name)
                session.commit()
            except Exception:
                session.rollback()
                raise
        return rebuild(session, index, encoder)
