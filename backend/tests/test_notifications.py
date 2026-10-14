from datetime import date

from sqlalchemy import func, select

from app.core.roles import VaiTro
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.thong_bao import DE_TAI_PHAN_CONG, ThongBao

# NOTF-01/D-05/D-08/T-03-37/T-03-39: GVHD giao đề tài -> SV nhận DE_TAI_PHAN_CONG
# trong CÙNG transaction với lần ghi; lần giao bị từ chối (409) không tạo gì; mỗi
# người chỉ đọc/đếm/đánh dấu thông báo của chính mình.


def _notes(db, tai_khoan_id) -> list[ThongBao]:
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    return (
        db.execute(select(ThongBao).where(ThongBao.tai_khoan_id == tai_khoan_id))
        .scalars()
        .all()
    )


def _assign(client, auth_headers, gv, sv, cohort_id, ten):
    return client.post(
        "/api/topics",
        json={
            "dot_do_an_id": cohort_id,
            "ten_de_tai": ten,
            "sinh_vien_id": sv.sinh_vien_id,
            "gui": True,
        },
        headers=auth_headers(gv),
    )


def test_notifications_are_private_and_follow_state_changes(
    client, make_account, auth_headers, assign_gvhd, db
):
    gv = make_account(VaiTro.GIANG_VIEN, ho_ten="Trần Văn Hướng")
    sv = make_account(VaiTro.SINH_VIEN, ho_ten="Nguyễn Thị An")
    sv2 = make_account(VaiTro.SINH_VIEN)
    other = make_account(VaiTro.SINH_VIEN)

    cohort = DotDoAn(
        ten_dot="Đợt kiểm thử thông báo",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    assign_gvhd(sv, gv, cohort.id)
    assign_gvhd(sv2, gv, cohort.id)

    # GVHD giao đề tài -> mỗi SV nhận đúng một DE_TAI_PHAN_CONG; GVHD không có thông báo.
    r1 = _assign(client, auth_headers, gv, sv, cohort.id, "Hệ thống quản lý ký túc xá")
    assert r1.status_code == 201
    t1 = r1.json()["id"]
    sv_notes = _notes(db, sv.tai_khoan_id)
    assert [n.loai for n in sv_notes] == [DE_TAI_PHAN_CONG]
    assert "Thạc sĩ Trần Văn Hướng" in sv_notes[0].noi_dung
    assert sv_notes[0].lien_ket == f"/de-tai/{t1}"
    assert _notes(db, gv.tai_khoan_id) == []

    r2 = _assign(client, auth_headers, gv, sv2, cohort.id, "Ứng dụng đặt lịch khám bệnh")
    assert r2.status_code == 201
    sv2_notes = _notes(db, sv2.tai_khoan_id)
    assert [n.loai for n in sv2_notes] == [DE_TAI_PHAN_CONG]
    assert sv2_notes[0].lien_ket == f"/de-tai/{r2.json()['id']}"

    # Lần giao bị từ chối (SV đã có đề tài đang hoạt động) không tạo thông báo.
    total_before = db.execute(select(func.count()).select_from(ThongBao)).scalar_one()
    again = _assign(client, auth_headers, gv, sv, cohort.id, "Một đề tài khác hẳn")
    assert again.status_code == 409
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    assert db.execute(select(func.count()).select_from(ThongBao)).scalar_one() == total_before

    # Riêng tư: B không thấy và không đánh dấu được thông báo của A.
    a_id = sv_notes[0].id
    b_list = client.get("/api/notifications", headers=auth_headers(other))
    assert b_list.status_code == 200
    assert b_list.json()["items"] == []
    assert client.post(
        f"/api/notifications/{a_id}/read", headers=auth_headers(other)
    ).status_code == 404
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    assert db.get(ThongBao, a_id).da_doc is False

    # Đếm / đánh dấu đã đọc / đánh dấu tất cả của chính SV A (có 1 thông báo).
    sv_count = client.get("/api/notifications/unread-count", headers=auth_headers(sv))
    assert sv_count.status_code == 200
    assert sv_count.json()["chua_doc"] == len(_notes(db, sv.tai_khoan_id)) == 1

    assert client.post(
        f"/api/notifications/{a_id}/read", headers=auth_headers(sv)
    ).status_code == 204
    assert client.get(
        "/api/notifications/unread-count", headers=auth_headers(sv)
    ).json()["chua_doc"] == 0

    assert client.post("/api/notifications/read-all", headers=auth_headers(sv)).status_code == 204
    # read-all của SV A không đụng tới thông báo của SV B.
    assert _notes(db, sv2.tai_khoan_id)[0].da_doc is False
