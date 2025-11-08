# 프론트엔드 스크린샷 촬영 가이드

백엔드 없이 프론트엔드 UI 스크린샷을 촬영하는 방법

## 개요

백엔드 API 서버 없이도 프론트엔드 UI를 화면 캡처할 수 있습니다.
- **MSW (Mock Service Worker)**: API 요청을 브라우저에서 가로채어 mock 응답 제공
- **Playwright**: 헤드리스 브라우저로 자동 스크린샷 촬영

## 전제 조건

```bash
# Playwright가 설치되어 있어야 함
pip install playwright
playwright install chromium

# MSW가 프로젝트에 설치되어 있어야 함
# package.json devDependencies에 msw가 있는지 확인
```

## 단계별 절차

### 1. MSW 설정 파일 생성

**1-1. Mock 데이터 정의** (`frontend/src/mocks/data.ts`)
```typescript
// TEMPORARY: Mock data for UI preview
export const mockInventoryRAW = [
  { id: 1, item_id: 101, site_id: 1, current_stock: 500, reserved_stock: 100, available_stock: 400 },
  // ... 실제 데이터 구조에 맞게 작성
];
```

**1-2. API 핸들러 정의** (`frontend/src/mocks/handlers.ts`)
```typescript
// TEMPORARY: MSW handlers for UI preview
import { http, HttpResponse } from 'msw';
import { mockInventoryRAW } from './data';

export const handlers = [
  // 실제 API 엔드포인트 경로에 맞춰 작성
  http.get('/api/v1/inventory', ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get('category');
    if (category === 'RAW') return HttpResponse.json(mockInventoryRAW);
    return HttpResponse.json([]);
  }),

  // 모든 미처리 요청에 대한 fallback
  http.get('/api/v1/*', () => HttpResponse.json([])),
];
```

**1-3. Worker 설정** (`frontend/src/mocks/browser.ts`)
```typescript
// TEMPORARY: MSW browser setup for UI preview
import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);
```

### 2. 앱에 MSW 초기화 추가

**`frontend/src/main.tsx` 수정**
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// TEMPORARY: MSW for UI preview only in development
async function enableMocking() {
  if (import.meta.env.DEV) {
    const { worker } = await import('./mocks/browser')
    return worker.start({ onUnhandledRequest: 'bypass' })
  }
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
```

### 3. 인증 우회 (필요시)

**ProtectedRoute 컴포넌트 임시 수정**
```typescript
// TEMPORARY: Authentication bypass for screenshot
interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  return <>{children}</>;
}
```

### 4. MSW Service Worker 초기화

```bash
cd frontend
npx msw init public/ --save
```

이 명령은 다음을 수행합니다:
- `public/mockServiceWorker.js` 파일 생성
- `package.json`에 MSW 설정 추가

### 5. 개발 서버 실행

```bash
npm run dev
# 서버가 http://localhost:3000 등에서 실행됨
```

브라우저 콘솔에서 MSW 활성화 메시지 확인:
```
[MSW] Mocking enabled.
```

### 6. Playwright 스크린샷 스크립트 작성

**데스크톱 + 모바일 스크린샷** (`take_screenshots.py`)
```python
from playwright.sync_api import sync_playwright
import time

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # Desktop screenshots
        print("Taking desktop screenshots...")
        page_desktop = browser.new_page(viewport={'width': 1920, 'height': 1080})

        pages = [
            ('http://localhost:3000/login', 'screenshots/01_login.png', 'Login'),
            ('http://localhost:3000/overview', 'screenshots/02_overview.png', 'Overview'),
            ('http://localhost:3000/calendar', 'screenshots/03_calendar.png', 'Calendar'),
        ]

        for url, path, name in pages:
            print(f"Taking {name} screenshot...")
            page_desktop.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(4)  # 컴포넌트 렌더링 대기
            page_desktop.screenshot(path=path, full_page=True)
            print(f"{name} screenshot saved")

        page_desktop.close()

        # Mobile screenshots (iPhone X size: 375x812)
        print("\nTaking mobile screenshots...")
        page_mobile = browser.new_page(viewport={'width': 375, 'height': 812})

        mobile_pages = [
            ('http://localhost:3000/login', 'screenshots/mobile_01_login.png', 'Login'),
            ('http://localhost:3000/overview', 'screenshots/mobile_02_overview.png', 'Overview'),
        ]

        for url, path, name in mobile_pages:
            print(f"Taking mobile {name} screenshot...")
            page_mobile.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(4)
            page_mobile.screenshot(path=path, full_page=True)
            print(f"Mobile {name} screenshot saved")

        page_mobile.close()
        browser.close()
        print("\nAll screenshots completed!")

if __name__ == '__main__':
    take_screenshots()
```

### 7. 스크린샷 촬영 실행

```bash
python3 take_screenshots.py
```

**출력 예시:**
```
Taking desktop screenshots...
Taking Login screenshot...
Login screenshot saved
Taking Overview screenshot...
Overview screenshot saved
...
All screenshots completed!
```

### 8. 원상복구

**임시 파일 삭제:**
```bash
# MSW 파일 삭제
rm -rf frontend/src/mocks
rm -f frontend/public/mockServiceWorker.js

# 스크립트 삭제
rm -f take_screenshots.py
```

**수정된 파일 복원:**
```bash
cd frontend
git restore src/main.tsx
git restore src/components/auth/ProtectedRoute.tsx
git restore package.json
```

**상태 확인:**
```bash
git status
# MSW 관련 변경사항이 모두 제거되었는지 확인
```

## 주요 팁

### API 엔드포인트 확인 방법

**1. API 서비스 파일 확인**
```bash
# React Query 사용 시
grep -r "useQuery" frontend/src/hooks/
grep -r "apiClient.get" frontend/src/services/
```

**2. 브라우저 DevTools Network 탭**
- 실제 백엔드와 연결 시 어떤 API가 호출되는지 확인
- Request URL과 Response 구조 파악

### 한글 폰트 문제 해결

WSL 환경에서 한글이 깨질 경우:
```bash
sudo apt-get update
sudo apt-get install -y fonts-nanum fonts-noto-cjk
```

### 타임아웃 에러 발생 시

**증상:** `Page.goto: Timeout 30000ms exceeded`

**원인:** MSW가 특정 API 요청을 처리하지 못함

**해결:**
1. 브라우저 DevTools Console에서 어떤 API가 실패했는지 확인
2. `handlers.ts`에 누락된 엔드포인트 추가:
```typescript
// 모든 미처리 요청에 빈 배열 반환
http.get('/api/v1/*', () => HttpResponse.json([])),
```

### wait_until 옵션

```python
# networkidle: 네트워크 요청이 모두 완료될 때까지 대기 (권장하지 않음)
page.goto(url, wait_until='networkidle', timeout=30000)

# domcontentloaded: DOM이 로드되면 바로 진행 (권장)
page.goto(url, wait_until='domcontentloaded', timeout=30000)
```

MSW 사용 시 `domcontentloaded`가 더 안정적입니다.

## 모바일 뷰포트 크기

```python
# iPhone SE (구형)
viewport={'width': 320, 'height': 568}

# iPhone X/11/12/13 (일반)
viewport={'width': 375, 'height': 812}

# iPhone 14 Pro Max (대형)
viewport={'width': 430, 'height': 932}

# iPad (태블릿)
viewport={'width': 768, 'height': 1024}
```

## 체크리스트

스크린샷 촬영 전:
- [ ] MSW 패키지 설치 확인 (`package.json`)
- [ ] Playwright 설치 (`pip install playwright`)
- [ ] 크롬 브라우저 설치 (`playwright install chromium`)
- [ ] 촬영할 페이지 목록 작성
- [ ] 각 페이지의 API 엔드포인트 파악

작업 후:
- [ ] MSW 임시 파일 삭제 확인
- [ ] Git 상태 확인 (`git status`)
- [ ] 원상복구 완료 확인
- [ ] 스크린샷 폴더 생성 확인

## 참고 자료

- [MSW 공식 문서](https://mswjs.io/)
- [Playwright 공식 문서](https://playwright.dev/python/)
- [React Query Devtools](https://tanstack.com/query/latest/docs/framework/react/devtools)
