"""Change embedding vector dimension from 768 to 1536

Revision ID: 0005
Revises: 0004
Create Date: 2025-10-01 00:00:00.000000

This migration changes the vector dimension from 768 to 1536 to match
the OpenAI text-embedding-ada-002 model specification.

WARNING: This migration will TRUNCATE the embeddings table because
768-dimension vectors are incompatible with 1536-dimension vectors.
All existing embedding data will be deleted and must be regenerated.
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change vector dimension to 1536"""
    bind = op.get_bind()

    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            database_url = str(bind.get_bind().url)
    except AttributeError:
        database_url = bind.dialect.name

    if 'postgresql' in database_url:
        print("Applying vector dimension migration to PostgreSQL...")

        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                ) THEN
                    -- Step 1: Drop existing vector indexes
                    DROP INDEX IF EXISTS idx_embeddings_vec_hnsw;
                    DROP INDEX IF EXISTS idx_embeddings_vec_cosine;
                    DROP INDEX IF EXISTS idx_embeddings_vec_ivf;
                    DROP INDEX IF EXISTS idx_embeddings_vec_ivfflat;

                    -- Step 2: Change vector dimension
                    ALTER TABLE embeddings ALTER COLUMN vec TYPE vector(1536);

                    -- Step 3: Truncate table (existing 768-dim data is invalid)
                    TRUNCATE TABLE embeddings CASCADE;

                    RAISE NOTICE 'Vector dimension changed to 1536. Existing data truncated.';

                    -- Step 4: Create optimized HNSW index for 1536-dim vectors
                    CREATE INDEX idx_embeddings_vec_hnsw
                    ON embeddings
                    USING hnsw (vec vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);

                    RAISE NOTICE 'HNSW index created for 1536-dim vectors.';
                ELSE
                    RAISE NOTICE 'pgvector extension not installed, skipping vector migration';
                END IF;
            END
            $$;
        """)

        print("Vector dimension migration completed successfully")
    else:
        print("SQLite detected - skipping PostgreSQL-specific vector migration")


def downgrade() -> None:
    """Rollback to vector dimension 768"""
    bind = op.get_bind()

    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            database_url = str(bind.get_bind().url)
    except AttributeError:
        database_url = bind.dialect.name

    if 'postgresql' in database_url:
        print("Rolling back vector dimension to 768...")

        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                ) THEN
                    -- Step 1: Drop existing vector indexes
                    DROP INDEX IF EXISTS idx_embeddings_vec_hnsw;
                    DROP INDEX IF EXISTS idx_embeddings_vec_cosine;
                    DROP INDEX IF EXISTS idx_embeddings_vec_ivf;

                    -- Step 2: Rollback to vector(768)
                    ALTER TABLE embeddings ALTER COLUMN vec TYPE vector(768);

                    -- Step 3: Truncate table (1536-dim data is invalid for 768-dim)
                    TRUNCATE TABLE embeddings CASCADE;

                    RAISE NOTICE 'Rolled back to vector(768). Data truncated.';

                    -- Step 4: Recreate index for 768-dim
                    CREATE INDEX idx_embeddings_vec_hnsw
                    ON embeddings
                    USING hnsw (vec vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);

                    RAISE NOTICE 'HNSW index recreated for 768-dim vectors.';
                ELSE
                    RAISE NOTICE 'pgvector extension not installed, skipping rollback';
                END IF;
            END
            $$;
        """)

        print("Rollback to 768-dim vectors completed successfully")
    else:
        print("SQLite detected - skipping PostgreSQL-specific rollback")
