import threading
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.roles import VaiTro
from app.main import app
from app.models.de_tai import DA_PHAN_CONG, DeTai
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.thong_bao import DE_TAI_PHAN_CONG, ThongBao

# Góp ý GVHD mục 1 (quick 261014-u0j): SV không tự đề xuất/đăng ký đề tài trên
# hệ thống; chỉ GVHD (GV Bộ môn phân công cho SV trong đợt, UC0.8) tạo và giao
# đề tài thẳng cho SV trong lớp mình -> Đã phân công ngay, kiểm tra trùng tên
# UC0.6 lưu cùng transaction, SV nhận thông báo DE_TAI_PHAN_CONG.
# D-06: route còn tồn tại nhưng chỉ GV -> 403 cho SV/Bộ môn; route đã gỡ -> 404.


def _make_open_cohort(db) -> DotDoAn:
    cohort = DotDoAn(
        ten_dot="Đợt đồ án test giao đề tài",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


def _body(cohort_id: int, sinh_vien_id: int | None, ten: str, gui: bool = True) -> dict:
    body: dict = {"dot_do_an_id": cohort_id, "ten_de_tai": ten, "gui": gui}
    if sinh_vien_id is not None:
        body["sinh_vien_id"] = sinh_vien_id
    return body


def test_sv_and_bomon_cannot_create_edit_submit_or_check_title(
    client, make_account, auth_headers, assign_gvhd, db
):
    """D-01/D-04/D-06, T-u0j-01: SV/Bộ môn nhận 403 trên mọi route ghi đề tài."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    bomon = make_account(VaiTro.BO_MON)
    assign_gvhd(sv, gv, cohort.id)

    draft = client.post(
        "/api/topics",
        json=_body(cohort.id, sv.sinh_vien_id, "Hệ thống quản lý thư viện số", gui=False),
        headers=auth_headers(gv),
    )
    assert draft.status_code == 201
    topic_id = draft.json()["id"]

    for actor in (sv, bomon):
        h = auth_headers(actor)
        assert (
            client.post(
                "/api/topics",
                json=_body(cohort.id, sv.sinh_vien_id, "Đề tài tự đề xuất không hợp lệ"),
                headers=h,
            ).status_code
            == 403
        )
        assert (
            client.put(
                f"/api/topics/{topic_id}",
                json={
                    "dot_do_an_id": cohort.id,
                    "ten_de_tai": "Tên đề tài đổi trái phép",
                    "sinh_vien_id": sv.sinh_vien_id,
                },
                headers=h,
            ).status_code
            == 403
        )
        assert client.post(f"/api/topics/{topic_id}/submit", headers=h).status_code == 403
        assert (
            client.post(
                "/api/topics/check-title", json={"ten_de_tai": "Hệ thống quản lý"}, headers=h
            ).status_code
            == 403
        )

    # GV thì dùng được check-title (UC0.6 giữ cho GVHD).
    ok = client.post(
        "/api/topics/check-title",
        json={"ten_de_tai": "Hệ thống quản lý thư viện số"},
        headers=auth_headers(gv),
    )
    assert ok.status_code == 200


def test_registration_and_approval_routes_are_gone(
    client, make_account, auth_headers, assign_gvhd, db
):
    """D-02/D-06, T-u0j-04: route đăng ký đề tài và router duyệt đề tài đã gỡ -> 404."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    created = client.post(
        "/api/topics",
        json=_body(cohort.id, sv.sinh_vien_id, "Ứng dụng quản lý thư viện số"),
        headers=auth_headers(gv),
    )
    topic_id = created.json()["id"]

    assert client.post(f"/api/topics/{topic_id}/register", headers=auth_headers(sv)).status_code in (
        404,
        405,
    )
    assert client.get("/api/topic-approvals", headers=auth_headers(gv)).status_code == 404
    assert (
        client.post(f"/api/topic-approvals/{topic_id}/approve", headers=auth_headers(gv)).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/topic-approvals/{topic_id}/reject",
            json={"ly_do": "x"},
            headers=auth_headers(gv),
        ).status_code
        == 404
    )


def test_gv_assigns_topic_directly_and_student_is_notified(
    client, make_account, auth_headers, assign_gvhd, db
):
    """D-04/D-05/D-07: GVHD giao -> Đã phân công ngay, lưu kiem_tra_ten, SV nhận
    đúng một thông báo DE_TAI_PHAN_CONG có liên kết /de-tai/{id}."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN, ho_ten="Trần Văn Hướng")
    sv = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)

    resp = client.post(
        "/api/topics",
        json=_body(cohort.id, sv.sinh_vien_id, "Hệ thống quản lý ký túc xá"),
        headers=auth_headers(gv),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["trang_thai"] == "DA_PHAN_CONG"
    assert body["sinh_vien"]["id"] == sv.sinh_vien_id
    assert body["giang_vien_huong_dan"]["id"] == gv.giang_vien_id
    assert body["kiem_tra_ten"] is not None
    assert body["kiem_tra_ten"]["trang_thai"] == "HOAN_TAT"

    db.rollback()
    notes = db.execute(select(ThongBao).where(ThongBao.tai_khoan_id == sv.tai_khoan_id)).scalars().all()
    assert [n.loai for n in notes] == [DE_TAI_PHAN_CONG]
    assert "Thạc sĩ Trần Văn Hướng" in notes[0].noi_dung
    assert notes[0].lien_ket == f"/de-tai/{body['id']}"

    # GV không nhận thông báo "chờ duyệt" nào (luồng duyệt đã bỏ).
    gv_notes = db.execute(select(ThongBao).where(ThongBao.tai_khoan_id == gv.tai_khoan_id)).scalars().all()
    assert gv_notes == []


def test_sinh_vien_id_required_and_must_be_my_student(
    client, make_account, auth_headers, assign_gvhd, db
):
    """D-02/D-07, T-u0j-02: thiếu sinh_vien_id -> 422; SV lớp khác / GV không phải
    GVHD -> 409 'không thuộc lớp hướng dẫn'."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)
    gv_other = make_account(VaiTro.GIANG_VIEN)
    sv_mine = make_account(VaiTro.SINH_VIEN)
    sv_other = make_account(VaiTro.SINH_VIEN)
    sv_unassigned = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv_mine, gv, cohort.id)
    assign_gvhd(sv_other, gv_other, cohort.id)

    missing = client.post(
        "/api/topics",
        json=_body(cohort.id, None, "Đề tài không chọn sinh viên"),
        headers=auth_headers(gv),
    )
    assert missing.status_code == 422

    msg = "Sinh viên không thuộc lớp hướng dẫn của bạn trong đợt này"
    for sv_id in (sv_other.sinh_vien_id, sv_unassigned.sinh_vien_id):
        r = client.post(
            "/api/topics",
            json=_body(cohort.id, sv_id, "Đề tài giao nhầm sinh viên"),
            headers=auth_headers(gv),
        )
        assert r.status_code == 409
        assert r.json()["detail"] == msg

    # GV khác (không phải GVHD của sv_mine) cũng bị từ chối.
    r = client.post(
        "/api/topics",
        json=_body(cohort.id, sv_mine.sinh_vien_id, "Đề tài giao nhầm giảng viên"),
        headers=auth_headers(gv_other),
    )
    assert r.status_code == 409
    assert r.json()["detail"] == msg


def _create_concurrently(requests: list[tuple[dict, dict]]) -> tuple[list[int], list[str | None]]:
    """Chạy N request POST /api/topics cùng lúc (mỗi thread một TestClient +
    threading.Barrier riêng), trả (status_codes, details) theo thứ tự `requests`."""
    barrier = threading.Barrier(len(requests))
    statuses: list[int | None] = [None] * len(requests)
    details: list[str | None] = [None] * len(requests)

    def _worker(idx: int, body: dict, headers: dict) -> None:
        with TestClient(app, base_url="https://testserver") as c:
            barrier.wait()
            resp = c.post("/api/topics", json=body, headers=headers)
            statuses[idx] = resp.status_code
            try:
                details[idx] = resp.json().get("detail")
            except ValueError:
                details[idx] = None

    threads = [
        threading.Thread(target=_worker, args=(i, body, headers))
        for i, (body, headers) in enumerate(requests)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return statuses, details  # type: ignore[return-value]


def test_concurrent_assign_one_active_topic_per_student(
    make_account, auth_headers, assign_gvhd, db
):
    """FR-DT-06, T-u0j-05: hai request giao đề tài đồng thời cho cùng một SV —
    đúng 1 request 201, request còn lại 409; CSDL còn đúng 1 đề tài đang hoạt động."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)

    for i in range(3):
        sv = make_account(VaiTro.SINH_VIEN)
        assign_gvhd(sv, gv, cohort.id)
        headers = auth_headers(gv)
        statuses, details = _create_concurrently(
            [
                (_body(cohort.id, sv.sinh_vien_id, f"Đề tài giao đồng thời A {i}"), headers),
                (_body(cohort.id, sv.sinh_vien_id, f"Đề tài giao đồng thời B {i}"), headers),
            ]
        )
        assert sorted(statuses) == [201, 409]
        assert details[statuses.index(409)] == "Sinh viên này đã có một đề tài đang hoạt động"

        with SessionLocal() as fresh:
            active = (
                fresh.execute(
                    select(DeTai.id).where(DeTai.sinh_vien_id_dang_hoat_dong == sv.sinh_vien_id)
                )
                .scalars()
                .all()
            )
            assert len(active) == 1


def test_gv_draft_is_hidden_from_student_then_submit_assigns(
    client, make_account, auth_headers, assign_gvhd, db
):
    """Nháp GV chỉ GV thấy; gửi nháp -> Đã phân công + thông báo SV; SV chỉ thấy
    đề tài của chính mình."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    classmate = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    assign_gvhd(classmate, gv, cohort.id)

    draft = client.post(
        "/api/topics",
        json=_body(cohort.id, sv.sinh_vien_id, "Ứng dụng đặt lịch khám bệnh", gui=False),
        headers=auth_headers(gv),
    )
    assert draft.status_code == 201
    assert draft.json()["trang_thai"] == "NHAP"
    topic_id = draft.json()["id"]

    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(sv)).status_code == 403
    for pham_vi in ("tat_ca", "cua_toi"):
        listed = client.get(f"/api/topics?pham_vi={pham_vi}", headers=auth_headers(sv)).json()
        assert topic_id not in [t["id"] for t in listed["items"]]

    sub = client.post(f"/api/topics/{topic_id}/submit", headers=auth_headers(gv))
    assert sub.status_code == 200
    assert sub.json()["trang_thai"] == "DA_PHAN_CONG"
    assert sub.json()["kiem_tra_ten"] is not None

    db.rollback()
    notes = db.execute(select(ThongBao).where(ThongBao.tai_khoan_id == sv.tai_khoan_id)).scalars().all()
    assert [n.loai for n in notes] == [DE_TAI_PHAN_CONG]

    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(sv)).status_code == 200
    # SV cùng lớp thấy danh sách rỗng và không xem được đề tài của bạn.
    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(classmate)).status_code == 403
    for pham_vi in ("tat_ca", "cua_toi"):
        mine = client.get(f"/api/topics?pham_vi={pham_vi}", headers=auth_headers(sv)).json()
        assert [t["id"] for t in mine["items"]] == [topic_id]
        theirs = client.get(f"/api/topics?pham_vi={pham_vi}", headers=auth_headers(classmate)).json()
        assert theirs["items"] == []
        assert "co_the_dang_ky" not in mine["items"][0]


def test_submit_draft_whose_student_was_detached_is_409(
    client, make_account, auth_headers, assign_gvhd, db
):
    """Nháp mất SV (Bộ môn đổi GVHD) -> gửi trả 409 yêu cầu chọn lại sinh viên."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)
    sv = make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    draft = client.post(
        "/api/topics",
        json=_body(cohort.id, sv.sinh_vien_id, "Hệ thống điểm danh bằng QR", gui=False),
        headers=auth_headers(gv),
    )
    topic_id = draft.json()["id"]

    db.rollback()
    topic = db.get(DeTai, topic_id)
    topic.sinh_vien_id = None  # mô phỏng assignments.reassign gỡ SV khỏi nháp
    db.commit()

    r = client.post(f"/api/topics/{topic_id}/submit", headers=auth_headers(gv))
    assert r.status_code == 409
    assert "chọn sinh viên" in r.json()["detail"]
    db.rollback()
    assert db.get(DeTai, topic_id).trang_thai != DA_PHAN_CONG
