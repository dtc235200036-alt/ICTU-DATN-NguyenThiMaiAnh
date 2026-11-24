"""0020: GV/Bộ môn tải một tệp lên để kiểm tra trùng lặp với kho — chạy nền như
kiểm tra tài liệu, nhưng ref_id 0, không loại trừ, không ingest; chỉ người tải
lên xem được kết quả."""
from app.core.roles import VaiTro

_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class _FakeAi:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def check_document(self, ref_id, text, top_k=5, nguong_doan=None, loai_tru=None):
        self.calls.append(("check", ref_id, set(loai_tru or ()), text))
        return {
            "ty_le_tong": 40.0,
            "do_an_trung": [{"ref_id": 7, "ty_le": 40.0}],
            "chi_tiet": [
                {
                    "ref_id": 7,
                    "ty_le": 95.0,
                    "doan_nguon": "Câu trong tệp tải lên",
                    "doan_trung": "Câu trong đồ án nguồn",
                    "vi_tri": "Câu 1–2",
                    "tin_hieu": "NGUYEN_VAN",
                }
            ],
            "so_doan": 5,
            "so_doan_loai_tru": 0,
            "ty_le_loai_tru": 0.0,
        }

    def ingest(self, ref_id, loai, text, nhom=None):
        self.calls.append(("ingest", ref_id))
        return {"chunk_count": 1, "indexed": True}


def test_upload_check_flow(client, make_account, auth_headers, docx_bytes, pdf_bytes, monkeypatch):
    from app.services import ai_index, document_check

    fake = _FakeAi()
    monkeypatch.setattr(document_check, "get_ai_client", lambda _db: fake)
    monkeypatch.setattr(ai_index, "get_ai_client", lambda _db: fake)
    gv = make_account(VaiTro.GIANG_VIEN)

    resp = client.post(
        "/api/upload-checks",
        headers=auth_headers(gv),
        files={"file": ("bai-can-kiem-tra.docx", docx_bytes(["Nội dung cần kiểm tra trùng lặp"]), _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    assert resp.json()["ten_tep"] == "bai-can-kiem-tra.docx"
    ket_qua_id = resp.json()["id"]

    # Không thuộc kho: ref_id 0, không loại trừ gì, không bao giờ ingest.
    assert [c[:3] for c in fake.calls] == [("check", 0, set())]
    assert "Nội dung cần kiểm tra trùng lặp" in fake.calls[0][3]

    detail = client.get(f"/api/upload-checks/{ket_qua_id}", headers=auth_headers(gv)).json()
    assert detail["trang_thai"] == "HOAN_TAT"
    assert detail["ty_le_nguon_cao_nhat"] == 40.0
    assert detail["vuot_nguong"] is True and detail["ly_do_vuot_nguong"] == "MOT_NGUON"
    assert detail["chi_tiet"][0]["doan_trung"] == "Câu trong đồ án nguồn"
    assert detail["chi_tiet"][0]["vi_tri"].endswith("trùng nguyên văn")
    assert [m["ty_le"] for m in detail["do_an_trung"]] == [40.0]

    history = client.get("/api/upload-checks", headers=auth_headers(gv)).json()
    assert [h["id"] for h in history] == [ket_qua_id]

    # Người khác không xem được; SV không dùng được chức năng.
    other = make_account(VaiTro.BO_MON)
    assert client.get(f"/api/upload-checks/{ket_qua_id}", headers=auth_headers(other)).status_code == 404
    assert client.get("/api/upload-checks", headers=auth_headers(other)).json() == []
    sv = make_account(VaiTro.SINH_VIEN)
    assert client.get("/api/upload-checks", headers=auth_headers(sv)).status_code == 403

    # PDF không có chữ: báo ngay, không tạo kết quả.
    blank = client.post(
        "/api/upload-checks",
        headers=auth_headers(gv),
        files={"file": ("trong.pdf", pdf_bytes([]), "application/pdf")},
    )
    assert blank.status_code == 422
    assert len(client.get("/api/upload-checks", headers=auth_headers(gv)).json()) == 1


def test_upload_check_limits_running_checks(client, make_account, auth_headers, docx_bytes, monkeypatch):
    from app.services import document_check

    # Tác vụ nền không chạy -> các lần kiểm tra giữ trạng thái DANG_KIEM_TRA.
    monkeypatch.setattr(document_check, "run", lambda *_args: None)
    gv = make_account(VaiTro.GIANG_VIEN)

    def upload():
        return client.post(
            "/api/upload-checks",
            headers=auth_headers(gv),
            files={"file": ("a.docx", docx_bytes(["Nội dung"]), _DOCX_CT)},
        )

    assert upload().status_code == 202
    assert upload().status_code == 202
    busy = upload()
    assert busy.status_code == 429
    assert "chưa xong" in busy.json()["detail"]
    # Người khác vẫn kiểm tra được.
    other = make_account(VaiTro.GIANG_VIEN)
    resp = client.post(
        "/api/upload-checks",
        headers=auth_headers(other),
        files={"file": ("b.docx", docx_bytes(["Nội dung"]), _DOCX_CT)},
    )
    assert resp.status_code == 202
