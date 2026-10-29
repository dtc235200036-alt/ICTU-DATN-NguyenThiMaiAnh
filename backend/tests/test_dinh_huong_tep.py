"""0019: Bộ môn tải lên/thay/gỡ file PDF mô tả định hướng; SV, GV, Bộ môn xem
và tải về."""
import pytest
from sqlalchemy.orm import Session

from app.core.roles import VaiTro
from app.models.dinh_huong import DinhHuong
from app.services import documents

_PDF_CT = "application/pdf"
_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _dinh_huong(db, ma="H01", ten="Phát triển ứng dụng", hoat_dong=True) -> DinhHuong:
    item = DinhHuong(ma=ma, ten=ten, hoat_dong=hoat_dong)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _upload(client, headers, dinh_huong_id, name, content, content_type=_PDF_CT):
    return client.post(
        f"/api/dinh-huong/{dinh_huong_id}/tep",
        headers=headers,
        files={"file": (name, content, content_type)},
    )


def _ten_luu_tru(db, dinh_huong_id) -> str | None:
    # Kết thúc transaction (snapshot REPEATABLE READ) của session test và bỏ
    # giá trị đã nạp để đọc được dữ liệu API vừa commit.
    db.rollback()
    db.expire_all()
    return db.get(DinhHuong, dinh_huong_id).tep_ten_luu_tru


def test_bo_mon_upload_and_everyone_downloads(client, db, make_account, auth_headers, pdf_bytes):
    dh = _dinh_huong(db)
    bm = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)

    listed = client.get("/api/dinh-huong", headers=auth_headers(sv)).json()
    assert listed[0]["tep"] is None

    content = pdf_bytes(["Mo ta dinh huong H01"])
    resp = _upload(client, auth_headers(bm), dh.id, "Mô tả H01.pdf", content)
    assert resp.status_code == 200, resp.text
    tep = resp.json()["tep"]
    assert tep["ten_goc"] == "Mô tả H01.pdf"
    assert tep["kich_thuoc"] == len(content)
    assert tep["cap_nhat_luc"].endswith("+00:00")

    ten_luu_tru = _ten_luu_tru(db, dh.id)
    assert ten_luu_tru.startswith("DINH_HUONG/") and ten_luu_tru.endswith(".pdf")
    assert documents.storage_path(ten_luu_tru).read_bytes() == content

    listed = client.get("/api/dinh-huong", headers=auth_headers(sv)).json()
    assert listed[0]["tep"]["ten_goc"] == "Mô tả H01.pdf"

    for account in (sv, gv, bm):
        resp = client.get(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(account))
        assert resp.status_code == 200
        assert resp.headers["content-type"] == _PDF_CT
        assert resp.headers["cache-control"] == "no-cache"
        assert resp.content == content


def test_upload_rejects_non_pdf_and_non_bo_mon(
    client, db, make_account, auth_headers, pdf_bytes, docx_bytes
):
    dh = _dinh_huong(db)
    bm = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)

    resp = _upload(client, auth_headers(bm), dh.id, "mo-ta.docx", docx_bytes(["Mô tả"]), _DOCX_CT)
    assert resp.status_code == 422
    assert resp.json()["detail"] == "File mô tả định hướng phải là PDF"
    # Đuôi .pdf nhưng nội dung không phải PDF -> kiểm tra magic bytes như đề cương.
    resp = _upload(client, auth_headers(bm), dh.id, "gia.pdf", docx_bytes(["Mô tả"]))
    assert resp.status_code == 422
    assert _ten_luu_tru(db, dh.id) is None

    content = pdf_bytes(["Mo ta"])
    for account in (sv, gv):
        resp = _upload(client, auth_headers(account), dh.id, "mo-ta.pdf", content)
        assert resp.status_code == 403
        resp = client.delete(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(account))
        assert resp.status_code == 403

    resp = _upload(client, auth_headers(bm), 99999, "mo-ta.pdf", content)
    assert resp.status_code == 404
    resp = client.get(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(sv))
    assert resp.status_code == 404


def test_replace_removes_old_file_and_delete(client, db, make_account, auth_headers, pdf_bytes):
    dh = _dinh_huong(db, hoat_dong=False)
    bm = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)

    resp = _upload(client, auth_headers(bm), dh.id, "ban-1.pdf", pdf_bytes(["Ban 1"]))
    assert resp.status_code == 200, resp.text
    cu = _ten_luu_tru(db, dh.id)

    moi_content = pdf_bytes(["Ban 2", "Bo sung"])
    resp = _upload(client, auth_headers(bm), dh.id, "ban-2.pdf", moi_content)
    assert resp.status_code == 200, resp.text
    assert resp.json()["tep"]["ten_goc"] == "ban-2.pdf"
    moi = _ten_luu_tru(db, dh.id)
    assert moi != cu
    assert not documents.storage_path(cu).exists()
    assert documents.storage_path(moi).exists()

    # Định hướng ngừng sử dụng vẫn xem được file (đề tài cũ còn gắn với nó).
    resp = client.get(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(sv))
    assert resp.status_code == 200 and resp.content == moi_content

    resp = client.delete(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(bm))
    assert resp.status_code == 204
    assert _ten_luu_tru(db, dh.id) is None
    assert not documents.storage_path(moi).exists()

    resp = client.get(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(sv))
    assert resp.status_code == 404
    resp = client.delete(f"/api/dinh-huong/{dh.id}/tep", headers=auth_headers(bm))
    assert resp.status_code == 404
    listed = client.get("/api/dinh-huong", headers=auth_headers(bm)).json()
    assert listed[0]["tep"] is None


def test_upload_commit_failure_removes_new_file(
    client, db, make_account, auth_headers, pdf_bytes, monkeypatch
):
    dh = _dinh_huong(db)
    headers = auth_headers(make_account(VaiTro.BO_MON))
    thu_muc = documents.storage_path("DINH_HUONG")
    truoc = set(thu_muc.glob("*.pdf")) if thu_muc.exists() else set()

    def _commit_loi(self):
        raise RuntimeError("commit lỗi")

    monkeypatch.setattr(Session, "commit", _commit_loi)
    with pytest.raises(RuntimeError):
        _upload(client, headers, dh.id, "mo-ta.pdf", pdf_bytes(["Mo ta"]))
    monkeypatch.undo()

    assert set(thu_muc.glob("*.pdf")) == truoc
    assert _ten_luu_tru(db, dh.id) is None
