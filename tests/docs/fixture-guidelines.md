# 테스트 픽스처 가이드라인

@DOC:FIXTURE-GUIDELINES | SPEC-TEST-STABILIZE-002

## 개요

이 문서는 Phase 1 (SPEC-TEST-STABILIZE-001)에서 도입된 `async_client` 표준 픽스처 네이밍 컨벤션을 설명합니다. 프로젝트 전반의 일관성과 유지보수성을 향상시키기 위해 비동기 HTTP 클라이언트 픽스처의 명명 규칙을 표준화했습니다.

## 네이밍 컨벤션

### 표준 패턴 (권장)

**✅ `async_client` - 표준 픽스처 이름**

```python
@pytest.fixture
async def async_client() -> AsyncGenerator:
    """
    Async HTTP client for integration tests

    Provides an httpx AsyncClient configured with the FastAPI app
    for testing async API endpoints without running a real server.

    @CODE:FIXTURE-RENAME | SPEC-TEST-STABILIZE-001
    """
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app
    from apps.api.deps import verify_api_key
    from apps.api.security.api_key_storage import APIKeyInfo
    from datetime import timezone

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

    app.dependency_overrides[verify_api_key] = mock_verify_api_key

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=10.0,
    ) as client:
        yield client

    app.dependency_overrides.clear()
```

### 테스트 함수에서 사용

```python
@pytest.mark.asyncio
async def test_example(async_client):
    """
    @TEST:PHASE-2-STABILIZATION

    Given: Async client is available
    When: Making API request
    Then: Response should be successful
    """
    response = await async_client.get("/api/endpoint")
    assert response.status_code == 200
```

### 하위 호환성 별칭 (레거시 지원)

**⚠️ `api_client` - 하위 호환성 유지용 별칭**

기존 테스트 코드와의 호환성을 위해 `api_client` 별칭이 제공됩니다:

```python
@pytest.fixture
async def api_client(async_client) -> AsyncGenerator:
    """
    Backward compatibility alias for async_client fixture.

    @CODE:FIXTURE-RENAME | SPEC-TEST-STABILIZE-001
    """
    yield async_client
```

### 금지 패턴

**❌ 피해야 할 패턴:**

- `client` - 너무 일반적, 동기/비동기 구분 불명확
- `http_client` - 프로토콜보다 목적 중심 명명 선호
- `test_client` - FastAPI의 `TestClient`와 혼동 가능
- 프로젝트별 커스텀 이름 (예: `my_client`, `app_client`)

## TAG 통합

픽스처 관련 변경사항은 다음 TAG를 사용합니다:

- **@CODE:FIXTURE-RENAME**: 픽스처 이름 변경 또는 표준화
- **@TEST:PHASE-2-STABILIZATION**: Phase 2에서 수정된 테스트

## 마이그레이션 체크리스트

기존 테스트를 `async_client` 표준으로 마이그레이션할 때:

1. [ ] 테스트 함수 파라미터를 `api_client` → `async_client`로 변경
2. [ ] 테스트 상단에 `@TEST:PHASE-2-STABILIZATION` TAG 추가
3. [ ] Given-When-Then 형식의 docstring 추가 (없는 경우)
4. [ ] 테스트 실행하여 정상 동작 확인: `pytest tests/path/test_file.py::test_name -v`
5. [ ] 회귀 테스트 실행: `pytest -n auto`

## 참고 자료

- Phase 1 구현: `tests/conftest.py` Line 122-181
- 인증 우회 패턴: `tests/docs/auth-bypass-patterns.md`
- 테스트 모범 사례: `tests/docs/test-best-practices.md`
