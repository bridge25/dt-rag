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
Standardize the building blocks to use the "Ethereal Glass" aesthetic by default.

#### [MODIFY] [components/ui/card.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui/card.tsx)
- Update default styles to use `bg-white/5`, `border-white/10`, and `backdrop-blur-md`.

#### [MODIFY] [components/ui/button.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui/button.tsx)
- Update variants (default, secondary, ghost, outline) to use glass styles and glowing hover effects.

#### [MODIFY] [components/ui/input.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui/input.tsx)
- Update to transparent background with `border-white/10` and `focus:border-blue-500/50`.

#### [MODIFY] [components/ui/dialog.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui/dialog.tsx)
- Update overlay to `bg-black/80` and content to `bg-[#0b1121]/90` with glass border.

#### [MODIFY] [components/ui/tabs.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui/tabs.tsx)
- Update tab list to `bg-white/5` and triggers to use glass active states.

#### [MODIFY] [components/ui/badge.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/components/ui/badge.tsx)
- Update default badge to use glass background and subtle border.

#### [MODIFY] [app/not-found.tsx](file:///wsl.localhost/Ubuntu/home/a/projects/dt-rag-standalone/apps/frontend/app/not-found.tsx)
- Update to use the new glass components and layout.

## Verification Plan
### Automated Tests
- Build verification: `npm run build`
- Lint check: `npm run lint`

### Manual Verification
- **Visual Check**: Verify "Ethereal Glass" look on all pages.
- **Responsiveness**: Check Sidebar and Layout on mobile view.
- **Interactions**: Test hover states, focus states, and transitions.
