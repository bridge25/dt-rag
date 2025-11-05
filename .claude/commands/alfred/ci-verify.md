---
name: alfred:ci-verify
description: "CI/CD verification automation - dependency check, local tests, and GitHub Actions monitoring"
# Translations:
# - ko: "CI/CD 검증 자동화 - 의존성 검사, 로컬 테스트, GitHub Actions 모니터링"
# - ja: "CI/CD検証の自動化 - 依存関係チェック、ローカルテスト、GitHub Actionsモニタリング"
# - zh: "CI/CD验证自动化 - 依赖检查、本地测试、GitHub Actions监控"
argument-hint: "[PR-NUMBER] - Optional PR number to monitor (default: current branch PR)"
allowed-tools:
  - Read
  - Bash(python3:*)
  - Bash(pytest:*)
  - Bash(pip:*)
  - Bash(gh:*)
  - Bash(git:*)
  - Task
  - Grep
  - Glob
  - TodoWrite
---

# 🔍 MoAI-ADK CI/CD Verification - Automated quality gate

> **Note**: This command delegates work to specialized agents using the Task tool for efficient parallel execution.

## 🎯 Command Purpose

Automate CI/CD verification workflow to eliminate GitHub Actions runner wait time and catch issues early. Executes local pre-flight checks immediately, then monitors GitHub Actions in the background with automated diagnostics.

**Verify**: $ARGUMENTS (default: current PR)

## 💡 Execution Philosophy: "Local First, Remote Monitor"

`/alfred:ci-verify` eliminates the commit-push-wait cycle by:
- ✅ **Immediate local validation** (2-3 minutes)
- 🔄 **Background CI/CD monitoring** (async)
- 🤖 **Auto-diagnosis on failure** (AI-powered)

---

## 📋 Phase 1: Local Pre-flight Checks (Immediate)

### Step 1.1: Dependency Verification
```bash
# Validate requirements.txt matches actual imports
python3 -m pytest --collect-only 2>&1 | grep "ModuleNotFoundError"

# Check if all dependencies are installed
pip list --format=freeze | grep -f requirements.txt
```

**Delegate to**: `general-purpose` agent
- Tool access: Read, Bash, Grep
- Timeout: 60 seconds
- Output: List of missing dependencies

### Step 1.2: Fast Unit Tests
```bash
# Run only unit tests (exclude integration/e2e)
python3 -m pytest tests/unit -x --tb=short -q
```

**Delegate to**: `general-purpose` agent
- Tool access: Bash(pytest:*)
- Timeout: 3 minutes
- Output: Test results summary

### Step 1.3: Code Quality Checks
```bash
# Optional: Run linters if configured
ruff check . || true
black --check . || true
```

**Delegate to**: `general-purpose` agent (optional)
- Tool access: Bash
- Timeout: 30 seconds
- Output: Lint issues (non-blocking)

---

## 📊 Phase 2: GitHub Actions Monitoring (Background)

### Step 2.1: Identify Current PR
```bash
# Get PR number for current branch
gh pr view --json number -q '.number'

# Or use provided argument
PR_NUMBER=$ARGUMENTS
```

### Step 2.2: Monitor Workflow Status
```bash
# Watch CI/CD status every 10 seconds
gh pr checks $PR_NUMBER --watch --interval 10
```

**Delegate to**: `observability-engineer` agent
- Tool access: Bash(gh:*), Read
- Timeout: 15 minutes
- Output: Real-time status updates

### Step 2.3: Auto-Diagnosis on Failure
```bash
# If workflow fails, analyze logs
gh run view --log-failed | tail -100

# Extract error patterns
grep -E "ModuleNotFoundError|ImportError|FAILED" logs
```

**Delegate to**: `debug-helper` agent
- Tool access: Bash(gh:*), Grep, Read
- Triggered: On workflow failure
- Output: Root cause analysis + fix suggestions

---

## 🔧 Phase 3: Auto-Fix (Optional)

### Step 3.1: Dependency Auto-Fix
If ModuleNotFoundError detected:
```bash
# Add missing package to requirements.txt
echo "missing-package>=1.0.0" >> requirements.txt

# Commit and push
git add requirements.txt
git commit -m "fix: add missing dependency"
git push
```

**Delegate to**: `general-purpose` agent
- Tool access: Edit, Bash(git:*)
- Requires: User approval via AskUserQuestion
- Output: Auto-fix commit

### Step 3.2: Re-trigger CI/CD
```bash
# Create empty commit to re-trigger
git commit --allow-empty -m "chore: re-trigger CI/CD"
git push
```

---

## 📈 Execution Flow

```
User: /alfred:ci-verify 18

Alfred (main):
├─ [Parallel] Launch Phase 1 agents
│  ├─ Task(general-purpose): Dependency check
│  ├─ Task(general-purpose): Unit tests
│  └─ Task(general-purpose): Linters
│
├─ Wait for Phase 1 completion (max 3 min)
│
├─ If Phase 1 ✅ Pass:
│  └─ [Background] Task(observability-engineer): Monitor GitHub Actions
│     ├─ Poll every 10 seconds
│     ├─ If ✅ Pass: Report success
│     └─ If ❌ Fail: Task(debug-helper): Auto-diagnose
│        └─ AskUserQuestion: Apply auto-fix?
│
└─ If Phase 1 ❌ Fail:
   └─ Report errors immediately (skip GitHub Actions)
```

---

## 🎯 Success Criteria

### Phase 1 (Local)
- ✅ All dependencies installed
- ✅ Unit tests pass (100%)
- ✅ No import errors during pytest collection

### Phase 2 (Remote)
- ✅ GitHub Actions workflow completes
- ✅ All CI/CD jobs pass
- ✅ No test failures or errors

---

## 📝 Output Format

```markdown
## 🔍 CI/CD Verification Report

### Phase 1: Local Checks (Completed in 2m 34s)
- ✅ Dependencies: 45/45 installed
- ✅ Unit Tests: 127 passed
- ⚠️  Linters: 3 warnings (non-blocking)

### Phase 2: GitHub Actions (PR #18)
- 🔄 Status: Running (3m 12s elapsed)
- 📊 Jobs:
  - ✅ TAG Validation (45s)
  - 🔄 dt-rag Pipeline (in progress)

### Next Steps
- Wait for GitHub Actions completion
- Ready to merge if all checks pass
```

---

## 🚨 Error Handling

### Common Issues

**Issue 1: ModuleNotFoundError**
- Auto-detect: Parse pytest collection output
- Auto-fix: Add to requirements.txt
- User approval: Required before commit

**Issue 2: Test Failures**
- Report: Show failed test names
- Delegate: Task(debug-helper) for root cause
- No auto-fix: Requires manual intervention

**Issue 3: GitHub Actions Timeout**
- Wait: Maximum 15 minutes
- Fallback: Provide GitHub Actions URL
- User action: Check browser manually

---

## 🔗 Integration with MoAI Workflow

This command integrates with the standard MoAI workflow:

```bash
/alfred:1-plan SPEC-001    # Plan the feature
/alfred:2-run SPEC-001     # Implement with TDD
/alfred:ci-verify          # ⭐ Verify CI/CD (new!)
/alfred:3-sync             # Sync documentation
```

**Recommended usage**: Run `/alfred:ci-verify` after `/alfred:2-run` and before `/alfred:3-sync` to ensure code quality before documentation updates.

---

## 🎓 Benefits

| Traditional | With /alfred:ci-verify |
|-------------|----------------------|
| Commit → Push → Wait 5-10 min → Check logs → Fix → Repeat | Run locally → Fix immediately → Push once → Background monitor |
| Manual log analysis | AI auto-diagnosis |
| Multiple failed CI/CD runs | Single successful run |
| 30-60 min debugging cycle | 5-10 min total time |

**Time savings**: 70-85% faster iteration cycle

---

## 🎬 Example Usage

```bash
# Verify current branch PR
/alfred:ci-verify

# Verify specific PR
/alfred:ci-verify 18

# After implementation
/alfred:2-run SPEC-001 && /alfred:ci-verify
```

---

## 🎨 Customization

Edit this file to customize behavior:
- Adjust timeout values (default: 15 min)
- Enable/disable auto-fix (default: manual approval)
- Add custom lint commands
- Configure notification webhooks

