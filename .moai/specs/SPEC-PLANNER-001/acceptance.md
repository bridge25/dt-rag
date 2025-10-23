# @SPEC:PLANNER-001 인수 기준 (Acceptance Criteria)

## 개요
Meta-Planner 구현의 완료 조건과 품질 게이트를 정의합니다. 모든 테스트 시나리오는 Given-When-Then 형식으로 작성됩니다.

---

## Given-When-Then 시나리오

### 시나리오 1: 단순 쿼리 처리
**Given**:
- `meta_planner` flag가 True로 설정됨
- 사용자 쿼리: "보일러 고장 사례 찾아줘"
- 복잡도 분석 결과: "simple"

**When**:
- step3_plan()이 실행됨
- LLM이 전략을 반환함

**Then**:
- PipelineState에 `planner_output`이 저장됨
- `planner_output["strategy"]` == "simple"
- `planner_output["tools"]` == ["case_search"]
- step4로 정상 진행됨

**검증 방법**:
```python
# tests/integration/test_pipeline_steps.py
async def test_step3_simple_query():
    state = {
        "query": "보일러 고장 사례 찾아줘",
        "feature_flags": {"meta_planner": True}
    }
    result = await step3_plan(state)

    assert "planner_output" in result
    assert result["planner_output"]["strategy"] == "simple"
    assert "case_search" in result["planner_output"]["tools"]
```

---

### 시나리오 2: 복잡한 쿼리 처리
**Given**:
- `meta_planner` flag가 True로 설정됨
- 사용자 쿼리: "A와 B 제품의 성능을 비교 분석하고 예측해줘"
- 복잡도 분석 결과: "complex"

**When**:
- step3_plan()이 실행됨
- LLM이 복잡 전략을 반환함

**Then**:
- `planner_output["strategy"]` == "complex"
- `planner_output["tools"]` == ["case_search", "external_api", "analysis"]
- step4에서 모든 도구 병렬 호출됨

**검증 방법**:
```python
async def test_step3_complex_query():
    state = {
        "query": "A와 B 제품의 성능을 비교 분석하고 예측해줘",
        "feature_flags": {"meta_planner": True}
    }
    result = await step3_plan(state)

    assert result["planner_output"]["strategy"] == "complex"
    assert len(result["planner_output"]["tools"]) >= 2
    assert "analysis" in result["planner_output"]["tools"]
```

---

### 시나리오 3: Flag OFF 시 스킵
**Given**:
- `meta_planner` flag가 False로 설정됨
- 사용자 쿼리: "아무 쿼리"

**When**:
- step3_plan()이 호출됨

**Then**:
- step3이 즉시 스킵됨
- `planner_output`이 State에 추가되지 않음
- step4로 바로 진행됨
- 로그에 "[step3] meta_planner OFF, skipping" 기록됨

**검증 방법**:
```python
async def test_step3_flag_off():
    state = {
        "query": "test",
        "feature_flags": {"meta_planner": False}
    }
    result = await step3_plan(state)

    assert "planner_output" not in result
    # 로그 검증
    assert "[step3] meta_planner OFF" in captured_logs
```

---

### 시나리오 4: Fallback 동작
**Given**:
- `meta_planner` flag가 True로 설정됨
- LLM API가 10초 이상 응답하지 않음 (타임아웃)

**When**:
- step3_plan()이 실행됨
- `asyncio.wait_for()`가 TimeoutError를 발생시킴

**Then**:
- Fallback 전략이 적용됨
- `planner_output["strategy"]` == "fallback"
- `planner_output["tools"]` == ["all"]
- 로그에 "[step3] Planner timeout, using fallback" 기록됨
- 파이프라인이 중단되지 않고 step4로 진행됨

**검증 방법**:
```python
async def test_step3_timeout_fallback():
    # Mock: LLM API 타임아웃 시뮬레이션
    with patch("call_planner_llm", side_effect=TimeoutError):
        state = {
            "query": "test",
            "feature_flags": {"meta_planner": True}
        }
        result = await step3_plan(state)

    assert result["planner_output"]["strategy"] == "fallback"
    assert result["planner_output"]["tools"] == ["all"]
    assert "[step3] Planner timeout" in captured_logs
```

---

## 품질 게이트

### 1. 테스트 커버리지
**기준**:
- 신규 코드 커버리지 100% (step3_plan, analyze_query_complexity, call_planner_llm)
- 전체 파이프라인 커버리지 35% 이상 (기존 34% 유지)

**검증 명령**:
```bash
pytest --cov=apps/orchestration --cov-report=term-missing
```

### 2. 타임아웃 준수
**기준**:
- LLM 호출 타임아웃 10초 이내
- 전체 step3 실행 시간 15초 이내

**검증 방법**:
```python
import time

start = time.time()
await step3_plan(state)
elapsed = time.time() - start

assert elapsed < 15.0
```

### 3. 회귀 방지
**기준**:
- 기존 Step(1, 2, 4, 5, 6, 7) 동작 변경 없음
- 기존 17개 테스트 모두 통과

**검증 명령**:
```bash
pytest tests/integration/test_pipeline_steps.py -v
```

---

## 검증 방법 및 도구

### 단위 테스트
**도구**: pytest

**파일**: `tests/unit/test_meta_planner.py`

**커버리지**:
- `analyze_query_complexity()` 10개 케이스
- `call_planner_llm()` 5개 케이스 (성공, 실패, 타임아웃)

### 통합 테스트
**도구**: pytest + pytest-asyncio

**파일**: `tests/integration/test_pipeline_steps.py`

**시나리오**: 위 4개 Given-When-Then 시나리오

### 성능 테스트
**도구**: pytest-benchmark

**측정 항목**:
- step3 평균 실행 시간
- LLM API 응답 시간 분포

---

## 완료 조건 (Definition of Done)

### 코드 구현
- [ ] `analyze_query_complexity()` 구현 완료
- [ ] `call_planner_llm()` 구현 완료
- [ ] `step3_plan()` 스텁 → 실제 로직 교체
- [ ] Fallback 전략 구현

### 테스트
- [ ] 단위 테스트 15개 통과
- [ ] 통합 테스트 4개 시나리오 통과
- [ ] 기존 17개 테스트 회귀 없음
- [ ] 커버리지 100% (신규 코드)

### 문서
- [ ] spec.md HISTORY 섹션 업데이트
- [ ] plan.md 구현 완료 기록
- [ ] acceptance.md 시나리오 결과 기록

### 코드 리뷰
- [ ] Linter 통과 (ruff, mypy)
- [ ] 보안 검증 (bandit)
- [ ] 동료 리뷰 승인 (최소 1명)

### 배포 준비
- [ ] Feature Flag `meta_planner` 환경 변수 문서화
- [ ] LLM API 타임아웃 설정 문서화
- [ ] 모니터링 메트릭 추가 (타임아웃 빈도, 전략 분포)

---

## 성공 지표 (KPI)

### 즉시 측정 가능한 지표
1. **Planner 성공률**: LLM 호출 성공 비율 ≥ 95%
2. **평균 응답 시간**: step3 실행 시간 < 5초
3. **Fallback 비율**: 타임아웃으로 인한 Fallback < 5%

### 장기 측정 지표
1. **전략 정확도**: 사용자 피드백 기반 전략 적합성 ≥ 80%
2. **도구 사용 효율**: 불필요한 도구 호출 < 10%

---

## 롤백 조건

다음 경우 `meta_planner` flag를 OFF로 전환:
1. Planner 성공률 < 90% (24시간 평균)
2. Fallback 비율 > 20% (1시간 평균)
3. step3 평균 실행 시간 > 10초

**롤백 절차**:
```bash
# 환경 변수 설정
export FEATURE_META_PLANNER=false

# 서비스 재시작
systemctl restart orchestration-service
```

---

**TAG**: @ACCEPT:PLANNER-001
