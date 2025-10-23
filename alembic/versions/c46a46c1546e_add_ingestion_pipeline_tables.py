"""Add ingestion pipeline tables and functions

@CODE:DATABASE-001:MIGRATION:INGESTION-PIPELINE
@SPEC:DATABASE-001
@TEST:test_schema.py::test_ingestion_pipeline_tables

Revision ID: c46a46c1546e
Revises: 4b62d8cc3712
Create Date: 2025-10-22 21:30:41.100513

This migration adds document ingestion pipeline infrastructure:
- ingestion_jobs table (tracks ingestion job status)
- ingestion_stats view (aggregated job statistics)
- documents table extensions (doc_hash, updated_at)
- cleanup_old_ingestion_jobs() function (automatic cleanup)
- get_ingestion_metrics() function (performance metrics)

Based on feat/a-ingest-pipeline branch 0004_ingestion_pipeline_tables.sql
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c46a46c1546e'
down_revision = '4b62d8cc3712'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ingestion pipeline tables and functions"""

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
        print("SQLite detected - skipping ingestion pipeline (PostgreSQL-only)")
        return

    print("Adding ingestion pipeline tables and functions...")

    # 1. Create ingestion_jobs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            job_id VARCHAR(36) PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            doc_hash VARCHAR(64) NOT NULL,
            doc_type VARCHAR(20) NOT NULL CHECK (doc_type IN ('pdf', 'markdown', 'html')),
            content_type VARCHAR(100),
            size_bytes BIGINT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'dlq')),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            chunks_created INTEGER DEFAULT 0,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            content_blob BYTEA
        );
    """)
    print("Created ingestion_jobs table")

    # 2. Create indexes for ingestion_jobs
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs (status);
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_doc_hash ON ingestion_jobs (doc_hash);
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_created_at ON ingestion_jobs (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_created ON ingestion_jobs (status, created_at DESC);
    """)
    print("Created ingestion_jobs indexes")

    # 3. Create ingestion_stats view
    op.execute("""
        CREATE OR REPLACE VIEW ingestion_stats AS
        SELECT
            status,
            COUNT(*) as job_count,
            AVG(chunks_created) as avg_chunks_per_job,
            MAX(created_at) as last_job_time,
            SUM(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) as jobs_last_24h
        FROM ingestion_jobs
        GROUP BY status;
    """)
    print("Created ingestion_stats view")

    # 4. Extend documents table
    op.execute("""
        DO $$
        BEGIN
            -- doc_hash column
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name = 'documents' AND column_name = 'doc_hash') THEN
                ALTER TABLE documents ADD COLUMN doc_hash VARCHAR(64);
                RAISE NOTICE 'Added doc_hash column to documents';
            END IF;

            -- doc_hash unique constraint
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                           WHERE table_name = 'documents' AND constraint_name = 'documents_doc_hash_unique') THEN
                ALTER TABLE documents ADD CONSTRAINT documents_doc_hash_unique UNIQUE (doc_hash);
                RAISE NOTICE 'Added unique constraint to doc_hash';
            END IF;

            -- updated_at column
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name = 'documents' AND column_name = 'updated_at') THEN
                ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                RAISE NOTICE 'Added updated_at column to documents';
            END IF;
        END $$;
    """)
    print("Extended documents table with doc_hash and updated_at")

    # 5. Create cleanup_old_ingestion_jobs function
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_ingestion_jobs()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM ingestion_jobs
            WHERE status = 'completed'
            AND created_at < NOW() - INTERVAL '30 days';

            GET DIAGNOSTICS deleted_count = ROW_COUNT;

            -- Log to audit_log if table exists
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log') THEN
                INSERT INTO audit_log (action, actor, detail)
                VALUES ('ingestion_cleanup', 'system',
                       jsonb_build_object('deleted_jobs', deleted_count, 'cleanup_date', NOW()));
            END IF;

            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
    """)
    print("Created cleanup_old_ingestion_jobs function")

    # 6. Create get_ingestion_metrics function
    op.execute("""
        CREATE OR REPLACE FUNCTION get_ingestion_metrics(
            time_window INTERVAL DEFAULT '24 hours'
        )
        RETURNS JSON AS $$
        DECLARE
            result JSON;
        BEGIN
            SELECT json_build_object(
                'time_window', time_window,
                'total_jobs', COUNT(*),
                'successful_jobs', COUNT(CASE WHEN status = 'completed' THEN 1 END),
                'failed_jobs', COUNT(CASE WHEN status = 'failed' OR status = 'dlq' THEN 1 END),
                'success_rate', ROUND(
                    COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL /
                    NULLIF(COUNT(*), 0) * 100, 2
                ),
                'avg_chunks_per_doc', ROUND(AVG(
                    CASE WHEN status = 'completed' THEN chunks_created END
                ), 2),
                'total_documents_processed', SUM(
                    CASE WHEN status = 'completed' THEN 1 ELSE 0 END
                ),
                'total_chunks_created', SUM(
                    CASE WHEN status = 'completed' THEN chunks_created ELSE 0 END
                )
            ) INTO result
            FROM ingestion_jobs
            WHERE created_at > NOW() - time_window;

            RETURN result;
        END;
        $$ LANGUAGE plpgsql;
    """)
    print("Created get_ingestion_metrics function")

    # 7. Add table and function comments
    op.execute("""
        COMMENT ON TABLE ingestion_jobs IS 'Document ingestion pipeline job tracking';
        COMMENT ON FUNCTION cleanup_old_ingestion_jobs() IS 'Automatic cleanup of completed jobs older than 30 days';
        COMMENT ON FUNCTION get_ingestion_metrics(INTERVAL) IS 'Ingestion pipeline performance metrics';
    """)

    print("Ingestion pipeline migration completed successfully")


def downgrade() -> None:
    """Remove ingestion pipeline tables and functions"""

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
        return

    print("Removing ingestion pipeline tables and functions...")

    # Drop in reverse order
    op.execute("DROP FUNCTION IF EXISTS get_ingestion_metrics(INTERVAL);")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_ingestion_jobs();")
    op.execute("DROP VIEW IF EXISTS ingestion_stats;")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_status_created;")
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_doc_hash;")
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_status;")

    # Drop table
    op.execute("DROP TABLE IF EXISTS ingestion_jobs;")

    # Remove documents extensions
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_doc_hash_unique;")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS updated_at;")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS doc_hash;")

    print("Ingestion pipeline removed successfully")