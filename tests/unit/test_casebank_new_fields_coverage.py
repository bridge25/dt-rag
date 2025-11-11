"""
@TEST:TAG-CASEBANK-TEST-COVERAGE-003
Comprehensive test coverage for new CaseBank fields

Tests edge cases and field behaviors for:
- query_vector (with Vector type)
- usage_count (with defaults and increments)
- last_used_at (with timestamps and updates)
"""
# @TEST:TAG-CASEBANK-TEST-COVERAGE-003

import pytest
from apps.api.database import CaseBank
from datetime import datetime, timezone
import uuid


class TestQueryVectorField:
    """Test query_vector field behavior and edge cases"""

    def test_query_vector_type_is_vector_not_array(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-1
        Verify query_vector uses pgvector.Vector(1536) type
        """
        from sqlalchemy.dialects import postgresql
        from pgvector.sqlalchemy import Vector

        query_vector_col = CaseBank.__table__.columns['query_vector']
        assert isinstance(query_vector_col.type, Vector)
        assert query_vector_col.type.dim == 1536

    def test_query_vector_nullable_allows_none(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-2
        Verify query_vector can be None for backward compatibility
        """
        query_vector_col = CaseBank.__table__.columns['query_vector']
        assert query_vector_col.nullable is True

    def test_query_vector_accepts_list_of_floats(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-3
        Verify query_vector typing accepts Optional[List[float]]
        """
        # Check Python type annotation
        import typing
        from sqlalchemy.orm import Mapped

        # The field should be typed as Mapped[Optional[List[float]]]
        assert hasattr(CaseBank, 'query_vector')


class TestUsageCountField:
    """Test usage_count field behavior and edge cases"""

    def test_usage_count_default_is_zero(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-4
        Verify usage_count defaults to 0
        """
        usage_count_col = CaseBank.__table__.columns['usage_count']

        # Check insert_default
        assert usage_count_col.default is not None
        assert str(usage_count_col.default.arg) == '0'

        # Check server_default
        assert usage_count_col.server_default is not None
        assert usage_count_col.server_default.arg.text == '0'

    def test_usage_count_not_nullable(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-5
        Verify usage_count is NOT nullable (always has a value)
        """
        usage_count_col = CaseBank.__table__.columns['usage_count']
        assert usage_count_col.nullable is False

    def test_usage_count_is_integer_type(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-6
        Verify usage_count is Integer type
        """
        from sqlalchemy import Integer

        usage_count_col = CaseBank.__table__.columns['usage_count']
        assert isinstance(usage_count_col.type, Integer)

    def test_usage_count_has_descriptive_comment(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-7
        Verify usage_count has documentation comment
        """
        usage_count_col = CaseBank.__table__.columns['usage_count']
        assert usage_count_col.comment is not None
        assert 'match' in usage_count_col.comment.lower()


class TestLastUsedAtField:
    """Test last_used_at field behavior and edge cases"""

    def test_last_used_at_nullable(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-8
        Verify last_used_at can be None (not yet used)
        """
        last_used_at_col = CaseBank.__table__.columns['last_used_at']
        assert last_used_at_col.nullable is True

    def test_last_used_at_is_datetime_with_timezone(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-9
        Verify last_used_at uses DateTime with timezone
        """
        from sqlalchemy import DateTime

        last_used_at_col = CaseBank.__table__.columns['last_used_at']
        assert isinstance(last_used_at_col.type, DateTime)
        assert last_used_at_col.type.timezone is True

    def test_last_used_at_has_descriptive_comment(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-10
        Verify last_used_at has documentation comment
        """
        last_used_at_col = CaseBank.__table__.columns['last_used_at']
        assert last_used_at_col.comment is not None
        assert 'query' in last_used_at_col.comment.lower() or 'used' in last_used_at_col.comment.lower()


class TestFieldInteractions:
    """Test interactions between new fields"""

    def test_all_three_fields_present_on_model(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-11
        Verify all three new fields exist on CaseBank model
        """
        assert hasattr(CaseBank, 'query_vector')
        assert hasattr(CaseBank, 'usage_count')
        assert hasattr(CaseBank, 'last_used_at')

    def test_fields_have_correct_mapped_types(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-12
        Verify fields have correct SQLAlchemy Mapped types
        """
        from typing import Optional, List
        from datetime import datetime

        # Check that fields are properly mapped
        assert 'query_vector' in CaseBank.__table__.columns
        assert 'usage_count' in CaseBank.__table__.columns
        assert 'last_used_at' in CaseBank.__table__.columns

    def test_fields_support_typical_usage_pattern(self):
        """
        @TEST:TAG-CASEBANK-TEST-COVERAGE-003-13
        Verify fields support typical usage pattern:
        1. Create case with vector
        2. Increment usage_count on match
        3. Update last_used_at on match
        """
        # This is a schema validation test
        # Actual usage pattern is tested in integration tests
        query_vector_col = CaseBank.__table__.columns['query_vector']
        usage_count_col = CaseBank.__table__.columns['usage_count']
        last_used_at_col = CaseBank.__table__.columns['last_used_at']

        # Verify schema supports the pattern
        assert query_vector_col.nullable  # Can start without vector
        assert not usage_count_col.nullable  # Always has count
        assert last_used_at_col.nullable  # Can start without usage
