# Implementation Plan - Frontend Rebuild (Ethereal Glass)

## Goal
Rebuild the entire frontend application to fully adopt the "Ethereal Glass" design aesthetic. This involves updating the core layout, redesigning remaining pages, and standardizing all UI components.

## User Review Required
> [!IMPORTANT]
> This is a major visual overhaul. All existing "Cyberpunk" or "Default" styles will be replaced with the "Ethereal Glass" theme (Deep Navy, Glassmorphism, Subtle Glows).

## Proposed Changes

### Phase 1: Core Shell & Foundation
Establish the global look and feel.
#### [MODIFY] [globals.css](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/globals.css)
- Enforce deep navy background (`#0b1121`).
- Add global glass utilities (`.bg-glass`, `.text-glow`).
#### [MODIFY] [layout.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/layout.tsx)
- Apply global font and background.
#### [MODIFY] [Sidebar.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/layout/Sidebar.tsx)
- Convert to a glass panel with blurred background.
- Update navigation links with glowing hover states.
#### [MODIFY] [Header.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/layout/Header.tsx)
- Minimalist glass header.

### Phase 2: Dashboard Home
Redesign the main landing view.
#### [MODIFY] [page.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/(dashboard)/page.tsx)
- Create a "Mission Control" dashboard.
- Use glass cards for high-level metrics (System Health, Recent Activity).

### Phase 3: Secondary Pages
Apply the design to remaining routes.
#### [MODIFY] [Agents Page](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/(dashboard)/agents/page.tsx)
- Grid view of agents with holographic cards.
#### [MODIFY] [Monitoring Page](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/(dashboard)/monitoring/page.tsx)
- Real-time charts in glass containers.
#### [MODIFY] [Taxonomy Builder](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/(dashboard)/taxonomy-builder/page.tsx)
- Interactive tree builder with glass nodes.
#### [MODIFY] [Research Page](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/research/page.tsx)
- Document reading pane and note-taking area in split glass view.

### Phase 4: UI Components
Standardize the building blocks.
#### [MODIFY] [components/ui/*](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui)
- **Card**: Glass background, white/10 border.
- **Button**: Glass hover effects, glowing primary buttons.
- **Input/Select**: Transparent backgrounds with bottom borders or glass fills.
- **Dialog/Modal**: Backdrop blur and glass container.

## Verification Plan
### Automated Tests
- Build verification: `npm run build`
- Lint check: `npm run lint`

### Manual Verification
- **Visual Check**: Verify "Ethereal Glass" look on all pages.
- **Responsiveness**: Check Sidebar and Layout on mobile view.
- **Interactions**: Test hover states, focus states, and transitions.
