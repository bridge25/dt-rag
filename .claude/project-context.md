# Project Context for Claude Code

> **IMPORTANT**: Read this file every time you analyze this project

## 🎯 Development Status (2025-10-14)

**Mode**: Single Developer (NOT team collaboration)
**Integration**: All A/B/C components fully integrated
**Production Ready**: 98%

## ⚠️ Critical Information

### What This Project Is
- **Unified RAG System**: All components (API + Orchestration + Frontend) integrated
- **Single Developer**: Originally planned for team collaboration, now solo-developed
- **Production Ready**: v2.0.0-rc1, fully functional and tested

### What to IGNORE
❌ **DO NOT** reference documents in `docs/archive/team-collaboration/`
❌ **DO NOT** assume A/B/C team separation still exists
❌ **DO NOT** look for separate team branches
❌ **DO NOT** expect PR-based workflow (PR-1, PR-2, etc.)

### What to FOCUS ON
✅ **DO** use actual code in `apps/` directory
✅ **DO** check `git log` for recent commits
✅ **DO** refer to root `README.md` for current status
✅ **DO** assume all components work together

## 📁 Project Structure (Truth)

```
dt-rag/
├── apps/
│   ├── api/              ✅ ACTIVE - FastAPI Backend (Port 8000)
│   ├── orchestration/    ✅ ACTIVE - LangGraph (Port 8001)
│   └── frontend/         ✅ ACTIVE - Next.js Dashboard (Port 3000)
├── packages/
│   └── common-schemas/   ✅ ACTIVE - Shared Pydantic Models (v0.1.3)
├── tests/               ✅ ACTIVE - Integration & E2E Tests
├── migrations/          ✅ ACTIVE - PostgreSQL Migrations
└── docs/
    └── archive/
        └── team-collaboration/  ❌ ARCHIVED - Ignore these docs
```

## 🔍 When Checking Project Status

Always do this:
```bash
# 1. Check actual code
ls -la apps/

# 2. Check recent commits
git log --oneline -10

# 3. Check current status
cat README.md | head -20
```

Never do this:
```bash
# ❌ Don't check archived team docs
cat docs/archive/team-collaboration/*.md

# ❌ Don't look for team-specific branches
git branch | grep "team"
```

## 💡 Quick Facts

- **Ports**: API (8000), Orchestration (8001), Frontend (3000)
- **Database**: PostgreSQL with pgvector
- **Framework**: FastAPI + LangGraph + Next.js 14
- **Models**: 16 Pydantic models in common-schemas
- **Tests**: pytest for backend, Jest for frontend

## 📋 Common Tasks

### Start All Services
```bash
# Terminal 1: API
cd apps/api && uvicorn main:app --reload --port 8000

# Terminal 2: Orchestration
cd apps/orchestration/src && uvicorn main:app --reload --port 8001

# Terminal 3: Frontend
cd apps/frontend && npm run dev
```

### Run Tests
```bash
pytest tests/ -v
```

### Check Database
```bash
alembic current
alembic upgrade head
```

## 🚨 Anti-Patterns to Avoid

1. **Assuming team separation**: All components are integrated
2. **Looking for team PRs**: No PR workflow, direct commits to main
3. **Referencing archived docs**: Use root README.md
4. **Expecting team branches**: Only main branch is active

---

**Last Updated**: 2025-10-14
**Remember**: This is a SINGLE-DEVELOPER project with FULL INTEGRATION.
