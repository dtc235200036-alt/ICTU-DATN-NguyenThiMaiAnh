"""Chỉ số PAN-PC (Potthast và cs. 2010, "An Evaluation Framework for Plagiarism
Detection", COLING): precision/recall vĩ mô, granularity, plagdet.

Một ca (s) hoặc một phát hiện (r) = (susp_id, src_id, susp_start, susp_end,
src_start, src_end), khoảng ký tự nửa mở; phần tử thừa phía sau bị bỏ qua.
Tập ký tự = ký tự phía nghi vấn ∪ ký tự phía nguồn (hai không gian tách rời).
r phát hiện s khi cùng cặp tài liệu, chồng lấn ở phía nghi vấn VÀ ở phía
nguồn (như bộ đo tham chiếu của PAN); khi đó s ⊓ r = s ∩ r, ngược lại ∅.
"""
import math
from collections import defaultdict


def _size(x) -> int:
    return (x[3] - x[2]) + (x[5] - x[4])


def _detects(s, r) -> bool:
    return s[:2] == r[:2] and s[2] < r[3] and r[2] < s[3] and s[4] < r[5] and r[4] < s[5]


def _union_len(spans) -> int:
    total = end = 0
    for a, b in sorted(spans):
        a = max(a, end)
        if b > a:
            total += b - a
        end = max(end, b)
    return total


def _by_pair(xs) -> dict:
    out = defaultdict(list)
    for x in xs:
        out[x[:2]].append(x)
    return out


def _covered(x, others: dict) -> int:
    """|∪_y (x ⊓ y)| với y chạy trên others (đã nhóm theo cặp tài liệu)."""
    hits = [y for y in others.get(x[:2], []) if _detects(x, y)]
    return _union_len((max(x[2], y[2]), min(x[3], y[3])) for y in hits) + _union_len(
        (max(x[4], y[4]), min(x[5], y[5])) for y in hits
    )


def case_recall(cases, detections) -> list[float]:
    """Recall của từng ca: |∪_r (s ⊓ r)| / |s|."""
    dets = _by_pair(detections)
    return [_covered(s, dets) / _size(s) for s in cases]


def detection_precision(cases, detections) -> list[float]:
    """Precision của từng phát hiện: |∪_s (s ⊓ r)| / |r| (0 = không trùng ca nào)."""
    by_case = _by_pair(cases)
    return [_covered(r, by_case) / _size(r) for r in detections]


def granularity(cases, detections) -> float:
    """Số phát hiện trung bình trên mỗi ca được phát hiện; 1 khi không ca nào."""
    dets = _by_pair(detections)
    counts = [n for s in cases if (n := sum(_detects(s, r) for r in dets.get(s[:2], [])))]
    return sum(counts) / len(counts) if counts else 1.0


def pan_scores(cases, detections) -> dict:
    """precision, recall (vĩ mô), granularity, plagdet = F1 / log2(1 + gran)."""
    rc = case_recall(cases, detections)
    pr = detection_precision(cases, detections)
    p = sum(pr) / len(pr) if pr else 0.0
    r = sum(rc) / len(rc) if rc else 0.0
    g = granularity(cases, detections)
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "granularity": g, "plagdet": f1 / math.log2(1 + g)}
