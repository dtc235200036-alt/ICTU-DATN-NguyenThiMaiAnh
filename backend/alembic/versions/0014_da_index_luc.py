"""tai_lieu_do_an.da_index_luc — thời điểm tài liệu vào chỉ mục AI

WR-06 (04-REVIEW): ingest DOCUMENT sau kiểm tra chỉ ghi log khi lỗi, và tài
liệu không có trạng thái "chưa index" như do_an_kho.trang_thai_index — tài liệu
lỡ ingest không bao giờ vào kho so khớp, bản chép sau đó của nó được 0 %. Cột
mới: NULL = chưa vào chỉ mục (Web API thử lại, `ai_index backfill --loai
DOCUMENT --chua-index` và số đếm trên dashboard Bộ môn), có giá trị = lần
ingest thành công gần nhất (DATETIME naive UTC như mọi cột thời điểm khác).

Dòng hiện có để NULL: `deploy/seed-ai.sh` (backfill DOCUMENT) hoặc lần thử lại
tự động điền; ingest lại văn bản không đổi là no-op phía dịch vụ AI.

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tai_lieu_do_an", sa.Column("da_index_luc", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("tai_lieu_do_an", "da_index_luc")
