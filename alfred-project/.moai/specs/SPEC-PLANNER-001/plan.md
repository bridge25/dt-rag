# @SPEC:PLANNER-001 구현 계획서

## 개요
LangGraph step3_plan() 구현을 통해 Meta-Planner를 활성화합니다. 쿼리 복잡도 분석 및 LLM 기반 실행 전략 생성이 핵심 목표입니다.

---

## 마일스톤

### Phase 1.1: 복잡도 분석 엔진
**우선순위**: High

**목표**:
- 쿼리 복잡도 분류 로직 구현 (simple/medium/complex)
- 휴리스틱 규칙 기반 분석

**산출물**:
- `analyze_query_complexity(query: str) -> str` 메서드
- 단위 테스트 (10개 쿼리 샘플)

**의존성**: 없음 (독립 실행 가능)

---

### Phase 1.2: LLM 기반 Planner
**우선순위**: High

**목표**:
- LLM API 호출 및 JSON 파싱
- 프롬프트 설계 및 타임아웃 처리
- Fallback 전략 구현

**산출물**:
- `call_planner_llm(query, complexity)` 메서드
- LLM 프롬프트 템플릿
- 타임아웃 핸들러 (10초)

**의존성**: Phase 1.1 완료 후 진행

---

### Phase 1.3: step3 통합 및 테스트
**우선순위**: High

**목표**:
- step3_plan() 스텁을 실제 로직으로 교체
- PipelineState에 planner_output 저장
- 통합 테스트 (7-Step 파이프라인)

**산출물**:
- `step3_plan()` 완전 구현
- 통합 테스트 (4개 시나리오)
- 기존 Step 회귀 검증

**의존성**: Phase 1.1 + Phase 1.2 완료 후 진행

---

## 기술적 접근 방법

### 1. LLM 프롬프트 설계
**원칙**:
- Few-shot 예제 포함 (3개 샘플)
- JSON 스키마 강제 (Pydantic 모델 사용)
- 복잡도 힌트 제공 (휴리스틱 결과 전달)

**예시 프롬프트**:
```
You are a Meta-Planner for a RAG system.

Query: "비교해줘: A와 B의 차이점"
Complexity: medium

Output JSON:
{
  "strategy": "medium",
  "reasoning": "비교 요청이므로 Case 검색 + 분석 필요",
  "tools": ["case_search", "analysis"]
}
```

### 2. 타임아웃 처리
**구현**:
- `asyncio.wait_for(call_llm(), timeout=10)`
- 타임아웃 시 `TimeoutError` catch
- Fallback: `{"strategy": "fallback", "tools": ["all"]}`

**로그**:
- 성공: `[step3] Plan generated: {strategy}`
- 실패: `[step3] Planner timeout, using fallback`

### 3. Fallback 전략
**목적**: LLM 실패 시 안전한 기본 동작 보장

**전략**:
- 모든 도구 사용 (case_search + external_api)
- step4에서 필터링 (debate_mode flag 참조)

---

## 아키텍처 설계

### PipelineState 확장
**추가 필드**:
```python
{
    "query": str,                    # 기존
    "feature_flags": dict,           # 기존
    "planner_output": {              # 신규
        "strategy": str,
        "reasoning": str,
        "tools": List[str]
    }
}
```

### step3_plan() 구조
```python
async def step3_plan(state: PipelineState) -> PipelineState:
    # 1. Flag 확인
    if not state["feature_flags"].get("meta_planner"):
        return state  # 스킵

    # 2. 복잡도 분석
    complexity = analyze_query_complexity(state["query"])

    # 3. LLM 호출 (타임아웃)
    try:
        plan = await call_planner_llm(state["query"], complexity)
    except TimeoutError:
        plan = fallback_plan()

    # 4. State 업데이트
    state["planner_output"] = plan
    return state
```

---

## 리스크 및 대응 방안

### 리스크 1: LLM 호출 실패
**원인**: API 장애, 네트워크 오류, 크레딧 소진

**대응**:
- Fallback 전략 (모든 도구 사용)
- 재시도 로직 (최대 3회, 지수 백오프)
- 에러 로그 상세 기록

### 리스크 2: 타임아웃 초과
**원인**: LLM 응답 지연 (>10초)

**대응**:
- `asyncio.wait_for()` 강제 중단
- Fallback 자동 적용
- 모니터링 알림 (타임아웃 빈도 추적)

### 리스크 3: 복잡도 오판
**원인**: 휴리스틱 규칙 부정확

**대응**:
- LLM이 최종 전략 결정 (휴리스틱은 힌트로만 사용)
- 사용자 피드백 수집 (향후 개선)
- A/B 테스트 (복잡도 분류 정확도 측정)

---

## 테스트 전략

### 단위 테스트
**대상**: `analyze_query_complexity()`, `call_planner_llm()`

**시나리오**:
- 단순 쿼리 → "simple"
- 비교 쿼리 → "medium"
- 긴 쿼리 (>15단어) → "complex"
- LLM 타임아웃 → Fallback

### 통합 테스트
**대상**: `step3_plan()` + 전체 파이프라인

**시나리오**:
- Flag OFF → step3 스킵
- Flag ON + 단순 쿼리 → Case 검색만 사용
- Flag ON + 복잡 쿼리 → 모든 도구 사용
- LLM 실패 → Fallback 동작

---

## 구현 순서

1. **Phase 1.1**: 복잡도 분석 로직 구현 (휴리스틱)
2. **Phase 1.2**: LLM 프롬프트 설계 및 API 호출
3. **Phase 1.3**: step3_plan() 통합 및 테스트
4. **검증**: 기존 Step 회귀 테스트 (step1~step7)

---

## 다음 단계
- Phase 2A: Neural CBR (step2 확장)
- Phase 2B: MCP Tools (step4 확장)
- Phase 3: Soft-Q/Bandit (step5 확장)

**TAG**: @PLAN:PLANNER-001
