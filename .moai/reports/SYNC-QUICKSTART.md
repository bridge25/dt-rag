# Document Synchronization - Quick Reference & Command Guide
## dt-rag-standalone (2025-10-24)

**Use this guide to execute the synchronization plan rapidly.**

---

## PHASE A: ORPHAN REMEDIATION (8-10 hours)

### Step 1: CODE-Only Orphans (6 hours)

These 11 TAGs have @CODE but no @SPEC. Create SPEC wrappers:

```bash
# Verify orphan TAGs exist
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone

# Find all orphan CODE TAGs
rg '@CODE:(AUTH-002|BTN-001|BUGFIX-001|CICD|HOOKS-REFACTOR-001|JOB-OPTIMIZE-001|PAYMENT-001|PAYMENT-005|TECH-DEBT-001|TEST-E2E-001|UI-INTEGRATION-001)' -n src/ tests/ apps/

# For each TAG, create SPEC directory:
mkdir -p .moai/specs/SPEC-AUTH-002
mkdir -p .moai/specs/SPEC-BTN-001
mkdir -p .moai/specs/SPEC-BUGFIX-001
# ... etc for all 11
```

**For each CODE orphan:**

1. **Find location of @CODE:ID**
   ```bash
   rg '@CODE:AUTH-002' -n src/
   # Example: src/auth/service.py:15
   ```

2. **Review implementation**
   ```bash
   head -100 src/auth/service.py | grep -A 20 "@CODE:AUTH-002"
   ```

3. **Create minimal SPEC**
   ```bash
   cat > .moai/specs/SPEC-AUTH-002/spec.md << 'EOF'
   ---
   id: AUTH-002
   version: 0.0.1
   status: documented
   created: 2025-10-24
   author: @Alfred (REMEDIATION)
   source: src/auth/service.py:15
   ---

   # AUTH-002: [Feature Name from Code]

   ## HISTORY
   ### v0.0.1 (2025-10-24)
   - **REMEDIATION**: Documented existing @CODE:AUTH-002
   - **SOURCE**: [Copy actual file locations]

   ## Implementation Location
   - @CODE:AUTH-002 in src/auth/service.py
   - Tests: [list test files if exist]

   ## Overview
   [Copy purpose from code comments/docstrings]

   ## Acceptance Criteria
   - Status: DOCUMENTED (retroactive)
   EOF
   ```

### Step 2: TEST-Only Orphans (2 hours)

These 12 TAGs have @TEST but no @SPEC. Decide: **Implement or Remove?**

```bash
# Find all TEST orphans
rg '@TEST:(AGENT-GROWTH-002-PHASE2|BREADCRUMB-INTEGRATION|...)' -n tests/

# Review test content
cat tests/integration/test_breadcrumb_integration.py | head -50
```

**For each TEST orphan:**
- **If valuable test:** Create SPEC → Implement CODE in Phase B
- **If obsolete:** Remove test file and orphan TAG

**Examples to keep (likely valuable):**
- BREADCRUMB-INTEGRATION (UI component)
- CONTAINER-INTEGRATION (layout)
- GRID-INTEGRATION (layout)
- STACK-INTEGRATION (layout)
- TABS-INTEGRATION (component)
- TOOLTIP-INTEGRATION (component)

**Examples to remove (likely obsolete):**
- AGENT-GROWTH-002-PHASE2 (duplicate naming)

### Step 3: DOC-Only Orphans (2 hours)

These 13 TAGs are documentation without corresponding code. Categorize:

```bash
# Find DOC orphans
rg '@DOC:(ARCHITECTURE-001|DEPLOY-001|...)' -n docs/ .moai/

# Check content
cat docs/ARCHITECTURE-001.md
```

**For each DOC orphan:**
- **Reference docs** (architecture, policy): Move to `.moai/memory/`
- **Feature docs** (deploy, integration): Create as full SPEC+CODE in Phase B

**Action for each category:**

```bash
# Move reference docs to memory
mv docs/ARCHITECTURE-001.md .moai/memory/
mv docs/FRAMEWORK-001.md .moai/memory/
# ... etc for policy/architecture/reference docs

# Create SPEC for feature docs
# (These become Phase B implementation tasks)
```

**Result after Phase A:**
- 11 CODE→SPEC created
- 12 TEST→decision made (implement or remove)
- 13 DOC→categorized (move or implement)
- **Orphan rate: 52% → <5%**

---

## PHASE B: COMPLETE CHAINS (12-15 hours)

### Step 1: Implement CODE for 7 Priority Specs (8 hours)

Focus on these in order (highest value first):

```
1. TOOLS-001       - Foundation for others
2. NEURAL-001      - AI/ML core
3. DEBATE-001      - Orchestration
4. REPLAY-001      - State management
5. PLANNER-001     - Planning engine
6. + 2 others from incomplete list
```

**For each:**

1. **Read SPEC file**
   ```bash
   cat .moai/specs/SPEC-TOOLS-001/spec.md
   ```

2. **Review test expectations**
   ```bash
   cat tests/unit/test_tools_001.py
   ```

3. **Execute RED→GREEN→REFACTOR**
   ```bash
   # RED: Tests should already exist, run them
   pytest tests/unit/test_tools_001.py -v
   # (Tests FAIL - that's expected)

   # GREEN: Implement to make tests pass
   # Add @CODE:TOOLS-001 to implementation file
   cat src/tools/executor.py  # Add code here

   # Run again
   pytest tests/unit/test_tools_001.py -v
   # (Tests PASS)

   # REFACTOR: Clean up
   # Keep @CODE:TOOLS-001 tag
   ```

### Step 2: Add @DOC Tags (4 hours)

These 13 TAGs have SPEC+TEST+CODE but no documentation:

```
API-001, AUTH, AGENT-GROWTH-005, CASEBANK-002, CLASS-001,
CONSOLIDATION-001, DATABASE-001, EMBED-001, ENV-VALIDATE-001,
REFLECTION-001, SEARCH-001, SOFTQ-001, TEST-002
```

**For each:**

1. **Create documentation file**
   ```bash
   cat > docs/API-001.md << 'EOF'
   # API-001 Documentation

   @DOC:API-001

   ## Overview
   [Copy from SPEC and CODE docstrings]

   ## Implementation
   - Location: src/api/endpoints/...
   - Test: tests/integration/test_api_001.py

   ## Usage Example
   [Copy from docstring examples]
   EOF
   ```

2. **Add @DOC reference to SPEC**
   ```bash
   # Edit .moai/specs/SPEC-API-001/spec.md
   # Add line: @DOC:API-001 in docs/API-001.md
   ```

3. **Add @DOC reference to CODE**
   ```bash
   # Edit src/api/endpoints/....py
   # Add comment: @DOC:API-001 (links to docs/API-001.md)
   ```

**Result after Phase B:**
- 7 new implementations complete
- 13 documentation links established
- **Chain quality: 17% → 70%+**

---

## PHASE C: DOCUMENTATION SYNC (4-6 hours)

### Step 1: README.md (1.5 hours)

```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone

# 1. Test quick-start commands
pip install -e packages/common-schemas/
cd apps/api && uvicorn main:app --reload --port 8000 &
cd apps/orchestration/src && uvicorn main:app --reload --port 8001 &
cd apps/frontend && npm install && npm run dev &

# 2. Update versions in README
grep -r "version" package.json pyproject.toml setup.py | head -10

# 3. Add git info
git describe --tags  # Latest tag
git log --oneline -5 # Last 5 commits

# 4. Update README with actual output
# Edit README.md:
#   - Update version numbers
#   - Update commit hashes
#   - Verify command paths match actual layout
```

### Step 2: CHANGELOG.md (0.5 hours)

```bash
# Create changelog entry
cat > .moai/reports/CHANGELOG-2025-10-24.md << 'EOF'
# Changelog - 2025-10-24 Synchronization

## [2.0.0-rc1] - 2025-10-24

### Fixed
- @CODE:ROUTER-IMPORT-FIX-001: Router import issues resolved
- @CODE:DATABASE-001: Database initialization fixed
- @CODE:ASYNC-FIX-001: Async driver enforcement

### Added
- @SPEC:CICD-001: CI/CD import validation automation
- @SPEC:TEST-003: Integration test suite
- Pre-commit hook validation

### Changed
- @CODE:DATABASE: Classes restored and verified
- Import paths standardized to relative paths

### Status
- Production readiness: 99%
- TAG chain quality: 17% → 85%+
- Orphan rate: 52% → <5%
EOF
```

### Step 3: tech.md (1.5 hours)

```bash
# Update technology stack details
cat > .moai/project/tech.md << 'EOF'
# Tech Stack (Updated 2025-10-24)

## Backend
- **Framework:** FastAPI [check version]
- **Async Driver:** asyncpg (enforced)
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL + pgvector
- **Validation:** Pydantic v2

## Frontend
- **Framework:** Next.js [check version]
- **UI Library:** React 18
- **Components:** [List actual]
- **Testing:** vitest

## Testing
- **Backend:** pytest
- **Frontend:** vitest
- **E2E:** [specify tool]
- **Performance:** Custom benchmarks in tests/performance/

## Infrastructure
- **API Server:** FastAPI (Port 8000)
- **Orchestration:** LangGraph (Port 8001)
- **Frontend:** Next.js (Port 3000)

[Include actual versions from package files]
EOF
```

### Step 4: structure.md (1 hour)

```bash
# Update actual directory structure
cat > .moai/project/structure.md << 'EOF'
# Project Structure (Verified 2025-10-24)

dt-rag-standalone/
├── .moai/
│   ├── specs/              # 36 SPEC definitions
│   ├── reports/            # Verification + sync reports
│   ├── project/            # Product, structure, tech docs
│   └── memory/             # Development guide
├── apps/
│   ├── api/                # FastAPI (Port 8000)
│   ├── orchestration/      # LangGraph (Port 8001)
│   ├── frontend/           # Next.js (Port 3000)
│   ├── classification/     # ML classifier
│   └── evaluation/         # Golden dataset
├── packages/
│   └── common-schemas/     # Shared models (v0.1.3)
├── tests/                  # Unit, integration, e2e, performance
├── db/                     # Database schemas
├── migrations/             # SQL + Alembic
└── docs/                   # User documentation

[Count actual files: find . -type f | wc -l]
EOF
```

**Result after Phase C:**
- README.md: Tested and current
- CHANGELOG.md: Created with Phase A-C updates
- tech.md: Actual versions documented
- structure.md: Real directory layout shown

---

## PHASE D: AUTOMATION (3-4 hours)

### Step 1: Pre-commit Hook (1.5 hours)

```bash
# Expand existing pre-commit hook
cat >> .claude/hooks/alfred/import-validator.py << 'EOF'

def validate_tags_on_commit():
    """Enforce TAG integrity rules on commit"""

    import subprocess
    import re

    # Check 1: No orphan @CODE TAGs
    result = subprocess.run(
        "rg '@CODE:[A-Z]+-' src/ -n",
        shell=True, capture_output=True, text=True
    )
    code_tags = set(re.findall(r'@CODE:([A-Z]+-\d+)', result.stdout))

    result = subprocess.run(
        "rg '@SPEC:[A-Z]+-' .moai/specs/ -n",
        shell=True, capture_output=True, text=True
    )
    spec_tags = set(re.findall(r'@SPEC:([A-Z]+-\d+)', result.stdout))

    orphans = code_tags - spec_tags
    if orphans:
        print(f"ERROR: Orphan @CODE TAGs found (no matching @SPEC):")
        for tag in orphans:
            print(f"  - {tag}")
        return False

    # Check 2: TAG naming convention
    invalid_tags = []
    for tag in code_tags | spec_tags:
        if not re.match(r'^[A-Z]+-\d{3}$', tag):
            invalid_tags.append(tag)

    if invalid_tags:
        print(f"ERROR: Invalid TAG format (use DOMAIN-NNN):")
        for tag in invalid_tags:
            print(f"  - {tag}")
        return False

    return True

if __name__ == '__main__':
    if not validate_tags_on_commit():
        exit(1)
EOF

# Make executable
chmod +x .claude/hooks/alfred/import-validator.py

# Install hook
cp .claude/hooks/alfred/import-validator.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Step 2: CI/CD Workflow (1.5 hours)

```bash
# Create monthly TAG verification workflow
cat > .github/workflows/tag-integrity-monthly.yml << 'EOF'
name: Monthly TAG Integrity Verification
on:
  schedule:
    - cron: '0 0 1 * *'  # 1st of each month
  workflow_dispatch:

jobs:
  verify-tags:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install ripgrep
        run: sudo apt-get install -y ripgrep

      - name: Scan TAGs
        run: |
          rg '@(SPEC|TEST|CODE|DOC):[A-Z]+-\d{3}' -n > tag-scan.txt
          echo "=== TAG Distribution ==="
          grep -c '@SPEC:' tag-scan.txt || echo "0"
          grep -c '@CODE:' tag-scan.txt || echo "0"
          grep -c '@TEST:' tag-scan.txt || echo "0"
          grep -c '@DOC:' tag-scan.txt || echo "0"

      - name: Generate report
        run: |
          echo "# TAG Integrity Report - $(date)" > TAG_REPORT.md
          echo "" >> TAG_REPORT.md
          rg '@CODE:' src/ -n | wc -l | xargs echo "CODE TAGs:" >> TAG_REPORT.md
          rg '@SPEC:' .moai/specs/ -n | wc -l | xargs echo "SPEC TAGs:" >> TAG_REPORT.md

      - name: Check quality threshold
        run: |
          orphan_count=$(rg '@CODE:' src/ -n | wc -l)
          spec_count=$(rg '@SPEC:' .moai/specs/ -n | wc -l)

          if [ $orphan_count -gt 0 ] && [ $spec_count -gt 0 ]; then
            orphan_rate=$(echo "scale=2; 100 * (1 - $spec_count / $orphan_count)" | bc)
            echo "Orphan rate: ${orphan_rate}%"
            if (( $(echo "$orphan_rate > 25" | bc -l) )); then
              echo "WARN: Orphan rate exceeds 25% threshold"
            fi
          fi

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: tag-integrity-report-$(date +%Y%m%d)
          path: TAG_REPORT.md
EOF

git add .github/workflows/tag-integrity-monthly.yml
git commit -m "chore: add monthly TAG integrity verification workflow"
```

### Step 3: Development Guide (0.5 hours)

```bash
# Add TAG governance section to development guide
cat >> .moai/memory/development-guide.md << 'EOF'

## TAG System Governance (Added 2025-10-24)

### CODE-FIRST Principle
Every @CODE:ID must have a matching @SPEC:ID. This is now enforced by:
1. Pre-commit hook (blocks commits with orphan TAGs)
2. Monthly CI/CD verification (generates report)
3. Manual review during code review process

### TAG Naming Convention
- Format: `DOMAIN-NNN` (e.g., AUTH-001, TOOLS-002)
- Domain: Uppercase letters only (AUTH, API, TOOLS, NEURAL, etc.)
- Number: 3 digits zero-padded (001, 002, ... 999)
- Invalid: AUTH-1, auth-001, AUTH_001 (all will fail validation)

### TAG Lifecycle
1. Create SPEC first (@SPEC:ID)
2. Write tests (@TEST:ID)
3. Implement code (@CODE:ID)
4. Document (@DOC:ID)
5. Update HISTORY section with changes

### Handling Orphans (Retroactively)
If code exists without SPEC (orphan):
1. Create matching .moai/specs/SPEC-ID/spec.md
2. Set version: 0.0.1, status: documented
3. Reference existing @CODE locations
4. Document HISTORY entry
5. This restores CODE-FIRST compliance

EOF
```

**Result after Phase D:**
- Pre-commit hook blocks new orphans
- Monthly CI/CD verification active
- TAG governance documented
- **Zero new orphans allowed going forward**

---

## VERIFICATION CHECKLIST

After each phase, verify results:

### After Phase A (Day 1-2)
```bash
# Check orphan rate
rg '@CODE:' src/ -n | wc -l  # Should decrease
rg '@SPEC:' .moai/specs/ -n | wc -l  # Should increase

# Calculate rate
orphan_count=$(rg '@CODE:' src/ -n | wc -l)
spec_count=$(rg '@SPEC:' .moai/specs/ -n | wc -l)
echo "Orphan rate: $(( (orphan_count - spec_count) * 100 / orphan_count ))%"
# Target: <5%
```

### After Phase B (Day 3-4)
```bash
# Check implementation completeness
rg '@CODE:TOOLS-001' src/ -n | head -5  # Should exist
rg '@CODE:NEURAL-001' src/ -n | head -5  # Should exist

# Check documentation coverage
rg '@DOC:API-001' docs/ -n | head -5  # Should exist
rg '@DOC:EMBED-001' docs/ -n | head -5  # Should exist

# Run tests
pytest tests/unit/ -v --tb=short  # All should pass
pytest tests/integration/ -v --tb=short  # All should pass
```

### After Phase C (Day 5)
```bash
# Verify README works
head -50 README.md  # Quick-start clear?
grep -E "Port [0-9]{4}" README.md  # Ports correct?

# Verify CHANGELOG
cat .moai/reports/CHANGELOG-2025-10-24.md  # Entries present?

# Verify tech.md
grep -E "(FastAPI|Next.js|PostgreSQL)" .moai/project/tech.md
```

### After Phase D (Day 5)
```bash
# Test pre-commit hook
cd /tmp && git init test-repo && cd test-repo
cp .git/hooks/pre-commit /tmp/test-repo/.git/hooks/  # If applicable
# Try committing with orphan TAG and verify rejection

# Verify CI/CD workflow
cat .github/workflows/tag-integrity-monthly.yml | grep "on:"  # Should have schedule
```

---

## COMMAND QUICK REFERENCE

| Task | Command |
|------|---------|
| Find all orphan TAGs | `rg '@CODE:' src/ -n | cut -d: -f3 | sort -u` |
| Find all SPECs | `find .moai/specs/ -name spec.md` |
| Count complete chains | `rg '@SPEC:' .moai/specs/ \| wc -l` |
| View specific TAG locations | `rg '@CODE:AUTH-001' -n src/` |
| Create SPEC directory | `mkdir -p .moai/specs/SPEC-ID` |
| Run tests | `pytest tests/unit/ -v` |
| Generate TAG report | `rg '@(SPEC\|CODE\|TEST\|DOC):' -n > tags.txt` |
| Install pre-commit hook | `cp .claude/hooks/alfred/import-validator.py .git/hooks/pre-commit` |

---

## TROUBLESHOOTING

### "Pre-commit hook blocks my commit"
```bash
# Check what TAGs are causing issue
git diff --cached | grep -E '@(CODE|SPEC):'

# Either:
# 1. Create matching SPEC file and re-commit
# 2. Remove orphan TAG from code comment and re-commit
```

### "Tests fail after implementing CODE"
```bash
# Check if test expectations match implementation
diff -u <(grep "def test_" tests/unit/test_TOOLS-001.py) \
         <(grep "def " src/tools/executor.py)

# Update implementation to match test expectations
# OR update test expectations to match implementation
# Then re-run: pytest tests/unit/test_TOOLS-001.py -v
```

### "Documentation TAG not found"
```bash
# Create @DOC file in docs/
echo "@DOC:API-001" > docs/API-001.md

# Add to SPEC
echo "- @DOC:API-001 in docs/API-001.md" >> .moai/specs/SPEC-API-001/spec.md

# Verify
rg '@DOC:API-001' docs/ -n
```

---

## SUCCESS INDICATORS

✅ **Phase A Complete:**
- All 40 orphans have SPEC definitions or categorized
- Orphan rate: 52% → <5%
- 11 new SPEC files created

✅ **Phase B Complete:**
- 7 new CODE implementations (TOOLS-001, NEURAL-001, etc.)
- 13 @DOC tags added to documentation files
- All tests passing

✅ **Phase C Complete:**
- README.md tested and verified (quick-start works)
- CHANGELOG.md created with 2025-10-24 entries
- tech.md shows actual framework versions
- structure.md shows real directory layout

✅ **Phase D Complete:**
- Pre-commit hook installed and tested
- CI/CD workflow file created
- Development guide updated with TAG governance
- Zero new orphans allowed

✅ **Final State:**
- Chain quality score: 17% → 85%+
- All TAGs traceable and complete
- Living Document synchronized
- Project ready for production deployment

---

**Last Updated:** 2025-10-24
**Estimated Time:** 27-35 hours over 4-5 days
**Next Step:** Execute Phase A

