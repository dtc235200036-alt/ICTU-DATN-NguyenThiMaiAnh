from datetime import date

import pytest

from app.core.roles import VaiTro
from app.models.de_tai import CHO_DUYET, DeTai, GIANG_VIEN
from app.models.dot_do_an import DANG_MO, DotDoAn

# T-02-34/UC1.3/AUTH-03/ROADMAP SC5: mọi endpoint trên /api/topic-approvals
# chỉ Bộ môn được gọi — SV, một GV không liên quan và CHÍNH GV đã đề xuất đề
# tài đó đều phải nhận 403, đề tài không đổi trạng thái/GVHD. Đây là ví dụ
# "SV không duyệt được đề tài" của SC5 — không thêm test nào khác.

_APPROVAL_ENDPOINTS = [
    ("GET", "/api/topic-approvals", None),
    ("POST", "/api/topic-approvals/{id}/approve", {"giang_vien_id": None}),
    ("POST", "/api/topic-approvals/{id}/reject", {"ly_do": "Không phù hợp"}),
]


def _make_pending_topic_with_sv(db, giang_vien_id: int, sinh_vien_id: int) -> DeTai:
    cohort = DotDoAn(
        ten_dot="Đợt RBAC duyệt đề tài",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.flush()

    topic = DeTai(
        dot_do_an_id=cohort.id,
        giang_vien_id=giang_vien_id,
        sinh_vien_id=sinh_vien_id,
        ten_de_tai="Đề tài kiểm thử RBAC duyệt",
        linh_vuc="Hệ thống thông tin",
        trang_thai=CHO_DUYET,
        loai_nguoi_de_xuat=GIANG_VIEN,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@pytest.mark.parametrize("caller_role", ["sv", "unrelated_gv", "proposing_gv"])
@pytest.mark.parametrize("method,path_template,body", _APPROVAL_ENDPOINTS)
def test_non_bomon_gets_403_on_every_approval_endpoint(
    client, make_account, auth_headers, db, caller_role, method, path_template, body
):
    proposing_gv = make_account(VaiTro.GIANG_VIEN)
    unrelated_gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)

    topic = _make_pending_topic_with_sv(db, proposing_gv.giang_vien_id, sv.sinh_vien_id)

    actor = {"sv": sv, "unrelated_gv": unrelated_gv, "proposing_gv": proposing_gv}[caller_role]
    path = path_template.format(id=topic.id)

    resp = client.request(method, path, json=body, headers=auth_headers(actor))

    assert resp.status_code == 403

    row = db.get(DeTai, topic.id)
    assert row is not None
    assert row.trang_thai == CHO_DUYET
    assert row.giang_vien_id == proposing_gv.giang_vien_id
    assert row.sinh_vien_id == sv.sinh_vien_id
    assert row.ly_do_tu_choi is None
