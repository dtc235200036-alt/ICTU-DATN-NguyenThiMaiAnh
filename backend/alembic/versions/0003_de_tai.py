"""de_tai — đề xuất/đăng ký đề tài (D-04, D-05, UC1.1)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "de_tai",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dot_do_an_id", sa.BigInteger(), nullable=False),
        sa.Column("giang_vien_id", sa.BigInteger(), nullable=True),
        sa.Column("sinh_vien_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "sinh_vien_id_dang_hoat_dong",
            sa.BigInteger(),
            sa.Computed(
                "CASE WHEN trang_thai IN ('CHO_DUYET','DA_DUYET','DA_PHAN_CONG')"
                " THEN sinh_vien_id END",
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column("ten_de_tai", sa.String(length=255), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),
        sa.Column("linh_vuc", sa.String(length=100), nullable=True),
        sa.Column("trang_thai", sa.String(length=20), nullable=False),
        sa.Column("loai_nguoi_de_xuat", sa.String(length=10), nullable=False),
        sa.Column("ly_do_tu_choi", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_de_tai"),
        sa.ForeignKeyConstraint(
            ["dot_do_an_id"],
            ["dot_do_an.id"],
            name="fk_de_tai_dot_do_an",
        ),
        sa.ForeignKeyConstraint(
            ["giang_vien_id"],
            ["giang_vien.id"],
            name="fk_de_tai_giang_vien",
        ),
        sa.ForeignKeyConstraint(
            ["sinh_vien_id"],
            ["sinh_vien.id"],
            name="fk_de_tai_sinh_vien",
        ),
        sa.UniqueConstraint(
            "sinh_vien_id_dang_hoat_dong", name="uk_de_tai_sv_hoat_dong"
        ),
        sa.CheckConstraint(
            "trang_thai IN ('NHAP', 'CHO_DUYET', 'DA_DUYET', 'TU_CHOI', 'DA_PHAN_CONG')",
            name="ck_de_tai_trang_thai",
        ),
        sa.CheckConstraint(
            "loai_nguoi_de_xuat IN ('GIANG_VIEN', 'SINH_VIEN')",
            name="ck_de_tai_loai_nguoi_de_xuat",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )
    op.create_index(
        "ix_de_tai_dot_trang_thai", "de_tai", ["dot_do_an_id", "trang_thai"]
    )


def downgrade() -> None:
    op.drop_index("ix_de_tai_dot_trang_thai", table_name="de_tai")
    op.drop_table("de_tai")
