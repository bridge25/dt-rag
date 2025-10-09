# @SPEC:PLANNER-001 @TEST:PLANNER-001:0.1
"""
Unit tests for Meta-Planner (SPEC-PLANNER-001)

Tests complexity analysis and LLM-based planning logic:
- Query complexity classification (simple/medium/complex)
- LLM planner invocation with timeout handling
- Fallback strategy when LLM fails
- JSON response parsing
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio


class TestComplexityAnalysis:
    """Test query complexity analysis logic"""

    def test_simple_query_classification(self):
        """TEST-PLANNER-001-001: 단순 키워드 쿼리는 simple로 분류"""
        from apps.orchestration.src.meta_planner import analyze_complexity

        query = "보일러 고장 사례 찾아줘"
        result = asyncio.run(analyze_complexity(query))

        assert result["complexity"] == "simple"
        assert result["strategy"] == "direct"

    def test_comparison_query_classification(self):
        """TEST-PLANNER-001-002: 비교 쿼리는 medium 또는 complex로 분류"""
        from apps.orchestration.src.meta_planner import analyze_complexity

        query = "A와 B 제품의 차이점을 비교해줘"
        result = asyncio.run(analyze_complexity(query))

        assert result["complexity"] in ["medium", "complex"]

    def test_analysis_query_classification(self):
        """TEST-PLANNER-001-003: 분석/예측 쿼리는 complex로 분류"""
        from apps.orchestration.src.meta_planner import analyze_complexity

        query = "향후 5년간 시장 트렌드를 분석하고 예측해줘"
        result = asyncio.run(analyze_complexity(query))

        assert result["complexity"] == "complex"

    def test_long_query_classification(self):
        """TEST-PLANNER-001-004: 15단어 이상 긴 쿼리는 complex로 분류"""
        from apps.orchestration.src.meta_planner import analyze_complexity

        query = "이 문장은 매우 긴 쿼리로 15단어를 넘어가는 복잡한 질문입니다 과연 제대로 분류될까요 아마도 단어가 충분히 많으면 작동할 것입니다"
        result = asyncio.run(analyze_complexity(query))

        assert result["complexity"] == "complex"


class TestLLMPlanner:
    """Test LLM-based planning logic"""

    @pytest.mark.asyncio
    async def test_successful_plan_generation(self):
        """TEST-PLANNER-001-005: LLM이 정상적으로 계획을 생성"""
        from apps.orchestration.src.meta_planner import generate_plan

        with patch("apps.orchestration.src.meta_planner.call_llm") as mock_llm:
            mock_llm.return_value = {
                "strategy": "simple",
                "reasoning": "단순 검색 쿼리",
                "tools": ["case_search"]
            }

            result = await generate_plan(
                query="보일러 고장 사례",
                complexity="simple",
                timeout=10.0
            )

            assert "tools" in result
            assert "steps" in result
            assert "case_search" in result["tools"]

    @pytest.mark.asyncio
    async def test_llm_timeout_fallback(self):
        """TEST-PLANNER-001-006: LLM 타임아웃 시 Fallback 전략 반환"""
        from apps.orchestration.src.meta_planner import generate_plan

        with patch("apps.orchestration.src.meta_planner.call_llm") as mock_llm:
            async def slow_llm(*args, **kwargs):
                await asyncio.sleep(15)  # 타임아웃 초과
                return {}

            mock_llm.side_effect = slow_llm

            result = await generate_plan(
                query="test query",
                complexity="simple",
                timeout=1.0  # 짧은 타임아웃으로 테스트
            )

            # Fallback 전략 확인
            assert result["strategy"] == "fallback"
            assert "all" in result["tools"] or len(result["tools"]) > 1

    @pytest.mark.asyncio
    async def test_llm_error_fallback(self):
        """TEST-PLANNER-001-007: LLM API 에러 시 Fallback 전략 반환"""
        from apps.orchestration.src.meta_planner import generate_plan

        with patch("apps.orchestration.src.meta_planner.call_llm") as mock_llm:
            mock_llm.side_effect = Exception("API Error")

            result = await generate_plan(
                query="test query",
                complexity="simple",
                timeout=10.0
            )

            # Fallback 전략 확인
            assert result["strategy"] == "fallback"
            assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_complex_query_plan(self):
        """TEST-PLANNER-001-008: 복잡한 쿼리는 다단계 계획 생성"""
        from apps.orchestration.src.meta_planner import generate_plan

        with patch("apps.orchestration.src.meta_planner.call_llm") as mock_llm:
            mock_llm.return_value = {
                "strategy": "complex",
                "reasoning": "다단계 분석 필요",
                "tools": ["case_search", "external_api", "analysis"]
            }

            result = await generate_plan(
                query="A와 B를 비교 분석하고 예측해줘",
                complexity="complex",
                timeout=10.0
            )

            assert len(result["tools"]) >= 2
            assert "analysis" in result["tools"] or "case_search" in result["tools"]

    @pytest.mark.asyncio
    async def test_plan_json_schema(self):
        """TEST-PLANNER-001-009: 계획 출력이 올바른 JSON 스키마를 따름"""
        from apps.orchestration.src.meta_planner import generate_plan

        with patch("apps.orchestration.src.meta_planner.call_llm") as mock_llm:
            mock_llm.return_value = {
                "strategy": "simple",
                "reasoning": "test",
                "tools": ["case_search"]
            }

            result = await generate_plan(
                query="test",
                complexity="simple",
                timeout=10.0
            )

            # 필수 필드 검증
            assert "tools" in result
            assert "steps" in result
            assert isinstance(result["tools"], list)
            assert isinstance(result["steps"], list)
