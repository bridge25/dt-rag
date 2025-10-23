---
id: IMPORT-ASYNC-FIX-001
version: 0.1.0
status: completed
created: 2025-10-23
updated: 2025-10-23
author: "@assistant"
priority: high
category: bugfix
labels: [import, async, database, pytest]
depends_on: [SPEC-ROUTER-IMPORT-FIX-001]
related_specs: [SPEC-TEST-001, SPEC-API-001]
---

# @SPEC:IMPORT-ASYNC-FIX-001: API import 경로 및 async 드라이버 수정

## HISTORY

### v0.1.0 (2025-10-23)
- **IMPLEMENTATION COMPLETED**: API import 경로 및 async 드라이버 이슈 수정 완료
- **AUTHOR**: @assistant
- **TDD CYCLE**: 수정 후 pytest 테스트 통과 확인 (GREEN)
- **PROBLEM**:
  1. main.py absolute import로 인한 ModuleNotFoundError
  2. conftest.py import 경로 불일치로 pytest 실패
  3. SQLAlchemy가 psycopg2 선택하여 async 드라이버 충돌
- **SOLUTION**:
  1. main.py를 relative import로 변경
  2. conftest.py에서 apps.api.main import 경로 수정
  3. database.py에 asyncpg 명시적 지정 로직 추가
- **FILES**:
  - apps/api/main.py
  - tests/conftest.py
  - apps/api/database.py
- **CHANGES**:
  - main.py: from routers → from .routers, from database → from .database
  - conftest.py: from main → from apps.api.main
  - database.py: asyncpg 자동 변환 로직 추가
- **TEST RESULT**: tests/integration/test_api_endpoints.py PASSED

## Environment

Python 3.12.3, pytest 8.4.2, SQLAlchemy async, PostgreSQL+asyncpg

## Requirements

### Event-driven Requirements

- WHEN API server starts, system must import all modules using relative imports
- WHEN pytest runs, system must import FastAPI app from apps.api.main
- WHEN DATABASE_URL lacks +asyncpg, system must auto-convert to postgresql+asyncpg://

## Traceability (@TAG)

- **SPEC**: @SPEC:IMPORT-ASYNC-FIX-001
- **CODE**: apps/api/main.py, tests/conftest.py, apps/api/database.py
- **TEST**: tests/integration/test_api_endpoints.py
