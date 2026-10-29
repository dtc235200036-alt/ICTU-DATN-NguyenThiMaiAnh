"""dinh_huong: file PDF mô tả định hướng

Ngoài mô tả ngắn (mo_ta), Bộ môn tải lên một file PDF mô tả cho mỗi định
hướng (H01, H02, ...; tải lên lại là thay, có thể gỡ); SV, GV và Bộ môn xem
trực tiếp trên trình duyệt hoặc tải về.

- File lưu dưới UPLOAD_DIR/DINH_HUONG/<uuid>.pdf (tên lưu trữ do server sinh).
- Không dùng tai_lieu_do_an (bảng đó bắt buộc gắn với một đề tài) — thông tin
  file nằm ngay trên dinh_huong: tep_ten_goc, tep_ten_luu_tru (UNIQUE),
  tep_kich_thuoc, tep_cap_nhat_luc (UTC naive). Cả bốn cột NULL khi chưa có
  file, nên định hướng hiện có không cần cập nhật dữ liệu.

Downgrade bỏ bốn cột; file đã tải lên vẫn nằm trên đĩa, không còn được tham
chiếu.

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dinh_huong", sa.Column("tep_ten_goc", sa.String(255), nullable=True))
    op.add_column("dinh_huong", sa.Column("tep_ten_luu_tru", sa.String(255), nullable=True))
    op.add_column("dinh_huong", sa.Column("tep_kich_thuoc", sa.BigInteger(), nullable=True))
    op.add_column("dinh_huong", sa.Column("tep_cap_nhat_luc", sa.DateTime(), nullable=True))
    op.create_unique_constraint(
        "uq_dinh_huong_tep_ten_luu_tru", "dinh_huong", ["tep_ten_luu_tru"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_dinh_huong_tep_ten_luu_tru", "dinh_huong", type_="unique")
    op.drop_column("dinh_huong", "tep_cap_nhat_luc")
    op.drop_column("dinh_huong", "tep_kich_thuoc")
    op.drop_column("dinh_huong", "tep_ten_luu_tru")
    op.drop_column("dinh_huong", "tep_ten_goc")
