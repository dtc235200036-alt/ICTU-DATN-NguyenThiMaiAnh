"""ket_qua_kiem_tra_trung_lap.ty_le_nguon_cao_nhat + chi_tiet_trung_lap.ty_le_nguon

CR-01 (04-REVIEW): NGUONG_TAI_LIEU (10.4) được hiệu chỉnh trên tỷ lệ trùng với
MỘT đồ án nguồn (`do_an_trung[].ty_le` của dịch vụ AI), không phải `ty_le_tong`
(chỉ để hiển thị — plan 04-04). Lưu đúng thống kê đó để quyết định "Vượt
ngưỡng cảnh báo" (ty_le_nguon_cao_nhat >= nguong_ap_dung) được tính một lần ở
Web API, không giao diện nào tự suy ra một quy tắc khác:

- ty_le_nguon_cao_nhat: max do_an_trung[].ty_le của lần kiểm tra tài liệu;
- chi_tiet_trung_lap.ty_le_nguon: tỷ lệ theo nguồn của nguồn mà đoạn thuộc về
  (MH-14/MH-09 "Đồ án trùng" đọc trực tiếp, không ước lượng lại).

Dòng HOAN_TAT cũ được điền bằng đúng phép ước lượng 04-07 đã dùng
(ty_le_tong × ký tự đoạn của nguồn / ký tự mọi đoạn — chính xác tới dấu cách
ghép đoạn vì mỗi câu chỉ thuộc một nguồn); không có đoạn nào -> 0.

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ket_qua_kiem_tra_trung_lap",
        sa.Column("ty_le_nguon_cao_nhat", sa.Numeric(5, 2), nullable=True),
    )
    op.add_column(
        "chi_tiet_trung_lap", sa.Column("ty_le_nguon", sa.Numeric(5, 2), nullable=True)
    )
    op.execute(
        """
        UPDATE ket_qua_kiem_tra_trung_lap k
        JOIN (
            SELECT ket_qua_id, MAX(so_ky_tu) AS cao_nhat, SUM(so_ky_tu) AS tong
            FROM (
                SELECT ket_qua_id, doi_tuong_trung,
                       SUM(CHAR_LENGTH(COALESCE(doan_nguon, ''))) AS so_ky_tu
                FROM chi_tiet_trung_lap
                GROUP BY ket_qua_id, doi_tuong_trung
            ) theo_nguon
            GROUP BY ket_qua_id
        ) s ON s.ket_qua_id = k.id
        SET k.ty_le_nguon_cao_nhat = LEAST(100, ROUND(k.ty_le_tong * s.cao_nhat / s.tong, 2))
        WHERE k.loai_kiem_tra = 'TAI_LIEU' AND k.trang_thai = 'HOAN_TAT'
          AND k.ty_le_tong IS NOT NULL AND s.tong > 0
        """
    )
    op.execute(
        """
        UPDATE ket_qua_kiem_tra_trung_lap
        SET ty_le_nguon_cao_nhat = 0
        WHERE loai_kiem_tra = 'TAI_LIEU' AND trang_thai = 'HOAN_TAT'
          AND ty_le_nguon_cao_nhat IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("chi_tiet_trung_lap", "ty_le_nguon")
    op.drop_column("ket_qua_kiem_tra_trung_lap", "ty_le_nguon_cao_nhat")
