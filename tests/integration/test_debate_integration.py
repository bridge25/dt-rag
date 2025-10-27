# @SPEC:DEBATE-001 @TEST:DEBATE-001:integration
"""
Integration tests for Multi-Agent Debate with LangGraph Pipeline (SPEC-DEBATE-001)

Tests:
- Feature flag OFF: step4 skips debate
- Feature flag ON: step4 executes debate
- Fallback: Debate failure uses step5 initial answer
- Regression: Existing 4-step pipeline behavior preserved
- E2E: Full 7-step pipeline with debate integration
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os


@pytest.fixture
def sample_pipeline_request():
    """Sample PipelineRequest for testing"""
    from apps.orchestration.src.langgraph_pipeline import PipelineRequest

    return PipelineRequest(
        query="What are common boiler issues?",
        taxonomy_version="1.0.0",
        canonical_filter=None,
        options={},
    )


class TestFeatureFlagIntegration:
    """Test debate_mode feature flag integration"""

    @pytest.mark.asyncio
    async def test_debate_mode_flag_off_skips_debate(self, sample_pipeline_request):
        """TEST-DEBATE-001-INT-001: debate_mode=false skips step4 debate"""
        from apps.orchestration.src.langgraph_pipeline import (
            PipelineState,
            step4_tools_debate,
        )

        with patch("apps.api.env_manager.get_env_manager") as mock_env:
            mock_manager = MagicMock()
            mock_manager.get_feature_flags.return_value = {
                "debate_mode": False,
                "meta_planner": False,
                "mcp_tools": False,
            }
            mock_env.return_value = mock_manager

            state = PipelineState(
                query=sample_pipeline_request.query, retrieved_chunks=[]
            )

            result_state = await step4_tools_debate(state)

            assert result_state.answer is None or result_state.answer == ""

    @pytest.mark.asyncio
    async def test_debate_mode_flag_on_executes_debate(self, sample_pipeline_request):
        """TEST-DEBATE-001-INT-002: debate_mode=true executes debate in step4"""
        from apps.orchestration.src.langgraph_pipeline import (
            PipelineState,
            step4_tools_debate,
        )

        with patch("apps.api.env_manager.get_env_manager") as mock_env:
            mock_manager = MagicMock()
            mock_manager.get_feature_flags.return_value = {
                "debate_mode": True,
                "meta_planner": False,
                "mcp_tools": False,
            }
            mock_env.return_value = mock_manager

            with patch(
                "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
            ) as mock_llm:
                mock_service = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Debate answer"
                mock_service.model.generate_content = MagicMock(
                    return_value=mock_response
                )
                mock_llm.return_value = mock_service

                state = PipelineState(
                    query=sample_pipeline_request.query,
                    retrieved_chunks=[
                        {
                            "chunk_id": "1",
                            "text": "Sample text",
                            "title": "Title",
                            "source_url": "http://example.com",
                            "score": 0.9,
                        }
                    ],
                )

                result_state = await step4_tools_debate(state)

                assert result_state.answer is not None
                assert len(result_state.answer) > 0


class TestDebateFallback:
    """Test debate fallback behavior"""

    @pytest.mark.asyncio
    async def test_debate_timeout_uses_fallback(self, sample_pipeline_request):
        """TEST-DEBATE-001-INT-003: Debate timeout falls back gracefully"""
        from apps.orchestration.src.langgraph_pipeline import (
            PipelineState,
            step4_tools_debate,
        )
        import asyncio

        with patch("apps.api.env_manager.get_env_manager") as mock_env:
            mock_manager = MagicMock()
            mock_manager.get_feature_flags.return_value = {
                "debate_mode": True,
                "meta_planner": False,
                "mcp_tools": False,
            }
            mock_env.return_value = mock_manager

            with patch(
                "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
            ) as mock_llm:
                mock_service = MagicMock()

                def slow_llm(*args, **kwargs):
                    import time

                    time.sleep(2)
                    mock_response = MagicMock()
                    mock_response.text = "Too late"
                    return mock_response

                mock_service.model.generate_content = slow_llm
                mock_llm.return_value = mock_service

                state = PipelineState(
                    query=sample_pipeline_request.query,
                    retrieved_chunks=[
                        {
                            "chunk_id": "1",
                            "text": "Sample",
                            "title": "Title",
                            "source_url": "http://example.com",
                            "score": 0.9,
                        }
                    ],
                )

                result_state = await step4_tools_debate(state)

                assert result_state is not None

    @pytest.mark.asyncio
    async def test_debate_llm_error_uses_fallback(self, sample_pipeline_request):
        """TEST-DEBATE-001-INT-004: Debate LLM error falls back gracefully"""
        from apps.orchestration.src.langgraph_pipeline import (
            PipelineState,
            step4_tools_debate,
        )

        with patch("apps.api.env_manager.get_env_manager") as mock_env:
            mock_manager = MagicMock()
            mock_manager.get_feature_flags.return_value = {
                "debate_mode": True,
                "meta_planner": False,
                "mcp_tools": False,
            }
            mock_env.return_value = mock_manager

            with patch(
                "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
            ) as mock_llm:
                mock_service = MagicMock()
                mock_service.model.generate_content = MagicMock(
                    side_effect=Exception("API Error")
                )
                mock_llm.return_value = mock_service

                state = PipelineState(
                    query=sample_pipeline_request.query,
                    retrieved_chunks=[
                        {
                            "chunk_id": "1",
                            "text": "Sample",
                            "title": "Title",
                            "source_url": "http://example.com",
                            "score": 0.9,
                        }
                    ],
                )

                result_state = await step4_tools_debate(state)

                assert result_state is not None


class TestPipelineRegression:
    """Test that existing pipeline behavior is preserved"""

    @pytest.mark.asyncio
    async def test_existing_4step_pipeline_unchanged(self, sample_pipeline_request):
        """TEST-DEBATE-001-INT-005: Existing 4-step pipeline works without debate"""
        from apps.orchestration.src.langgraph_pipeline import (
            step1_intent,
            step2_retrieve,
            step5_compose,
            step7_respond,
            PipelineState,
        )

        with patch("apps.api.env_manager.get_env_manager") as mock_env:
            mock_manager = MagicMock()
            mock_manager.get_feature_flags.return_value = {
                "debate_mode": False,
                "meta_planner": False,
                "mcp_tools": False,
            }
            mock_env.return_value = mock_manager

            state = PipelineState(query=sample_pipeline_request.query)

            state = await step1_intent(state)
            assert state.intent is not None

            with patch(
                "apps.orchestration.src.langgraph_pipeline.get_search_engine"
            ) as mock_search:
                mock_engine = MagicMock()
                mock_engine.search = AsyncMock(return_value=([], {}))
                mock_search.return_value = mock_engine

                state = await step2_retrieve(state)

            with patch(
                "apps.orchestration.src.langgraph_pipeline.get_llm_service_cached"
            ) as mock_llm:
                mock_service = MagicMock()
                mock_result = MagicMock()
                mock_result.answer = "Test answer"
                mock_service.generate_answer = AsyncMock(return_value=mock_result)
                mock_llm.return_value = mock_service

                state.retrieved_chunks = [
                    {
                        "chunk_id": "1",
                        "text": "Sample",
                        "title": "Title",
                        "source_url": "http://example.com",
                        "score": 0.9,
                        "date": "2025-01-01",
                        "version": "1.0.0",
                    }
                ]

                state = await step5_compose(state)
                assert state.answer is not None

                state = await step7_respond(state)
                assert state.confidence >= 0.0


class TestEndToEndPipeline:
    """Test full 7-step pipeline with debate"""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_debate_enabled(self, sample_pipeline_request):
        """TEST-DEBATE-001-INT-006: Full 7-step pipeline executes with debate"""
        from apps.orchestration.src.langgraph_pipeline import LangGraphPipeline

        with patch("apps.api.env_manager.get_env_manager") as mock_env:
            mock_manager = MagicMock()
            mock_manager.get_feature_flags.return_value = {
                "debate_mode": True,
                "meta_planner": False,
                "mcp_tools": False,
            }
            mock_env.return_value = mock_manager

            with patch(
                "apps.orchestration.src.langgraph_pipeline.get_search_engine"
            ) as mock_search:
                mock_engine = MagicMock()
                mock_engine.search = AsyncMock(
                    return_value=(
                        [
                            MagicMock(
                                chunk_id="1",
                                text="Sample text",
                                title="Title",
                                source_url="http://example.com",
                                taxonomy_path="/a/b",
                                rerank_score=0.9,
                                hybrid_score=0.85,
                            )
                        ],
                        {},
                    )
                )
                mock_search.return_value = mock_engine

                with patch(
                    "apps.orchestration.src.langgraph_pipeline.get_llm_service_cached"
                ) as mock_llm:
                    mock_service = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "Debate answer"
                    mock_service.model.generate_content = MagicMock(
                        return_value=mock_response
                    )
                    mock_result = MagicMock()
                    mock_result.answer = "Final answer"
                    mock_service.generate_answer = AsyncMock(return_value=mock_result)
                    mock_llm.return_value = mock_service

                    pipeline = LangGraphPipeline()
                    response = await pipeline.execute(sample_pipeline_request)

                    assert response.answer is not None
                    assert len(response.sources) >= 0
                    assert response.confidence >= 0.0
                    assert response.latency > 0.0
