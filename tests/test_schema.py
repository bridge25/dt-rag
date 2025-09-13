"""
Database schema tests for Dynamic Taxonomy RAG v1.8.1
Tests all tables, indexes, constraints, and procedures
"""

import pytest
import psycopg2
import os
from typing import List, Dict, Any
import uuid
from datetime import datetime


class TestDatabaseSchema:
    """Test suite for database schema validation"""

    @pytest.fixture(scope="function")  # Changed to function scope for isolation
    def db_connection(self):
        """Create database connection for testing"""
        # Use test database URL from environment or default
        database_url = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:password@localhost:5432/dt_rag_test')
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        
        try:
            yield conn
        finally:
            # Always rollback to clean state after each test
            if not conn.closed:
                conn.rollback()
            conn.close()

    def test_extensions_loaded(self, db_connection):
        """Test that required PostgreSQL extensions are loaded"""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('vector', 'btree_gist', 'pg_trgm')
                ORDER BY extname;
            """)
            extensions = [row[0] for row in cursor.fetchall()]
            
        assert 'vector' in extensions, "vector extension not loaded"
        assert 'btree_gist' in extensions, "btree_gist extension not loaded"
        # pg_trgm is optional
        
    def test_core_tables_exist(self, db_connection):
        """Test that all core tables exist with correct structure"""
        expected_tables = {
            'taxonomy_nodes', 'taxonomy_edges', 'taxonomy_migrations',
            'documents', 'chunks', 'embeddings', 'doc_taxonomy',
            'audit_log', 'hitl_queue'
        }
        
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            actual_tables = {row[0] for row in cursor.fetchall()}
            
        missing_tables = expected_tables - actual_tables
        assert not missing_tables, f"Missing tables: {missing_tables}"

    def test_taxonomy_nodes_constraints(self, db_connection):
        """Test taxonomy_nodes table constraints"""
        with db_connection.cursor() as cursor:
            # Test valid node insertion
            cursor.execute("""
                INSERT INTO taxonomy_nodes (canonical_path, node_name, version)
                VALUES (ARRAY['AI', 'Machine Learning'], 'Neural Networks', 1)
                RETURNING node_id;
            """)
            node_id = cursor.fetchone()[0]
            assert node_id is not None
            
            # Commit the valid insertion first
            db_connection.commit()
            
            # Test invalid path constraint (empty array should violate CHECK constraint)
            try:
                cursor.execute("""
                    INSERT INTO taxonomy_nodes (canonical_path, node_name, version)
                    VALUES (ARRAY[]::TEXT[], 'Invalid', 1);
                """)
                # If we get here without exception, the constraint is not working
                pytest.fail("Expected IntegrityError for empty canonical_path array, but insert succeeded")
            except psycopg2.IntegrityError as e:
                # This is expected - the CHECK constraint should prevent empty arrays
                assert "valid_path_format" in str(e) or "canonical_path" in str(e)
                db_connection.rollback()  # Rollback after IntegrityError
                pass  # Test passes
            except Exception as e:
                db_connection.rollback()  # Rollback after any other exception
                pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")

            # Test invalid version constraint
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO taxonomy_nodes (canonical_path, node_name, version)
                    VALUES (ARRAY['Test'], 'Invalid Version', 0);
                """)
            db_connection.rollback()

    def test_chunks_span_constraints(self, db_connection):
        """Test chunks table span range constraints"""
        with db_connection.cursor() as cursor:
            # First create a document
            cursor.execute("""
                INSERT INTO documents (title, content_type)
                VALUES ('Test Document', 'text/plain')
                RETURNING doc_id;
            """)
            doc_id = cursor.fetchone()[0]
            
            # Test valid chunk with span
            cursor.execute("""
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (%s, 'This is test content', int4range(0, 20), 0)
                RETURNING chunk_id;
            """, (doc_id,))
            chunk_id = cursor.fetchone()[0]
            assert chunk_id is not None
            
            # Test empty span constraint
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO chunks (doc_id, text, span, chunk_index)
                    VALUES (%s, 'Invalid span', 'empty'::int4range, 1);
                """, (doc_id,))
            db_connection.rollback()

    def test_embeddings_vector_constraint(self, db_connection):
        """Test embeddings table vector dimension constraint"""
        with db_connection.cursor() as cursor:
            # Create document and chunk first
            cursor.execute("""
                INSERT INTO documents (title) VALUES ('Test Doc') RETURNING doc_id;
            """)
            doc_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (%s, 'Test content', int4range(0, 12), 0)
                RETURNING chunk_id;
            """, (doc_id,))
            chunk_id = cursor.fetchone()[0]
            
            # Test valid 1536-dimension vector
            valid_vector = '[' + ','.join(['0.1'] * 1536) + ']'
            cursor.execute("""
                INSERT INTO embeddings (chunk_id, vec)
                VALUES (%s, %s::vector)
                RETURNING embedding_id;
            """, (chunk_id, valid_vector))
            embedding_id = cursor.fetchone()[0]
            assert embedding_id is not None
            
            # Commit the valid insertion first
            db_connection.commit()
            
            # Test invalid dimension vector (using wrong dimension: 512 instead of 1536)
            invalid_vector = '[' + ','.join(['0.1'] * 512) + ']'  # Wrong dimension - should be 1536
            with pytest.raises(psycopg2.errors.DataException):  # Changed from IntegrityError to DataException
                cursor.execute("""
                    INSERT INTO embeddings (chunk_id, vec)
                    VALUES (%s, %s::vector);
                """, (chunk_id, invalid_vector))
            # No need for explicit rollback - pytest will handle transaction cleanup

    def test_confidence_constraints(self, db_connection):
        """Test confidence value constraints across tables"""
        with db_connection.cursor() as cursor:
            # Setup test data
            cursor.execute("INSERT INTO documents (title) VALUES ('Test') RETURNING doc_id;")
            doc_id = cursor.fetchone()[0]
            
            # Test doc_taxonomy confidence constraint
            cursor.execute("""
                INSERT INTO doc_taxonomy (doc_id, path, confidence)
                VALUES (%s, ARRAY['AI'], 0.85)
                RETURNING mapping_id;
            """, (doc_id,))
            mapping_id = cursor.fetchone()[0]
            assert mapping_id is not None
            
            # Test invalid confidence (> 1.0)
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO doc_taxonomy (doc_id, path, confidence)
                    VALUES (%s, ARRAY['Invalid'], 1.5);
                """, (doc_id,))
            db_connection.rollback()
            
            # Test invalid confidence (< 0.0)
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO doc_taxonomy (doc_id, path, confidence)
                    VALUES (%s, ARRAY['Invalid'], -0.1);
                """, (doc_id,))
            db_connection.rollback()

    def test_required_indexes_exist(self, db_connection):
        """Test that all required indexes exist"""
        required_indexes = {
            'idx_chunks_span_gist',  # GiST for span range queries
            'idx_taxonomy_canonical',  # GIN for taxonomy path arrays
            'idx_embeddings_vec_ivf',  # IVFFlat for vector similarity
            'idx_doc_taxonomy_path',   # GIN for doc taxonomy paths
            'idx_embeddings_bm25',     # GIN for BM25 tokens
            'idx_audit_log_timestamp', # B-tree for audit log queries
            'idx_hitl_queue_status_priority'  # Composite for HITL queue
        }
        
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE schemaname = 'public'
            """)
            actual_indexes = {row[0] for row in cursor.fetchall()}
            
        missing_indexes = required_indexes - actual_indexes
        assert not missing_indexes, f"Missing indexes: {missing_indexes}"

    def test_utility_functions_exist(self, db_connection):
        """Test that utility functions are created correctly"""
        with db_connection.cursor() as cursor:
            # Test chunk_span_length function
            cursor.execute("SELECT chunk_span_length(int4range(10, 25));")
            length = cursor.fetchone()[0]
            assert length == 15
            
            # Test spans_overlap function
            cursor.execute("SELECT spans_overlap(int4range(0, 10), int4range(5, 15));")
            overlap = cursor.fetchone()[0]
            assert overlap is True
            
            cursor.execute("SELECT spans_overlap(int4range(0, 5), int4range(10, 15));")
            no_overlap = cursor.fetchone()[0]
            assert no_overlap is False
            
            # Test taxonomy_depth function
            cursor.execute("SELECT taxonomy_depth(ARRAY['AI', 'Machine Learning', 'Deep Learning']);")
            depth = cursor.fetchone()[0]
            assert depth == 3

    def test_taxonomy_rollback_procedure_exists(self, db_connection):
        """Test that the taxonomy rollback procedure exists and is callable"""
        with db_connection.cursor() as cursor:
            # Check if procedure exists
            cursor.execute("""
                SELECT proname FROM pg_proc 
                WHERE proname = 'taxonomy_rollback';
            """)
            result = cursor.fetchone()
            assert result is not None, "taxonomy_rollback procedure not found"

    def test_audit_trigger_functionality(self, db_connection):
        """Test that audit triggers work correctly"""
        with db_connection.cursor() as cursor:
            # Count existing audit log entries
            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'taxonomy_create';")
            initial_count = cursor.fetchone()[0]
            
            # Create a taxonomy node (should trigger audit)
            cursor.execute("""
                INSERT INTO taxonomy_nodes (canonical_path, node_name, version)
                VALUES (ARRAY['Test', 'Trigger'], 'Audit Test', 1);
            """)
            
            # Check that audit log entry was created
            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'taxonomy_create';")
            new_count = cursor.fetchone()[0]
            
            assert new_count == initial_count + 1, "Audit trigger not working"

    def test_hitl_queue_constraints(self, db_connection):
        """Test HITL queue table constraints and logic"""
        with db_connection.cursor() as cursor:
            # Setup test data
            cursor.execute("INSERT INTO documents (title) VALUES ('HITL Test') RETURNING doc_id;")
            doc_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (%s, 'Low confidence text', int4range(0, 18), 0)
                RETURNING chunk_id;
            """, (doc_id,))
            chunk_id = cursor.fetchone()[0]
            
            # Test valid HITL queue entry
            classification = '{"canonical": ["AI"], "confidence": 0.65}'
            cursor.execute("""
                INSERT INTO hitl_queue 
                (chunk_id, original_classification, suggested_paths, confidence, priority, status)
                VALUES (%s, %s::jsonb, ARRAY['AI', 'Tech'], 0.65, 2, 'pending')
                RETURNING queue_id;
            """, (chunk_id, classification))
            queue_id = cursor.fetchone()[0]
            assert queue_id is not None
            
            # Test assignment logic constraint
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute("""
                    INSERT INTO hitl_queue 
                    (chunk_id, original_classification, suggested_paths, confidence, status)
                    VALUES (%s, %s::jsonb, ARRAY['Test'], 0.5, 'assigned');
                """, (chunk_id, classification))
            db_connection.rollback()

    def test_views_exist_and_functional(self, db_connection):
        """Test that created views exist and return data correctly"""
        with db_connection.cursor() as cursor:
            # Test v_taxonomy_version_summary view
            cursor.execute("SELECT * FROM v_taxonomy_version_summary LIMIT 1;")
            # Should not error even if empty
            
            # Test v_low_confidence_classifications view  
            cursor.execute("SELECT * FROM v_low_confidence_classifications LIMIT 1;")
            # Should not error even if empty

    def test_add_to_hitl_queue_function(self, db_connection):
        """Test the add_to_hitl_queue function"""
        with db_connection.cursor() as cursor:
            # Setup test data
            cursor.execute("INSERT INTO documents (title) VALUES ('Function Test') RETURNING doc_id;")
            doc_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO chunks (doc_id, text, span, chunk_index)
                VALUES (%s, 'Function test content', int4range(0, 21), 0)
                RETURNING chunk_id;
            """, (doc_id,))
            chunk_id = cursor.fetchone()[0]
            
            # Test the function
            classification = '{"canonical": ["Test"], "confidence": 0.4}'
            cursor.execute("""
                SELECT add_to_hitl_queue(%s, %s::jsonb, ARRAY['Test', 'Function'], 0.4);
            """, (chunk_id, classification))
            returned_queue_id = cursor.fetchone()[0]
            
            assert returned_queue_id is not None
            
            # Verify the entry was created
            cursor.execute("""
                SELECT confidence, suggested_paths FROM hitl_queue WHERE queue_id = %s;
            """, (returned_queue_id,))
            result = cursor.fetchone()
            assert result[0] == 0.4  # confidence
            assert result[1] == ['Test', 'Function']  # suggested_paths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])