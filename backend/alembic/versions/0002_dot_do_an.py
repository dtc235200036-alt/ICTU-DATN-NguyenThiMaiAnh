"""dot_do_an — đợt đồ án theo khóa (D-04, UC0.3)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-28

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dot_do_an",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ten_dot", sa.String(length=100), nullable=False),
        sa.Column("khoa", sa.String(length=20), nullable=False),
        sa.Column("nam_hoc", sa.String(length=20), nullable=True),
        sa.Column("ngay_bat_dau", sa.Date(), nullable=False),
        sa.Column("ngay_ket_thuc", sa.Date(), nullable=True),
        sa.Column(
            "trang_thai",
            sa.String(length=20),
            server_default=sa.text("'DANG_MO'"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dot_do_an"),
        sa.CheckConstraint(
            "trang_thai IN ('DANG_MO', 'DA_DONG')",
            name="ck_dot_do_an_trang_thai",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )
    op.create_index("ix_dot_do_an_trang_thai", "dot_do_an", ["trang_thai"])


def downgrade() -> None:
    op.drop_index("ix_dot_do_an_trang_thai", table_name="dot_do_an")
    op.drop_table("dot_do_an")
