# SPEC-CICD-001 Implementation Plan

**@PLAN:CICD-001**

---

## 1. Executive Summary

### 1.1 Objective
CI/CD 파이프라인에 Python import 검증 자동화 시스템을 구축하여 프로덕션 배포 전 import 오류를 사전 차단한다.

### 1.2 Scope Summary
- **Phase 1 (P0)**: GitHub Actions Workflow - CI/CD 통합 (필수)
- **Phase 2 (P1)**: Pre-commit Hook - 커밋 전 검증 (권장)
- **Phase 3 (P2)**: Pytest Fixture - 로컬 테스트 검증 (선택)

### 1.3 Success Metrics
- ✅ GitHub Actions에서 import 오류 100% 감지
- ✅ CI/CD 실행 시간 < 5분
- ✅ False negative rate = 0%
- ✅ 3단계 모두 동일한 검증 기준 적용

---

## 2. Phase Breakdown

### Phase 1: GitHub Actions Workflow (P0) - **MUST**

**Priority**: High (회귀 방지 필수)

**Objective**: CI/CD 파이프라인에서 모든 push/PR에 대해 자동 import 검증 수행

**Deliverables**:
1. `.github/workflows/import-validation.yml` 생성
2. 3단계 검증 로직 구현 (compileall → alembic → api)
3. 실패 시 PR merge 차단
4. 명확한 오류 리포팅

**Technical Approach**:

```yaml
# .github/workflows/import-validation.yml

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
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Validate Python syntax
        run: |
          echo "🔍 Step 1: Validating Python syntax..."
          python -m compileall -q apps/ tests/
          echo "✓ Syntax validation passed"

      - name: Validate Alembic migrations
        run: |
          echo "🔍 Step 2: Validating Alembic migrations..."
          alembic upgrade head --sql > /dev/null
          echo "✓ Alembic validation passed"

      - name: Validate API imports
        run: |
          echo "🔍 Step 3: Validating API imports..."
          python -c "from apps.api.main import app; print('✓ API imports validated')"

      - name: Report success
        if: success()
        run: |
          echo "✅ All import validations passed successfully"

      - name: Report failure
        if: failure()
        run: |
          echo "❌ Import validation failed. Please check the logs above."
          exit 1
```

**Implementation Steps**:

1. **Create workflow file**
   - Path: `.github/workflows/import-validation.yml`
   - Trigger: push to `master` or `feature/**`, PR to `master`
   - Timeout: 5 minutes

2. **Setup environment**
   - Python 3.11
   - pip cache 활성화
   - requirements.txt 설치

3. **Implement validation steps**
   - Step 1: `python -m compileall` - 구문 검증
   - Step 2: `alembic upgrade head --sql` - 마이그레이션 검증
   - Step 3: `python -c "from apps.api.main import app"` - API import 검증

4. **Configure failure handling**
   - 각 단계 실패 시 즉시 workflow 중단
   - 실패 원인 명확히 표시
   - PR merge 자동 차단

**Testing Strategy**:
- **Positive Test**: 정상 코드에서 workflow 통과 확인
- **Negative Test**: 고의로 import 오류 삽입 후 감지 확인
- **Regression Test**: `QueryProcessor` import 오류 재현 후 감지 확인

**Dependencies**:
- GitHub Actions 활성화
- requirements.txt 최신 상태 유지
- Python 3.11 환경

**Risks & Mitigation**:
- **Risk 1**: CI/CD 실행 시간 증가
  - **Mitigation**: pip cache 활용, timeout 5분 설정
- **Risk 2**: 네트워크 장애로 인한 의존성 설치 실패
  - **Mitigation**: setup-python cache 옵션 활용
- **Risk 3**: Alembic 검증 시 DB 연결 필요
  - **Mitigation**: `--sql` 옵션으로 dry-run만 수행

**Acceptance Criteria**:
- ✅ GitHub Actions UI에서 "Import Validation" job 확인
- ✅ 정상 코드에서 모든 단계 통과
- ✅ import 오류 시 PR merge 차단
- ✅ 실행 시간 < 5분

---

### Phase 2: Pre-commit Hook (P1) - **SHOULD**

**Priority**: Medium (개발자 경험 개선)

**Objective**: commit 전 로컬에서 import 검증을 수행하여 CI/CD 실패 횟수 감소

**Deliverables**:
1. `.pre-commit-config.yaml` 생성
2. pre-commit 설치 가이드 추가
3. 검증 실패 시 명확한 오류 메시지
4. 긴급 우회 옵션 (`--no-verify`) 문서화

**Technical Approach**:

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: validate-python-imports
        name: Validate Python Imports
        entry: bash -c 'python -m compileall -q apps/ tests/ && python -c "from apps.api.main import app"'
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
```

**Installation Commands**:

```bash
# 1. Install pre-commit
pip install pre-commit

# 2. Install hooks
pre-commit install

# 3. (Optional) Run manually
pre-commit run --all-files

# 4. Bypass hook if needed
git commit --no-verify -m "Emergency fix"
```

**Implementation Steps**:

1. **Create configuration file**
   - Path: `.pre-commit-config.yaml`
   - Hook type: local (no remote dependency)
   - Execution: always run on commit

2. **Define validation logic**
   - Use same validation as GitHub Actions
   - Run compileall + API import check
   - Timeout: 15 seconds

3. **Setup hook installation**
   - Add installation guide to README
   - Provide troubleshooting tips
   - Document bypass option for emergencies

4. **Test hook behavior**
   - Test normal commit flow
   - Test failure scenarios
   - Verify bypass option works

**Testing Strategy**:
- **Positive Test**: 정상 코드에서 commit 성공
- **Negative Test**: import 오류 시 commit 차단
- **Bypass Test**: `--no-verify` 옵션으로 우회 가능 확인

**Dependencies**:
- pre-commit 패키지 설치
- Git hooks 디렉토리 쓰기 권한
- Python 환경 활성화

**Risks & Mitigation**:
- **Risk 1**: 개발자가 pre-commit 설치를 생략할 수 있음
  - **Mitigation**: CI/CD에서 무조건 검증하므로 영향 최소화
- **Risk 2**: pre-commit 실행 시간이 길어질 수 있음
  - **Mitigation**: compileall `-q` 옵션으로 출력 최소화
- **Risk 3**: Windows 환경에서 bash 명령 실행 실패
  - **Mitigation**: `language: system` 사용, Python 스크립트로 변경 가능

**Acceptance Criteria**:
- ✅ `.pre-commit-config.yaml` 파일 존재
- ✅ `pre-commit install` 명령 성공
- ✅ import 오류 시 commit 차단
- ✅ 실행 시간 < 15초

---

### Phase 3: Pytest Fixture (P2) - **COULD**

**Priority**: Low (추가 안전망)

**Objective**: pytest 실행 시 자동으로 import 검증을 수행하여 로컬 테스트 신뢰성 향상

**Deliverables**:
1. `tests/conftest.py`에 `validate_imports` fixture 추가
2. Session-scoped, autouse fixture로 구현
3. 검증 실패 시 테스트 스위트 중단
4. 명확한 실패 메시지 출력

**Technical Approach**:

```python
# tests/conftest.py

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
    print("\n" + "="*60)
    print("🔍 Pre-test Import Validation")
    print("="*60)

    # Step 1: compileall 검증
    print("\n[1/2] Validating Python syntax (compileall)...")
    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "apps/", "tests/"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        error_msg = (
            f"\n{'='*60}\n"
            f"❌ Import Validation Failed: Python Syntax Error\n"
            f"{'='*60}\n"
            f"{result.stderr}\n"
            f"{'='*60}\n"
            f"Fix the syntax errors above before running tests.\n"
        )
        pytest.fail(error_msg, pytrace=False)

    print("   ✓ Python syntax validated")

    # Step 2: API import 검증
    print("\n[2/2] Validating API imports...")
    try:
        from apps.api.main import app
        print("   ✓ API imports validated")
    except ImportError as e:
        error_msg = (
            f"\n{'='*60}\n"
            f"❌ Import Validation Failed: API Import Error\n"
            f"{'='*60}\n"
            f"{str(e)}\n"
            f"{'='*60}\n"
            f"Fix the import errors above before running tests.\n"
        )
        pytest.fail(error_msg, pytrace=False)

    print("\n" + "="*60)
    print("✅ All imports validated successfully")
    print("="*60 + "\n")
```

**Implementation Steps**:

1. **Add fixture to conftest.py**
   - Scope: session (테스트 스위트당 1회 실행)
   - Autouse: True (모든 테스트에 자동 적용)
   - TAG: `@TEST:CICD-001`

2. **Implement validation logic**
   - Use subprocess to run compileall
   - Import API app directly
   - Format error messages clearly

3. **Configure failure handling**
   - Use `pytest.fail()` to stop test execution
   - Set `pytrace=False` to hide irrelevant traceback
   - Provide actionable error messages

4. **Test fixture behavior**
   - Run pytest with normal code
   - Inject import error and verify failure
   - Check execution time

**Testing Strategy**:
- **Positive Test**: 정상 코드에서 fixture 통과 후 테스트 실행
- **Negative Test**: import 오류 시 fixture 실패, 테스트 중단
- **Performance Test**: fixture 실행 시간 < 5초

**Dependencies**:
- pytest 8.4.2+
- subprocess 모듈
- tests/conftest.py 파일

**Risks & Mitigation**:
- **Risk 1**: fixture 실행 시간이 테스트 시작 시간을 증가시킴
  - **Mitigation**: session scope로 1회만 실행
- **Risk 2**: 다른 fixture와 실행 순서 충돌
  - **Mitigation**: autouse=True로 명시적 우선순위 설정
- **Risk 3**: Docker 환경에서 subprocess 실행 제한
  - **Mitigation**: Python 표준 라이브러리만 사용

**Acceptance Criteria**:
- ✅ `tests/conftest.py`에 `validate_imports` fixture 존재
- ✅ `pytest -v` 출력에서 fixture 실행 확인
- ✅ import 오류 시 테스트 스위트 중단
- ✅ 실행 시간 < 5초

---

## 3. Implementation Order

### 3.1 Recommended Sequence

**Week 1: Phase 1 (P0) - CI/CD Workflow**
- Day 1-2: Workflow 파일 작성 및 기본 구조 구현
- Day 3: 3단계 검증 로직 구현 (compileall → alembic → api)
- Day 4: 실패 처리 및 리포팅 개선
- Day 5: 테스트 및 문서화

**Week 2: Phase 2 (P1) - Pre-commit Hook**
- Day 1: `.pre-commit-config.yaml` 작성
- Day 2: 설치 가이드 및 테스트
- Day 3: 팀원 교육 및 피드백 수집

**Week 3: Phase 3 (P2) - Pytest Fixture** (Optional)
- Day 1: `conftest.py`에 fixture 추가
- Day 2: 테스트 및 문서화
- Day 3: 성능 최적화

### 3.2 Alternative Sequence (Fast Track)

**Week 1: Phase 1 + Phase 3**
- Day 1-3: CI/CD Workflow 구현
- Day 4-5: Pytest Fixture 구현

**Week 2: Phase 2**
- Day 1-2: Pre-commit Hook 구현
- Day 3: 통합 테스트 및 문서화

**Rationale**: Phase 3 (Pytest)이 Phase 2 (Pre-commit)보다 구현이 간단하고, 로컬 테스트 신뢰성 향상 효과가 즉시 나타남

---

## 4. Architecture Design

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Developer Workflow                    │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│  Local Test   │   │ Git Commit   │   │  Git Push    │
│  (pytest)     │   │ (pre-commit) │   │  (GitHub)    │
└───────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│  Phase 3      │   │  Phase 2     │   │  Phase 1     │
│  Pytest       │   │  Pre-commit  │   │  GitHub      │
│  Fixture      │   │  Hook        │   │  Actions     │
└───────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Import Validation    │
                │  ─────────────────    │
                │  1. compileall        │
                │  2. alembic (dry-run) │
                │  3. API import        │
                └───────────────────────┘
```

### 4.2 Validation Flow

```
┌──────────────────────────────────────────────────────────┐
│                  Import Validation Flow                  │
└──────────────────────────────────────────────────────────┘

    [Start]
       │
       ▼
┌─────────────┐
│  Step 1:    │  python -m compileall -q apps/ tests/
│  Syntax     │  ───────────────────────────────────────►
│  Check      │  ✓ Pass: Continue
└─────────────┘  ✗ Fail: Exit with error
       │
       ▼
┌─────────────┐
│  Step 2:    │  alembic upgrade head --sql
│  Alembic    │  ───────────────────────────────────────►
│  Migration  │  ✓ Pass: Continue
└─────────────┘  ✗ Fail: Exit with error
       │
       ▼
┌─────────────┐
│  Step 3:    │  python -c "from apps.api.main import app"
│  API Import │  ───────────────────────────────────────►
│  Check      │  ✓ Pass: Success
└─────────────┘  ✗ Fail: Exit with error
       │
       ▼
    [End]
```

---

## 5. Technology Stack

### 5.1 Core Technologies
- **Python**: 3.11+
- **compileall**: Python 표준 라이브러리 (구문 검증)
- **Alembic**: 1.16.4 (마이그레이션 검증)
- **pytest**: 8.4.2 (테스트 프레임워크)
- **pre-commit**: 4.0+ (Git hook 관리)

### 5.2 CI/CD Tools
- **GitHub Actions**: Workflow 자동화
- **setup-python**: Python 환경 설정
- **pip cache**: 의존성 캐싱

### 5.3 Supporting Libraries
- **subprocess**: Python 표준 라이브러리 (외부 명령 실행)
- **sys**: Python 표준 라이브러리 (인터프리터 정보)

---

## 6. Testing Strategy

### 6.1 Unit Testing
- **Target**: 각 검증 단계 개별 테스트
- **Tools**: pytest
- **Coverage**: 95%+

### 6.2 Integration Testing
- **Target**: 3단계 검증 플로우 전체 테스트
- **Scenarios**:
  1. 정상 코드 → 모든 단계 통과
  2. Syntax error → Step 1 실패
  3. Alembic error → Step 2 실패
  4. Import error → Step 3 실패

### 6.3 Regression Testing
- **Target**: 과거 발생한 import 오류 재현
- **Cases**:
  1. `QueryProcessor` import 오류 (실제 발생 사례)
  2. Circular import 감지
  3. Missing dependency 감지

### 6.4 Performance Testing
- **Target**: 각 검증 단계 실행 시간
- **Acceptance**:
  - compileall: < 10초
  - alembic: < 10초
  - API import: < 5초
  - Total: < 30초

---

## 7. Risk Management

### 7.1 Identified Risks

**Risk 1: CI/CD 실행 시간 증가**
- **Impact**: High
- **Probability**: Medium
- **Mitigation**: pip cache 활용, timeout 설정, 병렬 실행 고려
- **Contingency**: 검증 단계 최적화 또는 선택적 실행

**Risk 2: Pre-commit 설치율 저조**
- **Impact**: Low
- **Probability**: High
- **Mitigation**: CI/CD 검증 필수화, 설치 가이드 제공
- **Contingency**: Phase 1 (CI/CD)만으로도 목표 달성 가능

**Risk 3: False positive (정상 코드 오류 판정)**
- **Impact**: High
- **Probability**: Low
- **Mitigation**: compileall `-q` 옵션, 충분한 테스트
- **Contingency**: 검증 로직 개선, 예외 규칙 추가

**Risk 4: 네트워크 장애로 인한 의존성 설치 실패**
- **Impact**: Medium
- **Probability**: Low
- **Mitigation**: setup-python cache 옵션, requirements.txt 최신 유지
- **Contingency**: GitHub Actions retry 설정

---

## 8. Documentation Requirements

### 8.1 User Documentation
- **README.md**: Pre-commit 설치 가이드 추가
- **CONTRIBUTING.md**: Import 검증 정책 명시
- **docs/troubleshooting.md**: 검증 실패 해결 방법

### 8.2 Developer Documentation
- **Inline Comments**: 각 검증 단계 설명
- **SPEC-CICD-001/spec.md**: 상세 요구사항
- **SPEC-CICD-001/plan.md**: 구현 계획 (현재 문서)
- **SPEC-CICD-001/acceptance.md**: 인수 기준

### 8.3 Operational Documentation
- **Runbook**: CI/CD 실패 대응 절차
- **Monitoring**: GitHub Actions 실행 로그 분석 방법

---

## 9. Success Metrics

### 9.1 Quantitative Metrics
- **Import 오류 감지율**: 100% (false negative = 0)
- **CI/CD 실행 시간**: < 5분
- **Pre-commit 실행 시간**: < 15초
- **False positive rate**: < 1%

### 9.2 Qualitative Metrics
- **개발자 만족도**: Pre-commit 유용성 평가
- **프로덕션 안정성**: Import 오류로 인한 장애 0건
- **코드 품질**: Import 관련 기술 부채 감소

### 9.3 Verification Methods
- **Manual Testing**: 고의로 오류 삽입 후 감지 확인
- **Automated Testing**: pytest로 검증 로직 테스트
- **Regression Testing**: 과거 사례 재현 후 감지 확인
- **User Feedback**: 팀원 인터뷰 및 설문조사

---

## 10. Next Steps

### 10.1 Immediate Actions
1. ✅ SPEC 문서 리뷰 및 승인
2. 🔲 `/alfred:2-run SPEC-CICD-001` 실행하여 Phase 1 구현 시작
3. 🔲 GitHub Actions workflow 파일 작성
4. 🔲 기본 검증 로직 구현 (compileall → alembic → api)

### 10.2 Follow-up Actions
1. 🔲 Phase 1 구현 완료 후 테스트 및 문서화
2. 🔲 Phase 2 (Pre-commit) 구현 여부 결정
3. 🔲 Phase 3 (Pytest) 구현 여부 결정
4. 🔲 `/alfred:3-sync` 실행하여 Living Docs 업데이트

### 10.3 Future Considerations
1. 🔲 Slack/이메일 알림 시스템 추가 검토
2. 🔲 Import 검증 성능 최적화 연구
3. 🔲 다른 프로젝트로 확장 가능성 평가

---

**문서 작성자**: spec-builder agent
**최종 수정일**: 2025-01-24
**다음 단계**: Phase 1 구현 시작
