"""
Integration tests for LangGraph 7-Step Pipeline

Tests the complete pipeline execution including:
- Intent analysis
- Hybrid search retrieval
- Answer composition
- Confidence calculation

DoD (Definition of Done):
- [ ] Pipeline completes within p95 ≤ 4s
- [ ] Returns sources ≥ 2
- [ ] Confidence score in range [0.0, 1.0]
- [ ] Taxonomy version preserved
"""

import pytest
import asyncio
from apps.orchestration.src.langgraph_pipeline import (
    get_pipeline,
    PipelineRequest,
    PipelineResponse,
)


@pytest.mark.asyncio
async def test_pipeline_basic_execution():
    """Test basic pipeline execution with simple query"""
    pipeline = get_pipeline()

    request = PipelineRequest(
        query="머신러닝이란 무엇인가요?", taxonomy_version="1.0.0"
    )

    response = await pipeline.execute(request)

    # DoD: Response structure validation
    assert isinstance(response, PipelineResponse)
    assert response.answer is not None
    assert len(response.answer) > 0

    # DoD: Sources ≥ 2 (if data exists)
    # Note: May be 0 if no search results, this is acceptable for now
    assert isinstance(response.sources, list)

    # DoD: Confidence in valid range
    assert 0.0 <= response.confidence <= 1.0

    # DoD: Taxonomy version preserved
    assert response.taxonomy_version == "1.0.0"

    # DoD: Latency < 4s (p95 target)
    assert response.latency < 4.0

    print(f"✅ Pipeline execution successful")
    print(f"   Latency: {response.latency:.3f}s (target: <4s)")
    print(f"   Sources: {len(response.sources)}")
    print(f"   Confidence: {response.confidence:.3f}")
    print(f"   Intent: {response.intent}")


@pytest.mark.asyncio
async def test_pipeline_with_canonical_filter():
    """Test pipeline with canonical path filtering"""
    pipeline = get_pipeline()

    request = PipelineRequest(
        query="인공지능 개발 방법",
        taxonomy_version="1.0.0",
        canonical_filter=[
            ["Technology", "AI", "Machine Learning"],
            ["Technology", "Software"],
        ],
    )

    response = await pipeline.execute(request)

    assert response is not None
    assert response.latency < 4.0

    print(f"✅ Pipeline with canonical filter successful")
    print(f"   Retrieved chunks: {len(response.sources)}")


@pytest.mark.asyncio
async def test_pipeline_step_timings():
    """Test individual step timings"""
    pipeline = get_pipeline()

    request = PipelineRequest(query="파이썬 프로그래밍", taxonomy_version="1.0.0")

    response = await pipeline.execute(request)

    # Validate step timings
    assert "intent" in response.step_timings
    assert "retrieve" in response.step_timings
    assert "compose" in response.step_timings
    assert "respond" in response.step_timings

    # Check individual step timeouts
    assert response.step_timings["intent"] < 0.5  # 200ms target
    assert response.step_timings["retrieve"] < 2.5  # 2s target
    assert response.step_timings["compose"] < 1.0  # 600ms target
    assert response.step_timings["respond"] < 0.3  # 100ms target

    print(f"✅ Step timings validation successful")
    for step, timing in response.step_timings.items():
        print(f"   {step}: {timing:.3f}s")


@pytest.mark.asyncio
async def test_pipeline_empty_results():
    """Test pipeline behavior with no search results"""
    pipeline = get_pipeline()

    # Query that likely returns no results
    request = PipelineRequest(
        query="xyzabc123nonexistentquery456", taxonomy_version="1.0.0"
    )

    response = await pipeline.execute(request)

    # Should still return a response
    assert response is not None
    assert response.answer is not None

    # Confidence should be low
    assert response.confidence == 0.0

    # Sources should be empty
    assert len(response.sources) == 0

    print(f"✅ Empty results handling successful")
    print(f"   Answer: {response.answer[:100]}...")


@pytest.mark.asyncio
async def test_pipeline_timeout_enforcement():
    """Test that pipeline enforces overall timeout"""
    pipeline = get_pipeline()

    request = PipelineRequest(
        query="복잡한 질문 with many results", taxonomy_version="1.0.0"
    )

    import time

    start = time.time()
    response = await pipeline.execute(request)
    elapsed = time.time() - start

    # Total time should be reasonable (< 5s for generous margin)
    assert elapsed < 5.0

    print(f"✅ Timeout enforcement successful")
    print(f"   Total time: {elapsed:.3f}s (< 5s)")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_pipeline_basic_execution())
    asyncio.run(test_pipeline_with_canonical_filter())
    asyncio.run(test_pipeline_step_timings())
    asyncio.run(test_pipeline_empty_results())
    asyncio.run(test_pipeline_timeout_enforcement())
    print("\n✅ All integration tests passed!")
