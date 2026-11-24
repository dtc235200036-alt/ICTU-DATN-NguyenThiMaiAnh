"""Các kiểu biến đổi đoạn đạo văn (evaluation/obfuscate.py) trên văn bản bịa, seed cố định."""
import random
from collections import Counter

from app.nlp.chunking import sentences
from app.nlp.normalize import syllables
from evaluation import obfuscate as ob

DOAN = (
    "Hệ thống quản lý thư viện được xây dựng nhằm hỗ trợ người dùng tra cứu sách một cách nhanh chóng. "
    "Ứng dụng sử dụng cơ sở dữ liệu quan hệ để lưu trữ thông tin về sách, độc giả và các phiếu mượn trả, "
    "đồng thời cung cấp chức năng thống kê số lượt mượn theo từng tháng trong năm học. "
    "Giao diện được thiết kế đơn giản, thân thiện và dễ sử dụng trên cả máy tính lẫn điện thoại. "
    "Tuy nhiên, phiên bản hiện tại vẫn còn một số hạn chế về hiệu năng khi số người dùng tăng cao. "
    "Trong thời gian tới, nhóm sẽ tiếp tục nghiên cứu các giải pháp tối ưu để nâng cao chất lượng dịch vụ. "
    "Ngoài ra, hệ thống cũng cần bổ sung tính năng gửi thông báo cho độc giả khi sắp đến hạn trả sách."
)
SEEDS = range(20)


def _giu_lai(goc: str, moi: str) -> float:
    """Tỷ lệ âm tiết (đếm theo túi) của bản gốc còn trong bản mới."""
    a, b = Counter(syllables(goc)), Counter(syllables(moi))
    return sum((a & b).values()) / sum(a.values())


def test_nguyen_van_giu_nguyen():
    assert ob.nguyen_van(DOAN, random.Random(0)) == DOAN


def test_dao_cau_doi_thu_tu_giu_tap_cau():
    goc = sentences([DOAN])
    for seed in SEEDS:
        moi = sentences([ob.dao_cau(DOAN, random.Random(seed))])
        assert sorted(moi) == sorted(goc)
        assert moi != goc


def test_gop_cau_giam_va_tach_cau_tang_so_cau():
    n = len(sentences([DOAN]))
    for seed in SEEDS:
        assert len(sentences([ob.gop_cau(DOAN, random.Random(seed))])) < n
        assert len(sentences([ob.tach_cau(DOAN, random.Random(seed))])) > n


def test_sua_nhe_doi_vai_tu_giu_phan_lon():
    for seed in SEEDS:
        moi = ob.sua_nhe(DOAN, random.Random(seed))
        assert Counter(syllables(moi)) != Counter(syllables(DOAN))
        assert _giu_lai(DOAN, moi) >= 0.8


def test_xao_tron_giu_phan_lon_tui_tu():
    for seed in SEEDS:
        moi = ob.xao_tron(DOAN, random.Random(seed))
        assert moi != DOAN
        assert _giu_lai(DOAN, moi) >= 0.85
