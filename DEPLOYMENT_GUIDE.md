# 🚀 DT-RAG Railway + Vercel 배포 가이드

<!-- @DOC:DEPLOY-001 - Deployment guide for Railway + Vercel -->

**프로젝트**: dt-rag v2.0.0
**배포 아키텍처**: Railway (백엔드) + Vercel (프론트엔드)
**작성일**: 2025-11-12

---

## 📋 목차

1. [배포 개요](#배포-개요)
2. [사전 준비사항](#사전-준비사항)
3. [Railway 백엔드 배포](#railway-백엔드-배포)
4. [Vercel 프론트엔드 배포](#vercel-프론트엔드-배포)
5. [배포 후 검증](#배포-후-검증)
6. [트러블슈팅](#트러블슈팅)

---

## 배포 개요

### 아키텍처 구조

```
┌─────────────────────────────────────────────────────┐
│                   인터넷 사용자                        │
└───────────────┬──────────────────┬──────────────────┘
                │                  │
                ▼                  ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  Vercel (CDN)    │  │  Railway         │
    │  - 프론트엔드     │──│  - FastAPI 백엔드 │
    │  - Static Assets │  │  - PostgreSQL    │
    └──────────────────┘  │  - Redis         │
                          │  - pgvector      │
                          └──────────────────┘
```

### 배포 방식

- **Railway**: 백엔드 API, 데이터베이스, 캐시를 모두 호스팅
- **Vercel**: 프론트엔드 정적 파일을 CDN으로 배포
- **통신**: Vercel → Railway API (CORS 설정 필요)

---

## 사전 준비사항

### 1. 계정 준비

✅ **Railway 계정** ([railway.app](https://railway.app))
- GitHub 연동 완료
- 신용카드 등록 (프리 티어: $5/월 크레딧)

✅ **Vercel 계정** ([vercel.com](https://vercel.com))
- GitHub 연동 완료
- 프리 티어 사용 가능

### 2. 리포지토리 준비

현재 프로젝트를 GitHub에 푸시:

```bash
# 현재 작업중인 브랜치 확인
git branch

# 배포 설정 파일들 커밋
git add railway.toml nixpacks.toml vercel.json .railwayignore
git commit -m "chore: Add Railway and Vercel deployment configuration"

# GitHub에 푸시
git push origin feature/SPEC-AGENT-ROUTER-BUGFIX-001
```

### 3. 환경 변수 준비

다음 키들을 미리 준비하세요:

| 키 | 설명 | 필수 여부 |
|----|------|----------|
| `DATABASE_URL` | Railway가 자동 생성 | ✅ 필수 |
| `REDIS_URL` | Railway가 자동 생성 | ✅ 필수 |
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ 필수 |
| `GEMINI_API_KEY` | Google Gemini API 키 | ⚠️ 선택 |
| `SENTRY_DSN` | Sentry 모니터링 DSN | ⚠️ 선택 |
| `LANGFUSE_PUBLIC_KEY` | Langfuse 퍼블릭 키 | ⚠️ 선택 |
| `LANGFUSE_SECRET_KEY` | Langfuse 시크릿 키 | ⚠️ 선택 |
| `API_KEY` | 백엔드 API 인증 키 | ✅ 필수 |

**API_KEY 생성 방법**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Railway 백엔드 배포

### Step 1: Railway 프로젝트 생성

1. **Railway 대시보드 접속**: [railway.app/dashboard](https://railway.app/dashboard)
2. **"New Project" 클릭**
3. **"Deploy from GitHub repo" 선택**
4. **리포지토리 선택**: `your-username/dt-rag-standalone`
5. **브랜치 선택**: `main` 또는 배포용 브랜치

### Step 2: PostgreSQL 데이터베이스 추가

1. Railway 프로젝트 내에서 **"+ New"** 클릭
2. **"Database" → "PostgreSQL"** 선택
3. 데이터베이스가 생성되면 자동으로 `DATABASE_URL` 환경 변수 생성됨

### Step 3: Redis 캐시 추가

1. Railway 프로젝트 내에서 **"+ New"** 클릭
2. **"Database" → "Redis"** 선택
3. Redis가 생성되면 자동으로 `REDIS_URL` 환경 변수 생성됨

### Step 4: pgvector Extension 활성화

Railway PostgreSQL에 pgvector를 활성화하려면:

1. Railway 대시보드에서 PostgreSQL 서비스 클릭
2. **"Data" 탭** 클릭
3. **"Query" 입력창**에서 다음 실행:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

4. 결과 확인:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Step 5: 백엔드 서비스 환경 변수 설정

1. Railway 대시보드에서 백엔드 서비스 클릭
2. **"Variables" 탭** 클릭
3. 다음 환경 변수 추가:

```bash
# 필수 환경 변수
ENVIRONMENT=production
PYTHON_VERSION=3.11
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# API 설정
API_V1_STR=/api/v1
PROJECT_NAME=DT-RAG

# 인증 키 (직접 생성한 값 입력)
API_KEY=your-generated-api-key-here

# AI 서비스 키
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...

# 모니터링 (선택사항)
SENTRY_DSN=https://...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# CORS 설정 (Vercel 도메인 추가)
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

**중요**: `DATABASE_URL`과 `REDIS_URL`은 자동으로 생성되므로 수동 입력 불필요

### Step 6: 배포 트리거

1. **"Settings" 탭** → **"Deploy"** 섹션
2. **"Deploy Trigger" 확인**: GitHub push 시 자동 배포
3. **"Deploy Now" 클릭** (수동 배포 트리거)

### Step 7: 배포 로그 확인

1. **"Deployments" 탭** 클릭
2. 최신 배포 로그 확인:
   - ✅ `pip install -r requirements.txt` 성공
   - ✅ `alembic upgrade head` 마이그레이션 실행
   - ✅ `uvicorn` 서버 시작

### Step 8: 백엔드 URL 확인

1. **"Settings" 탭** → **"Networking"** 섹션
2. **"Public Networking"** 활성화
3. **생성된 URL 복사**: `https://your-backend.railway.app`

### Step 9: 헬스 체크 테스트

Railway 백엔드가 정상 작동하는지 확인:

```bash
curl https://your-backend.railway.app/health
```

예상 응답:
```json
{
  "status": "healthy",
  "version": "1.8.1",
  "environment": "production",
  "database": "connected",
  "redis": "connected"
}
```

---

## Vercel 프론트엔드 배포

### Step 1: Vercel 프로젝트 생성

1. **Vercel 대시보드 접속**: [vercel.com/dashboard](https://vercel.com/dashboard)
2. **"Add New..." → "Project"** 클릭
3. **"Import Git Repository"**: GitHub 연동
4. **리포지토리 선택**: `your-username/dt-rag-standalone`

### Step 2: 프로젝트 설정

**Framework Preset**: Vite

**Build Settings**:
- **Build Command**: `cd frontend && npm install && npm run build`
- **Output Directory**: `frontend/dist`
- **Install Command**: `npm install --prefix frontend`

### Step 3: 환경 변수 설정

**Environment Variables** 섹션에서 추가:

```bash
# Railway 백엔드 API URL
VITE_API_BASE_URL=https://your-backend.railway.app
```

**중요**: Railway 백엔드 URL을 정확히 입력하세요!

### Step 4: 배포 실행

1. **"Deploy" 클릭**
2. 빌드 로그 확인:
   - ✅ `npm install` 성공
   - ✅ `npm run build` 성공
   - ✅ Static files generated

### Step 5: 프론트엔드 URL 확인

배포 완료 후 생성된 URL 확인:
- **Production URL**: `https://your-app.vercel.app`
- **Preview URL**: 각 PR마다 자동 생성

---

## Railway CORS 설정 업데이트

Vercel 프론트엔드가 Railway 백엔드와 통신할 수 있도록 CORS 설정 업데이트:

### Railway 환경 변수 수정

1. Railway 대시보드 → 백엔드 서비스 → **"Variables" 탭**
2. `CORS_ORIGINS` 값 업데이트:

```bash
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-*.vercel.app,http://localhost:3000
```

**설명**:
- `your-app.vercel.app`: Production 도메인
- `your-app-*.vercel.app`: Preview 도메인 (PR별 미리보기)
- `localhost:3000`: 로컬 개발 환경

3. **"Redeploy" 클릭** (변경사항 적용)

---

## 배포 후 검증

### 1. 백엔드 API 테스트

```bash
# Health Check
curl https://your-backend.railway.app/health

# API Version
curl https://your-backend.railway.app/api/v1/

# Search Endpoint (인증 필요)
curl -X POST https://your-backend.railway.app/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"q": "test query", "final_topk": 3}'
```

### 2. 프론트엔드 접속 테스트

1. 브라우저에서 `https://your-app.vercel.app` 접속
2. 개발자 도구 (F12) → **"Network" 탭** 확인
3. API 요청이 Railway 백엔드로 정상 전송되는지 확인
4. **CORS 에러**가 없는지 확인

### 3. 데이터베이스 연결 확인

Railway PostgreSQL에 연결하여 테이블 확인:

```bash
# Railway CLI 설치 (Mac/Linux)
brew install railway

# 로그인
railway login

# 프로젝트 선택
railway link

# PostgreSQL 연결
railway run psql $DATABASE_URL

# 테이블 확인
\dt
```

### 4. 마이그레이션 상태 확인

```bash
# Alembic 마이그레이션 이력 확인
railway run alembic history

# 현재 버전 확인
railway run alembic current
```

---

## 트러블슈팅

### 문제 1: Railway 빌드 실패

**증상**: `pip install -r requirements.txt` 실패

**해결 방법**:
1. Railway 대시보드 → **"Logs" 탭**에서 에러 메시지 확인
2. `nixpacks.toml` 파일에서 필요한 시스템 패키지 추가:
```toml
[phases.setup]
aptPkgs = ["build-essential", "libpq-dev", "python3-dev"]
```

### 문제 2: PostgreSQL pgvector Extension 없음

**증상**: `ERROR: type "vector" does not exist`

**해결 방법**:
```sql
-- Railway PostgreSQL Query 탭에서 실행
CREATE EXTENSION IF NOT EXISTS vector;

-- Extension 확인
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 문제 3: Vercel 빌드 실패

**증상**: `npm run build` 실패

**해결 방법**:
1. Vercel 대시보드 → **"Deployments" 탭** → 실패한 배포 클릭
2. 빌드 로그에서 에러 확인
3. 로컬에서 테스트:
```bash
cd frontend
npm install
npm run build
```

### 문제 4: CORS 에러

**증상**: 브라우저 콘솔에 `Access-Control-Allow-Origin` 에러

**해결 방법**:
1. Railway 백엔드 `CORS_ORIGINS` 환경 변수 확인
2. Vercel 도메인이 정확히 포함되어 있는지 확인
3. Railway 재배포 후 브라우저 캐시 삭제 (Ctrl+Shift+R)

### 문제 5: 환경 변수가 적용되지 않음

**증상**: API 키 인증 실패, 데이터베이스 연결 실패

**해결 방법**:
1. Railway/Vercel 대시보드에서 환경 변수 재확인
2. 변경 후 **"Redeploy" 반드시 실행**
3. 로그에서 환경 변수가 제대로 로드되는지 확인

### 문제 6: 데이터베이스 마이그레이션 실패

**증상**: `alembic upgrade head` 실패

**해결 방법**:
1. Railway 대시보드 → PostgreSQL → **"Query" 탭**
2. 현재 스키마 상태 확인:
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```
3. Alembic 버전 테이블 확인:
```sql
SELECT * FROM alembic_version;
```
4. 필요 시 수동으로 마이그레이션 실행:
```bash
railway run alembic upgrade head
```

---

## 성능 최적화 팁

### Railway 백엔드

1. **Worker 수 조정**: `nixpacks.toml`에서 `--workers 2` → `--workers 4`
2. **타임아웃 설정**: 긴 쿼리를 위한 타임아웃 증가
3. **Redis 캐싱**: 빈번한 쿼리 결과 캐싱

### Vercel 프론트엔드

1. **Code Splitting**: Vite가 자동으로 처리
2. **Image Optimization**: Vercel Image Optimization 사용
3. **CDN Caching**: Static assets 캐싱 최대화

---

## 모니터링 설정

### Sentry (에러 추적)

1. [sentry.io](https://sentry.io) 프로젝트 생성
2. DSN 복사
3. Railway 환경 변수에 `SENTRY_DSN` 추가
4. 재배포 후 에러가 Sentry 대시보드에 자동 수집

### Langfuse (LLM 모니터링)

1. [langfuse.com](https://langfuse.com) 프로젝트 생성
2. Public Key, Secret Key 복사
3. Railway 환경 변수에 추가:
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`
4. LLM 호출 추적 및 비용 모니터링

---

## 비용 예상

### Railway (월간)

| 서비스 | 예상 비용 |
|--------|-----------|
| PostgreSQL (1GB) | $5 |
| Redis (512MB) | $3 |
| API Server (0.5GB RAM) | $7 |
| **합계** | **~$15/월** |

**프리 티어**: 첫 달 $5 크레딧 제공

### Vercel (월간)

| 플랜 | 가격 | 제한 |
|------|------|------|
| **Hobby (무료)** | $0 | 100GB bandwidth |
| **Pro** | $20 | 1TB bandwidth |

**권장**: 초기에는 Vercel Hobby 플랜으로 시작

---

## 다음 단계

✅ **배포 완료 후**:
1. 커스텀 도메인 연결 (Railway + Vercel)
2. SSL 인증서 자동 생성 확인
3. CI/CD 파이프라인 설정 (GitHub Actions)
4. 백업 전략 수립 (Railway PostgreSQL 스냅샷)
5. 로그 보관 정책 수립

✅ **운영 체크리스트**:
- [ ] 프로덕션 환경 변수 검증
- [ ] API 키 보안 강화 (rotation 정책)
- [ ] 데이터베이스 백업 자동화
- [ ] 모니터링 알림 설정
- [ ] 성능 벤치마크 수립

---

**문서 작성**: Alfred (MoAI-ADK)
**최종 수정**: 2025-11-12
**버전**: v1.0.0
