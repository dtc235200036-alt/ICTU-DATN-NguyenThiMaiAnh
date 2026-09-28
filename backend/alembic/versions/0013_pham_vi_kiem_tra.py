"""ket_qua_kiem_tra_trung_lap.so_doan / so_doan_loai_tru / ty_le_loai_tru

CR-04 (04-REVIEW): Dịch vụ AI loại phần mẫu chung (bìa, mục lục, tài liệu tham
khảo, phụ lục…) trước khi so sánh và đã trả số câu được kiểm tra (so_doan),
số dòng bị loại (so_doan_loai_tru) và phần ký tự bị loại (ty_le_loai_tru, %),
nhưng Web API bỏ đi — GVHD không biết bao nhiêu nội dung không được kiểm tra.
Lưu lại để MH-09/MH-14 hiển thị và cảnh báo khi hơn một nửa văn bản bị loại.

Cả ba cột nullable: kết quả kiểm tra tên đề tài và kết quả cũ không có.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ket_qua_kiem_tra_trung_lap", sa.Column("so_doan", sa.Integer(), nullable=True))
    op.add_column(
        "ket_qua_kiem_tra_trung_lap", sa.Column("so_doan_loai_tru", sa.Integer(), nullable=True)
    )
    op.add_column(
        "ket_qua_kiem_tra_trung_lap",
        sa.Column("ty_le_loai_tru", sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ket_qua_kiem_tra_trung_lap", "ty_le_loai_tru")
    op.drop_column("ket_qua_kiem_tra_trung_lap", "so_doan_loai_tru")
    op.drop_column("ket_qua_kiem_tra_trung_lap", "so_doan")
