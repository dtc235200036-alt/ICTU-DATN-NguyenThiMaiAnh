"""dinh_huong + duyệt đề cương hai cấp (GVHD -> Lãnh đạo bộ môn)

Góp ý GVHD (giao diện SV/GV/Khoa):
- Thay "Lĩnh vực" bằng danh mục "Định hướng" (H01, H02, ...) do Bộ môn quản
  lý; đề tài cũ giữ dinh_huong_id NULL (cột linh_vuc giữ nguyên, không xóa).
- Đề cương: GVHD duyệt (GVHD_DA_DUYET) rồi nộp lên Bộ môn (CHO_BO_MON_DUYET);
  Lãnh đạo bộ môn phê duyệt kèm file đã ký số (DA_DUYET) hoặc trả lại
  (YEU_CAU_SUA). Đề cương đã DA_DUYET trước đây giữ nguyên DA_DUYET.
- Ghi chú người nộp trên từng phiên bản tài liệu.

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dinh_huong",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ma", sa.String(10), nullable=False),
        sa.Column("ten", sa.String(255), nullable=False),
        sa.Column("mo_ta", sa.Text(), nullable=True),
        sa.Column("hoat_dong", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name="pk_dinh_huong"),
        sa.UniqueConstraint("ma", name="uk_dinh_huong_ma"),
    )
    # Hai định hướng theo biểu mẫu CLO-PI của Khoa; Bộ môn sửa/thêm trong ứng dụng.
    op.execute(
        """
        INSERT IGNORE INTO dinh_huong (ma, ten, hoat_dong) VALUES
            ('H01', 'Phát triển ứng dụng', 1),
            ('H02', 'Hệ thống AI và ứng dụng', 1)
        """
    )

    op.add_column("de_tai", sa.Column("dinh_huong_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_de_tai_dinh_huong", "de_tai", "dinh_huong", ["dinh_huong_id"], ["id"]
    )

    # Tên CHECK thực tế theo naming convention của metadata (ck_<bảng>_<tên>).
    op.execute("ALTER TABLE de_cuong DROP CHECK ck_de_cuong_ck_de_cuong_trang_thai")
    op.execute(
        "ALTER TABLE de_cuong ADD CONSTRAINT ck_de_cuong_ck_de_cuong_trang_thai CHECK ("
        "trang_thai IN ('CHUA_NOP', 'CHO_DUYET', 'YEU_CAU_SUA', 'GVHD_DA_DUYET',"
        " 'CHO_BO_MON_DUYET', 'DA_DUYET'))"
    )
    op.execute("ALTER TABLE tai_lieu_do_an DROP CHECK ck_tai_lieu_do_an_ck_tai_lieu_do_an_loai")
    op.execute(
        "ALTER TABLE tai_lieu_do_an ADD CONSTRAINT ck_tai_lieu_do_an_ck_tai_lieu_do_an_loai"
        " CHECK (loai IN ('DE_CUONG', 'BAO_CAO_TIEN_DO', 'BAO_CAO_CUOI', 'KHO',"
        " 'DE_CUONG_KY_SO', 'DE_TAI'))"
    )

    op.add_column("de_cuong", sa.Column("nop_bo_mon_luc", sa.DateTime(), nullable=True))
    op.add_column("de_cuong", sa.Column("ket_qua_bo_mon", sa.String(20), nullable=True))
    op.add_column("tai_lieu_do_an", sa.Column("ghi_chu", sa.Text(), nullable=True))

    op.create_table(
        "luot_duyet_bo_mon",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_cuong_id", sa.BigInteger(), nullable=False),
        sa.Column("tai_lieu_do_an_id", sa.BigInteger(), nullable=False),
        sa.Column("tai_khoan_id", sa.BigInteger(), nullable=False),
        sa.Column("ket_qua", sa.String(20), nullable=False),
        sa.Column("nhan_xet", sa.Text(), nullable=True),
        sa.Column("thoi_diem", sa.DateTime(), nullable=False),
        sa.Column("tai_lieu_ky_so_id", sa.BigInteger(), nullable=True),
        sa.Column("nguoi_ky", sa.String(255), nullable=True),
        sa.Column("thoi_diem_ky", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_luot_duyet_bo_mon"),
        sa.ForeignKeyConstraint(
            ["de_cuong_id"], ["de_cuong.id"], name="fk_luot_duyet_bo_mon_de_cuong"
        ),
        sa.ForeignKeyConstraint(
            ["tai_lieu_do_an_id"], ["tai_lieu_do_an.id"], name="fk_luot_duyet_bo_mon_tai_lieu"
        ),
        sa.ForeignKeyConstraint(
            ["tai_khoan_id"], ["tai_khoan.id"], name="fk_luot_duyet_bo_mon_tai_khoan"
        ),
        sa.ForeignKeyConstraint(
            ["tai_lieu_ky_so_id"], ["tai_lieu_do_an.id"], name="fk_luot_duyet_bo_mon_ky_so"
        ),
        sa.CheckConstraint("ket_qua IN ('DA_DUYET', 'TRA_LAI')", name="ck_luot_duyet_bo_mon_ket_qua"),
    )


def downgrade() -> None:
    op.drop_table("luot_duyet_bo_mon")
    op.drop_column("tai_lieu_do_an", "ghi_chu")
    op.drop_column("de_cuong", "ket_qua_bo_mon")
    op.drop_column("de_cuong", "nop_bo_mon_luc")
    op.execute("ALTER TABLE tai_lieu_do_an DROP CHECK ck_tai_lieu_do_an_ck_tai_lieu_do_an_loai")
    op.execute(
        "ALTER TABLE tai_lieu_do_an ADD CONSTRAINT ck_tai_lieu_do_an_ck_tai_lieu_do_an_loai"
        " CHECK (loai IN ('DE_CUONG', 'BAO_CAO_TIEN_DO', 'BAO_CAO_CUOI', 'KHO'))"
    )
    op.execute("ALTER TABLE de_cuong DROP CHECK ck_de_cuong_ck_de_cuong_trang_thai")
    op.execute(
        "ALTER TABLE de_cuong ADD CONSTRAINT ck_de_cuong_ck_de_cuong_trang_thai CHECK ("
        "trang_thai IN ('CHUA_NOP', 'CHO_DUYET', 'YEU_CAU_SUA', 'DA_DUYET'))"
    )
    op.drop_constraint("fk_de_tai_dinh_huong", "de_tai", type_="foreignkey")
    op.drop_column("de_tai", "dinh_huong_id")
    op.drop_table("dinh_huong")
