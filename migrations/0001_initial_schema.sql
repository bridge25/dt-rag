-- Dynamic Taxonomy RAG v1.8.1 - Initial Schema
-- Migration: 0001_initial_schema.sql
-- Purpose: Core taxonomy, document, and embeddings tables
-- Dependencies: PostgreSQL 15+, pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Drop tables if they exist (for clean re-runs)
DROP TABLE IF EXISTS doc_taxonomy CASCADE;
DROP TABLE IF EXISTS embeddings CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS taxonomy_migrations CASCADE;
DROP TABLE IF EXISTS taxonomy_edges CASCADE;
DROP TABLE IF EXISTS taxonomy_nodes CASCADE;

-- 1. Taxonomy Nodes (DAG versioning)
CREATE TABLE taxonomy_nodes (
    node_id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    canonical_path TEXT[] NOT NULL,
    node_name TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_path_format CHECK (array_length(canonical_path, 1) >= 1),
    CONSTRAINT valid_node_name CHECK (length(node_name) > 0),
    CONSTRAINT valid_version CHECK (version > 0)
);

-- 2. Taxonomy Edges (parent-child relationships)
CREATE TABLE taxonomy_edges (
    edge_id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    parent_node_id INTEGER NOT NULL REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    child_node_id INTEGER NOT NULL REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT no_self_reference CHECK (parent_node_id != child_node_id),
    CONSTRAINT valid_edge_version CHECK (version > 0),
    UNIQUE(version, parent_node_id, child_node_id)
);

-- 3. Taxonomy Migrations (version tracking)
CREATE TABLE taxonomy_migrations (
    migration_id SERIAL PRIMARY KEY,
    from_version INTEGER,
    to_version INTEGER NOT NULL,
    migration_type VARCHAR(50) NOT NULL, -- 'upgrade', 'rollback'
    changes JSONB NOT NULL, -- detailed change log
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT DEFAULT current_user,
    
    -- Constraints
    CONSTRAINT valid_migration_type CHECK (migration_type IN ('upgrade', 'rollback')),
    CONSTRAINT valid_version_transition CHECK (
        (migration_type = 'upgrade' AND to_version > COALESCE(from_version, 0)) OR
        (migration_type = 'rollback' AND to_version < from_version)
    )
);

-- 4. Documents table
CREATE TABLE documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT,
    title TEXT,
    content_type VARCHAR(100) DEFAULT 'text/plain',
    file_size INTEGER,
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_content_type CHECK (content_type IN ('text/plain', 'text/html', 'application/pdf', 'application/json')),
    CONSTRAINT valid_file_size CHECK (file_size IS NULL OR file_size > 0)
);

-- 5. Chunks table (document text segments with span tracking)
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    span INT4RANGE NOT NULL, -- character range in original document
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_text_length CHECK (length(text) > 0),
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT non_empty_span CHECK (NOT isempty(span))
);

-- 6. Embeddings table (vector storage)
CREATE TABLE embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    vec VECTOR(1536) NOT NULL, -- OpenAI ada-002 dimensionality
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    bm25_tokens TEXT[], -- preprocessed tokens for BM25
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_model_name CHECK (length(model_name) > 0)
    -- NOTE: vector(1536) type itself enforces dimension; do not call array_length on vector
);

-- 7. Document-Taxonomy mapping (many-to-many)
CREATE TABLE doc_taxonomy (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    path TEXT[] NOT NULL, -- canonical taxonomy path
    confidence REAL NOT NULL DEFAULT 0.0,
    source VARCHAR(50) NOT NULL DEFAULT 'manual', -- 'manual', 'llm', 'rule'
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by TEXT DEFAULT current_user,
    
    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT valid_source CHECK (source IN ('manual', 'llm', 'rule', 'hybrid')),
    CONSTRAINT valid_path_length CHECK (array_length(path, 1) >= 1)
);

-- Basic indexes for performance
CREATE INDEX idx_taxonomy_nodes_version ON taxonomy_nodes(version);
CREATE INDEX idx_taxonomy_nodes_active ON taxonomy_nodes(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_taxonomy_edges_version ON taxonomy_edges(version);
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_doc_taxonomy_doc_id ON doc_taxonomy(doc_id);

-- Comments for documentation (conditional to avoid errors if tables don't exist)
DO $$
BEGIN
    -- Table comments
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'taxonomy_nodes') THEN
        COMMENT ON TABLE taxonomy_nodes IS 'Versioned taxonomy node definitions with DAG structure';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'taxonomy_edges') THEN
        COMMENT ON TABLE taxonomy_edges IS 'Parent-child relationships between taxonomy nodes';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'taxonomy_migrations') THEN
        COMMENT ON TABLE taxonomy_migrations IS 'Version tracking and migration history';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        COMMENT ON TABLE documents IS 'Source documents with metadata';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chunks') THEN
        COMMENT ON TABLE chunks IS 'Text segments with character span ranges';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'embeddings') THEN
        COMMENT ON TABLE embeddings IS 'Vector embeddings with BM25 tokens';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'doc_taxonomy') THEN
        COMMENT ON TABLE doc_taxonomy IS 'Document classification mappings';
    END IF;
    
    -- Column comments
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'chunks' AND column_name = 'span') THEN
        COMMENT ON COLUMN chunks.span IS 'int4range: character positions in source document';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'embeddings' AND column_name = 'vec') THEN
        COMMENT ON COLUMN embeddings.vec IS 'vector(1536): OpenAI ada-002 embeddings';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'taxonomy_nodes' AND column_name = 'canonical_path') THEN
        COMMENT ON COLUMN taxonomy_nodes.canonical_path IS 'TEXT[]: hierarchical path like ["AI", "Machine Learning"]';
    END IF;
END $$;
