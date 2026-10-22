"""NGUONG_TONG_TAI_LIEU + ket_qua_kiem_tra_trung_lap.nguong_tong_ap_dung

Cảnh báo bài ghép từ nhiều đồ án: quy tắc CR-01 (0012) chỉ so tỷ lệ trùng với
MỘT đồ án nguồn cao nhất với NGUONG_TAI_LIEU, nên bài chép mỗi đồ án một ít
(mỗi nguồn dưới ngưỡng) không bao giờ bị cảnh báo. Thêm ngưỡng thứ hai trên tỷ
lệ tổng mọi nguồn (ty_le_tong): "Vượt ngưỡng cảnh báo" khi
ty_le_nguon_cao_nhat >= nguong_ap_dung HOẶC ty_le_tong >= nguong_tong_ap_dung.

Giá trị lấy từ ai-service/calibration/nguong-de-xuat.json (nguong_tong_tai_lieu,
trung điểm trên tập HIEU_CHINH, profile bkai, ngày 2026-10-21 — hiệu chỉnh lại
với tín hiệu nguyên văn bằng vân tay) và GHI CỨNG ở đây. Ba ngưỡng cũ giữ nguyên
giá trị của 0010.

- cau_hinh_nguong: dòng NGUONG_TONG_TAI_LIEU = 14.80 (không ghi đè nếu đã có).
- nguong_tong_ap_dung DECIMAL(5,2) NULL: snapshot lúc tạo kết quả chờ, như
  nguong_ap_dung; kết quả cũ để NULL -> chỉ xét ngưỡng theo một đồ án như lúc
  kiểm tra (không hồi tố).

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ai-service/calibration/nguong-de-xuat.json (2026-10-21)
NGUONG_TONG_TAI_LIEU_HIEU_CHINH = 14.80


def upgrade() -> None:
    op.add_column(
        "ket_qua_kiem_tra_trung_lap",
        sa.Column("nguong_tong_ap_dung", sa.Numeric(5, 2), nullable=True),
    )
    op.get_bind().execute(
        sa.text(
            "INSERT INTO cau_hinh_nguong (loai, gia_tri, tai_khoan_id, thoi_diem_cap_nhat) "
            "SELECT 'NGUONG_TONG_TAI_LIEU', :gia_tri, NULL, UTC_TIMESTAMP() FROM DUAL "
            "WHERE NOT EXISTS (SELECT 1 FROM cau_hinh_nguong WHERE loai = 'NGUONG_TONG_TAI_LIEU')"
        ),
        {"gia_tri": NGUONG_TONG_TAI_LIEU_HIEU_CHINH},
    )


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM cau_hinh_nguong WHERE loai = 'NGUONG_TONG_TAI_LIEU'"))
    op.drop_column("ket_qua_kiem_tra_trung_lap", "nguong_tong_ap_dung")
