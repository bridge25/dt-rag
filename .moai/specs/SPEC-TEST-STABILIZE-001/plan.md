# Implementation Plan: SPEC-TEST-STABILIZE-001

## @TAG BLOCK

**Plan TAG**: `@PLAN:TEST-STABILIZE-001`
**Related SPEC**: `@SPEC:TEST-STABILIZE-001`

---

## OVERVIEW

이 문서는 테스트 안정화 Phase 1의 구현 계획을 상세히 기술합니다. 6개의 빠른 수정 대상 테스트 실패를 해결하여 CI 파이프라인 안정성을 30% 향상시킵니다.

### 목표

- Reflection API 픽스처 불일치 해결 (4개 테스트)
- Hybrid Search 인증 우회 적용 (2개 테스트)
- 전체 테스트 통과율: 68 passed → 74 passed
- 회귀 없는 수정 보장

---

## IMPLEMENTATION STRATEGY

### 접근 방식

1. **순차적 수정**: Problem 1 → Problem 2 순서로 진행
2. **개별 검증**: 각 문제 해결 후 해당 테스트만 먼저 실행
3. **전체 검증**: 모든 수정 완료 후 전체 테스트 스위트 실행
4. **영향 분석**: 픽스처 이름 변경 전 전체 코드베이스 검색

### 우선순위

- **Priority 1 (High)**: Reflection API 픽스처 수정 (4개 테스트, 영향 범위 넓음)
- **Priority 2 (Medium)**: Hybrid Search 인증 우회 (2개 테스트, 격리된 문제)

---

## PHASE 1: Reflection API Fixture Fix

### 목표

`tests/conftest.py`의 픽스처 이름을 `api_client`에서 `async_client`로 변경하여 Reflection API 테스트 4개를 수정합니다.

### 수정 대상 파일

**Primary File**:
- `tests/conftest.py` (Line 122)

**Affected Test File**:
- `tests/integration/test_phase3_reflection.py` (Lines 171, 185, 202, 225)

### 구현 단계

#### Step 1: 영향 분석 (필수)

**목적**: `api_client` 픽스처를 사용하는 다른 테스트 파일이 있는지 확인

**실행 명령**:
```bash
# 전체 코드베이스에서 api_client 픽스처 사용 검색
grep -r "api_client" tests/ --include="*.py"

# 또는 더 정확한 패턴 매칭
grep -r "def.*api_client" tests/ --include="*.py"
```

**예상 결과**:
- `tests/conftest.py`: 픽스처 정의 발견
- `tests/integration/test_phase3_reflection.py`: 사용되지 않음 (async_client 기대)
- 다른 파일: 사용 여부 확인 필요

**결정 기준**:
- 다른 파일이 `api_client`를 사용하면 → 해당 파일도 수정 필요
- 사용하지 않으면 → 픽스처 이름 변경 안전

#### Step 2: 픽스처 이름 변경

**파일**: `tests/conftest.py`
**라인**: 122 (예상 위치)

**변경 전**:
```python
@pytest.fixture
def api_client():
    """Provides an async HTTP client for testing."""
    # ... fixture implementation ...
```

**변경 후**:
```python
@pytest.fixture
def async_client():
    """Provides an async HTTP client for testing."""
    # ... fixture implementation ...
```

**주의 사항**:
- 픽스처 내부 로직은 변경하지 않음
- docstring은 명확성을 위해 유지 또는 개선
- 픽스처 스코프 설정은 유지 (function/module/session)

#### Step 3: 개별 테스트 검증

**실행 명령**:
```bash
# Reflection API 테스트 4개만 실행
pytest tests/integration/test_phase3_reflection.py::test_reflection_suggestions_authentication -v
pytest tests/integration/test_phase3_reflection.py::test_reflection_health_check -v
pytest tests/integration/test_phase3_reflection.py::test_reflection_analyze_performance -v
pytest tests/integration/test_phase3_reflection.py::test_reflection_batch_performance -v

# 또는 전체 파일 실행
pytest tests/integration/test_phase3_reflection.py -v
```

**성공 기준**:
- 4개 테스트 모두 PASSED 상태
- ERROR 또는 fixture 관련 오류 없음
- 테스트 실행 시간 정상 범위 내

**실패 시 대응**:
- 픽스처 이름 확인 (대소문자, 오타)
- conftest.py 위치 확인 (pytest가 발견 가능한지)
- 픽스처 스코프 확인

#### Step 4: 영향받은 테스트 확인

**만약 Step 1에서 다른 파일이 `api_client`를 사용한다면**:

**실행 명령**:
```bash
# 영향받은 테스트 파일 실행
pytest tests/path/to/affected_test.py -v
```

**수정 옵션**:
- **Option A**: 해당 테스트도 `async_client`로 변경
- **Option B**: 픽스처 별칭 추가 (하위 호환성)
  ```python
  @pytest.fixture
  def async_client():
      # ... implementation ...

  @pytest.fixture
  def api_client(async_client):
      """Alias for backward compatibility."""
      return async_client
  ```

### 완료 기준

- ✅ `tests/conftest.py` 픽스처 이름 변경 완료
- ✅ Reflection API 4개 테스트 PASSED
- ✅ 영향받은 다른 테스트 없음 또는 수정 완료
- ✅ 픽스처 관련 오류 0건

### 예상 소요 시간

- 영향 분석: 2분
- 픽스처 이름 변경: 1분
- 개별 테스트 검증: 2분
- **총 예상 시간: 5분**

---

## PHASE 2: Hybrid Search Authentication Fix

### 목표

`tests/integration/test_hybrid_search.py`의 Hybrid Search 테스트 2개에 인증 우회를 적용하여 403 오류를 해결합니다.

### 수정 대상 파일

**Primary File**:
- `tests/integration/test_hybrid_search.py` (Lines 189-217)

**Reference File**:
- `tests/conftest.py` (인증 우회 픽스처 확인)

### 구현 단계

#### Step 1: 현재 인증 우회 패턴 확인

**목적**: 프로젝트의 표준 인증 우회 방식 파악

**실행 명령**:
```bash
# conftest.py에서 인증 관련 픽스처 검색
grep -A 10 "verify_api_key\|auth\|override" tests/conftest.py

# 다른 통합 테스트에서 인증 우회 패턴 확인
grep -B 5 -A 5 "dependency_overrides\|X-API-Key" tests/integration/*.py | head -50
```

**확인 사항**:
- 의존성 오버라이드 픽스처 존재 여부
- TestClient 생성 패턴
- 기존 인증 우회 방식 (헤더 vs 오버라이드)

#### Step 2: 인증 우회 적용 (Option A - 의존성 오버라이드)

**파일**: `tests/integration/test_hybrid_search.py`
**라인**: 189-217

**변경 전** (예상):
```python
def test_hybrid_search_bm25_only():
    """Test hybrid search without neural reranking."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    response = client.post("/search", json={...})
    assert response.status_code == 200  # 실패: 403 Forbidden
```

**변경 후** (의존성 오버라이드 사용):
```python
def test_hybrid_search_bm25_only():
    """Test hybrid search without neural reranking."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.dependencies import verify_api_key

    # Mock authentication dependency
    async def override_verify_api_key():
        return {"valid": True}

    app.dependency_overrides[verify_api_key] = override_verify_api_key

    try:
        client = TestClient(app)
        response = client.post("/search", json={...})
        assert response.status_code == 200
    finally:
        # Clean up override
        app.dependency_overrides.clear()
```

**장점**:
- FastAPI 표준 패턴
- 의존성 주입 아키텍처 유지
- 다른 인증 메커니즘과 일관성

#### Step 3: 인증 우회 적용 (Option B - 헤더 방식)

**대안 구현** (Option A가 복잡한 경우):

**변경 후** (헤더 기반):
```python
def test_hybrid_search_bm25_only():
    """Test hybrid search without neural reranking."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    # Add test API key header
    headers = {"X-API-Key": "test-api-key-12345"}
    response = client.post("/search", json={...}, headers=headers)
    assert response.status_code == 200
```

**장점**:
- 간단하고 직관적
- 코드 변경 최소화
- 테스트 환경 API 키 사용

**주의 사항**:
- 테스트 API 키가 환경 변수로 관리되는지 확인
- 프로덕션 키와 명확히 구분

#### Step 4: 두 번째 테스트 수정

**파일**: `tests/integration/test_hybrid_search.py`
**라인**: 204-217

**적용**: Step 2 또는 Step 3의 동일한 패턴 적용

```python
def test_hybrid_search_with_neural():
    """Test hybrid search with neural reranking."""
    # Step 2 또는 Step 3의 인증 우회 로직 적용
    # 테스트 본문은 기존과 동일
```

#### Step 5: 개별 테스트 검증

**실행 명령**:
```bash
# Hybrid Search 테스트 2개 실행
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_bm25_only -v
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_with_neural -v

# 또는 특정 섹션 실행
pytest tests/integration/test_hybrid_search.py -v -k "hybrid"
```

**성공 기준**:
- 2개 테스트 모두 PASSED 상태
- 200 OK 응답 수신
- 403 Forbidden 오류 없음
- JSON 응답 검증 성공

**실패 시 대응**:
- 인증 우회 로직 확인
- API 엔드포인트 경로 확인 (/search)
- 테스트 데이터 유효성 확인

#### Step 6: 전체 Hybrid Search 테스트 확인

**실행 명령**:
```bash
# 전체 hybrid search 테스트 파일 실행
pytest tests/integration/test_hybrid_search.py -v
```

**목적**: 다른 hybrid search 테스트가 영향받지 않았는지 확인

**성공 기준**:
- 모든 hybrid search 테스트 통과
- 새로운 실패 없음

### 완료 기준

- ✅ `tests/integration/test_hybrid_search.py` 인증 우회 적용 완료
- ✅ Hybrid Search 2개 테스트 PASSED (200 OK)
- ✅ 403 Forbidden 오류 제거
- ✅ 다른 hybrid search 테스트 영향 없음

### 예상 소요 시간

- 인증 패턴 확인: 3분
- 인증 우회 적용: 5분
- 개별 테스트 검증: 2분
- **총 예상 시간: 10분**

---

## PHASE 3: Comprehensive Verification

### 목표

전체 테스트 스위트를 실행하여 회귀가 없고 모든 수정이 통합되었는지 확인합니다.

### 검증 단계

#### Step 1: 전체 테스트 스위트 실행

**실행 명령**:
```bash
# 병렬 실행으로 빠른 검증
pytest -n 4 -v

# 또는 느린 테스트 제외
pytest -n 4 -m "not slow" -v

# 커버리지 포함
pytest -n 4 --cov --cov-report=term-missing
```

**예상 결과**:
- **이전**: 68 passed, 20 failed
- **이후**: 74 passed, 14 failed (6개 수정 완료)

**성공 기준**:
- 최소 74개 테스트 통과
- 새로운 실패 0건
- 기존 68개 통과 테스트 유지

#### Step 2: 수정된 테스트 재확인

**실행 명령**:
```bash
# Phase 1 수정 테스트 (Reflection API)
pytest tests/integration/test_phase3_reflection.py -v

# Phase 2 수정 테스트 (Hybrid Search)
pytest tests/integration/test_hybrid_search.py::test_hybrid_search_bm25_only \
      tests/integration/test_hybrid_search.py::test_hybrid_search_with_neural -v
```

**성공 기준**:
- 6개 테스트 모두 PASSED
- 실행 시간 정상 범위
- 오류 메시지 없음

#### Step 3: CI 파이프라인 검증

**실행 명령** (로컬에서 CI 환경 시뮬레이션):
```bash
# GitHub Actions 워크플로우 시뮬레이션
pytest -n 4 -v --tb=short

# 또는 tox 사용 (설정되어 있다면)
tox
```

**성공 기준**:
- CI 파이프라인 통과
- 모든 품질 게이트 충족
- 타임아웃 없음

#### Step 4: 결과 문서화

**생성 문서**:
- 테스트 결과 스크린샷 또는 로그
- 수정 전후 비교 (68 vs 74 passed)
- 남은 14개 실패 목록 (Phase 2 대상)

**저장 위치**:
```
.moai/specs/SPEC-TEST-STABILIZE-001/
├── spec.md
├── plan.md
├── acceptance.md
└── verification_results.txt  (선택 사항)
```

### 완료 기준

- ✅ 전체 테스트 스위트에서 74개 통과
- ✅ 6개 대상 테스트 모두 PASSED
- ✅ 회귀 없음 (기존 68개 유지)
- ✅ CI 파이프라인 통과 가능

---

## TECHNICAL APPROACH

### 아키텍처 고려사항

#### Fixture Architecture
- pytest fixture 스코프: function-level (테스트 격리)
- conftest.py 계층 구조: tests/ 루트에 위치
- 픽스처 네이밍: snake_case, 명확한 의미

#### Authentication Architecture
- 의존성 주입 패턴: FastAPI standard
- 테스트 환경 격리: dependency_overrides 사용
- 프로덕션 보안: 테스트 코드와 분리

### 코딩 패턴

#### Pattern 1: Fixture Naming Standard
```python
# 표준 네이밍
@pytest.fixture
def async_client():
    """Provides an async HTTP client for testing."""
    pass

# 별칭 지원 (선택 사항)
@pytest.fixture
def api_client(async_client):
    """Backward compatibility alias."""
    return async_client
```

#### Pattern 2: Authentication Override
```python
# 의존성 오버라이드 패턴
from backend.app.dependencies import verify_api_key

async def override_verify_api_key():
    return {"valid": True}

app.dependency_overrides[verify_api_key] = override_verify_api_key

try:
    # 테스트 실행
    pass
finally:
    app.dependency_overrides.clear()
```

#### Pattern 3: Test Client Setup
```python
# 표준 TestClient 생성
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# 헤더 기반 인증
headers = {"X-API-Key": "test-key"}
response = client.post("/endpoint", headers=headers)
```

### 디버깅 전략

#### 픽스처 오류 디버깅
```bash
# 픽스처 목록 확인
pytest --fixtures tests/integration/test_phase3_reflection.py

# 픽스처 의존성 트리 확인
pytest --setup-show tests/integration/test_phase3_reflection.py::test_name -v
```

#### 인증 오류 디버깅
```python
# 로깅 추가
import logging
logging.basicConfig(level=logging.DEBUG)

# 요청/응답 내용 출력
print(f"Request headers: {response.request.headers}")
print(f"Response status: {response.status_code}")
print(f"Response body: {response.text}")
```

---

## RISKS & MITIGATION

### 위험 관리

#### Risk 1: 픽스처 이름 충돌
**완화**: Step 1의 영향 분석 필수 수행
**검증**: 전체 테스트 스위트 실행으로 회귀 확인

#### Risk 2: 인증 우회 실패
**완화**: 두 가지 옵션 제시 (의존성 오버라이드 vs 헤더)
**검증**: 개별 테스트 먼저 실행 후 전체 검증

#### Risk 3: CI 환경 차이
**완화**: 로컬에서 CI 환경 시뮬레이션
**검증**: 실제 CI 파이프라인 재실행으로 최종 확인

---

## DELIVERABLES

### 수정 파일 목록

1. `tests/conftest.py` - 픽스처 이름 변경
2. `tests/integration/test_hybrid_search.py` - 인증 우회 적용

### 검증 결과

- 전체 테스트 결과 로그
- 수정 전후 비교 표
- CI 파이프라인 통과 확인

### 문서

- 이 구현 계획 문서 (plan.md)
- 승인 기준 문서 (acceptance.md)
- SPEC 문서 (spec.md)

---

## NEXT STEPS

### Phase 1 완료 후

1. **PR 생성**: 수정 사항 리뷰 요청
2. **CI 파이프라인 확인**: 자동 빌드 통과 확인
3. **Phase 2 계획**: 나머지 14개 테스트 분석

### Phase 2 준비

- 14개 남은 테스트 실패 원인 분석
- 복잡도 평가 및 우선순위 지정
- 더 큰 리팩토링 필요 여부 판단

### 장기 개선

- 테스트 픽스처 표준화 가이드라인 작성
- 인증 우회 패턴 공식 문서화
- CI 파이프라인 안정성 모니터링

---

**Plan Document End**
