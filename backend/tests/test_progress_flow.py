"""UC3 (tiến độ) — 2 test tập trung theo kế hoạch 03-06: (1) quy tắc mốc +
cờ trễ mốc tính theo ngày (D-05), (2) nộp lại/ghi đè, phạm vi nhận xét và
thông báo (PROG-01/02, NOTF-01)."""
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select, text, update

from app.core.roles import VaiTro
from app.core.timeutil import today_vn
from app.models.de_cuong import DC_CHO_DUYET, DC_DA_DUYET, DeCuong, TaiLieuDoAn
from app.models.de_tai import DeTai
from app.services import documents

_PDF_CT = "application/pdf"


def _set_outline(db, topic, trang_thai):
    db.add(DeCuong(de_tai_id=topic.id, trang_thai=trang_thai))
    db.commit()


def _create_milestone(client, headers, dot_id, ten_moc, han_nop):
    return client.post(
        "/api/progress/milestones",
        headers=headers,
        json={"dot_do_an_id": dot_id, "ten_moc": ten_moc, "han_nop": han_nop.isoformat()},
    )


def _statuses(moc_list):
    return {m["ten_moc"]: m["trang_thai"] for m in moc_list}


def test_milestones_and_late_flags(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    bm = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)  # đợt DANG_MO, ngay_bat_dau 2026-01-01
    _set_outline(db, topic, DC_DA_DUYET)
    dot_id = topic.dot_do_an_id
    bm_h, sv_h, gv_h = auth_headers(bm), auth_headers(sv), auth_headers(gv)

    today = today_vn()
    yesterday, tomorrow = today - timedelta(days=1), today + timedelta(days=1)

    # UC3.1 E1: hạn nộp trước ngày mở đợt -> 422
    resp = _create_milestone(client, bm_h, dot_id, "Mốc sai", date(2025, 12, 31))
    assert resp.status_code == 422, resp.text
    assert "Hạn nộp nằm ngoài thời gian đợt đồ án" in resp.json()["detail"]

    # SV/GV không quản lý mốc, không xem dashboard toàn khoa
    for h in (sv_h, gv_h):
        assert _create_milestone(client, h, dot_id, "X", tomorrow).status_code == 403
        assert client.get("/api/progress/dashboard", headers=h).status_code == 403

    ids = {}
    for ten, han in (("M1", yesterday), ("M2", yesterday), ("M3", tomorrow), ("M4", tomorrow)):
        resp = _create_milestone(client, bm_h, dot_id, ten, han)
        assert resp.status_code == 201, resp.text
        ids[ten] = resp.json()["id"]
    listed = client.get(f"/api/progress/milestones?dot_do_an_id={dot_id}", headers=sv_h)
    assert [m["ten_moc"] for m in listed.json()] == ["M1", "M2", "M3", "M4"]

    resp = client.post(
        f"/api/progress/reports/{ids['M2']}", headers=sv_h, data={"noi_dung": "Làm xong M2"}
    )
    assert resp.status_code == 200, resp.text
    resp = client.post(
        f"/api/progress/reports/{ids['M3']}",
        headers=sv_h,
        data={"noi_dung": "Làm xong M3"},
        files={"file": ("tien-do-m3.pdf", pdf_bytes(["Progress M3"]), _PDF_CT)},
    )
    assert resp.status_code == 200, resp.text

    me = client.get("/api/progress/me", headers=sv_h).json()
    expected = {"M1": "TRE_MOC", "M2": "NOP_TRE", "M3": "DUNG_HAN", "M4": "CHUA_DEN_HAN"}
    assert _statuses(me["de_tai"]["moc"]) == expected
    m3 = next(m for m in me["de_tai"]["moc"] if m["ten_moc"] == "M3")
    assert m3["bao_cao"]["tep"]["ten_goc"] == "tien-do-m3.pdf"
    assert me["de_tai"]["tre_moc"] is True

    dash = client.get(f"/api/progress/dashboard?dot_do_an_id={dot_id}", headers=bm_h).json()
    assert dash["so_sv_tre_moc"] == 1 and dash["total"] == 1
    row = dash["items"][0]
    assert row["tre_moc"] is True and row["de_tai"]["id"] == topic.id
    by_id = {c["moc_id"]: c["trang_thai"] for c in row["o"]}
    assert by_id == {ids[k]: v for k, v in expected.items()}
    late_only = client.get(
        f"/api/progress/dashboard?dot_do_an_id={dot_id}&chi_tre_moc=true", headers=bm_h
    ).json()
    assert [r["de_tai"]["id"] for r in late_only["items"]] == [topic.id]

    # UC3.1 A1: mốc đã có báo cáo không xóa được; mốc trống thì xóa được
    resp = client.delete(f"/api/progress/milestones/{ids['M3']}", headers=bm_h)
    assert resp.status_code == 409, resp.text
    assert client.delete(f"/api/progress/milestones/{ids['M4']}", headers=bm_h).status_code == 204


def test_report_resubmit_and_review_scope(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, docx_bytes, db
):
    bm = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    sv_other = make_account(VaiTro.SINH_VIEN)
    gv_other = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)
    other_topic = make_assigned_topic(sv_other, gv_other)
    # SV khác cùng đợt nhưng đề cương mới Chờ duyệt
    db.execute(
        update(DeTai).where(DeTai.id == other_topic.id).values(dot_do_an_id=topic.dot_do_an_id)
    )
    db.commit()
    _set_outline(db, topic, DC_DA_DUYET)
    _set_outline(db, other_topic, DC_CHO_DUYET)
    sv_h, sv_other_h = auth_headers(sv), auth_headers(sv_other)

    m3 = _create_milestone(
        client, auth_headers(bm), topic.dot_do_an_id, "Mốc 3", today_vn() + timedelta(days=3)
    ).json()["id"]

    resp = client.post(f"/api/progress/reports/{m3}", headers=sv_other_h, data={"noi_dung": "x"})
    assert resp.status_code == 409, resp.text
    assert "Đề cương chưa được duyệt" in resp.json()["detail"]

    first = client.post(
        f"/api/progress/reports/{m3}",
        headers=sv_h,
        data={"noi_dung": "Bản đầu"},
        files={"file": ("v1.pdf", pdf_bytes(["v1"]), _PDF_CT)},
    )
    assert first.status_code == 200, first.text
    first_report = next(m for m in first.json()["de_tai"]["moc"] if m["id"] == m3)["bao_cao"]
    second = client.post(
        f"/api/progress/reports/{m3}",
        headers=sv_h,
        data={"noi_dung": "Bản sửa lại"},
        files={"file": ("v2.docx", docx_bytes(["Tiến độ bản hai"]), "application/octet-stream")},
    )
    assert second.status_code == 200, second.text
    second_report = next(m for m in second.json()["de_tai"]["moc"] if m["id"] == m3)["bao_cao"]
    assert second_report["id"] == first_report["id"]
    assert second_report["noi_dung"] == "Bản sửa lại"
    assert second_report["tep"]["ten_goc"] == "v2.docx"
    assert db.execute(
        text("SELECT COUNT(*) FROM bao_cao_tien_do WHERE de_tai_id = :t"), {"t": topic.id}
    ).scalar_one() == 1
    versions = db.execute(
        select(TaiLieuDoAn)
        .where(TaiLieuDoAn.de_tai_id == topic.id)
        .where(TaiLieuDoAn.loai == "BAO_CAO_TIEN_DO")
        .order_by(TaiLieuDoAn.so_phien_ban)
    ).scalars().all()
    assert [v.so_phien_ban for v in versions] == [1, 2]
    assert Path(documents.storage_path(versions[0].ten_luu_tru)).exists()

    # Phạm vi xem / nhận xét
    assert client.get(f"/api/progress/topics/{topic.id}", headers=sv_other_h).status_code == 403
    review = {"nhan_xet": "Tốt, tiếp tục", "danh_gia": "DAT"}
    bao_cao_id = second_report["id"]
    resp = client.post(
        f"/api/progress/reports/{bao_cao_id}/review", headers=auth_headers(gv_other), json=review
    )
    assert resp.status_code == 403, resp.text
    resp = client.post(
        f"/api/progress/reports/{bao_cao_id}/review", headers=auth_headers(gv), json=review
    )
    assert resp.status_code == 200, resp.text

    notifs = client.get("/api/notifications", headers=sv_h).json()["items"]
    assert any(n["loai"] == "TIEN_DO_NHAN_XET" for n in notifs)

    resp = client.post(f"/api/progress/reports/{m3}", headers=sv_h, data={"noi_dung": "Lần 3"})
    assert resp.status_code == 409, resp.text
    assert "không thể nộp lại" in resp.json()["detail"]
    assert db.execute(
        select(func.count()).select_from(TaiLieuDoAn).where(TaiLieuDoAn.de_tai_id == topic.id)
    ).scalar_one() == 2
