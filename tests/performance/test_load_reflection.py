"""
Load tests for Reflection API endpoints
@TEST:TEST-003:LOAD-REFLECTION | SPEC: SPEC-TEST-003.md

Tests concurrent user load scenarios:
- 10 concurrent users (baseline)
- 50 concurrent users (medium load)
- 100 concurrent users (high load)

Performance targets:
- P95 latency within SLA under load
- Error rate < 1% (50 users), < 5% (100 users)
- System remains stable for test duration
"""
import pytest
import asyncio
import time
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class LoadTestResult:
    """Load test result metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    requests_per_second: float


async def run_concurrent_requests(
    async_client,
    endpoint: str,
    num_users: int,
    duration_seconds: int = 60,
    payload: dict = None,
) -> LoadTestResult:
    """
    Run concurrent load test for specified endpoint

    Args:
        async_client: AsyncClient instance
        endpoint: API endpoint path
        num_users: Number of concurrent users
        duration_seconds: Test duration
        payload: Request JSON payload

    Returns:
        LoadTestResult with performance metrics
    """
    start_time = time.perf_counter()
    end_time = start_time + duration_seconds

    timings = []
    errors = []
    successful = 0
    failed = 0

    async def make_request():
        """Single user request"""
        nonlocal successful, failed

        while time.perf_counter() < end_time:
            req_start = time.perf_counter()
            try:
                if payload:
                    response = await async_client.post(
                        endpoint,
                        json=payload,
                        headers={"X-API-Key": "test_api_key_for_testing"}
                    )
                else:
                    response = await async_client.post(
                        endpoint,
                        headers={"X-API-Key": "test_api_key_for_testing"}
                    )
                req_end = time.perf_counter()

                if response.status_code == 200:
                    successful += 1
                    timings.append((req_end - req_start) * 1000)
                else:
                    failed += 1
                    errors.append(f"HTTP {response.status_code}")
            except Exception as e:
                failed += 1
                errors.append(str(e))

            # Small delay to simulate realistic user behavior
            await asyncio.sleep(0.1)

    # Run concurrent users
    tasks = [make_request() for _ in range(num_users)]
    await asyncio.gather(*tasks)

    total_duration = (time.perf_counter() - start_time) * 1000
    total_requests = successful + failed

    if timings:
        import statistics
        p50 = statistics.median(timings)
        p95 = statistics.quantiles(timings, n=20)[18] if len(timings) >= 20 else max(timings)
        p99 = statistics.quantiles(timings, n=100)[98] if len(timings) >= 100 else max(timings)
    else:
        p50 = p95 = p99 = 0

    error_rate = (failed / total_requests * 100) if total_requests > 0 else 0
    rps = total_requests / (total_duration / 1000) if total_duration > 0 else 0

    return LoadTestResult(
        total_requests=total_requests,
        successful_requests=successful,
        failed_requests=failed,
        total_duration_ms=total_duration,
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
        error_rate=error_rate,
        requests_per_second=rps
    )


class TestReflectionLoad:
    """Load tests for Reflection API endpoints"""

    # @TEST:TEST-003:LOAD-REFLECTION-10USERS | SPEC: SPEC-TEST-003.md
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_reflection_analyze_10_users(self, async_client, sample_case_bank, sample_execution_logs):
        """
        Load test: 10 concurrent users on /reflection/analyze

        Target:
        - P95 latency within SLA (< 1s)
        - Error rate < 0.1%
        - System stable for 60 seconds
        """
        result = await run_concurrent_requests(
            async_client,
            "/reflection/analyze",
            num_users=10,
            duration_seconds=60,
            payload={"case_id": "test-case-003", "limit": 100}
        )

        print(f"\n[10 users /reflection/analyze]")
        print(f"  Total requests: {result.total_requests}")
        print(f"  Success: {result.successful_requests}, Failed: {result.failed_requests}")
        print(f"  P50: {result.p50_latency_ms:.2f}ms, P95: {result.p95_latency_ms:.2f}ms, P99: {result.p99_latency_ms:.2f}ms")
        print(f"  Error rate: {result.error_rate:.2f}%")
        print(f"  RPS: {result.requests_per_second:.2f}")

        # Assertions: REQ-5
        assert result.p95_latency_ms < 1000, f"P95 latency {result.p95_latency_ms:.2f}ms exceeds SLA"
        assert result.error_rate < 0.1, f"Error rate {result.error_rate:.2f}% exceeds 0.1%"
        assert result.successful_requests > 0, "No successful requests"

    # @TEST:TEST-003:LOAD-REFLECTION-50USERS | SPEC: SPEC-TEST-003.md
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_reflection_analyze_50_users(self, async_client, sample_case_bank, sample_execution_logs):
        """
        Load test: 50 concurrent users on /reflection/analyze

        Target:
        - P95 latency increase < 50% from baseline
        - Error rate < 1%
        - Database connection pool not exhausted
        """
        result = await run_concurrent_requests(
            async_client,
            "/reflection/analyze",
            num_users=50,
            duration_seconds=60,
            payload={"case_id": "test-case-003", "limit": 100}
        )

        print(f"\n[50 users /reflection/analyze]")
        print(f"  Total requests: {result.total_requests}")
        print(f"  Success: {result.successful_requests}, Failed: {result.failed_requests}")
        print(f"  P50: {result.p50_latency_ms:.2f}ms, P95: {result.p95_latency_ms:.2f}ms, P99: {result.p99_latency_ms:.2f}ms")
        print(f"  Error rate: {result.error_rate:.2f}%")
        print(f"  RPS: {result.requests_per_second:.2f}")

        # Assertions: REQ-6
        assert result.p95_latency_ms < 1500, f"P95 latency {result.p95_latency_ms:.2f}ms exceeds 50% increase target"
        assert result.error_rate < 1.0, f"Error rate {result.error_rate:.2f}% exceeds 1%"
        assert result.successful_requests > 0, "No successful requests"

    # @TEST:TEST-003:LOAD-REFLECTION-100USERS | SPEC: SPEC-TEST-003.md
    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_reflection_analyze_100_users(self, async_client, sample_case_bank, sample_execution_logs):
        """
        Load test: 100 concurrent users on /reflection/analyze

        Target:
        - P95 latency increase < 100% from baseline
        - Error rate < 5%
        - System gracefully degrades (no crash)
        """
        result = await run_concurrent_requests(
            async_client,
            "/reflection/analyze",
            num_users=100,
            duration_seconds=60,
            payload={"case_id": "test-case-003", "limit": 100}
        )

        print(f"\n[100 users /reflection/analyze]")
        print(f"  Total requests: {result.total_requests}")
        print(f"  Success: {result.successful_requests}, Failed: {result.failed_requests}")
        print(f"  P50: {result.p50_latency_ms:.2f}ms, P95: {result.p95_latency_ms:.2f}ms, P99: {result.p99_latency_ms:.2f}ms")
        print(f"  Error rate: {result.error_rate:.2f}%")
        print(f"  RPS: {result.requests_per_second:.2f}")

        # Assertions: REQ-7
        assert result.p95_latency_ms < 2000, f"P95 latency {result.p95_latency_ms:.2f}ms exceeds 100% increase target"
        assert result.error_rate < 5.0, f"Error rate {result.error_rate:.2f}% exceeds 5%"
        assert result.successful_requests > 0, "System crashed - no successful requests"
