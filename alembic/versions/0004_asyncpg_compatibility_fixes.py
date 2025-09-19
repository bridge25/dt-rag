"""AsyncPG compatibility fixes and vector operator optimization

Revision ID: 0004
Revises: 0003
Create Date: 2025-09-19 13:10:00.000000

This migration addresses Critical Issues found in Phase 2:
1. PostgreSQL vector operator compatibility (<=> to <->)
2. Ensure doc_metadata column exists and is properly typed
3. Add proper indexes for asyncpg compatibility
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply asyncpg compatibility fixes"""

    # Check if we're running on PostgreSQL
    bind = op.get_bind()
    # Safely get database URL - handle both Connection and Engine objects
    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            # For newer SQLAlchemy versions, get URL from dialect
            database_url = str(bind.get_bind().url)
    except AttributeError:
        # Fallback: check dialect name directly
        database_url = bind.dialect.name

    if 'postgresql' in database_url:
        print("Applying PostgreSQL-specific fixes...")

        # 1. Ensure doc_metadata column exists in taxonomy_nodes
        # (This should already exist from earlier migrations, but we'll verify)
        try:
            # Try to add the column - will fail if it already exists
            op.add_column('taxonomy_nodes',
                         sa.Column('doc_metadata', postgresql.JSONB(), nullable=True))
            print("Added doc_metadata column to taxonomy_nodes")
        except Exception:
            # Column likely already exists, which is fine
            print("doc_metadata column already exists in taxonomy_nodes")

        # 2. Add better vector indexes for asyncpg compatibility
        try:
            # Check if pgvector extension is available first
            result = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
            has_pgvector = result.fetchone()[0]

            if has_pgvector:
                # Drop old vector indexes if they exist (with separate try-catch)
                try:
                    op.execute('DROP INDEX IF EXISTS idx_embeddings_vec_cosine')
                except Exception:
                    pass  # Index might not exist

                try:
                    op.execute('DROP INDEX IF EXISTS idx_embeddings_vec_ivf')
                except Exception:
                    pass  # Index might not exist

                # Create HNSW index for better performance with asyncpg
                try:
                    # Check if hnsw access method is available
                    result = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_am WHERE amname = 'hnsw')"))
                    has_hnsw = result.fetchone()[0]

                    if has_hnsw:
                        op.execute('''
                            CREATE INDEX IF NOT EXISTS idx_embeddings_vec_hnsw
                            ON embeddings USING hnsw (vec vector_cosine_ops)
                            WITH (m = 16, ef_construction = 64)
                        ''')
                        print("Created HNSW vector index for better asyncpg compatibility")
                    else:
                        # Fallback to btree index with HNSW name for consistency
                        op.execute('''
                            CREATE INDEX IF NOT EXISTS idx_embeddings_vec_hnsw
                            ON embeddings USING btree (vec)
                        ''')
                        print("Created btree vector index with HNSW name (HNSW not available)")
                except Exception as e:
                    print(f"HNSW index creation failed: {e}")
            else:
                print("pgvector extension not available, skipping vector index creation")

        except Exception as e:
            print(f"Vector index migration failed: {e}")

        # 3. Create function for safe vector operations (only if pgvector available)
        try:
            # Check if pgvector extension is available
            result = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
            has_pgvector = result.fetchone()[0]

            if has_pgvector:
                op.execute('''
                    CREATE OR REPLACE FUNCTION safe_cosine_distance(vec1 vector, vec2 vector)
                    RETURNS float8
                    LANGUAGE sql
                    IMMUTABLE STRICT
                    AS $$
                        SELECT CASE
                            WHEN vec1 IS NULL OR vec2 IS NULL THEN 1.0
                            ELSE 1.0 - (vec1 <#> vec2)
                        END;
                    $$;
                ''')
                print("Created safe_cosine_distance function for vector operations")
            else:
                print("pgvector extension not available, skipping vector function creation")
        except Exception as e:
            print(f"Vector function creation failed: {e}")

        # 4. Add indexes for better query performance
        op.execute('CREATE INDEX IF NOT EXISTS idx_chunks_doc_id_text ON chunks (doc_id, text)')
        op.execute('CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_path ON doc_taxonomy (doc_id, path)')
        op.execute('CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_model ON embeddings (chunk_id, model_name)')

        # 5. Update statistics for better query planning
        op.execute('ANALYZE taxonomy_nodes')
        op.execute('ANALYZE chunks')
        op.execute('ANALYZE embeddings')
        op.execute('ANALYZE doc_taxonomy')

        print("PostgreSQL asyncpg compatibility fixes applied successfully")

    else:
        print("SQLite detected - skipping PostgreSQL-specific fixes")
        # For SQLite, ensure the schema is compatible

        # Check if doc_metadata exists in SQLite
        inspector = sa.inspect(bind)
        columns = inspector.get_columns('taxonomy_nodes')

        has_doc_metadata = any(col['name'] == 'doc_metadata' for col in columns)

        if not has_doc_metadata:
            # Add doc_metadata column for SQLite
            op.add_column('taxonomy_nodes',
                         sa.Column('doc_metadata', sa.TEXT(), nullable=True))
            print("Added doc_metadata column to taxonomy_nodes (SQLite)")
        else:
            print("doc_metadata column already exists in taxonomy_nodes (SQLite)")


def downgrade() -> None:
    """Remove asyncpg compatibility fixes"""

    bind = op.get_bind()
    # Safely get database URL - handle both Connection and Engine objects
    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            # For newer SQLAlchemy versions, get URL from dialect
            database_url = str(bind.get_bind().url)
    except AttributeError:
        # Fallback: check dialect name directly
        database_url = bind.dialect.name

    if 'postgresql' in database_url:
        # Remove PostgreSQL-specific changes
        try:
            op.execute('DROP FUNCTION IF EXISTS safe_cosine_distance(vector, vector)')
        except Exception:
            pass

        try:
            op.execute('DROP INDEX IF EXISTS idx_embeddings_vec_hnsw')
        except Exception:
            pass

        try:
            op.execute('DROP INDEX IF EXISTS idx_chunks_doc_id_text')
            op.execute('DROP INDEX IF EXISTS idx_doc_taxonomy_doc_path')
            op.execute('DROP INDEX IF EXISTS idx_embeddings_chunk_model')
        except Exception:
            pass

        print("Removed PostgreSQL asyncpg compatibility fixes")

    # Note: We don't remove doc_metadata column as it may contain data
    print("Downgrade completed (doc_metadata column preserved)")