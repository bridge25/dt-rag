---
id: CICD-001
title: CI/CD Import 검증 자동화
version: 0.0.1
status: draft
created: 2025-01-24
domain: CICD
priority: high
---

# SPEC-CICD-001: CI/CD Import 검증 자동화

**@SPEC:CICD-001**

## HISTORY

### v0.0.1 (2025-01-24)
- **INITIAL**: CI/CD Import 검증 자동화 SPEC 초안 작성
- Python import 오류 회귀 방지를 위한 3단계 검증 시스템 설계
- compileall + Alembic CLI + pytest 기반 검증 전략 수립

---

## 1. Overview

### 1.1 Purpose
Python import 오류가 프로덕션 배포 이후 발견되는 회귀를 방지하기 위해 CI/CD 파이프라인에서 자동화된 import 검증 시스템을 구축한다.

### 1.2 Background
- **문제**: `apps/api/routers/search.py`에서 `QueryProcessor` import 오류가 배포 후 발견됨
- **영향**: API 서버 시작 실패, 프로덕션 장애
- **원인**: 로컬 테스트에서 누락된 import 검증
- **해결 방향**: 3단계 자동 검증 (CI/CD → Pre-commit → Local Test)

### 1.3 Scope
- **Phase 1 (P0)**: GitHub Actions Workflow - CI/CD 파이프라인 통합
- **Phase 2 (P1)**: Pre-commit Hook - 커밋 전 자동 검증
- **Phase 3 (P2)**: Pytest Fixture - 로컬 테스트 환경 검증

### 1.4 Dependencies
- Python 3.11+
- compileall (Python 표준 라이브러리)
- Alembic 1.16.4
- pytest 8.4.2
- pre-commit 4.0+ (신규 설치)

---

## 2. EARS Requirements

### 2.1 Event-driven Requirements

**E1: GitHub Push Event**
- **WHEN** 개발자가 `master` 또는 feature 브랜치에 코드를 push할 때
- **THEN** GitHub Actions workflow가 자동으로 트리거되어 import 검증을 실행해야 한다
- **ACCEPTANCE**: workflow 실행 로그에서 "Import validation passed" 확인

**E2: Git Commit Event**
- **WHEN** 개발자가 `git commit` 명령을 실행할 때
- **THEN** pre-commit hook이 자동으로 실행되어 import 검증을 수행해야 한다
- **ACCEPTANCE**: commit 실패 시 명확한 오류 메시지 출력

**E3: Pytest Execution Event**
- **WHEN** 개발자가 `pytest` 명령을 실행할 때
- **THEN** session-scoped fixture가 모든 테스트 실행 전 import 검증을 수행해야 한다
- **ACCEPTANCE**: import 오류 발견 시 테스트 스위트 실행 중단

### 2.2 Action-driven Requirements

**A1: Syntax Validation**
- **IF** Python 파일이 컴파일 가능한 상태인지 검증이 필요하다면
- **THEN** `python -m compileall` 명령을 사용하여 전체 코드베이스를 컴파일해야 한다
- **CONSTRAINTS**:
  - 검증 대상: `apps/`, `tests/` 디렉토리
  - 타임아웃: 30초 이내

**A2: Alembic Migration Validation**
- **IF** 데이터베이스 마이그레이션 스크립트의 import가 유효한지 검증이 필요하다면
- **THEN** `alembic upgrade head --sql` 명령을 dry-run 모드로 실행해야 한다
- **CONSTRAINTS**:
  - 실제 DB 변경 없이 SQL만 생성
  - 실행 시간: 10초 이내

**A3: API Server Import Validation**
- **IF** FastAPI 애플리케이션의 모든 import가 유효한지 검증이 필요하다면
- **THEN** `python -c "from apps.api.main import app"` 명령을 실행해야 한다
- **CONSTRAINTS**:
  - 서버 시작 없이 import만 수행
  - 실행 시간: 5초 이내

### 2.3 Response Requirements

**R1: CI/CD Failure Response**
- **IF** GitHub Actions에서 import 오류가 발견되면
- **THEN** workflow는 즉시 실패하고 다음 정보를 포함한 오류 보고서를 생성해야 한다:
  - 실패한 검증 단계 (compileall/alembic/api)
  - 구체적인 오류 메시지
  - 영향받는 파일 경로
- **ACCEPTANCE**: PR 상태가 "failed"로 표시되고 merge 차단

**R2: Pre-commit Failure Response**
- **IF** pre-commit hook에서 import 오류가 발견되면
- **THEN** commit이 중단되고 다음 안내 메시지를 출력해야 한다:
  - 오류 위치 및 원인
  - 수정 방법 제안
  - 재시도 명령어
- **ACCEPTANCE**: commit 실패 + 명확한 오류 가이드

**R3: Pytest Failure Response**
- **IF** pytest fixture에서 import 오류가 발견되면
- **THEN** 테스트 스위트 실행이 중단되고 다음 정보를 출력해야 한다:
  - 검증 실패 이유
  - 영향받는 모듈 목록
  - 로컬 수정 가이드
- **ACCEPTANCE**: 테스트 실행 중단 + exit code 1

### 2.4 State Requirements

**S1: CI/CD Workflow State**
- **WHILE** GitHub Actions workflow가 실행 중일 때
- **THEN** 다음 단계가 순차적으로 실행되어야 한다:
  1. Checkout 코드
  2. Python 환경 설정
  3. 의존성 설치
  4. Import 검증 (compileall → alembic → api)
  5. 결과 리포팅
- **ACCEPTANCE**: 각 단계의 로그가 GitHub Actions UI에 표시됨

**S2: Pre-commit Hook State**
- **WHILE** pre-commit hook이 활성화된 상태일 때
- **THEN** 모든 commit 시도에서 import 검증이 자동으로 실행되어야 한다
- **CONSTRAINTS**:
  - hook 실행 시간: 15초 이내
  - bypass 옵션: `--no-verify` 플래그로 긴급 우회 가능
- **ACCEPTANCE**: `.git/hooks/pre-commit` 파일 존재 확인

**S3: Pytest Session State**
- **WHILE** pytest 세션이 초기화 중일 때
- **THEN** `validate_imports` fixture가 먼저 실행되어 import 검증을 완료해야 한다
- **CONSTRAINTS**:
  - scope: session (테스트 스위트당 1회 실행)
  - autouse: True (모든 테스트에 자동 적용)
- **ACCEPTANCE**: pytest verbose 출력에서 fixture 실행 확인

---

## 3. Technical Specifications

### 3.1 Phase 1: GitHub Actions Workflow

**파일 경로**: `.github/workflows/import-validation.yml`

```yaml
name: Import Validation

on:
  push:
    branches: [master, 'feature/**']
  pull_request:
    branches: [master]

jobs:
  validate-imports:
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Validate Python syntax
        run: |
          python -m compileall -q apps/ tests/

      - name: Validate Alembic migrations
        run: |
          alembic upgrade head --sql > /dev/null

      - name: Validate API imports
        run: |
          python -c "from apps.api.main import app; print('✓ API imports validated')"
```

### 3.2 Phase 2: Pre-commit Hook

**설치 파일**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-imports
        name: Validate Python Imports
        entry: bash -c 'python -m compileall -q apps/ tests/ && python -c "from apps.api.main import app"'
        language: system
        pass_filenames: false
        always_run: true
```

**설치 명령**:
```bash
pip install pre-commit
pre-commit install
```

### 3.3 Phase 3: Pytest Fixture

**파일 경로**: `tests/conftest.py`

```python
import subprocess
import sys
import pytest

@pytest.fixture(scope="session", autouse=True)
def validate_imports():
    """
    @TEST:CICD-001
    모든 테스트 실행 전 Python import 검증을 수행한다.

    검증 항목:
    1. compileall - 전체 코드베이스 컴파일 가능 여부
    2. API import - FastAPI 애플리케이션 import 가능 여부

    실패 시 테스트 스위트 실행을 중단한다.
    """
    print("\n🔍 Validating imports before test execution...")

    # Step 1: compileall 검증
    result = subprocess.run(
        ["python", "-m", "compileall", "-q", "apps/", "tests/"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(
            f"❌ Import validation failed (compileall):\n{result.stderr}",
            pytrace=False
        )

    # Step 2: API import 검증
    try:
        from apps.api.main import app
        print("✓ API imports validated")
    except ImportError as e:
        pytest.fail(
            f"❌ Import validation failed (API):\n{str(e)}",
            pytrace=False
        )

    print("✓ All imports validated successfully\n")
```

---

## 4. Constraints

### 4.1 Performance Constraints
- **P1**: 각 검증 단계는 30초 이내에 완료되어야 함
- **P2**: 전체 CI/CD workflow는 5분 이내에 완료되어야 함
- **P3**: Pre-commit hook은 15초 이내에 완료되어야 함

### 4.2 Reliability Constraints
- **R1**: False positive rate < 1% (정상 코드를 오류로 판단하는 비율)
- **R2**: False negative rate = 0% (import 오류를 놓치는 경우 없음)
- **R3**: 네트워크 장애 시에도 로컬 검증은 정상 작동해야 함

### 4.3 Compatibility Constraints
- **C1**: Python 3.11+ 지원
- **C2**: Linux/macOS/Windows 모두 지원
- **C3**: 기존 pytest 설정과 충돌하지 않아야 함

### 4.4 Security Constraints
- **S1**: 검증 과정에서 실제 DB 변경 금지 (dry-run only)
- **S2**: 민감 정보(API key, password) 로그 출력 금지
- **S3**: CI/CD secrets는 GitHub Secrets 사용

---

## 5. Traceability

### 5.1 Related TAGs
- **@CODE:CICD-001**: GitHub Actions workflow 구현
- **@CODE:CICD-001:HOOK**: Pre-commit hook 설정
- **@CODE:CICD-001:TEST**: Pytest fixture 구현
- **@TEST:CICD-001**: Import 검증 테스트

### 5.2 Related Documents
- `docs/troubleshooting.md`: 회귀 방지 전략
- `.moai/specs/SPEC-CICD-001/plan.md`: 구현 계획
- `.moai/specs/SPEC-CICD-001/acceptance.md`: 인수 기준

### 5.3 Related Issues
- GitHub Issue: [SPEC-CICD-001] CI/CD Import 검증 자동화
- PR: feature/SPEC-CICD-001 브랜치

---

## 6. Success Criteria

### 6.1 Functional Success
- ✅ GitHub Actions에서 import 오류 자동 감지
- ✅ Pre-commit hook에서 commit 전 검증
- ✅ Pytest에서 테스트 실행 전 검증
- ✅ 3단계 모두에서 동일한 검증 기준 적용

### 6.2 Non-functional Success
- ✅ CI/CD 실행 시간 < 5분
- ✅ Pre-commit 실행 시간 < 15초
- ✅ 명확한 오류 메시지 및 수정 가이드 제공

### 6.3 Verification Methods
- Manual: 고의로 import 오류를 삽입하여 3단계 모두에서 감지되는지 확인
- Automated: 정상 코드에서 3단계 모두 통과하는지 확인
- Regression: 실제 발생했던 `QueryProcessor` import 오류 재현 후 감지 확인

---

## 7. Assumptions

1. Python 3.11 환경이 CI/CD 및 로컬 개발 환경에 설정되어 있다
2. GitHub Actions runner가 Docker 기반 컨테이너를 사용한다
3. 개발자는 pre-commit을 설치하고 활성화할 의향이 있다
4. Alembic migration 파일은 `alembic/versions/` 디렉토리에 위치한다
5. FastAPI 애플리케이션 entry point는 `apps.api.main:app`이다

---

## 8. Open Questions

1. **Q1**: Pre-commit hook이 실패할 경우 긴급 배포 시 우회 프로세스가 필요한가?
   - **Option A**: `--no-verify` 플래그 허용 + 사후 리뷰
   - **Option B**: 우회 불가, 반드시 수정 후 commit

2. **Q2**: Import 검증 실패 시 Slack/이메일 알림이 필요한가?
   - **Option A**: GitHub Actions 기본 알림만 사용
   - **Option B**: 추가 알림 채널 설정

3. **Q3**: Phase 2, 3 구현 우선순위를 조정할 필요가 있는가?
   - **Current**: P0(CI/CD) → P1(Pre-commit) → P2(Pytest)
   - **Alternative**: P0(CI/CD) → P2(Pytest) → P1(Pre-commit)

---

**문서 작성자**: spec-builder agent
**최종 수정일**: 2025-01-24
**다음 단계**: `/alfred:2-run SPEC-CICD-001` 실행하여 Phase 1 구현 시작
