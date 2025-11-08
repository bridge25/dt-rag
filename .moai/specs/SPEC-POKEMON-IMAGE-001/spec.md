---
# Required Fields (7)
id: POKEMON-IMAGE-001
version: 0.0.1
status: draft
created: 2025-11-08
updated: 2025-11-08
author: @Alfred
priority: high

# Optional Fields – Classification/Meta
category: feature
labels:
  - pokemon-card
  - character-image
  - full-stack
  - ui-enhancement

# Optional Fields – Scope/Impact
scope:
  packages:
    - apps/api/schemas
    - apps/api/database
    - frontend/src/components/agent-card
    - frontend/src/lib/api
  files:
    - apps/api/schemas/agent_schemas.py
    - apps/api/database.py
    - frontend/src/components/agent-card/AgentCard.tsx
    - frontend/src/lib/api/types.ts
---

<!-- @SPEC:POKEMON-IMAGE-001 -->
# SPEC: Pokemon Card Character Image Implementation

## HISTORY

### v0.0.1 (2025-11-08)
- **INITIAL**: SPEC creation for Pokemon card character image feature
- **AUTHOR**: @Alfred
- **SECTIONS**: Environment, Assumptions, Requirements, Specifications
- **SCOPE**: Full-stack implementation (DB → API → Frontend)

---

## @SPEC:POKEMON-IMAGE-001-ENV-001 Environment

### Business Context

The Pokemon-styled agent card UI is **missing the character image feature** across the entire stack. This is not a CSS styling issue but a **complete feature gap** from database schema to frontend rendering.

**Business Value**: HIGH
- User-visible feature enhancing visual appeal
- Aligns with Pokemon card aesthetic (character image is central element)
- Improves user engagement and brand identity

**Discovery Context**: Identified during screenshot review session when user noted:
> "프론트엔드 개발 작업 당시 이 카드 부분은 pokemon 스타일로 캐릭터 이미지도 카드안에 삽입되게 주문하여 작업한거로 기억하는데 스크린샷에서는 그것을 확인하지 못했어"

### Technical Context

**Current State Analysis**:
1. **Database**: No `avatar_url` or `character_image_url` column in agents table
2. **API Schema**: `AgentResponse` missing image-related fields
3. **Frontend Types**: `AgentCardDataSchema` has no image field definitions
4. **Component**: `AgentCard.tsx` has no image rendering logic

**Reference Document**: `.moai/issues/POKEMON_CARD_IMAGE_MISSING.md` (comprehensive full-stack analysis)

### System Architecture

**Stack**:
- **Backend**: FastAPI + SQLAlchemy + Alembic migrations
- **Frontend**: React + TypeScript + Tailwind CSS
- **Data Flow**: PostgreSQL → FastAPI → React components

**Pokemon Card Layout Requirement**:
```
┌─────────────────────────────┐
│ [Name]         [Rarity Badge]│  ← Header
├─────────────────────────────┤
│                             │
│    🧙 [Character Image]      │  ← MISSING IMPLEMENTATION
│         (Large)             │
│                             │
├─────────────────────────────┤
│ [XP Progress Bar]           │
├─────────────────────────────┤
│ [Stats: HP/Attack/Defense]  │
├─────────────────────────────┤
│ [Action Buttons]            │
└─────────────────────────────┘
```

---

## @SPEC:POKEMON-IMAGE-001-ASMP-001 Assumptions

### Technical Assumptions

1. **Image Storage Strategy**: Default avatar images stored in `frontend/public/avatars/` directory
   - No external CDN required for Phase 1
   - Future: S3/Cloudinary integration for custom uploads

2. **Rarity-Based Avatar Assignment**: Rarity tier (Common/Rare/Epic/Legendary) determines avatar pool
   - 3 default avatars per rarity tier (12 total)
   - Deterministic selection based on agent_id hash

3. **Fallback Strategy**: Emoji icons used when image fails to load
   - Common: 🤖
   - Rare: 💎
   - Epic: ⚡
   - Legendary: 👑

4. **Database Migration**: Backward-compatible schema change
   - New columns nullable (`avatar_url`, `rarity`, `character_description`)
   - Existing agents receive default values via migration

5. **API Compatibility**: Non-breaking change to `AgentResponse` schema
   - New fields optional with defaults
   - Existing clients can ignore new fields

### Business Assumptions

1. **User Expectation**: Users expect visual character representation in Pokemon-style cards
2. **Default Assets Acceptable**: Pre-designed default avatars sufficient for initial release
3. **No User Upload Required**: Phase 1 does not require user-uploaded custom images

### Risk Assumptions

1. **Image Load Performance**: Avatar images <100KB each, negligible load time impact
2. **Browser Compatibility**: Modern browsers support standard image formats (PNG/WebP)
3. **Accessibility**: Alt text and fallback icons ensure screen reader compatibility

---

## @SPEC:POKEMON-IMAGE-001-REQ-001 Requirements

### Ubiquitous Requirements (Foundation)

**@SPEC:POKEMON-IMAGE-001-REQ-001.1**: The system shall provide character image display for all agent cards in Pokemon style.

**@SPEC:POKEMON-IMAGE-001-REQ-001.2**: The system shall store agent avatar URLs in the database with nullable constraints.

**@SPEC:POKEMON-IMAGE-001-REQ-001.3**: The system shall return avatar image data in all agent API responses.

**@SPEC:POKEMON-IMAGE-001-REQ-001.4**: The system shall render character images between the card header and XP progress bar.

### Event-Driven Requirements

**@SPEC:POKEMON-IMAGE-001-REQ-002.1**: WHEN an agent is created, the system shall assign a default avatar URL based on rarity tier.

**@SPEC:POKEMON-IMAGE-001-REQ-002.2**: WHEN an avatar image fails to load, the system shall display a rarity-specific fallback emoji icon.

**@SPEC:POKEMON-IMAGE-001-REQ-002.3**: WHEN the API returns agent data, the system shall include `avatar_url`, `rarity`, and `character_description` fields.

**@SPEC:POKEMON-IMAGE-001-REQ-002.4**: WHEN a user views an agent card, the system shall lazy-load the character image to optimize performance.

### State-Driven Requirements

**@SPEC:POKEMON-IMAGE-001-REQ-003.1**: WHILE an image is loading, the system shall display a gradient background placeholder.

**@SPEC:POKEMON-IMAGE-001-REQ-003.2**: WHILE an agent has no custom avatar, the system shall use the deterministic default avatar selection algorithm.

### Optional Features

**@SPEC:POKEMON-IMAGE-001-REQ-004.1**: WHERE future enhancement is implemented, the system may support AI-generated avatars via DALL-E/Stable Diffusion.

**@SPEC:POKEMON-IMAGE-001-REQ-004.2**: WHERE user customization is enabled, the system may allow avatar uploads to external storage (S3/Cloudinary).

### Constraints

**@SPEC:POKEMON-IMAGE-001-REQ-005.1**: IF database migration fails, the system shall rollback and preserve existing data integrity.

**@SPEC:POKEMON-IMAGE-001-REQ-005.2**: IF avatar URL is invalid or null, the system shall enforce fallback to deterministic default selection.

**@SPEC:POKEMON-IMAGE-001-REQ-005.3**: IF image format is unsupported, the system shall reject the avatar URL and use default fallback.

**@SPEC:POKEMON-IMAGE-001-REQ-005.4**: IF screen reader is detected, the system shall provide descriptive alt text for all avatar images.

---

## @SPEC:POKEMON-IMAGE-001-SPEC-001 Specifications

### Database Schema Changes

#### Migration: Add Avatar Fields to Agents Table

**File**: `alembic/versions/XXXX_add_agent_avatar_fields.py`

**Schema Changes**:
```python
def upgrade():
    op.add_column('agents', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('agents', sa.Column('rarity', sa.String(20), nullable=True, server_default='Common'))
    op.add_column('agents', sa.Column('character_description', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('agents', 'character_description')
    op.drop_column('agents', 'rarity')
    op.drop_column('agents', 'avatar_url')
```

**Migration Execution**:
```bash
alembic revision --autogenerate -m "Add avatar fields to agents table"
alembic upgrade head
```

**Test Migration**:
```bash
# Verify backward compatibility
alembic downgrade -1
alembic upgrade head
```

### API Schema Update

#### Pydantic Schema Extension

**File**: `apps/api/schemas/agent_schemas.py`

**Rarity Enum**:
```python
from typing import Literal, Optional

Rarity = Literal["Common", "Rare", "Epic", "Legendary"]
```

**Extended AgentResponse**:
```python
class AgentResponse(BaseModel):
    # ... existing fields ...

    # New Image Fields
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to agent's avatar/character image"
    )
    rarity: Rarity = Field(
        default="Common",
        description="Agent rarity tier (Pokemon-style)"
    )
    character_description: Optional[str] = Field(
        None,
        max_length=500,
        description="Character description for AI-generated avatars (future use)"
    )
```

#### Agent Creation Logic

**File**: `apps/api/agent_dao.py`

**Default Rarity Calculation**:
```python
def calculate_initial_rarity(taxonomy_node_ids: List[UUID]) -> str:
    """Calculate initial rarity based on taxonomy scope"""
    node_count = len(taxonomy_node_ids)
    if node_count >= 10:
        return "Legendary"
    elif node_count >= 5:
        return "Epic"
    elif node_count >= 2:
        return "Rare"
    else:
        return "Common"
```

**Default Avatar Assignment**:
```python
def get_default_avatar_url(rarity: str, agent_id: UUID) -> str:
    """Get deterministic default avatar based on rarity and agent_id"""
    avatar_index = int(str(agent_id).split('-')[0], 16) % 3 + 1
    return f"/avatars/{rarity.lower()}/default-{avatar_index}.png"
```

**Updated Create Agent**:
```python
async def create_agent(
    session: AsyncSession,
    name: str,
    taxonomy_node_ids: List[UUID],
    avatar_url: Optional[str] = None,
    rarity: Optional[str] = None,
    # ... existing params ...
) -> Agent:
    if not rarity:
        rarity = calculate_initial_rarity(taxonomy_node_ids)

    if not avatar_url:
        avatar_url = get_default_avatar_url(rarity, uuid4())

    agent = Agent(
        agent_id=uuid4(),
        name=name,
        avatar_url=avatar_url,
        rarity=rarity,
        # ... existing fields ...
    )

    session.add(agent)
    await session.commit()
    return agent
```

### Frontend Type Definitions

#### TypeScript Schema Update

**File**: `frontend/src/lib/api/types.ts`

**Extended Schema**:
```typescript
export const AgentCardDataSchema = z.object({
  // ... existing fields ...

  // New Image Fields
  avatar_url: z.string().url().optional().nullable(),
  rarity: RaritySchema,  // Already exists
  character_description: z.string().max(500).optional().nullable(),
})

export type AgentCardData = z.infer<typeof AgentCardDataSchema>
```

**Helper Function**:
```typescript
export function getDefaultAvatarUrl(rarity: Rarity, agentId: string): string {
  const hash = agentId.split('-')[0]
  const index = (parseInt(hash, 16) % 3) + 1
  return `/avatars/${rarity.toLowerCase()}/default-${index}.png`
}
```

### Frontend Component Implementation

#### AgentAvatar Component (New)

**File**: `frontend/src/components/agent-card/AgentAvatar.tsx`

**Component Structure**:
```tsx
import { memo, useState } from 'react'
import { cn } from '@/lib/utils'
import type { Rarity } from '@/lib/api/types'

interface AgentAvatarProps {
  avatarUrl: string
  agentName: string
  rarity: Rarity
  className?: string
}

const FALLBACK_ICONS: Record<Rarity, string> = {
  Legendary: '👑',
  Epic: '⚡',
  Rare: '💎',
  Common: '🤖',
}

export const AgentAvatar = memo<AgentAvatarProps>(function AgentAvatar({
  avatarUrl,
  agentName,
  rarity,
  className,
}) {
  const [imageError, setImageError] = useState(false)

  if (imageError) {
    return (
      <div
        className={cn(
          'flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg',
          className
        )}
        role="img"
        aria-label={`${agentName} avatar fallback`}
      >
        <span className="text-6xl" role="img" aria-label={`${rarity} tier icon`}>
          {FALLBACK_ICONS[rarity]}
        </span>
      </div>
    )
  }

  return (
    <img
      src={avatarUrl}
      alt={`${agentName} character avatar`}
      className={cn('w-full h-full object-cover rounded-lg', className)}
      onError={() => setImageError(true)}
      loading="lazy"
    />
  )
})
```

#### AgentCard Component Update

**File**: `frontend/src/components/agent-card/AgentCard.tsx`

**Updated Component**:
```tsx
import { AgentAvatar } from './AgentAvatar'
import { getDefaultAvatarUrl } from '@/lib/api/types'

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent, onView, onDelete, className
}) {
  const avatarUrl = agent.avatar_url || getDefaultAvatarUrl(agent.rarity, agent.agent_id)

  return (
    <article className={cn(/* ... */)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{agent.name}</h3>
          <p className="text-sm text-gray-600">Level {agent.level}</p>
        </div>
        <RarityBadge rarity={agent.rarity} />
      </div>

      {/* CHARACTER IMAGE SECTION (NEW) */}
      <div className="relative w-full h-48 mb-4">
        <AgentAvatar
          avatarUrl={avatarUrl}
          agentName={agent.name}
          rarity={agent.rarity}
          className="w-full h-48"
        />
      </div>

      {/* XP Progress */}
      <div className="mb-4">
        <ProgressBar
          current={agent.current_xp}
          max={agent.next_level_xp || agent.current_xp}
          label={`${agent.current_xp} / ${agent.next_level_xp || 'MAX'} XP`}
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <StatDisplay label="Docs" value={agent.total_documents} />
        <StatDisplay label="Queries" value={agent.total_queries} />
        <StatDisplay label="Quality" value={agent.quality_score} />
      </div>

      {/* Action Buttons */}
      <ActionButtons onView={onView} onDelete={onDelete} />
    </article>
  )
})
```

### Image Asset Management

#### Default Avatar Directory Structure

**Directory**: `frontend/public/avatars/`

**Structure**:
```
frontend/public/avatars/
├── common/
│   ├── default-1.png  (Simple robot)
│   ├── default-2.png  (Basic AI assistant)
│   └── default-3.png  (Generic agent)
├── rare/
│   ├── default-1.png  (Enhanced robot with blue accents)
│   └── default-2.png  (Advanced AI with glow effects)
├── epic/
│   ├── default-1.png  (Powerful agent with purple aura)
│   └── default-2.png  (Elite AI with energy effects)
└── legendary/
    ├── default-1.png  (Master AI with golden crown)
    └── default-2.png  (Ultimate agent with cosmic background)
```

**Image Specifications**:
- Format: PNG with transparency
- Dimensions: 400x400px (rendered at 192px height)
- File Size: <100KB per image
- Color Palette: Matches rarity badge colors

---

## @SPEC:POKEMON-IMAGE-001-TRACE-001 Traceability

### Dependencies

**Depends On**:
- None (standalone feature)

**Blocks**:
- Future AI avatar generation feature
- Future user avatar upload feature

### Related SPECs

- Related to Pokemon card UI design (no formal SPEC)
- Related to rarity system (implemented in `RarityBadge.tsx`)

### TAG Chain

**SPEC → Implementation Flow**:
```
@SPEC:POKEMON-IMAGE-001
  ├─ @TEST:POKEMON-IMAGE-001-DB-001 (Database migration tests)
  ├─ @TEST:POKEMON-IMAGE-001-API-001 (API schema tests)
  ├─ @TEST:POKEMON-IMAGE-001-FE-001 (Component tests)
  ├─ @CODE:POKEMON-IMAGE-001-MIGRATION-001 (Alembic migration)
  ├─ @CODE:POKEMON-IMAGE-001-SCHEMA-001 (Pydantic schema)
  ├─ @CODE:POKEMON-IMAGE-001-DAO-001 (Agent DAO updates)
  ├─ @CODE:POKEMON-IMAGE-001-TYPES-001 (TypeScript types)
  ├─ @CODE:POKEMON-IMAGE-001-AVATAR-001 (AgentAvatar component)
  ├─ @CODE:POKEMON-IMAGE-001-CARD-001 (AgentCard updates)
  └─ @DOC:POKEMON-IMAGE-001-README-001 (README updates)
```

### Reference Documents

- **Issue Analysis**: `.moai/issues/POKEMON_CARD_IMAGE_MISSING.md`
- **Screenshot Reference**: `screenshots/FINAL_desktop_tall.png`
- **Component Source**: `frontend/src/components/agent-card/AgentCard.tsx`
- **API Schema Source**: `apps/api/schemas/agent_schemas.py`

---

## Quality Gates

### Test Coverage Requirements

- **Backend**: >90% coverage for avatar-related logic
- **Frontend**: >85% coverage for AgentAvatar and updated AgentCard
- **Integration**: End-to-end test for agent creation → avatar display

### Performance Criteria

- Avatar image load time: <500ms (lazy loading)
- No layout shift during image load (placeholder height reserved)
- Fallback icon render: <50ms

### Accessibility Requirements

- All images have descriptive alt text
- Fallback icons have aria-labels
- Screen reader announces rarity tier
- Keyboard navigation unaffected

### Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

---

**SPEC Status**: Draft (v0.0.1)
**Next Step**: `/alfred:2-run SPEC-POKEMON-IMAGE-001` for TDD implementation
**Expected Completion Version**: v0.1.0 (after implementation and sync)
