# Implementation Plan - ENV-VALIDATE-001

## 개요

본 문서는 `SPEC-ENV-VALIDATE-001`의 구현 계획을 단계별로 정의한다. 각 Phase는 독립적으로 테스트 가능하며, RED-GREEN-REFACTOR 사이클을 따른다.

---

## Phase 1: API 키 형식 검증 함수 추가

### 목표
`config.py`에 API 키 형식 검증 함수를 추가하여 재사용 가능한 검증 로직을 제공한다.

### 작업 항목

1. **함수 구현**: `_validate_openai_api_key(api_key: str) -> bool`
   - 접두사 검증: `sk-` 또는 `sk-proj-`
   - 최소 길이: 48자
   - 빈 문자열 처리

2. **테스트 작성** (RED)
   - 유효한 API 키: `sk-` + 45자
   - 유효한 API 키: `sk-proj-` + 40자
   - 무효한 API 키: 짧은 길이
   - 무효한 API 키: 잘못된 접두사
   - 빈 문자열 처리

3. **구현 완료** (GREEN)
   - 모든 테스트 통과 확인

4. **리팩토링** (REFACTOR)
   - 코드 간결성 확인
   - 타입 힌트 추가

### 기술적 접근 방법
- `config.py`의 `_validate_secret_strength()` 패턴을 참조
- 단순하고 명확한 검증 로직 (복잡한 정규식 사용하지 않음)
- Docstring에 검증 규칙 명시

### 영향 범위
- **파일**: `apps/api/config.py`
- **테스트**: `tests/test_config.py` (기존 파일에 추가)
- **의존성**: 없음 (독립 함수)

---

## Phase 2: Startup 검증 로직 구현

### 목표
FastAPI 앱 시작 시 환경별로 API 키를 검증하여 프로덕션 오동작을 방지한다.

### 작업 항목

1. **Startup 이벤트 핸들러 추가**
   - `@app.on_event("startup")` 데코레이터 사용
   - 환경별 분기 로직 구현

2. **환경별 검증 정책**
   - **프로덕션**: API 키 필수, 형식 검증, 실패 시 ValueError
   - **스테이징**: API 키 권장, 실패 시 WARNING 로그
   - **개발/테스트**: API 키 선택, 실패 시 INFO 로그

3. **로그 메시지 표준화**
   - 성공: `✅ OpenAI API key validated (environment)`
   - 경고: `⚠️ OpenAI API key is invalid or missing`
   - 에러: `❌ OPENAI_API_KEY is REQUIRED in production`

4. **테스트 작성** (RED)
   - 프로덕션 환경 + API 키 없음 → ValueError
   - 프로덕션 환경 + 무효한 API 키 → ValueError
   - 프로덕션 환경 + 유효한 API 키 → 성공
   - 개발 환경 + API 키 없음 → INFO 로그
   - 스테이징 환경 + 무효한 API 키 → WARNING 로그

5. **구현 완료** (GREEN)
   - 모든 환경 시나리오 테스트 통과

6. **리팩토링** (REFACTOR)
   - 중복 코드 제거
   - 로그 메시지 포맷 일관성 확인

### 기술적 접근 방법
- `env_manager.get_env_manager().current_env`로 환경 확인
- Phase 1의 `_validate_openai_api_key()` 함수 재사용
- FastAPI Lifespan 이벤트 활용

### 영향 범위
- **파일**: `apps/api/main.py`
- **테스트**: `tests/test_startup_validation.py` (신규 생성)
- **의존성**: `config.py`, `env_manager.py`

### 리스크 및 대응
- **리스크**: 기존 로컬 개발 환경에 API 키 없어서 시작 실패
- **대응**: 개발 환경에서는 경고만 출력하고 계속 진행

---

## Phase 3: Health Check 확장

### 목표
`/health` 엔드포인트에 API 키 상태와 폴백 모드를 반영하여 운영 가시성을 향상시킨다.

### 작업 항목

1. **`health_check()` 함수 수정**
   - API 키 유효성 검증 추가
   - `api_key_configured` 필드 추가
   - `fallback_mode` 필드 추가
   - 상태별 반환값 정의:
     - `healthy`: OpenAI 클라이언트 사용 중, API 키 유효
     - `degraded`: Sentence Transformers 폴백 모드
     - `unhealthy`: 모든 모델 사용 불가

2. **응답 스키마 확장**
   ```json
   {
     "status": "healthy|degraded|unhealthy",
     "model_name": "text-embedding-3-large",
     "openai_available": true,
     "api_key_configured": true,
     "fallback_mode": false,
     "warning": "Optional warning message"
   }
   ```

3. **테스트 작성** (RED)
   - OpenAI 사용 중 → `status: healthy`
   - Sentence Transformers 폴백 → `status: degraded`
   - 모델 없음 → `status: unhealthy`
   - API 키 없음 → `api_key_configured: false`

4. **구현 완료** (GREEN)
   - Health check 응답 검증

5. **리팩토링** (REFACTOR)
   - 상태 판단 로직 명확성 확보

### 기술적 접근 방법
- `embedding_service.py`의 `health_check()` 함수 수정
- Phase 1의 검증 함수 재사용 (또는 간단한 검증 로직 내장)
- Kubernetes Readiness/Liveness Probe 호환 고려

### 영향 범위
- **파일**: `apps/api/embedding_service.py`
- **테스트**: `tests/test_embedding_service.py` (기존 파일에 추가)
- **의존성**: 없음

---

## Phase 4: 401 에러 핸들링 강화

### 목표
OpenAI API 호출 시 401 Unauthorized 에러를 명시적으로 처리하여 디버깅을 용이하게 한다.

### 작업 항목

1. **`_generate_openai_embedding()` 함수 수정**
   - 401 에러 명시적 catch
   - 명확한 에러 메시지 로깅
   - 에러 재발생 (fallback 트리거)

2. **로그 메시지**
   ```
   ❌ OpenAI API Key is invalid or expired (401 Unauthorized).
   Please check OPENAI_API_KEY environment variable.
   ```

3. **테스트 작성** (RED)
   - Mock OpenAI 클라이언트 401 에러 → 로그 확인
   - 401 에러 후 폴백 동작 확인

4. **구현 완료** (GREEN)
   - 에러 처리 테스트 통과

5. **리팩토링** (REFACTOR)
   - 에러 메시지 일관성 확인
   - 다른 에러 코드도 고려 (429 Rate Limit 등)

### 기술적 접근 방법
- `try-except` 블록에서 에러 메시지 검사
- `"401" in str(e)` 또는 `"unauthorized" in str(e).lower()` 검사
- 로그 레벨: ERROR

### 영향 범위
- **파일**: `apps/api/embedding_service.py`
- **테스트**: `tests/test_embedding_service.py` (기존 파일에 추가)
- **의존성**: 없음

---

## Phase 5: 통합 테스트 및 문서화

### 목표
모든 Phase를 통합하고 엔드투엔드 시나리오를 검증한다.

### 작업 항목

1. **통합 테스트 시나리오**
   - 프로덕션 환경 시뮬레이션 (API 키 없음 → 시작 실패)
   - 개발 환경 시뮬레이션 (API 키 없음 → 폴백 모드)
   - Health check 엔드포인트 호출 검증

2. **문서 업데이트**
   - `spec.md` HISTORY 섹션 업데이트 (v0.2.0 IMPLEMENTED)
   - `acceptance.md` 시나리오 검증 완료 표시

3. **코드 리뷰 준비**
   - 모든 테스트 통과 확인
   - Linter 검증 (flake8, mypy)
   - 코드 커버리지 확인 (pytest-cov)

### 기술적 접근 방법
- Docker Compose로 프로덕션 환경 시뮬레이션
- `pytest -v --cov=apps/api` 실행
- CI/CD 파이프라인 통과 확인

### 영향 범위
- **파일**: 모든 Phase 파일
- **테스트**: `tests/integration/test_env_validation_e2e.py` (신규 생성)
- **의존성**: Docker, pytest-cov

---

## 기술 스택 및 도구

### 언어 및 프레임워크
- Python 3.11+
- FastAPI 0.104+

### 테스트 도구
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock

### 환경 관리
- `env_manager.py` (기존)
- `config.py` (기존)

### 로깅
- Python `logging` 모듈
- 로그 레벨: INFO, WARNING, ERROR

---

## 리스크 및 대응 전략

### 리스크 1: 기존 로컬 개발 환경 영향
- **설명**: 로컬 개발자가 API 키 없이 작업 중인 경우 시작 실패 가능
- **대응**: 개발 환경에서는 경고만 출력하고 계속 진행
- **확인 방법**: Phase 2 테스트 시나리오로 검증

### 리스크 2: Health Check 호환성
- **설명**: Kubernetes Probe가 새로운 `degraded` 상태를 어떻게 처리할지 불확실
- **대응**: `status` 필드 외에 HTTP 상태 코드는 200 유지
- **확인 방법**: Kubernetes 배포 테스트

### 리스크 3: 401 에러 오탐
- **설명**: 네트워크 오류를 401 에러로 오인할 가능성
- **대응**: 에러 메시지를 명확히 검사 (`"401"` 또는 `"unauthorized"`)
- **확인 방법**: Mock 테스트로 다양한 에러 시나리오 검증

---

## 우선순위 및 마일스톤

### 1차 목표 (필수)
- Phase 1: API 키 형식 검증 함수
- Phase 2: Startup 검증 로직 (프로덕션 보호)

### 2차 목표 (권장)
- Phase 3: Health Check 확장
- Phase 4: 401 에러 핸들링

### 3차 목표 (최적화)
- Phase 5: 통합 테스트 및 문서화
- 코드 커버리지 90% 이상 달성

---

## 완료 조건 (Definition of Done)

- [ ] 모든 Phase의 테스트 통과
- [ ] 코드 리뷰 승인
- [ ] Linter 검증 통과 (flake8, mypy)
- [ ] 코드 커버리지 80% 이상
- [ ] `acceptance.md`의 모든 시나리오 검증 완료
- [ ] CI/CD 파이프라인 통과
- [ ] 문서 업데이트 완료 (HISTORY 섹션)

---

## 참고 자료

### 코드 참조
- `apps/api/config.py:260-292` - SECRET_KEY 검증 패턴
- `apps/api/embedding_service.py:86-93` - 현재 API 키 처리
- `apps/api/embedding_service.py:332-367` - Health Check 함수

### 외부 문서
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [OpenAI API Error Codes](https://platform.openai.com/docs/guides/error-codes)
- [12-Factor App: Config](https://12factor.net/config)
