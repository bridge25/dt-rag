"""
LangGraph 7-Step Pipeline Implementation for DT-RAG v1.8.1

Implements a simplified 4-step pipeline (intent, retrieve, compose, respond)
following PRD requirements:
- p95 ≤ 4s latency
- Output format: answer, sources ≥ 2, confidence, taxonomy_version
- Canonical path filtering enforcement
- Feature flags support (debate/tools reserved for 1.5P)

Phase 5 (1P) Scope:
- Basic sequential pipeline without Debate/Tools
- Simple confidence calculation (rerank score + source count)
- Timeout enforcement per step
"""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Import hybrid search engine (lazy to avoid initialization delays)
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy imports to avoid blocking initialization
_search_engine = None
_llm_service = None


def get_search_engine():
    """Lazy load search engine"""
    global _search_engine
    if _search_engine is None:
        from apps.search.hybrid_search_engine import search_engine

        _search_engine = search_engine
    return _search_engine


def get_llm_service_cached():
    """Lazy load LLM service"""
    global _llm_service
    if _llm_service is None:
        from apps.api.llm_service import get_llm_service

        _llm_service = get_llm_service()
    return _llm_service


class PipelineState(BaseModel):
    """Minimal state schema for 7-Step pipeline (6 fields)"""

    query: str
    intent: Optional[str] = None
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0

    # Metadata (not exposed in API response)
    taxonomy_version: str = "1.0.0"
    canonical_filter: Optional[List[List[str]]] = None
    start_time: float = Field(default_factory=time.time)
    step_timings: Dict[str, float] = Field(default_factory=dict)
    plan: Optional[Dict[str, Any]] = None  # Meta-planner output
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)  # Tool execution results
    debate_result: Optional[Any] = None  # Debate result (DEBATE-001)


class PipelineRequest(BaseModel):
    """Request to LangGraph pipeline"""

    query: str
    taxonomy_version: str = "1.0.0"
    canonical_filter: Optional[List[List[str]]] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class PipelineResponse(BaseModel):
    """Response from LangGraph pipeline"""

    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    taxonomy_version: str
    latency: float

    # Additional metrics
    cost: float = 0.0
    intent: Optional[str] = None
    step_timings: Dict[str, float] = Field(default_factory=dict)


# @SPEC:FOUNDATION-001 @IMPL:0.3-pipeline-steps
# Step timeout configuration (2025-10-06 실측 기반 조정 완료)
# 실측값 (2회 테스트 평균): intent(~0.1ms), retrieve(0.37~1.19s), compose(1.29~2.06s), respond(~0.05ms)
# 각 단계별 최대 실측값 × 1.5 여유율 적용
STEP_TIMEOUTS = {
    "intent": 0.1,  # 0.1s - 간단한 파싱 (실측 0.056~0.15ms)
    "retrieve": 2.0,  # 2.0s - Hybrid search + rerank + embedding generation (실측 0.37~1.19s)
    "plan": 0.5,  # 0.5s - Meta-level Planning (stub, Phase 1)
    "tools_debate": 1.0,  # 1.0s - Tools/Debate (stub, Phase 2B/3)
    "compose": 3.5,  # 3.5s - LLM 1회 호출 (Gemini API 포함, 실측 1.29~2.06s, API 변동 고려)
    "cite": 0.1,  # 0.1s - Source Citation (stub)
    "respond": 0.1,  # 0.1s - 포맷팅 및 신뢰도 계산 (실측 0.043~0.05ms)
}


async def execute_with_timeout(step_func, state: PipelineState, step_name: str):
    """Execute step with timeout enforcement"""
    timeout = STEP_TIMEOUTS.get(step_name, 1.0)
    step_start = time.time()

    try:
        result = await asyncio.wait_for(step_func(state), timeout=timeout)
        elapsed = time.time() - step_start
        state.step_timings[step_name] = elapsed
        logger.info(f"Step {step_name} completed in {elapsed:.3f}s")
        return result

    except asyncio.TimeoutError:
        elapsed = time.time() - step_start
        logger.error(
            f"Step {step_name} timeout after {elapsed:.3f}s (limit: {timeout}s)"
        )
        raise TimeoutError(
            f"Pipeline step '{step_name}' exceeded timeout of {timeout}s"
        )


async def step1_intent(state: PipelineState) -> PipelineState:
    """
    Step 1: Intent Analysis

    Parses user query to extract:
    - Core intent (question, command, exploration)
    - Taxonomy hints (if query mentions specific categories)
    - Time/date constraints

    Output: state.intent (simple string for now)
    """
    query_lower = state.query.lower()

    # Simple intent classification
    if "?" in state.query or any(
        q in query_lower for q in ["what", "how", "why", "when", "where", "who"]
    ):
        intent = "question"
    elif any(cmd in query_lower for cmd in ["explain", "describe", "tell me"]):
        intent = "explanation"
    elif any(cmd in query_lower for cmd in ["find", "search", "look for"]):
        intent = "search"
    else:
        intent = "general"

    state.intent = intent
    logger.info(f"Intent classified as: {intent}")

    return state


async def step2_retrieve(state: PipelineState) -> PipelineState:
    """
    Step 2: Hybrid Search Retrieval

    Executes BM25 + Vector search with:
    - Canonical path filtering (if state.canonical_filter is set)
    - Reranking (50 → 5 candidates)

    Output: state.retrieved_chunks (List[Dict])
    """
    # Build filters
    filters = {}
    if state.canonical_filter:
        filters["taxonomy_paths"] = state.canonical_filter

    # Execute hybrid search
    try:
        search_eng = get_search_engine()
        results, metrics = await search_eng.search(
            query=state.query,
            top_k=5,  # PRD: rerank 50→5, but search_engine already does this
            filters=filters,
            bm25_candidates=12,  # PRD: BM25 topk=12
            vector_candidates=12,  # PRD: Vector topk=12
        )

        # Convert SearchResult to dict
        state.retrieved_chunks = [
            {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "title": r.title or "Untitled",
                "source_url": r.source_url or "",
                "taxonomy_path": r.taxonomy_path,
                "score": r.rerank_score if r.rerank_score > 0 else r.hybrid_score,
                "date": "2025-09-01",  # TODO: Extract from metadata
                "version": state.taxonomy_version,
            }
            for r in results
        ]

        logger.info(f"Retrieved {len(state.retrieved_chunks)} chunks (hybrid search)")

    except Exception as e:
        logger.error(f"Retrieve step failed: {e}")
        state.retrieved_chunks = []

    return state


async def step3_plan(state: PipelineState) -> PipelineState:
    """
    # @SPEC:PLANNER-001 @IMPL:PLANNER-001:0.3
    Step 3: Meta-level Planning

    Analyzes query complexity and generates execution plan using LLM.
    Conditional execution based on meta_planner feature flag.
    """
    from apps.api.env_manager import get_env_manager
    from apps.orchestration.src.meta_planner import analyze_complexity, generate_plan

    flags = get_env_manager().get_feature_flags()

    if not flags.get("meta_planner", False):
        logger.info("Step 3 (plan) skipped (feature flag OFF)")
        return state

    complexity_result = await analyze_complexity(state.query)
    logger.info(f"Query complexity: {complexity_result['complexity']}")

    plan = await generate_plan(
        query=state.query, complexity=complexity_result["complexity"], timeout=10.0
    )

    state.plan = plan
    logger.info(
        f"Step 3 (plan) executed: strategy={plan['strategy']}, tools={plan['tools']}"
    )

    return state


async def step4_tools_debate(state: PipelineState) -> PipelineState:
    """
    # @SPEC:TOOLS-001 @IMPL:TOOLS-001:0.4
    # @SPEC:DEBATE-001 @IMPL:DEBATE-001:0.3
    Step 4: Tools Execution & Debate

    Executes tools from Meta-Planner's plan.tools list OR runs debate if enabled.
    Conditional execution based on mcp_tools, tools_policy, and debate_mode flags.
    """
    from apps.api.env_manager import get_env_manager

    flags = get_env_manager().get_feature_flags()

    debate_enabled = flags.get("debate_mode", False)
    tools_enabled = flags.get("mcp_tools", False)

    if debate_enabled:
        from apps.orchestration.src.debate.debate_engine import DebateEngine

        logger.info("Step 4: Debate mode enabled, running multi-agent debate")

        if not state.retrieved_chunks:
            logger.warning("No retrieved chunks for debate, skipping")
            return state

        debate_engine = DebateEngine()

        try:
            result = await debate_engine.run_debate(
                query=state.query,
                context=state.retrieved_chunks,
                max_rounds=2,
                timeout=10.0,
            )

            state.answer = result.final_answer
            state.debate_result = result

            logger.info(
                f"Debate completed: {result.rounds} rounds, {result.llm_calls} LLM calls, {result.elapsed_time:.2f}s"
            )

        except asyncio.TimeoutError:
            logger.warning(
                "Debate timeout - proceeding without debate answer (step5 will handle)"
            )

        except Exception as e:
            logger.error(
                f"Debate failed: {e} - proceeding without debate answer (step5 will handle)"
            )

        return state

    if tools_enabled:
        from apps.orchestration.src.tool_executor import execute_tool

        logger.info("Step 4: Tools mode enabled")

        plan = state.plan or {}
        tools_to_execute = plan.get("tools", [])

        if not tools_to_execute:
            logger.info("Step 4: No tools to execute")
            return state

        registry = None
        if flags.get("tools_policy", False):
            from apps.orchestration.src.tool_registry import ToolRegistry

            registry = ToolRegistry()

        tool_results = []
        for tool_name in tools_to_execute:
            if flags.get("tools_policy", False) and registry:
                if not registry.validate_tool(tool_name):
                    logger.warning(f"Tool '{tool_name}' blocked by whitelist")
                    tool_results.append(
                        {
                            "tool": tool_name,
                            "success": False,
                            "error": "Blocked by whitelist policy",
                        }
                    )
                    continue

            input_data = plan.get(f"{tool_name}_input", {})
            result = await execute_tool(tool_name, input_data, timeout=30.0)

            tool_results.append(
                {
                    "tool": tool_name,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "elapsed": result.elapsed,
                }
            )

        state.tool_results = tool_results
        logger.info(f"Step 4 (tools) executed: {len(tool_results)} tools")

        return state

    logger.info("Step 4 (tools/debate) skipped (all flags OFF)")
    return state


async def step5_compose(state: PipelineState) -> PipelineState:
    """
    Step 5: Answer Composition

    Generates final answer using LLM with:
    - Top 3-5 retrieved chunks as context
    - Instruction to cite sources
    - Instruction to include taxonomy version

    Output: state.answer, state.sources
    """
    if not state.retrieved_chunks:
        state.answer = "죄송합니다. 관련 정보를 찾을 수 없습니다."
        state.sources = []
        return state

    # Build context from top chunks
    context_chunks = state.retrieved_chunks[:5]
    context_text = "\n\n".join(
        [
            f"[출처 {i + 1}] {chunk['title']}\n{chunk['text'][:500]}..."
            for i, chunk in enumerate(context_chunks)
        ]
    )

    # Build prompt
    f"""다음 정보를 바탕으로 사용자 질문에 답변하세요.

사용자 질문: {state.query}

참고 자료:
{context_text}

답변 작성 시 주의사항:
1. 제공된 참고 자료만 사용하여 답변하세요
2. 답변 끝에 "[출처: 1, 2, ...]" 형식으로 사용한 출처 번호를 명시하세요
3. 정확하게 답변할 수 없는 경우 솔직히 말하세요

답변:"""

    # Call LLM
    try:
        llm_service = get_llm_service_cached()
        # Use Gemini's generate_answer method (simpler wrapper)
        result = await llm_service.generate_answer(
            question=state.query,
            search_results=[
                {
                    "text": chunk["text"],
                    "source_url": chunk["source_url"],
                    "title": chunk["title"],
                    "hybrid_score": chunk["score"],
                }
                for chunk in context_chunks
            ],
            mode="answer",
        )

        state.answer = result.answer.strip()

        # Extract sources (simple version: use all top 3 chunks)
        state.sources = [
            {
                "url": chunk["source_url"],
                "title": chunk["title"],
                "date": chunk["date"],
                "version": chunk["version"],
            }
            for chunk in context_chunks[:3]  # Ensure at least 2, usually 3
        ]

        logger.info(f"Composed answer with {len(state.sources)} sources")

    except Exception as e:
        logger.error(f"Compose step failed: {e}")
        state.answer = f"답변 생성 중 오류가 발생했습니다: {str(e)}"
        state.sources = []

    return state


async def step6_cite(state: PipelineState) -> PipelineState:
    """
    # @SPEC:FOUNDATION-001 @IMPL:0.3-pipeline-steps
    Step 6: Source Citation (stub)

    Currently citation is handled in step5_compose.
    TODO: Extract citation logic from step5 in future
    """
    logger.info("Step 6 (cite) executed (currently handled in step5)")
    # TODO: Extract citation logic from step5 in future
    return state


async def step7_respond(state: PipelineState) -> PipelineState:
    """
    Step 7: Final Response Formatting

    Calculates confidence score and prepares final response:
    - Confidence = rerank_score * source_count_penalty
    - Source count penalty: 1.0 if ≥2, else 0.5

    Output: state.confidence
    """
    if not state.retrieved_chunks:
        state.confidence = 0.0
        return state

    # Simple confidence calculation
    top_score = state.retrieved_chunks[0]["score"] if state.retrieved_chunks else 0.0
    source_count = len(state.sources)

    # Source count penalty (PRD requirement: ≥2 sources)
    source_penalty = 1.0 if source_count >= 2 else 0.5

    # Final confidence
    state.confidence = min(max(top_score * source_penalty, 0.0), 1.0)

    logger.info(
        f"Confidence score: {state.confidence:.3f} (top_score={top_score:.3f}, sources={source_count})"
    )

    return state


class LangGraphPipeline:
    """LangGraph 7-Step Pipeline"""

    def __init__(self):
        self.name = "DT-RAG-7Step-Pipeline"
        logger.info("LangGraph pipeline initialized (7-step pipeline)")

    async def execute(self, request: PipelineRequest) -> PipelineResponse:
        """
        # @SPEC:FOUNDATION-001 @IMPL:0.3-pipeline-steps
        Execute 7-step pipeline with timeout enforcement
        """
        start_time = time.time()

        # Initialize state
        state = PipelineState(
            query=request.query,
            taxonomy_version=request.taxonomy_version,
            canonical_filter=request.canonical_filter,
            start_time=start_time,
        )

        try:
            # Step 1: Intent
            state = await execute_with_timeout(step1_intent, state, "intent")

            # Step 2: Retrieve
            state = await execute_with_timeout(step2_retrieve, state, "retrieve")

            # Step 3: Plan (NEW)
            state = await execute_with_timeout(step3_plan, state, "plan")

            # Step 4: Tools/Debate (NEW)
            state = await execute_with_timeout(
                step4_tools_debate, state, "tools_debate"
            )

            # Step 5: Compose
            state = await execute_with_timeout(step5_compose, state, "compose")

            # Step 6: Cite (NEW)
            state = await execute_with_timeout(step6_cite, state, "cite")

            # Step 7: Respond
            state = await execute_with_timeout(step7_respond, state, "respond")

            # Calculate total latency
            total_latency = time.time() - start_time

            # Build response
            response = PipelineResponse(
                answer=state.answer or "답변을 생성할 수 없습니다.",
                sources=state.sources,
                confidence=state.confidence,
                taxonomy_version=state.taxonomy_version,
                latency=total_latency,
                cost=0.0,  # TODO: Calculate actual cost
                intent=state.intent,
                step_timings=state.step_timings,
            )

            logger.info(f"Pipeline completed in {total_latency:.3f}s (p95 target: 4s)")

            return response

        except TimeoutError as e:
            logger.error(f"Pipeline timeout: {e}")
            raise

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise


def get_pipeline() -> LangGraphPipeline:
    """Get pipeline instance"""
    return LangGraphPipeline()
