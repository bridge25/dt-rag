"""
Investigate Hybrid Search Issues
Focus on BM25 and taxonomy filtering problems
"""

import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apps.search.hybrid_search_engine import search_engine
from apps.core.db_session import DATABASE_URL, async_session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database_schema():
    """Check actual database schema"""
    print("\n" + "="*80)
    print("DATABASE SCHEMA INVESTIGATION")
    print("="*80)
    print(f"\nDatabase URL: {DATABASE_URL}")

    try:
        async with async_session() as session:
            # Check if tables exist
            if "postgresql" in DATABASE_URL:
                query = text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            else:
                # SQLite
                query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    ORDER BY name
                """)

            result = await session.execute(query)
            tables = result.fetchall()

            print(f"\nTables found: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")

            # Check chunks table structure
            if "postgresql" in DATABASE_URL:
                query = text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'chunks'
                    ORDER BY ordinal_position
                """)
            else:
                query = text("PRAGMA table_info(chunks)")

            result = await session.execute(query)
            columns = result.fetchall()

            print(f"\nChunks table columns:")
            for col in columns:
                print(f"  - {col}")

            # Check embeddings table
            if "postgresql" in DATABASE_URL:
                query = text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'embeddings'
                    ORDER BY ordinal_position
                """)
            else:
                query = text("PRAGMA table_info(embeddings)")

            result = await session.execute(query)
            columns = result.fetchall()

            print(f"\nEmbeddings table columns:")
            for col in columns:
                print(f"  - {col}")

            # Count data
            query = text("SELECT COUNT(*) FROM chunks")
            result = await session.execute(query)
            chunk_count = result.scalar()
            print(f"\nTotal chunks: {chunk_count}")

            query = text("SELECT COUNT(*) FROM embeddings")
            result = await session.execute(query)
            embedding_count = result.scalar()
            print(f"Total embeddings: {embedding_count}")

            # Sample data
            query = text("SELECT chunk_id, text FROM chunks LIMIT 3")
            result = await session.execute(query)
            samples = result.fetchall()

            print(f"\nSample chunks:")
            for chunk in samples:
                print(f"  - {chunk[0]}: {chunk[1][:60]}...")

    except Exception as e:
        logger.error(f"Schema check failed: {e}", exc_info=True)


async def test_bm25_query_directly():
    """Test BM25 query directly with SQLite"""
    print("\n" + "="*80)
    print("DIRECT BM25 QUERY TEST")
    print("="*80)

    query_text = "machine learning"

    try:
        async with async_session() as session:
            if "postgresql" in DATABASE_URL:
                # PostgreSQL FTS
                sql = text("""
                    SELECT
                        c.chunk_id,
                        c.text,
                        ts_rank_cd(
                            to_tsvector('english', c.text),
                            plainto_tsquery('english', :query),
                            32 | 1
                        ) as bm25_score
                    FROM chunks c
                    WHERE to_tsvector('english', c.text) @@ plainto_tsquery('english', :query)
                    ORDER BY bm25_score DESC
                    LIMIT 3
                """)
            else:
                # SQLite - simple LIKE search
                sql = text("""
                    SELECT
                        c.chunk_id,
                        c.text,
                        1.0 as bm25_score
                    FROM chunks c
                    WHERE c.text LIKE '%' || :query || '%'
                    LIMIT 3
                """)

            result = await session.execute(sql, {"query": query_text})
            rows = result.fetchall()

            print(f"\nQuery: '{query_text}'")
            print(f"Results: {len(rows)}")

            for i, row in enumerate(rows, 1):
                print(f"\n  [{i}] Chunk ID: {row[0]}")
                print(f"      Text: {row[1][:80]}...")
                print(f"      Score: {row[2]:.4f}")

    except Exception as e:
        logger.error(f"Direct BM25 query failed: {e}", exc_info=True)


async def test_vector_query_directly():
    """Test vector query directly"""
    print("\n" + "="*80)
    print("DIRECT VECTOR QUERY TEST")
    print("="*80)

    try:
        from apps.api.embedding_service import embedding_service

        query_text = "deep learning"
        print(f"\nQuery: '{query_text}'")

        # Generate embedding
        embedding = await embedding_service.generate_embedding(query_text)
        print(f"Embedding generated: {len(embedding)} dimensions")

        async with async_session() as session:
            if "postgresql" in DATABASE_URL:
                # PostgreSQL with pgvector
                vector_str = "[" + ",".join(map(str, embedding)) + "]"
                sql = text(f"""
                    SELECT
                        c.chunk_id,
                        c.text,
                        1 - (e.embedding <=> '{vector_str}'::vector) as cosine_similarity
                    FROM chunks c
                    JOIN embeddings e ON c.chunk_id = e.chunk_id
                    WHERE e.embedding IS NOT NULL
                    ORDER BY e.embedding <=> '{vector_str}'::vector
                    LIMIT 3
                """)
                query_params = {}
            else:
                # SQLite - just return any chunks with embeddings
                sql = text("""
                    SELECT
                        c.chunk_id,
                        c.text,
                        0.5 as cosine_similarity
                    FROM chunks c
                    JOIN embeddings e ON c.chunk_id = e.chunk_id
                    WHERE e.vec IS NOT NULL
                    LIMIT 3
                """)
                query_params = {}

            result = await session.execute(sql, query_params)
            rows = result.fetchall()

            print(f"Results: {len(rows)}")

            for i, row in enumerate(rows, 1):
                print(f"\n  [{i}] Chunk ID: {row[0]}")
                print(f"      Text: {row[1][:80]}...")
                print(f"      Similarity: {row[2]:.4f}")

    except Exception as e:
        logger.error(f"Direct vector query failed: {e}", exc_info=True)


async def test_taxonomy_filtering_issue():
    """Test taxonomy filtering syntax issue"""
    print("\n" + "="*80)
    print("TAXONOMY FILTERING ISSUE INVESTIGATION")
    print("="*80)

    try:
        async with async_session() as session:
            # Check doc_taxonomy table
            query = text("SELECT COUNT(*) FROM doc_taxonomy")
            result = await session.execute(query)
            count = result.scalar()
            print(f"\nTotal taxonomy records: {count}")

            if count > 0:
                query = text("SELECT doc_id, path FROM doc_taxonomy LIMIT 3")
                result = await session.execute(query)
                samples = result.fetchall()

                print(f"\nSample taxonomy paths:")
                for sample in samples:
                    print(f"  - Doc ID: {sample[0]}, Path: {sample[1]}")

            # Test problematic filter clause
            filter_clause = search_engine._build_filter_clause({
                "taxonomy_paths": [["Technology", "Software", "Databases"]]
            })

            print(f"\nGenerated filter clause:")
            print(f"  {filter_clause}")

    except Exception as e:
        logger.error(f"Taxonomy investigation failed: {e}", exc_info=True)


async def test_search_with_debugging():
    """Test search with detailed debugging"""
    print("\n" + "="*80)
    print("SEARCH WITH DETAILED DEBUGGING")
    print("="*80)

    query = "artificial intelligence"
    print(f"\nQuery: '{query}'")

    try:
        # Test BM25 search directly
        print("\n--- Testing BM25 Search ---")
        bm25_results = await search_engine._perform_bm25_search(query, 5, {})
        print(f"BM25 results: {len(bm25_results)}")
        for i, r in enumerate(bm25_results[:3], 1):
            print(f"  [{i}] {r.chunk_id}: BM25={r.bm25_score:.4f}")

        # Test Vector search directly
        print("\n--- Testing Vector Search ---")
        from apps.api.embedding_service import embedding_service
        embedding = await embedding_service.generate_embedding(query)
        vector_results = await search_engine._perform_vector_search(embedding, 5, {})
        print(f"Vector results: {len(vector_results)}")
        for i, r in enumerate(vector_results[:3], 1):
            print(f"  [{i}] {r.chunk_id}: Vector={r.vector_score:.4f}")

        # Test full hybrid search
        print("\n--- Testing Full Hybrid Search ---")
        results, metrics = await search_engine.search(query, top_k=5)
        print(f"Hybrid results: {len(results)}")
        print(f"Metrics: BM25={metrics.bm25_time:.3f}s, Vector={metrics.vector_time:.3f}s, Total={metrics.total_time:.3f}s")

        for i, r in enumerate(results[:3], 1):
            print(f"  [{i}] {r.chunk_id}: BM25={r.bm25_score:.4f}, Vector={r.vector_score:.4f}, Hybrid={r.hybrid_score:.4f}")

    except Exception as e:
        logger.error(f"Search debugging failed: {e}", exc_info=True)


async def main():
    """Run all investigations"""
    print("\n" + "="*80)
    print("HYBRID SEARCH ISSUE INVESTIGATION")
    print("="*80)

    await check_database_schema()
    await test_bm25_query_directly()
    await test_vector_query_directly()
    await test_taxonomy_filtering_issue()
    await test_search_with_debugging()

    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
