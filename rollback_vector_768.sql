-- Emergency Rollback Script: Vector Dimension 1536 → 768
-- Created: 2025-10-01
-- Database: dt_rag_test
--
-- USAGE:
--   docker exec dt_rag_postgres_test psql -U postgres -d dt_rag_test -f rollback_vector_768.sql
--
-- WARNING: This will TRUNCATE the embeddings table!

BEGIN;

-- Step 1: Drop HNSW index
DROP INDEX IF EXISTS idx_embeddings_vec_hnsw;

-- Step 2: Rollback vector dimension
ALTER TABLE embeddings ALTER COLUMN vec TYPE vector(768);

-- Step 3: Truncate embeddings (1536-dim data is incompatible with 768-dim schema)
TRUNCATE TABLE embeddings CASCADE;

-- Step 4: Recreate HNSW index for 768-dim
CREATE INDEX idx_embeddings_vec_hnsw
ON embeddings
USING hnsw (vec vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Verify changes
SELECT 'Rollback successful: vec dimension = ' ||
       substring(pg_typeof(vec)::text from 'vector\((\d+)\)')
FROM embeddings
LIMIT 1;

COMMIT;
