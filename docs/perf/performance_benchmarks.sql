-- Performance Benchmark Queries for Dynamic Taxonomy RAG v1.8.1
-- Purpose: Measure and verify index performance improvements
-- Usage: psql -d dt_rag -f performance_benchmarks.sql

\echo '========================================'
\echo 'Performance Benchmarks - Dynamic Taxonomy RAG v1.8.1'
\echo 'Timestamp:' `date -u +"%Y-%m-%d %H:%M:%S UTC"`
\echo '========================================'

-- Test setup: Ensure we have test data
\echo ''
\echo '=== Test Data Verification ==='
SELECT 
    'taxonomy_nodes' as table_name, COUNT(*) as count FROM taxonomy_nodes
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks  
UNION ALL
SELECT 'embeddings', COUNT(*) FROM embeddings
UNION ALL
SELECT 'doc_taxonomy', COUNT(*) FROM doc_taxonomy;

-- Performance test configuration
SET work_mem = '256MB';
SET random_page_cost = 1.1;  -- SSD optimization

\echo ''
\echo '=== 1. Vector Similarity Search (IVFFlat Index) ==='

-- Force index usage for testing
SET enable_seqscan = off;

-- Test vector similarity with EXPLAIN ANALYZE
\echo 'Testing IVFFlat vector index performance:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    chunk_id, 
    vec <=> (SELECT vec FROM embeddings LIMIT 1) as distance
FROM embeddings 
ORDER BY distance 
LIMIT 10;

-- Reset seqscan
SET enable_seqscan = on;

\echo ''
\echo '=== 2. Span Range Overlap Queries (GiST Index) ==='

-- Test int4range overlap performance
\echo 'Testing GiST span range index performance:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    chunk_id, text, span
FROM chunks 
WHERE span && int4range(100, 500);

-- Test span containment
\echo 'Testing span containment queries:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)  
SELECT 
    chunk_id, text, span
FROM chunks
WHERE span @> 250;  -- Contains position 250

\echo ''
\echo '=== 3. Taxonomy Path Search (GIN Index) ==='

-- Test taxonomy path array search
\echo 'Testing GIN taxonomy path index performance:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    node_id, canonical_path, node_name
FROM taxonomy_nodes
WHERE canonical_path && ARRAY['AI'];  -- Overlap with AI

-- Test exact path matching
\echo 'Testing exact path matching:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    node_id, canonical_path, node_name  
FROM taxonomy_nodes
WHERE canonical_path = ARRAY['AI', 'Machine Learning'];

\echo ''
\echo '=== 4. BM25 Token Search (GIN Index) ==='

-- Test BM25 token array search
\echo 'Testing GIN BM25 token index performance:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    embedding_id, chunk_id, bm25_tokens
FROM embeddings
WHERE bm25_tokens && ARRAY['machine', 'learning'];

\echo ''
\echo '=== 5. Document Classification Search ==='

-- Test doc_taxonomy path search
\echo 'Testing document classification path search:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    d.title, dt.path, dt.confidence
FROM doc_taxonomy dt
JOIN documents d ON dt.doc_id = d.doc_id
WHERE dt.path @> ARRAY['AI'];  -- Contains AI in path

\echo ''
\echo '=== 6. Composite Query Performance ==='

-- Test realistic hybrid search query
\echo 'Testing composite hybrid search query:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
WITH vector_candidates AS (
    SELECT chunk_id, vec <=> (SELECT vec FROM embeddings LIMIT 1) as distance
    FROM embeddings 
    ORDER BY distance 
    LIMIT 20
),
bm25_candidates AS (
    SELECT DISTINCT e.chunk_id, 0.5 as score
    FROM embeddings e
    WHERE e.bm25_tokens && ARRAY['machine', 'learning']
    LIMIT 20
)
SELECT 
    c.chunk_id,
    c.text,
    d.title,
    dt.path,
    dt.confidence
FROM vector_candidates vc
JOIN chunks c ON vc.chunk_id = c.chunk_id
JOIN documents d ON c.doc_id = d.doc_id
LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
ORDER BY vc.distance
LIMIT 5;

\echo ''
\echo '=== 7. HITL Queue Performance ==='

-- Test HITL queue queries
\echo 'Testing HITL queue query performance:'
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT 
    queue_id, chunk_id, confidence, priority, status
FROM hitl_queue 
WHERE status = 'pending' 
  AND confidence < 0.7
ORDER BY priority, created_at
LIMIT 10;

\echo ''
\echo '=== 8. Rollback Procedure Performance ==='

-- Test rollback procedure (dry run analysis)
\echo 'Testing taxonomy rollback procedure performance:'
\echo 'Note: This is a read-only analysis of what rollback would affect'

-- Analyze nodes that would be affected by rollback
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT COUNT(*) as nodes_to_remove
FROM taxonomy_nodes 
WHERE version > 1;

-- Analyze doc_taxonomy mappings that would need updating  
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT COUNT(*) as mappings_to_check
FROM doc_taxonomy dt
JOIN taxonomy_nodes tn ON dt.path = tn.canonical_path
WHERE tn.version > 1;

\echo ''
\echo '=== 9. Index Usage Statistics ==='

-- Show index usage stats (requires pg_stat_statements extension)
\echo 'Index size and usage statistics:'
SELECT 
    schemaname,
    tablename, 
    indexname,
    pg_size_pretty(pg_total_relation_size(indexrelid)) as index_size,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
  AND indexname IN (
    'idx_chunks_span_gist',
    'idx_embeddings_vec_ivf', 
    'idx_taxonomy_canonical',
    'idx_doc_taxonomy_path',
    'idx_embeddings_bm25'
  )
ORDER BY pg_total_relation_size(indexrelid) DESC;

\echo ''
\echo '=== 10. Performance Summary ==='

-- Performance summary with timing estimates
SELECT 
    'Performance Benchmark Completed' as status,
    CURRENT_TIMESTAMP as completed_at,
    'Check EXPLAIN ANALYZE output above for actual timings' as note;

-- Table and index size summary
\echo ''
\echo 'Storage size summary:'
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''
\echo '========================================'
\echo 'Benchmark completed. Review EXPLAIN ANALYZE output above.'
\echo 'Expected improvements with proper indexes:'
\echo '- Span overlap queries: ~50x faster'
\echo '- Vector similarity: ~50x faster'  
\echo '- Path searches: ~50x faster'
\echo '- Rollback TTR: <15 minutes target'
\echo '========================================'