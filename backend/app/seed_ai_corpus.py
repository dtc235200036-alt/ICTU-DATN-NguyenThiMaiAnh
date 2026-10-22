"""DATA-03 / D-06 (plan 04-06): nạp 25 tài liệu nguồn (A) của seed-data vào hệ
thống như đồ án của các khóa trước — để bài nộp của sinh viên (tài liệu B)
được kiểm tra trùng lặp với chúng qua đúng đường nghiệp vụ.

Với mỗi cặp trong seed-data/manifest.json:
  - tìm bản ghi kho IMPORT khớp (khoa, ten_de_tai) — do bước import CSV của
    deploy/seed-ai.sh tạo (DATA-02);
  - lấy/tạo đợt "Dữ liệu lịch sử {khóa}" (DA_DONG — không bao giờ mở đăng ký);
  - tạo de_tai DA_PHAN_CONG của GVHD ghi trong manifest (sinh_vien_id NULL:
    SV khóa cũ không có tài khoản; ảnh chụp mã/họ tên SV nằm ở do_an_kho);
  - lưu file qua documents.validate_bytes + documents.store (BAO_CAO_CUOI) —
    cùng bộ kiểm tra magic bytes và trích xuất văn bản của Web API;
  - liên kết do_an_kho.de_tai_id, commit, rồi /ingest DOCUMENT.
Tài liệu B KHÔNG được nạp — chúng là bài nộp dùng khi demo/e2e.

Chạy lại không đổi gì: bản ghi kho đã liên kết một đề tài có báo cáo cuối thì
bỏ qua. Đây là công cụ seed (không phải tính năng) — chạy trong container api:

    python -m app.seed_ai_corpus --data /seed-data
"""
import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.de_cuong import LOAI_BAO_CAO_CUOI, TaiLieuDoAn
from app.models.de_tai import DA_PHAN_CONG, GIANG_VIEN, DeTai
from app.models.dot_do_an import DA_DONG, DotDoAn
from app.models.kho import IMPORT, DoAnKho
from app.models.tai_khoan import GiangVien
from app.schemas.common import nfc
from app.services import documents
from app.services.ai_client import get_ai_client
from app.services.ai_index import LOAI_DOCUMENT

_logger = logging.getLogger(__name__)

MO_TA = "Đồ án khóa cũ — dữ liệu thử nghiệm DATA-03"


class SeedError(Exception):
    pass


def _nam_vao(khoa: str) -> int:
    """K22 -> 2022 (năm nhập học của khóa)."""
    digits = "".join(ch for ch in khoa if ch.isdigit())
    if not digits:
        raise SeedError(f"Khóa không hợp lệ: {khoa!r}")
    return 2000 + int(digits)


def _dot_lich_su(db: Session, khoa: str) -> DotDoAn:
    """Đợt khớp CẢ ten_dot lẫn khoa — không bao giờ dùng lại một đợt khác của
    cùng khóa (vd. đợt K22 đang mở của seed demo)."""
    ten_dot = f"Dữ liệu lịch sử {khoa}"
    dot = db.execute(
        select(DotDoAn).where(DotDoAn.ten_dot == ten_dot).where(DotDoAn.khoa == khoa)
    ).scalar_one_or_none()
    if dot is not None:
        return dot
    nam_tot_nghiep = _nam_vao(khoa) + 4
    dot = DotDoAn(
        ten_dot=ten_dot,
        khoa=khoa,
        nam_hoc=f"{nam_tot_nghiep - 1}-{nam_tot_nghiep}",
        ngay_bat_dau=date(nam_tot_nghiep, 2, 1),
        ngay_ket_thuc=date(nam_tot_nghiep, 6, 30),
        trang_thai=DA_DONG,
    )
    db.add(dot)
    db.flush()
    return dot


def _has_final_report(db: Session, de_tai_id: int) -> bool:
    return (
        db.execute(
            select(func.count())
            .select_from(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == de_tai_id)
            .where(TaiLieuDoAn.loai == LOAI_BAO_CAO_CUOI)
        ).scalar_one()
        > 0
    )


def _find_archive(db: Session, khoa: str, ten_de_tai: str) -> DoAnKho:
    kho = (
        db.execute(
            select(DoAnKho)
            .where(DoAnKho.nguon == IMPORT)
            .where(DoAnKho.khoa == khoa)
            .where(DoAnKho.ten_de_tai == nfc(ten_de_tai))
            .order_by(DoAnKho.id)
        )
        .scalars()
        .first()
    )
    if kho is None:
        raise SeedError(
            f"Không thấy bản ghi kho IMPORT ({khoa}, {ten_de_tai!r}) —"
            " chạy bước import của deploy/seed-ai.sh trước"
        )
    return kho


def _seed_one(db: Session, data_dir: Path, ma_cap: str, a: dict) -> tuple[str, int | None, int | None]:
    """Trả (trạng thái, đợt id, tai_lieu_do_an id) — trạng thái 'moi' | 'da_co'."""
    khoa = a["khoa"]
    kho = _find_archive(db, khoa, a["ten_de_tai"])
    if kho.de_tai_id is not None and _has_final_report(db, kho.de_tai_id):
        topic = db.get(DeTai, kho.de_tai_id)
        return "da_co", topic.dot_do_an_id if topic is not None else None, None

    path = (data_dir / a["tep"]).resolve()
    if data_dir.resolve() not in path.parents:
        raise SeedError(f"{ma_cap}: đường dẫn tệp nằm ngoài thư mục dữ liệu: {a['tep']}")
    if not path.is_file():
        raise SeedError(f"{ma_cap}: không thấy tệp {path}")
    try:
        vf = documents.validate_bytes(path.read_bytes(), path.name)
    except HTTPException as exc:
        raise SeedError(f"{ma_cap}: tệp không hợp lệ ({exc.detail})") from None
    if not vf.text:
        raise SeedError(f"{ma_cap}: không trích xuất được văn bản từ {path.name}")

    dot = _dot_lich_su(db, khoa)
    if kho.de_tai_id is not None:
        topic = db.get(DeTai, kho.de_tai_id)
    else:
        gv = db.execute(
            select(GiangVien).where(GiangVien.ma_giang_vien == a["ma_giang_vien"])
        ).scalar_one_or_none()
        topic = DeTai(
            dot_do_an_id=dot.id,
            giang_vien_id=gv.id if gv is not None else kho.giang_vien_id,
            sinh_vien_id=None,
            ten_de_tai=kho.ten_de_tai,
            mo_ta=MO_TA,
            trang_thai=DA_PHAN_CONG,
            loai_nguoi_de_xuat=GIANG_VIEN,
        )
        db.add(topic)
        db.flush()

    doc = documents.store(db, de_tai_id=topic.id, loai=LOAI_BAO_CAO_CUOI, vf=vf)
    kho.de_tai_id = topic.id
    try:
        db.commit()
    except Exception:
        db.rollback()
        documents.remove_file_quietly(doc.ten_luu_tru)
        raise
    return "moi", topic.dot_do_an_id, doc.id


def seed(data_dir: Path) -> int:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"Không thấy {manifest_path}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    db = SessionLocal()
    seeded: list[tuple[str, str, int | None, int]] = []
    existing = 0
    ingest_failed: list[str] = []
    try:
        client = get_ai_client(db)
        for cap in manifest["cap"]:
            ma_cap = cap["ma_cap"]
            try:
                state, dot_id, doc_id = _seed_one(db, data_dir, ma_cap, cap["A"])
            except SeedError as exc:
                db.rollback()
                print(f"FAIL: {exc}", file=sys.stderr)
                return 1
            if state == "da_co":
                existing += 1
                continue
            doc = db.get(TaiLieuDoAn, doc_id)
            try:
                client.ingest(doc_id, LOAI_DOCUMENT, doc.noi_dung_trich_xuat, nhom=doc.de_tai_id)
            except Exception as exc:  # noqa: BLE001 — backfill DOCUMENT sửa lại sau
                ingest_failed.append(f"{ma_cap} ({type(exc).__name__})")
            seeded.append((ma_cap, cap["A"]["khoa"], dot_id, doc_id))
    finally:
        db.close()

    for ma_cap, khoa, dot_id, doc_id in seeded:
        print(f"  {ma_cap}: {khoa} đợt #{dot_id}, tai_lieu_do_an #{doc_id}")
    print(f"OK: {len(seeded) + existing} đồ án nguồn (mới {len(seeded)}, đã có {existing})")
    if ingest_failed:
        print(
            "CẢNH BÁO: ingest DOCUMENT lỗi cho " + ", ".join(ingest_failed)
            + " — chạy `python -m app.services.ai_index backfill --loai DOCUMENT`",
            file=sys.stderr,
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.seed_ai_corpus")
    parser.add_argument("--data", default="/seed-data", help="thư mục seed-data (có manifest.json)")
    args = parser.parse_args(argv)
    return seed(Path(args.data))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main())
