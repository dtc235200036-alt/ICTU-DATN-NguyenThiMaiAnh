"""Đường kiểm tra tài liệu: lọc phần mẫu chung, chia câu, hai tín hiệu, loại
trừ, REPLACE, giới hạn kích thước, /reindex. Luôn gửi ngưỡng tường minh để giá
trị mặc định hiệu chỉnh sau này (plan 04-04) không đổi kết quả test."""
from sqlalchemy import create_engine, text

from app.nlp.boilerplate import strip_boilerplate
from app.nlp.chunking import sentences
from conftest import HEADERS

COVER = [
    "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG",
    "KHOA CÔNG NGHỆ THÔNG TIN",
    "ĐỒ ÁN TỐT NGHIỆP",
    "XÂY DỰNG HỆ THỐNG QUẢN LÝ THƯ VIỆN TRƯỜNG THPT",
    "Sinh viên thực hiện: Nguyễn Văn An",
    "Giảng viên hướng dẫn: ThS. Trần Thị Bình",
    "Lớp: CNTT K22A",
    "Thái Nguyên, tháng 12 năm 2026",
]
FRONT = [
    "LỜI CAM ĐOAN",
    "Em xin cam đoan đồ án tốt nghiệp này là công trình nghiên cứu của riêng em dưới sự hướng dẫn của giảng viên.",
    "Các số liệu và kết quả nêu trong đồ án là trung thực và chưa từng được công bố.",
    "MỤC LỤC",
    "LỜI CAM ĐOAN .................................... i",
    "MỞ ĐẦU .......................................... 1",
    "CHƯƠNG 1. TỔNG QUAN ............................. 3",
    "1.1. Khảo sát hiện trạng ......................... 3",
    "TÀI LIỆU THAM KHẢO .............................. 40",
    "DANH MỤC HÌNH ẢNH",
    "Hình 1.1: Kiến trúc tổng thể của hệ thống ........ 5",
]
REFS = [
    "TÀI LIỆU THAM KHẢO",
    "[1] Nguyễn Văn Cường (2020), Giáo trình cơ sở dữ liệu, Nhà xuất bản Giáo dục Việt Nam.",
    "[2] Lê Thị Dung (2021), Phân tích và thiết kế hệ thống thông tin, Nhà xuất bản Khoa học.",
]
HEADER = "Đồ án tốt nghiệp - Khoa Công nghệ thông tin"

P1 = [
    "Hệ thống quản lý thư viện giúp cán bộ theo dõi việc mượn và trả sách của học sinh.",
    "Mỗi lượt mượn được ghi nhận kèm thời hạn trả và trạng thái của cuốn sách.",
]
P2 = [
    "Chức năng thống kê cho phép lập báo cáo số lượng sách theo từng thể loại.",
    "Báo cáo được xuất ra định dạng bảng tính để nộp cho ban giám hiệu.",
]
P3 = [
    "Cơ sở dữ liệu được thiết kế gồm các bảng độc giả, đầu sách, bản sao và phiếu mượn.",
    "Khóa ngoại giữa phiếu mượn và bản sao đảm bảo không có bản sao nào bị mượn hai lần cùng lúc.",
]
P4 = [
    "Giao diện web được xây dựng theo hướng đáp ứng để dùng tốt trên điện thoại.",
    "Người dùng có thể tra cứu sách theo tên, tác giả hoặc mã phân loại.",
]
U1 = [
    "Mô hình học sâu được huấn luyện trên tập ảnh biển số thu thập tại bãi gửi xe của trường.",
    "Độ chính xác nhận dạng đạt khoảng chín mươi phần trăm trong điều kiện đủ ánh sáng.",
]
U2 = ["Ứng dụng di động gửi thông báo nhắc lịch khám cho bệnh nhân trước một ngày."]
U3 = [
    "Dữ liệu cảm biến nhiệt độ được truyền về máy chủ qua giao thức MQTT mỗi năm giây.",
    "Khi nhiệt độ vượt ngưỡng, hệ thống bật quạt và ghi lại sự kiện vào nhật ký.",
]

REMOVED = COVER + FRONT + REFS + [HEADER]


def _wrap(paragraph: list[str], width: int) -> list[str]:
    """Bẻ đoạn thành nhiều dòng kiểu PDF (page.get_text() giữ nguyên xuống dòng)."""
    words = " ".join(paragraph).split(" ")
    return [" ".join(words[i : i + width]) for i in range(0, len(words), width)]


def _pdf_like(paragraphs: list[list[str]], width: int) -> str:
    """Tài liệu kiểu PDF: phần mẫu chung + mỗi đoạn một trang có header + số trang."""
    lines = COVER + FRONT + ["MỞ ĐẦU"]
    for page, paragraph in enumerate(paragraphs, start=1):
        if page == 2:
            lines += ["CHƯƠNG 1. TỔNG QUAN VỀ BÀI TOÁN", "1.1. Khảo sát hiện trạng"]
        if page == 3:
            lines.append("Hình 1.1: Kiến trúc tổng thể của hệ thống")
        lines += _wrap(paragraph, width)
        lines += [HEADER, str(page)]
    return "\n".join(lines + REFS)


def _docx_like(paragraphs: list[list[str]]) -> str:
    lines = COVER + FRONT + ["MỞ ĐẦU"]
    lines += [" ".join(p) for p in paragraphs]
    return "\n".join(lines + REFS)


def _check(client, text, **kw):
    body = {"ref_id": 99, "text": text, "top_k": 5, "nguong_doan": 95.0, "nguong_nguyen_van": 60.0}
    body.update(kw)
    r = client.post("/check-document", json=body, headers=HEADERS)
    assert r.status_code == 200, r.text
    return r.json()


def test_boilerplate_and_sentences():
    content = [P1, P2, P3, P4]
    stripped = strip_boilerplate(_pdf_like(content, width=7))
    result = sentences(stripped.lines)
    assert result == [s for p in content for s in p]
    assert stripped.removed > 0
    for chunk in result:
        for removed in REMOVED:
            assert removed not in chunk
        assert "......" not in chunk


def test_chunking_is_linear_on_adversarial_text():
    """CR-03 (04-REVIEW): văn bản do sinh viên kiểm soát không được làm lọc +
    chia câu chạy bậc hai — mỗi mẫu ~200 KB phải xong dưới 2 s, và không mảnh
    nào vượt trần ký tự."""
    import time

    from app.nlp.chunking import MAX_CHARS

    n = 200_000
    cases = {
        "không âm tiết": "Hệ thống " * 130 + "- , " * (n // 4),
        "ranh giới dày": "X. " * (n // 3),
        "chấm phẩy": "; " * (n // 2),
        "từ dài": "a-b" * (n // 3),
        "chuỗi chấm": "Nội dung " + "." * n + " x",
    }
    for name, text in cases.items():
        start = time.perf_counter()
        result = sentences(strip_boilerplate(text).lines)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"{name}: {elapsed:.2f} s"
        assert all(len(s) <= MAX_CHARS for s in result), name


def test_check_document_signals_exclusion_replace(client, db_path):
    corpus_a = _docx_like([P1, P2, P3, P4])
    r = client.post("/ingest", json={"id": 10, "type": "DOCUMENT", "text": corpus_a}, headers=HEADERS)
    assert r.json() == {"chunk_count": 8, "indexed": True}

    query_paragraphs = [P1, U1, P3, U2, U3]
    query = _pdf_like(query_paragraphs, width=5)
    result = _check(client, query)
    copied = {" ".join(P1), " ".join(P3)}
    assert {d["doan_nguon"] for d in result["chi_tiet"]} == copied
    for detail in result["chi_tiet"]:
        assert detail["ref_id"] == 10
        assert detail["tin_hieu"] == "NGUYEN_VAN"
        assert detail["doan_trung"] == detail["doan_nguon"]
        for removed in REMOVED:
            assert removed not in detail["doan_nguon"]
            assert removed not in detail["doan_trung"]
    all_sentences = [s for p in query_paragraphs for s in p]
    flagged = sum(len(s) for s in P1 + P3)
    expected = 100 * flagged / sum(len(s) for s in all_sentences)
    assert abs(result["ty_le_tong"] - expected) <= 0.01
    assert result["so_doan"] == len(all_sentences)
    assert result["so_doan_loai_tru"] > 0
    assert [d["ref_id"] for d in result["do_an_trung"]] == [10]

    # Chính tài liệu đang kiểm tra và loai_tru không bao giờ được so khớp.
    for kw in ({"loai_tru": [10]}, {"ref_id": 10}):
        excluded = _check(client, query, **kw)
        assert excluded["ty_le_tong"] == 0 and excluded["chi_tiet"] == []

    # Chỉ trùng phần mẫu chung → 0.
    only_template = _check(client, _pdf_like([U1, U2, U3], width=6))
    assert only_template["ty_le_tong"] == 0 and only_template["chi_tiet"] == []

    # Ngưỡng theo request (D-04).
    too_high = client.post(
        "/check-document",
        json={"ref_id": 99, "text": query, "nguong_nguyen_van": 100.01},
        headers=HEADERS,
    )
    assert too_high.status_code == 422
    assert _check(client, query, nguong_doan=0)["ty_le_tong"] == 100.0

    # Giới hạn kích thước: văn bản quá MAX_TEXT_CHARS → 422; thân quá lớn → 413.
    huge = client.post(
        "/check-document", json={"ref_id": 1, "text": "a" * 2_000_001}, headers=HEADERS
    )
    assert huge.status_code == 422
    oversize = client.post(
        "/check-document",
        content=b"{" + b" " * (8 * 1024 * 1024 + 1) + b"}",
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    assert oversize.status_code == 413

    # REPLACE: ingest lại id 10 với nội dung khác → đoạn trùng cũ biến mất.
    client.post("/ingest", json={"id": 10, "type": "DOCUMENT", "text": _docx_like([P2, P4])}, headers=HEADERS)
    replaced = _check(client, query)
    assert replaced["ty_le_tong"] == 0 and replaced["chi_tiet"] == []

    # /reindex có items: một lần encode cho cả lô.
    before = client.get("/health").json()["encode_calls"]
    items = [
        {"id": 20, "type": "DOCUMENT", "text": _docx_like([P1])},
        {"id": 21, "type": "ARCHIVE", "text": "Hệ thống quản lý thư viện trường học"},
    ]
    r = client.post("/reindex", json={"items": items}, headers=HEADERS)
    assert r.json() == {"indexed_count": 2}
    assert client.get("/health").json()["encode_calls"] == before + 1

    # /reindex rỗng: chỉ encode các chunk thiếu embedding rồi dựng lại bộ nhớ.
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        missing = conn.execute(
            text("SELECT id FROM chunk WHERE loai_nguon='DOCUMENT' AND ma_nguon=20")
        ).scalars().all()
        conn.execute(text(f"DELETE FROM embedding WHERE chunk_id IN ({','.join(map(str, missing))})"))
        kept = set(conn.execute(text("SELECT id FROM embedding")).scalars().all())
    before = client.get("/health").json()["encode_calls"]
    r = client.post("/reindex", headers=HEADERS)
    total = client.get("/health").json()
    assert r.json() == {"indexed_count": total["index_size"]}
    assert total["encode_calls"] == before + 1
    assert total["thieu_embedding"] == 0
    with engine.begin() as conn:
        after = set(conn.execute(text("SELECT id FROM embedding")).scalars().all())
    assert kept <= after and len(after - kept) == len(missing)
    assert _check(client, _pdf_like([P1], width=4))["chi_tiet"][0]["ref_id"] == 20
