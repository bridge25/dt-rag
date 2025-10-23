# Acceptance Criteria - ENV-VALIDATE-001

## 개요

본 문서는 `SPEC-ENV-VALIDATE-001`의 상세한 수락 기준을 정의한다. 모든 시나리오는 Given-When-Then 형식으로 작성되었으며, 각 시나리오는 독립적으로 테스트 가능하다.

---

## Scenario 1: 프로덕션 환경에서 API 키 부재 시 시스템 시작 거부

### Given
- 환경 변수 `ENVIRONMENT=production` 설정
- `OPENAI_API_KEY` 환경 변수가 설정되지 않음
- FastAPI 앱 시작 준비

### When
- 앱 시작 이벤트가 트리거됨
- `validate_environment()` 함수가 실행됨

### Then
- `ValueError` 예외가 발생해야 한다
- 에러 메시지는 다음을 포함해야 한다:
  ```
  OPENAI_API_KEY environment variable is REQUIRED in production.
  ```
- 앱은 시작되지 않아야 한다
- 로그 레벨: ERROR

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_production_missing_api_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="REQUIRED in production"):
        await validate_environment()
```

### 검증 기준
- [ ] ValueError 발생 확인
- [ ] 에러 메시지 내용 확인
- [ ] 로그에 에러 메시지 기록 확인

---

## Scenario 2: 프로덕션 환경에서 무효한 API 키 형식 시 시스템 시작 거부

### Given
- 환경 변수 `ENVIRONMENT=production` 설정
- `OPENAI_API_KEY=invalid-key` (잘못된 형식)
  - 접두사가 `sk-`가 아님
  - 또는 길이가 48자 미만

### When
- 앱 시작 이벤트가 트리거됨
- `_validate_openai_api_key()` 함수가 API 키 형식을 검증함

### Then
- `ValueError` 예외가 발생해야 한다
- 에러 메시지는 다음을 포함해야 한다:
  ```
  Invalid OPENAI_API_KEY format.
  OpenAI API keys must start with 'sk-' and be at least 48 characters.
  ```
- 앱은 시작되지 않아야 한다
- 로그 레벨: ERROR

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_production_invalid_api_key_format(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OPENAI_API_KEY", "invalid-key")

    with pytest.raises(ValueError, match="Invalid OPENAI_API_KEY format"):
        await validate_environment()
```

### 검증 기준
- [ ] ValueError 발생 확인
- [ ] API 키 형식 검증 로직 작동 확인
- [ ] 에러 메시지 정확성 확인

---

## Scenario 3: 개발 환경에서 API 키 부재 시 경고와 함께 폴백 허용

### Given
- 환경 변수 `ENVIRONMENT=development` 설정
- `OPENAI_API_KEY` 환경 변수가 설정되지 않음
- FastAPI 앱 시작 준비

### When
- 앱 시작 이벤트가 트리거됨
- `validate_environment()` 함수가 실행됨

### Then
- 예외가 발생하지 않아야 한다
- INFO 레벨 로그가 출력되어야 한다:
  ```
  ℹ️ OPENAI_API_KEY not set in development.
  Embedding service will use dummy/fallback mode.
  ```
- 앱은 정상적으로 시작되어야 한다
- `embedding_service` 인스턴스는 폴백 모드로 초기화되어야 한다

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_development_missing_api_key_fallback(monkeypatch, caplog):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Should not raise
    await validate_environment()

    # Check log message
    assert "OPENAI_API_KEY not set in development" in caplog.text
    assert "dummy/fallback mode" in caplog.text
```

### 검증 기준
- [ ] 예외 발생하지 않음
- [ ] INFO 로그 출력 확인
- [ ] 앱 정상 시작 확인
- [ ] 폴백 모드 활성화 확인

---

## Scenario 4: OpenAI API 401 Unauthorized 에러 시 명시적 경고 로깅

### Given
- OpenAI 클라이언트가 초기화됨
- `OPENAI_API_KEY`가 설정되어 있지만 유효하지 않음 (또는 만료됨)
- 임베딩 생성 요청 발생

### When
- `generate_embedding("test text")` 호출
- OpenAI API가 401 Unauthorized 에러 반환

### Then
- ERROR 레벨 로그가 출력되어야 한다:
  ```
  ❌ OpenAI API Key is invalid or expired (401 Unauthorized).
  Please check OPENAI_API_KEY environment variable.
  ```
- 예외가 재발생되어야 한다 (폴백 트리거)
- 더미 임베딩으로 폴백되어야 한다 (개발 환경)

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_openai_401_error_logging(monkeypatch, caplog):
    mock_client = AsyncMock()
    mock_client.embeddings.create.side_effect = Exception("401 Unauthorized")

    service = EmbeddingService()
    service._openai_client = mock_client

    result = await service.generate_embedding("test")

    # Check error log
    assert "401 Unauthorized" in caplog.text
    assert "OpenAI API Key is invalid or expired" in caplog.text

    # Should fallback to dummy
    assert len(result) == 1536
```

### 검증 기준
- [ ] 401 에러 감지 확인
- [ ] ERROR 로그 출력 확인
- [ ] 폴백 동작 확인
- [ ] 더미 임베딩 생성 확인 (1536차원)

---

## Scenario 5: Health Check 엔드포인트에 API 키 상태 반영

### Given
- FastAPI 앱이 실행 중
- `/health` 엔드포인트가 존재
- 다양한 API 키 상태 (유효/무효/없음)

### When
- `/health` 엔드포인트에 GET 요청 전송

### Then
- 응답 JSON에 다음 필드가 포함되어야 한다:
  ```json
  {
    "status": "healthy|degraded|unhealthy",
    "api_key_configured": true|false,
    "fallback_mode": true|false,
    "openai_available": true|false
  }
  ```
- API 키 유효 + OpenAI 사용 중 → `status: "healthy"`
- API 키 없음 + Sentence Transformers 폴백 → `status: "degraded"`
- 모든 모델 사용 불가 → `status: "unhealthy"`

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_health_check_api_key_status(client, monkeypatch):
    # Case 1: Valid API key
    monkeypatch.setenv("OPENAI_API_KEY", "sk-" + "x" * 46)
    response = await client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "healthy"
    assert data["api_key_configured"] is True
    assert data["fallback_mode"] is False

    # Case 2: No API key (fallback)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = await client.get("/health")
    data = response.json()

    assert data["status"] in ["degraded", "unhealthy"]
    assert data["api_key_configured"] is False
    assert data["fallback_mode"] is True
```

### 검증 기준
- [ ] HTTP 200 응답 (모든 상태에서)
- [ ] `status` 필드 정확성 확인
- [ ] `api_key_configured` 필드 정확성 확인
- [ ] `fallback_mode` 필드 정확성 확인

---

## Scenario 6: 스테이징 환경에서 API 키 부재 시 WARNING 로그

### Given
- 환경 변수 `ENVIRONMENT=staging` 설정
- `OPENAI_API_KEY` 환경 변수가 설정되지 않음

### When
- 앱 시작 이벤트가 트리거됨

### Then
- 예외가 발생하지 않아야 한다
- WARNING 레벨 로그가 출력되어야 한다:
  ```
  ⚠️ OpenAI API key is invalid or missing in staging.
  Embedding service will use fallback mode.
  ```
- 앱은 정상적으로 시작되어야 한다

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_staging_missing_api_key_warning(monkeypatch, caplog):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    await validate_environment()

    assert "OpenAI API key is invalid or missing in staging" in caplog.text
    assert caplog.records[-1].levelname == "WARNING"
```

### 검증 기준
- [ ] 예외 발생하지 않음
- [ ] WARNING 로그 출력 확인
- [ ] 로그 메시지 내용 확인

---

## Scenario 7: API 키 형식 검증 함수 단위 테스트

### Given
- `_validate_openai_api_key()` 함수가 존재
- 다양한 API 키 형식 입력

### When
- 함수 호출

### Then
- 다음 케이스를 검증해야 한다:

| 입력 | 예상 결과 | 설명 |
|------|-----------|------|
| `sk-` + 45자 랜덤 문자열 | `True` | 유효한 표준 키 |
| `sk-proj-` + 40자 랜덤 문자열 | `True` | 유효한 프로젝트 키 |
| `invalid-key` | `False` | 접두사 불일치 |
| `sk-short` | `False` | 길이 부족 |
| `""` (빈 문자열) | `False` | 빈 값 |
| `None` | `False` | Null 값 |

### 테스트 코드 예시
```python
def test_validate_openai_api_key():
    # Valid keys
    assert _validate_openai_api_key("sk-" + "x" * 46) is True
    assert _validate_openai_api_key("sk-proj-" + "y" * 40) is True

    # Invalid keys
    assert _validate_openai_api_key("invalid-key") is False
    assert _validate_openai_api_key("sk-short") is False
    assert _validate_openai_api_key("") is False
    assert _validate_openai_api_key(None) is False
```

### 검증 기준
- [ ] 모든 테스트 케이스 통과
- [ ] Edge case 처리 확인 (None, 빈 문자열)
- [ ] 접두사 검증 정확성 확인
- [ ] 길이 검증 정확성 확인

---

## Scenario 8: 더미 임베딩 모드 시 Health Check 상태 "degraded" 반환

### Given
- `OPENAI_API_KEY` 환경 변수가 설정되지 않음
- Sentence Transformers 폴백 모드 활성화
- `/health` 엔드포인트 호출

### When
- Health check 요청

### Then
- 응답 JSON은 다음을 포함해야 한다:
  ```json
  {
    "status": "degraded",
    "fallback_mode": true,
    "warning": "Using Sentence Transformers fallback (768d -> 1536d padded)"
  }
  ```
- HTTP 상태 코드는 200이어야 한다 (Kubernetes Probe 호환)

### 테스트 코드 예시
```python
@pytest.mark.asyncio
async def test_health_check_degraded_mode(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    service = EmbeddingService()
    health = service.health_check()

    assert health["status"] in ["degraded", "unhealthy"]
    assert health["fallback_mode"] is True
    if "warning" in health:
        assert "fallback" in health["warning"].lower()
```

### 검증 기준
- [ ] `status: "degraded"` 반환 확인
- [ ] `fallback_mode: true` 반환 확인
- [ ] 경고 메시지 포함 확인
- [ ] HTTP 200 응답 확인

---

## 품질 게이트 (Quality Gates)

### 필수 조건
- [ ] 모든 Scenario 테스트 통과 (8개)
- [ ] 코드 커버리지 80% 이상
- [ ] Linter 검증 통과 (flake8, mypy)
- [ ] 통합 테스트 통과

### 권장 조건
- [ ] 코드 커버리지 90% 이상
- [ ] 성능 테스트 (API 키 검증 10초 이내)
- [ ] 보안 스캔 통과 (bandit)

---

## 테스트 실행 방법

### 단위 테스트
```bash
pytest tests/test_config.py -v
pytest tests/test_embedding_service.py -v
```

### 통합 테스트
```bash
pytest tests/integration/test_env_validation_e2e.py -v
```

### 커버리지 측정
```bash
pytest --cov=apps/api --cov-report=html --cov-report=term
```

### 특정 시나리오만 실행
```bash
pytest -k "test_production_missing_api_key" -v
```

---

## 완료 조건 (Definition of Done)

- [ ] 모든 Scenario 테스트 작성 완료
- [ ] 모든 Scenario 테스트 통과
- [ ] 코드 리뷰 승인
- [ ] 문서화 완료 (spec.md, plan.md 업데이트)
- [ ] CI/CD 파이프라인 통과
- [ ] QA 팀 승인 (Team 모드인 경우)

---

## 참고 자료

### 테스트 도구
- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-cov: https://pytest-cov.readthedocs.io/

### BDD (Behavior-Driven Development)
- Given-When-Then 형식: https://martinfowler.com/bliki/GivenWhenThen.html

### OpenAI API
- Error Codes: https://platform.openai.com/docs/guides/error-codes
- Authentication: https://platform.openai.com/docs/api-reference/authentication
