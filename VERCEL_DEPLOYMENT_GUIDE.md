# Vercel 배포 가이드 - DT-RAG Frontend

## CLI로 직접 배포하기

### 1단계: Vercel 로그인
```bash
cd /home/a/projects/dt-rag-standalone/apps/frontend
vercel login
```

### 2단계: 프로젝트 초기 배포
```bash
vercel
```

**질문에 답변:**
- Set up and deploy "~/projects/dt-rag-standalone/apps/frontend"? → **Y**
- Which scope do you want to deploy to? → **Select your account**
- Link to existing project? → **N**
- What's your project's name? → **dt-rag-frontend** (또는 원하는 이름)
- In which directory is your code located? → **./** (Enter)
- Want to override the settings? → **N**

### 3단계: 환경 변수 설정
```bash
vercel env add NEXT_PUBLIC_API_URL
→ Value: https://dt-rag-production.up.railway.app
→ Environment: Production, Preview, Development

vercel env add NEXT_PUBLIC_API_TIMEOUT
→ Value: 30000
→ Environment: Production, Preview, Development
```

### 4단계: Production 배포
```bash
vercel --prod
```

## 배포 후 확인사항

### 1. 배포 URL 확인
```bash
vercel ls
```

### 2. 로그 확인
```bash
vercel logs
```

### 3. 도메인 설정 (선택사항)
```bash
# 커스텀 도메인 추가
vercel domains add your-domain.com

# DNS 설정
vercel domains inspect your-domain.com
```

## 자동 배포 설정

### Git 자동 배포 활성화

Vercel은 GitHub 저장소와 연동하면 자동으로:
- **main/master 브랜치 push** → Production 배포
- **다른 브랜치 push** → Preview 배포
- **Pull Request** → Preview 배포 + 댓글

설정 방법:
1. Vercel Dashboard → 프로젝트 선택
2. Settings → Git → GitHub 저장소 연결
3. Production Branch: **main** (또는 master)

## 환경 변수 관리

### Vercel Dashboard에서 설정
```
프로젝트 선택 → Settings → Environment Variables

NEXT_PUBLIC_API_URL
- Production: https://dt-rag-production.up.railway.app
- Preview: https://dt-rag-production.up.railway.app (또는 staging URL)
- Development: http://localhost:8000
```

### CLI로 확인
```bash
# 환경 변수 목록
vercel env ls

# 특정 변수 가져오기
vercel env pull .env.local
```

## 배포 최적화 팁

### 1. 빌드 캐싱 활성화
Vercel은 자동으로 node_modules, .next 캐싱

### 2. 이미지 최적화
Next.js Image 컴포넌트는 Vercel CDN 자동 최적화

### 3. Analytics 활성화 (선택사항)
```
프로젝트 → Analytics → Enable
→ 실시간 페이지 뷰, 성능 메트릭
```

### 4. Edge Network 활용
Vercel은 자동으로 전 세계 CDN 배포

## 문제 해결

### 빌드 실패
```bash
# 로컬에서 빌드 테스트
cd apps/frontend
npm run build

# Vercel 빌드 로그 확인
vercel logs --output build
```

### 환경 변수 적용 안 됨
```bash
# 환경 변수 재배포
vercel --prod --force
```

### CORS 에러
백엔드(Railway)에서 Vercel 도메인 허용:
```python
# apps/api/main.py
CORS_ORIGINS = [
    "https://your-project.vercel.app",
    "https://dt-rag-production.up.railway.app"
]
```

## 유용한 명령어

```bash
# 배포 상태 확인
vercel inspect

# 특정 배포 롤백
vercel rollback

# 프로젝트 삭제
vercel remove

# Vercel 버전 확인
vercel --version

# 도움말
vercel --help
```

## 비용 정보

### Hobby (무료)
- ✅ 무제한 배포
- ✅ 100GB 대역폭/월
- ✅ Serverless Functions
- ✅ Edge Network
- ⚠️ 개인 프로젝트만

### Pro ($20/월)
- ✅ 팀 협업
- ✅ 1TB 대역폭/월
- ✅ Analytics
- ✅ 우선 지원

## 참고 링크

- Vercel 문서: https://vercel.com/docs
- Next.js 배포: https://nextjs.org/docs/deployment
- Vercel CLI: https://vercel.com/docs/cli
- 환경 변수: https://vercel.com/docs/environment-variables
