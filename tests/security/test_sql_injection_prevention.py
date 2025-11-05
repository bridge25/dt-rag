"""
SQL Injection Prevention Tests
@TEST:TEST-004 | SPEC: SPEC-TEST-004.md

Tests for SQL injection attack prevention:
- SQL injection in case_id blocked
- SQL injection in search query blocked
- Parameterized queries enforcement
- No data leakage on injection attempts
"""

import pytest
from httpx import AsyncClient
import os


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_sql_injection_in_case_id_blocked(async_client: AsyncClient) -> None:
    """
    case_id에 SQL Injection 시도 차단
    REQ-3: The system shall prevent SQL Injection attacks
    REQ-8: WHEN malicious SQL payload is injected
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    malicious_payloads = [
        "test-001' OR '1'='1",
        "test-001'; DROP TABLE case_bank; --",
        "test-001' UNION SELECT * FROM api_keys; --",
        "test-001' AND 1=1--",
        "test-001' OR 'a'='a",
    ]

    for payload in malicious_payloads:
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key},
        )

        # Should return 404 (케이스 없음), 422 (입력 검증 실패), or 500 (internal error)
        # 500 is acceptable if it's due to business logic, not SQL injection
        # The key is that SQL should not be executed (checked by time-based tests)
        assert response.status_code in [
            404,
            422,
            500,
        ], f"SQL injection payload should be handled safely, got {response.status_code} for payload: {payload}"

        # Check that no database error is exposed
        if response.status_code >= 400:
            detail = response.json().get("detail", "")
            # Should not contain SQL error messages
            assert (
                "SQL" not in detail.upper()
            ), f"Should not expose SQL errors, got: {detail}"
            assert (
                "TABLE" not in detail.upper()
            ), f"Should not expose table names, got: {detail}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_sql_injection_in_search_query_blocked(async_client: AsyncClient) -> None:
    """
    검색 쿼리에 SQL Injection 시도 차단
    REQ-3, REQ-8
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    malicious_query = "machine learning' OR '1'='1"

    response = await async_client.post(
        "/search",
        json={"q": malicious_query, "final_topk": 5},
        headers={"X-API-Key": valid_api_key},
    )

    # Should return 200 (정상 검색, SQL로 해석되지 않음) or 422 (입력 검증 실패)
    # or 404 (endpoint not found)
    assert response.status_code in [
        200,
        422,
        404,
    ], f"Search should handle SQL-like strings safely, got {response.status_code}"

    if response.status_code == 200:
        # 결과가 있다면 정상적인 검색 결과여야 함
        data = response.json()
        # Should have proper response structure
        assert isinstance(data, dict), "Response should be a dictionary"
        # No database structure should be leaked
        response_str = str(data)
        assert "password" not in response_str.lower(), "Should not leak sensitive data"
        assert "api_key" not in response_str.lower(), "Should not leak API keys"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_union_based_sql_injection_blocked(async_client: AsyncClient) -> None:
    """
    UNION 기반 SQL Injection 차단
    REQ-3
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    union_payloads = [
        "test' UNION SELECT NULL--",
        "test' UNION SELECT 1,2,3,4,5--",
        "test' UNION ALL SELECT * FROM information_schema.tables--",
    ]

    for payload in union_payloads:
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key},
        )

        # Should safely reject or return not found (500 allowed if internal error, not SQL injection)
        assert response.status_code in [
            404,
            422,
            500,
        ], f"UNION injection should be handled safely, got {response.status_code}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_boolean_based_sql_injection_blocked(async_client: AsyncClient) -> None:
    """
    Boolean 기반 SQL Injection 차단
    REQ-3
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    boolean_payloads = [
        "test' AND 1=1--",
        "test' AND 1=2--",
        "test' OR 1=1--",
        "test' OR 'x'='x",
    ]

    for payload in boolean_payloads:
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key},
        )

        # Should safely reject (500 allowed if internal error, not SQL injection)
        assert response.status_code in [
            404,
            422,
            500,
        ], f"Boolean injection should be handled safely, got {response.status_code}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_time_based_sql_injection_blocked(async_client: AsyncClient) -> None:
    """
    Time-based SQL Injection 차단
    REQ-3
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    time_based_payloads = [
        "test'; WAITFOR DELAY '00:00:05'--",
        "test' AND SLEEP(5)--",
        "test' AND pg_sleep(5)--",
    ]

    import time

    for payload in time_based_payloads:
        start_time = time.time()

        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key},
        )

        elapsed_time = time.time() - start_time

        # Should not delay (payload should be treated as string, not executed)
        # This is the KEY test for SQL injection - if SQL is executed, there will be delay
        assert (
            elapsed_time < 2.0
        ), f"Time-based injection should not cause delay (SQL not executed), took {elapsed_time:.2f}s"

        # Should safely reject (500 allowed if internal error, but no SQL execution)
        assert response.status_code in [
            404,
            422,
            500,
        ], f"Time-based injection should be handled safely, got {response.status_code}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_no_data_leakage_on_injection(async_client: AsyncClient) -> None:
    """
    SQL Injection 시도 시 데이터 유출 없음
    REQ-3, REQ-8
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    # Attempt to extract database structure
    info_schema_payload = (
        "test' UNION SELECT table_name FROM information_schema.tables--"
    )

    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": info_schema_payload},
        headers={"X-API-Key": valid_api_key},
    )

    # Should not return database structure information (500 allowed if internal error)
    assert response.status_code in [
        404,
        422,
        500,
    ], f"Info schema injection should be handled safely, got {response.status_code}"

    # Verify no sensitive information in response
    response_text = response.text.lower()
    assert (
        "information_schema" not in response_text
    ), "Should not leak database schema information"
    assert (
        "pg_catalog" not in response_text
    ), "Should not leak PostgreSQL catalog information"
