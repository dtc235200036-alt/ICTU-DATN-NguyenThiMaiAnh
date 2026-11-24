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


def test_section_headings_cannot_hide_chapters():
    """CR-04 (04-REVIEW): một dòng "Phụ lục" chèn dưới mỗi tiêu đề chương không
    được làm cả chương biến khỏi phép kiểm tra; tài liệu không có tiêu đề lớn
    cũng không bị xóa sạch bằng các dòng "Phụ lục" lặp lại."""
    body = [
        "CHƯƠNG 1. TỔNG QUAN", "Phụ lục", *P1, *P2,
        "CHƯƠNG 2. THIẾT KẾ", "Phụ lục", *P3, *P4,
        "KẾT LUẬN", "Phụ lục", *U1,
        "TÀI LIỆU THAM KHẢO", *REFS[1:],
    ]
    kept = strip_boilerplate("\n".join(COVER + FRONT + body))
    assert sentences(kept.lines) == P1 + P2 + P3 + P4
    assert 0 < kept.removed_chars < kept.total_chars

    # Không có CHƯƠNG/MỞ ĐẦU/KẾT LUẬN: trần độ dài giữ phần lớn nội dung.
    prose = [f"Câu nội dung số {i} mô tả chức năng quản lý thư viện của trường." for i in range(300)]
    flat = []
    for i, line in enumerate(prose):
        if i % 30 == 0:
            flat.append("Phụ lục")
        flat.append(line)
    result = strip_boilerplate("\n".join(flat))
    assert len(result.lines) >= 0.55 * len(prose)  # trần tổng 40 % số dòng

    # Nhãn bìa đứng riêng ngay trước tiêu đề lớn không được "nuốt" tiêu đề đó
    # (nếu nuốt, mục LỜI CAM ĐOAN đang mở lan sang cả phần MỞ ĐẦU).
    for label in ("Lớp:", "Đề tài:"):
        doc = COVER + FRONT[:3] + [label, "MỞ ĐẦU", *P1, "KẾT LUẬN", *P2]
        assert sentences(strip_boilerplate("\n".join(doc)).lines) == P1 + P2, label


def test_spaced_dot_leaders_and_cover_values():
    """pan-eval (105 đồ án): PDF từ LaTeX ghi mục lục/danh mục hình bằng dải chấm
    cách ". . . ." (số trang thường rơi xuống dòng sau, có dòng chỉ có dải chấm);
    bìa + phụ bìa đặt nhãn và giá trị trên hai dòng — tên GVHD, lớp chỉ lặp 2 lần
    nên quy tắc (e) không bắt, và trùng nguyên văn giữa các đồ án cùng GVHD."""
    cover = [
        "KHOA CÔNG NGHỆ THÔNG TIN",
        "Giảng viên hướng dẫn:", "TS. Lê Văn Cường",
        "Sinh viên thực hiện:", "Phạm Thị Dung",
        "Lớp:", "Kỹ thuật phần mềm K22B",
    ]
    front = cover + cover[:1] + ["Giáo viên hướng dẫn:"] + cover[2:] + [
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "Độc lập - Tự do - Hạnh phúc",
        "MỤC LỤC",
        # Số trang ở dòng sau: dòng chương trong mục lục bị coi là tiêu đề lớn,
        # kết thúc mục (a) sớm → các dòng dưới chỉ còn quy tắc (c) chặn.
        "CHƯƠNG 1. TỔNG QUAN", "1",
        "1.1. Khảo sát hiện trạng thư viện . . . . . . . . . . . .",
        "Quy trình mượn trả sách hiện tại . . . . . . . . . .", "2",
        "1.2. Phân tích yêu cầu", ". . . . . . . . . . . . . .", "3",
        "Biểu đồ hoạt động mượn sách . . . . . . . . 6",
    ]
    ellipsis = [
        "Thủ thư quét mã vạch, chờ hệ thống tra cứu . . . rồi xác nhận lượt mượn.",
        "Mã bản sao được đánh số 1, 2, . . . . , n theo thứ tự nhập kho.",
        "Nếu quá hạn, hệ thống nhắc độc giả mỗi ngày cho tới khi trả sách . . .",
    ]
    body = [
        "CHƯƠNG 1. TỔNG QUAN", *P1, *ellipsis,
        # Nhãn bìa chèn vào thân bài không kéo theo dòng nội dung ngay sau nó.
        "CHƯƠNG 2. THIẾT KẾ", "Giảng viên hướng dẫn:", *_wrap(P3, 7),
        "KẾT LUẬN", *U2,
    ]
    kept = strip_boilerplate("\n".join(front + body))
    assert sentences(kept.lines) == P1 + ellipsis + P3 + U2


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
        "chuỗi chấm không số trang": "Nội dung " + "." * n + " nội dung",
        "chuỗi chấm cách": "Nội dung " + ". " * (n // 2) + "nội dung",
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


def test_passage_labels_nguyen_van_sua_nhe_ngu_nghia():
    """Nhãn đoạn: đa số ký tự gắn cờ vân tay → NGUYEN_VAN khi chữ khớp y hệt
    đoạn nguồn (tỷ lệ khớp chữ ≥ NGUONG_SUA_NHE), SUA_NHE khi đã sửa; đa số
    ngữ nghĩa → NGU_NGHIA. diem_nguyen_van thấp (mép câu) không đổi nhãn của
    bản chép y hệt. SUA_NHE chỉ là nhãn hiển thị: cờ từng câu và tỷ lệ không đổi."""
    from app.pipeline import ChunkScore, DocumentScores, check_document

    goc = "Hệ thống quản lý đồ án tốt nghiệp giúp giảng viên theo dõi tiến độ của sinh viên hằng tuần."
    sua = "Hệ thống quản trị đồ án tốt nghiệp giúp giảng viên giám sát tiến độ sinh viên hằng tuần."

    def chunk(vi_tri: int, ref: int | None, verb: float, sem: float) -> ChunkScore:
        text = {1: goc, 3: sua}.get(vi_tri, f"Câu thứ {vi_tri} của tài liệu đang được kiểm tra.")
        src = (goc if vi_tri in (1, 3) else f"Câu thứ {vi_tri} của đồ án nguồn.") if ref else None
        return ChunkScore(vi_tri=vi_tri, text=text, n_chars=len(text),
                          sem_ref=ref, sem_text=src, sem_thu_tu=vi_tri if ref else None, sem_score=sem,
                          verb_ref=ref, verb_text=src, verb_thu_tu=vi_tri if ref else None, verb_score=verb)

    chunks = [
        chunk(1, 1, 0.8, 0.99),  # chép y hệt, độ phủ hụt ở mép câu → vẫn nguyên văn
        chunk(2, None, 0.0, 0.0),
        chunk(3, 2, 0.9, 0.99),  # thay 2 từ, bỏ 1 hư từ → sửa nhẹ
        chunk(4, None, 0.0, 0.0),
        chunk(5, 3, 0.3, 0.9),  # độ phủ dưới ngưỡng nguyên văn, cosine đạt → ngữ nghĩa
        chunk(6, 3, 0.3, 0.9),
    ]
    res = check_document(DocumentScores(chunks, 0), 80.0, 60.0, top_k=5, chi_tiet_toi_da=10)
    by_vi_tri = {d["vi_tri"]: d for d in res["chi_tiet"]}
    assert {k: d["tin_hieu"] for k, d in by_vi_tri.items()} == {
        "Câu 1": "NGUYEN_VAN", "Câu 3": "SUA_NHE", "Câu 5–6": "NGU_NGHIA",
    }
    assert (by_vi_tri["Câu 1"]["diem_nguyen_van"], by_vi_tri["Câu 3"]["diem_nguyen_van"]) == (80.0, 90.0)
    flagged = sum(c.n_chars for c in chunks if c.verb_ref)
    assert res["ty_le_tong"] == round(100 * flagged / sum(c.n_chars for c in chunks), 2)
    assert {d["ref_id"] for d in res["do_an_trung"]} == {1, 2, 3}


def test_check_then_ingest_reuses_vectors(client):
    """CR-02 (04-REVIEW): Web API ingest DOCUMENT ngay sau /check-document của
    cùng tài liệu — dùng lại vector đã mã hóa lúc kiểm tra, không mã hóa lần hai."""
    text = _docx_like([P1, P2, P3])
    _check(client, text, ref_id=42)
    before = client.get("/health").json()["encode_calls"]
    r = client.post("/ingest", json={"id": 42, "type": "DOCUMENT", "text": text}, headers=HEADERS)
    assert r.status_code == 200 and r.json()["chunk_count"] == 6
    assert client.get("/health").json()["encode_calls"] == before
    # Vector dùng lại đúng là vector của các câu đó: bản sao khớp tài liệu 42.
    result = _check(client, text, ref_id=0)
    assert result["do_an_trung"][0] == {"ref_id": 42, "ty_le": 100.0}
    # Ingest lại (không còn trong bộ nhớ đệm, văn bản đổi) thì mã hóa bình thường.
    before = client.get("/health").json()["encode_calls"]
    client.post("/ingest", json={"id": 42, "type": "DOCUMENT", "text": _docx_like([P4])}, headers=HEADERS)
    assert client.get("/health").json()["encode_calls"] == before + 1
