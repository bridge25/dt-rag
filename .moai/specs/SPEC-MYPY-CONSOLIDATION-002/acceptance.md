# @SPEC:MYPY-CONSOLIDATION-002: Acceptance Criteria

> **Test Strategy**: Given-When-Then scenarios for MyPy strict mode compliance
>
> **Quality Gates**: MyPy 0 errors + 85%+ test coverage + CI/CD enforcement

---

## Overview

본 문서는 SPEC-MYPY-CONSOLIDATION-002의 완료 기준을 정의한다. 각 Phase별 검증 시나리오와 최종 시스템 통합 테스트를 포함한다.

---

## AC-1: MyPy Strict Mode Compliance

### Scenario 1.1: Zero MyPy Errors

**Given**: 코드베이스에 1,079개의 MyPy strict mode 오류가 존재한다
**When**: 5-Phase 전략을 완료한다
**Then**: MyPy는 0개의 오류를 보고해야 한다

**Verification**:
```bash
# Test execution
mypy --strict apps/ tests/ 2>&1 | tee mypy-report.txt

# Success criteria
echo $?  # Expected: 0 (exit code)
grep "error:" mypy-report.txt | wc -l  # Expected: 0
grep "Success:" mypy-report.txt  # Expected: "Success: no issues found"
```

**Acceptance**:
- [ ] MyPy exit code = 0
- [ ] No lines containing "error:" in output
- [ ] "Success: no issues found" message appears

---

### Scenario 1.2: Configuration Compliance

**Given**: pyproject.toml에 MyPy strict mode 설정이 있다
**When**: MyPy를 실행한다
**Then**: 모든 strict 플래그가 활성화되어야 한다

**Verification**:
```bash
# Check configuration
grep -A 20 "\[tool.mypy\]" pyproject.toml

# Expected flags:
# - strict = true
# - disallow_untyped_defs = true
# - disallow_any_generics = true
# - no_implicit_optional = true
# - warn_return_any = true
```

**Acceptance**:
- [ ] `strict = true` 설정 확인
- [ ] 모든 disallow_* 플래그 활성화
- [ ] 모든 warn_* 플래그 활성화

---

## AC-2: Test Suite Integrity

### Scenario 2.1: All Tests Pass

**Given**: 타입 힌트가 추가된 코드베이스가 있다
**When**: 전체 테스트 스위트를 실행한다
**Then**: 모든 테스트가 통과해야 한다

**Verification**:
```bash
# Run tests
pytest tests/ -v --tb=short 2>&1 | tee test-report.txt

# Success criteria
echo $?  # Expected: 0
grep "passed" test-report.txt  # Expected: "XXX passed"
grep "failed" test-report.txt  # Expected: no output
```

**Acceptance**:
- [ ] Pytest exit code = 0
- [ ] No failed tests
- [ ] No skipped tests (unless explicitly marked)

---

### Scenario 2.2: Coverage Maintained

**Given**: 코드베이스의 현재 테스트 커버리지가 85% 이상이다
**When**: 타입 힌트 추가 후 커버리지를 측정한다
**Then**: 커버리지는 85% 이상을 유지해야 한다

**Verification**:
```bash
# Run coverage analysis
pytest tests/ --cov=apps --cov-report=term-missing --cov-report=html --cov-fail-under=85

# Check coverage report
coverage report | tail -1
# Expected: TOTAL ... XXX ... 85% or higher
```

**Acceptance**:
- [ ] Overall coverage ≥ 85%
- [ ] No critical modules below 80%
- [ ] Coverage report generated in htmlcov/

---

### Scenario 2.3: Type Safety Tests

**Given**: 타입 안전성을 검증하는 테스트가 필요하다
**When**: 타입 관련 테스트를 실행한다
**Then**: 모든 타입 안전성 테스트가 통과해야 한다

**Verification**:
```bash
# Run type safety tests
pytest tests/type_safety/ -v

# Expected tests:
# - test_phase1_sqlalchemy_types.py
# - test_phase2_critical_errors.py
# - test_phase3_type_annotations.py
# - test_phase4_pattern_fixes.py
# - test_phase5_import_cleanup.py
```

**Acceptance**:
- [ ] SQLAlchemy model types validated
- [ ] Function signature types validated
- [ ] Return type consistency validated
- [ ] Union type handling validated
- [ ] Import resolution validated

---

## AC-3: CI/CD Integration

### Scenario 3.1: CI Pipeline Enforcement

**Given**: GitHub Actions CI 워크플로우가 있다
**When**: 코드를 푸시한다
**Then**: MyPy strict mode가 품질 게이트로 작동해야 한다

**Verification**:
```yaml
# .github/workflows/ci.yml
jobs:
  type-check:
    steps:
      - name: Run MyPy strict mode
        run: mypy --strict apps/ tests/
        continue-on-error: false  # MUST be false

# Test with intentional error
echo "def broken() -> int: return 'string'" >> apps/test_error.py
git add . && git commit -m "test: CI enforcement" && git push

# Expected: CI build FAILS
```

**Acceptance**:
- [ ] `continue-on-error: false` in CI config
- [ ] CI fails when MyPy errors exist
- [ ] CI passes when MyPy clean
- [ ] Type check runs before tests

---

### Scenario 3.2: Pre-commit Hook

**Given**: 로컬 개발 환경에 pre-commit hook이 있다
**When**: 커밋을 시도한다
**Then**: MyPy가 자동으로 실행되어야 한다

**Verification**:
```bash
# Check pre-commit config
cat .pre-commit-config.yaml | grep mypy

# Test hook
echo "def untyped(x): return x" >> apps/test_hook.py
git add apps/test_hook.py
git commit -m "test: pre-commit hook"

# Expected: Commit blocked, MyPy errors shown
```

**Acceptance**:
- [ ] Pre-commit hook configured
- [ ] MyPy runs on staged files
- [ ] Commit blocked if MyPy fails
- [ ] Clear error messages shown

---

### Scenario 3.3: Fast Feedback Loop

**Given**: 개발자가 로컬에서 작업 중이다
**When**: MyPy를 실행한다
**Then**: 30초 이내에 결과를 반환해야 한다

**Verification**:
```bash
# Benchmark MyPy runtime
time mypy --strict apps/ tests/

# Expected: real time < 30 seconds
```

**Acceptance**:
- [ ] MyPy runtime < 30 seconds
- [ ] Incremental mode enabled (`.mypy_cache/`)
- [ ] Cache persisted between runs

---

## AC-4: Phase-Specific Validation

### Scenario 4.1: Phase 1 - SQLAlchemy Types

**Given**: SQLAlchemy 모델에 81개의 assignment 오류가 있다
**When**: Phase 1을 완료한다
**Then**: 모든 Column이 Mapped[] 타입을 가져야 한다

**Verification**:
```bash
# Check for old-style columns
rg "Column\(Integer|String|Boolean" --type python apps/
# Expected: no results

# Check for new-style mapped_column
rg "Mapped\[" --type python apps/ | wc -l
# Expected: > 0

# MyPy check
mypy --strict apps/ 2>&1 | grep "assignment.*incompatible" | wc -l
# Expected: 0
```

**Test Cases**:
```python
# tests/type_safety/test_phase1_sqlalchemy_types.py

def test_all_columns_have_mapped_type():
    """All SQLAlchemy columns should use Mapped[] type hints"""
    from apps.fastapi_app.models import User
    import inspect

    annotations = inspect.get_annotations(User)
    for field, type_hint in annotations.items():
        assert "Mapped" in str(type_hint), f"Field {field} missing Mapped[] type"

def test_nullable_fields_use_optional():
    """Nullable columns should use Mapped[Optional[T]]"""
    from apps.fastapi_app.models import User
    from typing import get_origin, get_args

    # Check email field (nullable)
    email_type = User.__annotations__["email"]
    assert "Optional" in str(email_type) or "None" in str(get_args(email_type))
```

**Acceptance**:
- [ ] 0 assignment errors
- [ ] All Column → mapped_column
- [ ] All fields have Mapped[] type
- [ ] Nullable fields use Optional

---

### Scenario 4.2: Phase 2 - Critical Errors

**Given**: 163개의 call-arg 및 attr-defined 오류가 있다
**When**: Phase 2를 완료한다
**Then**: 모든 함수 호출과 속성 접근이 타입 안전해야 한다

**Verification**:
```bash
# MyPy check
mypy --strict apps/ 2>&1 | grep -E "(call-arg|attr-defined)" | wc -l
# Expected: 0

# Check for hasattr guards
rg "hasattr\(" --type python apps/ | wc -l
# Expected: > 0 (guard clauses added)

# Check for type casting
rg "cast\(" --type python apps/ | wc -l
# Expected: > 0 (explicit casts added)
```

**Test Cases**:
```python
# tests/type_safety/test_phase2_critical_errors.py

def test_function_calls_have_correct_types():
    """Function calls should match parameter types"""
    from apps.fastapi_app.services import process_data

    # Should accept correct type
    result = process_data({"key": "value"})
    assert isinstance(result, dict)

    # MyPy should catch incorrect type at static analysis time

def test_attribute_access_is_guarded():
    """Dynamic attribute access should have guards"""
    from apps.fastapi_app.models import Base

    obj = Base()
    # Should not directly access potentially missing attributes
    # Should use hasattr or type narrowing
```

**Acceptance**:
- [ ] 0 call-arg errors
- [ ] 0 attr-defined errors
- [ ] Type guards added where needed
- [ ] Explicit casts documented

---

### Scenario 4.3: Phase 3 - Type Annotations

**Given**: 464개의 no-untyped-def 오류가 있다
**When**: Phase 3을 완료한다
**Then**: 모든 함수가 완전한 타입 시그니처를 가져야 한다

**Verification**:
```bash
# MyPy check
mypy --strict apps/ 2>&1 | grep "no-untyped-def" | wc -l
# Expected: 0

# Check annotation completeness
python -c "
import ast
import glob

for file in glob.glob('apps/**/*.py', recursive=True):
    with open(file) as f:
        tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns is None:
                    print(f'{file}:{node.name} missing return type')
                for arg in node.args.args:
                    if arg.annotation is None:
                        print(f'{file}:{node.name}:{arg.arg} missing param type')
"
# Expected: no output
```

**Test Cases**:
```python
# tests/type_safety/test_phase3_type_annotations.py

def test_all_functions_have_return_types():
    """All functions should have explicit return type annotations"""
    import inspect
    import apps.fastapi_app.services as services

    for name, obj in inspect.getmembers(services, inspect.isfunction):
        sig = inspect.signature(obj)
        assert sig.return_annotation != inspect.Signature.empty, \
            f"Function {name} missing return type"

def test_all_parameters_have_types():
    """All function parameters should have type annotations"""
    import inspect
    import apps.fastapi_app.services as services

    for name, obj in inspect.getmembers(services, inspect.isfunction):
        sig = inspect.signature(obj)
        for param_name, param in sig.parameters.items():
            if param_name != "self":
                assert param.annotation != inspect.Parameter.empty, \
                    f"Function {name} parameter {param_name} missing type"
```

**Acceptance**:
- [ ] 0 no-untyped-def errors
- [ ] All functions have return types
- [ ] All parameters have types
- [ ] Complex types use generics

---

### Scenario 4.4: Phase 4 - Pattern Fixes

**Given**: 105개의 union-attr 및 no-any-return 오류가 있다
**When**: Phase 4를 완료한다
**Then**: Union 타입 처리와 Any 타입 제거가 완료되어야 한다

**Verification**:
```bash
# MyPy check
mypy --strict apps/ 2>&1 | grep -E "(union-attr|no-any-return)" | wc -l
# Expected: 0

# Check for type narrowing
rg "isinstance\(" --type python apps/ | wc -l
# Expected: > 0

# Check for Any usage
rg "from typing import.*Any" --type python apps/ | wc -l
# Expected: minimal (only for JSON values)
```

**Test Cases**:
```python
# tests/type_safety/test_phase4_pattern_fixes.py

def test_union_types_have_narrowing():
    """Union type access should use type narrowing"""
    from apps.fastapi_app.utils import format_value

    # Should handle both types correctly
    assert format_value("test") == "TEST"
    assert format_value(42) == "42"

def test_no_any_return_types():
    """Functions should not return Any type"""
    import inspect
    import apps.fastapi_app.services as services

    for name, obj in inspect.getmembers(services, inspect.isfunction):
        sig = inspect.signature(obj)
        return_type = str(sig.return_annotation)
        assert "Any" not in return_type or name.startswith("_"), \
            f"Function {name} returns Any type"
```

**Acceptance**:
- [ ] 0 union-attr errors
- [ ] 0 no-any-return errors
- [ ] Type narrowing implemented
- [ ] Any usage minimized

---

### Scenario 4.5: Phase 5 - Import Cleanup

**Given**: 266개의 import 관련 오류가 있다
**When**: Phase 5를 완료한다
**Then**: 모든 import가 해결되거나 정당화되어야 한다

**Verification**:
```bash
# MyPy check
mypy --strict apps/ tests/ 2>&1 | grep "error:" | wc -l
# Expected: 0

# Check for type: ignore with justification
rg "# type: ignore\[" --type python apps/ -A 1
# Expected: All have comments explaining why

# Check for py.typed markers
find apps/ -name "py.typed"
# Expected: apps/fastapi_app/py.typed, etc.
```

**Test Cases**:
```python
# tests/type_safety/test_phase5_import_cleanup.py

def test_all_imports_resolved():
    """All imports should be resolvable by MyPy"""
    # MyPy should pass with 0 errors (tested via CI)
    pass

def test_type_ignore_has_justification():
    """All type: ignore comments should have justification"""
    import re
    import glob

    pattern = re.compile(r'#\s*type:\s*ignore(?!\[)')
    for file in glob.glob('apps/**/*.py', recursive=True):
        with open(file) as f:
            for i, line in enumerate(f, 1):
                match = pattern.search(line)
                assert match is None, \
                    f"{file}:{i} has type: ignore without error code"
```

**Acceptance**:
- [ ] 0 import-not-found errors
- [ ] 0 import-untyped errors
- [ ] All type: ignore have codes
- [ ] All type: ignore have justification

---

## AC-5: Documentation and Maintainability

### Scenario 5.1: Type Ignore Justification

**Given**: 코드에 `# type: ignore` 주석이 있다
**When**: 주석을 검토한다
**Then**: 모든 주석에 오류 코드와 정당화 사유가 있어야 한다

**Verification**:
```bash
# Find all type: ignore comments
rg "# type: ignore" --type python apps/ tests/

# Check for format: # type: ignore[error-code]  # Justification
rg "# type: ignore\[[a-z-]+\].*# .+" --type python apps/ tests/ | wc -l
rg "# type: ignore" --type python apps/ tests/ | wc -l

# Both counts should match (all have justification)
```

**Acceptance**:
- [ ] All `# type: ignore` have error codes
- [ ] All have justification comments
- [ ] Justifications are meaningful
- [ ] Documented in code review

---

### Scenario 5.2: Type Documentation

**Given**: 프로젝트에 타입 안전성 가이드가 필요하다
**When**: 문서를 생성한다
**Then**: 개발자가 타입 시스템을 이해할 수 있어야 한다

**Verification**:
```bash
# Check for documentation
test -f docs/mypy-strict-mode-guide.md
echo $?  # Expected: 0 (file exists)

# Check for key sections
grep "## Type Annotation Guidelines" docs/mypy-strict-mode-guide.md
grep "## Common Patterns" docs/mypy-strict-mode-guide.md
grep "## Error Resolution" docs/mypy-strict-mode-guide.md
```

**Acceptance**:
- [ ] Type safety guide created
- [ ] Common patterns documented
- [ ] Error resolution examples provided
- [ ] Best practices documented

---

### Scenario 5.3: Future Maintenance

**Given**: 새로운 코드가 추가된다
**When**: 타입 힌트 없이 커밋을 시도한다
**Then**: MyPy가 즉시 오류를 보고해야 한다

**Verification**:
```bash
# Add untyped function
echo "def new_function(x): return x * 2" >> apps/test_new.py
git add apps/test_new.py

# Pre-commit should fail
git commit -m "test: untyped function"
# Expected: blocked by pre-commit hook

# CI should fail if committed
git commit -m "test: untyped function" --no-verify
git push
# Expected: CI build fails
```

**Acceptance**:
- [ ] Pre-commit hook catches violations
- [ ] CI catches violations
- [ ] Clear error messages
- [ ] Developer guidance provided

---

## Final Acceptance Checklist

### Critical Requirements

- [ ] **AC-1**: MyPy strict mode exits with code 0
- [ ] **AC-2**: All tests pass with 85%+ coverage
- [ ] **AC-3**: CI/CD enforces MyPy strict mode (`continue-on-error: false`)
- [ ] **AC-4**: All 5 Phases reduce target errors to 0
- [ ] **AC-5**: All `# type: ignore` have error codes and justification

### Phase Completion

- [ ] **Phase 1**: SQLAlchemy Casting (81 → 0)
- [ ] **Phase 2**: Critical Errors (163 → 0)
- [ ] **Phase 3**: Type Annotations (464 → 0)
- [ ] **Phase 4**: Pattern Fixes (105 → 0)
- [ ] **Phase 5**: Import Cleanup (266 → 0)

### Quality Gates

- [ ] MyPy runtime < 30 seconds
- [ ] Test coverage ≥ 85%
- [ ] No unjustified `# type: ignore`
- [ ] Pre-commit hook enabled
- [ ] CI/CD integration verified
- [ ] Documentation complete

### Performance Metrics

- [ ] MyPy error count: 1,079 → 0
- [ ] Test pass rate: 100%
- [ ] CI build time increase: < 10%
- [ ] Developer feedback loop: < 1 minute (pre-commit)

---

## Definition of Done

**SPEC-MYPY-CONSOLIDATION-002는 다음 조건이 모두 충족될 때 완료된 것으로 간주한다**:

1. **Zero MyPy Errors**: `mypy --strict apps/ tests/` 실행 시 exit code 0
2. **Test Suite Pass**: 모든 테스트 통과, 85%+ 커버리지 유지
3. **CI/CD Enforcement**: GitHub Actions에서 MyPy strict mode 강제 적용
4. **Documentation**: 모든 `# type: ignore`에 정당화 사유 포함
5. **Validation**: 위 acceptance criteria 모두 충족

**Verification Command**:
```bash
# One-line verification
mypy --strict apps/ tests/ && pytest tests/ --cov=apps --cov-fail-under=85 && echo "✅ SPEC-MYPY-CONSOLIDATION-002 COMPLETE"
```

---

**END OF ACCEPTANCE CRITERIA**
