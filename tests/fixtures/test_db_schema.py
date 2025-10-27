"""
Test database schema initialization and mock data fixtures
테스트 DB 스키마 초기화 및 Mock 데이터 픽스처
"""

import asyncio
import json
from sqlalchemy import text
from apps.core.db_session import engine, Base
import uuid
from datetime import datetime


def _import_models():
    """Import models to register them with Base.metadata (avoid circular import at module level)"""
    from apps.api.database import (
        Document,
        DocumentChunk,
        Embedding,
        DocTaxonomy,
        TaxonomyNode,
        db_manager,
    )

    return Document, DocumentChunk, Embedding, DocTaxonomy, TaxonomyNode, db_manager


async def init_test_db():
    """
    테스트 DB 스키마 초기화 - Self-contained
    CLAUDE.md 원칙: 코드로 정의된 사실만 사용, 추측 금지
    """
    # Import models to register with Base.metadata (avoid circular import)
    _import_models()

    async with engine.begin() as conn:
        # 0. PostgreSQL: pgvector extension 활성화
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as e:
            print(f"Extension creation failed (expected for SQLite): {e}")

        # 1. 모든 테이블 생성
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"FATAL: Table creation failed: {e}")
            raise

        # 2. SQLite FTS5 테이블 생성 (BM25 검색용) - PostgreSQL에서는 스킵
        from apps.core.db_session import DATABASE_URL

        if "sqlite" in DATABASE_URL.lower():
            try:
                await conn.execute(
                    text(
                        """
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
                    USING fts5(chunk_id UNINDEXED, text, tokenize='porter unicode61');
                """
                    )
                )
            except Exception as e:
                print(f"FTS5 creation failed: {e}")

        # 3. Golden Dataset 주입
        await _insert_golden_dataset(conn)


async def _insert_golden_dataset(conn):
    """Golden Dataset 주입 - 검증 가능한 실제 데이터"""

    # Document 1: ML Algorithms
    doc_id_1 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO documents (doc_id, title, source_url, content_type, doc_metadata, chunk_metadata, processed_at, created_at)
        VALUES (:doc_id, :title, :source_url, :content_type, :doc_metadata, :chunk_metadata, :processed_at, :created_at)
    """
        ),
        {
            "doc_id": doc_id_1,
            "title": "Machine Learning Algorithms Guide",
            "source_url": "https://example.com/ml-algorithms",
            "content_type": "article",
            "doc_metadata": json.dumps({}),
            "chunk_metadata": json.dumps({}),
            "processed_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        },
    )

    # Chunk 1-1
    chunk_id_1_1 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO chunks (chunk_id, doc_id, text, span, chunk_index, chunk_metadata, token_count, has_pii, pii_types, created_at)
        VALUES (:chunk_id, :doc_id, :text, :span, :chunk_index, :chunk_metadata, :token_count, :has_pii, :pii_types, :created_at)
    """
        ),
        {
            "chunk_id": chunk_id_1_1,
            "doc_id": doc_id_1,
            "text": "Machine learning algorithms are computational methods that enable automatic learning from data.",
            "span": "0,100",
            "chunk_index": 0,
            "chunk_metadata": json.dumps({}),
            "token_count": 15,
            "has_pii": False,
            "pii_types": [],
            "created_at": datetime.utcnow(),
        },
    )

    # FTS 인덱스에 추가 (SQLite only)
    from apps.core.db_session import DATABASE_URL

    if "sqlite" in DATABASE_URL.lower():
        await conn.execute(
            text(
                """
            INSERT INTO chunks_fts (chunk_id, text)
            VALUES (:chunk_id, :text)
        """
            ),
            {
                "chunk_id": chunk_id_1_1,
                "text": "Machine learning algorithms are computational methods that enable automatic learning from data.",
            },
        )

    # Embedding (1536차원 Mock)
    embedding_vector_1 = [0.1] * 1536
    embedding_id_1 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO embeddings (embedding_id, chunk_id, vec, model_name, created_at)
        VALUES (:embedding_id, :chunk_id, :vec, :model_name, :created_at)
    """
        ),
        {
            "embedding_id": embedding_id_1,
            "chunk_id": chunk_id_1_1,
            "vec": embedding_vector_1,
            "model_name": "text-embedding-ada-002",
            "created_at": datetime.utcnow(),
        },
    )

    # Taxonomy 매핑 - source와 assigned_at 컬럼은 실제 스키마에 없음
    # doc_taxonomy는 (doc_id, node_id, version) 복합키를 사용
    # 간단히 하기 위해 생략 (테스트에서 실제로 사용되지 않음)

    # Document 2: Neural Networks
    doc_id_2 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO documents (doc_id, title, source_url, content_type, doc_metadata, chunk_metadata, processed_at, created_at)
        VALUES (:doc_id, :title, :source_url, :content_type, :doc_metadata, :chunk_metadata, :processed_at, :created_at)
    """
        ),
        {
            "doc_id": doc_id_2,
            "title": "Neural Networks Tutorial",
            "source_url": "https://example.com/neural-networks",
            "content_type": "tutorial",
            "doc_metadata": json.dumps({}),
            "chunk_metadata": json.dumps({}),
            "processed_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        },
    )

    # Chunk 2-1
    chunk_id_2_1 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO chunks (chunk_id, doc_id, text, span, chunk_index, chunk_metadata, token_count, has_pii, pii_types, created_at)
        VALUES (:chunk_id, :doc_id, :text, :span, :chunk_index, :chunk_metadata, :token_count, :has_pii, :pii_types, :created_at)
    """
        ),
        {
            "chunk_id": chunk_id_2_1,
            "doc_id": doc_id_2,
            "text": "Neural networks are computational models inspired by biological neural networks.",
            "span": "0,80",
            "chunk_index": 0,
            "chunk_metadata": json.dumps({}),
            "token_count": 12,
            "has_pii": False,
            "pii_types": [],
            "created_at": datetime.utcnow(),
        },
    )

    if "sqlite" in DATABASE_URL.lower():
        await conn.execute(
            text(
                """
            INSERT INTO chunks_fts (chunk_id, text)
            VALUES (:chunk_id, :text)
        """
            ),
            {
                "chunk_id": chunk_id_2_1,
                "text": "Neural networks are computational models inspired by biological neural networks.",
            },
        )

    # Embedding 2
    embedding_vector_2 = [0.2] * 1536
    embedding_id_2 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO embeddings (embedding_id, chunk_id, vec, model_name, created_at)
        VALUES (:embedding_id, :chunk_id, :vec, :model_name, :created_at)
    """
        ),
        {
            "embedding_id": embedding_id_2,
            "chunk_id": chunk_id_2_1,
            "vec": embedding_vector_2,
            "model_name": "text-embedding-ada-002",
            "created_at": datetime.utcnow(),
        },
    )

    # Taxonomy 매핑 생략 (스키마 불일치)

    # Document 3: NLP
    doc_id_3 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO documents (doc_id, title, source_url, content_type, doc_metadata, chunk_metadata, processed_at, created_at)
        VALUES (:doc_id, :title, :source_url, :content_type, :doc_metadata, :chunk_metadata, :processed_at, :created_at)
    """
        ),
        {
            "doc_id": doc_id_3,
            "title": "Natural Language Processing",
            "source_url": "https://example.com/nlp",
            "content_type": "article",
            "doc_metadata": json.dumps({}),
            "chunk_metadata": json.dumps({}),
            "processed_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        },
    )

    chunk_id_3_1 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO chunks (chunk_id, doc_id, text, span, chunk_index, chunk_metadata, token_count, has_pii, pii_types, created_at)
        VALUES (:chunk_id, :doc_id, :text, :span, :chunk_index, :chunk_metadata, :token_count, :has_pii, :pii_types, :created_at)
    """
        ),
        {
            "chunk_id": chunk_id_3_1,
            "doc_id": doc_id_3,
            "text": "Natural language processing involves computational analysis of human language.",
            "span": "0,75",
            "chunk_index": 0,
            "chunk_metadata": json.dumps({}),
            "token_count": 11,
            "has_pii": False,
            "pii_types": [],
            "created_at": datetime.utcnow(),
        },
    )

    if "sqlite" in DATABASE_URL.lower():
        await conn.execute(
            text(
                """
            INSERT INTO chunks_fts (chunk_id, text)
            VALUES (:chunk_id, :text)
        """
            ),
            {
                "chunk_id": chunk_id_3_1,
                "text": "Natural language processing involves computational analysis of human language.",
            },
        )

    embedding_vector_3 = [0.15] * 1536
    embedding_id_3 = str(uuid.uuid4())
    await conn.execute(
        text(
            """
        INSERT INTO embeddings (embedding_id, chunk_id, vec, model_name, created_at)
        VALUES (:embedding_id, :chunk_id, :vec, :model_name, :created_at)
    """
        ),
        {
            "embedding_id": embedding_id_3,
            "chunk_id": chunk_id_3_1,
            "vec": embedding_vector_3,
            "model_name": "text-embedding-ada-002",
            "created_at": datetime.utcnow(),
        },
    )

    # Taxonomy 매핑 생략 (스키마 불일치)


async def cleanup_test_db():
    """테스트 DB 정리"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                try:
                    await conn.execute(text("DROP TABLE IF EXISTS chunks_fts"))
                except Exception:
                    pass
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(
                    f"Cleanup attempt {attempt + 1} failed, retrying after disposing engine: {e}"
                )
                await engine.dispose()
                await asyncio.sleep(0.2)
            else:
                print(
                    f"Warning: Database cleanup failed after {max_retries} attempts: {e}"
                )
                pass
