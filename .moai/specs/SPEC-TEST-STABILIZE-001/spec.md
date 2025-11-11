# SPEC-TEST-STABILIZE-001: 테스트 안정화 Phase 1 - Reflection API 및 Hybrid Search 빠른 수정

---
id: TEST-STABILIZE-001
version: 0.0.1
status: draft
created: 2025-11-11
updated: 2025-11-11
author: Alfred (MoAI-ADK)
priority: high
type: bugfix
tags: [test-stabilization, reflection-api, hybrid-search, ci-pipeline, quick-fix]
dependencies: []
related_specs: [SPEC-AGENT-ROUTER-BUGFIX-001]
---

## @TAG BLOCK

**Primary TAG**: `@SPEC:TEST-STABILIZE-001`

**Related TAGs**:
- `@SPEC:AGENT-ROUTER-BUGFIX-001` (완료됨: 16/16 테스트 통과)
- `@TEST:REFLECTION-API-FIXTURE` (픽스처 네이밍 불일치)
- `@TEST:HYBRID-SEARCH-AUTH` (인증 우회 누락)

---

## HISTORY

### v0.0.1 (2025-11-11)
- Initial SPEC 작성
- 6개의 빠른 수정 대상 테스트 실패 식별 (4개 Reflection API + 2개 Hybrid Search)
- 픽스처 이름 변경 및 인증 우회 전략 정의
- Phase 1 범위: 20개 실패 중 6개 해결 (30% 안정화)

---

## OVERVIEW

### 배경 및 문맥

PR #24 (Agent Router Bugfix) 구현이 완료되어 모든 16개 테스트가 통과했습니다 (100% 성공률). 그러나 CI 파이프라인은 코드베이스의 다른 부분에서 발생한 20개의 무관한 테스트 실패로 인해 실패합니다. 이 SPEC은 Phase 1 빠른 수정을 다룹니다: 6개의 고영향 실패를 해결하여 30% 안정화를 달성합니다.

### 목표

1. **Reflection API 픽스처 불일치 해결** (4개 테스트)
2. **Hybrid Search 인증 우회 적용** (2개 테스트)
3. **CI 파이프라인 안정성 향상** (68 passed → 74 passed)
4. **회귀 없는 수정 보장** (기존 통과 테스트 유지)

### 범위

**포함 사항**:
- `tests/conftest.py` 픽스처 이름 변경 (`api_client` → `async_client`)
- `tests/integration/test_hybrid_search.py` 인증 우회 적용
- 6개 대상 테스트의 검증 및 확인

**제외 사항**:
- 나머지 14개 테스트 실패 (Phase 2로 연기)
- 프로덕션 코드 변경
- 새로운 기능 추가

---

## ENVIRONMENT (환경 가정)

### 시스템 환경

**E1**: 테스트는 pytest 프레임워크를 사용하여 실행됩니다
**E2**: CI 파이프라인은 GitHub Actions 또는 유사한 환경에서 실행됩니다
**E3**: Python 비동기 테스트는 pytest-asyncio를 사용합니다
**E4**: API 인증은 X-API-Key 헤더 또는 의존성 오버라이드를 통해 우회 가능합니다

### 테스트 환경

**E5**: 통합 테스트는 `tests/integration/` 디렉토리에 위치합니다
**E6**: 공통 픽스처는 `tests/conftest.py`에 정의되어 있습니다
**E7**: FastAPI TestClient는 의존성 주입 오버라이드를 지원합니다
**E8**: 테스트는 병렬 실행 가능 (`pytest -n 4`)합니다

---

## ASSUMPTIONS (전제 조건)

### 기술 가정

**A1**: `tests/conftest.py`의 픽스처 이름 변경은 다른 테스트에 부작용을 일으키지 않습니다
**A2**: Reflection API 테스트는 `async_client` 픽스처를 기대합니다
**A3**: Hybrid Search 엔드포인트는 테스트 환경에서 인증 우회가 필요합니다
**A4**: 현재 68개의 통과 테스트는 올바르게 작동하고 있습니다

### 프로세스 가정

**A5**: 이 수정은 프로덕션 코드에 영향을 주지 않습니다 (테스트 파일만 수정)
**A6**: CI 파이프라인은 수정 후 자동으로 재실행됩니다
**A7**: 픽스처 이름 변경 시 전체 코드베이스 검색이 수행됩니다
**A8**: 인증 우회는 테스트 환경에만 적용되며 프로덕션에 영향을 주지 않습니다

---

## REQUIREMENTS (요구사항)

### Ubiquitous Behaviors (보편적 행동)

**U1**: 모든 통합 테스트는 일관된 픽스처 네이밍 규칙을 따라야 합니다
- `async_client` 표준 사용
- 픽스처 이름 불일치 방지
- 명확한 픽스처 문서화

**U2**: 모든 API 엔드포인트 테스트는 인증 우회 메커니즘을 적용해야 합니다
- 의존성 오버라이드 또는 테스트 API 키 사용
- 403 Forbidden 에러 방지
- 일관된 인증 우회 패턴

### Event-Driven Behaviors (이벤트 기반 행동)

**E1**: WHEN 통합 테스트가 실행될 때
IF `async_client` 픽스처가 요청되면
THEN `tests/conftest.py`의 해당 픽스처가 주입되어야 합니다

**E2**: WHEN Hybrid Search 테스트가 실행될 때
IF API 인증이 필요하면
THEN 테스트 환경에서는 인증을 자동으로 우회해야 합니다

**E3**: WHEN 픽스처 이름이 변경될 때
IF 다른 테스트 파일이 해당 픽스처를 참조하면
THEN 변경 전에 영향 분석이 수행되어야 합니다

### State-Driven Behaviors (상태 기반 행동)

**S1**: WHILE CI 파이프라인이 실행 중일 때
Reflection API 테스트는 픽스처 주입 오류 없이 통과해야 합니다

**S2**: WHILE 로컬 테스트가 실행 중일 때
Hybrid Search 테스트는 403 인증 오류 없이 200 응답을 받아야 합니다

**S3**: WHILE 테스트 스위트가 실행 중일 때
기존 68개 통과 테스트는 여전히 통과 상태를 유지해야 합니다

### Optional Behaviors (선택적 행동)

**O1**: 픽스처 별칭을 추가하여 `api_client`와 `async_client` 모두 지원 가능
- 하위 호환성 유지
- 점진적 마이그레이션 지원

**O2**: 환경 변수를 통해 테스트 API 키를 동적으로 설정 가능
- `.env.test` 파일 지원
- 유연한 테스트 구성

### Unwanted Behaviors (원하지 않는 행동)

**U-1**: 픽스처 이름 변경 시 다른 테스트 파일에 부작용이 발생해서는 안 됩니다
- 전체 코드베이스 검색 필수
- 영향받는 모든 테스트 식별

**U-2**: 인증 우회 로직이 프로덕션 코드에 영향을 주어서는 안 됩니다
- 테스트 환경 격리 유지
- 프로덕션 보안 손상 방지

**U-3**: 수정 후 새로운 테스트 실패가 발생해서는 안 됩니다
- 회귀 테스트 수행
- 전체 테스트 스위트 검증

---

## SPECIFICATIONS (상세 사양)

### Problem 1: Reflection API Fixture Mismatch (4 test failures)

**위치**: `tests/integration/test_phase3_reflection.py`
**근본 원인**: 테스트는 `async_client` 픽스처를 기대하지만 conftest.py는 `api_client`로 정의됨

**영향받는 테스트**:
1. Line 171: `test_reflection_suggestions_authentication`
2. Line 185: `test_reflection_health_check`
3. Line 202: `test_reflection_analyze_performance`
4. Line 225: `test_reflection_batch_performance`

**수정 전략**:
- `tests/conftest.py` Line 122의 픽스처 이름을 `api_client`에서 `async_client`로 변경
- 전체 코드베이스에서 `api_client` 픽스처 참조 검색
- 영향받는 다른 테스트 식별 및 업데이트

**기대 결과**:
- 4개 테스트 모두 픽스처 주입 성공
- ERROR 상태에서 PASSED 상태로 전환
- 테스트 실행 시간 정상화

### Problem 2: Hybrid Search Authentication Bypass (2 test failures)

**위치**: `tests/integration/test_hybrid_search.py`
**근본 원인**: TestClient가 의존성 오버라이드 없이 생성되어 403 인증 오류 발생

**영향받는 테스트**:
1. Line 189-202: Hybrid search without neural reranking
2. Line 204-217: Hybrid search with neural reranking

**수정 전략 (옵션 A - 권장)**:
- `conftest.py`의 `verify_api_key` 의존성 오버라이드 픽스처 적용
- TestClient 생성 시 `app.dependency_overrides` 설정
- 기존 패턴과 일관성 유지

**수정 전략 (옵션 B - 대안)**:
- 테스트 요청에 `X-API-Key` 헤더 추가
- 테스트 환경용 API 키 사용
- 헤더 기반 인증 우회

**기대 결과**:
- 2개 테스트 모두 200 OK 응답 수신
- 403 Forbidden 에러 제거
- 검색 결과 JSON 응답 검증 성공

---

## CONSTRAINTS (제약 조건)

### 기술 제약

**C1**: 프로덕션 코드는 수정하지 않습니다 (테스트 파일만 수정)
**C2**: pytest 및 pytest-asyncio 프레임워크 규칙을 따릅니다
**C3**: FastAPI 의존성 주입 패턴을 준수합니다
**C4**: 기존 픽스처 아키텍처를 유지합니다

### 프로세스 제약

**C5**: 수정은 Phase 1 범위에 한정됩니다 (6개 테스트만)
**C6**: 각 수정은 독립적으로 검증 가능해야 합니다
**C7**: 전체 테스트 스위트는 회귀 없이 실행되어야 합니다
**C8**: CI 파이프라인은 수정 후 통과해야 합니다

---

## RISKS & MITIGATION (위험 및 대응)

### 위험 1: 픽스처 이름 변경의 부작용

**위험 수준**: Medium
**설명**: `api_client` 픽스처를 사용하는 다른 테스트가 실패할 수 있음

**완화 전략**:
- 전체 코드베이스에서 `api_client` 문자열 검색 수행
- 영향받는 모든 테스트 파일 식별
- 변경 전 영향 분석 완료

**검증 방법**:
- `pytest -n 4` 전체 테스트 스위트 실행
- 새로운 실패가 없는지 확인

### 위험 2: 인증 우회의 보안 영향

**위험 수준**: Low
**설명**: 인증 우회 로직이 프로덕션에 영향을 줄 수 있음

**완화 전략**:
- 테스트 환경 격리 확인
- 의존성 오버라이드는 테스트 코드에만 존재
- 프로덕션 코드에 테스트 전용 로직 없음

**검증 방법**:
- 프로덕션 API 엔드포인트 보안 검증
- 실제 인증 요구사항 유지 확인

### 위험 3: 불완전한 수정

**위험 수준**: Low
**설명**: 6개 테스트 중 일부만 수정될 수 있음

**완화 전략**:
- 각 테스트를 개별적으로 검증
- 수정 후 전체 테스트 재실행
- 명확한 체크리스트 사용

**검증 방법**:
- 6개 테스트 모두 PASSED 상태 확인
- CI 파이프라인 통과 확인

---

## TRACEABILITY (추적 가능성)

### 상위 문서

- `@DOC:development-guide.md` - 테스트 작성 가이드라인
- `@DOC:README.md` - 프로젝트 테스트 전략

### 관련 SPEC

- `@SPEC:AGENT-ROUTER-BUGFIX-001` - 완료된 버그 수정 (16/16 테스트 통과)

### 구현 대상

- `@CODE:tests/conftest.py` - 픽스처 정의 파일
- `@CODE:tests/integration/test_phase3_reflection.py` - Reflection API 테스트
- `@CODE:tests/integration/test_hybrid_search.py` - Hybrid Search 테스트

### 검증 기준

- `@TEST:REFLECTION-API-FIXTURE` - 픽스처 주입 테스트
- `@TEST:HYBRID-SEARCH-AUTH` - 인증 우회 테스트

---

## ACCEPTANCE CRITERIA (승인 기준)

자세한 승인 기준은 `acceptance.md`를 참조하세요.

### 핵심 기준

1. ✅ Reflection API 4개 테스트가 픽스처 오류 없이 통과
2. ✅ Hybrid Search 2개 테스트가 403 오류 없이 200 응답 수신
3. ✅ 기존 68개 통과 테스트 유지 (회귀 없음)
4. ✅ CI 파이프라인에서 74개 테스트 통과 (68 + 6)
5. ✅ 프로덕션 코드 무변경 (테스트 파일만 수정)

---

## NOTES (참고 사항)

### 개발 노트

- Phase 1은 빠른 수정에 집중 (5-10분 내 완료 가능)
- 나머지 14개 실패는 Phase 2에서 더 복잡한 수정 필요
- 픽스처 네이밍 표준화로 향후 유사 문제 방지

### 참조 문서

- pytest fixtures documentation: https://docs.pytest.org/en/stable/fixture.html
- FastAPI testing guide: https://fastapi.tiangolo.com/tutorial/testing/
- pytest-asyncio documentation: https://pytest-asyncio.readthedocs.io/

---

**Document End**
