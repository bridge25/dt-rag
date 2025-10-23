# SPEC-DEBATE-001: Acceptance Criteria

## Overview

Multi-Agent Debate Mode의 인수 기준입니다. Given-When-Then 형식의 테스트 시나리오로 구성되며, 모든 시나리오가 통과해야 Phase 3.2가 완료됩니다.

## Scenario 1: 2-Agent Debate Round 1 실행

### Given
- debate_mode=true로 설정
- step2_retrieve에서 5개 chunks 검색 완료
- step4_tools_debate 진입

### When
- DebateEngine.run_debate() 호출
- Round 1 시작: Affirmative와 Critical 에이전트가 독립 답변 생성

### Then
- [ ] Affirmative 에이전트가 답변 A1 생성 (LLM 호출 1)
- [ ] Critical 에이전트가 답변 C1 생성 (LLM 호출 2)
- [ ] 두 답변이 각각 500 토큰 이하
- [ ] 두 답변이 병렬 실행 (총 소요 시간 < max(A1, C1) + 오버헤드)
- [ ] state.debate_result.llm_calls == 2

### Test Code
```python
async def test_round1_independent_answers():
    """Round 1에서 2개 에이전트가 독립적으로 답변 생성"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="What is RAG?",
        context=[
            {"text": "RAG is Retrieval-Augmented Generation..."},
            {"text": "RAG combines retrieval and generation..."}
        ],
        max_rounds=1
    )

    # Assertions
    assert result.affirmative_answer is not None
    assert result.critical_answer is not None
    assert len(result.affirmative_answer.split()) <= 500
    assert len(result.critical_answer.split()) <= 500
    assert result.llm_calls == 2
    assert result.rounds == 1
```

---

## Scenario 2: Critique Round (Round 2) 실행

### Given
- Round 1 완료 (A1, C1 답변 존재)
- max_rounds=2로 설정

### When
- Round 2 시작: 각 에이전트가 상대 답변을 참조하여 개선

### Then
- [ ] Affirmative 에이전트가 C1을 참조하여 A2 생성 (LLM 호출 3)
- [ ] Critical 에이전트가 A1을 참조하여 C2 생성 (LLM 호출 4)
- [ ] A2와 C2가 각각 상대 답변의 valid points 반영
- [ ] A2와 C2가 각각 500 토큰 이하
- [ ] state.debate_result.llm_calls == 4

### Test Code
```python
async def test_round2_critique():
    """Round 2에서 상대 답변을 참조하여 개선"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="What is RAG?",
        context=[{"text": "RAG is..."}],
        max_rounds=2
    )

    # Assertions
    assert result.llm_calls == 4  # Round 1 (2) + Round 2 (2)
    assert result.rounds == 2
    assert result.affirmative_answer is not None
    assert result.critical_answer is not None

    # Round 2 답변이 Round 1 답변과 다름 (개선됨)
    # (실제 테스트에서는 mock을 사용하여 검증)
```

---

## Scenario 3: Final Synthesis 생성

### Given
- Round 2 완료 (A2, C2 답변 존재)
- Synthesis 단계 진입

### When
- Synthesizer가 A2와 C2를 통합하여 최종 답변 생성

### Then
- [ ] Synthesizer가 A2와 C2를 참조한 final_answer 생성 (LLM 호출 5)
- [ ] final_answer가 800 토큰 이하
- [ ] final_answer가 양측 관점을 균형있게 반영
- [ ] state.answer == result.final_answer
- [ ] state.debate_result.llm_calls == 5

### Test Code
```python
async def test_synthesis():
    """Synthesis가 2개 답변을 통합"""
    engine = DebateEngine()
    result = await engine.run_debate(
        query="What is RAG?",
        context=[{"text": "RAG is..."}],
        max_rounds=2
    )

    # Assertions
    assert result.final_answer is not None
    assert len(result.final_answer.split()) <= 800
    assert result.llm_calls == 5  # Round 1 (2) + Round 2 (2) + Synthesis (1)

    # final_answer가 A2와 C2의 내용을 포함하는지 검증
    # (실제 테스트에서는 키워드 매칭 또는 semantic similarity 검증)
```

---

## Scenario 4: Timeout Fallback 처리

### Given
- debate_mode=true로 설정
- step4_tools_debate 타임아웃 10초 설정
- LLM API 응답 지연 발생 (또는 강제 지연)

### When
- Debate 실행 중 10초 타임아웃 발생

### Then
- [ ] TimeoutError 발생
- [ ] step4_tools_debate에서 예외 처리
- [ ] state.answer가 step5의 초기 답변으로 유지
- [ ] 로그에 "Debate timeout - using initial answer" 기록
- [ ] 전체 파이프라인은 정상 완료

### Test Code
```python
async def test_timeout_fallback():
    """10초 타임아웃 발생 시 fallback"""
    engine = DebateEngine()

    # Timeout 강제 발생
    with pytest.raises(TimeoutError):
        await engine.run_debate(
            query="Complex query...",
            context=[{"text": "..."}],
            timeout=0.001  # 1ms 타임아웃 (강제)
        )

async def test_step4_timeout_fallback():
    """step4에서 timeout 시 step5 답변 사용"""
    from apps.orchestration.src.langgraph_pipeline import LangGraphPipeline
    from apps.api.env_manager import get_env_manager

    # Feature Flag ON
    env = get_env_manager()
    env.set_feature_flag("debate_mode", True)

    # Mock DebateEngine to raise TimeoutError
    with patch("apps.orchestration.src.debate.debate_engine.DebateEngine.run_debate") as mock_debate:
        mock_debate.side_effect = TimeoutError("Debate timeout")

        pipeline = LangGraphPipeline()
        response = await pipeline.execute(
            PipelineRequest(query="What is RAG?")
        )

        # Assertions
        assert response.answer is not None  # step5 답변 사용
        assert "debate" not in response.step_timings  # Debate 미완료
```

---

## Scenario 5: Feature Flag OFF 시 스킵

### Given
- debate_mode=false로 설정 (기본값)
- step4_tools_debate 진입

### When
- step4_tools_debate 실행

### Then
- [ ] Feature Flag 체크 통과
- [ ] Debate 로직 스킵
- [ ] 로그에 "Step 4 (debate) skipped (feature flag OFF)" 기록
- [ ] state 변경 없이 반환
- [ ] 다음 step5로 즉시 진행
- [ ] 기존 4-step 파이프라인 동작 유지

### Test Code
```python
async def test_feature_flag_off():
    """debate_mode=false 시 step4 스킵"""
    from apps.orchestration.src.langgraph_pipeline import step4_tools_debate
    from apps.api.env_manager import get_env_manager

    # Feature Flag OFF
    env = get_env_manager()
    env.set_feature_flag("debate_mode", False)

    # Mock state
    state = PipelineState(
        query="What is RAG?",
        retrieved_chunks=[{"text": "..."}]
    )

    # Execute
    result = await step4_tools_debate(state)

    # Assertions
    assert result == state  # state 변경 없음
    assert not hasattr(result, "debate_result")  # Debate 미실행
```

---

## Quality Gates

### Definition of Done (DoD)

모든 시나리오가 다음 조건을 만족해야 완료로 간주:

#### 1. 기능 검증
- [ ] Scenario 1~5 모두 통과
- [ ] Unit Test 커버리지 90% 이상
- [ ] Integration Test 100% 통과
- [ ] E2E Test 100% 통과

#### 2. 성능 검증
- [ ] step4 타임아웃 10초 준수
- [ ] LLM 호출 5회 이하
- [ ] Round 1/2 병렬 실행 확인
- [ ] 기존 4-step 파이프라인 성능 회귀 없음

#### 3. 보안 검증
- [ ] Feature Flag 검증 통과
- [ ] 입력 검증 (query, context)
- [ ] 에러 핸들링 완료
- [ ] 로그에 민감 정보 미포함

#### 4. 품질 검증
- [ ] TRUST 원칙 80% 이상
  - T (Test First): 90% 이상
  - R (Readable): 70% 이상
  - U (Unified): 80% 이상
  - S (Secured): 100%
  - T (Trackable): 100%
- [ ] TAG 체인 무결성 100%
  - @SPEC:DEBATE-001
  - @IMPL:0.1/0.2/0.3/0.4
  - @TEST:0.1/0.2/0.3/0.4

#### 5. 회귀 검증
- [ ] 기존 4-step 파이프라인 테스트 100% 통과
- [ ] debate_mode=false 시 동작 보존
- [ ] step1, step2, step5, step7 영향 없음

### Verification Methods

#### Unit Test
```bash
pytest tests/unit/test_debate_engine.py -v --cov=apps/orchestration/src/debate
```

#### Integration Test
```bash
pytest tests/integration/test_debate_integration.py -v --cov=apps/orchestration
```

#### E2E Test
```bash
pytest tests/integration/test_debate_integration.py::test_debate_e2e -v
```

#### Regression Test
```bash
# 기존 파이프라인 테스트
pytest tests/integration/test_pipeline_steps.py -v

# debate_mode=false 테스트
DEBATE_MODE=false pytest tests/integration/test_debate_integration.py::test_feature_flag_off -v
```

#### Performance Test
```bash
# 타임아웃 검증
pytest tests/integration/test_debate_integration.py::test_timeout_fallback -v

# LLM 호출 횟수 검증
pytest tests/unit/test_debate_engine.py::test_llm_call_count -v
```

---

## Edge Cases

### Edge Case 1: 빈 컨텍스트
- **Given**: context=[]
- **Expected**: Debate 실행하되, 컨텍스트 없이 답변 생성 또는 에러 처리

### Edge Case 2: 매우 긴 쿼리
- **Given**: query 길이 > 1000자
- **Expected**: 쿼리 트리밍 또는 에러 처리

### Edge Case 3: LLM API 실패
- **Given**: LLM API 호출 실패 (500 에러)
- **Expected**: 재시도 또는 fallback (step5 답변 사용)

### Edge Case 4: 답변이 모두 동일
- **Given**: A1 == C1, A2 == C2
- **Expected**: Synthesis가 중복 제거 및 통합

### Edge Case 5: 최대 라운드 초과
- **Given**: max_rounds=10 (비정상적 설정)
- **Expected**: 3 라운드로 제한 (설계상 최대 3)

---

## Rollback Plan

Debate Mode 배포 후 문제 발생 시:

### Step 1: Feature Flag OFF
```python
# .env 또는 환경 변수
DEBATE_MODE=false
```

### Step 2: 기존 4-step 파이프라인으로 복귀
- step4 스킵 확인
- step5 정상 동작 확인

### Step 3: 로그 분석
- Debate 실패 원인 분석
- LLM API 응답 시간 확인
- 에러 패턴 분석

### Step 4: 핫픽스 배포
- 타임아웃 조정
- Fallback 로직 강화
- 에러 핸들링 개선

---

## Success Metrics

### 배포 후 모니터링 지표

#### 1. 기능 지표
- Debate 실행 성공률: 95% 이상
- Fallback 발생률: 5% 이하
- Feature Flag OFF 비율: 10% 이하

#### 2. 성능 지표
- step4 평균 실행 시간: 6~8초
- step4 타임아웃 발생률: 1% 이하
- LLM 호출 횟수: 평균 5회

#### 3. 품질 지표
- 답변 품질 점수: Debate 적용 후 20% 향상
- 사용자 만족도: 4.0/5.0 이상
- 에러 발생률: 0.1% 이하

#### 4. 비용 지표
- LLM API 비용: 기존 대비 5배 증가 (5회 호출)
- 인프라 비용: 기존과 동일 (CPU/메모리 변화 없음)
