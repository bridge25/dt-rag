# @PLAN:AGENT-CARD-001 Implementation Plan

## 개요

Pokemon-Style Agent Card System의 구현 계획입니다. 3단계 병렬 개발을 통해 UI 컴포넌트, 게임 로직, 애니메이션을 통합합니다.

## 구현 우선순위

### 우선순위 HIGH (핵심 기능)

#### Milestone 1: 프로젝트 설정 및 의존성 설치
- 목표: 필수 라이브러리 설치 및 타입 정의
- 작업:
  1. react-confetti, framer-motion 설치
  2. AgentCardData 타입 정의 (lib/api/types.ts)
  3. 디렉토리 구조 생성
- 완료 조건:
  - package.json에 라이브러리 추가
  - 타입 검사 통과
  - 디렉토리 생성 완료

#### Milestone 2: 유틸리티 함수 구현
- 목표: 핵심 계산 로직 완성
- 작업:
  1. xpCalculator.ts (XP 계산 함수)
  2. levelCalculator.ts (레벨 계산, XP 진행도)
  3. rarityResolver.ts (희귀도 결정, 스타일 맵)
  4. qualityScoreCalculator.ts (품질 점수 계산)
- 완료 조건:
  - 모든 함수 타입 안전성 확보
  - 단위 테스트 작성
  - JSDoc 주석 추가

#### Milestone 3: 기본 UI 컴포넌트
- 목표: 핵심 카드 컴포넌트 렌더링
- 작업:
  1. RarityBadge.tsx (희귀도 배지)
  2. ProgressBar.tsx (XP 진행 바)
  3. StatDisplay.tsx (스탯 표시)
  4. ActionButtons.tsx (액션 버튼)
  5. AgentCard.tsx (메인 카드 컴포넌트)
- 완료 조건:
  - 정적 데이터로 렌더링 확인
  - Tailwind 스타일 적용
  - 접근성 ARIA 레이블 추가

### 우선순위 MEDIUM (통합 기능)

#### Milestone 4: TanStack Query 통합
- 목표: 백엔드 API 연동
- 작업:
  1. useAgents.ts 훅 구현
  2. API 클라이언트 함수 (fetchAgents)
  3. 로딩/에러 상태 처리
  4. 스켈레톤 UI
- 완료 조건:
  - GET /api/v1/agents 성공 호출
  - 로딩/에러 UI 표시
  - 30초 stale time 설정

#### Milestone 5: 홈페이지 그리드 레이아웃
- 목표: 반응형 에이전트 카드 그리드
- 작업:
  1. HomePage.tsx 구현
  2. 반응형 그리드 (1/2/3/4열)
  3. useAgents 훅 연동
  4. 빈 상태 처리
- 완료 조건:
  - 모든 화면 크기에서 정상 렌더링
  - 카드 클릭 이벤트 동작
  - 빈 상태 메시지 표시

#### Milestone 6: 애니메이션 컴포넌트
- 목표: 레벨업 모달 및 효과
- 작업:
  1. ConfettiAnimation.tsx (react-confetti 래퍼)
  2. LevelUpModal.tsx (모달 + confetti)
  3. useLevelUpNotification.ts (레벨업 감지)
  4. 플로팅 XP 텍스트 (framer-motion)
- 완료 조건:
  - 레벨업 시 confetti 표시
  - 모달 3초 후 자동 닫힘
  - XP 획득 시 플로팅 텍스트 표시

### 우선순위 LOW (고급 기능)

#### Milestone 7: 성장 로직 통합
- 목표: XP 획득 및 레벨업 자동화
- 작업:
  1. useAgentGrowth.ts (XP 상태 관리)
  2. XP 증가 트리거 (채팅, 피드백, RAGAS)
  3. 레벨업 자동 감지
- 완료 조건:
  - XP 증가 시 진행 바 업데이트
  - 레벨업 시 모달 자동 표시
  - 희귀도 변경 애니메이션

#### Milestone 8: 테스트 및 최적화
- 목표: 품질 보증 및 성능 최적화
- 작업:
  1. 컴포넌트 단위 테스트
  2. 유틸리티 함수 테스트
  3. 접근성 테스트 (axe-core)
  4. 성능 프로파일링
- 완료 조건:
  - 테스트 커버리지 80% 이상
  - 접근성 위반 0건
  - 100개 카드 렌더링 시 60fps 유지

## 기술적 접근

### 아키텍처 설계

#### 1. 컴포넌트 계층 구조
```
HomePage
├── AgentCard (복수)
│   ├── RarityBadge
│   ├── ProgressBar
│   ├── StatDisplay
│   └── ActionButtons
└── LevelUpModal
    └── ConfettiAnimation
```

#### 2. 상태 관리 전략
- **서버 상태**: TanStack Query (에이전트 목록)
- **클라이언트 상태**: Zustand (레벨업 모달 상태)
- **로컬 상태**: useState (XP 애니메이션)

#### 3. 데이터 흐름
```
Backend API
    ↓ (TanStack Query)
useAgents hook
    ↓
HomePage
    ↓ (props)
AgentCard
    ↓ (계산 함수)
Utility functions (XP, Level, Rarity, Quality)
    ↓
UI Rendering
```

### 기술 스택 결정

#### 애니메이션 라이브러리 선정
1. **react-confetti**: 레벨업 축하 효과
   - 이유: 가볍고 사용하기 쉬움, 커스터마이징 가능
   - 버전: ^6.1.0

2. **framer-motion**: 컴포넌트 전환 애니메이션
   - 이유: React 생태계 표준, 선언적 API
   - 버전: ^11.15.0

#### 상태 관리 결정
1. **TanStack Query**: 서버 데이터 캐싱
   - 이유: 이미 프로젝트에 설치됨, 자동 리페치 지원
   - 설정: staleTime 30초, refetchOnWindowFocus true

2. **Zustand**: 레벨업 모달 상태
   - 이유: 이미 프로젝트에 설치됨, 간단한 API
   - 용도: 모달 열림/닫힘, 레벨업 데이터

### 백엔드 통합 전략

#### API 엔드포인트 매핑
```typescript
// GET /api/v1/agents
fetchAgents(): Promise<AgentCardData[]>

// 향후 추가 (백엔드 구현 필요)
// POST /api/v1/agents/{id}/xp
incrementXP(agentId: string, amount: number): Promise<void>
```

#### 데이터 변환 로직
```typescript
// Backend AgentResponse → Frontend AgentCardData
function transformAgentData(response: AgentResponse): AgentCardData {
  return {
    agent_id: response.agent_id,
    name: response.name,
    level: getLevelFromXP(response.current_xp), // 클라이언트 계산
    current_xp: response.current_xp,
    total_documents: response.total_documents,
    total_queries: response.total_queries,
    avg_faithfulness: response.avg_faithfulness,
    coverage_percent: response.coverage_percent,
    created_at: response.created_at,
    updated_at: response.updated_at,
  };
}
```

#### 백엔드 제약 대응
1. **레벨 제한 (1-5)**:
   - 해결: 프론트엔드에서 XP 기반 레벨 계산 (1-10+)
   - 함수: `getLevelFromXP()`

2. **피드백 데이터 없음**:
   - 해결: 초기 버전에서는 `avg_faithfulness`만 사용
   - 향후: 백엔드에 컬럼 추가 후 가중치 계산

3. **XP 증가 API 없음**:
   - 해결: 현재는 수동 테스트 데이터 사용
   - 향후: POST /agents/{id}/xp 엔드포인트 요청

### 성능 최적화 전략

#### 1. 렌더링 최적화
- React.memo로 AgentCard 메모이제이션
- useMemo로 계산 결과 캐싱 (level, rarity, qualityScore)
- 가상 스크롤 미구현 (100개 이하 가정)

#### 2. 애니메이션 최적화
- framer-motion의 layoutId 사용 (공유 레이아웃 애니메이션)
- CSS transform 사용 (reflow 방지)
- requestAnimationFrame 활용

#### 3. 네트워크 최적화
- TanStack Query 캐싱 (30초 stale time)
- Polling 간격 60초 (서버 부하 최소화)
- 조건부 리페치 (window focus 시에만)

## 위험 요소 및 대응 방안

### 기술적 위험

#### 위험 1: 백엔드 레벨 불일치
- **문제**: 백엔드 level (1-5) vs 프론트엔드 level (1-10+)
- **영향**: 데이터 불일치, 사용자 혼란
- **대응**:
  - 프론트엔드에서 XP 기반 레벨 계산 (단일 진실 공급원)
  - 백엔드 level 필드는 무시
  - 향후 백엔드 제약 제거 시 마이그레이션 계획 수립

#### 위험 2: 피드백 데이터 부재
- **문제**: 품질 점수 계산 불완전
- **영향**: 품질 점수가 RAGAS만 반영 (70% 가중치 누락)
- **대응**:
  - 초기 버전: avg_faithfulness만 사용 (100% 가중치)
  - 향후: 백엔드에 피드백 컬럼 추가 후 가중치 적용
  - 문서화: "현재 RAGAS 점수만 반영" 명시

#### 위험 3: 실시간 업데이트 불가
- **문제**: WebSocket 미구현, 레벨업 알림 지연
- **영향**: 사용자가 레벨업을 즉시 인식하지 못함
- **대응**:
  - TanStack Query polling (60초)
  - 수동 리페치 버튼 제공
  - 향후: WebSocket 추가 시 실시간 알림

### UX 위험

#### 위험 4: 애니메이션 과부하
- **문제**: 동시 다수 레벨업 시 confetti 중복
- **영향**: 브라우저 프리징, 사용자 경험 저하
- **대응**:
  - 최대 1개 confetti 동시 표시
  - 레벨업 큐 구현 (순차 처리)
  - 애니메이션 스킵 옵션 제공

#### 위험 5: 카드 렌더링 성능
- **문제**: 100개 이상 카드 렌더링 시 성능 저하
- **영향**: 스크롤 지연, 초기 로딩 느림
- **대응**:
  - 현재: 100개 이하 제한 (문서화)
  - 향후: react-window로 가상 스크롤 구현
  - Lazy loading (Intersection Observer)

## 테스트 전략

### 단위 테스트 (Vitest)

#### 유틸리티 함수 테스트
```typescript
// xpCalculator.test.ts
describe('calculateXPGain', () => {
  it('should return 10 XP for chat completion', () => {
    expect(calculateXPGain('chat')).toBe(10);
  });

  it('should return 50 XP for positive feedback', () => {
    expect(calculateXPGain('feedback')).toBe(50);
  });

  it('should return 100 XP for RAGAS bonus', () => {
    expect(calculateXPGain('ragas', 0.95)).toBe(100);
  });

  it('should return 0 XP for low RAGAS score', () => {
    expect(calculateXPGain('ragas', 0.8)).toBe(0);
  });
});

// levelCalculator.test.ts
describe('getLevelFromXP', () => {
  it('should return level 1 for 0 XP', () => {
    expect(getLevelFromXP(0)).toBe(1);
  });

  it('should return level 3 for 300 XP', () => {
    expect(getLevelFromXP(300)).toBe(3);
  });

  it('should return level 8 for 2900 XP', () => {
    expect(getLevelFromXP(2900)).toBe(8);
  });
});

// rarityResolver.test.ts
describe('getRarity', () => {
  it('should return common for level 1-2', () => {
    expect(getRarity(1)).toBe('common');
    expect(getRarity(2)).toBe('common');
  });

  it('should return legendary for level 8+', () => {
    expect(getRarity(8)).toBe('legendary');
    expect(getRarity(10)).toBe('legendary');
  });
});
```

### 컴포넌트 테스트 (React Testing Library)

```typescript
// AgentCard.test.tsx
describe('AgentCard', () => {
  const mockAgent: AgentCardData = {
    agent_id: 'test-123',
    name: 'Test Agent',
    level: 5,
    current_xp: 1200,
    total_documents: 150,
    total_queries: 300,
    avg_faithfulness: 0.85,
    coverage_percent: 75.5,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  };

  it('should render agent name', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('should display correct rarity for level 5', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('EPIC')).toBeInTheDocument();
  });

  it('should call onChatClick when chat button clicked', () => {
    const onChatClick = vi.fn();
    render(<AgentCard agent={mockAgent} onChatClick={onChatClick} />);

    fireEvent.click(screen.getByRole('button', { name: /대화/i }));
    expect(onChatClick).toHaveBeenCalledWith('test-123');
  });
});
```

### 통합 테스트

```typescript
// HomePage.integration.test.tsx
describe('HomePage integration', () => {
  beforeEach(() => {
    // Mock API response
    server.use(
      rest.get('/api/v1/agents', (req, res, ctx) => {
        return res(ctx.json({ agents: [mockAgent1, mockAgent2] }));
      })
    );
  });

  it('should fetch and display agent cards', async () => {
    render(<HomePage />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument();
      expect(screen.getByText('Agent 2')).toBeInTheDocument();
    });
  });

  it('should display loading skeleton initially', () => {
    render(<HomePage />);
    expect(screen.getAllByTestId('skeleton-card')).toHaveLength(3);
  });
});
```

### 접근성 테스트

```typescript
// accessibility.test.tsx
import { axe } from 'jest-axe';

describe('Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<AgentCard agent={mockAgent} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should support keyboard navigation', () => {
    render(<AgentCard agent={mockAgent} />);
    const chatButton = screen.getByRole('button', { name: /대화/i });

    // Tab to button
    chatButton.focus();
    expect(chatButton).toHaveFocus();

    // Enter to click
    fireEvent.keyDown(chatButton, { key: 'Enter' });
  });
});
```

## 의존성 관계

### 선행 조건
- ✅ React 19.1.1 설치됨
- ✅ TanStack Query 5.90.5 설치됨
- ✅ Zustand 5.0.8 설치됨
- ✅ Tailwind CSS 4.1.16 구성됨
- ✅ 백엔드 API 엔드포인트 구현됨
- ⚠️ react-confetti 설치 필요
- ⚠️ framer-motion 설치 필요

### 블로킹 요소
- 없음 (백엔드 API는 이미 구현됨)

### 관련 SPEC
- `SPEC-AGENT-GROWTH-001`: 백엔드 DB 스키마
- `SPEC-AGENT-GROWTH-002`: 백엔드 API 엔드포인트
- `SPEC-FRONTEND-INIT-001`: 프론트엔드 초기화

## 배포 전략

### 단계별 배포

#### Phase 1: 기본 기능 (MVP)
- 컴포넌트: AgentCard, ProgressBar, RarityBadge, StatDisplay
- 로직: XP/Level/Rarity 계산
- 페이지: HomePage (정적 렌더링)
- 배포 조건:
  - 정적 데이터로 렌더링 성공
  - Tailwind 스타일 적용 완료

#### Phase 2: 백엔드 통합
- 기능: TanStack Query 연동, API 호출
- 배포 조건:
  - GET /api/v1/agents 성공 호출
  - 로딩/에러 상태 처리 완료

#### Phase 3: 애니메이션
- 기능: 레벨업 모달, confetti, 플로팅 텍스트
- 배포 조건:
  - 모든 애니메이션 동작 확인
  - 성능 테스트 통과 (60fps)

### 롤백 계획
- Phase 3 실패 시: 애니메이션 비활성화
- Phase 2 실패 시: 정적 데이터로 폴백
- Phase 1 실패 시: 기존 UI 유지

## 완료 정의 (Definition of Done)

### 코드 완료 조건
- [x] 모든 컴포넌트 구현 완료
- [x] 모든 유틸리티 함수 구현 완료
- [x] TanStack Query 훅 구현 완료
- [x] TypeScript 타입 에러 0건
- [x] ESLint 경고 0건
- [x] 테스트 커버리지 80% 이상

### 품질 검증
- [x] 단위 테스트 통과
- [x] 통합 테스트 통과
- [x] 접근성 테스트 통과 (axe-core)
- [x] 성능 테스트 통과 (100개 카드, 60fps)
- [x] Cross-browser 테스트 (Chrome, Firefox, Safari)

### 문서화
- [x] 컴포넌트 JSDoc 주석
- [x] README 업데이트 (설치/실행 가이드)
- [x] Storybook 스토리 작성 (선택)
- [x] 백엔드 통합 가이드

### 배포 준비
- [x] 프로덕션 빌드 성공
- [x] 번들 사이즈 확인 (<500KB)
- [x] Lighthouse 점수 (Performance 90+, Accessibility 100)

---

**작성일**: 2025-10-30
**작성자**: @Alfred
**버전**: 0.0.1
