# Acceptance Scenarios: SPEC-FRONTEND-INIT-001

## Format: Given-When-Then (Gherkin-style)

---

## Scenario 1: Project Initialization Success

**Feature**: Frontend project setup with Vite + React 18 + TypeScript 5

**Scenario**: Developer initializes new frontend project

**Given** the root directory contains `package.json` with workspace configuration
**And** pnpm 9.0+ is installed on the system
**And** Node.js 20+ is available

**When** the developer runs:
```bash
pnpm create vite@latest frontend --template react-ts
cd frontend
pnpm install
```

**Then** the `frontend/` directory should be created
**And** `frontend/package.json` should contain:
  - `"react": "^18.3.1"`
  - `"vite": "^5.4.6"`
  - `"typescript": "^5.6.2"`
**And** the command `pnpm dev` should start the dev server at `http://localhost:5173`
**And** the command `pnpm build` should succeed with output in `frontend/dist/`
**And** zero errors should be logged in the terminal

---

## Scenario 2: Cherry-Picked Code Integration

**Feature**: Reuse existing type-safe API layer

**Scenario**: Developer copies and adapts cherry-picked files

**Given** the existing frontend has:
  - `apps/frontend/lib/api/types.ts` (409 lines, Zod schemas)
  - `apps/frontend/lib/api/client.ts` (axios client)
  - `apps/frontend/lib/env.ts` (environment validation)
  - `apps/frontend/lib/utils.ts` (cn utility)

**When** the developer copies these 4 files to `frontend/src/lib/`
**And** adapts `env.ts` to use `VITE_*` environment variables instead of `NEXT_PUBLIC_*`
**And** creates `.env.example` with:
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000
VITE_API_KEY=your-api-key-here
```

**Then** importing types should work without errors:
```typescript
import { SearchRequest, SearchResponse, TaxonomyNode } from '@/lib/api/types'
```
**And** the IDE should provide autocomplete for all 40+ types from `types.ts`
**And** the command `pnpm type-check` (tsc --noEmit) should succeed with zero errors
**And** `apiClient` from `@/lib/api/client` should be importable
**And** `env.VITE_API_URL` should resolve to the default value or environment variable

---

## Scenario 3: Build and Type-Check Success

**Feature**: TypeScript strict mode compilation

**Scenario**: Developer runs build and type-check commands

**Given** the project has:
  - `tsconfig.json` with `"strict": true`
  - All cherry-picked files in `src/lib/`
  - Core dependencies installed (React, axios, zod, etc.)

**When** the developer runs:
```bash
pnpm type-check  # or tsc --noEmit
pnpm lint
pnpm build
```

**Then** the `type-check` command should exit with code 0 (no TypeScript errors)
**And** the `lint` command should report 0 warnings
**And** the `build` command should create an optimized bundle in `frontend/dist/`
**And** the build output should show:
  - Vite build completed in < 10 seconds
  - Chunk sizes optimized (main chunk < 500 KB)
  - No warnings about missing modules

---

## Scenario 4: Tailwind CSS Configuration

**Feature**: Design system color setup

**Scenario**: Developer configures Tailwind with DT-RAG color palette

**Given** Tailwind CSS 3.4.12+ is installed
**And** `tailwind.config.js` defines custom colors:
  - `primary`: `#0099FF`
  - `accent.purple`: `#A78BFA`
  - `accent.gold`: `#F59E0B`

**When** the developer creates a test component:
```tsx
export function TestCard() {
  return (
    <div className="bg-primary text-white p-4 rounded-lg">
      <span className="text-accent-gold">Legendary</span>
    </div>
  )
}
```
**And** runs `pnpm dev`

**Then** the component should render with:
  - Background color `#0099FF` (primary blue)
  - Text color `#F59E0B` for "Legendary" (gold)
**And** the IDE should provide autocomplete for custom Tailwind colors
**And** the build should purge unused styles (build size < 50 KB for CSS)

---

## Scenario 5: Environment Variable Loading

**Feature**: Zod-based environment validation

**Scenario**: Developer verifies environment variables are loaded correctly

**Given** `.env` file exists in project root with:
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_KEY=test-api-key-1234567890abcdefghijklmnopqrstuvwxyz
```

**When** the developer imports and uses `env`:
```typescript
import { env } from '@/lib/env'

console.log('API URL:', env.VITE_API_URL)
console.log('API Key:', env.VITE_API_KEY)
```

**Then** `env.VITE_API_URL` should equal `"http://localhost:8000/api/v1"`
**And** `env.VITE_API_KEY` should equal the test API key
**And** no validation errors should be thrown by Zod
**And** changing `.env` values should reflect in the next dev server restart

---

## Scenario 6: Import Path Alias Resolution

**Feature**: TypeScript path alias for clean imports

**Scenario**: Developer uses `@/*` alias for imports

**Given** `tsconfig.json` defines:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```
**And** `vite.config.ts` resolves the alias

**When** the developer writes:
```typescript
import { apiClient } from '@/lib/api/client'
import { SearchRequest } from '@/lib/api/types'
import { cn } from '@/lib/utils'
```

**Then** all imports should resolve without errors
**And** the IDE should provide "Go to Definition" navigation for each import
**And** TypeScript should not report module resolution errors
**And** the build should bundle correctly with path alias resolution

---

## Scenario 7: ESLint Code Quality Check

**Feature**: Automated code linting

**Scenario**: Developer runs ESLint to catch code quality issues

**Given** `.eslintrc.cjs` is configured with:
  - TypeScript rules enabled
  - React Hooks rules enabled
  - Max warnings set to 0

**When** the developer runs:
```bash
pnpm lint
```

**Then** ESLint should analyze all `.ts` and `.tsx` files in `src/`
**And** the command should exit with code 0 (no errors)
**And** zero warnings should be reported
**And** if a developer writes unused variables, ESLint should catch them before commit

---

## Scenario 8: Dev Server Hot Reload

**Feature**: Fast development feedback loop

**Scenario**: Developer makes changes and sees instant updates

**Given** the dev server is running via `pnpm dev`
**And** the browser is open at `http://localhost:5173`

**When** the developer modifies `src/App.tsx`:
```tsx
// Change background color
<div className="bg-primary" /> // Changed from bg-white
```

**Then** the browser should automatically reload within 1 second
**And** the new background color should be visible without manual refresh
**And** no console errors should appear in the browser DevTools
**And** Vite HMR (Hot Module Replacement) should preserve React component state

---

## Scenario 9: Cherry-Picked Types Autocomplete

**Feature**: Full TypeScript IntelliSense for API types

**Scenario**: Developer uses IDE autocomplete for backend API types

**Given** `src/lib/api/types.ts` contains 409 lines of Zod schemas
**And** VS Code (or similar IDE) is open with TypeScript language server

**When** the developer types:
```typescript
import { SearchRequest } from '@/lib/api/types'

const req: SearchRequest = {
  q: "machine learning",
  final_topk: // <-- cursor here
}
```

**Then** the IDE should suggest `number` type for `final_topk`
**And** hovering over `SearchRequest` should show the full Zod schema structure
**And** pressing Ctrl+Space should show all available fields from `SearchRequest`
**And** TypeScript should flag missing required fields with red squiggles

---

## Scenario 10: Production Build Optimization

**Feature**: Optimized bundle for deployment

**Scenario**: Developer builds for production

**Given** all dependencies are installed
**And** source code is error-free

**When** the developer runs:
```bash
pnpm build
```

**Then** Vite should create an optimized bundle in `frontend/dist/`
**And** the main JavaScript chunk should be < 500 KB
**And** the main CSS file should be < 50 KB
**And** all assets should have hashed filenames (e.g., `app.abc123.js`)
**And** the `dist/index.html` should reference all assets correctly
**And** running `npx serve dist` should serve a functional app at `http://localhost:3000`

---

## Edge Cases & Error Handling

### Edge Case 1: Missing Environment Variables

**Given** `.env` file does not exist or is incomplete

**When** the app tries to import `env` from `@/lib/env`

**Then** Zod validation should throw an error with message:
```
Environment validation failed: {
  VITE_API_URL: "Invalid url"
}
```
**And** the app should NOT start with undefined environment variables
**And** the error message should clearly indicate which variables are missing

### Edge Case 2: Next.js Import in Cherry-Picked Code

**Given** `lib/api/client.ts` originally contained `import { useRouter } from 'next/router'`

**When** the file is copied to Vite project without removing Next.js imports

**Then** TypeScript should report:
```
Cannot find module 'next/router' or its corresponding type declarations.
```
**And** the developer must remove or replace Next.js-specific code before build succeeds

### Edge Case 3: Tailwind Purge Removes Active Styles

**Given** Tailwind config has incorrect `content` paths:
```javascript
content: ["./src/**/*.tsx"] // Missing .ts files
```

**When** a utility function uses Tailwind classes dynamically

**Then** those classes might be purged from the final CSS bundle
**And** the fix is to update `content` to include all relevant files:
```javascript
content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"]
```

---

## Success Criteria Summary

**All 10 scenarios must pass:**
- ✅ Project initializes with Vite + React 18 + TypeScript 5
- ✅ Cherry-picked code (4 files) integrates successfully
- ✅ Build and type-check succeed with zero errors
- ✅ Tailwind CSS renders custom colors correctly
- ✅ Environment variables load and validate via Zod
- ✅ Path alias `@/*` resolves in imports
- ✅ ESLint runs with zero warnings
- ✅ Dev server hot reloads changes instantly
- ✅ IDE provides autocomplete for all API types
- ✅ Production build is optimized and functional

**Edge cases handled:**
- ✅ Missing environment variables throw clear errors
- ✅ Next.js imports are removed from cherry-picked code
- ✅ Tailwind purge does not remove active styles

---

**Last Updated**: 2025-10-30
**Status**: Ready for Testing
