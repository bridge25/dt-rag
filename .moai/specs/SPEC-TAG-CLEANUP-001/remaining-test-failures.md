# Remaining Test Failures - Post PR #20

**Created:** 2025-11-06 20:30 UTC
**Status:** 📋 Documented for future SPEC
**Context:** After resolving test_search_missing_query hang in PR #20

---

## ✅ PR #20 Success Criteria (Achieved)

- ✅ test_search_missing_query hang resolved (24min → 11sec)
- ✅ TAG-CLEANUP-001 Phase 2 completed
- ✅ Orphan TAGs eliminated (41 → 0)
- ✅ Health Grade improved (F 46.3 → A 85.5)
- ✅ TAG Validation: PASSED
- ✅ Production stability improved (DB session bug fixed)

---

## ❌ Remaining Test Failures (Separate from TAG-CLEANUP-001)

These failures are **unrelated to TAG-CLEANUP-001** and **not caused by our fixes**. They existed before and should be addressed in separate SPECs.

---

## 1. test_hybrid_search.py (5 failures)

### Location
`tests/integration/test_hybrid_search.py`

### Failures
```
FAILED TestHybridSearchE2E::test_hybrid_search_full_flow
FAILED TestHybridSearchE2E::test_vector_search_timeout_fallback
FAILED TestHybridSearchE2E::test_embedding_generation_failure_fallback
FAILED TestHybridSearchE2E::test_feature_flag_off_bm25_only
FAILED TestHybridSearchE2E::test_hybrid_score_ranking
```

### Root Cause
1. **Tests create their own FastAPI app** → dependency override not applied
2. **CaseBank model error**: `TypeError: 'response_text' is an invalid keyword argument`
3. **Need to use `api_client` fixture** instead of `TestClient`

### Fix Approach
- Modify all test methods to accept `api_client` parameter
- Change `TestClient` to `api_client.post()` calls
- Update endpoint paths to `/api/v1/search`
- Fix CaseBank model initialization

### Priority
**Medium** - SPEC-NEURAL-001 tests, not blocking TAG-CLEANUP

### Estimated Effort
30-45 minutes

---

## 2. test_api_endpoints.py /classify (2 failures)

### Location
`tests/integration/test_api_endpoints.py`

### Failures
```
FAILED TestClassifyEndpoint::test_classify_endpoint_exists - assert 404 in [200, 422]
FAILED TestErrorHandling::test_classify_missing_text - assert 404 == 422
```

### Root Cause
**404 Not Found** - `/classify` endpoint routing issue

### Investigation Needed
1. Check if `/classify` endpoint exists in `main.py`
2. Verify router inclusion
3. Check endpoint path (might be `/api/v1/classify`)

### Fix Approach
```python
# Expected: /classify
# Actual: /api/v1/classify?

# Update test to use correct path
response = await api_client.post("/api/v1/classify", ...)
```

### Priority
**High** - Core API endpoint not accessible

### Estimated Effort
15-20 minutes

---

## 3. test_phase3_consolidation.py (5 errors)

### Location
`tests/integration/test_phase3_consolidation.py`

### Errors
```
ERROR TestConsolidationAPI::test_consolidation_run_performance
ERROR TestConsolidationAPI::test_consolidation_summary_performance
ERROR TestConsolidationAPI::test_consolidation_database_verification
ERROR TestConsolidationAPI::test_consolidation_error_handling
ERROR TestReflectionAPI::test_reflection_analyze_valid_case
```

### Root Cause
**Phase 3 functionality errors** - Collection/setup errors

### Investigation Needed
- Check if Phase 3 endpoints are implemented
- Verify database schema for Phase 3 features
- Check test fixtures and dependencies

### Priority
**Low** - Phase 3 feature, not core functionality

### Estimated Effort
1-2 hours (depends on Phase 3 implementation status)

---

## 4. test_consolidation_workflow.py (hang - 22 minutes)

### Location
`tests/integration/test_consolidation_workflow.py`

### Failures
```
FAILED test_full_consolidation_workflow (22min)
FAILED test_dry_run_no_changes
FAILED test_restore_archived_case
```

### Root Cause
**Similar to test_search_missing_query** - potential hang in consolidation logic

### Investigation Needed
1. Check for missing timeouts in consolidation endpoints
2. Verify database connections are released
3. Check for infinite loops or blocking operations

### Fix Approach
- Apply same timeout patterns as test_search_missing_query fix
- Add dependency overrides if needed
- Check async context management

### Priority
**Medium** - Separate hang issue, needs investigation

### Estimated Effort
1-2 hours (similar to test_search_missing_query debug)

---

## 📊 Summary Table

| Test File | Failures | Root Cause | Priority | Effort |
|-----------|----------|------------|----------|--------|
| test_hybrid_search.py | 5 FAILED | api_client fixture needed | Medium | 30-45min |
| test_api_endpoints.py | 2 FAILED | /classify 404 routing | High | 15-20min |
| test_phase3_consolidation.py | 5 ERROR | Phase 3 implementation | Low | 1-2hrs |
| test_consolidation_workflow.py | 3 FAILED | Hang (22min) | Medium | 1-2hrs |
| **Total** | **15 issues** | - | - | **3-5 hours** |

---

## 🎯 Recommended Next Steps

### Option A: Quick Fixes First (Recommended)
1. Fix `/classify` 404 routing (15min) → High impact
2. Fix `test_hybrid_search.py` api_client (30min) → SPEC-NEURAL-001
3. Create separate SPEC for Phase 3 + consolidation hang

**Total Time**: 45 minutes
**Impact**: 7/15 failures resolved

### Option B: Comprehensive Fix
1. All above + Phase 3 investigation (1-2hrs)
2. Consolidation workflow hang debug (1-2hrs)

**Total Time**: 3-5 hours
**Impact**: All 15 failures resolved

### Option C: Document and Defer
1. ✅ Already documented in this file
2. Create SPEC-TEST-FIX-002 for remaining issues
3. Focus on next feature development

**Total Time**: 0 hours
**Impact**: Issues tracked, not blocking TAG-CLEANUP-001

---

## 📝 Proposed SPEC Structure

```
SPEC-TEST-FIX-002: Remaining Test Failures Resolution
├─ Phase 1: Quick Wins (45min)
│  ├─ Fix /classify routing
│  └─ Fix test_hybrid_search api_client
├─ Phase 2: Phase 3 Investigation (1-2hrs)
│  └─ Implement/fix Phase 3 consolidation tests
└─ Phase 3: Consolidation Hang (1-2hrs)
   └─ Debug and resolve 22-minute hang
```

---

## 🔗 References

- **Original Issue**: PR #20 CI/CD failures
- **Resolved**: test_search_missing_query hang
- **Documentation**: `.moai/specs/SPEC-TAG-CLEANUP-001/test-fix-history.md`
- **Commits**: c6165330, b8649221

---

**Last Updated:** 2025-11-06 20:30 UTC
**Status:** Ready for separate SPEC creation
