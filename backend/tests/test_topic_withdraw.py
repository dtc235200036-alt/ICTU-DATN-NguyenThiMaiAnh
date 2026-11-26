"""Thu hồi đề tài đã giao về Nháp để sửa và giao lại (GVHD hoặc Bộ môn)."""
from datetime import date

from sqlalchemy import select

from app.core.roles import VaiTro
from app.models.de_cuong import DC_CHO_DUYET, DeCuong
from app.models.dot_do_an import DANG_MO, DA_DONG, DotDoAn
from app.models.thong_bao import ThongBao
from app.services import title_check


def _cohort(db, trang_thai: str = DANG_MO) -> DotDoAn:
    cohort = DotDoAn(
        ten_dot="Đợt test thu hồi đề tài",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=trang_thai,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


def _assigned_topic(client, auth_headers, gv, sv, cohort_id: int, ten: str) -> int:
    res = client.post(
        "/api/topics",
        json={"dot_do_an_id": cohort_id, "ten_de_tai": ten, "sinh_vien_id": sv.sinh_vien_id, "gui": True},
        headers=auth_headers(gv),
    )
    assert res.status_code == 201, res.text
    assert res.json()["quyen"]["thu_hoi"] is True
    return res.json()["id"]


def _notes(db, account) -> list[str]:
    db.rollback()
    return list(db.scalars(select(ThongBao.noi_dung).where(ThongBao.tai_khoan_id == account.tai_khoan_id)))


def test_gvhd_withdraws_then_edits_and_reassigns(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _cohort(db)
    gv, sv = make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    topic_id = _assigned_topic(client, auth_headers, gv, sv, cohort.id, "Hệ thống quản lý thư viện số")

    res = client.post(f"/api/topics/{topic_id}/withdraw", json={"ly_do": "Đổi hướng"}, headers=auth_headers(gv))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["trang_thai"] == "NHAP"
    assert body["quyen"] == {"sua": True, "gui": True, "thu_hoi": False}
    assert any("đã thu hồi đề tài 'Hệ thống quản lý thư viện số'. Lý do: Đổi hướng" in n for n in _notes(db, sv))
    # SV không còn thấy đề tài (nay là nháp của GV); thu hồi lần nữa -> 409.
    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(sv)).status_code == 403
    again = client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(gv))
    assert again.status_code == 409

    # Sửa tên rồi giao lại cho chính SV đó.
    put = client.put(
        f"/api/topics/{topic_id}",
        json={"dot_do_an_id": cohort.id, "ten_de_tai": "Ứng dụng mượn sách trực tuyến", "sinh_vien_id": sv.sinh_vien_id},
        headers=auth_headers(gv),
    )
    assert put.status_code == 200, put.text
    sub = client.post(f"/api/topics/{topic_id}/submit", headers=auth_headers(gv))
    assert sub.status_code == 200, sub.text
    assert sub.json()["trang_thai"] == "DA_PHAN_CONG"
    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(sv)).status_code == 200


def test_withdraw_frees_student_for_a_new_topic(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _cohort(db)
    gv, sv = make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    old_id = _assigned_topic(client, auth_headers, gv, sv, cohort.id, "Website bán hàng thời trang")
    body = {"dot_do_an_id": cohort.id, "ten_de_tai": "Ứng dụng học từ vựng", "sinh_vien_id": sv.sinh_vien_id, "gui": True}

    assert client.post("/api/topics", json=body, headers=auth_headers(gv)).status_code == 409
    assert client.post(f"/api/topics/{old_id}/withdraw", json={}, headers=auth_headers(gv)).status_code == 200
    assert client.post("/api/topics", json=body, headers=auth_headers(gv)).status_code == 201


def test_bomon_can_withdraw_and_lecturer_is_notified(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _cohort(db)
    gv, sv, bomon = make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.SINH_VIEN), make_account(VaiTro.BO_MON)
    assign_gvhd(sv, gv, cohort.id)
    topic_id = _assigned_topic(client, auth_headers, gv, sv, cohort.id, "Phần mềm quản lý phòng khám")

    detail = client.get(f"/api/topics/{topic_id}", headers=auth_headers(bomon)).json()
    assert detail["quyen"]["thu_hoi"] is True
    res = client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(bomon))
    assert res.status_code == 200, res.text
    assert res.json()["trang_thai"] == "NHAP"
    assert any(n.startswith("Bộ môn đã thu hồi đề tài") for n in _notes(db, gv))
    assert any(n.startswith("Bộ môn đã thu hồi đề tài") for n in _notes(db, sv))


def test_other_lecturer_and_student_cannot_withdraw(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _cohort(db)
    gv, other, sv = make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    topic_id = _assigned_topic(client, auth_headers, gv, sv, cohort.id, "Hệ thống điểm danh bằng mã QR")

    assert client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(other)).status_code == 403
    assert client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(sv)).status_code == 403
    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(sv)).json()["trang_thai"] == "DA_PHAN_CONG"


def test_cannot_withdraw_after_outline_or_when_cohort_closed(client, make_account, auth_headers, assign_gvhd, db):
    cohort = _cohort(db)
    gv, sv = make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    topic_id = _assigned_topic(client, auth_headers, gv, sv, cohort.id, "Ứng dụng quản lý chi tiêu cá nhân")

    db.add(DeCuong(de_tai_id=topic_id, trang_thai=DC_CHO_DUYET))
    db.commit()
    res = client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(gv))
    assert res.status_code == 409
    assert "đề cương" in res.json()["detail"]

    db.query(DeCuong).delete()
    db.query(DotDoAn).filter(DotDoAn.id == cohort.id).update({"trang_thai": DA_DONG})
    db.commit()
    assert client.get(f"/api/topics/{topic_id}", headers=auth_headers(gv)).json()["quyen"]["thu_hoi"] is False
    assert client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(gv)).status_code == 409


def test_withdrawn_topic_is_not_a_title_match(client, make_account, auth_headers, assign_gvhd, db):
    """Vector cũ của đề tài vừa thu hồi còn trong chỉ mục AI — không được hiện là đề tài trùng."""
    cohort = _cohort(db)
    gv, sv = make_account(VaiTro.GIANG_VIEN), make_account(VaiTro.SINH_VIEN)
    assign_gvhd(sv, gv, cohort.id)
    topic_id = _assigned_topic(client, auth_headers, gv, sv, cohort.id, "Hệ thống gợi ý món ăn theo khẩu vị")

    db.rollback()
    assert title_check._resolve_match(db, "TOPIC", topic_id, 90.0, None) is not None
    client.post(f"/api/topics/{topic_id}/withdraw", json={}, headers=auth_headers(gv))
    db.rollback()
    assert title_check._resolve_match(db, "TOPIC", topic_id, 90.0, None) is None
