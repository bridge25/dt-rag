---
id: SPEC-FRONTEND-INIT-001
title: Vite + React 18 + TypeScript Frontend Initialization with Cherry-Picked Code
status: completed
priority: P0
assignee: tdd-implementer
created: 2025-10-30
updated: 2025-10-30
completed: 2025-10-30
version: 0.1.0
tags: [frontend, initialization, vite, react, typescript, cherry-pick]
dependencies: []
---

# SPEC-FRONTEND-INIT-001: Vite + React 18 + TypeScript Frontend Initialization with Cherry-Picked Code

## 1. Overview

### 1.1 Purpose
Initialize a new frontend project using Vite 5, React 18, and TypeScript 5 to replace the existing Next.js admin dashboard with a user-centric SaaS platform. Cherry-pick valuable code from the existing frontend (`apps/frontend/lib/`) to accelerate development.

### 1.2 Background
- Current frontend: Next.js 14 admin dashboard (to be replaced)
- New vision: User-centric SaaS with game-style agent cards, Korean language support, and TAXONOMY visualization
- Master plan document: `docs/frontend-design-master-plan.md`
- Cherry-pick targets: 4 critical files providing type safety, API client, and utilities

### 1.3 Scope
**In Scope:**
- Create new Vite project with React 18 + TypeScript 5
- Set up directory structure (`src/{components,pages,hooks,stores,lib,types,utils}`)
- Cherry-pick 4 files from existing frontend:
  - `lib/api/types.ts` (409 lines of Zod schemas - CRITICAL)
  - `lib/api/client.ts` (axios with interceptors)
  - `lib/env.ts` (Zod-based environment validation)
  - `lib/utils.ts` (cn utility for Tailwind)
- Install core dependencies (React Router, TanStack Query, Zustand, Tailwind CSS, etc.)
- Configure Tailwind CSS with design system colors
- Verify build and type-check success

**Out of Scope:**
- UI component implementation (Phase 2)
- API integration testing (Phase 2)
- Deployment configuration (Phase 3)

## 2. EARS Requirements

### 2.1 Ubiquitous Behaviors

**REQ-INIT-001**: **WHILE** the frontend project is being initialized, **THE SYSTEM SHALL** use Vite 5.4.6+ as the build tool to ensure fast development experience.

**REQ-INIT-002**: **WHILE** setting up TypeScript configuration, **THE SYSTEM SHALL** enable strict mode (`"strict": true`) to catch type errors at compile time.

**REQ-INIT-003**: **WHILE** installing dependencies, **THE SYSTEM SHALL** use pnpm as the package manager for fast installation and disk space efficiency.

**REQ-INIT-004**: **WHILE** cherry-picking code from existing frontend, **THE SYSTEM SHALL** copy files to `frontend/src/lib/` maintaining the same directory structure.

### 2.2 Event-Driven Behaviors

**REQ-INIT-005**: **WHEN** the developer runs `pnpm create vite@latest`, **THE SYSTEM SHALL** create a new project with React-TypeScript template in the `frontend/` directory.

**REQ-INIT-006**: **WHEN** copying `lib/api/types.ts`, **THE SYSTEM SHALL** preserve all 409 lines of Zod schemas without modification to maintain type safety with backend API.

**REQ-INIT-007**: **WHEN** copying `lib/env.ts`, **THE SYSTEM SHALL** adapt environment variable prefixes from `NEXT_PUBLIC_*` to `VITE_*` for Vite compatibility.

**REQ-INIT-008**: **WHEN** Tailwind CSS is configured, **THE SYSTEM SHALL** define design system colors in `tailwind.config.js`:
- Primary: `#0099FF`
- Primary light: `#E6F5FF`
- Accent purple: `#A78BFA` (Epic rarity)
- Accent pink: `#FB7185`
- Accent green: `#34D399`
- Accent yellow: `#FCD34D`
- Accent orange: `#FB923C` (Rare rarity)
- Accent gold: `#F59E0B` (Legendary rarity)

**REQ-INIT-009**: **WHEN** the developer runs `pnpm build`, **THE SYSTEM SHALL** successfully compile TypeScript without errors.

**REQ-INIT-010**: **WHEN** the developer runs `pnpm type-check`, **THE SYSTEM SHALL** verify all types are correct with zero TypeScript errors.

### 2.3 State-Driven Behaviors

**REQ-INIT-011**: **WHILE** the project is in development mode (`pnpm dev`), **IF** cherry-picked types are imported, **THE SYSTEM SHALL** provide autocomplete for all API types from `lib/api/types.ts`.

**REQ-INIT-012**: **WHILE** ESLint is running, **IF** code violates style rules, **THE SYSTEM SHALL** report violations and provide fixable suggestions.

### 2.4 Optional Behaviors

**REQ-INIT-013**: **WHERE** the developer wants dark mode, **THE SYSTEM MAY** include dark mode color definitions in Tailwind config for future implementation.

**REQ-INIT-014**: **WHERE** additional testing tools are needed, **THE SYSTEM MAY** install Vitest for unit testing in Phase 2.

### 2.5 Unwanted Behaviors

**REQ-INIT-015**: **IF** cherry-picked code contains Next.js-specific imports (e.g., `next/router`), **THE SYSTEM SHALL NOT** include those files or **SHALL** remove those imports before copying.

**REQ-INIT-016**: **IF** TypeScript build fails, **THE SYSTEM SHALL NOT** proceed with Git commit until all errors are resolved.

**REQ-INIT-017**: **THE SYSTEM SHALL NOT** modify the existing Next.js frontend (`apps/frontend/`) during this initialization phase.

## 3. Technical Specifications

### 3.1 Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components (Phase 2)
│   ├── pages/          # Page components (Phase 2)
│   ├── hooks/          # Custom React hooks (Phase 2)
│   ├── stores/         # Zustand stores (Phase 2)
│   ├── lib/            # Cherry-picked code + utilities
│   │   ├── api/
│   │   │   ├── types.ts     # 409 lines of Zod schemas (CRITICAL)
│   │   │   └── client.ts    # Axios client with interceptors
│   │   ├── env.ts           # Zod-based environment validation
│   │   └── utils.ts         # cn() utility for Tailwind
│   ├── types/          # Additional TypeScript types (Phase 2)
│   ├── utils/          # Helper functions (Phase 2)
│   ├── App.tsx         # Root component
│   └── main.tsx        # Entry point
├── .env.example        # Environment variables template
├── .eslintrc.cjs       # ESLint config
├── tsconfig.json       # TypeScript config
├── vite.config.ts      # Vite config
├── tailwind.config.js  # Tailwind CSS config
├── postcss.config.js   # PostCSS config
└── package.json        # Dependencies
```

### 3.2 Core Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.56.0",
    "zustand": "^4.5.5",
    "axios": "^1.7.7",
    "zod": "^3.23.8",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.0",
    "lucide-react": "^0.446.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.9",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.2",
    "typescript": "^5.6.2",
    "vite": "^5.4.6",
    "eslint": "^9.11.1",
    "@typescript-eslint/eslint-plugin": "^8.7.0",
    "@typescript-eslint/parser": "^8.7.0",
    "tailwindcss": "^3.4.12",
    "postcss": "^8.4.47",
    "autoprefixer": "^10.4.20"
  }
}
```

### 3.3 TypeScript Configuration (tsconfig.json)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3.4 Cherry-Pick Adaptations

#### env.ts Adaptation
```typescript
// Original: NEXT_PUBLIC_API_URL
// New: VITE_API_URL

const envSchema = z.object({
  VITE_API_URL: z.string().url().optional().default("http://localhost:8000/api/v1"),
  VITE_API_TIMEOUT: z.string().optional().default("30000").pipe(z.string().regex(/^\d+$/).transform(Number)),
  VITE_API_KEY: z.string().min(32).optional(),
})

const parsedEnv = envSchema.safeParse({
  VITE_API_URL: import.meta.env.VITE_API_URL,
  VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT,
  VITE_API_KEY: import.meta.env.VITE_API_KEY,
})
```

## 4. Acceptance Criteria

See `acceptance.md` for detailed Given-When-Then scenarios.

## 5. Implementation Plan

See `plan.md` for milestone breakdown.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Cherry-picked code has Next.js dependencies | High | Manual review and removal of Next.js imports |
| TypeScript strict mode causes errors | Medium | Fix type errors incrementally during cherry-pick |
| Vite environment variables not loaded | Medium | Create `.env.example` with clear documentation |
| Tailwind CSS purge removes needed styles | Low | Configure `content` paths correctly in `tailwind.config.js` |

## 7. Testing Strategy

- **Build Test**: `pnpm build` succeeds with zero errors
- **Type Check**: `pnpm type-check` (tsc --noEmit) succeeds
- **Lint Check**: `pnpm lint` succeeds with zero warnings
- **Import Test**: Create test file importing cherry-picked types and verify autocomplete works

## 8. Documentation

- README.md: Project setup instructions
- .env.example: Environment variables documentation
- Inline comments in cherry-picked files explaining adaptations

## 9. Related Documents

- Master Plan: `docs/frontend-design-master-plan.md`
- Backend Architecture: `docs/backend-architecture-frontend-ui-proposal.md`
- Existing Frontend: `apps/frontend/`

## 10. HISTORY

### v0.1.0 - 2025-10-30 - Implementation Complete
- ✅ Vite 7.1.7 + React 19.1.1 + TypeScript 5.9.3 프로젝트 초기화 완료
- ✅ Cherry-picked 4개 파일 및 Vite 적응:
  - `lib/api/types.ts` (411 lines) - Zod 스키마 100% 보존
  - `lib/api/client.ts` (25 lines) - VITE_* 환경변수 적용
  - `lib/env.ts` (20 lines) - import.meta.env 변환
  - `lib/utils.ts` (6 lines) - 변경 없음
- ✅ Tailwind CSS v4.1.16 디자인 시스템 색상 구성
- ✅ 모든 품질 게이트 통과:
  - Build: Success (0 errors, 8.28s)
  - Type-Check: Success (0 errors)
  - Lint: Success (0 warnings)
- ✅ 20개 파일 추가, 3,239 lines
- **Branch:** feature/SPEC-FRONTEND-INIT-001
- **Commits:**
  - 68166e6d - 🎩 SPEC 문서 생성
  - 0dfd1a5b - 🟢 GREEN 구현 완료
- **Quality Verification:** 18/18 items passed (0 critical, 0 warnings)

### v0.0.1 - 2025-10-30 - SPEC Creation
- Initial SPEC creation based on user requirements and master plan
- Defined EARS requirements for Vite + React 18 initialization
- Specified cherry-pick strategy for 4 critical files
- Documented technical specifications and acceptance criteria
