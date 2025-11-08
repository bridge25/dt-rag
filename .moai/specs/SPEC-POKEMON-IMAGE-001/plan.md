<!-- @DOC:POKEMON-IMAGE-001-PLAN-001 -->
# Implementation Plan: Pokemon Card Character Image

**SPEC ID**: SPEC-POKEMON-IMAGE-001
**Status**: Draft
**Created**: 2025-11-08
**Priority**: High

---

## 📊 Executive Summary

### Implementation Overview

**Scope**: Full-stack feature implementation adding character image support to Pokemon-styled agent cards.

**Components**:
- Database migration (3 new columns)
- API schema updates (FastAPI/Pydantic)
- Frontend type definitions (TypeScript/Zod)
- UI components (React/Tailwind)
- Default avatar assets (12 PNG images)

**Complexity**: MEDIUM
- Database schema change requires migration
- Full-stack coordination (Backend + Frontend)
- Asset preparation and integration
- Comprehensive test coverage required

**Dependencies**: None (standalone feature)

---

## 🎯 Implementation Strategy

### TDD Approach (RED → GREEN → REFACTOR)

#### Phase 1: Backend Foundation (Database + API)

**RED Phase**:
1. Write failing test for database migration (column existence)
2. Write failing test for `AgentResponse` schema validation
3. Write failing test for agent creation with avatar_url
4. Write failing test for default avatar assignment logic

**GREEN Phase**:
1. Create Alembic migration adding avatar fields
2. Update `AgentResponse` schema with image fields
3. Implement `calculate_initial_rarity()` function
4. Implement `get_default_avatar_url()` function
5. Update `create_agent()` DAO method

**REFACTOR Phase**:
1. Extract avatar logic into separate service module
2. Optimize rarity calculation algorithm
3. Add comprehensive docstrings
4. Validate migration rollback safety

#### Phase 2: Frontend Foundation (Types + Utilities)

**RED Phase**:
1. Write failing test for `AgentCardDataSchema` validation
2. Write failing test for `getDefaultAvatarUrl()` helper
3. Write failing test for rarity-based avatar selection

**GREEN Phase**:
1. Update `AgentCardDataSchema` with image fields
2. Implement `getDefaultAvatarUrl()` utility
3. Update type definitions

**REFACTOR Phase**:
1. Optimize type safety (strict null checks)
2. Add JSDoc comments
3. Extract constants to shared config

#### Phase 3: UI Components (AgentAvatar + AgentCard)

**RED Phase**:
1. Write failing test for `AgentAvatar` component rendering
2. Write failing test for image error fallback
3. Write failing test for lazy loading
4. Write failing test for `AgentCard` integration

**GREEN Phase**:
1. Create `AgentAvatar` component
2. Implement image error handling
3. Add fallback emoji system
4. Update `AgentCard` to include avatar section

**REFACTOR Phase**:
1. Extract fallback icon mapping to constants
2. Optimize component re-rendering (memoization)
3. Improve accessibility attributes
4. Add loading state animations

#### Phase 4: Asset Integration

**Tasks**:
1. Create avatar directory structure (`frontend/public/avatars/`)
2. Design or acquire 12 default avatar images
3. Optimize image sizes (<100KB each)
4. Test image loading across browsers

#### Phase 5: Integration Testing & Quality Gates

**Tests**:
1. End-to-end: Create agent → Verify avatar in UI
2. Performance: Measure image load times
3. Accessibility: Screen reader validation
4. Cross-browser: Chrome, Firefox, Safari testing

---

## 🗺️ Milestone Roadmap

### Milestone 1: Database & API (Primary Goal)

**Objective**: Backend fully supports avatar fields

**Tasks**:
- [ ] Database migration created and tested
- [ ] `AgentResponse` schema updated
- [ ] Rarity calculation logic implemented
- [ ] Default avatar URL generation implemented
- [ ] Agent DAO updated
- [ ] API tests passing (>90% coverage)

**Validation Criteria**:
- Migration runs forward and backward without errors
- API returns avatar_url and rarity in responses
- Default avatars assigned deterministically

### Milestone 2: Frontend Types & Utilities (Secondary Goal)

**Objective**: TypeScript types match backend schema

**Tasks**:
- [ ] `AgentCardDataSchema` updated
- [ ] `getDefaultAvatarUrl()` helper implemented
- [ ] Type definitions validated
- [ ] Unit tests passing

**Validation Criteria**:
- Zod schema validates API responses
- Type safety enforced (no `any` types)
- Helper function produces correct URLs

### Milestone 3: UI Components (Primary Goal)

**Objective**: Avatar images render correctly in agent cards

**Tasks**:
- [ ] `AgentAvatar` component created
- [ ] Image error handling implemented
- [ ] Fallback emoji system working
- [ ] `AgentCard` updated with avatar section
- [ ] Component tests passing (>85% coverage)

**Validation Criteria**:
- Images display between header and XP bar
- Fallback icons appear on image error
- Lazy loading reduces initial page load

### Milestone 4: Asset Preparation (Secondary Goal)

**Objective**: Default avatar images ready for production

**Tasks**:
- [ ] Avatar directory structure created
- [ ] 12 default images designed/acquired
- [ ] Images optimized and validated
- [ ] Images committed to repository

**Validation Criteria**:
- All images <100KB each
- PNG format with transparency
- 400x400px dimensions

### Milestone 5: Integration & QA (Final Goal)

**Objective**: Feature complete and production-ready

**Tasks**:
- [ ] End-to-end tests passing
- [ ] Performance benchmarks met (<500ms load)
- [ ] Accessibility audit passed
- [ ] Cross-browser testing complete
- [ ] Documentation updated

**Validation Criteria**:
- All tests green
- No layout shifts during image load
- Screen readers announce avatars correctly
- Works on Chrome, Firefox, Safari

---

## 🏗️ Technical Architecture

### System Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AgentCard Component                                        │
│    ├─ Header (Name + Rarity Badge)                          │
│    ├─ AgentAvatar Component (NEW)                           │
│    │   ├─ Image Load Success → Display PNG                  │
│    │   └─ Image Load Error → Display Fallback Emoji         │
│    ├─ XP Progress Bar                                       │
│    └─ Stats Grid                                            │
│                                                             │
│  Type Definitions (types.ts)                                │
│    ├─ AgentCardDataSchema (extended with avatar_url)        │
│    └─ getDefaultAvatarUrl() helper                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ HTTP GET /agents/search
                           │ Response: { avatar_url, rarity, ... }
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Agent Router (/agents/search, /agents/from-taxonomy)       │
│    └─ Returns AgentResponse with avatar fields              │
│                                                             │
│  Agent DAO (create_agent, get_agent)                        │
│    ├─ calculate_initial_rarity()                            │
│    └─ get_default_avatar_url()                              │
│                                                             │
│  Pydantic Schema (agent_schemas.py)                         │
│    └─ AgentResponse: avatar_url, rarity, character_desc     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ SQLAlchemy ORM
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  agents table                                               │
│    ├─ agent_id (UUID, PK)                                   │
│    ├─ name (String)                                         │
│    ├─ avatar_url (String, nullable) ← NEW                   │
│    ├─ rarity (String, default='Common') ← NEW               │
│    ├─ character_description (Text, nullable) ← NEW          │
│    └─ ... (existing fields)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Sequence

**Agent Creation Flow**:
```
User Request → API Endpoint → DAO.create_agent()
  ├─ calculate_initial_rarity(taxonomy_node_ids) → "Epic"
  ├─ get_default_avatar_url("Epic", agent_id) → "/avatars/epic/default-2.png"
  └─ Insert into DB with avatar_url and rarity

API Response → Frontend
  └─ AgentCardDataSchema validates response
      └─ AgentCard renders with AgentAvatar component
          ├─ Load image from avatar_url
          └─ On error → Show fallback emoji ⚡
```

**Avatar Display Flow**:
```
AgentCard receives agent data
  ├─ Check agent.avatar_url
  │   ├─ If present → Use provided URL
  │   └─ If null → getDefaultAvatarUrl(rarity, agent_id)
  └─ Pass to AgentAvatar component
      ├─ Attempt image load (lazy)
      ├─ On success → Display image
      └─ On error → Display fallback emoji based on rarity
```

---

## 🧪 Testing Strategy

### Unit Tests

#### Backend Tests

**File**: `tests/unit/test_agent_avatar_logic.py`

**Test Cases**:
```python
def test_calculate_initial_rarity_legendary():
    """Test rarity calculation for 10+ taxonomy nodes"""
    node_ids = [uuid4() for _ in range(12)]
    assert calculate_initial_rarity(node_ids) == "Legendary"

def test_calculate_initial_rarity_epic():
    """Test rarity calculation for 5-9 taxonomy nodes"""
    node_ids = [uuid4() for _ in range(7)]
    assert calculate_initial_rarity(node_ids) == "Epic"

def test_get_default_avatar_url_deterministic():
    """Test that same agent_id always returns same avatar"""
    agent_id = uuid4()
    url1 = get_default_avatar_url("Rare", agent_id)
    url2 = get_default_avatar_url("Rare", agent_id)
    assert url1 == url2

def test_get_default_avatar_url_format():
    """Test URL format matches expected pattern"""
    url = get_default_avatar_url("Epic", uuid4())
    assert url.startswith("/avatars/epic/default-")
    assert url.endswith(".png")
```

#### Frontend Tests

**File**: `frontend/src/lib/api/__tests__/types.test.ts`

**Test Cases**:
```typescript
describe('getDefaultAvatarUrl', () => {
  it('should generate deterministic URL based on agent_id', () => {
    const agentId = '123e4567-e89b-12d3-a456-426614174000'
    const url1 = getDefaultAvatarUrl('Rare', agentId)
    const url2 = getDefaultAvatarUrl('Rare', agentId)
    expect(url1).toBe(url2)
  })

  it('should generate different URLs for different rarities', () => {
    const agentId = '123e4567-e89b-12d3-a456-426614174000'
    const commonUrl = getDefaultAvatarUrl('Common', agentId)
    const epicUrl = getDefaultAvatarUrl('Epic', agentId)
    expect(commonUrl).not.toBe(epicUrl)
  })
})
```

**File**: `frontend/src/components/agent-card/__tests__/AgentAvatar.test.tsx`

**Test Cases**:
```typescript
describe('AgentAvatar', () => {
  it('should render image with correct src', () => {
    render(
      <AgentAvatar
        avatarUrl="/avatars/epic/default-1.png"
        agentName="Test Agent"
        rarity="Epic"
      />
    )
    const img = screen.getByAlt('Test Agent character avatar')
    expect(img).toHaveAttribute('src', '/avatars/epic/default-1.png')
  })

  it('should show fallback icon on image error', () => {
    render(
      <AgentAvatar
        avatarUrl="/invalid.png"
        agentName="Test Agent"
        rarity="Legendary"
      />
    )
    const img = screen.getByAlt('Test Agent character avatar')
    fireEvent.error(img)
    expect(screen.getByText('👑')).toBeInTheDocument()
  })

  it('should have aria-label for accessibility', () => {
    render(
      <AgentAvatar
        avatarUrl="/avatars/rare/default-1.png"
        agentName="Test Agent"
        rarity="Rare"
      />
    )
    expect(screen.getByAlt('Test Agent character avatar')).toBeInTheDocument()
  })
})
```

### Integration Tests

**File**: `tests/integration/test_agent_avatar_api.py`

**Test Cases**:
```python
async def test_agent_creation_includes_avatar_fields():
    """Test that agent creation returns avatar_url and rarity"""
    response = await client.post("/agents/from-taxonomy", json={
        "name": "Integration Test Agent",
        "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    })

    assert response.status_code == 201
    data = response.json()
    assert "avatar_url" in data
    assert "rarity" in data
    assert data["rarity"] in ["Common", "Rare", "Epic", "Legendary"]
    assert data["avatar_url"].startswith("/avatars/")

async def test_agent_list_returns_avatar_data():
    """Test that agent search endpoint includes avatar fields"""
    response = await client.get("/agents/search")

    assert response.status_code == 200
    agents = response.json()["agents"]
    for agent in agents:
        assert "avatar_url" in agent
        assert "rarity" in agent
```

### End-to-End Tests

**File**: `tests/e2e/test_agent_card_avatar.spec.ts` (Playwright)

**Test Cases**:
```typescript
test('should display avatar image in agent card', async ({ page }) => {
  await page.goto('/')

  // Wait for agent cards to load
  await page.waitForSelector('[data-testid="agent-card"]')

  // Verify avatar image is present
  const avatar = page.locator('[alt*="character avatar"]').first()
  await expect(avatar).toBeVisible()
  await expect(avatar).toHaveAttribute('src', /\/avatars\//)
})

test('should show fallback icon when image fails', async ({ page }) => {
  // Mock API to return invalid avatar URL
  await page.route('**/agents/search', async route => {
    const json = await route.fetch()
    const data = await json.json()
    data.agents[0].avatar_url = '/invalid.png'
    await route.fulfill({ json: data })
  })

  await page.goto('/')

  // Verify fallback icon appears
  const fallbackIcon = page.locator('[role="img"][aria-label*="tier icon"]').first()
  await expect(fallbackIcon).toBeVisible()
})
```

---

## 🔧 Development Workflow

### Step-by-Step Implementation

#### Step 1: Database Migration

```bash
# Create migration
cd /home/a/projects/dt-rag-standalone
alembic revision --autogenerate -m "Add avatar fields to agents table"

# Review generated migration file
# Edit if necessary to ensure correct column types and defaults

# Apply migration
alembic upgrade head

# Test rollback
alembic downgrade -1
alembic upgrade head
```

#### Step 2: Backend Implementation

**Files to Modify**:
1. `apps/api/schemas/agent_schemas.py` - Add avatar fields to `AgentResponse`
2. `apps/api/agent_dao.py` - Add avatar assignment logic
3. `apps/api/database.py` - Verify ORM model updated by migration

**Commit Sequence**:
```bash
# RED commit
git add tests/unit/test_agent_avatar_logic.py
git commit -m "test(avatar): add failing tests for avatar logic

@TEST:POKEMON-IMAGE-001-API-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# GREEN commit
git add apps/api/schemas/agent_schemas.py apps/api/agent_dao.py
git commit -m "feat(avatar): implement avatar assignment logic

@CODE:POKEMON-IMAGE-001-SCHEMA-001
@CODE:POKEMON-IMAGE-001-DAO-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# REFACTOR commit
git add apps/api/services/avatar_service.py
git commit -m "refactor(avatar): extract avatar logic to service

@CODE:POKEMON-IMAGE-001-SERVICE-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Step 3: Frontend Types

**Files to Modify**:
1. `frontend/src/lib/api/types.ts` - Extend `AgentCardDataSchema`

**Commit**:
```bash
git add frontend/src/lib/api/types.ts frontend/src/lib/api/__tests__/types.test.ts
git commit -m "feat(types): add avatar fields to AgentCardDataSchema

@CODE:POKEMON-IMAGE-001-TYPES-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Step 4: UI Components

**Files to Modify**:
1. `frontend/src/components/agent-card/AgentAvatar.tsx` (new)
2. `frontend/src/components/agent-card/AgentCard.tsx` (update)

**Commit Sequence**:
```bash
# RED commit
git add frontend/src/components/agent-card/__tests__/AgentAvatar.test.tsx
git commit -m "test(avatar): add failing tests for AgentAvatar component

@TEST:POKEMON-IMAGE-001-FE-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# GREEN commit
git add frontend/src/components/agent-card/AgentAvatar.tsx
git commit -m "feat(avatar): implement AgentAvatar component

@CODE:POKEMON-IMAGE-001-AVATAR-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# Integration commit
git add frontend/src/components/agent-card/AgentCard.tsx
git commit -m "feat(card): integrate avatar into AgentCard

@CODE:POKEMON-IMAGE-001-CARD-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### Step 5: Asset Integration

**Tasks**:
```bash
# Create directory structure
mkdir -p frontend/public/avatars/{common,rare,epic,legendary}

# Add placeholder images (replace with actual designs)
# NOTE: Actual image acquisition outside scope of this plan

# Commit assets
git add frontend/public/avatars/
git commit -m "assets(avatar): add default avatar images

@CODE:POKEMON-IMAGE-001-ASSETS-001

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 📏 Quality Metrics

### Code Coverage Targets

| Component | Target Coverage | Current | Status |
|-----------|----------------|---------|--------|
| Backend avatar logic | >90% | 0% | ⚠️ Pending |
| Frontend types | >85% | 0% | ⚠️ Pending |
| AgentAvatar component | >85% | 0% | ⚠️ Pending |
| AgentCard updates | >80% | TBD | ⚠️ Pending |

### Performance Benchmarks

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Avatar image load time | <500ms | N/A | ⚠️ Pending |
| Fallback icon render | <50ms | N/A | ⚠️ Pending |
| Layout shift (CLS) | <0.1 | N/A | ⚠️ Pending |
| Image size | <100KB | N/A | ⚠️ Pending |

### Accessibility Checklist

- [ ] All images have descriptive alt text
- [ ] Fallback icons have aria-labels
- [ ] Color contrast meets WCAG AA (4.5:1 minimum)
- [ ] Keyboard navigation functional
- [ ] Screen reader announces avatar presence
- [ ] Focus states visible

---

## 🚨 Risk Management

### Identified Risks

#### Risk 1: Database Migration Failure

**Probability**: Low
**Impact**: High (blocks entire feature)

**Mitigation**:
- Test migration on development database first
- Implement rollback plan
- Backup production data before migration
- Validate column types and constraints

**Contingency**:
- Manual schema update if Alembic fails
- Rollback to previous migration version
- Hotfix migration file if errors detected

#### Risk 2: Image Load Performance

**Probability**: Medium
**Impact**: Medium (user experience degradation)

**Mitigation**:
- Implement lazy loading (loading="lazy")
- Optimize image sizes (<100KB)
- Use modern formats (WebP with PNG fallback)
- Reserve layout space to prevent CLS

**Contingency**:
- Reduce image dimensions if load times exceed 500ms
- Use external CDN for faster delivery
- Implement progressive image loading

#### Risk 3: Cross-Browser Compatibility

**Probability**: Low
**Impact**: Medium (some users affected)

**Mitigation**:
- Test on Chrome, Firefox, Safari before deployment
- Use standard HTML <img> tags (broad support)
- Polyfill for older browsers if needed

**Contingency**:
- Feature detection to show emoji-only fallback on unsupported browsers
- Document minimum browser version requirements

#### Risk 4: Asset Design Delays

**Probability**: Medium
**Impact**: Low (can use emoji fallbacks initially)

**Mitigation**:
- Prepare emoji fallback system as primary implementation
- Decouple asset acquisition from code deployment
- Allow external designers time for quality artwork

**Contingency**:
- Deploy feature with emoji fallbacks only
- Add PNG avatars in subsequent release
- Use AI-generated placeholder images temporarily

---

## 📚 Documentation Updates

### Files Requiring Updates

#### README.md Additions

**Section**: Features
```markdown
### Pokemon-Style Agent Cards

- **Character Avatars**: Each agent displays a unique character image based on rarity tier
- **Rarity System**: Common, Rare, Epic, Legendary tiers with visual distinction
- **Fallback Icons**: Graceful degradation with emoji icons when images fail to load
- **Default Avatars**: Deterministic avatar assignment based on agent properties
```

#### API Documentation (OpenAPI/Swagger)

**Update**: `AgentResponse` schema definition

```yaml
AgentResponse:
  type: object
  properties:
    # ... existing fields ...
    avatar_url:
      type: string
      format: uri
      nullable: true
      description: URL to agent's avatar/character image
      example: "/avatars/epic/default-1.png"
    rarity:
      type: string
      enum: [Common, Rare, Epic, Legendary]
      default: Common
      description: Agent rarity tier (Pokemon-style)
    character_description:
      type: string
      nullable: true
      maxLength: 500
      description: Character description for AI-generated avatars
```

#### Component Documentation (Storybook/JSDoc)

**File**: `frontend/src/components/agent-card/AgentAvatar.tsx`

```typescript
/**
 * AgentAvatar Component
 *
 * Displays agent character avatar with automatic fallback handling.
 *
 * Features:
 * - Lazy loading for performance optimization
 * - Graceful error handling with rarity-based emoji fallback
 * - Accessible with descriptive alt text and aria-labels
 *
 * @example
 * ```tsx
 * <AgentAvatar
 *   avatarUrl="/avatars/epic/default-1.png"
 *   agentName="RAG Assistant Alpha"
 *   rarity="Epic"
 *   className="w-full h-48"
 * />
 * ```
 */
```

---

## 🎓 Knowledge Transfer

### Key Learnings for Future Features

1. **Deterministic Default Assignment**: Using agent_id hash ensures consistent avatar selection without database overhead
2. **Fallback Strategy**: Multi-layer fallback (URL → default → emoji) ensures resilience
3. **Lazy Loading Best Practice**: Always use `loading="lazy"` for images below the fold
4. **Accessibility First**: Alt text and aria-labels are non-negotiable for inclusive design

### Reusable Patterns

**Avatar Selection Algorithm**:
```typescript
// Pattern: Deterministic selection from pool based on unique ID
function selectFromPool<T>(pool: T[], uniqueId: string): T {
  const hash = uniqueId.split('-')[0]
  const index = parseInt(hash, 16) % pool.length
  return pool[index]
}
```

**Graceful Image Degradation**:
```tsx
// Pattern: Progressive fallback with error handling
const [imageError, setImageError] = useState(false)

return imageError ? <FallbackComponent /> : (
  <img onError={() => setImageError(true)} ... />
)
```

---

## 🔄 Post-Implementation Sync

### `/alfred:3-sync` Checklist

After implementation completes, run `/alfred:3-sync` to:

- [ ] Update SPEC status from `draft` to `completed`
- [ ] Bump SPEC version from `0.0.1` to `0.1.0`
- [ ] Generate TAG health report
- [ ] Validate @TAG chain integrity (SPEC → TEST → CODE → DOC)
- [ ] Update documentation with actual implementation details
- [ ] Create PR with comprehensive description
- [ ] Link PR to SPEC directory

---

**Plan Status**: Draft
**Next Action**: `/alfred:2-run SPEC-POKEMON-IMAGE-001`
**Expected Outcome**: TDD implementation with RED → GREEN → REFACTOR commits
