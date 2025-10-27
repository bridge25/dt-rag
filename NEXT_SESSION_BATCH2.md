# 📋 Next Session: SPEC-MYPY-001 Phase 2 BATCH2

## 🎯 현재 상태 (Session End: 2025-10-25)

**Date**: 2025-10-25
**Branch**: `feature/SPEC-MYPY-001`
**Last Commit**: `f91c10d` - Phase 2 BATCH1 checkpoint #2 (9/9 files complete)

### Progress Summary
- **Session Start**: 887 errors (87 files) → 778 errors (85 files) at Phase 2 start
- **BATCH1 Progress**: 778 → 601 errors (177 errors fixed, 22.7% improvement)
- **BATCH1 Completion**: 9/9 files (100% COMPLETE) ✅
- **Current Error Count**: 601 errors (79 files)

### BATCH1 Completed Files ✅

| File | Errors Fixed | Status |
|------|------|--------|
| 1. `apps/api/routers/search.py` | 42 → 0 | ✅ |
| 2. `apps/orchestration/src/main.py` | 38 → 0 | ✅ |
| 3. `apps/api/cache/redis_manager.py` | 37 → 0 | ✅ |
| 4. `apps/api/cache/search_cache.py` | 34 → 0 | ✅ |
| 5. `apps/api/routers/search_router.py` | 31 → 0 | ✅ |
| 6. `apps/api/routers/classification_router.py` | 31 → 0 | ✅ |
| 7. `apps/evaluation/test_ragas_system.py` | 30 → 0 | ✅ |
| 8. `apps/api/main.py` | 28 → 0 | ✅ |
| 9. `apps/api/routers/admin/api_keys.py` | 27 → 0 | ✅ |

**Total BATCH1 Impact**: 298 errors → 0 errors (100% of target files fixed)

---

## 🚀 Next Session Quick Start

### Step 1: 현재 상태 확인
```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone

# Verify branch and commit
git log --oneline -5
# Expected: f91c10d fix(types): Phase 2 BATCH1 checkpoint #2

# Verify MyPy error count
~/.local/bin/mypy apps/ --config-file=pyproject.toml | grep "^Found"
# Expected: Found 601 errors in 79 files
```

### Step 2: MoAI-ADK 명령어로 작업 시작
```bash
/alfred:2-run SPEC-MYPY-001 --continue-batch2
```

---

## 📊 BATCH2 작업 계획

### Remaining High-Error Files (Priority Order)

**Target**: Top 10 files with highest error counts

Run this to identify BATCH2 files:
```bash
~/.local/bin/mypy apps/ --config-file=pyproject.toml 2>&1 | \
  grep "error:" | \
  sed -E 's/^([^:]+):.*/\1/' | \
  sort | uniq -c | sort -rn | head -20
```

### Expected BATCH2 Files (based on previous analysis)

These are likely candidates (subject to verification in next session):

1. **apps/core/rag/components/indexing/indexer.py** (~35 errors)
2. **apps/core/rag/query/search.py** (~32 errors)
3. **apps/core/vector_database/vector_db.py** (~30 errors)
4. **apps/api/monitoring/ragas_metrics_extension.py** (~28 errors)
5. **apps/core/data_models/document.py** (~26 errors)
6. **apps/ingestion/loaders/document_loader.py** (~25 errors)
7. **apps/api/llm_config.py** (~24 errors)
8. **apps/core/rag/workflow/workflow_manager.py** (~23 errors)
9. **apps/api/monitoring/sentry_reporter.py** (~22 errors)
10. **apps/ingestion/parsers/pdf_parser.py** (~20 errors)

> **Note**: Actual BATCH2 files will be confirmed based on latest MyPy output when session starts.

### Estimated Progress
- **Current**: 601 errors in 79 files
- **Target after BATCH2**: ~350-400 errors (10 files × ~20-25 errors each)
- **Estimated time**: 3-4 hours
- **Success criteria**: 10 files → 0 errors each

---

## 🛠️ Proven Patterns from BATCH1 (Reusable)

### Pattern 1: Optional Type Annotations
```python
# ❌ Before
def method(param: Dict = None):
    ...

# ✅ After
def method(param: Optional[Dict[str, Any]] = None) -> None:
    if param is None:
        param = {}
    ...
```

### Pattern 2: Union/Attribute Errors (union-attr)
```python
# ❌ Before
search_metrics.record_search(...)

# ✅ After
if search_metrics is not None:
    search_metrics.record_search(...)
```

### Pattern 3: Return Type Annotations
```python
# ❌ Before
async def get_data():
    return {"key": "value"}

# ✅ After
async def get_data() -> Dict[str, Any]:
    return {"key": "value"}
```

### Pattern 4: Function Parameter Annotations (no-untyped-def)
```python
# ❌ Before
async def process(request, config, timeout):
    ...

# ✅ After
async def process(
    request: RequestType,
    config: ConfigType,
    timeout: int
) -> ResultType:
    ...
```

### Pattern 5: Type Assignments
```python
# ❌ Before
data = get_response()

# ✅ After
data: Dict[str, Any] = get_response()
```

### Pattern 6: AsyncGenerator Types
```python
# ❌ Before
async def stream_results(query):
    yield item

# ✅ After
async def stream_results(query: str) -> AsyncGenerator[ItemType, None]:
    yield item
```

### Pattern 7: List Comprehension Type Inference
```python
# ❌ Before
results = [x for x in data]

# ✅ After
results: List[ItemType] = [x for x in data]
```

### Pattern 8: Decorator with Types
```python
# ❌ Before
@decorator
def method(self, arg):
    ...

# ✅ After
@decorator
def method(self, arg: ArgType) -> ReturnType:
    ...
```

---

## 📋 Quality Assurance Checklist

### Before Starting BATCH2
- [ ] Verify branch: `feature/SPEC-MYPY-001`
- [ ] Verify last commit: `f91c10d`
- [ ] Verify error count: ~601 errors in 79 files
- [ ] Review BATCH1 patterns (above)

### During BATCH2 Execution (MoAI-ADK handles)
- [ ] implementation-planner analyzes top 10 files
- [ ] User approves execution plan
- [ ] tdd-implementer fixes files one by one
- [ ] Each file verified: `mypy <file>` → 0 errors
- [ ] git-manager creates checkpoint commits every 3-5 files

### After BATCH2 Completion
- [ ] Full MyPy check: Expected ~350-400 errors
- [ ] All changes committed with @CODE:MYPY-001:PHASE2:BATCH2 tags
- [ ] No regressions detected
- [ ] Ready for BATCH3 or final optimization phase

---

## 🎯 Phase 2 Overall Strategy

### Progress Tracking

| Batch | Status | Files | Errors Fixed | Target Errors |
|-------|--------|-------|--------------|---------------|
| BATCH1 | ✅ COMPLETE | 9/9 | 177 (778→601) | 601 |
| BATCH2 | ⏳ PENDING | 10/10 | ~200 | ~400 |
| BATCH3 | ⏳ PENDING | 10/10 | ~200 | ~200 |
| Final | ⏳ PENDING | Remaining | ~200 | 0 |

### Estimated Total Time
- **BATCH1**: 4 hours ✅ COMPLETE
- **BATCH2**: 3-4 hours
- **BATCH3**: 3-4 hours
- **Final cleanup**: 2-3 hours
- **Total Phase 2**: ~12-15 hours to reach 0 errors

---

## 📚 Reference Files

| File | Purpose |
|------|---------|
| `.moai/specs/SPEC-MYPY-001/spec.md` | Main SPEC document |
| `.moai/specs/SPEC-MYPY-001/phase2-guide.md` | Detailed Phase 2 implementation guide |
| `NEXT_SESSION_BATCH2.md` | This file (next session guide) |
| `mypy_phase2_baseline.txt` | Full MyPy output for reference |
| `error_types.txt` | Common error patterns found |
| `error_files.txt` | List of files with error counts |

---

## 🚨 Important Reminders

### DO ✅
- **Use MoAI-ADK command**: `/alfred:2-run SPEC-MYPY-001 --continue-batch2`
- **Trust the workflow**: Let agents handle analysis, execution, and commits
- **Approve when asked**: Review and approve implementation-planner's plan
- **Save this file**: Keep this guide for reference

### DON'T ❌
- **DON'T manually edit files**: MoAI-ADK does this automatically
- **DON'T run mypy directly**: Agents will run verification
- **DON'T skip agents**: Always use the full MoAI-ADK workflow
- **DON'T use `# type: ignore`**: Fix errors properly with specific error codes
- **DON'T force-push**: Keep a clean commit history

---

## 🔄 Workflow Summary

### Phase 2 TDD Cycle (Repeated for each BATCH)

```
BATCH1 (9 files, 298 errors)
├─ implementation-planner: Analyze 9 files
├─ User approval
├─ tdd-implementer: Fix RED → GREEN → REFACTOR
├─ git-manager: Create checkpoint commits
└─ Quality gate: Verify 0 errors per file

BATCH2 (10 files, ~200 errors)
├─ implementation-planner: Analyze 10 files
├─ User approval
├─ tdd-implementer: Fix all 10 files
├─ git-manager: Create checkpoint commits
└─ Quality gate: Verify all at 0 errors

BATCH3 + Final (remaining files)
├─ Repeat same cycle
├─ Adjust batch sizes as needed
└─ Complete when total errors = 0
```

---

## 🎓 Learning from BATCH1

**What Worked Well**:
1. ✅ Checkpoint commits every 3 files kept history clear
2. ✅ Proven patterns applied consistently across files
3. ✅ Early MyPy runs verified fixes immediately
4. ✅ TAG tracking (@CODE:MYPY-001:PHASE2:BATCH1) maintained traceability
5. ✅ Quality gates (0 errors per file) prevented regressions

**Key Success Factors**:
- Batch strategy (9 files at a time) was optimal
- Consistent patterns reduced implementation time
- Clear checkpoint commits aid future debugging
- Verification after each file ensured quality

**For BATCH2**:
- Continue batch size of 10 files
- Apply same proven patterns
- Maintain checkpoint commit frequency
- Keep verification strict (0 errors threshold)

---

## 💡 Why MoAI-ADK Workflow?

**Benefits**:
1. **Systematic**: implementation-planner ensures thorough analysis
2. **Automated**: tdd-implementer applies patterns consistently
3. **Verified**: Each file checked with MyPy before moving on
4. **Traceable**: git-manager creates structured commits with TAGs
5. **Efficient**: Takes 3-4 hours per batch vs 6-8 hours manual

**Comparison**:
- ✅ MoAI-ADK: Structured, verified, traceable, fast
- ❌ Manual: Inconsistent, hard to track, slower, error-prone

---

## 📞 Contact & Support

If BATCH2 encounters issues:
1. Document the error with MyPy output
2. Check error pattern against BATCH1 reference patterns
3. Run `/alfred:2-run SPEC-MYPY-001 --continue-batch2` again
4. Escalate to debug-helper if pattern not recognized

---

## 🏁 Success Criteria (BATCH2)

- ✅ All 10 target files: 0 MyPy errors each
- ✅ Total errors: 601 → ~350-400
- ✅ All commits tagged: @CODE:MYPY-001:PHASE2:BATCH2
- ✅ No regressions in previously fixed files
- ✅ Ready to proceed to BATCH3

---

**Last Updated**: 2025-10-25 (Session End)
**Status**: Ready for Next Session
**Next Command**: `/alfred:2-run SPEC-MYPY-001 --continue-batch2`
**Estimated Start**: Any time after this session

---

*This guide will be used at the start of the next session. Ensure all commands are run from the correct directory and on the correct branch.*
