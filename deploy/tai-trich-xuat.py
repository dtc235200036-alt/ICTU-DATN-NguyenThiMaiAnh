"""Trích xuất lại mọi tài liệu PDF đã lưu bằng extract_text mới (một lần, sau deploy).
Chạy: docker compose -f deploy/docker-compose.yml exec -T api python - < deploy/tai-trich-xuat.py
Không bao giờ ghi đè văn bản cũ bằng None; chỉ cập nhật khi văn bản đổi."""
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.de_cuong import PDF, TaiLieuDoAn
from app.services.documents import extract_text, storage_path

db = SessionLocal()
doi = giu = thieu_tep = 0
try:
    ids = db.execute(
        select(TaiLieuDoAn.id).where(TaiLieuDoAn.dinh_dang == PDF).order_by(TaiLieuDoAn.id)
    ).scalars().all()
    for doc_id in ids:
        doc = db.get(TaiLieuDoAn, doc_id)
        try:
            content = storage_path(doc.ten_luu_tru).read_bytes()
        except OSError:
            thieu_tep += 1
            continue
        text = extract_text(content, doc.dinh_dang)
        if text is not None and text != doc.noi_dung_trich_xuat:
            doc.noi_dung_trich_xuat = text
            doc.trich_xuat_loi = False
            doi += 1
        else:
            giu += 1
        db.commit()
finally:
    db.close()
print(f"PDF: {len(ids)}; cập nhật {doi}, giữ nguyên {giu}, thiếu tệp {thieu_tep}")
