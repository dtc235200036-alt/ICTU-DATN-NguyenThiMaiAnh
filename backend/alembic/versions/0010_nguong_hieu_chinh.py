"""Ngưỡng hiệu chỉnh (D-04, Phase 4) + NGUONG_DOAN_TRUNG — chỉ dữ liệu

Giá trị lấy từ ai-service/calibration/nguong-de-xuat.json (tap HIEU_CHINH,
profile bkai, ngày 2026-09-28 — plan 04-04) và GHI CỨNG ở đây: migration không
được đọc file của repo lúc chạy. Không đổi schema (check-erd-db giữ nguyên).

- NGUONG_TEN_DE_TAI 50.00 -> 67.80 (nguong_ten_de_tai, Youden)
- NGUONG_TAI_LIEU   30.00 -> 10.40 (nguong_tai_lieu, trung điểm)
- NGUONG_DOAN_TRUNG (mới)    67.70 (nguong_doan, Youden — ngữ nghĩa từng câu)

T-04-19: chỉ cập nhật dòng tai_khoan_id IS NULL — ngưỡng Bộ môn đã sửa qua
màn hình cấu hình không bao giờ bị ghi đè; downgrade đối xứng.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ai-service/calibration/nguong-de-xuat.json (2026-09-28)
NGUONG_TEN_DE_TAI_HIEU_CHINH = 67.80
NGUONG_TAI_LIEU_HIEU_CHINH = 10.40
NGUONG_DOAN_TRUNG_HIEU_CHINH = 67.70

# Giá trị seed của migration 0004 (khôi phục khi downgrade).
NGUONG_TEN_DE_TAI_0004 = 50.00
NGUONG_TAI_LIEU_0004 = 30.00


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO cau_hinh_nguong (loai, gia_tri, tai_khoan_id, thoi_diem_cap_nhat) "
            "SELECT 'NGUONG_DOAN_TRUNG', :gia_tri, NULL, UTC_TIMESTAMP() FROM DUAL "
            "WHERE NOT EXISTS (SELECT 1 FROM cau_hinh_nguong WHERE loai = 'NGUONG_DOAN_TRUNG')"
        ),
        {"gia_tri": NGUONG_DOAN_TRUNG_HIEU_CHINH},
    )
    for loai, gia_tri in (
        ("NGUONG_TEN_DE_TAI", NGUONG_TEN_DE_TAI_HIEU_CHINH),
        ("NGUONG_TAI_LIEU", NGUONG_TAI_LIEU_HIEU_CHINH),
    ):
        conn.execute(
            sa.text(
                "UPDATE cau_hinh_nguong SET gia_tri = :gia_tri, thoi_diem_cap_nhat = UTC_TIMESTAMP() "
                "WHERE loai = :loai AND tai_khoan_id IS NULL"
            ),
            {"gia_tri": gia_tri, "loai": loai},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM cau_hinh_nguong WHERE loai = 'NGUONG_DOAN_TRUNG'"))
    for loai, gia_tri in (
        ("NGUONG_TEN_DE_TAI", NGUONG_TEN_DE_TAI_0004),
        ("NGUONG_TAI_LIEU", NGUONG_TAI_LIEU_0004),
    ):
        conn.execute(
            sa.text(
                "UPDATE cau_hinh_nguong SET gia_tri = :gia_tri, thoi_diem_cap_nhat = UTC_TIMESTAMP() "
                "WHERE loai = :loai AND tai_khoan_id IS NULL"
            ),
            {"gia_tri": gia_tri, "loai": loai},
        )
