-- @MIGRATION:CASEBANK-002:0.4
-- @SPEC:CASEBANK-002
-- Migration: CASEBANK-002 Schema Extension (4 NEW fields + 3 indices)
-- Created: 2025-10-09
-- Author: Claude Code (TDD Implementation)
-- Description: Extends case_bank table with version management, lifecycle status, and enhanced timestamps

BEGIN;

-- Add version management fields (2 fields)
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);

-- Add lifecycle status field (1 field)
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active' NOT NULL;

-- Add enhanced timestamp field (1 field, created_at already exists)
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;

-- Create performance indices (3 indices)
CREATE INDEX IF NOT EXISTS idx_casebank_status ON case_bank(status);
CREATE INDEX IF NOT EXISTS idx_casebank_version ON case_bank(version DESC);
CREATE INDEX IF NOT EXISTS idx_casebank_updated_at ON case_bank(updated_at DESC);

-- Create trigger function for updated_at auto-update and version increment
CREATE OR REPLACE FUNCTION update_casebank_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;

    -- Auto-increment version on update (only if row is being modified, not inserted)
    IF TG_OP = 'UPDATE' THEN
        NEW.version = OLD.version + 1;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_casebank_update_timestamp ON case_bank;

-- Create trigger for updated_at auto-update and version increment
CREATE TRIGGER trigger_casebank_update_timestamp
    BEFORE UPDATE ON case_bank
    FOR EACH ROW
    EXECUTE FUNCTION update_casebank_timestamp();

-- Verify migration
DO $$
DECLARE
    version_col_exists BOOLEAN;
    updated_by_col_exists BOOLEAN;
    status_col_exists BOOLEAN;
    updated_at_col_exists BOOLEAN;
    idx_status_exists BOOLEAN;
    idx_version_exists BOOLEAN;
    idx_updated_at_exists BOOLEAN;
BEGIN
    -- Check columns
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'case_bank' AND column_name = 'version'
    ) INTO version_col_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'case_bank' AND column_name = 'updated_by'
    ) INTO updated_by_col_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'case_bank' AND column_name = 'status'
    ) INTO status_col_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'case_bank' AND column_name = 'updated_at'
    ) INTO updated_at_col_exists;

    -- Check indices
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'case_bank' AND indexname = 'idx_casebank_status'
    ) INTO idx_status_exists;

    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'case_bank' AND indexname = 'idx_casebank_version'
    ) INTO idx_version_exists;

    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'case_bank' AND indexname = 'idx_casebank_updated_at'
    ) INTO idx_updated_at_exists;

    -- Raise notice with results
    RAISE NOTICE 'Migration Verification:';
    RAISE NOTICE '  version column: %', CASE WHEN version_col_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  updated_by column: %', CASE WHEN updated_by_col_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  status column: %', CASE WHEN status_col_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  updated_at column: %', CASE WHEN updated_at_col_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  idx_casebank_status: %', CASE WHEN idx_status_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  idx_casebank_version: %', CASE WHEN idx_version_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  idx_casebank_updated_at: %', CASE WHEN idx_updated_at_exists THEN 'EXISTS' ELSE 'MISSING' END;

    -- Fail if any required object is missing
    IF NOT (version_col_exists AND updated_by_col_exists AND status_col_exists AND updated_at_col_exists
            AND idx_status_exists AND idx_version_exists AND idx_updated_at_exists) THEN
        RAISE EXCEPTION 'Migration verification failed: Required objects missing';
    END IF;

    RAISE NOTICE 'Migration CASEBANK-002 completed successfully!';
END $$;

COMMIT;
