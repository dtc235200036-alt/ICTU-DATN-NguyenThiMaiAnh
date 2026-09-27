"""Seed dữ liệu mẫu (DATA-01, D-13): Bộ môn, 100 SV, 30 GV, một đợt đồ án mở.

Chạy: python -m app.seed

Idempotent: chạy lại không tạo trùng, không đổi dữ liệu của tài khoản/đợt đồ án
đã tồn tại — chỉ tạo phần còn thiếu (khớp ma_dang_nhap / ten_dot).
"""
import sys
import unicodedata
from datetime import date

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.roles import VaiTro
from app.core.security import hash_password
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan

BO_MON_MA_DANG_NHAP = "bomon"
BO_MON_EMAIL = "bomon@ictu.edu.vn"

GV_COUNT = 30
SV_COUNT = 100
HOC_VI_CYCLE = ("ThS.", "TS.", "ThS.", "PGS.TS.")
LOP_CYCLE = ("CNTT K22A", "CNTT K22B", "CNTT K22C", "CNTT K22D")
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


def _generate_ho_ten(fake: Faker, *, female: bool) -> str:
    """D-06/Pitfall 5: không dùng Faker `.name()` (trộn thứ tự Tây + đôi khi thêm
    prefix Ông/Bà) hay provider địa chỉ vi_VN (rò rỉ token "John" — xem
    02-RESEARCH.md). Ghép thủ công theo thứ tự Việt Nam Họ + [đệm] + Tên từ các
    provider tên riêng lẻ, luôn NFC-normalize và tự kiểm tra trước khi dùng.
    """
    last = fake.last_name()
    middle = fake.middle_name()
    first = fake.first_name_female() if female else fake.first_name_male()
    ho_ten = _nfc(f"{last} {middle} {first}")
    assert len(ho_ten.split()) >= 2, f"Tên sinh ra không hợp lệ (thiếu từ): {ho_ten!r}"
    assert "John" not in ho_ten, f"Faker rò rỉ token tiếng Anh vào tên: {ho_ten!r}"
    return ho_ten


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


def _ensure_giang_vien(db: Session, fake: Faker, password_hash: str) -> int:
    created = 0
    for i in range(1, GV_COUNT + 1):
        code = f"GV{i:03d}"
        existing = db.execute(
            select(TaiKhoan).where(TaiKhoan.ma_dang_nhap == code)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        ho_ten = _generate_ho_ten(fake, female=(i % 2 == 0))
        email = f"{code.lower()}@ictu.edu.vn"

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
                ho_ten=ho_ten,
                email=email,
                hoc_vi=HOC_VI_CYCLE[(i - 1) % len(HOC_VI_CYCLE)],
            )
        )
        created += 1
    return created


def _ensure_sinh_vien(db: Session, fake: Faker, password_hash: str) -> int:
    created = 0
    for i in range(1, SV_COUNT + 1):
        code = f"DTC225200{i:03d}"
        existing = db.execute(
            select(TaiKhoan).where(TaiKhoan.ma_dang_nhap == code)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        ho_ten = _generate_ho_ten(fake, female=(i % 2 == 0))
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
                ho_ten=ho_ten,
                email=email,
                lop=LOP_CYCLE[(i - 1) % len(LOP_CYCLE)],
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


def seed_all() -> None:
    settings = get_settings()
    if not settings.SEED_DEFAULT_PASSWORD:
        print("LỖI: SEED_DEFAULT_PASSWORD chưa được thiết lập — không thể seed dữ liệu.")
        sys.exit(1)

    # NFR-17: băm bcrypt cost 12 cho ~130 tài khoản tốn ~30s nếu lặp lại cho từng
    # tài khoản — băm một lần, dùng lại cho mọi tài khoản MỚI của lần chạy này.
    # Tài khoản đã tồn tại giữ nguyên mật khẩu cũ (idempotent).
    password_hash = hash_password(settings.SEED_DEFAULT_PASSWORD)

    # D-13/Pitfall 5: một Faker(vi_VN) cố định seed, gọi theo thứ tự GV rồi SV để
    # lần chạy nào cũng sinh ra đúng cùng một dãy tên (khi tài khoản chưa tồn tại).
    fake = Faker("vi_VN")
    Faker.seed(2026)

    with SessionLocal() as db:
        _ensure_bo_mon(db, password_hash)
        gv_created = _ensure_giang_vien(db, fake, password_hash)
        sv_created = _ensure_sinh_vien(db, fake, password_hash)
        cohort_created = _ensure_open_cohort(db)
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
        f"'{COHORT_TEN_DOT}' (tổng đang mở: {len(open_cohorts_total)})."
    )


if __name__ == "__main__":
    seed_all()
