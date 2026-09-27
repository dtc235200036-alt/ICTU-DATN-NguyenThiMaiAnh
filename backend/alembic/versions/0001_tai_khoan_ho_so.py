"""tai_khoan, sinh_vien, giang_vien + collation utf8mb4_vietnamese_ci

Revision ID: 0001
Revises:
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # D-04: collation ở mức database, kế thừa xuống bảng/cột (§3.2.1).
    op.execute("ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci")

    op.create_table(
        "tai_khoan",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ma_dang_nhap", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("mat_khau_bam", sa.String(length=255), nullable=False),
        sa.Column(
            "vai_tro",
            sa.Enum("SINH_VIEN", "GIANG_VIEN", "BO_MON", name="vai_tro"),
            nullable=False,
        ),
        sa.Column("bi_khoa", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tai_khoan"),
        sa.UniqueConstraint("ma_dang_nhap", name="uq_tai_khoan_ma_dang_nhap"),
        sa.UniqueConstraint("email", name="uq_tai_khoan_email"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "sinh_vien",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tai_khoan_id", sa.BigInteger(), nullable=False),
        sa.Column("ma_so_sinh_vien", sa.String(length=20), nullable=True),
        sa.Column("ho_ten", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("lop", sa.String(length=50), nullable=True),
        sa.Column("khoa", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_sinh_vien"),
        sa.UniqueConstraint("tai_khoan_id", name="uq_sinh_vien_tai_khoan_id"),
        sa.UniqueConstraint("ma_so_sinh_vien", name="uq_sinh_vien_ma_so_sinh_vien"),
        sa.ForeignKeyConstraint(
            ["tai_khoan_id"],
            ["tai_khoan.id"],
            name="fk_sinh_vien_tai_khoan",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "giang_vien",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tai_khoan_id", sa.BigInteger(), nullable=False),
        sa.Column("ma_giang_vien", sa.String(length=20), nullable=True),
        sa.Column("ho_ten", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("hoc_vi", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_giang_vien"),
        sa.UniqueConstraint("tai_khoan_id", name="uq_giang_vien_tai_khoan_id"),
        sa.UniqueConstraint("ma_giang_vien", name="uq_giang_vien_ma_giang_vien"),
        sa.ForeignKeyConstraint(
            ["tai_khoan_id"],
            ["tai_khoan.id"],
            name="fk_giang_vien_tai_khoan",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )


def downgrade() -> None:
    op.drop_table("giang_vien")
    op.drop_table("sinh_vien")
    op.drop_table("tai_khoan")
