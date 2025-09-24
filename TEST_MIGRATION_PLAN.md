# 기존 테스트 파일들 마이그레이션 계획

## 현재 상태 분석

### 기존 테스트 파일들
1. `tests/security/test_api_key_validation.py` - API 키 검증 테스트
2. `tests/test_db_integration.py` - 데이터베이스 통합 테스트
3. `.claude/hooks/test_python_hook.py` - Claude 후크 테스트 (제외)

## 마이그레이션 계획

### 1. tests/security/test_api_key_validation.py
- **현재 위치**: `tests/security/test_api_key_validation.py`
- **유지 여부**: ✅ 현재 위치 유지
- **이유**: 이미 적절한 security 하위 디렉토리에 위치
- **분류**: Integration Test (API와 보안 시스템의 통합)
- **추가 작업**:
  - `@pytest.mark.integration` 마커 추가 권장
  - `@pytest.mark.security` 마커 추가 권장

### 2. tests/test_db_integration.py
- **현재 위치**: `tests/test_db_integration.py`
- **이동 예정**: `tests/integration/test_database.py`
- **이유**: 데이터베이스 통합 테스트이므로 integration 디렉토리가 적합
- **분류**: Integration Test
- **추가 작업**:
  - `@pytest.mark.integration` 마커 추가
  - `@pytest.mark.slow` 마커 추가 (DB 테스트는 일반적으로 느림)

### 3. .claude/hooks/test_python_hook.py
- **현재 위치**: `.claude/hooks/test_python_hook.py`
- **이동 여부**: ❌ 이동하지 않음
- **이유**: Claude Code 관련 도구 테스트로 프로젝트 테스트 스위트와 별개

## 새로운 테스트 구조

```
dt-rag/tests/
├── __init__.py
├── conftest.py                 # 공통 fixtures 및 설정
├── unit/                       # 단위 테스트
│   ├── __init__.py
│   ├── api/                    # API 컴포넌트 단위 테스트
│   ├── agent_system/           # 에이전트 시스템 단위 테스트
│   └── utils/                  # 유틸리티 함수 단위 테스트
├── integration/                # 통합 테스트
│   ├── __init__.py
│   ├── test_database.py        # DB 통합 테스트 (이동됨)
│   ├── test_api_endpoints.py   # API 엔드포인트 통합 테스트
│   └── test_agent_workflows.py # 에이전트 워크플로우 통합 테스트
├── e2e/                        # E2E 테스트
│   ├── __init__.py
│   ├── test_search_workflow.py # 전체 검색 워크플로우
│   └── test_agent_orchestration.py # 전체 에이전트 오케스트레이션
├── security/                   # 보안 테스트 (기존 유지)
│   ├── test_api_key_validation.py # 기존 파일 유지
│   └── test_authentication.py  # 추가 보안 테스트
└── evaluation/                 # 성능 평가 테스트 (기존 유지)
    └── performance_tests.py
```

## 마이그레이션 실행 단계

### Phase 1: 즉시 실행 가능
1. ✅ pytest.ini 생성 완료
2. ✅ pyproject.toml 생성 완료
3. ✅ 새로운 디렉토리 구조 생성 완료
4. ✅ conftest.py 생성 완료
5. ✅ __init__.py 파일들 생성 완료

### Phase 2: 기존 파일 마이그레이션 (권장)
1. `tests/test_db_integration.py` → `tests/integration/test_database.py`
2. 테스트 마커 추가
3. 기존 파일 정리

### Phase 3: 새로운 테스트 작성 (향후)
1. 단위 테스트 작성 (`tests/unit/`)
2. E2E 테스트 작성 (`tests/e2e/`)
3. 추가 통합 테스트 작성

## 마이그레이션 스크립트

```bash
# Phase 2 실행 스크립트
#!/bin/bash

# 1. 데이터베이스 통합 테스트 이동
mv tests/test_db_integration.py tests/integration/test_database.py

# 2. Git으로 변경사항 추적
git add tests/integration/test_database.py
git rm tests/test_db_integration.py
```

## 테스트 실행 명령어

```bash
# 전체 테스트 실행
pytest

# 카테고리별 테스트 실행
pytest tests/unit/          # 단위 테스트만
pytest tests/integration/   # 통합 테스트만
pytest tests/e2e/          # E2E 테스트만

# 마커별 테스트 실행
pytest -m unit              # 단위 테스트 마커
pytest -m integration       # 통합 테스트 마커
pytest -m "not slow"        # 느린 테스트 제외

# 커버리지 포함
pytest --cov=apps --cov-report=html
```

## 주의사항

1. **기존 테스트 파일 백업**: 이동 전에 백업 생성 권장
2. **Import 경로 수정**: 파일 이동 시 import 경로 확인 필요
3. **CI/CD 파이프라인 업데이트**: 테스트 경로 변경 시 CI 설정 확인
4. **문서 업데이트**: README 및 개발 가이드에 새로운 테스트 구조 반영

## 완료 체크리스트

- [x] pytest.ini 생성
- [x] pyproject.toml 생성
- [x] 테스트 디렉토리 구조 생성
- [x] conftest.py 생성
- [x] __init__.py 파일들 생성
- [x] 마이그레이션 계획 수립
- [ ] 기존 파일 이동 (선택사항)
- [ ] 테스트 마커 추가 (선택사항)
- [ ] 새로운 테스트 작성 (향후)