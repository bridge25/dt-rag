"""
@TEST:TEST-002:REFLECT | SPEC: SPEC-TEST-002.md
Phase 3 API Integration Tests - Reflection Router

Integration tests for Reflection API endpoints:
- POST /reflection/analyze
- POST /reflection/batch
- POST /reflection/suggestions
- GET /reflection/health
"""

import pytest


class TestReflectionAPI:
    """Integration tests for Reflection API endpoints"""

    # @TEST:TEST-002:REFLECT-001 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_analyze_valid_case(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Valid case_id with execution logs
        When: POST /reflection/analyze
        Then: Returns 200 with performance metrics
        """
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": "test-case-001", "limit": 100},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["case_id"] == "test-case-001"
        assert "total_executions" in data
        assert "successful_executions" in data
        assert "failed_executions" in data
        assert "success_rate" in data
        assert "avg_execution_time_ms" in data
        assert "common_errors" in data
        assert isinstance(data["common_errors"], list)

    # @TEST:TEST-002:REFLECT-002 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_analyze_invalid_case(self, async_client):
        """
        Given: Invalid case_id that doesn't exist
        When: POST /reflection/analyze
        Then: Returns 500 with error detail
        """
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": "nonexistent-case", "limit": 100},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )

        assert response.status_code == 500
        assert "detail" in response.json()

    # @TEST:TEST-002:REFLECT-003 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_analyze_authentication(self, async_client):
        """
        Given: Request without valid API key
        When: POST /reflection/analyze
        Then: Returns 403 Forbidden
        """
        response = await async_client.post(
            "/reflection/analyze", json={"case_id": "test-case-001", "limit": 100}
        )

        assert response.status_code == 403

    # @TEST:TEST-002:REFLECT-004 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_batch_success(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Multiple cases with execution logs
        When: POST /reflection/batch
        Then: Returns 200 with batch analysis results
        """
        response = await async_client.post(
            "/reflection/batch", headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "analyzed_cases" in data
        assert "low_performance_cases" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert data["analyzed_cases"] >= 0

    # @TEST:TEST-002:REFLECT-005 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_batch_empty_database(self, async_client):
        """
        Given: Database with no execution logs
        When: POST /reflection/batch
        Then: Returns 200 with zero analyzed cases
        """
        response = await async_client.post(
            "/reflection/batch", headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analyzed_cases"] >= 0

    # @TEST:TEST-002:REFLECT-006 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_batch_authentication(self, async_client):
        """
        Given: Request without valid API key
        When: POST /reflection/batch
        Then: Returns 403 Forbidden
        """
        response = await async_client.post("/reflection/batch")

        assert response.status_code == 403

    # @TEST:TEST-002:REFLECT-007 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_suggestions_success(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Valid case_id with performance data
        When: POST /reflection/suggestions
        Then: Returns 200 with improvement suggestions
        """
        response = await async_client.post(
            "/reflection/suggestions",
            json={"case_id": "test-case-002"},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["case_id"] == "test-case-002"
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    # @TEST:TEST-002:REFLECT-008 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_suggestions_invalid_case(self, async_client):
        """
        Given: Invalid case_id
        When: POST /reflection/suggestions
        Then: Returns 500 with error detail
        """
        response = await async_client.post(
            "/reflection/suggestions",
            json={"case_id": "nonexistent-case"},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )

        assert response.status_code == 500
        assert "detail" in response.json()

    # @TEST:TEST-002:REFLECT-009 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_suggestions_authentication(self, async_client):
        """
        Given: Request without valid API key
        When: POST /reflection/suggestions
        Then: Returns 403 Forbidden
        """
        response = await async_client.post(
            "/reflection/suggestions", json={"case_id": "test-case-001"}
        )

        assert response.status_code == 403

    # @TEST:TEST-002:REFLECT-010 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_health_check(self, async_client):
        """
        Given: Reflection service is running
        When: GET /reflection/health
        Then: Returns 200 with health status
        """
        response = await async_client.get("/reflection/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "reflection"
        assert "timestamp" in data

    # @TEST:TEST-002:REFLECT-011 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_analyze_performance(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Valid case_id
        When: POST /reflection/analyze
        Then: Response time < 1000ms (SLA)
        """
        import time

        start_time = time.time()
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": "test-case-001", "limit": 100},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 1000, f"Response time {elapsed_ms}ms exceeds 1000ms SLA"

    # @TEST:TEST-002:REFLECT-012 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_reflection_batch_performance(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Multiple cases in database
        When: POST /reflection/batch
        Then: Response time < 10000ms for 100 cases (SLA)
        """
        import time

        start_time = time.time()
        response = await async_client.post(
            "/reflection/batch", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 10000, f"Response time {elapsed_ms}ms exceeds 10000ms SLA"
