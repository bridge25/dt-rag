# SPEC-CICD-001 Acceptance Criteria

**@ACCEPTANCE:CICD-001**

---

## 1. Overview

### 1.1 Purpose
이 문서는 SPEC-CICD-001 "CI/CD Import 검증 자동화" 기능의 완료 조건을 정의한다. 모든 인수 기준이 충족되어야 해당 SPEC이 완료된 것으로 간주한다.

### 1.2 Verification Method
- **Automated Testing**: pytest를 사용한 자동화 테스트
- **Manual Testing**: 고의로 오류를 삽입하여 감지 여부 확인
- **Regression Testing**: 과거 발생한 실제 오류 재현 후 감지 확인
- **Performance Testing**: 실행 시간 측정 및 목표 달성 여부 확인

### 1.3 Definition of Done
- ✅ 모든 Given-When-Then 시나리오 통과
- ✅ 모든 Edge Case 처리 확인
- ✅ 성능 기준 충족 (CI/CD < 5분, Pre-commit < 15초)
- ✅ 문서화 완료 (README, troubleshooting guide)
- ✅ 코드 리뷰 승인

---

## 2. Acceptance Criteria by Phase

### 2.1 Phase 1: GitHub Actions Workflow (P0)

#### AC1.1: Workflow 기본 구조

**Given-When-Then**:
```gherkin
Given GitHub repository가 설정되어 있고
When 개발자가 master 브랜치에 코드를 push하면
Then GitHub Actions workflow가 자동으로 트리거되어야 한다

And workflow 이름은 "Import Validation"이어야 한다
And Python 3.11 환경이 설정되어야 한다
And pip cache가 활성화되어야 한다
```

**Verification Steps**:
1. Feature 브랜치 생성: `git checkout -b test/ac1.1`
2. 정상 코드를 master에 push
3. GitHub Actions UI 확인:
   - "Import Validation" workflow 존재 확인
   - Python 3.11 setup 단계 통과 확인
   - pip cache hit 로그 확인

**Expected Output**:
```yaml
✓ Checkout code
✓ Set up Python 3.11
✓ Cache hit: /opt/hostedrunner/.cache/pip
✓ Install dependencies
```

**Acceptance**:
- ✅ Workflow 파일이 `.github/workflows/import-validation.yml`에 존재
- ✅ Workflow가 push/PR 이벤트에서 트리거됨
- ✅ Python 3.11 환경 설정 성공
- ✅ pip cache 작동 확인

---

#### AC1.2: Compileall 구문 검증

**Given-When-Then**:
```gherkin
Given Python 코드베이스가 존재하고
When GitHub Actions workflow가 실행되면
Then python -m compileall 명령으로 apps/ 및 tests/ 디렉토리를 검증해야 한다

And 구문 오류가 없으면 통과해야 한다
And 구문 오류가 있으면 실패하고 명확한 오류 메시지를 출력해야 한다
```

**Verification Steps**:

**Test Case 1: 정상 코드**
1. 정상 코드를 push
2. GitHub Actions 로그 확인

**Expected Output**:
```
🔍 Step 1: Validating Python syntax...
✓ Syntax validation passed
```

**Test Case 2: 구문 오류 주입**
1. 고의로 구문 오류 삽입:
   ```python
   # apps/api/test_syntax_error.py
   def broken_function(
       # Missing closing parenthesis
   ```
2. Push 후 GitHub Actions 확인

**Expected Output**:
```
❌ Syntax validation failed
SyntaxError: invalid syntax (test_syntax_error.py, line 2)
```

**Acceptance**:
- ✅ 정상 코드에서 compileall 통과
- ✅ 구문 오류 시 workflow 실패
- ✅ 오류 위치 명확히 표시 (파일명, 라인 번호)
- ✅ 실행 시간 < 10초

---

#### AC1.3: Alembic Migration 검증

**Given-When-Then**:
```gherkin
Given Alembic migration 파일이 존재하고
When GitHub Actions workflow가 실행되면
Then alembic upgrade head --sql 명령으로 dry-run 검증을 수행해야 한다

And migration import 오류가 없으면 통과해야 한다
And migration import 오류가 있으면 실패하고 오류를 리포팅해야 한다
And 실제 DB 변경은 발생하지 않아야 한다
```

**Verification Steps**:

**Test Case 1: 정상 Migration**
1. 정상 migration 파일 push
2. GitHub Actions 로그 확인

**Expected Output**:
```
🔍 Step 2: Validating Alembic migrations...
✓ Alembic validation passed
```

**Test Case 2: Migration Import 오류**
1. Migration 파일에 잘못된 import 추가:
   ```python
   # alembic/versions/xxx_test_migration.py
   from non_existent_module import NonExistentClass
   ```
2. Push 후 GitHub Actions 확인

**Expected Output**:
```
❌ Alembic validation failed
ModuleNotFoundError: No module named 'non_existent_module'
```

**Acceptance**:
- ✅ 정상 migration에서 alembic 검증 통과
- ✅ Import 오류 시 workflow 실패
- ✅ `--sql` 옵션으로 dry-run만 수행 (실제 DB 변경 없음)
- ✅ 실행 시간 < 10초

---

#### AC1.4: API Import 검증

**Given-When-Then**:
```gherkin
Given FastAPI 애플리케이션이 존재하고
When GitHub Actions workflow가 실행되면
Then python -c "from apps.api.main import app" 명령으로 API import를 검증해야 한다

And API import 오류가 없으면 통과해야 한다
And API import 오류가 있으면 실패하고 상세 오류를 출력해야 한다
```

**Verification Steps**:

**Test Case 1: 정상 API**
1. 정상 API 코드 push
2. GitHub Actions 로그 확인

**Expected Output**:
```
🔍 Step 3: Validating API imports...
✓ API imports validated
```

**Test Case 2: API Import 오류 (Regression Test)**
1. `QueryProcessor` import 오류 재현:
   ```python
   # apps/api/routers/search.py
   from apps.core.query.processor import QueryProcessor  # Wrong path
   ```
2. Push 후 GitHub Actions 확인

**Expected Output**:
```
❌ API import validation failed
ModuleNotFoundError: No module named 'apps.core.query.processor'
Did you mean: 'apps.core.query_processor'?
```

**Acceptance**:
- ✅ 정상 API에서 import 검증 통과
- ✅ Import 오류 시 workflow 실패 (Regression 방지)
- ✅ 오류 메시지에 모듈 경로 및 수정 제안 포함
- ✅ 실행 시간 < 5초

---

#### AC1.5: PR Merge 차단

**Given-When-Then**:
```gherkin
Given Pull Request가 생성되어 있고
When Import 검증이 실패하면
Then PR merge가 자동으로 차단되어야 한다

And GitHub UI에 "Some checks failed" 메시지가 표시되어야 한다
And 개발자가 수정 후 재검증할 수 있어야 한다
```

**Verification Steps**:
1. Import 오류가 있는 PR 생성
2. GitHub PR UI 확인:
   - "Import Validation" check 상태 = Failed
   - "Merge pull request" 버튼 비활성화
3. 오류 수정 후 push
4. Re-run 후 merge 가능 여부 확인

**Expected Output**:
```
PR Status:
✗ Import Validation — Failed
  Some checks failed

[Merge pull request] (disabled)
```

**Acceptance**:
- ✅ 검증 실패 시 PR merge 차단
- ✅ 실패 원인 명확히 표시
- ✅ 재검증 가능 (push 또는 re-run)
- ✅ 수정 후 merge 가능

---

#### AC1.6: 성능 요구사항

**Given-When-Then**:
```gherkin
Given GitHub Actions workflow가 실행되고
When 모든 검증 단계를 완료하면
Then 전체 실행 시간은 5분 이내여야 한다

And 각 검증 단계는 다음 시간 이내에 완료되어야 한다:
  - compileall: < 10초
  - alembic: < 10초
  - API import: < 5초
```

**Verification Steps**:
1. 정상 코드로 workflow 실행
2. GitHub Actions 로그에서 각 단계 실행 시간 확인
3. 10회 반복 후 평균 시간 계산

**Expected Output**:
```
Step 1: Validating Python syntax... (7s)
Step 2: Validating Alembic migrations... (5s)
Step 3: Validating API imports... (3s)
Total: 15s (including setup)
```

**Acceptance**:
- ✅ 전체 workflow 실행 시간 < 5분
- ✅ compileall < 10초
- ✅ alembic < 10초
- ✅ API import < 5초
- ✅ 평균 실행 시간 < 30초 (검증 단계만)

---

### 2.2 Phase 2: Pre-commit Hook (P1)

#### AC2.1: Pre-commit 설치 및 활성화

**Given-When-Then**:
```gherkin
Given .pre-commit-config.yaml 파일이 존재하고
When 개발자가 pre-commit install 명령을 실행하면
Then .git/hooks/pre-commit 파일이 생성되어야 한다

And commit 시 자동으로 import 검증이 실행되어야 한다
```

**Verification Steps**:
1. pre-commit 설치:
   ```bash
   pip install pre-commit
   pre-commit install
   ```
2. `.git/hooks/pre-commit` 파일 존재 확인
3. 테스트 commit 시도:
   ```bash
   git add .
   git commit -m "Test commit"
   ```

**Expected Output**:
```
Validate Python Imports................................................Passed
[test-branch abc1234] Test commit
```

**Acceptance**:
- ✅ `.pre-commit-config.yaml` 파일 존재
- ✅ `pre-commit install` 명령 성공
- ✅ `.git/hooks/pre-commit` 파일 생성
- ✅ Commit 시 자동 검증 실행

---

#### AC2.2: Pre-commit 검증 실패 처리

**Given-When-Then**:
```gherkin
Given Pre-commit hook이 활성화되어 있고
When Import 오류가 있는 코드를 commit하려고 하면
Then Commit이 중단되어야 한다

And 명확한 오류 메시지가 출력되어야 한다
And 개발자가 오류를 수정할 수 있도록 안내해야 한다
```

**Verification Steps**:
1. Import 오류 코드 작성:
   ```python
   # test_import_error.py
   from non_existent_module import Something
   ```
2. Commit 시도:
   ```bash
   git add test_import_error.py
   git commit -m "Test import error"
   ```

**Expected Output**:
```
Validate Python Imports................................................Failed
- hook id: validate-python-imports
- exit code: 1

ModuleNotFoundError: No module named 'non_existent_module'

Fix the import errors above before committing.
```

**Acceptance**:
- ✅ Import 오류 시 commit 중단
- ✅ 오류 메시지 명확히 출력
- ✅ 수정 방법 안내 포함
- ✅ 재시도 가능

---

#### AC2.3: Pre-commit Bypass 옵션

**Given-When-Then**:
```gherkin
Given Pre-commit hook이 활성화되어 있고
When 긴급 상황에서 검증을 우회해야 하면
Then --no-verify 옵션으로 commit이 가능해야 한다

And 우회 사용이 문서화되어 있어야 한다
And CI/CD에서 무조건 검증되므로 안전성이 보장되어야 한다
```

**Verification Steps**:
1. Import 오류 코드 작성
2. `--no-verify` 옵션으로 commit:
   ```bash
   git commit --no-verify -m "Emergency fix"
   ```
3. Commit 성공 확인
4. GitHub Actions에서 검증 실패 확인

**Expected Output**:
```
[test-branch def5678] Emergency fix
 1 file changed, 1 insertion(+)

(GitHub Actions will catch the error)
```

**Acceptance**:
- ✅ `--no-verify` 옵션으로 우회 가능
- ✅ 우회 방법 README에 문서화
- ✅ CI/CD에서 최종 검증 보장
- ✅ 긴급 상황 대응 가능

---

#### AC2.4: Pre-commit 성능

**Given-When-Then**:
```gherkin
Given Pre-commit hook이 실행되고
When 검증이 완료되면
Then 전체 실행 시간은 15초 이내여야 한다

And 개발자 경험에 부정적 영향을 주지 않아야 한다
```

**Verification Steps**:
1. 정상 코드로 10회 commit
2. 각 commit의 pre-commit 실행 시간 측정
3. 평균 실행 시간 계산

**Expected Output**:
```
Validate Python Imports......................................Passed (3.2s)
```

**Acceptance**:
- ✅ 평균 실행 시간 < 15초
- ✅ 최대 실행 시간 < 20초
- ✅ 개발자 피드백 긍정적

---

### 2.3 Phase 3: Pytest Fixture (P2)

#### AC3.1: Pytest Fixture 자동 실행

**Given-When-Then**:
```gherkin
Given tests/conftest.py에 validate_imports fixture가 정의되어 있고
When pytest 명령을 실행하면
Then 모든 테스트 실행 전 자동으로 import 검증이 수행되어야 한다

And Session-scoped이므로 테스트 스위트당 1회만 실행되어야 한다
```

**Verification Steps**:
1. pytest 실행:
   ```bash
   pytest -v
   ```
2. 출력에서 fixture 실행 확인

**Expected Output**:
```
============================================================
🔍 Pre-test Import Validation
============================================================

[1/2] Validating Python syntax (compileall)...
   ✓ Python syntax validated

[2/2] Validating API imports...
   ✓ API imports validated

============================================================
✅ All imports validated successfully
============================================================

tests/test_example.py::test_something PASSED
```

**Acceptance**:
- ✅ Fixture 자동 실행 (autouse=True)
- ✅ Session scope로 1회만 실행
- ✅ 검증 통과 후 테스트 진행
- ✅ 명확한 검증 결과 출력

---

#### AC3.2: Pytest Fixture 검증 실패 처리

**Given-When-Then**:
```gherkin
Given Import 오류가 있는 코드가 존재하고
When pytest를 실행하면
Then Fixture가 실패하고 테스트 스위트 실행이 중단되어야 한다

And 명확한 오류 메시지가 출력되어야 한다
And pytrace=False로 불필요한 traceback이 숨겨져야 한다
```

**Verification Steps**:
1. Import 오류 코드 작성
2. pytest 실행
3. 출력 확인

**Expected Output**:
```
============================================================
❌ Import Validation Failed: API Import Error
============================================================
ModuleNotFoundError: No module named 'non_existent_module'
============================================================
Fix the import errors above before running tests.

FAILED tests/conftest.py::validate_imports
```

**Acceptance**:
- ✅ Import 오류 시 fixture 실패
- ✅ 테스트 스위트 실행 중단
- ✅ 명확한 오류 메시지
- ✅ 불필요한 traceback 숨김

---

#### AC3.3: Pytest Fixture 성능

**Given-When-Then**:
```gherkin
Given Pytest fixture가 실행되고
When 검증이 완료되면
Then 실행 시간은 5초 이내여야 한다

And 테스트 시작 시간 증가가 최소화되어야 한다
```

**Verification Steps**:
1. pytest 실행 후 fixture 실행 시간 측정
2. 10회 반복 후 평균 시간 계산

**Expected Output**:
```
validate_imports (3.1s)
tests/test_example.py::test_something (0.2s)
```

**Acceptance**:
- ✅ 평균 fixture 실행 시간 < 5초
- ✅ 최대 실행 시간 < 7초
- ✅ 테스트 시작 지연 최소화

---

## 3. Edge Cases

### 3.1 Circular Import

**Scenario**:
```python
# module_a.py
from module_b import func_b

# module_b.py
from module_a import func_a
```

**Expected Behavior**:
- ✅ compileall은 구문 오류만 검증하므로 통과
- ✅ API import 시 circular import 오류 감지
- ✅ 명확한 오류 메시지 출력

**Verification**:
- Import 오류 감지 확인
- 오류 메시지에 circular import 안내 포함

---

### 3.2 Optional Dependency Missing

**Scenario**:
```python
try:
    import optional_package
except ImportError:
    optional_package = None
```

**Expected Behavior**:
- ✅ compileall 통과 (구문적으로 정상)
- ✅ API import 통과 (try-except로 처리)
- ✅ Optional dependency 누락은 허용

**Verification**:
- Optional dependency 없이 검증 통과
- 런타임 오류는 별도 테스트로 감지

---

### 3.3 Dynamic Import

**Scenario**:
```python
module_name = "some.module"
imported = importlib.import_module(module_name)
```

**Expected Behavior**:
- ✅ compileall 통과 (구문적으로 정상)
- ✅ API import 통과 (문자열 기반 import)
- ⚠️ 런타임 오류는 감지하지 못함

**Limitation**:
- Dynamic import는 정적 분석으로 검증 불가
- 별도 integration test 필요

---

### 3.4 Empty Repository

**Scenario**:
- `apps/` 디렉토리가 비어 있음
- `tests/` 디렉토리가 비어 있음

**Expected Behavior**:
- ✅ compileall 통과 (빈 디렉토리 허용)
- ✅ API import 실패 (apps.api.main 존재하지 않음)
- ✅ 명확한 오류 메시지 출력

**Verification**:
- 빈 디렉토리에서 검증 동작 확인
- API import 오류 메시지 확인

---

## 4. Non-functional Requirements

### 4.1 Performance

**Acceptance Criteria**:
- ✅ CI/CD 전체 실행 시간 < 5분
- ✅ Pre-commit 실행 시간 < 15초
- ✅ Pytest fixture 실행 시간 < 5초

**Verification Method**:
- 10회 반복 실행 후 평균 시간 측정
- 95th percentile < 목표 시간의 120%

---

### 4.2 Reliability

**Acceptance Criteria**:
- ✅ False negative rate = 0% (import 오류를 절대 놓치지 않음)
- ✅ False positive rate < 1% (정상 코드를 오류로 판정하는 비율)
- ✅ 네트워크 장애 시에도 로컬 검증 작동

**Verification Method**:
- 100개 테스트 케이스로 false negative/positive 측정
- 네트워크 차단 후 로컬 검증 테스트

---

### 4.3 Usability

**Acceptance Criteria**:
- ✅ 명확한 오류 메시지 (문제 위치, 원인, 수정 방법)
- ✅ 개발자 문서 완비 (README, troubleshooting guide)
- ✅ 긴급 우회 옵션 제공 (`--no-verify`)

**Verification Method**:
- 5명의 개발자에게 사용성 평가 요청
- 평균 만족도 > 4.0/5.0

---

### 4.4 Maintainability

**Acceptance Criteria**:
- ✅ 코드 주석 충분 (각 검증 단계 설명)
- ✅ TAG 추가 (`@CODE:CICD-001`, `@TEST:CICD-001`)
- ✅ 문서화 완료 (SPEC, plan, acceptance)

**Verification Method**:
- 코드 리뷰 체크리스트 통과
- 문서 완성도 검토

---

## 5. Integration Testing Scenarios

### 5.1 Full Workflow Test

**Scenario**:
```gherkin
Given 새로운 feature 브랜치가 생성되고
When 개발자가 정상 코드를 작성하고 commit하면
Then Pre-commit hook이 통과하고
And GitHub Actions workflow가 자동으로 실행되고
And 모든 검증 단계가 통과하고
And PR merge가 가능해야 한다
```

**Verification Steps**:
1. Feature 브랜치 생성
2. 정상 코드 작성
3. Commit (pre-commit 검증)
4. Push (GitHub Actions 검증)
5. PR 생성 및 merge 확인

**Expected Result**:
- ✅ Pre-commit 통과
- ✅ GitHub Actions 통과
- ✅ PR merge 성공

---

### 5.2 Regression Prevention Test

**Scenario**:
```gherkin
Given QueryProcessor import 오류가 재현되고
When 개발자가 오류 코드를 commit하려고 하면
Then Pre-commit hook이 오류를 감지하고 commit을 차단해야 한다

And --no-verify로 우회하여 push하면
Then GitHub Actions가 오류를 감지하고 PR merge를 차단해야 한다
```

**Verification Steps**:
1. `QueryProcessor` import 오류 재현:
   ```python
   from apps.core.query.processor import QueryProcessor  # Wrong
   ```
2. Commit 시도 (pre-commit 검증)
3. `--no-verify`로 우회 후 push
4. GitHub Actions 검증 확인

**Expected Result**:
- ✅ Pre-commit에서 오류 감지
- ✅ GitHub Actions에서 오류 감지
- ✅ PR merge 차단

---

### 5.3 Emergency Deployment Test

**Scenario**:
```gherkin
Given 긴급 배포가 필요한 상황이고
When 개발자가 --no-verify로 commit하고 push하면
Then CI/CD가 최종적으로 검증하고 오류가 있으면 배포를 차단해야 한다
```

**Verification Steps**:
1. 긴급 수정 코드 작성
2. `--no-verify`로 commit
3. Push 후 GitHub Actions 확인
4. Import 오류 시 배포 차단 확인

**Expected Result**:
- ✅ Pre-commit 우회 성공
- ✅ GitHub Actions 최종 검증
- ✅ 오류 시 배포 차단

---

## 6. Quality Gates

### 6.1 Phase 1 (P0) Completion Checklist

- ✅ AC1.1: Workflow 기본 구조 구현 완료
- ✅ AC1.2: Compileall 구문 검증 구현 완료
- ✅ AC1.3: Alembic migration 검증 구현 완료
- ✅ AC1.4: API import 검증 구현 완료
- ✅ AC1.5: PR merge 차단 기능 작동
- ✅ AC1.6: 성능 요구사항 충족 (< 5분)
- ✅ Regression test 통과 (QueryProcessor 오류 감지)
- ✅ 문서화 완료 (README 업데이트)

---

### 6.2 Phase 2 (P1) Completion Checklist

- ✅ AC2.1: Pre-commit 설치 및 활성화 가능
- ✅ AC2.2: 검증 실패 시 commit 차단
- ✅ AC2.3: Bypass 옵션 제공 및 문서화
- ✅ AC2.4: 성능 요구사항 충족 (< 15초)
- ✅ 설치 가이드 작성 (README)
- ✅ 팀원 교육 완료

---

### 6.3 Phase 3 (P2) Completion Checklist

- ✅ AC3.1: Pytest fixture 자동 실행
- ✅ AC3.2: 검증 실패 시 테스트 중단
- ✅ AC3.3: 성능 요구사항 충족 (< 5초)
- ✅ conftest.py 문서화
- ✅ Pytest verbose 출력 검증

---

## 7. Success Metrics Summary

### 7.1 Quantitative Metrics

| Metric | Target | Verification Method |
|--------|--------|-------------------|
| Import 오류 감지율 | 100% | Regression test with 10 known errors |
| False negative rate | 0% | 100 test cases, no missed errors |
| False positive rate | < 1% | 100 test cases, < 1 false alarm |
| CI/CD 실행 시간 | < 5분 | 10 runs, average time |
| Pre-commit 실행 시간 | < 15초 | 10 runs, average time |
| Pytest fixture 실행 시간 | < 5초 | 10 runs, average time |

---

### 7.2 Qualitative Metrics

| Metric | Target | Verification Method |
|--------|--------|-------------------|
| 개발자 만족도 | > 4.0/5.0 | User survey (5 developers) |
| 프로덕션 안정성 | 0 import-related incidents | 1 month monitoring |
| 코드 품질 | Import 기술 부채 감소 | Code review feedback |
| 문서 완성도 | 모든 시나리오 문서화 | Documentation review |

---

## 8. Final Verification Checklist

### 8.1 Pre-deployment Verification

- ✅ 모든 Given-When-Then 시나리오 통과
- ✅ 모든 Edge Case 처리 확인
- ✅ 모든 Performance 기준 충족
- ✅ Regression test 통과 (QueryProcessor 오류 감지)
- ✅ 통합 테스트 시나리오 완료
- ✅ 문서화 완료 (SPEC, plan, acceptance, README)

---

### 8.2 Post-deployment Verification

- ✅ 1주일간 CI/CD 실행 로그 모니터링
- ✅ Import 오류 감지 건수 집계
- ✅ False positive/negative rate 측정
- ✅ 개발자 피드백 수집 및 개선
- ✅ Retrospective 회의 개최

---

## 9. Known Limitations

### 9.1 Static Analysis Limitations

**Limitation**: Dynamic import는 정적 분석으로 검증 불가
```python
module_name = "some.module"
imported = importlib.import_module(module_name)
```

**Mitigation**: 별도 integration test 필요

---

### 9.2 Optional Dependency Handling

**Limitation**: Optional dependency 누락은 감지하지 못함
```python
try:
    import optional_package
except ImportError:
    optional_package = None
```

**Mitigation**: 런타임 테스트로 별도 검증

---

### 9.3 Network Dependency

**Limitation**: GitHub Actions는 네트워크 의존성 있음

**Mitigation**: Pre-commit hook과 pytest fixture로 로컬 검증 보완

---

## 10. Next Steps After Acceptance

1. ✅ `/alfred:3-sync` 실행하여 Living Docs 업데이트
2. ✅ GitHub Issue 상태를 "Done"으로 변경
3. ✅ PR merge 후 master 브랜치에 반영
4. ✅ 팀원에게 Pre-commit 설치 안내
5. ✅ 1주일 후 Retrospective 회의 개최
6. ✅ 다른 프로젝트로 확장 가능성 평가

---

**문서 작성자**: spec-builder agent
**최종 수정일**: 2025-01-24
**다음 단계**: Phase 1 구현 시작 후 AC 검증
