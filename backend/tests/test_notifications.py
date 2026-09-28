from datetime import date

from sqlalchemy import func, select

from app.core.roles import VaiTro
from app.models.de_tai import CHO_DUYET, GIANG_VIEN, SINH_VIEN, DeTai
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.thong_bao import (
    DE_TAI_DUYET,
    DE_TAI_PHAN_CONG,
    DE_TAI_TU_CHOI,
    ThongBao,
)

# NOTF-01/D-08/T-03-37/T-03-39: quyết định duyệt/từ chối đề tài (Phase 2) tạo
# thông báo trong CÙNG transaction với UPDATE trạng thái, quyết định bị từ chối
# (409) không tạo gì; mỗi người chỉ đọc/đếm/đánh dấu thông báo của chính mình.


def _pending(db, cohort_id, *, ten, loai, sinh_vien_id=None, giang_vien_id=None) -> DeTai:
    topic = DeTai(
        dot_do_an_id=cohort_id,
        giang_vien_id=giang_vien_id,
        sinh_vien_id=sinh_vien_id,
        ten_de_tai=ten,
        trang_thai=CHO_DUYET,
        loai_nguoi_de_xuat=loai,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def _notes(db, tai_khoan_id) -> list[ThongBao]:
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    return (
        db.execute(select(ThongBao).where(ThongBao.tai_khoan_id == tai_khoan_id))
        .scalars()
        .all()
    )


def test_notifications_are_private_and_follow_state_changes(
    client, make_account, auth_headers, db
):
    bomon = make_account(VaiTro.BO_MON)
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

    # Duyệt đề tài SV tự đề xuất + phân công GVHD -> SV và GVHD cùng nhận.
    t1 = _pending(db, cohort.id, ten="Hệ thống A", loai=SINH_VIEN, sinh_vien_id=sv.sinh_vien_id)
    resp = client.post(
        f"/api/topic-approvals/{t1.id}/approve",
        json={"giang_vien_id": gv.giang_vien_id},
        headers=auth_headers(bomon),
    )
    assert resp.status_code == 200
    sv_notes = _notes(db, sv.tai_khoan_id)
    gv_notes = _notes(db, gv.tai_khoan_id)
    assert [n.loai for n in sv_notes] == [DE_TAI_PHAN_CONG]
    assert "Thạc sĩ Trần Văn Hướng" in sv_notes[0].noi_dung
    assert sv_notes[0].lien_ket == f"/de-tai/{t1.id}"
    assert [n.loai for n in gv_notes] == [DE_TAI_PHAN_CONG]
    assert "Nguyễn Thị An" in gv_notes[0].noi_dung

    total_before = db.execute(select(func.count()).select_from(ThongBao)).scalar_one()
    again = client.post(
        f"/api/topic-approvals/{t1.id}/approve",
        json={"giang_vien_id": gv.giang_vien_id},
        headers=auth_headers(bomon),
    )
    assert again.status_code == 409
    db.rollback()  # REPEATABLE READ: bỏ snapshot cũ trước khi đọc lại
    assert db.execute(select(func.count()).select_from(ThongBao)).scalar_one() == total_before

    # GV đề xuất, chưa có SV -> GV đề xuất nhận DE_TAI_DUYET.
    t2 = _pending(db, cohort.id, ten="Hệ thống B", loai=GIANG_VIEN, giang_vien_id=gv.giang_vien_id)
    assert (
        client.post(
            f"/api/topic-approvals/{t2.id}/approve", json={}, headers=auth_headers(bomon)
        ).status_code
        == 200
    )
    assert DE_TAI_DUYET in [n.loai for n in _notes(db, gv.tai_khoan_id)]

    # Từ chối -> người đề xuất (SV) nhận DE_TAI_TU_CHOI kèm lý do.
    t3 = _pending(db, cohort.id, ten="Hệ thống C", loai=SINH_VIEN, sinh_vien_id=sv2.sinh_vien_id)
    assert (
        client.post(
            f"/api/topic-approvals/{t3.id}/reject",
            json={"ly_do": "Trùng hướng với đề tài khóa trước"},
            headers=auth_headers(bomon),
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
        f"/api/topic-approvals/{t2.id}/reject", json={"ly_do": "x"}, headers=auth_headers(bomon)
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
