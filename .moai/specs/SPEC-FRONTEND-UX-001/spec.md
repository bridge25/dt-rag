---
id: SPEC-FRONTEND-UX-001
title: Research Agent Interface Design
status: draft
created: 2025-11-23
author: "@user"
tags: [frontend, ux, research-agent, interface-design]
version: 1.0.0
---

# SPEC-FRONTEND-UX-001: Research Agent Interface Design

## Overview

리서치 에이전트 인터페이스는 사용자가 자연어로 원하는 전문 지식 영역을 설명하면,
시스템이 자동으로 웹에서 관련 자료를 수집하여 지식 베이스를 구축하는 핵심 기능의 UI/UX 설계입니다.

## Requirements (EARS Format)

### Functional Requirements

**EARS-001**: WHEN 사용자가 리서치 페이지에 접근 THEN 시스템은 대화형 인터페이스와 진행 상태 패널을 분할 화면으로 표시해야 한다

**EARS-002**: WHEN 사용자가 "암 전문 의학박사 에이전트 만들고 싶어" 같은 자연어 입력 THEN 시스템은 다음을 수행해야 한다:
- 필요한 지식 카테고리 자동 추출
- 예상 수집 범위 표시
- 사용자 확인 요청

**EARS-003**: WHILE 리서치가 진행 중일 때 THEN 시스템은 실시간으로 다음을 표시해야 한다:
- 현재 진행 단계 (Planning → Searching → Collecting → Organizing)
- 진행률 (0-100%)
- 현재 검색 중인 소스
- 발견된 문서 수
- 예상 남은 시간

**EARS-004**: WHEN 중간 결과가 준비되면 THEN 시스템은 사용자에게 다음 옵션을 제공해야 한다:
- 수집된 자료 미리보기
- 계속 진행
- 수정 요청
- 취소

### UI Layout Requirements

**EARS-005**: The interface SHALL be divided into three main zones:
```
┌──────────────────────────────────────────────────┐
│                  Header Zone                      │
│  Title | Status Badge | Help Icon                 │
├────────────────┬──────────────────────────────────┤
│                │                                  │
│  Chat Zone     │     Progress Zone                │
│  (40% width)   │     (60% width)                  │
│                │                                  │
│  - Input area  │  - Stage indicator               │
│  - Messages    │  - Progress bars                 │
│  - Actions     │  - Found items list              │
│                │  - Source breakdown              │
│                │                                  │
└────────────────┴──────────────────────────────────┘
```

### Interaction Flow

**EARS-006**: The user journey SHALL follow this sequence:
1. Initial Query Input
2. Scope Confirmation
3. Real-time Progress Monitoring
4. Intermediate Review (optional)
5. Final Approval
6. Integration with Knowledge Base

### Visual Design Guidelines for Nanobanana

**EARS-007**: The interface SHOULD follow these design principles:

```yaml
Color Scheme:
  primary: "#0099FF"      # Action buttons, links
  success: "#10B981"      # Progress indicators
  warning: "#F59E0B"      # Confirmation states
  neutral: "#6B7280"      # Secondary text
  background: "#FFFFFF"   # Main background
  surface: "#F9FAFB"      # Card backgrounds

Typography:
  heading: "32px, Bold, -0.02em"
  subheading: "18px, SemiBold"
  body: "16px, Regular, 1.6 line-height"
  caption: "14px, Regular"

Spacing:
  component-gap: "24px"
  section-gap: "48px"
  padding: "16px"

Components:
  border-radius: "12px"
  shadow: "0 1px 3px rgba(0,0,0,0.1)"
  transition: "all 0.2s ease"
```

### State Management

**EARS-008**: The interface SHALL handle these states:
- `idle`: Waiting for user input
- `analyzing`: Processing user query
- `searching`: Active web search
- `collecting`: Downloading and processing
- `organizing`: Structuring into taxonomy
- `confirming`: Awaiting user approval
- `completed`: Successfully integrated
- `error`: Failed with recovery options

### Responsive Behavior

**EARS-009**: WHEN viewport width < 768px THEN the layout SHALL stack vertically:
- Chat zone: 100% width, top
- Progress zone: 100% width, bottom
- Collapsible sections for space efficiency

### Accessibility Requirements

**EARS-010**: The interface SHALL comply with WCAG 2.1 Level AA:
- All interactive elements keyboard accessible
- ARIA labels for screen readers
- Color contrast ratio ≥ 4.5:1
- Focus indicators visible

## Unwanted Behaviors

**UB-001**: The system SHALL NOT start collecting without user confirmation
**UB-002**: The system SHALL NOT block the UI during long operations
**UB-003**: The system SHALL NOT lose progress if connection is interrupted
**UB-004**: The system SHALL NOT collect from unreliable sources without warning

## Technical Specifications

### Component Structure
```typescript
interface ResearchAgentInterface {
  // Main container
  container: {
    layout: "split" | "stacked";
    theme: "light" | "dark";
  };

  // Chat zone
  chat: {
    messages: ChatMessage[];
    input: TextInput;
    suggestions: string[];
    actions: ActionButton[];
  };

  // Progress zone
  progress: {
    stage: ResearchStage;
    percentage: number;
    metrics: {
      sourcesSearched: number;
      documentsFound: number;
      qualityScore: number;
    };
    timeline: StageTimeline[];
    preview: DocumentPreview[];
  };
}
```

### API Integration Points
```typescript
// WebSocket for real-time updates
ws.on('research:progress', (data) => {
  updateProgress(data);
});

// REST endpoints
POST /api/v1/research/start
GET  /api/v1/research/{id}/status
POST /api/v1/research/{id}/confirm
POST /api/v1/research/{id}/cancel
```

## Acceptance Criteria

- [ ] User can describe desired knowledge domain in natural language
- [ ] Progress is visible in real-time with meaningful stages
- [ ] User can preview and approve collected materials
- [ ] Interface is responsive and accessible
- [ ] Error states provide clear recovery actions
- [ ] Successfully collected data integrates with taxonomy

## Implementation Priority

1. **Phase 1**: Basic chat interface + mock progress
2. **Phase 2**: Real-time progress with WebSocket
3. **Phase 3**: Preview and approval flow
4. **Phase 4**: Advanced features (source filtering, quality settings)

## Design Mockup Instructions for Nanobanana

### Prompt for Main Screen:
```
Create a modern web interface for a research agent with:
- Split layout: 40% chat on left, 60% progress dashboard on right
- Clean, minimal design with #0099FF as primary color
- Chat area with message bubbles and input field at bottom
- Progress dashboard showing:
  - Circular progress indicator (big, centered)
  - Stage timeline (Planning → Searching → Collecting → Organizing)
  - Metrics cards showing sources, documents, quality score
  - List of found items with source badges
- Use Inter font, plenty of whitespace, subtle shadows
- Professional yet friendly appearance
```

### Prompt for Mobile Version:
```
Create a mobile version of the research agent interface:
- Single column layout
- Chat interface at top with collapsible history
- Progress section below with expandable details
- Bottom navigation with stage indicators
- Thumb-friendly touch targets (min 44px)
- Same color scheme but adapted for mobile
```

## Related SPECs

- SPEC-FRONTEND-UX-002: Agent Creation Flow
- SPEC-FRONTEND-UX-003: Conversation Interface
- SPEC-BACKEND-RESEARCH-001: Research Agent Backend

---

## History

- 2025-11-23: Initial draft created