"""chi_tiet_trung_lap.loai_nguon + nguon_id — nguồn của đoạn trùng theo không gian id AI

WR-06 (03-REVIEW): một ref_id do dịch vụ AI trả về chỉ có nghĩa kèm không gian
id của nó (TOPIC = de_tai.id, ARCHIVE = do_an_kho.id, DOCUMENT =
tai_lieu_do_an.id). Lưu cả hai để nhãn được tra đúng bảng và để WR-07 quyết
định lúc đọc: SV chỉ thấy đoạn nguồn khi nguồn là đồ án đã vào kho.

Cả hai cột nullable (dòng cũ và kết quả kiểm tra tên đề tài không có); KHÔNG
có FK — tham chiếu đa hình, và nguồn có thể bị xóa sau khi kiểm tra.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chi_tiet_trung_lap", sa.Column("loai_nguon", sa.String(length=20), nullable=True)
    )
    op.add_column("chi_tiet_trung_lap", sa.Column("nguon_id", sa.BigInteger(), nullable=True))
    op.create_check_constraint(
        "ck_chi_tiet_trung_lap_loai_nguon",
        "chi_tiet_trung_lap",
        "loai_nguon IS NULL OR loai_nguon IN ('TOPIC', 'ARCHIVE', 'DOCUMENT')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_chi_tiet_trung_lap_loai_nguon", "chi_tiet_trung_lap", type_="check")
    op.drop_column("chi_tiet_trung_lap", "nguon_id")
    op.drop_column("chi_tiet_trung_lap", "loai_nguon")
