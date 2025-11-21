# 🔐 환경 변수 설정 가이드

<!-- @DOC:CONFIG-001 - Environment configuration guide -->

**프로젝트**: dt-rag v2.0.0
**플랫폼**: Railway (백엔드) + Vercel (프론트엔드)

---

## Railway 백엔드 환경 변수

### ✅ 필수 환경 변수

| 변수명 | 설명 | 예시 값 | 생성 방법 |
|--------|------|---------|----------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql://user:pass@host:port/db` | Railway 자동 생성 |
| `REDIS_URL` | Redis 연결 URL | `redis://default:pass@host:port` | Railway 자동 생성 |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-...` | [OpenAI Dashboard](https://platform.openai.com/api-keys) |
| `API_KEY` | 백엔드 API 인증 키 | `random-32-char-string` | 아래 스크립트 참조 |

### ⚙️ 애플리케이션 설정 (필수)

```bash
# Python 환경
PYTHON_VERSION=3.11
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# 환경 구분
ENVIRONMENT=production

# API 설정
API_V1_STR=/api/v1
PROJECT_NAME=DT-RAG

# CORS 설정 (Vercel 도메인 추가)
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-*.vercel.app,http://localhost:3000
```

### ⚠️ 선택적 환경 변수

| 변수명 | 설명 | 예시 값 | 관련 서비스 |
|--------|------|---------|-------------|
| `GEMINI_API_KEY` | Google Gemini API 키 | `AIza...` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `SENTRY_DSN` | Sentry 에러 추적 DSN | `https://...@sentry.io/...` | [Sentry Dashboard](https://sentry.io) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse 퍼블릭 키 | `pk-lf-...` | [Langfuse Dashboard](https://langfuse.com) |
| `LANGFUSE_SECRET_KEY` | Langfuse 시크릿 키 | `sk-lf-...` | [Langfuse Dashboard](https://langfuse.com) |
| `SENTRY_TRACES_SAMPLE_RATE` | Sentry 트레이스 샘플링 비율 | `1.0` | Sentry 설정 |
| `RATE_LIMIT_ENABLED` | Rate Limiting 활성화 | `true` | - |
| `RATE_LIMIT_PER_MINUTE` | 분당 요청 제한 | `60` | - |

---

## Vercel 프론트엔드 환경 변수

### ✅ 필수 환경 변수

| 변수명 | 설명 | 예시 값 |
|--------|------|---------|
| `VITE_API_BASE_URL` | Railway 백엔드 API URL | `https://your-backend.railway.app` |

### Vercel 설정 방법

1. Vercel 대시보드 → 프로젝트 선택
2. **Settings** → **Environment Variables**
3. 다음 추가:

```bash
VITE_API_BASE_URL=https://your-backend.railway.app
```

**중요**: Railway 백엔드 배포 완료 후 정확한 URL로 업데이트하세요!

---

## API 키 생성 방법

### 1. 백엔드 API 인증 키 생성

**Python 스크립트**:
```bash
python3 -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
```

**출력 예시**:
```
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

이 값을 복사하여 Railway 환경 변수에 추가하세요.

### 2. OpenAI API 키 발급

1. [OpenAI Platform](https://platform.openai.com/) 로그인
2. **API Keys** 메뉴 클릭
3. **"Create new secret key"** 클릭
4. 키 이름 입력 (예: `dt-rag-production`)
5. 생성된 키 복사 (한 번만 표시됨!)
6. Railway 환경 변수에 추가

**요금**:
- GPT-4: $0.03/1K tokens (input), $0.06/1K tokens (output)
- GPT-3.5: $0.0015/1K tokens (input), $0.002/1K tokens (output)

### 3. Google Gemini API 키 발급 (선택)

1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. **"Get API Key"** 클릭
3. 프로젝트 선택 또는 생성
4. API 키 생성 및 복사
5. Railway 환경 변수에 추가

**요금**:
- Gemini 1.5 Pro: $0.0035/1K tokens (무료 티어 포함)

---

## Railway 환경 변수 설정 단계별 가이드

### Step 1: Railway 프로젝트 접속

1. [Railway Dashboard](https://railway.app/dashboard) 접속
2. 프로젝트 선택
3. 백엔드 서비스 클릭

### Step 2: Variables 탭 이동

1. **"Variables" 탭** 클릭
2. 기존 환경 변수 확인:
   - ✅ `DATABASE_URL` (자동 생성)
   - ✅ `REDIS_URL` (자동 생성)

### Step 3: 필수 환경 변수 추가

**"New Variable" 버튼 클릭** 후 하나씩 추가:

```bash
# 1. Python 환경
PYTHON_VERSION
```
**Value**: `3.11`

```bash
# 2. 애플리케이션 환경
ENVIRONMENT
```
**Value**: `production`

```bash
# 3. API 인증 키 (직접 생성한 값)
API_KEY
```
**Value**: `your-generated-api-key`

```bash
# 4. OpenAI API 키
OPENAI_API_KEY
```
**Value**: `sk-proj-...`

```bash
# 5. CORS 설정 (Vercel 배포 후 업데이트)
CORS_ORIGINS
```
**Value**: `https://your-app.vercel.app,https://your-app-*.vercel.app,http://localhost:3000`

### Step 4: 추가 설정 변수 (복사 붙여넣기)

아래 변수들을 **"Bulk Import"** 기능으로 한 번에 추가:

```bash
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
API_V1_STR=/api/v1
PROJECT_NAME=DT-RAG
```

### Step 5: 선택적 환경 변수 추가

모니터링이 필요한 경우 추가:

```bash
# Sentry (에러 추적)
SENTRY_DSN=https://...@sentry.io/...
SENTRY_TRACES_SAMPLE_RATE=1.0

# Langfuse (LLM 모니터링)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### Step 6: 재배포

1. **"Settings" 탭** → **"Deploy"** 섹션
2. **"Redeploy"** 클릭
3. 배포 로그에서 환경 변수가 제대로 로드되는지 확인

---

## 환경 변수 검증 체크리스트

### Railway 백엔드

```bash
# Railway CLI로 환경 변수 확인
railway variables

# 출력 예시:
# ✅ DATABASE_URL: postgresql://...
# ✅ REDIS_URL: redis://...
# ✅ API_KEY: a1b2c3...
# ✅ OPENAI_API_KEY: sk-proj-...
# ✅ ENVIRONMENT: production
# ✅ PYTHON_VERSION: 3.11
# ✅ CORS_ORIGINS: https://your-app.vercel.app,...
```

### Vercel 프론트엔드

```bash
# Vercel CLI로 환경 변수 확인
vercel env ls

# 출력 예시:
# ✅ VITE_API_BASE_URL (Production): https://your-backend.railway.app
```

---

## 트러블슈팅

### 문제 1: DATABASE_URL이 자동 생성되지 않음

**원인**: PostgreSQL 서비스가 Railway 프로젝트에 추가되지 않음

**해결**:
1. Railway 프로젝트 → **"+ New"** → **"Database"** → **"PostgreSQL"**
2. 서비스 생성 후 자동으로 `DATABASE_URL` 생성됨
3. 백엔드 서비스에서 PostgreSQL 연결 확인

### 문제 2: CORS 에러 발생

**원인**: `CORS_ORIGINS`에 Vercel 도메인이 누락되거나 잘못 입력됨

**해결**:
1. Vercel 프로덕션 URL 정확히 복사 (예: `https://dt-rag-abc123.vercel.app`)
2. Railway `CORS_ORIGINS` 업데이트:
```bash
CORS_ORIGINS=https://dt-rag-abc123.vercel.app,https://dt-rag-*.vercel.app,http://localhost:3000
```
3. Railway 재배포

### 문제 3: API 키 인증 실패

**증상**: 백엔드 응답 `403 Forbidden`

**해결**:
1. Railway `API_KEY` 환경 변수 확인
2. 프론트엔드 요청 헤더 확인:
```javascript
headers: {
  'X-API-Key': 'your-api-key'
}
```
3. 키 값이 정확히 일치하는지 확인 (공백, 특수문자 주의)

### 문제 4: Vite 환경 변수가 빌드에 포함되지 않음

**원인**: Vite는 `VITE_` 접두사가 있는 환경 변수만 클라이언트에 노출

**해결**:
1. Vercel 환경 변수 이름이 `VITE_API_BASE_URL`로 시작하는지 확인
2. 빌드 후 `dist/_app.js`에서 환경 변수 확인:
```bash
grep "VITE_API_BASE_URL" frontend/dist/_app.js
```

---

## 환경별 설정 예시

### Development (로컬)

`.env.local` 파일 생성:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dt_rag
REDIS_URL=redis://localhost:6379

# API
API_KEY=dev-api-key-do-not-use-in-production
OPENAI_API_KEY=sk-proj-...

# Environment
ENVIRONMENT=development
API_V1_STR=/api/v1
PROJECT_NAME=DT-RAG-Dev

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (Railway)

Railway Dashboard Variables:

```bash
# Database (자동 생성)
DATABASE_URL=postgresql://postgres.railway.internal:5432/railway
REDIS_URL=redis://default:password@redis.railway.internal:6379

# API (직접 설정)
API_KEY=secure-production-api-key-32-chars
OPENAI_API_KEY=sk-proj-production-key...

# Environment
ENVIRONMENT=production
PYTHON_VERSION=3.11
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
API_V1_STR=/api/v1
PROJECT_NAME=DT-RAG

# CORS
CORS_ORIGINS=https://dt-rag.vercel.app,https://dt-rag-*.vercel.app
```

---

## 보안 권장사항

### ✅ DO

- ✅ API 키는 안전하게 보관 (1Password, Bitwarden 등)
- ✅ 프로덕션과 개발 환경 키 분리
- ✅ API 키 정기적으로 로테이션 (3-6개월)
- ✅ Railway/Vercel 환경 변수만 사용 (코드에 하드코딩 금지)
- ✅ `.env` 파일을 `.gitignore`에 추가

### ❌ DON'T

- ❌ API 키를 Git에 커밋하지 말 것
- ❌ 개발 환경 키를 프로덕션에 사용하지 말 것
- ❌ API 키를 로그에 출력하지 말 것
- ❌ 브라우저에서 접근 가능한 환경 변수에 민감 정보 저장 금지
- ❌ 공개 리포지토리에 환경 변수 예시 파일 업로드 금지

---

## 참고 링크

- **Railway 환경 변수 문서**: https://docs.railway.app/guides/variables
- **Vercel 환경 변수 문서**: https://vercel.com/docs/environment-variables
- **Vite 환경 변수 문서**: https://vitejs.dev/guide/env-and-mode.html
- **OpenAI API Keys**: https://platform.openai.com/api-keys
- **Google AI Studio**: https://aistudio.google.com/app/apikey

---

**문서 작성**: Alfred (MoAI-ADK)
**최종 수정**: 2025-11-12
**버전**: v1.0.0
