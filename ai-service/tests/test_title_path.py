import unicodedata

from conftest import API_KEY, HEADERS, make_client

TITLES = {
    ("ARCHIVE", 1): "Xây dựng hệ thống quản lý thư viện cho trường trung học phổ thông",
    ("ARCHIVE", 2): "Ứng dụng học sâu nhận diện biển số xe máy",
    ("ARCHIVE", 3): "Website thương mại điện tử bán đồ gia dụng",
    ("TOPIC", 7): "Hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt",
    ("TOPIC", 8): "Ứng dụng di động đặt lịch khám bệnh trực tuyến",
}


def _ingest(client, loai, ref_id, text):
    return client.post("/ingest", json={"id": ref_id, "type": loai, "text": text}, headers=HEADERS)


def _check(client, text, **kw):
    r = client.post("/check-title", json={"text": text, **kw}, headers=HEADERS)
    assert r.status_code == 200, r.text
    return r.json()


def _encode_calls(client):
    return client.get("/health").json()["encode_calls"]


def test_api_key_guards_every_route_but_health(client):
    routes = [
        ("/ingest", {"id": 1, "type": "ARCHIVE", "text": "Quản lý thư viện"}),
        ("/check-title", {"text": "Quản lý thư viện"}),
    ]
    for path, body in routes:
        missing = client.post(path, json=body)
        assert missing.status_code == 401
        wrong = client.post(path, json=body, headers={"X-API-Key": "sai-" + API_KEY[4:]})
        assert wrong.status_code == 401
        for resp in (missing, wrong):
            assert API_KEY not in resp.text
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


def test_title_ingest_check_restart(client, db_path):
    base = _encode_calls(client)
    for (loai, ref_id), title in TITLES.items():
        r = _ingest(client, loai, ref_id, title)
        assert r.json() == {"chunk_count": 1, "indexed": True}
    assert _encode_calls(client) == base + 5

    # Ingest lại đúng tiêu đề cũ: không encode.
    _ingest(client, "ARCHIVE", 2, TITLES[("ARCHIVE", 2)])
    assert _encode_calls(client) == base + 5

    # REPLACE: ARCHIVE 1 đổi tiêu đề → tiêu đề cũ không còn tìm thấy.
    old_title = TITLES[("ARCHIVE", 1)]
    _ingest(client, "ARCHIVE", 1, "Phân tích dữ liệu bán hàng bằng Power BI")
    assert _encode_calls(client) == base + 6
    exact_old = _check(client, old_title, nguong=99.5)["matches"]
    assert exact_old == []

    title = TITLES[("TOPIC", 7)]
    result = _check(client, title)
    assert result["matches"][0] == {"ref_id": 7, "loai": "TOPIC", "ty_le": 100.0}
    nfd = _check(client, unicodedata.normalize("NFD", title))
    assert nfd == result

    exact = _check(client, title, nguong=99.5)["matches"]
    assert exact == [{"ref_id": 7, "loai": "TOPIC", "ty_le": 100.0}]
    assert len(_check(client, title, top_k=2)["matches"]) == 2

    # Văn bản rỗng xóa nguồn.
    assert _ingest(client, "ARCHIVE", 3, "").json()["chunk_count"] == 0
    gone = _check(client, TITLES[("ARCHIVE", 3)], nguong=99.5)["matches"]
    assert gone == []

    snapshot = _check(client, title)
    size = client.get("/health").json()["index_size"]
    assert size == 4

    # Khởi động lại trên cùng file DB: dựng lại từ thesis_ai, 0 lần encode.
    with make_client(db_path) as restarted:
        health = restarted.get("/health").json()
        assert health["encode_calls"] == 0
        assert health["index_size"] == 4
        assert health["thieu_embedding"] == 0
        assert _check(restarted, title) == snapshot
