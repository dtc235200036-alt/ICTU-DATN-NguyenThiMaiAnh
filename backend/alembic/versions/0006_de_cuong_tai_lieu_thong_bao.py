"""de_cuong, tai_lieu_do_an, luot_duyet_de_cuong, thong_bao (D-01..D-04, D-08, UC2)

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "de_cuong",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_tai_id", sa.BigInteger(), nullable=False),
        sa.Column("trang_thai", sa.String(length=20), nullable=False),
        sa.Column("ngay_nop_dau_tien", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_de_cuong"),
        sa.ForeignKeyConstraint(
            ["de_tai_id"], ["de_tai.id"], name="fk_de_cuong_de_tai"
        ),
        sa.UniqueConstraint("de_tai_id", name="uq_de_cuong_de_tai_id"),
        sa.CheckConstraint(
            "trang_thai IN ('CHUA_NOP', 'CHO_DUYET', 'YEU_CAU_SUA', 'DA_DUYET')",
            name="ck_de_cuong_trang_thai",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "tai_lieu_do_an",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_tai_id", sa.BigInteger(), nullable=False),
        sa.Column("de_cuong_id", sa.BigInteger(), nullable=True),
        sa.Column("loai", sa.String(length=20), nullable=False),
        sa.Column("so_phien_ban", sa.Integer(), nullable=False),
        sa.Column("ten_goc", sa.String(length=255), nullable=False),
        sa.Column("ten_luu_tru", sa.String(length=255), nullable=False),
        sa.Column("kich_thuoc", sa.BigInteger(), nullable=False),
        sa.Column("dinh_dang", sa.String(length=10), nullable=False),
        sa.Column("thoi_diem_nop", sa.DateTime(), nullable=False),
        # D-03/Pitfall 3 (research 03-RESEARCH.md): văn bản trích xuất lúc
        # nộp — cột bổ sung ngoài §3.2.3 gốc, ghi ngược lại ERD/dictionary
        # cùng migration này (xem docs/chuong-3-thiet-ke/csdl/erd.puml).
        sa.Column("noi_dung_trich_xuat", mysql.LONGTEXT(), nullable=True),
        sa.Column(
            "trich_xuat_loi",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tai_lieu_do_an"),
        sa.ForeignKeyConstraint(
            ["de_tai_id"], ["de_tai.id"], name="fk_tai_lieu_do_an_de_tai"
        ),
        sa.ForeignKeyConstraint(
            ["de_cuong_id"], ["de_cuong.id"], name="fk_tai_lieu_do_an_de_cuong"
        ),
        sa.UniqueConstraint(
            "de_tai_id", "loai", "so_phien_ban", name="uq_tai_lieu_do_an_phien_ban"
        ),
        sa.UniqueConstraint("ten_luu_tru", name="uq_tai_lieu_do_an_ten_luu_tru"),
        sa.CheckConstraint(
            "loai IN ('DE_CUONG', 'BAO_CAO_TIEN_DO', 'BAO_CAO_CUOI', 'KHO')",
            name="ck_tai_lieu_do_an_loai",
        ),
        sa.CheckConstraint(
            "dinh_dang IN ('DOCX', 'PDF')", name="ck_tai_lieu_do_an_dinh_dang"
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "luot_duyet_de_cuong",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("de_cuong_id", sa.BigInteger(), nullable=False),
        sa.Column("tai_lieu_do_an_id", sa.BigInteger(), nullable=False),
        sa.Column("giang_vien_id", sa.BigInteger(), nullable=False),
        sa.Column("ket_qua", sa.String(length=20), nullable=False),
        sa.Column("nhan_xet", sa.Text(), nullable=True),
        sa.Column("thoi_diem", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_luot_duyet_de_cuong"),
        sa.ForeignKeyConstraint(
            ["de_cuong_id"],
            ["de_cuong.id"],
            name="fk_luot_duyet_de_cuong_de_cuong",
        ),
        sa.ForeignKeyConstraint(
            ["tai_lieu_do_an_id"],
            ["tai_lieu_do_an.id"],
            name="fk_luot_duyet_de_cuong_tai_lieu",
        ),
        sa.ForeignKeyConstraint(
            ["giang_vien_id"],
            ["giang_vien.id"],
            name="fk_luot_duyet_de_cuong_giang_vien",
        ),
        sa.UniqueConstraint(
            "tai_lieu_do_an_id", name="uq_luot_duyet_de_cuong_tai_lieu"
        ),
        sa.CheckConstraint(
            "ket_qua IN ('DA_DUYET', 'YEU_CAU_SUA')",
            name="ck_luot_duyet_de_cuong_ket_qua",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )

    op.create_table(
        "thong_bao",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tai_khoan_id", sa.BigInteger(), nullable=False),
        sa.Column("loai", sa.String(length=30), nullable=False),
        sa.Column("noi_dung", sa.Text(), nullable=False),
        sa.Column("lien_ket", sa.String(length=255), nullable=True),
        sa.Column("da_doc", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("thoi_diem", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_thong_bao"),
        sa.ForeignKeyConstraint(
            ["tai_khoan_id"], ["tai_khoan.id"], name="fk_thong_bao_tai_khoan"
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_vietnamese_ci",
    )
    op.create_index(
        "ix_thong_bao_tai_khoan_da_doc",
        "thong_bao",
        ["tai_khoan_id", "da_doc", "thoi_diem"],
    )

    # Pitfall 2 (03-RESEARCH.md): tai_lieu_do_an phải tồn tại trước khi thêm
    # FK này — cột ket_qua_kiem_tra_trung_lap.tai_lieu_do_an_id đã UNIQUE sẵn
    # từ migration 0004 nhưng cố ý chưa có FK ("Phase 3 thêm FK khi bảng đó
    # ra đời").
    op.create_foreign_key(
        "fk_ket_qua_kttl_tai_lieu_do_an",
        "ket_qua_kiem_tra_trung_lap",
        "tai_lieu_do_an",
        ["tai_lieu_do_an_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ket_qua_kttl_tai_lieu_do_an",
        "ket_qua_kiem_tra_trung_lap",
        type_="foreignkey",
    )
    op.drop_index("ix_thong_bao_tai_khoan_da_doc", table_name="thong_bao")
    op.drop_table("thong_bao")
    op.drop_table("luot_duyet_de_cuong")
    op.drop_table("tai_lieu_do_an")
    op.drop_table("de_cuong")
