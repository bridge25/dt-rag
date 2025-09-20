"""Vector search performance optimization

Revision ID: 0005
Revises: 0004
Create Date: 2025-09-20 00:15:00.000000

Optimizes pgvector HNSW index parameters and adds specialized indexes
for high-performance vector search and hybrid retrieval.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def check_index_exists(index_name: str) -> bool:
    """Check if index exists using pg_indexes"""
    bind = op.get_bind()
    result = bind.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE indexname = :index_name
        )
    """), {"index_name": index_name})
    return result.scalar()


def get_table_size(table_name: str) -> int:
    """Get approximate table row count"""
    bind = op.get_bind()
    try:
        result = bind.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar() or 0
    except Exception:
        return 0


def upgrade() -> None:
    """Apply vector search performance optimizations"""

    bind = op.get_bind()

    # Check if we're using PostgreSQL with pgvector
    is_postgresql = False
    pgvector_available = False

    try:
        database_url = str(bind.engine.url) if hasattr(bind, 'engine') else str(bind.url)
        is_postgresql = 'postgresql' in database_url.lower()
    except Exception:
        try:
            is_postgresql = bind.dialect.name == 'postgresql'
        except Exception:
            is_postgresql = False

    if is_postgresql:
        try:
            # Check pgvector availability
            bind.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            pgvector_available = True
        except Exception:
            pgvector_available = False

    if not (is_postgresql and pgvector_available):
        print("⚠ Skipping vector optimizations: PostgreSQL with pgvector required")
        return

    print("🚀 Applying vector search performance optimizations...")

    # 1. Optimize HNSW index parameters based on data size
    embeddings_count = get_table_size('embeddings')

    # Determine optimal parameters based on dataset size
    if embeddings_count < 1000:
        # Small dataset: favor recall over build time
        m_param = 16
        ef_construction = 64
        ef_search = 40
    elif embeddings_count < 10000:
        # Medium dataset: balanced approach
        m_param = 24
        ef_construction = 128
        ef_search = 64
    else:
        # Large dataset: favor build time, still good recall
        m_param = 32
        ef_construction = 200
        ef_search = 80

    try:
        # Drop existing HNSW index if it exists
        if check_index_exists('idx_embeddings_vec_hnsw'):
            bind.execute(text('DROP INDEX idx_embeddings_vec_hnsw'))
            print("✓ Dropped existing HNSW index for optimization")

        # Create optimized HNSW index
        bind.execute(text(f'''
            CREATE INDEX idx_embeddings_vec_hnsw_optimized
            ON embeddings USING hnsw (vec vector_cosine_ops)
            WITH (m = {m_param}, ef_construction = {ef_construction})
        '''))
        print(f"✓ Created optimized HNSW index (m={m_param}, ef_construction={ef_construction})")

        # Set runtime parameter for search
        bind.execute(text(f'SET hnsw.ef_search = {ef_search}'))
        print(f"✓ Set HNSW ef_search parameter to {ef_search}")

    except Exception as e:
        print(f"⚠ HNSW optimization failed: {e}")

    # 2. Create specialized indexes for hybrid search
    try:
        # BM25 + metadata composite index
        if not check_index_exists('idx_embeddings_hybrid_search'):
            bind.execute(text('''
                CREATE INDEX idx_embeddings_hybrid_search
                ON embeddings (chunk_id, model_name, created_at)
                INCLUDE (bm25_tokens)
            '''))
            print("✓ Created hybrid search composite index")

        # Taxonomy path optimization for filtered search
        if not check_index_exists('idx_doc_taxonomy_path_gin_optimized'):
            bind.execute(text('''
                CREATE INDEX idx_doc_taxonomy_path_gin_optimized
                ON doc_taxonomy USING GIN (path gin__int_ops)
            '''))
            print("✓ Created optimized taxonomy path GIN index")

    except Exception as e:
        print(f"⚠ Hybrid search index creation failed: {e}")

    # 3. Create covering indexes for frequent query patterns
    covering_indexes = [
        {
            'name': 'idx_chunks_search_covering',
            'table': 'chunks',
            'definition': '''
                CREATE INDEX idx_chunks_search_covering
                ON chunks (doc_id, chunk_index)
                INCLUDE (text, span, chunk_metadata)
            '''
        },
        {
            'name': 'idx_documents_metadata_covering',
            'table': 'documents',
            'definition': '''
                CREATE INDEX idx_documents_metadata_covering
                ON documents (doc_id)
                INCLUDE (title, source_url, doc_metadata, processed_at)
            '''
        }
    ]

    for idx in covering_indexes:
        try:
            if not check_index_exists(idx['name']):
                bind.execute(text(idx['definition']))
                print(f"✓ Created covering index: {idx['name']}")
        except Exception as e:
            print(f"⚠ Failed to create {idx['name']}: {e}")

    # 4. Optimize PostgreSQL settings for vector workloads
    try:
        # Increase work_mem for vector operations
        bind.execute(text("SET work_mem = '256MB'"))

        # Optimize for vector similarity queries
        bind.execute(text("SET enable_seqscan = off"))
        bind.execute(text("SET random_page_cost = 1.1"))

        # Update table statistics for better query planning
        for table in ['embeddings', 'chunks', 'documents', 'doc_taxonomy']:
            bind.execute(text(f'ANALYZE {table}'))

        print("✓ Applied PostgreSQL optimization settings")

    except Exception as e:
        print(f"⚠ PostgreSQL settings optimization failed: {e}")

    # 5. Create materialized view for hot search paths
    try:
        if not check_index_exists('mv_hot_search_paths'):  # Reusing function for existence check
            bind.execute(text('''
                CREATE MATERIALIZED VIEW mv_hot_search_paths AS
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    e.vec,
                    e.bm25_tokens,
                    c.chunk_metadata
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                JOIN embeddings e ON c.chunk_id = e.chunk_id
                WHERE e.vec IS NOT NULL
                  AND array_length(e.bm25_tokens, 1) > 0
            '''))

            # Create index on materialized view
            bind.execute(text('''
                CREATE INDEX idx_mv_hot_search_paths_vec
                ON mv_hot_search_paths USING hnsw (vec vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            '''))

            bind.execute(text('''
                CREATE INDEX idx_mv_hot_search_paths_text
                ON mv_hot_search_paths USING GIN (to_tsvector('english', text))
            '''))

            print("✓ Created materialized view for hot search paths")

    except Exception as e:
        print(f"⚠ Materialized view creation failed: {e}")

    print("✅ Vector search performance optimizations completed")


def downgrade() -> None:
    """Remove vector search performance optimizations"""

    bind = op.get_bind()

    try:
        # Remove materialized view
        bind.execute(text('DROP MATERIALIZED VIEW IF EXISTS mv_hot_search_paths'))

        # Remove specialized indexes
        indexes_to_remove = [
            'idx_embeddings_vec_hnsw_optimized',
            'idx_embeddings_hybrid_search',
            'idx_doc_taxonomy_path_gin_optimized',
            'idx_chunks_search_covering',
            'idx_documents_metadata_covering'
        ]

        for idx_name in indexes_to_remove:
            if check_index_exists(idx_name):
                bind.execute(text(f'DROP INDEX IF EXISTS {idx_name}'))
                print(f"✓ Removed index: {idx_name}")

        # Restore default HNSW index
        if not check_index_exists('idx_embeddings_vec_hnsw'):
            bind.execute(text('''
                CREATE INDEX idx_embeddings_vec_hnsw
                ON embeddings USING hnsw (vec vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            '''))
            print("✓ Restored default HNSW index")

        print("✅ Vector optimizations rollback completed")

    except Exception as e:
        print(f"⚠ Error during downgrade: {e}")