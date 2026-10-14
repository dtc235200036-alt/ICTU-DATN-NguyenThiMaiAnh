"""Seed dữ liệu (DATA-01, D-13): Bộ môn, danh sách SV K22 thật (seed_data/sinh_vien.csv,
đăng nhập bằng mã SV), danh sách GV Khoa CNTT thật (seed_data/giang_vien.csv, mã
GV001.. theo STT, đăng nhập bằng mã hoặc email), một đợt đồ án mở và phân công
GVHD mặc định cho đợt đó (UC0.8: SV thứ i -> GV thứ ((i-1) mod số GV)+1).
Mọi tài khoản dùng chung mật khẩu SEED_DEFAULT_PASSWORD.

Chạy: python -m app.seed

Idempotent: chạy lại không tạo trùng, không đổi dữ liệu của tài khoản/đợt đồ án
đã tồn tại — chỉ tạo phần còn thiếu (khớp ma_dang_nhap / ten_dot).
"""
import csv
import sys
import unicodedata
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.roles import VaiTro
from app.core.security import hash_password
from app.core.timeutil import now_utc
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.phan_cong import PhanCongHuongDan
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan

BO_MON_MA_DANG_NHAP = "bomon"
BO_MON_EMAIL = "bomon@ictu.edu.vn"

SEED_DATA_DIR = Path(__file__).parent / "seed_data"
KHOA_SV = "Công nghệ thông tin"

# UC1 demo: một đợt đồ án đang mở theo K22 — không bao giờ đổi trạng thái nếu
# đã tồn tại (chạy lại seed không được phép đóng một đợt đang mở cho demo).
COHORT_TEN_DOT = "Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)"
COHORT_KHOA = "K22"
COHORT_NAM_HOC = "2026-2027"
COHORT_NGAY_BAT_DAU = date(2026, 9, 28)
COHORT_NGAY_KET_THUC = date(2026, 12, 7)


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _load_csv(name: str) -> list[dict[str, str]]:
    with open(SEED_DATA_DIR / name, encoding="utf-8-sig", newline="") as f:
        return [
            {k: _nfc(v.strip()) for k, v in row.items()}
            for row in csv.DictReader(f)
        ]


def _ensure_bo_mon(db: Session, password_hash: str) -> None:
    existing = db.execute(
        select(TaiKhoan).where(TaiKhoan.ma_dang_nhap == BO_MON_MA_DANG_NHAP)
    ).scalar_one_or_none()
    if existing is not None:
        return
    db.add(
        TaiKhoan(
            ma_dang_nhap=BO_MON_MA_DANG_NHAP,
            email=BO_MON_EMAIL,
            mat_khau_bam=password_hash,
            vai_tro=VaiTro.BO_MON,
            bi_khoa=False,
        )
    )


def _ensure_giang_vien(db: Session, rows: list[dict[str, str]], password_hash: str) -> int:
    created = 0
    for row in rows:
        code = row["ma_giang_vien"]
        existing = db.execute(
            select(TaiKhoan).where(TaiKhoan.ma_dang_nhap == code)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        email = row["email"]

        account = TaiKhoan(
            ma_dang_nhap=code,
            email=email,
            mat_khau_bam=password_hash,
            vai_tro=VaiTro.GIANG_VIEN,
            bi_khoa=False,
        )
        db.add(account)
        db.flush()

        db.add(
            GiangVien(
                tai_khoan_id=account.id,
                ma_giang_vien=code,
                ho_ten=row["ho_ten"],
                email=email,
                hoc_vi=row["hoc_vi"] or None,
            )
        )
        created += 1
    return created


def _ensure_sinh_vien(db: Session, rows: list[dict[str, str]], password_hash: str) -> int:
    created = 0
    for row in rows:
        code = row["ma_so_sinh_vien"]
        existing = db.execute(
            select(TaiKhoan).where(TaiKhoan.ma_dang_nhap == code)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        email = f"{code.lower()}@ictu.edu.vn"

        account = TaiKhoan(
            ma_dang_nhap=code,
            email=email,
            mat_khau_bam=password_hash,
            vai_tro=VaiTro.SINH_VIEN,
            bi_khoa=False,
        )
        db.add(account)
        db.flush()

        db.add(
            SinhVien(
                tai_khoan_id=account.id,
                ma_so_sinh_vien=code,
                ho_ten=row["ho_ten"],
                email=email,
                lop=row["lop"],
                khoa=KHOA_SV,
            )
        )
        created += 1
    return created


def _ensure_open_cohort(db: Session) -> bool:
    existing = db.execute(
        select(DotDoAn).where(DotDoAn.ten_dot == COHORT_TEN_DOT)
    ).scalar_one_or_none()
    if existing is not None:
        return False

    db.add(
        DotDoAn(
            ten_dot=COHORT_TEN_DOT,
            khoa=COHORT_KHOA,
            nam_hoc=COHORT_NAM_HOC,
            ngay_bat_dau=COHORT_NGAY_BAT_DAU,
            ngay_ket_thuc=COHORT_NGAY_KET_THUC,
            trang_thai=DANG_MO,
        )
    )
    return True


def _ensure_assignments(
    db: Session, sv_rows: list[dict[str, str]], gv_rows: list[dict[str, str]]
) -> int:
    """UC0.8: SV chưa có GVHD trong đợt demo được gán vòng tròn theo thứ tự trong
    danh sách (SV thứ 11 -> GV011, …) — không đổi phân công đã có (idempotent)."""
    cohort = db.execute(
        select(DotDoAn).where(DotDoAn.ten_dot == COHORT_TEN_DOT)
    ).scalar_one_or_none()
    if cohort is None:
        return 0
    assigned = set(
        db.execute(
            select(PhanCongHuongDan.sinh_vien_id).where(
                PhanCongHuongDan.dot_do_an_id == cohort.id
            )
        ).scalars()
    )
    gv_by_ma = {
        gv.ma_giang_vien: gv.id
        for gv in db.execute(select(GiangVien)).scalars()
    }
    created = 0
    now = now_utc()
    sv_by_ma = {
        sv.ma_so_sinh_vien: sv for sv in db.execute(select(SinhVien)).scalars()
    }
    for i, row in enumerate(sv_rows):
        sv = sv_by_ma.get(row["ma_so_sinh_vien"])
        gv_id = gv_by_ma.get(gv_rows[i % len(gv_rows)]["ma_giang_vien"])
        if sv is None or gv_id is None or sv.id in assigned:
            continue
        db.add(
            PhanCongHuongDan(
                dot_do_an_id=cohort.id, sinh_vien_id=sv.id, giang_vien_id=gv_id, thoi_diem=now
            )
        )
        created += 1
    return created


def seed_all() -> None:
    settings = get_settings()
    if not settings.SEED_DEFAULT_PASSWORD:
        print("LỖI: SEED_DEFAULT_PASSWORD chưa được thiết lập — không thể seed dữ liệu.")
        sys.exit(1)

    # NFR-17: băm bcrypt cost 12 cho ~650 tài khoản tốn ~30s nếu lặp lại cho từng
    # tài khoản — băm một lần, dùng lại cho mọi tài khoản MỚI của lần chạy này.
    # Tài khoản đã tồn tại giữ nguyên mật khẩu cũ (idempotent).
    password_hash = hash_password(settings.SEED_DEFAULT_PASSWORD)

    gv_rows = _load_csv("giang_vien.csv")
    sv_rows = _load_csv("sinh_vien.csv")

    with SessionLocal() as db:
        _ensure_bo_mon(db, password_hash)
        gv_created = _ensure_giang_vien(db, gv_rows, password_hash)
        sv_created = _ensure_sinh_vien(db, sv_rows, password_hash)
        cohort_created = _ensure_open_cohort(db)
        db.flush()
        pc_created = _ensure_assignments(db, sv_rows, gv_rows)
        db.commit()

        gv_total = db.execute(
            select(TaiKhoan).where(TaiKhoan.vai_tro == VaiTro.GIANG_VIEN)
        ).scalars().all()
        sv_total = db.execute(
            select(TaiKhoan).where(TaiKhoan.vai_tro == VaiTro.SINH_VIEN)
        ).scalars().all()
        open_cohorts_total = db.execute(
            select(DotDoAn).where(DotDoAn.trang_thai == DANG_MO)
        ).scalars().all()

    print(
        "Seed: "
        f"GV mới {gv_created} (tổng {len(gv_total)}), "
        f"SV mới {sv_created} (tổng {len(sv_total)}), "
        f"đợt đồ án {'đã tạo' if cohort_created else 'đã tồn tại'} "
        f"'{COHORT_TEN_DOT}' (tổng đang mở: {len(open_cohorts_total)}), "
        f"phân công GVHD mới {pc_created}."
    )


if __name__ == "__main__":
    seed_all()
