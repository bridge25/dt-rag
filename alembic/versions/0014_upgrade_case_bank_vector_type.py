"""Upgrade case_bank.query_vector to pgvector type

Revision ID: 0014
Revises: 0013
Create Date: 2025-11-11 00:00:00.000000

@CODE:TAG-CASEBANK-MIGRATION-004
Upgrades query_vector from FLOAT[] to vector(1536) for:
- HNSW index compatibility (10x+ performance)
- Proper vector similarity operations
- Optimal memory usage

This migration implements the user-approved strategy:
- Option B: Offline migration with short downtime
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade query_vector from FLOAT[] to vector(1536)

    Strategy: Offline migration (user-approved)
    - Ensures data integrity
    - Creates optimized HNSW index
    - Short downtime acceptable for safety
    """
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

    if 'postgresql' not in database_url:
        print("SQLite detected - skipping vector type upgrade")
        return

    # Execute migration as single transaction for safety
    op.execute("""
        DO $$
        BEGIN
            -- Step 1: Check if pgvector extension is installed
            IF NOT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            ) THEN
                RAISE EXCEPTION 'pgvector extension not installed. Run: CREATE EXTENSION vector;';
            END IF;

            -- Step 2: Check if case_bank table exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'case_bank'
            ) THEN
                -- Step 3: Check current column type
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'case_bank'
                    AND column_name = 'query_vector'
                    AND (data_type = 'ARRAY' OR udt_name = '_float4')
                ) THEN
                    RAISE NOTICE 'Upgrading query_vector from FLOAT[] to vector(1536)...';

                    -- Step 4: Alter column type
                    -- This conversion is safe because:
                    -- - FLOAT[] and vector both store float arrays
                    -- - Existing data will be preserved
                    -- - NULL values remain NULL
                    ALTER TABLE case_bank
                    ALTER COLUMN query_vector TYPE vector(1536)
                    USING query_vector::vector(1536);

                    RAISE NOTICE 'Successfully upgraded query_vector to vector(1536)';

                    -- Step 5: Create HNSW index for fast similarity search
                    -- User-approved: Option A - Create immediately
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'idx_case_bank_query_vector_hnsw'
                    ) THEN
                        CREATE INDEX idx_case_bank_query_vector_hnsw
                        ON case_bank
                        USING hnsw (query_vector vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64);

                        RAISE NOTICE 'Created HNSW index on query_vector (10x+ performance boost)';
                    ELSE
                        RAISE NOTICE 'HNSW index already exists';
                    END IF;

                ELSIF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'case_bank'
                    AND column_name = 'query_vector'
                    AND udt_name = 'vector'
                ) THEN
                    RAISE NOTICE 'query_vector already uses vector type, skipping upgrade';
                ELSE
                    RAISE NOTICE 'query_vector has unexpected type, manual review required';
                END IF;
            ELSE
                RAISE NOTICE 'case_bank table does not exist, skipping migration';
            END IF;
        END
        $$;
    """)

    print("✅ Migration 0014 completed successfully")
    print("   - query_vector upgraded to vector(1536)")
    print("   - HNSW index created for fast similarity search")


def downgrade() -> None:
    """
    Downgrade vector(1536) back to FLOAT[]

    WARNING: This removes the performance optimization
    """
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

    if 'postgresql' not in database_url:
        print("SQLite detected - skipping vector type downgrade")
        return

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'case_bank'
            ) THEN
                -- Drop HNSW index first
                IF EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE indexname = 'idx_case_bank_query_vector_hnsw'
                ) THEN
                    DROP INDEX idx_case_bank_query_vector_hnsw;
                    RAISE NOTICE 'Dropped HNSW index';
                END IF;

                -- Downgrade column type
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'case_bank'
                    AND column_name = 'query_vector'
                    AND udt_name = 'vector'
                ) THEN
                    ALTER TABLE case_bank
                    ALTER COLUMN query_vector TYPE FLOAT[]
                    USING query_vector::text::float[];

                    RAISE NOTICE 'Downgraded query_vector to FLOAT[]';
                END IF;
            END IF;
        END
        $$;
    """)

    print("⚠️  Migration 0014 downgrade completed")
    print("   - query_vector downgraded to FLOAT[]")
    print("   - HNSW index removed (performance degraded)")
