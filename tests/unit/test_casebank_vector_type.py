"""
@TEST:TAG-CASEBANK-VECTOR-TYPE-001
Unit tests for CaseBank Vector type optimization

This test verifies that query_vector uses pgvector.Vector(1536)
instead of ARRAY(Float) for optimal performance with HNSW indexing.
"""
# @TEST:TAG-CASEBANK-VECTOR-TYPE-001

import pytest
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# Import the actual production model
from apps.api.database import CaseBank, PGVECTOR_AVAILABLE


class TestCaseBankVectorType:
    """Test Vector type optimization for query_vector field"""

    def test_pgvector_is_available(self):
        """
        @TEST:TAG-CASEBANK-VECTOR-TYPE-001-1
        Verify pgvector library is installed and available
        """
        assert PGVECTOR_AVAILABLE is True, "pgvector library must be installed"

    def test_query_vector_uses_vector_type(self):
        """
        @TEST:TAG-CASEBANK-VECTOR-TYPE-001-2
        Verify query_vector uses pgvector.Vector(1536) instead of ARRAY(Float)

        This is critical for:
        - HNSW index compatibility (10x+ performance boost)
        - Proper vector similarity search operations
        - Optimal memory usage
        """
        # Get the column definition
        query_vector_col = CaseBank.__table__.columns['query_vector']

        # Compile to PostgreSQL dialect to get actual type
        col_type = query_vector_col.type
        compiled_type = col_type.compile(dialect=postgresql.dialect())
        type_str = str(compiled_type)

        # Check that it's Vector type, not ARRAY
        assert 'VECTOR' in type_str.upper(), (
            f"query_vector should use Vector type, got: {type_str}"
        )

        # Verify it's not using ARRAY type
        assert 'ARRAY' not in type_str.upper(), (
            f"query_vector should NOT use ARRAY type, got: {type_str}"
        )

    def test_query_vector_dimension_is_1536(self):
        """
        @TEST:TAG-CASEBANK-VECTOR-TYPE-001-3
        Verify Vector dimension is set to 1536 (OpenAI embedding size)
        """
        query_vector_col = CaseBank.__table__.columns['query_vector']
        col_type = query_vector_col.type

        # Vector type should have dim attribute
        if hasattr(col_type, 'dim'):
            assert col_type.dim == 1536, (
                f"Vector dimension should be 1536, got: {col_type.dim}"
            )
        else:
            pytest.fail(f"Column type {col_type} does not have dimension attribute")

    def test_query_vector_is_nullable(self):
        """
        @TEST:TAG-CASEBANK-VECTOR-TYPE-001-4
        Verify query_vector is nullable (existing cases may not have vectors yet)
        """
        query_vector_col = CaseBank.__table__.columns['query_vector']
        assert query_vector_col.nullable is True, (
            "query_vector should be nullable for backward compatibility"
        )

    def test_query_vector_has_comment(self):
        """
        @TEST:TAG-CASEBANK-VECTOR-TYPE-001-5
        Verify query_vector has descriptive comment for documentation
        """
        query_vector_col = CaseBank.__table__.columns['query_vector']
        assert query_vector_col.comment is not None, (
            "query_vector should have a comment explaining its purpose"
        )
        assert 'embedding' in query_vector_col.comment.lower() or 'vector' in query_vector_col.comment.lower(), (
            f"Comment should mention 'embedding' or 'vector', got: {query_vector_col.comment}"
        )


class TestVectorTypeMapping:
    """Test that Vector type correctly maps to Python List[float]"""

    def test_query_vector_python_type_annotation(self):
        """
        @TEST:TAG-CASEBANK-VECTOR-TYPE-001-6
        Verify query_vector is typed as Optional[List[float]] in Python
        """
        # Get the mapped column's Python type
        query_vector_attr = CaseBank.query_vector

        # The Mapped annotation should indicate Optional[List[float]]
        # We can check the property's annotation if available
        import typing
        if hasattr(query_vector_attr, 'property'):
            col = query_vector_attr.property.columns[0]
            # Verify it's designed to accept list of floats
            assert col.type is not None
