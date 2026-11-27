import uuid
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Index,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, BOOLEAN, ENUM, JSONB, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import SchemaItem
from sqlalchemy.types import Integer

from app.core.database import Base


def get_enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [str(e.value) for e in enum_cls]


class Status(StrEnum):
    PENDING = "pending"
    IN_WORK = "in_work"
    READY = "ready"
    FAILED = "failed"


class Documents(Base):
    __tablename__: str = "documents"
    document_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_path: Mapped[str] = mapped_column(TEXT, nullable=False)
    file_type: Mapped[str] = mapped_column(TEXT, nullable=False)
    meta_data: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    status: Mapped[Status] = mapped_column(
        ENUM(
            Status,
            name="status",
            values_callable=get_enum_values,
            create_type=True,
        ),
        nullable=False,
        default=Status.PENDING,
        server_default=Status.PENDING.value,
    )
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)

    __table_args__: tuple[SchemaItem] = (
        UniqueConstraint("document_id", "tenant_id", name="uq_document_id_tenant_id"),
    )


class Chunks(Base):
    __tablename__: str = "chunks"
    chunk_id: Mapped[int] = mapped_column(
        BIGINT, Identity(always=True), primary_key=True
    )
    document_id: Mapped[UUID] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(HALFVEC(1536))
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
    allowed_roles: Mapped[list[str]] = mapped_column(
        ARRAY(TEXT), nullable=False, server_default=text("'{}'::text[]"), default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(
        BOOLEAN, nullable=False, default=False, server_default=false()
    )

    __table_args__: tuple[SchemaItem, ...] = (
        ForeignKeyConstraint(
            ["document_id", "tenant_id"],
            ["documents.document_id", "documents.tenant_id"],
            ondelete="CASCADE",
            name="fk_document_id_tenant_id",
        ),
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_index_chunk_id"),
        Index(
            "idx_documents_id",
            "document_id",
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "idx_tenant_id",
            "tenant_id",
            postgresql_using="btree",
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "idx_chunks_embeddings",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "halfvec_cosine_ops"},
            postgresql_where=text("is_deleted = false"),
        ),
    )
