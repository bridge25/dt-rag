---
id: TECH-001
version: 2.0.1
status: active
created: 2025-10-01
updated: 2025-11-10
author: @tech-lead
priority: medium
---

# dt-rag Technology Stack

## HISTORY

### v2.0.1 (2025-11-10)
- **MERGE**: 백업 파일 병합 완료 (MoAI-ADK 0.22.5 업데이트 후 자동 최적화)
- **AUTHOR**: @Alfred
- **BACKUP_SOURCE**: .moai-backups/backup/ (2025-10-27)
- **REASON**: moai-adk 재초기화 후 사용자 커스터마이징 복원
- **METADATA**: authors → author 필드 변환 (v0.22.5 템플릿 표준)

### v2.0.0 (2025-10-13)
- **LEGACY_ANALYSIS**: 기존 기술 스택 분석 완료 (pyproject.toml, package.json, docker-compose.yml)
- **AUTHOR**: @tech-lead, @sonheungmin
- **UPDATES**: 언어/런타임, 프레임워크, 품질 게이트, 보안, 배포 채널 작성
- **PROJECT_TYPE**: Hybrid Stack (Python 3.9+ Backend, TypeScript 5 Frontend)
- **CONTEXT**: DT-RAG v2.0.0 - Production-Ready Tech Stack

### v0.1.1 (2025-10-17)
- **UPDATED**: Template version synced (v0.3.8)
- **AUTHOR**: @Alfred
- **SECTIONS**: Metadata standardization (single `author` field, added `priority`)

### v0.1.0 (2025-10-01)
- **INITIAL**: 프로젝트 기술 스택 문서 템플릿 생성
- **AUTHOR**: @tech-lead

---

## @DOC:STACK-001 언어 & 런타임

### 주 언어 선택

**Backend**:
- **언어**: Python 3.9+
- **버전**: 3.9, 3.10, 3.11 지원 (pyproject.toml 명시)
- **선택 이유**:
  - FastAPI 비동기 I/O 지원 (asyncio, AsyncSession)
  - ML/AI 생태계 성숙도 (Sentence-Transformers, LangChain, RAGAS)
  - Pydantic 자동 검증 + OpenAPI 문서 자동 생성
  - PostgreSQL asyncpg 드라이버 지원
- **패키지 매니저**: pip + pyproject.toml (setuptools build backend)

**Frontend**:
- **언어**: TypeScript 5.x
- **버전**: TypeScript 5 (package.json 명시)
- **선택 이유**:
  - Next.js 14 App Router와 완벽한 통합
  - 타입 안정성으로 런타임 에러 사전 방지
  - React 18 Server Components 지원
  - Zod 스키마 검증과 타입 추론 통합
- **패키지 매니저**: npm (package-lock.json)

### 멀티 플랫폼 지원

| 플랫폼 | 지원 상태 | 검증 도구 | 주요 제약 |
|--------|-----------|-----------|-----------|
| **Windows** | ✅ 지원 | WSL2 + Docker Desktop | 파일 경로 슬래시 차이 (pathlib 사용 권장) |
| **macOS** | ✅ 지원 | Docker Desktop | M1/M2 ARM 아키텍처 (Docker image 빌드 시간 증가) |
| **Linux** | ✅ 지원 (프로덕션 권장) | Docker Engine | 없음 (네이티브 지원) |

**Docker 기반 통합 환경**:
- PostgreSQL 12+ (pgvector extension)
- Redis 7-alpine
- 모든 플랫폼에서 동일한 환경 보장 (docker-compose.yml)

---

## @DOC:FRAMEWORK-001 핵심 프레임워크 & 라이브러리

### 1. Backend 주요 의존성

```toml
# pyproject.toml - [project.dependencies]
[project]
dependencies = [
    # Core web framework
    "fastapi>=0.104.0",              # FastAPI 비동기 웹 프레임워크
    "uvicorn[standard]>=0.24.0",     # ASGI 서버 (production)
    "pydantic>=2.5.0",               # 데이터 검증 + OpenAPI 스키마 생성
    "slowapi>=0.1.9",                # Rate Limiting (Redis 기반)

    # Database
    "sqlalchemy[asyncio]>=2.0.0",    # ORM + AsyncSession
    "asyncpg>=0.29.0",               # PostgreSQL 비동기 드라이버
    "alembic>=1.13.0",               # DB 마이그레이션
    "redis[hiredis]>=5.0.0",         # Redis 클라이언트 (Hiredis C 확장)

    # HTTP client
    "httpx>=0.25.0",                 # 비동기 HTTP 클라이언트

    # Data processing
    "numpy>=1.24.0",                 # 수치 계산
    "pandas>=2.0.0",                 # 데이터 프레임

    # Vector embeddings
    "sentence-transformers>=2.2.0",  # Sentence Embeddings (768-dim)
    "torch>=1.9.0",                  # PyTorch (CUDA 지원)
    "transformers>=4.21.0",          # HuggingFace Transformers
    "scikit-learn>=1.0.0",           # ML 유틸리티 (Cosine Similarity)

    # Configuration
    "python-dotenv>=1.0.0",          # 환경 변수 로드
]
```

### 2. Backend 개발 도구

```toml
# pyproject.toml - [project.optional-dependencies]
[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.0",                 # 테스트 프레임워크
    "pytest-asyncio>=0.21.0",        # 비동기 테스트 지원
    "pytest-cov>=4.1.0",             # 커버리지 측정
    "pytest-mock>=3.12.0",           # Mock 객체
    "pytest-xdist>=3.3.0",           # 병렬 테스트 실행
    "httpx>=0.25.0",                 # FastAPI 엔드포인트 테스트

    # Code quality
    "black>=23.9.0",                 # 코드 포매터
    "isort>=5.12.0",                 # Import 정렬
    "flake8>=6.1.0",                 # Linter
    "mypy>=1.6.0",                   # 타입 체커
    "pre-commit>=3.5.0",             # Git pre-commit hooks

    # Documentation
    "sphinx>=7.2.0",                 # API 문서 생성
    "sphinx-rtd-theme>=1.3.0",       # Read the Docs 테마
]
```

### 3. Frontend 주요 의존성

```json
// apps/frontend/package.json
{
  "dependencies": {
    "@radix-ui/react-checkbox": "^1.3.3",      // Radix UI primitives
    "@radix-ui/react-dialog": "^1.1.2",        // 모달 다이얼로그
    "@radix-ui/react-label": "^2.1.7",         // 레이블 컴포넌트
    "@radix-ui/react-progress": "^1.1.7",      // 프로그레스 바
    "@radix-ui/react-slot": "^1.2.3",          // Slot 패턴
    "@tanstack/react-query": "^5.0.0",         // 서버 상태 관리
    "axios": "^1.12.2",                        // HTTP 클라이언트
    "class-variance-authority": "^0.7.1",      // CSS variant 관리
    "clsx": "^2.1.1",                          // 클래스 조건부 결합
    "lucide-react": "^0.544.0",                // 아이콘 라이브러리
    "next": "^14.2.10",                        // Next.js 14 (App Router)
    "next-themes": "^0.4.6",                   // 다크 모드 지원
    "react": "^18",                            // React 18
    "react-dom": "^18",                        // React DOM
    "react-focus-lock": "^2.13.6",             // Focus 관리 (a11y)
    "recharts": "^3.2.1",                      // 차트 라이브러리
    "sonner": "^2.0.7",                        // Toast 알림
    "tailwind-merge": "^3.3.1",                // Tailwind 클래스 머지
    "tailwindcss-animate": "^1.0.7",           // Tailwind 애니메이션
    "zod": "^4.1.11"                           // 스키마 검증
  }
}
```

### 4. Frontend 개발 도구

```json
// apps/frontend/package.json
{
  "devDependencies": {
    "@types/node": "^20",                      // Node.js 타입 정의
    "@types/react": "^18",                     // React 타입 정의
    "@types/react-dom": "^18",                 // React DOM 타입 정의
    "eslint": "^8",                            // Linter
    "eslint-config-next": "14.2.0",            // Next.js ESLint 설정
    "postcss": "^8",                           // PostCSS (Tailwind)
    "tailwindcss": "^3.4.1",                   // Tailwind CSS
    "typescript": "^5"                         // TypeScript 컴파일러
  }
}
```

### 5. 빌드 시스템

**Backend**:
- **빌드 도구**: setuptools (pyproject.toml build-backend)
- **번들링**: 없음 (Python은 인터프리터 언어)
- **타겟**: Python 3.9+ 런타임
- **성능 목표**: 패키지 설치 < 5분 (pip install)

**Frontend**:
- **빌드 도구**: Next.js 14 내장 빌드 시스템 (Turbopack 실험 지원)
- **번들링**: Webpack 5 (Next.js 기본), Turbopack (dev mode 옵션)
- **타겟**: 브라우저 (ES2020+), Node.js 18+ (SSR)
- **성능 목표**: 프로덕션 빌드 < 3분 (next build)

---

## @DOC:QUALITY-001 품질 게이트 & 정책

### 테스트 커버리지

**Backend (Python)**:
- **목표**: 85% 이상 (현재 Memento Framework 통합 후 80% 이상 달성)
- **측정 도구**: pytest-cov
- **실패 시 대응**: CI/CD 빌드 실패 (커버리지 < 85% 시)

```bash
# 커버리지 측정
pytest --cov=apps --cov-report=term-missing --cov-report=html

# 커버리지 목표 검증
pytest --cov=apps --cov-fail-under=85
```

**Frontend (TypeScript)**:
- **목표**: 80% 이상 (React 컴포넌트 중심)
- **측정 도구**: Vitest (권장, 현재 미설정) 또는 Jest
- **실패 시 대응**: CI/CD 경고 (커버리지 < 80% 시)

### 정적 분석

| 도구 | 역할 | 설정 파일 | 실패 시 조치 |
|------|------|-----------|--------------|
| **black** | Python 코드 포매터 | `pyproject.toml` → `[tool.black]` | CI/CD 빌드 실패 (포맷 미준수 시) |
| **isort** | Python import 정렬 | `pyproject.toml` → `[tool.isort]` | CI/CD 빌드 실패 (정렬 미준수 시) |
| **flake8** | Python Linter | `.flake8` (선택) | CI/CD 경고 (심각도 높은 에러만 실패) |
| **mypy** | Python 타입 체커 | `pyproject.toml` → `[tool.mypy]` | CI/CD 경고 (타입 힌트 권장) |
| **ESLint** | TypeScript/React Linter | `.eslintrc.json` | CI/CD 빌드 실패 (에러 발생 시) |

**pyproject.toml 설정**:
```toml
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.mypy_cache
  | \.venv
  | build
  | dist
  | migrations
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["apps"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false  # 테스트 코드는 타입 힌트 선택적
```

### 자동화 스크립트

```bash
# 품질 검사 파이프라인 (Backend)
pytest --cov=apps --cov-fail-under=85           # 테스트 + 커버리지
black --check apps/ tests/                      # 코드 포맷 검증
isort --check-only apps/ tests/                 # Import 정렬 검증
mypy apps/ --ignore-missing-imports             # 타입 체크
flake8 apps/ tests/ --max-line-length=88        # Linter

# 품질 검사 파이프라인 (Frontend)
cd apps/frontend
npm run lint                                     # ESLint
npm run build                                    # 빌드 검증
npm run type-check                               # TypeScript 타입 체크 (tsc --noEmit)
```

**CI/CD 통합 예시 (GitHub Actions)**:
```yaml
name: Quality Gate

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=apps --cov-fail-under=85
      - run: black --check apps/ tests/
      - run: isort --check-only apps/ tests/
      - run: mypy apps/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd apps/frontend && npm ci
      - run: cd apps/frontend && npm run lint
      - run: cd apps/frontend && npm run build
```

---

## @DOC:SECURITY-001 보안 정책 & 운영

### 비밀 관리

**정책**: 모든 비밀 정보는 환경 변수로 관리, 코드에 하드코딩 금지

**도구**:
- **로컬 개발**: `.env.local` 파일 (Git ignore 대상)
- **프로덕션**: 환경 변수 (Docker Compose, Kubernetes Secrets)
- **CI/CD**: GitHub Secrets, GitLab CI/CD Variables

**검증**:
```bash
# .env.local 파일이 Git에 추적되지 않는지 확인
git ls-files | grep '.env.local'  # 결과 없어야 함

# 비밀 정보 하드코딩 검사
grep -r "OPENAI_API_KEY" apps/ --exclude-dir=.git  # 환경 변수 로드 코드만 존재해야 함
```

**필수 환경 변수**:
```bash
# .env.local (예시)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...  # OpenAI API Key
GEMINI_API_KEY=...     # Gemini API Key (Backup)
SECRET_KEY=...         # JWT 서명 키
SENTRY_DSN=...         # Sentry Error Tracking (선택)
LANGFUSE_PUBLIC_KEY=...  # LangFuse Observability (선택)
LANGFUSE_SECRET_KEY=...
```

### 의존성 보안

```json
{
  "security": {
    "audit_tool": "pip-audit (Python), npm audit (Node.js)",
    "update_policy": "월 1회 보안 업데이트 검토 및 적용",
    "vulnerability_threshold": "CVSS 7.0 이상 High/Critical 즉시 패치"
  }
}
```

**보안 감사 스크립트**:
```bash
# Python 의존성 보안 감사
pip install pip-audit
pip-audit --require-hashes --disable-pip

# Node.js 의존성 보안 감사
cd apps/frontend
npm audit --audit-level=high  # High/Critical 취약점만 리포트
npm audit fix                 # 자동 패치 가능한 취약점 수정
```

**Dependabot 설정** (GitHub):
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "npm"
    directory: "/apps/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

### 로깅 정책

**로그 수준**:
- **DEBUG**: 개발 환경 전용 (민감 정보 포함 가능)
- **INFO**: 일반 요청/응답 로그 (민감 정보 제외)
- **WARNING**: 경고 (비정상 동작, 폴백 사용)
- **ERROR**: 에러 (스택 트레이스 포함, Sentry 전송)

**민감정보 마스킹**:
- API Key: `sk-****1234` (마지막 4자리만 표시)
- 비밀번호: `***` (완전 마스킹)
- 이메일: `user@******.com` (도메인 마스킹)

```python
# 로깅 마스킹 예시 (apps/core/logger.py)
import logging
import re

class MaskingFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        # API Key 마스킹
        msg = re.sub(r'(sk-[a-zA-Z0-9]{4})[a-zA-Z0-9]+', r'\1****', msg)
        # 이메일 마스킹
        msg = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1@******', msg)
        return msg
```

**보존 정책**:
- **로그 파일**: 30일 보존 (로컬 디스크)
- **Sentry 에러**: 90일 보존 (Sentry 서버)
- **Prometheus 메트릭**: 15일 보존 (Prometheus 서버)

---

## @DOC:DEPLOY-001 배포 채널 & 전략

### 1. 배포 채널

**주 채널**: Docker Compose (개발/프로덕션 통합)

**릴리스 절차**:
1. **개발**: `git checkout -b feature/SPEC-XXX`
2. **코드 작성**: TDD 방식 (Test → Code → Refactor)
3. **품질 검증**: `pytest`, `black`, `isort`, `mypy`, `eslint`, `npm run build`
4. **PR 생성**: GitHub Pull Request
5. **코드 리뷰**: 최소 1명 승인 필요
6. **Merge**: `git merge --no-ff feature/SPEC-XXX` → `master`
7. **배포**: `git tag v2.0.1` → `docker-compose up -d --build`

**버전 정책**: Semantic Versioning (vMAJOR.MINOR.PATCH)
- **MAJOR**: Breaking Changes (API 변경, DB 스키마 변경)
- **MINOR**: 새 기능 추가 (하위 호환)
- **PATCH**: 버그 수정

**rollback 전략**:
1. **DB 롤백**: Alembic downgrade (15분 이내 복구 목표)
2. **코드 롤백**: `git revert` → `docker-compose up -d --build`
3. **Feature Flag 롤백**: 환경 변수 `FEATURE_*=false` 설정 후 재시작

---

### 2. 개발 설치

```bash
# 로컬 설치 명령어 (MacOS/Linux)
# 1. 저장소 클론
git clone https://github.com/yourorg/dt-rag.git
cd dt-rag

# 2. Python 가상 환경 생성
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Python 의존성 설치
pip install -e ".[dev]"   # 개발 도구 포함 설치

# 4. Frontend 의존성 설치
cd apps/frontend
npm install
cd ../..

# 5. 환경 변수 설정
cp .env.example .env.local
# .env.local 파일 편집 (DATABASE_URL, OPENAI_API_KEY 등)

# 6. Docker 컨테이너 시작 (PostgreSQL + Redis)
docker-compose up -d postgres redis

# 7. 데이터베이스 마이그레이션
alembic upgrade head

# 8. 개발 서버 시작
# Terminal 1: Backend
uvicorn apps.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/frontend
npm run dev  # 포트 3000

# Terminal 3: Background Worker (선택)
python -m apps.api.background.agent_task_worker
```

**Windows (WSL2) 설치**:
```powershell
# WSL2 설치 후 Ubuntu 22.04 터미널에서
wsl --install
wsl
# 이후 위의 MacOS/Linux 설치 과정과 동일
```

---

### 3. CI/CD 파이프라인

| 단계 | 목적 | 사용 도구 | 성공 조건 |
|------|------|-----------|-----------|
| **Checkout** | 코드 가져오기 | `actions/checkout@v3` | Git clone 성공 |
| **Setup** | 런타임 설치 | `actions/setup-python@v4`, `actions/setup-node@v3` | Python 3.10, Node 18 설치 |
| **Install** | 의존성 설치 | `pip install -e ".[dev]"`, `npm ci` | 의존성 설치 성공 |
| **Lint** | 코드 품질 검사 | `black`, `isort`, `mypy`, `eslint` | Linter 통과 |
| **Test** | 테스트 실행 | `pytest --cov=apps` | 테스트 통과 + Coverage ≥ 85% |
| **Build** | 빌드 검증 | `docker build`, `npm run build` | 빌드 성공 |
| **Deploy** | 배포 (master 브랜치만) | `docker-compose up -d` | 컨테이너 시작 성공 |

**GitHub Actions 예시**:
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [master, feature/**]
  pull_request:
    branches: [master]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=apps --cov-fail-under=85
      - run: black --check apps/ tests/
      - run: isort --check-only apps/ tests/
      - run: mypy apps/ --ignore-missing-imports

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd apps/frontend && npm ci
      - run: cd apps/frontend && npm run lint
      - run: cd apps/frontend && npm run build

  deploy:
    needs: [backend-test, frontend-test]
    if: github.ref == 'refs/heads/master'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose up -d --build
```

---

## 환경별 설정

### 개발 환경 (`dev`)

```bash
export PROJECT_MODE=development
export LOG_LEVEL=debug
export DEBUG=true

# FastAPI 개발 서버 시작 (Hot Reload 활성화)
uvicorn apps.api.main:app --reload --port 8000

# Next.js 개발 서버 시작 (Fast Refresh 활성화)
cd apps/frontend && npm run dev
```

**특징**:
- Hot Reload 활성화 (코드 변경 시 자동 재시작)
- DEBUG 로그 출력 (민감 정보 포함 가능)
- CORS 모든 Origin 허용 (`allow_origins=["*"]`)
- Mock 데이터 사용 가능 (Feature Flag)

---

### 테스트 환경 (`test`)

```bash
export PROJECT_MODE=test
export LOG_LEVEL=info
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test

# 테스트 전용 DB 컨테이너 시작
docker-compose up -d postgres-test

# 테스트 실행
pytest tests/ -v
```

**특징**:
- 테스트 전용 DB 사용 (postgres-test 컨테이너, 포트 5433)
- Rollback 자동 활성화 (각 테스트 후 DB 초기화)
- Mock 외부 API 호출 (OpenAI, Gemini)
- Feature Flag 모두 비활성화 (기본 동작만 테스트)

---

### 프로덕션 환경 (`production`)

```bash
export PROJECT_MODE=production
export LOG_LEVEL=warning
export DEBUG=false

# 프로덕션 서버 시작 (Gunicorn + Uvicorn Workers)
gunicorn apps.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -

# 또는 Docker Compose로 시작
docker-compose up -d api frontend
```

**특징**:
- 프로덕션 최적화 빌드 (`npm run build`)
- Multi-worker 구성 (Gunicorn 4 workers)
- CORS 제한 (allow_origins 화이트리스트)
- Sentry 에러 추적 활성화
- Rate Limiting 활성화 (Redis 기반)
- Feature Flag 선택적 활성화 (환경 변수)

---

## @CODE:TECH-DEBT-001 기술 부채 관리

### 현재 기술 부채

1. **Frontend 테스트 부재** - apps/frontend에 단위 테스트 미구현
   - **우선순위**: 높음
   - **예상 공수**: 2주
   - **해결 방안**: Vitest + React Testing Library 도입

2. **Poetry 미사용** - 현재 pip + pyproject.toml 사용, Poetry로 전환 권장
   - **우선순위**: 중간
   - **예상 공수**: 1주
   - **해결 방안**: `poetry init` → `poetry.lock` 생성

3. **Alembic Migration 수동 관리** - 자동 마이그레이션 생성 스크립트 부재
   - **우선순위**: 중간
   - **예상 공수**: 3일
   - **해결 방안**: `alembic revision --autogenerate` 워크플로우 구축

4. **DB Connection Pool 제한** - 현재 최대 20개, 트래픽 증가 시 병목 가능성
   - **우선순위**: 낮음 (현재 문제 없음)
   - **예상 공수**: 1일
   - **해결 방안**: 환경 변수 `DB_POOL_SIZE=50` 증가

5. **Feature Flag 중앙 관리 부재** - 환경 변수로만 관리, UI 없음
   - **우선순위**: 낮음
   - **예상 공수**: 1주
   - **해결 방안**: LaunchDarkly 또는 Custom Feature Flag UI 구축

### 개선 계획

**단기 (1개월)**:
1. Frontend 테스트 구축 (Vitest + React Testing Library)
2. Alembic 자동 마이그레이션 워크플로우 구축

**중기 (3개월)**:
3. Poetry로 전환 (의존성 관리 개선)
4. Feature Flag UI 구축 (관리자 대시보드)

**장기 (6개월+)**:
5. Kubernetes 마이그레이션 (Docker Compose → Helm Chart)
6. GraphQL API 추가 (RESTful API 외)
7. Multimodal 지원 (PDF, 이미지 OCR)

---

## EARS 기술 요구사항 작성법

### 기술 스택에서의 EARS 활용

기술적 의사결정과 품질 게이트 설정 시 EARS 구문을 활용하여 명확한 기술 요구사항을 정의하세요:

#### 기술 스택 EARS 예시

```markdown
### Ubiquitous Requirements (기본 기술 요구사항)
- 시스템은 Python 3.9+ 및 TypeScript 5를 사용해야 한다
- 시스템은 FastAPI 비동기 I/O를 지원해야 한다
- 시스템은 PostgreSQL + pgvector를 사용해야 한다 (별도 Vector DB 불필요)

### Event-driven Requirements (이벤트 기반 기술)
- WHEN 코드가 커밋되면, 시스템은 자동으로 black, isort, mypy, eslint를 실행해야 한다 (pre-commit hook)
- WHEN 빌드가 실패하면, 시스템은 개발자에게 Slack 알림을 보내야 한다
- WHEN 테스트 커버리지가 85% 미만이면, CI/CD 파이프라인은 빌드를 실패시켜야 한다

### State-driven Requirements (상태 기반 기술)
- WHILE 개발 모드일 때, 시스템은 uvicorn --reload 및 npm run dev를 제공해야 한다
- WHILE 프로덕션 모드일 때, 시스템은 Gunicorn + Uvicorn Workers (4개)로 동작해야 한다
- WHILE 테스트 모드일 때, 시스템은 테스트 전용 DB (포트 5433)를 사용해야 한다

### Optional Features (선택적 기술)
- WHERE Docker 환경이면, 시스템은 docker-compose.yml로 배포할 수 있다
- WHERE Kubernetes 환경이면, 시스템은 Helm Chart로 배포할 수 있다
- WHERE CI/CD가 구성되면, 시스템은 GitHub Actions로 자동 배포를 수행할 수 있다

### Constraints (기술적 제약사항)
- IF 의존성에 CVSS 7.0 이상 보안 취약점이 발견되면, 시스템은 빌드를 중단해야 한다
- 테스트 커버리지는 85% 이상을 유지해야 한다
- Backend 빌드 시간은 5분을 초과하지 않아야 한다
- Frontend 빌드 시간은 3분을 초과하지 않아야 한다
- DB Connection Pool은 최소 10개, 최대 20개를 유지해야 한다
```

---

_이 기술 스택은 `/alfred:2-run` 실행 시 TDD 도구 선택과 품질 게이트 적용의 기준이 됩니다._
