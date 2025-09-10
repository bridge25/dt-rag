# 🎨 C팀 (Frontend Admin) 온보딩 가이드

## 📋 PR-1 완료! 이제 C팀 착수 가능

**A팀의 OpenAPI v1.8.1 스펙이 준비되었습니다.** TypeScript 클라이언트를 생성하여 안전하게 개발할 수 있습니다.

## 🎯 C팀 첫 실행 명령어

### 1단계: 환경 설정
```bash
# 저장소 클론 및 이동 
git clone https://github.com/bridge25/Unmanned.git
cd Unmanned

# Node.js 20 확인
node --version  # v20.x.x 확인

# OpenAPI Generator 설치
npm install -g @openapitools/openapi-generator-cli
```

### 2단계: C팀 스택드 PR 생성
```bash
# 최신 상태 가져오기
git fetch origin

# PR-1 기반으로 C팀 브랜치 생성
git switch -c dt-rag/feat/c-tree-ui origin/dt-rag/feat/common-schemas-sync

# C팀 앱 디렉토리 초기화
mkdir -p dt-rag/apps/frontend-admin/{src,public,docs}
echo "# Frontend Admin UI (Team C)" > dt-rag/apps/frontend-admin/README.md

# 초기 커밋
git add dt-rag/apps/frontend-admin
git commit -m "chore(dt-rag/frontend): scaffold admin app"
git push -u origin dt-rag/feat/c-tree-ui

# 스택드 드래프트 PR 생성
gh pr create --repo bridge25/Unmanned \
  --base dt-rag/feat/common-schemas-sync \
  --head dt-rag/feat/c-tree-ui \
  --title "feat(dt-rag/frontend): scaffold admin UI" \
  --body "Stacked on PR-1; UI path CI" --draft
```

### 3단계: TypeScript 클라이언트 생성
```bash
cd dt-rag/apps/frontend-admin

# OpenAPI 스펙으로부터 TypeScript 클라이언트 생성
openapi-generator-cli generate \
  -i ../../docs/openapi.yaml \
  -g typescript-axios \
  -o src/generated/api-client \
  --additional-properties=supportsES6=true,withSeparateModelsAndApi=true,modelPropertyNaming=original

# Next.js 프로젝트 초기화
npx create-next-app@latest . --typescript --tailwind --eslint --app

# 의존성 설치
npm install axios lucide-react @radix-ui/react-select
npm install -D @types/node
```

### 4단계: 초기 트리뷰 UI 구현
```bash
# API 클라이언트 설정
cat > src/lib/api.ts << EOF
import { DefaultApi, Configuration } from '../generated/api-client';

const apiConfig = new Configuration({
  basePath: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
});

export const taxonomyApi = new DefaultApi(apiConfig);
EOF

# 트리뷰 컴포넌트 생성
mkdir -p src/components
cat > src/components/TaxonomyTree.tsx << EOF
'use client';

import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Folder, File } from 'lucide-react';

interface TreeNode {
  id: string;
  label: string;
  children?: TreeNode[];
  isExpanded?: boolean;
}

export function TaxonomyTree() {
  const [treeData, setTreeData] = useState<TreeNode[]>([
    {
      id: 'ai',
      label: 'AI',
      children: [
        { id: 'ml', label: 'Machine Learning' },
        { id: 'rag', label: 'RAG Systems' }
      ]
    }
  ]);

  return (
    <div className="p-4 border rounded-lg">
      <h2 className="text-lg font-semibold mb-4">Taxonomy Tree (v1.8.1)</h2>
      {/* TODO: 실제 API 연동 */}
      <div className="text-sm text-gray-500">
        🚧 Mock UI - API 연동 예정
      </div>
    </div>
  );
}
EOF

# 메인 페이지 업데이트
cat > src/app/page.tsx << EOF
import { TaxonomyTree } from '@/components/TaxonomyTree';

export default function Home() {
  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Dynamic Taxonomy RAG Admin</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <TaxonomyTree />
        <div className="p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-4">분류 테스트</h2>
          <div className="text-sm text-gray-500">
            🚧 분류 UI - 구현 예정
          </div>
        </div>
      </div>
    </main>
  );
}
EOF
```

## 🛠️ C팀 주요 작업 범위

### Phase 1: 트리형 UI 구현
1. **계층형 트리뷰** (expand/collapse)
2. **노드 선택/이동** (drag & drop)
3. **버전 관리** (v1.8.1 기반)
4. **실시간 업데이트** (WebSocket)

### Phase 2: 관리 기능
- **분류 테스트 도구** (chunk 입력 → 분류 결과)
- **HITL 큐 관리** (낮은 confidence 수동 처리)
- **성능 모니터링 대시보드** (p95/p50 응답시간)
- **감사 로그 뷰어** (분류 이력 추적)

### Phase 3: UX 최적화
- **반응형 디자인** (모바일 지원)
- **접근성** (ARIA, 키보드 네비게이션)
- **다크모드** (사용자 설정)
- **국제화** (i18n 준비)

## 📦 권장 기술 스택

### Core
- **Next.js 14** (App Router)
- **TypeScript** (타입 안전성)
- **Tailwind CSS** (스타일링)

### UI Components
- **Radix UI** (접근성)
- **Lucide React** (아이콘)
- **React Hook Form** (폼 관리)

### State Management
- **Zustand** (가벼운 상태 관리)
- **TanStack Query** (서버 상태)

## 📊 CI/CD 자동화

C팀 전용 CI가 자동 설정됩니다:
- 경로 필터: `dt-rag/apps/frontend-admin/**`
- TypeScript 빌드 테스트
- ESLint, Prettier 검사

## 🔗 API 연동 가이드

### 생성된 클라이언트 사용
```typescript
import { taxonomyApi } from '@/lib/api';
import { ClassifyRequest } from '@/generated/api-client';

// 분류 요청
const classifyText = async (text: string) => {
  try {
    const request: ClassifyRequest = {
      chunk_id: `chunk_${Date.now()}`,
      text: text,
      hint_paths: [["AI", "RAG"]]
    };
    
    const response = await taxonomyApi.classifyPost(request);
    return response.data;
  } catch (error) {
    console.error('Classification failed:', error);
  }
};

// 검색 요청
const searchDocuments = async (query: string) => {
  try {
    const response = await taxonomyApi.searchPost({
      q: query,
      final_topk: 5
    });
    return response.data;
  } catch (error) {
    console.error('Search failed:', error);
  }
};
```

## 🚨 중요 규칙

1. **폴더 규칙**: `dt-rag/apps/frontend-admin/` 내에서만 작업
2. **API 스펙 준수**: OpenAPI v1.8.1 클라이언트만 사용
3. **드래프트 PR**: CI 그린 + 리뷰 1+ 후 머지
4. **환경변수**: `.env.local`은 절대 커밋 금지

## 🎨 디자인 가이드라인

### 색상 팔레트
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Warning**: Amber (#F59E0B)
- **Error**: Red (#EF4444)

### 컴포넌트 스타일
- **카드**: `border rounded-lg p-4`
- **버튼**: `px-4 py-2 rounded-md`
- **입력**: `border rounded-md px-3 py-2`

## 📞 지원 채널

- **기술 문의**: Slack #dynamic-taxonomy-rag
- **A팀 연락**: team-a@example.com  
- **GitHub 이슈**: PR 코멘트 활용
- **UI/UX 논의**: Slack #frontend-design

---
**Generated**: 2025-09-04  
**Base PR**: #3 (dt-rag/feat/common-schemas-sync)  
**Team**: C팀 (Frontend Admin)