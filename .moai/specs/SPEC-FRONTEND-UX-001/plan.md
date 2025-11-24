# Implementation Plan: SPEC-FRONTEND-UX-001

## Overview
Research Agent Interface - 자연어 기반 지식 수집 인터페이스 구현

## Implementation Phases

### Phase 1: Basic Layout & Components (2-3 hours)
- [ ] Create ResearchAgent page component
- [ ] Implement split layout (Chat 40% / Progress 60%)
- [ ] Build ChatZone component with message bubbles
- [ ] Build ProgressZone component with stage indicator
- [ ] Add responsive stacking for mobile

### Phase 2: State Management & Mock Data (1-2 hours)
- [ ] Create ResearchState store with Zustand
- [ ] Implement state machine (idle → analyzing → searching → collecting → organizing → confirming → completed)
- [ ] Add mock progress data for testing
- [ ] Create useResearchAgent hook

### Phase 3: Real-time Progress Updates (2-3 hours)
- [ ] Set up WebSocket connection
- [ ] Implement progress event handlers
- [ ] Add circular progress indicator
- [ ] Create stage timeline component
- [ ] Display metrics cards (sources, documents, quality)

### Phase 4: Preview & Approval Flow (2-3 hours)
- [ ] Build document preview component
- [ ] Implement approval/rejection UI
- [ ] Add source filtering options
- [ ] Create final confirmation dialog

### Phase 5: Polish & Accessibility (1-2 hours)
- [ ] Add keyboard navigation
- [ ] Implement ARIA labels
- [ ] Add focus indicators
- [ ] Test responsive behavior
- [ ] Write component tests

## Technical Stack
- Next.js 14 (App Router)
- Tailwind CSS + shadcn/ui
- Zustand (state management)
- WebSocket (real-time updates)
- React Query (API calls)

## File Structure
```
apps/frontend/
├── app/research/
│   └── page.tsx              # Research Agent page
├── components/research/
│   ├── ChatZone.tsx          # Chat interface
│   ├── ProgressZone.tsx      # Progress dashboard
│   ├── StageTimeline.tsx     # Stage indicator
│   ├── MetricsCard.tsx       # Stats display
│   ├── DocumentPreview.tsx   # Preview component
│   └── ResearchActions.tsx   # Action buttons
├── stores/
│   └── researchStore.ts      # Zustand store
├── hooks/
│   └── useResearchAgent.ts   # Custom hook
└── types/
    └── research.ts           # Type definitions
```

## API Endpoints (Backend)
```
POST /api/v1/research/start         # Start research
GET  /api/v1/research/{id}/status   # Get status
POST /api/v1/research/{id}/confirm  # Confirm results
POST /api/v1/research/{id}/cancel   # Cancel research
WS   /ws/research/{id}              # Real-time updates
```

## Estimated Timeline
- **Total**: 8-13 hours
- **MVP (Phases 1-2)**: 3-5 hours
- **Full Features**: 8-13 hours
