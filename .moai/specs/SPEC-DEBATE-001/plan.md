# SPEC-DEBATE-001: Implementation Plan

## Overview

Multi-Agent Debate Mode 구현을 위한 체계적인 실행 계획입니다. TDD 기반으로 Red-Green-Refactor 사이클을 따르며, Phase 3.2 요구사항을 충족합니다.

## Milestones

### 1차 목표: Debate Engine 핵심 구현
- Debate Engine 클래스 설계 및 구현
- Agent Prompts 템플릿 정의
- Unit Test 작성 및 통과 (Red-Green-Refactor)

### 2차 목표: Pipeline 통합
- step4_tools_debate 확장
- Feature Flag 통합
- Fallback 로직 구현

### 3차 목표: 검증 및 최적화
- Integration Test 작성 및 통과
- 기존 파이프라인 회귀 테스트
- 성능 프로파일링 및 최적화

## Technical Approach

### Phase 1: Red (테스트 작성)

**목표**: 실패하는 테스트 먼저 작성

**파일**: `tests/unit/test_debate_engine.py`

**테스트 시나리오**:
```python
# 1. Round 1: 독립 답변 생성
async def test_round1_independent_answers():
    """Round 1에서 2개 에이전트가 독립적으로 답변 생성"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="What is RAG?",
        context=[{"text": "RAG is Retrieval-Augmented Generation..."}],
        max_rounds=1
    )
    assert result.affirmative_answer is not None
    assert result.critical_answer is not None
    assert result.llm_calls == 2  # Round 1만

# 2. Round 2: Critique 및 개선
async def test_round2_critique():
    """Round 2에서 상대 답변을 참조하여 개선"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="What is RAG?",
        context=[{"text": "RAG is..."}],
        max_rounds=2
    )
    assert result.llm_calls == 4  # Round 1 (2) + Round 2 (2)

# 3. Synthesis: 최종 답변 통합
async def test_synthesis():
    """Synthesis가 2개 답변을 통합"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="What is RAG?",
        context=[{"text": "RAG is..."}],
        max_rounds=2
    )
    assert result.final_answer is not None
    assert result.llm_calls == 5  # Round 1 (2) + Round 2 (2) + Synthesis (1)

# 4. Timeout: 10초 초과 시 폴백
async def test_timeout_fallback():
    """10초 타임아웃 발생 시 에러 발생"""
    engine = DebateEngine()
    with pytest.raises(TimeoutError):
        await engine.run_debate(
            query="Complex query...",
            context=[...],
            timeout=0.001  # 강제 타임아웃
        )

# 5. Token Limit: 500 토큰 제한
async def test_token_limit():
    """에이전트 답변이 500 토큰을 초과하지 않음"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="Long query...",
        context=[...]
    )
    assert len(result.affirmative_answer.split()) <= 500
    assert len(result.critical_answer.split()) <= 500
```

### Phase 2: Green (최소 구현)

**목표**: 테스트를 통과하는 최소한의 코드 작성

**파일**: `apps/orchestration/src/debate/debate_engine.py`

**최소 구현**:
```python
from typing import List, Dict, Optional
from pydantic import BaseModel
import asyncio

class DebateResult(BaseModel):
    """Debate 실행 결과"""
    affirmative_answer: str
    critical_answer: str
    final_answer: str
    rounds: int
    llm_calls: int
    elapsed: float

class DebateAgent:
    """Base debate agent"""
    def __init__(self, role: str, max_tokens: int = 500):
        self.role = role
        self.max_tokens = max_tokens

    async def generate_answer(
        self,
        query: str,
        context: List[Dict],
        opponent_answer: Optional[str] = None
    ) -> str:
        """Generate answer (Round 1 or Round 2 with critique)"""
        from apps.api.llm_service import get_llm_service
        from apps.orchestration.src.debate.agent_prompts import (
            get_prompt_r1, get_prompt_r2
        )

        llm = get_llm_service()

        # Round 1: 독립 답변
        if opponent_answer is None:
            prompt = get_prompt_r1(self.role, query, context)
        # Round 2: Critique 및 개선
        else:
            prompt = get_prompt_r2(self.role, query, context, opponent_answer)

        # LLM 호출
        response = await llm.generate_text(
            prompt=prompt,
            max_tokens=self.max_tokens
        )

        return response.text.strip()

class DebateEngine:
    """Main debate orchestrator"""

    async def run_debate(
        self,
        query: str,
        context: List[Dict],
        max_rounds: int = 2,
        timeout: float = 10.0
    ) -> DebateResult:
        """Execute multi-round debate"""
        start = asyncio.get_event_loop().time()
        llm_calls = 0

        # Round 1: 독립 답변 (병렬 실행)
        aff = DebateAgent("affirmative")
        crit = DebateAgent("critical")

        answer_a1, answer_c1 = await asyncio.gather(
            aff.generate_answer(query, context),
            crit.generate_answer(query, context)
        )
        llm_calls += 2

        # Round 2: Critique 및 개선 (병렬 실행)
        answer_a2, answer_c2 = await asyncio.gather(
            aff.generate_answer(query, context, opponent_answer=answer_c1),
            crit.generate_answer(query, context, opponent_answer=answer_a1)
        )
        llm_calls += 2

        # Synthesis: 최종 답변 통합
        final_answer = await self._synthesize(
            query, context, answer_a2, answer_c2
        )
        llm_calls += 1

        elapsed = asyncio.get_event_loop().time() - start

        # Timeout 검증
        if elapsed > timeout:
            raise TimeoutError(f"Debate exceeded timeout: {elapsed:.2f}s > {timeout}s")

        return DebateResult(
            affirmative_answer=answer_a2,
            critical_answer=answer_c2,
            final_answer=final_answer,
            rounds=2,
            llm_calls=llm_calls,
            elapsed=elapsed
        )

    async def _synthesize(
        self,
        query: str,
        context: List[Dict],
        answer_a: str,
        answer_c: str
    ) -> str:
        """Synthesize final answer from both agents"""
        from apps.api.llm_service import get_llm_service
        from apps.orchestration.src.debate.agent_prompts import SYNTHESIS_PROMPT

        llm = get_llm_service()
        prompt = SYNTHESIS_PROMPT.format(
            affirmative_answer=answer_a,
            critical_answer=answer_c
        )

        response = await llm.generate_text(prompt=prompt, max_tokens=800)
        return response.text.strip()
```

**파일**: `apps/orchestration/src/debate/agent_prompts.py`

```python
from typing import List, Dict

def get_prompt_r1(role: str, query: str, context: List[Dict]) -> str:
    """Round 1 prompt (독립 답변)"""
    context_text = "\n".join([c["text"] for c in context[:3]])

    if role == "affirmative":
        return f"""[Role] You are an Affirmative agent. Provide a well-supported answer.

[Task] Answer the following question using the provided context:
Question: {query}

Context:
{context_text}

[Constraints]
- Maximum 500 tokens
- Cite sources
- Be confident but precise
"""
    else:  # critical
        return f"""[Role] You are a Critical agent. Provide a skeptical, alternative perspective.

[Task] Answer the following question, challenging common assumptions:
Question: {query}

Context:
{context_text}

[Constraints]
- Maximum 500 tokens
- Highlight uncertainties
- Question the evidence
"""

def get_prompt_r2(
    role: str,
    query: str,
    context: List[Dict],
    opponent_answer: str
) -> str:
    """Round 2 prompt (Critique 및 개선)"""
    return f"""[Role] You are a {role} agent. Improve your previous answer.

[Task] Review the opponent's answer and refine yours:
Opponent's answer: {opponent_answer}

Question: {query}

[Constraints]
- Address opponent's valid points
- Strengthen weak arguments
- Maximum 500 tokens
"""

SYNTHESIS_PROMPT = """[Role] You are a Synthesizer. Combine the best arguments from both agents.

[Task] Generate the final answer by synthesizing:
Affirmative: {affirmative_answer}
Critical: {critical_answer}

[Constraints]
- Balanced perspective
- Cite sources from both
- Maximum 800 tokens
"""
```

### Phase 3: Refactor (코드 개선)

**목표**: 테스트 통과 후 코드 품질 향상

**리팩토링 항목**:
1. **Timeout 처리 개선**: `asyncio.wait_for()` 사용
2. **에러 핸들링**: LLM API 실패 시 재시도 로직
3. **로깅 강화**: 각 Round별 상세 로그
4. **메트릭 추가**: 답변 품질 점수, 토큰 사용량

**리팩토링 예시**:
```python
async def run_debate(self, ...) -> DebateResult:
    """Execute multi-round debate with timeout"""
    try:
        return await asyncio.wait_for(
            self._run_debate_internal(...),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Debate timeout after {timeout}s")
        raise TimeoutError(...)
```

### Phase 4: Integration

**목표**: step4_tools_debate 통합 및 E2E 테스트

**파일**: `apps/orchestration/src/langgraph_pipeline.py`

**step4 확장**:
```python
async def step4_tools_debate(state: PipelineState) -> PipelineState:
    """Step 4: Tools Execution & Debate"""
    from apps.api.env_manager import get_env_manager
    from apps.orchestration.src.debate.debate_engine import DebateEngine

    flags = get_env_manager().get_feature_flags()

    # Feature Flag 체크
    if not flags.get("debate_mode", False):
        logger.info("Step 4 (debate) skipped (feature flag OFF)")
        return state

    # Debate 실행
    debate_engine = DebateEngine()
    try:
        result = await debate_engine.run_debate(
            query=state.query,
            context=state.retrieved_chunks,
            max_rounds=2,
            timeout=10.0
        )

        # State 업데이트
        state.answer = result.final_answer
        state.debate_result = result

        logger.info(
            f"Debate completed: {result.rounds} rounds, "
            f"{result.llm_calls} LLM calls, {result.elapsed:.2f}s"
        )

    except TimeoutError as e:
        logger.warning(f"Debate timeout: {e} - using initial answer")
        # Fallback: step5의 초기 답변 사용 (state.answer 유지)

    except Exception as e:
        logger.error(f"Debate failed: {e} - using initial answer")
        # Fallback: step5의 초기 답변 사용

    return state
```

**Integration Test**:
```python
# tests/integration/test_debate_integration.py
async def test_debate_e2e():
    """E2E: 전체 7-step 파이프라인 통합 테스트"""
    from apps.orchestration.src.langgraph_pipeline import LangGraphPipeline
    from apps.api.env_manager import get_env_manager

    # Feature Flag ON
    env = get_env_manager()
    env.set_feature_flag("debate_mode", True)

    # Pipeline 실행
    pipeline = LangGraphPipeline()
    response = await pipeline.execute(
        PipelineRequest(query="What is RAG?")
    )

    # 검증
    assert response.answer is not None
    assert "debate" in response.step_timings
    assert response.step_timings["tools_debate"] < 10.0
```

## Architecture Decisions

### Decision 1: 2-Agent vs N-Agent
- **선택**: 2-Agent (Affirmative vs Critical)
- **이유**:
  - 단순성: 2개 에이전트로 충분한 품질 향상 가능
  - 성능: LLM 호출 5회로 제한 (10초 내 완료)
  - 확장성: 필요 시 3-agent로 확장 가능

### Decision 2: Round 수
- **선택**: 2-Round (독립 답변 + Critique)
- **이유**:
  - 1-Round: Critique 없음 (품질 개선 부족)
  - 2-Round: 최적 균형 (품질 vs 성능)
  - 3-Round: 과도한 LLM 호출 (타임아웃 위험)

### Decision 3: Synthesis 방식
- **선택**: LLM 기반 Synthesis (1회 추가 호출)
- **이유**:
  - Rule-based: 단순 병합 (품질 낮음)
  - LLM-based: 지능형 통합 (품질 높음)
  - 성능 영향: 1회 LLM 호출 추가 (~2초)

### Decision 4: Fallback 전략
- **선택**: step5 초기 답변 사용
- **이유**:
  - Debate 실패 시에도 사용자에게 답변 제공
  - 기존 4-step 파이프라인과 동일한 품질 보장
  - 회귀 없음 (기존 동작 보존)

## Risk Mitigation

### Risk 1: LLM API 지연
- **완화 방안**:
  - Round 1/2 병렬 실행 (2배 속도 향상)
  - 10초 타임아웃 강제
  - Fallback: step5 초기 답변 사용

### Risk 2: 토큰 초과
- **완화 방안**:
  - 에이전트 답변 500 토큰 제한
  - LLM max_tokens 파라미터 강제
  - 초과 시 자동 트리밍

### Risk 3: 기존 파이프라인 회귀
- **완화 방안**:
  - Feature Flag 기반 조건부 실행
  - debate_mode=false 시 step4 스킵
  - Integration Test로 회귀 검증

### Risk 4: Debate 품질 저하
- **완화 방안**:
  - 명확한 Agent Role 정의
  - Prompt Engineering 최적화
  - 품질 메트릭 추적 (confidence score)

## Success Criteria

### 기능 요구사항
- [ ] 2-agent debate 구조 구현 완료
- [ ] 2-round 프로세스 정상 동작
- [ ] Final Synthesis 생성 완료
- [ ] Feature Flag 통합 완료
- [ ] Fallback 로직 정상 동작

### 성능 요구사항
- [ ] step4 타임아웃 10초 준수
- [ ] LLM 호출 5회 이하
- [ ] 에이전트당 500 토큰 제한 준수
- [ ] 기존 4-step 파이프라인 회귀 없음

### 품질 요구사항
- [ ] Unit Test 커버리지 90% 이상
- [ ] Integration Test 100% 통과
- [ ] TRUST 원칙 준수 (80% 이상)
- [ ] TAG 체인 무결성 100%

## Next Steps

### 우선순위 High
1. Debate Engine 핵심 구현 (Red-Green-Refactor)
2. Agent Prompts 템플릿 정의
3. Unit Test 작성 및 통과

### 우선순위 Medium
4. step4_tools_debate 확장
5. Feature Flag 통합
6. Integration Test 작성

### 우선순위 Low
7. 성능 프로파일링
8. 품질 메트릭 추적
9. 문서화 및 리뷰
