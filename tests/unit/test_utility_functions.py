"""
Unit tests for utility functions and helper modules

This test module provides comprehensive coverage for utility functions,
helper methods, and common functionality used across the DT-RAG system.
"""

import pytest
import json
import uuid
import hashlib
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# Mock data and utility functions for testing
def validate_uuid_format(value: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def calculate_hash(data: str) -> str:
    """Calculate SHA-256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime"""
    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re

    # Remove dangerous characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Limit length
    return safe_filename[:255]


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def parse_query_string(query_string: str) -> Dict[str, Any]:
    """Parse query string into dictionary"""
    from urllib.parse import parse_qs

    parsed = parse_qs(query_string, keep_blank_values=True)

    # Convert single-item lists to strings
    result = {}
    for key, value_list in parsed.items():
        if len(value_list) == 1:
            result[key] = value_list[0]
        else:
            result[key] = value_list

    return result


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying functions on failure"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2**attempt))  # Exponential backoff
            return None

        return wrapper

    return decorator


class TestUtilityFunctions:
    """Test cases for utility functions"""

    @pytest.mark.unit
    def test_validate_uuid_format_valid(self):
        """Test UUID validation with valid UUIDs"""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000",
            str(uuid.uuid4()),
            str(uuid.uuid1()),
        ]

        for uuid_str in valid_uuids:
            assert validate_uuid_format(uuid_str) is True

    @pytest.mark.unit
    def test_validate_uuid_format_invalid(self):
        """Test UUID validation with invalid UUIDs"""
        invalid_uuids = [
            "invalid-uuid",
            "123e4567-e89b-12d3-a456-42661417400",  # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
            "",
            "not-a-uuid-at-all",
            "12345678-1234-1234-1234-123456789012g",  # Invalid character
        ]

        for uuid_str in invalid_uuids:
            assert validate_uuid_format(uuid_str) is False

    @pytest.mark.unit
    def test_calculate_hash_consistency(self):
        """Test hash calculation consistency"""
        test_data = "test data for hashing"

        hash1 = calculate_hash(test_data)
        hash2 = calculate_hash(test_data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in hash1)

    @pytest.mark.unit
    def test_calculate_hash_different_data(self):
        """Test hash calculation produces different hashes for different data"""
        data1 = "first test data"
        data2 = "second test data"

        hash1 = calculate_hash(data1)
        hash2 = calculate_hash(data2)

        assert hash1 != hash2
        assert len(hash1) == len(hash2) == 64

    @pytest.mark.unit
    def test_calculate_hash_empty_string(self):
        """Test hash calculation for empty string"""
        empty_hash = calculate_hash("")

        assert len(empty_hash) == 64
        assert (
            empty_hash
            == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    @pytest.mark.unit
    def test_format_timestamp(self):
        """Test timestamp formatting"""
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)

        formatted = format_timestamp(dt)

        assert isinstance(formatted, str)
        assert "2024-01-15" in formatted
        assert "10:30:45" in formatted
        assert formatted == "2024-01-15T10:30:45.123456"

    @pytest.mark.unit
    def test_parse_timestamp(self):
        """Test timestamp parsing"""
        timestamp_str = "2024-01-15T10:30:45.123456"

        parsed = parse_timestamp(timestamp_str)

        assert isinstance(parsed, datetime)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30
        assert parsed.second == 45

    @pytest.mark.unit
    def test_parse_timestamp_with_timezone(self):
        """Test timestamp parsing with timezone"""
        timestamp_str = "2024-01-15T10:30:45Z"

        parsed = parse_timestamp(timestamp_str)

        assert isinstance(parsed, datetime)
        assert parsed.year == 2024

    @pytest.mark.unit
    def test_timestamp_round_trip(self):
        """Test timestamp format and parse round trip"""
        original_dt = datetime.now()

        formatted = format_timestamp(original_dt)
        parsed = parse_timestamp(formatted)

        # Should be very close (microsecond precision)
        assert abs((original_dt - parsed).total_seconds()) < 1

    @pytest.mark.unit
    def test_sanitize_filename_dangerous_chars(self):
        """Test filename sanitization removes dangerous characters"""
        dangerous_filename = 'test<>:"/\\|?*.txt'

        safe_filename = sanitize_filename(dangerous_filename)

        assert safe_filename == "test_________.txt"
        assert all(c not in '<>:"/\\|?*' for c in safe_filename)

    @pytest.mark.unit
    def test_sanitize_filename_long_filename(self):
        """Test filename sanitization limits length"""
        long_filename = "a" * 300 + ".txt"

        safe_filename = sanitize_filename(long_filename)

        assert len(safe_filename) <= 255

    @pytest.mark.unit
    def test_sanitize_filename_normal_filename(self):
        """Test filename sanitization preserves normal filenames"""
        normal_filename = "document_2024_01_15.pdf"

        safe_filename = sanitize_filename(normal_filename)

        assert safe_filename == normal_filename

    @pytest.mark.unit
    def test_calculate_similarity_identical_texts(self):
        """Test similarity calculation for identical texts"""
        text = "machine learning algorithms"

        similarity = calculate_similarity(text, text)

        assert similarity == 1.0

    @pytest.mark.unit
    def test_calculate_similarity_completely_different(self):
        """Test similarity calculation for completely different texts"""
        text1 = "machine learning algorithms"
        text2 = "database query optimization"

        similarity = calculate_similarity(text1, text2)

        assert similarity == 0.0

    @pytest.mark.unit
    def test_calculate_similarity_partial_match(self):
        """Test similarity calculation for partially matching texts"""
        text1 = "machine learning algorithms"
        text2 = "machine learning systems"

        similarity = calculate_similarity(text1, text2)

        assert 0.0 < similarity < 1.0
        assert similarity == 2 / 4  # "machine" and "learning" are common

    @pytest.mark.unit
    def test_calculate_similarity_empty_texts(self):
        """Test similarity calculation for empty texts"""
        similarity_both_empty = calculate_similarity("", "")
        similarity_one_empty = calculate_similarity("test", "")

        assert similarity_both_empty == 1.0
        assert similarity_one_empty == 0.0

    @pytest.mark.unit
    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes"""
        sizes_and_expected = [
            (0, "0 B"),
            (1, "1.0 B"),
            (512, "512.0 B"),
            (1023, "1023.0 B"),
        ]

        for size_bytes, expected in sizes_and_expected:
            assert format_file_size(size_bytes) == expected

    @pytest.mark.unit
    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobytes"""
        sizes_and_expected = [
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (2048, "2.0 KB"),
        ]

        for size_bytes, expected in sizes_and_expected:
            assert format_file_size(size_bytes) == expected

    @pytest.mark.unit
    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabytes"""
        sizes_and_expected = [
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 2.5, "2.5 MB"),
            (1024 * 1024 * 1000, "1000.0 MB"),
        ]

        for size_bytes, expected in sizes_and_expected:
            result = format_file_size(int(size_bytes))
            assert result == expected

    @pytest.mark.unit
    def test_format_file_size_large_sizes(self):
        """Test file size formatting for large sizes"""
        gb_size = 1024 * 1024 * 1024
        tb_size = gb_size * 1024

        gb_result = format_file_size(gb_size)
        tb_result = format_file_size(tb_size)

        assert "GB" in gb_result
        assert "TB" in tb_result

    @pytest.mark.unit
    def test_parse_query_string_simple(self):
        """Test query string parsing for simple parameters"""
        query_string = "param1=value1&param2=value2"

        result = parse_query_string(query_string)

        assert result == {"param1": "value1", "param2": "value2"}

    @pytest.mark.unit
    def test_parse_query_string_multiple_values(self):
        """Test query string parsing with multiple values for same parameter"""
        query_string = "tags=python&tags=programming&tags=web"

        result = parse_query_string(query_string)

        assert result["tags"] == ["python", "programming", "web"]

    @pytest.mark.unit
    def test_parse_query_string_empty_values(self):
        """Test query string parsing with empty values"""
        query_string = "param1=&param2=value2&param3="

        result = parse_query_string(query_string)

        assert result["param1"] == ""
        assert result["param2"] == "value2"
        assert result["param3"] == ""

    @pytest.mark.unit
    def test_parse_query_string_url_encoded(self):
        """Test query string parsing with URL-encoded values"""
        query_string = "search=hello%20world&category=machine%20learning"

        result = parse_query_string(query_string)

        assert result["search"] == "hello world"
        assert result["category"] == "machine learning"

    @pytest.mark.unit
    def test_retry_on_failure_decorator_success_first_try(self):
        """Test retry decorator when function succeeds on first try"""

        @retry_on_failure(max_retries=3)
        def successful_function():
            return "success"

        result = successful_function()

        assert result == "success"

    @pytest.mark.unit
    def test_retry_on_failure_decorator_success_after_retries(self):
        """Test retry decorator when function succeeds after failures"""
        call_count = 0

        @retry_on_failure(max_retries=3, delay=0.01)  # Very short delay for testing
        def function_fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success after retries"

        result = function_fails_twice()

        assert result == "success after retries"
        assert call_count == 3

    @pytest.mark.unit
    def test_retry_on_failure_decorator_all_attempts_fail(self):
        """Test retry decorator when all attempts fail"""

        @retry_on_failure(max_retries=2, delay=0.01)
        def always_failing_function():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_failing_function()


class TestDataStructureHelpers:
    """Test cases for data structure helper functions"""

    @pytest.mark.unit
    def test_deep_merge_dictionaries(self):
        """Test deep merging of dictionaries"""

        def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
            """Deep merge two dictionaries"""
            result = dict1.copy()

            for key, value in dict2.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value

            return result

        dict1 = {"a": 1, "b": {"c": 2, "d": 3}}

        dict2 = {"b": {"d": 4, "e": 5}, "f": 6}

        merged = deep_merge(dict1, dict2)

        expected = {
            "a": 1,
            "b": {"c": 2, "d": 4, "e": 5},  # Overwritten  # Added
            "f": 6,
        }

        assert merged == expected

    @pytest.mark.unit
    def test_flatten_dictionary(self):
        """Test flattening nested dictionaries"""

        def flatten_dict(
            d: Dict[str, Any], parent_key: str = "", sep: str = "."
        ) -> Dict[str, Any]:
            """Flatten nested dictionary"""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        nested_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3}}, "f": 4}

        flattened = flatten_dict(nested_dict)

        expected = {"a": 1, "b.c": 2, "b.d.e": 3, "f": 4}

        assert flattened == expected

    @pytest.mark.unit
    def test_filter_dict_by_keys(self):
        """Test filtering dictionary by keys"""

        def filter_dict_by_keys(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
            """Filter dictionary to only include specified keys"""
            return {k: v for k, v in d.items() if k in keys}

        original_dict = {
            "name": "John",
            "age": 30,
            "email": "john@example.com",
            "password": "secret123",
            "internal_id": "xyz789",
        }

        public_keys = ["name", "age", "email"]
        filtered = filter_dict_by_keys(original_dict, public_keys)

        expected = {"name": "John", "age": 30, "email": "john@example.com"}

        assert filtered == expected
        assert "password" not in filtered
        assert "internal_id" not in filtered

    @pytest.mark.unit
    def test_group_by_key(self):
        """Test grouping list of dictionaries by key"""

        def group_by_key(
            items: List[Dict[str, Any]], key: str
        ) -> Dict[str, List[Dict[str, Any]]]:
            """Group list of dictionaries by specified key"""
            grouped = {}
            for item in items:
                group_key = item.get(key)
                if group_key not in grouped:
                    grouped[group_key] = []
                grouped[group_key].append(item)
            return grouped

        items = [
            {"name": "Alice", "department": "Engineering", "role": "Developer"},
            {"name": "Bob", "department": "Engineering", "role": "Manager"},
            {"name": "Carol", "department": "Marketing", "role": "Analyst"},
            {"name": "Dave", "department": "Engineering", "role": "Developer"},
        ]

        grouped = group_by_key(items, "department")

        assert len(grouped["Engineering"]) == 3
        assert len(grouped["Marketing"]) == 1
        assert grouped["Engineering"][0]["name"] == "Alice"


class TestValidationHelpers:
    """Test cases for validation helper functions"""

    @pytest.mark.unit
    def test_validate_email_format(self):
        """Test email format validation"""

        def validate_email(email: str) -> bool:
            """Simple email validation"""
            import re

            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return bool(re.match(pattern, email))

        valid_emails = [
            "user@example.com",
            "test.email+tag@domain.co.uk",
            "user123@test-domain.org",
        ]

        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user space@domain.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True

        for email in invalid_emails:
            assert validate_email(email) is False

    @pytest.mark.unit
    def test_validate_json_structure(self):
        """Test JSON structure validation"""

        def validate_json_structure(
            data: Dict[str, Any], required_keys: List[str]
        ) -> bool:
            """Validate that dictionary has required keys"""
            return all(key in data for key in required_keys)

        test_data = {"name": "Test", "age": 25, "email": "test@example.com"}

        assert validate_json_structure(test_data, ["name", "email"]) is True
        assert validate_json_structure(test_data, ["name", "age", "email"]) is True
        assert validate_json_structure(test_data, ["name", "phone"]) is False
        assert validate_json_structure(test_data, []) is True

    @pytest.mark.unit
    def test_validate_range(self):
        """Test numeric range validation"""

        def validate_range(value: float, min_val: float, max_val: float) -> bool:
            """Validate that value is within range"""
            return min_val <= value <= max_val

        assert validate_range(5, 0, 10) is True
        assert validate_range(0, 0, 10) is True
        assert validate_range(10, 0, 10) is True
        assert validate_range(-1, 0, 10) is False
        assert validate_range(11, 0, 10) is False
        assert validate_range(5.5, 5, 6) is True


class TestCacheHelpers:
    """Test cases for cache helper functions"""

    @pytest.mark.unit
    def test_simple_cache_decorator(self):
        """Test simple caching decorator"""
        cache = {}

        def simple_cache(func):
            """Simple cache decorator"""

            def wrapper(*args, **kwargs):
                key = str(args) + str(sorted(kwargs.items()))
                if key not in cache:
                    cache[key] = func(*args, **kwargs)
                return cache[key]

            return wrapper

        call_count = 0

        @simple_cache
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # Second call with same arguments should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment

        # Different arguments should execute function again
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2

    @pytest.mark.unit
    def test_ttl_cache_expiration(self):
        """Test TTL (time-to-live) cache behavior"""

        def create_ttl_cache(ttl_seconds: float = 1.0):
            cache = {}

            def ttl_cache(func):
                def wrapper(*args, **kwargs):
                    key = str(args) + str(sorted(kwargs.items()))
                    current_time = time.time()

                    if key in cache:
                        value, timestamp = cache[key]
                        if current_time - timestamp < ttl_seconds:
                            return value

                    result = func(*args, **kwargs)
                    cache[key] = (result, current_time)
                    return result

                return wrapper

            return ttl_cache

        call_count = 0
        ttl_cache = create_ttl_cache(0.01)  # Very short TTL for testing

        @ttl_cache
        def cached_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = cached_function(5)
        assert result1 == 10
        assert call_count == 1

        # Immediate second call should use cache
        result2 = cached_function(5)
        assert result2 == 10
        assert call_count == 1

        # Wait for TTL to expire
        time.sleep(0.02)

        # Call after TTL should execute function again
        result3 = cached_function(5)
        assert result3 == 10
        assert call_count == 2
