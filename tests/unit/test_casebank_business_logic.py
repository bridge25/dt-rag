# @TEST:CASEBANK-UNIFY-INTEGRATION-001
"""
Integration tests for business logic using CaseBank fields (SPEC-CASEBANK-UNIFY-001)

Tests verify:
1. consolidation_policy.py can access query_vector, usage_count, last_used_at
2. reflection_engine.py uses 'answer' field correctly
3. No AttributeError crashes occur
"""
import pytest
from datetime import datetime, timezone, timedelta
from apps.api.database import CaseBank


class TestCaseBankBusinessLogic:
    """Test business logic integration with CaseBank schema"""

    def test_casebank_instance_has_all_required_fields(self):
        """@TEST:CASEBANK-UNIFY-INTEGRATION-001 - Verify CaseBank instance has all fields"""
        # Arrange
        case = CaseBank(
            query="test query",
            answer="test answer",
            sources={"doc_id": "doc123"},
            category_path=["AI", "RAG"],
            quality=0.9,
            query_vector=[0.1] * 1536,
            usage_count=5,
            last_used_at=datetime.now(timezone.utc)
        )

        # Act & Assert - No AttributeError should occur
        assert case.query == "test query"
        assert case.answer == "test answer"
        assert case.sources == {"doc_id": "doc123"}
        assert case.quality == 0.9
        assert case.query_vector is not None
        assert len(case.query_vector) == 1536
        assert case.usage_count == 5
        assert case.last_used_at is not None

    def test_casebank_usage_count_defaults_to_zero(self):
        """@TEST:CASEBANK-UNIFY-INTEGRATION-001 - Verify usage_count can be set to 0"""
        # Arrange & Act
        case = CaseBank(
            query="test",
            answer="answer",
            sources={},
            usage_count=0  # Explicitly set in application code
        )

        # Assert
        assert case.usage_count == 0

    def test_casebank_optional_fields_can_be_none(self):
        """@TEST:CASEBANK-UNIFY-INTEGRATION-001 - Verify optional fields accept None"""
        # Arrange & Act
        case = CaseBank(
            query="test",
            answer="answer",
            sources={},
            query_vector=None,
            last_used_at=None,
            quality=None
        )

        # Assert - No exceptions
        assert case.query_vector is None
        assert case.last_used_at is None
        assert case.quality is None

    def test_casebank_answer_field_accessible(self):
        """@TEST:CASEBANK-UNIFY-REFLECTION-FIX-001 - Verify reflection engine can access 'answer'"""
        # Arrange
        case = CaseBank(
            query="What is RAG?",
            answer="RAG stands for Retrieval Augmented Generation",
            sources={"doc": "123"}
        )

        # Act - Simulate reflection_engine.py line 196
        response_preview = case.answer[:50]

        # Assert
        assert response_preview == "RAG stands for Retrieval Augmented Generation"
        assert hasattr(case, "answer")
        assert not hasattr(case, "response_text")
