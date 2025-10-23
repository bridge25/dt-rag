-- Dynamic Taxonomy RAG v1.8.1 - Span Range and Indexes
-- Migration: 0002_span_range_and_indexes.sql  
-- Purpose: Advanced indexing for span ranges, text search, and performance optimization
-- Dependencies: 0001_initial_schema.sql

-- Ensure extensions are available
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. GiST index for span range operations (overlap, contains, etc.)
CREATE INDEX idx_chunks_span_gist ON chunks USING gist (span);

-- 2. Composite GiST index for document + span queries
CREATE INDEX idx_chunks_doc_span_gist ON chunks USING gist (doc_id, span);

-- 3. GIN indexes for array and text search operations
CREATE INDEX idx_taxonomy_canonical ON taxonomy_nodes USING GIN (canonical_path);
CREATE INDEX idx_doc_taxonomy_path ON doc_taxonomy USING GIN (path);
CREATE INDEX idx_embeddings_bm25 ON embeddings USING GIN (bm25_tokens);

-- 4. B-tree indexes for common filtering and sorting
CREATE INDEX idx_chunks_chunk_index ON chunks (doc_id, chunk_index);
CREATE INDEX idx_doc_taxonomy_confidence ON doc_taxonomy (confidence DESC) WHERE confidence >= 0.7;
CREATE INDEX idx_taxonomy_migrations_versions ON taxonomy_migrations (from_version, to_version);

-- 5. Partial indexes for active data
CREATE INDEX idx_taxonomy_nodes_active_version ON taxonomy_nodes (version, canonical_path) 
WHERE is_active = TRUE;

-- 6. Covering indexes for common queries
CREATE INDEX idx_chunks_metadata_cover ON chunks (doc_id, chunk_index) 
INCLUDE (chunk_id, text);

-- 7. Multi-column indexes for join performance  
CREATE INDEX idx_doc_taxonomy_composite ON doc_taxonomy (doc_id, path, confidence);
CREATE INDEX idx_embeddings_model_created ON embeddings (model_name, created_at);

-- 8. Hash indexes for exact equality lookups
CREATE INDEX idx_documents_checksum_hash ON documents USING HASH (checksum) 
WHERE checksum IS NOT NULL;

-- 9. Expression indexes for computed columns
CREATE INDEX idx_chunks_text_length ON chunks (length(text)) WHERE length(text) > 1000;
CREATE INDEX idx_taxonomy_path_depth ON taxonomy_nodes (array_length(canonical_path, 1));

-- 10. Functional indexes for search optimization
CREATE INDEX idx_embeddings_model_lower ON embeddings (lower(model_name));
CREATE INDEX idx_documents_title_trgm ON documents USING gin (title gin_trgm_ops)
WHERE title IS NOT NULL;

-- Utility functions for span operations
CREATE OR REPLACE FUNCTION chunk_span_length(span_range int4range)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE 
        WHEN isempty(span_range) THEN 0
        ELSE upper(span_range) - lower(span_range)
    END;
$$;

-- Function to check if spans overlap
CREATE OR REPLACE FUNCTION spans_overlap(span1 int4range, span2 int4range)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT span1 && span2;
$$;

-- Function to get taxonomy path depth
CREATE OR REPLACE FUNCTION taxonomy_depth(path TEXT[])
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT array_length(path, 1);
$$;

-- Statistics collection for query planning
ANALYZE taxonomy_nodes;
ANALYZE taxonomy_edges; 
ANALYZE chunks;
ANALYZE embeddings;
ANALYZE doc_taxonomy;
ANALYZE documents;

-- Comments for maintenance
COMMENT ON INDEX idx_chunks_span_gist IS 'GiST index for efficient int4range overlap and containment queries';
COMMENT ON INDEX idx_taxonomy_canonical IS 'GIN index for taxonomy path array searches';
COMMENT ON INDEX idx_embeddings_bm25 IS 'GIN index for BM25 token array searches';
COMMENT ON FUNCTION chunk_span_length IS 'Calculate character length of a span range';
COMMENT ON FUNCTION spans_overlap IS 'Check if two span ranges overlap';
COMMENT ON FUNCTION taxonomy_depth IS 'Get depth/level of taxonomy path';

-- Performance tuning settings (session-level)
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';
SET random_page_cost = 1.1;  -- SSD optimization