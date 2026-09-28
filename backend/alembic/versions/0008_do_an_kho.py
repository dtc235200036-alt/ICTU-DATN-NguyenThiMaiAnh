"""do_an_kho (+ ma_so_sinh_vien, ho_ten_sinh_vien snapshot) — UC5.2, D-07

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "do_an_kho",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_tai_id", sa.BigInteger(), nullable=True),
        sa.Column("sinh_vien_id", sa.BigInteger(), nullable=True),
        sa.Column("giang_vien_id", sa.BigInteger(), nullable=True),
        sa.Column("khoa", sa.String(length=20), nullable=True),
        sa.Column("ten_de_tai", sa.String(length=255), nullable=False),
        sa.Column("tu_khoa", sa.String(length=255), nullable=True),
        sa.Column("diem", sa.Numeric(4, 2), nullable=True),
        sa.Column("nguon", sa.String(length=20), nullable=False),
        sa.Column("trang_thai_index", sa.String(length=20), nullable=False),
        # Cột bổ sung khi thi công Phase 3: ảnh chụp mã/họ tên SV tại thời
        # điểm lưu kho — bản ghi import khóa cũ không có tài khoản SV.
        sa.Column("ma_so_sinh_vien", sa.String(length=20), nullable=True),
        sa.Column("ho_ten_sinh_vien", sa.String(length=150), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_do_an_kho"),
        sa.ForeignKeyConstraint(["de_tai_id"], ["de_tai.id"], name="fk_do_an_kho_de_tai"),
        sa.ForeignKeyConstraint(["sinh_vien_id"], ["sinh_vien.id"], name="fk_do_an_kho_sinh_vien"),
        sa.ForeignKeyConstraint(["giang_vien_id"], ["giang_vien.id"], name="fk_do_an_kho_giang_vien"),
        sa.UniqueConstraint("de_tai_id", name="uq_do_an_kho_de_tai_id"),
        sa.CheckConstraint("nguon IN ('HE_THONG', 'IMPORT')", name="ck_do_an_kho_nguon"),
        sa.CheckConstraint(
            "trang_thai_index IN ('CHUA_INDEX', 'DA_INDEX')",
            name="ck_do_an_kho_trang_thai_index",
        ),
        sa.CheckConstraint(
            "diem IS NULL OR (diem >= 0 AND diem <= 10)", name="ck_do_an_kho_diem"
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )
    op.create_index("ix_do_an_kho_khoa", "do_an_kho", ["khoa"])
    op.create_index("ix_do_an_kho_giang_vien_id", "do_an_kho", ["giang_vien_id"])


def downgrade() -> None:
    op.drop_table("do_an_kho")
