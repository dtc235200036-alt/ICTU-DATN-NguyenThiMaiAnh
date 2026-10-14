from datetime import date

from app.core.roles import VaiTro
from app.models.dot_do_an import DANG_MO, DotDoAn

# T-02-22/T-02-23 (D-08) + UC0.8 (0015): chỉ chủ sở hữu đề tài (người đứng tên
# đề xuất) mới được sửa/gửi; đề tài SV đề xuất chỉ SV đó, GVHD của SV và Bộ môn
# xem được; GV giao đề tài thẳng cho SV trong lớp mình, không cho SV lớp khác.


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

    # Không giao cho SV nào -> mở cho lớp của GV đăng ký (không qua Bộ môn).
    submit_resp = client.post(f"/api/topics/{topic_id}/submit", headers=auth_headers(gv_a))
    assert submit_resp.status_code == 200
    assert submit_resp.json()["trang_thai"] == "DA_DUYET"


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


def test_sv_proposal_goes_to_own_gvhd(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _make_open_cohort(db)
    sv_a = make_account(VaiTro.SINH_VIEN)
    sv_b = make_account(VaiTro.SINH_VIEN)
    gvhd = make_account(VaiTro.GIANG_VIEN)
    other_gv = make_account(VaiTro.GIANG_VIEN)
    bomon = make_account(VaiTro.BO_MON)

    payload = {
        "dot_do_an_id": cohort.id,
        "ten_de_tai": "Ứng dụng học tiếng Anh cho trẻ em",
        "linh_vuc": "Công nghệ phần mềm",
        "gui": True,
    }
    # Chưa được phân công GVHD -> không đề xuất được.
    no_gvhd = client.post("/api/topics", json=payload, headers=auth_headers(sv_a))
    assert no_gvhd.status_code == 409

    assign_gvhd(sv_a, gvhd, cohort.id)
    create_resp = client.post("/api/topics", json=payload, headers=auth_headers(sv_a))
    assert create_resp.status_code == 201
    topic_id = create_resp.json()["id"]
    assert create_resp.json()["trang_thai"] == "CHO_DUYET"
    assert create_resp.json()["giang_vien_huong_dan"]["id"] == gvhd.giang_vien_id

    for actor in (sv_b, other_gv):
        resp = client.get(f"/api/topics/{topic_id}", headers=auth_headers(actor))
        assert resp.status_code == 403

    for actor in (sv_a, gvhd):
        assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(actor)).status_code == 200

    resp_bomon = client.get(f"/api/topics/{topic_id}", headers=auth_headers(bomon))
    assert resp_bomon.status_code == 200
    # UC0.6/D-10: mọi submit lưu đúng 1 kết quả kiểm tra trùng tên, snapshot
    # ngưỡng NGUONG_TEN_DE_TAI mặc định (50.00) từ migration 0004.
    kiem_tra_ten = resp_bomon.json()["kiem_tra_ten"]
    assert kiem_tra_ten is not None
    assert kiem_tra_ten["trang_thai"] == "HOAN_TAT"
    assert kiem_tra_ten["nguong_ap_dung"] == 50.0

    # T-02-29/UC1.4 A1: GET /api/topics scope không bao giờ lộ đề tài Chờ duyệt
    # của SV khác cho SV B / GV khác, kể cả khi lọc trạng thái + pham_vi=tat_ca.
    for actor in (sv_b, other_gv):
        listed = client.get(
            "/api/topics?trang_thai=CHO_DUYET&pham_vi=tat_ca", headers=auth_headers(actor)
        )
        assert listed.status_code == 200
        assert topic_id not in [item["id"] for item in listed.json()["items"]]

    for actor in (gvhd, bomon):
        listed = client.get("/api/topics?trang_thai=CHO_DUYET", headers=auth_headers(actor))
        assert topic_id in [item["id"] for item in listed.json()["items"]]
