-- Migration: 0004_reflection_and_consolidation
-- Description: Add ExecutionLog and CaseBankArchive tables for Reflection and Consolidation features
-- @CODE:REFLECTION-001 | SPEC: SPEC-REFLECTION-001.md
-- @CODE:CONSOLIDATION-001 | SPEC: SPEC-CONSOLIDATION-001.md
-- Created: 2025-10-23
-- Author: @assistant

-- ==========================
-- REFLECTION-001: ExecutionLog Table
-- ==========================

CREATE TABLE IF NOT EXISTS execution_log (
    log_id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) NOT NULL,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    execution_time_ms INTEGER,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ExecutionLog
CREATE INDEX IF NOT EXISTS idx_execution_log_case_id ON execution_log(case_id);
CREATE INDEX IF NOT EXISTS idx_execution_log_created_at ON execution_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_log_success ON execution_log(success);

-- Add composite index for common queries
CREATE INDEX IF NOT EXISTS idx_execution_log_case_success ON execution_log(case_id, success, created_at DESC);

-- ==========================
-- CONSOLIDATION-001: CaseBankArchive Table
-- ==========================

CREATE TABLE IF NOT EXISTS case_bank_archive (
    archive_id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    response_text TEXT NOT NULL,
    category_path VARCHAR(255),
    query_vector VECTOR(1536),
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_reason VARCHAR(255),
    original_created_at TIMESTAMP WITH TIME ZONE,
    original_updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for CaseBankArchive
CREATE INDEX IF NOT EXISTS idx_archive_case_id ON case_bank_archive(case_id);
CREATE INDEX IF NOT EXISTS idx_archive_archived_at ON case_bank_archive(archived_at DESC);
CREATE INDEX IF NOT EXISTS idx_archive_archived_reason ON case_bank_archive(archived_reason);

-- Vector similarity index for duplicate detection (if needed for analysis)
CREATE INDEX IF NOT EXISTS idx_archive_query_vector ON case_bank_archive
USING ivfflat (query_vector vector_cosine_ops) WITH (lists = 100);

-- ==========================
-- Helper Functions
-- ==========================

-- Function to calculate case success rate
CREATE OR REPLACE FUNCTION calculate_case_success_rate(p_case_id VARCHAR)
RETURNS REAL AS $$
DECLARE
    v_total INTEGER;
    v_success INTEGER;
    v_success_rate REAL;
BEGIN
    SELECT COUNT(*), SUM(CASE WHEN success THEN 1 ELSE 0 END)
    INTO v_total, v_success
    FROM execution_log
    WHERE case_id = p_case_id;

    IF v_total = 0 THEN
        RETURN 0.0;
    END IF;

    v_success_rate := (v_success::REAL / v_total::REAL) * 100.0;
    RETURN v_success_rate;
END;
$$ LANGUAGE plpgsql;

-- Function to get recent error patterns
CREATE OR REPLACE FUNCTION get_error_patterns(p_case_id VARCHAR, p_limit INTEGER DEFAULT 100)
RETURNS TABLE(error_type VARCHAR, error_count BIGINT, last_occurred TIMESTAMP WITH TIME ZONE) AS $$
BEGIN
    RETURN QUERY
    SELECT
        el.error_type,
        COUNT(*) as error_count,
        MAX(el.created_at) as last_occurred
    FROM execution_log el
    WHERE el.case_id = p_case_id
      AND el.success = FALSE
      AND el.error_type IS NOT NULL
      AND el.created_at > NOW() - INTERVAL '30 days'
    GROUP BY el.error_type
    ORDER BY error_count DESC, last_occurred DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to archive a case (copy to archive table)
CREATE OR REPLACE FUNCTION archive_case(
    p_case_id VARCHAR,
    p_archived_reason VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_case_exists BOOLEAN;
BEGIN
    -- Check if case exists in case_bank (assuming this table exists from previous migrations)
    SELECT EXISTS(
        SELECT 1 FROM case_bank WHERE case_id = p_case_id
    ) INTO v_case_exists;

    IF NOT v_case_exists THEN
        RAISE NOTICE 'Case % not found or already archived', p_case_id;
        RETURN FALSE;
    END IF;

    -- Insert into archive table
    INSERT INTO case_bank_archive (
        case_id, query, response_text, category_path, query_vector,
        usage_count, success_rate, archived_reason,
        original_created_at, original_updated_at
    )
    SELECT
        case_id, query, response_text, category_path, query_vector,
        usage_count, success_rate, p_archived_reason,
        created_at, last_used_at
    FROM case_bank
    WHERE case_id = p_case_id;

    -- Delete from original table (since there's no status column)
    DELETE FROM case_bank
    WHERE case_id = p_case_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ==========================
-- Views for Analytics
-- ==========================

-- View: Recent case performance
CREATE OR REPLACE VIEW v_case_performance AS
SELECT
    cb.case_id,
    cb.query,
    cb.category_path,
    cb.usage_count,
    cb.success_rate as stored_success_rate,
    calculate_case_success_rate(cb.case_id) as calculated_success_rate,
    COUNT(el.log_id) as total_executions_30d,
    SUM(CASE WHEN el.success THEN 1 ELSE 0 END) as successful_executions_30d,
    AVG(el.execution_time_ms) as avg_execution_time_ms,
    MAX(el.created_at) as last_executed_at
FROM case_bank cb
LEFT JOIN execution_log el ON cb.case_id = el.case_id
    AND el.created_at > NOW() - INTERVAL '30 days'
GROUP BY cb.case_id, cb.query, cb.category_path, cb.usage_count, cb.success_rate;

-- View: Low performance cases (for Consolidation)
CREATE OR REPLACE VIEW v_low_performance_cases AS
SELECT
    cp.*,
    CASE
        WHEN cp.calculated_success_rate < 30 AND cp.total_executions_30d > 10 THEN 'remove'
        WHEN cp.total_executions_30d = 0 AND cp.usage_count > 0 THEN 'inactive'
        ELSE 'monitor'
    END as consolidation_action
FROM v_case_performance cp
WHERE cp.calculated_success_rate < 50 OR cp.total_executions_30d = 0
ORDER BY cp.calculated_success_rate ASC, cp.total_executions_30d DESC;

-- ==========================
-- Comments
-- ==========================

COMMENT ON TABLE execution_log IS 'Tracks case execution results for Reflection Engine (SPEC-REFLECTION-001)';
COMMENT ON TABLE case_bank_archive IS 'Archives removed cases for Consolidation Policy (SPEC-CONSOLIDATION-001)';
COMMENT ON FUNCTION calculate_case_success_rate(VARCHAR) IS 'Calculates success rate from execution logs';
COMMENT ON FUNCTION get_error_patterns(VARCHAR, INTEGER) IS 'Returns error patterns for a case';
COMMENT ON FUNCTION archive_case(VARCHAR, VARCHAR) IS 'Archives a case with reason';
COMMENT ON VIEW v_case_performance IS 'Real-time case performance metrics';
COMMENT ON VIEW v_low_performance_cases IS 'Cases eligible for consolidation';

-- ==========================
-- Grants (adjust as needed)
-- ==========================

-- Grant permissions to application role (if exists)
-- GRANT SELECT, INSERT ON execution_log TO dt_rag_app;
-- GRANT SELECT, INSERT ON case_bank_archive TO dt_rag_app;
-- GRANT EXECUTE ON FUNCTION calculate_case_success_rate(VARCHAR) TO dt_rag_app;
-- GRANT EXECUTE ON FUNCTION get_error_patterns(VARCHAR, INTEGER) TO dt_rag_app;
-- GRANT EXECUTE ON FUNCTION archive_case(VARCHAR, VARCHAR) TO dt_rag_app;

-- ==========================
-- Rollback Script (for reference)
-- ==========================

/*
-- To rollback this migration:

DROP VIEW IF EXISTS v_low_performance_cases CASCADE;
DROP VIEW IF EXISTS v_case_performance CASCADE;
DROP FUNCTION IF EXISTS archive_case(VARCHAR, VARCHAR) CASCADE;
DROP FUNCTION IF EXISTS get_error_patterns(VARCHAR, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS calculate_case_success_rate(VARCHAR) CASCADE;
DROP TABLE IF EXISTS case_bank_archive CASCADE;
DROP TABLE IF EXISTS execution_log CASCADE;
*/
