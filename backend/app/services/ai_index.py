"""AISV-02 / §3.3.8 — đẩy dữ liệu sang chỉ mục của dịch vụ AI ngay khi ghi
(push-on-write), không bao giờ tính lại cả corpus.

- `run_ingest_topic(de_tai_id)`: chạy trong BackgroundTasks SAU commit khi một
  đề tài vào CHO_DUYET (tạo với gui=True hoặc gửi bản nháp) — /ingest
  `{id: de_tai.id, type: TOPIC, text: tên đề tài NFC}` = đúng một lần encode
  (NFR-11). Lỗi AI chỉ ghi cảnh báo, không bao giờ chặn nghiệp vụ (UC1.1 E2).
- `backfill(loai)`: đẩy lại mọi đề tài không phải nháp (TOPIC) và mọi bản ghi
  kho (ARCHIVE). Văn bản không đổi là no-op phía AI, nên chạy lại rẻ và tự
  chữa khi volume thesis_ai bị xóa.
- `purge(loai, ids)`: /ingest với text rỗng (REPLACE bằng không có gì) — CHỈ
  dùng cho phần dọn dẹp của test tự động (e2e) để không để lại vector mồ côi;
  không luồng nghiệp vụ nào gọi hàm này.

CLI (trong container api, chỉ khi AI_CLIENT=http):
    python -m app.services.ai_index backfill [--loai TOPIC ARCHIVE]
    python -m app.services.ai_index purge --loai TOPIC|ARCHIVE|DOCUMENT --ids 1,2,3
"""
import argparse
import logging
import sys

from sqlalchemy import select, update

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.de_tai import NHAP, DeTai
from app.models.kho import CHUA_INDEX, DA_INDEX, DoAnKho
from app.schemas.common import nfc
from app.services.ai_client import get_ai_client
from app.services.archive import ingest_payload

_logger = logging.getLogger(__name__)

LOAI_TOPIC = "TOPIC"
LOAI_ARCHIVE = "ARCHIVE"
LOAI_DOCUMENT = "DOCUMENT"
_COMMIT_EVERY = 50


def run_ingest_topic(de_tai_id: int) -> None:
    """Chạy nền SAU commit — SessionLocal riêng, chỉ id (int) đi qua ranh
    giới request. Bỏ qua đề tài không còn tồn tại hoặc còn là nháp."""
    task_db = SessionLocal()
    try:
        topic = task_db.get(DeTai, de_tai_id)
        if topic is None or topic.trang_thai == NHAP:
            return
        get_ai_client(task_db).ingest(topic.id, LOAI_TOPIC, nfc(topic.ten_de_tai))
    except Exception as exc:  # noqa: BLE001 — không bao giờ chặn nghiệp vụ
        _logger.warning(
            "ai_index.run_ingest_topic thất bại cho de_tai_id=%s (%s)",
            de_tai_id,
            type(exc).__name__,
        )
    finally:
        task_db.close()


def _backfill_topics(db) -> tuple[int, int]:
    client = get_ai_client(db)
    ok = failed = 0
    rows = db.execute(select(DeTai.id, DeTai.ten_de_tai).where(DeTai.trang_thai != NHAP)).all()
    for row in rows:
        try:
            client.ingest(row.id, LOAI_TOPIC, nfc(row.ten_de_tai))
            ok += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            _logger.warning("backfill TOPIC %s thất bại (%s)", row.id, type(exc).__name__)
    return ok, failed


def _backfill_archive(db) -> tuple[int, int]:
    client = get_ai_client(db)
    ok = failed = 0
    ids = db.execute(select(DoAnKho.id).order_by(DoAnKho.id)).scalars().all()
    for n, kho_id in enumerate(ids, start=1):
        kho = db.get(DoAnKho, kho_id)
        if kho is None:
            continue
        loai, text = ingest_payload(db, kho)
        try:
            client.ingest(kho.id, loai, text)
            state = DA_INDEX
            ok += 1
        except Exception as exc:  # noqa: BLE001
            state = CHUA_INDEX
            failed += 1
            _logger.warning("backfill ARCHIVE %s thất bại (%s)", kho_id, type(exc).__name__)
        db.execute(update(DoAnKho).where(DoAnKho.id == kho_id).values(trang_thai_index=state))
        if n % _COMMIT_EVERY == 0:
            db.commit()
    db.commit()
    return ok, failed


def backfill(loai: list[str]) -> dict[str, tuple[int, int]]:
    """Trả {loai: (thành công, thất bại)}."""
    db = SessionLocal()
    try:
        result: dict[str, tuple[int, int]] = {}
        if LOAI_TOPIC in loai:
            result[LOAI_TOPIC] = _backfill_topics(db)
        if LOAI_ARCHIVE in loai:
            result[LOAI_ARCHIVE] = _backfill_archive(db)
        return result
    finally:
        db.close()


def purge(loai: str, ids: list[int]) -> tuple[int, int]:
    """Thay nguồn (loai, id) bằng văn bản rỗng -> không còn chunk nào trong chỉ
    mục AI. CHỈ dùng cho dọn dẹp của test tự động."""
    db = SessionLocal()
    try:
        client = get_ai_client(db)
        ok = failed = 0
        for ref_id in ids:
            try:
                client.ingest(ref_id, loai, "")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                _logger.warning("purge %s %s thất bại (%s)", loai, ref_id, type(exc).__name__)
        return ok, failed
    finally:
        db.close()


def _parse_ids(raw: str) -> list[int]:
    return [int(part) for part in raw.replace(" ", "").split(",") if part]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.services.ai_index")
    sub = parser.add_subparsers(dest="lenh", required=True)
    p_backfill = sub.add_parser("backfill", help="đẩy lại đề tài (TOPIC) và kho (ARCHIVE)")
    p_backfill.add_argument(
        "--loai", nargs="+", choices=[LOAI_TOPIC, LOAI_ARCHIVE], default=[LOAI_TOPIC, LOAI_ARCHIVE]
    )
    p_purge = sub.add_parser("purge", help="xóa nguồn khỏi chỉ mục AI (chỉ cho test)")
    p_purge.add_argument("--loai", required=True, choices=[LOAI_TOPIC, LOAI_ARCHIVE, LOAI_DOCUMENT])
    p_purge.add_argument("--ids", required=True, help="danh sách id, phân cách bằng dấu phẩy")
    args = parser.parse_args(argv)

    if get_settings().AI_CLIENT != "http":
        print("Từ chối: AI_CLIENT không phải 'http' (bộ giả lập không có chỉ mục)", file=sys.stderr)
        return 2

    if args.lenh == "backfill":
        for loai, (ok, failed) in backfill(args.loai).items():
            print(f"backfill {loai}: {ok} thành công, {failed} lỗi")
        return 0

    ids = _parse_ids(args.ids)
    ok, failed = purge(args.loai, ids)
    print(f"purge {args.loai}: {ok} thành công, {failed} lỗi")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main())
