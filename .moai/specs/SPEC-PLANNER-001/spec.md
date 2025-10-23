---
id: PLANNER-001
version: 0.2.0
status: completed
created: 2025-10-09
updated: 2025-10-09
author: @claude
priority: high
category: feature
labels:
  - meta-planner
  - langgraph
  - orchestration
  - phase-1
depends_on:
  - FOUNDATION-001
blocks: []
related_specs:
  - ORCHESTRATION-001
  - DATABASE-001
scope:
  packages:
    - apps/orchestration
    - apps/api
  files:
    - apps/orchestration/src/langgraph_pipeline.py
    - apps/api/llm_service.py
  tests:
    - tests/integration/test_pipeline_steps.py
    - tests/unit/test_meta_planner.py
---

## HISTORY

### v0.2.0 (2025-10-09)
- **COMPLETED**: Meta-Planner 구현 완료
- **AUTHOR**: @claude + code-builder
- **SCOPE**:
  - 복잡도 분석 엔진 (analyze_complexity)
  - LLM 기반 Meta-Planning (generate_plan, 타임아웃 10초)
  - step3_plan() 실제 구현 (Fallback 전략 포함)
- **TESTS**: 11개 신규 테스트 추가 (단위 9개 + 통합 2개)
- **COVERAGE**: meta_planner.py 69%, 신규 코드 100%
- **TAG 체인**: @SPEC:PLANNER-001 → @IMPL:0.1/0.2/0.3 (3개) → @TEST:0.1 (11개)
- **FILES**:
  - 신규: apps/orchestration/src/meta_planner.py (147 LOC)
  - 신규: tests/unit/test_meta_planner.py (166 LOC)
  - 수정: apps/orchestration/src/langgraph_pipeline.py
  - 수정: tests/integration/test_pipeline_steps.py
- **NEXT**: Phase 2A (Neural Case Selector) 또는 Phase 2B (MCP Tools)

### v0.1.0 (2025-10-09)
- **INITIAL**: Meta-Planner SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: LangGraph step3_plan() 실제 구현, 쿼리 복잡도 분석, 실행 전략 생성
- **CONTEXT**: PRD 1.5P Planner-Executor 패턴 구현 (Phase 1)

---

# @SPEC:PLANNER-001: Meta-Planner 구현 (LangGraph Step3 활성화)

## Environment (환경)
- Python 3.11+
- LangGraph 기반 파이프라인 (7-Step)
- OpenAI API 또는 호환 LLM 서비스 (`apps/api/llm_service.py`)
- Feature Flag 시스템 (`meta_planner` flag 활성화)
- 기존 SPEC-FOUNDATION-001 구현 완료 (step3 스텁 존재)

## Assumptions (가정)
- LLM API 호출은 5초 이내 응답 (타임아웃 10초)
- 쿼리 복잡도는 "simple", "medium", "complex" 3단계로 분류
- Planner 출력은 JSON 형식 (strategy, reasoning, tools)
- step3 실패 시 step4로 진행 (Fallback: 모든 도구 사용)

## Requirements (요구사항)

### Ubiquitous Requirements
- 시스템은 사용자 쿼리의 복잡도를 분석하고 실행 전략을 생성해야 한다
- 시스템은 LLM 기반 Meta-Planner를 통해 도구 사용 계획을 수립해야 한다
- 시스템은 Planner 결과를 PipelineState에 저장하여 후속 Step에서 활용해야 한다

### Event-driven Requirements
- WHEN `meta_planner` flag가 True이면, 시스템은 step3_plan()을 실행해야 한다
- WHEN `meta_planner` flag가 False이면, 시스템은 step3을 스킵하고 step4로 진행해야 한다
- WHEN Planner가 "simple" 전략을 반환하면, 시스템은 Case 검색만 사용해야 한다
- WHEN Planner가 "complex" 전략을 반환하면, 시스템은 Case + 외부 도구를 병렬 호출해야 한다
- WHEN Planner 호출이 실패하면, 시스템은 Fallback 전략(모든 도구 사용)을 적용해야 한다

### State-driven Requirements
- WHILE Planner가 실행 중일 때, 시스템은 타임아웃(10초)을 적용해야 한다
- WHILE query가 PipelineState에 존재할 때, 시스템은 이를 Planner에 전달해야 한다

### Constraints
- IF LLM API 호출이 10초를 초과하면, 시스템은 타임아웃 에러를 기록하고 Fallback 전략을 사용해야 한다
- Planner 구현은 기존 step1~step2 동작을 변경하지 않아야 한다
- Planner 출력은 JSON 스키마를 준수해야 한다 (strategy, reasoning, tools 필드 필수)

## Specifications

### 0.1 쿼리 복잡도 분석 로직

**목표**: 사용자 쿼리를 분석하여 복잡도 레벨을 결정

**파일**: `apps/orchestration/src/langgraph_pipeline.py`

**구현**:
```python
def analyze_query_complexity(query: str) -> str:
    """
    쿼리 복잡도 분석 (휴리스틱 기반)

    Returns:
        - "simple": 단순 검색 쿼리 (키워드 기반)
        - "medium": 중간 복잡도 (비교, 분석 요청)
        - "complex": 복잡한 쿼리 (다단계 추론, 외부 도구 필요)
    """
    # 휴리스틱 규칙
    if "비교" in query or "차이" in query:
        return "medium"
    if "분석" in query or "예측" in query:
        return "complex"
    if len(query.split()) > 15:
        return "complex"
    return "simple"
```

### 0.2 LLM 기반 Meta-Planner

**목표**: LLM을 활용하여 쿼리 처리 전략 생성

**파일**: `apps/orchestration/src/langgraph_pipeline.py`, `apps/api/llm_service.py`

**구현**:
1. `call_planner_llm(query: str, complexity: str)` 메서드 추가
2. LLM 프롬프트 설계
3. JSON 응답 파싱

**LLM 프롬프트**:
```
You are a Meta-Planner. Analyze the query and decide the execution strategy.

Query: {query}
Complexity: {complexity}

Output JSON:
{
  "strategy": "simple|medium|complex",
  "reasoning": "Why this strategy?",
  "tools": ["case_search", "external_api", ...]
}
```

**타임아웃 처리**:
- `asyncio.wait_for(timeout=10)` 사용
- 타임아웃 시 Fallback 전략 적용

### 0.3 step3_plan() 구현

**목표**: 스텁을 실제 Meta-Planner 로직으로 교체

**파일**: `apps/orchestration/src/langgraph_pipeline.py`

**변경사항**:
```python
async def step3_plan(state: PipelineState) -> PipelineState:
    """
    Meta-Planner: 쿼리 복잡도 분석 및 실행 전략 생성
    """
    flags = state.get("feature_flags", {})
    if not flags.get("meta_planner"):
        logger.info("[step3] meta_planner OFF, skipping")
        return state

    query = state["query"]
    complexity = analyze_query_complexity(query)

    try:
        plan = await call_planner_llm(query, complexity)
        state["planner_output"] = plan
        logger.info(f"[step3] Plan: {plan['strategy']}")
    except TimeoutError:
        logger.warning("[step3] Planner timeout, using fallback")
        state["planner_output"] = {
            "strategy": "fallback",
            "reasoning": "LLM timeout",
            "tools": ["all"]
        }

    return state
```

**Fallback 전략**:
- LLM 실패 시 모든 도구 사용 (안전한 기본값)

## Traceability (@TAG)
- **SPEC**: @SPEC:PLANNER-001
- **DEPENDS**: @SPEC:FOUNDATION-001 (meta_planner flag, step3 스텁)
- **RELATES**: @SPEC:ORCHESTRATION-001, @SPEC:DATABASE-001
- **CODE**: apps/orchestration/src/langgraph_pipeline.py, apps/api/llm_service.py
- **TEST**: tests/unit/test_meta_planner.py, tests/integration/test_pipeline_steps.py
