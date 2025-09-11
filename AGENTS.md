# AGENTS.md — Rules for Coding Agents & Humans

## How to run
- Python: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && alembic upgrade head && pytest -q`
- Lint: `ruff check . && ruff format --check .`
- Node: `npm ci && npm test`
- DB: `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_test` (CI와 일치)
- (프로젝트에 해당 없으면 건너뜀)

## Conventions
- Commits: Conventional Commits (feat|fix|chore|refactor|test|docs)
- Branch: feature/* → PR → master
- Don't touch (protected): /infra/, /secrets/, .github/workflows/*

## PR expectations
- Include: before/after summary, failing→passing test logs
- Keep patches minimal, with clear commit messages