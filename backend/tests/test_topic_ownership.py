from datetime import date

import pytest

from app.core.roles import VaiTro
from app.models.dot_do_an import DANG_MO, DotDoAn

# T-02-22/T-02-23 (D-08): chỉ chủ sở hữu đề tài (người đứng tên đề xuất) mới
# được sửa/gửi đề xuất; chi tiết đề tài chỉ chủ sở hữu, Bộ môn, hoặc (khi đã
# duyệt và còn trống) bất kỳ ai mới được xem.


def _make_open_cohort(db) -> DotDoAn:
    cohort = DotDoAn(
        ten_dot="Đợt đồ án test UC1.1",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


def test_gv_draft_ownership_enforced(client, make_account, auth_headers, db):
    cohort = _make_open_cohort(db)
    gv_a = make_account(VaiTro.GIANG_VIEN)
    gv_b = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    bomon = make_account(VaiTro.BO_MON)

    create_resp = client.post(
        "/api/topics",
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Hệ thống quản lý đồ án tốt nghiệp",
            "linh_vuc": "Hệ thống thông tin",
            "gui": False,
        },
        headers=auth_headers(gv_a),
    )
    assert create_resp.status_code == 201
    topic = create_resp.json()
    assert topic["trang_thai"] == "NHAP"
    topic_id = topic["id"]

    update_payload = {
        "dot_do_an_id": cohort.id,
        "ten_de_tai": "Tên đề tài đổi trái phép",
        "linh_vuc": "Hệ thống thông tin",
    }

    for actor in (gv_b, sv, bomon):
        resp = client.put(
            f"/api/topics/{topic_id}", json=update_payload, headers=auth_headers(actor)
        )
        assert resp.status_code == 403

    submit_by_other_resp = client.post(
        f"/api/topics/{topic_id}/submit", headers=auth_headers(gv_b)
    )
    assert submit_by_other_resp.status_code == 403

    submit_resp = client.post(f"/api/topics/{topic_id}/submit", headers=auth_headers(gv_a))
    assert submit_resp.status_code == 200
    assert submit_resp.json()["trang_thai"] == "CHO_DUYET"


def test_sv_proposal_visibility_enforced(client, make_account, auth_headers, db):
    cohort = _make_open_cohort(db)
    sv_a = make_account(VaiTro.SINH_VIEN)
    sv_b = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    bomon = make_account(VaiTro.BO_MON)

    create_resp = client.post(
        "/api/topics",
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Ứng dụng học tiếng Anh cho trẻ em",
            "linh_vuc": "Công nghệ phần mềm",
            "gui": True,
        },
        headers=auth_headers(sv_a),
    )
    assert create_resp.status_code == 201
    topic_id = create_resp.json()["id"]
    assert create_resp.json()["trang_thai"] == "CHO_DUYET"

    for actor in (sv_b, gv):
        resp = client.get(f"/api/topics/{topic_id}", headers=auth_headers(actor))
        assert resp.status_code == 403

    resp_owner = client.get(f"/api/topics/{topic_id}", headers=auth_headers(sv_a))
    assert resp_owner.status_code == 200

    resp_bomon = client.get(f"/api/topics/{topic_id}", headers=auth_headers(bomon))
    assert resp_bomon.status_code == 200
