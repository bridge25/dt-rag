-- @MIGRATION:CONSOLIDATION-001:0.4
-- @SPEC:CONSOLIDATION-001
-- Migration: Add CaseBankArchive table for backup
-- Created: 2025-10-09
-- Author: code-builder TDD implementation
-- Description: Creates case_bank_archive table for storing archived cases

BEGIN;

-- 1. Create CaseBankArchive table (optional backup)
CREATE TABLE IF NOT EXISTS case_bank_archive (
    archive_id SERIAL PRIMARY KEY,
    case_id UUID NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB NOT NULL,
    category_path TEXT[],
    quality FLOAT,
    success_rate REAL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    archived_reason VARCHAR(255)
);

-- 2. Create indices for query performance
CREATE INDEX IF NOT EXISTS idx_archive_case_id
    ON case_bank_archive(case_id);

CREATE INDEX IF NOT EXISTS idx_archive_archived_at
    ON case_bank_archive(archived_at DESC);

CREATE INDEX IF NOT EXISTS idx_archive_archived_reason
    ON case_bank_archive(archived_reason);

-- 3. Add comments for documentation
COMMENT ON TABLE case_bank_archive IS 'Archive table for removed CaseBank cases (backup/audit)';
COMMENT ON COLUMN case_bank_archive.archive_id IS 'Primary key auto-incrementing ID';
COMMENT ON COLUMN case_bank_archive.case_id IS 'Original case_id from case_bank (UUID)';
COMMENT ON COLUMN case_bank_archive.query IS 'Original query text';
COMMENT ON COLUMN case_bank_archive.answer IS 'Original answer text';
COMMENT ON COLUMN case_bank_archive.sources IS 'Original sources (JSONB)';
COMMENT ON COLUMN case_bank_archive.category_path IS 'Original taxonomy category path';
COMMENT ON COLUMN case_bank_archive.quality IS 'Quality score at time of archiving';
COMMENT ON COLUMN case_bank_archive.success_rate IS 'Success rate at time of archiving';
COMMENT ON COLUMN case_bank_archive.archived_at IS 'Timestamp when case was archived';
COMMENT ON COLUMN case_bank_archive.archived_reason IS 'Reason for archiving (low_performance, duplicate, inactive)';

-- 4. Verification
DO $$
DECLARE
    table_exists BOOLEAN;
    idx_case_id_exists BOOLEAN;
    idx_archived_at_exists BOOLEAN;
    idx_reason_exists BOOLEAN;
BEGIN
    -- Check table existence
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'case_bank_archive'
    ) INTO table_exists;

    -- Check indices
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'case_bank_archive' AND indexname = 'idx_archive_case_id'
    ) INTO idx_case_id_exists;

    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'case_bank_archive' AND indexname = 'idx_archive_archived_at'
    ) INTO idx_archived_at_exists;

    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'case_bank_archive' AND indexname = 'idx_archive_archived_reason'
    ) INTO idx_reason_exists;

    -- Raise notice with results
    RAISE NOTICE 'Migration Verification:';
    RAISE NOTICE '  case_bank_archive table: %', CASE WHEN table_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  idx_archive_case_id: %', CASE WHEN idx_case_id_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  idx_archive_archived_at: %', CASE WHEN idx_archived_at_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  idx_archive_archived_reason: %', CASE WHEN idx_reason_exists THEN 'EXISTS' ELSE 'MISSING' END;

    -- Fail if any required object is missing
    IF NOT (table_exists AND idx_case_id_exists AND idx_archived_at_exists AND idx_reason_exists) THEN
        RAISE EXCEPTION 'Migration verification failed: Required objects missing';
    END IF;

    RAISE NOTICE 'Migration CONSOLIDATION-001 completed successfully!';
END $$;

COMMIT;
