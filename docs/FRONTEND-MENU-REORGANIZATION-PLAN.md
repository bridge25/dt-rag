# Frontend Menu Reorganization Plan

**SPEC Reference**: SPEC-FRONTEND-REDESIGN-001
**Date**: 2025-11-28
**Status**: Planning Complete → Ready for Implementation

---

## Executive Summary

DT-RAG 프론트엔드의 메뉴 구조를 **이벤트 플로우 중심**으로 재구성합니다.
핵심 원칙: "Taxonomy(땅)에서 Agent(생명)가 탄생하고, 성장하며, 세상과 연결된다"

### Current vs Target Structure

| 현재 순서 | 변경 후 순서 |
|-----------|--------------|
| 1. Dashboard | 1. Dashboard |
| 2. Search | 2. **Taxonomy** ← 시작점 |
| 3. Documents | 3. **Agents** ← Taxonomy에서 탄생 |
| 4. Taxonomy | 4. **Chat** (Search 리브랜딩) |
| 5. Agents | 5. **Connect** (신규) |
| 6. Pipeline | 6. **System** ▼ (서브메뉴) |
| 7. HITL Review | → Pipeline |
| 8. Monitoring | → HITL Review |
| | → Monitoring |

---

## Progress Tracking

### Overall Progress

| Phase | 상태 | 진행률 | 시작일 | 완료일 |
|-------|------|--------|--------|--------|
| Phase 1 | ✅ 완료 | 100% | 2025-11-28 | 2025-11-28 |
| Phase 2 | ✅ 완료 | 100% | 2025-11-28 | 2025-11-28 |
| Phase 3 | ✅ 완료 | 100% | 2025-11-28 | 2025-11-28 |
| Phase 4 | ✅ 완료 | 100% | 2025-11-28 | 2025-11-28 |

**상태 범례**: ⬜ 대기 | 🔄 진행중 | ✅ 완료 | ⏸️ 보류

---

## Phase 1: Quick Wins (예상 1일)

### Phase 1 Progress: ✅ 12/12 완료

#### 1.1 Sidebar Navigation 재구성

**File**: `apps/frontend/components/layout/Sidebar.tsx`

| # | 작업 | 파일:라인 | 상태 | 완료일 |
|---|------|-----------|------|--------|
| 1.1.1 | [x] `MessageSquare` 아이콘 import 추가 | `Sidebar.tsx:13` | ✅ | 2025-11-28 |
| 1.1.2 | [x] `Plug` 아이콘 import 추가 (Connect용) | `Sidebar.tsx:11` | ⏸️ Phase 4 | |
| 1.1.3 | [x] navigation 배열에서 Taxonomy를 2번째로 이동 | `Sidebar.tsx:27` | ✅ | 2025-11-28 |
| 1.1.4 | [x] navigation 배열에서 Agents를 3번째로 이동 | `Sidebar.tsx:28` | ✅ | 2025-11-28 |
| 1.1.5 | [x] Search → Chat으로 name 변경 | `Sidebar.tsx:29` | ✅ | 2025-11-28 |
| 1.1.6 | [x] Search 아이콘 → MessageSquare로 변경 | `Sidebar.tsx:29` | ✅ | 2025-11-28 |
| 1.1.7 | [x] 변경 후 브라우저에서 사이드바 확인 | 브라우저 테스트 | ✅ | 2025-11-28 |

**변경 전 코드** (Line 25-34):
```typescript
const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Search", href: "/search", icon: Search },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Taxonomy", href: "/taxonomy", icon: Network },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Pipeline", href: "/pipeline", icon: Workflow },
  { name: "HITL Review", href: "/hitl", icon: UserCheck },
  { name: "Monitoring", href: "/monitoring", icon: Activity },
];
```

**변경 후 코드**:
```typescript
const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Taxonomy", href: "/taxonomy", icon: Network },      // 2. 시작점
  { name: "Agents", href: "/agents", icon: Bot },               // 3. 탄생
  { name: "Chat", href: "/search", icon: MessageSquare },       // 4. 채팅
  { name: "Pipeline", href: "/pipeline", icon: Workflow },
  { name: "HITL Review", href: "/hitl", icon: UserCheck },
  { name: "Monitoring", href: "/monitoring", icon: Activity },
];
```

---

#### 1.2 Search → Chat 리브랜딩

**File**: `apps/frontend/app/(dashboard)/search/page.tsx`

| # | 작업 | 파일:라인 | 상태 | 완료일 |
|---|------|-----------|------|--------|
| 1.2.1 | [x] 페이지 타이틀 변경: "Command Center" → "Neural Chat" | `search/page.tsx:54` | ✅ | 2025-11-28 |
| 1.2.2 | [x] 설명 텍스트 변경 | `search/page.tsx:57` | ✅ | 2025-11-28 |
| 1.2.3 | [x] placeholder 변경: "Initiate search sequence..." → "Ask your question..." | `search/page.tsx:86` | ✅ | 2025-11-28 |
| 1.2.4 | [x] 버튼 텍스트 변경: "EXECUTE SEARCH" → "SEND MESSAGE" | `search/page.tsx:145` | ✅ | 2025-11-28 |
| 1.2.5 | [x] 변경 후 브라우저에서 Chat 페이지 확인 | 브라우저 테스트 | ✅ | 2025-11-28 |

**변경 상세**:

| 위치 | 변경 전 | 변경 후 |
|------|---------|---------|
| Line 52 | `Command Center` | `Neural Chat` |
| Line 56 | `Access the neural network...` | `Engage with your intelligent agents` |
| Line 86 | `Initiate search sequence...` | `Ask your question...` |
| Line 145 | `EXECUTE SEARCH` | `SEND MESSAGE` |

---

### Phase 1 Completion Checklist

```
Phase 1 완료 조건:
[x] 모든 1.1.x 작업 완료
[x] 모든 1.2.x 작업 완료
[x] 사이드바 순서: Dashboard → Taxonomy → Agents → Chat → ...
[x] Chat 페이지 UI 리브랜딩 확인
[x] 기존 검색 기능 정상 동작 확인
[x] 콘솔 에러 없음 확인

Phase 1 완료일: 2025-11-28
Phase 1 완료자: Alfred (MoAI-ADK)
```

---

## Phase 2: System Submenu (예상 2-3일)

### Phase 2 Progress: ✅ 10/10 완료

#### 2.1 SidebarSubmenu 컴포넌트 생성

**New File**: `apps/frontend/components/layout/SidebarSubmenu.tsx`

| # | 작업 | 파일 | 상태 | 완료일 |
|---|------|------|------|--------|
| 2.1.1 | [x] SidebarSubmenu.tsx 파일 생성 | `components/layout/SidebarSubmenu.tsx` | ✅ | 2025-11-28 |
| 2.1.2 | [x] useState로 isOpen 상태 관리 구현 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 2.1.3 | [x] ChevronDown 토글 아이콘 (회전 애니메이션) | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 2.1.4 | [x] 하위 메뉴 아이템 렌더링 + 활성 상태 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 2.1.5 | [x] animate-in 애니메이션 적용 | 컴포넌트 내부 | ✅ | 2025-11-28 |

**컴포넌트 스펙**:
```typescript
interface SidebarSubmenuProps {
  title: string;              // "System"
  icon: React.ElementType;    // Settings 아이콘
  items: Array<{
    name: string;             // "Pipeline", "HITL Review", "Monitoring"
    href: string;             // "/pipeline", "/hitl", "/monitoring"
    icon: React.ElementType;
  }>;
  defaultOpen?: boolean;      // 기본 펼침 상태
}
```

---

#### 2.2 Sidebar에 System 서브메뉴 통합

**File**: `apps/frontend/components/layout/Sidebar.tsx`

| # | 작업 | 파일:라인 | 상태 | 완료일 |
|---|------|-----------|------|--------|
| 2.2.1 | [x] SidebarSubmenu import 추가 | `Sidebar.tsx:26` | ✅ | 2025-11-28 |
| 2.2.2 | [x] Settings 아이콘 import 추가 | `Sidebar.tsx:23` | ✅ | 2025-11-28 |
| 2.2.3 | [x] mainNavigation으로 분리 (Pipeline/HITL/Monitoring 제외) | `Sidebar.tsx:28-35` | ✅ | 2025-11-28 |
| 2.2.4 | [x] systemNavigation 배열 생성 | `Sidebar.tsx:37-42` | ✅ | 2025-11-28 |
| 2.2.5 | [x] SidebarSubmenu 컴포넌트 렌더링 추가 | `Sidebar.tsx:93-99` | ✅ | 2025-11-28 |

**변경 후 navigation 배열**:
```typescript
const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Taxonomy", href: "/taxonomy", icon: Network },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Chat", href: "/search", icon: MessageSquare },
];

const systemNavigation = [
  { name: "Pipeline", href: "/pipeline", icon: Workflow },
  { name: "HITL Review", href: "/hitl", icon: UserCheck },
  { name: "Monitoring", href: "/monitoring", icon: Activity },
];
```

---

### Phase 2 Completion Checklist

```
Phase 2 완료 조건:
[x] SidebarSubmenu 컴포넌트 생성 완료
[x] System 서브메뉴 토글 동작 확인
[x] 서브메뉴 펼침/접힘 애니메이션 동작
[x] 서브메뉴 아이템 클릭 시 해당 페이지 이동
[x] 현재 페이지 활성 상태 하이라이트 (자동 펼침)
[x] 콘솔 에러 없음 확인

Phase 2 완료일: 2025-11-28
Phase 2 완료자: Alfred (MoAI-ADK)
```

---

## Phase 3: Documents → Taxonomy 통합 (예상 3-5일)

### Phase 3 Progress: ✅ 14/14 완료

#### 3.1 ImportKnowledgeModal 컴포넌트 생성

**New File**: `apps/frontend/components/taxonomy/ImportKnowledgeModal.tsx`

| # | 작업 | 파일 | 상태 | 완료일 |
|---|------|------|------|--------|
| 3.1.1 | [x] ImportKnowledgeModal.tsx 파일 생성 | `components/taxonomy/ImportKnowledgeModal.tsx` | ✅ | 2025-11-28 |
| 3.1.2 | [x] 모달 오버레이 및 컨테이너 구현 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 3.1.3 | [x] Documents 페이지의 Drag & Drop 로직 복사 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 3.1.4 | [x] 파일 목록 및 업로드 상태 표시 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 3.1.5 | [x] uploadDocument API 연동 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 3.1.6 | [x] 닫기 버튼 및 ESC 키 핸들링 | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 3.1.7 | [x] Ethereal Glass 테마 적용 | 컴포넌트 내부 | ✅ | 2025-11-28 |

**컴포넌트 Props**:
```typescript
interface ImportKnowledgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete?: (results: UploadResult[]) => void;
}
```

---

#### 3.2 Taxonomy 페이지에 FAB 버튼 추가

**File**: `apps/frontend/app/(dashboard)/taxonomy/page.tsx`

| # | 작업 | 파일:라인 | 상태 | 완료일 |
|---|------|-----------|------|--------|
| 3.2.1 | [x] showUploadModal useState 추가 | `taxonomy/page.tsx:320` | ✅ | 2025-11-28 |
| 3.2.2 | [x] Upload 아이콘 import 추가 | `taxonomy/page.tsx:36` | ✅ | 2025-11-28 |
| 3.2.3 | [x] ImportKnowledgeModal import 추가 | `taxonomy/page.tsx:37` | ✅ | 2025-11-28 |
| 3.2.4 | [x] FAB 버튼 JSX 추가 (우측 하단 고정) | `taxonomy/page.tsx:428-444` | ✅ | 2025-11-28 |
| 3.2.5 | [x] ImportKnowledgeModal 조건부 렌더링 | `taxonomy/page.tsx:446-454` | ✅ | 2025-11-28 |

**FAB 버튼 코드**:
```typescript
<button
  onClick={() => setShowUploadModal(true)}
  className="fixed bottom-8 right-8 z-30 p-4 rounded-full
             bg-gradient-to-r from-cyan-500 to-purple-500
             text-white shadow-lg shadow-cyan-500/30
             hover:scale-110 transition-transform
             hover:shadow-[0_0_20px_rgba(0,247,255,0.5)]"
  title="Import Knowledge"
>
  <Upload className="w-6 h-6" />
</button>
```

---

#### 3.3 Documents 페이지 정리

**File**: `apps/frontend/components/layout/Sidebar.tsx`

| # | 작업 | 파일:라인 | 상태 | 완료일 |
|---|------|-----------|------|--------|
| 3.3.1 | [x] navigation 배열에서 Documents 항목 제거 | `Sidebar.tsx:30-35` | ✅ | 2025-11-28 |
| 3.3.2 | [x] FileText import 제거 (더 이상 사용 안 함) | `Sidebar.tsx:12-23` | ✅ | 2025-11-28 |

---

### Phase 3 Completion Checklist

```
Phase 3 완료 조건:
[x] ImportKnowledgeModal 컴포넌트 완성
[x] Taxonomy 페이지 FAB 버튼 표시
[x] FAB 클릭 시 모달 열림
[x] 파일 Drag & Drop 동작
[x] 파일 업로드 성공/실패 표시
[x] 업로드 완료 후 모달 닫힘
[x] Documents 메뉴 사이드바에서 제거됨
[x] 콘솔 에러 없음 확인

Phase 3 완료일: 2025-11-28
Phase 3 완료자: Alfred (MoAI-ADK)
```

---

## Phase 4: Connect 신규 페이지 (예상 1-2주)

### Phase 4 Progress: ✅ 20/20 완료

#### 4.1 Connect 페이지 기본 구조

**New File**: `apps/frontend/app/(dashboard)/connect/page.tsx`

| # | 작업 | 파일 | 상태 | 완료일 |
|---|------|------|------|--------|
| 4.1.1 | [x] connect 폴더 생성 | `app/(dashboard)/connect/` | ✅ | 2025-11-28 |
| 4.1.2 | [x] page.tsx 파일 생성 | `connect/page.tsx` | ✅ | 2025-11-28 |
| 4.1.3 | [x] 페이지 레이아웃 구조 (헤더 + 그리드) | 컴포넌트 내부 | ✅ | 2025-11-28 |
| 4.1.4 | [x] Ethereal Glass 배경 효과 적용 | 컴포넌트 내부 | ✅ | 2025-11-28 |

---

#### 4.2 API Keys 섹션 (페이지 내 구현)

| # | 작업 | 파일 | 상태 | 완료일 |
|---|------|------|------|--------|
| 4.2.1 | [x] API 키 목록 카드 UI | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.2.2 | [x] API 키 목록 표시 UI | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.2.3 | [x] 새 API 키 생성 버튼 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.2.4 | [x] API 키 복사 기능 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.2.5 | [x] API 키 삭제 버튼 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |

---

#### 4.3 MCP Servers 섹션 (페이지 내 구현)

| # | 작업 | 파일 | 상태 | 완료일 |
|---|------|------|------|--------|
| 4.3.1 | [x] MCP Servers 카드 UI | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.3.2 | [x] 연결된 서버 목록 표시 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.3.3 | [x] 연결 상태 인디케이터 (green/gray dot) | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.3.4 | [x] 새 서버 추가 버튼 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |

---

#### 4.4 Channels 섹션 (페이지 내 구현)

| # | 작업 | 파일 | 상태 | 완료일 |
|---|------|------|------|--------|
| 4.4.1 | [x] Channels 카드 UI | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.4.2 | [x] Web Widget 채널 표시 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.4.3 | [x] Slack Integration 채널 표시 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |
| 4.4.4 | [x] REST API 채널 표시 | `connect/page.tsx` 내부 | ✅ | 2025-11-28 |

---

#### 4.5 Sidebar에 Connect 메뉴 추가

**File**: `apps/frontend/components/layout/Sidebar.tsx`

| # | 작업 | 파일:라인 | 상태 | 완료일 |
|---|------|-----------|------|--------|
| 4.5.1 | [x] Plug 아이콘 import 추가 | `Sidebar.tsx:17` | ✅ | 2025-11-28 |
| 4.5.2 | [x] navigation 배열에 Connect 항목 추가 | `Sidebar.tsx:36` | ✅ | 2025-11-28 |

---

### Phase 4 Completion Checklist

```
Phase 4 완료 조건:
[x] /connect 라우트 접근 가능
[x] Connect 페이지 Ethereal Glass 테마 적용
[x] API Keys 섹션 표시 (Mock 데이터)
[x] MCP Servers 섹션 표시 (Mock 데이터)
[x] Channels 섹션 표시 (Mock 데이터)
[x] 사이드바에 Connect 메뉴 표시
[x] 반응형 레이아웃 동작 (3-column grid)
[x] Integration Status 통계 카드

Phase 4 완료일: 2025-11-28
Phase 4 완료자: Alfred (MoAI-ADK)

Note: Backend API 연동은 추후 구현 예정 (현재 Mock 데이터 사용)
```

---

## Quick Reference: 파일 변경 요약

| 파일 경로 | Phase | 변경 유형 |
|-----------|-------|-----------|
| `components/layout/Sidebar.tsx` | 1, 2, 3, 4 | 수정 |
| `app/(dashboard)/search/page.tsx` | 1 | 수정 |
| `components/layout/SidebarSubmenu.tsx` | 2 | 신규 |
| `components/taxonomy/ImportKnowledgeModal.tsx` | 3 | 신규 |
| `app/(dashboard)/taxonomy/page.tsx` | 3 | 수정 |
| `app/(dashboard)/connect/page.tsx` | 4 | 신규 |
| `components/connect/APIKeysCard.tsx` | 4 | 신규 |
| `components/connect/MCPServersCard.tsx` | 4 | 신규 |
| `components/connect/ChannelsCard.tsx` | 4 | 신규 |

---

## Technical Dependencies

### Phase 1
- 의존성 없음 (즉시 실행 가능)

### Phase 2
- Phase 1 완료 필요
- shadcn/ui Collapsible 컴포넌트 (선택적)

### Phase 3
- Documents 페이지의 uploadDocument API 재사용
- Modal/Sheet 컴포넌트

### Phase 4
- Backend API 엔드포인트 (구현 필요):
  - `GET/POST /api/v1/connect/api-keys`
  - `GET/POST /api/v1/connect/mcp-servers`
  - `GET/POST /api/v1/connect/channels`

---

## Risk Assessment

| 위험 요소 | 영향도 | 완화 방안 |
|-----------|--------|----------|
| /search URL 변경 시 기존 북마크 깨짐 | 중 | URL은 유지하고 표시명만 변경 |
| Documents 제거 시 직접 접근 불가 | 하 | 라우트는 유지, Taxonomy로 리다이렉트 |
| System 서브메뉴 UX | 중 | 기본 펼쳐진 상태로 시작 |

---

## Reference Documents

- `docs/DT-RAG-PRODUCT-GUIDE.md` - 제품 종합 가이드
- `apps/frontend/DESIGN-SYSTEM.md` - 디자인 시스템 (최신)
- `.moai/specs/SPEC-FRONTEND-REDESIGN-001/spec.md` - 현재 구현 SPEC

---

**Author**: Alfred (MoAI-ADK Orchestrator)
**Last Updated**: 2025-11-28
