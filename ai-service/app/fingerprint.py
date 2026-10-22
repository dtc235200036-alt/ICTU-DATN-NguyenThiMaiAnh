"""Tín hiệu nguyên văn (D-03): vân tay k-gram âm tiết + winnowing.

Thay cho MinHash so vét cạn (mỗi câu so với MỌI câu của kho, thời gian tăng
tuyến tính theo kho). Theo Sorokina và cs. (2006, "Plagiarism Detection in
arXiv") và Schleimer và cs. (2003, "Winnowing"):

- k-gram âm tiết của một câu được băm 64 bit (đa thức kiểu Rabin trên băm từng
  âm tiết, rồi trộn bit). Băm ổn định giữa các lần khởi động (blake2b), nhưng
  vẫn KHÔNG lưu xuống CSDL: dựng lại từ chunk.noi_dung khi rebuild.
- Kho chỉ giữ vân tay đã winnowing: trong mỗi cửa sổ w k-gram liên tiếp giữ
  giá trị nhỏ nhất. Bảo đảm: hai câu có chung một đoạn ≥ t = w + k − 1 âm tiết
  liên tiếp thì chung ít nhất một vân tay → luôn được tìm thấy qua tra bảng
  (không quét cả kho).
- Cụm phổ biến (L-common): k-gram xuất hiện ở ≥ L nhóm tài liệu khác nhau
  (nhóm = đề tài, các phiên bản của cùng một đề tài là một nhóm — tương ứng
  "tác giả không trùng nhau" của Sorokina) là cụm khuôn mẫu, không tính là
  bằng chứng sao chép.
- Điểm nguyên văn của một câu = độ phủ: tỷ lệ âm tiết của câu nằm trong các
  đoạn chung (liên tiếp, ≥ min(t, số âm tiết của câu)) với MỘT câu của kho,
  chỉ tính k-gram không phổ biến. Chép cả câu → 1,0; sửa một từ trong câu 30
  âm tiết vẫn ≈ 0,97 (Jaccard MinHash rơi xuống ≈ 0,74); chép nửa câu → ≈ 0,5.
"""
import hashlib
from functools import lru_cache

import numpy as np

from app.nlp.normalize import syllables

_P = np.uint64(0x9E3779B97F4A7C15)  # hệ số đa thức (lẻ, 64 bit)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
_EMPTY = np.zeros((0,), dtype=np.uint64)


@lru_cache(maxsize=1 << 20)
def _syllable_hash(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "little")


def _mix(x: np.ndarray) -> np.ndarray:
    """Bộ trộn splitmix64 (vector hóa; phép nhân uint64 tự quay vòng mod 2^64)."""
    x = x ^ (x >> np.uint64(30))
    x = x * _M1
    x = x ^ (x >> np.uint64(27))
    x = x * _M2
    return x ^ (x >> np.uint64(31))


def sentence_kgrams(text: str, k: int) -> tuple[np.ndarray, int]:
    """(băm các k-gram âm tiết theo thứ tự, số âm tiết) của câu: n − k + 1 giá
    trị; câu ngắn hơn k âm tiết → một giá trị băm của cả câu; câu rỗng → rỗng."""
    toks = syllables(text)
    if not toks:
        return _EMPTY, 0
    s = np.fromiter((_syllable_hash(t) for t in toks), dtype=np.uint64, count=len(toks))
    width = min(k, len(s))
    m = len(s) - width + 1
    acc = np.zeros(m, dtype=np.uint64)
    for j in range(width):
        acc = acc * _P + s[j : j + m]
    return _mix(acc + np.uint64(width)), len(toks)


def winnow(hashes: np.ndarray, w: int) -> np.ndarray:
    """Vân tay đã winnowing (giá trị phân biệt, đã sắp xếp): giá trị nhỏ nhất
    của mỗi cửa sổ w băm liên tiếp, lấy vị trí phải nhất khi bằng nhau. Ít hơn
    w băm → một vân tay (nhỏ nhất); w ≤ 1 → giữ mọi băm."""
    n = len(hashes)
    if n == 0:
        return _EMPTY
    if w <= 1:
        return np.unique(hashes)
    if n <= w:
        return np.unique(hashes[[n - 1 - int(np.argmin(hashes[::-1]))]])
    windows = np.lib.stride_tricks.sliding_window_view(hashes, w)
    pos = np.arange(n - w + 1) + (w - 1 - np.argmin(windows[:, ::-1], axis=1))
    return np.unique(hashes[pos])


def coverage(matched: np.ndarray, k: int, n_syllables: int, min_run: int) -> float:
    """Tỷ lệ âm tiết của câu nằm trong các đoạn chung đủ dài.

    matched[i] = k-gram thứ i của câu có trong câu so sánh (và không phổ biến).
    Một đoạn chung = dải âm tiết liên tiếp được phủ bởi các k-gram khớp; chỉ
    đoạn dài ≥ min(min_run, n_syllables) được tính."""
    if n_syllables <= 0 or not matched.any():
        return 0.0
    width = min(k, n_syllables)
    starts = np.flatnonzero(matched)
    delta = np.zeros(n_syllables + 1, dtype=np.int32)
    np.add.at(delta, starts, 1)
    np.add.at(delta, starts + width, -1)
    covered = np.cumsum(delta[:-1]) > 0
    # Độ dài các dải True liên tiếp.
    edges = np.diff(np.concatenate(([0], covered.astype(np.int8), [0])))
    run_starts = np.flatnonzero(edges == 1)
    run_ends = np.flatnonzero(edges == -1)
    lengths = run_ends - run_starts
    need = min(min_run, n_syllables)
    return float(lengths[lengths >= need].sum()) / n_syllables
