from datetime import date

from app.core.roles import VaiTro
from app.models.dot_do_an import DANG_MO, DotDoAn

# T-02-22/T-02-23 (D-08) + UC0.8 (0015): chỉ GVHD đứng tên đề tài mới được
# sửa/gửi bản nháp; GV giao đề tài thẳng cho SV trong lớp mình, không cho SV
# lớp khác (góp ý GVHD mục 1: SV không còn tự đề xuất).


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


def test_gv_draft_ownership_enforced(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _make_open_cohort(db)
    gv_a = make_account(VaiTro.GIANG_VIEN)
    gv_b = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    bomon = make_account(VaiTro.BO_MON)
    assign_gvhd(sv, gv_a, cohort.id)

    create_resp = client.post(
        "/api/topics",
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Hệ thống quản lý đồ án tốt nghiệp",
            "linh_vuc": "Hệ thống thông tin",
            "sinh_vien_id": sv.sinh_vien_id,
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
        "sinh_vien_id": sv.sinh_vien_id,
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

    # Chủ sở hữu gửi nháp -> giao thẳng cho SV (Đã phân công).
    submit_resp = client.post(f"/api/topics/{topic_id}/submit", headers=auth_headers(gv_a))
    assert submit_resp.status_code == 200
    assert submit_resp.json()["trang_thai"] == "DA_PHAN_CONG"


def test_gv_assigns_topic_only_to_own_student(
    client, make_account, auth_headers, assign_gvhd, db
):
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)
    gv_other = make_account(VaiTro.GIANG_VIEN)
    sv_mine = make_account(VaiTro.SINH_VIEN)
    sv_other = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv_mine, gv, cohort.id)
    assign_gvhd(sv_other, gv_other, cohort.id)

    body = {
        "dot_do_an_id": cohort.id,
        "ten_de_tai": "Ứng dụng quản lý thư viện số",
        "gui": True,
    }
    bad = client.post(
        "/api/topics", json={**body, "sinh_vien_id": sv_other.sinh_vien_id}, headers=auth_headers(gv)
    )
    assert bad.status_code == 409
    assert bad.json()["detail"] == "Sinh viên không thuộc lớp hướng dẫn của bạn trong đợt này"

    ok = client.post(
        "/api/topics", json={**body, "sinh_vien_id": sv_mine.sinh_vien_id}, headers=auth_headers(gv)
    )
    assert ok.status_code == 201
    assert ok.json()["trang_thai"] == "DA_PHAN_CONG"
    assert ok.json()["sinh_vien"]["id"] == sv_mine.sinh_vien_id

    # SV đã có đề tài đang hoạt động -> giao thêm bị chặn.
    dup = client.post(
        "/api/topics",
        json={**body, "ten_de_tai": "Một đề tài khác hẳn", "sinh_vien_id": sv_mine.sinh_vien_id},
        headers=auth_headers(gv),
    )
    assert dup.status_code == 409
    assert dup.json()["detail"] == "Sinh viên này đã có một đề tài đang hoạt động"
