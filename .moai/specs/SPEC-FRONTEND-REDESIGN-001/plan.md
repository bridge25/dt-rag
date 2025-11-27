# SPEC-FRONTEND-REDESIGN-001: Implementation Plan

## Executive Summary

**총 예상 기간:** 14일 (2주)
**우선순위:** P0 (Critical)
**담당:** 형 + AI 에이전트 팀

---

## Phase Overview

```
Phase 1 (Day 1-2)     Phase 2 (Day 3-4)     Phase 3 (Day 5-7)
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  디자인 시스템   │ → │  나노바나나     │ → │  에이전트 카드  │
│  기반 구축      │   │  에셋 생성      │   │  재설계         │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                                                    ↓
Phase 6 (Day 13-14)   Phase 5 (Day 11-12)   Phase 4 (Day 8-10)
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  테스트 및      │ ← │  전체 페이지    │ ← │  Taxonomy       │
│  최적화         │   │  통합           │   │  Constellation  │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## Phase 1: 디자인 시스템 기반 구축 (Day 1-2)

### 목표
Ethereal Glass 디자인 시스템의 토대를 Tailwind 설정에 반영

### Tasks

#### 1.1 Tailwind 설정 업데이트
**파일:** `apps/frontend/tailwind.config.ts`

```typescript
// 추가할 색상
colors: {
  'space': {
    DEFAULT: '#0b1121',
    light: '#0f172a',
  },
  'ethereal': {
    cyan: '#00f7ff',
    purple: '#bc13fe',
    gold: '#ffd700',
    green: '#0aff0a',
  },
  'glass': {
    surface: 'rgba(30, 41, 59, 0.4)',
    border: 'rgba(255, 255, 255, 0.1)',
    highlight: 'rgba(255, 255, 255, 0.15)',
  }
}

// 추가할 그림자
boxShadow: {
  'ethereal-sm': '0 0 10px rgba(0, 247, 255, 0.15)',
  'ethereal-md': '0 0 20px rgba(0, 247, 255, 0.25)',
  'ethereal-lg': '0 0 40px rgba(0, 247, 255, 0.35)',
  'ethereal-gold': '0 0 30px rgba(255, 215, 0, 0.4)',
  'ethereal-purple': '0 0 25px rgba(188, 19, 254, 0.3)',
}

// 추가할 애니메이션
animation: {
  'glow-pulse': 'glowPulse 2s ease-in-out infinite',
  'float': 'float 6s ease-in-out infinite',
  'energy-beam': 'energyBeam 2s linear infinite',
}
```

#### 1.2 글로벌 스타일 강화
**파일:** `apps/frontend/app/globals.css`

```css
/* Ethereal Glass 유틸리티 클래스 */
.ethereal-card {
  @apply bg-glass-surface backdrop-blur-xl
         border border-glass-border rounded-2xl
         transition-all duration-300;
}

.ethereal-card:hover {
  @apply border-ethereal-cyan/30 shadow-ethereal-md
         -translate-y-1;
}

/* 희귀도별 글로우 */
.rarity-common { --glow-color: rgba(156, 163, 175, 0.3); }
.rarity-rare { --glow-color: rgba(0, 247, 255, 0.4); }
.rarity-epic { --glow-color: rgba(188, 19, 254, 0.4); }
.rarity-legendary { --glow-color: rgba(255, 215, 0, 0.5); }

/* 우주 배경 강화 */
.space-background {
  background-color: #0b1121;
  background-image:
    /* 네뷸라 레이어 */
    radial-gradient(ellipse at 15% 25%, rgba(0, 247, 255, 0.06), transparent 50%),
    radial-gradient(ellipse at 85% 75%, rgba(188, 19, 254, 0.04), transparent 50%),
    /* 별 파티클 */
    radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.2), transparent),
    radial-gradient(2px 2px at 40% 70%, rgba(255,255,255,0.15), transparent),
    radial-gradient(1px 1px at 60% 20%, rgba(255,255,255,0.1), transparent),
    radial-gradient(1px 1px at 80% 50%, rgba(255,255,255,0.12), transparent);
}
```

#### 1.3 폰트 확인
- Inter 폰트 설정 확인
- Font weight 300, 400, 500, 600 로딩

### Deliverables
- [ ] `tailwind.config.ts` 업데이트 완료
- [ ] `globals.css` Ethereal Glass 클래스 추가
- [ ] 색상/그림자/애니메이션 토큰 정의

### Validation
```bash
npm run build  # 빌드 오류 없음 확인
npm run dev    # 기존 UI 깨짐 없음 확인
```

### 🎭 Playwright 자동화 검증
```yaml
검증 항목:
  - 배경색 #0b1121 적용 확인 (browser_snapshot)
  - 글래스 효과 CSS 변수 로드 확인
  - 네온 색상 Tailwind 클래스 동작 확인

실행:
  - mcp__playwright__browser_navigate → http://localhost:3000
  - mcp__playwright__browser_snapshot → DOM 구조 확인
  - mcp__playwright__browser_take_screenshot → 전체 페이지 캡처
```

### 🔧 Chrome DevTools 디버깅 (필요 시)
```yaml
사용 시점:
  - CSS 변수가 적용되지 않을 때
  - 글래스 효과가 렌더링되지 않을 때

도구:
  - mcp__chrome-devtools__take_snapshot → 요소 스타일 확인
  - mcp__chrome-devtools__list_console_messages → 에러 확인
```

---

## Phase 2: 나노바나나 에셋 생성 (Day 3-4)

### 목표
16종 커스텀 로봇 이미지 생성 (희귀도별 4종 × 4 희귀도)

### Tasks

#### 2.1 나노바나나 환경 설정
```bash
# .env 파일에 API 키 설정
GOOGLE_API_KEY=your_gemini_api_key_here
```

#### 2.2 디자인 방향: 귀여운 마스코트 스타일

> **중요:** 모든 로봇은 **과하지 않고 귀여운 마스코트 스타일**로 생성
> - 둥글둥글한 형태, 큰 눈, 친근한 표정
> - 복잡한 디테일보다 심플하고 깔끔한 디자인
> - 위협적이지 않은 친근한 포즈
> - 뉴디자인1.png의 로봇들 참고 (SD캐릭터 느낌)

#### 2.3 Common 로봇 생성 (4종)

**프롬프트 예시:**
```
A cute small robot mascot character with a round head
and big friendly circular LED eyes. Simple chibi-like
proportions with short stubby arms and legs.
Soft gray-blue metallic body with minimal details.
Standing in a friendly welcoming pose, slightly tilted head.
Adorable and approachable design, soft studio lighting.
Transparent PNG background, front-facing view.
Style: kawaii tech mascot, Pixar-like 3D render, clean simple design.
Aspect ratio: 1:1, centered composition.
```

**변형 포인트:**
1. robot-common-01: 둥근 머리, 기본 포즈
2. robot-common-02: 더 큰 눈, 작은 체형 (더 귀여움)
3. robot-common-03: 안테나 달린 정사각형 머리, 웃는 눈
4. robot-common-04: 헬멧 스타일 머리, 호기심 가득한 표정

#### 2.4 Rare 로봇 생성 (4종)

**프롬프트 예시:**
```
A cute advanced robot mascot with soft glowing cyan accents.
Round friendly face with big expressive eyes that glow
gentle teal color. Slightly more detailed than basic model
but still maintaining adorable chibi proportions.
Clean silver-cyan color scheme with subtle light lines.
Cheerful confident pose, transparent PNG background.
Style: cute tech mascot, friendly 3D character, clean design.
NOT aggressive or intimidating, keep it approachable and cute.
```

#### 2.5 Epic 로봇 생성 (4종)

**프롬프트 예시:**
```
A cute elite robot mascot with soft purple glow accents.
Round head with big sparkly eyes, small decorative
wing-like attachments on back (not intimidating, decorative).
Lavender and silver color scheme with gentle purple highlights.
Proud but friendly pose, like a happy mascot character.
Transparent PNG background, soft magical lighting.
Style: cute fantasy mascot, adorable 3D character.
Keep proportions chibi-like and approachable, NOT scary or aggressive.
```

#### 2.6 Legendary 로봇 생성 (4종)

**프롬프트 예시:**
```
A cute premium robot mascot with warm golden glow accents.
Round adorable head with big shiny eyes, small crown-like
decoration (simple, not elaborate). White and gold color
scheme with gentle golden highlights. Happy majestic pose
like a proud but friendly mascot. Soft sparkles around.
Transparent PNG background, warm ethereal lighting.
Style: cute royal mascot, premium adorable 3D character.
Keep it cute and friendly despite being "legendary" tier.
NOT intimidating, maintain kawaii aesthetic throughout.
```

#### 2.6 이미지 후처리
```bash
# WebP 변환 및 최적화
for img in *.png; do
  cwebp -q 90 "$img" -o "${img%.png}.webp"
done

# 저장 경로
apps/frontend/public/assets/agents/
├── common/robot-common-{01-04}.webp
├── rare/robot-rare-{01-04}.webp
├── epic/robot-epic-{01-04}.webp
└── legendary/robot-legendary-{01-04}.webp
```

### Deliverables
- [ ] Common 로봇 4종 생성 및 저장
- [ ] Rare 로봇 4종 생성 및 저장
- [ ] Epic 로봇 4종 생성 및 저장
- [ ] Legendary 로봇 4종 생성 및 저장
- [ ] 모든 이미지 WebP 변환 완료

### Validation
- 이미지 품질 검수 (해상도, 투명 배경, 스타일 일관성)
- 뉴디자인1 로봇들과 분위기 일치 확인

---

## Phase 3: 에이전트 카드 재설계 (Day 5-7)

### 목표
뉴디자인1.png와 동일한 에이전트 카드 구현

### Tasks

#### 3.1 AgentCard 컴포넌트 재작성
**파일:** `apps/frontend/components/agent-card/AgentCard.tsx`

```tsx
// 핵심 구조
<div className="ethereal-card group relative overflow-hidden">
  {/* 로봇 이미지 영역 */}
  <div className="relative h-40 flex items-center justify-center">
    <Image
      src={`/assets/agents/${rarity}/${getRandomRobotImage(agentId, rarity)}`}
      alt={name}
      className="drop-shadow-[0_0_15px_var(--glow-color)]"
    />
  </div>

  {/* 희귀도 프로그레스 바 */}
  <div className={`h-1 bg-gradient-to-r ${rarityGradient}`} />

  {/* 통계 영역 */}
  <div className="p-4 space-y-2">
    <StatRow label="Users" value={formatNumber(users)} />
    <StatRow label="Robos" value={formatCurrency(robos)} />
    <StatRow label="Revenue" value={formatCurrency(revenue)} />
    <StatRow label="Growth" value={`+${growth}%`} highlight />
  </div>
</div>
```

#### 3.2 희귀도별 스타일링

```typescript
const rarityStyles = {
  common: {
    gradient: 'from-gray-400 via-gray-500 to-gray-400',
    glow: 'shadow-gray-500/20',
    border: 'hover:border-gray-400/30',
  },
  rare: {
    gradient: 'from-cyan-400 via-cyan-500 to-cyan-400',
    glow: 'shadow-ethereal-sm',
    border: 'hover:border-ethereal-cyan/30',
  },
  epic: {
    gradient: 'from-purple-400 via-fuchsia-500 to-purple-400',
    glow: 'shadow-ethereal-purple',
    border: 'hover:border-purple-400/30',
  },
  legendary: {
    gradient: 'from-amber-400 via-yellow-500 to-amber-400',
    glow: 'shadow-ethereal-gold',
    border: 'hover:border-amber-400/40',
  },
};
```

#### 3.3 호버 애니메이션 구현

```css
.agent-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.agent-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 8px 32px var(--glow-color),
    0 0 0 1px var(--glow-color);
}

/* 내부 shine 효과 */
.agent-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    transparent 40%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 60%
  );
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.agent-card:hover::before {
  transform: translateX(100%);
}
```

#### 3.4 이미지 매핑 유틸리티

```typescript
// lib/agentImageMapper.ts
export function getAgentImage(agentId: string, rarity: Rarity): string {
  // agentId 해시로 1-4 중 결정적 선택
  const hash = hashString(agentId);
  const imageIndex = (hash % 4) + 1;
  const rarityLower = rarity.toLowerCase();

  return `/assets/agents/${rarityLower}/robot-${rarityLower}-0${imageIndex}.webp`;
}
```

### Deliverables
- [ ] `AgentCard.tsx` 재작성 완료
- [ ] `AgentCardAvatar.tsx` 커스텀 이미지 로딩
- [ ] 희귀도별 스타일 구현
- [ ] 호버 애니메이션 구현
- [ ] 그리드 레이아웃 조정 (5열 그리드)

### Validation
- 뉴디자인1.png와 시각적 비교
- 호버 효과 부드러움 확인
- 이미지 로딩 성능 확인

### 🎭 Playwright 자동화 검증
```yaml
검증 항목:
  - 카드 그리드 5열 레이아웃 확인
  - 각 희귀도별 카드 렌더링 확인
  - 호버 시 translateY(-4px) 적용 확인
  - 로봇 이미지 로딩 상태 확인

실행:
  - mcp__playwright__browser_navigate → http://localhost:3000/agents
  - mcp__playwright__browser_snapshot → 카드 그리드 구조 확인
  - mcp__playwright__browser_hover → 카드 호버 효과 테스트
  - mcp__playwright__browser_take_screenshot → 뉴디자인1과 비교용 캡처

스크린샷 비교:
  - 뉴디자인1.png와 실제 구현 스크린샷 나란히 비교
  - 글로우 효과, 색상, 레이아웃 일치 여부 확인
```

### 🔧 Chrome DevTools 디버깅 (필요 시)
```yaml
사용 시점:
  - 호버 애니메이션이 동작하지 않을 때
  - 이미지 로딩 실패 시
  - 글로우 효과가 렌더링되지 않을 때

도구:
  - mcp__chrome-devtools__take_snapshot → 카드 요소 스타일 검사
  - mcp__chrome-devtools__list_network_requests → 이미지 로딩 확인
  - mcp__chrome-devtools__list_console_messages → 에러 로그 확인
  - mcp__chrome-devtools__performance_start_trace → 애니메이션 FPS 측정
```

---

## Phase 4: Taxonomy Constellation 재설계 (Day 8-10)

### 목표
뉴디자인2.png와 동일한 트리 시각화 구현

### Tasks

#### 4.1 Glass Orb Node 컴포넌트
**파일:** `apps/frontend/components/taxonomy/TaxonomyGraphNode.tsx`

```tsx
const ConstellationNode = ({ data, selected }: NodeProps) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={cn(
        "relative w-16 h-16 rounded-full",
        "bg-gradient-to-br from-white/10 to-white/5",
        "border border-white/20 backdrop-blur-md",
        "flex items-center justify-center",
        "transition-all duration-300",
        isHovered && "border-ethereal-cyan/50 shadow-ethereal-md scale-110"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Inner glow */}
      <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white/5 to-transparent" />

      {/* Icon */}
      <Icon className={cn(
        "w-6 h-6 text-white/70",
        isHovered && "text-ethereal-cyan drop-shadow-[0_0_8px_rgba(0,247,255,0.8)]"
      )} />

      {/* HOVERED badge */}
      {isHovered && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-3 py-1
                        bg-ethereal-cyan/20 border border-ethereal-cyan/50
                        rounded-md text-ethereal-cyan text-xs font-medium">
          HOVERED
        </div>
      )}

      {/* Detail tooltip */}
      {isHovered && (
        <div className="absolute left-full ml-4 top-0 p-3 rounded-xl
                        bg-glass-surface backdrop-blur-md border border-glass-border
                        text-sm w-48 z-50">
          <div className="text-ethereal-cyan text-xs mb-1">NODE DETAILS:</div>
          <div className="text-white/80">ACTIVE CONNECTIONS - {data.connections}</div>
        </div>
      )}

      {/* Label */}
      <div className="absolute top-full mt-2 text-center text-xs text-white/60
                      whitespace-nowrap font-medium">
        {data.label}
      </div>

      {/* Handles */}
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
    </div>
  );
};
```

#### 4.2 Energy Beam Edge 컴포넌트

```tsx
const EnergyBeamEdge = ({ sourceX, sourceY, targetX, targetY }: EdgeProps) => {
  const [edgePath] = getBezierPath({ sourceX, sourceY, targetX, targetY });

  return (
    <>
      {/* Base line */}
      <path
        d={edgePath}
        fill="none"
        stroke="rgba(255, 255, 255, 0.2)"
        strokeWidth={2}
      />
      {/* Animated glow */}
      <path
        d={edgePath}
        fill="none"
        stroke="url(#energyGradient)"
        strokeWidth={2}
        className="animate-energy-beam"
      />
      <defs>
        <linearGradient id="energyGradient">
          <stop offset="0%" stopColor="transparent" />
          <stop offset="50%" stopColor="rgba(0, 247, 255, 0.6)" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
    </>
  );
};
```

#### 4.3 Control Panel 컴포넌트

```tsx
const ControlPanel = () => (
  <div className="absolute bottom-8 left-8 p-4 rounded-2xl
                  bg-glass-surface backdrop-blur-md border border-glass-border w-64">
    <div className="space-y-2">
      <ControlButton icon={ZoomIn} label="ZOOM IN" onClick={zoomIn} />
      <ControlButton icon={ZoomOut} label="ZOOM OUT" onClick={zoomOut} />
      <ControlButton icon={Filter} label="FILTER" hasSubmenu />
      <ControlButton icon={Settings} label="SETTINGS" hasSubmenu />
    </div>

    <div className="mt-4 pt-4 border-t border-glass-border">
      <div className="text-xs text-white/50 mb-2">DATA DENSITY</div>
      <input
        type="range"
        className="w-full h-1 bg-white/20 rounded-full appearance-none
                   [&::-webkit-slider-thumb]:appearance-none
                   [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                   [&::-webkit-slider-thumb]:bg-ethereal-cyan
                   [&::-webkit-slider-thumb]:rounded-full"
      />
    </div>
  </div>
);
```

#### 4.4 Root Node 특별 스타일링

```tsx
const RootNode = ({ data }: NodeProps) => (
  <div className="relative w-24 h-24 rounded-full
                  bg-gradient-to-br from-ethereal-cyan/20 to-transparent
                  border-2 border-ethereal-cyan/50
                  shadow-ethereal-lg
                  flex items-center justify-center
                  animate-glow-pulse">
    <Search className="w-10 h-10 text-ethereal-cyan drop-shadow-[0_0_12px_rgba(0,247,255,1)]" />

    {/* Label */}
    <div className="absolute left-full ml-4 text-sm">
      <div className="text-white/50 text-xs">ROOT NODE:</div>
      <div className="text-white font-medium">PROJECT PHOENIX</div>
    </div>
  </div>
);
```

### Deliverables
- [ ] `TaxonomyGraphNode.tsx` 유리 구체 노드 구현
- [ ] `TaxonomyEdge.tsx` 에너지 빔 엣지 구현
- [ ] `ControlPanel.tsx` 컨트롤 패널 구현
- [ ] 호버 상태 + 배지 + 툴팁 구현
- [ ] 루트 노드 특별 스타일링

### Validation
- 뉴디자인2.png와 시각적 비교
- 줌/패닝 부드러움 확인
- 호버 인터랙션 테스트

### 🎭 Playwright 자동화 검증
```yaml
검증 항목:
  - React Flow 캔버스 렌더링 확인
  - 노드 유리 구체 스타일 적용 확인
  - 호버 시 HOVERED 배지 표시 확인
  - 상세 정보 툴팁 표시 확인
  - 줌인/아웃 동작 테스트
  - 컨트롤 패널 버튼 클릭 테스트

실행:
  - mcp__playwright__browser_navigate → http://localhost:3000/taxonomy
  - mcp__playwright__browser_snapshot → 노드/엣지 구조 확인
  - mcp__playwright__browser_hover → 노드 호버 효과 테스트 (HOVERED 배지)
  - mcp__playwright__browser_click → 컨트롤 패널 버튼 테스트
  - mcp__playwright__browser_take_screenshot → 뉴디자인2와 비교용 캡처

인터랙션 테스트:
  - 마우스 휠로 줌인/아웃 동작 확인
  - 드래그로 패닝 동작 확인
  - 노드 클릭 시 선택 상태 확인
```

### 🔧 Chrome DevTools 디버깅 (필요 시)
```yaml
사용 시점:
  - React Flow 렌더링 문제 발생 시
  - 연결선 애니메이션이 동작하지 않을 때
  - 줌/패닝 성능 저하 시

도구:
  - mcp__chrome-devtools__take_snapshot → 노드 DOM 구조 확인
  - mcp__chrome-devtools__list_console_messages → React Flow 에러 확인
  - mcp__chrome-devtools__performance_start_trace → 줌/패닝 FPS 측정
  - mcp__chrome-devtools__performance_analyze_insight → 렌더링 병목 분석
```

---

## Phase 5: 전체 페이지 통합 (Day 11-12)

### 목표
모든 페이지에 Ethereal Glass 디자인 시스템 일관 적용

### Tasks

#### 5.1 Dashboard 페이지 업데이트
- 통계 카드 글래스 효과 강화
- 네온 액센트 추가
- 헤더 "ETHEREAL GLASS" 스타일 적용

#### 5.2 Agents 페이지 업데이트
- 그리드 레이아웃 조정 (5열)
- 페이지 헤더 스타일링
- 검색/필터 글래스 스타일

#### 5.3 Taxonomy 페이지 업데이트
- "CONSTELLATION EXPLORER" 헤더
- 배경 네뷸라 효과 강화

#### 5.4 Sidebar 최적화
- 너비 축소 (256px → 80px 아이콘 전용)
- 글래스 배경 강화
- 아이콘 호버 글로우

#### 5.5 UI 프리미티브 업데이트
- Button: 네온 글로우 호버
- Input: 글래스 스타일 + 포커스 링
- Modal: 글래스 백드롭
- Progress: 그라데이션 바

### Deliverables
- [ ] Dashboard 페이지 업데이트
- [ ] Agents 페이지 업데이트
- [ ] Taxonomy 페이지 업데이트
- [ ] Sidebar 최적화
- [ ] UI 프리미티브 업데이트

### 🎭 Playwright 자동화 검증 (전체 페이지)
```yaml
검증 항목:
  - 모든 페이지 스크린샷 캡처 및 비교
  - 네비게이션 플로우 테스트
  - 반응형 레이아웃 검증

실행:
  # Dashboard
  - mcp__playwright__browser_navigate → http://localhost:3000
  - mcp__playwright__browser_take_screenshot → dashboard.png

  # Agents
  - mcp__playwright__browser_navigate → http://localhost:3000/agents
  - mcp__playwright__browser_take_screenshot → agents.png

  # Taxonomy
  - mcp__playwright__browser_navigate → http://localhost:3000/taxonomy
  - mcp__playwright__browser_take_screenshot → taxonomy.png

반응형 테스트:
  - mcp__playwright__browser_resize → { width: 375, height: 812 }  # Mobile
  - mcp__playwright__browser_take_screenshot → mobile.png
  - mcp__playwright__browser_resize → { width: 768, height: 1024 } # Tablet
  - mcp__playwright__browser_take_screenshot → tablet.png
  - mcp__playwright__browser_resize → { width: 1920, height: 1080 } # Wide
  - mcp__playwright__browser_take_screenshot → wide.png
```

---

## Phase 6: 테스트 및 최적화 (Day 13-14)

### 목표
품질 보증 및 성능 최적화

### Tasks

#### 6.1 크로스 브라우저 테스트
- Chrome (최신)
- Firefox (최신)
- Safari (최신)
- Edge (최신)

#### 6.2 성능 프로파일링
```bash
# Lighthouse 실행
npm run build
npx lighthouse http://localhost:3000 --view

# 목표: Performance 90+
```

#### 6.3 접근성 검증
```bash
# axe-core 테스트
npm run test:a11y

# WCAG 2.1 AA 준수 확인
```

#### 6.4 반응형 테스트
- Mobile (375px)
- Tablet (768px)
- Desktop (1280px)
- Wide (1920px)

### Deliverables
- [ ] 크로스 브라우저 호환성 확인
- [ ] Lighthouse 90+ 달성
- [ ] 접근성 검증 통과
- [ ] 반응형 동작 확인

### 🎭 Playwright 자동화 테스트 (최종 검증)
```yaml
크로스 브라우저 테스트:
  # Playwright 멀티 브라우저 지원
  - chromium, firefox, webkit 브라우저에서 동일 테스트 실행
  - 각 브라우저별 스크린샷 비교

E2E 시나리오 테스트:
  - 대시보드 → 에이전트 목록 → 에이전트 상세 네비게이션
  - Taxonomy 줌/패닝 → 노드 호버 → 상세 정보 확인
  - 검색/필터 기능 동작 확인

스크린샷 회귀 테스트:
  - 각 페이지 스크린샷 저장
  - 이전 버전과 시각적 차이 비교 (pixel diff)
```

### 🔧 Chrome DevTools 성능 분석 (최종)
```yaml
성능 프로파일링:
  - mcp__chrome-devtools__performance_start_trace → 페이지 로드
  - mcp__chrome-devtools__performance_stop_trace → 트레이스 수집
  - mcp__chrome-devtools__performance_analyze_insight → Core Web Vitals 분석

분석 항목:
  - LCP (Largest Contentful Paint) < 2.5s 확인
  - FID (First Input Delay) < 100ms 확인
  - CLS (Cumulative Layout Shift) < 0.1 확인
  - 애니메이션 중 60fps 유지 확인

문제 발견 시:
  - mcp__chrome-devtools__list_network_requests → 느린 리소스 식별
  - mcp__chrome-devtools__list_console_messages → 에러/경고 확인
  - Performance Insight 상세 분석 → 병목 지점 파악
```

---

## Risk Mitigation

| 리스크 | 발생 시 대응 |
|--------|-------------|
| 나노바나나 품질 불만족 | 프롬프트 수정 후 재생성, 최대 3회 반복 |
| 글래스모피즘 성능 저하 | backdrop-filter 범위 축소, will-change 적용 |
| React Flow 커스터마이징 한계 | Custom SVG 노드로 대체 |
| 일정 지연 | Phase 5-6 압축, 핵심 기능 우선 |

---

## Success Criteria Checklist

- [ ] 뉴디자인1과 에이전트 카드 90%+ 일치
- [ ] 뉴디자인2와 Taxonomy 90%+ 일치
- [ ] 16종 커스텀 로봇 이미지 적용
- [ ] Lighthouse Performance 90+
- [ ] 60fps 유지 (Chrome DevTools 확인)
- [ ] WCAG 2.1 AA 준수
- [ ] 크로스 브라우저 호환

---

## Next Steps

1. **Phase 1 시작**: `tailwind.config.ts` 업데이트
2. **나노바나나 준비**: GOOGLE_API_KEY 설정 확인
3. **디자인 검토**: 뉴디자인 이미지 세부 분석

**Ready to execute: `/moai:2-run SPEC-FRONTEND-REDESIGN-001`**
