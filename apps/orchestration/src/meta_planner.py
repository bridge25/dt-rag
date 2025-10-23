# @SPEC:PLANNER-001 @IMPL:PLANNER-001:0.1,0.2
"""
Meta-Planner Implementation

Provides query complexity analysis and LLM-based planning for DT-RAG pipeline.
Supports timeout handling and fallback strategies.
"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def analyze_complexity(query: str) -> Dict[str, str]:
    """
    @IMPL:PLANNER-001:0.1
    Analyze query complexity using heuristic rules

    Args:
        query: User query string

    Returns:
        Dict with 'complexity' (simple/medium/complex) and 'strategy' (direct/multi_step)
    """
    query_lower = query.lower()
    word_count = len(query.split())

    if word_count > 15:
        return {"complexity": "complex", "strategy": "multi_step"}

    if any(
        keyword in query_lower for keyword in ["분석", "예측", "analyze", "predict"]
    ):
        return {"complexity": "complex", "strategy": "multi_step"}

    if any(
        keyword in query_lower for keyword in ["비교", "차이", "compare", "difference"]
    ):
        return {"complexity": "medium", "strategy": "multi_step"}

    return {"complexity": "simple", "strategy": "direct"}


async def call_llm(query: str, complexity: str) -> Dict[str, Any]:
    """
    Call LLM for meta-planning

    Args:
        query: User query
        complexity: Complexity level from analyze_complexity()

    Returns:
        Dict with strategy, reasoning, tools
    """
    from apps.api.llm_service import get_llm_service

    llm_service = get_llm_service()

    prompt = f"""You are a Meta-Planner for a RAG system. Analyze the query and decide the execution strategy.

Query: {query}
Complexity: {complexity}

Available tools:
- case_search: Search historical cases in the database
- external_api: Call external APIs for additional data
- analysis: Perform analytical processing

Output JSON format:
{{
  "strategy": "simple|medium|complex",
  "reasoning": "Why this strategy?",
  "tools": ["case_search", "external_api", ...]
}}

Provide only the JSON response, no additional text."""

    response = llm_service.model.generate_content(prompt)
    response_text = response.text.strip()

    import json

    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    result = json.loads(response_text)
    return result


async def generate_plan(
    query: str, complexity: str, timeout: float = 10.0
) -> Dict[str, Any]:
    """
    @IMPL:PLANNER-001:0.2
    Generate execution plan using LLM with timeout and fallback

    Args:
        query: User query
        complexity: Complexity level from analyze_complexity()
        timeout: LLM call timeout in seconds (default: 10.0)

    Returns:
        Dict with 'tools', 'steps', 'strategy', 'reasoning'
    """
    try:
        llm_result = await asyncio.wait_for(
            call_llm(query, complexity), timeout=timeout
        )

        plan = {
            "tools": llm_result.get("tools", ["case_search"]),
            "steps": ["retrieve", "compose", "respond"],
            "strategy": llm_result.get("strategy", complexity),
            "reasoning": llm_result.get("reasoning", "LLM generated plan"),
        }

        logger.info(
            f"Plan generated: {plan['strategy']} with {len(plan['tools'])} tools"
        )
        return plan

    except asyncio.TimeoutError:
        logger.warning(f"LLM timeout after {timeout}s, using fallback strategy")
        return _fallback_plan()

    except Exception as e:
        logger.error(f"LLM call failed: {e}, using fallback strategy")
        return _fallback_plan()


def _fallback_plan() -> Dict[str, Any]:
    """
    Fallback strategy when LLM fails

    Returns all available tools to ensure safe operation
    """
    return {
        "tools": ["case_search", "external_api"],
        "steps": ["retrieve", "compose", "respond"],
        "strategy": "fallback",
        "reasoning": "LLM unavailable, using all tools",
    }
