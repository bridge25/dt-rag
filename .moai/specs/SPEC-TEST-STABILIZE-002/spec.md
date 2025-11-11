# SPEC-TEST-STABILIZE-002: CI 테스트 안정화 Phase 2 - 패턴 문서화 및 테스트 수정

---
id: TEST-STABILIZE-002
version: 0.0.1
status: draft
created: 2025-11-11
updated: 2025-11-11
author: Alfred (MoAI-ADK)
priority: high
type: bugfix
category: test-stabilization
tags: [test-stabilization, pattern-documentation, test-refactoring, ci-pipeline, phase-2]
depends_on: [TEST-STABILIZE-001]
related_specs: [SPEC-AGENT-ROUTER-BUGFIX-001, SPEC-TEST-STABILIZE-001]
scope:
  packages:
    - tests/integration
    - tests/conftest.py
    - tests/docs
  files:
    - tests/docs/fixture-guidelines.md
    - tests/docs/auth-bypass-patterns.md
    - tests/docs/test-best-practices.md
---

## @TAG BLOCK

**Primary TAG**: `@SPEC:TEST-STABILIZE-002`

**Related TAGs**:
- `@SPEC:TEST-STABILIZE-001` (완료됨: 7/7 테스트 통과, Phase 1 성공)
- `@DOC:FIXTURE-GUIDELINES` (Phase 2A: 픽스처 네이밍 가이드라인)
- `@DOC:AUTH-BYPASS-PATTERNS` (Phase 2A: 인증 우회 패턴)
- `@DOC:TEST-BEST-PRACTICES` (Phase 2A: 테스트 베스트 프랙티스)
- `@TEST:PHASE-2-STABILIZATION` (Phase 2B: 13개 테스트 수정)

---

## HISTORY

### v0.0.1 (2025-11-11)
- Initial SPEC 작성
- Phase 1 성과 기반 Phase 2 전략 수립
- Phase A: 패턴 문서화 (3개 문서 생성)
- Phase B: 테스트 안정화 (13개 테스트 수정)
- 통합 접근법: 문서화 → 테스트 수정 순차 진행
- 목표: CI 파이프라인 100% 통과 (960 tests passed)

---

## OVERVIEW

### 배경 및 문맥

**Phase 1 성공** (SPEC-TEST-STABILIZE-001):
- 7개 테스트 안정화 완료 (Reflection API 4개 + Hybrid Search 3개)
- 픽스처 네이밍 표준화 (`api_client` → `async_client`)
- 인증 우회 패턴 확립 (`app.dependency_overrides` 방식)
- CI 파이프라인 안정성: 68 passed → 75 passed (35% 개선)

**Phase 2 필요성**:
- 남은 13개 테스트 실패가 CI 파이프라인 통과를 차단
- Phase 1에서 확립된 패턴의 문서화 필요
- 체계적인 테스트 수정 전략 요구
- 장기 유지보수를 위한 베스트 프랙티스 정립

### 목표

**Phase A: 패턴 문서화** (우선순위 1)
1. **픽스처 네이밍 가이드라인 문서 작성** (`tests/docs/fixture-guidelines.md`)
   - Phase 1에서 확립된 `async_client` 표준 설명
   - pytest 픽스처 네이밍 컨벤션
   - 하위 호환성 관리 전략

2. **인증 우회 패턴 문서 작성** (`tests/docs/auth-bypass-patterns.md`)
   - Phase 1에서 검증된 `app.dependency_overrides` 패턴
   - FastAPI 의존성 주입 오버라이드 베스트 프랙티스
   - 안전한 정리 메커니즘 (try-finally)

3. **테스트 베스트 프랙티스 문서 작성** (`tests/docs/test-best-practices.md`)
   - 통합 테스트 작성 가이드라인
   - 비동기 테스트 패턴 (pytest-asyncio)
   - TAG 추적 시스템 통합

**Phase B: 테스트 안정화** (우선순위 2)
4. **남은 13개 테스트 실패 분석 및 수정**
   - 실패 원인 카테고리화 (픽스처/인증/타입/로직)
   - Phase A 문서의 패턴 체계적 적용
   - 회귀 없는 안전한 수정
   - 960 tests passed 달성

### 범위

**포함 사항**:
- Phase A: 3개 문서 생성 (`tests/docs/` 디렉토리)
- Phase B: 13개 테스트 실패 분석 및 수정
- TAG 체인 완성 (@SPEC → @DOC → @TEST)
- CI 파이프라인 100% 통과 검증

**제외 사항**:
- 프로덕션 코드 변경 (테스트/문서만 수정)
- 새로운 기능 추가
- 성능 최적화 (안정성에 집중)

---

## ENVIRONMENT (환경 가정)

### 시스템 환경

**E1**: pytest 테스트 프레임워크 사용 (pytest-asyncio 플러그인 포함)
**E2**: CI 파이프라인은 GitHub Actions 또는 유사한 환경에서 실행
**E3**: FastAPI 애플리케이션 아키텍처 (의존성 주입 패턴 지원)
**E4**: Python 3.10+ 비동기 프로그래밍 환경

### 문서 환경

**E5**: 테스트 문서는 `tests/docs/` 디렉토리에 Markdown 형식으로 저장
**E6**: 문서는 개발자가 쉽게 참조 가능한 위치에 배치
**E7**: 모든 패턴 문서는 실제 구현 예시 포함
**E8**: TAG 시스템을 통한 추적 가능성 보장

### 테스트 환경

**E9**: 통합 테스트는 `tests/integration/` 디렉토리에 위치
**E10**: 공통 픽스처는 `tests/conftest.py`에 정의
**E11**: 테스트는 병렬 실행 가능 (`pytest -n auto`)
**E12**: Phase 1에서 확립된 패턴이 표준으로 사용됨

---

## ASSUMPTIONS (전제 조건)

### 기술 가정

**A1**: Phase 1에서 확립된 `async_client` 픽스처 표준은 전체 코드베이스에 적용 가능
**A2**: `app.dependency_overrides` 패턴은 모든 인증 관련 테스트에 재사용 가능
**A3**: 남은 13개 테스트 실패는 패턴 적용으로 해결 가능 (프로덕션 코드 변경 불필요)
**A4**: 현재 75개의 통과 테스트는 Phase 2 수정으로 영향받지 않음

### 프로세스 가정

**A5**: 문서화(Phase A) → 테스트 수정(Phase B) 순차 진행이 효율적
**A6**: 각 문서는 독립적으로 작성 가능 (병렬 작업 지원)
**A7**: 테스트 수정은 문서의 패턴을 참조하여 일관성 유지
**A8**: CI 파이프라인은 수정 후 자동으로 재실행되어 검증

### 문서 가정

**A9**: 가이드라인 문서는 1-2페이지 분량으로 간결하게 작성
**A10**: 모든 문서는 실제 코드 예시 포함 (Phase 1 구현 기반)
**A11**: 문서는 한국어로 작성 (프로젝트 conversation_language 준수)
**A12**: 문서는 개발자 온보딩 및 지속적 참조 자료로 활용

---

## REQUIREMENTS (요구사항)

### Ubiquitous Behaviors (보편적 행동)

**U1**: 모든 테스트 관련 문서는 `tests/docs/` 디렉토리에 위치해야 합니다
- 일관된 문서 구조 유지
- 쉬운 참조 및 검색 지원
- 프로젝트 표준 준수

**U2**: 모든 패턴 문서는 실제 구현 예시를 포함해야 합니다
- Phase 1 코드 기반 예시 제공
- Copy-paste 가능한 템플릿
- 명확한 주석 및 설명

**U3**: 모든 테스트 수정은 문서화된 패턴을 따라야 합니다
- 일관된 코드 스타일 유지
- 패턴 재사용 촉진
- 유지보수성 향상

### Event-Driven Behaviors (이벤트 기반 행동)

**E1**: WHEN Phase A 문서 작성이 시작될 때
IF 기존 `tests/docs/` 디렉토리가 없으면
THEN 디렉토리를 생성하고 `.gitkeep` 추가

**E2**: WHEN 픽스처 가이드라인 문서가 작성될 때
IF Phase 1의 `async_client` 표준이 참조되면
THEN 실제 `tests/conftest.py` 코드 예시 포함

**E3**: WHEN 인증 우회 패턴 문서가 작성될 때
IF Phase 1의 `app.dependency_overrides` 패턴이 설명되면
THEN `test_hybrid_search.py`의 실제 구현 예시 포함

**E4**: WHEN Phase B 테스트 수정이 시작될 때
IF 실패 원인이 분석되면
THEN Phase A 문서의 해당 패턴 적용

**E5**: WHEN 13개 테스트 수정이 완료될 때
IF 전체 테스트 스위트가 실행되면
THEN 960 tests passed 달성 및 회귀 없음 확인

### State-Driven Behaviors (상태 기반 행동)

**S1**: WHILE Phase A 문서 작성이 진행 중일 때
각 문서는 독립적으로 완성되어야 하며 순서 무관

**S2**: WHILE Phase B 테스트 수정이 진행 중일 때
각 수정은 개별 테스트 실행으로 검증 후 다음 단계 진행

**S3**: WHILE CI 파이프라인이 실행 중일 때
모든 960개 테스트는 실패 없이 통과해야 함

**S4**: WHILE TAG 체인이 구축되는 동안
@SPEC → @DOC → @TEST 순서로 추적 가능성 유지

### Optional Behaviors (선택적 행동)

**O1**: 문서에 다이어그램 또는 플로우차트 추가 가능
- 복잡한 패턴의 시각적 설명
- Mermaid 또는 ASCII 다이어그램

**O2**: 테스트 수정 시 추가 리팩토링 가능
- 중복 코드 제거
- 테스트 가독성 향상
- 단, 기능 변경 없이 구조 개선만

**O3**: 문서에 FAQ 섹션 추가 가능
- 자주 발생하는 오류 해결법
- 트러블슈팅 가이드

### Unwanted Behaviors (원하지 않는 행동)

**U-1**: Phase A 문서가 Phase 1 패턴과 일치하지 않아서는 안 됩니다
- 문서는 검증된 패턴만 포함
- 이론적 접근보다 실제 구현 기반

**U-2**: Phase B 테스트 수정이 새로운 테스트 실패를 야기해서는 안 됩니다
- 각 수정 후 회귀 테스트 필수
- 기존 75개 통과 테스트 유지

**U-3**: 문서가 과도하게 길거나 복잡해서는 안 됩니다
- 1-2페이지 분량 유지
- 핵심 패턴에 집중
- 불필요한 세부사항 제외

**U-4**: 프로덕션 코드가 테스트 수정으로 영향받아서는 안 됩니다
- 테스트 환경 격리 유지
- 의존성 오버라이드는 테스트에만 적용

---

## SPECIFICATIONS (상세 사양)

### Phase A: 패턴 문서화 (3개 문서)

#### Document 1: Fixture Guidelines (`tests/docs/fixture-guidelines.md`)

**목적**: pytest 픽스처 네이밍 및 사용 표준 정의

**내용 구조**:
1. **개요**
   - Phase 1에서 확립된 `async_client` 표준
   - pytest 픽스처의 역할 및 중요성

2. **네이밍 컨벤션**
   - 표준 네이밍: `async_client`, `test_db`, `mock_service`
   - 금지 패턴: `api_client` (deprecated), `client1`, `temp_client`
   - 네이밍 규칙: 소문자 + 언더스코어, 명확한 역할 표시

3. **픽스처 정의 베스트 프랙티스**
   - Phase 1 `conftest.py` 예시 (Line 122-133)
   - 하위 호환성 관리: 별칭 픽스처 (Line 174-181)
   - Docstring 작성 가이드라인

4. **TAG 통합**
   - @CODE:FIXTURE-RENAME 사용 예시
   - TAG 추적 시스템과의 연계

**실제 코드 예시** (Phase 1 기반):
```python
# @CODE:FIXTURE-RENAME
@pytest_asyncio.fixture
async def async_client():
    """Standard async HTTP client for API testing.

    Replaces deprecated 'api_client' fixture.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

**기대 효과**:
- 픽스처 네이밍 불일치 방지
- 신규 테스트 작성 시 표준 준수
- 팀 전체 코드 일관성 향상

#### Document 2: Auth Bypass Patterns (`tests/docs/auth-bypass-patterns.md`)

**목적**: 테스트 환경에서 인증 우회 패턴 표준화

**내용 구조**:
1. **개요**
   - 테스트 환경 인증 우회의 필요성
   - FastAPI 의존성 주입 오버라이드 메커니즘

2. **권장 패턴: Dependency Override (Option A)**
   - Phase 1 `test_hybrid_search.py` 예시 (Line 110-151)
   - `app.dependency_overrides` 사용법
   - try-finally를 통한 안전한 정리

3. **대안 패턴: Header Injection (Option B)**
   - `X-API-Key` 헤더 사용
   - 환경 변수 기반 테스트 키
   - 적용 시나리오

4. **주의사항**
   - 테스트 환경 격리 보장
   - 프로덕션 보안 영향 방지
   - 오버라이드 정리 필수

**실제 코드 예시** (Phase 1 기반):
```python
# @CODE:AUTH-BYPASS
from apps.api.deps import verify_api_key

async def mock_verify_api_key() -> str:
    """Mock API key verification for testing."""
    return "test_api_key"

# Apply override
app.dependency_overrides[verify_api_key] = mock_verify_api_key
try:
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
finally:
    app.dependency_overrides.clear()
```

**기대 효과**:
- 403 Forbidden 에러 제거
- 일관된 인증 우회 메커니즘
- 안전한 테스트 환경 관리

#### Document 3: Test Best Practices (`tests/docs/test-best-practices.md`)

**목적**: 통합 테스트 작성 종합 가이드

**내용 구조**:
1. **테스트 구조**
   - AAA 패턴 (Arrange-Act-Assert)
   - Given-When-Then 매핑
   - 테스트 독립성 보장

2. **비동기 테스트**
   - pytest-asyncio 사용법
   - `@pytest.mark.asyncio` 데코레이터
   - async/await 패턴

3. **픽스처 활용**
   - `async_client` 표준 픽스처 사용
   - 커스텀 픽스처 정의
   - 픽스처 스코프 관리 (function/module/session)

4. **인증 및 보안**
   - Phase 1 인증 우회 패턴 적용
   - 테스트 환경 격리
   - 민감 정보 관리

5. **TAG 시스템 통합**
   - @TEST, @CODE TAG 사용법
   - 추적 가능성 확보
   - TAG 체인 구축

6. **일반 지침**
   - 명확한 테스트 이름
   - 충분한 assertion
   - 실패 메시지 작성

**실제 코드 예시** (Phase 1 통합):
```python
# @TEST:HYBRID-SEARCH-AUTH
@pytest.mark.asyncio
async def test_vector_search_timeout_fallback(async_client):
    """
    GIVEN: Neural case selector enabled, vector search timeout
    WHEN: Hybrid search API called
    THEN: Falls back to BM25, returns valid results
    """
    # Arrange: Auth bypass
    from apps.api.deps import verify_api_key
    async def mock_verify_api_key() -> str:
        return "test_api_key"

    app.dependency_overrides[verify_api_key] = mock_verify_api_key
    try:
        # Act: API call
        response = await async_client.post("/api/search", json=payload)

        # Assert: Success
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    finally:
        app.dependency_overrides.clear()
```

**기대 효과**:
- 일관된 테스트 작성 스타일
- 신규 개발자 온보딩 가속
- 테스트 품질 및 유지보수성 향상

### Phase B: 테스트 안정화 (13개 테스트 수정)

#### 분석 전략

**Step 1: 실패 원인 카테고리화**
- pytest 출력 분석 (`pytest -v` 실행)
- 13개 테스트 실패를 다음으로 분류:
  1. **픽스처 관련** (fixture mismatch, injection error)
  2. **인증 관련** (403 Forbidden, authentication error)
  3. **타입 관련** (type mismatch, validation error)
  4. **로직 관련** (assertion failure, unexpected behavior)

**Step 2: 패턴 매핑**
- 각 실패 카테고리를 Phase A 문서의 패턴에 매핑
- 픽스처 관련 → `fixture-guidelines.md` 참조
- 인증 관련 → `auth-bypass-patterns.md` 참조
- 기타 → `test-best-practices.md` 참조

**Step 3: 우선순위 지정**
- **High**: 픽스처/인증 (Phase A 패턴 직접 적용 가능)
- **Medium**: 타입/간단한 로직 (빠른 수정 가능)
- **Low**: 복잡한 로직 (세부 분석 필요)

#### 수정 프로세스

**개별 테스트 수정 워크플로우**:
1. **분석**: 실패 원인 식별 (pytest traceback 검토)
2. **패턴 선택**: Phase A 문서에서 해당 패턴 참조
3. **코드 수정**: 문서의 패턴 적용
4. **TAG 추가**: @TEST:PHASE-2-STABILIZATION 추가
5. **개별 검증**: 해당 테스트만 실행하여 통과 확인
6. **회귀 테스트**: 전체 스위트 실행하여 부작용 없음 확인

**예상 수정 패턴 분포**:
- 픽스처 네이밍 불일치: 4-5개 테스트
- 인증 우회 누락: 3-4개 테스트
- 타입 불일치: 2-3개 테스트
- 기타 로직: 1-2개 테스트

**수정 후 검증 체크리스트**:
- [ ] 13개 테스트 모두 PASSED 상태
- [ ] 기존 75개 테스트 여전히 PASSED (회귀 없음)
- [ ] 전체 960 tests passed 달성
- [ ] CI 파이프라인 통과
- [ ] TAG 체인 완성 (@SPEC → @DOC → @TEST)

#### 기대 결과

**Phase B 완료 시**:
- CI 파이프라인: 75 passed → 960 passed (100% 성공률)
- 테스트 안정성: Phase 1 (35%) → Phase 2 (100%)
- 패턴 재사용: 모든 수정은 문서화된 패턴 기반
- 추적 가능성: TAG 체인 완전 연결

---

## CONSTRAINTS (제약 조건)

### 기술 제약

**C1**: 프로덕션 코드는 수정하지 않습니다 (테스트/문서만 수정)
**C2**: pytest 및 pytest-asyncio 프레임워크 규칙을 준수합니다
**C3**: FastAPI 의존성 주입 패턴을 유지합니다
**C4**: Phase 1에서 확립된 표준을 따릅니다

### 문서 제약

**C5**: 각 문서는 1-2페이지 분량으로 간결하게 작성
**C6**: 모든 문서는 한국어로 작성 (conversation_language 준수)
**C7**: 실제 코드 예시 필수 포함
**C8**: Markdown 형식 및 프로젝트 표준 준수

### 프로세스 제약

**C9**: Phase A 완료 후 Phase B 시작 (순차 진행)
**C10**: 각 테스트 수정은 개별 검증 후 다음 단계 진행
**C11**: 전체 회귀 테스트는 각 단계마다 수행
**C12**: CI 파이프라인은 Phase B 완료 후 100% 통과해야 함

---

## RISKS & MITIGATION (위험 및 대응)

### 위험 1: Phase A 문서가 Phase 1 패턴과 불일치

**위험 수준**: Medium
**설명**: 문서화 시 Phase 1 구현과 다른 패턴 설명 가능성

**완화 전략**:
- Phase 1 실제 코드 직접 참조 (`conftest.py`, `test_hybrid_search.py`)
- 코드 예시는 Phase 1 구현 그대로 사용
- 문서 작성 후 코드와 교차 검증

**검증 방법**:
- Phase 1 sync report 참조하여 정확성 확인
- 실제 파일 Line 번호와 일치 여부 검토

### 위험 2: 13개 테스트 중 일부가 패턴으로 해결 불가능

**위험 수준**: Medium
**설명**: 예상치 못한 실패 원인으로 Phase A 패턴 적용 불가

**완화 전략**:
- 실패 원인 사전 분석 (pytest -v 출력 검토)
- 복잡한 케이스는 별도 전략 수립
- 필요 시 프로덕션 코드 최소 수정 고려 (SPEC 범위 확장)

**검증 방법**:
- Phase B 시작 전 13개 테스트 실패 로그 전수 분석
- 패턴 적용 가능 여부 사전 평가

### 위험 3: Phase B 수정이 기존 테스트에 회귀 유발

**위험 수준**: Low
**설명**: 13개 테스트 수정 시 기존 75개 테스트 영향 가능성

**완화 전략**:
- 각 수정 후 전체 테스트 스위트 실행
- 픽스처 변경은 별칭 사용하여 하위 호환성 유지
- 공통 코드 변경 최소화

**검증 방법**:
- `pytest -n auto` 전체 실행 (각 단계마다)
- 기존 75개 테스트 PASSED 상태 유지 확인

### 위험 4: 문서가 과도하게 복잡해져 활용도 저하

**위험 수준**: Low
**설명**: 문서가 너무 길거나 이론적이어서 실용성 떨어짐

**완화 전략**:
- 1-2페이지 분량 제한 엄수
- 핵심 패턴과 예시에 집중
- FAQ 및 트러블슈팅은 선택적 추가

**검증 방법**:
- 문서 작성 후 실제 테스트 수정 시 참조 가능 여부 확인
- 개발자 피드백 수집 (가독성, 유용성)

---

## TRACEABILITY (추적 가능성)

### 상위 SPEC

- `@SPEC:TEST-STABILIZE-001` (Phase 1: 7개 테스트 안정화 완료)
- `@SPEC:AGENT-ROUTER-BUGFIX-001` (완료: 16/16 테스트 통과)

### 구현 대상

**Phase A: 문서**
- `@DOC:tests/docs/fixture-guidelines.md` (픽스처 가이드라인)
- `@DOC:tests/docs/auth-bypass-patterns.md` (인증 우회 패턴)
- `@DOC:tests/docs/test-best-practices.md` (테스트 베스트 프랙티스)

**Phase B: 테스트 코드**
- `@TEST:tests/integration/*` (13개 테스트 파일)
- `@CODE:tests/conftest.py` (필요 시 픽스처 추가)

### 검증 기준

- `@TEST:PHASE-2-STABILIZATION` (13개 테스트 수정)
- `@TEST:CI-PIPELINE-PASS` (960 tests passed)

### 관련 문서

- `@DOC:development-guide.md` (프로젝트 테스트 전략)
- `@DOC:README.md` (프로젝트 개요)

---

## ACCEPTANCE CRITERIA (승인 기준)

자세한 승인 기준은 `acceptance.md`를 참조하세요.

### Phase A 기준

1. [ ] `fixture-guidelines.md` 작성 완료 (Phase 1 패턴 기반)
2. [ ] `auth-bypass-patterns.md` 작성 완료 (실제 코드 예시 포함)
3. [ ] `test-best-practices.md` 작성 완료 (TAG 통합 설명)
4. [ ] 모든 문서는 한국어로 작성되고 1-2페이지 분량
5. [ ] TAG 체인: @SPEC:TEST-STABILIZE-002 → @DOC:*

### Phase B 기준

6. [ ] 13개 테스트 실패 원인 분석 완료 (카테고리화)
7. [ ] Phase A 문서 패턴을 체계적으로 적용
8. [ ] 13개 테스트 모두 PASSED 상태
9. [ ] 기존 75개 테스트 유지 (회귀 없음)
10. [ ] 전체 960 tests passed 달성

### 통합 기준

11. [ ] CI 파이프라인 100% 통과
12. [ ] TAG 체인 완전 연결: @SPEC → @DOC → @TEST
13. [ ] 프로덕션 코드 무변경 (테스트/문서만)
14. [ ] Phase 2 sync report 작성 완료

---

## NOTES (참고 사항)

### 개발 노트

- **Phase 1 성과**: 7개 테스트 안정화 (계획 6개 초과 달성)
- **Phase 2 전략**: 문서화 → 테스트 수정 순차 진행 (통합 접근)
- **예상 소요 시간**: Phase A (20분) + Phase B (1-2시간, 변동 가능)
- **주요 위험**: 13개 테스트 중 패턴 적용 불가능 케이스 존재 가능성

### 참조 문서

- Phase 1 SPEC: `.moai/specs/SPEC-TEST-STABILIZE-001/spec.md`
- Phase 1 Sync Report: `docs/status/sync-report-test-stabilize-001.md`
- pytest documentation: https://docs.pytest.org/en/stable/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/

### 향후 개선 사항

- 테스트 픽스처 자동화 도구 개발
- CI 파이프라인 안정성 모니터링 대시보드
- 테스트 패턴 라이브러리 구축

---

**Document End**
