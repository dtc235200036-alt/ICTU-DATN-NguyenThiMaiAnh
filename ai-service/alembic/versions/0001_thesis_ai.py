"""thesis_ai: chunk, embedding, index_metadata (§3.2.6, AISV-02)

Schema riêng của dịch vụ AI — lịch sử migration độc lập với thesis_core
(§3.2.1, DEPL-01). loai_nguon = VARCHAR(20) + CHECK (TOPIC, ARCHIVE,
DOCUMENT) theo quy ước liệt kê của dự án (không dùng ENUM gốc).

Revision ID: 0001
Revises:
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BIG_ID = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
_TABLE_KWARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_vietnamese_ci",
}


def upgrade() -> None:
    op.create_table(
        "chunk",
        sa.Column("id", _BIG_ID, autoincrement=True, nullable=False),
        sa.Column("loai_nguon", sa.String(length=20), nullable=False),
        sa.Column("ma_nguon", sa.BigInteger(), nullable=False),
        sa.Column("thu_tu", sa.Integer(), nullable=False),
        sa.Column("noi_dung", sa.Text(), nullable=False),
        sa.Column(
            "bam_noi_dung",
            sa.String(length=64).with_variant(mysql.CHAR(length=64), "mysql"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chunk"),
        sa.UniqueConstraint(
            "loai_nguon", "ma_nguon", "thu_tu", name="uq_chunk_loai_nguon_ma_nguon_thu_tu"
        ),
        sa.CheckConstraint(
            "loai_nguon IN ('TOPIC', 'ARCHIVE', 'DOCUMENT')", name="ck_chunk_loai_nguon"
        ),
        **_TABLE_KWARGS,
    )
    op.create_index("ix_chunk_loai_nguon_ma_nguon", "chunk", ["loai_nguon", "ma_nguon"])

    op.create_table(
        "embedding",
        sa.Column("id", _BIG_ID, autoincrement=True, nullable=False),
        sa.Column("chunk_id", sa.BigInteger(), nullable=False),
        sa.Column("ten_model", sa.String(length=100), nullable=False),
        sa.Column("so_chieu", sa.Integer(), nullable=False),
        sa.Column("vector", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_embedding"),
        sa.ForeignKeyConstraint(
            ["chunk_id"], ["chunk.id"], name="fk_embedding_chunk", ondelete="CASCADE"
        ),
        sa.UniqueConstraint("chunk_id", "ten_model", name="uq_embedding_chunk_id_ten_model"),
        **_TABLE_KWARGS,
    )

    op.create_table(
        "index_metadata",
        sa.Column("id", _BIG_ID, autoincrement=True, nullable=False),
        sa.Column("ten_model", sa.String(length=100), nullable=False),
        sa.Column("so_vector", sa.BigInteger(), nullable=False),
        sa.Column("cap_nhat_luc", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_index_metadata"),
        sa.UniqueConstraint("ten_model", name="uq_index_metadata_ten_model"),
        **_TABLE_KWARGS,
    )


def downgrade() -> None:
    op.drop_table("index_metadata")
    op.drop_table("embedding")
    op.drop_index("ix_chunk_loai_nguon_ma_nguon", table_name="chunk")
    op.drop_table("chunk")
