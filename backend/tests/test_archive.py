"""UC5.1/UC5.3/UC5.4 — kho đồ án (REPO-02, REPO-03, D-07): mọi vai trò tra cứu,
chỉ Bộ môn ghi/xóa/index lại/import CSV; import CSV thành công một phần kèm
số dòng + lý do; mọi bản ghi mới/sửa được đẩy sang seam AI sau commit."""
import unicodedata
from decimal import Decimal

from sqlalchemy import select

from app.core.roles import VaiTro
from app.models.kho import CHUA_INDEX, DA_INDEX, IMPORT, DoAnKho


def _seed_record(db, **overrides) -> int:
    values = dict(
        khoa="K20",
        ten_de_tai="Hệ thống quản lý thư viện số",
        tu_khoa="thư viện, quản lý",
        diem=Decimal("8.00"),
        nguon=IMPORT,
        trang_thai_index=DA_INDEX,
    )
    values.update(overrides)
    kho = DoAnKho(**values)
    db.add(kho)
    db.commit()
    return kho.id


def test_archive_writes_are_bomon_only(client, make_account, auth_headers, db):
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    kho_id = _seed_record(db)
    body = {"khoa": "K21", "ten_de_tai": "Tên đề tài bị sửa trái phép"}
    csv_bytes = "khoa,ten_de_tai\nK21,Đề tài import trái phép\n".encode("utf-8")

    for account in (sv, gv):
        h = auth_headers(account)
        assert client.post("/api/archive", headers=h, json=body).status_code == 403
        assert client.put(f"/api/archive/{kho_id}", headers=h, json=body).status_code == 403
        assert client.delete(f"/api/archive/{kho_id}", headers=h).status_code == 403
        assert client.post(f"/api/archive/{kho_id}/reindex", headers=h).status_code == 403
        resp = client.post(
            "/api/archive/import", headers=h, files={"file": ("k.csv", csv_bytes, "text/csv")}
        )
        assert resp.status_code == 403
        assert client.get("/api/archive", headers=h).status_code == 200
        assert client.get(f"/api/archive/{kho_id}", headers=h).status_code == 200
        assert client.get("/api/archive/khoa", headers=h).status_code == 200

    db.rollback()
    rows = db.execute(select(DoAnKho)).scalars().all()
    assert len(rows) == 1
    assert (rows[0].khoa, rows[0].ten_de_tai, rows[0].trang_thai_index) == (
        "K20",
        "Hệ thống quản lý thư viện số",
        DA_INDEX,
    )


def test_csv_import_partial_success_search_and_reindex(
    client, make_account, auth_headers, db, monkeypatch
):
    from app.services.ai_client import INGEST_LOG, AiClientStub, AiServiceError

    bomon = make_account(VaiTro.BO_MON)
    gv = make_account(VaiTro.GIANG_VIEN)
    from app.models.tai_khoan import GiangVien

    gv_ma = db.get(GiangVien, gv.giang_vien_id).ma_giang_vien
    title_a_nfc = "Ứng dụng học sâu nhận diện chữ viết tay tiếng Việt"
    title_a_nfd = unicodedata.normalize("NFD", title_a_nfc)
    assert title_a_nfd != title_a_nfc

    csv_text = (
        "khoa,ten_de_tai,ma_so_sinh_vien,ho_ten_sinh_vien,ma_giang_vien,tu_khoa,diem,cot_la\n"
        f'K19,{title_a_nfd},DTC1500001,Nguyễn Văn A,{gv_ma},"học sâu, OCR","8,5",x\n'
        "K18,Website bán hàng trực tuyến,,,,,,\n"
        "K19,,,,,,,\n"
        "K19,Hệ thống điểm danh bằng khuôn mặt,,,GV_KHONG_TON_TAI,,,\n"
        f"K19,{title_a_nfc},,,,,,\n"
    )
    ingest_before = len(INGEST_LOG)
    resp = client.post(
        "/api/archive/import",
        headers=auth_headers(bomon),
        files={"file": ("khoa-cu.csv", b"\xef\xbb\xbf" + csv_text.encode("utf-8"), "text/csv")},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert (result["tong_dong"], result["thanh_cong"]) == (5, 2)
    loi = {e["dong"]: e["ly_do"] for e in result["loi"]}
    assert sorted(loi) == [4, 5, 6]
    assert "Thiếu tên đề tài" in loi[4]
    assert "Không tìm thấy giảng viên mã" in loi[5]
    assert "Trùng bản ghi" in loi[6]

    db.rollback()
    rows = {r.ten_de_tai: r for r in db.execute(select(DoAnKho)).scalars().all()}
    assert set(rows) == {title_a_nfc, "Website bán hàng trực tuyến"}
    rec_a = rows[title_a_nfc]
    assert rec_a.diem == Decimal("8.50") and rec_a.giang_vien_id == gv.giang_vien_id
    assert rec_a.nguon == IMPORT and rec_a.tu_khoa == "học sâu, OCR"
    assert all(r.trang_thai_index == DA_INDEX for r in rows.values())
    assert len(INGEST_LOG) == ingest_before + 2

    h = auth_headers(bomon)
    found = client.get("/api/archive", headers=h, params={"q": "chữ viết tay"}).json()
    assert [i["id"] for i in found["items"]] == [rec_a.id]
    by_khoa = client.get("/api/archive", headers=h, params={"khoa": "K18"}).json()
    assert [i["ten_de_tai"] for i in by_khoa["items"]] == ["Website bán hàng trực tuyến"]
    by_gv = client.get("/api/archive", headers=h, params={"giang_vien_id": gv.giang_vien_id}).json()
    assert [i["id"] for i in by_gv["items"]] == [rec_a.id]
    assert client.get("/api/archive", headers=h, params={"q": "%"}).json()["total"] == 0

    def _boom(self, ref_id, loai, text):
        raise AiServiceError("mô phỏng AI lỗi")

    monkeypatch.setattr(AiClientStub, "ingest", _boom)
    resp = client.put(
        f"/api/archive/{rec_a.id}",
        headers=h,
        json={"khoa": "K19", "ten_de_tai": title_a_nfc, "giang_vien_id": gv.giang_vien_id,
              "tu_khoa": "học sâu, OCR, nhận dạng", "diem": 8.5},
    )
    assert resp.status_code == 200, resp.text
    assert client.get(f"/api/archive/{rec_a.id}", headers=h).json()["trang_thai_index"] == CHUA_INDEX

    monkeypatch.undo()
    assert client.post(f"/api/archive/{rec_a.id}/reindex", headers=h).status_code == 202
    assert client.get(f"/api/archive/{rec_a.id}", headers=h).json()["trang_thai_index"] == DA_INDEX

    assert client.delete(f"/api/archive/{rec_a.id}", headers=h).status_code == 204
    assert client.get(f"/api/archive/{rec_a.id}", headers=h).status_code == 404
