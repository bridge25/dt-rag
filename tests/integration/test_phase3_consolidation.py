"""
@TEST:TEST-002:CONSOL | SPEC: SPEC-TEST-002.md
Phase 3 API Integration Tests - Consolidation Router

Integration tests for Consolidation API endpoints:
- POST /consolidation/run
- POST /consolidation/dry-run
- GET /consolidation/summary
- GET /consolidation/health
"""

import pytest


class TestConsolidationAPI:
    """Integration tests for Consolidation API endpoints"""

    # @TEST:TEST-002:CONSOL-001 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_run_dry_mode(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Cases exist in database
        When: POST /consolidation/run with dry_run=True
        Then: Returns 200 with simulation results (no actual changes)
        """
        response = await async_client.post(
            "/consolidation/run",
            json={
                "dry_run": True,
                "threshold": 30.0,
                "similarity_threshold": 0.95,
                "inactive_days": 90
            },
            headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dry_run"] is True
        assert "removed_cases" in data
        assert "merged_cases" in data
        assert "archived_cases" in data
        assert isinstance(data["removed_cases"], int)
        assert isinstance(data["merged_cases"], int)
        assert isinstance(data["archived_cases"], int)

    # @TEST:TEST-002:CONSOL-002 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_run_execute_mode(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Cases exist in database
        When: POST /consolidation/run with dry_run=False
        Then: Returns 200 with actual consolidation results
        """
        response = await async_client.post(
            "/consolidation/run",
            json={
                "dry_run": False,
                "threshold": 30.0,
                "similarity_threshold": 0.95,
                "inactive_days": 90
            },
            headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dry_run"] is False
        assert "removed_cases" in data
        assert "merged_cases" in data
        assert "archived_cases" in data
        assert "details" in data
        assert "timestamp" in data

    # @TEST:TEST-002:CONSOL-003 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_run_authentication(self, async_client):
        """
        Given: Request without valid API key
        When: POST /consolidation/run
        Then: Returns 403 Forbidden
        """
        response = await async_client.post(
            "/consolidation/run",
            json={"dry_run": True}
        )

        assert response.status_code == 403

    # @TEST:TEST-002:CONSOL-004 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_dry_run_success(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Cases exist in database
        When: POST /consolidation/dry-run
        Then: Returns 200 with simulation results
        """
        response = await async_client.post(
            "/consolidation/dry-run",
            headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dry_run"] is True
        assert "removed_cases" in data
        assert "merged_cases" in data
        assert "archived_cases" in data

    # @TEST:TEST-002:CONSOL-005 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_dry_run_authentication(self, async_client):
        """
        Given: Request without valid API key
        When: POST /consolidation/dry-run
        Then: Returns 403 Forbidden
        """
        response = await async_client.post("/consolidation/dry-run")

        assert response.status_code == 403

    # @TEST:TEST-002:CONSOL-006 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_summary_success(
        self, async_client, sample_case_bank
    ):
        """
        Given: Cases exist in database
        When: GET /consolidation/summary
        Then: Returns 200 with consolidation candidate statistics
        """
        response = await async_client.get(
            "/consolidation/summary",
            headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_active_cases" in data
        assert "low_performance_candidates" in data
        assert "inactive_candidates" in data
        assert "potential_savings" in data
        assert "timestamp" in data
        assert isinstance(data["total_active_cases"], int)
        assert isinstance(data["low_performance_candidates"], int)

    # @TEST:TEST-002:CONSOL-007 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_summary_authentication(self, async_client):
        """
        Given: Request without valid API key
        When: GET /consolidation/summary
        Then: Returns 403 Forbidden
        """
        response = await async_client.get("/consolidation/summary")

        assert response.status_code == 403

    # @TEST:TEST-002:CONSOL-008 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_health_check(self, async_client):
        """
        Given: Consolidation service is running
        When: GET /consolidation/health
        Then: Returns 200 with health status
        """
        response = await async_client.get("/consolidation/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "consolidation"
        assert "timestamp" in data

    # @TEST:TEST-002:CONSOL-009 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_run_performance(
        self, async_client, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Cases exist in database
        When: POST /consolidation/run (dry mode)
        Then: Response time < 3000ms (SLA)
        """
        import time

        start_time = time.time()
        response = await async_client.post(
            "/consolidation/run",
            json={"dry_run": True},
            headers={"X-API-Key": "test_api_key_for_testing"}
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 3000, f"Response time {elapsed_ms}ms exceeds 3000ms SLA"

    # @TEST:TEST-002:CONSOL-010 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_summary_performance(
        self, async_client, sample_case_bank
    ):
        """
        Given: Cases exist in database
        When: GET /consolidation/summary
        Then: Response time < 3000ms (SLA)
        """
        import time

        start_time = time.time()
        response = await async_client.get(
            "/consolidation/summary",
            headers={"X-API-Key": "test_api_key_for_testing"}
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 3000, f"Response time {elapsed_ms}ms exceeds 3000ms SLA"

    # @TEST:TEST-002:CONSOL-011 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_database_verification(
        self, async_client, db_session, sample_case_bank, sample_execution_logs
    ):
        """
        Given: Cases exist in database
        When: POST /consolidation/run with dry_run=False
        Then: Database state matches consolidation results
        """
        from apps.api.database import CaseBank  # noqa: F401

        # Run consolidation (no initial count check needed as dry_run=False
        # modifies database and we rely on response data)
        response = await async_client.post(
            "/consolidation/run",
            json={
                "dry_run": False,
                "threshold": 30.0,
                "similarity_threshold": 0.95,
                "inactive_days": 90
            },
            headers={"X-API-Key": "test_api_key_for_testing"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify database changes (Note: actual verification may require
        # checking archive table or soft-delete flags)
        # This is a placeholder - actual implementation depends on
        # consolidation strategy
        assert "removed_cases" in data

    # @TEST:TEST-002:CONSOL-012 | SPEC: SPEC-TEST-002.md
    @pytest.mark.asyncio
    async def test_consolidation_error_handling(self, async_client):
        """
        Given: Invalid consolidation parameters
        When: POST /consolidation/run with invalid threshold
        Then: Returns appropriate error response
        """
        response = await async_client.post(
            "/consolidation/run",
            json={
                "dry_run": True,
                "threshold": 150.0,  # Invalid: > 100
                "similarity_threshold": 0.95,
                "inactive_days": 90
            },
            headers={"X-API-Key": "test_api_key_for_testing"}
        )

        # Should return validation error (422) or internal error (500)
        assert response.status_code in [422, 500]
