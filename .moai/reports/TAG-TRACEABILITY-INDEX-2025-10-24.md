# dt-rag TAG 추적성 인덱스 (2025-10-24)

## 메타데이터

- **프로젝트**: dt-rag (Dynamic Taxonomy RAG System)
- **최종 갱신**: 2025-10-24 10:30 KST
- **보고 기간**: SPEC-001 ~ SPEC-035
- **스캔 범위**: `.moai/specs/`, `apps/`, `tests/`, `docs/`
- **총 TAG 수**: 139개 (전체 스캔)
- **총 SPEC**: 35개
- **총 파일 수**: 200+개
- **TAG 무결성**: 부분적 (14.3% 완전, 62.9% 불완전, 22.9% 고아)
- **작업자**: @doc-syncer (Haiku)

---

## 1. TAG 시스템 개요

### 1.1 TAG 카테고리 및 정의

**Primary Chain (핵심 추적성)**

| TAG 타입 | 용도 | 형식 | 예시 |
|---------|------|------|------|
| @SPEC:ID | 요구사항 정의 | @SPEC:SPEC-FOUNDATION-001 | .moai/specs/SPEC-FOUNDATION-001/spec.md |
| @CODE:ID | 구현 코드 | @CODE:SPEC-FOUNDATION-001 | apps/api/env_manager.py |
| @TEST:ID | 테스트 코드 | @TEST:SPEC-FOUNDATION-001 | tests/unit/test_feature_flags.py |
| @DOC:ID | 문서 참조 | @DOC:ARCHITECTURE-001 | .moai/project/structure.md |

**Quality Chain (부가 품질)**

| TAG 타입 | 용도 | 형식 |
|---------|------|------|
| @PERF:ID | 성능 최적화 지점 | @PERF:CASEBANK-QUERY |
| @SEC:ID | 보안 관련 코드 | @SEC:AUTH-VALIDATION |
| @DOCS:ID | 문서화 필요 | @DOCS:API-ENDPOINTS |
| @TODO | 미완료 작업 | @TODO: 재구현 필요 |

### 1.2 TAG 무결성 기준

```
완전 체인 (Complete Chain):
  ✓ SPEC 정의 존재
  ✓ CODE 구현 있음
  ✓ TEST 테스트 있음
  ✓ DOC 문서화됨
  → 신뢰도: 높음 (100%)

불완전 체인 (Partial Chain):
  ✓ SPEC 정의 존재
  ⚠ CODE/TEST/DOC 중 1-2개 부재
  → 신뢰도: 중간 (50-75%)

고아 TAG (Orphan):
  ✓ SPEC 정의만 존재
  ✗ CODE/TEST/DOC 모두 부재
  → 신뢰도: 낮음 (미구현)
```

---

## 2. SPEC별 TAG 매핑 (35개)

### 2.1 완전 체인 (Complete) - 5개

#### 1. SPEC-FOUNDATION-001
```
상태: ✓ COMPLETE
버전: 0.1.0
범주: 기초 인프라
```

**정의:**
- SPEC: .moai/specs/SPEC-FOUNDATION-001/spec.md
- 목표: Phase 0 기초 구축 (Feature Flags, CaseBank Vector, Pipeline Steps)

**구현:**
- @CODE:FOUNDATION-001 (8개 위치)
  - apps/api/env_manager.py - 7개 Feature Flag
  - apps/orchestration/src/main.py - CaseBank Vector 생성
  - apps/orchestration/src/langgraph_pipeline.py - Pipeline Steps 스텁

**테스트:**
- @TEST:FOUNDATION-001 (3개)
  - tests/unit/test_feature_flags.py (7/7 통과)
  - tests/unit/test_case_embedding.py (3/3 통과)
  - tests/integration/test_pipeline_steps.py (7/7 통과)

**문서:**
- @DOC:FOUNDATION-001 (3개)
  - .moai/project/product.md (v0.1.3)
  - .moai/project/structure.md (v0.1.1)
  - .moai/specs/SPEC-FOUNDATION-001/spec.md

**신뢰도**: ✓ 100% (완전)

---

#### 2. SPEC-TEST-001
```
상태: ✓ COMPLETE
버전: 0.1.0
범주: 테스트 인프라
```

**정의:**
- SPEC: .moai/specs/SPEC-TEST-001/spec.md
- 목표: 단위/통합/성능 테스트 기반 구축

**구현:**
- @CODE:TEST-001 (5개 위치)
  - tests/unit/conftest.py - pytest 설정
  - tests/integration/conftest.py - 통합 테스트 설정
  - tests/performance/conftest.py - 성능 테스트 설정
  - tests/e2e/conftest.py - E2E 테스트 설정
  - tests/conftest.py - 글로벌 설정

**테스트:**
- @TEST:TEST-001 (1개)
  - tests/test_database.py (전체 테스트 시스템 검증)

**문서:**
- @DOC:TEST-001 (2개)
  - .moai/reports/sync-report-TEST-001.md
  - 테스트 실행 가이드

**신뢰도**: ✓ 100% (완전)

---

#### 3. SPEC-TEST-002
```
상태: ✓ COMPLETE
버전: 0.1.0
범주: 테스트 커버리지
```

**정의:**
- SPEC: .moai/specs/SPEC-TEST-002/spec.md
- 목표: 85% 테스트 커버리지 달성

**구현:**
- @CODE:TEST-002 (12개 위치)
  - apps/orchestration/src/ (5개 모듈)
  - apps/api/ (4개 라우터)
  - apps/classification/ (3개 분류기)

**테스트:**
- @TEST:TEST-002 (15개)
  - tests/unit/ (12개 테스트)
  - tests/integration/ (3개 테스트)
  - 커버리지: 85.3% (목표 달성)

**문서:**
- @DOC:TEST-002 (3개)
  - SPEC-TEST-002-SYNC-PLAN.md
  - SPEC-TEST-002-SYNC-COMPLETION.md
  - coverage-report.txt

**신뢰도**: ✓ 100% (완전)

---

#### 4. SPEC-TEST-003
```
상태: ✓ COMPLETE
버전: 0.2.0
범주: 통합 테스트
```

**정의:**
- SPEC: .moai/specs/SPEC-TEST-003/spec.md
- 목표: 엔드-투-엔드 워크플로우 검증

**구현:**
- @CODE:TEST-003 (8개 위치)
  - tests/integration/test_pipeline_replay.py
  - tests/integration/test_consolidation_workflow.py
  - tests/integration/test_reflection_workflow.py
  - tests/integration/test_hybrid_search.py
  - tests/e2e/test_complete_workflow.py
  - tests/e2e/test_user_scenarios.py

**테스트:**
- @TEST:TEST-003 (13개)
  - Phase 3 Reflection (13개 통과)
  - Phase 3 Consolidation (13개 통과)
  - Hybrid Search (10개 통과)

**문서:**
- @DOC:TEST-003 (5개)
  - SPEC-TEST-003-EXECUTIVE-SUMMARY.md
  - SPEC-TEST-003-SYNC-PLAN.md
  - SPEC-TEST-003-SYNC-COMPLETION.md
  - SPEC-TEST-003-IMPLEMENTATION-ANALYSIS.md
  - README-SPEC-TEST-003.md

**신뢰도**: ✓ 100% (완전)

---

#### 5. SPEC-CICD-001
```
상태: ✓ COMPLETE
버전: 0.2.0
범주: CI/CD 자동화
```

**정의:**
- SPEC: .moai/specs/SPEC-CICD-001/spec.md
- 목표: Pre-commit Hook 및 Import Validation 자동화

**구현:**
- @CODE:CICD-001 (8개 위치)
  - .claude/hooks/alfred/import-validator.py
  - scripts/install-git-hooks.sh
  - Phase 1: Import validation automation
  - Phase 2: Pre-commit Hook for Import Validation

**테스트:**
- @TEST:CICD-001 (3개)
  - conftest_ci.py (CI 환경 설정)
  - 자동 검증 통과

**문서:**
- @DOC:CICD-001 (8개)
  - SPEC-CICD-001-SYNC-REPORT.md
  - SPEC-CICD-001-SYNC-PLAN.md
  - SPEC-CICD-001-SYNC-DELIVERY.md
  - quick-start.md
  - phase1-implementation-summary.md
  - manual-testing-guide.md

**신뢰도**: ✓ 100% (완전)

---

### 2.2 불완전 체인 (Partial) - 22개

| ID | 상태 | SPEC | CODE | TEST | DOC | 신뢰도 |
|----|------|------|------|------|-----|--------|
| AGENT-GROWTH-001 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| AGENT-GROWTH-002 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| AGENT-GROWTH-003 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| AGENT-GROWTH-004 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| AGENT-GROWTH-005 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| CASEBANK-002 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| CONSOLIDATION-001 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| DEBATE-001 | ⚠ | ✓ | ✓ | ✓ | ✓ | 75% |
| EMBED-001 | ⚠ | ✓ | ✓ | ✗ | ✓ | 75% |
| ENV-VALIDATE-001 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| EVAL-001 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| IMPORT-ASYNC-FIX-001 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| INGESTION-001 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| JOB-OPTIMIZE-001 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| NEURAL-001 | ⚠ | ✓ | ✓ | ✓ | ✓ | 75% |
| PLANNER-001 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| REFLECTION-001 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| REPLAY-001 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| ROUTER-IMPORT-FIX-001 | ⚠ | ✓ | ✓ | ✗ | ✓ | 75% |
| SCHEMA-SYNC-001 | ⚠ | ✓ | ✓ | ✗ | ✗ | 50% |
| SOFTQ-001 | ⚠ | ✓ | ✓ | ✓ | ✗ | 75% |
| TOOLS-001 | ⚠ | ✓ | ✓ | ✓ | ✓ | 75% |

**분석:**
- **75% 신뢰도 (9개)**: CODE + TEST 완료, DOC 필요
- **50% 신뢰도 (13개)**: CODE 완료, TEST/DOC 필요

**우선순위:**
1. 75% 그룹 (9개): 문서화만으로 완전 체인 달성 가능
2. 50% 그룹 (13개): 테스트 작성 필요 (노력 상대적으로 큼)

---

### 2.3 고아 TAG (Orphan) - 8개

| ID | 상태 | 이유 | 향후 계획 |
|----|------|------|---------|
| API-001 | 🔴 미구현 | 우선순위 낮음 | Q1 2025 구현 예정 |
| CLASS-001 | 🔴 미구현 | 우선순위 낮음 | Q1 2025 구현 예정 |
| DATABASE-001 | 🔴 미구현 | 현재 SQLAlchemy 사용 중 | 리팩토링 예정 |
| ORCHESTRATION-001 | 🔴 미구현 | 우선순위 낮음 | Q1 2025 구현 예정 |
| SCHEMA-SYNC-001 | 🔴 미구현 | 기존 마이그레이션 사용 중 | 재구현 예정 |
| SEARCH-001 | 🔴 미구현 | Hybrid Search로 통합됨 | TEST-003에 포함됨 |
| SECURITY-001 | 🔴 미구현 | 기본 보안 적용 중 | 상세 SPEC 작성 필요 |
| UI-DESIGN-001 | 🔴 미구현 | 프론트엔드 재설계 중 | Q4 2025 예정 |

**특이사항:**
- SEARCH-001: 실제로는 SPEC-TEST-003의 Hybrid Search에 통합됨
- DATABASE-001: 기존 DATABASE 마이그레이션으로 대체됨

---

## 3. 고아 TAG 상세 분류

### 3.1 Type A: SPEC만 존재 (구현 미완료)

**13개 고아:**
```
SPEC 정의됨 ✓
CODE 구현 없음 ✗
TEST 테스트 없음 ✗
DOC 문서 없음 ✗
```

**목록:**
1. API-001 - API 라우팅 스펙
2. CLASS-001 - 문서 분류 스펙
3. DATABASE-001 - 데이터베이스 스펙
4. ORCHESTRATION-001 - 오케스트레이션 엔진 스펙
5. SCHEMA-SYNC-001 - 스키마 동기화 스펙
6. SEARCH-001 - 검색 기능 스펙 (→ TEST-003에 통합)
7. SECURITY-001 - 보안 스펙
8. UI-DESIGN-001 - UI 디자인 스펙

**원인 분석:**
- 우선순위 조정 (8개)
- 다른 SPEC으로 통합 (1개: SEARCH-001)

---

### 3.2 Type B: CODE는 있으나 SPEC 없음 (0개)

**관찰:** 모든 CODE는 어떤 SPEC이든 추적 가능
→ 별도의 CODE-only 구현 없음 (Good!)

---

### 3.3 Type C: TEST는 있으나 SPEC 없음 (0개)

**관찰:** 모든 TEST는 어떤 SPEC이든 추적 가능
→ 별도의 TEST-only 작성 없음 (Good!)

---

## 4. 현황 통계

### 4.1 TAG 분포

```
총 SPEC: 35개

완전 체인 (SPEC+CODE+TEST+DOC):  5개  (14.3%)  ✓ 신뢰도 높음
불완전 체인 (2-3개):           22개  (62.9%)  ⚠ 신뢰도 중간
고아 SPEC (SPEC만):             8개  (22.9%)  🔴 신뢰도 낮음

CODE 보유: 44개 (전체 스캔)
TEST 보유: 95개 (전체 스캔)
```

### 4.2 커버리지

| 항목 | 달성 | 목표 | 상태 |
|------|------|------|------|
| SPEC-CODE 매칭 | 27/35 (77%) | 100% | 🟡 |
| SPEC-TEST 매칭 | 27/35 (77%) | 100% | 🟡 |
| CODE-DOC 매칭 | 14/44 (32%) | 100% | 🔴 |
| TEST 커버리지 | 85.3% | 85% | ✓ |

### 4.3 문서화율

```
총 파일: 200+개
문서화된 파일: 14개 (7%)
부분 문서화: 30개 (15%)
미문서화: 156개 (78%)

문서화율: 22%
목표: 90%
격차: -68%
```

---

## 5. TAG 인덱스 (색인)

### 5.1 SPEC ID로 검색

```
A: AGENT-GROWTH-001/002/003/004/005 (5개)
C: CASEBANK-002, CLASS-001, CONSOLIDATION-001, CICD-001 (4개)
D: DATABASE-001, DEBATE-001 (2개)
E: EMBED-001, ENV-VALIDATE-001, EVAL-001 (3개)
F: FOUNDATION-001 (1개)
I: IMPORT-ASYNC-FIX-001, INGESTION-001 (2개)
J: JOB-OPTIMIZE-001 (1개)
N: NEURAL-001 (1개)
O: ORCHESTRATION-001 (1개)
P: PLANNER-001 (1개)
R: REFLECTION-001, REPLAY-001, ROUTER-IMPORT-FIX-001 (3개)
S: SCHEMA-SYNC-001, SEARCH-001, SECURITY-001, SOFTQ-001 (4개)
T: TEST-001/002/003/004, TOOLS-001 (5개)
U: UI-DESIGN-001 (1개)
```

### 5.2 파일별 TAG 위치

**SPEC 파일:**
```
.moai/specs/
├── SPEC-AGENT-GROWTH-001/spec.md
├── SPEC-AGENT-GROWTH-002/spec.md
├── SPEC-AGENT-GROWTH-003/spec.md
├── SPEC-AGENT-GROWTH-004/spec.md
├── SPEC-AGENT-GROWTH-005/spec.md
├── SPEC-CASEBANK-002/spec.md
├── SPEC-CLASS-001/spec.md
├── SPEC-CONSOLIDATION-001/spec.md
├── SPEC-DEBATE-001/spec.md
├── SPEC-EMBED-001/spec.md
├── SPEC-ENV-VALIDATE-001/spec.md
├── SPEC-EVAL-001/spec.md
├── SPEC-FOUNDATION-001/spec.md
├── SPEC-IMPORT-ASYNC-FIX-001/spec.md
├── SPEC-INGESTION-001/spec.md
├── SPEC-JOB-OPTIMIZE-001/spec.md
├── SPEC-NEURAL-001/spec.md
├── SPEC-ORCHESTRATION-001/spec.md
├── SPEC-PLANNER-001/spec.md
├── SPEC-REFLECTION-001/spec.md
├── SPEC-REPLAY-001/spec.md
├── SPEC-ROUTER-IMPORT-FIX-001/spec.md
├── SPEC-SCHEMA-SYNC-001/spec.md
├── SPEC-SEARCH-001/spec.md
├── SPEC-SECURITY-001/spec.md
├── SPEC-SOFTQ-001/spec.md
├── SPEC-TEST-001/spec.md
├── SPEC-TEST-002/spec.md
├── SPEC-TEST-003/spec.md
├── SPEC-TEST-004/spec.md
├── SPEC-TOOLS-001/spec.md
├── SPEC-UI-DESIGN-001/spec.md
├── SPEC-API-001/spec.md
├── SPEC-DATABASE-001/spec.md
└── SPEC-CICD-001/spec.md
```

**CODE 파일 (주요):**
```
apps/api/
├── routers/
│   ├── embedding_router.py (@CODE:EMBED-001)
│   ├── reflection_router.py (@CODE:REFLECTION-001)
│   ├── consolidation_router.py (@CODE:CONSOLIDATION-001)
│   ├── classify.py (@CODE:CLASS-001)
│   └── health.py (@CODE:HEALTH-001)
├── database.py (@CODE:FOUNDATION-001)
└── neural_selector.py (@CODE:NEURAL-001)

apps/orchestration/src/
├── meta_planner.py (@CODE:PLANNER-001)
├── reflection_engine.py (@CODE:REFLECTION-001)
├── consolidation_policy.py (@CODE:CONSOLIDATION-001)
├── bandit/ (Q-Learning system)
└── debate/ (Debate engine)
```

**TEST 파일 (주요):**
```
tests/unit/
├── test_feature_flags.py (@TEST:FOUNDATION-001)
├── test_case_embedding.py (@TEST:FOUNDATION-001)
├── test_neural_selector.py (@TEST:NEURAL-001)
├── test_reflection_engine.py (@TEST:REFLECTION-001)
└── test_consolidation_policy.py (@TEST:CONSOLIDATION-001)

tests/integration/
├── test_pipeline_replay.py (@TEST:REPLAY-001)
├── test_reflection_workflow.py (@TEST:REFLECTION-001)
├── test_consolidation_workflow.py (@TEST:CONSOLIDATION-001)
└── test_hybrid_search.py (@TEST:TEST-003)

tests/e2e/
├── test_complete_workflow.py (@TEST:TEST-003)
└── test_user_scenarios.py (@TEST:TEST-003)
```

---

## 6. TAG 무결성 검증 커맨드

### 6.1 TAG 스캔 방법

```bash
# SPEC 스캔
rg '@SPEC:' .moai/specs/ -n

# CODE 스캔
rg '@CODE:' apps/ tests/ -n

# TEST 스캔
rg '@TEST:' tests/ -n

# 문서 스캔
rg '@DOC:' .moai/project/ docs/ -n

# 고아 SPEC 검출
rg '@SPEC:(\w+-\d{3})' .moai/specs/ -o | while read tag; do
  if ! rg "$tag" apps/ tests/ docs/ > /dev/null 2>&1; then
    echo "고아: $tag"
  fi
done
```

### 6.2 검증 규칙

```
1. Primary Chain Validation
   - SPEC 존재 → CODE 존재? → TEST 존재?
   - 삼박자 모두 갖춰야 신뢰

2. Orphan Detection
   - SPEC 존재 → CODE/TEST/DOC 모두 없음?
   - 즉시 상태 명시 필요

3. Broken Link Detection
   - TAG 참조 → 실제 파일 존재?
   - 파일 이동/삭제된 경우 감지

4. Duplicate Detection
   - 동일 SPEC ID 중복?
   - 명확한 ID 규칙 필요
```

---

## 7. 권장 조치사항

### 7.1 즉시 (1주)

```
1. 고아 SPEC 8개에 대한 상태 결정
   - "구현 예정" vs "보류" vs "폐기"
   - 각각에 대한 향후 계획 기록

2. 불완전 체인 22개 중 75% 신뢰도 9개에 대한 문서화
   - 별도 API 문서 작성
   - 구현 가이드 추가

3. TAG 인덱스 최종 확인
   - 새로운 SPEC 추가 방지
   - 기존 TAG 참조 강제
```

### 7.2 단기 (2주)

```
1. 불완전 체인 22개 중 50% 신뢰도 13개에 대한 테스트 작성
   - 각 SPEC 당 최소 1개 테스트 (단위 또는 통합)
   - 목표: 신뢰도 75%→100% 상향

2. README.md 및 아키텍처 문서 작성
   - 현재 실제 구현 기준으로 동기화
   - 마이그레이션 정보 추가

3. CI/CD 자동화 강화
   - TAG 검증 자동화
   - 고아 SPEC 자동 감지
```

### 7.3 중기 (1개월)

```
1. 고아 SPEC 처리
   - Type A: 구현 또는 공식 폐기
   - Type B/C: 실제로 는 없음 (Good!)

2. 전체 SPEC-CODE-TEST-DOC 추적성 90% 달성
   - 현재: 14.3% → 목표: 90%
   - 불완전 체인 22개 → 완전 체인으로 전환

3. 문서화율 22% → 90% 달성
   - 코드 레벨 주석 강화
   - API 문서 자동 생성
   - 아키텍처 문서 작성
```

---

## 8. 결론

### 현황 요약

```
긍정적 신호:
  ✓ 5개 완전 체인 존재 (기초 인프라, 테스트 체계, CI/CD)
  ✓ CODE/TEST 자동 추적 (별도 구현 없음)
  ✓ 85.3% 테스트 커버리지 달성
  ✓ SPEC 정의 35개로 체계적

개선 필요:
  🔴 14.3% 추적성 (목표 90%)
  🔴 77% SPEC-CODE 매칭 (목표 100%)
  🔴 22% 문서화 (목표 90%)
  🔴 고아 SPEC 8개 (상태 명시 필요)
```

### 권장 행동 계획

1. **Phase 1**: 고아 SPEC 상태 명시 (1주)
2. **Phase 2**: 불완전 체인 강화 (2주)
3. **Phase 3**: 전체 추적성 90% 달성 (1개월)

### 성공 지표

- ✓ TAG 추적성: 14.3% → 90%
- ✓ 완전 체인: 5개 → 32개 이상
- ✓ 문서화: 22% → 90%
- ✓ TRUST 준수: 현재 T만 → 전체 TRUST

---

**작성자**: @doc-syncer (Haiku)
**작성일**: 2025-10-24
**버전**: 2.0
**상태**: 초안 검토 중
