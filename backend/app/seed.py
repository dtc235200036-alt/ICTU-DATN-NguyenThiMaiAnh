"""Seed bootstrap: đảm bảo tài khoản Bộ môn tồn tại (idempotent).

Chạy: python -m app.seed
Kế hoạch 02-03 sẽ mở rộng module này với 100 SV / 30 GV (D-13).
"""
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.roles import VaiTro
from app.core.security import hash_password
from app.models.tai_khoan import TaiKhoan

BO_MON_MA_DANG_NHAP = "bomon"
BO_MON_EMAIL = "bomon@ictu.edu.vn"


def seed_bo_mon() -> None:
    settings = get_settings()
    if not settings.SEED_DEFAULT_PASSWORD:
        print("LỖI: SEED_DEFAULT_PASSWORD chưa được thiết lập — không thể seed tài khoản Bộ môn.")
        sys.exit(1)

    with SessionLocal() as db:
        existing = db.execute(
            select(TaiKhoan).where(TaiKhoan.ma_dang_nhap == BO_MON_MA_DANG_NHAP)
        ).scalar_one_or_none()

        if existing is not None:
            print(f"Seed: tài khoản '{BO_MON_MA_DANG_NHAP}' đã tồn tại — bỏ qua.")
            return

        account = TaiKhoan(
            ma_dang_nhap=BO_MON_MA_DANG_NHAP,
            email=BO_MON_EMAIL,
            mat_khau_bam=hash_password(settings.SEED_DEFAULT_PASSWORD),
            vai_tro=VaiTro.BO_MON,
            bi_khoa=False,
        )
        db.add(account)
        db.commit()
        print(f"Seed: đã tạo tài khoản Bộ môn '{BO_MON_MA_DANG_NHAP}'.")


if __name__ == "__main__":
    seed_bo_mon()
