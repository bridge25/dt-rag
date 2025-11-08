---
id: TAILWIND-V4-COMPLETE-001
version: 0.0.2
status: in-review
created: 2025-11-08
updated: 2025-11-08
author: @project-owner
priority: high
category: refactor
labels:
  - frontend
  - tailwind
  - css
  - build-system
  - technical-debt
scope:
  packages:
    - frontend/src
  files:
    - frontend/src/index.css
    - frontend/tailwind.config.ts
    - frontend/postcss.config.js
    - frontend/src/components/agent-card/AgentCard.tsx
    - frontend/src/components/agent-card/RarityBadge.tsx
related_issue: "file://.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md"
---

<!-- @SPEC:TAILWIND-V4-COMPLETE-001 -->
# Complete Tailwind CSS v4 Migration

## HISTORY

### v0.0.2 (2025-11-08)
- **SYNC**: SPEC status updated to in-review after implementation completion
- **AUTHOR**: @doc-syncer
- **CHANGES**: Status draft → in-review, Updated README Known Issues, CHANGELOG entry added
- **NOTE**: All 6 SPEC phases completed, migration verification successful

### v0.0.1 (2025-11-08)
- **INITIAL**: SPEC created for complete Tailwind v4 migration verification
- **AUTHOR**: @spec-builder
- **SECTIONS**: Environment, Assumptions, Requirements, Specifications

---

## Executive Summary

This SPEC addresses the incomplete Tailwind CSS v4 migration discovered during frontend screenshot work. While partial fixes have been applied (CSS import syntax, OKLCH colors, JIT-compatible class patterns), **complete verification in API-connected environment has not been performed**. This SPEC defines requirements for full migration completion, verification, and documentation.

**Business Value**: HIGH - Eliminates technical debt and ensures build system stability
**Technical Complexity**: LOW-MEDIUM - Configuration verification and testing
**Risk**: MEDIUM - Tailwind v4 is still in beta; browser compatibility considerations

---

## @ENV:TAILWIND-V4-COMPLETE-001 Environment

### Development Environment

**WHEN** the frontend application is being developed:
- The development server runs on `http://localhost:5173` (Vite default port)
- Hot Module Replacement (HMR) applies CSS changes without full page reload
- JIT (Just-In-Time) compiler processes Tailwind classes dynamically
- Browser DevTools are available for CSS inspection

**WHEN** building for production:
- Vite build process generates optimized bundles
- Tailwind v4 tree-shaking eliminates unused CSS
- CSS bundle size should be smaller than Tailwind v3 equivalent
- Preview server validates production build at `http://localhost:4173`

### Technical Stack

**Tailwind CSS v4 Requirements**:
- Import syntax: `@import "tailwindcss";` (NOT `@tailwind` directives)
- Color format: OKLCH with numbered scales (e.g., `--color-accent-gold-500`)
- JIT compiler: Static analysis only (no runtime object lookups)
- Configuration: `tailwind.config.ts` or `@theme` blocks in CSS

**Browser Support**:
- Chrome 111+ (OKLCH support)
- Firefox 113+ (OKLCH support)
- Safari 15.4+ (OKLCH support)

### Current State Analysis

**Partially Completed Changes** (from TAILWIND_V4_MIGRATION_ISSUE.md):
1. ✅ CSS import syntax updated to `@import "tailwindcss";`
2. ✅ Custom colors converted to OKLCH format with numbered scales
3. ✅ AgentCard and RarityBadge refactored for JIT compatibility
4. ✅ Case-insensitive rarity comparison implemented
5. ⚠️ **NOT VERIFIED**: Real API integration scenarios
6. ⚠️ **NOT VERIFIED**: Other pages (AgentDetailPage, AgentHistoryPage, NotFoundPage)
7. ⚠️ **NOT VERIFIED**: Production build optimization
8. ⚠️ **UNKNOWN**: Tailwind config file completeness

---

## @ASSUME:TAILWIND-V4-COMPLETE-001 Assumptions

### Technical Assumptions

1. **Tailwind v4 Beta Stability**
   - ASSUMPTION: Tailwind v4 beta is stable enough for production use
   - RISK: Breaking changes may occur before stable release
   - MITIGATION: Lock dependency versions; monitor release notes

2. **Vite Compatibility**
   - ASSUMPTION: Vite + Tailwind v4 integration is reliable
   - KNOWN ISSUES: HMR may be unstable; CSS changes may require full reload
   - MITIGATION: Test HMR thoroughly; document workarounds

3. **OKLCH Browser Support**
   - ASSUMPTION: Target users have modern browsers (Chrome 111+, Firefox 113+, Safari 15.4+)
   - RISK: Older browsers will not render OKLCH colors correctly
   - MITIGATION: Consider fallback colors for legacy browser support (optional)

### Functional Assumptions

4. **API Contract Stability**
   - ASSUMPTION: Backend sends rarity values in lowercase (`"epic"`, `"legendary"`)
   - VERIFICATION: Backend schema validation required
   - MITIGATION: Case-insensitive comparison already implemented

5. **Component Coverage**
   - ASSUMPTION: AgentCard and RarityBadge are the primary Tailwind-dependent components
   - VERIFICATION: Code search for dynamic class patterns required
   - MITIGATION: Systematic component audit (see Requirements section)

### Scope Assumptions

6. **No Major Design Changes**
   - ASSUMPTION: Migration is refactoring-only; no visual design changes
   - CONSTRAINT: Existing screenshots serve as visual regression baseline
   - VERIFICATION: Compare before/after screenshots

---

## @REQ:TAILWIND-V4-COMPLETE-001 Requirements

### Ubiquitous Requirements (Foundational)

**REQ-1: Configuration Completeness**
- The system SHALL maintain a complete Tailwind v4 configuration
- Configuration SHALL include content paths for all component directories
- Configuration SHALL define custom theme variables (colors, spacing, etc.)

**REQ-2: OKLCH Color System**
- The system SHALL use OKLCH color space for all custom colors
- Custom colors SHALL follow numbered scale convention (`-500`, `-600`, etc.)
- Color definitions SHALL be centralized in `@theme` block or config file

**REQ-3: JIT Compiler Compatibility**
- All component class names SHALL be statically analyzable by JIT compiler
- The system SHALL NOT use runtime object lookups for class names
- Dynamic classes SHALL use explicit conditional patterns (`cn()` with ternaries)

### Event-driven Requirements

**REQ-4: Development Server Verification**
- WHEN the development server starts, the system SHALL compile all Tailwind classes successfully
- WHEN component files change, the system SHALL recompile affected styles within 200ms
- WHEN API data loads, the system SHALL apply correct rarity styles based on lowercase values

**REQ-5: API Integration Testing**
- WHEN HomePage fetches agent data from backend, the system SHALL render AgentCard components with correct Tailwind styles
- WHEN API returns error state, the system SHALL display error UI with correct Tailwind styles
- WHEN API is loading, the system SHALL show loading skeleton with correct Tailwind styles

**REQ-6: Browser Testing**
- WHEN the application loads in Chrome 111+, the system SHALL render OKLCH colors correctly
- WHEN the application loads in Firefox 113+, the system SHALL render OKLCH colors correctly
- WHEN the application loads in Safari 15.4+, the system SHALL render OKLCH colors correctly

### State-driven Requirements

**REQ-7: Production Build Optimization**
- WHILE building for production, the system SHALL tree-shake unused Tailwind classes
- WHILE in production mode, the system SHALL generate CSS bundle smaller than 50KB (gzipped)
- WHILE serving production build, the system SHALL NOT show FOUC (Flash of Unstyled Content)

**REQ-8: Responsive Design Consistency**
- WHILE viewport is mobile (< 640px), the system SHALL display single-column agent grid
- WHILE viewport is tablet (640px - 1024px), the system SHALL display 2-3 column agent grid
- WHILE viewport is desktop (> 1024px), the system SHALL display 5-column agent grid

### Constraints

**REQ-9: Version Locking**
- IF using Tailwind v4 beta, the system SHALL lock exact version in package.json
- IF Tailwind updates introduce breaking changes, the system SHALL block auto-updates
- IF migration fails, the system SHALL provide rollback procedure

**REQ-10: Code Pattern Enforcement**
- IF a component uses dynamic class names, the system SHALL reject patterns incompatible with JIT
- IF new components are added, the system SHALL enforce JIT-compatible class patterns
- IF custom colors are added, the system SHALL require OKLCH format with numbered scales

### Optional Features

**REQ-11: Fallback Color Support (Optional)**
- WHERE legacy browser support is required, the system MAY provide HEX color fallbacks
- WHERE OKLCH is unsupported, the system MAY detect browser capability and apply fallbacks

---

## @SPEC:TAILWIND-V4-COMPLETE-001 Specifications

### SPEC-1: Configuration Audit and Optimization

**Objective**: Ensure `tailwind.config.ts` and `postcss.config.js` are v4-compliant

**Acceptance Criteria**:
1. `tailwind.config.ts` (or `tailwind.config.js`) exists and is valid
2. Content paths include all component directories:
   ```typescript
   content: [
     "./index.html",
     "./src/**/*.{js,ts,jsx,tsx}",
   ]
   ```
3. PostCSS configuration loads Tailwind plugin correctly
4. No v3-specific configuration options remain

**Verification**:
- Read and validate config files
- Test build process with `npm run build`
- Check for warnings/errors in build output

---

### SPEC-2: Component Code Audit

**Objective**: Identify and fix all JIT-incompatible class patterns

**Acceptance Criteria**:
1. Search codebase for dynamic class patterns:
   - Object lookup: `styles[key]`
   - Template literals: `` `bg-${color}` ``
   - Runtime concatenation: `"bg-" + color`
2. Refactor all instances to explicit conditionals using `cn()` utility
3. Ensure case-insensitive rarity comparisons across all components

**Verification**:
- Run pattern searches (see Phase 2 in issue document)
- Code review of all component files
- Manual testing of all rarity variants

---

### SPEC-3: API Integration Verification

**Objective**: Test Tailwind styles in real API-connected environment

**Acceptance Criteria**:
1. Start backend server and frontend dev server
2. Navigate to HomePage and verify:
   - Loading state displays skeleton with Tailwind styles
   - Error state displays error UI with Tailwind styles
   - Success state renders AgentCard grid with correct rarity colors
3. Test all rarity values: `common`, `rare`, `epic`, `legendary`
4. Verify responsive grid behavior at 3 breakpoints

**Verification**:
- Manual QA in development server
- Browser DevTools CSS inspection
- Screenshot comparison with baseline

---

### SPEC-4: Cross-Browser Testing

**Objective**: Verify OKLCH color rendering in supported browsers

**Acceptance Criteria**:
1. Test in Chrome 111+ (or latest stable)
2. Test in Firefox 113+ (or latest stable)
3. Test in Safari 15.4+ (or latest stable)
4. Verify rarity badge colors match expected values:
   - Common: Gray (#6B7280)
   - Rare: Blue (#3B82F6)
   - Epic: Purple (#9333EA)
   - Legendary: Gold (OKLCH-based)

**Verification**:
- Cross-browser manual testing
- Screenshot comparison across browsers
- Optional: Automated visual regression tests (Playwright)

---

### SPEC-5: Production Build Validation

**Objective**: Ensure production build optimizes Tailwind correctly

**Acceptance Criteria**:
1. Run `npm run build` without errors/warnings
2. Verify CSS bundle size:
   - Total CSS < 50KB (gzipped)
   - Unused classes are tree-shaken
3. Run `npm run preview` and verify:
   - No FOUC (Flash of Unstyled Content)
   - All styles render correctly
   - Performance metrics acceptable (Lighthouse score > 90)

**Verification**:
- Build output analysis
- Bundle size inspection (`du -h dist/assets/*.css`)
- Preview server testing
- Lighthouse audit

---

### SPEC-6: Documentation Update

**Objective**: Document migration status and best practices

**Acceptance Criteria**:
1. Update `TAILWIND_V4_MIGRATION_ISSUE.md` with completion status
2. Create migration checklist in project documentation
3. Document JIT-compatible coding patterns for future developers
4. Update README.md to specify Tailwind v4 usage

**Verification**:
- Documentation review
- Checklist completeness
- Code pattern examples included

---

## Traceability

### TAG Chain
- **@SPEC:TAILWIND-V4-COMPLETE-001** → This specification document
- **@TEST:TAILWIND-V4-COMPLETE-001** → (To be created during `/alfred:2-run`)
- **@CODE:TAILWIND-V4-COMPLETE-001** → (To be implemented during `/alfred:2-run`)
- **@DOC:TAILWIND-V4-COMPLETE-001** → (To be updated during `/alfred:3-sync`)

### Related Documents
- `.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md` - Original issue report
- `frontend/src/index.css` - CSS entry point with `@import` and `@theme`
- `frontend/tailwind.config.ts` - Tailwind configuration (to be verified)
- `frontend/postcss.config.js` - PostCSS configuration (to be verified)

### Upstream Dependencies
- None (standalone refactoring task)

### Downstream Dependencies
- Future frontend components MUST follow JIT-compatible patterns
- Future color additions MUST use OKLCH format

---

## Risk Assessment

### High Priority Risks

1. **Tailwind v4 Beta Instability**
   - **Impact**: Breaking changes may require migration rework
   - **Probability**: Medium
   - **Mitigation**: Lock dependency versions; subscribe to release notes

2. **OKLCH Browser Compatibility**
   - **Impact**: Colors may not render in older browsers
   - **Probability**: Low (target audience likely uses modern browsers)
   - **Mitigation**: Optional fallback implementation; browser analytics check

### Medium Priority Risks

3. **Undiscovered JIT-Incompatible Patterns**
   - **Impact**: Some components may lose styles
   - **Probability**: Medium
   - **Mitigation**: Comprehensive code audit; systematic testing

4. **HMR Instability**
   - **Impact**: Developer experience degradation
   - **Probability**: Medium (known Vite + Tailwind v4 issue)
   - **Mitigation**: Document workaround (manual refresh); monitor upstream fixes

### Low Priority Risks

5. **Performance Regression**
   - **Impact**: Slower build times or larger bundle sizes
   - **Probability**: Low (v4 is designed to be faster/smaller)
   - **Mitigation**: Benchmark before/after; optimize if needed

---

## Success Criteria

### Functional Success
- ✅ All pages render correctly with Tailwind styles in development mode
- ✅ All pages render correctly with Tailwind styles in production build
- ✅ API integration scenarios display correct rarity colors
- ✅ Responsive design works across 3 breakpoints
- ✅ Cross-browser testing passes in Chrome, Firefox, Safari

### Technical Success
- ✅ Zero JIT-incompatible class patterns remain in codebase
- ✅ Production CSS bundle < 50KB (gzipped)
- ✅ Build process completes without errors/warnings
- ✅ HMR works reliably (or workaround documented)

### Documentation Success
- ✅ Migration issue document updated with completion status
- ✅ JIT coding patterns documented for future reference
- ✅ README.md reflects Tailwind v4 usage
- ✅ Verification checklist completed

---

## Implementation Notes

### Recommended Execution Order

1. **Phase 1: Configuration Audit** (SPEC-1)
2. **Phase 2: Component Code Audit** (SPEC-2)
3. **Phase 3: API Integration Testing** (SPEC-3)
4. **Phase 4: Cross-Browser Testing** (SPEC-4)
5. **Phase 5: Production Build** (SPEC-5)
6. **Phase 6: Documentation** (SPEC-6)

### Tools and Scripts

**Code Search Patterns** (from issue document):
```bash
# Find dynamic class patterns
grep -r "className={.*\[.*\]}" frontend/src/
grep -r "Styles\[" frontend/src/
grep -r "className={\`" frontend/src/

# Find case-sensitive rarity checks
grep -r "rarity ===" frontend/src/
```

**Build Verification**:
```bash
# Development server
npm run dev

# Production build
npm run build
npm run preview

# Bundle analysis
du -h dist/assets/*.css
```

### Testing Checklist

See `acceptance.md` for detailed test scenarios.

---

**Document Version**: v0.0.1
**Last Updated**: 2025-11-08
**Next Review**: After `/alfred:2-run` implementation phase
**Status**: Draft - Awaiting approval
