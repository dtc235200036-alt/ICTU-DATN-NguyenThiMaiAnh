"""WR-01: ten_model mang commit của mô hình (repo@12 ký tự đầu của SHA)

Trước sửa lỗi review Phase 4, embedding được khóa chỉ bằng tên repo nên một
lần tải lại trọng số khác (nhánh main đổi) vẫn bị coi là cùng không gian vector.
Nay dịch vụ nạp mô hình theo commit đã chốt ở bake-off (04-03-SUMMARY:
bkai 84f9d9ada0d1…, e5 d12875059715…) và ten_model = "repo@sha12".

Chỉ đổi nhãn (không mã hóa lại): các vector đang lưu được tính bằng đúng các
commit đó — volume ai-models chỉ có snapshot 84f9d9ada0d1a3c37557398b9ae9fcedcdf40be0
của bkai, cũng là commit bake-off và hiệu chỉnh đã dùng.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RENAMES = (
    ("bkai-foundation-models/vietnamese-bi-encoder", "84f9d9ada0d1"),
    ("intfloat/multilingual-e5-base", "d12875059715"),
)


def upgrade() -> None:
    for repo, sha12 in _RENAMES:
        for table in ("embedding", "index_metadata"):
            op.execute(
                f"UPDATE {table} SET ten_model = '{repo}@{sha12}' WHERE ten_model = '{repo}'"
            )


def downgrade() -> None:
    for repo, sha12 in _RENAMES:
        for table in ("embedding", "index_metadata"):
            op.execute(
                f"UPDATE {table} SET ten_model = '{repo}' WHERE ten_model = '{repo}@{sha12}'"
            )
