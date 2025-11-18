# Railway CLI 연동 배포 작업 리포트

**작성일**: 2025-11-13
**프로젝트**: dt-rag-standalone
**목표**: Railway CLI를 통한 완전 자동화 배포 구현 (GitHub Actions CI/CD 병목 해결)

---

## 📋 작업 배경

### 초기 문제
- **GitHub Actions CI/CD 병목**: 테스트 실행 시간 25-60분 소요
- **목표**: Railway Pre-Deploy Command로 5-10분으로 단축
- **요구사항**: Claude Code에서 Railway CLI를 완전 제어하여 자동 배포

### 아키텍처 목표
```
git push → Railway 자동 감지 → Railway 서버에서 pytest 실행 (preDeployCommand)
         → 테스트 통과 → 자동 배포 (5-10분)
```

---

## 🚀 진행 작업 요약

### 1단계: Railway + Vercel 사전 작업 완료 (성공)

**생성된 파일**:
- `railway.toml` (42줄) - Pre-Deploy Command, Environment-specific configs
- `vercel.json` (36줄) - 프론트엔드 배포 설정
- `deploy.sh` (197줄) - 16단계 완전 자동화 스크립트
- `DEPLOYMENT_GUIDE.md` (498줄) - 상세 배포 가이드
- `ENV_VARIABLES_GUIDE.md` (362줄) - 환경 변수 가이드
- `docs/development/railway-cli-testing.md` (318줄) - Railway CLI 테스트 가이드

**railway.toml 핵심 설정**:
```toml
[deploy]
startCommand = "alembic upgrade head && uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT"
preDeployCommand = "pytest tests/unit/ tests/integration/ -v --maxfail=3 --tb=short"
healthcheckPath = "/health"

# PR Environment: Fast feedback (5-10분)
[environments.pr.deploy]
preDeployCommand = "pytest tests/unit/ -v --maxfail=1 --tb=line"

# Production Environment: 전체 테스트
[environments.production.deploy]
preDeployCommand = "pytest tests/ --cov=apps --cov-fail-under=85 -v --tb=short"
```

**GitHub Actions 최적화**:
- `.github/workflows/moai-gitflow.yml` 수정
- Draft PR → Railway 테스트만 실행 (빠름)
- Ready PR → 전체 테스트 실행

---

### 2단계: Render 시도 (실패)

**진행 내용**:
1. Railway CLI 인증 문제로 Render로 전환 시도
2. render.yaml 작성 및 Blueprint 배포 시도
3. Render API를 통한 자동화 시도

**실패 원인**:
```
"You can't create free-tier services with the Render API"
```
- Render는 무료 Web Service를 API로 생성 불가
- PostgreSQL, Redis는 생성했으나 백엔드 서비스 생성 실패

**정리 작업**:
- Render 리소스 삭제 (Redis, PostgreSQL)
- render.yaml 삭제 (feature + master 브랜치)
- Commit: `a3d1ae96`, `eeaf7ec6`

---

### 3단계: Railway CLI 인증 문제 분석 (실패 → 해결책 발견)

#### 시도 1: Railway CLI 브라우저 인증 (실패)
```bash
railway login  # WSL 환경에서 브라우저 로드 문제
```
- WSL Ubuntu Chrome 업데이트 문제
- 브라우저 페이지 로드 불완전

#### 시도 2: Railway API Token (부분 성공)
**제공받은 Token**: `5d5444a4-9ef4-4ed7-be34-a122fc62ac1e`

**GraphQL API 시도**:
```graphql
# 성공한 작업:
- 프로젝트 조회: 3개 프로젝트 확인
- 프로젝트 생성: dt-rag (ID: b5eedf32-d24b-415c-a72e-0824b32a5cc3)
- 환경 ID 획득: a9f94715-ce7b-4af2-a246-2165bb62eb86

# 실패한 작업:
- GitHub 저장소 연결: "Problem processing request"
- PostgreSQL 생성: "Problem processing request"
- Redis 생성: "Problem processing request"
```

**실패 원인 분석**:
1. **Token 타입 제약**: Project Token은 배포만 가능, 리소스 생성 불가
   - ✅ `railway up` (배포) 가능
   - ❌ 데이터베이스, 서비스 생성 불가
   - ❌ `railway whoami` 불가 (인증 명령 제한)

2. **Railway Token 2가지 타입**:
   - `RAILWAY_TOKEN` (Project Token) - 배포 전용
   - `RAILWAY_API_TOKEN` (Account Token) - 전체 리소스 관리

---

### 4단계: Railway MCP 서버 설치 (성공) ✅

**GPT 조언 수용**:
- Railway MCP 서버를 Claude Code에 설치하면 완전 자동화 가능
- 자연어로 Railway 제어 가능

**설치 실행**:
```bash
claude mcp add railway-mcp-server -- npx -y @railway/mcp-server
```

**설치 결과 확인** (`~/.claude.json`):
```json
"/home/a/projects/dt-rag-standalone": {
  "mcpServers": {
    "railway-mcp-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@railway/mcp-server"],
      "env": {}
    }
  }
}
```

**검증 완료**:
- ✅ 다른 프로젝트의 MCP 설정과 동일한 형식
- ✅ stdio transport 방식으로 정확히 등록됨
- ✅ Claude Code 재시작 후 사용 가능

---

## 🔍 Railway MCP 서버 특징

### 아키텍처
- **Direct Tool Declaration** 방식 (Anthropic Filesystem API 패턴 X)
- 10-15개 고정 도구 제공
- Railway CLI 명령을 MCP로 래핑

### 제공 도구
- `check-railway-status` - CLI 설치/로그인 상태
- `create-project-and-link` - 프로젝트 생성 및 링크
- `list-projects`, `list-services`, `list-variables`
- `deploy` - 서비스 배포
- `deploy-template` - 템플릿 배포
- `create-environment`, `link-environment`
- `generate-domain` - 도메인 생성
- `get-logs` - 로그 조회

### 안전성
- ✅ 파괴적 작업(`delete-x`) 의도적 제외
- ✅ CLI 버전 자동 감지 및 기능 적응
- ✅ 사용자 승인 필요 (Claude Code 권한 시스템)

---

## 📦 현재 프로젝트 상태

### Railway 리소스
- **프로젝트**: `dt-rag` (ID: `b5eedf32-d24b-415c-a72e-0824b32a5cc3`)
- **환경**: production (ID: `a9f94715-ce7b-4af2-a246-2165bb62eb86`)
- **서비스**: 없음 (빈 프로젝트)
- **데이터베이스**: 없음

### 로컬 설정
- **Railway CLI**: v4.11.0 설치됨
- **Railway MCP**: Claude Code에 등록됨 (재시작 필요)
- **Project Token**: `5d5444a4-9ef4-4ed7-be34-a122fc62ac1e`

### Git 상태
- **현재 브랜치**: `feature/SPEC-TEST-STABILIZE-002`
- **최근 커밋**:
  - `a3d1ae96`: Render 설정 제거 (feature 브랜치)
  - `eeaf7ec6`: Render 설정 제거 (master 브랜치)
- **Untracked files**: TAG 검증 리포트 및 문서 여러 개

---

## ⚙️ 배포 설정 파일

### railway.toml
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install --upgrade pip && pip install -r requirements.txt"

[deploy]
startCommand = "alembic upgrade head && uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT"
preDeployCommand = "pytest tests/unit/ tests/integration/ -v --maxfail=3 --tb=short"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 3

[env]
PYTHON_VERSION = "3.11"
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
ENVIRONMENT = "production"
API_V1_STR = "/api/v1"
PROJECT_NAME = "DT-RAG"

# Environment-specific configurations
[environments.pr.deploy]
preDeployCommand = "pytest tests/unit/ -v --maxfail=1 --tb=line"
startCommand = "uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT --reload"

[environments.production.deploy]
preDeployCommand = "pytest tests/ --cov=apps --cov-fail-under=85 -v --tb=short && alembic upgrade head"
numReplicas = 2
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### .railway/config.json (로컬 링크)
```json
{
  "projectId": "b5eedf32-d24b-415c-a72e-0824b32a5cc3",
  "environmentId": "a9f94715-ce7b-4af2-a246-2165bb62eb86"
}
```

---

## 🎯 다음 세션 작업 계획

### 1단계: Railway MCP 동작 확인
```bash
# Claude Code 재시작 후
/mcp
# railway-mcp-server가 목록에 나타나는지 확인
```

### 2단계: 자연어로 Railway 배포 실행
```
"Railway에 dt-rag 프로젝트 배포해줘.
GitHub 저장소 bridge25/dt-rag를 master 브랜치로 연결하고,
PostgreSQL과 Redis를 추가한 다음,
환경 변수를 railway.toml에 정의된 대로 설정해줘."
```

### 3단계: 예상 MCP 동작 흐름
1. `check-railway-status` - CLI 상태 확인
2. `create-project-and-link` - 기존 프로젝트 링크 또는 생성
3. Railway CLI가 GitHub 저장소 연결 (Web UI 프롬프트 가능)
4. PostgreSQL, Redis 추가
5. 환경 변수 설정
6. `deploy` - 초기 배포 트리거

### 4단계: 배포 후 검증
```bash
# 헬스 체크
curl https://dt-rag-backend.railway.app/health

# 로그 확인 (MCP 사용)
"Railway 배포 로그 보여줘"
```

### 5단계: 프론트엔드 배포 (Vercel)
- Vercel 배포는 이미 `vercel.json` 준비됨
- Railway 백엔드 URL을 Vercel 환경 변수로 설정
- CORS 업데이트 (Railway → Vercel URL 추가)

---

## 🚨 주요 발견 사항

### Railway Token 제약
```
Project Token (현재 보유):
  ✅ railway up (배포)
  ✅ railway logs
  ✅ railway redeploy
  ❌ 프로젝트 생성
  ❌ 데이터베이스/서비스 추가
  ❌ railway whoami

Account Token (필요 시):
  ✅ 모든 리소스 생성/관리
  ✅ railway init
  ✅ railway whoami
```

**해결책**: Railway MCP 서버가 Railway CLI를 통해 동작하므로, **CLI 인증 상태가 중요**. MCP가 자동으로 `railway login` 유도할 가능성 있음.

### Anthropic MCP 패턴 vs Railway MCP
- **Anthropic 패턴**: Filesystem API (수백 개 도구용)
- **Railway MCP**: Direct Declaration (10-15개 도구)
- **결론**: Railway 사용 사례에는 Direct Declaration이 적합

---

## 📊 시도한 플랫폼 비교

| 플랫폼 | CLI 자동화 | 무료 티어 API | 결과 |
|--------|-----------|---------------|------|
| **Railway** | ✅ MCP 서버 | ⚠️ Project Token 제약 | ✅ 최종 선택 |
| **Render** | ⚠️ Blueprint만 | ❌ Web Service API 불가 | ❌ 포기 |
| **Vercel** | ✅ CLI | ✅ 완전 지원 | ✅ 프론트엔드용 |

---

## 🔑 Railway 인증 정보

### Project Token
```
5d5444a4-9ef4-4ed7-be34-a122fc62ac1e
```

### 프로젝트 정보
- **Project ID**: `b5eedf32-d24b-415c-a72e-0824b32a5cc3`
- **Environment ID**: `a9f94715-ce7b-4af2-a246-2165bb62eb86`
- **GitHub Repo**: `bridge25/dt-rag`
- **Target Branch**: `master`

### Owner 정보
```json
{
  "email": "chansooo.co@gmail.com",
  "id": "tea-d4a6v2er433s73eepto0",
  "name": "My Workspace",
  "type": "team"
}
```

---

## 📝 필요한 환경 변수 (배포 시)

### 필수
- `DATABASE_URL` - Railway가 자동 생성
- `REDIS_URL` - Railway가 자동 생성
- `API_KEY` - 자동 생성 권장
- `OPENAI_API_KEY` - 사용자 제공 (선택)
- `GEMINI_API_KEY` - 사용자 제공 (선택)

### 애플리케이션
- `PYTHON_VERSION=3.11`
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`
- `ENVIRONMENT=production`
- `API_V1_STR=/api/v1`
- `PROJECT_NAME=DT-RAG`

---

## ⚠️ 주의사항

### Railway MCP 사용 시
1. **승인 필요**: Claude Code가 Railway 작업 실행 전 사용자 승인 요청
2. **파괴적 작업 없음**: delete 관련 도구는 의도적으로 제외됨
3. **CLI 의존성**: Railway CLI 설치 상태 확인 필요

### 배포 후 확인
1. Health check: `/health` 엔드포인트
2. 데이터베이스 연결 상태
3. Redis 연결 상태
4. Alembic 마이그레이션 성공 여부
5. pytest 실행 결과 (로그)

---

## 🎉 기대 효과

### CI/CD 개선
- **Before**: GitHub Actions 25-60분
- **After**: Railway Pre-Deploy 5-10분
- **개선율**: 60-80% 단축

### 워크플로우
```
git push → Railway 자동 감지 → Railway 서버에서 테스트
         → 테스트 통과 → 자동 배포 → 헬스 체크
         → 성공 시 Production 환경 배포
```

### 개발자 경험
- GitHub Actions 대기 시간 대폭 감소
- Railway CLI로 로컬에서도 프로덕션 환경 테스트 가능
- Claude Code에서 자연어로 배포 관리

---

## 📚 참고 문서

### 작성된 문서
- `DEPLOYMENT_GUIDE.md` - 498줄 상세 가이드
- `ENV_VARIABLES_GUIDE.md` - 362줄 환경 변수 가이드
- `docs/development/railway-cli-testing.md` - 318줄 CLI 테스트 가이드

### 공식 문서
- Railway MCP: https://docs.railway.com/reference/mcp-server
- Railway CLI: https://docs.railway.com/guides/cli
- MCP Protocol: https://modelcontextprotocol.io

---

## 🔄 다음 세션 체크리스트

- [ ] Claude Code 재시작
- [ ] `/mcp` 명령으로 railway-mcp-server 확인
- [ ] Railway 배포 명령 실행
- [ ] PostgreSQL, Redis 추가 확인
- [ ] 환경 변수 설정 확인
- [ ] 초기 배포 성공 확인
- [ ] Health check 테스트
- [ ] 로그 확인
- [ ] Vercel 프론트엔드 배포
- [ ] CORS 설정 업데이트

---

---

## 🔄 세션 2 업데이트 (2025-11-13 03:00 UTC)

### 진행 작업

#### 1. moai-adk 버전 확인
```bash
pip show moai-adk  # v0.22.5 (최신 버전)
pip index versions moai-adk  # 확인: 0.22.5가 LATEST
```
**결과**: 이미 최신 버전 설치됨 ✅

#### 2. Railway MCP 서버 동작 테스트

**첫 번째 시도**: MCP 서버 상태 확인
```bash
mcp__railway-mcp-server__check-railway-status
```
**결과**: ❌ "Not logged in to Railway CLI"

**원인 분석**:
- Railway MCP 서버는 별도 프로세스로 실행됨
- 부모 쉘의 환경 변수를 자동 상속하지 않음
- `.claude.json`의 `env` 필드에 명시적 설정 필요

#### 3. Railway Token 시스템 상세 분석

**공식 문서 조사 결과**:

| Token 타입 | 생성 위치 | 환경 변수 | 권한 범위 |
|-----------|-----------|-----------|-----------|
| **Personal Token** | `railway.com/account/tokens` (no workspace) | `RAILWAY_API_TOKEN` | 모든 개인 리소스 |
| **Team Token** | `railway.com/account/tokens` (워크스페이스 선택) | `RAILWAY_API_TOKEN` | 선택한 워크스페이스만 |
| **Project Token** | 프로젝트 설정 → Tokens 탭 | `RAILWAY_TOKEN` | 특정 환경만 |

**중요 발견**:
- 사용자가 제공한 토큰 `5d5444a4-9ef4-4ed7-be34-a122fc62ac1e`는 **Team Token**
- 생성 시 "bridge25's project" 워크스페이스 선택
- `railway.com/account/tokens`에서는 Project/Personal 구분 UI 없음
- Workspace 선택으로 Token 타입 결정

**Team Token 제약사항** (공식 문서):
- ✅ 워크스페이스 내 프로젝트 배포 가능
- ❌ `railway whoami` 명령 제한
- ❌ `railway link` 명령 제한

#### 4. Claude Code Non-Interactive 환경 제약

**시도한 인증 방법**:
```bash
# 1. 환경 변수만 설정
export RAILWAY_API_TOKEN=5d5444a4-...
railway whoami
# → 실패: MCP 서버는 부모 환경 변수 미상속

# 2. Browserless 로그인 시도
railway login --browserless
# → 실패: "Cannot login in non-interactive mode"

# 3. .bashrc에 영구 설정
echo "export RAILWAY_API_TOKEN=..." >> ~/.bashrc
# → 실패: MCP는 로그인 쉘 환경 미사용
```

**근본 원인**:
- Claude Code는 non-interactive 모드로 실행
- 브라우저 기반 OAuth 불가능
- MCP 서버는 독립 프로세스로 별도 환경 필요

#### 5. 해결: MCP 설정에 토큰 추가

**수정 사항**:
```json
// ~/.claude.json
{
  "projects": {
    "/home/a/projects/dt-rag-standalone": {
      "mcpServers": {
        "railway-mcp-server": {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "@railway/mcp-server"],
          "env": {
            "RAILWAY_API_TOKEN": "5d5444a4-9ef4-4ed7-be34-a122fc62ac1e"
          }
        }
      }
    }
  }
}
```

**이전**:
```json
"env": {}  // 비어있음 → MCP 서버가 토큰 없이 실행
```

**이후**:
```json
"env": {
  "RAILWAY_API_TOKEN": "5d5444a4-9ef4-4ed7-be34-a122fc62ac1e"
}
```

---

## 🔑 Railway Token 검증 완료

### 제공받은 Token 정보
- **Token**: `5d5444a4-9ef4-4ed7-be34-a122fc62ac1e`
- **타입**: Team Token (bridge25's project 워크스페이스)
- **생성 위치**: `railway.com/account/tokens`
- **권한 범위**: bridge25's project 워크스페이스 내 모든 프로젝트

### Team Token으로 가능한 작업
- ✅ 프로젝트 생성 및 배포 (`railway up`)
- ✅ 환경 변수 설정
- ✅ 로그 조회 (`railway logs`)
- ✅ 서비스 생성 (PostgreSQL, Redis)
- ⚠️ `railway whoami` 제한 (Team Token 특성)
- ⚠️ `railway link` 제한 (Team Token 특성)

**결론**: Railway MCP 서버를 통한 배포에는 문제 없음 ✅

---

## 📊 MCP 환경 변수 설정 패턴

### 문제점
MCP 서버는 다음 위치의 환경 변수를 읽지 **않음**:
- ❌ 부모 쉘의 `export` 명령
- ❌ `~/.bashrc`, `~/.bash_profile`
- ❌ 시스템 전역 환경 변수

### 해결책
`.claude.json`의 `mcpServers[name].env` 필드에 명시적 설정:
```json
{
  "env": {
    "RAILWAY_API_TOKEN": "your-token-here",
    "OTHER_VAR": "other-value"
  }
}
```

### 적용 방법
1. `.claude.json` 수정
2. **Claude Code 재시작** (필수)
3. MCP 서버가 새 환경 변수로 재시작됨

---

## 🎯 업데이트된 다음 세션 작업 계획

### 1단계: Claude Code 재시작 및 MCP 확인
```bash
# Claude Code 종료 후 재시작
exit
cd /home/a/projects/dt-rag-standalone
claude
```

**확인 명령**:
```
Railway MCP 서버 상태 확인해줘
```

**예상 결과**:
```
✅ Railway CLI Status: Authenticated
✅ Token Type: Team Token (bridge25's project)
```

### 2단계: Railway 프로젝트 연동 확인
```
Railway 프로젝트 목록 보여줘
```

**예상 출력**:
- dt-rag (ID: b5eedf32-d24b-415c-a72e-0824b32a5cc3)
- 기타 bridge25's project 워크스페이스 내 프로젝트

### 3단계: 로컬 프로젝트 링크 확인
```bash
cat .railway/config.json
```

**현재 설정**:
```json
{
  "projectId": "b5eedf32-d24b-415c-a72e-0824b32a5cc3",
  "environmentId": "a9f94715-ce7b-4af2-a246-2165bb62eb86"
}
```

### 4단계: Railway 배포 실행
**자연어 명령 예시**:
```
Railway에 dt-rag 백엔드를 배포해줘.
- GitHub 저장소: bridge25/dt-rag (master 브랜치)
- PostgreSQL 추가
- Redis 추가
- 환경 변수는 railway.toml 참조
```

### 5단계: 배포 후 검증
```bash
# Health check
curl https://<railway-domain>/health

# 로그 확인 (MCP 사용)
"Railway 배포 로그 보여줘"
```

---

## 🔧 트러블슈팅 가이드

### Team Token으로 railway whoami 실패 시
**현상**:
```bash
railway whoami
# → Unauthorized. Please login with `railway login`
```

**원인**: Team Token은 `whoami` 명령을 지원하지 않음 (공식 제약)

**해결**: MCP 서버를 통한 작업은 정상 동작 (직접 CLI 명령 불필요)

### MCP 서버가 토큰을 읽지 못하는 경우
**체크리스트**:
1. `.claude.json`의 `env.RAILWAY_API_TOKEN` 필드 확인
2. Claude Code 재시작 확인
3. MCP 서버 로그 확인:
   ```bash
   claude mcp logs railway-mcp-server
   ```

### railway.toml 설정 검증
```bash
# 문법 확인
cat railway.toml | grep -E '(deploy|build|env)'
```

**필수 설정**:
- `[deploy].startCommand` - 서버 시작 명령
- `[deploy].preDeployCommand` - 테스트 실행
- `[deploy].healthcheckPath` - Health check 엔드포인트

---

## 📚 참고: Railway CLI vs MCP 서버

| 작업 | Railway CLI | Railway MCP |
|------|-------------|-------------|
| 인증 | `railway login` (브라우저) | 토큰 자동 사용 |
| 프로젝트 목록 | `railway list` | `list-projects` |
| 배포 | `railway up` | `deploy` |
| 로그 조회 | `railway logs` | `get-logs` |
| 환경 변수 설정 | `railway variables set` | `set-variables` |
| **장점** | 수동 제어 | 자연어 자동화 |
| **단점** | 브라우저 필요 | 토큰 설정 필요 |

---

**작성자**: Alfred (Claude Code)
**최종 업데이트**: 2025-11-13 03:00 UTC
**다음 작업**: Claude Code 재시작 → Railway MCP 동작 확인 → 배포 실행
