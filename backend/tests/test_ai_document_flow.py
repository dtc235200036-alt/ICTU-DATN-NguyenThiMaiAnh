"""AISV-04/AISV-06, D-03/D-04 (plan 04-06): hợp đồng giữa kiểm tra trùng lặp
tài liệu chạy nền và dịch vụ AI — ngưỡng đoạn + danh sách loại trừ gửi theo
từng request, tín hiệu ghi vào vi_tri, nhãn nguồn đúng không gian id (WR-06:
tai_lieu_do_an.id trùng số với do_an_kho.id), ingest DOCUMENT chỉ SAU khi
kiểm tra kết thúc HOAN_TAT và lỗi ingest không bao giờ đổi kết quả."""
from sqlalchemy import select

from app.core.roles import VaiTro
from app.models.cau_hinh_nguong import NGUONG_DOAN_TRUNG, CauHinhNguong
from app.models.kho import DA_INDEX, IMPORT, DoAnKho

_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class _RecordingAi:
    """Giả lập dịch vụ AI: ghi lại thứ tự lời gọi check_document / ingest."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.answer: dict | None = None
        self.fail_check = False
        self.fail_ingest = False

    def check_title(self, text, top_k=5, nguong=None):
        return {"matches": []}

    def check_document(self, ref_id, text, top_k=5, nguong_doan=None, loai_tru=None):
        from app.services.ai_client import AiServiceError

        self.calls.append(("check", ref_id, nguong_doan, set(loai_tru or ()), text))
        if self.fail_check:
            raise AiServiceError("Dịch vụ AI không phản hồi khi gọi /check-document (ConnectError)")
        return self.answer or {"ty_le_tong": 0.0, "do_an_trung": [], "chi_tiet": []}

    def ingest(self, ref_id, loai, text):
        from app.services.ai_client import AiServiceError

        self.calls.append(("ingest", ref_id, loai, text))
        if self.fail_ingest:
            raise AiServiceError("Dịch vụ AI không phản hồi khi gọi /ingest (ReadTimeout)")
        return {"chunk_count": 1, "indexed": True}


def test_document_check_uses_ai_contract(
    client, make_account, auth_headers, make_assigned_topic, docx_bytes, monkeypatch, db
):
    from app.services import ai_index, document_check

    fake = _RecordingAi()
    monkeypatch.setattr(document_check, "get_ai_client", lambda _db: fake)
    monkeypatch.setattr(ai_index, "get_ai_client", lambda _db: fake)

    def submit(topic_id, sv, name, paragraphs):
        resp = client.post(
            f"/api/outlines/{topic_id}/submit",
            headers=auth_headers(sv),
            files={"file": (name, docx_bytes(paragraphs), _DOCX_CT)},
        )
        assert resp.status_code == 202, resp.text
        return resp.json()["phien_ban"][0]["tai_lieu"]["id"]

    def request_changes(topic_id, gv, doc_id):
        resp = client.post(
            f"/api/outlines/{topic_id}/review",
            headers=auth_headers(gv),
            json={"tai_lieu_do_an_id": doc_id, "ket_qua": "YEU_CAU_SUA", "nhan_xet": "Cần sửa"},
        )
        assert resp.status_code == 200, resp.text

    def check_of(doc_id, gv):
        resp = client.get(f"/api/documents/{doc_id}/check", headers=auth_headers(gv))
        assert resp.status_code == 200, resp.text
        return resp.json()

    # Đề tài nguồn (một SV khác) có một đề cương -> tai_lieu_do_an id X; một
    # bản ghi kho mang ĐÚNG id X nhưng tên khác (WR-06: hai không gian id).
    sv_src = make_account(VaiTro.SINH_VIEN)
    gv_src = make_account(VaiTro.GIANG_VIEN)
    topic_src = make_assigned_topic(sv_src, gv_src)
    src_doc_id = submit(topic_src.id, sv_src, "nguon.docx", ["Nội dung đề cương nguồn dùng để so khớp"])
    db.add(
        DoAnKho(
            id=src_doc_id,
            khoa="K20",
            ten_de_tai="Bản ghi kho có id trùng số với tài liệu",
            nguon=IMPORT,
            trang_thai_index=DA_INDEX,
        )
    )
    db.commit()

    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)
    v1_id = submit(topic.id, sv, "v1.docx", ["Đề cương phiên bản một của đề tài kiểm thử"])
    request_changes(topic.id, gv, v1_id)

    fake.answer = {
        "ty_le_tong": 42.5,
        # CR-01: tổng 42.5 % (> ngưỡng stub 30) nhưng trải trên hai nguồn —
        # không nguồn nào tới ngưỡng -> KHÔNG vượt ngưỡng (ca P19 của 04-04).
        "do_an_trung": [{"ref_id": src_doc_id, "ty_le": 25.0}, {"ref_id": 999_999, "ty_le": 17.5}],
        # CR-04: phạm vi kiểm tra được lưu và báo khi hơn nửa văn bản bị loại.
        "so_doan": 40,
        "so_doan_loai_tru": 12,
        "ty_le_loai_tru": 55.5,
        "chi_tiet": [
            {
                "ref_id": src_doc_id,
                "doan_nguon": "Câu chép nguyên văn từ đề cương nguồn.",
                "doan_trung": "Câu chép nguyên văn từ đề cương nguồn.",
                "vi_tri": "Câu 3–4",
                "ty_le": 97.5,
                "tin_hieu": "NGUYEN_VAN",
                "diem_ngu_nghia": 97.5,
                "diem_nguyen_van": 100.0,
            },
            {
                # Một item mang loai ARCHIVE tường minh: cùng số id, khác không gian.
                "ref_id": src_doc_id,
                "loai": "ARCHIVE",
                "doan_nguon": "Câu diễn đạt lại.",
                "doan_trung": "Câu gốc trong kho.",
                "vi_tri": "Câu 7",
                "ty_le": 71.0,
                "tin_hieu": "NGU_NGHIA",
                "diem_ngu_nghia": 71.0,
                "diem_nguyen_van": 12.0,
            },
        ],
    }
    fake.calls.clear()
    v2_text = "Đề cương phiên bản hai có đoạn chép nguyên văn từ đề cương nguồn"
    v2_id = submit(topic.id, sv, "v2.docx", [v2_text])

    nguong_doan = float(
        db.execute(
            select(CauHinhNguong.gia_tri).where(CauHinhNguong.loai == NGUONG_DOAN_TRUNG)
        ).scalar_one()
    )
    checks = [c for c in fake.calls if c[0] == "check"]
    ingests = [c for c in fake.calls if c[0] == "ingest"]
    assert len(checks) == 1 and checks[0][1] == v2_id
    assert checks[0][2] == nguong_doan
    assert {v1_id, v2_id} <= checks[0][3]
    assert src_doc_id not in checks[0][3]
    # Ingest đúng một lần, SAU kiểm tra, cùng văn bản đã trích xuất.
    assert len(ingests) == 1
    assert fake.calls.index(ingests[0]) > fake.calls.index(checks[0])
    assert ingests[0][1:] == (v2_id, "DOCUMENT", checks[0][4])
    assert v2_text in ingests[0][3]

    detail = check_of(v2_id, gv)
    assert detail["trang_thai"] == "HOAN_TAT"
    assert detail["ty_le_tong"] == 42.5
    assert detail["ty_le_nguon_cao_nhat"] == 25.0
    assert detail["nguong_ap_dung"] == 30.0 and detail["vuot_nguong"] is False
    assert (detail["so_doan"], detail["so_doan_loai_tru"], detail["ty_le_loai_tru"]) == (40, 12, 55.5)
    assert detail["loai_tru_nhieu"] is True
    by_vi_tri = {seg["vi_tri"]: seg for seg in detail["chi_tiet"]}
    assert set(by_vi_tri) == {"Câu 3–4 · trùng nguyên văn", "Câu 7 · trùng ngữ nghĩa"}
    assert by_vi_tri["Câu 3–4 · trùng nguyên văn"]["doi_tuong_trung"] == f"{topic_src.ten_de_tai} (KTEST)"
    assert by_vi_tri["Câu 7 · trùng ngữ nghĩa"]["doi_tuong_trung"] == (
        "Bản ghi kho có id trùng số với tài liệu (K20)"
    )

    # Ingest lỗi -> kết quả kiểm tra vẫn HOAN_TAT.
    request_changes(topic.id, gv, v2_id)
    fake.fail_ingest = True
    fake.calls.clear()
    v3_id = submit(topic.id, sv, "v3.docx", ["Đề cương phiên bản ba sau khi sửa theo nhận xét"])
    assert [c[0] for c in fake.calls] == ["check", "ingest"]
    assert check_of(v3_id, gv)["trang_thai"] == "HOAN_TAT"

    # Kiểm tra lỗi -> LOI và không ingest.
    request_changes(topic.id, gv, v3_id)
    fake.fail_ingest = False
    fake.fail_check = True
    fake.calls.clear()
    v4_id = submit(topic.id, sv, "v4.docx", ["Đề cương phiên bản bốn khi dịch vụ AI lỗi"])
    assert [c[0] for c in fake.calls] == ["check"]
    assert check_of(v4_id, gv)["trang_thai"] == "LOI"

    # WR-05: văn bản vượt trần gửi AI -> không gọi AI, LOI không thử lại được,
    # lý do hiện qua tai_lieu.qua_dai_kiem_tra; "Kiểm tra lại" trả 409 rõ ràng.
    from app.core.config import get_settings

    request_changes(topic.id, gv, v4_id)
    fake.fail_check = False
    fake.calls.clear()
    monkeypatch.setattr(get_settings(), "AI_DOCUMENT_MAX_CHARS", 20)
    v5_id = submit(topic.id, sv, "v5.docx", ["Đề cương phiên bản năm dài hơn trần kiểm tra"])
    assert fake.calls == []
    too_long = check_of(v5_id, gv)
    assert too_long["trang_thai"] == "LOI" and too_long["tai_lieu"]["qua_dai_kiem_tra"] is True
    resp = client.post(f"/api/documents/{v5_id}/recheck", headers=auth_headers(gv))
    assert resp.status_code == 409 and "quá dài" in resp.json()["detail"], resp.text

    # WR-06: v3 hoàn tất kiểm tra nhưng ingest lỗi -> còn "chưa vào chỉ mục";
    # lần ingest thành công kế tiếp thử lại nó và đóng dấu da_index_luc.
    from app.models.de_cuong import TaiLieuDoAn

    monkeypatch.setattr(get_settings(), "AI_DOCUMENT_MAX_CHARS", 800_000)
    db.rollback()
    assert db.get(TaiLieuDoAn, v3_id).da_index_luc is None
    assert db.get(TaiLieuDoAn, v2_id).da_index_luc is not None
    assert ai_index.count_pending_documents(db) == 1
    fake.calls.clear()
    ai_index.ingest_document(v2_id)
    assert [(c[0], c[1]) for c in fake.calls] == [("ingest", v2_id), ("ingest", v3_id)]
    db.rollback()
    assert db.get(TaiLieuDoAn, v3_id).da_index_luc is not None
    assert ai_index.count_pending_documents(db) == 0
