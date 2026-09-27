"""ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap, cau_hinh_nguong (D-10, UC0.6)

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-28

"""
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ket_qua_kiem_tra_trung_lap",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_tai_id", sa.BigInteger(), nullable=True),
        # tai_lieu_do_an chưa tồn tại (đến ở Phase 3) — cột nullable, UNIQUE
        # nhưng CHƯA có FK; Phase 3's migration thêm FK khi bảng đó ra đời.
        sa.Column("tai_lieu_do_an_id", sa.BigInteger(), nullable=True),
        sa.Column("loai_kiem_tra", sa.String(length=20), nullable=False),
        sa.Column("trang_thai", sa.String(length=20), nullable=False),
        sa.Column("ty_le_tong", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("nguong_ap_dung", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("doi_tuong_duoc_kiem_tra", sa.String(length=255), nullable=True),
        sa.Column("thoi_diem", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ket_qua_kttl"),
        sa.ForeignKeyConstraint(
            ["de_tai_id"],
            ["de_tai.id"],
            name="fk_ket_qua_kttl_de_tai",
        ),
        sa.UniqueConstraint(
            "tai_lieu_do_an_id", name="uq_ket_qua_kttl_tai_lieu_do_an_id"
        ),
        sa.CheckConstraint(
            "loai_kiem_tra IN ('TEN_DE_TAI', 'TAI_LIEU')",
            name="ck_ket_qua_kttl_loai_kiem_tra",
        ),
        sa.CheckConstraint(
            "trang_thai IN ('DANG_KIEM_TRA', 'HOAN_TAT', 'LOI')",
            name="ck_ket_qua_kttl_trang_thai",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )
    op.create_index(
        "ix_ket_qua_kttl_de_tai_thoi_diem",
        "ket_qua_kiem_tra_trung_lap",
        ["de_tai_id", "thoi_diem"],
    )

    op.create_table(
        "chi_tiet_trung_lap",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ket_qua_id", sa.BigInteger(), nullable=False),
        sa.Column("doi_tuong_trung", sa.String(length=255), nullable=False),
        sa.Column("ty_le", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("doan_nguon", sa.Text(), nullable=True),
        sa.Column("doan_trung", sa.Text(), nullable=True),
        sa.Column("vi_tri", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_chi_tiet_trung_lap"),
        sa.ForeignKeyConstraint(
            ["ket_qua_id"],
            ["ket_qua_kiem_tra_trung_lap.id"],
            name="fk_chi_tiet_trung_lap_ket_qua",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "cau_hinh_nguong",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("loai", sa.String(length=30), nullable=False),
        sa.Column("gia_tri", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tai_khoan_id", sa.BigInteger(), nullable=True),
        sa.Column("thoi_diem_cap_nhat", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_cau_hinh_nguong"),
        sa.ForeignKeyConstraint(
            ["tai_khoan_id"],
            ["tai_khoan.id"],
            name="fk_cau_hinh_nguong_tai_khoan",
        ),
        sa.UniqueConstraint("loai", name="uq_cau_hinh_nguong_loai"),
        sa.CheckConstraint(
            "gia_tri >= 0 AND gia_tri <= 100", name="ck_cau_hinh_nguong_gia_tri"
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(
        sa.table(
            "cau_hinh_nguong",
            sa.column("loai", sa.String(length=30)),
            sa.column("gia_tri", sa.Numeric(precision=5, scale=2)),
            sa.column("thoi_diem_cap_nhat", sa.DateTime()),
        ),
        [
            {"loai": "NGUONG_TEN_DE_TAI", "gia_tri": 50.00, "thoi_diem_cap_nhat": now},
            {"loai": "NGUONG_TAI_LIEU", "gia_tri": 30.00, "thoi_diem_cap_nhat": now},
        ],
    )


def downgrade() -> None:
    op.drop_table("cau_hinh_nguong")
    op.drop_table("chi_tiet_trung_lap")
    op.drop_index(
        "ix_ket_qua_kttl_de_tai_thoi_diem", table_name="ket_qua_kiem_tra_trung_lap"
    )
    op.drop_table("ket_qua_kiem_tra_trung_lap")
