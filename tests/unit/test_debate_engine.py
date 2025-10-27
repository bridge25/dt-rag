# @SPEC:DEBATE-001 @TEST:DEBATE-001:unit
"""
Unit tests for Multi-Agent Debate Engine (SPEC-DEBATE-001)

Tests:
- Round 1: Independent answer generation (2 parallel LLM calls)
- Round 2: Mutual critique and improvement (2 parallel LLM calls)
- Synthesis: Final answer integration (1 LLM call)
- Timeout handling (10 second limit)
- Token limit enforcement (500 tokens/agent, 800 tokens/synthesis)
- Error handling (LLM API failures)
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio


@pytest.fixture
def sample_query():
    """Sample user query for testing"""
    return "What are the main causes of boiler failures?"


@pytest.fixture
def sample_context():
    """Sample context chunks for testing"""
    return [
        {
            "chunk_id": "chunk-001",
            "text": "Boiler failures are commonly caused by lack of maintenance, corrosion, and overheating.",
            "title": "Boiler Maintenance Guide",
            "source_url": "https://example.com/guide",
            "score": 0.95,
        },
        {
            "chunk_id": "chunk-002",
            "text": "Water quality issues can lead to scale buildup and reduced efficiency.",
            "title": "Water Treatment for Boilers",
            "source_url": "https://example.com/water",
            "score": 0.87,
        },
    ]


class TestDebateAgent:
    """Test DebateAgent class functionality"""

    @pytest.mark.asyncio
    async def test_affirmative_agent_round1_generation(
        self, sample_query, sample_context
    ):
        """TEST-DEBATE-001-001: Affirmative agent generates positive answer in Round 1"""
        from apps.orchestration.src.debate.debate_engine import DebateAgent

        agent = DebateAgent(role="affirmative", max_tokens=500)

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Boiler failures are caused by maintenance issues, corrosion, and overheating. [Sources: 1, 2]"
            mock_service.model.generate_content = MagicMock(return_value=mock_response)
            mock_llm.return_value = mock_service

            answer = await agent.generate_answer(
                query=sample_query, context=sample_context
            )

            assert isinstance(answer, str)
            assert len(answer) > 0
            assert "maintenance" in answer.lower() or "corrosion" in answer.lower()

    @pytest.mark.asyncio
    async def test_critical_agent_round1_generation(self, sample_query, sample_context):
        """TEST-DEBATE-001-002: Critical agent generates skeptical answer in Round 1"""
        from apps.orchestration.src.debate.debate_engine import DebateAgent

        agent = DebateAgent(role="critical", max_tokens=500)

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "However, the evidence is incomplete. Other factors like installation quality may be important."
            mock_service.model.generate_content = MagicMock(return_value=mock_response)
            mock_llm.return_value = mock_service

            answer = await agent.generate_answer(
                query=sample_query, context=sample_context
            )

            assert isinstance(answer, str)
            assert len(answer) > 0

    @pytest.mark.asyncio
    async def test_agent_round2_with_opponent_answer(
        self, sample_query, sample_context
    ):
        """TEST-DEBATE-001-003: Agent improves answer in Round 2 with opponent's critique"""
        from apps.orchestration.src.debate.debate_engine import DebateAgent

        agent = DebateAgent(role="affirmative", max_tokens=500)
        opponent_answer = (
            "The evidence is limited and doesn't cover installation quality."
        )

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "You're right about installation quality. However, maintenance remains the top cause according to multiple sources."
            mock_service.model.generate_content = MagicMock(return_value=mock_response)
            mock_llm.return_value = mock_service

            improved_answer = await agent.generate_answer(
                query=sample_query,
                context=sample_context,
                own_previous_answer="Maintenance is the main cause.",
                opponent_answer=opponent_answer,
            )

            assert isinstance(improved_answer, str)
            assert len(improved_answer) > 0

    @pytest.mark.asyncio
    async def test_agent_token_limit_enforcement(self, sample_query, sample_context):
        """TEST-DEBATE-001-004: Agent respects 500 token limit"""
        from apps.orchestration.src.debate.debate_engine import DebateAgent

        agent = DebateAgent(role="affirmative", max_tokens=500)

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            long_answer = " ".join(["word"] * 1000)
            mock_response = MagicMock()
            mock_response.text = long_answer
            mock_service.model.generate_content = MagicMock(return_value=mock_response)
            mock_llm.return_value = mock_service

            answer = await agent.generate_answer(
                query=sample_query, context=sample_context
            )

            token_count = len(answer.split())
            assert token_count <= 500


class TestDebateEngine:
    """Test DebateEngine orchestration logic"""

    @pytest.mark.asyncio
    async def test_run_debate_two_rounds(self, sample_query, sample_context):
        """TEST-DEBATE-001-005: DebateEngine executes 2-round debate successfully"""
        from apps.orchestration.src.debate.debate_engine import DebateEngine

        engine = DebateEngine()

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Mocked answer"
            mock_service.model.generate_content = MagicMock(return_value=mock_response)
            mock_llm.return_value = mock_service

            result = await engine.run_debate(
                query=sample_query, context=sample_context, max_rounds=2, timeout=10.0
            )

            assert result.final_answer is not None
            assert len(result.final_answer) > 0
            assert result.rounds == 2
            assert result.llm_calls == 5

    @pytest.mark.asyncio
    async def test_debate_timeout_handling(self, sample_query, sample_context):
        """TEST-DEBATE-001-006: DebateEngine handles timeout gracefully"""
        from apps.orchestration.src.debate.debate_engine import DebateEngine

        engine = DebateEngine()

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()

            def slow_llm(*args, **kwargs):
                import time

                time.sleep(15)
                mock_response = MagicMock()
                mock_response.text = "Too late"
                return mock_response

            mock_service.model.generate_content = slow_llm
            mock_llm.return_value = mock_service

            with pytest.raises(asyncio.TimeoutError):
                await engine.run_debate(
                    query=sample_query,
                    context=sample_context,
                    max_rounds=2,
                    timeout=0.1,
                )

    @pytest.mark.asyncio
    async def test_debate_llm_api_error_handling(self, sample_query, sample_context):
        """TEST-DEBATE-001-007: DebateEngine handles LLM API errors"""
        from apps.orchestration.src.debate.debate_engine import DebateEngine

        engine = DebateEngine()

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            mock_service.model.generate_content = MagicMock(
                side_effect=Exception("API Error")
            )
            mock_llm.return_value = mock_service

            with pytest.raises(Exception):
                await engine.run_debate(
                    query=sample_query,
                    context=sample_context,
                    max_rounds=2,
                    timeout=10.0,
                )

    @pytest.mark.asyncio
    async def test_debate_result_structure(self, sample_query, sample_context):
        """TEST-DEBATE-001-008: DebateResult contains all required fields"""
        from apps.orchestration.src.debate.debate_engine import DebateEngine

        engine = DebateEngine()

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Answer"
            mock_service.model.generate_content = MagicMock(return_value=mock_response)
            mock_llm.return_value = mock_service

            result = await engine.run_debate(
                query=sample_query, context=sample_context, max_rounds=2, timeout=10.0
            )

            assert hasattr(result, "final_answer")
            assert hasattr(result, "rounds")
            assert hasattr(result, "llm_calls")
            assert hasattr(result, "affirmative_answers")
            assert hasattr(result, "critical_answers")
            assert hasattr(result, "elapsed_time")

    @pytest.mark.asyncio
    async def test_parallel_llm_calls_in_round1(self, sample_query, sample_context):
        """TEST-DEBATE-001-009: Round 1 executes 2 LLM calls in parallel"""
        from apps.orchestration.src.debate.debate_engine import DebateEngine
        import time

        engine = DebateEngine()

        call_times = []

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()

            def timed_llm(*args, **kwargs):
                call_times.append(time.time())
                mock_response = MagicMock()
                mock_response.text = "Answer"
                return mock_response

            mock_service.model.generate_content = timed_llm
            mock_llm.return_value = mock_service

            await engine.run_debate(
                query=sample_query, context=sample_context, max_rounds=2, timeout=10.0
            )

            assert len(call_times) == 5

            time_diff = abs(call_times[0] - call_times[1])
            assert time_diff < 0.05

    @pytest.mark.asyncio
    async def test_synthesis_max_tokens_800(self, sample_query, sample_context):
        """TEST-DEBATE-001-010: Synthesis respects 800 token limit"""
        from apps.orchestration.src.debate.debate_engine import DebateEngine

        engine = DebateEngine()

        with patch(
            "apps.orchestration.src.debate.debate_engine.get_llm_service_cached"
        ) as mock_llm:
            mock_service = MagicMock()

            call_count = [0]

            def mock_generate(*args, **kwargs):
                call_count[0] += 1
                mock_response = MagicMock()
                if call_count[0] == 5:
                    mock_response.text = " ".join(["word"] * 1500)
                else:
                    mock_response.text = "Short answer"
                return mock_response

            mock_service.model.generate_content = mock_generate
            mock_llm.return_value = mock_service

            result = await engine.run_debate(
                query=sample_query, context=sample_context, max_rounds=2, timeout=10.0
            )

            token_count = len(result.final_answer.split())
            assert token_count <= 800
