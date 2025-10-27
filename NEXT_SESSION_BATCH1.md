# 📋 Next Session: SPEC-MYPY-001 Phase 2 BATCH1 Continuation

## 🎯 Current Status (Session End)

**Date**: 2025-10-25
**Branch**: `feature/SPEC-MYPY-001`
**Last Commit**: `7d8d7df` - Phase 2 BATCH1 checkpoint (database.py complete)

### Progress Summary
- **Starting errors**: 982 errors (88 files)
- **Current errors**: 887 errors (87 files)
- **Errors fixed**: **95 errors** (9.7% improvement)
- **BATCH1 completion**: **1/10 files** (10%)

### Completed Files ✅
1. **apps/api/database.py** - 95 errors → 0 errors (100% COMPLETE)
   - TypeDecorator return types fixed
   - Type helper functions corrected
   - Optional parameters added
   - Async function return types annotated

### Partially Fixed Files 🔄
2. **apps/api/routers/search.py** - ~5 import errors fixed, 42 remaining

---

## 🚀 Next Session Quick Start

### Step 1: Verify Current State

```bash
# Navigate to project
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone

# Check branch and commit
git log --oneline -5
# Expected: 7d8d7df fix(types): Phase 2 BATCH1 checkpoint...

# Verify MyPy error count
~/.local/bin/mypy apps/ --config-file=pyproject.toml | grep "^Found"
# Expected: Found 887 errors in 87 files
```

### Step 2: Continue BATCH1

Run Alfred command to continue:

```bash
/alfred:2-run SPEC-MYPY-001 --continue-batch1
```

Or manually continue with remaining files.

---

## 📊 BATCH1 Remaining Work

### Files to Fix (Priority Order)

**Remaining 9/10 files** (~303 errors estimated):

3. **apps/api/routers/search.py** (42 errors remaining) 🔄
4. **apps/orchestration/src/main.py** (38 errors)
5. **apps/api/cache/redis_manager.py** (37 errors)
6. **apps/api/cache/search_cache.py** (34 errors)
7. **apps/api/routers/search_router.py** (31 errors)
8. **apps/api/routers/classification_router.py** (31 errors)
9. **apps/evaluation/test_ragas_system.py** (30 errors)
10. **apps/api/main.py** (28 errors)
11. **apps/api/routers/admin/api_keys.py** (27 errors)

### Estimated Time Remaining
- **Per file**: 30-60 minutes (based on database.py experience)
- **Total BATCH1**: 4-6 hours for remaining 9 files
- **Target**: 887 → ~630 errors after BATCH1 completion

---

## 🛠️ Fix Patterns (From database.py)

### Pattern 1: TypeDecorator Return Types
```python
# ❌ Before
def process_bind_param(self, value, dialect) -> None:
    if value is not None:
        return json.dumps(value)
    return value

# ✅ After
def process_bind_param(self, value, dialect) -> Optional[str]:
    if value is not None:
        return json.dumps(value)
    return None
```

### Pattern 2: Optional Parameters
```python
# ❌ Before
def hybrid_search(query: str, filters: Dict = None) -> List[Dict]:
    ...

# ✅ After
def hybrid_search(query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    ...
```

### Pattern 3: Function Return Types
```python
# ❌ Before
def get_json_type() -> None:
    if "sqlite" in DATABASE_URL:
        return JSONType()
    return JSON

# ✅ After
def get_json_type() -> Union[type[JSON], JSONType]:
    if "sqlite" in DATABASE_URL:
        return JSONType()
    return JSON
```

### Pattern 4: Union-Attr (None Checks)
```python
# ❌ Before
def process(user: Optional[User]) -> str:
    return user.name  # Error: None has no attribute 'name'

# ✅ After
def process(user: Optional[User]) -> str:
    if user is None:
        return "Unknown"
    return user.name
```

### Pattern 5: Import Suppressions
```python
# For missing library stubs
import asyncpg  # type: ignore[import-untyped]
import pymupdf  # type: ignore[import-not-found]
```

---

## 📋 Execution Checklist

For each remaining file:

- [ ] Read the file
- [ ] Get MyPy errors for that file: `mypy <file> --config-file=pyproject.toml`
- [ ] Apply fix patterns systematically
- [ ] Verify: `mypy <file> --config-file=pyproject.toml` → 0 errors
- [ ] Run related tests: `pytest tests/ -k <module_name>`
- [ ] Move to next file

After all 10 files:
- [ ] Full MyPy check: Expected ~630 errors
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Create BATCH1 completion commit
- [ ] Proceed to BATCH2

---

## 🎯 BATCH1 Success Criteria

- ✅ All 10 files with 0 MyPy errors
- ✅ Total errors: 887 → ~630 (257 more errors fixed)
- ✅ All tests passing
- ✅ No regressions
- ✅ TAG annotations: @CODE:MYPY-001:PHASE2:BATCH1

---

## 📚 Reference Files

| File | Purpose |
|------|---------|
| `.moai/specs/SPEC-MYPY-001/spec.md` | Main SPEC document |
| `.moai/specs/SPEC-MYPY-001/phase2-guide.md` | Detailed Phase 2 guide |
| `error_types.txt` | Error type breakdown |
| `error_files.txt` | Top 20 files by error count |
| `mypy_phase2_baseline.txt` | Full MyPy output (baseline) |

---

## 🚨 Important Notes

1. **Do not skip difficult errors** - Handle all errors in each file
2. **No `# type: ignore` without specific error codes** - Always include `[error-type]`
3. **Test after each file** - Verify no regressions immediately
4. **Commit at BATCH boundaries** - After every 5-10 files
5. **Use established patterns** - Reference database.py fixes

---

## 🔄 After BATCH1 Completion

Next steps (in new session):
1. Review BATCH1 completion (887 → ~630 errors)
2. Proceed to BATCH2 (domain core files)
3. Continue until Phase 2 complete (0 errors)

---

**Last Updated**: 2025-10-25 12:35 KST
**Session**: SPEC-MYPY-001 Phase 2 BATCH1 Checkpoint
**Next Command**: `/alfred:2-run SPEC-MYPY-001 --continue-batch1`
