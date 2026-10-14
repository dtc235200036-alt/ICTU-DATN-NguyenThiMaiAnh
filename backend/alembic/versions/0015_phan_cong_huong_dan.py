"""phan_cong_huong_dan — Bộ môn gán SV cho GVHD theo đợt; GVHD duyệt đề tài

Đổi nghiệp vụ UC1: mỗi SV được Bộ môn gán cho đúng MỘT GVHD trong một đợt
(uk_phan_cong_sv_dot); đề tài SV đề xuất do GVHD của SV duyệt (không còn qua
Bộ môn); GV giao đề tài thẳng cho SV trong lớp mình hoặc mở cho lớp đăng ký,
SV đăng ký là Đã phân công ngay.

Chuyển dữ liệu hiện có:
- mọi đề tài đang hoạt động đã có cả SV và GV sinh ra một dòng phân công (giữ
  đúng cặp SV–GV đang làm việc với nhau);
- đề tài GV đề xuất mà SV đã đăng ký và còn Chờ duyệt (luồng cũ chờ Bộ môn
  xác nhận) chuyển thẳng sang Đã phân công — luồng mới không còn bước đó.

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "phan_cong_huong_dan",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dot_do_an_id", sa.BigInteger(), nullable=False),
        sa.Column("sinh_vien_id", sa.BigInteger(), nullable=False),
        sa.Column("giang_vien_id", sa.BigInteger(), nullable=False),
        sa.Column("thoi_diem", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_phan_cong_huong_dan"),
        sa.ForeignKeyConstraint(
            ["dot_do_an_id"], ["dot_do_an.id"], name="fk_phan_cong_dot_do_an"
        ),
        sa.ForeignKeyConstraint(
            ["sinh_vien_id"], ["sinh_vien.id"], name="fk_phan_cong_sinh_vien"
        ),
        sa.ForeignKeyConstraint(
            ["giang_vien_id"], ["giang_vien.id"], name="fk_phan_cong_giang_vien"
        ),
        sa.UniqueConstraint("dot_do_an_id", "sinh_vien_id", name="uk_phan_cong_sv_dot"),
    )

    op.execute(
        """
        INSERT IGNORE INTO phan_cong_huong_dan
            (dot_do_an_id, sinh_vien_id, giang_vien_id, thoi_diem)
        SELECT dot_do_an_id, sinh_vien_id, giang_vien_id, UTC_TIMESTAMP()
        FROM de_tai
        WHERE sinh_vien_id_dang_hoat_dong IS NOT NULL
          AND giang_vien_id IS NOT NULL
        ORDER BY id
        """
    )
    op.execute(
        """
        UPDATE de_tai SET trang_thai = 'DA_PHAN_CONG'
        WHERE trang_thai = 'CHO_DUYET'
          AND loai_nguoi_de_xuat = 'GIANG_VIEN'
          AND sinh_vien_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_table("phan_cong_huong_dan")
