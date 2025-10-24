# SPEC-CICD-001 Sync Plan - Quick Reference

**Status**: Ready for Execution
**Time to Complete**: ~1 hour (execution) + 4-24 hours (review)
**Complexity**: Low (document sync + index update + PR handling)

---

## At a Glance

| Item | Status | Action |
|------|--------|--------|
| Implementation | ✅ Complete | 3 files created + tested |
| Living Docs Sync | ⏳ Pending | Update README + tags.json |
| PR Creation | ⏳ Pending | Create PR to master |
| TAG Index | ⏳ Pending | Add CICD-001 entry |
| SPEC Status | ⏳ Pending | Keep "draft" (→ "active" post-merge) |
| Uncommitted Files | ⚠️ Decision | Stash & handle separately |

**Integrity Score**: 88/100 (Excellent)
**Next Gate**: Manual GitHub Actions workflow verification

---

## 5-Step Execution Plan

### Step 1: Stash Uncommitted Changes (2 min)
```bash
git stash  # Preserves .claude/settings, Dockerfile.api, main.py changes
```

### Step 2: Update Living Documents (15 min)

**2a. README.md** - Add SPEC-CICD-001 to completed SPECs section:
```markdown
- ✅ SPEC-CICD-001: CI/CD Import 검증 자동화 (Phase 1 complete)
  - GitHub Actions workflow for import validation
  - Status: Active, Phase 2-3 planned
```

**2b. .moai/indexes/tags.json** - Add CICD-001 entry:
```json
{
  "spec_id": "CICD-001",
  "spec_file": ".moai/specs/SPEC-CICD-001/spec.md",
  "status": "draft",
  "version": "0.0.1",
  "tags": [
    {"type": "SPEC", "id": "CICD-001", "count": 1, "references": [...]},
    {"type": "PLAN", "id": "CICD-001", "count": 1, "references": [...]},
    {"type": "CODE", "id": "CICD-001", "count": 1, "references": [...]},
    {"type": "DOC", "id": "CICD-001", "count": 2, "references": [...]}
  ]
}
```

**2c. Commit & Push**:
```bash
git add README.md .moai/indexes/tags.json
git commit -m "docs: update living documents for SPEC-CICD-001 Phase 1"
git push origin feature/SPEC-CICD-001
```

### Step 3: Create PR (5 min)
```bash
gh pr create \
  --title "feat(cicd): add import validation automation (SPEC-CICD-001)" \
  --body "Implements Phase 1 of SPEC-CICD-001 CI/CD import validation automation" \
  --base master \
  --head feature/SPEC-CICD-001 \
  --draft
```

### Step 4: Verify Workflow (5 min)
- Go to GitHub Actions tab
- Confirm workflow runs on push
- Check all 3 stages pass:
  - ✅ Python syntax validation
  - ✅ Alembic migration validation
  - ✅ API import validation

### Step 5: Set PR to Ready for Review (1 min)
- Click "Ready for review" button on PR
- Add comments if needed
- Request team review

---

## TAG Summary

**Complete Chain** (5 of 6 complete, Phase 3 pending):

```
@SPEC:CICD-001 ──┬─→ @CODE:CICD-001 (import-validation.yml)
                 ├─→ @DOC:CICD-001 (2 files: manual-testing-guide.md, phase1-implementation-summary.md)
                 ├─→ @PLAN:CICD-001 (plan.md)
                 └─→ @ACCEPTANCE:CICD-001 (acceptance.md)
                      │
                      └─→ @TEST:CICD-001 (PENDING - Phase 3)
```

---

## Key Files Created

| File | PATH | TAG | Status |
|------|------|-----|--------|
| GitHub Actions Workflow | `.github/workflows/import-validation.yml` | @CODE:CICD-001 | ✅ Complete |
| Manual Testing Guide | `.moai/specs/SPEC-CICD-001/manual-testing-guide.md` | @DOC:CICD-001 | ✅ Complete |
| Implementation Summary | `.moai/specs/SPEC-CICD-001/phase1-implementation-summary.md` | @DOC:CICD-001 | ✅ Complete |
| SPEC Document | `.moai/specs/SPEC-CICD-001/spec.md` | @SPEC:CICD-001 | ✅ Complete |
| Plan Document | `.moai/specs/SPEC-CICD-001/plan.md` | @PLAN:CICD-001 | ✅ Complete |
| Acceptance Criteria | `.moai/specs/SPEC-CICD-001/acceptance.md` | @ACCEPTANCE:CICD-001 | ✅ Complete |

---

## Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Include uncomitted files in PR? | NO (Stash) | Separate concerns for cleaner PR history |
| SPEC status: draft→active? | Keep "draft" until merge | Signals ongoing Phase 2-3 work |
| Create optional quickref guide? | Deferred | Can add post-merge if needed |
| Merge strategy? | Squash merge | Single commit for cleaner history |

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Workflow YAML syntax error | Low | Pre-validated before commit |
| Missing .env variables for Alembic | Medium | Using --sql flag (dry-run) |
| Import path issues (cross-platform) | Low | Workflow runs on ubuntu-latest |
| TAG index JSON corruption | Very Low | Validate JSON syntax post-edit |

**Overall**: ✅ **LOW RISK**

---

## Commands Reference

```bash
# Stash uncommitted changes
git stash

# Update and commit living documents
git add README.md .moai/indexes/tags.json
git commit -m "docs: update living documents for SPEC-CICD-001 Phase 1"
git push origin feature/SPEC-CICD-001

# Create PR
gh pr create \
  --title "feat(cicd): add import validation automation (SPEC-CICD-001)" \
  --body "Implements Phase 1: GitHub Actions CI/CD import validation workflow" \
  --base master \
  --head feature/SPEC-CICD-001 \
  --draft

# Validate TAG integrity
rg "@.*:CICD-001" -n --stats

# Validate JSON
python3 -c "import json; json.load(open('.moai/indexes/tags.json'))"

# Restore changes after merge
git stash pop
```

---

## Success Criteria

- [x] All Phase 1 files created with correct TAGs
- [ ] README.md updated with SPEC-CICD-001 reference
- [ ] .moai/indexes/tags.json updated with CICD-001 entry
- [ ] PR created and GitHub Actions succeeds
- [ ] Team review approval received
- [ ] PR merged to master
- [ ] SPEC status updated to "active" (post-merge)

---

## Timeline

| Step | Duration | Total Time |
|------|----------|-----------|
| Stash changes | 2 min | 2 min |
| Update living docs | 15 min | 17 min |
| Create PR | 5 min | 22 min |
| Verify workflow | 5 min | 27 min |
| Set PR ready | 1 min | 28 min |
| **Team review** | **4-24 hrs** | **4-24 hrs** |
| Merge & cleanup | 5 min | **~29 min + 4-24 hrs** |

---

## Full Plan Details

For comprehensive information, see: `.moai/reports/SPEC-CICD-001-SYNC-PLAN.md`

**Document Sections**:
1. Executive Summary
2. Living Documents Update Strategy
3. TAG Index Refresh
4. SPEC Status Management
5. PR Management Strategy
6. Uncommitted Changes Decision
7. Document Creation Summary
8. Risk Assessment
9. Success Criteria
10. Timeline & Handoff
11. Appendices (file locations, TAG references, commit templates)

---

**Created**: 2025-10-24 | **Status**: Ready for Execution | **Author**: doc-syncer agent
