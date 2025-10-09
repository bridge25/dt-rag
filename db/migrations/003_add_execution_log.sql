-- @SPEC:REFLECTION-001
-- Migration: Add ExecutionLog table and indices for reflection engine
-- Created: 2025-10-09
-- Purpose: Track case execution results for performance analysis

-- Create ExecutionLog table
CREATE TABLE IF NOT EXISTS execution_log (
    log_id SERIAL PRIMARY KEY,
    case_id UUID NOT NULL REFERENCES case_bank(case_id),
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    execution_time_ms INTEGER,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indices for query optimization
CREATE INDEX IF NOT EXISTS idx_execution_log_case_id
    ON execution_log(case_id);

CREATE INDEX IF NOT EXISTS idx_execution_log_created_at
    ON execution_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_execution_log_success
    ON execution_log(success);

-- Add success_rate column to CaseBank (if not exists)
-- This allows ReflectionEngine to cache computed success rates
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'case_bank'
        AND column_name = 'success_rate'
    ) THEN
        ALTER TABLE case_bank ADD COLUMN success_rate FLOAT;
    END IF;
END $$;

-- Comments for documentation
COMMENT ON TABLE execution_log IS 'Logs execution results for each case usage';
COMMENT ON COLUMN execution_log.case_id IS 'Foreign key to case_bank';
COMMENT ON COLUMN execution_log.success IS 'Whether execution succeeded';
COMMENT ON COLUMN execution_log.error_type IS 'Type of error if failed';
COMMENT ON COLUMN execution_log.error_message IS 'Detailed error message';
COMMENT ON COLUMN execution_log.execution_time_ms IS 'Execution time in milliseconds';
COMMENT ON COLUMN execution_log.context IS 'Additional context as JSON';
COMMENT ON COLUMN execution_log.created_at IS 'Timestamp when log was created';
