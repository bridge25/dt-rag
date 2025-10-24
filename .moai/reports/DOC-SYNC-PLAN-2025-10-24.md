# Document Synchronization Plan
## dt-rag-standalone Project

**Report Date:** 2025-10-24
**Project:** dt-rag-standalone
**Project Mode:** Personal
**Location:** `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone`

---

## EXECUTIVE SUMMARY

The dt-rag-standalone project requires comprehensive document synchronization to restore Living Document integrity and TAG traceability. Current state:

| Metric | Value | Status |
|--------|-------|--------|
| Total SPECs | 36 | ✅ Exist |
| Complete TAG chains (S+T+C+D) | 13 (17%) | ⚠️ Low |
| Partial chains (S+T+C, missing D) | 13 (17%) | ⚠️ Incomplete |
| Orphan TAGs (no SPEC) | 40 (52%) | 🔴 Critical |
| Incomplete TDD chains | 11 (14%) | ⚠️ Problematic |
| Project documents | 3 | ✅ Exist (needs update) |

**Overall Chain Quality Score: 17.1% - CRITICAL**

---

## SYNCHRONIZATION STRATEGY

### Recommended Approach: **PHASED HYBRID SYNC**

Given the project's personal mode and CODE-FIRST principle, we will execute:

1. **Phase A: Critical Orphan Remediation** (Immediate)
   - Create SPEC definitions for 40 orphan TAGs
   - Link existing CODE/TEST to new SPECs
   - Restore CODE-FIRST compliance

2. **Phase B: Complete TDD Chains** (High Priority)
   - Implement missing CODE for 11 incomplete specs
   - Add missing TEST suites
   - Repair SPEC+TEST+CODE linearity

3. **Phase C: Documentation Sync** (Medium Priority)
   - Add @DOC tags to 13 partial chains
   - Update Living Documents (README, CHANGELOG, tech.md, structure.md)
   - Synchronize project-level docs with code reality

4. **Phase D: Governance & Automation** (Ongoing)
   - Enforce TAG integrity in CI/CD
   - Create TAG validation pre-commit hooks
   - Schedule monthly verification runs

---

## DETAILED SYNCHRONIZATION PLAN

### Phase A: Critical Orphan Remediation (IMMEDIATE)

**Objective:** Eliminate 40 orphan TAGs and restore CODE-FIRST compliance
**Estimated Effort:** 8-10 hours
**Priority:** 🔴 CRITICAL (blocks all other work)

#### A.1: CODE-Only Orphans (11 TAGs)
**Issue:** Implementation exists without SPEC definition
**Action:** Create minimal SPEC definition that documents existing CODE

**TAGs to remediate:**
```
1. AUTH-002           → Create SPEC-AUTH-002
2. BTN-001            → Create SPEC-BTN-001
3. BUGFIX-001         → Create SPEC-BUGFIX-001
4. CICD               → Create SPEC-CICD (standardize to SPEC-CICD-002)
5. HOOKS-REFACTOR-001 → Create SPEC-HOOKS-REFACTOR-001
6. JOB-OPTIMIZE-001   → Create SPEC-JOB-OPTIMIZE-001
7. PAYMENT-001        → Create SPEC-PAYMENT-001
8. PAYMENT-005        → Create SPEC-PAYMENT-005
9. TECH-DEBT-001      → Create SPEC-TECH-DEBT-001
10. TEST-E2E-001      → Create SPEC-TEST-E2E-001
11. UI-INTEGRATION-001 → Create SPEC-UI-INTEGRATION-001
```

**Per-TAG workflow:**
1. Read @CODE:ID locations in source files
2. Understand implementation intent
3. Create `.moai/specs/SPEC-{ID}/` directory
4. Author minimal SPEC (version: 0.0.1, status: documented)
5. Reference existing @CODE locations
6. Document HISTORY entry

#### A.2: TEST-Only Orphans (12 TAGs)
**Issue:** Tests exist without SPEC or CODE implementation
**Action:** Create SPEC + implement corresponding CODE, OR remove tests if obsolete

**TAGs to remediate:**
```
1. AGENT-GROWTH-002-PHASE2
2. AUTH-002           (matches CODE orphan - synchronize)
3. BREADCRUMB-INTEGRATION
4. BTN-001            (matches CODE orphan - synchronize)
5. CONTAINER-INTEGRATION
6. E2E
7. GRID-INTEGRATION
8. JOB-OPTIMIZE-001   (matches CODE orphan - synchronize)
9. STACK-INTEGRATION
10. TABS-INTEGRATION
11. TOOLTIP-INTEGRATION
12. UI-INTEGRATION-001 (matches CODE orphan - synchronize)
```

**Workflow:**
1. Review test files under `tests/` for each TAG
2. Determine: Is test code valid and worth implementing?
   - YES → Create SPEC + implement CODE
   - NO → Remove test and orphan TAG
3. If implementing: Follow RED→GREEN→REFACTOR with SPEC first

#### A.3: DOC-Only Orphans (13 TAGs)
**Issue:** Documentation exists without corresponding implementation
**Action:** Determine if doc is reference or feature, then reconcile

**TAGs to remediate:**
```
1. ARCHITECTURE-001       (reference doc)
2. DEPLOY-001             (reference doc)
3. FRAMEWORK-001          (reference doc)
4. GITFLOW-POLICY-001     (reference doc)
5. INTEGRATION-001        (reference doc)
6. MISSION-001            (reference doc)
7. MODULES-001            (reference doc)
8. QUALITY-001            (reference doc)
9. STACK-001              (reference doc)
10. STRATEGY-001          (reference doc)
11. TRACEABILITY-001      (reference doc)
12. UPDATE-001            (reference doc)
13. UPDATE-REFACTOR-001   (reference doc)
```

**Decision for each:**
- **If reference doc (architecture, policy):** Move @DOC to `.moai/memory/` or docs/archive/
  - These describe the system, not feature requirements
  - Remove from primary @DOC TAG tracking

- **If feature doc (deploy, integration):** Create full SPEC+TEST+CODE
  - These describe capabilities that should be implemented
  - Add to implementation backlog

**Recommendation:**
- Move 11 reference docs → `.moai/memory/development-guide.md` (meta-documentation)
- Keep only 2-3 critical policy docs as standalone

---

### Phase B: Complete TDD Chains (HIGH PRIORITY)

**Objective:** Resolve 11 incomplete chains + 13 partial chains
**Estimated Effort:** 12-15 hours
**Priority:** 🟡 High (enables production readiness)

#### B.1: Incomplete TDD Chains (11 TAGs with SPEC+TEST but NO CODE)

**Issue:** SPEC drafted and tests written, but implementation not completed

**TAGs:**
```
1. DEBATE-001           [SPEC ✅  TEST ✅  CODE ❌]
2. NEURAL-001           [SPEC ✅  TEST ✅  CODE ❌]
3. PLANNER-001          [SPEC ✅  TEST ✅  CODE ❌]
4. REPLAY-001           [SPEC ✅  TEST ✅  CODE ❌]
5. TOOLS-001            [SPEC ✅  TEST ✅  CODE ❌]
6. UI-DESIGN-001        [SPEC ✅  TEST ✅  CODE ❌]
7. USER-003             [SPEC ✅  TEST ✅  CODE ❌]
+ 4 others with mixed status (IMPORT-ASYNC-FIX-001, EVAL-001, REFACTOR-001, ROUTER-IMPORT-FIX-001)
```

**Action per TAG:**
1. **Review SPEC**: Understand requirements and acceptance criteria
2. **Review TEST**: Verify test suite matches SPEC requirements
3. **Decision:**
   - **If high priority:** Implement CODE following GREEN phase of TDD
   - **If low priority:** Archive SPEC as draft, mark as "deferred"
   - **If obsolete:** Remove both SPEC and TEST, mark in HISTORY

**Recommended Implementation Order:**
1. TOOLS-001 (foundational, blocks other features)
2. NEURAL-001 (AI/ML core)
3. DEBATE-001 (orchestration)
4. REPLAY-001 (state management)
5. PLANNER-001 (planning engine)

#### B.2: Partial Chains (13 TAGs with SPEC+TEST+CODE but NO DOC)

**Issue:** Implementation complete but not documented

**TAGs:**
```
1. API-001
2. AUTH
3. AGENT-GROWTH-005
4. CASEBANK-002
5. CLASS-001
6. CONSOLIDATION-001
7. DATABASE-001
8. EMBED-001
9. ENV-VALIDATE-001
10. REFLECTION-001
11. SEARCH-001
12. SOFTQ-001
13. TEST-002
```

**Action per TAG:**
1. Read SPEC file (understand requirements)
2. Scan CODE files (identify implementation patterns)
3. Create or update corresponding @DOC tag in:
   - README.md (feature summary)
   - `/docs/` subdirectory (detailed documentation)
   - API docs (if REST endpoint)
4. Add @DOC cross-reference in SPEC and CODE

**Documentation Format:**
- For APIs: OpenAPI/Swagger inline documentation
- For modules: Module-level docstrings + README
- For features: Feature guide in `/docs/features/`

---

### Phase C: Living Document Synchronization (MEDIUM PRIORITY)

**Objective:** Update project-level documentation to reflect current state
**Estimated Effort:** 4-6 hours
**Priority:** 🟡 Medium (improves developer experience)

#### C.1: README.md Updates

**Current Status:** Last updated 2025-10-17
**Required Updates:**

1. **Verify Quick Start section accuracy**
   - Test Python environment setup (pip install -e packages/...)
   - Test API server startup (Port 8000)
   - Test Orchestration startup (Port 8001)
   - Test Frontend startup (Port 3000)
   - **Action:** Run through setup sequence, update paths/commands if incorrect

2. **Update Version numbers**
   - Current: v2.0.0-rc1 (API), v1.8.1 (System)
   - Check git tags and package.json for actual versions
   - **Action:** Align to actual deployed versions

3. **Add Architecture Diagram**
   - Current: Text-based diagram
   - **Action:** Add visual ASCII art or reference to structure.md

4. **Document Recent Changes**
   - Last milestone: main→master merge (2025-10-23)
   - **Action:** Add CHANGELOG entries for:
     - database.py restoration (commit 2763d04)
     - CI/CD automation (SPEC-CICD-001)
     - Import validation (SPEC-TEST-002)

5. **Update Status badges**
   - Check CI/CD status: ![staging-smoke](https://github.com/bridge25/Unmanned/actions/workflows/staging-smoke.yml/badge.svg)
   - **Action:** Verify workflow still exists and is passing

#### C.2: CHANGELOG.md Creation or Update

**Current Status:** Does not exist or out of date
**Action:**

1. Create `.moai/reports/CHANGELOG-2025.md` with entries:
   ```
   ## [2.0.0-rc1] - 2025-10-24

   ### Changed
   - database.py classes restored (2763d04)
   - Import validation automation (SPEC-CICD-001)
   - Async database driver enforcement (SPEC-TEST-002)

   ### Fixed
   - Router import issues (SPEC-ROUTER-IMPORT-FIX-001)
   - Execution log table creation (SPEC-TEST-003)

   ### Added
   - Pre-commit hook validation (SPEC-CICD-001 Phase 1)
   - Execution pipeline tests (SPEC-TEST-003)
   ```

2. Reference SPECs with @TAG links

#### C.3: Tech Stack Documentation

**File:** `.moai/project/tech.md`
**Current Status:** Last updated 2025-10-17
**Action:**

1. **Verify Python stack:**
   - FastAPI: Check version in requirements.txt
   - SQLAlchemy + asyncpg: Verify async driver config
   - pgvector: Check PostgreSQL integration
   - Pydantic: Check schema validation setup

2. **Verify TypeScript stack:**
   - Next.js: Check version in package.json
   - Components: List UI component library
   - Testing: Verify vitest configuration

3. **Verify Testing stack:**
   - pytest: Backend unit + integration
   - vitest: Frontend unit
   - Performance benchmarks: Document in tests/performance/

4. **Update Section:**
   - Add tool versions to tech.md
   - Reference actual configuration files
   - Add performance baselines from benchmarks

#### C.4: Project Structure Sync

**File:** `.moai/project/structure.md`
**Current Status:** Last updated 2025-10-17 (template format)
**Action:**

1. Update with ACTUAL directory structure:
   ```
   dt-rag/
   ├── .moai/
   │   ├── specs/              # 36 SPEC definitions
   │   ├── reports/            # Verification + sync reports
   │   ├── project/            # Product, Structure, Tech docs
   │   └── memory/             # Development guide
   ├── apps/
   │   ├── api/                # FastAPI (Port 8000)
   │   ├── orchestration/      # LangGraph (Port 8001)
   │   ├── frontend/           # Next.js (Port 3000)
   │   ├── classification/     # ML classifier
   │   └── evaluation/         # Golden dataset
   ├── packages/
   │   └── common-schemas/     # Shared Pydantic models
   ├── tests/
   │   ├── unit/               # Unit tests (36 files)
   │   ├── integration/        # Integration tests (15 files)
   │   ├── e2e/                # End-to-end tests
   │   └── performance/        # Benchmarks
   ├── migrations/             # SQL + Alembic migrations
   ├── db/                     # Database schemas
   └── docs/                   # User documentation
   ```

2. Add actual file counts and dependencies

3. Reference SPEC-FOUNDATION-001 for system design rationale

---

### Phase D: Governance & Automation (ONGOING)

**Objective:** Prevent future TAG integrity issues
**Estimated Effort:** 3-4 hours initial setup + 30 min/month maintenance
**Priority:** 🟢 Medium (long-term value)

#### D.1: Pre-commit Hook for TAG Validation

**File:** `.claude/hooks/alfred/import-validator.py` (exists, expand for TAG validation)

**New checks to add:**
```python
def validate_tag_on_commit():
    """Enforce TAG naming and completeness rules"""

    # Check 1: No orphan TAGs
    # If @CODE:ID exists, require matching @SPEC:ID

    # Check 2: No duplicate TAG IDs
    # Scan for duplicate @SPEC, @CODE, @TEST, @DOC assignments

    # Check 3: Naming convention
    # Format: @(SPEC|CODE|TEST|DOC):DOMAIN-NNN
    # Accept: AGENT-GROWTH, CICD-001, TEST-E2E-001

    # Check 4: SPEC-first discipline
    # If new @CODE:ID added, require existing @SPEC:ID

    # Block commit if any check fails
    # Provide clear remediation instructions
```

#### D.2: CI/CD Integration

**File:** `.github/workflows/tag-validation.yml`

**New workflow:**
```yaml
name: TAG Integrity Check
on: [pull_request]
jobs:
  validate-tags:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Scan TAGs
        run: |
          rg '@(SPEC|CODE|TEST|DOC):[A-Z]+-\d{3}' -n > tag-scan.txt
          python .moai/scripts/validate_tag_chains.py < tag-scan.txt
      - name: Check orphan rate
        run: |
          orphan_count=$(rg '@CODE:' src/ | wc -l)
          spec_count=$(rg '@SPEC:' .moai/specs/ | wc -l)
          if [ $orphan_count -gt $spec_count ]; then
            echo "ERROR: Orphan rate > 20%"
            exit 1
          fi
      - name: Generate report
        run: python .moai/scripts/generate_tag_report.py
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: tag-integrity-report
          path: .moai/reports/TAG_INTEGRITY_REPORT_*.md
```

#### D.3: Monthly Verification Schedule

**Schedule:** 1st of each month at 00:00 UTC
**Action:** Run `/alfred:3-sync` to generate integrity report
**Threshold:** If orphan rate > 25%, alert project owner

---

## DOCUMENT UPDATE PRIORITY MATRIX

| Document | Complexity | Impact | Time | Priority |
|----------|-----------|--------|------|----------|
| **README.md** | Low | High | 1-2h | 🔴 CRITICAL |
| **CHANGELOG.md** | Low | Medium | 0.5-1h | 🟡 High |
| **tech.md** | Medium | Medium | 1-2h | 🟡 High |
| **structure.md** | Medium | Medium | 1-2h | 🟡 High |
| **40 Orphan SPECS** | High | Critical | 6-8h | 🔴 CRITICAL |
| **11 Incomplete chains** | High | High | 4-6h | 🟡 High |
| **13 Partial chains (@DOC)** | Medium | Medium | 2-3h | 🟡 High |
| **Pre-commit hooks** | Low | High (preventive) | 1-2h | 🟢 Medium |
| **CI/CD integration** | Medium | High (preventive) | 2-3h | 🟢 Medium |

---

## RISK ASSESSMENT

### Critical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Orphan TAGs represent real code** | Medium | Review @CODE locations before creating SPEC; document existing intent |
| **Tests may be obsolete** | Medium | Review test content; validate against running codebase |
| **Documentation gaps large** | Medium | Prioritize high-value docs (README, API) first |
| **Effort underestimated** | High | Start with Phase A (4 hrs), reassess before Phase B |

### Assumptions

1. ✅ All 36 existing SPECs are valid (no removal needed)
2. ✅ CODE-FIRST principle can be retroactively applied (create specs for existing code)
3. ✅ Git history available for understanding implementation intent
4. ✅ Project owner (personal mode) can approve documentation changes without review

---

## EXECUTION ROADMAP

### Week 1: Phase A (Orphan Remediation)
- **Days 1-2:** Analyze 11 CODE-only orphans, create SPEC definitions
- **Days 3-4:** Analyze 12 TEST-only orphans, create SPEC + CODE or remove
- **Day 5:** Reconcile 13 DOC-only orphans, move to memory or implement

**Expected output:** 30-35 new/updated SPEC files, orphan rate reduced to <5%

### Week 2: Phase B (Complete Chains)
- **Days 1-3:** Implement CODE for 7 critical incomplete SPECs (TOOLS-001, NEURAL-001, etc.)
- **Days 4-5:** Add @DOC tags to 13 partial chains

**Expected output:** 7 new CODE modules, 13 documentation updates

### Week 3: Phase C (Documentation Sync)
- **Days 1-2:** Update README.md with accurate quick-start + version info
- **Days 3-4:** Create/update CHANGELOG.md, tech.md, structure.md
- **Day 5:** Final QA on all documentation

**Expected output:** Updated README, CHANGELOG, tech.md, structure.md

### Week 4: Phase D (Governance)
- **Days 1-2:** Create pre-commit hook for TAG validation
- **Days 3-4:** Create CI/CD workflow for monthly verification
- **Day 5:** Document process in development-guide.md

**Expected output:** Automated TAG validation + monthly verification

---

## SUCCESS CRITERIA

### Phase A Success
- ✅ Orphan rate reduced from 52% to <5%
- ✅ All CODE TAGs have matching SPEC definitions
- ✅ All TEST TAGs have matching SPEC definitions
- ✅ All DOC-only TAGs reconciled (moved to memory or implemented)

### Phase B Success
- ✅ All 11 incomplete TDD chains resolved (implemented or archived)
- ✅ All 13 partial chains have @DOC tags
- ✅ TAG quality score improved from 17% to 75%+

### Phase C Success
- ✅ README.md tested (quick-start verified to work)
- ✅ CHANGELOG.md covers all changes since v1.8.0
- ✅ tech.md reflects actual versions and configurations
- ✅ structure.md shows actual directory structure with file counts

### Phase D Success
- ✅ Pre-commit hook blocks orphan TAGs
- ✅ CI/CD workflow runs on every PR
- ✅ Monthly verification schedule established
- ✅ Development guide documents TAG governance

### Overall Success Threshold
- **Chain Quality Score:** 17% → 85%+ (target)
- **Orphan Rate:** 52% → <5%
- **Complete Chains (S+T+C+D):** 13 → 30+
- **Zero blockers for production deployment**

---

## ESTIMATED TOTAL EFFORT

| Phase | Hours | Days | Priority |
|-------|-------|------|----------|
| **A - Orphan Remediation** | 8-10h | 1-2 days | 🔴 CRITICAL |
| **B - Complete Chains** | 12-15h | 2-3 days | 🟡 High |
| **C - Doc Sync** | 4-6h | 1 day | 🟡 High |
| **D - Governance** | 3-4h | 0.5 days | 🟢 Medium |
| **TOTAL** | **27-35h** | **4-6 days** | - |

**Recommended pace:** 6-8 hours/day over 4-5 working days

---

## APPENDIX: TAG REMEDIATION TEMPLATE

### For each orphan TAG, use this template:

```markdown
# SPEC-{DOMAIN}-{NNN} Template

---
id: {DOMAIN}-{NNN}
version: 0.0.1
status: documented
created: 2025-10-24
author: @Alfred (REMEDIATION)
source: [Link to @CODE:ID that triggered remediation]
---

## HISTORY

### v0.0.1 (2025-10-24)
- **REMEDIATION**: Created to document existing @CODE:{DOMAIN}-{NNN}
- **SOURCE**: [List files where @CODE:ID appears]
- **RATIONALE**: [Brief explanation of why code exists]

---

## Overview

This SPEC documents implementation that pre-existed the formal SPEC system.

### Implementation Location
- @CODE:{DOMAIN}-{NNN} in [file path]
- Tests: [test file paths if exist]

### Key Behaviors
[Copy key behaviors from code comments or docstrings]

---

## Acceptance Criteria

### Status: DOCUMENTED (Retroactive)
This SPEC captures existing implementation and does NOT require new work.
```

---

## NEXT STEPS

1. **Review this plan** with project context
2. **Confirm effort estimate** (27-35h realistic?)
3. **Choose start date:** Recommend immediately (blocking other work)
4. **Execute Phase A first:** Should be complete within 1-2 days
5. **Report progress** in `.moai/reports/SYNC-PROGRESS-LOG.md`

---

**Plan Created:** 2025-10-24
**Status:** Ready for execution
**Owner:** @doc-syncer / Alfred
**Next Review:** After Phase A completion

