-- Dynamic Taxonomy RAG v1.8.1 - Span Range and Indexes
-- Migration: 0002_span_range_and_indexes.sql  
-- Purpose: Advanced indexing for span ranges, text search, and performance optimization
-- Dependencies: 0001_initial_schema.sql

-- Ensure btree_gist is available for composite indexes
CREATE EXTENSION IF NOT EXISTS btree_gist;

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

-- Create trigram extension if available (for fuzzy text search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

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

-- Statistics collection for query planning (conditional)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'taxonomy_nodes') THEN
        ANALYZE taxonomy_nodes;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'taxonomy_edges') THEN
        ANALYZE taxonomy_edges;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chunks') THEN
        ANALYZE chunks;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'embeddings') THEN
        ANALYZE embeddings;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'doc_taxonomy') THEN
        ANALYZE doc_taxonomy;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        ANALYZE documents;
    END IF;
END $$;

-- Comments for maintenance (conditional)
DO $$
BEGIN
    -- Index comments
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_chunks_span_gist') THEN
        COMMENT ON INDEX idx_chunks_span_gist IS 'GiST index for efficient int4range overlap and containment queries';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_taxonomy_canonical') THEN
        COMMENT ON INDEX idx_taxonomy_canonical IS 'GIN index for taxonomy path array searches';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_embeddings_bm25') THEN
        COMMENT ON INDEX idx_embeddings_bm25 IS 'GIN index for BM25 token array searches';
    END IF;
    
    -- Function comments (with proper signatures)
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'chunk_span_length') THEN
        COMMENT ON FUNCTION chunk_span_length(span_range int4range) IS 'Calculate character length of a span range';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'spans_overlap') THEN
        COMMENT ON FUNCTION spans_overlap(span1 int4range, span2 int4range) IS 'Check if two span ranges overlap';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'taxonomy_depth') THEN
        COMMENT ON FUNCTION taxonomy_depth(path TEXT[]) IS 'Get depth/level of taxonomy path';
    END IF;
END $$;

-- Performance tuning settings (session-level)
SET work_mem = '256MB';
SET maintenance_work_mem = '1GB';
SET random_page_cost = 1.1;  -- SSD optimization