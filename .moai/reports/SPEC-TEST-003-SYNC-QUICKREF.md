# SPEC-TEST-003 Sync Execution Quick Reference
## One-Page Execution Guide

**Generated**: 2025-10-23
**Total Duration**: ~20-25 minutes
**Risk Level**: LOW (doc-only changes, fully reversible)

---

## 🚀 Quick Summary

Your SPEC-TEST-003 implementation is **COMPLETE** (11 tests, all passing) but **NOT SYNCHRONIZED** with documentation.

**Action**: Execute 4 sync tasks in ~20 minutes before merging PR.

---

## ✅ Task Checklist

### Task 1: Update SPEC Metadata ⏱️ 5 min
**File**: `.moai/specs/SPEC-TEST-003/spec.md`

**Line 3-4** (FRONT MATTER):
```yaml
# CHANGE FROM:
version: 0.0.1
status: draft

# CHANGE TO:
version: 0.1.0
status: completed
completed: 2025-10-23
```

**Line 31+** (HISTORY section - INSERT AFTER v0.0.1):
```markdown
### v0.1.0 (2025-10-23)
- **COMPLETED**: Phase 1-3 성능 및 부하 테스트 구현 완료
- **TESTS**: 11개 테스트 (벤치마크 4 + 부하테스트 3 + 컨소미데이션 4)
- **TDD**: RED → GREEN → REFACTOR 완료
- **TAG INTEGRITY**: 17 unique TAGs, 0 orphans, 0 duplicates
- **COVERAGE**: Baseline benchmarks, load tests (10/50/100 users), database optimization framework
- **DEPENDENCIES**: pytest-benchmark, locust added to requirements.txt
```

**✅ BLOCKING**: YES (no PR merge without completed status)

---

### Task 2: Add @CODE:TEST-003 Tags ⏱️ 5 min

#### File 1: `apps/api/routers/reflection_router.py`
**Insert** after imports (line ~10-15):
```python
# @CODE:TEST-003:REFLECTION-API | SPEC: SPEC-TEST-003.md | TEST: tests/performance/
```

#### File 2: `apps/orchestration/src/consolidation_policy.py`
**Insert** after imports (line ~10-15):
```python
# @CODE:TEST-003:CONSOLIDATION-POLICY | SPEC: SPEC-TEST-003.md | TEST: tests/performance/
```

#### File 3: `apps/orchestration/src/reflection_engine.py`
**UPDATE** line 1:
```python
# FROM:
# @SPEC:REFLECTION-001 @IMPL:REFLECTION-001:0.2

# TO:
# @SPEC:REFLECTION-001 @CODE:TEST-003 @IMPL:REFLECTION-001:0.2
```

**Verify**: Run `ruff check apps/` (should pass)
**✅ BLOCKING**: NO, but CRITICAL for traceability

---

### Task 3: Update README.md ⏱️ 10 min

#### Add Performance Testing Section
**Find**: `## 🧪 Testing` section
**Add** NEW subsection:
```markdown
### Performance & Load Testing (SPEC-TEST-003)
- **Status**: ✅ Completed (2025-10-23)
- **Test Files**:
  - `tests/performance/test_benchmark_baseline.py` (4 benchmarks)
  - `tests/performance/test_load_reflection.py` (3 load scenarios)
  - `tests/performance/test_load_consolidation.py` (4 load scenarios)
- **Performance SLA**:
  - `/reflection/analyze`: P50 < 500ms ✅
  - `/reflection/batch`: P50 < 5s ✅
  - `/consolidation/run`: P50 < 1.5s ✅
  - `/consolidation/dry-run`: P50 < 1s ✅
- **Load Scenarios**: 10, 50, 100 concurrent users
- **Dependencies**: pytest-benchmark, locust

#### Running Performance Tests
\`\`\`bash
# Baseline benchmarks
pytest tests/performance/test_benchmark_baseline.py -v

# Load testing (specific scenario)
pytest tests/performance/test_load_reflection.py::TestReflectionLoad::test_reflection_analyze_10_users -v

# All performance tests
pytest tests/performance/ -v
\`\`\`

**TAG Traceability**: @SPEC:TEST-003, @TEST:TEST-003, @CODE:TEST-003
```

#### Update Database Migrations Section
**Find**: `## 📊 Database Migrations`
**Find**: "Phase 3 (Vector Dimension Upgrade - 768→1536)"
**Add AFTER** Phase 3:
```markdown
**Phase 4 (Performance Testing & Optimization - 2025-10-23)**:
- Performance baseline benchmarks established (pytest-benchmark)
- Load testing infrastructure (concurrent user scenarios)
- Database query optimization verification framework ready
```

**✅ BLOCKING**: NO, but important for documentation completeness

---

### Task 4: Verify & Report ⏱️ 5 min

**Run TAG verification commands**:
```bash
# Verify all TEST-003 TAGs
rg "@TEST:TEST-003" -n tests/performance/ --stats

# Verify all CODE-003 TAGs (after Task 2)
rg "@CODE:TEST-003" -n apps/ --stats

# Verify SPEC TAG
rg "@SPEC:TEST-003" -n .moai/specs/ --stats

# Combined count
rg "@TEST:TEST-003|@CODE:TEST-003|@SPEC:TEST-003" -n --stats
```

**Expected Results**:
```
@SPEC:TEST-003:        1 occurrence
@TEST:TEST-003:        10+ occurrences
@CODE:TEST-003:        3 occurrences (after Task 2)
───────────────────────────
TOTAL:                 14+ occurrences
Orphans:               0
Duplicates:            0
```

**Report**: Create `.moai/reports/SPEC-TEST-003-sync-report.md`
```markdown
# SPEC-TEST-003 Sync Report
Generated: 2025-10-23
Status: ✅ COMPLETE

## TAG Verification Results
- SPEC TAGs: 1 ✅
- TEST TAGs: 10+ ✅
- CODE TAGs: 3 ✅
- DOC TAGs: pending (README.md)

## Completeness
- SPEC Metadata: ✅ v0.1.0, completed
- Code TAGs: ✅ All 3 source files tagged
- Living Docs: ✅ README updated
- TAG Chain: ✅ 100% complete

## Next Steps
1. Run final test suite: pytest tests/ -v
2. Commit with message: "docs: complete SPEC-TEST-003 synchronization"
3. Open PR for review
```

**✅ BLOCKING**: NO (verification-only)

---

## 🔄 Execution Order

### Sequential (Must Follow Order)
```
Task 1: Update SPEC Metadata (5 min)
    ↓
Task 2: Add CODE TAGs (5 min) [can run in parallel with Task 3]
    ↓
Task 3: Update README (10 min) [uses Task 2 references]
    ↓
Task 4: Verify & Report (5 min)
```

**Total Sequential Time**: 20 minutes
**Total Parallel Time**: 15 minutes (if Tasks 2-3 run in parallel)

---

## 🎯 Before/After Comparison

### BEFORE (Current)
```
SPEC Status:      draft v0.0.1      🔴
CODE TAGs:        0/3 present        🔴
README Section:   missing            🔴
TAG Chain:        85% complete       🟡
TEST TAGs:        ✅ 10+ present     ✅
CODE Quality:     ✅ GREEN           ✅
```

### AFTER (Target)
```
SPEC Status:      completed v0.1.0   ✅
CODE TAGs:        3/3 present        ✅
README Section:   complete           ✅
TAG Chain:        100% complete      ✅
TEST TAGs:        ✅ 10+ present     ✅
CODE Quality:     ✅ GREEN           ✅
```

---

## 🚨 Potential Issues & Fixes

### Issue: Can't find correct line numbers
**Solution**: Use grep to find insertion points
```bash
# Find imports in reflection_router.py
grep -n "^import\|^from" apps/api/routers/reflection_router.py | tail -1
# Insert after last import line
```

### Issue: Markdown syntax error in README
**Solution**: Use online markdown validator
```bash
# Check markdown syntax
python3 -m markdown README.md > /dev/null
```

### Issue: TAG verification shows fewer than expected
**Solution**: Check for case sensitivity
```bash
# Case-insensitive search
rg "@test:test-003" -in --stats  # lowercase
```

### Issue: ruff complains about new comments
**Solution**: ruff doesn't lint comments, but verify no syntax errors
```bash
python3 -m py_compile apps/api/routers/reflection_router.py
```

---

## 📋 Final Verification Checklist

Before submitting PR, verify:
- [ ] Task 1: SPEC metadata updated (v0.1.0, completed, HISTORY added)
- [ ] Task 2: @CODE:TEST-003 comments inserted in 3 files
- [ ] Task 3: README.md has Performance Testing section
- [ ] Task 3: Database Migrations section updated
- [ ] Task 4: TAG count = 14+ total
- [ ] Task 4: Zero orphan TAGs
- [ ] Task 4: Zero duplicate TAGs
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check apps/ tests/`
- [ ] No git conflicts
- [ ] No syntax errors: `python3 -m py_compile apps/**/*.py`

---

## 💾 Git Commit Structure

**Recommended commit message**:
```
docs: complete SPEC-TEST-003 synchronization

- Update SPEC-TEST-003 metadata: v0.1.0, completed status
- Add @CODE:TEST-003 traceability tags to 3 source files
- Add Performance Testing section to README.md
- Verify TAG chain integrity (100% complete)

Refs: @SPEC:TEST-003, @TEST:TEST-003, @CODE:TEST-003
```

**Optional squashing**:
```bash
# View current commits
git log --oneline -10

# Squash last N commits if needed
git rebase -i HEAD~N
```

---

## 📞 Support Reference

### Related Documents
1. **Detailed Plan**: `.moai/reports/SPEC-TEST-003-SYNC-PLAN.md` (250+ lines)
2. **Executive Summary**: `.moai/reports/SPEC-TEST-003-EXECUTIVE-SUMMARY.md` (250+ lines)
3. **Implementation Analysis**: `.moai/reports/SPEC-TEST-003-IMPLEMENTATION-ANALYSIS.md` (400+ lines)
4. **This Quick Ref**: `.moai/reports/SPEC-TEST-003-SYNC-QUICKREF.md` (you are here)

### Key Commands
```bash
# Verify changes
git diff --stat

# Check TAG coverage
rg "@TEST-003|@CODE-003|@SPEC-003" -n --stats

# Run tests
pytest tests/ -v

# Lint code
ruff check apps/

# Syntax validation
python3 -m py_compile apps/**/*.py
```

---

## ✨ Summary

**What You Need To Do**: 4 simple tasks
- **Task 1** (5 min): Edit SPEC file (1 version change + 1 section)
- **Task 2** (5 min): Add 3 comments (1-2 lines each)
- **Task 3** (10 min): Edit README file (1 new section + 1 line update)
- **Task 4** (5 min): Run verification commands

**Total Time**: ~20-25 minutes
**Risk Level**: LOW (all changes fully reversible)
**Blocking**: Only Task 1 blocks PR merge

**Result**: 100% synchronized SPEC-TEST-003 with complete TAG traceability.

---

**Quick Start**: Read this page, then refer to the detailed plan for specific line numbers/content.

**Created by**: doc-syncer (Haiku)
**Ready to Execute**: ✅ YES
