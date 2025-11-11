# 테스트 작성 모범 사례

@DOC:TEST-BEST-PRACTICES | SPEC-TEST-STABILIZE-002

## 개요

이 문서는 dt-rag 프로젝트의 통합 테스트 작성 시 따라야 할 표준 패턴과 모범 사례를 종합적으로 정리합니다. Phase 1과 Phase 2에서 확립된 픽스처 네이밍, 인증 우회, TAG 시스템을 통합하여 일관되고 유지보수 가능한 테스트 코드를 작성하는 방법을 제시합니다.

## 1. 테스트 구조

### 파일 구조

```
tests/
├── conftest.py                 # 공통 픽스처 정의
├── integration/               # 통합 테스트
│   ├── test_hybrid_search.py
│   ├── test_reflection_api.py
│   └── ...
├── unit/                      # 단위 테스트
│   ├── test_casebank.py
│   └── ...
└── docs/                      # 테스트 문서
    ├── fixture-guidelines.md
    ├── auth-bypass-patterns.md
    └── test-best-practices.md
```

### 테스트 클래스 구조

```python
class TestHybridSearch:
    """
    Hybrid Search API integration tests

    Tests cover neural search, BM25 fallback, and hybrid mode scenarios
    with proper authentication bypass and fixture usage.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_feature_name(self, async_client):
        """
        @TEST:FEATURE-001:0.1.0

        Brief description of what this test verifies

        Given: Initial conditions and setup
        When: Action or event occurs
        Then: Expected outcome
        """
        # Test implementation
        pass
```

## 2. 비동기 테스트 작성

### 기본 패턴

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_endpoint(async_client: AsyncClient):
    """
    @TEST:PHASE-2-STABILIZATION

    Test async API endpoint

    Given: Async client is available
    When: POST request to /api/endpoint
    Then: Response status is 200
    """
    response = await async_client.post(
        "/api/endpoint",
        json={"key": "value"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
```

### 동기 테스트 (TestClient)

일부 시나리오에서는 동기 `TestClient`를 사용할 수 있습니다:

```python
from fastapi.testclient import TestClient
from apps.api.main import app

def test_sync_endpoint():
    """
    @TEST:PHASE-2-STABILIZATION

    Test synchronous endpoint

    Given: TestClient is configured
    When: GET request to /health
    Then: Response is 200 OK
    """
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
```

## 3. 픽스처 사용

### 표준 픽스처: async_client

**✅ 권장 패턴:**

```python
@pytest.mark.asyncio
async def test_with_standard_fixture(async_client):
    """
    @TEST:PHASE-2-STABILIZATION

    Use standard async_client fixture

    Given: async_client fixture provides authenticated client
    When: Making API request
    Then: Authentication is automatically handled
    """
    response = await async_client.get("/api/protected")
    assert response.status_code == 200
```

### 레거시 픽스처: api_client

**⚠️ 하위 호환성 유지 (신규 코드에서는 사용 금지):**

```python
# 기존 테스트 유지보수 시에만 사용
@pytest.mark.asyncio
async def test_legacy_fixture(api_client):
    """Legacy test using api_client alias"""
    response = await api_client.get("/api/endpoint")
    assert response.status_code == 200
```

### 커스텀 픽스처

필요한 경우 테스트별 픽스처를 정의할 수 있습니다:

```python
@pytest.fixture
async def mock_openai_embeddings():
    """Mock OpenAI embeddings for testing"""
    from unittest.mock import patch

    with patch("apps.api.neural_selector.generate_embeddings") as mock:
        mock.return_value = [0.1] * 1536  # Mock 1536-dim vector
        yield mock
```

## 4. 인증 우회

### Option A: 테스트별 Override (특수 시나리오)

```python
@pytest.mark.asyncio
async def test_with_custom_auth():
    """
    @TEST:PHASE-2-STABILIZATION
    @CODE:AUTH-BYPASS | SPEC-TEST-STABILIZE-001

    Test with custom authentication override

    Given: Custom permission scope is needed
    When: Making API request with special permissions
    Then: Request succeeds with custom auth
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from apps.api.deps import verify_api_key
    from apps.api.security.api_key_storage import APIKeyInfo
    from datetime import datetime, timezone

    app = FastAPI()
    # ... include routers ...

    async def mock_verify_api_key() -> APIKeyInfo:
        return APIKeyInfo(
            key_id="custom_key",
            name="Custom Test Key",
            scope="admin",  # Custom scope
            permissions=["admin:*"],
            # ... other fields ...
        )

    app.dependency_overrides[verify_api_key] = mock_verify_api_key

    try:
        client = TestClient(app)
        response = client.post("/admin/endpoint", json={...})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
```

### Option B: Fixture Level (일반 테스트)

```python
# conftest.py에 이미 구현됨
@pytest.mark.asyncio
async def test_with_fixture_auth(async_client):
    """
    @TEST:PHASE-2-STABILIZATION

    Test using fixture-level authentication bypass

    Given: async_client has pre-configured auth bypass
    When: Making API request
    Then: No additional auth setup needed
    """
    response = await async_client.get("/api/endpoint")
    assert response.status_code == 200
```

## 5. TAG 시스템

### TAG 작성 규칙

1. **테스트 TAG**: `@TEST:[FEATURE-ID]:[VERSION]` 또는 `@TEST:PHASE-2-STABILIZATION`
2. **코드 TAG**: `@CODE:[PATTERN-NAME]` (예: `@CODE:AUTH-BYPASS`, `@CODE:FIXTURE-RENAME`)
3. **문서 TAG**: `@DOC:[DOC-NAME]` (예: `@DOC:FIXTURE-GUIDELINES`)

### TAG 배치

```python
@pytest.mark.asyncio
async def test_example(async_client):
    """
    @TEST:NEURAL-001:0.2.1
    @CODE:AUTH-BYPASS | SPEC-TEST-STABILIZE-001

    Test description with TAGs

    Given: Preconditions
    When: Action
    Then: Expected result
    """
    # Implementation
    pass
```

### TAG 추적

- Phase 1 TAGs: `@CODE:FIXTURE-RENAME`, `@CODE:AUTH-BYPASS`
- Phase 2 TAGs: `@TEST:PHASE-2-STABILIZATION`, `@DOC:*`

## 6. Given-When-Then 패턴

### 기본 구조

```python
@pytest.mark.asyncio
async def test_user_registration(async_client):
    """
    @TEST:USER-001:0.1.0

    Test user registration with valid data

    Given: New user data is prepared
    When: POST request to /users/register
    Then: User is created and response contains user_id
    """
    # Given: Prepare test data
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "Test User"
    }

    # When: Make API request
    response = await async_client.post(
        "/users/register",
        json=user_data
    )

    # Then: Verify response
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert data["email"] == user_data["email"]
```

### 복잡한 시나리오

```python
@pytest.mark.asyncio
async def test_complex_workflow(async_client, mock_openai):
    """
    @TEST:WORKFLOW-001:0.1.0

    Test multi-step workflow with external dependencies

    Given: User is authenticated and OpenAI is mocked
    When: Complex workflow is executed
    Then: All steps complete successfully
    """
    # Given: Setup mocks and preconditions
    mock_openai.return_value = [0.1] * 1536

    # When: Step 1 - Create resource
    create_response = await async_client.post(
        "/resources",
        json={"name": "Test Resource"}
    )
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    # When: Step 2 - Process resource
    process_response = await async_client.post(
        f"/resources/{resource_id}/process"
    )
    assert process_response.status_code == 200

    # Then: Verify final state
    get_response = await async_client.get(f"/resources/{resource_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "processed"
```

## 7. 종합 예시: 픽스처 + 인증 + TAG 통합

```python
import pytest
from httpx import AsyncClient
from unittest.mock import patch

class TestNeuralSearchIntegration:
    """
    Neural search integration tests with proper patterns

    Demonstrates fixture usage, auth bypass, and TAG system
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_neural_search_with_fallback(self, async_client: AsyncClient):
        """
        @TEST:NEURAL-002:0.2.0
        @CODE:AUTH-BYPASS | SPEC-TEST-STABILIZE-001

        Test neural search with BM25 fallback on timeout

        Given: Vector search is configured to timeout
        When: Neural search request is made
        Then: System falls back to BM25 and returns results
        """
        # Given: Mock vector search to timeout
        with patch("apps.api.neural_selector.vector_similarity_search") as mock_vs:
            import asyncio

            async def timeout_search(*args, **kwargs):
                await asyncio.sleep(0.15)
                raise asyncio.TimeoutError("Vector search timeout")

            mock_vs.side_effect = timeout_search

            # When: Make neural search request
            response = await async_client.post(
                "/search",
                json={
                    "q": "machine learning algorithms",
                    "max_results": 10,
                    "use_neural": True
                }
            )

            # Then: Verify fallback behavior
            assert response.status_code == 200
            data = response.json()

            assert data["mode"] == "bm25_fallback"
            assert len(data["results"]) > 0
            assert all("score" in result for result in data["results"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_neural_search_success(self, async_client: AsyncClient):
        """
        @TEST:NEURAL-003:0.2.0

        Test successful neural search without fallback

        Given: Vector search is available
        When: Neural search request is made
        Then: Neural search results are returned
        """
        # When: Make neural search request
        response = await async_client.post(
            "/search",
            json={
                "q": "Python programming",
                "max_results": 5,
                "use_neural": True
            }
        )

        # Then: Verify neural search results
        assert response.status_code == 200
        data = response.json()

        assert data["mode"] in ["neural", "hybrid"]
        assert len(data["results"]) <= 5
        assert all("score" in result for result in data["results"])
```

## 8. 일반 지침

### DO ✅

1. **명확한 docstring 작성**: TAG + Given-When-Then 패턴 사용
2. **async_client 픽스처 사용**: 신규 테스트는 표준 픽스처 사용
3. **인증 우회 문서화**: `@CODE:AUTH-BYPASS` TAG 추가
4. **테스트 격리 보장**: try-finally로 cleanup 처리
5. **의미 있는 assertion**: 단순 status code 외에 응답 내용 검증
6. **테스트 마커 사용**: `@pytest.mark.integration`, `@pytest.mark.asyncio`

### DON'T ❌

1. **레거시 픽스처 사용 금지**: 신규 코드에서 `api_client` 사용 금지
2. **인증 우회 누락**: 통합 테스트에서 403 에러 방지
3. **TAG 누락**: 모든 테스트에 적절한 TAG 추가
4. **Cleanup 누락**: `app.dependency_overrides.clear()` 필수
5. **하드코딩된 값**: 테스트 데이터는 의미 있는 변수로 관리
6. **과도한 Mock**: 필요한 경우에만 최소한의 Mock 사용

### 테스트 실행

```bash
# 전체 테스트 실행
pytest -n auto

# 특정 테스트 파일 실행
pytest tests/integration/test_hybrid_search.py -v

# 특정 테스트 함수 실행
pytest tests/integration/test_hybrid_search.py::TestHybridSearch::test_neural_search -v

# 통합 테스트만 실행
pytest -m integration -v

# 실패한 테스트만 재실행
pytest --lf -v
```

## 참고 자료

- **픽스처 가이드**: [fixture-guidelines.md](./fixture-guidelines.md)
- **인증 우회 패턴**: [auth-bypass-patterns.md](./auth-bypass-patterns.md)
- **Phase 1 구현**: `tests/conftest.py`, `tests/integration/test_hybrid_search.py`
- **pytest 공식 문서**: [pytest.org](https://docs.pytest.org/)
- **FastAPI 테스팅**: [Testing - FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
