-- Migration: 0003.5 - CaseBank Table Creation
-- @CODE:CASEBANK-002:MIGRATION | SPEC: SPEC-CASEBANK-002.md
-- Created: 2025-10-23
-- Description: Create case_bank table for storing RAG case examples
--
-- This migration was created to fix the missing case_bank table that was
-- only defined in SQLAlchemy ORM but never created via SQL migration.
-- The table is required by migration 0004 (reflection_and_consolidation).

-- ==========================
-- CaseBank Table
-- ==========================

CREATE TABLE IF NOT EXISTS case_bank (
    case_id VARCHAR(255) PRIMARY KEY,
    query TEXT NOT NULL,
    response_text TEXT NOT NULL,
    category_path TEXT[] NOT NULL,
    query_vector VECTOR(1536) NOT NULL,
    quality_score REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- ==========================
-- Indexes for Performance
-- ==========================

-- GIN index for array search on category_path
CREATE INDEX IF NOT EXISTS idx_case_bank_category
ON case_bank USING GIN(category_path);

-- B-tree indexes for sorting and filtering
CREATE INDEX IF NOT EXISTS idx_case_bank_quality
ON case_bank(quality_score DESC);

CREATE INDEX IF NOT EXISTS idx_case_bank_usage
ON case_bank(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_case_bank_success_rate
ON case_bank(success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_case_bank_created_at
ON case_bank(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_case_bank_last_used_at
ON case_bank(last_used_at DESC);

-- ==========================
-- pgvector Index for Similarity Search
-- ==========================

-- IVFFlat index for approximate nearest neighbor search
-- Lists parameter (100) should be adjusted based on data size:
-- - Small dataset (<10k rows): 10-50 lists
-- - Medium dataset (10k-100k rows): 100-200 lists
-- - Large dataset (>100k rows): 500-1000 lists
CREATE INDEX IF NOT EXISTS idx_case_bank_vector
ON case_bank USING ivfflat (query_vector vector_cosine_ops)
WITH (lists = 100);

-- ==========================
-- Comments
-- ==========================

COMMENT ON TABLE case_bank IS 'Stores case examples for RAG system (SPEC-CASEBANK-002)';
COMMENT ON COLUMN case_bank.case_id IS 'Unique identifier for the case';
COMMENT ON COLUMN case_bank.query IS 'Original user query';
COMMENT ON COLUMN case_bank.response_text IS 'System response';
COMMENT ON COLUMN case_bank.category_path IS 'Taxonomy path array (e.g., [''AI'', ''ML'', ''NLP''])';
COMMENT ON COLUMN case_bank.query_vector IS '1536-dim embedding vector for similarity search';
COMMENT ON COLUMN case_bank.quality_score IS 'Quality score (0.0-1.0) from evaluator';
COMMENT ON COLUMN case_bank.usage_count IS 'Number of times this case was retrieved';
COMMENT ON COLUMN case_bank.success_rate IS 'Success rate percentage (0.0-100.0)';
COMMENT ON COLUMN case_bank.created_at IS 'Timestamp when case was created';
COMMENT ON COLUMN case_bank.last_used_at IS 'Timestamp when case was last retrieved';

-- ==========================
-- Rollback Script (for reference)
-- ==========================

/*
-- To rollback this migration:

DROP INDEX IF EXISTS idx_case_bank_vector CASCADE;
DROP INDEX IF EXISTS idx_case_bank_last_used_at CASCADE;
DROP INDEX IF EXISTS idx_case_bank_created_at CASCADE;
DROP INDEX IF EXISTS idx_case_bank_success_rate CASCADE;
DROP INDEX IF EXISTS idx_case_bank_usage CASCADE;
DROP INDEX IF EXISTS idx_case_bank_quality CASCADE;
DROP INDEX IF EXISTS idx_case_bank_category CASCADE;
DROP TABLE IF EXISTS case_bank CASCADE;
*/
