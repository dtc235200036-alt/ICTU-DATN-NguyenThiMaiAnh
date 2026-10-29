"""Bỏ kiểm tra chữ ký số khi Lãnh đạo bộ môn phê duyệt đề cương

Từ 0016, Lãnh đạo bộ môn phê duyệt bằng bản PDF có chữ ký số PKCS#7 nhúng
trong file; hệ thống đọc chữ ký, từ chối file chưa ký hoặc đã sửa sau khi ký và
lưu người ký/thời điểm ký. Nay bỏ hẳn bước này: chỉ cần tải lên bản PDF đề
cương đã ký (ký tay rồi quét, hay ký bằng công cụ bên ngoài đều được), hệ thống
không đọc hay kiểm tra chữ ký.

- luot_duyet_bo_mon: bỏ hai cột nguoi_ky, thoi_diem_ky.
- Giữ tai_lieu_ky_so_id và loại tài liệu DE_CUONG_KY_SO (file phê duyệt vẫn lưu
  vào thư mục đề cương của đợt như cũ).

Downgrade thêm lại hai cột (NULL) — giá trị cũ không khôi phục được.

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("luot_duyet_bo_mon", "thoi_diem_ky")
    op.drop_column("luot_duyet_bo_mon", "nguoi_ky")


def downgrade() -> None:
    op.add_column("luot_duyet_bo_mon", sa.Column("nguoi_ky", sa.String(255), nullable=True))
    op.add_column("luot_duyet_bo_mon", sa.Column("thoi_diem_ky", sa.DateTime(), nullable=True))
