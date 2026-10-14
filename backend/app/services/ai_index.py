"""AISV-02 / §3.3.8 — đẩy dữ liệu sang chỉ mục của dịch vụ AI ngay khi ghi
(push-on-write), không bao giờ tính lại cả corpus.

- `run_ingest_topic(de_tai_id)`: chạy trong BackgroundTasks SAU commit khi một
  đề tài được GVHD giao cho SV (tạo với gui=True hoặc gửi bản nháp) — /ingest
  `{id: de_tai.id, type: TOPIC, text: tên đề tài NFC}` = đúng một lần encode
  (NFR-11). Lỗi AI chỉ ghi cảnh báo, không bao giờ chặn nghiệp vụ (UC1.1 E2).
- `ingest_document(tai_lieu_do_an_id)` (04-06): gọi SAU khi kiểm tra trùng
  lặp của tài liệu đã commit HOAN_TAT — /ingest `{id, DOCUMENT, văn bản trích
  xuất}` để các lần nộp sau so khớp được với nó (chỉ DE_CUONG/BAO_CAO_CUOI).
- `backfill(loai)`: đẩy lại mọi đề tài không phải nháp và chưa vào kho (TOPIC
  — đề tài đã có dòng do_an_kho do bản ghi ARCHIVE đại diện), mọi bản ghi kho
  (ARCHIVE) và mọi phiên bản đề cương/báo cáo cuối có văn bản (DOCUMENT). Văn
  bản không đổi là no-op phía AI, nên chạy lại rẻ và tự chữa khi volume
  thesis_ai bị xóa.
- `purge(loai, ids)`: /ingest với text rỗng (REPLACE bằng không có gì) — dùng
  cho phần dọn dẹp của test tự động (e2e) để không để lại vector mồ côi.
- `remove_archive(kho_id)` / `remove_archived_topic(kho_id)` (WR-04, 04-REVIEW):
  luồng nghiệp vụ gỡ vector — xóa bản ghi kho gỡ vector ARCHIVE của nó; chốt
  bảo vệ (đồ án vào kho) gỡ vector TOPIC của đề tài, vì bản ghi ARCHIVE mới đại
  diện cho đồ án đó (khớp backfill TOPIC vốn bỏ đề tài đã vào kho). Vector cũ
  không còn chiếm chỗ trong top-k của /check-title.

CLI (trong container api, chỉ khi AI_CLIENT=http):
    python -m app.services.ai_index backfill [--loai TOPIC ARCHIVE DOCUMENT] [--chua-index]
    python -m app.services.ai_index purge --loai TOPIC|ARCHIVE|DOCUMENT --ids 1,2,3
"""
import argparse
import logging
import sys

from sqlalchemy import func, or_, select, update

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.timeutil import now_utc
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, LOAI_DE_CUONG, TaiLieuDoAn
from app.models.de_tai import NHAP, DeTai
from app.models.kho import CHUA_INDEX, DA_INDEX, DoAnKho
from app.models.trung_lap import HOAN_TAT, KetQuaKiemTraTrungLap
from app.schemas.common import nfc
from app.services.ai_client import get_ai_client
from app.services.archive import ingest_payload
from app.services.documents import too_long_for_check

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


_DOCUMENT_LOAI = (LOAI_DE_CUONG, LOAI_BAO_CAO_CUOI)


# WR-06: số tài liệu chưa index được thử lại sau mỗi lần ingest thành công.
_RETRY_PER_INGEST = 3


def pending_documents_query():
    """WR-06: tài liệu đáng lẽ đã nằm trong chỉ mục AI nhưng chưa — đề cương /
    báo cáo cuối có văn bản (trong trần gửi AI), da_index_luc NULL, và kiểm tra
    trùng lặp đã HOAN_TAT hoặc không có (tài liệu seed khóa cũ). Tài liệu đang
    kiểm tra / LOI không tính (luồng "kiểm tra trước, index sau")."""
    return (
        select(TaiLieuDoAn.id)
        .outerjoin(
            KetQuaKiemTraTrungLap,
            KetQuaKiemTraTrungLap.tai_lieu_do_an_id == TaiLieuDoAn.id,
        )
        .where(TaiLieuDoAn.loai.in_(_DOCUMENT_LOAI))
        .where(TaiLieuDoAn.trich_xuat_loi.is_(False))
        .where(TaiLieuDoAn.noi_dung_trich_xuat.is_not(None))
        .where(func.char_length(TaiLieuDoAn.noi_dung_trich_xuat) <= get_settings().AI_DOCUMENT_MAX_CHARS)
        .where(TaiLieuDoAn.da_index_luc.is_(None))
        .where(
            or_(
                KetQuaKiemTraTrungLap.id.is_(None),
                KetQuaKiemTraTrungLap.trang_thai == HOAN_TAT,
            )
        )
    )


def count_pending_documents(db) -> int:
    return int(db.execute(select(func.count()).select_from(pending_documents_query().subquery())).scalar_one())


def _ingest_one(task_db, client, doc_id: int) -> bool:
    """Ingest một tài liệu và đóng dấu da_index_luc; False nếu bỏ qua."""
    doc = task_db.get(TaiLieuDoAn, doc_id)
    if (
        doc is None
        or doc.loai not in _DOCUMENT_LOAI
        or doc.trich_xuat_loi
        or not doc.noi_dung_trich_xuat
        or too_long_for_check(doc.noi_dung_trich_xuat)
    ):
        return False
    text = doc.noi_dung_trich_xuat
    task_db.commit()  # không giữ transaction đọc trong lúc gọi AI
    client.ingest(doc_id, LOAI_DOCUMENT, text)
    task_db.execute(
        update(TaiLieuDoAn).where(TaiLieuDoAn.id == doc_id).values(da_index_luc=now_utc())
    )
    task_db.commit()
    return True


def ingest_document(tai_lieu_do_an_id: int) -> None:
    """AISV-06: đưa một đề cương/báo cáo cuối đã kiểm tra xong vào chỉ mục AI
    (DOCUMENT, id = tai_lieu_do_an.id) — SessionLocal riêng, lỗi chỉ ghi cảnh
    báo (không bao giờ đổi kết quả kiểm tra đã lưu). WR-06: thành công thì
    đóng dấu da_index_luc rồi thử lại vài tài liệu còn chưa index (lỗi ingest
    trước đó, AI khởi động lại…), nên không tài liệu nào bị bỏ sót vĩnh viễn."""
    task_db = SessionLocal()
    try:
        client = get_ai_client(task_db)
        _ingest_one(task_db, client, tai_lieu_do_an_id)
    except Exception as exc:  # noqa: BLE001 — không bao giờ chặn nghiệp vụ
        task_db.rollback()
        _logger.warning(
            "ai_index.ingest_document thất bại cho tai_lieu_do_an_id=%s (%s)",
            tai_lieu_do_an_id,
            type(exc).__name__,
        )
        task_db.close()
        return
    try:
        pending = (
            task_db.execute(
                pending_documents_query()
                .where(TaiLieuDoAn.id != tai_lieu_do_an_id)
                .order_by(TaiLieuDoAn.id)
                .limit(_RETRY_PER_INGEST)
            )
            .scalars()
            .all()
        )
        for doc_id in pending:
            _ingest_one(task_db, client, doc_id)
    except Exception as exc:  # noqa: BLE001
        task_db.rollback()
        _logger.warning("ai_index thử lại tài liệu chưa index thất bại (%s)", type(exc).__name__)
    finally:
        task_db.close()


def _remove(loai: str, ref_id: int | None) -> None:
    """WR-04: REPLACE bằng văn bản rỗng = gỡ nguồn khỏi chỉ mục AI; chạy nền
    sau commit, lỗi chỉ ghi cảnh báo (không bao giờ chặn nghiệp vụ)."""
    if ref_id is None:
        return
    task_db = SessionLocal()
    try:
        get_ai_client(task_db).ingest(ref_id, loai, "")
    except Exception as exc:  # noqa: BLE001 — không bao giờ chặn nghiệp vụ
        _logger.warning("ai_index gỡ %s %s thất bại (%s)", loai, ref_id, type(exc).__name__)
    finally:
        task_db.close()


def remove_archive(do_an_kho_id: int) -> None:
    """WR-04: bản ghi kho đã bị xóa khỏi thesis_core -> gỡ vector ARCHIVE."""
    _remove(LOAI_ARCHIVE, do_an_kho_id)


def remove_archived_topic(do_an_kho_id: int) -> None:
    """WR-04: đồ án vừa vào kho (chốt bảo vệ) -> gỡ vector TOPIC của đề tài,
    bản ghi ARCHIVE thay thế nó trong /check-title."""
    task_db = SessionLocal()
    try:
        kho = task_db.get(DoAnKho, do_an_kho_id)
        de_tai_id = kho.de_tai_id if kho is not None else None
    finally:
        task_db.close()
    _remove(LOAI_TOPIC, de_tai_id)


def _backfill_topics(db) -> tuple[int, int]:
    client = get_ai_client(db)
    ok = failed = 0
    archived = select(DoAnKho.de_tai_id).where(DoAnKho.de_tai_id.is_not(None))
    rows = db.execute(
        select(DeTai.id, DeTai.ten_de_tai)
        .where(DeTai.trang_thai != NHAP)
        .where(DeTai.id.not_in(archived))
    ).all()
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


def _backfill_documents(db, chua_index: bool = False) -> tuple[int, int]:
    """Mọi đề cương/báo cáo cuối có văn bản (hoặc, với chua_index, chỉ các tài
    liệu pending — WR-06); đóng dấu da_index_luc khi thành công."""
    client = get_ai_client(db)
    ok = failed = 0
    if chua_index:
        query = pending_documents_query()
    else:
        query = (
            select(TaiLieuDoAn.id)
            .where(TaiLieuDoAn.loai.in_(_DOCUMENT_LOAI))
            .where(TaiLieuDoAn.trich_xuat_loi.is_(False))
            .where(TaiLieuDoAn.noi_dung_trich_xuat.is_not(None))
        )
    ids = db.execute(query.order_by(TaiLieuDoAn.id)).scalars().all()
    db.commit()
    for doc_id in ids:
        try:
            if _ingest_one(db, client, doc_id):
                ok += 1
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            failed += 1
            _logger.warning("backfill DOCUMENT %s thất bại (%s)", doc_id, type(exc).__name__)
    return ok, failed


def backfill(loai: list[str], chua_index: bool = False) -> dict[str, tuple[int, int]]:
    """Trả {loai: (thành công, thất bại)}."""
    db = SessionLocal()
    try:
        result: dict[str, tuple[int, int]] = {}
        if LOAI_TOPIC in loai:
            result[LOAI_TOPIC] = _backfill_topics(db)
        if LOAI_ARCHIVE in loai:
            result[LOAI_ARCHIVE] = _backfill_archive(db)
        if LOAI_DOCUMENT in loai:
            result[LOAI_DOCUMENT] = _backfill_documents(db, chua_index)
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
    p_backfill = sub.add_parser(
        "backfill", help="đẩy lại đề tài (TOPIC), kho (ARCHIVE) và tài liệu (DOCUMENT)"
    )
    p_backfill.add_argument(
        "--loai",
        nargs="+",
        choices=[LOAI_TOPIC, LOAI_ARCHIVE, LOAI_DOCUMENT],
        default=[LOAI_TOPIC, LOAI_ARCHIVE, LOAI_DOCUMENT],
    )
    p_backfill.add_argument(
        "--chua-index",
        action="store_true",
        help="DOCUMENT: chỉ thử lại tài liệu chưa vào chỉ mục (da_index_luc NULL, WR-06)",
    )
    p_purge = sub.add_parser("purge", help="xóa nguồn khỏi chỉ mục AI (chỉ cho test)")
    p_purge.add_argument("--loai", required=True, choices=[LOAI_TOPIC, LOAI_ARCHIVE, LOAI_DOCUMENT])
    p_purge.add_argument("--ids", required=True, help="danh sách id, phân cách bằng dấu phẩy")
    args = parser.parse_args(argv)

    if get_settings().AI_CLIENT != "http":
        print("Từ chối: AI_CLIENT không phải 'http' (bộ giả lập không có chỉ mục)", file=sys.stderr)
        return 2

    if args.lenh == "backfill":
        for loai, (ok, failed) in backfill(args.loai, args.chua_index).items():
            print(f"backfill {loai}: {ok} thành công, {failed} lỗi")
        db = SessionLocal()
        try:
            print(f"tài liệu chưa vào chỉ mục AI: {count_pending_documents(db)}")
        finally:
            db.close()
        return 0

    ids = _parse_ids(args.ids)
    ok, failed = purge(args.loai, ids)
    print(f"purge {args.loai}: {ok} thành công, {failed} lỗi")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main())
