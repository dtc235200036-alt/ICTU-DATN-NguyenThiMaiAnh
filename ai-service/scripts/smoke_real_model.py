"""Smoke mô hình thật + đo thông lượng CPU trên máy này (Pitfall D).

    uv run python scripts/smoke_real_model.py --profile bkai

Dùng SQLite tạm + Encoder thật (mỗi tiến trình chỉ nạp MỘT mô hình). In một
dòng JSON {profile, model, load_s, title_query_ms, encode_300_s, peak_rss_mb};
thoát 1 khi tiêu đề diễn đạt lại không đứng đầu, NFC/NFD lệch, hoặc
encode_300_s > 20 (ngân sách NFR-09 30 s trừ chi phí phía Web API).
"""
import argparse
import itertools
import json
import os
import resource
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

TITLES = [
    "Xây dựng hệ thống quản lý thư viện cho trường trung học phổ thông",
    "Ứng dụng học sâu nhận diện biển số xe máy tại bãi gửi xe",
    "Website thương mại điện tử bán đồ gia dụng tích hợp thanh toán trực tuyến",
    "Hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt",
    "Ứng dụng di động đặt lịch khám bệnh cho phòng khám tư nhân",
]
QUERY = "Phát triển phần mềm quản lý thư viện trường THPT"

_CHU_THE = [
    "Hệ thống", "Mô-đun quản trị", "Ứng dụng di động", "Dịch vụ nền",
    "Cơ sở dữ liệu", "Giao diện người dùng", "Bộ phận kiểm thử", "Máy chủ ứng dụng",
    "Thuật toán gợi ý", "Tầng nghiệp vụ",
]
_HANH_DONG = [
    "cho phép quản lý thông tin", "tự động tổng hợp báo cáo về",
    "ghi nhận và lưu trữ lịch sử của", "kiểm tra tính hợp lệ của",
    "gửi thông báo khi có thay đổi đối với", "phân quyền truy cập vào",
]
_DOI_TUONG = [
    "sinh viên và giảng viên hướng dẫn", "các đơn hàng trong ngày",
    "hồ sơ bệnh nhân tại phòng khám", "sách mượn trả của thư viện",
    "tiến độ thực hiện đồ án",
]
_BOI_CANH = [
    "nhằm giảm thời gian xử lý thủ công của cán bộ.",
    "trong môi trường mạng nội bộ của nhà trường.",
    "dựa trên kiến trúc hướng dịch vụ đã thiết kế ở chương trước.",
    "với dữ liệu được chuẩn hóa theo bảng mã Unicode.",
    "đáp ứng yêu cầu phi chức năng về thời gian phản hồi.",
]


def sentences_300() -> list[str]:
    combos = itertools.product(_CHU_THE, _HANH_DONG, _DOI_TUONG, _BOI_CANH)
    return [f"{a} {b} {c} {d}" for a, b, c, d in itertools.islice(combos, 300)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["bkai", "e5"], required=True)
    args = parser.parse_args()

    tmp = tempfile.mkdtemp(prefix="ai-smoke-")
    db = Path(tmp) / "thesis_ai.db"
    os.environ.update(
        APP_ENV="smoke",
        AI_MODEL_PROFILE=args.profile,
        AI_API_KEY="s" * 40,
        DATABASE_URL=f"sqlite:///{db}",
    )

    from alembic import command
    from alembic.config import Config

    from app import pipeline
    from app.core.config import get_settings
    from app.db import make_engine, make_session_factory
    from app.embedding import Encoder
    from app.index import CorpusIndex

    cfg = Config(str(SERVICE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVICE_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db}")
    command.upgrade(cfg, "head")

    settings = get_settings()
    t0 = time.perf_counter()
    encoder = Encoder(args.profile, settings.TORCH_THREADS)
    load_s = time.perf_counter() - t0

    index = CorpusIndex(encoder.dim)
    factory = make_session_factory(make_engine(settings.DATABASE_URL))
    with factory() as session:
        for i, title in enumerate(TITLES, start=1):
            pipeline.ingest(session, index, encoder, "ARCHIVE", i, title)

    t0 = time.perf_counter()
    matches = pipeline.check_title(index, encoder, QUERY, 5, None)
    title_query_ms = (time.perf_counter() - t0) * 1000
    nfd = pipeline.check_title(index, encoder, unicodedata.normalize("NFD", QUERY), 5, None)

    texts = sentences_300()
    assert len(set(texts)) == 300
    t0 = time.perf_counter()
    encoder.encode(texts)
    encode_300_s = time.perf_counter() - t0

    result = {
        "profile": args.profile,
        "model": encoder.name,
        "load_s": round(load_s, 2),
        "title_query_ms": round(title_query_ms, 1),
        "encode_300_s": round(encode_300_s, 2),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "torch_threads": settings.TORCH_THREADS,
        "top": matches[:3],
    }
    print(json.dumps(result, ensure_ascii=False))

    ok = True
    if not matches or matches[0]["ref_id"] != 1:
        print("FAIL: tiêu đề thư viện không đứng đầu", file=sys.stderr)
        ok = False
    elif len(matches) > 1 and not matches[0]["ty_le"] > matches[1]["ty_le"]:
        print("FAIL: top-1 không cao hơn hẳn top-2", file=sys.stderr)
        ok = False
    if nfd != matches:
        print("FAIL: NFC và NFD cho kết quả khác nhau", file=sys.stderr)
        ok = False
    if encode_300_s > 20:
        print(f"FAIL: encode 300 câu mất {encode_300_s:.1f}s > 20s", file=sys.stderr)
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
