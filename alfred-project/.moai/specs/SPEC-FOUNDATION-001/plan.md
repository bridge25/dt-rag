# SPEC-FOUNDATION-001 구현 계획

## 개요
- **SPEC ID**: FOUNDATION-001
- **우선순위**: Critical
- **작업 순서**: 0.1 → 0.2 → 0.3 (순차)

## 작업 분할

### 0.1 Feature Flag 시스템 강화 (독립 작업)

**파일**: `apps/api/env_manager.py`

**구현 단계**:
1. `get_feature_flags()` 메서드 수정
2. 7개 Flag 추가 (PRD 1.5P 4개 + Memento 3개)
3. 환경 변수 Override 로직 추가
4. 단위 테스트 작성 (`tests/unit/test_feature_flags.py`)

**리스크**: 없음 (기존 Flag와 독립적)

### 0.2 CaseBank Vector 활성화 (0.1 선행 권장)

**파일**: `apps/api/database.py`, `apps/orchestration/src/main.py`

**구현 단계**:
1. `generate_case_embedding()` 메서드 구현
   - EmbeddingService 호출
   - 에러 처리 (더미 벡터 폴백)
2. `add_case()` 메서드 수정
   - 임베딩 생성 호출
   - query_vector 필드에 저장
3. 단위 테스트 작성 (`tests/unit/test_case_embedding.py`)
   - 정상 케이스: 1536차원 벡터 검증
   - 실패 케이스: 더미 벡터 + 경고 로그 검증

**리스크**:
- 임베딩 API 실패 → 더미 벡터 폴백으로 완화
- OpenAI API 비용 발생 (테스트 시 주의)

### 0.3 Pipeline Step 스텁 구현 (0.1 선행 필수)

**파일**: `apps/orchestration/src/langgraph_pipeline.py`

**구현 단계**:
1. `step3_plan()` 스텁 구현
   - meta_planner flag 확인
   - 로그 기록
2. `step4_tools_debate()` 스텁 구현
   - debate_mode, tools_policy flag 확인
   - 로그 기록
3. `step6_cite()` 스텁 구현
   - 현재는 pass (step5에서 처리)
4. `LangGraphPipeline.execute()` 수정
   - 7-step 순차 실행
   - STEP_TIMEOUTS 업데이트
5. 통합 테스트 수정 (`tests/integration/test_pipeline_steps.py`)
   - Flag OFF: Step 스킵 검증
   - Flag ON: Step 실행 검증 (로그)
   - 기존 4-step 회귀 없음 검증

**리스크**:
- 기존 파이프라인 회귀 → 통합 테스트로 완화
- Timeout 설정 부적절 → 실측 후 조정

## 의존성 그래프

```
0.1 Feature Flag
    ↓ (권장)
0.2 CaseBank Vector
    ↓ (필수)
0.3 Pipeline Steps
```

## 검증 계획

### 단위 테스트
- `test_feature_flags.py`: Flag 기본값, Override 동작
- `test_case_embedding.py`: 임베딩 생성, 실패 폴백

### 통합 테스트
- `test_pipeline_steps.py`: 7-step 실행, Flag 기반 스킵

### 수동 테스트
- Feature Flag 환경 변수 설정 후 파이프라인 실행
- CaseBank에 케이스 추가 후 query_vector 확인

## 롤백 계획

- Git 브랜치: `feature/SPEC-FOUNDATION-001`
- 문제 발생 시: 브랜치 삭제 후 `feat/dt-rag-v1.8.1-implementation`로 복귀
- 데이터베이스: CaseBank 스키마 변경 없으므로 롤백 불필요
