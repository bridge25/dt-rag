---
id: ROUTER-IMPORT-FIX-001
version: 0.1.0
status: completed
created: 2025-10-23
author: "@assistant"
tags: ["import", "router", "bugfix", "retrospective"]
---

# SPEC-ROUTER-IMPORT-FIX-001: API 라우터 Import 경로 수정

@SPEC:ROUTER-IMPORT-FIX-001 | IMPLEMENTATION: apps/api/routers/*.py | TEST: Manual verification

## HISTORY

### v0.1.0 (2025-10-23)
- **IMPLEMENTATION COMPLETED**: API 라우터 모듈 import 경로 수정 완료
- **AUTHOR**: @assistant
- **PROBLEM**: absolute import로 인한 ModuleNotFoundError 발생
  - `from deps import ...` → ModuleNotFoundError: No module named 'deps'
  - `from database import ...` → ModuleNotFoundError: No module named 'database'
- **SOLUTION**: 4개 라우터 파일의 import 문을 relative import로 변경
- **FILES**:
  - apps/api/routers/health.py
  - apps/api/routers/classify.py
  - apps/api/routers/search.py
  - apps/api/routers/taxonomy.py
- **CHANGES**:
  - `from deps import` → `from ..deps import`
  - `from database import` → `from ..database import`

---

## Environment

**WHEN** API 서버가 FastAPI 애플리케이션을 시작할 때,
**THEN** 시스템은 `apps/api/routers/` 디렉토리의 라우터 모듈을 로드한다.

**Context**:
- Python 패키지 구조: `apps/api/routers/*.py`
- 의존 모듈 위치: `apps/api/deps.py`, `apps/api/database.py`
- 실행 환경: FastAPI + Uvicorn

## Assumptions

**UBIQUITOUS**: 모든 라우터 파일은 동일한 import 패턴을 따른다.
- 모든 라우터는 `apps.api.routers` 패키지 내부에 위치
- 공통 의존성(`deps`, `database`)은 부모 패키지(`apps.api`)에 위치

**UBIQUITOUS**: Python 상대 경로 import 규칙을 준수한다.
- `..` 접두사는 부모 디렉토리를 의미
- 동일 패키지 내 모듈 간 import는 relative import를 권장

## Requirements

### ⚠️ 문제 정의

**PROBLEM**: 기존 absolute import 방식의 한계
- `from deps import verify_api_key` → `ModuleNotFoundError`
- Python이 `apps.api.deps`를 찾지 못함 (패키지 컨텍스트 누락)

### ✅ 해결 방안

**IF** 라우터 파일이 `deps` 또는 `database` 모듈을 import할 때,
**THEN** 시스템은 relative import 구문(`..deps`, `..database`)을 사용해야 한다.

**WHY**:
- FastAPI가 `apps.api.main:app` 형태로 ASGI 앱을 로드할 때 패키지 컨텍스트 유지
- Python 모듈 검색 경로(sys.path) 의존성 제거
- 패키지 재배치 시 유지보수성 향상

## Specifications

### 1. Import 문 수정 (4개 파일)

**FILE**: `apps/api/routers/health.py`
```python
# BEFORE (❌ absolute import)
from deps import verify_api_key, get_current_timestamp, get_taxonomy_version

# AFTER (✅ relative import)
from ..deps import verify_api_key, get_current_timestamp, get_taxonomy_version
```

**FILE**: `apps/api/routers/classify.py`
```python
# BEFORE (❌ absolute import)
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import ClassifyDAO

# AFTER (✅ relative import)
from ..deps import verify_api_key, generate_request_id, get_taxonomy_version
from ..database import ClassifyDAO
```

**FILE**: `apps/api/routers/search.py`
```python
# BEFORE (❌ absolute import)
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import SearchDAO

# AFTER (✅ relative import)
from ..deps import verify_api_key, generate_request_id, get_taxonomy_version
from ..database import SearchDAO
```

**FILE**: `apps/api/routers/taxonomy.py`
```python
# BEFORE (❌ absolute import)
from deps import verify_api_key
from database import TaxonomyDAO

# AFTER (✅ relative import)
from ..deps import verify_api_key
from ..database import TaxonomyDAO
```

### 2. 검증 기준

**IF** FastAPI 서버가 정상적으로 시작되고,
**THEN** 모든 라우터 엔드포인트가 정상 작동해야 한다.

**Verification**:
- `uvicorn apps.api.main:app --reload` 실행 시 ModuleNotFoundError 미발생
- 4개 라우터의 모든 엔드포인트 정상 응답
  - GET /healthz → 200 OK
  - POST /classify → 200 OK (with valid request)
  - POST /search → 200 OK (with valid request)
  - GET /taxonomy/1.8.1/tree → 200 OK

### 3. 부작용 방지

**CONSTRAINT**: 기존 TAG 구조 유지
- 기존 `@CODE:TEST-001:TAG-00X` TAG는 그대로 유지
- 새로운 `@CODE:ROUTER-IMPORT-FIX-001` TAG 추가 (별도 라인)

**CONSTRAINT**: 라우터 로직 변경 없음
- import 문만 수정, 비즈니스 로직은 불변
- 함수 시그니처, 반환값, 동작 모두 동일

## Traceability

### Related Files
- **Implementation**:
  - `apps/api/routers/health.py`
  - `apps/api/routers/classify.py`
  - `apps/api/routers/search.py`
  - `apps/api/routers/taxonomy.py`
- **Dependencies**:
  - `apps/api/deps.py`
  - `apps/api/database.py`
- **SPEC**: `.moai/specs/SPEC-ROUTER-IMPORT-FIX-001/spec.md`
- **Plan**: `.moai/specs/SPEC-ROUTER-IMPORT-FIX-001/plan.md`
- **Acceptance**: `.moai/specs/SPEC-ROUTER-IMPORT-FIX-001/acceptance.md`

### TAG Chain
- `@SPEC:ROUTER-IMPORT-FIX-001` (this document)
- `@CODE:ROUTER-IMPORT-FIX-001` (router docstrings에 추가 예정)

### Related SPECs
- `SPEC-TEST-001`: API 엔드포인트 통합 테스트 (기존 TAG 보존)
- `SPEC-API-001`: API 전체 구조 설계

## Notes

**Retrospective Documentation**: 이 SPEC은 이미 구현 완료된 작업에 대한 회고적(retrospective) 문서입니다.

**Purpose**:
- Traceability 확보 (변경 이유와 방법 명확화)
- 향후 유사한 import 이슈 발생 시 참고 자료
- TAG 시스템 통합을 통한 변경 이력 추적

**Implementation Status**: ✅ 완료 (2025-10-23)
