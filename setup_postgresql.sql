-- PostgreSQL 설정 스크립트
-- pgvector 확장과 full-text search 설정

-- pgvector 확장 활성화 (PostgreSQL 14+ 필요)
CREATE EXTENSION IF NOT EXISTS vector;

-- 기본 스키마 및 테이블 생성
CREATE TABLE IF NOT EXISTS documents (
    doc_id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    source_url TEXT,
    content_type VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id SERIAL PRIMARY KEY,
    doc_id INTEGER REFERENCES documents(doc_id),
    text TEXT NOT NULL,
    chunk_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id INTEGER PRIMARY KEY REFERENCES chunks(chunk_id),
    embedding vector(768),  -- OpenAI embedding dimensions
    embedding_json JSONB,   -- Fallback for complex queries
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doc_taxonomy (
    doc_id INTEGER PRIMARY KEY REFERENCES documents(doc_id),
    path TEXT[],  -- PostgreSQL array type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Taxonomy hierarchy tables
CREATE TABLE IF NOT EXISTS taxonomy_nodes (
    node_id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    canonical_path TEXT[] NOT NULL,
    node_name VARCHAR(255) NOT NULL,
    description TEXT,
    doc_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS taxonomy_edges (
    edge_id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    parent_node_id INTEGER NOT NULL,
    child_node_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS taxonomy_migrations (
    migration_id SERIAL PRIMARY KEY,
    from_version INTEGER,
    to_version INTEGER NOT NULL,
    migration_type VARCHAR(50) NOT NULL,
    changes JSONB NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT
);

-- Full-text search 인덱스 생성
CREATE INDEX IF NOT EXISTS chunks_text_fts_idx
ON chunks USING GIN (to_tsvector('english', text));

-- 벡터 유사도 검색을 위한 인덱스 (HNSW 인덱스 - 고성능)
CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx
ON embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat 인덱스도 생성 (메모리 효율적)
CREATE INDEX IF NOT EXISTS embeddings_ivfflat_idx
ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 성능을 위한 추가 인덱스
CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS documents_source_url_idx ON documents(source_url);
CREATE INDEX IF NOT EXISTS doc_taxonomy_path_idx ON doc_taxonomy USING GIN(path);

-- Taxonomy indexes for performance
CREATE INDEX IF NOT EXISTS taxonomy_nodes_version_idx ON taxonomy_nodes(version);
CREATE INDEX IF NOT EXISTS taxonomy_nodes_path_idx ON taxonomy_nodes USING GIN(canonical_path);
CREATE INDEX IF NOT EXISTS taxonomy_nodes_name_idx ON taxonomy_nodes(node_name);
CREATE INDEX IF NOT EXISTS taxonomy_edges_parent_idx ON taxonomy_edges(parent_node_id);
CREATE INDEX IF NOT EXISTS taxonomy_edges_child_idx ON taxonomy_edges(child_node_id);
CREATE INDEX IF NOT EXISTS taxonomy_edges_version_idx ON taxonomy_edges(version);

-- 샘플 데이터 삽입 (테스트용)
INSERT INTO documents (title, content, source_url, content_type)
VALUES
    ('Machine Learning Guide', 'Machine learning algorithms are computational methods that enable automatic learning from data. These algorithms build mathematical models based on training data to make predictions or decisions.', 'https://example.com/ml-guide', 'article'),
    ('Neural Network Basics', 'Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes that process and transmit information.', 'https://example.com/nn-basics', 'article'),
    ('Deep Learning Introduction', 'Deep learning is a subset of machine learning that uses neural networks with multiple layers. It has revolutionized fields like computer vision and natural language processing.', 'https://example.com/dl-intro', 'article')
ON CONFLICT (doc_id) DO NOTHING;

INSERT INTO chunks (doc_id, text, chunk_order)
VALUES
    (1, 'Machine learning algorithms are computational methods that enable automatic learning from data.', 1),
    (1, 'These algorithms build mathematical models based on training data to make predictions or decisions.', 2),
    (2, 'Neural networks are computational models inspired by biological neural networks.', 1),
    (2, 'They consist of interconnected nodes that process and transmit information.', 2),
    (3, 'Deep learning is a subset of machine learning that uses neural networks with multiple layers.', 1),
    (3, 'It has revolutionized fields like computer vision and natural language processing.', 2)
ON CONFLICT (chunk_id) DO NOTHING;

INSERT INTO doc_taxonomy (doc_id, path)
VALUES
    (1, '{"AI", "Machine Learning"}'),
    (2, '{"AI", "Neural Networks"}'),
    (3, '{"AI", "Deep Learning"}')
ON CONFLICT (doc_id) DO NOTHING;

-- Taxonomy nodes sample data
INSERT INTO taxonomy_nodes (node_name, canonical_path, version, description, is_active)
VALUES
    ('AI', '{"AI"}', 1, 'Artificial Intelligence root category', TRUE),
    ('Machine Learning', '{"AI", "Machine Learning"}', 1, 'Machine learning algorithms and techniques', TRUE),
    ('Neural Networks', '{"AI", "Neural Networks"}', 1, 'Neural network architectures', TRUE),
    ('Deep Learning', '{"AI", "Deep Learning"}', 1, 'Deep learning methods', TRUE),
    ('RAG', '{"AI", "RAG"}', 1, 'Retrieval-Augmented Generation', TRUE),
    ('Taxonomy', '{"AI", "Taxonomy"}', 1, 'Taxonomy management', TRUE),
    ('General', '{"AI", "General"}', 1, 'General AI topics', TRUE)
ON CONFLICT DO NOTHING;

-- Taxonomy edges sample data (AI -> children)
INSERT INTO taxonomy_edges (parent_node_id, child_node_id, version)
SELECT p.node_id, c.node_id, 1
FROM taxonomy_nodes p
CROSS JOIN taxonomy_nodes c
WHERE p.node_name = 'AI'
  AND c.node_name IN ('Machine Learning', 'Neural Networks', 'Deep Learning', 'RAG', 'Taxonomy', 'General')
  AND p.version = 1
  AND c.version = 1
ON CONFLICT DO NOTHING;

-- 샘플 임베딩 데이터 (실제로는 OpenAI API에서 생성)
INSERT INTO embeddings (chunk_id, embedding, embedding_json)
VALUES
    (1, '[0.1,0.2,0.3]'::vector, '{"embedding": [0.1,0.2,0.3], "model": "text-embedding-ada-002"}'),
    (2, '[0.2,0.3,0.4]'::vector, '{"embedding": [0.2,0.3,0.4], "model": "text-embedding-ada-002"}'),
    (3, '[0.3,0.4,0.5]'::vector, '{"embedding": [0.3,0.4,0.5], "model": "text-embedding-ada-002"}'),
    (4, '[0.4,0.5,0.6]'::vector, '{"embedding": [0.4,0.5,0.6], "model": "text-embedding-ada-002"}'),
    (5, '[0.5,0.6,0.7]'::vector, '{"embedding": [0.5,0.6,0.7], "model": "text-embedding-ada-002"}'),
    (6, '[0.6,0.7,0.8]'::vector, '{"embedding": [0.6,0.7,0.8], "model": "text-embedding-ada-002"}')
ON CONFLICT (chunk_id) DO NOTHING;

-- 권한 설정
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- PostgreSQL 설정 최적화
-- shared_preload_libraries에 'vector' 추가 필요 (postgresql.conf에서)
-- 다음 명령으로 확인: SHOW shared_preload_libraries;

-- 벡터 검색 성능 테스트 쿼리
-- SELECT chunk_id, 1 - (embedding <=> '[0.1,0.2,0.3]'::vector) as similarity
-- FROM embeddings
-- ORDER BY embedding <=> '[0.1,0.2,0.3]'::vector
-- LIMIT 5;

-- Full-text search 테스트 쿼리
-- SELECT chunk_id, text, ts_rank_cd(to_tsvector('english', text), plainto_tsquery('english', 'machine learning')) as rank
-- FROM chunks
-- WHERE to_tsvector('english', text) @@ plainto_tsquery('english', 'machine learning')
-- ORDER BY rank DESC;