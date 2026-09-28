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
