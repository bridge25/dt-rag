<!-- @ACCEPT:TAILWIND-V4-COMPLETE-001 -->
# Acceptance Criteria: Complete Tailwind CSS v4 Migration

**SPEC Reference**: @SPEC:TAILWIND-V4-COMPLETE-001
**Created**: 2025-11-08
**Status**: Draft
**Priority**: High

---

## 📋 Overview

This document defines the detailed acceptance criteria and test scenarios for validating the complete Tailwind CSS v4 migration. All scenarios follow the **Given-When-Then** format for clarity and traceability.

---

## 🎯 Quality Gates

### Gate 1: Configuration Validation
**Criteria**: Tailwind and PostCSS configurations are v4-compliant and functional

### Gate 2: Code Quality
**Criteria**: All components use JIT-compatible class patterns; zero anti-patterns remain

### Gate 3: Functional Verification
**Criteria**: All UI scenarios work correctly in development and production environments

### Gate 4: Cross-Browser Compatibility
**Criteria**: OKLCH colors render correctly in Chrome, Firefox, and Safari

### Gate 5: Production Readiness
**Criteria**: Build process is optimized; bundle size meets targets; performance metrics acceptable

### Gate 6: Documentation Completeness
**Criteria**: Migration is fully documented; future developers have clear guidance

---

## 🧪 Test Scenarios

### AC-1: Tailwind Configuration Validity

#### Scenario 1.1: Config File Exists and is Valid
**Given** the frontend project has been set up
**When** I check for Tailwind configuration file
**Then** `tailwind.config.ts` OR `tailwind.config.js` should exist
**And** the file should parse without syntax errors
**And** the file should export a valid Tailwind config object

**Verification**:
```bash
# Check file existence
ls frontend/tailwind.config.ts || ls frontend/tailwind.config.js

# Validate syntax (TypeScript)
npx tsc --noEmit frontend/tailwind.config.ts

# Test config loading
cd frontend && npm run build
```

---

#### Scenario 1.2: Content Paths Include All Components
**Given** the Tailwind configuration file exists
**When** I examine the `content` array
**Then** it should include `"./index.html"`
**And** it should include `"./src/**/*.{js,ts,jsx,tsx}"`
**And** all component directories should be covered

**Verification**:
```typescript
// tailwind.config.ts
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  // ...
}
```

---

#### Scenario 1.3: PostCSS Loads Tailwind Correctly
**Given** the PostCSS configuration file exists
**When** I examine `postcss.config.js`
**Then** it should load `tailwindcss` plugin
**And** plugin order should be correct (Tailwind before autoprefixer)

**Verification**:
```javascript
// postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

---

### AC-2: JIT Compiler Compatibility

#### Scenario 2.1: No Object Lookup Patterns
**Given** all component files have been audited
**When** I search for object lookup patterns
**Then** zero instances of `className={styles[key]}` should be found
**And** zero instances of `className={mapping[prop]}` should be found

**Verification**:
```bash
# Search for object lookup patterns
grep -r "className={.*\[.*\]}" frontend/src/
grep -r "Styles\[" frontend/src/

# Expected output: No matches (or only non-Tailwind cases)
```

---

#### Scenario 2.2: No Template Literal Classes
**Given** all component files have been audited
**When** I search for template literal class patterns
**Then** zero instances of `` className={`bg-${color}`} `` should be found
**And** zero instances of runtime concatenation should be found

**Verification**:
```bash
# Search for template literal patterns
grep -r "className={\`" frontend/src/

# Search for runtime concatenation
grep -r '"bg-" +' frontend/src/
grep -r '"text-" +' frontend/src/

# Expected output: No matches
```

---

#### Scenario 2.3: Explicit Conditionals Used
**Given** components need dynamic styles based on props
**When** I examine RarityBadge and AgentCard components
**Then** class names should use explicit conditional patterns
**And** `cn()` utility should be used for combining classes
**And** all class values should be statically analyzable

**Verification**:
```tsx
// ✅ CORRECT Pattern
<span
  className={cn(
    'base-class',
    condition && 'conditional-class',
    anotherCondition && 'another-class'
  )}
/>

// ❌ INCORRECT Pattern
const styles = { variant: 'some-class' };
<span className={styles[variant]} />
```

---

### AC-3: API Integration Testing

#### Scenario 3.1: Loading State Displays Correctly
**Given** the frontend application is connected to the backend
**And** the backend has a delayed response (simulated or real)
**When** I navigate to HomePage
**Then** I should see a loading skeleton
**And** the skeleton should have correct Tailwind styles applied
**And** no unstyled elements should be visible

**Verification**:
1. Start backend and frontend dev servers
2. Navigate to `http://localhost:5173`
3. Observe initial loading state
4. Inspect skeleton elements in DevTools
5. Verify computed styles match Tailwind classes

---

#### Scenario 3.2: Error State Displays Correctly
**Given** the frontend application is running
**When** the backend API returns an error (500, network failure, etc.)
**Then** I should see an error message UI
**And** the error UI should have correct Tailwind styles applied
**And** the error message should be readable and styled

**Verification**:
1. Simulate API error (stop backend or use mock error)
2. Observe error state on HomePage
3. Inspect error elements in DevTools
4. Verify styles are applied correctly

---

#### Scenario 3.3: Success State Renders Agent Cards
**Given** the frontend application is connected to the backend
**When** the backend API returns agent data successfully
**Then** I should see a grid of AgentCard components
**And** each card should have correct Tailwind styles applied
**And** the grid layout should match the design (5 columns on desktop)

**Verification**:
1. Start backend and frontend dev servers
2. Navigate to `http://localhost:5173`
3. Wait for data to load
4. Verify AgentCard grid is visible
5. Inspect grid container and card elements

---

#### Scenario 3.4: All Rarity Variants Display Correctly
**Given** the backend API returns agents with various rarity values
**When** I observe the rendered AgentCard components
**Then** agents with `rarity: "common"` should have gray badge and border
**And** agents with `rarity: "rare"` should have blue badge and border
**And** agents with `rarity: "epic"` should have purple badge and border
**And** agents with `rarity: "legendary"` should have gold badge and border

**Verification**:
```bash
# Check API response format
curl http://localhost:8000/api/agents | jq '.[].rarity'

# Expected: "common", "rare", "epic", "legendary" (lowercase)
```

**Visual Check**:
- Common: Gray (#6B7280) badge, gray border
- Rare: Blue (#3B82F6) badge, blue border
- Epic: Purple (#9333EA) badge, purple border
- Legendary: Gold (OKLCH) badge, gold border

---

### AC-4: Responsive Design

#### Scenario 4.1: Mobile Layout (< 640px)
**Given** the frontend application is running
**When** I resize the viewport to mobile size (e.g., 375px width)
**Then** the AgentCard grid should display in a single column
**And** cards should stack vertically
**And** all styles should remain intact

**Verification**:
1. Open DevTools
2. Enable device emulation (iPhone SE, 375px width)
3. Navigate to HomePage
4. Verify grid shows 1 column
5. Check responsive classes in computed styles

---

#### Scenario 4.2: Tablet Layout (640px - 1024px)
**Given** the frontend application is running
**When** I resize the viewport to tablet size (e.g., 768px width)
**Then** the AgentCard grid should display in 2-3 columns
**And** cards should wrap appropriately
**And** all styles should remain intact

**Verification**:
1. Open DevTools
2. Enable device emulation (iPad, 768px width)
3. Navigate to HomePage
4. Verify grid shows 2-3 columns
5. Check responsive classes in computed styles

---

#### Scenario 4.3: Desktop Layout (> 1024px)
**Given** the frontend application is running
**When** I view the application at desktop size (e.g., 1920px width)
**Then** the AgentCard grid should display in 5 columns
**And** cards should fill the width evenly
**And** all styles should remain intact

**Verification**:
1. Open browser at full desktop width
2. Navigate to HomePage
3. Verify grid shows 5 columns
4. Check grid container class: `grid-cols-5` or similar

---

### AC-5: Cross-Browser Testing

#### Scenario 5.1: Chrome Rendering
**Given** the frontend application is running
**When** I load the application in Chrome 111+ (or latest stable)
**Then** all Tailwind styles should apply correctly
**And** OKLCH colors should render accurately
**And** rarity badges should show expected colors
**And** no console errors should appear

**Verification**:
1. Open application in Chrome
2. Navigate to HomePage
3. Inspect rarity badges (all 4 variants)
4. Compare colors with baseline screenshots
5. Check console for errors

---

#### Scenario 5.2: Firefox Rendering
**Given** the frontend application is running
**When** I load the application in Firefox 113+ (or latest stable)
**Then** all Tailwind styles should apply correctly
**And** OKLCH colors should render accurately
**And** rarity badges should show expected colors
**And** no console errors should appear

**Verification**:
1. Open application in Firefox
2. Navigate to HomePage
3. Inspect rarity badges (all 4 variants)
4. Compare colors with baseline screenshots
5. Check console for errors

---

#### Scenario 5.3: Safari Rendering (Optional)
**Given** the frontend application is running
**When** I load the application in Safari 15.4+ (or latest stable)
**Then** all Tailwind styles should apply correctly
**And** OKLCH colors should render accurately
**And** rarity badges should show expected colors
**And** no console errors should appear

**Verification**:
1. Open application in Safari (if available)
2. Navigate to HomePage
3. Inspect rarity badges (all 4 variants)
4. Compare colors with baseline screenshots
5. Check console for errors

---

### AC-6: Production Build Validation

#### Scenario 6.1: Build Process Succeeds
**Given** the frontend codebase is ready for production
**When** I run `npm run build` in the frontend directory
**Then** the build should complete without errors
**And** the build should complete without warnings
**And** production artifacts should be generated in `dist/` directory

**Verification**:
```bash
cd frontend
npm run build

# Expected output: BUILD SUCCESS, no errors/warnings
# Expected files: dist/index.html, dist/assets/*.js, dist/assets/*.css
```

---

#### Scenario 6.2: CSS Bundle Size Meets Target
**Given** the production build has completed
**When** I measure the CSS bundle size
**Then** the total CSS file size should be less than 50KB (gzipped)
**And** unused Tailwind classes should be tree-shaken

**Verification**:
```bash
# Check uncompressed size
du -h frontend/dist/assets/*.css

# Check gzipped size
gzip -c frontend/dist/assets/*.css | wc -c

# Expected: < 50000 bytes (50KB)
```

---

#### Scenario 6.3: Production Preview Works Correctly
**Given** the production build has completed
**When** I run `npm run preview` and navigate to `http://localhost:4173`
**Then** the application should load successfully
**And** all styles should render correctly (same as dev mode)
**And** all API integration scenarios should work
**And** no FOUC (Flash of Unstyled Content) should occur

**Verification**:
```bash
cd frontend
npm run preview

# Open http://localhost:4173 in browser
# Test all scenarios from AC-3
```

---

#### Scenario 6.4: No FOUC on Page Load
**Given** the production preview server is running
**When** I perform a hard refresh (Ctrl+Shift+R) on the page
**Then** I should NOT see any unstyled content during load
**And** styles should be applied immediately
**And** the page should not "flicker" or change appearance after load

**Verification**:
1. Open production preview in browser
2. Open DevTools Network tab
3. Throttle network to "Fast 3G" (to simulate slower loads)
4. Hard refresh page (Ctrl+Shift+R)
5. Observe for any unstyled content flash

---

### AC-7: Performance Validation

#### Scenario 7.1: Lighthouse Performance Score
**Given** the production preview server is running
**When** I run a Lighthouse audit in Chrome DevTools
**Then** the Performance score should be greater than 90
**And** the Best Practices score should be greater than 90
**And** the Accessibility score should be greater than 90

**Verification**:
1. Open production preview in Chrome
2. Open DevTools → Lighthouse tab
3. Run audit (Desktop, Performance + Best Practices + Accessibility)
4. Verify scores meet targets

---

#### Scenario 7.2: HMR Performance (Development)
**Given** the development server is running
**When** I modify a CSS file (e.g., change a color in `@theme`)
**Then** the styles should update within 200ms
**And** the page should NOT perform a full reload (HMR only)
**Or** if HMR is unstable, the workaround should be documented

**Verification**:
1. Start dev server: `npm run dev`
2. Open browser and DevTools console
3. Modify `frontend/src/index.css` (change a color value)
4. Observe update speed and method (HMR vs full reload)

**Note**: If HMR is unstable, document manual refresh workflow as acceptable

---

### AC-8: Documentation Completeness

#### Scenario 8.1: Issue Document Updated
**Given** the migration has been completed successfully
**When** I open `.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md`
**Then** the document should have a "Resolved" section
**And** the resolution timestamp should be present
**And** all verification results should be documented

**Verification**:
```markdown
<!-- Expected in issue document -->
## ✅ Resolution

**Resolved**: 2025-11-08
**Status**: Complete

### Verification Results
- [x] Configuration validated
- [x] Components audited (zero JIT-incompatible patterns)
- [x] API integration verified
- [x] Cross-browser tested (Chrome, Firefox, Safari)
- [x] Production build optimized (CSS < 50KB gzipped)
- [x] Documentation updated
```

---

#### Scenario 8.2: Migration Checklist Documented
**Given** the migration has been completed
**When** I search for migration documentation
**Then** a migration checklist should exist (in issue document or separate file)
**And** the checklist should include all verification steps
**And** all checklist items should be marked as complete

**Verification**:
- Check `.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md` for checklist section
- Verify all items are checked: `[x]`

---

#### Scenario 8.3: README Updated with Tailwind v4
**Given** the migration has been completed
**When** I open the project README.md
**Then** it should mention Tailwind CSS v4
**And** it should specify minimum browser requirements
**And** it should link to migration issue document (optional)

**Verification**:
```markdown
<!-- Expected in README.md -->
## Frontend

The frontend uses **Tailwind CSS v4** for styling.

**Browser Requirements**:
- Chrome 111+
- Firefox 113+
- Safari 15.4+

For migration details, see [Tailwind v4 Migration Issue](./.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md).
```

---

#### Scenario 8.4: Developer Guidelines Documented
**Given** the migration has been completed
**When** future developers need to add Tailwind classes
**Then** coding guidelines should be available
**And** guidelines should include JIT-compatible examples
**And** guidelines should include anti-pattern warnings

**Verification**:
```markdown
<!-- Expected in docs/CODING_STANDARDS.md or equivalent -->
## Tailwind CSS v4 Best Practices

### ✅ JIT-Compatible Patterns
- Use explicit conditionals with `cn()` utility
- Avoid runtime object lookups or template literals
- Ensure all class names are statically analyzable

### Examples
// ✅ CORRECT
<span className={cn(
  'base-class',
  variant === 'primary' && 'bg-blue-500',
  variant === 'secondary' && 'bg-gray-500'
)} />

// ❌ AVOID
const styles = { primary: 'bg-blue-500' };
<span className={styles[variant]} />
```

---

## ✅ Definition of Done

### Overall SPEC Completion Criteria

**All of the following must be true**:

1. **Configuration**:
   - [ ] `tailwind.config.ts` exists and is valid
   - [ ] `postcss.config.js` exists and loads Tailwind correctly
   - [ ] Build process completes without errors/warnings

2. **Code Quality**:
   - [ ] Zero JIT-incompatible class patterns found in codebase
   - [ ] All components use explicit conditional patterns
   - [ ] Case-insensitive rarity comparisons implemented everywhere

3. **Functional Verification**:
   - [ ] Loading state displays correctly with Tailwind styles
   - [ ] Error state displays correctly with Tailwind styles
   - [ ] Success state renders AgentCard grid correctly
   - [ ] All 4 rarity variants (common, rare, epic, legendary) display correct colors
   - [ ] Responsive design works at 3 breakpoints (mobile, tablet, desktop)

4. **Cross-Browser Compatibility**:
   - [ ] Application renders correctly in Chrome 111+
   - [ ] Application renders correctly in Firefox 113+
   - [ ] Application renders correctly in Safari 15.4+ (optional)
   - [ ] OKLCH colors display accurately in all tested browsers

5. **Production Readiness**:
   - [ ] Production build completes successfully
   - [ ] CSS bundle size < 50KB (gzipped)
   - [ ] Production preview server works correctly
   - [ ] No FOUC observed
   - [ ] Lighthouse performance score > 90

6. **Documentation**:
   - [ ] `.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md` updated with resolution
   - [ ] Migration checklist documented and complete
   - [ ] README.md reflects Tailwind v4 usage
   - [ ] Developer guidelines include JIT-compatible patterns
   - [ ] Changelog entry added (if applicable)

---

## 🚨 Rejection Criteria

**The SPEC implementation will be REJECTED if**:

1. **Build Failures**:
   - Production build fails with errors
   - Warnings indicate missing classes or configuration issues

2. **Visual Regressions**:
   - Any rarity variant displays incorrect colors
   - Responsive layout breaks at any breakpoint
   - FOUC observed in production build

3. **JIT Incompatibility**:
   - Dynamic class patterns remain in codebase
   - JIT compiler fails to generate styles for components

4. **Cross-Browser Issues**:
   - OKLCH colors do not render in supported browsers
   - Console errors appear in any tested browser

5. **Performance Degradation**:
   - CSS bundle size exceeds 50KB (gzipped)
   - Lighthouse performance score < 90

6. **Documentation Gaps**:
   - Migration issue not updated with completion status
   - Developer guidelines missing or incomplete
   - README.md does not reflect Tailwind v4 usage

---

## 📊 Test Coverage Summary

| Test Category | Scenarios | Critical | High | Medium | Low |
|---------------|-----------|----------|------|--------|-----|
| Configuration | 3 | 2 | 1 | 0 | 0 |
| JIT Compatibility | 3 | 3 | 0 | 0 | 0 |
| API Integration | 4 | 4 | 0 | 0 | 0 |
| Responsive Design | 3 | 2 | 1 | 0 | 0 |
| Cross-Browser | 3 | 1 | 1 | 1 | 0 |
| Production Build | 4 | 3 | 1 | 0 | 0 |
| Performance | 2 | 1 | 1 | 0 | 0 |
| Documentation | 4 | 0 | 2 | 2 | 0 |
| **TOTAL** | **26** | **16** | **7** | **3** | **0** |

---

## 🔗 Traceability Matrix

| Requirement ID | Test Scenario(s) | Status |
|----------------|------------------|--------|
| REQ-1: Configuration Completeness | AC-1.1, AC-1.2, AC-1.3 | Pending |
| REQ-2: OKLCH Color System | AC-5.1, AC-5.2, AC-5.3 | Pending |
| REQ-3: JIT Compiler Compatibility | AC-2.1, AC-2.2, AC-2.3 | Pending |
| REQ-4: Development Server Verification | AC-3.1, AC-3.2, AC-3.3, AC-7.2 | Pending |
| REQ-5: API Integration Testing | AC-3.1, AC-3.2, AC-3.3, AC-3.4 | Pending |
| REQ-6: Browser Testing | AC-5.1, AC-5.2, AC-5.3 | Pending |
| REQ-7: Production Build Optimization | AC-6.1, AC-6.2, AC-6.3, AC-6.4 | Pending |
| REQ-8: Responsive Design Consistency | AC-4.1, AC-4.2, AC-4.3 | Pending |
| REQ-9: Version Locking | (Manual verification in package.json) | Pending |
| REQ-10: Code Pattern Enforcement | AC-2.1, AC-2.2, AC-2.3 | Pending |
| REQ-11: Fallback Color Support | (Optional - not tested) | N/A |

---

**Document Version**: v0.0.1
**Last Updated**: 2025-11-08
**Next Review**: After implementation and testing
**Status**: Draft - Awaiting implementation
