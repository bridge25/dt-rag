# Implementation Plan: SPEC-FRONTEND-INIT-001

## Milestone Breakdown

### Milestone 1: Project Scaffolding (Day 1, 2 hours)

**Goal**: Create Vite project with React-TypeScript template

**Tasks**:
1. Run `pnpm create vite@latest frontend --template react-ts`
2. Navigate to `frontend/` directory
3. Install base dependencies: `pnpm install`
4. Verify dev server starts: `pnpm dev`
5. Verify build succeeds: `pnpm build`

**Acceptance**:
- ✅ `frontend/` directory exists with Vite template
- ✅ Dev server accessible at `http://localhost:5173`
- ✅ Build output in `frontend/dist/`

---

### Milestone 2: Core Dependencies Installation (Day 1, 1 hour)

**Goal**: Install React Router, TanStack Query, Zustand, Tailwind CSS

**Tasks**:
1. Install routing: `pnpm add react-router-dom`
2. Install data fetching: `pnpm add @tanstack/react-query`
3. Install state management: `pnpm add zustand`
4. Install axios & zod: `pnpm add axios zod`
5. Install Tailwind utilities: `pnpm add clsx tailwind-merge`
6. Install icons: `pnpm add lucide-react`
7. Install Tailwind CSS: `pnpm add -D tailwindcss postcss autoprefixer`
8. Initialize Tailwind: `npx tailwindcss init -p`

**Acceptance**:
- ✅ All dependencies in `package.json`
- ✅ `tailwind.config.js` and `postcss.config.js` created
- ✅ No dependency conflicts

---

### Milestone 3: TypeScript Configuration (Day 1, 30 minutes)

**Goal**: Configure strict TypeScript with path aliases

**Tasks**:
1. Update `tsconfig.json`:
   - Enable `"strict": true`
   - Add `"noUnusedLocals": true`
   - Add `"noUnusedParameters": true`
   - Add path alias: `"@/*": ["./src/*"]`
2. Create `tsconfig.node.json` for Vite config
3. Update `vite.config.ts` to support path aliases

**Acceptance**:
- ✅ `pnpm type-check` (tsc --noEmit) succeeds
- ✅ Path alias `@/` resolves correctly

---

### Milestone 4: Directory Structure Creation (Day 1, 30 minutes)

**Goal**: Create organized directory structure

**Tasks**:
1. Create directories:
   ```bash
   mkdir -p src/components
   mkdir -p src/pages
   mkdir -p src/hooks
   mkdir -p src/stores
   mkdir -p src/lib/api
   mkdir -p src/types
   mkdir -p src/utils
   ```
2. Create placeholder files for future implementation:
   - `src/pages/HomePage.tsx`
   - `src/pages/TaxonomyPage.tsx`
   - `src/pages/UploadPage.tsx`

**Acceptance**:
- ✅ All directories exist
- ✅ Project structure matches SPEC

---

### Milestone 5: Cherry-Pick Code from Existing Frontend (Day 2, 3 hours)

**Goal**: Copy 4 critical files and adapt for Vite

**Tasks**:

#### Task 5.1: Copy `lib/api/types.ts` (CRITICAL - NO CHANGES)
1. Copy `apps/frontend/lib/api/types.ts` → `frontend/src/lib/api/types.ts`
2. **DO NOT MODIFY** - This file is 100% reusable
3. Verify imports resolve (zod should be installed)

#### Task 5.2: Copy `lib/api/client.ts` (Minor adaptation)
1. Copy `apps/frontend/lib/api/client.ts` → `frontend/src/lib/api/client.ts`
2. Change import: `from "../env"` → `from "@/lib/env"`
3. Verify axios imports resolve

#### Task 5.3: Adapt `lib/env.ts` (Environment variables)
1. Copy `apps/frontend/lib/env.ts` → `frontend/src/lib/env.ts`
2. Replace all `NEXT_PUBLIC_` prefixes with `VITE_`
3. Replace `process.env.NEXT_PUBLIC_API_URL` with `import.meta.env.VITE_API_URL`
4. Create `.env.example`:
   ```bash
   VITE_API_URL=http://localhost:8000/api/v1
   VITE_API_TIMEOUT=30000
   VITE_API_KEY=your-api-key-here
   ```

#### Task 5.4: Copy `lib/utils.ts` (NO CHANGES)
1. Copy `apps/frontend/lib/utils.ts` → `frontend/src/lib/utils.ts`
2. Verify `clsx` and `tailwind-merge` imports resolve

**Acceptance**:
- ✅ 4 files copied to `frontend/src/lib/`
- ✅ `env.ts` adapted for Vite (VITE_* prefixes)
- ✅ No Next.js-specific imports remain
- ✅ `.env.example` created
- ✅ TypeScript builds without errors

---

### Milestone 6: Tailwind CSS Configuration (Day 2, 1 hour)

**Goal**: Configure Tailwind with design system colors

**Tasks**:
1. Update `tailwind.config.js`:
   ```javascript
   export default {
     content: [
       "./index.html",
       "./src/**/*.{js,ts,jsx,tsx}",
     ],
     theme: {
       extend: {
         colors: {
           primary: {
             DEFAULT: '#0099FF',
             light: '#E6F5FF',
             dark: '#0066CC',
           },
           accent: {
             purple: '#A78BFA',  // Epic
             pink: '#FB7185',
             green: '#34D399',
             yellow: '#FCD34D',
             orange: '#FB923C',  // Rare
             gold: '#F59E0B',    // Legendary
           },
           surface: {
             DEFAULT: '#F9FAFB',
             hover: '#F3F4F6',
           },
           border: {
             DEFAULT: '#E5E7EB',
             strong: '#D1D5DB',
           },
         },
         fontFamily: {
           sans: ['Pretendard', 'Inter', 'sans-serif'],
         },
       },
     },
     plugins: [],
   }
   ```
2. Add Tailwind directives to `src/index.css`:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```
3. Test Tailwind: Add a colored div to `App.tsx` with `bg-primary`

**Acceptance**:
- ✅ Tailwind colors available in autocomplete
- ✅ Test div renders with correct color
- ✅ Build size is optimized (Tailwind purge works)

---

### Milestone 7: ESLint Configuration (Day 2, 30 minutes)

**Goal**: Set up ESLint for code quality

**Tasks**:
1. Install ESLint dependencies:
   ```bash
   pnpm add -D eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser
   ```
2. Create `.eslintrc.cjs`:
   ```javascript
   module.exports = {
     root: true,
     env: { browser: true, es2020: true },
     extends: [
       'eslint:recommended',
       'plugin:@typescript-eslint/recommended',
       'plugin:react-hooks/recommended',
     ],
     ignorePatterns: ['dist', '.eslintrc.cjs'],
     parser: '@typescript-eslint/parser',
     plugins: ['react-refresh'],
     rules: {
       'react-refresh/only-export-components': [
         'warn',
         { allowConstantExport: true },
       ],
     },
   }
   ```
3. Add lint script to `package.json`: `"lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"`
4. Run `pnpm lint` and fix any warnings

**Acceptance**:
- ✅ `pnpm lint` runs with zero warnings
- ✅ ESLint catches common issues

---

### Milestone 8: Verification & Testing (Day 2, 1 hour)

**Goal**: Ensure everything works end-to-end

**Tasks**:
1. **Build Test**:
   ```bash
   pnpm build
   # Should succeed with no errors
   ```
2. **Type Check Test**:
   ```bash
   pnpm type-check  # or tsc --noEmit
   # Should succeed with no errors
   ```
3. **Lint Test**:
   ```bash
   pnpm lint
   # Should succeed with 0 warnings
   ```
4. **Import Test**:
   - Create `src/test-imports.ts`:
     ```typescript
     import { SearchRequest, SearchResponse, TaxonomyNode } from '@/lib/api/types'
     import { apiClient } from '@/lib/api/client'
     import { env } from '@/lib/env'
     import { cn } from '@/lib/utils'

     // Test autocomplete for types
     const testSearch: SearchRequest = {
       q: "test",
       final_topk: 3,
     }

     // Test env variables
     console.log(env.VITE_API_URL)

     // Test cn utility
     const className = cn("bg-primary", "text-white")
     ```
   - Verify IDE autocomplete works for all imports
   - Verify no TypeScript errors
5. **Dev Server Test**:
   ```bash
   pnpm dev
   # Open http://localhost:5173, verify no console errors
   ```

**Acceptance**:
- ✅ All 5 tests pass
- ✅ Autocomplete works for cherry-picked types
- ✅ Dev server runs without errors
- ✅ Build produces optimized bundle

---

## Timeline Summary

| Milestone | Duration | Day |
|-----------|----------|-----|
| 1. Project Scaffolding | 2h | Day 1 |
| 2. Dependencies Installation | 1h | Day 1 |
| 3. TypeScript Config | 0.5h | Day 1 |
| 4. Directory Structure | 0.5h | Day 1 |
| 5. Cherry-Pick Code | 3h | Day 2 |
| 6. Tailwind CSS Config | 1h | Day 2 |
| 7. ESLint Config | 0.5h | Day 2 |
| 8. Verification & Testing | 1h | Day 2 |
| **Total** | **9.5 hours** | **2 days** |

---

## Rollback Plan

If critical issues occur:

1. **TypeScript Errors from Cherry-Picked Code**:
   - Revert to manual type definitions
   - Copy only working parts of `types.ts`

2. **Vite Environment Variables Not Loading**:
   - Add debug logging in `env.ts`
   - Verify `.env` file is in project root
   - Check Vite docs for `import.meta.env` usage

3. **Tailwind Purge Removes Needed Styles**:
   - Add safelist in `tailwind.config.js`
   - Verify `content` paths include all TSX files

---

## Next Steps After Completion

1. **Phase 2**: Implement Agent Card component (SPEC-FRONTEND-AGENT-CARD-001)
2. **Phase 2**: Implement XP & Level system (SPEC-FRONTEND-AGENT-GROWTH-001)
3. **Phase 2**: Integrate TAXONOMY visualization (SPEC-FRONTEND-TAXONOMY-VIZ-001)

---

## Success Metrics

- ✅ Build time < 5 seconds (Vite fast build)
- ✅ Zero TypeScript errors
- ✅ Zero ESLint warnings
- ✅ All cherry-picked files working without modifications (except env.ts)
- ✅ Full autocomplete for 409 API types from `types.ts`

---

**Last Updated**: 2025-10-30
**Status**: Ready for Implementation
