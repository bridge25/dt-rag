# DT-RAG Frontend Design System

## Ethereal Glass Theme - 뉴디자인 컨셉 가이드

**Version**: 1.0.0
**Last Updated**: 2025-11-28
**적용 완료 페이지**: AI Agents, Taxonomy Constellation

---

## 1. Core Design Principles

### 1.1 Glassmorphism + Neon Glow 조합

```
기본 원칙:
- 반투명 유리 효과 (bg-white/5 ~ bg-white/10)
- Backdrop blur (backdrop-blur-lg ~ backdrop-blur-xl)
- 다층 글로우 효과 (흰색 기본 + 시안 네온)
- 깊이감 있는 그림자 (shadow-2xl + 색상 글로우)
```

### 1.2 Color Palette

| 용도 | Color | Tailwind Class | HEX/RGBA |
|------|-------|----------------|----------|
| **Primary Neon** | Cyan | `text-cyan-400` | `rgba(0,247,255,1)` |
| **Secondary Neon** | Amber (Root/Special) | `text-amber-400` | `rgba(251,191,36,1)` |
| **Background Dark** | Deep Navy | `bg-[#050a15]` | `#050a15` |
| **Background Mid** | Slate | `bg-slate-900` | `#0f172a` |
| **Glass Border** | White Opacity | `border-white/10` | `rgba(255,255,255,0.1)` |
| **Nebula Purple** | Purple | - | `rgba(139,92,246,0.4)` |
| **Nebula Pink** | Pink | - | `rgba(236,72,153,0.3)` |

---

## 2. Component Patterns

### 2.1 Card Component (Agent Cards 패턴)

```tsx
// 기본 카드 스타일
<div className={cn(
  // Glass morphism 기본
  "bg-white/5 backdrop-blur-lg",
  "border border-white/10 rounded-2xl",

  // 복합 글로우 (기본)
  "shadow-[0_4px_15px_rgba(0,0,0,0.2)]",

  // Hover: 네온 글로우 강화
  "transition-all duration-300",
  "hover:border-cyan-400/50",
  "hover:shadow-[0_4px_20px_rgba(0,0,0,0.3),_0_0_25px_rgba(0,247,255,0.8)]",
)}>
  {/* 컨텐츠 */}
</div>
```

### 2.2 3D Glass Sphere (Taxonomy Node 패턴)

```tsx
// 3D 구체 효과 - radial-gradient로 입체감 생성
<div
  className="rounded-full transition-all duration-300"
  style={{
    // 핵심: 좌상단(30% 30%)에서 시작하는 radial-gradient
    background: `radial-gradient(
      circle at 30% 30%,
      rgba(0,247,255,0.4) 0%,
      rgba(0,247,255,0.2) 40%,
      rgba(0,247,255,0.05) 70%,
      transparent 100%
    )`,
    border: "1px solid rgba(0,247,255,0.5)",
  }}
>
  {/* Inner Highlight - 구체 상단 반사광 */}
  <div
    className="absolute top-1 left-1/4 w-1/3 h-1/4 rounded-full opacity-60"
    style={{
      background: "radial-gradient(ellipse at center, rgba(255,255,255,0.8) 0%, transparent 70%)",
    }}
  />
</div>
```

### 2.3 Transparent Image Container (로봇 이미지 패턴)

```tsx
// 투명 PNG 이미지를 위한 컨테이너
<div className="rounded-xl bg-gradient-to-b from-slate-800/40 to-slate-900/60 border border-white/10">
  <img
    src="/assets/agents/nobg/category/robot.png"  // 투명 PNG 사용
    className={cn(
      "object-contain",
      // 네온 글로우 효과
      "drop-shadow-[0_0_20px_rgba(0,247,255,0.6)]",
      // Hover 애니메이션
      "transition-transform duration-300 group-hover:scale-105"
    )}
  />
</div>
```

### 2.4 Space/Nebula Background

```tsx
// 우주 배경 레이어 구조
<div className="absolute inset-0 pointer-events-none overflow-hidden">
  {/* Layer 1: Base gradient */}
  <div className="absolute inset-0 bg-gradient-to-b from-[#0a0f1a] via-[#0d1425] to-[#050a15]" />

  {/* Layer 2: Purple nebula - top right */}
  <div
    className="absolute -top-20 -right-20 w-[600px] h-[600px] rounded-full opacity-30 blur-3xl"
    style={{ background: "radial-gradient(circle, rgba(139,92,246,0.4) 0%, transparent 70%)" }}
  />

  {/* Layer 3: Cyan nebula - bottom left */}
  <div
    className="absolute -bottom-40 -left-20 w-[500px] h-[500px] rounded-full opacity-25 blur-3xl"
    style={{ background: "radial-gradient(circle, rgba(0,247,255,0.3) 0%, transparent 70%)" }}
  />

  {/* Layer 4: Stars */}
  <div className="absolute inset-0 opacity-60"
    style={{
      backgroundImage: `
        radial-gradient(1px 1px at 20px 30px, white, transparent),
        radial-gradient(1.5px 1.5px at 160px 120px, rgba(0,247,255,0.9), transparent),
        radial-gradient(1.5px 1.5px at 250px 50px, rgba(139,92,246,0.9), transparent)
      `,
      backgroundSize: "400px 300px",
    }}
  />
</div>
```

---

## 3. Neon Glow Patterns

### 3.1 Text Glow

```tsx
// 기본 네온 텍스트
<span className="text-cyan-400 drop-shadow-[0_0_5px_rgba(0,247,255,0.7)]">
  Neon Text
</span>

// 강한 네온 텍스트 (호버/선택 시)
<span className="text-cyan-400 drop-shadow-[0_0_10px_rgba(0,247,255,0.8)]">
  Strong Neon
</span>
```

### 3.2 Icon Glow

```tsx
// 아이콘 글로우
<Icon className="text-cyan-400 drop-shadow-[0_0_8px_rgba(0,247,255,0.7)]" />

// Amber 아이콘 (Root/Special)
<Icon className="text-amber-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.7)]" />
```

### 3.3 Box Shadow Glow

```tsx
// 복합 글로우 (흰색 + 시안)
className="shadow-[0_0_15px_rgba(255,255,255,0.3),_0_0_25px_rgba(0,247,255,0.7)]"

// 호버 시 강화된 글로우
className="hover:shadow-[0_0_20px_rgba(0,247,255,0.5),_0_0_40px_rgba(0,247,255,0.3)]"
```

---

## 4. Interactive States

### 4.1 Hover Effects

```tsx
// 기본 호버 패턴
className={cn(
  "transition-all duration-300",
  "hover:border-cyan-400/50",
  "hover:scale-105",
  "hover:shadow-[0_0_25px_rgba(0,247,255,0.6)]"
)}
```

### 4.2 Selected/Active State

```tsx
// 선택된 상태
selected && cn(
  "border-cyan-400/60",
  "scale-110",
  "shadow-[0_0_20px_rgba(0,247,255,0.5),_0_0_40px_rgba(0,247,255,0.3)]"
)
```

### 4.3 Tooltip/Badge Pattern

```tsx
// HOVERED 배지 스타일
<div className={cn(
  "px-3 py-1 rounded-md",
  "bg-cyan-500 text-white text-xs font-bold uppercase tracking-wider",
  "shadow-lg shadow-cyan-500/50",
  "animate-in fade-in slide-in-from-bottom-2 duration-200"
)}>
  HOVERED
</div>

// 상세 정보 툴팁
<div className={cn(
  "px-4 py-3 rounded-lg",
  "bg-slate-800/90 backdrop-blur-xl border border-white/10",
  "shadow-2xl shadow-black/50"
)}>
  {/* 툴팁 컨텐츠 */}
</div>
```

---

## 5. Stats Cards Pattern

```tsx
// 통계 카드 (Dashboard 상단)
<div className={cn(
  "p-4 rounded-xl",
  "bg-white/5 backdrop-blur-lg",
  "border border-white/10",
  "shadow-lg shadow-black/20"
)}>
  <div className="flex items-center gap-3">
    <span className="text-2xl">🤖</span>
    <div>
      <p className="text-white/60 text-xs uppercase tracking-wider">Total Agents</p>
      <p className="text-white text-xl font-bold">15</p>
    </div>
  </div>
</div>
```

---

## 6. Progress Bar Pattern

```tsx
// 시안 네온 프로그레스 바
<div className="w-full h-1 rounded-full bg-slate-600/50 overflow-hidden">
  <div
    className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-400 shadow-[0_0_10px_rgba(34,211,238,0.6)]"
    style={{ width: `${progress}%` }}
  />
</div>
```

---

## 7. Button Patterns

### 7.1 Primary Button (Neon)

```tsx
<button className={cn(
  "px-4 py-2 rounded-lg",
  "bg-cyan-500/20 border border-cyan-400/50",
  "text-cyan-400 font-medium",
  "hover:bg-cyan-500/30 hover:border-cyan-400",
  "hover:shadow-[0_0_15px_rgba(0,247,255,0.5)]",
  "transition-all duration-300"
)}>
  + New Agent
</button>
```

### 7.2 Ghost Button

```tsx
<button className={cn(
  "px-3 py-2 rounded-lg",
  "text-gray-200 text-xs uppercase tracking-wider",
  "hover:bg-white/10",
  "transition-colors duration-200"
)}>
  Filter
</button>
```

---

## 8. Form Input Pattern

```tsx
// Search Input
<div className="relative">
  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
  <input
    type="text"
    placeholder="Search..."
    className={cn(
      "w-full pl-10 pr-4 py-2 rounded-lg",
      "bg-white/5 border border-white/10",
      "text-white placeholder:text-white/40",
      "focus:border-cyan-400/50 focus:outline-none",
      "focus:shadow-[0_0_10px_rgba(0,247,255,0.3)]",
      "transition-all duration-300"
    )}
  />
</div>
```

---

## 9. Animation Classes

```tsx
// Tailwind animate-in 확장 (globals.css에 추가 필요)
@keyframes glow-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.animate-glow-pulse {
  animation: glow-pulse 2s ease-in-out infinite;
}

// 사용 예시
<div className="animate-glow-pulse">Glowing Element</div>
```

---

## 10. 남은 페이지 적용 계획

### 10.1 적용 완료

- [x] **AI Agents** (`/agents`) - 투명 로봇 PNG, 카드 글로우
- [x] **Taxonomy Constellation** (`/taxonomy`) - 3D 구체 노드, 우주 배경

### 10.2 적용 필요

| 페이지 | 경로 | 적용 패턴 | 우선순위 |
|--------|------|----------|---------|
| Dashboard | `/` | Stats Cards, Chart Glow | High |
| Search | `/search` | Input, Results Card | High |
| Documents | `/documents` | Card Grid, Table Row | Medium |
| Settings | `/settings` | Form Inputs, Toggle | Low |
| Upload | `/upload` | Drag Zone, Progress | Medium |

### 10.3 적용 체크리스트

각 페이지 적용 시 확인사항:

```
□ 배경: bg-[#050a15] 또는 성운 배경 적용
□ 카드: bg-white/5 backdrop-blur-lg border-white/10
□ 호버: border-cyan-400/50 + 네온 글로우
□ 텍스트: 중요 수치는 text-cyan-400 + drop-shadow
□ 아이콘: drop-shadow-[0_0_8px_rgba(0,247,255,0.7)]
□ 버튼: 시안 네온 스타일 적용
□ 입력창: focus 시 시안 글로우
□ 프로그레스: 시안 그라데이션 + 글로우
```

---

## 11. Image Assets

### 11.1 투명 로봇 이미지 위치

```
/public/assets/agents/nobg/
├── common/
│   ├── robot-common-01.png
│   ├── robot-common-02.png
│   ├── robot-common-03.png
│   └── robot-common-04.png
├── rare/
│   └── ... (4 files)
├── epic/
│   └── ... (4 files)
└── legendary/
    └── ... (4 files)
```

### 11.2 새 이미지 추가 시

```bash
# rembg로 배경 제거
pip install rembg onnxruntime
python -c "
from rembg import remove
from PIL import Image

with open('input.webp', 'rb') as f:
    output = remove(f.read())
with open('output.png', 'wb') as f:
    f.write(output)
"
```

---

## 12. Quick Reference

### 가장 많이 사용하는 클래스 조합

```tsx
// 글래스 카드
"bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl"

// 네온 글로우 (시안)
"shadow-[0_0_15px_rgba(0,247,255,0.5)]"

// 네온 텍스트
"text-cyan-400 drop-shadow-[0_0_5px_rgba(0,247,255,0.7)]"

// 호버 효과
"hover:border-cyan-400/50 hover:shadow-[0_0_25px_rgba(0,247,255,0.8)] transition-all duration-300"

// 3D 구체 배경
"radial-gradient(circle at 30% 30%, rgba(0,247,255,0.4) 0%, transparent 100%)"
```

---

## 13. Deprecated 파일 목록

### 13.1 사용하지 말아야 할 파일들

| 경로 | 상태 | 대체 위치 |
|------|------|----------|
| `/components/constellation/` | ⚠️ DEPRECATED | `/components/taxonomy/` |
| `/public/avatars/robots/*.svg` | ⚠️ DEPRECATED | `/public/assets/agents/nobg/` |
| `/design-compliance-test.spec.ts` | ⚠️ 업데이트 필요 | 테스트 기준 변경됨 |

### 13.2 변경 이력

| 날짜 | 변경 사항 |
|------|----------|
| 2025-11-28 | 초기 DESIGN-SYSTEM.md 생성 |
| 2025-11-28 | 투명 PNG 로봇 이미지 적용 (rembg) |
| 2025-11-28 | 3D 유리 구체 노드 스타일 적용 |
| 2025-11-28 | 우주 성운 배경 추가 |
| 2025-11-28 | constellation/ 폴더 deprecated 처리 |

### 13.3 주의사항

- 새 컴포넌트 작성 시 반드시 이 가이드 참조
- deprecated 폴더의 컴포넌트 import 금지
- 디자인 변경 시 이 문서도 함께 업데이트

---

**이 가이드를 참조하여 남은 모든 페이지에 일관된 Ethereal Glass 테마를 적용하세요.**
