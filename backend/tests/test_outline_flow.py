"""UC2 (đề cương) — 4 test tập trung theo yêu cầu của kế hoạch: upload bị từ
chối trước khi tạo phiên bản, luồng trạng thái một chiều, kiểm tra nền luôn
kết thúc (kể cả khi lỗi), và phạm vi truy cập theo vai trò."""
import zipfile
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from sqlalchemy import func, select, update

from app.core.roles import VaiTro
from app.core.timeutil import now_utc
from app.models.de_cuong import DC_CHUA_NOP, DeCuong, TaiLieuDoAn
from app.models.trung_lap import DANG_KIEM_TRA, KetQuaKiemTraTrungLap

_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PDF_CT = "application/pdf"


def test_upload_rejected_before_any_version(
    client, make_account, auth_headers, make_assigned_topic, pdf_bytes, db
):
    import os

    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)
    headers = auth_headers(sv)

    # UPLOAD_DIR là một thư mục tạm DÙNG CHUNG cho cả phiên pytest (không bị
    # dọn giữa các test) — các test khác (vd. tests/test_defense_flow.py chạy
    # trước file này khi gọi `pytest tests/test_defense_flow.py
    # tests/test_outline_flow.py ...`) hợp lệ ghi file thật vào đây trước khi
    # test này chạy. Chỉ so sánh phần chênh lệch MỚI sinh ra bởi chính test
    # này, không quét toàn bộ cây thư mục (Rule 1 — bug lộ ra khi kết hợp hai
    # file test, không phải khi chạy một mình test_outline_flow.py).
    upload_dir_before = Path(os.environ["UPLOAD_DIR"])
    files_before = set(upload_dir_before.rglob("*")) if upload_dir_before.exists() else set()

    # (a) .docx là ZIP không có word/document.xml
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("not-a-document.txt", "hello")
    bad_docx = zip_buf.getvalue()

    # (b) .pdf có bytes bắt đầu bằng GIF89a
    bad_pdf = b"GIF89a" + b"0" * 20

    # (c) bytes PDF thật nhưng đặt tên .docx
    real_pdf = pdf_bytes(["Hello world"])

    # (d) .pdf 20 MB + 1 byte, bắt đầu đúng %PDF-
    oversized_pdf = b"%PDF-" + b"0" * (20 * 1024 * 1024)

    # (e) file .txt
    txt_bytes = b"just plain text, not a real document"

    cases = [
        ("bad.docx", bad_docx, _DOCX_CT),
        ("bad.pdf", bad_pdf, _PDF_CT),
        ("real-pdf-named.docx", real_pdf, _DOCX_CT),
        ("oversized.pdf", oversized_pdf, _PDF_CT),
        ("plain.txt", txt_bytes, "text/plain"),
    ]

    responses = {}
    for filename, content, content_type in cases:
        resp = client.post(
            f"/api/outlines/{topic.id}/submit",
            headers=headers,
            files={"file": (filename, content, content_type)},
        )
        assert resp.status_code == 422, f"{filename}: {resp.status_code} {resp.text}"
        responses[filename] = resp

    assert "20 MB" in responses["oversized.pdf"].json()["detail"]

    assert db.execute(select(func.count()).select_from(TaiLieuDoAn)).scalar_one() == 0
    de_cuong = db.execute(
        select(DeCuong).where(DeCuong.de_tai_id == topic.id)
    ).scalar_one_or_none()
    assert de_cuong is None or de_cuong.trang_thai == DC_CHUA_NOP

    files_after = set(upload_dir_before.rglob("*")) if upload_dir_before.exists() else set()
    new_files = files_after - files_before
    assert not any(f.is_file() for f in new_files)


def test_outline_state_machine_one_way(
    client, make_account, auth_headers, make_assigned_topic, docx_bytes, pdf_bytes, db
):
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)
    sv_headers = auth_headers(sv)
    gv_headers = auth_headers(gv)

    v1 = docx_bytes(
        ["Nội dung đề cương phiên bản một của đề tài kiểm thử dùng để kiểm tra hệ thống"]
    )
    resp = client.post(
        f"/api/outlines/{topic.id}/submit",
        headers=sv_headers,
        files={"file": ("v1.docx", v1, _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    v1_id = body["phien_ban"][0]["tai_lieu"]["id"]
    # response 202 được xây trước khi BackgroundTasks chạy (submit() gọi
    # get_detail() trước khi router add_task) — đọc lại để thấy trạng thái
    # kiểm tra sau khi tác vụ nền đã hoàn tất (TestClient chạy nền trước khi
    # client.post(...) trả về).
    reread = client.get(f"/api/outlines/{topic.id}", headers=sv_headers).json()
    assert reread["phien_ban"][0]["kiem_tra"]["trang_thai"] == "HOAN_TAT"

    # nộp lại khi đang Chờ duyệt -> 409
    resp = client.post(
        f"/api/outlines/{topic.id}/submit",
        headers=sv_headers,
        files={"file": ("v1b.docx", v1, _DOCX_CT)},
    )
    assert resp.status_code == 409

    # GVHD yêu cầu sửa không kèm nhận xét -> 422
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=gv_headers,
        json={"tai_lieu_do_an_id": v1_id, "ket_qua": "YEU_CAU_SUA"},
    )
    assert resp.status_code == 422

    # có nhận xét -> Yêu cầu sửa + SV có thông báo
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=gv_headers,
        json={
            "tai_lieu_do_an_id": v1_id,
            "ket_qua": "YEU_CAU_SUA",
            "nhan_xet": "Cần bổ sung mục tiêu và phạm vi dữ liệu",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["trang_thai"] == "YEU_CAU_SUA"

    notif_resp = client.get("/api/notifications", headers=sv_headers)
    assert any(
        n["loai"] == "DE_CUONG_YEU_CAU_SUA" for n in notif_resp.json()["items"]
    )

    # SV nộp v2 dạng PDF -> Chờ duyệt, phiên bản 2, v1 không đổi
    v2 = pdf_bytes(["Second version content for outline test document"])
    resp = client.post(
        f"/api/outlines/{topic.id}/submit",
        headers=sv_headers,
        files={"file": ("v2.pdf", v2, _PDF_CT)},
    )
    assert resp.status_code == 202, resp.text
    body2 = resp.json()
    assert body2["trang_thai"] == "CHO_DUYET"
    versions = body2["phien_ban"]
    assert len(versions) == 2
    v2_version = next(v for v in versions if v["tai_lieu"]["so_phien_ban"] == 2)
    v1_version = next(v for v in versions if v["tai_lieu"]["so_phien_ban"] == 1)
    v2_id = v2_version["tai_lieu"]["id"]
    assert v1_version["tai_lieu"]["id"] == v1_id

    # GVHD duyệt nhầm id của v1 (đã cũ) -> 409
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=gv_headers,
        json={"tai_lieu_do_an_id": v1_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 409

    # duyệt v2 -> Đã duyệt
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=gv_headers,
        json={"tai_lieu_do_an_id": v2_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["trang_thai"] == "DA_DUYET"

    # duyệt lần hai -> 409
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=gv_headers,
        json={"tai_lieu_do_an_id": v2_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 409

    # nộp lại sau khi Đã duyệt -> 409
    resp = client.post(
        f"/api/outlines/{topic.id}/submit",
        headers=sv_headers,
        files={"file": ("v3.docx", v1, _DOCX_CT)},
    )
    assert resp.status_code == 409

    # GET chi tiết liệt kê 2 phiên bản, mỗi phiên bản có kiểm tra + duyệt riêng
    resp = client.get(f"/api/outlines/{topic.id}", headers=sv_headers)
    versions_final = resp.json()["phien_ban"]
    assert len(versions_final) == 2
    for v in versions_final:
        assert v["kiem_tra"] is not None
        assert v["luot_duyet"] is not None


def test_background_check_always_terminates(
    client, make_account, auth_headers, make_assigned_topic, docx_bytes, monkeypatch, db
):
    sv_a = make_account(VaiTro.SINH_VIEN)
    gv_a = make_account(VaiTro.GIANG_VIEN)
    topic_a = make_assigned_topic(sv_a, gv_a)

    sv_b = make_account(VaiTro.SINH_VIEN)
    gv_b = make_account(VaiTro.GIANG_VIEN)
    topic_b = make_assigned_topic(sv_b, gv_b)

    shared_1 = (
        "Đây là đoạn văn bản dùng chung để kiểm tra phát hiện trùng lặp giữa"
        " hai đề tài khác nhau trong hệ thống"
    )
    shared_2 = (
        "Đoạn thứ hai cũng được sao chép nguyên văn để tăng tỷ lệ trùng lặp"
        " phát hiện được trong bài kiểm thử này"
    )

    doc_a = docx_bytes([shared_1, shared_2, "Nội dung riêng của đề tài A không liên quan gì"])
    resp = client.post(
        f"/api/outlines/{topic_a.id}/submit",
        headers=auth_headers(sv_a),
        files={"file": ("a.docx", doc_a, _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    a_v1_id = resp.json()["phien_ban"][0]["tai_lieu"]["id"]
    resp = client.post(
        f"/api/outlines/{topic_a.id}/review",
        headers=auth_headers(gv_a),
        json={"tai_lieu_do_an_id": a_v1_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 200, resp.text

    doc_b = docx_bytes([shared_1, shared_2, "Nội dung riêng của đề tài B cũng không liên quan"])
    resp = client.post(
        f"/api/outlines/{topic_b.id}/submit",
        headers=auth_headers(sv_b),
        files={"file": ("b.docx", doc_b, _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    body_b = resp.json()
    b_doc_id = body_b["phien_ban"][0]["tai_lieu"]["id"]

    check_detail = client.get(
        f"/api/documents/{b_doc_id}/check", headers=auth_headers(sv_b)
    ).json()
    assert check_detail["trang_thai"] == "HOAN_TAT"
    assert check_detail["ty_le_tong"] > 0
    assert any(topic_a.ten_de_tai in seg["doi_tuong_trung"] for seg in check_detail["chi_tiet"])
    # WR-07: nguồn là đề cương chưa công bố của SV khác -> SV không thấy đoạn
    # nguồn; GVHD thấy đủ
    assert all(seg["doan_trung"] is None and seg["doan_trung_an"] for seg in check_detail["chi_tiet"])
    gv_view = client.get(f"/api/documents/{b_doc_id}/check", headers=auth_headers(gv_b)).json()
    assert all(seg["doan_trung"] and not seg["doan_trung_an"] for seg in gv_view["chi_tiet"])
    # ... còn khi đề tài nguồn đã vào kho (đồ án công bố) thì SV thấy đoạn nguồn
    from app.models.kho import DoAnKho

    db.add(DoAnKho(de_tai_id=topic_a.id, ten_de_tai=topic_a.ten_de_tai, nguon="IMPORT", trang_thai_index="DA_INDEX"))
    db.commit()
    sv_view = client.get(f"/api/documents/{b_doc_id}/check", headers=auth_headers(sv_b)).json()
    assert all(seg["doan_trung"] and not seg["doan_trung_an"] for seg in sv_view["chi_tiet"])

    # Yêu cầu sửa để SV B có thể nộp lại
    resp = client.post(
        f"/api/outlines/{topic_b.id}/review",
        headers=auth_headers(gv_b),
        json={
            "tai_lieu_do_an_id": b_doc_id,
            "ket_qua": "YEU_CAU_SUA",
            "nhan_xet": "Cần bổ sung thêm nội dung chương 2",
        },
    )
    assert resp.status_code == 200, resp.text

    from app.services import ai_client as ai_client_module

    def _boom(self, ref_id, text, top_k=5):
        raise RuntimeError("boom")

    monkeypatch.setattr(ai_client_module.AiClientStub, "check_document", _boom)

    doc_c = docx_bytes(
        ["Một đoạn văn bản khác hoàn toàn không liên quan tới hai đề tài phía trên"]
    )
    resp = client.post(
        f"/api/outlines/{topic_b.id}/submit",
        headers=auth_headers(sv_b),
        files={"file": ("c.docx", doc_c, _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    body_c = resp.json()
    c_doc_id = body_c["phien_ban"][0]["tai_lieu"]["id"]
    check_c = client.get(
        f"/api/documents/{c_doc_id}/check", headers=auth_headers(gv_b)
    ).json()
    assert check_c["trang_thai"] == "LOI"

    monkeypatch.undo()

    resp = client.post(f"/api/documents/{c_doc_id}/recheck", headers=auth_headers(gv_b))
    assert resp.status_code == 202, resp.text
    check_after_fix = client.get(
        f"/api/documents/{c_doc_id}/check", headers=auth_headers(gv_b)
    ).json()
    assert check_after_fix["trang_thai"] == "HOAN_TAT"

    # kiểm tra lại một dòng đã Hoàn tất -> 409
    resp = client.post(f"/api/documents/{c_doc_id}/recheck", headers=auth_headers(gv_b))
    assert resp.status_code == 409

    # dòng bị ép về Đang kiểm tra 10 phút trước -> đọc lại thành Lỗi
    db.execute(
        update(KetQuaKiemTraTrungLap)
        .where(KetQuaKiemTraTrungLap.tai_lieu_do_an_id == c_doc_id)
        .values(trang_thai=DANG_KIEM_TRA, thoi_diem=now_utc() - timedelta(minutes=10))
    )
    db.commit()
    resp = client.get(f"/api/documents/{c_doc_id}/check", headers=auth_headers(gv_b))
    assert resp.json()["trang_thai"] == "LOI"

    # yêu cầu sửa lần nữa để nộp phiên bản DOCX có word/document.xml hỏng
    resp = client.post(
        f"/api/outlines/{topic_b.id}/review",
        headers=auth_headers(gv_b),
        json={
            "tai_lieu_do_an_id": c_doc_id,
            "ket_qua": "YEU_CAU_SUA",
            "nhan_xet": "Vui lòng nộp lại đúng định dạng",
        },
    )
    assert resp.status_code == 200, resp.text

    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("word/document.xml", "<not valid xml")
    broken_docx = zip_buf.getvalue()

    resp = client.post(
        f"/api/outlines/{topic_b.id}/submit",
        headers=auth_headers(sv_b),
        files={"file": ("broken.docx", broken_docx, _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    latest_version = resp.json()["phien_ban"][0]
    assert latest_version["tai_lieu"]["trich_xuat_loi"] is True
    broken_doc_id = latest_version["tai_lieu"]["id"]
    broken_check = client.get(
        f"/api/documents/{broken_doc_id}/check", headers=auth_headers(gv_b)
    ).json()
    assert broken_check["trang_thai"] == "LOI"
    # IN-11: không trích xuất được văn bản -> kiểm tra lại là vô ích -> 409
    resp = client.post(f"/api/documents/{broken_doc_id}/recheck", headers=auth_headers(gv_b))
    assert resp.status_code == 409, resp.text


def test_outline_access_is_scoped(
    client, make_account, auth_headers, make_assigned_topic, docx_bytes, db
):
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)

    other_sv = make_account(VaiTro.SINH_VIEN)
    other_gv = make_account(VaiTro.GIANG_VIEN)
    bomon = make_account(VaiTro.BO_MON)

    content = docx_bytes(
        ["Nội dung đề cương dùng để kiểm tra phạm vi truy cập giữa các vai trò"]
    )
    resp = client.post(
        f"/api/outlines/{topic.id}/submit",
        headers=auth_headers(sv),
        files={"file": ("đề cương v1.docx", content, _DOCX_CT)},
    )
    assert resp.status_code == 202, resp.text
    doc_id = resp.json()["phien_ban"][0]["tai_lieu"]["id"]

    # SV khác: 403 trên GET outline/check/download/submit
    assert client.get(f"/api/outlines/{topic.id}", headers=auth_headers(other_sv)).status_code == 403
    assert (
        client.get(f"/api/documents/{doc_id}/check", headers=auth_headers(other_sv)).status_code
        == 403
    )
    assert (
        client.get(f"/api/documents/{doc_id}/download", headers=auth_headers(other_sv)).status_code
        == 403
    )
    resp = client.post(
        f"/api/outlines/{topic.id}/submit",
        headers=auth_headers(other_sv),
        files={"file": ("x.docx", content, _DOCX_CT)},
    )
    assert resp.status_code == 403

    # danh sách đề cương của SV khác không có đề tài này
    resp = client.get("/api/outlines", headers=auth_headers(other_sv))
    assert all(item["de_tai_id"] != topic.id for item in resp.json()["items"])

    # GV không liên quan: 403 trên GET outline/review/download
    assert client.get(f"/api/outlines/{topic.id}", headers=auth_headers(other_gv)).status_code == 403
    assert (
        client.get(f"/api/documents/{doc_id}/download", headers=auth_headers(other_gv)).status_code
        == 403
    )
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=auth_headers(other_gv),
        json={"tai_lieu_do_an_id": doc_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 403

    # Bộ môn: 200 trên GET outline/download, 403 trên review
    assert client.get(f"/api/outlines/{topic.id}", headers=auth_headers(bomon)).status_code == 200
    assert (
        client.get(f"/api/documents/{doc_id}/download", headers=auth_headers(bomon)).status_code
        == 200
    )
    resp = client.post(
        f"/api/outlines/{topic.id}/review",
        headers=auth_headers(bomon),
        json={"tai_lieu_do_an_id": doc_id, "ket_qua": "DA_DUYET"},
    )
    assert resp.status_code == 403

    # download id không tồn tại -> 404
    assert (
        client.get("/api/documents/999999999/download", headers=auth_headers(sv)).status_code
        == 404
    )

    # download của chủ sở hữu trả đúng bytes + ten_goc tiếng Việt trong Content-Disposition
    own_download = client.get(f"/api/documents/{doc_id}/download", headers=auth_headers(sv))
    assert own_download.status_code == 200
    assert own_download.content == content
    content_disposition = own_download.headers.get("content-disposition", "")
    assert "filename*=utf-8''" in content_disposition.lower()
