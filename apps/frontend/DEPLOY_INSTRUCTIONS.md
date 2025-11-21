# 🚀 Vercel CLI 배포 가이드

## 빠른 시작 (자동 스크립트)

### 옵션 1: 자동 배포 스크립트 실행

```bash
cd /home/a/projects/dt-rag-standalone/apps/frontend
bash deploy-to-vercel.sh
```

**스크립트가 자동으로:**
1. ✅ 환경 확인 (Node.js, Vercel CLI)
2. ✅ Vercel 로그인 (브라우저 열림)
3. ✅ Preview 배포 (대화형 질문)
4. ✅ 환경 변수 설정
5. ✅ Production 배포

---

## 수동 배포 (단계별 명령어)

### 1단계: 디렉토리 이동 및 확인

```bash
cd /home/a/projects/dt-rag-standalone/apps/frontend
pwd
# 출력: /home/a/projects/dt-rag-standalone/apps/frontend

ls package.json
# 출력: package.json 확인
```

---

### 2단계: Vercel 로그인

```bash
vercel login
```

**브라우저가 자동으로 열립니다:**
1. GitHub 계정 선택
2. "Authorize Vercel" 클릭
3. 터미널로 돌아오면 완료

**확인:**
```bash
vercel whoami
# 출력: your-username
```

---

### 3단계: 초기 배포 (Preview)

```bash
vercel
```

**대화형 질문:**

```
? Set up and deploy "~/projects/dt-rag-standalone/apps/frontend"? (Y/n)
답변: Y

? Which scope do you want to deploy to? (Use arrow keys)
답변: [당신의 계정 선택] → Enter

? Link to existing project? (y/N)
답변: N

? What's your project's name? (frontend)
답변: dt-rag-frontend

? In which directory is your code located? (./)
답변: Enter (기본값 사용)

Auto-detected Project Settings (Next.js):
- Build Command: next build
- Development Command: next dev --port $PORT
- Install Command: `yarn install`, `pnpm install`, or `npm install`
- Output Directory: Next.js default

? Want to modify these settings? (y/N)
답변: N
```

**빌드 시작:**
```
🔍  Inspect: https://vercel.com/xxx/dt-rag-frontend/xxx
✅  Preview: https://dt-rag-frontend-xxx.vercel.app
```

**Preview URL이 생성됩니다!** (아직 환경 변수 없음)

---

### 4단계: 환경 변수 설정

#### 4-1. NEXT_PUBLIC_API_URL 추가

```bash
vercel env add NEXT_PUBLIC_API_URL
```

**대화형 질문:**
```
? What's the value of NEXT_PUBLIC_API_URL?
답변: https://dt-rag-production.up.railway.app

? Add NEXT_PUBLIC_API_URL to which Environments? (Press <space> to select, <a> to toggle all, <i> to invert selection)
답변: 스페이스바로 모두 선택
  ◉ Production
  ◉ Preview
  ◉ Development
→ Enter

✅ Added Environment Variable NEXT_PUBLIC_API_URL
```

#### 4-2. NEXT_PUBLIC_API_TIMEOUT 추가

```bash
vercel env add NEXT_PUBLIC_API_TIMEOUT
```

**대화형 질문:**
```
? What's the value of NEXT_PUBLIC_API_TIMEOUT?
답변: 30000

? Add NEXT_PUBLIC_API_TIMEOUT to which Environments?
답변: 스페이스바로 모두 선택
  ◉ Production
  ◉ Preview
  ◉ Development
→ Enter

✅ Added Environment Variable NEXT_PUBLIC_API_TIMEOUT
```

#### 환경 변수 확인

```bash
vercel env ls
```

**출력:**
```
Environment Variables for Project dt-rag-frontend

  name                        value      created
  NEXT_PUBLIC_API_URL         Encrypted  2s ago
  NEXT_PUBLIC_API_TIMEOUT     Encrypted  1s ago
```

---

### 5단계: Production 배포

```bash
vercel --prod
```

**자동 프로세스:**
```
🔍 Inspecting deployment...
📦 Building...
   ▲ Next.js 14.2.33
   ✓ Creating an optimized production build
   ✓ Compiled successfully
   ✓ Linting and checking validity of types
   ✓ Collecting page data
   ✓ Generating static pages (13/13)
   ✓ Finalizing page optimization

✅ Production: https://dt-rag-frontend.vercel.app
```

**Production URL이 생성됩니다!** 🎉

---

## 배포 후 확인사항

### 1. 배포 목록 확인

```bash
vercel ls
```

**출력:**
```
dt-rag-frontend
  url                               deployment    status
  dt-rag-frontend.vercel.app        123abc        Ready
  dt-rag-frontend-xxx.vercel.app    456def        Ready (Preview)
```

### 2. 상세 정보 확인

```bash
vercel inspect
```

**출력:**
```
General
  id              123abc456def
  name            dt-rag-frontend
  status          READY
  url             https://dt-rag-frontend.vercel.app
  created         2m ago

Build
  framework       Next.js
  node version    22.x
  build time      54s

Environment Variables
  NEXT_PUBLIC_API_URL        https://dt-rag-production.up.railway.app
  NEXT_PUBLIC_API_TIMEOUT    30000
```

### 3. 로그 확인

```bash
vercel logs
```

### 4. 실제 접속 테스트

```bash
curl -I https://dt-rag-frontend.vercel.app
```

**예상 출력:**
```
HTTP/2 200
content-type: text/html; charset=utf-8
x-vercel-id: sfo1::xxxxx
```

**브라우저에서 접속:**
```
https://dt-rag-frontend.vercel.app
```

---

## 문제 해결

### 빌드 실패 시

```bash
# 로컬에서 빌드 테스트
npm run build

# Vercel 빌드 로그 확인
vercel logs --output build
```

### 환경 변수 적용 안 됨

```bash
# 환경 변수 재확인
vercel env ls

# 강제 재배포
vercel --prod --force
```

### 로그인 문제

```bash
# 로그아웃 후 재로그인
vercel logout
vercel login
```

### CORS 에러 발생 시

백엔드에 Vercel 도메인 추가 필요:

```python
# Railway apps/api/main.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://dt-rag-frontend.vercel.app",
    "https://dt-rag-frontend-*.vercel.app",  # Preview 배포용
]
```

---

## Git 자동 배포 설정 (선택사항)

### Vercel Dashboard에서 설정

1. https://vercel.com/dashboard → 프로젝트 선택
2. Settings → Git → Connect GitHub Repository
3. Repository: dt-rag-standalone
4. Production Branch: main

**설정 후:**
- `git push origin main` → Production 자동 배포
- `git push origin feature-branch` → Preview 자동 배포
- Pull Request 생성 → Preview 자동 배포 + 댓글

---

## 유용한 명령어

```bash
# 배포 상태 확인
vercel inspect

# 특정 배포 롤백
vercel rollback [deployment-url]

# 프로젝트 삭제
vercel remove dt-rag-frontend

# 도메인 추가 (선택사항)
vercel domains add your-domain.com

# 환경 변수 로컬 다운로드
vercel env pull .env.local

# 텔레메트리 비활성화
vercel telemetry disable
```

---

## 배포 체크리스트

- [ ] Vercel 계정 생성 (GitHub 로그인)
- [ ] Vercel CLI 설치 확인
- [ ] `vercel login` 완료
- [ ] Preview 배포 성공
- [ ] 환경 변수 2개 추가
- [ ] Production 배포 성공
- [ ] URL 접속 확인
- [ ] API 연동 테스트
- [ ] Git 자동 배포 설정 (선택)

---

## 예상 소요 시간

- Vercel 로그인: 1분
- Preview 배포: 2-3분
- 환경 변수 설정: 2분
- Production 배포: 2-3분

**총 소요 시간: 약 8-10분**

---

## 다음 단계

배포가 완료되면:

1. ✅ 프론트엔드 URL 확인
2. ✅ 백엔드 연동 테스트
3. ✅ 주요 기능 동작 확인:
   - Dashboard 페이지
   - Search 기능
   - Documents 업로드
   - Taxonomy 트리
4. ✅ 커스텀 도메인 설정 (선택)
5. ✅ Git 자동 배포 활성화 (선택)

---

## 참고 링크

- Vercel CLI 문서: https://vercel.com/docs/cli
- Next.js 배포 가이드: https://nextjs.org/docs/deployment
- 환경 변수 설정: https://vercel.com/docs/environment-variables
- 커스텀 도메인: https://vercel.com/docs/custom-domains
