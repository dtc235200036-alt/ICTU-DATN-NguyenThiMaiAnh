"""UC4 (bảo vệ) — 2 test tập trung theo yêu cầu của kế hoạch: cổng nộp báo
cáo cuối (UC4.1) và các quy tắc hội đồng/xếp lịch bao gồm chặn GVHD (UC4.2,
D-06)."""
from sqlalchemy import func, select

from app.core.roles import VaiTro
from app.models.bao_ve import LichBaoVe

_PDF_CT = "application/pdf"


def _approve_outline(db, topic):
    from app.models.de_cuong import DC_DA_DUYET, DeCuong

    de_cuong = DeCuong(de_tai_id=topic.id, trang_thai=DC_DA_DUYET)
    db.add(de_cuong)
    db.commit()


def test_final_report_gate(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    other_sv = make_account(VaiTro.SINH_VIEN)
    bomon = make_account(VaiTro.BO_MON)
    topic = make_assigned_topic(sv, gv)

    content = pdf_bytes(["Báo cáo cuối dùng để kiểm thử cổng nộp UC4.1"])

    # đề cương chưa Đã duyệt -> 409
    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(sv),
        files={"file": ("bao-cao.pdf", content, _PDF_CT)},
    )
    assert resp.status_code == 409, resp.text

    _approve_outline(db, topic)

    # GV/Bộ môn không nộp được (403 qua require_role)
    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(gv),
        files={"file": ("bao-cao.pdf", content, _PDF_CT)},
    )
    assert resp.status_code == 403
    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(bomon),
        files={"file": ("bao-cao.pdf", content, _PDF_CT)},
    )
    assert resp.status_code == 403

    # SV chủ đề tài nộp -> 202, v1 tồn tại, kiểm tra Hoàn tất
    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(sv),
        files={"file": ("bao-cao.pdf", content, _PDF_CT)},
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["phien_ban"][0]["tai_lieu"]["so_phien_ban"] == 1

    reread = client.get(
        f"/api/defense/final-reports/{topic.id}", headers=auth_headers(sv)
    ).json()
    assert reread["phien_ban"][0]["kiem_tra"]["trang_thai"] == "HOAN_TAT"

    # SV khác -> 403 trên GET
    resp = client.get(
        f"/api/defense/final-reports/{topic.id}", headers=auth_headers(other_sv)
    )
    assert resp.status_code == 403

    # sau khi được xếp lịch bảo vệ, nộp lại -> 409
    from datetime import date, time

    from app.models.bao_ve import CHU_TICH, THU_KY, UY_VIEN, HoiDong, ThanhVienHoiDong

    gv2 = make_account(VaiTro.GIANG_VIEN)
    gv3 = make_account(VaiTro.GIANG_VIEN)
    hoi_dong = HoiDong(
        ten_hoi_dong="Hội đồng kiểm thử cổng nộp",
        ngay_bao_ve=date(2026, 10, 1),
        gio_bao_ve=time(8, 0),
        phong="P101",
    )
    db.add(hoi_dong)
    db.flush()
    db.add_all(
        [
            ThanhVienHoiDong(hoi_dong_id=hoi_dong.id, giang_vien_id=gv2.giang_vien_id, vai_tro=CHU_TICH),
            ThanhVienHoiDong(hoi_dong_id=hoi_dong.id, giang_vien_id=gv3.giang_vien_id, vai_tro=THU_KY),
            ThanhVienHoiDong(hoi_dong_id=hoi_dong.id, giang_vien_id=gv.giang_vien_id, vai_tro=UY_VIEN),
        ]
    )
    db.add(LichBaoVe(hoi_dong_id=hoi_dong.id, de_tai_id=topic.id, sinh_vien_id=sv.sinh_vien_id, thu_tu=1))
    db.commit()

    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(sv),
        files={"file": ("bao-cao-v2.pdf", content, _PDF_CT)},
    )
    assert resp.status_code == 409, resp.text


def test_committee_rules(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    bomon = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)  # GVHD của topic
    topic = make_assigned_topic(sv, gv)
    _approve_outline(db, topic)

    content = pdf_bytes(["Báo cáo cuối dùng để kiểm thử quy tắc hội đồng"])
    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(sv),
        files={"file": ("bao-cao.pdf", content, _PDF_CT)},
    )
    assert resp.status_code == 202, resp.text

    gv1 = make_account(VaiTro.GIANG_VIEN)
    gv2 = make_account(VaiTro.GIANG_VIEN)
    gv3 = make_account(VaiTro.GIANG_VIEN)

    base_payload = {
        "ngay_bao_ve": "2026-10-01",
        "gio_bao_ve": "08:00",
        "phong": "P301",
    }

    # SV/GV bị từ chối 403 trên mọi route hội đồng/xếp lịch
    assert client.get("/api/defense/committees", headers=auth_headers(sv)).status_code == 403
    assert client.get("/api/defense/committees", headers=auth_headers(gv)).status_code == 403
    assert client.get("/api/defense/eligible-students", headers=auth_headers(gv)).status_code == 403
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(sv),
        json={
            **base_payload,
            "ten_hoi_dong": "HD do SV tạo",
            "thanh_vien": [
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "THU_KY"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 403
    resp = client.post(
        "/api/defense/committees/1/schedules",
        headers=auth_headers(sv),
        json={"de_tai_id": topic.id},
    )
    assert resp.status_code == 403

    # 2 thành viên -> 422
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(bomon),
        json={
            **base_payload,
            "ten_hoi_dong": "HD thiếu người",
            "thanh_vien": [
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 422, resp.text

    # 2 Chủ tịch -> 422
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(bomon),
        json={
            **base_payload,
            "ten_hoi_dong": "HD hai chủ tịch",
            "thanh_vien": [
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 422, resp.text

    # GV lặp lại -> 422
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(bomon),
        json={
            **base_payload,
            "ten_hoi_dong": "HD trùng GV",
            "thanh_vien": [
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "UY_VIEN"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 422, resp.text

    # hội đồng chứa GVHD của SV -> tạo được (chưa xếp lịch), nhưng xếp lịch vào đó -> 409, không tạo lich_bao_ve
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(bomon),
        json={
            "ten_hoi_dong": "HD chứa GVHD",
            "ngay_bao_ve": "2026-10-01",
            "gio_bao_ve": "08:00",
            "phong": "P302",
            "thanh_vien": [
                {"giang_vien_id": gv.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "THU_KY"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    committee_with_gvhd_id = resp.json()["id"]

    resp = client.post(
        f"/api/defense/committees/{committee_with_gvhd_id}/schedules",
        headers=auth_headers(bomon),
        json={"de_tai_id": topic.id},
    )
    assert resp.status_code == 409, resp.text
    assert db.execute(select(func.count()).select_from(LichBaoVe)).scalar_one() == 0

    # hội đồng hợp lệ (không có GVHD) -> 201, mỗi thành viên có thông báo HOI_DONG_PHAN_CONG
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(bomon),
        json={
            "ten_hoi_dong": "HD hợp lệ",
            "ngay_bao_ve": "2026-10-01",
            "gio_bao_ve": "09:00",
            "phong": "P303",
            "thanh_vien": [
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "THU_KY"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    valid_committee_id = resp.json()["id"]

    notif = client.get("/api/notifications", headers=auth_headers(gv1)).json()
    assert any(n["loai"] == "HOI_DONG_PHAN_CONG" for n in notif["items"])

    eligible = client.get("/api/defense/eligible-students", headers=auth_headers(bomon)).json()
    assert any(item["de_tai_id"] == topic.id for item in eligible)

    # xếp SV -> 201 thu_tu 1, SV có thông báo LICH_BAO_VE
    resp = client.post(
        f"/api/defense/committees/{valid_committee_id}/schedules",
        headers=auth_headers(bomon),
        json={"de_tai_id": topic.id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["thu_tu"] == 1

    sv_notif = client.get("/api/notifications", headers=auth_headers(sv)).json()
    assert any(n["loai"] == "LICH_BAO_VE" for n in sv_notif["items"])

    eligible_after = client.get("/api/defense/eligible-students", headers=auth_headers(bomon)).json()
    assert all(item["de_tai_id"] != topic.id for item in eligible_after)

    # xếp vào một hội đồng khác (không chứa GVHD) -> 409 (đã có lịch)
    resp = client.post(
        "/api/defense/committees",
        headers=auth_headers(bomon),
        json={
            "ten_hoi_dong": "HD hợp lệ 2",
            "ngay_bao_ve": "2026-10-01",
            "gio_bao_ve": "10:00",
            "phong": "P304",
            "thanh_vien": [
                {"giang_vien_id": gv1.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "THU_KY"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    second_committee_id = resp.json()["id"]

    resp = client.post(
        f"/api/defense/committees/{second_committee_id}/schedules",
        headers=auth_headers(bomon),
        json={"de_tai_id": topic.id},
    )
    assert resp.status_code == 409, resp.text

    # PUT thêm GVHD của SV đã xếp lịch vào hội đồng valid_committee_id -> 409
    resp = client.put(
        f"/api/defense/committees/{valid_committee_id}",
        headers=auth_headers(bomon),
        json={
            "ten_hoi_dong": "HD hợp lệ",
            "ngay_bao_ve": "2026-10-01",
            "gio_bao_ve": "09:00",
            "phong": "P303",
            "thanh_vien": [
                {"giang_vien_id": gv.giang_vien_id, "vai_tro": "CHU_TICH"},
                {"giang_vien_id": gv2.giang_vien_id, "vai_tro": "THU_KY"},
                {"giang_vien_id": gv3.giang_vien_id, "vai_tro": "UY_VIEN"},
            ],
        },
    )
    assert resp.status_code == 409, resp.text


def test_scoring_is_committee_scoped_and_finalize_is_one_way(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    """UC4.3–4.5 + UC5.2 (DEFN-03/04, REPO-01, D-06/D-07): chỉ thành viên hội
    đồng chấm/xem báo cáo cuối; chốt chỉ khi đủ điểm, một chiều, tự lưu kho
    và đẩy index (stub) sau commit; SV chỉ thấy điểm sau khi chốt."""
    from datetime import time, timedelta

    from app.core.timeutil import today_vn
    from app.models.bao_ve import CHU_TICH, THU_KY, UY_VIEN, HoiDong, ThanhVienHoiDong
    from app.models.kho import DoAnKho
    from app.services.ai_client import INGEST_LOG

    bomon = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)
    gvhd = make_account(VaiTro.GIANG_VIEN)
    gv_a = make_account(VaiTro.GIANG_VIEN)
    gv_b = make_account(VaiTro.GIANG_VIEN)
    gv_c = make_account(VaiTro.GIANG_VIEN)
    gv_d = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gvhd)
    _approve_outline(db, topic)

    resp = client.post(
        f"/api/defense/final-reports/{topic.id}",
        headers=auth_headers(sv),
        files={"file": ("bao-cao.pdf", pdf_bytes(["Final report for scoring test"]), _PDF_CT)},
    )
    assert resp.status_code == 202, resp.text
    final_doc_id = resp.json()["phien_ban"][0]["tai_lieu"]["id"]

    def _committee(ten, ngay, members):
        hd = HoiDong(ten_hoi_dong=ten, ngay_bao_ve=ngay, gio_bao_ve=time(8, 0), phong="P302")
        db.add(hd)
        db.flush()
        roles = [CHU_TICH, THU_KY, UY_VIEN]
        for idx, gv in enumerate(members):
            db.add(ThanhVienHoiDong(hoi_dong_id=hd.id, giang_vien_id=gv.giang_vien_id, vai_tro=roles[idx]))
        db.flush()
        return hd

    today = today_vn()
    hd1 = _committee("Hội đồng chấm 1", today, [gv_a, gv_b, gv_c])
    _committee("Hội đồng chấm 2", today, [gv_d, gv_b, gv_c])
    lich = LichBaoVe(hoi_dong_id=hd1.id, de_tai_id=topic.id, sinh_vien_id=sv.sinh_vien_id, thu_tu=1)
    db.add(lich)
    db.commit()
    lich_id = lich.id

    def _score(account, diem, nhan_xet="Trình bày rõ ràng"):
        return client.put(
            f"/api/defense/schedules/{lich_id}/score",
            headers=auth_headers(account),
            json={"diem": diem, "nhan_xet": nhan_xet},
        )

    # GV D (hội đồng khác) -> 403 trên cả 4 đường; C (thành viên) tải được
    assert client.get(f"/api/defense/schedules/{lich_id}", headers=auth_headers(gv_d)).status_code == 403
    assert _score(gv_d, 7.0).status_code == 403
    assert client.get(f"/api/documents/{final_doc_id}/download", headers=auth_headers(gv_d)).status_code == 403
    assert client.get(f"/api/documents/{final_doc_id}/check", headers=auth_headers(gv_d)).status_code == 403
    assert client.get(f"/api/documents/{final_doc_id}/download", headers=auth_headers(gv_c)).status_code == 200
    detail = client.get(f"/api/defense/schedules/{lich_id}", headers=auth_headers(gv_c))
    assert detail.status_code == 200, detail.text
    assert detail.json()["co_the_cham"] is True

    # sai vai trò -> 403; điểm ngoài khoảng / quá 1 chữ số thập phân -> 422
    assert _score(sv, 8.0).status_code == 403
    assert _score(bomon, 8.0).status_code == 403
    assert _score(gv_a, 10.5).status_code == 422
    assert _score(gv_a, 8.25).status_code == 422

    assert _score(gv_a, 8.0).status_code == 200
    assert _score(gv_b, 8.5).status_code == 200

    # chốt khi mới 2/3 -> 409, chưa có bản ghi kho, SV thấy lịch nhưng không thấy điểm
    resp = client.post(f"/api/defense/schedules/{lich_id}/finalize", headers=auth_headers(bomon))
    assert resp.status_code == 409 and "2/3" in resp.json()["detail"], resp.text
    assert db.execute(select(func.count()).select_from(DoAnKho)).scalar_one() == 0
    me = client.get("/api/defense/me", headers=auth_headers(sv)).json()
    assert me["lich"]["ten_hoi_dong"] == "Hội đồng chấm 1" and me["ket_qua"] is None

    ingest_before = len(INGEST_LOG)
    assert _score(gv_c, 9.0).status_code == 200
    resp = client.post(f"/api/defense/schedules/{lich_id}/finalize", headers=auth_headers(bomon))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["lich"]["da_chot"] is True and body["lich"]["diem_trung_binh"] == 8.5

    db.rollback()  # kết thúc snapshot REPEATABLE READ của phiên test trước khi đọc lại
    rows = db.execute(select(DoAnKho)).scalars().all()
    assert len(rows) == 1
    kho = rows[0]
    assert (kho.id, kho.nguon, kho.khoa, kho.ten_de_tai) == (body["do_an_kho_id"], "HE_THONG", "KTEST", topic.ten_de_tai)
    assert kho.sinh_vien_id == sv.sinh_vien_id and kho.ma_so_sinh_vien and kho.ho_ten_sinh_vien
    assert kho.giang_vien_id == gvhd.giang_vien_id and str(kho.diem) == "8.50" and kho.tu_khoa is None
    assert kho.trang_thai_index == "DA_INDEX"
    assert len(INGEST_LOG) == ingest_before + 1 and INGEST_LOG[-1]["ref_id"] == kho.id

    notif = client.get("/api/notifications", headers=auth_headers(sv)).json()
    assert any(n["loai"] == "KET_QUA_BAO_VE" for n in notif["items"])
    me = client.get("/api/defense/me", headers=auth_headers(sv)).json()
    assert me["ket_qua"]["diem_trung_binh"] == 8.5

    # một chiều: chốt lại / sửa điểm sau chốt -> 409
    assert client.post(f"/api/defense/schedules/{lich_id}/finalize", headers=auth_headers(bomon)).status_code == 409
    assert _score(gv_a, 9.5).status_code == 409

    # hội đồng ngày mai: thành viên chấm -> 409 (chưa đến ngày bảo vệ)
    sv2 = make_account(VaiTro.SINH_VIEN)
    topic2 = make_assigned_topic(sv2, gvhd)
    hd3 = _committee("Hội đồng ngày mai", today + timedelta(days=1), [gv_a, gv_b, gv_c])
    lich2 = LichBaoVe(hoi_dong_id=hd3.id, de_tai_id=topic2.id, sinh_vien_id=sv2.sinh_vien_id, thu_tu=1)
    db.add(lich2)
    db.commit()
    resp = client.put(
        f"/api/defense/schedules/{lich2.id}/score", headers=auth_headers(gv_a), json={"diem": 8.0}
    )
    assert resp.status_code == 409, resp.text
