# SPEC-FOUNDATION-001 수락 기준

## Given-When-Then 시나리오

### 시나리오 1: Feature Flag 추가

**Given**: `apps/api/env_manager.py`의 `get_feature_flags()` 메서드가 존재한다
**When**: 메서드를 호출한다
**Then**: 다음 7개 Flag가 포함되어야 한다:
- `neural_case_selector: False`
- `soft_q_bandit: False`
- `debate_mode: False`
- `tools_policy: False`
- `meta_planner: False`
- `mcp_tools: False`
- `experience_replay: False`

### 시나리오 2: Feature Flag 환경 변수 Override

**Given**: 환경 변수 `FEATURE_DEBATE_MODE=true`가 설정되어 있다
**When**: `get_feature_flags()`를 호출한다
**Then**: `debate_mode` Flag가 `True`를 반환해야 한다

### 시나리오 3: CaseBank 임베딩 생성 (정상)

**Given**: `add_case({"query": "test query", ...})` 호출
**When**: 임베딩 생성이 성공한다
**Then**:
- `query_vector` 필드에 1536차원 벡터가 저장되어야 한다
- 벡터의 모든 요소가 0.0이 아니어야 한다

### 시나리오 4: CaseBank 임베딩 생성 (실패)

**Given**: 임베딩 API가 실패한다
**When**: `add_case()` 호출
**Then**:
- `query_vector` 필드에 더미 벡터 `[0.0] * 1536`이 저장되어야 한다
- 경고 로그가 기록되어야 한다

### 시나리오 5: Pipeline Step3 스킵 (Flag OFF)

**Given**: `meta_planner` Flag가 `False`이다
**When**: 파이프라인 실행
**Then**:
- step3_plan()이 스킵되어야 한다
- 로그에 "Step 3 (plan) skipped (feature flag OFF)" 메시지가 기록되어야 한다

### 시나리오 6: Pipeline Step3 실행 (Flag ON)

**Given**: `meta_planner` Flag가 `True`이다
**When**: 파이프라인 실행
**Then**:
- step3_plan()이 실행되어야 한다
- 로그에 "Step 3 (plan) executed (stub)" 메시지가 기록되어야 한다

### 시나리오 7: Pipeline Step4 스킵 (모든 Flag OFF)

**Given**: `debate_mode`와 `tools_policy` Flag가 모두 `False`이다
**When**: 파이프라인 실행
**Then**:
- step4_tools_debate()이 스킵되어야 한다
- 로그에 "Step 4 (tools/debate) skipped (feature flags OFF)" 메시지가 기록되어야 한다

### 시나리오 8: Pipeline Step4 실행 (Debate Flag ON)

**Given**: `debate_mode` Flag가 `True`이다
**When**: 파이프라인 실행
**Then**:
- step4_tools_debate()이 실행되어야 한다
- 로그에 "Step 4 (tools/debate) executed (stub)" 메시지가 기록되어야 한다

### 시나리오 9: Pipeline 7-Step 순차 실행

**Given**: 모든 Feature Flag가 `False`이다
**When**: 파이프라인 실행
**Then**: 다음 순서로 실행되어야 한다:
1. step1_intent
2. step2_retrieve
3. step3_plan (스킵)
4. step4_tools_debate (스킵)
5. step5_compose
6. step6_cite (스킵)
7. step7_respond

### 시나리오 10: 기존 4-Step 회귀 없음

**Given**: Feature Flag가 모두 `False`이다
**When**: 기존 테스트 케이스 실행
**Then**:
- 모든 기존 테스트가 통과해야 한다
- p95 latency ≤ 4s 유지

### 시나리오 11: 기존 Feature Flag 동작 불변

**Given**: 기존 Flag (enable_swagger_ui, enable_metrics 등)가 있다
**When**: 새로운 7개 Flag 추가 후 `get_feature_flags()` 호출
**Then**: 기존 Flag 값이 변경되지 않아야 한다

### 시나리오 12: CaseBank 스키마 불변

**Given**: CaseBank 테이블이 존재한다
**When**: `generate_case_embedding()` 메서드 추가
**Then**:
- 테이블 스키마가 변경되지 않아야 한다
- 기존 레코드가 영향받지 않아야 한다

## 비기능 요구사항

### 성능
- Feature Flag 조회: < 1ms
- 임베딩 생성: < 500ms (OpenAI API 포함)
- Pipeline 전체 실행: p95 ≤ 4s (기존 목표 유지)

### 호환성
- 기존 4-step 파이프라인 100% 호환
- CaseBank 기존 데이터 100% 호환

### 테스트 커버리지
- 단위 테스트: 90%+
- 통합 테스트: 주요 시나리오 100% 커버
