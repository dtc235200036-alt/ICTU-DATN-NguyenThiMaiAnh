"""ket_qua_kiem_tra_trung_lap: kiểm tra trùng lặp một tệp tải lên

GV/Bộ môn tải một tệp PDF/DOCX bất kỳ lên để kiểm tra trùng lặp với kho, không
gắn với đề tài nào. Kết quả dùng lại bảng ket_qua_kiem_tra_trung_lap (loại
TAI_LIEU, tai_lieu_do_an_id NULL) và chi_tiet_trung_lap; cột mới tai_khoan_id
là người tải lên — chỉ người đó xem được kết quả. Tệp không được lưu và không
được đưa vào chỉ mục AI.

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ket_qua_kiem_tra_trung_lap",
        sa.Column("tai_khoan_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_ket_qua_kttl_tai_khoan",
        "ket_qua_kiem_tra_trung_lap",
        "tai_khoan",
        ["tai_khoan_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ket_qua_kttl_tai_khoan", "ket_qua_kiem_tra_trung_lap", type_="foreignkey"
    )
    op.drop_column("ket_qua_kiem_tra_trung_lap", "tai_khoan_id")
