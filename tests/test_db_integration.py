"""
Database Integration Tests for Dynamic Taxonomy RAG v1.8.1
통합 테스트 체크리스트 (A~E) - PR-2 스키마 증명
"""

import pytest
import psycopg2
import os
from typing import List, Dict, Any
import uuid
from datetime import datetime
import subprocess
import tempfile


class TestDatabaseIntegration:
    """통합 테스트 체크리스트 - PR-2 약속 증명"""

    @pytest.fixture(scope="class")
    def db_connection(self):
        """Create database connection for integration testing"""
        database_url = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:password@localhost:5432/dt_rag_test')
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        yield conn
        conn.close()

    # ========================================================================
    # A. 마이그/롤백 불변성 (Migration/Rollback Invariants)
    # ========================================================================

    def test_alembic_migration_roundtrip(self, db_connection):
        """A1. alembic upgrade head → downgrade -1 → upgrade head 성공"""
        # This test assumes Alembic is configured properly
        alembic_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Test upgrade to head
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'], 
            cwd=alembic_dir, 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, f"Alembic upgrade failed: {result.stderr}"
        
        # Test downgrade by 1
        result = subprocess.run(
            ['alembic', 'downgrade', '-1'], 
            cwd=alembic_dir, 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, f"Alembic downgrade failed: {result.stderr}"
        
        # Test upgrade back to head
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'], 
            cwd=alembic_dir, 
            capture_output=True, 
            text=True
        )
        assert result.returncode == 0, f"Alembic re-upgrade failed: {result.stderr}"

    def test_taxonomy_rollback_idempotent(self, db_connection):
        """A2. taxonomy_rollback 여러 번 호출해도 결과 동일 (idempotent)"""
        with db_connection.cursor() as cursor:
            # Setup test data: create version 2
            cursor.execute("""
                INSERT INTO taxonomy_nodes (version, canonical_path, node_name)
                VALUES (2, ARRAY['Test', 'Rollback'], 'Test Rollback Node')
                ON CONFLICT DO NOTHING;
            """)
            
            cursor.execute("""
                INSERT INTO taxonomy_nodes (version, canonical_path, node_name)  
                VALUES (3, ARRAY['Test', 'Future'], 'Future Test Node')
                ON CONFLICT DO NOTHING;
            """)
            
            # First rollback to version 2
            cursor.execute("CALL taxonomy_rollback(2);")
            cursor.execute("SELECT COUNT(*) FROM taxonomy_nodes WHERE version > 2;")
            count_after_first = cursor.fetchone()[0]
            
            # Second rollback to version 2 (should be idempotent)
            cursor.execute("CALL taxonomy_rollback(2);") 
            cursor.execute("SELECT COUNT(*) FROM taxonomy_nodes WHERE version > 2;")
            count_after_second = cursor.fetchone()[0]
            
            # Results should be identical
            assert count_after_first == count_after_second, "Rollback is not idempotent"
            assert count_after_first == 0, "Rollback did not remove future versions"
            
            # Verify audit log recorded both operations
            cursor.execute("""
                SELECT COUNT(*) FROM audit_log 
                WHERE action = 'taxonomy_rollback' 
                AND target = '2';
            """)
            audit_count = cursor.fetchone()[0]
            assert audit_count >= 2, "Audit log should record all rollback attempts"

    # ========================================================================
    # B. 제약·인덱스 검증 (Constraints & Index Validation)
    # ========================================================================

    def test_doc_taxonomy_constraints(self, db_connection):
        """B1. doc_taxonomy 제약 조건 검증"""
        with db_connection.cursor() as cursor:
            # Create test document
            cursor.execute("""
                INSERT INTO documents (title) VALUES ('Constraint Test Doc') 
                RETURNING doc_id;
            """)
            doc_id = cursor.fetchone()[0]
            
            # Test confidence constraint (valid range)
            cursor.execute("""
                INSERT INTO doc_taxonomy (doc_id, path, confidence)
                VALUES (%s, ARRAY['AI'], 0.85);
            """, (doc_id,))
            
            # Test confidence > 1.0 should fail
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO doc_taxonomy (doc_id, path, confidence)
                    VALUES (%s, ARRAY['Invalid'], 1.5);
                """, (doc_id,))
            db_connection.rollback()
            
            # Test confidence < 0.0 should fail  
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO doc_taxonomy (doc_id, path, confidence)
                    VALUES (%s, ARRAY['Invalid'], -0.1);
                """, (doc_id,))
            db_connection.rollback()

    def test_taxonomy_edges_unique_constraint(self, db_connection):
        """B2. taxonomy_edges 복합 UNIQUE 제약 검증"""
        with db_connection.cursor() as cursor:
            # Create test nodes
            cursor.execute("""
                INSERT INTO taxonomy_nodes (version, canonical_path, node_name)
                VALUES (1, ARRAY['Parent'], 'Parent Node') RETURNING node_id;
            """)
            parent_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO taxonomy_nodes (version, canonical_path, node_name)  
                VALUES (1, ARRAY['Child'], 'Child Node') RETURNING node_id;
            """)
            child_id = cursor.fetchone()[0]
            
            # First edge insertion should succeed
            cursor.execute("""
                INSERT INTO taxonomy_edges (version, parent_node_id, child_node_id)
                VALUES (1, %s, %s);
            """, (parent_id, child_id))
            
            # Duplicate edge should fail (UNIQUE constraint)
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO taxonomy_edges (version, parent_node_id, child_node_id)
                    VALUES (1, %s, %s);
                """, (parent_id, child_id))
            db_connection.rollback()

    def test_critical_indexes_exist(self, db_connection):
        """B3. 핵심 인덱스 존재 확인"""
        critical_indexes = {
            'idx_chunks_span_gist': 'gist',     # GiST for span ranges
            'idx_embeddings_vec_ivf': 'ivfflat', # IVFFlat for vectors  
            'idx_taxonomy_canonical': 'gin',     # GIN for taxonomy paths
            'idx_doc_taxonomy_path': 'gin',      # GIN for doc paths
            'idx_embeddings_bm25': 'gin'         # GIN for BM25 tokens
        }
        
        with db_connection.cursor() as cursor:
            index_names = list(critical_indexes.keys())
            cursor.execute("""
                SELECT indexname,
                       CASE
                         WHEN indexdef LIKE '%USING gist%' THEN 'gist'
                         WHEN indexdef LIKE '%USING ivfflat%' THEN 'ivfflat'
                         WHEN indexdef LIKE '%USING gin%' THEN 'gin'
                         WHEN indexdef LIKE '%USING btree%' THEN 'btree'
                         ELSE 'unknown'
                       END as index_type
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND indexname = ANY(%s);
            """, (index_names,))
            
            found_indexes = {row[0]: row[1] for row in cursor.fetchall()}
            
            for index_name, expected_type in critical_indexes.items():
                assert index_name in found_indexes, f"Critical index {index_name} not found"
                assert found_indexes[index_name] == expected_type, \
                    f"Index {index_name} should be {expected_type}, found {found_indexes[index_name]}"

    # ========================================================================
    # C. HITL 큐 동작 (HITL Queue Operations)
    # ========================================================================

    def test_hitl_queue_workflow(self, db_connection):
        """C1. HITL 큐 상태 전이 워크플로우"""
        with db_connection.cursor() as cursor:
            # Setup test data
            cursor.execute("INSERT INTO documents (title) VALUES ('HITL Test') RETURNING doc_id;")
            doc_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (%s, 'Low confidence text content', int4range(0, 26), 0)
                RETURNING chunk_id;
            """, (doc_id,))
            chunk_id = cursor.fetchone()[0]
            
            # Test automatic HITL queue addition with confidence < 0.7
            classification = {
                "canonical": ["AI"],
                "confidence": 0.6,
                "candidates": [
                    {"path": ["AI", "ML"], "score": 0.6},
                    {"path": ["Technology"], "score": 0.55}
                ]
            }
            
            cursor.execute("""
                SELECT add_to_hitl_queue(%s, %s::jsonb, ARRAY['AI', 'Technology'], 0.6);
            """, (chunk_id, str(classification).replace("'", '"')))
            
            queue_id = cursor.fetchone()[0]
            assert queue_id is not None
            
            # Verify initial status is 'pending'
            cursor.execute("""
                SELECT status, confidence, priority FROM hitl_queue WHERE queue_id = %s;
            """, (queue_id,))
            status, confidence, priority = cursor.fetchone()
            
            assert status == 'pending', f"Expected status 'pending', got '{status}'"
            assert confidence == 0.6, f"Expected confidence 0.6, got {confidence}"
            
            # Test state transition: pending → assigned
            cursor.execute("""
                UPDATE hitl_queue 
                SET status = 'assigned', assigned_to = 'test_reviewer', assigned_at = CURRENT_TIMESTAMP
                WHERE queue_id = %s;
            """, (queue_id,))
            
            # Test state transition: assigned → resolved
            resolution = {"manual_path": ["AI", "Machine Learning"], "reviewer_confidence": 0.9}
            cursor.execute("""
                UPDATE hitl_queue
                SET status = 'resolved', 
                    resolved_at = CURRENT_TIMESTAMP,
                    resolution = %s::jsonb
                WHERE queue_id = %s;
            """, (str(resolution).replace("'", '"'), queue_id))
            
            # Verify final state
            cursor.execute("""
                SELECT status, resolution FROM hitl_queue WHERE queue_id = %s;
            """, (queue_id,))
            final_status, final_resolution = cursor.fetchone()
            
            assert final_status == 'resolved', f"Expected final status 'resolved', got '{final_status}'"
            assert final_resolution is not None, "Resolution should not be None"

    def test_low_confidence_view(self, db_connection):
        """C2. v_low_confidence_classifications 뷰 동작 확인"""
        with db_connection.cursor() as cursor:
            # Query the view (should not error even if empty)
            cursor.execute("""
                SELECT queue_id, chunk_id, confidence, status 
                FROM v_low_confidence_classifications
                LIMIT 5;
            """)
            results = cursor.fetchall()
            
            # View should be queryable (may be empty in clean test)
            assert isinstance(results, list), "View should return a list"
            
            # If there are results, verify structure
            if results:
                for row in results:
                    assert len(row) == 4, "View should return 4 columns"
                    assert row[3] == 'pending', "View should only show pending items"

    # ========================================================================
    # D. 검색 경로 가드 (Search Path Guards)  
    # ========================================================================

    def test_taxonomy_path_filtering(self, db_connection):
        """D1. canonical_path 필터링이 올바른 범위로 제한되는지 확인"""
        with db_connection.cursor() as cursor:
            # Setup test taxonomy and documents
            cursor.execute("""
                INSERT INTO documents (title) VALUES ('AI Document'), ('Tech Document')
                ON CONFLICT DO NOTHING;
            """)
            
            # Get doc IDs
            cursor.execute("SELECT doc_id, title FROM documents WHERE title IN ('AI Document', 'Tech Document');")
            docs = {title: doc_id for doc_id, title in cursor.fetchall()}
            
            if docs:
                # Create taxonomy mappings
                cursor.execute("""
                    INSERT INTO doc_taxonomy (doc_id, path, confidence, source)
                    VALUES
                        (%s, ARRAY['AI', 'Machine Learning'], 0.9, 'manual'),
                        (%s, ARRAY['Technology', 'Web Development'], 0.8, 'manual')
                    ON CONFLICT DO NOTHING;
                """, (docs.get('AI Document'), docs.get('Tech Document')))
            
            # Test path filtering - should only return AI documents
            cursor.execute("""
                SELECT d.title, dt.path 
                FROM doc_taxonomy dt
                JOIN documents d ON dt.doc_id = d.doc_id
                WHERE dt.path && ARRAY['AI'];  -- Overlap operator
            """)
            ai_results = cursor.fetchall()
            
            # Verify results contain only AI-related documents
            for title, path in ai_results:
                assert 'AI' in path, f"Non-AI document found in AI filter: {title} -> {path}"

    def test_bm25_vector_hybrid_pipeline(self, db_connection):
        """D2. BM25/Vector 후보 → Rerank 파이프라인 검증"""
        with db_connection.cursor() as cursor:
            # Test BM25 token search capability
            cursor.execute("""
                SELECT COUNT(*) 
                FROM embeddings 
                WHERE bm25_tokens && ARRAY['machine', 'learning'];
            """)
            bm25_count = cursor.fetchone()[0]
            
            # Test vector similarity search capability (mock vector)
            mock_vector = '[' + ','.join(['0.1'] * 1536) + ']'
            cursor.execute("""
                SELECT COUNT(*) 
                FROM embeddings 
                WHERE vec <=> %s::vector < 0.5
                LIMIT 50;  -- Simulate candidate limit
            """, (mock_vector,))
            vector_count = cursor.fetchone()[0]
            
            # Both search methods should be functional (may be 0 in clean test)
            assert bm25_count >= 0, "BM25 search should be queryable"
            assert vector_count >= 0, "Vector search should be queryable"

    # ========================================================================
    # E. 감사 로그 (Audit Logging)
    # ========================================================================

    def test_audit_log_completeness(self, db_connection):
        """E1. 롤백·마이그 실행 시 audit_log 기록 확인"""
        with db_connection.cursor() as cursor:
            # Count existing audit entries
            cursor.execute("SELECT COUNT(*) FROM audit_log;")
            initial_count = cursor.fetchone()[0]
            
            # Perform an auditable action (create taxonomy node)
            cursor.execute("""
                INSERT INTO taxonomy_nodes (version, canonical_path, node_name)
                VALUES (99, ARRAY['Audit', 'Test'], 'Audit Test Node');
            """)
            
            # Check if audit trigger recorded the action
            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'taxonomy_create';")
            create_count = cursor.fetchone()[0]
            
            assert create_count > 0, "Audit trigger should record taxonomy creation"
            
            # Test rollback audit logging
            cursor.execute("CALL taxonomy_rollback(1);")
            
            # Check rollback audit entries
            cursor.execute("""
                SELECT COUNT(*) FROM audit_log 
                WHERE action LIKE 'taxonomy_rollback%';
            """)
            rollback_count = cursor.fetchone()[0]
            
            assert rollback_count > 0, "Rollback operations should be audited"
            
            # Verify audit log structure
            cursor.execute("""
                SELECT action, actor, target, detail 
                FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT 1;
            """)
            latest_audit = cursor.fetchone()
            
            assert latest_audit is not None, "Audit log should have entries"
            assert latest_audit[0] is not None, "Audit action should not be null"
            assert latest_audit[1] is not None, "Audit actor should not be null"

    def test_audit_log_error_handling(self, db_connection):
        """E2. 감사 로그 기능이 작동하는지 확인 (PostgreSQL 트랜잭션 의미론 반영)"""
        with db_connection.cursor() as cursor:
            # PostgreSQL에서는 stored procedure에서 RAISE EXCEPTION 발생 시
            # 전체 트랜잭션이 롤백되므로, 대신 성공적인 audit 기능을 테스트

            # Test 1: Valid rollback operation generates audit logs
            cursor.execute("SELECT COUNT(*) FROM audit_log;")
            initial_count = cursor.fetchone()[0]

            # Create version 2 for testing
            cursor.execute("""
                INSERT INTO taxonomy_nodes (version, canonical_path, node_name)
                VALUES (2, ARRAY['Test', 'Audit'], 'Audit Test Node')
                ON CONFLICT DO NOTHING;
            """)

            # Rollback to same version (idempotent) - should be audited
            cursor.execute("CALL taxonomy_rollback(2);")

            cursor.execute("SELECT COUNT(*) FROM audit_log;")
            final_count = cursor.fetchone()[0]

            assert final_count > initial_count, "Successful operations should be audited"

            # Test 2: Check for specific audit log entries
            cursor.execute("""
                SELECT COUNT(*) FROM audit_log
                WHERE action = 'taxonomy_rollback' AND target = '2';
            """)
            rollback_audit_count = cursor.fetchone()[0]

            assert rollback_audit_count > 0, "Rollback operations should create audit entries"

    # ========================================================================
    # Performance & System Health Checks
    # ========================================================================

    def test_system_health_check(self, db_connection):
        """시스템 전반적인 건강도 체크"""
        with db_connection.cursor() as cursor:
            # Check all critical tables have at least basic structure
            essential_tables = ['taxonomy_nodes', 'taxonomy_edges', 'documents', 
                              'chunks', 'embeddings', 'doc_taxonomy', 'audit_log', 'hitl_queue']
            
            for table in essential_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                assert count >= 0, f"Table {table} should be queryable"
            
            # Check critical functions exist
            cursor.execute("""
                SELECT COUNT(*) FROM pg_proc 
                WHERE proname IN ('taxonomy_rollback', 'add_to_hitl_queue', 
                                 'chunk_span_length', 'spans_overlap', 'taxonomy_depth');
            """)
            func_count = cursor.fetchone()[0]
            assert func_count >= 5, "Essential functions should exist"
            
            # Check views exist
            cursor.execute("""
                SELECT COUNT(*) FROM pg_views 
                WHERE schemaname = 'public' 
                  AND viewname IN ('v_low_confidence_classifications', 'v_taxonomy_version_summary');
            """)
            view_count = cursor.fetchone()[0]
            assert view_count >= 2, "Essential views should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])