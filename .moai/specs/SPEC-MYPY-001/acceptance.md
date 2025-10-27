# @DOC:MYPY-001 - Acceptance Criteria

## Overview

이 문서는 **SPEC-MYPY-001 (MyPy Strict Mode 완전 준수)** 의 상세 인수 기준(Acceptance Criteria)을 정의합니다.

**검증 목표**: 1,008개 타입 오류 제로화 및 CI/CD Quality Gate 통과

---

## 1. Acceptance Criteria (Given-When-Then 형식)

### AC-1: 로컬 MyPy Strict Mode 검증

**Given**: 모든 Phase (1-3) 완료 후
**When**: 로컬 환경에서 `mypy --strict . --exclude venv` 실행 시
**Then**:
- ✅ Exit code 0 반환
- ✅ "Success: no issues found in X source files" 메시지 출력
- ✅ 오류 개수 0개 (error, warning, note 포함)

**Verification Command**:
```bash
mypy --strict . --exclude venv
echo "Exit code: $?"  # Expected: 0
```

**Expected Output**:
```
Success: no issues found in 265 source files
Exit code: 0
```

---

### AC-2: CI/CD Quality Gate 통과

**Given**: `.github/workflows/ci.yml`에서 `continue-on-error` 제거 후
**When**: Pull Request 생성 및 CI 실행 시
**Then**:
- ✅ MyPy Type Check 단계 성공 (초록색 체크마크)
- ✅ CI 전체 워크플로우 통과
- ✅ 3회 연속 CI 통과 (안정성 검증)

**CI Log 예시**:
```yaml
Run mypy --strict . --exclude venv
Success: no issues found in 265 source files
✅ MyPy Type Check passed (2m 15s)
```

**Verification**:
- GitHub Actions UI에서 초록색 체크마크 확인
- PR merge 차단 없음 (required check 통과)

---

### AC-3: 기존 기능 보존 (Zero Regression)

**Given**: 타입 어노테이션 추가 및 수정 완료 후
**When**: 전체 테스트 스위트 실행 시
**Then**:
- ✅ 모든 pytest 테스트 통과 (100% pass rate)
- ✅ 기존 테스트 개수 유지 (추가는 허용, 삭제는 금지)
- ✅ 테스트 실행 시간 변화 < 10%

**Verification Command**:
```bash
pytest tests/ -v --tb=short
echo "Exit code: $?"  # Expected: 0
```

**Expected Output**:
```
=============== X passed in Y.YYs ===============
Exit code: 0
```

**Failure Scenario**:
- ❌ 단일 테스트라도 실패 시 AC-3 미충족
- ❌ 타입 변경으로 인한 런타임 오류 발생 시 AC-3 미충족

---

### AC-4: Test Coverage 유지

**Given**: 타입 수정 완료 후
**When**: pytest coverage 측정 시
**Then**:
- ✅ Coverage 수준 유지 또는 향상
- ✅ Coverage 감소 < 2% (허용 오차)
- ✅ Critical path (핵심 로직) coverage 100% 유지

**Verification Command**:
```bash
pytest --cov --cov-report=term-missing --cov-report=html
```

**Expected Output**:
```
---------- coverage: platform linux, python 3.9.X -----------
Name                           Stmts   Miss  Cover
--------------------------------------------------
apps/api/main.py                 150      5    97%
apps/orchestration/main.py       200      8    96%
...
--------------------------------------------------
TOTAL                           5000    150    97%
```

**Comparison**:
```bash
# Before (baseline)
TOTAL: 5000 statements, 150 missed, 97% coverage

# After (target)
TOTAL: 5000 statements, ≤153 missed, ≥95% coverage
```

---

### AC-5: Type Ignore 최소화

**Given**: 모든 Phase 완료 후
**When**: 프로젝트 전체에서 `# type: ignore` 검색 시
**Then**:
- ✅ `# type: ignore` 사용 0건 (이상적)
- ✅ 불가피한 경우 문서화된 주석과 함께 최소화
- ✅ 사용 시 명확한 사유 주석 필수

**Verification Command**:
```bash
rg "# type: ignore" --count-matches
```

**Expected Output**:
```
# 이상적: 0 matches found
# 허용: <5 matches with documented reasons
```

**Documented Exception Example**:
```python
# type: ignore[import-untyped]  # TODO(MYPY-001): Add types-XXX package
from external_library import untyped_function
```

---

### AC-6: Type Accuracy (Any 최소화)

**Given**: Phase 2 수동 수정 완료 후
**When**: 프로젝트 전체에서 `Any` 사용 검사 시
**Then**:
- ✅ `Any` 사용 최소화 (구체적 타입 선호)
- ✅ `Any` 사용 시 TODO 주석으로 향후 개선 표시
- ✅ 자동화 스크립트가 추가한 `Any`는 수동 검토 대상

**Verification Command**:
```bash
rg ":\s*Any\b" --count-matches
```

**Acceptable Use Cases**:
```python
# ✅ 허용: 동적 데이터 구조
def parse_json(data: str) -> Any:
    return json.loads(data)

# ✅ 허용: 제네릭 컨테이너 (임시)
cache: Dict[str, Any] = {}  # TODO(MYPY-001): Define specific schema

# ❌ 금지: 명확한 타입 정의 가능한 경우
def get_user_id(user: Any) -> int:  # Should be User
    return user.id
```

---

## 2. Test Scenarios (Given-When-Then)

### Scenario 1: Phase 1 자동화 성공 검증

**Given**:
- `scripts/fix_mypy_auto.py` 스크립트 준비 완료
- `mypy_errors.txt`에 1,008개 오류 존재

**When**:
- `python scripts/fix_mypy_auto.py --errors no-untyped-def,var-annotated` 실행

**Then**:
- ✅ ~600개 오류 자동 수정 (no-untyped-def, var-annotated)
- ✅ 모든 수정 파일 pytest 통과
- ✅ MyPy 오류 개수: 1,008 → ~400 감소
- ✅ Commit: `fix(mypy): apply automated type annotations (Phase 1)`

**Verification**:
```bash
# Before
mypy --strict . --exclude venv 2>&1 | grep "error:" | wc -l
# Output: 1008

# After Phase 1
mypy --strict . --exclude venv 2>&1 | grep "error:" | wc -l
# Expected: ~400
```

---

### Scenario 2: Phase 2 수동 수정 검증

**Given**:
- Phase 1 완료 후 ~400개 오류 남음
- 오류 유형: assignment, arg-type, call-arg 등

**When**:
- 파일별 수동 수정 진행 (10개 파일마다 checkpoint commit)

**Then**:
- ✅ 각 파일 수정 후 해당 테스트 통과
- ✅ 타입 정확도 향상 (`Any` 사용 최소화)
- ✅ 10개 파일마다 commit 및 CI 검증
- ✅ 최종 MyPy 오류 개수 0개

**Checkpoint Verification**:
```bash
# 10개 파일 수정 후
mypy --strict . --exclude venv 2>&1 | grep "error:" | wc -l
# Expected: ~350 (50개 감소)

pytest tests/ -v
# Expected: 100% passed
```

---

### Scenario 3: Phase 3 CI/CD 통합 검증

**Given**:
- Phase 1, 2 완료 후 로컬에서 MyPy 오류 0개

**When**:
- `.github/workflows/ci.yml`에서 `continue-on-error: true` 제거
- Pull Request 생성 및 CI 실행

**Then**:
- ✅ CI MyPy Type Check 단계 성공
- ✅ 전체 CI 워크플로우 통과
- ✅ 3회 연속 CI 통과 (안정성 검증)
- ✅ PR merge 가능 상태

**CI Workflow Verification**:
```yaml
# CI Log
✅ Checkout code
✅ Set up Python 3.9
✅ Install dependencies
✅ MyPy Type Check (2m 15s)
   └─ Success: no issues found in 265 source files
✅ Pytest (5m 30s)
   └─ 500 passed in 5.28s
✅ Build (3m 10s)
```

---

### Scenario 4: Regression 방지 검증

**Given**:
- 타입 어노테이션 추가 중 API 시그니처 변경 발생

**When**:
- 함수 파라미터 타입 변경 (예: `str` → `Union[str, int]`)

**Then**:
- ✅ 모든 호출부 검색 및 수정 완료
- ✅ 변경 파일의 모든 테스트 통과
- ✅ 통합 테스트 통과 (e2e 시나리오)
- ✅ API 호환성 유지 (기존 동작 보존)

**Example**:
```python
# Before
def process_id(user_id: int) -> User:
    return User.get(user_id)

# After (타입 확장)
def process_id(user_id: Union[int, str]) -> User:
    uid = int(user_id) if isinstance(user_id, str) else user_id
    return User.get(uid)

# 모든 호출부 확인
rg "process_id\(" -A 2
# Expected: 모든 호출부 변경 없이 동작 (Union 타입 호환)
```

---

## 3. Quality Gates

### 3.1 Phase 1 Quality Gate

**Entry Criteria**:
- ✅ 스크립트 개발 완료 (`fix_mypy_auto.py`)
- ✅ 샘플 파일로 스크립트 검증 완료

**Exit Criteria**:
- ✅ ~600개 오류 제거 (no-untyped-def, var-annotated)
- ✅ 모든 테스트 통과
- ✅ MyPy 오류 < 450개
- ✅ Commit 완료

**Verification**:
```bash
mypy --strict . --exclude venv | tee phase1_result.txt
grep "error:" phase1_result.txt | wc -l  # Expected: <450
pytest tests/ -v  # Expected: 100% passed
```

---

### 3.2 Phase 2 Quality Gate

**Entry Criteria**:
- ✅ Phase 1 Quality Gate 통과

**Exit Criteria**:
- ✅ 모든 수동 수정 대상 오류 제거
- ✅ MyPy 오류 0개
- ✅ 모든 테스트 통과
- ✅ Coverage 유지 (≥95%)
- ✅ 10개 파일마다 checkpoint commit 완료

**Verification**:
```bash
mypy --strict . --exclude venv  # Expected: "Success: no issues found"
pytest tests/ -v --cov  # Expected: 100% passed, coverage ≥95%
```

---

### 3.3 Phase 3 Quality Gate

**Entry Criteria**:
- ✅ Phase 2 Quality Gate 통과
- ✅ 로컬 검증 완료

**Exit Criteria**:
- ✅ CI/CD Quality Gate 활성화 (`continue-on-error` 제거)
- ✅ CI 3회 연속 통과
- ✅ PR merge 가능 상태
- ✅ Living Docs 업데이트 완료

**Verification**:
```bash
# CI 검증
gh pr checks  # Expected: All checks passed

# Quality metrics
mypy --strict . --exclude venv  # Exit code: 0
pytest --cov --cov-report=term  # Coverage: ≥95%
rg "# type: ignore" --count  # Expected: 0 or <5
```

---

## 4. Definition of Done (DoD)

### 4.1 Primary DoD

- ✅ **D1**: `mypy --strict . --exclude venv` exit code 0
- ✅ **D2**: CI/CD MyPy Type Check 단계 통과 (3회 연속)
- ✅ **D3**: 모든 pytest 테스트 통과 (100% pass rate)
- ✅ **D4**: Coverage 유지 또는 향상 (≥95%)

### 4.2 Secondary DoD

- ✅ **D5**: `# type: ignore` 사용 최소화 (<5 with documentation)
- ✅ **D6**: `Any` 사용 최소화 (TODO 주석 포함)
- ✅ **D7**: Living Docs 업데이트 (`.moai/specs/` 동기화)
- ✅ **D8**: Git commit history 정리 (squash 가능)

### 4.3 Documentation DoD

- ✅ **D9**: SPEC-MYPY-001 문서 최신 상태 유지
- ✅ **D10**: Phase별 결과 리포트 작성
- ✅ **D11**: 자동화 스크립트 README 작성
- ✅ **D12**: CI/CD Quality Gate 변경 사항 문서화

---

## 5. Test Execution Checklist

### 5.1 로컬 테스트 체크리스트

**Phase 1 완료 후**:
- [ ] `mypy --strict . --exclude venv` 실행
- [ ] 오류 개수 < 450개 확인
- [ ] `pytest tests/ -v` 실행 (100% passed)
- [ ] Phase 1 결과 commit

**Phase 2 완료 후**:
- [ ] `mypy --strict . --exclude venv` 실행 (오류 0개)
- [ ] `pytest tests/ -v --cov` 실행
- [ ] Coverage ≥95% 확인
- [ ] `rg "# type: ignore" --count` (0 or <5)
- [ ] Phase 2 최종 commit

**Phase 3 진입 전**:
- [ ] 로컬 최종 검증 완료
- [ ] `.github/workflows/ci.yml` 업데이트
- [ ] PR 생성 및 CI 모니터링

---

### 5.2 CI/CD 테스트 체크리스트

**PR 생성 후**:
- [ ] MyPy Type Check 단계 통과 확인
- [ ] Pytest 단계 통과 확인
- [ ] 전체 CI 워크플로우 성공 (초록색)
- [ ] CI 3회 연속 통과 검증

**Merge 전**:
- [ ] 모든 required checks 통과
- [ ] Code review 승인 (선택적)
- [ ] Living Docs 최신화 확인

---

## 6. Acceptance Sign-off

### 6.1 Sign-off Criteria

**SPEC-MYPY-001 최종 승인 조건**:
1. ✅ 모든 Acceptance Criteria (AC-1 ~ AC-6) 충족
2. ✅ 모든 Quality Gates (Phase 1-3) 통과
3. ✅ Definition of Done (D1 ~ D12) 완료
4. ✅ Test Execution Checklist 전체 체크
5. ✅ 사용자 최종 승인 (spec-builder → Alfred → User)

### 6.2 Sign-off Process

```
Phase 1 Complete
    ↓
Phase 1 Quality Gate → spec-builder review
    ↓
Phase 2 Complete
    ↓
Phase 2 Quality Gate → spec-builder review
    ↓
Phase 3 Complete
    ↓
Phase 3 Quality Gate → spec-builder review
    ↓
Final Acceptance → User approval
    ↓
SPEC-MYPY-001 Closed (status: completed)
```

### 6.3 Final Verification Command

```bash
#!/bin/bash
# final_verification.sh

echo "=== SPEC-MYPY-001 Final Verification ==="

# AC-1: MyPy strict mode
echo "▶ AC-1: MyPy Strict Mode"
mypy --strict . --exclude venv
if [ $? -eq 0 ]; then
    echo "✅ AC-1 Passed"
else
    echo "❌ AC-1 Failed"
    exit 1
fi

# AC-3: All tests
echo "▶ AC-3: All Tests"
pytest tests/ -v
if [ $? -eq 0 ]; then
    echo "✅ AC-3 Passed"
else
    echo "❌ AC-3 Failed"
    exit 1
fi

# AC-4: Coverage
echo "▶ AC-4: Coverage"
pytest --cov --cov-report=term | grep "TOTAL"
# Manual check: coverage ≥95%

# AC-5: Type ignore count
echo "▶ AC-5: Type Ignore Count"
COUNT=$(rg "# type: ignore" --count-matches | wc -l)
echo "Type ignore count: $COUNT (expected: 0 or <5)"

# AC-2: CI Status (manual check)
echo "▶ AC-2: CI Status (check GitHub Actions UI)"
gh pr checks
if [ $? -eq 0 ]; then
    echo "✅ AC-2 Passed"
else
    echo "⚠️ AC-2: Check CI manually"
fi

echo ""
echo "=== Final Verification Complete ==="
echo "Review results and confirm all criteria met."
```

---

**Acceptance Owner**: spec-builder agent
**Review Status**: Draft
**Last Updated**: 2025-01-25
**Next Step**: `/alfred:2-run SPEC-MYPY-001` 실행 후 AC 검증
