# 테스트 인증 우회 패턴

@DOC:AUTH-BYPASS-PATTERNS | SPEC-TEST-STABILIZE-002

## 개요

FastAPI 통합 테스트에서 API 키 인증을 우회하는 표준 패턴을 설명합니다. 의존성 주입(Dependency Injection) 메커니즘을 활용하여 데이터베이스/Redis 연결 없이 안전하게 인증을 모킹합니다.

## 권장 패턴: app.dependency_overrides (Option A)

### 개념

FastAPI의 `app.dependency_overrides` 딕셔너리를 사용하여 프로덕션 의존성을 테스트용 mock 함수로 대체합니다. 이 방식은 FastAPI가 공식적으로 지원하며, 테스트 격리와 클린업을 보장합니다.

### 구현 예시

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_search_timeout_fallback(self):
    """
    @TEST:NEURAL-001:0.2.2
    @CODE:AUTH-BYPASS | SPEC-TEST-STABILIZE-001

    Test vector search timeout with BM25 fallback

    Given: Vector search exceeds timeout (100ms)
    When: Neural search is requested
    Then: Fallback to BM25, mode="bm25_fallback"
    """
    from apps.api.routers.search_router import search_router
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    import asyncio

    app = FastAPI()
    app.include_router(search_router)

    # Step 1: Import authentication dependency
    from apps.api.deps import verify_api_key
    from apps.api.security.api_key_storage import APIKeyInfo
    from datetime import datetime, timezone

    # Step 2: Create mock function
    async def mock_verify_api_key() -> APIKeyInfo:
        return APIKeyInfo(
            key_id="test_key_001",
            name="Test API Key",
            description="Mock API key for integration tests",
            scope="write",
            permissions=["*"],
            allowed_ips=None,
            rate_limit=1000,
            is_active=True,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
            total_requests=0,
            failed_requests=0,
        )

    # Step 3: Override dependency
    app.dependency_overrides[verify_api_key] = mock_verify_api_key

    # Step 4: Create test client
    client = TestClient(app)

    try:
        # Step 5: Execute test
        response = client.post(
            "/search",
            json={"q": "test query", "max_results": 5, "use_neural": True},
        )

        # Step 6: Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "bm25_fallback"

    finally:
        # Step 7: Clean up override
        app.dependency_overrides.clear()
```

### 핵심 요소

1. **Import 의존성**: 프로덕션 코드에서 사용하는 실제 의존성 함수를 import
2. **Mock 함수 생성**: 동일한 반환 타입(`APIKeyInfo`)을 가진 mock 함수 정의
3. **Override 적용**: `app.dependency_overrides[원본] = mock` 형식으로 교체
4. **Try-Finally 블록**: 테스트 실패 시에도 반드시 cleanup 실행
5. **Clear 호출**: `app.dependency_overrides.clear()`로 다른 테스트 격리 보장

## 대안 패턴: X-API-Key 헤더 (Option B)

### 개념

테스트 환경에서 API 키 검증을 간소화하고 미리 정의된 테스트 키를 허용하는 방식입니다. `conftest.py`의 `async_client` 픽스처가 이미 이 패턴을 적용하고 있습니다.

### 구현 예시

```python
@pytest.fixture
async def async_client() -> AsyncGenerator:
    """
    Async HTTP client with pre-configured authentication bypass
    """
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app
    from apps.api.deps import verify_api_key
    from apps.api.security.api_key_storage import APIKeyInfo

    async def mock_verify_api_key() -> APIKeyInfo:
        """Mock API key verification for tests"""
        return APIKeyInfo(
            key_id="test_key_001",
            name="Test API Key",
            description="Mock API key for integration tests",
            scope="write",
            permissions=["*"],
            allowed_ips=None,
            rate_limit=1000,
            is_active=True,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            last_used_at=None,
            total_requests=0,
            failed_requests=0,
        )

    # Apply global override in fixture
    app.dependency_overrides[verify_api_key] = mock_verify_api_key

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=10.0,
    ) as client:
        yield client

    # Clean up after all tests using this fixture
    app.dependency_overrides.clear()
```

### 장단점 비교

| 특성 | Option A (override per test) | Option B (fixture level) |
|------|------------------------------|--------------------------|
| **격리 수준** | 테스트별 독립적 override | 픽스처 스코프 내 공유 |
| **유연성** | 테스트마다 다른 mock 가능 | 고정된 mock 사용 |
| **코드 중복** | 각 테스트에 반복 코드 | 픽스처 한 곳에만 정의 |
| **디버깅** | 테스트 내에서 명시적으로 확인 가능 | 픽스처 내부 확인 필요 |
| **권장 사용** | 특수 인증 시나리오 테스트 | 일반적인 API 엔드포인트 테스트 |

## 주의사항

### 1. 항상 try-finally 사용

```python
# ❌ 잘못된 예시
app.dependency_overrides[verify_api_key] = mock_verify_api_key
response = client.post("/search", json={...})
app.dependency_overrides.clear()  # assertion 실패 시 실행 안됨!

# ✅ 올바른 예시
app.dependency_overrides[verify_api_key] = mock_verify_api_key
try:
    response = client.post("/search", json={...})
    assert response.status_code == 200
finally:
    app.dependency_overrides.clear()  # 항상 실행됨
```

### 2. 반환 타입 일치

Mock 함수의 반환 타입은 원본 의존성과 정확히 일치해야 합니다:

```python
# ❌ 잘못된 예시
async def mock_verify_api_key() -> dict:  # 잘못된 타입!
    return {"key_id": "test"}

# ✅ 올바른 예시
async def mock_verify_api_key() -> APIKeyInfo:
    return APIKeyInfo(key_id="test", ...)
```

### 3. 테스트 격리

여러 테스트가 동일한 FastAPI 앱 인스턴스를 공유하는 경우, 각 테스트 후 반드시 clear 호출:

```python
# Option 1: 각 테스트에서 명시적 cleanup
finally:
    app.dependency_overrides.clear()

# Option 2: pytest fixture teardown
@pytest.fixture
def auth_bypass():
    from apps.api.main import app
    # ... setup override ...
    yield
    app.dependency_overrides.clear()
```

## TAG 통합

인증 우회 관련 변경사항은 다음 TAG를 사용합니다:

- **@CODE:AUTH-BYPASS**: 인증 우회 패턴 적용 코드
- **@TEST:PHASE-2-STABILIZATION**: Phase 2에서 수정된 테스트

## 참고 자료

- Phase 1 구현: `tests/integration/test_hybrid_search.py` Line 110-155
- Fixture 가이드: `tests/docs/fixture-guidelines.md`
- FastAPI 공식 문서: [Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
