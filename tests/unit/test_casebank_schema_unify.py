# @TEST:CASEBANK-UNIFY-001
"""
Unit tests for CaseBank schema unification (SPEC-CASEBANK-UNIFY-001)

Tests verify:
1. Production model has all required fields
2. Field names match between model and migration
3. Business logic can access all fields without AttributeError
"""
import pytest
from sqlalchemy import inspect
from apps.api.database import CaseBank


class TestCaseBankSchemaUnification:
    """Test suite for SPEC-CASEBANK-UNIFY-001"""

    def test_casebank_has_query_vector_field(self):
        """@TEST:CASEBANK-UNIFY-UNIT-001 - Verify query_vector field exists"""
        # RED: This should fail because database.py doesn't have query_vector yet
        mapper = inspect(CaseBank)
        column_names = [col.key for col in mapper.columns]
        assert "query_vector" in column_names, "CaseBank model missing query_vector field"

    def test_casebank_has_usage_count_field(self):
        """@TEST:CASEBANK-UNIFY-UNIT-001 - Verify usage_count field exists"""
        # RED: This should fail because database.py doesn't have usage_count yet
        mapper = inspect(CaseBank)
        column_names = [col.key for col in mapper.columns]
        assert "usage_count" in column_names, "CaseBank model missing usage_count field"

    def test_casebank_has_last_used_at_field(self):
        """@TEST:CASEBANK-UNIFY-UNIT-001 - Verify last_used_at field exists"""
        # RED: This should fail because database.py doesn't have last_used_at yet
        mapper = inspect(CaseBank)
        column_names = [col.key for col in mapper.columns]
        assert "last_used_at" in column_names, "CaseBank model missing last_used_at field"

    def test_casebank_uses_answer_not_response_text(self):
        """@TEST:CASEBANK-UNIFY-UNIT-001 - Verify field name is 'answer' not 'response_text'"""
        mapper = inspect(CaseBank)
        column_names = [col.key for col in mapper.columns]
        assert "answer" in column_names, "CaseBank model should use 'answer' field"
        assert "response_text" not in column_names, "CaseBank model should NOT have 'response_text'"

    def test_casebank_uses_quality_not_quality_score(self):
        """@TEST:CASEBANK-UNIFY-UNIT-001 - Verify field name is 'quality' not 'quality_score'"""
        mapper = inspect(CaseBank)
        column_names = [col.key for col in mapper.columns]
        assert "quality" in column_names, "CaseBank model should use 'quality' field"
        assert "quality_score" not in column_names, "CaseBank model should NOT have 'quality_score'"

    def test_casebank_has_sources_field(self):
        """@TEST:CASEBANK-UNIFY-UNIT-001 - Verify sources field exists"""
        mapper = inspect(CaseBank)
        column_names = [col.key for col in mapper.columns]
        assert "sources" in column_names, "CaseBank model missing sources field"
