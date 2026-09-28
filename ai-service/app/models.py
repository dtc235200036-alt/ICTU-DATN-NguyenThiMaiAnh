"""Bảng của schema thesis_ai (§3.2.6, erd-thesis-ai.puml).

Không có khóa ngoại nào trỏ sang thesis_core: ma_nguon chỉ là tham chiếu
logic do Web API gửi kèm (TOPIC = de_tai.id, ARCHIVE = do_an_kho.id,
DOCUMENT = tai_lieu_do_an.id). Liệt kê giá trị dùng VARCHAR + CHECK theo quy
ước của dự án (không dùng ENUM gốc).
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}

TABLE_KWARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_vietnamese_ci",
}

LOAI_TOPIC = "TOPIC"
LOAI_ARCHIVE = "ARCHIVE"
LOAI_DOCUMENT = "DOCUMENT"
LOAI_NGUON = (LOAI_TOPIC, LOAI_ARCHIVE, LOAI_DOCUMENT)

# BIGINT trên MySQL, INTEGER trên SQLite để SQLite tự tăng khóa chính (test).
BigId = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Chunk(Base):
    __tablename__ = "chunk"
    __table_args__ = (
        UniqueConstraint(
            "loai_nguon", "ma_nguon", "thu_tu", name="uq_chunk_loai_nguon_ma_nguon_thu_tu"
        ),
        CheckConstraint(
            "loai_nguon IN ('TOPIC', 'ARCHIVE', 'DOCUMENT')", name="ck_chunk_loai_nguon"
        ),
        Index("ix_chunk_loai_nguon_ma_nguon", "loai_nguon", "ma_nguon"),
        TABLE_KWARGS,
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    loai_nguon: Mapped[str] = mapped_column(String(20), nullable=False)
    ma_nguon: Mapped[int] = mapped_column(BigInteger, nullable=False)
    thu_tu: Mapped[int] = mapped_column(Integer, nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    bam_noi_dung: Mapped[str] = mapped_column(
        String(64).with_variant(CHAR(64), "mysql"), nullable=False
    )


class Embedding(Base):
    __tablename__ = "embedding"
    __table_args__ = (
        UniqueConstraint("chunk_id", "ten_model", name="uq_embedding_chunk_id_ten_model"),
        TABLE_KWARGS,
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    chunk_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chunk.id", ondelete="CASCADE", name="fk_embedding_chunk"),
        nullable=False,
    )
    ten_model: Mapped[str] = mapped_column(String(100), nullable=False)
    so_chieu: Mapped[int] = mapped_column(Integer, nullable=False)
    # float32 little-endian, L2-normalized (np.ndarray.astype('<f4').tobytes()).
    vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)


class IndexMetadata(Base):
    __tablename__ = "index_metadata"
    __table_args__ = (
        UniqueConstraint("ten_model", name="uq_index_metadata_ten_model"),
        TABLE_KWARGS,
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    ten_model: Mapped[str] = mapped_column(String(100), nullable=False)
    so_vector: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # DATETIME naive UTC (cùng quy ước với thesis_core).
    cap_nhat_luc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
