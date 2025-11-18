# Avatar Feature Implementation - Quick Start Guide

## 3-Layer Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  FRONTEND (React 19 + TypeScript)                │
│  - AgentCardAvatar.tsx (NEW)                     │
│  - types.ts (extend AgentCardData)               │
│  - agents.ts (API client - no changes needed)    │
└─────────────────────┬───────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │ REST API (/api/v1/agents)  │
        └─────────────┬──────────────┘
                      │
┌─────────────────────────────────────────────────┐
│  BACKEND (FastAPI + Pydantic)                    │
│  - agent_schemas.py (extend AgentResponse)       │
│  - database.py (add avatar fields to Agent ORM)  │
│  - agent_router.py (no changes needed)           │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│  DATABASE (PostgreSQL/SQLite)                    │
│  - Migration 0013 (add avatar_url, avatar_style) │
│  - Alembic handles multi-DB support              │
└─────────────────────────────────────────────────┘
```

---

## Critical Files to Modify

### Backend (3 files)

#### 1. `/home/a/projects/dt-rag-standalone/alembic/versions/0013_add_agent_avatar_fields.py` (NEW)
```python
# Create new migration following 0011_add_agents_table.py pattern
# Add columns: avatar_url (Text), avatar_style (String), avatar_metadata (JSONB/JSON)
# Handle PostgreSQL vs SQLite differences
```

#### 2. `/home/a/projects/dt-rag-standalone/apps/api/database.py` (MODIFY Agent class)
```python
class Agent(Base):
    # ... existing fields ...
    
    # NEW: Avatar fields
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_metadata: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict, nullable=False
    )
```

#### 3. `/home/a/projects/dt-rag-standalone/apps/api/schemas/agent_schemas.py` (MODIFY/ADD)
```python
# ADD new schema class
class AvatarMetadata(BaseModel):
    url: Optional[str] = None
    style: Optional[str] = None  # 'pokemon', 'pixel', '3d'
    traits: List[str] = Field(default_factory=list)
    colors: Dict[str, str] = Field(default_factory=dict)

# MODIFY AgentResponse - add field
class AgentResponse(BaseModel):
    # ... existing fields ...
    avatar: Optional[AvatarMetadata] = None

# MODIFY AgentCreateRequest - add optional field
class AgentCreateRequest(BaseModel):
    # ... existing fields ...
    avatar: Optional[AvatarMetadata] = None

# MODIFY AgentUpdateRequest - add optional field
class AgentUpdateRequest(BaseModel):
    # ... existing fields ...
    avatar: Optional[AvatarMetadata] = None
```

### Frontend (2 files)

#### 4. `/home/a/projects/dt-rag-standalone/frontend/src/lib/api/types.ts` (MODIFY)
```typescript
// ADD new schemas
export const AvatarMetadataSchema = z.object({
  url: z.string().url().optional(),
  style: z.enum(['pokemon', 'pixel', '3d']).optional(),
  traits: z.array(z.string()).default([]),
  colors: z.record(z.string(), z.string()).default({}),
})

export type AvatarMetadata = z.infer<typeof AvatarMetadataSchema>

// MODIFY AgentCardDataSchema - add field
export const AgentCardDataSchema = z.object({
  // ... existing fields ...
  avatar: AvatarMetadataSchema.optional(),
})
```

#### 5. `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/AgentCardAvatar.tsx` (NEW)
```typescript
import { memo } from 'react'
import { cn } from '@/lib/utils'
import type { AvatarMetadata, Rarity } from '@/lib/api/types'

interface AgentCardAvatarProps {
  avatar?: AvatarMetadata
  rarity: Rarity
  name: string
  level: number
  className?: string
}

export const AgentCardAvatar = memo<AgentCardAvatarProps>(function AgentCardAvatar({
  avatar,
  rarity,
  name,
  level,
  className
}) {
  return (
    <div className={cn(
      'relative w-16 h-16 rounded border-2 flex-shrink-0',
      rarity.toLowerCase() === 'common' && 'border-gray-300',
      rarity.toLowerCase() === 'rare' && 'border-blue-400',
      rarity.toLowerCase() === 'epic' && 'border-purple-500',
      rarity.toLowerCase() === 'legendary' && 'border-accent-gold-500',
      className
    )}>
      {avatar?.url ? (
        <img
          src={avatar.url}
          alt={`${name} avatar`}
          className="w-full h-full object-cover rounded"
          onError={(e) => {
            e.currentTarget.style.display = 'none'
          }}
        />
      ) : (
        <div className="flex items-center justify-center w-full h-full bg-gray-100 rounded">
          <span className="text-2xl">🤖</span>
        </div>
      )}
    </div>
  )
})
```

#### 6. `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/AgentCard.tsx` (MODIFY header layout)
```typescript
// Current header layout:
<div className="flex items-start justify-between mb-3">
  <div>
    <h3 className="text-lg font-bold text-gray-900">{agent.name}</h3>
    <p className="text-sm text-gray-600">Level {agent.level}</p>
  </div>
  <RarityBadge rarity={agent.rarity} />
</div>

// NEW header layout with avatar:
<div className="flex items-start justify-between mb-3 gap-3">
  <AgentCardAvatar
    avatar={agent.avatar}
    rarity={agent.rarity}
    name={agent.name}
    level={agent.level}
  />
  <div className="flex-1">
    <h3 className="text-lg font-bold text-gray-900">{agent.name}</h3>
    <p className="text-sm text-gray-600">Level {agent.level}</p>
  </div>
  <RarityBadge rarity={agent.rarity} />
</div>
```

---

## Implementation Checklist

### Phase 1: Database (1-2 hours)

- [ ] Create migration file `0013_add_agent_avatar_fields.py`
- [ ] Test migration on PostgreSQL
- [ ] Test migration on SQLite
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify columns exist in database

### Phase 2: Backend Schema (30 mins)

- [ ] Update `database.py` Agent class (3 new fields)
- [ ] Add `AvatarMetadata` Pydantic class to `agent_schemas.py`
- [ ] Update `AgentResponse` to include avatar field
- [ ] Update `AgentCreateRequest` to include avatar
- [ ] Update `AgentUpdateRequest` to include avatar
- [ ] Run backend tests: `pytest tests/unit/test_agent_*.py`

### Phase 3: Frontend Types (30 mins)

- [ ] Add `AvatarMetadataSchema` to `types.ts`
- [ ] Add `AvatarMetadata` type export
- [ ] Update `AgentCardDataSchema` with avatar field
- [ ] Run frontend type-check: `npm run type-check`

### Phase 4: Frontend Components (2-3 hours)

- [ ] Create `AgentCardAvatar.tsx` component
- [ ] Add component tests in `__tests__/AgentCardAvatar.test.tsx`
- [ ] Import `AgentCardAvatar` in `AgentCard.tsx`
- [ ] Update AgentCard header layout
- [ ] Test responsive sizing on mobile/desktop
- [ ] Run frontend tests: `npm run test`

### Phase 5: E2E Testing (1 hour)

- [ ] Create agent without avatar (should show 🤖 placeholder)
- [ ] Create agent with avatar URL (should display image)
- [ ] Test broken image URL (should fall back to placeholder)
- [ ] Test all rarity tiers (border colors match)
- [ ] Test mobile responsiveness

### Phase 6: Optional Enhancements (2-4 hours)

- [ ] Create `AvatarUploadModal.tsx` component
  - File input
  - Image preview
  - Style selector dropdown
  - Trait selector (checkboxes)
  - Color picker integration
- [ ] Add avatar upload endpoint: `PATCH /api/v1/agents/{id}/avatar`
- [ ] Add avatar delete endpoint: `DELETE /api/v1/agents/{id}/avatar`

---

## Validation Patterns to Follow

### Pydantic (Backend)
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict

class AvatarMetadata(BaseModel):
    url: Optional[HttpUrl] = None  # Validates URL format
    style: Optional[str] = Field(None, pattern="^(pokemon|pixel|3d)$")
    traits: List[str] = Field(default_factory=list, max_length=10)
    colors: Dict[str, str] = Field(default_factory=dict, max_length=5)
```

### Zod (Frontend)
```typescript
export const AvatarMetadataSchema = z.object({
  url: z.string().url().optional(),
  style: z.enum(['pokemon', 'pixel', '3d']).optional(),
  traits: z.array(z.string().min(1).max(50)).default([]),
  colors: z.record(z.string(), z.string()).default({}),
})
```

---

## Testing Strategy

### Unit Tests
- AvatarMetadata schema validation (Pydantic + Zod)
- AgentCardAvatar rendering with/without URL
- Rarity-based border colors

### Integration Tests
- Create agent with avatar via API
- Update agent avatar
- Delete agent removes avatar
- API response schema validation

### E2E Tests
- User flow: Create agent → Upload avatar → View card
- Broken image fallback
- Mobile responsiveness

---

## Color System Reference

For avatar frame borders, use the existing rarity color system:

```css
/* Common */
border-gray-300

/* Rare */
border-blue-400

/* Epic */
border-purple-500

/* Legendary */
border-accent-gold-500
```

This maintains visual consistency with rarity badges and card borders.

---

## Common Pitfalls to Avoid

1. **Forget to test migration on SQLite** - Use `get_json_type()` for compatibility
2. **Hardcode Tailwind classes** - Use explicit color classes, not dynamic ones (Tailwind v4 JIT)
3. **Missing image error handling** - Always provide fallback for broken URLs
4. **Forget optional fields** - Use `Optional[Type]` in Pydantic, `.optional()` in Zod
5. **Forget to export types** - Export `AvatarMetadata` from `types.ts`
6. **Ignore memo optimization** - Update `arePropsEqual` in AgentCard if avatar affects memo

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/agent-avatar-support

# Make changes per checklist
# Commit incrementally
git commit -m "feat: add avatar fields to Agent database schema"
git commit -m "feat: add AvatarMetadata Pydantic schema"
git commit -m "feat: add avatar types to frontend"
git commit -m "feat: implement AgentCardAvatar component"

# Run tests
npm run test
pytest tests/

# Create PR when ready
# Request review focusing on:
# - Migration works on both PostgreSQL and SQLite
# - Type safety throughout stack
# - Component accessibility
# - Mobile responsiveness
```

---

## Reference Files (Absolute Paths)

- Full analysis: `/home/a/projects/dt-rag-standalone/POKEMON_AGENT_CARDS_ANALYSIS.md`
- Backend: `/home/a/projects/dt-rag-standalone/apps/api/database.py`
- Schemas: `/home/a/projects/dt-rag-standalone/apps/api/schemas/agent_schemas.py`
- Migration example: `/home/a/projects/dt-rag-standalone/alembic/versions/0011_add_agents_table.py`
- Frontend types: `/home/a/projects/dt-rag-standalone/frontend/src/lib/api/types.ts`
- Component example: `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/RarityBadge.tsx`

