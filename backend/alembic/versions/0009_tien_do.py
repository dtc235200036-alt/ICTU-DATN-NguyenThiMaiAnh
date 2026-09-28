"""moc_tien_do, bao_cao_tien_do (+ tai_lieu_do_an_id đính kèm) — UC3, D-05

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE_OPTS = dict(
    mysql_engine="InnoDB", mysql_charset="utf8mb4", mysql_collate="utf8mb4_vietnamese_ci"
)


def upgrade() -> None:
    op.create_table(
        "moc_tien_do",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dot_do_an_id", sa.BigInteger(), nullable=False),
        sa.Column("ten_moc", sa.String(length=100), nullable=False),
        sa.Column("thu_tu", sa.Integer(), nullable=False),
        sa.Column("han_nop", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_moc_tien_do"),
        sa.ForeignKeyConstraint(
            ["dot_do_an_id"], ["dot_do_an.id"], name="fk_moc_tien_do_dot_do_an"
        ),
        **_TABLE_OPTS,
    )
    op.create_index("ix_moc_tien_do_dot_thu_tu", "moc_tien_do", ["dot_do_an_id", "thu_tu"])

    op.create_table(
        "bao_cao_tien_do",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_tai_id", sa.BigInteger(), nullable=False),
        sa.Column("moc_tien_do_id", sa.BigInteger(), nullable=False),
        sa.Column("noi_dung", sa.Text(), nullable=True),
        sa.Column("thoi_diem_nop", sa.DateTime(), nullable=False),
        sa.Column("nhan_xet", sa.Text(), nullable=True),
        sa.Column("danh_gia", sa.String(length=20), nullable=True),
        # Cột bổ sung khi thi công Phase 3 (PROG-01 "file tùy chọn"): trỏ tới
        # phiên bản tai_lieu_do_an loại BAO_CAO_TIEN_DO mới nhất của báo cáo.
        sa.Column("tai_lieu_do_an_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_bao_cao_tien_do"),
        sa.ForeignKeyConstraint(["de_tai_id"], ["de_tai.id"], name="fk_bao_cao_tien_do_de_tai"),
        sa.ForeignKeyConstraint(
            ["moc_tien_do_id"], ["moc_tien_do.id"], name="fk_bao_cao_tien_do_moc"
        ),
        sa.ForeignKeyConstraint(
            ["tai_lieu_do_an_id"], ["tai_lieu_do_an.id"], name="fk_bao_cao_tien_do_tai_lieu"
        ),
        sa.UniqueConstraint(
            "de_tai_id", "moc_tien_do_id", name="uq_bao_cao_tien_do_de_tai_moc"
        ),
        sa.CheckConstraint(
            "danh_gia IS NULL OR danh_gia IN ('DAT', 'CAN_CAI_THIEN', 'CHUA_DAT')",
            name="ck_bao_cao_tien_do_danh_gia",
        ),
        **_TABLE_OPTS,
    )


def downgrade() -> None:
    op.drop_table("bao_cao_tien_do")
    op.drop_table("moc_tien_do")
