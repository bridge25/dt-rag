# @SPEC:ENV-VALIDATE-001 - OpenAI API 키 환경변수 검증 및 개발환경 더미 폴백

---
id: ENV-VALIDATE-001
version: 1.0.0
status: completed
created: 2025-10-12
updated: 2025-10-12
implemented: 2025-10-12
author: @Claude
priority: high
category: security
labels:
  - environment-variables
  - api-key
  - validation
  - openai
depends_on:
  - EMBED-001
scope:
  packages:
    - apps/api
  files:
    - apps/api/embedding_service.py
    - apps/api/config.py
    - apps/api/main.py
commits:
  - 5ceea19: "feat(ENV-VALIDATE-001): Implement OpenAI API key validation (Phase 1-2)"
  - a110a5c: "feat(ENV-VALIDATE-001): Implement health check expansion and 401 error logging (Phase 3-4)"
test_results:
  total: 18
  passed: 18
  failed: 0
  coverage: "100%"
---

## HISTORY

| Version | Date       | Author  | Changes          |
|---------|------------|---------|------------------|
| 0.1.0   | 2025-10-12 | @Claude | INITIAL - SPEC 최초 작성 |
| 1.0.0   | 2025-10-12 | @Claude | COMPLETED - Phase 1-4 구현 완료, 테스트 18개 전체 통과 |

---

## 개요 (Overview)

현재 `embedding_service.py`는 `OPENAI_API_KEY` 환경변수 부재 시 자동으로 Sentence Transformers 폴백 모드로 전환되지만, 프로덕션 환경에서 이러한 자동 폴백은 예상치 못한 동작을 야기할 수 있다. 본 SPEC은 환경변수 검증 로직을 추가하여 다음을 달성한다:

1. **프로덕션 환경**: API 키 부재 시 시스템 시작 거부
2. **개발 환경**: API 키 부재 시 경고와 함께 더미 모드 허용
3. **API 키 형식 검증**: `sk-` 접두사, 최소 길이 확인
4. **Health Check 확장**: API 키 상태 및 폴백 모드를 `/health` 엔드포인트에 반영

이를 통해 프로덕션 환경의 오동작을 사전에 차단하고, 개발 환경에서의 유연성을 유지한다.

---

## Environment (환경 및 가정사항)

### 현재 환경 분석

1. **OpenAI API 키 형식**
   - 접두사: `sk-` (48자 이상)
   - 예시: `sk-proj-...` (실제 키는 환경변수로 관리)

2. **기존 폴백 메커니즘**
   - `embedding_service.py:86-93`: API 키 부재 시 Sentence Transformers 자동 전환
   - `embedding_service.py:305-318`: `_generate_dummy_embedding()` 더미 벡터 생성

3. **참조 코드 패턴**
   - `config.py:260-292`: SECRET_KEY 검증 로직 (환경별 분기, 프로덕션 필수 검증)
   - `config.py:86-117`: `_validate_secret_strength()` 강도 검증 함수

4. **환경 구분**
   - `env_manager.py`: Environment Enum (DEVELOPMENT, TESTING, STAGING, PRODUCTION)
   - 현재 환경: `config.environment` 속성으로 접근 가능

---

## Assumptions (전제 조건)

1. **프로덕션 환경**
   - 프로덕션 환경에서는 항상 유효한 OpenAI API 키가 필수
   - 더미 임베딩 모드는 프로덕션에서 절대 허용되지 않음

2. **개발/테스트 환경**
   - 개발 환경에서는 API 키 없이 더미 모드 허용 (경고 로그 필수)
   - 테스트 환경에서는 모든 모드 허용 (테스트 격리)

3. **API 키 형식 표준**
   - OpenAI API 키는 `sk-` 또는 `sk-proj-`로 시작
   - 최소 길이: 48자 (OpenAI 공식 형식)

4. **Startup 검증**
   - 시스템 시작 시 10초 이내에 API 키 검증 완료
   - 검증 실패 시 명확한 에러 메시지 제공

---

## Requirements (요구사항 - EARS)

### Ubiquitous (필수 요구사항)

**@REQ:ENV-VALIDATE-001-U1** - API 키 존재 검증
- 시스템은 `OPENAI_API_KEY` 환경 변수의 존재를 검증해야 한다

**@REQ:ENV-VALIDATE-001-U2** - API 키 형식 검증
- 시스템은 API 키 형식을 검증해야 한다 (접두사 `sk-`, 최소 길이 48자)

**@REQ:ENV-VALIDATE-001-U3** - 환경별 정책 분리
- 시스템은 환경(개발/스테이징/프로덕션)에 따라 다른 검증 정책을 적용해야 한다

### Event-driven (이벤트 기반 요구사항)

**@REQ:ENV-VALIDATE-001-E1** - Startup 검증
- WHEN 시스템이 시작되면, API 키 존재와 형식을 검증해야 한다

**@REQ:ENV-VALIDATE-001-E2** - 401 에러 처리
- WHEN OpenAI API 호출이 401 Unauthorized 에러를 반환하면, 명시적 경고를 로깅해야 한다

**@REQ:ENV-VALIDATE-001-E3** - 더미 모드 폴백 경고
- WHEN 더미 임베딩으로 폴백하면, WARNING 레벨 로그를 발생시켜야 한다

### State-driven (상태 기반 요구사항)

**@REQ:ENV-VALIDATE-001-S1** - 개발 환경 허용
- WHILE 개발 환경일 때, API 키 없이 더미 임베딩 사용을 허용해야 한다

**@REQ:ENV-VALIDATE-001-S2** - 프로덕션 환경 거부
- WHILE 프로덕션 환경일 때, 유효하지 않은 API 키 시 시스템 시작을 거부해야 한다

**@REQ:ENV-VALIDATE-001-S3** - Health Check 상태 반영
- WHILE 더미 임베딩 모드일 때, health check는 "degraded" 상태를 반환해야 한다

### Constraints (제약사항)

**@CONSTRAINT:ENV-VALIDATE-001-C1** - 프로덕션 더미 모드 금지
- IF 프로덕션 환경이면, 더미 임베딩 사용 시 ValueError를 발생시켜야 한다

**@CONSTRAINT:ENV-VALIDATE-001-C2** - 검증 성능
- API 키 검증은 시스템 시작 시 10초 이내에 완료되어야 한다

**@CONSTRAINT:ENV-VALIDATE-001-C3** - 환경변수 우선순위
- `.env.local` > `.env.development` > `.env` 순서로 환경변수를 로드해야 한다

---

## Specifications (상세 명세)

### 1. API 키 검증 함수 (`config.py` 추가)

```python
def _validate_openai_api_key(api_key: str) -> bool:
    """
    OpenAI API 키 형식 검증

    Args:
        api_key: 검증할 API 키

    Returns:
        bool: 형식이 유효하면 True

    Validation Rules:
        - 접두사: "sk-" 또는 "sk-proj-"로 시작
        - 최소 길이: 48자
    """
    if not api_key:
        return False

    # 접두사 검증
    if not (api_key.startswith("sk-") or api_key.startswith("sk-proj-")):
        return False

    # 최소 길이 검증 (OpenAI 표준)
    if len(api_key) < 48:
        return False

    return True
```

### 2. Startup 검증 로직 (`main.py` 추가)

```python
@app.on_event("startup")
async def validate_environment():
    """
    시스템 시작 시 환경변수 검증

    Raises:
        ValueError: 프로덕션 환경에서 유효하지 않은 API 키
    """
    from .config import get_api_config
    from .env_manager import get_env_manager, Environment

    config = get_api_config()
    env_manager = get_env_manager()

    api_key = os.getenv("OPENAI_API_KEY")

    # 프로덕션 환경: API 키 필수
    if env_manager.current_env == Environment.PRODUCTION:
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is REQUIRED in production. "
                "Please set a valid OpenAI API key."
            )

        if not _validate_openai_api_key(api_key):
            raise ValueError(
                "Invalid OPENAI_API_KEY format. "
                "OpenAI API keys must start with 'sk-' and be at least 48 characters."
            )

        logger.info("✅ OpenAI API key validated (production)")

    # 스테이징 환경: API 키 필수 (경고)
    elif env_manager.current_env == Environment.STAGING:
        if not api_key or not _validate_openai_api_key(api_key):
            logger.warning(
                "⚠️ OpenAI API key is invalid or missing in staging. "
                "Embedding service will use fallback mode."
            )

    # 개발/테스트 환경: API 키 선택 (정보 로그)
    else:
        if not api_key:
            logger.info(
                "ℹ️ OPENAI_API_KEY not set in development. "
                "Embedding service will use dummy/fallback mode."
            )
        elif not _validate_openai_api_key(api_key):
            logger.warning(
                "⚠️ OPENAI_API_KEY format is invalid. "
                "Embedding service may fail or use fallback mode."
            )
        else:
            logger.info("✅ OpenAI API key validated (development)")
```

### 3. Health Check 확장 (`embedding_service.py` 수정)

```python
def health_check(self) -> Dict[str, Any]:
    """
    서비스 상태 확인 (API 키 검증 포함)
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        api_key_valid = bool(api_key and api_key.startswith("sk-") and len(api_key) >= 48)

        if self._openai_client and api_key_valid:
            return {
                "status": "healthy",
                "model_name": self.model_name,
                "model_loaded": True,
                "target_dimensions": self.TARGET_DIMENSIONS,
                "openai_available": True,
                "api_key_configured": True,
                "fallback_mode": False,
                "cache_size": len(self.embedding_cache)
            }
        elif self._sentence_transformer:
            return {
                "status": "degraded",
                "model_name": self.model_name,
                "model_loaded": True,
                "target_dimensions": self.TARGET_DIMENSIONS,
                "openai_available": False,
                "api_key_configured": api_key_valid,
                "fallback_mode": True,
                "cache_size": len(self.embedding_cache),
                "warning": "Using Sentence Transformers fallback (768d -> 1536d padded)"
            }
        else:
            return {
                "status": "unhealthy",
                "model_loaded": False,
                "api_key_configured": api_key_valid,
                "fallback_mode": True,
                "error": "No embedding model available (neither OpenAI nor Sentence Transformers)"
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "model_loaded": False,
            "fallback_mode": True
        }
```

### 4. 401 에러 핸들링 (`embedding_service.py` 수정)

```python
async def _generate_openai_embedding(self, text: str) -> List[float]:
    """OpenAI API로 임베딩 생성 (401 에러 핸들링 추가)"""
    try:
        response = await self._openai_client.embeddings.create(
            model=self.model_name,
            input=text,
            encoding_format="float",
            dimensions=1536
        )
        embedding = response.data[0].embedding
        return embedding

    except Exception as e:
        # 401 Unauthorized 에러 명시적 처리
        if "401" in str(e) or "unauthorized" in str(e).lower():
            logger.error(
                "❌ OpenAI API Key is invalid or expired (401 Unauthorized). "
                "Please check OPENAI_API_KEY environment variable."
            )
        raise
```

---

## Traceability (추적성)

### TAG Chain
- `@SPEC:ENV-VALIDATE-001` → 본 문서
- `@CODE:ENV-VALIDATE-001:CONFIG` → `apps/api/config.py` 수정 ✅
- `@CODE:ENV-VALIDATE-001:STARTUP` → `apps/api/main.py` 수정 ✅
- `@CODE:ENV-VALIDATE-001:HEALTH` → `apps/api/embedding_service.py` 수정 ✅
- `@TEST:ENV-VALIDATE-001:CONFIG` → `tests/unit/test_config.py` 추가 (6개) ✅
- `@TEST:ENV-VALIDATE-001:STARTUP` → `tests/test_main.py` 추가 (5개) ✅
- `@TEST:ENV-VALIDATE-001:HEALTH` → `tests/test_embedding_service.py` 추가 (5개) ✅
- `@TEST:ENV-VALIDATE-001:401ERROR` → `tests/test_embedding_service.py` 추가 (2개) ✅

### Implementation Summary
**Phase 1: API 키 형식 검증 함수 (`config.py`)**
- `_validate_openai_api_key()` 함수 추가 (L119-L143)
- 접두사 검증: `sk-` 또는 `sk-proj-`
- 최소 길이 검증: 48자
- 테스트: 6개 전체 통과

**Phase 2: Startup 검증 로직 (`main.py`)**
- `lifespan()` 함수 내 검증 로직 추가 (L117-L131)
- 프로덕션 환경: API 키 필수, 검증 실패 시 ValueError
- 개발 환경: 경고 로그, 폴백 모드 허용
- 테스트: 5개 전체 통과

**Phase 3: Health Check 확장 (`embedding_service.py`)**
- `health_check()` 메서드 확장 (L344-L397)
- API 키 상태 및 폴백 모드 명시
- `api_key_configured`, `fallback_mode` 필드 추가
- 테스트: 5개 전체 통과

**Phase 4: 401 에러 명시적 로깅 (`embedding_service.py`)**
- `_generate_openai_embedding()` 401 에러 핸들링 (L164-L185)
- AuthenticationError 및 401 status code 감지
- 명시적 에러 로그 출력
- 테스트: 2개 전체 통과

### Dependencies
- **Depends on**: `EMBED-001` (기존 임베딩 서비스)
- **Referenced by**: 향후 모든 API 키 검증 표준
- **Related SPEC**: `SPEC-JOB-OPTIMIZE-001` (리소스 최적화)

---

## References

### 코드 참조
- `apps/api/config.py:260-292` - SECRET_KEY 검증 패턴
- `apps/api/config.py:86-117` - `_validate_secret_strength()` 함수
- `apps/api/embedding_service.py:86-93` - 현재 API 키 처리 로직
- `apps/api/embedding_service.py:332-367` - `health_check()` 함수

### 외부 문서
- [OpenAI API Keys Documentation](https://platform.openai.com/docs/api-reference/authentication)
- [12-Factor App: Config](https://12factor.net/config)
