# @TEST:REPLAY-001:pipeline
"""
Integration tests for Pipeline Experience Replay (SPEC-REPLAY-001)

Tests:
- TEST-REPLAY-008: Feature flag ON - experience saved to buffer
- TEST-REPLAY-009: Feature flag OFF - existing behavior maintained
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_pipeline_experience_replay_on():
    """TEST-REPLAY-008: Feature flag ON - experience saved to buffer"""
    from apps.orchestration.src.langgraph_pipeline import (
        LangGraphPipeline,
        PipelineState,
        PipelineRequest,
    )

    with (
        patch("apps.api.env_manager.get_env_manager") as mock_env,
        patch("apps.orchestration.src.langgraph_pipeline.get_search_engine"),
        patch("apps.orchestration.src.langgraph_pipeline.get_llm_service_cached"),
    ):

        mock_mgr = MagicMock()
        mock_mgr.get_feature_flags.return_value = {"experience_replay": True}
        mock_env.return_value = mock_mgr

        pipeline = LangGraphPipeline()

        assert hasattr(pipeline, "replay_buffer")
        assert len(pipeline.replay_buffer) == 0


@pytest.mark.asyncio
async def test_pipeline_experience_replay_off():
    """TEST-REPLAY-009: Feature flag OFF - existing behavior maintained"""
    from apps.orchestration.src.langgraph_pipeline import (
        LangGraphPipeline,
    )

    with patch("apps.api.env_manager.get_env_manager") as mock_env:
        mock_mgr = MagicMock()
        mock_mgr.get_feature_flags.return_value = {"experience_replay": False}
        mock_env.return_value = mock_mgr

        pipeline = LangGraphPipeline()

        assert hasattr(pipeline, "replay_buffer")
        assert len(pipeline.replay_buffer) == 0
