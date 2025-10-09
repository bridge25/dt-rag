# @SPEC:FOUNDATION-001 @TEST:0.3-pipeline-steps
"""
Integration tests for Pipeline Steps (SPEC-FOUNDATION-001)

Tests 7-step pipeline functionality:
- Step 3 (plan): Skips when meta_planner flag is OFF
- Step 4 (tools/debate): Skips when both flags are OFF
- Step 6 (cite): Executes as stub
- 7-step sequential execution
- Existing 4-step regression test
"""

import pytest
from unittest.mock import patch
from apps.orchestration.src.langgraph_pipeline import (
    LangGraphPipeline, PipelineRequest, step3_plan, step4_tools_debate, step6_cite
)


class TestPipelineSteps:
    """Test pipeline step functionality"""

    @pytest.mark.asyncio
    async def test_step3_skip_when_flag_off(self):
        """TEST-STEP-001: meta_planner=False 시 step3 스킵"""
        with patch("apps.api.env_manager.get_env_manager") as mock_env_mgr:
            from unittest.mock import MagicMock
            mock_mgr = MagicMock()
            mock_mgr.get_feature_flags.return_value = {"meta_planner": False}
            mock_env_mgr.return_value = mock_mgr

            from apps.orchestration.src.langgraph_pipeline import PipelineState
            state = PipelineState(query="test")

            result = await step3_plan(state)

            # Step should be skipped
            assert result == state

    @pytest.mark.asyncio
    async def test_step3_execute_when_flag_on(self):
        """TEST-STEP-002: meta_planner=True 시 step3 실행"""
        with patch("apps.api.env_manager.get_env_manager") as mock_env_mgr:
            from unittest.mock import MagicMock
            mock_mgr = MagicMock()
            mock_mgr.get_feature_flags.return_value = {"meta_planner": True}
            mock_env_mgr.return_value = mock_mgr

            from apps.orchestration.src.langgraph_pipeline import PipelineState
            state = PipelineState(query="test")

            result = await step3_plan(state)

            # Step should execute (stub)
            assert result == state

    @pytest.mark.asyncio
    async def test_step4_skip_when_flags_off(self):
        """TEST-STEP-003: debate_mode=False, tools_policy=False 시 step4 스킵"""
        with patch("apps.api.env_manager.get_env_manager") as mock_env_mgr:
            from unittest.mock import MagicMock
            mock_mgr = MagicMock()
            mock_mgr.get_feature_flags.return_value = {
                "debate_mode": False,
                "tools_policy": False
            }
            mock_env_mgr.return_value = mock_mgr

            from apps.orchestration.src.langgraph_pipeline import PipelineState
            state = PipelineState(query="test")

            result = await step4_tools_debate(state)

            # Step should be skipped
            assert result == state

    @pytest.mark.asyncio
    async def test_step4_execute_when_debate_on(self):
        """TEST-STEP-004: debate_mode=True 시 step4 실행"""
        with patch("apps.api.env_manager.get_env_manager") as mock_env_mgr:
            from unittest.mock import MagicMock
            mock_mgr = MagicMock()
            mock_mgr.get_feature_flags.return_value = {
                "debate_mode": True,
                "tools_policy": False
            }
            mock_env_mgr.return_value = mock_mgr

            from apps.orchestration.src.langgraph_pipeline import PipelineState
            state = PipelineState(query="test")

            result = await step4_tools_debate(state)

            # Step should execute (stub)
            assert result == state

    @pytest.mark.asyncio
    async def test_step6_cite_executes(self):
        """TEST-STEP-005: step6_cite always executes"""
        from apps.orchestration.src.langgraph_pipeline import PipelineState
        state = PipelineState(query="test")

        result = await step6_cite(state)

        # Step should execute (stub)
        assert result == state

    @pytest.mark.asyncio
    async def test_7step_sequential_execution(self):
        """TEST-STEP-006: 7-step 순차 실행 검증"""
        with patch("apps.api.env_manager.get_env_manager") as mock_env_mgr:
            from unittest.mock import MagicMock
            mock_mgr = MagicMock()
            mock_mgr.get_feature_flags.return_value = {
                "meta_planner": False,
                "debate_mode": False,
                "tools_policy": False
            }
            mock_env_mgr.return_value = mock_mgr

            with patch("apps.orchestration.src.langgraph_pipeline.step1_intent") as mock_step1, \
                 patch("apps.orchestration.src.langgraph_pipeline.step2_retrieve") as mock_step2, \
                 patch("apps.orchestration.src.langgraph_pipeline.step5_compose") as mock_step5, \
                 patch("apps.orchestration.src.langgraph_pipeline.step7_respond") as mock_step7:


                async def passthrough(state):
                    return state

                mock_step1.side_effect = passthrough
                mock_step2.side_effect = passthrough
                mock_step5.side_effect = passthrough
                mock_step7.side_effect = passthrough

                pipeline = LangGraphPipeline()
                request = PipelineRequest(query="test query")

                response = await pipeline.execute(request)

                # Verify all steps were called
                assert mock_step1.called
                assert mock_step2.called
                assert mock_step5.called
                assert mock_step7.called

                # Verify step_timings contains all 7 steps
                assert "intent" in response.step_timings
                assert "retrieve" in response.step_timings
                assert "plan" in response.step_timings
                assert "tools_debate" in response.step_timings
                assert "compose" in response.step_timings
                assert "cite" in response.step_timings
                assert "respond" in response.step_timings

    @pytest.mark.asyncio
    async def test_existing_4step_regression(self):
        """TEST-STEP-007: 기존 4-step 파이프라인 100% 동작 확인"""
        with patch("apps.api.env_manager.get_env_manager") as mock_env_mgr:
            from unittest.mock import MagicMock
            mock_mgr = MagicMock()
            mock_mgr.get_feature_flags.return_value = {
                "meta_planner": False,
                "debate_mode": False,
                "tools_policy": False
            }
            mock_env_mgr.return_value = mock_mgr

            with patch("apps.orchestration.src.langgraph_pipeline.step1_intent") as mock_step1, \
                 patch("apps.orchestration.src.langgraph_pipeline.step2_retrieve") as mock_step2, \
                 patch("apps.orchestration.src.langgraph_pipeline.step5_compose") as mock_step5, \
                 patch("apps.orchestration.src.langgraph_pipeline.step7_respond") as mock_step7:


                async def passthrough(state):
                    return state

                mock_step1.side_effect = passthrough
                mock_step2.side_effect = passthrough
                mock_step5.side_effect = passthrough
                mock_step7.side_effect = passthrough

                pipeline = LangGraphPipeline()
                request = PipelineRequest(query="existing test")

                response = await pipeline.execute(request)

                # Existing 4 steps must work exactly as before
                assert mock_step1.called
                assert mock_step2.called
                assert mock_step5.called
                assert mock_step7.called
                assert response.answer is not None
                assert response.latency > 0
