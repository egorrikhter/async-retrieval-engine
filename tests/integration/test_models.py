from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunks, Documents, Status


async def test_preservation_and_defaults(db_session: AsyncSession) -> None:
    tenant_id = uuid4()

    doc = Documents(
        source_path="test_path_to_file",
        file_type="test_file_type",
        tenant_id=tenant_id,
    )

    db_session.add(doc)
    await db_session.flush()

    chunk = Chunks(
        document_id=doc.document_id,
        content="test_content_for_chunk",
        chunk_index=0,
        embedding=[0.5] * 1536,
        tenant_id=tenant_id,
    )
    db_session.add(chunk)
    await db_session.commit()
    db_session.expunge_all()

    stmt_doc = select(Documents).where(Documents.document_id == doc.document_id)
    saved_doc = await db_session.scalar(stmt_doc)

    stmt_chunk = select(Chunks).where(Chunks.chunk_id == chunk.chunk_id)
    saved_chunk = await db_session.scalar(stmt_chunk)
    assert saved_doc is not None
    assert saved_doc.document_id == doc.document_id
    assert saved_doc.source_path == doc.source_path
    assert saved_doc.file_type == doc.file_type
    assert saved_doc.tenant_id == doc.tenant_id
    assert saved_doc.meta_data == {}
    assert saved_doc.created_at is not None
    assert saved_doc.deleted_at is None
    assert saved_doc.status is Status.PENDING

    assert saved_chunk is not None
    assert saved_chunk.chunk_id is not None
    assert saved_chunk.chunk_id == chunk.chunk_id
    assert saved_chunk.content == chunk.content
    assert saved_chunk.chunk_index == chunk.chunk_index
    assert saved_chunk.embedding is not None
    assert len(saved_chunk.embedding) == 1536
    assert list(saved_chunk.embedding) == chunk.embedding
    assert saved_chunk.tenant_id == chunk.tenant_id
    assert saved_chunk.allowed_roles == []
    assert saved_chunk.created_at is not None
    assert saved_chunk.is_deleted is False


async def test_unique_constraint(db_session: AsyncSession) -> None:
    tenant_id = uuid4()

    doc = Documents(
        source_path="test_path_to_file",
        file_type="test_file_type",
        tenant_id=tenant_id,
    )

    db_session.add(doc)
    await db_session.flush()

    first_chunk = Chunks(
        document_id=doc.document_id,
        content="test_content_for_chunk",
        chunk_index=0,
        embedding=[0.5] * 1536,
        tenant_id=tenant_id,
    )
    db_session.add(first_chunk)
    await db_session.flush()

    second_chunk = Chunks(
        document_id=doc.document_id,
        content="test_content_for_chunk",
        chunk_index=0,
        embedding=[0.5] * 1536,
        tenant_id=tenant_id,
    )

    db_session.add(second_chunk)
    with pytest.raises(IntegrityError) as exc_info:
        await db_session.commit()

    assert "uq_chunk_index_chunk_id" in str(exc_info.value)


async def test_cascade_delete(db_session: AsyncSession) -> None:
    tenant_id = uuid4()

    doc = Documents(
        source_path="test_path_to_file",
        file_type="test_file_type",
        tenant_id=tenant_id,
    )

    db_session.add(doc)
    await db_session.flush()

    chunk = Chunks(
        document_id=doc.document_id,
        content="test_content_for_chunk",
        chunk_index=0,
        embedding=[0.5] * 1536,
        tenant_id=tenant_id,
    )
    db_session.add(chunk)
    await db_session.commit()
    _ = await db_session.execute(
        delete(Documents).where(Documents.document_id == doc.document_id)
    )
    db_session.expunge_all()

    stmt = select(Chunks).where(Chunks.chunk_id == chunk.chunk_id)
    deleted_chunk = await db_session.scalar(stmt)

    assert deleted_chunk is None


async def test_check_indexes(db_session: AsyncSession) -> None:
    stmt = text(
        """ SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'chunks';"""
    )
    indexes: dict[str, str] = dict((await db_session.execute(stmt)).all())

    assert indexes.get("idx_documents_id") is not None
    assert indexes.get("idx_tenant_id") is not None
    assert indexes.get("idx_chunks_embeddings") is not None
    assert "is_deleted" in indexes["idx_documents_id"].lower()
    assert "is_deleted" in indexes["idx_tenant_id"].lower()
    assert "is_deleted" in indexes["idx_chunks_embeddings"].lower()
    assert "hnsw" in indexes["idx_chunks_embeddings"].lower()
    assert "halfvec_cosine_ops" in indexes["idx_chunks_embeddings"].lower()


async def test_fk_foreign_chunk(db_session: AsyncSession) -> None:
    tenant_id_doc = uuid4()
    tenant_id_chunk = uuid4()

    doc = Documents(
        source_path="test_path_to_file",
        file_type="test_file_type",
        tenant_id=tenant_id_doc,
    )

    db_session.add(doc)
    await db_session.flush()

    first_chunk = Chunks(
        document_id=doc.document_id,
        content="test_content_for_chunk",
        chunk_index=0,
        embedding=[0.5] * 1536,
        tenant_id=tenant_id_chunk,
    )
    db_session.add(first_chunk)

    with pytest.raises(IntegrityError) as exc_info:
        await db_session.commit()

    assert "fk_document_id_tenant_id" in str(exc_info.value)
