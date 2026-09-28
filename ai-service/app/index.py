"""Chỉ mục FAISS trong bộ nhớ (§3.3.8, AISV-03).

Hai phân vùng:
- tieu_de  : TOPIC + ARCHIVE (một chunk = một tiêu đề), dùng cho /check-title;
- tai_lieu : DOCUMENT (các câu của tài liệu), dùng cho /check-document.
Mỗi phân vùng = IndexIDMap2(IndexFlatIP(dim)) — tìm kiếm CHÍNH XÁC, cosine vì
vector đã chuẩn hóa L2 — khóa theo chunk.id. Chỉ mục KHÔNG bao giờ lưu ra
file: luôn dựng lại từ thesis_ai lúc khởi động (index_metadata phát hiện lệch).
Phân vùng tai_lieu giữ thêm ma trận chữ ký MinHash thẳng hàng với chunk id
(thêm khi add, xóa khi remove_source, dựng lại cùng rebuild).
Một RLock bao mọi thao tác đọc/ghi.
"""
import threading
from collections.abc import Callable
from dataclasses import dataclass

import faiss
import numpy as np

from app.models import LOAI_ARCHIVE, LOAI_DOCUMENT, LOAI_TOPIC

TIEU_DE = "tieu_de"
TAI_LIEU = "tai_lieu"

_PARTITION_OF = {LOAI_TOPIC: TIEU_DE, LOAI_ARCHIVE: TIEU_DE, LOAI_DOCUMENT: TAI_LIEU}


def partition_of(loai: str) -> str:
    return _PARTITION_OF[loai]


@dataclass(frozen=True)
class ChunkRow:
    id: int
    loai: str
    ma_nguon: int
    thu_tu: int
    noi_dung: str


class _Partition:
    def __init__(self, dim: int) -> None:
        self.faiss = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        self.rows: dict[int, ChunkRow] = {}
        self.by_source: dict[tuple[str, int], list[int]] = {}
        # Chỉ phân vùng tai_lieu dùng: MinHash thẳng hàng với mh_ids/mh_refs.
        self.mh_ids = np.zeros((0,), dtype=np.int64)
        self.mh_refs = np.zeros((0,), dtype=np.int64)
        self.mh_matrix: np.ndarray | None = None


class CorpusIndex:
    def __init__(self, dim: int, signer: Callable[[str], np.ndarray] | None = None) -> None:
        self.dim = dim
        self.signer = signer
        self.lock = threading.RLock()
        self._parts = {TIEU_DE: _Partition(dim), TAI_LIEU: _Partition(dim)}

    def partition(self, name: str) -> _Partition:
        return self._parts[name]

    def add(self, partition: str, rows: list[ChunkRow], vectors: np.ndarray) -> None:
        if not rows:
            return
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        if vectors.shape != (len(rows), self.dim):
            raise ValueError("Số vector không khớp số chunk hoặc sai số chiều")
        ids = np.fromiter((r.id for r in rows), dtype=np.int64, count=len(rows))
        with self.lock:
            part = self._parts[partition]
            part.faiss.add_with_ids(vectors, ids)
            for row in rows:
                part.rows[row.id] = row
                part.by_source.setdefault((row.loai, row.ma_nguon), []).append(row.id)
            if partition == TAI_LIEU and self.signer is not None:
                sigs = np.vstack([self.signer(r.noi_dung) for r in rows])
                part.mh_matrix = sigs if part.mh_matrix is None else np.vstack([part.mh_matrix, sigs])
                part.mh_ids = np.concatenate([part.mh_ids, ids])
                part.mh_refs = np.concatenate(
                    [part.mh_refs, np.fromiter((r.ma_nguon for r in rows), dtype=np.int64, count=len(rows))]
                )

    def remove_source(self, loai: str, ma_nguon: int) -> int:
        with self.lock:
            part = self._parts[partition_of(loai)]
            ids = part.by_source.pop((loai, ma_nguon), [])
            if ids:
                part.faiss.remove_ids(np.asarray(ids, dtype=np.int64))
                for chunk_id in ids:
                    part.rows.pop(chunk_id, None)
                if part.mh_matrix is not None:
                    keep = ~np.isin(part.mh_ids, np.asarray(ids, dtype=np.int64))
                    part.mh_matrix = part.mh_matrix[keep]
                    part.mh_ids = part.mh_ids[keep]
                    part.mh_refs = part.mh_refs[keep]
            return len(ids)

    def search(
        self, partition: str, vectors: np.ndarray, k: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Trả (scores, chunk_ids) dạng (n, k'); id -1 = không có."""
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        with self.lock:
            part = self._parts[partition]
            k = min(k, part.faiss.ntotal)
            if k <= 0 or len(vectors) == 0:
                empty = np.zeros((len(vectors), 0))
                return empty.astype(np.float32), empty.astype(np.int64)
            return part.faiss.search(vectors, k)

    def row(self, partition: str, chunk_id: int) -> ChunkRow | None:
        with self.lock:
            return self._parts[partition].rows.get(chunk_id)

    def size(self, partition: str) -> int:
        with self.lock:
            return int(self._parts[partition].faiss.ntotal)

    def clear(self) -> None:
        with self.lock:
            self._parts = {TIEU_DE: _Partition(self.dim), TAI_LIEU: _Partition(self.dim)}
