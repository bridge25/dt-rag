# Quick Start Guide: Import Validation Workflow

**@DOC:CICD-001**

## 🚀 Immediate Next Steps

### 1. Commit and Push (1 minute)

```bash
# Add new files
git add .github/workflows/import-validation.yml
git add .moai/specs/SPEC-CICD-001/manual-testing-guide.md
git add .moai/specs/SPEC-CICD-001/phase1-implementation-summary.md
git add .moai/specs/SPEC-CICD-001/quick-start.md

# Commit with proper message
git commit -m "feat(cicd): add import validation workflow (SPEC-CICD-001)

Implements Phase 1 of SPEC-CICD-001:
- Stage 1: Python syntax validation (compileall)
- Stage 2: Alembic migration validation (dry-run)
- Stage 3: API import validation

This workflow prevents import errors from reaching production
by validating all Python imports in CI/CD pipeline.

Refs: @CODE:CICD-001"

# Push to feature branch
git push origin feature/SPEC-CICD-001
```

### 2. Observe GitHub Actions (2 minutes)

1. Go to: https://github.com/[your-repo]/actions
2. Find: "Import Validation" workflow
3. Watch: Real-time execution logs
4. Verify: All 3 stages pass ✅

### 3. Create Pull Request (1 minute)

**GitHub UI**:
- Click: "Pull requests" → "New pull request"
- Base: `master`
- Compare: `feature/SPEC-CICD-001`
- Title: `feat(cicd): add import validation automation (SPEC-CICD-001)`
- Description:

```markdown
## Summary
Implements automated Python import validation in CI/CD pipeline to prevent production incidents.

## Changes
- Added `.github/workflows/import-validation.yml` (3-stage validation)
- Added manual testing guide and documentation

## Validation
This workflow would have caught today's `env_manager.py` syntax error before deployment.

## Testing
- [x] Workflow triggers on push
- [x] All 3 stages execute successfully
- [ ] Manual error testing pending

## Related
- SPEC: `.moai/specs/SPEC-CICD-001/spec.md`
- Implementation: `.moai/specs/SPEC-CICD-001/phase1-implementation-summary.md`
- Testing: `.moai/specs/SPEC-CICD-001/manual-testing-guide.md`

Refs: @CODE:CICD-001
```

---

## 📋 What Was Implemented

### File Created
`.github/workflows/import-validation.yml` (@CODE:CICD-001)

### 3-Stage Validation
1. **compileall**: Syntax errors (quotes, colons, indentation)
2. **alembic**: Migration script imports (dry-run)
3. **API import**: FastAPI application imports

### Trigger Events
- Push to `master`
- Push to `feature/**` branches
- Pull requests to `master`

---

## 🎯 Real-world Impact

### Before This Workflow
❌ `env_manager.py` syntax error → deployed to production → 26 test failures

### After This Workflow
✅ `env_manager.py` syntax error → caught in CI → PR blocked → fixed before merge

---

## 🧪 Manual Testing (Optional)

See: `.moai/specs/SPEC-CICD-001/manual-testing-guide.md`

**3 Test Scenarios**:
1. Normal code (should pass)
2. Syntax error (should fail at Stage 1)
3. Import error (should fail at Stage 3)

---

## 📊 Expected Results

### GitHub Actions Output
```
✅ Import Validation

  ✓ Checkout code
  ✓ Set up Python 3.11
  ✓ Install dependencies
  ✓ Stage 1: Python 구문 검증 완료
  ✓ Stage 2: Alembic 마이그레이션 검증 완료
  ✓ Stage 3: API import 검증 완료
  ✓ 모든 import 검증 단계 통과

Total time: ~2-3 minutes
```

### PR Status
```
✅ All checks have passed
   Import Validation — Passed in 2m 34s
```

---

## 🔧 Troubleshooting

### Workflow not running?
1. Check: GitHub repository → Settings → Actions → "Allow all actions"
2. Check: Workflow file in `.github/workflows/` directory
3. Check: Branch name matches trigger pattern (`master`, `feature/**`)

### Stage 2 (Alembic) failing?
1. Check: `alembic==1.16.4` in `requirements.txt`
2. Check: `alembic.ini` file exists
3. Check: Migration files are valid Python

### Stage 3 (API) failing locally but passing in CI?
1. Check: `.env` file in local environment
2. Add: Required environment variables to GitHub Secrets
3. Update: Workflow to use `env:` section if needed

---

## 📈 Next Phases

**Phase 2** (P1): Pre-commit Hook
- Local validation before commit
- Faster feedback loop

**Phase 3** (P2): Pytest Fixture
- Validation before test execution
- Consistent test environment

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `spec.md` | Requirements (EARS format) |
| `plan.md` | Implementation strategy |
| `phase1-implementation-summary.md` | Detailed implementation notes |
| `manual-testing-guide.md` | Testing procedures |
| `quick-start.md` | This file (quick reference) |

---

## ✅ Completion Checklist

- [x] Workflow file created (`.github/workflows/import-validation.yml`)
- [x] @CODE:CICD-001 TAG added
- [x] 3 validation stages implemented
- [x] Documentation completed
- [ ] Committed and pushed to feature branch
- [ ] GitHub Actions execution verified
- [ ] Pull request created
- [ ] Manual testing completed (optional)
- [ ] PR merged to master

---

**Time to complete**: ~5 minutes (commit → push → PR)
**Validation time**: ~2-3 minutes (GitHub Actions execution)
**Total**: ~8 minutes to full deployment

---

**문서 작성자**: tdd-implementer agent
**최종 수정일**: 2025-01-24
**관련 TAG**: @CODE:CICD-001, @DOC:CICD-001
