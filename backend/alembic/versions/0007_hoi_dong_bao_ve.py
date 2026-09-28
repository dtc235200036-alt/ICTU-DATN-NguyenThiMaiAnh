"""hoi_dong, thanh_vien_hoi_dong, lich_bao_ve, diem_bao_ve (D-06, UC4.1/4.2)

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hoi_dong",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ten_hoi_dong", sa.String(length=150), nullable=False),
        sa.Column("ngay_bao_ve", sa.Date(), nullable=False),
        sa.Column("gio_bao_ve", sa.Time(), nullable=False),
        sa.Column("phong", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_hoi_dong"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "thanh_vien_hoi_dong",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("hoi_dong_id", sa.BigInteger(), nullable=False),
        sa.Column("giang_vien_id", sa.BigInteger(), nullable=False),
        sa.Column("vai_tro", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_thanh_vien_hoi_dong"),
        sa.ForeignKeyConstraint(
            ["hoi_dong_id"], ["hoi_dong.id"], name="fk_thanh_vien_hoi_dong_hoi_dong"
        ),
        sa.ForeignKeyConstraint(
            ["giang_vien_id"], ["giang_vien.id"], name="fk_thanh_vien_hoi_dong_giang_vien"
        ),
        sa.UniqueConstraint(
            "hoi_dong_id", "giang_vien_id", name="uq_thanh_vien_hoi_dong"
        ),
        sa.CheckConstraint(
            "vai_tro IN ('CHU_TICH', 'THU_KY', 'UY_VIEN')",
            name="ck_thanh_vien_hoi_dong_vai_tro",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "lich_bao_ve",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("hoi_dong_id", sa.BigInteger(), nullable=False),
        sa.Column("de_tai_id", sa.BigInteger(), nullable=False),
        sa.Column("sinh_vien_id", sa.BigInteger(), nullable=False),
        sa.Column("thu_tu", sa.Integer(), nullable=True),
        sa.Column("diem_trung_binh", sa.Numeric(4, 2), nullable=True),
        sa.Column("da_chot", sa.Boolean(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_lich_bao_ve"),
        sa.ForeignKeyConstraint(
            ["hoi_dong_id"], ["hoi_dong.id"], name="fk_lich_bao_ve_hoi_dong"
        ),
        sa.ForeignKeyConstraint(
            ["de_tai_id"], ["de_tai.id"], name="fk_lich_bao_ve_de_tai"
        ),
        sa.ForeignKeyConstraint(
            ["sinh_vien_id"], ["sinh_vien.id"], name="fk_lich_bao_ve_sinh_vien"
        ),
        sa.UniqueConstraint("sinh_vien_id", name="uq_lich_bao_ve_sinh_vien_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "diem_bao_ve",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lich_bao_ve_id", sa.BigInteger(), nullable=False),
        sa.Column("giang_vien_id", sa.BigInteger(), nullable=False),
        sa.Column("diem", sa.Numeric(4, 2), nullable=False),
        sa.Column("nhan_xet", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_diem_bao_ve"),
        sa.ForeignKeyConstraint(
            ["lich_bao_ve_id"], ["lich_bao_ve.id"], name="fk_diem_bao_ve_lich_bao_ve"
        ),
        sa.ForeignKeyConstraint(
            ["giang_vien_id"], ["giang_vien.id"], name="fk_diem_bao_ve_giang_vien"
        ),
        sa.UniqueConstraint(
            "lich_bao_ve_id", "giang_vien_id", name="uq_diem_bao_ve"
        ),
        sa.CheckConstraint("diem >= 0 AND diem <= 10", name="ck_diem_bao_ve_diem"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )


def downgrade() -> None:
    op.drop_table("diem_bao_ve")
    op.drop_table("lich_bao_ve")
    op.drop_table("thanh_vien_hoi_dong")
    op.drop_table("hoi_dong")
