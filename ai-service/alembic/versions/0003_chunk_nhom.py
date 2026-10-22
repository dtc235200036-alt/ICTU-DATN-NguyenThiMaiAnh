"""Nhóm của nguồn DOCUMENT (chunk.nhom) cho tín hiệu nguyên văn bằng vân tay

Tín hiệu nguyên văn chuyển từ MinHash so vét cạn sang vân tay k-gram âm tiết
đã winnowing (app/fingerprint.py). Cụm k-gram có trong nhiều đồ án KHÁC NHAU
là cụm khuôn mẫu; các phiên bản đề cương/báo cáo của cùng một đề tài phải
được đếm là một → Web API gửi de_tai.id kèm /ingest DOCUMENT (nhom).
Dòng cũ để NULL (mỗi nguồn một nhóm) tới khi Web API nạp lại (backfill).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-22

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
    op.add_column("chunk", sa.Column("nhom", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("chunk", "nhom")
