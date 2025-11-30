"""
Document Repository Implementation

SQLAlchemy implementation of IDocumentRepository interface.

@CODE:CLEAN-ARCHITECTURE-DOCUMENT-REPOSITORY-IMPL
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ...domain.entities.document import Document, DocumentChunk, DocumentWithChunks
from ...domain.repositories.document_repository import (
    IDocumentRepository,
    DocumentFilterParams,
    ChunkFilterParams,
    CreateDocumentParams,
    CreateChunkParams,
)
from ..mappers.document_mapper import DocumentMapper
from ...database import Document as DocumentModel, DocumentChunk as ChunkModel

logger = logging.getLogger(__name__)


class DocumentRepositoryImpl(IDocumentRepository):
    """
    Document Repository Implementation

    SQLAlchemy-based implementation of document data access.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # Document Operations

    async def get_document_by_id(self, doc_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        try:
            result = await self._session.execute(
                select(DocumentModel).where(DocumentModel.doc_id == doc_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return DocumentMapper.document_to_domain(model)
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise

    async def get_all_documents(
        self,
        params: Optional[DocumentFilterParams] = None
    ) -> List[Document]:
        """Get all documents with optional filtering"""
        try:
            query = select(DocumentModel)

            if params:
                conditions = []

                if params.content_type:
                    conditions.append(DocumentModel.content_type == params.content_type)

                if params.source_url_contains:
                    conditions.append(
                        DocumentModel.source_url.ilike(f"%{params.source_url_contains}%")
                    )

                if params.created_after:
                    conditions.append(DocumentModel.created_at >= params.created_after)

                if params.created_before:
                    conditions.append(DocumentModel.created_at <= params.created_before)

                if conditions:
                    query = query.where(and_(*conditions))

                query = query.limit(params.limit).offset(params.offset)

            result = await self._session.execute(query)
            models = result.scalars().all()

            return [DocumentMapper.document_to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            raise

    async def create_document(self, params: CreateDocumentParams) -> Document:
        """Create a new document"""
        try:
            model = DocumentModel(
                doc_id=uuid4(),
                title=params.title,
                source_url=params.source_url,
                content_type=params.content_type,
                file_size=params.file_size,
                checksum=params.checksum,
                version_tag=params.version_tag,
                license_tag=params.license_tag,
                doc_metadata=params.metadata or {},
                chunk_metadata={},
                created_at=datetime.utcnow(),
                processed_at=datetime.utcnow(),
            )

            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)

            return DocumentMapper.document_to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create document: {e}")
            raise

    async def delete_document(self, doc_id: UUID) -> bool:
        """Delete a document and all its chunks"""
        try:
            result = await self._session.execute(
                select(DocumentModel).where(DocumentModel.doc_id == doc_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return False

            await self._session.delete(model)
            await self._session.commit()

            return True
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    async def get_document_by_checksum(self, checksum: str) -> Optional[Document]:
        """Find document by content checksum"""
        try:
            result = await self._session.execute(
                select(DocumentModel).where(DocumentModel.checksum == checksum)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return DocumentMapper.document_to_domain(model)
        except Exception as e:
            logger.error(f"Failed to get document by checksum: {e}")
            raise

    async def count_documents(
        self,
        params: Optional[DocumentFilterParams] = None
    ) -> int:
        """Count documents matching filters"""
        try:
            query = select(func.count()).select_from(DocumentModel)

            if params:
                conditions = []
                if params.content_type:
                    conditions.append(DocumentModel.content_type == params.content_type)
                if params.source_url_contains:
                    conditions.append(
                        DocumentModel.source_url.ilike(f"%{params.source_url_contains}%")
                    )
                if conditions:
                    query = query.where(and_(*conditions))

            result = await self._session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            raise

    # Chunk Operations

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk by ID"""
        try:
            result = await self._session.execute(
                select(ChunkModel).where(ChunkModel.chunk_id == chunk_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return DocumentMapper.chunk_to_domain(model)
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            raise

    async def get_chunks_by_doc_id(self, doc_id: UUID) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        try:
            result = await self._session.execute(
                select(ChunkModel)
                .where(ChunkModel.doc_id == doc_id)
                .order_by(ChunkModel.chunk_index)
            )
            models = result.scalars().all()

            return [DocumentMapper.chunk_to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get chunks for document {doc_id}: {e}")
            raise

    async def get_chunks(
        self,
        params: Optional[ChunkFilterParams] = None
    ) -> List[DocumentChunk]:
        """Get chunks with optional filtering"""
        try:
            query = select(ChunkModel)

            if params:
                conditions = []

                if params.doc_id:
                    conditions.append(ChunkModel.doc_id == params.doc_id)

                if params.has_embedding is not None:
                    if params.has_embedding:
                        conditions.append(ChunkModel.embedding.isnot(None))
                    else:
                        conditions.append(ChunkModel.embedding.is_(None))

                if params.has_pii is not None:
                    conditions.append(ChunkModel.has_pii == params.has_pii)

                if params.min_token_count is not None:
                    conditions.append(ChunkModel.token_count >= params.min_token_count)

                if params.max_token_count is not None:
                    conditions.append(ChunkModel.token_count <= params.max_token_count)

                if conditions:
                    query = query.where(and_(*conditions))

                query = query.limit(params.limit).offset(params.offset)

            result = await self._session.execute(query)
            models = result.scalars().all()

            return [DocumentMapper.chunk_to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            raise

    async def create_chunk(self, params: CreateChunkParams) -> DocumentChunk:
        """Create a new chunk"""
        try:
            model = ChunkModel(
                chunk_id=uuid4(),
                doc_id=params.doc_id,
                text=params.text,
                chunk_index=params.chunk_index,
                span=f"{params.span[0]},{params.span[1]}",
                token_count=params.token_count,
                embedding=params.embedding,
                has_pii=params.has_pii,
                pii_types=params.pii_types or [],
                chunk_metadata=params.metadata or {},
                created_at=datetime.utcnow(),
            )

            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)

            return DocumentMapper.chunk_to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create chunk: {e}")
            raise

    async def create_chunks_batch(
        self,
        chunks: List[CreateChunkParams]
    ) -> List[DocumentChunk]:
        """Create multiple chunks in batch"""
        try:
            models = []
            for params in chunks:
                model = ChunkModel(
                    chunk_id=uuid4(),
                    doc_id=params.doc_id,
                    text=params.text,
                    chunk_index=params.chunk_index,
                    span=f"{params.span[0]},{params.span[1]}",
                    token_count=params.token_count,
                    embedding=params.embedding,
                    has_pii=params.has_pii,
                    pii_types=params.pii_types or [],
                    chunk_metadata=params.metadata or {},
                    created_at=datetime.utcnow(),
                )
                models.append(model)

            self._session.add_all(models)
            await self._session.commit()

            for model in models:
                await self._session.refresh(model)

            return [DocumentMapper.chunk_to_domain(m) for m in models]
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create chunks batch: {e}")
            raise

    async def update_chunk_embedding(
        self,
        chunk_id: UUID,
        embedding: List[float]
    ) -> DocumentChunk:
        """Update chunk embedding vector"""
        try:
            result = await self._session.execute(
                select(ChunkModel).where(ChunkModel.chunk_id == chunk_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                raise ValueError(f"Chunk not found: {chunk_id}")

            model.embedding = embedding

            await self._session.commit()
            await self._session.refresh(model)

            return DocumentMapper.chunk_to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to update chunk embedding {chunk_id}: {e}")
            raise

    async def count_chunks(
        self,
        params: Optional[ChunkFilterParams] = None
    ) -> int:
        """Count chunks matching filters"""
        try:
            query = select(func.count()).select_from(ChunkModel)

            if params:
                conditions = []
                if params.doc_id:
                    conditions.append(ChunkModel.doc_id == params.doc_id)
                if params.has_embedding is not None:
                    if params.has_embedding:
                        conditions.append(ChunkModel.embedding.isnot(None))
                    else:
                        conditions.append(ChunkModel.embedding.is_(None))
                if conditions:
                    query = query.where(and_(*conditions))

            result = await self._session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count chunks: {e}")
            raise

    # Combined Operations

    async def get_document_with_chunks(
        self,
        doc_id: UUID
    ) -> Optional[DocumentWithChunks]:
        """Get document with all its chunks"""
        document = await self.get_document_by_id(doc_id)
        if document is None:
            return None

        chunks = await self.get_chunks_by_doc_id(doc_id)

        return DocumentWithChunks(document=document, chunks=chunks)

    async def get_chunks_without_embeddings(
        self,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """Get chunks that need embedding generation"""
        params = ChunkFilterParams(has_embedding=False, limit=limit)
        return await self.get_chunks(params)

    # Statistics

    async def get_statistics(self) -> Dict[str, Any]:
        """Get document/chunk statistics"""
        try:
            total_docs = await self.count_documents()
            total_chunks = await self.count_chunks()
            embedded_chunks = await self.count_chunks(
                ChunkFilterParams(has_embedding=True)
            )

            # Get total tokens
            result = await self._session.execute(
                select(func.sum(ChunkModel.token_count))
            )
            total_tokens = result.scalar() or 0

            embedding_coverage = (
                (embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0
            )

            return {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "total_tokens": total_tokens,
                "embedding_coverage": embedding_coverage,
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "embedded_chunks": 0,
                "total_tokens": 0,
                "embedding_coverage": 0,
            }
