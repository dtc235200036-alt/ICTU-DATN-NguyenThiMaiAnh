from datetime import date

import pytest

from app.core.roles import VaiTro
from app.models.de_tai import NHAP, DeTai
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.phan_cong import PhanCongHuongDan

# UC0.8: Bộ môn gán mỗi SV cho đúng một GVHD trong đợt; đổi GVHD gỡ SV khỏi
# bản nháp của GV cũ, bị chặn khi SV đã có đề tài Đã phân công; GV xem lớp của
# mình, SV xem GVHD của mình; chỉ Bộ môn ghi được phân công.


def _cohort(db) -> DotDoAn:
    cohort = DotDoAn(
        ten_dot="Đợt kiểm thử phân công",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


def _put(client, headers, cohort_id, items):
    return client.put(
        "/api/assignments", json={"dot_do_an_id": cohort_id, "items": items}, headers=headers
    )


@pytest.mark.parametrize("role", [VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN])
def test_only_bomon_writes_assignments(client, make_account, auth_headers, db, role):
    cohort = _cohort(db)
    actor = make_account(role)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    item = [{"sinh_vien_id": sv.sinh_vien_id, "giang_vien_id": gv.giang_vien_id}]

    assert _put(client, auth_headers(actor), cohort.id, item).status_code == 403
    assert client.get(
        f"/api/assignments?dot_do_an_id={cohort.id}", headers=auth_headers(actor)
    ).status_code == 403
    db.rollback()
    assert db.query(PhanCongHuongDan).count() == 0


def test_assign_list_and_views(client, make_account, auth_headers, db):
    cohort = _cohort(db)
    bomon = make_account(VaiTro.BO_MON)
    gv1 = make_account(VaiTro.GIANG_VIEN)
    gv2 = make_account(VaiTro.GIANG_VIEN)
    sv1 = make_account(VaiTro.SINH_VIEN)
    sv2 = make_account(VaiTro.SINH_VIEN)
    sv3 = make_account(VaiTro.SINH_VIEN)

    resp = _put(
        client,
        auth_headers(bomon),
        cohort.id,
        [
            {"sinh_vien_id": sv1.sinh_vien_id, "giang_vien_id": gv1.giang_vien_id},
            {"sinh_vien_id": sv2.sinh_vien_id, "giang_vien_id": gv1.giang_vien_id},
        ],
    )
    assert resp.status_code == 200
    assert resp.json()["cap_nhat"] == 2

    page = client.get(
        f"/api/assignments?dot_do_an_id={cohort.id}", headers=auth_headers(bomon)
    ).json()
    assert page["tong_sinh_vien"] == 3 and page["da_phan_cong"] == 2
    by_sv = {row["sinh_vien"]["id"]: row for row in page["items"]}
    assert by_sv[sv1.sinh_vien_id]["giang_vien"]["id"] == gv1.giang_vien_id
    assert by_sv[sv3.sinh_vien_id]["giang_vien"] is None
    load = {x["giang_vien"]["id"]: x["so_sinh_vien"] for x in page["tai_giang_vien"]}
    assert load == {gv1.giang_vien_id: 2, gv2.giang_vien_id: 0}

    chua = client.get(
        f"/api/assignments?dot_do_an_id={cohort.id}&loc=chua_phan_cong",
        headers=auth_headers(bomon),
    ).json()
    assert [r["sinh_vien"]["id"] for r in chua["items"]] == [sv3.sinh_vien_id]

    lop = client.get("/api/assignments/my-students", headers=auth_headers(gv1)).json()
    assert [s["sinh_vien"]["id"] for s in lop[0]["items"]] == [sv1.sinh_vien_id, sv2.sinh_vien_id]
    assert client.get("/api/assignments/my-students", headers=auth_headers(gv2)).json()[0][
        "items"
    ] == []

    adv = client.get("/api/assignments/my-advisor", headers=auth_headers(sv1)).json()
    assert adv[0]["giang_vien"]["id"] == gv1.giang_vien_id
    assert client.get("/api/assignments/my-advisor", headers=auth_headers(sv3)).json() == []


def test_reassign_detaches_draft_and_blocks_assigned(
    client, make_account, auth_headers, assign_gvhd, db
):
    cohort = _cohort(db)
    bomon = make_account(VaiTro.BO_MON)
    gv_old = make_account(VaiTro.GIANG_VIEN)
    gv_new = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv_old, cohort.id)

    # GV cũ lưu nháp cho SV; Bộ môn chuyển SV sang GV mới -> nháp mất SV.
    created = client.post(
        "/api/topics",
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Hệ thống điểm danh bằng QR",
            "sinh_vien_id": sv.sinh_vien_id,
            "gui": False,
        },
        headers=auth_headers(gv_old),
    )
    assert created.status_code == 201
    draft_id = created.json()["id"]
    move = _put(client, auth_headers(bomon), cohort.id, [
        {"sinh_vien_id": sv.sinh_vien_id, "giang_vien_id": gv_new.giang_vien_id}
    ])
    assert move.status_code == 200
    db.rollback()
    draft = db.get(DeTai, draft_id)
    assert draft.trang_thai == NHAP and draft.sinh_vien_id is None
    assert client.post(
        f"/api/topics/{draft_id}/submit", headers=auth_headers(gv_old)
    ).status_code == 409

    # GV mới giao đề tài cho SV.
    assigned = client.post(
        "/api/topics",
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Ứng dụng quản lý lớp học trực tuyến",
            "sinh_vien_id": sv.sinh_vien_id,
            "gui": True,
        },
        headers=auth_headers(gv_new),
    )
    assert assigned.status_code == 201
    assert assigned.json()["trang_thai"] == "DA_PHAN_CONG"

    # Đã phân công: không đổi, cũng không gỡ được GVHD nữa.
    back = _put(client, auth_headers(bomon), cohort.id, [
        {"sinh_vien_id": sv.sinh_vien_id, "giang_vien_id": gv_old.giang_vien_id}
    ])
    assert back.status_code == 409
    assert "Đã phân công" in back.json()["detail"]
    remove = _put(client, auth_headers(bomon), cohort.id, [
        {"sinh_vien_id": sv.sinh_vien_id, "giang_vien_id": None}
    ])
    assert remove.status_code == 409


def test_import_csv_reports_bad_lines(client, make_account, auth_headers, db):
    cohort = _cohort(db)
    bomon = make_account(VaiTro.BO_MON)
    gv = make_account(VaiTro.GIANG_VIEN, ma="GVIMP01")
    sv1 = make_account(VaiTro.SINH_VIEN)
    sv2 = make_account(VaiTro.SINH_VIEN)
    from app.models.tai_khoan import GiangVien, SinhVien

    m1 = db.get(SinhVien, sv1.sinh_vien_id).ma_so_sinh_vien
    m2 = db.get(SinhVien, sv2.sinh_vien_id).ma_so_sinh_vien
    mgv = db.get(GiangVien, gv.giang_vien_id).ma_giang_vien
    csv_text = f"ma_so_sinh_vien,ma_giang_vien\n{m1},{mgv}\n{m2},KHONGCO\nSVKHONGCO,{mgv}\n"

    resp = client.post(
        "/api/assignments/import",
        json={"dot_do_an_id": cohort.id, "noi_dung": csv_text},
        headers=auth_headers(bomon),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["cap_nhat"] == 1
    assert len(body["loi"]) == 2
    db.rollback()
    rows = db.query(PhanCongHuongDan).all()
    assert [(r.sinh_vien_id, r.giang_vien_id) for r in rows] == [
        (sv1.sinh_vien_id, gv.giang_vien_id)
    ]
