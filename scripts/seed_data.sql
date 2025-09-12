-- Dynamic Taxonomy RAG v1.8.1 - Test Data Seeding
-- Purpose: Insert sample data for development and testing
-- Usage: psql -d dt_rag -f seed_data.sql

-- Clear existing data (in reverse dependency order)
DELETE FROM audit_log;
DELETE FROM hitl_queue;
DELETE FROM doc_taxonomy;
DELETE FROM embeddings;
DELETE FROM chunks;
DELETE FROM documents;
DELETE FROM taxonomy_edges;
DELETE FROM taxonomy_nodes;
DELETE FROM taxonomy_migrations;

-- Reset sequences (check if they exist first)
DO $$
BEGIN
    -- Reset taxonomy sequences
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'taxonomy_nodes_node_id_seq') THEN
        ALTER SEQUENCE taxonomy_nodes_node_id_seq RESTART WITH 1;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'taxonomy_edges_edge_id_seq') THEN
        ALTER SEQUENCE taxonomy_edges_edge_id_seq RESTART WITH 1;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'taxonomy_migrations_migration_id_seq') THEN
        ALTER SEQUENCE taxonomy_migrations_migration_id_seq RESTART WITH 1;
    END IF;
    
    -- Note: audit_log and hitl_queue use UUID primary keys, no sequences to reset
END $$;

-- Sample Taxonomy Nodes (Version 1)
INSERT INTO taxonomy_nodes (node_id, version, canonical_path, node_name, description) VALUES
(1, 1, ARRAY['AI'], 'Artificial Intelligence', 'Parent category for all AI-related content'),
(2, 1, ARRAY['AI', 'Machine Learning'], 'Machine Learning', 'Algorithms that learn from data'),
(3, 1, ARRAY['AI', 'Machine Learning', 'Deep Learning'], 'Deep Learning', 'Neural networks with multiple layers'),
(4, 1, ARRAY['AI', 'Machine Learning', 'Supervised Learning'], 'Supervised Learning', 'Learning with labeled training data'),
(5, 1, ARRAY['AI', 'Machine Learning', 'Unsupervised Learning'], 'Unsupervised Learning', 'Learning patterns without labels'),
(6, 1, ARRAY['AI', 'NLP'], 'Natural Language Processing', 'Processing and understanding human language'),
(7, 1, ARRAY['AI', 'NLP', 'Text Classification'], 'Text Classification', 'Categorizing text into predefined classes'),
(8, 1, ARRAY['AI', 'NLP', 'Named Entity Recognition'], 'Named Entity Recognition', 'Identifying entities in text'),
(9, 1, ARRAY['Technology'], 'Technology', 'General technology category'),
(10, 1, ARRAY['Technology', 'Web Development'], 'Web Development', 'Creating web applications and sites'),
(11, 1, ARRAY['Technology', 'Web Development', 'Frontend'], 'Frontend Development', 'Client-side web development'),
(12, 1, ARRAY['Technology', 'Web Development', 'Backend'], 'Backend Development', 'Server-side development'),
(13, 1, ARRAY['Technology', 'Databases'], 'Databases', 'Data storage and management systems'),
(14, 1, ARRAY['Technology', 'Databases', 'SQL'], 'SQL Databases', 'Relational database systems'),
(15, 1, ARRAY['Technology', 'Databases', 'NoSQL'], 'NoSQL Databases', 'Non-relational database systems');

-- Sample Taxonomy Edges (Version 1)
INSERT INTO taxonomy_edges (version, parent_node_id, child_node_id) VALUES
(1, 1, 2),   -- AI -> Machine Learning
(1, 1, 6),   -- AI -> NLP
(1, 2, 3),   -- Machine Learning -> Deep Learning
(1, 2, 4),   -- Machine Learning -> Supervised Learning
(1, 2, 5),   -- Machine Learning -> Unsupervised Learning
(1, 6, 7),   -- NLP -> Text Classification
(1, 6, 8),   -- NLP -> Named Entity Recognition
(1, 9, 10),  -- Technology -> Web Development
(1, 9, 13),  -- Technology -> Databases
(1, 10, 11), -- Web Development -> Frontend
(1, 10, 12), -- Web Development -> Backend
(1, 13, 14), -- Databases -> SQL
(1, 13, 15); -- Databases -> NoSQL

-- Sample Documents
INSERT INTO documents (doc_id, source_url, title, content_type, metadata) VALUES
(gen_random_uuid(), 'https://example.com/ml-guide', 'Introduction to Machine Learning', 'text/html', '{"author": "Dr. Smith", "publication_date": "2024-01-15"}'),
(gen_random_uuid(), 'https://example.com/deep-learning', 'Deep Learning Fundamentals', 'text/html', '{"author": "Prof. Johnson", "difficulty": "intermediate"}'),
(gen_random_uuid(), 'https://example.com/nlp-tutorial', 'Natural Language Processing Tutorial', 'text/html', '{"author": "AI Research Team", "tags": ["tutorial", "beginner"]}'),
(gen_random_uuid(), 'https://example.com/web-dev-guide', 'Modern Web Development Practices', 'text/html', '{"author": "Tech Corp", "framework": "React"}'),
(gen_random_uuid(), 'https://example.com/sql-basics', 'SQL Database Design Principles', 'text/html', '{"author": "Database Expert", "level": "beginner"}');

-- Sample Chunks with realistic text content
WITH doc_data AS (
  SELECT doc_id, title FROM documents
)
INSERT INTO chunks (chunk_id, doc_id, text, span, chunk_index, metadata)
SELECT 
  gen_random_uuid(),
  d.doc_id,
  CASE 
    WHEN d.title LIKE '%Machine Learning%' THEN 'Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. It uses algorithms to identify patterns in data and make predictions or classifications.'
    WHEN d.title LIKE '%Deep Learning%' THEN 'Deep learning is a specialized subset of machine learning that uses neural networks with multiple layers to process data. These networks can automatically learn complex patterns and representations from raw data, making them particularly effective for tasks like image recognition and natural language processing.'
    WHEN d.title LIKE '%Natural Language Processing%' THEN 'Natural Language Processing (NLP) is a field of AI that focuses on enabling computers to understand, interpret, and generate human language. Key tasks in NLP include text classification, sentiment analysis, named entity recognition, and machine translation.'
    WHEN d.title LIKE '%Web Development%' THEN 'Modern web development involves creating dynamic, responsive web applications using frameworks like React, Vue.js, or Angular. Frontend development focuses on user interfaces, while backend development handles server-side logic, databases, and APIs.'
    WHEN d.title LIKE '%SQL%' THEN 'SQL (Structured Query Language) is used to manage and manipulate relational databases. Good database design principles include normalization, proper indexing, and maintaining referential integrity through foreign key constraints.'
    ELSE 'This is sample content for testing purposes.'
  END,
  int4range(0, 200),
  0,
  '{"section": "introduction", "word_count": 35}'
FROM doc_data d;

-- Sample Embeddings (with mock vectors)
-- Create a function to generate random vectors
CREATE OR REPLACE FUNCTION generate_random_vector(dimension INT)
RETURNS vector
LANGUAGE plpgsql
AS $$
DECLARE
    result_array FLOAT[];
    i INT;
BEGIN
    result_array := ARRAY[]::FLOAT[];
    FOR i IN 1..dimension LOOP
        result_array := array_append(result_array, (random() * 2 - 1)::FLOAT);
    END LOOP;
    RETURN array_to_string(result_array, ',')::vector;
END $$;

-- Insert embeddings with proper 1536-dimension vectors
WITH chunk_data AS (
    SELECT chunk_id, c.text 
    FROM chunks c
)
INSERT INTO embeddings (chunk_id, vec, model_name, bm25_tokens)
SELECT 
    chunk_id,
    generate_random_vector(1536),
    'text-embedding-ada-002',
    CASE 
        WHEN cd.text LIKE '%machine learning%' THEN ARRAY['machine', 'learning', 'data', 'algorithm', 'model', 'training']
        WHEN cd.text LIKE '%deep learning%' THEN ARRAY['deep', 'learning', 'neural', 'network', 'layers', 'artificial']
        WHEN cd.text LIKE '%natural language%' THEN ARRAY['natural', 'language', 'processing', 'text', 'nlp', 'classification']
        WHEN cd.text LIKE '%web development%' THEN ARRAY['web', 'development', 'frontend', 'backend', 'javascript', 'react']
        WHEN cd.text LIKE '%database%' THEN ARRAY['database', 'sql', 'data', 'query', 'table', 'relational']
        ELSE ARRAY['technology', 'computer', 'software', 'system', 'digital', 'information']
    END
FROM chunk_data cd;

-- Drop the helper function
DROP FUNCTION IF EXISTS generate_random_vector(INT);

-- Sample Document-Taxonomy Mappings
WITH doc_samples AS (
  SELECT doc_id, title FROM documents
)
INSERT INTO doc_taxonomy (doc_id, path, confidence, source)
SELECT 
  d.doc_id,
  CASE 
    WHEN d.title LIKE '%Machine Learning%' THEN ARRAY['AI', 'Machine Learning']
    WHEN d.title LIKE '%Deep Learning%' THEN ARRAY['AI', 'Machine Learning', 'Deep Learning']
    WHEN d.title LIKE '%Natural Language Processing%' THEN ARRAY['AI', 'NLP']
    WHEN d.title LIKE '%Web Development%' THEN ARRAY['Technology', 'Web Development']
    WHEN d.title LIKE '%SQL%' THEN ARRAY['Technology', 'Databases', 'SQL']
    ELSE ARRAY['Technology']
  END,
  0.85 + (random() * 0.1), -- Random confidence between 0.85-0.95
  'llm'
FROM doc_samples d;

-- Sample HITL Queue entries (only if table exists - created in migration 0003)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'hitl_queue') THEN
        WITH low_conf_chunks AS (
            SELECT c.chunk_id, c.text 
            FROM chunks c 
            JOIN documents d ON c.doc_id = d.doc_id 
            LIMIT 2
        )
        INSERT INTO hitl_queue (chunk_id, original_classification, suggested_paths, confidence, priority, status)
        SELECT 
            chunk_id,
            jsonb_build_object(
                'canonical', ARRAY['AI'],
                'candidates', jsonb_build_array(
                    jsonb_build_object('path', ARRAY['AI', 'Machine Learning'], 'score', 0.6),
                    jsonb_build_object('path', ARRAY['AI', 'NLP'], 'score', 0.55)
                ),
                'confidence', 0.6,
                'reasoning', ARRAY['Ambiguous technical content', 'Multiple possible categories']
            ),
            ARRAY['AI', 'Technology'],
            0.6,
            2, -- high priority
            'pending'
        FROM low_conf_chunks;
    END IF;
END $$;

-- Sample Migration Record
INSERT INTO taxonomy_migrations (from_version, to_version, migration_type, changes) VALUES
(NULL, 1, 'upgrade', jsonb_build_object(
  'description', 'Initial taxonomy structure',
  'nodes_added', 15,
  'edges_added', 13,
  'timestamp', CURRENT_TIMESTAMP
));

-- Sample Audit Log entries (only if table exists - created in migration 0003)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'audit_log') THEN
        INSERT INTO audit_log (action, actor, target, detail) VALUES
        ('taxonomy_create', 'system', '1', jsonb_build_object('canonical_path', ARRAY['AI'], 'version', 1)),
        ('document_upload', 'test_user', null, jsonb_build_object('document_count', 5, 'total_chunks', 5)),
        ('search', 'user123', null, jsonb_build_object('query', 'machine learning', 'results_count', 3, 'latency_ms', 45)),
        ('classify', 'system', null, jsonb_build_object('chunk_id', 'sample', 'confidence', 0.89, 'path', ARRAY['AI', 'Machine Learning'])),
        ('hitl_queue_add', 'system', null, jsonb_build_object('reason', 'Low confidence classification', 'confidence', 0.6));
    END IF;
END $$;

-- Update statistics for query planner (conditional based on table existence)
DO $$
BEGIN
    -- Analyze core tables that always exist
    ANALYZE taxonomy_nodes;
    ANALYZE taxonomy_edges;
    ANALYZE documents;
    ANALYZE chunks;
    ANALYZE embeddings;
    ANALYZE doc_taxonomy;
    
    -- Analyze optional tables only if they exist
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'audit_log') THEN
        ANALYZE audit_log;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'hitl_queue') THEN
        ANALYZE hitl_queue;
    END IF;
END $$;

-- Verification queries (safe table counting)
\echo 'Seeding completed. Verification:'
\echo '================================'

DO $$
DECLARE
    hitl_count INTEGER := 0;
    audit_count INTEGER := 0;
BEGIN
    -- Check optional table counts safely
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'hitl_queue') THEN
        SELECT COUNT(*) INTO hitl_count FROM hitl_queue;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'audit_log') THEN
        SELECT COUNT(*) INTO audit_count FROM audit_log;
    END IF;
    
    -- Display verification results
    RAISE NOTICE 'Seeding Verification Results:';
    RAISE NOTICE '============================';
    RAISE NOTICE 'Taxonomy Nodes: %', (SELECT COUNT(*) FROM taxonomy_nodes);
    RAISE NOTICE 'Taxonomy Edges: %', (SELECT COUNT(*) FROM taxonomy_edges);
    RAISE NOTICE 'Documents: %', (SELECT COUNT(*) FROM documents);
    RAISE NOTICE 'Chunks: %', (SELECT COUNT(*) FROM chunks);
    RAISE NOTICE 'Embeddings: %', (SELECT COUNT(*) FROM embeddings);
    RAISE NOTICE 'Doc Taxonomy: %', (SELECT COUNT(*) FROM doc_taxonomy);
    RAISE NOTICE 'HITL Queue: %', hitl_count;
    RAISE NOTICE 'Audit Log: %', audit_count;
END $$;

\echo ''
\echo 'Sample taxonomy tree (version 1):'
SELECT 
    array_to_string(canonical_path, ' > ') as taxonomy_path,
    node_name,
    description
FROM taxonomy_nodes 
WHERE version = 1 
ORDER BY canonical_path;