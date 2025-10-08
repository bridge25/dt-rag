# DT-RAG v1.8.1 Session Context
**Date**: 2025-10-02
**Current Task**: Production 배포 진행 중
**Status**: Docker Desktop 시작 대기

---

## 🎯 현재 진행 상황

### 완료된 작업 ✅

1. **Production 필수조치 3개 완료**
   - ✅ DATABASE_URL 환경변수 가이드 작성 (`PRODUCTION_DEPLOYMENT_GUIDE.md`)
   - ✅ taxonomy_nodes 테이블 스키마 추가 (`setup_postgresql.sql`)
   - ✅ SQLAlchemy metadata 예약어 충돌 해결 (`api_key_storage.py`, `search_router.py`)

2. **수정된 파일**
   - `apps/api/security/api_key_storage.py`: Line 108, 444, 453
     - `metadata` → `request_metadata` (3곳)
   - `apps/api/routers/search_router.py`:
     - Request 파라미터 순서 수정 (5개 함수)
     - slowapi 호환성 문제 해결
   - `setup_postgresql.sql`:
     - taxonomy_nodes, taxonomy_edges, taxonomy_migrations 테이블 추가
     - 6개 인덱스 추가
     - 7개 초기 데이터 추가

3. **검증 완료**
   - Security Tests: 11/11 passed (100%)
   - Unit Tests: 35 tests collected (metadata 오류 해결)
   - Hybrid Search: 15/16 tests passed (94%)

### 현재 작업 중 🔄

**Production 배포 단계**
- [ ] Docker Desktop 시작 ← **현재 위치**
- [ ] Docker Compose로 PostgreSQL + Redis 실행
- [ ] PostgreSQL 스키마 마이그레이션
- [ ] 환경변수 설정
- [ ] Production 서버 기동
- [ ] Health check 및 검증

---

## 🚀 다음 단계 (즉시 실행 가능)

### Step 1: Docker Desktop 확인
```bash
# Docker Desktop이 실행 중인지 확인
docker ps

# 출력이 정상이면 계속 진행
# 오류 발생 시 → Docker Desktop 수동 실행 필요 (작업 표시줄 고래 아이콘 확인)
```

### Step 2: Docker Compose 실행
```bash
cd C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag

# PostgreSQL + Redis 컨테이너 시작
docker-compose up -d postgres redis

# 상태 확인
docker-compose ps
```

### Step 3: PostgreSQL 스키마 마이그레이션
```bash
# 컨테이너가 준비될 때까지 대기 (약 10초)
timeout /t 10

# 스키마 적용
docker exec -i dt_rag_postgres psql -U postgres -d dt_rag < setup_postgresql.sql

# 확인
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "\dt"
```

### Step 4: 환경변수 설정
```powershell
# Windows PowerShell
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag"
$env:OPENAI_API_KEY = "sk-proj-..."  # 실제 키 입력
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"

# 확인
echo $env:DATABASE_URL
```

### Step 5: Production 서버 시작
```bash
# 서버 실행
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 또는 개발 모드
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Health Check
```bash
# 새 터미널에서
curl http://localhost:8000/health

# 또는 브라우저에서
http://localhost:8000/docs  # Swagger UI
```

---

## 📁 주요 파일 위치

### Production 관련 문서
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - 전체 배포 가이드
- `PRODUCTION_DEPLOYMENT_REPORT.md` - 검증 보고서 (75/100 → 95/100 예상)
- `PRODUCTION_TASKS_COMPLETED.md` - 완료 작업 상세
- `production_readiness_check.py` - 자동 검증 스크립트

### 설정 파일
- `docker-compose.yml` - Docker 환경 정의
- `setup_postgresql.sql` - 데이터베이스 스키마
- `pytest.ini` - 테스트 설정

### 코어 소스
- `apps/api/main.py` - FastAPI 애플리케이션
- `apps/api/security/api_key_storage.py` - API 인증 (수정됨)
- `apps/api/routers/search_router.py` - 검색 API (수정됨)
- `apps/search/hybrid_search_engine.py` - 하이브리드 검색 엔진

---

## 🔧 Docker Compose 구성

**현재 설정 (`docker-compose.yml`):**
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports: "5432:5432"
    environment:
      POSTGRES_DB: dt_rag
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: "6379:6379"
```

**컨테이너 이름:**
- PostgreSQL: `dt_rag_postgres`
- Redis: `dt_rag_redis`

---

## 📊 Production Readiness 현황

### 시스템 상태
```
Component               Status      Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Security               ✅ 100%     SQL Injection, API Auth, Rate Limiting
Hybrid Search          ✅ 94%      15/16 tests passed
Dependencies           ✅ 100%     7/7 installed
Database Schema        ✅ Ready    taxonomy_nodes added
API Endpoints          ✅ Ready    11 endpoints + auth
Metadata Conflict      ✅ Fixed    request_metadata rename
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Readiness:     95/100     (After DB migration)
```

### 필요한 환경변수
```bash
# 필수
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag
OPENAI_API_KEY=sk-proj-...

# 선택 (이미 Docker로 실행)
REDIS_HOST=localhost
REDIS_PORT=6379

# 선택 (나중에 추가 가능)
GEMINI_API_KEY=...
SENTRY_DSN=https://...
```

---

## ⚠️ 알려진 이슈

1. **Docker Desktop 수동 시작 필요**
   - Windows에서 자동 시작 안됨
   - 수동 실행: 시작 메뉴 → Docker Desktop

2. **테스트 환경 PostgreSQL 포트**
   - Production: 5432
   - Test: 5433 (충돌 방지)

3. **SQLite Fallback**
   - DATABASE_URL 없으면 자동으로 SQLite 사용
   - Production에서는 반드시 PostgreSQL 설정 필요

---

## 🎓 기술 스택

### Backend
- **FastAPI** 0.104+ - REST API
- **SQLAlchemy** 2.0+ - ORM (asyncpg driver)
- **PostgreSQL** 16 + pgvector - Vector DB
- **Redis** 7 - Caching
- **slowapi** - Rate Limiting

### Search
- **BM25** - PostgreSQL Full-text Search
- **Vector Search** - pgvector (HNSW index)
- **Cross-encoder** - ms-marco-MiniLM-L-6-v2
- **Embeddings** - OpenAI text-embedding-ada-002 (1536 dim)

### ML/AI
- **sentence-transformers** - Embedding models
- **RAGAS** - RAG evaluation
- **LangChain** - LLM integration (optional)

---

## 📝 최근 변경사항 (2025-10-02)

### 1. api_key_storage.py (Line 108, 444, 453)
```python
# Before
metadata = Column(Text, nullable=True)  # SQLAlchemy 예약어 충돌

# After
request_metadata = Column(Text, nullable=True)  # 수정 완료
```

### 2. search_router.py (5개 함수)
```python
# Before - slowapi 오류
async def search_documents(
    request: SearchRequest,
    request: Request,  # 중복!
    ...
)

# After - 수정 완료
async def search_documents(
    request: SearchRequest,
    http_request: Request,  # 이름 변경
    ...
)
```

### 3. setup_postgresql.sql (Line 37-140)
```sql
-- 추가된 테이블
CREATE TABLE taxonomy_nodes (...);
CREATE TABLE taxonomy_edges (...);
CREATE TABLE taxonomy_migrations (...);

-- 추가된 인덱스 (6개)
CREATE INDEX taxonomy_nodes_version_idx ...;
CREATE INDEX taxonomy_nodes_path_idx ...;
...

-- 추가된 초기 데이터 (7 nodes)
INSERT INTO taxonomy_nodes VALUES
  ('AI', ...),
  ('Machine Learning', ...),
  ...;
```

---

## 🔍 트러블슈팅

### Docker Desktop이 시작 안됨
```bash
# 확인
docker ps

# 오류 발생 시
# → 시작 메뉴에서 "Docker Desktop" 수동 실행
# → 작업 표시줄에 고래 아이콘 확인 (초록색 = 준비 완료)
```

### PostgreSQL 연결 실패
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs postgres

# 재시작
docker-compose restart postgres
```

### 포트 충돌
```bash
# 5432 포트 사용 중인 프로세스 확인
netstat -ano | findstr :5432

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

### 스키마 적용 실패
```bash
# 직접 psql 접속
docker exec -it dt_rag_postgres psql -U postgres -d dt_rag

# 테이블 확인
\dt

# Extension 확인
\dx

# 종료
\q
```

---

## 📞 추가 정보

### Production 검증 스크립트
```bash
# 자동 검증 실행
python production_readiness_check.py

# 기대 출력: 95-100/100 readiness score
```

### API 문서 접속
```
# 서버 시작 후
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
http://localhost:8000/openapi.json # OpenAPI spec
```

### 테스트 실행
```bash
# Security tests
python -m pytest tests/security/ -v

# Hybrid search tests
python -m pytest tests/test_hybrid_search.py -v

# All tests
python -m pytest tests/ -v
```

---

## 🎯 즉시 실행 명령어 요약

```bash
# 1. Docker 확인
docker ps

# 2. 컨테이너 시작
docker-compose up -d postgres redis

# 3. 스키마 적용
docker exec -i dt_rag_postgres psql -U postgres -d dt_rag < setup_postgresql.sql

# 4. 환경변수 (PowerShell)
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag"
$env:OPENAI_API_KEY = "sk-proj-..."

# 5. 서버 시작
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# 6. 확인
curl http://localhost:8000/health
```

---

**이 문서를 새 세션 시작 시 읽으면 작업을 즉시 이어갈 수 있습니다.**

**현재 위치**: Docker Desktop 시작 대기 → `docker ps` 실행하여 확인 → 정상이면 Step 2부터 진행
