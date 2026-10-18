"""Góp ý GVHD: định hướng thay lĩnh vực, duyệt đề cương hai cấp (GVHD -> Lãnh
đạo bộ môn), kiểm tra tên file/định hướng, phê duyệt kèm file đã ký số và
thư mục đề cương ký số của đợt."""
import io
import zipfile

from pdf_sign_helper import sign_pdf
from sqlalchemy import select

from app.core.roles import VaiTro
from app.models.de_cuong import DeCuong
from app.models.dinh_huong import DinhHuong
from app.models.tai_khoan import SinhVien
from app.services import outline_checks

_PDF_CT = "application/pdf"


def _dinh_huong(db, ma="H01", ten="Phát triển ứng dụng") -> DinhHuong:
    item = DinhHuong(ma=ma, ten=ten, hoat_dong=True)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _setup(db, make_account, make_assigned_topic, ma_dinh_huong="H01"):
    dh = _dinh_huong(db, ma=ma_dinh_huong)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    bm = make_account(VaiTro.BO_MON)
    topic = make_assigned_topic(sv, gv)
    topic.dinh_huong_id = dh.id
    db.commit()
    hs = db.get(SinhVien, sv.sinh_vien_id)
    ten_file = f"{ma_dinh_huong}.{hs.ma_so_sinh_vien}.{hs.ho_ten}.{hs.lop}.pdf"
    return sv, gv, bm, topic, ten_file


def _submit(client, headers, topic_id, name, content, ghi_chu=None):
    data = {"ghi_chu": ghi_chu} if ghi_chu else None
    resp = client.post(
        f"/api/outlines/{topic_id}/submit",
        headers=headers,
        files={"file": (name, content, _PDF_CT)},
        data=data,
    )
    assert resp.status_code == 202, resp.text
    return resp.json()


def _gv_approve(client, headers, topic_id, doc_id):
    resp = client.post(
        f"/api/outlines/{topic_id}/review",
        headers=headers,
        json={"tai_lieu_do_an_id": doc_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_ten_file_parsing():
    tach = outline_checks.tach_ten_file("H01.DTC235200036.Nguyễn Thị Mai Anh.CN CNTTK22A.docx")
    assert tach is not None
    assert (tach.ma_dinh_huong, tach.mssv, tach.ho_ten, tach.lop) == (
        "H01",
        "DTC235200036",
        "Nguyễn Thị Mai Anh",
        "CN CNTTK22A",
    )
    assert outline_checks.tach_ten_file("de-cuong.pdf") is None
    assert outline_checks.tach_ten_file("H1.DTC1.Ten.Lop.pdf") is None
    assert outline_checks.tach_ten_file("H01.DTC1.Ten.Lop.txt") is None


def test_signature_detection(pdf_bytes):
    base = pdf_bytes(["Signed outline"])
    assert outline_checks.doc_chu_ky_so(base) is None

    signed = sign_pdf(base, signer="Tran Van A")
    chu_ky = outline_checks.doc_chu_ky_so(signed)
    assert chu_ky is not None
    assert chu_ky.nguoi_ky == "Tran Van A"
    assert chu_ky.phu_toan_bo_file is True
    # /M (D:20261018093000+07'00') -> 02:30 UTC
    assert chu_ky.thoi_diem_ky is not None
    assert (chu_ky.thoi_diem_ky.hour, chu_ky.thoi_diem_ky.minute) == (2, 30)

    tampered = signed + b"\n% edited after signing\n"
    assert outline_checks.doc_chu_ky_so(tampered).phu_toan_bo_file is False


def test_dinh_huong_catalog_rbac(client, make_account, auth_headers):
    bm = make_account(VaiTro.BO_MON)
    gv = make_account(VaiTro.GIANG_VIEN)

    resp = client.post(
        "/api/dinh-huong", headers=auth_headers(gv), json={"ma": "H05", "ten": "Thử"}
    )
    assert resp.status_code == 403

    resp = client.post(
        "/api/dinh-huong", headers=auth_headers(bm), json={"ma": "h05", "ten": "Mạng máy tính"}
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["ma"] == "H05"

    resp = client.post(
        "/api/dinh-huong", headers=auth_headers(bm), json={"ma": "H05", "ten": "Trùng"}
    )
    assert resp.status_code == 409

    resp = client.post(
        "/api/dinh-huong", headers=auth_headers(bm), json={"ma": "X1", "ten": "Sai mã"}
    )
    assert resp.status_code == 422

    resp = client.put(
        f"/api/dinh-huong/{created['id']}",
        headers=auth_headers(bm),
        json={"ma": "H05", "ten": "Mạng máy tính", "hoat_dong": False},
    )
    assert resp.status_code == 200 and resp.json()["hoat_dong"] is False

    all_items = client.get("/api/dinh-huong", headers=auth_headers(gv)).json()
    assert any(i["ma"] == "H05" for i in all_items)
    active = client.get("/api/dinh-huong?chi_hoat_dong=true", headers=auth_headers(gv)).json()
    assert all(i["ma"] != "H05" for i in active)


def test_two_level_flow_and_signed_folder(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv, gv, bm, topic, ten_file = _setup(db, make_account, make_assigned_topic)
    sv_h, gv_h, bm_h = auth_headers(sv), auth_headers(gv), auth_headers(bm)

    body = _submit(
        client, sv_h, topic.id, ten_file, pdf_bytes(["Outline v1"]), ghi_chu="Em gửi bản đầu"
    )
    doc_id = body["phien_ban"][0]["tai_lieu"]["id"]
    detail = client.get(f"/api/outlines/{topic.id}", headers=gv_h).json()
    checks = {c["ma"]: c for c in detail["kiem_tra_nop"]}
    assert checks["TEN_FILE"]["dat"] is True, checks
    assert checks["DINH_HUONG"]["dat"] is True, checks
    assert detail["dinh_huong"]["ma"] == "H01"

    # Bộ môn chưa duyệt được khi GVHD chưa nộp lên.
    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/return", headers=bm_h, json={"nhan_xet": "x"}
    )
    assert resp.status_code == 409

    approved = _gv_approve(client, gv_h, topic.id, doc_id)
    assert approved["trang_thai"] == "GVHD_DA_DUYET"

    # Chỉ GVHD của đề tài nộp lên Bộ môn.
    resp = client.post(f"/api/outlines/{topic.id}/forward", headers=bm_h)
    assert resp.status_code == 403
    resp = client.post(f"/api/outlines/{topic.id}/forward", headers=gv_h)
    assert resp.status_code == 200, resp.text
    assert resp.json()["trang_thai"] == "CHO_BO_MON_DUYET"
    assert resp.json()["nop_bo_mon_luc"] is not None

    counts = client.get("/api/outlines/counts", headers=bm_h).json()
    assert counts["theo_trang_thai"].get("CHO_BO_MON_DUYET") == 1
    notifs = client.get("/api/notifications", headers=bm_h).json()["items"]
    assert any(n["loai"] == "DE_CUONG_NOP_BO_MON" for n in notifs)

    # Phê duyệt bằng PDF chưa ký -> 422; bản ký đã bị sửa -> 422.
    unsigned = pdf_bytes(["Outline v1 da ky"])
    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/approve",
        headers=bm_h,
        files={"file": (ten_file, unsigned, _PDF_CT)},
    )
    assert resp.status_code == 422
    assert "chữ ký số" in resp.json()["detail"]
    signed = sign_pdf(unsigned, signer="Pham Bo Mon")
    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/approve",
        headers=bm_h,
        files={"file": (ten_file, signed + b"\n%x\n", _PDF_CT)},
    )
    assert resp.status_code == 422

    # GVHD không được phê duyệt thay Bộ môn.
    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/approve",
        headers=gv_h,
        files={"file": (ten_file, signed, _PDF_CT)},
    )
    assert resp.status_code == 403

    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/approve",
        headers=bm_h,
        files={"file": (ten_file, signed, _PDF_CT)},
        data={"nhan_xet": "Đã ký số"},
    )
    assert resp.status_code == 200, resp.text
    final = resp.json()
    assert final["trang_thai"] == "DA_DUYET"
    review = final["luot_duyet_bo_mon"][0]
    assert review["ket_qua"] == "DA_DUYET"
    assert review["nguoi_ky"] == "Pham Bo Mon"
    assert review["tai_lieu_ky_so"]["loai"] == "DE_CUONG_KY_SO"

    sv_notifs = client.get("/api/notifications", headers=sv_h).json()["items"]
    assert any(n["loai"] == "DE_CUONG_BO_MON_DUYET" for n in sv_notifs)

    # Thư mục đề cương ký số của đợt: chỉ Bộ môn tải, ZIP chứa đúng file đã ký.
    resp = client.get(
        f"/api/outlines/export-signed?dot_do_an_id={topic.dot_do_an_id}", headers=gv_h
    )
    assert resp.status_code == 403
    resp = client.get(
        f"/api/outlines/export-signed?dot_do_an_id={topic.dot_do_an_id}", headers=bm_h
    )
    assert resp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        assert zf.namelist() == [ten_file]
        assert zf.read(ten_file) == signed


def test_forward_blocked_by_wrong_file_name(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv, gv, _bm, topic, _ten_file = _setup(db, make_account, make_assigned_topic)
    body = _submit(client, auth_headers(sv), topic.id, "de-cuong-cua-em.pdf", pdf_bytes(["v1"]))
    _gv_approve(client, auth_headers(gv), topic.id, body["phien_ban"][0]["tai_lieu"]["id"])

    resp = client.post(f"/api/outlines/{topic.id}/forward", headers=auth_headers(gv))
    assert resp.status_code == 409
    assert "Tên file" in resp.json()["detail"]
    db.rollback()  # bỏ snapshot REPEATABLE READ cũ của phiên test
    de_cuong = db.execute(select(DeCuong).where(DeCuong.de_tai_id == topic.id)).scalar_one()
    assert de_cuong.trang_thai == "GVHD_DA_DUYET"


def test_forward_blocked_by_dinh_huong_mismatch(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv, gv, _bm, topic, ten_file = _setup(db, make_account, make_assigned_topic)
    _dinh_huong(db, ma="H02", ten="Hệ thống AI và ứng dụng")
    wrong = "H02" + ten_file[3:]
    body = _submit(client, auth_headers(sv), topic.id, wrong, pdf_bytes(["v1"]))
    _gv_approve(client, auth_headers(gv), topic.id, body["phien_ban"][0]["tai_lieu"]["id"])

    resp = client.post(f"/api/outlines/{topic.id}/forward", headers=auth_headers(gv))
    assert resp.status_code == 409
    assert "Định hướng" in resp.json()["detail"]


def test_bo_mon_return_then_resubmit(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv, gv, bm, topic, ten_file = _setup(db, make_account, make_assigned_topic)
    sv_h, gv_h, bm_h = auth_headers(sv), auth_headers(gv), auth_headers(bm)
    body = _submit(client, sv_h, topic.id, ten_file, pdf_bytes(["v1"]))
    _gv_approve(client, gv_h, topic.id, body["phien_ban"][0]["tai_lieu"]["id"])
    assert client.post(f"/api/outlines/{topic.id}/forward", headers=gv_h).status_code == 200

    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/return", headers=bm_h, json={"nhan_xet": ""}
    )
    assert resp.status_code == 422
    resp = client.post(
        f"/api/outlines/{topic.id}/bo-mon/return",
        headers=bm_h,
        json={"nhan_xet": "Mục tiêu chưa khớp định hướng"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["trang_thai"] == "YEU_CAU_SUA"
    assert resp.json()["ket_qua_bo_mon"] == "TRA_LAI"

    returned = client.get("/api/outlines?trang_thai=BO_MON_TRA_LAI", headers=bm_h).json()
    assert [i["de_tai_id"] for i in returned["items"]] == [topic.id]
    assert client.get("/api/outlines/counts", headers=bm_h).json()["bo_mon_tra_lai"] == 1
    gv_notifs = client.get("/api/notifications", headers=gv_h).json()["items"]
    assert any(n["loai"] == "DE_CUONG_BO_MON_TRA_LAI" for n in gv_notifs)

    # SV nộp lại -> quay về chờ GVHD, kết quả Bộ môn cũ được xóa khỏi tab Từ chối.
    resubmitted = _submit(client, sv_h, topic.id, ten_file, pdf_bytes(["v2"]))
    assert resubmitted["trang_thai"] == "CHO_DUYET"
    assert resubmitted["ket_qua_bo_mon"] is None
    assert client.get("/api/outlines/counts", headers=bm_h).json()["bo_mon_tra_lai"] == 0


def test_outline_search_and_note(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv, _gv, bm, topic, ten_file = _setup(db, make_account, make_assigned_topic)
    _submit(client, auth_headers(sv), topic.id, ten_file, pdf_bytes(["v1"]), ghi_chu="Ghi chú")
    hs = db.get(SinhVien, sv.sinh_vien_id)

    found = client.get(
        f"/api/outlines?q={hs.ma_so_sinh_vien}", headers=auth_headers(bm)
    ).json()
    assert [i["de_tai_id"] for i in found["items"]] == [topic.id]
    none = client.get("/api/outlines?q=khongcoai", headers=auth_headers(bm)).json()
    assert none["total"] == 0


def test_topic_dinh_huong_and_attachment(
    client, make_account, auth_headers, assign_gvhd, pdf_bytes, db
):
    from datetime import date

    from app.models.dot_do_an import DANG_MO, DotDoAn

    dh = _dinh_huong(db)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    gv_other = make_account(VaiTro.GIANG_VIEN)
    cohort = DotDoAn(
        ten_dot="Đợt định hướng", khoa="K22", nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 9, 1), trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    assign_gvhd(sv, gv, cohort.id)

    resp = client.post(
        "/api/topics",
        headers=auth_headers(gv),
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Xây dựng hệ thống theo dõi định hướng",
            "dinh_huong_id": 99999,
            "sinh_vien_id": sv.sinh_vien_id,
            "gui": False,
        },
    )
    assert resp.status_code == 422

    resp = client.post(
        "/api/topics",
        headers=auth_headers(gv),
        json={
            "dot_do_an_id": cohort.id,
            "ten_de_tai": "Xây dựng hệ thống theo dõi định hướng",
            "dinh_huong_id": dh.id,
            "sinh_vien_id": sv.sinh_vien_id,
            "gui": True,
        },
    )
    assert resp.status_code == 201, resp.text
    topic = resp.json()
    assert topic["dinh_huong"]["ma"] == "H01"
    assert topic["ngay_giao"] is not None

    listed = client.get(f"/api/topics?dinh_huong_id={dh.id}", headers=auth_headers(gv)).json()
    assert [t["id"] for t in listed["items"]] == [topic["id"]]
    assert listed["items"][0]["dinh_huong"]["ma"] == "H01"

    attach = pdf_bytes(["Mo ta de tai"])
    resp = client.post(
        f"/api/topics/{topic['id']}/attachment",
        headers=auth_headers(gv_other),
        files={"file": ("mo-ta.pdf", attach, _PDF_CT)},
    )
    assert resp.status_code == 403
    resp = client.post(
        f"/api/topics/{topic['id']}/attachment",
        headers=auth_headers(gv),
        files={"file": ("mo-ta.pdf", attach, _PDF_CT)},
    )
    assert resp.status_code == 200, resp.text
    tep = resp.json()["tep_dinh_kem"]
    assert tep["ten_goc"] == "mo-ta.pdf"

    resp = client.get(f"/api/documents/{tep['id']}/download", headers=auth_headers(sv))
    assert resp.status_code == 200
    assert resp.content == attach


def test_progress_dashboard_outline_filters(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    from app.models.de_tai import DA_PHAN_CONG, GIANG_VIEN, DeTai

    sv1, gv, bm, topic1, ten_file = _setup(db, make_account, make_assigned_topic)
    sv2 = make_account(VaiTro.SINH_VIEN)
    topic2 = DeTai(
        dot_do_an_id=topic1.dot_do_an_id,
        giang_vien_id=gv.giang_vien_id,
        sinh_vien_id=sv2.sinh_vien_id,
        ten_de_tai="Đề tài thứ hai chưa nộp đề cương",
        trang_thai=DA_PHAN_CONG,
        loai_nguoi_de_xuat=GIANG_VIEN,
    )
    db.add(topic2)
    db.commit()
    _submit(client, auth_headers(sv1), topic1.id, ten_file, pdf_bytes(["v1"]))

    base = f"/api/progress/dashboard?dot_do_an_id={topic1.dot_do_an_id}"
    data = client.get(base, headers=auth_headers(bm)).json()
    assert (data["tong_sv"], data["da_nop_de_cuong"], data["chua_hoan_thanh"]) == (2, 1, 2)
    states = {r["de_tai"]["id"]: r["trang_thai_de_cuong"] for r in data["items"]}
    assert states == {topic1.id: "CHO_DUYET", topic2.id: "CHUA_NOP"}

    def ids(query: str) -> list[int]:
        resp = client.get(base + query, headers=auth_headers(bm))
        assert resp.status_code == 200, resp.text
        return [r["de_tai"]["id"] for r in resp.json()["items"]]

    assert ids("&loc_de_cuong=DA_NOP") == [topic1.id]
    assert ids("&loc_de_cuong=CHO_DUYET") == [topic1.id]
    assert ids("&loc_de_cuong=CHUA_NOP") == [topic2.id]
    assert ids("&q=thứ hai") == [topic2.id]


def test_topic_history_and_submissions(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    sv, gv, _bm, topic, ten_file = _setup(db, make_account, make_assigned_topic)
    other = make_account(VaiTro.SINH_VIEN)
    body = _submit(client, auth_headers(sv), topic.id, ten_file, pdf_bytes(["v1"]))
    _gv_approve(client, auth_headers(gv), topic.id, body["phien_ban"][0]["tai_lieu"]["id"])

    resp = client.get(f"/api/topics/{topic.id}/history", headers=auth_headers(other))
    assert resp.status_code == 403
    events = client.get(f"/api/topics/{topic.id}/history", headers=auth_headers(sv)).json()
    noi_dung = [e["noi_dung"] for e in events]
    assert noi_dung[0].startswith("GVHD duyệt đề cương phiên bản 1")
    assert "Nộp đề cương phiên bản 1" in noi_dung

    resp = client.get("/api/dashboard/sinh-vien/lich-su-nop", headers=auth_headers(gv))
    assert resp.status_code == 403
    rows = client.get("/api/dashboard/sinh-vien/lich-su-nop", headers=auth_headers(sv)).json()
    outline_rows = [r for r in rows if r["loai"] == "DE_CUONG"]
    assert outline_rows == [
        {
            "loai": "DE_CUONG",
            "noi_dung": "Nộp đề cương (phiên bản 1)",
            "thoi_diem_nop": outline_rows[0]["thoi_diem_nop"],
            "han_cuoi": None,
            "trang_thai": "GVHD_DA_DUYET",
            "trang_thai_label": "GVHD đã duyệt",
            "tai_lieu_id": body["phien_ban"][0]["tai_lieu"]["id"],
        }
    ]
    assert rows[0]["loai"] == "DE_TAI"
