---
id: FOUNDATION-001
version: 0.1.0
status: completed
created: 2025-10-09
updated: 2025-10-09
author: @claude
priority: critical
category: enhancement
labels:
  - feature-flags
  - casebank
  - pipeline
  - phase-0
depends_on: []
blocks: []
related_specs:
  - ORCHESTRATION-001
  - DATABASE-001
  - API-001
scope:
  packages:
    - apps/api
    - apps/orchestration
  files:
    - apps/api/env_manager.py
    - apps/api/database.py
    - apps/orchestration/src/langgraph_pipeline.py
    - apps/orchestration/src/main.py
  tests:
    - tests/unit/test_feature_flags.py
    - tests/unit/test_case_embedding.py
    - tests/integration/test_pipeline_steps.py
---

## HISTORY

### v0.1.0 (2025-10-09)
- **INITIAL**: Phase 0 Foundation SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: Feature Flag 시스템 강화, CaseBank Vector 활성화, Pipeline Step 스텁 구현
- **CONTEXT**: PRD 1.5P + Memento 통합을 위한 기반 작업

#### Implementation Completed (2025-10-09)
- **COMPLETED**: Phase 0 Foundation 구현 완료
  - 0.1 Feature Flags: 7개 Flag 추가 및 환경 변수 override 지원
    - 테스트: 7/7 통과 (test_feature_flags.py)
    - 커버리지: 100% (신규 코드)
  - 0.2 CaseBank Vector: 1536차원 임베딩 생성 및 저장, API 실패 시 fallback
    - 테스트: 3/3 통과 (test_case_embedding.py)
    - 커버리지: 100% (신규 코드)
  - 0.3 Pipeline Steps: 7-step 순차 실행 (step3, step4, step6 스텁)
    - 테스트: 7/7 통과 (test_pipeline_steps.py)
    - 기존 4-step 회귀 없음
  - **총 테스트**: 17/17 통과 (100%)
  - **커버리지**: 34% (신규 코드 100%, 기존 코드 보존)
  - **TRUST 품질 검증**: 83% (Warning, Critical 없음)
    - T (Test First): 60%
    - R (Readable): 65%
    - U (Unified): 90%
    - S (Secured): 100%
    - T (Trackable): 100%
  - **TAG 체인 무결성**: 100%
    - @SPEC:FOUNDATION-001 → @IMPL:0.1/0.2/0.3 (8개) → @TEST:0.1/0.2/0.3 (3개)
- **AUTHOR**: @claude + code-builder
- **COMMIT**: a7b6a0c "feat(SPEC-FOUNDATION-001): Implement Phase 0 foundation"
- **NEXT**: Phase 1 (Meta-Planner), Phase 2 (Neural CBR, MCP Tools), Phase 3 (Soft-Q/Bandit)

---

# @SPEC:FOUNDATION-001: Feature Flag 시스템 강화 및 CaseBank Vector 활성화

## Environment (환경)
- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- FastAPI + LangGraph
- 기존 Feature Flag 시스템 (`apps/api/env_manager.py`)
- 기존 CaseBank 테이블 (query_vector 필드 존재)

## Assumptions (가정)
- PRD 1.5P 구현은 이후 Phase에서 진행 (현재는 Flag만 추가)
- CaseBank 테이블 스키마는 변경하지 않음
- 기존 4-step 파이프라인 동작은 보존

## Requirements (요구사항)

### Ubiquitous Requirements
- 시스템은 PRD 1.5P 및 Memento 기능을 위한 7개 Feature Flag를 제공해야 한다
- 시스템은 CaseBank의 query_vector 필드에 임베딩을 저장해야 한다
- 시스템은 LangGraph 7-Step 파이프라인의 미구현 Step에 대한 스텁을 제공해야 한다

### Event-driven Requirements
- WHEN add_case() 메서드가 호출되면, 시스템은 query 텍스트에 대한 임베딩을 생성하고 query_vector에 저장해야 한다
- WHEN Feature Flag가 True이면, 시스템은 해당 Step을 실행해야 한다
- WHEN Feature Flag가 False이면, 시스템은 해당 Step을 스킵하고 다음 Step으로 진행해야 한다

### State-driven Requirements
- WHILE neural_case_selector가 활성화된 상태일 때, 시스템은 CaseBank의 Vector 검색 기능을 사용할 수 있어야 한다
- WHILE debate_mode가 비활성화된 상태일 때, 시스템은 step4를 스킵하고 step5로 진행해야 한다

### Constraints
- IF query_vector 생성 중 오류가 발생하면, 시스템은 더미 벡터 [0.0] * 1536을 저장하고 경고 로그를 기록해야 한다
- Feature Flag 추가 시 기존 Flag 동작을 변경하지 않아야 한다
- Step 스텁 구현 시 기존 Step(1, 2, 5, 7) 동작을 변경하지 않아야 한다

## Specifications

### 0.1 Feature Flag 시스템 강화

**목표**: PRD 1.5P 및 Memento 기능을 위한 7개 Feature Flag 추가

**파일**: `apps/api/env_manager.py`

**변경사항**:
- `get_feature_flags()` 메서드에 7개 Flag 추가
- 환경 변수 기반 Override 지원

**추가할 Flags**:
```python
# PRD 1.5P flags
"neural_case_selector": False,  # Phase 2A: Neural CBR
"soft_q_bandit": False,         # Phase 3: RL-based policy
"debate_mode": False,           # Phase 3: Multi-agent debate
"tools_policy": False,          # Phase 2B: Tool usage policy

# Memento flags
"meta_planner": False,          # Phase 1: Meta-level planning
"mcp_tools": False,             # Phase 2B: MCP protocol tools
"experience_replay": False,     # Phase 3: Experience replay buffer
```

### 0.2 CaseBank Vector 활성화

**목표**: CaseBank의 query_vector 필드를 활성화하여 임베딩 저장

**파일**: `apps/api/database.py`, `apps/orchestration/src/main.py`

**변경사항**:
1. `generate_case_embedding(query: str)` 정적 메서드 구현
2. `add_case()` 메서드에서 임베딩 생성 및 저장

**에러 처리**:
- 임베딩 생성 실패 시 더미 벡터 [0.0] * 1536 사용
- 경고 로그 기록

### 0.3 Pipeline Step 스텁 구현

**목표**: LangGraph 7-Step 파이프라인 완성 (스텁 형태)

**파일**: `apps/orchestration/src/langgraph_pipeline.py`

**변경사항**:
1. `step3_plan()` 스텁 구현 (meta_planner flag 확인)
2. `step4_tools_debate()` 스텁 구현 (debate_mode, tools_policy flag 확인)
3. `step6_cite()` 스텁 구현 (현재는 step5에서 처리)
4. `LangGraphPipeline.execute()` 메서드 수정 (7-step 순차 실행)

**Feature Flag 통합**:
- Flag OFF 시: Step 스킵 + 로그 기록
- Flag ON 시: Step 실행 (스텁 로직)

## Traceability (@TAG)
- **SPEC**: @SPEC:FOUNDATION-001
- **RELATES**: @SPEC:ORCHESTRATION-001, @SPEC:DATABASE-001, @SPEC:API-001
- **CODE**: apps/api/env_manager.py, apps/api/database.py, apps/orchestration/src/langgraph_pipeline.py
- **TEST**: tests/unit/test_feature_flags.py, tests/unit/test_case_embedding.py, tests/integration/test_pipeline_steps.py
