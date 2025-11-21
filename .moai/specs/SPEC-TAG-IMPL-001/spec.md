---
id: TAG-IMPL-001
version: 0.0.1
status: draft
created: 2025-11-21
updated: 2025-11-21
author: "@user"
priority: critical
category: Infrastructure
labels: [tag-system, traceability, documentation]
depends_on: []
blocks: []
related_specs: [TAG-CLEANUP-001]
scope: Backend 138 files + Frontend 122 files + Tests 108 files = ~370 files
---

# @SPEC:TAG-IMPL-001: TAG 시스템 구현 - SPEC-CODE-TEST 추적성 확보

## HISTORY

### v0.0.1 (2025-11-21)
- **INITIAL**: TAG 시스템 구현 명세서 초안 작성
- **AUTHOR**: @user
- **SCOPE**: 코드베이스 전체 (~370개 파일)에 @TAG 참조 추가
- **CONTEXT**: 현재 @TAG 참조 0개, TAG 체인 완성률 21.7%로 추적성 부재 상태. TRUST 5 원칙 준수 및 MoAI-ADK 표준 충족을 위해 체계적인 TAG 시스템 구현 필요

### SUMMARY (English)
This SPEC defines the implementation of a comprehensive @TAG system across the dt-rag-standalone codebase. Currently, there are zero @TAG references in the codebase, with only 21.7% TAG chain completeness. The implementation will add @SPEC, @CODE, @TEST, and @DOC tags to approximately 370 files (138 Python backend + 122 TypeScript frontend + 108 test files), enabling full bidirectional traceability between specifications, implementation code, tests, and documentation.

---

## 1. 개요

### 1.1 배경
현재 dt-rag-standalone 프로젝트는 61개의 SPEC 문서가 존재하지만, 코드베이스 내 @TAG 참조가 전혀 없어 SPEC과 코드/테스트 간의 추적성이 확보되지 않은 상태입니다.

### 1.2 문제 정의
| 항목 | 현재 상태 | 문제점 |
|------|-----------|--------|
| @TAG 참조 | 0개 | 추적 불가 |
| TAG 체인 완성률 | 21.7% | 78.3% 손상 |
| 고아 CODE 태그 | 57개 | SPEC 미연결 |
| 미구현 SPEC | 37개 | 상태 불명확 |

### 1.3 목표
- TAG 체인 완성률: 21.7% → **90%+**
- @TAG 참조 추가: **~370개 파일**
- 고아 CODE 태그: 57개 → **0개**

---

## 2. Requirements (EARS 형식)

### 2.1 Ubiquitous Requirements (항상 참)

**REQ-U1**: 시스템은 모든 구현 코드 파일의 상단에 `@CODE:DOMAIN-NNN` 형식의 TAG 주석을 포함해야 한다.

**REQ-U2**: 시스템은 모든 테스트 파일의 상단에 `@TEST:DOMAIN-NNN` 형식의 TAG 주석을 포함해야 한다.

**REQ-U3**: TAG 체인 (@SPEC → @CODE → @TEST → @DOC)은 양방향 추적이 가능해야 한다.

**REQ-U4**: TAG 형식은 MoAI-ADK 표준을 준수해야 한다:
- `@SPEC:DOMAIN-NNN` - SPEC 문서 참조
- `@CODE:DOMAIN-NNN` - 구현 코드 참조
- `@TEST:DOMAIN-NNN` - 테스트 참조
- `@DOC:DOMAIN-NNN` - 문서 참조

### 2.2 Event-driven Requirements (이벤트 기반)

**REQ-E1**: WHEN 새 코드 파일이 생성되면, THEN 해당 파일에 적절한 @CODE TAG가 추가되어야 한다.

**REQ-E2**: WHEN 새 테스트 파일이 생성되면, THEN 해당 테스트가 검증하는 코드의 @TEST TAG가 추가되어야 한다.

**REQ-E3**: WHEN TAG 검증 스크립트가 실행되면, THEN 다음 정보가 보고되어야 한다:
- TAG 체인 완성률
- 고아 TAG 목록
- 누락된 TAG 목록

**REQ-E4**: WHEN Git 커밋이 수행되면, THEN TAG 인덱스가 자동으로 업데이트되어야 한다.

### 2.3 State-driven Requirements (상태 기반)

**REQ-S1**: WHILE TAG 구현이 진행 중인 동안, THEN 시스템은 Phase별 진행률을 추적해야 한다.

**REQ-S2**: WHILE TAG 체인 완성률이 90% 미만인 동안, THEN CI/CD 파이프라인에서 경고를 표시해야 한다.

**REQ-S3**: WHILE TAG 인덱스가 존재하는 동안, THEN SPEC ID로 관련 파일 검색이 가능해야 한다.

### 2.4 Optional Requirements (선택적 기능)

**REQ-O1**: WHERE 파일이 여러 SPEC과 관련된 경우, THEN 다중 TAG를 지원할 수 있다.
```python
# @CODE:AUTH-001, @CODE:SECURITY-001
```

**REQ-O2**: WHERE 상세 추적이 필요한 경우, THEN 함수/클래스 레벨 TAG를 지원할 수 있다.
```python
def login():  # @CODE:AUTH-001-LOGIN
    pass
```

### 2.5 Unwanted Behaviors (원치 않는 동작)

**REQ-UB1**: IF TAG 형식이 표준(`@TAG_TYPE:DOMAIN-NNN`)과 불일치하면, THEN 검증 스크립트에서 오류를 보고해야 한다.

**REQ-UB2**: IF TAG가 존재하지 않는 SPEC을 참조하면, THEN 고아 TAG로 분류되어야 한다.

**REQ-UB3**: IF TAG 추가 작업이 코드 기능을 변경하면, THEN 해당 변경은 거부되어야 한다 (주석만 허용).

**REQ-UB4**: IF TAG 구현 후 테스트 통과율이 저하되면, THEN 롤백 경고가 발생해야 한다.

---

## 3. 상세 명세

### 3.1 TAG 형식 표준

#### Python 파일 (Backend)
```python
# -*- coding: utf-8 -*-
"""
모듈 설명

@CODE:DOMAIN-NNN
"""
```

#### TypeScript 파일 (Frontend)
```typescript
/**
 * 컴포넌트 설명
 *
 * @CODE:DOMAIN-NNN
 */
```

#### 테스트 파일
```python
"""
테스트 모듈 설명

@TEST:DOMAIN-NNN
"""
```

### 3.2 파일-SPEC 매핑 전략

| 경로 패턴 | 매핑 SPEC 도메인 | 예시 |
|-----------|-----------------|------|
| `apps/api/routers/` | API-001 또는 해당 기능 | `@CODE:API-001` |
| `apps/search/` | SEARCH-001 | `@CODE:SEARCH-001` |
| `apps/orchestration/` | ORCHESTRATION-001 | `@CODE:ORCHESTRATION-001` |
| `apps/classification/` | CLASS-001 | `@CODE:CLASS-001` |
| `apps/agent_system/` | AGENT-GROWTH-* | `@CODE:AGENT-GROWTH-001` |
| `frontend/src/components/agent-card/` | AGENT-CARD-001 | `@CODE:AGENT-CARD-001` |
| `frontend/src/components/taxonomy/` | TAXONOMY-VIZ-001 | `@CODE:TAXONOMY-VIZ-001` |
| `tests/unit/` | 대상 코드의 SPEC | `@TEST:SEARCH-001` |
| `tests/integration/` | 통합 대상 SPEC | `@TEST:API-001` |

### 3.3 TAG 인덱스 구조

```json
// .moai/indexes/tag_catalog.json
{
  "version": "1.0.0",
  "generated_at": "2025-11-21T00:00:00Z",
  "stats": {
    "total_tags": 370,
    "code_tags": 260,
    "test_tags": 108,
    "doc_tags": 2,
    "chain_completeness": 0.90
  },
  "tags": {
    "SEARCH-001": {
      "spec": ".moai/specs/SPEC-SEARCH-001/spec.md",
      "code": [
        "apps/search/hybrid_search_engine.py",
        "apps/search/bm25_engine.py"
      ],
      "tests": [
        "tests/unit/test_hybrid_search.py"
      ],
      "docs": []
    }
  }
}
```

---

## 4. 구현 Phase

### Phase 1: 핵심 Backend 모듈 (P0)
- **범위**: apps/api/, apps/search/ 핵심 파일 (~50개)
- **목표**: 핵심 비즈니스 로직에 TAG 추가
- **검증**: TAG 형식 표준 준수, 테스트 통과

### Phase 2: 나머지 Backend 파일 (P1)
- **범위**: apps/ 나머지 파일 (~88개)
- **목표**: 전체 Backend TAG 완성
- **검증**: Backend TAG 체인 100%

### Phase 3: Frontend 컴포넌트 (P2)
- **범위**: frontend/, apps/frontend/ (~122개)
- **목표**: UI 컴포넌트 TAG 완성
- **검증**: Frontend TAG 체인 100%

### Phase 4: 테스트 파일 (P1)
- **범위**: tests/ (~108개)
- **목표**: 테스트-코드 연결 완성
- **검증**: @TEST → @CODE 매핑 100%

### Phase 5: 자동화 및 CI 통합 (P0)
- **범위**: 검증 스크립트, GitHub Actions
- **목표**: TAG 유지보수 자동화
- **검증**: CI에서 TAG 검증 통과

---

## 5. Traceability (@TAG)

- **SPEC**: @SPEC:TAG-IMPL-001
- **CODE**: (구현 후 추가)
- **TEST**: (구현 후 추가)
- **DOC**: .moai/docs/TAG-GUIDELINES.md (생성 예정)

---

## 6. 제약사항

### 6.1 기술적 제약
- TAG 추가는 **주석으로만** 수행 (코드 기능 변경 금지)
- 기존 테스트 통과율 유지 필수
- MoAI-ADK TAG 형식 표준 준수 필수

### 6.2 운영적 제약
- Phase별 순차 진행 (의존성 고려)
- 각 Phase 완료 시 검증 필수
- Git 커밋으로 모든 변경 추적

---

## 7. 관련 문서

- [SPEC-TAG-CLEANUP-001](.moai/specs/SPEC-TAG-CLEANUP-001/spec.md) - 기존 고아 TAG 정리
- [MoAI-ADK TAG Guide](https://github.com/modu-ai/moai-adk) - TAG 표준 가이드
- [TRUST 5 Principles](CLAUDE.md) - 품질 원칙

---

**문서 작성**: spec-builder agent
**검토 상태**: draft (검토 대기)
