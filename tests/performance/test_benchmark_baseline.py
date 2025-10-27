"""
Performance baseline benchmarks for Phase 3 API endpoints
@TEST:TEST-003:BENCHMARK-BASELINE | SPEC: SPEC-TEST-003.md

Tests the performance of:
- Reflection /analyze (target: P50 < 500ms)
- Reflection /batch (target: P50 < 5s)
- Consolidation /run (target: P50 < 1.5s)
- Consolidation /dry-run (target: P50 < 1s)

Note: Using manual time measurement instead of pytest-benchmark
      since it doesn't support async functions well.
"""

import pytest
import time
import statistics


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_reflection_analyze_benchmark(
    async_client, sample_case_bank, sample_execution_logs
):
    """
    Benchmark: Reflection /analyze endpoint
    @TEST:TEST-003:BENCHMARK-BASELINE:REFLECTION-ANALYZE

    Target: P50 < 500ms
    """
    timings = []
    num_iterations = 10

    # Warm-up request
    await async_client.post(
        "/reflection/analyze",
        json={"case_id": "test-case-003", "limit": 100},
        headers={"X-API-Key": "test_api_key_for_testing"},
    )

    # Actual benchmark iterations
    for _ in range(num_iterations):
        start = time.perf_counter()
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": "test-case-003", "limit": 100},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        end = time.perf_counter()
        timings.append((end - start) * 1000)  # Convert to ms

        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert data["case_id"] == "test-case-003"

    # Calculate performance metrics
    p50 = statistics.median(timings)
    p95 = (
        statistics.quantiles(timings, n=20)[18] if len(timings) >= 20 else max(timings)
    )
    p99 = (
        statistics.quantiles(timings, n=100)[98]
        if len(timings) >= 100
        else max(timings)
    )

    print(
        f"\n[Reflection /analyze] P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms"
    )

    # Assert SLA: P50 < 500ms
    assert p50 < 500, f"P50 latency {p50:.2f}ms exceeds target of 500ms"


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_reflection_batch_benchmark(
    async_client, sample_case_bank, sample_execution_logs
):
    """
    Benchmark: Reflection /batch endpoint
    @TEST:TEST-003:BENCHMARK-BASELINE:REFLECTION-BATCH

    Target: P50 < 5s (for processing low-performing cases)
    """
    timings = []
    num_iterations = 5  # Fewer iterations for slower endpoint

    # Warm-up request
    await async_client.post(
        "/reflection/batch", headers={"X-API-Key": "test_api_key_for_testing"}
    )

    # Actual benchmark iterations
    for _ in range(num_iterations):
        start = time.perf_counter()
        response = await async_client.post(
            "/reflection/batch", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        end = time.perf_counter()
        timings.append((end - start) * 1000)  # Convert to ms

        assert response.status_code == 200
        data = response.json()
        assert "analyzed_cases" in data
        assert isinstance(data["analyzed_cases"], int)

    # Calculate performance metrics
    p50 = statistics.median(timings)
    p95 = max(timings)  # With 5 iterations, P95 ≈ max
    p99 = max(timings)

    print(f"\n[Reflection /batch] P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")

    # Assert SLA: P50 < 5000ms
    assert p50 < 5000, f"P50 latency {p50:.2f}ms exceeds target of 5000ms"


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_consolidation_run_benchmark(async_client, sample_case_bank):
    """
    Benchmark: Consolidation /run endpoint
    @TEST:TEST-003:BENCHMARK-BASELINE:CONSOLIDATION-RUN

    Target: P50 < 1.5s
    """
    timings = []
    num_iterations = 5  # Fewer iterations for slower endpoint

    # Warm-up request
    await async_client.post(
        "/consolidation/run", headers={"X-API-Key": "test_api_key_for_testing"}
    )

    # Actual benchmark iterations
    for _ in range(num_iterations):
        start = time.perf_counter()
        response = await async_client.post(
            "/consolidation/run", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        end = time.perf_counter()
        timings.append((end - start) * 1000)  # Convert to ms

        assert response.status_code == 200
        data = response.json()
        assert "removed_cases" in data or "dry_run" in data

    # Calculate performance metrics
    p50 = statistics.median(timings)
    p95 = max(timings)
    p99 = max(timings)

    print(
        f"\n[Consolidation /run] P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms"
    )

    # Assert SLA: P50 < 1500ms
    assert p50 < 1500, f"P50 latency {p50:.2f}ms exceeds target of 1500ms"


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_consolidation_dry_run_benchmark(async_client, sample_case_bank):
    """
    Benchmark: Consolidation /dry-run endpoint
    @TEST:TEST-003:BENCHMARK-BASELINE:CONSOLIDATION-DRY-RUN

    Target: P50 < 1s
    """
    timings = []
    num_iterations = 10

    # Warm-up request
    await async_client.post(
        "/consolidation/dry-run", headers={"X-API-Key": "test_api_key_for_testing"}
    )

    # Actual benchmark iterations
    for _ in range(num_iterations):
        start = time.perf_counter()
        response = await async_client.post(
            "/consolidation/dry-run", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        end = time.perf_counter()
        timings.append((end - start) * 1000)  # Convert to ms

        assert response.status_code == 200
        data = response.json()
        assert "removed_cases" in data or "dry_run" in data

    # Calculate performance metrics
    p50 = statistics.median(timings)
    p95 = (
        statistics.quantiles(timings, n=20)[18] if len(timings) >= 20 else max(timings)
    )
    p99 = max(timings)

    print(
        f"\n[Consolidation /dry-run] P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms"
    )

    # Assert SLA: P50 < 1000ms
    assert p50 < 1000, f"P50 latency {p50:.2f}ms exceeds target of 1000ms"
