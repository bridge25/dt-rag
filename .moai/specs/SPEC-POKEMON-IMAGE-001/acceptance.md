<!-- @DOC:POKEMON-IMAGE-001-ACCEPT-001 -->
# Acceptance Criteria: Pokemon Card Character Image

**SPEC ID**: SPEC-POKEMON-IMAGE-001
**Status**: Draft
**Created**: 2025-11-08

---

## 📋 Overview

This document defines the acceptance criteria for the Pokemon Card Character Image Implementation feature. All criteria must be met before marking the SPEC as `completed` and transitioning to version `0.1.0`.

---

## ✅ Acceptance Criteria

### AC-001: Database Schema

#### Scenario 1.1: Migration Creates Required Columns

**Given** the agents table exists in the database
**When** the Alembic migration is executed with `alembic upgrade head`
**Then** the agents table contains the following new columns:
- `avatar_url` (String, max 500 chars, nullable)
- `rarity` (String, max 20 chars, default 'Common')
- `character_description` (Text, nullable)

**Verification**:
```sql
-- Query to verify columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'agents'
  AND column_name IN ('avatar_url', 'rarity', 'character_description');
```

**Expected Result**:
```
column_name            | data_type | is_nullable | column_default
-----------------------+-----------+-------------+----------------
avatar_url             | varchar   | YES         | NULL
rarity                 | varchar   | YES         | 'Common'
character_description  | text      | YES         | NULL
```

---

#### Scenario 1.2: Migration Rollback Preserves Data

**Given** the migration has been applied
**When** the migration is rolled back with `alembic downgrade -1`
**Then** the three new columns are removed
**And** all existing agent data remains intact
**And** the agents table returns to its previous state

**Verification**:
```bash
# Count agents before migration
psql -c "SELECT COUNT(*) FROM agents;" > before.txt

# Apply and rollback migration
alembic upgrade head
alembic downgrade -1

# Count agents after rollback
psql -c "SELECT COUNT(*) FROM agents;" > after.txt

# Compare counts
diff before.txt after.txt  # Should show no difference
```

---

### AC-002: API Schema & Endpoints

#### Scenario 2.1: Agent Creation Returns Avatar Fields

**Given** the API server is running
**When** a POST request is sent to `/agents/from-taxonomy` with valid payload:
```json
{
  "name": "Test Agent Alpha",
  "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```
**Then** the response status code is `201 Created`
**And** the response body includes:
- `avatar_url` (string, starts with "/avatars/")
- `rarity` (string, one of "Common", "Rare", "Epic", "Legendary")
- `character_description` (string or null)

**Verification**:
```python
import httpx

response = httpx.post("http://localhost:8000/agents/from-taxonomy", json={
    "name": "Test Agent Alpha",
    "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
})

assert response.status_code == 201
data = response.json()
assert "avatar_url" in data
assert data["avatar_url"].startswith("/avatars/")
assert data["rarity"] in ["Common", "Rare", "Epic", "Legendary"]
```

---

#### Scenario 2.2: Agent Search Returns Avatar Fields

**Given** at least one agent exists in the database
**When** a GET request is sent to `/agents/search`
**Then** the response status code is `200 OK`
**And** each agent in the response includes:
- `avatar_url` (present and non-empty)
- `rarity` (valid enum value)

**Verification**:
```python
response = httpx.get("http://localhost:8000/agents/search")

assert response.status_code == 200
agents = response.json()["agents"]
assert len(agents) > 0

for agent in agents:
    assert "avatar_url" in agent
    assert "rarity" in agent
    assert agent["rarity"] in ["Common", "Rare", "Epic", "Legendary"]
```

---

#### Scenario 2.3: Rarity Calculation Based on Taxonomy Scope

**Given** the agent creation endpoint
**When** creating agents with different taxonomy node counts:
- 1 node → Rarity should be "Common"
- 3 nodes → Rarity should be "Rare"
- 7 nodes → Rarity should be "Epic"
- 12 nodes → Rarity should be "Legendary"
**Then** the assigned rarity matches the expected tier

**Verification**:
```python
test_cases = [
    (1, "Common"),
    (3, "Rare"),
    (7, "Epic"),
    (12, "Legendary"),
]

for node_count, expected_rarity in test_cases:
    node_ids = [str(uuid4()) for _ in range(node_count)]
    response = httpx.post("/agents/from-taxonomy", json={
        "name": f"Agent {node_count} Nodes",
        "taxonomy_node_ids": node_ids
    })
    assert response.json()["rarity"] == expected_rarity
```

---

### AC-003: Frontend Type Definitions

#### Scenario 3.1: Zod Schema Validates Avatar Fields

**Given** the `AgentCardDataSchema` is imported
**When** parsing API response data with avatar fields
**Then** the schema validation passes without errors

**Verification**:
```typescript
import { AgentCardDataSchema } from '@/lib/api/types'

const mockApiResponse = {
  agent_id: '123e4567-e89b-12d3-a456-426614174000',
  name: 'Test Agent',
  level: 5,
  current_xp: 5000,
  next_level_xp: 10000,
  rarity: 'Epic',
  avatar_url: '/avatars/epic/default-1.png',
  character_description: 'Powerful AI assistant',
  total_documents: 100,
  total_queries: 500,
  quality_score: 92,
  status: 'active',
  created_at: '2025-11-08T12:00:00Z',
}

const result = AgentCardDataSchema.safeParse(mockApiResponse)
expect(result.success).toBe(true)
```

---

#### Scenario 3.2: Default Avatar URL Helper Works Correctly

**Given** the `getDefaultAvatarUrl()` helper function
**When** calling with the same agent_id and rarity multiple times
**Then** the returned URL is deterministic (identical on each call)
**And** the URL format matches `/avatars/{rarity}/default-{1-3}.png`

**Verification**:
```typescript
import { getDefaultAvatarUrl } from '@/lib/api/types'

const agentId = '123e4567-e89b-12d3-a456-426614174000'
const rarity = 'Rare'

const url1 = getDefaultAvatarUrl(rarity, agentId)
const url2 = getDefaultAvatarUrl(rarity, agentId)

expect(url1).toBe(url2)  // Deterministic
expect(url1).toMatch(/^\/avatars\/rare\/default-[1-3]\.png$/)
```

---

### AC-004: UI Component Rendering

#### Scenario 4.1: AgentAvatar Renders Image Successfully

**Given** the `AgentAvatar` component is mounted
**When** provided with a valid avatar URL
**Then** the component renders an `<img>` tag
**And** the image source matches the provided URL
**And** the alt text includes the agent name

**Verification**:
```typescript
import { render, screen } from '@testing-library/react'
import { AgentAvatar } from '@/components/agent-card/AgentAvatar'

render(
  <AgentAvatar
    avatarUrl="/avatars/epic/default-1.png"
    agentName="Test Agent Alpha"
    rarity="Epic"
  />
)

const img = screen.getByAlt(/Test Agent Alpha.*avatar/)
expect(img).toBeInTheDocument()
expect(img).toHaveAttribute('src', '/avatars/epic/default-1.png')
expect(img).toHaveAttribute('loading', 'lazy')
```

---

#### Scenario 4.2: AgentAvatar Shows Fallback on Image Error

**Given** the `AgentAvatar` component is mounted
**When** the image fails to load (onError triggered)
**Then** the component displays a fallback emoji icon
**And** the emoji matches the rarity tier:
- Common → 🤖
- Rare → 💎
- Epic → ⚡
- Legendary → 👑

**Verification**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { AgentAvatar } from '@/components/agent-card/AgentAvatar'

const rarityToEmoji = {
  Common: '🤖',
  Rare: '💎',
  Epic: '⚡',
  Legendary: '👑',
}

Object.entries(rarityToEmoji).forEach(([rarity, emoji]) => {
  const { rerender } = render(
    <AgentAvatar
      avatarUrl="/invalid-url.png"
      agentName="Test Agent"
      rarity={rarity as Rarity}
    />
  )

  const img = screen.getByAlt(/Test Agent.*avatar/)
  fireEvent.error(img)

  expect(screen.getByText(emoji)).toBeInTheDocument()
  expect(screen.getByLabelText(`${rarity} tier icon`)).toBeInTheDocument()
})
```

---

#### Scenario 4.3: AgentCard Integrates Avatar Correctly

**Given** the `AgentCard` component is mounted with agent data
**When** the component renders
**Then** the avatar appears between the header and XP progress bar
**And** the avatar section has a height of 192px (h-48)
**And** the avatar uses the correct URL (custom or default)

**Verification**:
```typescript
import { render, screen } from '@testing-library/react'
import { AgentCard } from '@/components/agent-card/AgentCard'
import type { AgentCardData } from '@/lib/api/types'

const mockAgent: AgentCardData = {
  agent_id: '123e4567-e89b-12d3-a456-426614174000',
  name: 'RAG Assistant Alpha',
  level: 8,
  current_xp: 8500,
  next_level_xp: 10000,
  rarity: 'Epic',
  avatar_url: '/avatars/epic/default-1.png',
  total_documents: 1250,
  total_queries: 3420,
  quality_score: 92,
  status: 'active',
  created_at: '2025-11-08T12:00:00Z',
}

render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

// Verify avatar is present
const avatar = screen.getByAlt(/RAG Assistant Alpha.*avatar/)
expect(avatar).toBeInTheDocument()

// Verify layout order (header → avatar → XP bar)
const card = screen.getByRole('article')
const elements = Array.from(card.children)
const headerIndex = elements.findIndex(el => el.textContent?.includes('Level 8'))
const avatarIndex = elements.findIndex(el => el.querySelector('img[alt*="avatar"]'))
const xpBarIndex = elements.findIndex(el => el.textContent?.includes('8500'))

expect(avatarIndex).toBeGreaterThan(headerIndex)
expect(xpBarIndex).toBeGreaterThan(avatarIndex)
```

---

### AC-005: Performance & Optimization

#### Scenario 5.1: Avatar Images Load Within Performance Budget

**Given** an agent card with avatar image
**When** the page loads
**Then** the avatar image loads in less than 500ms
**And** lazy loading defers off-screen images

**Verification**:
```typescript
// Playwright performance test
test('avatar images meet performance budget', async ({ page }) => {
  await page.goto('/')

  const performanceMetrics = await page.evaluate(() => {
    const entries = performance.getEntriesByType('resource')
    const avatarImages = entries.filter(e => e.name.includes('/avatars/'))
    return avatarImages.map(img => ({
      url: img.name,
      duration: img.duration,
    }))
  })

  performanceMetrics.forEach(metric => {
    expect(metric.duration).toBeLessThan(500)  // <500ms load time
  })
})
```

---

#### Scenario 5.2: No Layout Shift During Image Load

**Given** an agent card is rendered
**When** the avatar image loads
**Then** the Cumulative Layout Shift (CLS) score remains below 0.1
**And** the avatar container reserves space before image loads

**Verification**:
```typescript
test('avatar loading does not cause layout shift', async ({ page }) => {
  await page.goto('/')

  // Measure CLS
  const cls = await page.evaluate(() => {
    return new Promise(resolve => {
      let clsScore = 0
      const observer = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'layout-shift' && !entry.hadRecentInput) {
            clsScore += entry.value
          }
        }
      })
      observer.observe({ type: 'layout-shift', buffered: true })

      setTimeout(() => {
        observer.disconnect()
        resolve(clsScore)
      }, 3000)
    })
  })

  expect(cls).toBeLessThan(0.1)
})
```

---

### AC-006: Accessibility

#### Scenario 6.1: Screen Readers Announce Avatar Properly

**Given** a screen reader is active (e.g., NVDA, JAWS, VoiceOver)
**When** navigating to an agent card
**Then** the avatar image is announced with descriptive text
**And** the fallback icon (if visible) has an aria-label

**Verification**:
```typescript
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

test('AgentAvatar has no accessibility violations', async () => {
  const { container } = render(
    <AgentAvatar
      avatarUrl="/avatars/epic/default-1.png"
      agentName="Test Agent"
      rarity="Epic"
    />
  )

  const results = await axe(container)
  expect(results).toHaveNoViolations()
})

test('Fallback icon has aria-label', () => {
  const { container } = render(
    <AgentAvatar
      avatarUrl="/invalid.png"
      agentName="Test Agent"
      rarity="Legendary"
    />
  )

  const img = container.querySelector('img')!
  fireEvent.error(img)

  const fallback = screen.getByLabelText(/Legendary tier icon/)
  expect(fallback).toBeInTheDocument()
})
```

---

#### Scenario 6.2: Keyboard Navigation Functions Correctly

**Given** the agent card is rendered
**When** navigating with keyboard (Tab key)
**Then** the avatar does not trap focus
**And** action buttons remain accessible

**Verification**:
```typescript
test('keyboard navigation works with avatar present', async () => {
  render(<AgentCard agent={mockAgent} onView={onView} onDelete={onDelete} />)

  // Tab through interactive elements
  await userEvent.tab()  // Should focus first button
  expect(screen.getByRole('button', { name: /view/i })).toHaveFocus()

  await userEvent.tab()  // Should focus second button
  expect(screen.getByRole('button', { name: /delete/i })).toHaveFocus()
})
```

---

### AC-007: Cross-Browser Compatibility

#### Scenario 7.1: Avatar Renders Correctly in All Browsers

**Given** the application is deployed
**When** accessing the page in the following browsers:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
**Then** the avatar images display correctly
**And** fallback icons work in all browsers

**Verification**:
```typescript
// Playwright cross-browser test
const browsers = ['chromium', 'firefox', 'webkit']

browsers.forEach(browserType => {
  test(`avatar works in ${browserType}`, async ({ browser }) => {
    const context = await browser.newContext()
    const page = await context.newPage()

    await page.goto('/')

    const avatar = page.locator('[alt*="character avatar"]').first()
    await expect(avatar).toBeVisible()
    await expect(avatar).toHaveAttribute('src', /\/avatars\//)
  })
})
```

---

### AC-008: Integration Testing

#### Scenario 8.1: End-to-End Agent Creation Flow

**Given** the application is running (frontend + backend)
**When** creating a new agent via the UI
**Then** the agent card displays with an avatar image
**And** the avatar matches the assigned rarity tier

**Verification**:
```typescript
test('end-to-end: create agent and verify avatar', async ({ page }) => {
  await page.goto('/')

  // Create new agent (assuming UI flow exists)
  await page.click('text=Create Agent')
  await page.fill('[name="agentName"]', 'E2E Test Agent')
  // ... select taxonomy nodes ...
  await page.click('text=Submit')

  // Verify avatar appears in card
  await page.waitForSelector('[alt*="E2E Test Agent.*avatar"]')

  const avatar = page.locator('[alt*="E2E Test Agent.*avatar"]')
  await expect(avatar).toBeVisible()

  const src = await avatar.getAttribute('src')
  expect(src).toMatch(/\/avatars\/(common|rare|epic|legendary)\/default-[1-3]\.png/)
})
```

---

## 📊 Definition of Done

### Code Quality

- [ ] All unit tests pass (>90% backend coverage, >85% frontend coverage)
- [ ] All integration tests pass
- [ ] All end-to-end tests pass
- [ ] No TypeScript type errors (`tsc --noEmit` passes)
- [ ] No ESLint errors or warnings
- [ ] Code reviewed and approved

### Functionality

- [ ] Database migration runs successfully (forward and backward)
- [ ] API returns avatar fields in all agent endpoints
- [ ] Frontend displays avatar images in agent cards
- [ ] Fallback emoji system works for all rarity tiers
- [ ] Default avatar selection is deterministic

### Performance

- [ ] Avatar images load in <500ms
- [ ] Lazy loading implemented and functional
- [ ] No layout shift during image load (CLS <0.1)
- [ ] All images optimized (<100KB each)

### Accessibility

- [ ] Alt text present on all images
- [ ] Fallback icons have aria-labels
- [ ] Keyboard navigation functional
- [ ] Screen reader testing passed
- [ ] Axe accessibility audit passed (0 violations)

### Documentation

- [ ] API schema updated (OpenAPI/Swagger)
- [ ] Component documentation added (JSDoc/Storybook)
- [ ] README updated with avatar feature description
- [ ] Migration guide documented
- [ ] TAG chain complete (SPEC → TEST → CODE → DOC)

### Deployment

- [ ] Migration script tested on staging database
- [ ] Avatar assets committed to repository
- [ ] Feature flag enabled (if applicable)
- [ ] Rollback plan documented
- [ ] Production deployment successful

---

## 🎯 Success Metrics

### User-Facing Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Avatar display rate | >99% | Analytics: Image load success rate |
| Fallback usage rate | <5% | Analytics: Error handler triggers |
| User engagement (card interaction) | +10% | Analytics: Click-through rate |
| Page load time increase | <200ms | Performance monitoring |

### Technical Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Test coverage (backend) | >90% | pytest-cov report |
| Test coverage (frontend) | >85% | Jest coverage report |
| API response time | <100ms | Load testing with k6 |
| Image optimization | 100% <100KB | File size audit |

---

## 🚦 Quality Gates

### Gate 1: Pre-Deployment Checklist

**Criteria**:
- [ ] All acceptance criteria scenarios pass
- [ ] Definition of Done 100% complete
- [ ] Performance benchmarks met
- [ ] Accessibility audit passed
- [ ] Cross-browser testing complete

**Approval Required**: Yes (Team Lead or Senior Developer)

---

### Gate 2: Post-Deployment Validation

**Criteria** (within 24 hours of deployment):
- [ ] No production errors related to avatar feature
- [ ] Avatar display rate >99%
- [ ] Database migration successful with no rollbacks
- [ ] User feedback positive (no reported visual bugs)

**Approval Required**: Yes (Product Owner)

---

## 📝 Test Execution Summary

### Scenario Pass/Fail Tracking

| Scenario ID | Description | Status | Notes |
|-------------|-------------|--------|-------|
| AC-001.1 | Migration creates columns | ⚠️ Pending | - |
| AC-001.2 | Migration rollback preserves data | ⚠️ Pending | - |
| AC-002.1 | Agent creation returns avatar fields | ⚠️ Pending | - |
| AC-002.2 | Agent search returns avatar fields | ⚠️ Pending | - |
| AC-002.3 | Rarity calculation | ⚠️ Pending | - |
| AC-003.1 | Zod schema validates avatar fields | ⚠️ Pending | - |
| AC-003.2 | Default avatar URL helper | ⚠️ Pending | - |
| AC-004.1 | AgentAvatar renders image | ⚠️ Pending | - |
| AC-004.2 | AgentAvatar shows fallback | ⚠️ Pending | - |
| AC-004.3 | AgentCard integrates avatar | ⚠️ Pending | - |
| AC-005.1 | Performance budget met | ⚠️ Pending | - |
| AC-005.2 | No layout shift | ⚠️ Pending | - |
| AC-006.1 | Screen reader announces avatar | ⚠️ Pending | - |
| AC-006.2 | Keyboard navigation functional | ⚠️ Pending | - |
| AC-007.1 | Cross-browser compatibility | ⚠️ Pending | - |
| AC-008.1 | End-to-end agent creation | ⚠️ Pending | - |

**Overall Status**: ⚠️ Implementation Not Started

---

## 🔄 Continuous Validation

### Automated Test Runs

**Frequency**: On every commit (CI/CD pipeline)

**Test Suite**:
```bash
# Backend tests
pytest tests/unit/test_agent_avatar_logic.py -v --cov
pytest tests/integration/test_agent_avatar_api.py -v

# Frontend tests
npm run test -- --coverage --watchAll=false

# E2E tests
npx playwright test tests/e2e/test_agent_card_avatar.spec.ts
```

**Pass Threshold**: 100% (all tests must pass for merge approval)

---

## 📞 Sign-Off

### Stakeholder Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| Product Owner | - | ⚠️ Pending | - |
| Technical Lead | - | ⚠️ Pending | - |
| QA Engineer | - | ⚠️ Pending | - |
| Designer | - | ⚠️ Pending | - |

**Final Approval Date**: TBD

---

**Acceptance Criteria Status**: Draft
**Next Action**: `/alfred:2-run SPEC-POKEMON-IMAGE-001` to begin TDD implementation
**Expected Completion**: After all scenarios pass and DoD achieved
