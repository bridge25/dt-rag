-- Initialize DT-RAG database with PRD v1.8.1 compliant schema
-- PRD Reference: Annex C.4 (Alembic Migration Standard)
-- Date: 2025-10-06

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- NEW SYSTEM TABLES (PRD Compliant - UUID based)
-- ============================================================================

-- Documents table (PRD line 290-296)
CREATE TABLE IF NOT EXISTS documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT,
    version_tag TEXT,
    license_tag TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chunks table (PRD line 297-303)
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    span TEXT,  -- int4range serialization (e.g., "[0,500)")
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Embeddings table (PRD line 304-308)
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    vec vector(1536),  -- PRD: 1536-dimensional embeddings
    model_name TEXT DEFAULT 'text-embedding-3-large',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Taxonomy nodes table (PRD line 309-315)
CREATE TABLE IF NOT EXISTS taxonomy_nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label TEXT NOT NULL,
    canonical_path TEXT[] NOT NULL,
    version TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Taxonomy edges table (PRD line 316-320)
CREATE TABLE IF NOT EXISTS taxonomy_edges (
    parent UUID NOT NULL REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    child UUID NOT NULL REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (parent, child, version)
);

-- Document taxonomy mapping (PRD line 321-328)
CREATE TABLE IF NOT EXISTS doc_taxonomy (
    doc_id UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    path TEXT[] NOT NULL,
    confidence FLOAT NOT NULL,
    hitl_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (doc_id, node_id, version)
);

-- Taxonomy migrations table (PRD line 329-336)
CREATE TABLE IF NOT EXISTS taxonomy_migrations (
    migration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_version TEXT NOT NULL,
    to_version TEXT NOT NULL,
    from_path TEXT[],
    to_path TEXT[],
    rationale TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Case bank for CBR (PRD line 173)
CREATE TABLE IF NOT EXISTS case_bank (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB NOT NULL,
    category_path TEXT[],
    quality FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search logs for RAGAS evaluation
CREATE TABLE IF NOT EXISTS search_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    response TEXT,
    retrieved_docs JSONB,
    context_precision FLOAT,
    context_recall FLOAT,
    faithfulness FLOAT,
    answer_relevancy FLOAT,
    search_type VARCHAR(50) DEFAULT 'hybrid',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ingestion jobs table (for document upload tracking)
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL DEFAULT 'pending',
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    failed_files INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES (PRD Section 7.2 line 175-178)
-- ============================================================================

-- Vector similarity search index (IVFFlat)
CREATE INDEX IF NOT EXISTS idx_embeddings_vec_ivfflat ON embeddings
USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);

-- BM25 full-text search on chunks
CREATE INDEX IF NOT EXISTS idx_chunks_text_fts ON chunks
USING gin(to_tsvector('english', text));

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id ON doc_taxonomy(doc_id);
CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_path ON doc_taxonomy USING gin(path);
CREATE INDEX IF NOT EXISTS idx_taxonomy_nodes_version ON taxonomy_nodes(version);
CREATE INDEX IF NOT EXISTS idx_taxonomy_nodes_canonical_path ON taxonomy_nodes USING gin(canonical_path);
CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON search_logs(created_at);

-- ============================================================================
-- LEGACY SYSTEM ISOLATION (Deprecated - DO NOT USE)
-- ============================================================================

-- Legacy tables are kept for data migration purposes only
-- These tables are NOT used by the application code
-- Migration from Legacy to New system should be performed separately

CREATE SCHEMA IF NOT EXISTS legacy;

CREATE TABLE IF NOT EXISTS legacy.documents_deprecated (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS legacy.document_taxonomy_deprecated (
    document_id INTEGER,
    taxonomy_id INTEGER,
    confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SAMPLE DATA (PRD compliant taxonomy)
-- ============================================================================

-- Insert sample taxonomy nodes (version 1.0.0)
INSERT INTO taxonomy_nodes (label, canonical_path, version, confidence) VALUES
('Technology', ARRAY['Technology'], '1.0.0', 1.0),
('Science', ARRAY['Science'], '1.0.0', 1.0),
('Business', ARRAY['Business'], '1.0.0', 1.0),
('AI/ML', ARRAY['Technology', 'AI/ML'], '1.0.0', 1.0),
('Software', ARRAY['Technology', 'Software'], '1.0.0', 1.0),
('Data Science', ARRAY['Technology', 'Data Science'], '1.0.0', 1.0)
ON CONFLICT DO NOTHING;

-- Insert sample taxonomy edges (version 1.0.0)
WITH tech_node AS (SELECT node_id FROM taxonomy_nodes WHERE label = 'Technology' AND version = '1.0.0'),
     ai_node AS (SELECT node_id FROM taxonomy_nodes WHERE label = 'AI/ML' AND version = '1.0.0'),
     sw_node AS (SELECT node_id FROM taxonomy_nodes WHERE label = 'Software' AND version = '1.0.0'),
     ds_node AS (SELECT node_id FROM taxonomy_nodes WHERE label = 'Data Science' AND version = '1.0.0')
INSERT INTO taxonomy_edges (parent, child, version)
SELECT tech_node.node_id, ai_node.node_id, '1.0.0' FROM tech_node, ai_node
UNION ALL
SELECT tech_node.node_id, sw_node.node_id, '1.0.0' FROM tech_node, sw_node
UNION ALL
SELECT tech_node.node_id, ds_node.node_id, '1.0.0' FROM tech_node, ds_node
ON CONFLICT DO NOTHING;

-- ============================================================================
-- FUNCTIONS & PROCEDURES
-- ============================================================================

-- Rollback taxonomy procedure (PRD Annex C.5 line 366-375)
CREATE OR REPLACE FUNCTION rollback_taxonomy(to_v TEXT)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE r RECORD;
BEGIN
    FOR r IN SELECT * FROM taxonomy_migrations WHERE to_version = to_v LOOP
        UPDATE doc_taxonomy
        SET path = r.from_path, version = r.from_version
        WHERE path = r.to_path AND version = to_v;
    END LOOP;

    DELETE FROM taxonomy_nodes WHERE version = to_v;
    DELETE FROM taxonomy_edges WHERE version = to_v;
END $$;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ingestion_jobs_updated_at
BEFORE UPDATE ON ingestion_jobs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE documents IS 'PRD v1.8.1 compliant: Document metadata with UUID primary key';
COMMENT ON TABLE chunks IS 'PRD v1.8.1 compliant: Document chunks for hybrid search (500 tokens, 128 overlap)';
COMMENT ON TABLE embeddings IS 'PRD v1.8.1 compliant: Vector embeddings (1536 dimensions) with BM25 tokens';
COMMENT ON TABLE taxonomy_nodes IS 'PRD v1.8.1 compliant: DAG nodes with canonical paths and versioning';
COMMENT ON TABLE taxonomy_edges IS 'PRD v1.8.1 compliant: Parent-child relationships with version awareness';
COMMENT ON TABLE doc_taxonomy IS 'PRD v1.8.1 compliant: Document-taxonomy mappings with confidence and HITL flags';
COMMENT ON TABLE taxonomy_migrations IS 'PRD v1.8.1 compliant: Taxonomy version migration history';
COMMENT ON TABLE case_bank IS 'PRD v1.8.1 compliant: Case-based reasoning repository (read-only in 1P)';
COMMENT ON SCHEMA legacy IS 'DEPRECATED: Legacy system tables isolated for migration purposes only';
