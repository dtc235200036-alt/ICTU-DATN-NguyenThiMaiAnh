"""D-07 / AISV-03 (plan 04-05): hợp đồng HTTP của AiClientHttp (X-API-Key,
payload §3.3.5, mọi lỗi -> AiServiceError không lộ khóa) và ánh xạ kết quả
/check-title TOPIC -> de_tai, ARCHIVE -> do_an_kho trong title_check."""
import json
from decimal import Decimal

import httpx
import pytest

from app.core.roles import VaiTro
from app.models.kho import DA_INDEX, IMPORT, DoAnKho

API_KEY = "khoa-noi-bo-kiem-thu-" + "k" * 32


def test_ai_client_http_contract_and_archive_mapping(
    db, make_account, make_assigned_topic, monkeypatch
):
    from app.services import title_check
    from app.services.ai_client import AiClientHttp, AiServiceError

    requests: list[httpx.Request] = []
    replies: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        reply = replies[request.url.path]
        if isinstance(reply, Exception):
            raise reply
        status, body = reply
        return httpx.Response(status, json=body)

    def make_client() -> AiClientHttp:
        return AiClientHttp(
            "http://ai.test:8002",
            API_KEY,
            title_timeout=4.0,
            document_timeout=24.0,
            ingest_timeout=60.0,
            transport=httpx.MockTransport(handler),
        )

    client = make_client()

    # check_title: POST /check-title, X-API-Key, {text, top_k, nguong}; loai giữ nguyên.
    replies["/check-title"] = (200, {"matches": [{"ref_id": 7, "loai": "ARCHIVE", "ty_le": 81.5}]})
    body = client.check_title("Quản lý thư viện", 10, nguong=67.8)
    sent = requests[-1]
    assert sent.method == "POST" and sent.url.path == "/check-title"
    assert sent.headers["X-API-Key"] == API_KEY
    assert json.loads(sent.content) == {"text": "Quản lý thư viện", "top_k": 10, "nguong": 67.8}
    assert body["matches"][0]["loai"] == "ARCHIVE"

    # 401, timeout, thân thiếu "matches" -> AiServiceError, không bao giờ chứa khóa.
    for reply in (
        (401, {"detail": "Thiếu hoặc sai API key nội bộ"}),
        httpx.ReadTimeout("hết thời gian chờ", request=httpx.Request("POST", "http://ai.test")),
        (200, {"ket_qua": []}),
    ):
        replies["/check-title"] = reply
        with pytest.raises(AiServiceError) as err:
            client.check_title("Quản lý thư viện", 5)
        assert API_KEY not in str(err.value)

    # ingest: POST /ingest {id, type, text}.
    replies["/ingest"] = (200, {"chunk_count": 1, "indexed": True})
    assert client.ingest(12, "ARCHIVE", "Tên đồ án")["indexed"] is True
    assert json.loads(requests[-1].content) == {"id": 12, "type": "ARCHIVE", "text": "Tên đồ án"}

    # Ánh xạ trong title_check: TOPIC + ARCHIVE; bản ghi kho liên kết cùng đề
    # tài (điểm thấp hơn) bị gộp; ARCHIVE không tồn tại bị bỏ qua.
    sv = make_account(VaiTro.SINH_VIEN)
    gv = make_account(VaiTro.GIANG_VIEN)
    topic = make_assigned_topic(sv, gv)
    kho = DoAnKho(
        khoa="K20", ten_de_tai="Hệ thống quản lý thư viện số", diem=Decimal("8.00"),
        nguon=IMPORT, trang_thai_index=DA_INDEX,
    )
    kho_linked = DoAnKho(
        de_tai_id=topic.id, khoa="KTEST", ten_de_tai=topic.ten_de_tai,
        nguon=IMPORT, trang_thai_index=DA_INDEX,
    )
    db.add_all([kho, kho_linked])
    db.commit()

    replies["/check-title"] = (200, {"matches": [
        {"ref_id": topic.id, "loai": "TOPIC", "ty_le": 90.0},
        {"ref_id": kho.id, "loai": "ARCHIVE", "ty_le": 75.0},
        {"ref_id": kho_linked.id, "loai": "ARCHIVE", "ty_le": 70.0},
        {"ref_id": kho.id + kho_linked.id + 1000, "loai": "ARCHIVE", "ty_le": 88.0},
    ]})
    monkeypatch.setattr(title_check, "get_ai_client", lambda _db: make_client())

    result = title_check.kiem_tra_ten(db, "Xây dựng hệ thống quản lý thư viện")
    assert result.trang_thai == "HOAN_TAT"
    assert json.loads(requests[-1].content)["nguong"] == 50.0 == result.nguong
    assert [(m.nguon, m.de_tai_id, m.do_an_kho_id, m.khoa, m.ty_le) for m in result.matches] == [
        ("DE_TAI", topic.id, None, "KTEST", 90.0),
        ("KHO", None, kho.id, "K20", 75.0),
    ]
