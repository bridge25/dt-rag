-- Dynamic Taxonomy RAG v1.8.1 - Test Data Seeding
-- Purpose: Insert sample data for development and testing
-- Usage: psql -d dt_rag -f seed_data.sql

-- Clear existing data (in dependency order)
DELETE FROM doc_taxonomy;
DELETE FROM embeddings;
DELETE FROM chunks;
DELETE FROM documents;
DELETE FROM taxonomy_edges;
DELETE FROM taxonomy_nodes;
DELETE FROM taxonomy_migrations;

-- Reset sequences
ALTER SEQUENCE taxonomy_nodes_node_id_seq RESTART WITH 1;
ALTER SEQUENCE taxonomy_edges_edge_id_seq RESTART WITH 1;
ALTER SEQUENCE taxonomy_migrations_migration_id_seq RESTART WITH 1;

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
WITH chunk_data AS (
  SELECT chunk_id FROM chunks
)
INSERT INTO embeddings (chunk_id, vec, model_name, bm25_tokens)
SELECT 
  chunk_id,
  ('[' || array_to_string(array_agg(random()::text), ',') || ']')::vector,
  'text-embedding-ada-002',
  ARRAY['machine', 'learning', 'artificial', 'intelligence', 'data', 'algorithm']
FROM chunk_data, generate_series(1, 1536) gs
GROUP BY chunk_id;

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

-- Sample HITL Queue entries (low confidence classifications)
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

-- Sample Migration Record
INSERT INTO taxonomy_migrations (from_version, to_version, migration_type, changes) VALUES
(NULL, 1, 'upgrade', jsonb_build_object(
  'description', 'Initial taxonomy structure',
  'nodes_added', 15,
  'edges_added', 13,
  'timestamp', CURRENT_TIMESTAMP
));

-- Sample Audit Log entries
INSERT INTO audit_log (action, actor, target, detail) VALUES
('taxonomy_create', 'system', '1', jsonb_build_object('canonical_path', ARRAY['AI'], 'version', 1)),
('document_upload', 'test_user', null, jsonb_build_object('document_count', 5, 'total_chunks', 5)),
('search', 'user123', null, jsonb_build_object('query', 'machine learning', 'results_count', 3, 'latency_ms', 45)),
('classify', 'system', null, jsonb_build_object('chunk_id', 'sample', 'confidence', 0.89, 'path', ARRAY['AI', 'Machine Learning'])),
('hitl_queue_add', 'system', null, jsonb_build_object('reason', 'Low confidence classification', 'confidence', 0.6));

-- Update statistics for query planner
ANALYZE taxonomy_nodes;
ANALYZE taxonomy_edges;
ANALYZE documents;
ANALYZE chunks;
ANALYZE embeddings;
ANALYZE doc_taxonomy;
ANALYZE audit_log;
ANALYZE hitl_queue;

-- Verification queries
\echo 'Seeding completed. Verification:'
\echo '================================'
SELECT 'Taxonomy Nodes:' as table_name, COUNT(*) as count FROM taxonomy_nodes
UNION ALL
SELECT 'Taxonomy Edges:', COUNT(*) FROM taxonomy_edges  
UNION ALL
SELECT 'Documents:', COUNT(*) FROM documents
UNION ALL
SELECT 'Chunks:', COUNT(*) FROM chunks
UNION ALL
SELECT 'Embeddings:', COUNT(*) FROM embeddings
UNION ALL
SELECT 'Doc Taxonomy:', COUNT(*) FROM doc_taxonomy
UNION ALL
SELECT 'HITL Queue:', COUNT(*) FROM hitl_queue
UNION ALL
SELECT 'Audit Log:', COUNT(*) FROM audit_log;

\echo ''
\echo 'Sample taxonomy tree (version 1):'
SELECT 
    array_to_string(canonical_path, ' > ') as taxonomy_path,
    node_name,
    description
FROM taxonomy_nodes 
WHERE version = 1 
ORDER BY canonical_path;