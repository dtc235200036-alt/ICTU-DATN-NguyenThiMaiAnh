from datetime import date

from sqlalchemy import func, select

from app.core.roles import VaiTro
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.thong_bao import (
    DE_TAI_CHO_DUYET,
    DE_TAI_PHAN_CONG,
    DE_TAI_TU_CHOI,
    ThongBao,
)

# NOTF-01/D-08/T-03-37/T-03-39: SV gửi đề tài và quyết định duyệt/từ chối của GVHD tạo
# thông báo trong CÙNG transaction với UPDATE trạng thái, quyết định bị từ chối
# (409) không tạo gì; mỗi người chỉ đọc/đếm/đánh dấu thông báo của chính mình.


def _notes(db, tai_khoan_id) -> list[ThongBao]:
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    return (
        db.execute(select(ThongBao).where(ThongBao.tai_khoan_id == tai_khoan_id))
        .scalars()
        .all()
    )


def _propose(client, auth_headers, sv, cohort_id, ten) -> int:
    resp = client.post(
        "/api/topics",
        json={"dot_do_an_id": cohort_id, "ten_de_tai": ten, "gui": True},
        headers=auth_headers(sv),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


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

    # SV gửi đề tài -> GVHD có việc duyệt; GVHD duyệt -> SV nhận DE_TAI_PHAN_CONG.
    t1 = _propose(client, auth_headers, sv, cohort.id, "Hệ thống quản lý ký túc xá")
    gv_notes = _notes(db, gv.tai_khoan_id)
    assert [n.loai for n in gv_notes] == [DE_TAI_CHO_DUYET]
    assert "Nguyễn Thị An" in gv_notes[0].noi_dung

    resp = client.post(f"/api/topic-approvals/{t1}/approve", headers=auth_headers(gv))
    assert resp.status_code == 200
    sv_notes = _notes(db, sv.tai_khoan_id)
    assert [n.loai for n in sv_notes] == [DE_TAI_PHAN_CONG]
    assert "Thạc sĩ Trần Văn Hướng" in sv_notes[0].noi_dung
    assert sv_notes[0].lien_ket == f"/de-tai/{t1}"

    total_before = db.execute(select(func.count()).select_from(ThongBao)).scalar_one()
    again = client.post(f"/api/topic-approvals/{t1}/approve", headers=auth_headers(gv))
    assert again.status_code == 409
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    assert db.execute(select(func.count()).select_from(ThongBao)).scalar_one() == total_before

    # Từ chối -> SV đề xuất nhận DE_TAI_TU_CHOI kèm lý do.
    t3 = _propose(client, auth_headers, sv2, cohort.id, "Ứng dụng đặt lịch khám bệnh")
    assert (
        client.post(
            f"/api/topic-approvals/{t3}/reject",
            json={"ly_do": "Trùng hướng với đề tài khóa trước"},
            headers=auth_headers(gv),
        ).status_code
        == 200
    )
    sv2_notes = _notes(db, sv2.tai_khoan_id)
    assert [n.loai for n in sv2_notes] == [DE_TAI_TU_CHOI]
    assert "Trùng hướng với đề tài khóa trước" in sv2_notes[0].noi_dung

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

    # Đếm / đánh dấu đã đọc / đánh dấu tất cả của chính A.
    extra = client.post(
        f"/api/topic-approvals/{t1}/reject", json={"ly_do": "x"}, headers=auth_headers(gv)
    )
    assert extra.status_code == 409  # đã duyệt rồi — không tạo thêm
    gv_count = client.get("/api/notifications/unread-count", headers=auth_headers(gv))
    assert gv_count.status_code == 200
    assert gv_count.json()["chua_doc"] == len(_notes(db, gv.tai_khoan_id)) == 2

    gv_first = _notes(db, gv.tai_khoan_id)[0].id
    assert client.post(
        f"/api/notifications/{gv_first}/read", headers=auth_headers(gv)
    ).status_code == 204
    assert client.get(
        "/api/notifications/unread-count", headers=auth_headers(gv)
    ).json()["chua_doc"] == 1

    assert client.post("/api/notifications/read-all", headers=auth_headers(gv)).status_code == 204
    assert client.get(
        "/api/notifications/unread-count", headers=auth_headers(gv)
    ).json()["chua_doc"] == 0
    # read-all của GV không đụng tới thông báo của SV.
    assert _notes(db, sv.tai_khoan_id)[0].da_doc is False
