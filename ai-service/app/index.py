"""Chỉ mục FAISS trong bộ nhớ (§3.3.8, AISV-03).

Hai phân vùng:
- tieu_de  : TOPIC + ARCHIVE (một chunk = một tiêu đề), dùng cho /check-title;
- tai_lieu : DOCUMENT (các câu của tài liệu), dùng cho /check-document.
Mỗi phân vùng = IndexIDMap2(IndexFlatIP(dim)) — tìm kiếm CHÍNH XÁC, cosine vì
vector đã chuẩn hóa L2 — khóa theo chunk.id. Chỉ mục KHÔNG bao giờ lưu ra
file: luôn dựng lại từ thesis_ai lúc khởi động (index_metadata phát hiện lệch).
Phân vùng tai_lieu giữ thêm chỉ mục vân tay (VanTayIndex: k-gram âm tiết đã
winnowing + tần suất theo nhóm đề tài) — thêm khi add, xóa khi remove_source,
dựng lại cùng rebuild.
Một RLock bao mọi thao tác đọc/ghi.
"""
import threading
from dataclasses import dataclass

import faiss
import numpy as np

from app.fingerprint import coverage, sentence_kgrams, winnow
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
    # Nhóm của nguồn DOCUMENT (de_tai.id do Web API gửi): mọi phiên bản đề
    # cương/báo cáo của một đề tài là MỘT nhóm khi đếm cụm phổ biến.
    nhom: int | None = None


def group_key(ma_nguon: int, nhom: int | None) -> int:
    """Khóa nhóm: nhom (≥ 1) khi Web API gửi, nếu không thì mỗi nguồn một nhóm
    riêng (−ma_nguon, không đụng khóa của nhom)."""
    return int(nhom) if nhom else -int(ma_nguon)


_EMPTY_U64 = np.zeros((0,), dtype=np.uint64)
_EMPTY_I64 = np.zeros((0,), dtype=np.int64)


@dataclass(frozen=True)
class VanTaySnapshot:
    """Ảnh chụp bất biến của VanTayIndex: các mảng không bao giờ bị sửa tại chỗ
    (biên dịch lại luôn tạo mảng mới) nên dùng được ngoài index.lock."""

    k: int
    w: int
    keys: np.ndarray  # vân tay đã winnowing, đã sắp xếp
    chunks: np.ndarray  # chunk id thẳng hàng với keys
    refs: np.ndarray  # ma_nguon thẳng hàng với keys
    kgrams: dict[int, np.ndarray]  # chunk id -> k-gram phân biệt, đã sắp xếp
    group_of: dict[int, int]  # ma_nguon -> khóa nhóm
    group_kgrams: dict[int, np.ndarray]  # khóa nhóm -> k-gram phân biệt của nhóm
    df_keys: np.ndarray  # k-gram phân biệt của kho
    df_counts: np.ndarray  # số nhóm chứa từng df_keys

    @property
    def min_run(self) -> int:
        """t = w + k − 1: đoạn chung từ t âm tiết luôn được tìm thấy (winnowing)."""
        return self.w + self.k - 1

    def common_mask(self, hashes: np.ndarray, excluded_refs: frozenset[int], pho_bien: int) -> np.ndarray:
        """k-gram phổ biến: có trong ≥ pho_bien nhóm, KHÔNG tính nhóm của các
        nguồn bị loại trừ (phiên bản khác của chính đề tài đang kiểm tra)."""
        if pho_bien <= 0 or len(hashes) == 0 or len(self.df_keys) == 0:
            return np.zeros(len(hashes), dtype=bool)
        uniq, inverse = np.unique(hashes, return_inverse=True)
        pos = np.searchsorted(self.df_keys, uniq)
        pos_ok = np.minimum(pos, len(self.df_keys) - 1)
        found = (pos < len(self.df_keys)) & (self.df_keys[pos_ok] == uniq)
        df = np.where(found, self.df_counts[pos_ok], 0).astype(np.int64)
        for g in {self.group_of[r] for r in excluded_refs if r in self.group_of}:
            df -= np.isin(uniq, self.group_kgrams.get(g, _EMPTY_U64), assume_unique=True)
        return (df >= pho_bien)[inverse]

    def match(
        self,
        queries: list[tuple[np.ndarray, int]],
        excluded_refs: frozenset[int],
        pho_bien: int,
        max_candidates: int = 20,
        max_postings: int = 5000,
    ) -> list[tuple[int | None, float]]:
        """Câu kho khớp nguyên văn tốt nhất cho từng câu truy vấn.

        queries[i] = (k-gram theo thứ tự, số âm tiết) của câu i. Bước 1 (tìm
        ứng viên): tra mọi k-gram không phổ biến của truy vấn trong bảng vân
        tay — không quét cả kho. Bước 2 (so chi tiết): với tối đa
        max_candidates câu chung nhiều vân tay nhất, tính độ phủ (coverage);
        trả (chunk id, độ phủ) tốt nhất hoặc (None, 0.0)."""
        best: list[tuple[int | None, float]] = [(None, 0.0)] * len(queries)
        if not queries or len(self.keys) == 0:
            return best
        lens = np.fromiter((len(h) for h, _ in queries), dtype=np.int64, count=len(queries))
        if lens.sum() == 0:
            return best
        all_q = np.concatenate([h for h, _ in queries])
        sent = np.repeat(np.arange(len(queries)), lens)
        q_start = np.concatenate(([0], np.cumsum(lens)[:-1]))
        common = self.common_mask(all_q, excluded_refs, pho_bien)

        occ = np.flatnonzero(~common)
        lo = np.searchsorted(self.keys, all_q[occ], side="left")
        hi = np.searchsorted(self.keys, all_q[occ], side="right")
        cnt = hi - lo
        # Vân tay lặp ở quá nhiều câu của kho (vd. một cụm lặp trong cùng đề
        # tài) không phân biệt được ứng viên: bỏ qua.
        cnt[cnt > max_postings] = 0
        keep = cnt > 0
        occ, lo, cnt = occ[keep], lo[keep], cnt[keep]
        if len(occ) == 0:
            return best
        offsets = np.cumsum(cnt) - cnt
        idx = np.arange(int(cnt.sum())) + np.repeat(lo - offsets, cnt)
        p_sent = np.repeat(sent[occ], cnt)
        p_chunk = self.chunks[idx]
        if excluded_refs:
            allowed = ~np.isin(self.refs[idx], np.fromiter(excluded_refs, dtype=np.int64))
            p_sent, p_chunk = p_sent[allowed], p_chunk[allowed]
        if len(p_sent) == 0:
            return best
        pairs, shared = np.unique(np.stack([p_sent, p_chunk], axis=1), axis=0, return_counts=True)
        # Theo câu truy vấn, ứng viên chung nhiều vân tay trước, rồi id nhỏ trước.
        order = np.lexsort((pairs[:, 1], -shared, pairs[:, 0]))
        pairs, shared = pairs[order], shared[order]
        bounds = np.flatnonzero(np.diff(pairs[:, 0])) + 1
        for group in np.split(np.arange(len(pairs)), bounds):
            s = int(pairs[group[0], 0])
            hashes, n_syll = queries[s]
            q_common = common[q_start[s] : q_start[s] + len(hashes)]
            top_id, top_score = None, 0.0
            for g in group[:max_candidates]:
                cand = self.kgrams.get(int(pairs[g, 1]))
                if cand is None:  # nguồn vừa bị thay sau khi chụp ảnh
                    continue
                matched = np.isin(hashes, cand) & ~q_common
                score = coverage(matched, self.k, n_syll, self.min_run)
                if score > top_score:
                    top_id, top_score = int(pairs[g, 1]), score
            best[s] = (top_id, top_score)
        return best


class VanTayIndex:
    """Vân tay của phân vùng tai_lieu. Ghi (add/remove/set_group) chỉ cập nhật
    các từ điển theo chunk và đánh dấu bẩn; snapshot() biên dịch lại bảng tra
    và tần suất theo nhóm khi cần (sau mỗi lần ingest, một lần)."""

    def __init__(self, k: int, w: int) -> None:
        self.k = k
        self.w = w
        self._kgrams: dict[int, np.ndarray] = {}
        self._fps: dict[int, np.ndarray] = {}
        self._ref: dict[int, int] = {}
        self._group: dict[int, int] = {}
        self._snapshot: VanTaySnapshot | None = None

    def add(self, rows: list[ChunkRow]) -> None:
        for row in rows:
            hashes, _ = sentence_kgrams(row.noi_dung, self.k)
            self._kgrams[row.id] = np.unique(hashes)
            self._fps[row.id] = winnow(hashes, self.w)
            self._ref[row.id] = row.ma_nguon
            self._group[row.ma_nguon] = group_key(row.ma_nguon, row.nhom)
        self._snapshot = None

    def remove(self, ma_nguon: int, chunk_ids: list[int]) -> None:
        for chunk_id in chunk_ids:
            self._kgrams.pop(chunk_id, None)
            self._fps.pop(chunk_id, None)
            self._ref.pop(chunk_id, None)
        self._group.pop(ma_nguon, None)
        self._snapshot = None

    def set_group(self, ma_nguon: int, nhom: int | None) -> None:
        key = group_key(ma_nguon, nhom)
        if self._group.get(ma_nguon) != key:
            self._group[ma_nguon] = key
            self._snapshot = None

    def snapshot(self) -> VanTaySnapshot:
        if self._snapshot is None:
            self._snapshot = self._compile()
        return self._snapshot

    def _compile(self) -> VanTaySnapshot:
        ids = np.fromiter(self._fps.keys(), dtype=np.int64, count=len(self._fps))
        if len(ids) == 0:
            return VanTaySnapshot(
                self.k, self.w, _EMPTY_U64, _EMPTY_I64, _EMPTY_I64, {}, {}, {}, _EMPTY_U64, _EMPTY_I64
            )
        fps = list(self._fps.values())
        lens = np.fromiter((len(f) for f in fps), dtype=np.int64, count=len(fps))
        refs_of_ids = np.fromiter((self._ref[int(c)] for c in ids), dtype=np.int64, count=len(ids))
        keys = np.concatenate(fps)
        chunks = np.repeat(ids, lens)
        refs = np.repeat(refs_of_ids, lens)
        order = np.argsort(keys, kind="stable")

        by_group: dict[int, list[np.ndarray]] = {}
        for chunk_id, ref in zip(ids.tolist(), refs_of_ids.tolist()):
            by_group.setdefault(self._group[ref], []).append(self._kgrams[chunk_id])
        group_kgrams = {g: np.unique(np.concatenate(parts)) for g, parts in by_group.items()}
        df_keys, df_counts = np.unique(np.concatenate(list(group_kgrams.values())), return_counts=True)
        return VanTaySnapshot(
            k=self.k,
            w=self.w,
            keys=keys[order],
            chunks=chunks[order],
            refs=refs[order],
            kgrams=dict(self._kgrams),
            group_of=dict(self._group),
            group_kgrams=group_kgrams,
            df_keys=df_keys,
            df_counts=df_counts,
        )


class _Partition:
    def __init__(self, dim: int, van_tay: tuple[int, int] | None = None) -> None:
        self.faiss = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        self.rows: dict[int, ChunkRow] = {}
        self.by_source: dict[tuple[str, int], list[int]] = {}
        # Chỉ phân vùng tai_lieu dùng (tín hiệu nguyên văn).
        self.van_tay = VanTayIndex(*van_tay) if van_tay else None


class CorpusIndex:
    def __init__(self, dim: int, van_tay: tuple[int, int] | None = None) -> None:
        """van_tay = (k, w) của vân tay k-gram âm tiết cho phân vùng tai_lieu;
        None → không có tín hiệu nguyên văn."""
        self.dim = dim
        self.van_tay = van_tay
        self.lock = threading.RLock()
        self._parts = self._new_parts()

    def _new_parts(self) -> dict[str, _Partition]:
        return {TIEU_DE: _Partition(self.dim), TAI_LIEU: _Partition(self.dim, self.van_tay)}

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
            if part.van_tay is not None:
                part.van_tay.add(rows)

    def remove_source(self, loai: str, ma_nguon: int) -> int:
        with self.lock:
            part = self._parts[partition_of(loai)]
            ids = part.by_source.pop((loai, ma_nguon), [])
            if ids:
                part.faiss.remove_ids(np.asarray(ids, dtype=np.int64))
                for chunk_id in ids:
                    part.rows.pop(chunk_id, None)
                if part.van_tay is not None:
                    part.van_tay.remove(ma_nguon, ids)
            return len(ids)

    def set_group(self, ma_nguon: int, nhom: int | None) -> None:
        """Đổi nhóm của một nguồn DOCUMENT mà không nạp lại (văn bản không đổi)."""
        with self.lock:
            part = self._parts[TAI_LIEU]
            ids = part.by_source.get((LOAI_DOCUMENT, ma_nguon), [])
            for chunk_id in ids:
                row = part.rows[chunk_id]
                part.rows[chunk_id] = ChunkRow(row.id, row.loai, row.ma_nguon, row.thu_tu, row.noi_dung, nhom)
            if ids and part.van_tay is not None:
                part.van_tay.set_group(ma_nguon, nhom)

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
            self._parts = self._new_parts()
