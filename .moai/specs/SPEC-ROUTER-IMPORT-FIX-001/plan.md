# SPEC-ROUTER-IMPORT-FIX-001: Implementation Plan

@SPEC:ROUTER-IMPORT-FIX-001 | IMPLEMENTATION: Complete

---

## 개요

**목표**: API 라우터 모듈의 import 경로를 absolute에서 relative로 변경하여 ModuleNotFoundError 해결

**상태**: ✅ 구현 완료 (2025-10-23)

**변경 범위**: 4개 라우터 파일의 import 문 수정

---

## 1. 문제 분석

### 1.1 발생한 문제

**증상**:
```
ModuleNotFoundError: No module named 'deps'
ModuleNotFoundError: No module named 'database'
```

**원인**:
- FastAPI가 `apps.api.main:app` 형태로 ASGI 앱을 로드
- 라우터 파일이 `from deps import ...` 형태의 absolute import 사용
- Python이 `deps`를 독립 모듈로 해석 (패키지 컨텍스트 누락)

### 1.2 영향 범위

**영향받는 파일** (4개):
1. `apps/api/routers/health.py` → `deps` 모듈 import 실패
2. `apps/api/routers/classify.py` → `deps`, `database` 모듈 import 실패
3. `apps/api/routers/search.py` → `deps`, `database` 모듈 import 실패
4. `apps/api/routers/taxonomy.py` → `deps`, `database` 모듈 import 실패

**영향받지 않는 파일**:
- `apps/api/deps.py` (의존성 제공자)
- `apps/api/database.py` (DAO 제공자)
- `apps/api/main.py` (FastAPI 앱 진입점)

---

## 2. 해결 방안

### 2.1 기술적 접근

**선택된 방법**: Relative import 사용
- `from deps` → `from ..deps`
- `from database` → `from ..database`

**이유**:
- ✅ Python 패키지 구조 표준 준수
- ✅ FastAPI ASGI 로더와 호환
- ✅ 패키지 재배치 시 유연성 확보
- ✅ sys.path 의존성 제거

**대안 (선택되지 않음)**:
- ❌ sys.path 조작: 환경 의존적, 유지보수 어려움
- ❌ `__init__.py` 재구성: 기존 구조 대폭 변경 필요

### 2.2 구현 단계

**Phase 1**: Import 문 수정 ✅
1. `health.py`: `from deps` → `from ..deps` (1개 import 문)
2. `classify.py`: `from deps`, `from database` → `from ..deps`, `from ..database` (2개 import 문)
3. `search.py`: `from deps`, `from database` → `from ..deps`, `from ..database` (2개 import 문)
4. `taxonomy.py`: `from deps`, `from database` → `from ..deps`, `from ..database` (2개 import 문)

**Phase 2**: 검증 ✅
1. FastAPI 서버 시작 테스트
   ```bash
   uvicorn apps.api.main:app --reload
   ```
2. 엔드포인트 응답 확인
   - GET /healthz → 200 OK
   - POST /classify → 200 OK
   - POST /search → 200 OK
   - GET /taxonomy/1.8.1/tree → 200 OK

**Phase 3**: 문서화 (현재 단계)
1. SPEC 문서 작성 ✅
2. TAG 추가 제안 (다음 단계)
3. Traceability 확립

---

## 3. 변경 상세

### 3.1 health.py

**변경 전**:
```python
from deps import verify_api_key, get_current_timestamp, get_taxonomy_version
```

**변경 후**:
```python
from ..deps import verify_api_key, get_current_timestamp, get_taxonomy_version
```

**영향**: 1개 import 문, 3개 함수

---

### 3.2 classify.py

**변경 전**:
```python
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import ClassifyDAO
```

**변경 후**:
```python
from ..deps import verify_api_key, generate_request_id, get_taxonomy_version
from ..database import ClassifyDAO
```

**영향**: 2개 import 문, 3개 함수 + 1개 DAO 클래스

---

### 3.3 search.py

**변경 전**:
```python
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import SearchDAO
```

**변경 후**:
```python
from ..deps import verify_api_key, generate_request_id, get_taxonomy_version
from ..database import SearchDAO
```

**영향**: 2개 import 문, 3개 함수 + 1개 DAO 클래스

---

### 3.4 taxonomy.py

**변경 전**:
```python
from deps import verify_api_key
from database import TaxonomyDAO
```

**변경 후**:
```python
from ..deps import verify_api_key
from ..database import TaxonomyDAO
```

**영향**: 2개 import 문, 1개 함수 + 1개 DAO 클래스

---

## 4. 리스크 및 완화 전략

### 4.1 식별된 리스크

| 리스크 | 영향도 | 완화 전략 | 상태 |
|--------|--------|-----------|------|
| 기존 TAG 충돌 | 낮음 | 새로운 TAG 라인 별도 추가 | ✅ 계획됨 |
| 라우터 동작 변경 | 없음 | import만 수정, 로직 불변 | ✅ 확인됨 |
| 다른 모듈 영향 | 없음 | 라우터 파일만 수정 | ✅ 격리됨 |

### 4.2 Rollback 계획

**IF** relative import가 문제를 일으킬 경우:
1. Git revert로 이전 커밋 복원
2. 대안 방법 (sys.path 조작) 재검토

**현재 상태**: Rollback 불필요 (정상 작동 확인)

---

## 5. TAG 통합 계획 (다음 단계)

### 5.1 기존 TAG 보존

각 라우터 파일의 docstring 첫 줄:
```python
"""
Health Check 엔드포인트
@CODE:TEST-001:TAG-004 | SPEC: SPEC-TEST-001.md | TEST: tests/integration/test_api_endpoints.py
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""
```

**보존 이유**:
- 기존 통합 테스트와의 traceability 유지
- Bridge Pack 스펙 준수 증적

### 5.2 새로운 TAG 추가 제안

**추가 위치**: 각 라우터 파일 docstring의 **두 번째 줄** (기존 TAG 바로 다음)

**형식**:
```python
"""
Health Check 엔드포인트
@CODE:TEST-001:TAG-004 | SPEC: SPEC-TEST-001.md | TEST: tests/integration/test_api_endpoints.py
@CODE:ROUTER-IMPORT-FIX-001 | SPEC: SPEC-ROUTER-IMPORT-FIX-001.md
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""
```

**적용 파일**: 4개 라우터 모두 동일 패턴 적용

---

## 6. 검증 결과

### 6.1 기능 검증 ✅

**서버 시작**:
```bash
uvicorn apps.api.main:app --reload
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**엔드포인트 테스트**:
- GET /healthz → ✅ 200 OK
- POST /classify → ✅ 200 OK (with valid API key)
- POST /search → ✅ 200 OK (with valid API key)
- GET /taxonomy/1.8.1/tree → ✅ 200 OK

### 6.2 부작용 검증 ✅

- ✅ 기존 TAG 구조 유지
- ✅ 라우터 로직 변경 없음
- ✅ 응답 스키마 동일
- ✅ 의존성 주입(Depends) 정상 작동

---

## 7. 타임라인 (회고)

| 단계 | 소요 시간 | 상태 |
|------|-----------|------|
| 문제 발견 | - | ✅ |
| 원인 분석 | 5분 | ✅ |
| 해결책 적용 | 5분 | ✅ |
| 검증 | 3분 | ✅ |
| SPEC 문서화 | 진행 중 | 🔄 |

**Total**: ~15분 (문서화 제외)

---

## 8. 학습 포인트

### 8.1 기술적 학습

**Python Import 규칙**:
- Absolute import는 최상위 패키지 기준 (`from apps.api.deps import ...`)
- Relative import는 현재 패키지 기준 (`from ..deps import ...`)
- FastAPI ASGI 로더는 패키지 컨텍스트 유지가 중요

**Best Practice**:
- 동일 프로젝트 내부 모듈 → relative import 권장
- 외부 라이브러리 → absolute import 필수

### 8.2 프로세스 학습

**Retrospective SPEC의 가치**:
- 이미 완료된 작업도 문서화하여 traceability 확보
- 미래 유지보수자를 위한 컨텍스트 제공
- TAG 시스템 통합으로 변경 이력 일원화

---

## 9. 다음 단계

1. **TAG 추가**: 4개 라우터 파일에 `@CODE:ROUTER-IMPORT-FIX-001` TAG 추가
2. **Git 커밋**: 문서화 작업 커밋 (SPEC 문서 3개)
3. **TAG 검증**: `rg '@CODE:ROUTER-IMPORT-FIX-001' -n` 실행 확인

---

## 참고 자료

- Python Packaging User Guide: [Relative imports](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/)
- FastAPI Documentation: [Module structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- PEP 328: [Imports: Multi-Line and Absolute/Relative](https://www.python.org/dev/peps/pep-0328/)
