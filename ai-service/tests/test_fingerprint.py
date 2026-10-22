"""Tín hiệu nguyên văn bằng vân tay (fingerprint.py, VanTayIndex): bảo đảm
của winnowing, độ phủ, chép một phần câu, cụm phổ biến đếm theo nhóm đề tài,
đổi nhóm không mã hóa lại, khởi động lại giữ nhóm."""
import random

import numpy as np

from app.fingerprint import coverage, sentence_kgrams, winnow
from app.index import ChunkRow, VanTayIndex
from conftest import HEADERS, make_client

K, W = 4, 4
T = K + W - 1

SRC = (
    "Hệ thống sử dụng mô hình ngôn ngữ đã huấn luyện trước để biểu diễn mỗi câu"
    " thành một vector có số chiều cố định phục vụ việc so khớp ngữ nghĩa."
)
OTHER = [
    "Mô hình học sâu được huấn luyện trên tập ảnh biển số thu thập tại bãi gửi xe của trường.",
    "Ứng dụng di động gửi thông báo nhắc lịch khám cho bệnh nhân trước một ngày.",
    "Dữ liệu cảm biến nhiệt độ được truyền về máy chủ qua giao thức MQTT mỗi năm giây.",
]
TEMPLATE = "Trong chương này em trình bày tổng quan về các công nghệ được sử dụng để xây dựng hệ thống."


def _words(n: int, rng: random.Random) -> list[str]:
    return [f"t{rng.randrange(10**6)}" for _ in range(n)]


def test_winnowing_guarantee_shared_run_of_t_syllables():
    """Hai câu chung một đoạn ≥ t = w + k − 1 âm tiết luôn chung ≥ 1 vân tay."""
    rng = random.Random(7)
    for _ in range(300):
        shared = _words(T, rng)
        a = _words(rng.randrange(0, 15), rng) + shared + _words(rng.randrange(0, 15), rng)
        b = _words(rng.randrange(0, 15), rng) + shared + _words(rng.randrange(0, 15), rng)
        fa = winnow(sentence_kgrams(" ".join(a), K)[0], W)
        hb, _ = sentence_kgrams(" ".join(b), K)
        assert np.isin(fa, hb).any()


def _score(query: str, source: str, min_run: int = T) -> float:
    q, n = sentence_kgrams(query, K)
    s, _ = sentence_kgrams(source, K)
    return coverage(np.isin(q, s), K, n, min_run)


def test_coverage_exact_edit_partial_short():
    assert _score(SRC, SRC) == 1.0
    words = SRC.split(" ")
    edited = " ".join(words[:10] + ["một"] + words[11:])  # đổi một từ
    assert _score(edited, SRC) >= 0.9
    half = " ".join(words[: len(words) // 2] + ["em", "tự", "viết", "thêm", "phần", "còn", "lại", "của", "câu", "này"])
    assert 0.4 <= _score(half, SRC) <= 0.7
    # Đoạn chung ngắn hơn t âm tiết không được tính.
    assert _score("mô hình ngôn ngữ đã huấn cho bài toán khác hẳn với đề tài", SRC) == 0.0  # chung 6 âm tiết
    # Câu ngắn hơn t chép trọn vẫn được tính (ngưỡng đoạn = số âm tiết của câu).
    assert _score("biểu diễn mỗi câu thành một", SRC) == 1.0


def test_index_match_excludes_refs_and_common_kgrams():
    idx = VanTayIndex(K, W)
    rows = [ChunkRow(1, "DOCUMENT", 10, 1, SRC, 100)]
    rows += [ChunkRow(10 + i, "DOCUMENT", 20 + i, 1, TEMPLATE, 200 + i) for i in range(4)]
    idx.add(rows)
    snap = idx.snapshot()
    queries = [sentence_kgrams(SRC, K), sentence_kgrams(TEMPLATE, K)]
    best = snap.match(queries, frozenset(), pho_bien=4)
    assert best[0] == (1, 1.0)
    assert best[1] == (None, 0.0)  # câu khuôn có trong 4 nhóm → cụm phổ biến
    # Loại trừ nguồn 10 → không khớp; loại trừ nhóm của một bản khuôn → còn 3 nhóm.
    best = snap.match(queries, frozenset({10, 20}), pho_bien=4)
    assert best[0] == (None, 0.0)
    assert best[1][0] in {11, 12, 13} and best[1][1] == 1.0
    # Không lọc cụm phổ biến (pho_bien = 0).
    assert snap.match(queries, frozenset(), pho_bien=0)[1][1] == 1.0


def test_same_group_counts_once():
    idx = VanTayIndex(K, W)
    idx.add([ChunkRow(10 + i, "DOCUMENT", 20 + i, 1, TEMPLATE, 7) for i in range(4)])
    query = [sentence_kgrams(TEMPLATE, K)]
    assert idx.snapshot().match(query, frozenset(), pho_bien=4)[0][1] == 1.0
    for i in range(4):
        idx.set_group(20 + i, 300 + i)
    assert idx.snapshot().match(query, frozenset(), pho_bien=4)[0] == (None, 0.0)


def _doc(*sentences: str) -> str:
    return "\n".join(["MỞ ĐẦU", *sentences])


def _check(client, text, **kw):
    body = {"ref_id": 0, "text": text, "nguong_doan": 99.0, "nguong_nguyen_van": 60.0}
    body.update(kw)
    r = client.post("/check-document", json=body, headers=HEADERS)
    assert r.status_code == 200, r.text
    return r.json()


def _ingest(client, ref_id: int, text: str, nhom: int | None = None):
    body = {"id": ref_id, "type": "DOCUMENT", "text": text}
    if nhom is not None:
        body["nhom"] = nhom
    r = client.post("/ingest", json=body, headers=HEADERS)
    assert r.status_code == 200, r.text


def test_partial_and_edited_copies_are_flagged(client):
    _ingest(client, 1, _doc(SRC, *OTHER), nhom=1)
    words = SRC.split(" ")
    # Sửa một từ giữa câu: hai đoạn chung còn lại đều ≥ t âm tiết với mọi k ≤ 6.
    edited = " ".join(words[:15] + ["từng"] + words[16:])
    half = " ".join(words[:18] + ["và", "kết", "quả", "được", "trình", "bày", "ở", "chương", "bốn", "của", "báo", "cáo", "này."])
    own = "Phần đánh giá dùng bộ dữ liệu do nhóm tự thu thập trong học kỳ vừa qua tại khoa."
    res = _check(client, _doc(edited, own))
    assert [d["tin_hieu"] for d in res["chi_tiet"]] == ["NGUYEN_VAN"]
    assert res["chi_tiet"][0]["doan_nguon"] == edited
    assert res["chi_tiet"][0]["diem_nguyen_van"] >= 90
    # Chép nửa câu: độ phủ ≈ 50 % — dưới ngưỡng 60, trên ngưỡng 40.
    assert _check(client, _doc(half, own))["chi_tiet"] == []
    flagged = _check(client, _doc(half, own), nguong_nguyen_van=40.0)["chi_tiet"]
    assert [d["doan_nguon"] for d in flagged] == [half]


def test_common_template_sentence_and_group_update(client, db_path):
    for i in range(4):
        _ingest(client, 10 + i, _doc(TEMPLATE, OTHER[i % 3]), nhom=50)
    query = _doc(TEMPLATE, "Phần đánh giá dùng bộ dữ liệu do nhóm tự thu thập trong học kỳ vừa qua.")
    # Cùng một đề tài (4 phiên bản) → chỉ 1 nhóm → câu khuôn vẫn là bằng chứng.
    assert len(_check(client, query)["chi_tiet"]) == 1

    # Đổi nhóm (văn bản giữ nguyên): không mã hóa lại, câu khuôn thành cụm phổ biến.
    before = client.get("/health").json()["encode_calls"]
    for i in range(4):
        _ingest(client, 10 + i, _doc(TEMPLATE, OTHER[i % 3]), nhom=60 + i)
    assert client.get("/health").json()["encode_calls"] == before
    assert _check(client, query)["chi_tiet"] == []
    # Tài liệu đang kiểm tra thuộc đề tài 60 (loai_tru bản cũ 10): còn 3 nhóm khác.
    assert len(_check(client, query, loai_tru=[10])["chi_tiet"]) == 1

    # Khởi động lại: nhóm được dựng lại từ thesis_ai.
    with make_client(db_path) as restarted:
        assert _check(restarted, query)["chi_tiet"] == []
        assert len(_check(restarted, query, loai_tru=[10])["chi_tiet"]) == 1


def test_ingest_rejects_bad_group(client):
    r = client.post("/ingest", json={"id": 1, "type": "DOCUMENT", "text": "x", "nhom": 0}, headers=HEADERS)
    assert r.status_code == 422
