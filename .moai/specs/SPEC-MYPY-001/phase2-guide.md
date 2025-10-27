# Phase 2 Implementation Guide - SPEC-MYPY-001

## 📊 Current Status (Phase 1 Complete)

**Commit**: `a734726` - Phase 1 automated type annotations (Option C)
**Branch**: `feature/SPEC-MYPY-001`
**Progress**: 1,045 → 982 errors (63 errors fixed, 6% improvement)

---

## 🎯 Phase 2 Objective

**Goal**: Eliminate remaining 982 mypy errors through manual fixes
**Estimated Time**: 4-6 hours
**Strategy**: File-by-file manual fixes with monkeytype assistance

---

## 🛠️ Phase 2 Execution Plan

### Step 1: Analyze Remaining Errors (30 min)

```bash
# Generate error breakdown by type
cat mypy_phase1_v2_result.txt | grep "error:" | \
  sed -E 's/.*error: (.+) \[(.+)\]$/\2/' | \
  sort | uniq -c | sort -rn > error_types.txt

# Identify files with most errors
cat mypy_phase1_v2_result.txt | grep "error:" | \
  sed -E 's/^([^:]+):.*/\1/' | \
  sort | uniq -c | sort -rn | head -20 > error_files.txt
```

**Expected top error types**:
1. `assignment` - Type mismatch (e.g., Optional[X] → X)
2. `arg-type` - Function argument type mismatch
3. `return-value` - Incorrect return type
4. `union-attr` - Optional attribute access without None check
5. `attr-defined` - Undefined attributes
6. `no-redef` - Name redefinition

---

### Step 2: Prioritize Files (15 min)

**Strategy**: Fix files with most errors first for maximum impact

```bash
# Top 20 files to fix
head -20 error_files.txt
```

**Prioritization criteria**:
1. High error count (>10 errors per file)
2. Critical files (e.g., API routers, core services)
3. Simple fixes (e.g., add Optional[], add None checks)

---

### Step 3: Setup monkeytype (Optional, 30 min)

monkeytype는 런타임 타입 추론을 통해 수동 수정을 가속화합니다.

```bash
# Install monkeytype (already installed)
python3 -c "import monkeytype; print('✓ monkeytype ready')"

# Run tests with monkeytype tracing
monkeytype run -m pytest tests/unit/ -v

# Generate stub for a specific module
monkeytype stub apps.api.routers.agent_router > stubs/agent_router.pyi

# Apply inferred types to source
monkeytype apply apps.api.routers.agent_router
```

**Note**: monkeytype는 실제 실행 경로에서만 타입을 추론하므로 테스트 커버리지가 중요합니다.

---

### Step 4: Manual Fixes (3-4 hours)

#### 4.1 Fix Pattern 1: Optional Types

**Error**: `assignment` - Incompatible default (None → non-Optional)

```python
# ❌ Before
def process(data: dict = None):  # mypy error: assignment
    ...

# ✅ After
from typing import Optional
def process(data: Optional[dict] = None):
    ...
```

#### 4.2 Fix Pattern 2: Union Attribute Access

**Error**: `union-attr` - Optional attribute access

```python
# ❌ Before
def get_name(user: Optional[User]) -> str:
    return user.name  # error: Item "None" has no attribute "name"

# ✅ After
def get_name(user: Optional[User]) -> str:
    if user is None:
        return "Unknown"
    return user.name
```

#### 4.3 Fix Pattern 3: Return Type Corrections

**Error**: `return-value` - Incompatible return type

```python
# ❌ Before
def find_user(id: int) -> User:  # error: can return None
    return db.query(User).filter_by(id=id).first()

# ✅ After
def find_user(id: int) -> Optional[User]:
    return db.query(User).filter_by(id=id).first()
```

#### 4.4 Fix Pattern 4: Argument Type Fixes

**Error**: `arg-type` - Incompatible argument type

```python
# ❌ Before
def send_email(to: str, body: str):
    ...

send_email(to=user.email, body=None)  # error: arg-type

# ✅ After
def send_email(to: str, body: Optional[str] = None):
    if body is None:
        body = "Default message"
    ...
```

---

### Step 5: Checkpoint Commits (Every 10 Files)

**Strategy**: Create checkpoint commits to enable easy rollback

```bash
# After fixing 10 files
git add apps/api/routers/*.py  # files you fixed
git commit -m "fix(types): manual type fixes batch 1 (files 1-10) @CODE:MYPY-001:PHASE2

- Fixed assignment errors (Optional types)
- Fixed union-attr errors (None checks)
- Fixed return-value errors (return type corrections)

Progress: 982 → ~850 errors
Refs: @SPEC:MYPY-001"

# Verify improvement
~/.local/bin/mypy apps/ --config-file=pyproject.toml | grep "^Found"
```

**Checkpoint schedule**:
- Batch 1: Files 1-10 (top error files)
- Batch 2: Files 11-20
- Batch 3: Files 21-30
- ... continue until 0 errors

---

### Step 6: Handle Difficult Cases (1-2 hours)

**Lambda parameter errors** (9 files failed in Phase 1):
- apps/api/cache/search_cache.py
- apps/api/database.py
- apps/api/routers/search.py
- apps/classification/semantic_classifier.py
- apps/ingestion/pii/detector.py
- apps/knowledge_builder/coverage/meter.py
- apps/orchestration/src/cbr_system.py
- apps/orchestration/src/reflection_engine.py
- apps/search/hybrid_search_engine.py

**Solution**: Refactor lambdas to named functions

```python
# ❌ Lambda cannot be typed
filtered = filter(lambda x: x > 0, items)

# ✅ Named function with types
def is_positive(x: int) -> bool:
    return x > 0

filtered = filter(is_positive, items)
```

**Import-not-found errors** (missing stubs):
- pymupdf, pymupdf4llm, docx, prometheus_client, sentry_sdk, langfuse

**Solution**: Add type stubs or use `# type: ignore[import]`

```python
import pymupdf  # type: ignore[import-not-found]
```

---

## 📋 Quality Checklist (Before Final Commit)

### Pre-commit Verification

```bash
# 1. MyPy must pass with 0 errors
~/.local/bin/mypy apps/ --config-file=pyproject.toml
# Expected: Found 0 errors in X files

# 2. All tests must pass
pytest tests/ -v
# Expected: 100% pass

# 3. Coverage must be ≥ 85%
pytest --cov=apps --cov-report=term
# Expected: >= 85%

# 4. Linter must pass
ruff check apps/
black --check apps/

# 5. No regression in functionality
pytest tests/integration/ -v
```

### Final Commit

```bash
git add apps/
git commit -m "feat(types): Phase 2 complete - MyPy strict mode 0 errors @CODE:MYPY-001:PHASE2

Complete manual type fixes for remaining 982 errors:
- Fixed assignment errors (Optional types, PEP 484 compliance)
- Fixed union-attr errors (None checks added)
- Fixed return-value errors (accurate return types)
- Fixed arg-type errors (function signatures corrected)
- Fixed attr-defined errors (type guards added)
- Refactored lambdas to typed functions (9 files)
- Added type stubs for missing imports

Progress: 982 → 0 errors (100% complete)
MyPy version: 1.18.2 strict mode
Coverage: 85%+

SPEC: .moai/specs/SPEC-MYPY-001/spec.md
Refs: @SPEC:MYPY-001"
```

---

## 🚀 Phase 3: CI/CD Integration (30 min)

### Verify CI/CD Pipeline

```bash
# Push to remote
git push origin feature/SPEC-MYPY-001

# Monitor CI/CD
gh pr view --web
# OR
gh run watch
```

**Expected CI/CD Results**:
1. ✅ MyPy type check: PASS (0 errors)
2. ✅ Pytest unit tests: PASS
3. ✅ Pytest integration tests: PASS
4. ✅ Coverage: ≥ 85%
5. ✅ Linter (ruff, black): PASS
6. ✅ Build validation: PASS

### PR Ready Transition

```bash
# Convert Draft PR to Ready PR
gh pr ready

# Add reviewers
gh pr edit --add-reviewer @team-lead

# Wait for approval
gh pr checks
```

---

## 📊 Success Metrics

| Metric | Baseline | Phase 1 | Phase 2 Target |
|--------|----------|---------|----------------|
| MyPy Errors | 1,045 | 982 | **0** |
| Files with Errors | 90 | 88 | **0** |
| Type Coverage | ~40% | ~45% | **100%** |
| Test Pass Rate | 100% | 100% | **100%** |
| Coverage | 85% | 85% | **≥ 85%** |

---

## ⚠️ Common Pitfalls

### Pitfall 1: Over-using `Any`
❌ Don't: `def process(data: Any) -> Any`
✅ Do: `def process(data: dict[str, Any]) -> Optional[User]`

### Pitfall 2: Ignoring None checks
❌ Don't: `# type: ignore[union-attr]`
✅ Do: Add proper `if x is not None:` check

### Pitfall 3: Breaking functionality
❌ Don't: Change logic to satisfy mypy
✅ Do: Add types that reflect existing logic

### Pitfall 4: Incomplete Optional handling
❌ Don't: `Optional[X]` without None handling
✅ Do: Always handle None case explicitly

---

## 🆘 Troubleshooting

### Issue: mypy errors increase after fixes
**Cause**: More precise types reveal hidden issues
**Solution**: This is good! Fix the real bugs

### Issue: Tests fail after type changes
**Cause**: Type signatures exposed incorrect usage
**Solution**: Fix the usage, not the types

### Issue: Can't infer correct type
**Solution**: Check runtime behavior, use debugging, or ask for help

---

## 📚 Resources

- MyPy documentation: https://mypy.readthedocs.io/
- PEP 484 (Type Hints): https://peps.python.org/pep-0484/
- Python typing module: https://docs.python.org/3/library/typing.html
- monkeytype: https://github.com/Instagram/MonkeyType

---

**Document Version**: 1.0
**Created**: 2025-10-25
**Phase 1 Commit**: a734726
**Next Action**: Start Phase 2 in new session
