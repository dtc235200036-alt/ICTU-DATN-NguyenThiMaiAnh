"""Tín hiệu nguyên văn (D-03): MinHash trên k-gram âm tiết.

datasketch 2.x dùng lược đồ hoán vị mặc định "affine32" (giá trị băm khác
1.x — không quan trọng vì chữ ký KHÔNG bao giờ được lưu: dựng lại từ
chunk.noi_dung lúc khởi động). Chữ ký là dữ liệu từ vựng dẫn xuất, không phải
embedding (NFR-11 không bị ảnh hưởng).
"""
import numpy as np
from datasketch import MinHash

from app.nlp.normalize import syllables


def shingles(text: str, k: int) -> set[str]:
    toks = syllables(text)
    if not toks:
        return set()
    if len(toks) < k:
        return {" ".join(toks)}
    return {" ".join(toks[i : i + k]) for i in range(len(toks) - k + 1)}


def signature(text: str, k: int, num_perm: int) -> np.ndarray:
    m = MinHash(num_perm=num_perm)
    m.update_batch([s.encode("utf-8") for s in shingles(text, k)])
    return np.asarray(m.hashvalues).copy()


def jaccard_many(sig: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Ước lượng Jaccard của sig với từng hàng của matrix (tỷ lệ hoán vị trùng)."""
    if matrix.size == 0:
        return np.zeros((0,), dtype=np.float64)
    return (matrix == sig[None, :]).mean(axis=1)
