from datetime import date

import pytest

from app.core.roles import VaiTro
from app.models.de_tai import CHO_DUYET, DA_PHAN_CONG, DeTai, SINH_VIEN
from app.models.dot_do_an import DANG_MO, DotDoAn

# T-02-34/UC1.3/AUTH-03 (đổi ở 0015): đề tài SV đề xuất chỉ GVHD của SV duyệt
# hoặc từ chối — SV, Bộ môn và một GV không phải GVHD đều nhận 403, đề tài
# không đổi trạng thái; GVHD duyệt thì đề tài sang Đã phân công.

_APPROVAL_ENDPOINTS = [
    ("POST", "/api/topic-approvals/{id}/approve", None),
    ("POST", "/api/topic-approvals/{id}/reject", {"ly_do": "Không phù hợp"}),
]


def _make_pending_sv_topic(db, giang_vien_id: int, sinh_vien_id: int) -> DeTai:
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
        loai_nguoi_de_xuat=SINH_VIEN,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@pytest.mark.parametrize("caller_role", ["sv", "bomon", "other_gv"])
@pytest.mark.parametrize("method,path_template,body", _APPROVAL_ENDPOINTS)
def test_only_gvhd_can_decide(
    client, make_account, auth_headers, db, caller_role, method, path_template, body
):
    gvhd = make_account(VaiTro.GIANG_VIEN)
    other_gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    bomon = make_account(VaiTro.BO_MON)

    topic = _make_pending_sv_topic(db, gvhd.giang_vien_id, sv.sinh_vien_id)

    actor = {"sv": sv, "bomon": bomon, "other_gv": other_gv}[caller_role]
    resp = client.request(
        method, path_template.format(id=topic.id), json=body, headers=auth_headers(actor)
    )
    assert resp.status_code == 403

    db.rollback()
    row = db.get(DeTai, topic.id)
    assert row.trang_thai == CHO_DUYET
    assert row.giang_vien_id == gvhd.giang_vien_id
    assert row.ly_do_tu_choi is None


def test_gvhd_sees_only_own_pending_and_approves(client, make_account, auth_headers, db):
    gvhd = make_account(VaiTro.GIANG_VIEN)
    other_gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    topic = _make_pending_sv_topic(db, gvhd.giang_vien_id, sv.sinh_vien_id)

    mine = client.get("/api/topic-approvals", headers=auth_headers(gvhd)).json()
    assert [t["id"] for t in mine["items"]] == [topic.id]
    theirs = client.get("/api/topic-approvals", headers=auth_headers(other_gv)).json()
    assert theirs["items"] == []

    resp = client.post(f"/api/topic-approvals/{topic.id}/approve", headers=auth_headers(gvhd))
    assert resp.status_code == 200
    assert resp.json()["trang_thai"] == DA_PHAN_CONG
    assert resp.json()["giang_vien_huong_dan"]["id"] == gvhd.giang_vien_id

    again = client.post(f"/api/topic-approvals/{topic.id}/approve", headers=auth_headers(gvhd))
    assert again.status_code == 409
