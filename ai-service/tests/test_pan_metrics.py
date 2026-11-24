"""Chỉ số PAN-PC trên các ví dụ tính tay."""
import math

import pytest

from evaluation.pan_metrics import case_recall, pan_scores

CA = ("S1", "R1", 0, 100, 50, 150)  # 100 ký tự nghi vấn + 100 ký tự nguồn


def test_phat_hien_hoan_hao():
    assert pan_scores([CA], [CA]) == {"precision": 1.0, "recall": 1.0, "granularity": 1.0, "plagdet": 1.0}


def test_hai_nua_cho_mot_ca():
    halves = [("S1", "R1", 0, 50, 50, 100), ("S1", "R1", 50, 100, 100, 150)]
    m = pan_scores([CA], halves)
    assert (m["precision"], m["recall"], m["granularity"]) == (1.0, 1.0, 2.0)
    assert m["plagdet"] == pytest.approx(1 / math.log2(3))


def test_phu_mot_nua_ca():
    assert case_recall([CA], [("S1", "R1", 0, 50, 50, 100)]) == [0.5]
    # Phát hiện rộng gấp đôi ca: recall 1, precision 200/400.
    m = pan_scores([CA], [("S1", "R1", 0, 200, 50, 250)])
    assert (m["precision"], m["recall"]) == (0.5, 1.0)


def test_sai_tai_lieu_nguon_khong_duoc_tinh():
    for det in [("S1", "R2", 0, 100, 50, 150), ("S1", "R1", 0, 100, 500, 600)]:
        m = pan_scores([CA], [det])
        assert (m["precision"], m["recall"], m["granularity"], m["plagdet"]) == (0.0, 0.0, 1.0, 0.0)


def test_khong_co_phat_hien():
    m = pan_scores([CA], [])
    assert (m["precision"], m["recall"], m["plagdet"]) == (0.0, 0.0, 0.0)
