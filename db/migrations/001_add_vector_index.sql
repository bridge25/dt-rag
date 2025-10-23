-- Migration: Add pgvector index for CaseBank query_vector field
-- SPEC: NEURAL-001
-- Created: 2025-10-09
-- Performance target: Vector search < 100ms

-- Create IVFFlat index for cosine similarity search on query_vector
-- IVFFlat parameters:
--   - lists=100: Number of inverted lists (recommended for 10K-1M vectors)
--   - vector_cosine_ops: Cosine distance operator class

CREATE INDEX IF NOT EXISTS idx_casebank_query_vector_cosine
ON case_bank
USING ivfflat (query_vector vector_cosine_ops)
WITH (lists = 100);

-- Alternative: HNSW index (faster queries, slower build)
-- Uncomment if preferred:
-- CREATE INDEX IF NOT EXISTS idx_casebank_query_vector_hnsw
-- ON case_bank
-- USING hnsw (query_vector vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- Analyze table for query planner optimization
ANALYZE case_bank;

-- Verify index creation
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'case_bank' AND indexname LIKE '%query_vector%';
