"""Bộ đo PAN chạy trọn đường (profile fake) trên bộ dữ liệu tự đặt: một ca
chép nguyên văn phải được định vị đúng khoảng ký tự ở cả hai phía."""
import json
from pathlib import Path

from app.models import LOAI_DOCUMENT
from app.pipeline import chunk_texts
from evaluation import pan_eval


def test_dinh_vi_cau_bi_so_trang_va_header_cat_ngang():
    header = "Khóa luận tốt nghiệp năm 2026"
    text = "\n".join([
        "Phần mở đầu giới thiệu  bối cảnh của bài toán quản lý thư viện ở trường phổ thông.  ",
        header,
        "  Hệ thống mới giúp thủ thư  theo dõi việc mượn trả ",
        "12",
        header,
        "sách của bạn đọc một cách nhanh chóng và chính xác.",
        "13",
        header,
        "Cuối cùng, bạn đọc nhận thông báo khi sách được trả về kho.",
    ])
    sents = chunk_texts(LOAI_DOCUMENT, text)
    # Số trang và header lặp đã bị lọc: câu thứ hai nối qua hai dòng bị bỏ.
    assert sents[1] == (
        "Hệ thống mới giúp thủ thư theo dõi việc mượn trả sách của bạn đọc một cách nhanh chóng và chính xác."
    )
    spans, du_phong = pan_eval.locate(text, sents)
    assert du_phong == 0
    assert spans == [
        (0, text.index("phổ thông.") + len("phổ thông.")),
        (text.index("Hệ thống mới"), text.index("chính xác.") + len("chính xác.")),
        (text.index("Cuối cùng"), len(text)),
    ]

R001 = [
    "Hệ thống quản lý thư viện giúp thủ thư theo dõi việc mượn trả sách của bạn đọc.",
    "Mỗi cuốn sách được gắn một mã vạch riêng để tra cứu nhanh trong kho lưu trữ.",
    "Bạn đọc có thể đặt trước sách qua trang web và nhận thông báo khi sách sẵn sàng.",
    "Báo cáo thống kê hằng tháng cho biết những đầu sách được mượn nhiều nhất.",
    "Quy trình kiểm kê định kỳ giúp phát hiện sách thất lạc hoặc hư hỏng.",
]
R002 = [
    "Ứng dụng đặt món ăn cho phép khách hàng chọn nhà hàng gần nhất theo vị trí hiện tại.",
    "Người giao hàng nhận đơn trên điện thoại và cập nhật trạng thái theo thời gian thực.",
    "Cửa hàng quản lý thực đơn, giá bán và chương trình khuyến mãi trên một màn hình.",
]
TRUOC = [
    "Trạm quan trắc đo nhiệt độ, độ ẩm và lượng mưa tại cánh đồng mỗi mười lăm phút.",
    "Dữ liệu cảm biến được gửi về máy chủ trung tâm qua mạng di động băng hẹp.",
]
SAU = ["Nông dân xem biểu đồ sinh trưởng của cây lúa ngay trên ứng dụng điện thoại."]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ca_nguyen_van_duoc_dinh_vi(tmp_path: Path):
    data = tmp_path / "pan"
    nguon = "\n".join(R001)
    doan = "\n".join(R001[1:4])
    nghi_van = "\n".join([*TRUOC, doan, *SAU])
    _write(data / "nguon/R001.txt", nguon)
    _write(data / "nguon/R002.txt", "\n".join(R002))
    _write(data / "nghi-van/S001.txt", nghi_van)
    ca = {"id": "C001", "nguon": "R001", "bien_doi": "nguyen_van",
          "nv_bat_dau": nghi_van.index(doan), "nv_do_dai": len(doan),
          "ng_bat_dau": nguon.index(doan), "ng_do_dai": len(doan)}
    nhan = {
        "seed": 1,
        "tham_so": {},
        "nguon": [{"id": r, "tep": f"nguon/{r}.txt", "ten_de_tai": r} for r in ("R001", "R002")],
        "nghi_van": [{"id": "S001", "tep": "nghi-van/S001.txt", "nen": "H001", "co_dao_van": True, "ca": [ca]}],
    }
    _write(data / "nhan.json", json.dumps(nhan, ensure_ascii=False))

    out = tmp_path / "ket-qua"
    assert pan_eval.main(["--data", str(data), "--out", str(out), "--nhan", "thu"]) == 0
    kq = json.loads((out / "ket-qua-thu.json").read_text(encoding="utf-8"))
    assert kq["ca"][0]["recall"] > 0.5
    assert kq["dinh_vi"]["nghi_van"] == {"so_cau": 6, "du_phong": 0, "khong_dinh_vi": 0}
    assert (out / "ket-qua-thu.md").exists()

    # Lần chạy thứ hai đọc vector từ cache đĩa và cho cùng kết quả.
    assert list((data / "cache-vector").glob("*/*.npz"))
    assert pan_eval.main(["--data", str(data), "--out", str(out), "--nhan", "lan-2"]) == 0
    lan_2 = json.loads((out / "ket-qua-lan-2.json").read_text(encoding="utf-8"))
    assert lan_2["tong"] == kq["tong"]
