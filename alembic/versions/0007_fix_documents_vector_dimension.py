"""Fix documents table vector dimension from 768 to 1536

Revision ID: 0007
Revises: 0006
Create Date: 2025-10-03 00:00:00.000000

This migration fixes the documents.embedding column to use 1536 dimensions
to match the embeddings table and the actual embedding model (OpenAI text-embedding-3-large).

Changes:
- ALTER documents.embedding from vector(768) to vector(1536)
- Recreate IVFFlat index with correct dimension
- Update any existing sample data (will be truncated)
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change documents.embedding dimension to 1536"""
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
        print("Fixing documents table vector dimension to 1536...")

        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                ) AND EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'documents'
                ) AND EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'embedding'
                ) THEN
                    -- Step 1: Drop existing IVFFlat index on documents
                    DROP INDEX IF EXISTS documents_embedding_idx;

                    -- Step 2: Set all embeddings to NULL (incompatible dimensions)
                    UPDATE documents SET embedding = NULL WHERE embedding IS NOT NULL;

                    -- Step 3: Change documents.embedding from vector(768) to vector(1536)
                    ALTER TABLE documents ALTER COLUMN embedding TYPE vector(1536);

                    RAISE NOTICE 'documents.embedding dimension changed to 1536';

                    -- Step 4: Create optimized IVFFlat index for 1536-dim vectors
                    -- Using lists=100 for moderate-sized datasets (can be tuned)
                    CREATE INDEX documents_embedding_idx
                    ON documents
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);

                    RAISE NOTICE 'IVFFlat index created for documents.embedding (1536-dim)';

                    -- Step 5: Update table comment
                    COMMENT ON COLUMN documents.embedding IS '1536-dimensional vector embedding from OpenAI text-embedding-3-large';
                ELSE
                    RAISE NOTICE 'Skipping vector migration: extension, table, or column not found';
                END IF;
            END
            $$;
        """)

        print("documents table vector dimension fixed successfully")
    else:
        print("SQLite detected - skipping PostgreSQL-specific vector migration")
        print("Note: SQLite stores vectors as JSON, no schema change needed")


def downgrade() -> None:
    """Rollback documents.embedding to vector(768)"""
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
        print("Rolling back documents.embedding to vector(768)...")

        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                ) THEN
                    -- Step 1: Drop IVFFlat index
                    DROP INDEX IF EXISTS documents_embedding_idx;

                    -- Step 2: Nullify embeddings (incompatible dimensions)
                    UPDATE documents SET embedding = NULL WHERE embedding IS NOT NULL;

                    -- Step 3: Rollback to vector(768)
                    ALTER TABLE documents ALTER COLUMN embedding TYPE vector(768);

                    RAISE NOTICE 'Rolled back documents.embedding to vector(768)';

                    -- Step 4: Recreate IVFFlat index for 768-dim
                    CREATE INDEX documents_embedding_idx
                    ON documents
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);

                    RAISE NOTICE 'IVFFlat index recreated for 768-dim vectors';
                ELSE
                    RAISE NOTICE 'pgvector extension not installed, skipping rollback';
                END IF;
            END
            $$;
        """)

        print("Rollback to 768-dim completed successfully")
    else:
        print("SQLite detected - skipping PostgreSQL-specific rollback")
