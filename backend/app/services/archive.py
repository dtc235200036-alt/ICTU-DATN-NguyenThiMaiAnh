"""UC5 — Kho đồ án (D-07). Phần này (plan 03-04): tự lưu kho khi Bộ môn chốt
kết quả bảo vệ (UC5.2) và đẩy bản ghi sang Dịch vụ AI để index qua seam
`ai_client` sau commit. Plan 03-05 bổ sung tìm kiếm/CRUD/import CSV.

Quy tắc payload /ingest (§3.3.5 `{id, type: TOPIC|DOCUMENT, text}`):
ref_id = do_an_kho.id; DOCUMENT kèm văn bản trích xuất của phiên bản báo cáo
cuối mới nhất khi có, ngược lại TOPIC với "ten_de_tai\\ntu_khoa"."""
import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.bao_ve import LichBaoVe
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, TaiLieuDoAn
from app.models.de_tai import DeTai
from app.models.kho import CHUA_INDEX, DA_INDEX, HE_THONG, DoAnKho
from app.models.tai_khoan import SinhVien
from app.services.ai_client import get_ai_client

_logger = logging.getLogger(__name__)

INGEST_DOCUMENT = "DOCUMENT"
INGEST_TOPIC = "TOPIC"


def insert_from_defense(db: Session, lich: LichBaoVe) -> DoAnKho:
    """UC5.2/REPO-01: một bản ghi kho HE_THONG cho SV vừa được chốt điểm —
    add + flush, KHÔNG commit (caller — defense.finalize — commit cùng lúc với
    da_chot và thông báo). UNIQUE(de_tai_id) chặn chèn trùng khi đua nhau."""
    topic = db.get(DeTai, lich.de_tai_id)
    sv = db.get(SinhVien, lich.sinh_vien_id)
    khoa = topic.dot_do_an.khoa if topic is not None and topic.dot_do_an is not None else None
    kho = DoAnKho(
        de_tai_id=lich.de_tai_id,
        sinh_vien_id=lich.sinh_vien_id,
        giang_vien_id=topic.giang_vien_id if topic is not None else None,
        khoa=khoa,
        ten_de_tai=topic.ten_de_tai if topic is not None else "",
        tu_khoa=None,
        diem=lich.diem_trung_binh,
        nguon=HE_THONG,
        trang_thai_index=CHUA_INDEX,
        ma_so_sinh_vien=sv.ma_so_sinh_vien if sv is not None else None,
        ho_ten_sinh_vien=sv.ho_ten if sv is not None else None,
    )
    db.add(kho)
    db.flush()
    return kho


def latest_final_report(db: Session, de_tai_id: int | None) -> TaiLieuDoAn | None:
    """"File" của bản ghi kho = phiên bản BAO_CAO_CUOI mới nhất của đề tài
    (không có cột riêng — D-07)."""
    if de_tai_id is None:
        return None
    return (
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == de_tai_id)
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
            .order_by(TaiLieuDoAn.so_phien_ban.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def ingest_payload(db: Session, kho: DoAnKho) -> tuple[str, str]:
    doc = latest_final_report(db, kho.de_tai_id)
    if doc is not None and not doc.trich_xuat_loi and doc.noi_dung_trich_xuat:
        return INGEST_DOCUMENT, doc.noi_dung_trich_xuat
    return INGEST_TOPIC, f"{kho.ten_de_tai}\n{kho.tu_khoa or ''}".strip()


def run_ingest(do_an_kho_ids: list[int]) -> None:
    """Chạy nền SAU commit (BackgroundTasks) — mở SessionLocal RIÊNG; mỗi id
    một try/except độc lập: lỗi AI để nguyên CHUA_INDEX, ghi log và sang id
    kế tiếp (UC5.2 E1 — không bao giờ chặn lưu kho; Bộ môn index lại sau)."""
    task_db = SessionLocal()
    try:
        for kho_id in do_an_kho_ids:
            try:
                kho = task_db.get(DoAnKho, kho_id)
                if kho is None:
                    continue
                loai, text = ingest_payload(task_db, kho)
                get_ai_client(task_db).ingest(kho.id, loai, text)
                task_db.execute(
                    update(DoAnKho).where(DoAnKho.id == kho_id).values(trang_thai_index=DA_INDEX)
                )
                task_db.commit()
            except Exception:
                task_db.rollback()
                try:
                    task_db.execute(
                        update(DoAnKho)
                        .where(DoAnKho.id == kho_id)
                        .values(trang_thai_index=CHUA_INDEX)
                    )
                    task_db.commit()
                except Exception:
                    task_db.rollback()
                _logger.exception("archive.run_ingest thất bại cho do_an_kho_id=%s", kho_id)
    finally:
        task_db.close()
