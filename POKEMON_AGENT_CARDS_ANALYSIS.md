# Pokemon-Style Agent Cards - Codebase Analysis Report

**Date**: 2025-11-08  
**Project**: dt-rag-standalone  
**Branch**: master  
**Thoroughness Level**: Medium (Agent Card-focused)

---

## Executive Summary

The dt-rag-standalone project implements a **Pokemon-inspired Agent Growth Platform** with gamified leveling, XP tracking, rarity tiers, and visual progression bars. The system consists of:

- **Backend**: FastAPI-based API with SQLAlchemy ORM, Pydantic schemas, and Alembic migrations
- **Frontend**: React 19 with TypeScript, Tailwind CSS v4, Zod validation, and Framer Motion animations
- **Database**: PostgreSQL (primary) with SQLite fallback, supporting UUID arrays and JSONB fields

The architecture is production-ready for adding avatar/image features because it already uses JSONB/JSON fields for flexible configs and follows clear layering patterns.

---

## Part 1: Backend Architecture

### 1.1 Agent Database Schema

**File**: `/home/a/projects/dt-rag-standalone/apps/api/database.py` (lines 366-405)

```python
class Agent(Base):
    __tablename__ = "agents"
    
    # Core Identity
    agent_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    taxonomy_node_ids: Mapped[List[uuid.UUID]]
    taxonomy_version: Mapped[str]
    scope_description: Mapped[Optional[str]]
    
    # Growth Metrics (Gamification)
    level: Mapped[int]                          # 1-5 range
    current_xp: Mapped[float]
    total_queries: Mapped[int]
    successful_queries: Mapped[int]
    
    # Quality Metrics
    coverage_percent: Mapped[float]             # 0-100%
    avg_faithfulness: Mapped[float]             # 0-1
    avg_response_time_ms: Mapped[float]
    
    # Coverage Tracking
    total_documents: Mapped[int]
    total_chunks: Mapped[int]
    last_coverage_update: Mapped[Optional[datetime]]
    
    # Configuration (JSON/JSONB)
    retrieval_config: Mapped[Dict[str, Any]]    # Flexible config storage
    features_config: Mapped[Dict[str, Any]]     # Feature flags
    
    # Timestamps
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    last_query_at: Mapped[Optional[datetime]]
```

**Key Design Pattern**: Uses SQLAlchemy's `Mapped` type hints with support for both PostgreSQL (native JSONB) and SQLite (JSON serialization).

### 1.2 Pydantic Request/Response Schemas

**File**: `/home/a/projects/dt-rag-standalone/apps/api/schemas/agent_schemas.py`

#### AgentCreateRequest
```python
class AgentCreateRequest(BaseModel):
    name: str                                   # 1-255 chars
    taxonomy_node_ids: List[UUID4]             # Required, min 1
    taxonomy_version: str = "1.0.0"
    scope_description: Optional[str] = None    # Max 500 chars
    retrieval_config: Optional[Dict[str, Any]] = default_factory
    features_config: Optional[Dict[str, Any]] = default_factory
```

#### AgentResponse (Read/List)
```python
class AgentResponse(BaseModel):
    agent_id: UUID4
    name: str
    level: int                                  # 1-5 constraint
    current_xp: int
    total_documents: int
    total_queries: int
    coverage_percent: float                     # 0-100%
    avg_faithfulness: float                     # 0-1
    avg_response_time_ms: float
    created_at: datetime
    updated_at: datetime
    last_query_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)  # ORM mapping
```

#### AgentUpdateRequest
```python
class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    scope_description: Optional[str] = None
    retrieval_config: Optional[Dict[str, Any]] = None
    features_config: Optional[Dict[str, Any]] = None
```

**Integration Point for Avatars**: The `retrieval_config` and `features_config` fields are flexible JSONB/JSON objects - avatar data could be stored here or as dedicated columns.

### 1.3 Database Migration Pattern

**File**: `/home/a/projects/dt-rag-standalone/alembic/versions/0011_add_agents_table.py`

The migration demonstrates:

1. **Multi-Database Support**:
   ```python
   bind = op.get_bind()
   is_postgresql = bind.dialect.name == 'postgresql'
   
   if is_postgresql:
       # Native UUID[] arrays, JSONB
       op.create_table('agents',
           sa.Column('taxonomy_node_ids', postgresql.ARRAY(...)),
           sa.Column('retrieval_config', postgresql.JSONB(...)),
       )
   else:
       # SQLite fallback with JSON string serialization
       op.create_table('agents',
           sa.Column('taxonomy_node_ids', sa.Text()),
           sa.Column('retrieval_config', sa.Text()),
       )
   ```

2. **Constraints for Data Integrity**:
   ```sql
   ALTER TABLE agents ADD CONSTRAINT valid_level
   CHECK (level >= 1 AND level <= 5)
   
   ALTER TABLE agents ADD CONSTRAINT valid_coverage
   CHECK (coverage_percent >= 0 AND coverage_percent <= 100)
   ```

3. **Indexes for Query Performance**:
   ```sql
   CREATE INDEX idx_agents_taxonomy ON agents USING GIN (taxonomy_node_ids)
   CREATE INDEX idx_agents_level ON agents (level)
   CREATE INDEX idx_agents_coverage ON agents (coverage_percent DESC)
   ```

**For Avatar Implementation**: Create a new migration following this pattern to add avatar fields (e.g., `avatar_url`, `avatar_style`, `avatar_metadata`).

### 1.4 API Router Pattern

**File**: `/home/a/projects/dt-rag-standalone/apps/api/routers/agent_router.py`

```python
router = APIRouter(prefix="/agents", tags=["agents"])

@router.post(
    "/from-taxonomy",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_from_taxonomy(
    request: AgentCreateRequest,
    session: AsyncSession = Depends(get_session),
    api_key: Any = Depends(verify_api_key),
) -> AgentResponse:
    # Validates taxonomy nodes
    # Creates Agent via DAO
    # Returns AgentResponse
    pass
```

**Pattern**: Controllers delegate to DAOs for data access, maintain separation of concerns.

---

## Part 2: Frontend Architecture

### 2.1 Type Definitions

**File**: `/home/a/projects/dt-rag-standalone/frontend/src/lib/api/types.ts` (lines 420-444)

```typescript
// Rarity Enum
export const RaritySchema = z.enum(['Common', 'Rare', 'Epic', 'Legendary'])
export type Rarity = z.infer<typeof RaritySchema>

// Agent Card Display Model
export const AgentCardDataSchema = z.object({
  agent_id: z.string().uuid('Invalid agent ID format'),
  name: z.string().min(1).max(100),
  level: z.number().int().min(1).max(10),        // Note: Frontend allows 1-10
  current_xp: z.number().int().min(0),
  next_level_xp: z.number().int().nullable(),
  rarity: RaritySchema,
  total_documents: z.number().int().min(0),
  total_queries: z.number().int().min(0),
  quality_score: z.number().min(0).max(100),     // 0-100% as percentage
  status: z.string().min(1),
  created_at: z.string().datetime(),
  last_used: z.string().datetime().optional(),
}).refine(
  (data) => data.next_level_xp === null || data.next_level_xp > data.current_xp,
  { message: 'next_level_xp must be greater than current_xp' }
)

export type AgentCardData = z.infer<typeof AgentCardDataSchema>
```

**Key Observations**:
- Rarity is an enum: `'Common' | 'Rare' | 'Epic' | 'Legendary'`
- Level: 1-10 frontend range (different from backend's 1-5)
- Quality score is 0-100 (different from backend's 0-1 faithfulness)
- Uses Zod for runtime validation
- Custom refinement for XP validation

### 2.2 Agent Card Component Structure

**Main Component**: `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/AgentCard.tsx`

```typescript
interface AgentCardProps {
  agent: AgentCardData
  onView: () => void
  onDelete: () => void
  className?: string
}

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent,
  onView,
  onDelete,
  className
}) {
  return (
    <article className={cn(
      'w-full p-4 bg-white rounded-lg border-2 shadow-md',
      agent.rarity.toLowerCase() === 'common' && 'border-gray-300',
      agent.rarity.toLowerCase() === 'rare' && 'border-blue-400',
      agent.rarity.toLowerCase() === 'epic' && 'border-purple-500',
      agent.rarity.toLowerCase() === 'legendary' && 'border-accent-gold-500',
    )}>
      {/* Header with name and rarity badge */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold">{agent.name}</h3>
          <p className="text-sm text-gray-600">Level {agent.level}</p>
        </div>
        <RarityBadge rarity={agent.rarity} />
      </div>
      
      {/* XP Progress Bar */}
      <ProgressBar
        current={agent.current_xp}
        max={agent.next_level_xp || agent.current_xp}
        label={`${agent.current_xp} / ${agent.next_level_xp} XP`}
      />
      
      {/* Stats Grid (3 columns) */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <StatDisplay label="Docs" value={agent.total_documents} />
        <StatDisplay label="Queries" value={agent.total_queries} />
        <StatDisplay label="Quality" value={agent.quality_score} />
      </div>
      
      {/* Action Buttons */}
      <ActionButtons onView={onView} onDelete={onDelete} />
    </article>
  )
}, arePropsEqual)
```

**Memo Optimization**: Uses custom `arePropsEqual` to skip re-renders when only styles change.

### 2.3 Sub-Components

#### RarityBadge
**File**: `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/RarityBadge.tsx`

```typescript
export const RarityBadge = memo<RarityBadgeProps>(function RarityBadge({
  rarity,
  className
}) {
  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
      rarity.toLowerCase() === 'common' && 'bg-gray-500 text-white',
      rarity.toLowerCase() === 'rare' && 'bg-blue-500 text-white',
      rarity.toLowerCase() === 'epic' && 'bg-purple-600 text-white',
      rarity.toLowerCase() === 'legendary' && 'bg-accent-gold-500 text-black',
    )}>
      {rarity}
    </span>
  )
})
```

**Key Pattern**: Rarity-based color styling using Tailwind's explicit class names (Tailwind v4 JIT requirement).

#### ProgressBar
**File**: `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/ProgressBar.tsx`

```typescript
export const ProgressBar = memo<ProgressBarProps>(function ProgressBar({
  current,
  max,
  label,
  ariaLabel = 'Progress',
  className,
}) {
  const percentage = max > 0 ? Math.min((current / max) * 100, 100) : 0

  return (
    <div className={cn('w-full', className)}>
      <div
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={ariaLabel}
        className="relative h-2 w-full bg-gray-200 rounded-full overflow-hidden"
      >
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      {label && (
        <p className="text-xs text-gray-600 mt-1 text-center">{label}</p>
      )}
    </div>
  )
})
```

**Accessibility**: Uses ARIA attributes for screen readers.

#### StatDisplay
**File**: `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/StatDisplay.tsx`

```typescript
interface StatDisplayProps {
  label: string
  value: string | number
  icon?: ReactNode
  variant?: 'default' | 'primary' | 'success' | 'warning'
  layout?: 'vertical' | 'horizontal'
  className?: string
}
```

#### LevelUpModal
**File**: `/home/a/projects/dt-rag-standalone/frontend/src/components/agent-card/LevelUpModal.tsx`

Uses Framer Motion for animations + react-confetti for celebratory effects:

```typescript
interface LevelUpModalProps {
  isOpen: boolean
  onClose: () => void
  oldLevel: number
  newLevel: number
  rarity: Rarity
  upgradeRarity?: Rarity
}

// Renders with:
// - Confetti animation (200 pieces, gravity=0.3)
// - Backdrop with black/50 opacity
// - Modal with spring animation (stiffness=300, damping=25)
// - Auto-closes after 3 seconds
```

### 2.4 API Client

**File**: `/home/a/projects/dt-rag-standalone/frontend/src/lib/api/agents.ts`

```typescript
export async function fetchAgents(params?: FetchAgentsParams): Promise<AgentCardData[]> {
  const response = await apiClient.get<AgentsListResponse>('/api/v1/agents', params)
  const validated = AgentsListResponseSchema.parse(response)
  return validated.agents
}

export async function fetchAgent(agentId: string): Promise<AgentCardData> {
  return apiClient.get<AgentCardData>(`/api/v1/agents/${agentId}`)
}

export async function calculateCoverage(agentId: string): Promise<CoverageResponse> {
  return apiClient.get<CoverageResponse>(`/api/v1/agents/${agentId}/coverage`)
}
```

**Pattern**: Schemas validated using Zod before returning to components.

---

## Part 3: Libraries & Versions

### 3.1 Backend Stack

**File**: `/home/a/projects/dt-rag-standalone/pyproject.toml`

| Library | Version | Purpose |
|---------|---------|---------|
| **FastAPI** | >= 0.104.0 | Web framework |
| **Pydantic** | >= 2.5.0 | Request/response validation |
| **SQLAlchemy** | >= 2.0.0 | ORM with async support |
| **asyncpg** | >= 0.29.0 | PostgreSQL async driver |
| **Alembic** | >= 1.13.0 | Database migrations |
| **Python** | >= 3.9 | Runtime |

### 3.2 Frontend Stack

**File**: `/home/a/projects/dt-rag-standalone/frontend/package.json`

| Library | Version | Purpose |
|---------|---------|---------|
| **React** | ^19.1.1 | UI framework |
| **TypeScript** | Latest | Type safety |
| **Tailwind CSS** | v4 with @tailwindcss/postcss | Styling |
| **Zod** | ^4.1.12 | Runtime validation |
| **Framer Motion** | ^11.18.2 | Animations |
| **react-confetti** | ^6.4.0 | Celebration effects |
| **axios** | ^1.13.1 | HTTP client |
| **zustand** | ^5.0.8 | State management |
| **@tanstack/react-query** | ^5.90.5 | Data fetching/caching |
| **@xyflow/react** | ^12.9.0 | Graph visualization |

---

## Part 4: Avatar Integration Points

### 4.1 Database Layer (Add to Migration)

Create a new migration `0013_add_agent_avatar_fields.py`:

```python
# PostgreSQL
sa.Column('avatar_url', sa.Text(), nullable=True),
sa.Column('avatar_style', sa.String(50), nullable=True),  # e.g., 'pixel', '3d', 'anime'
sa.Column('avatar_metadata', postgresql.JSONB(), 
          server_default='{"traits": [], "colors": {}}'),

# SQLite
sa.Column('avatar_url', sa.Text(), nullable=True),
sa.Column('avatar_style', sa.String(50), nullable=True),
sa.Column('avatar_metadata', sa.Text(),  # JSON string
          server_default='{"traits": [], "colors": {}}'),
```

OR store as part of existing config:

```python
# Enhanced retrieval_config/features_config approach
features_config: {
  "avatar": {
    "enabled": true,
    "style": "pokemon",
    "url": "https://...",
    "traits": ["fire", "dragon"],
    "colors": {"primary": "#FF6B35", "secondary": "#004E89"}
  }
}
```

### 4.2 Pydantic Schema Layer

Extend `AgentResponse`:

```python
class AvatarMetadata(BaseModel):
    url: Optional[str] = None
    style: Optional[str] = None  # 'pokemon', 'pixel', '3d'
    traits: List[str] = Field(default_factory=list)
    colors: Dict[str, str] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    # ... existing fields ...
    avatar: Optional[AvatarMetadata] = None
```

### 4.3 Frontend Type Layer

Extend `AgentCardData`:

```typescript
export const AvatarMetadataSchema = z.object({
  url: z.string().url().optional(),
  style: z.enum(['pokemon', 'pixel', '3d']).optional(),
  traits: z.array(z.string()).default([]),
  colors: z.record(z.string(), z.string()).default({}),
})

export const AgentCardDataSchema = z.object({
  // ... existing fields ...
  avatar: AvatarMetadataSchema.optional(),
})
```

### 4.4 UI Component Addition

New component: `AgentCardAvatar.tsx`

```typescript
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
  // Render avatar image or placeholder
  // Position in top-left of card above/beside name
  // Frame color matches rarity tier
  return (
    <div className={cn('relative w-16 h-16 rounded border-2', {
      'border-gray-300': rarity === 'Common',
      'border-blue-400': rarity === 'Rare',
      'border-purple-500': rarity === 'Epic',
      'border-accent-gold-500': rarity === 'Legendary',
    }, className)}>
      {avatar?.url ? (
        <img src={avatar.url} alt={name} className="w-full h-full object-cover rounded" />
      ) : (
        <div className="flex items-center justify-center w-full h-full bg-gray-200">
          <span className="text-2xl">🤖</span>
        </div>
      )}
    </div>
  )
})
```

### 4.5 Updated AgentCard Layout

```typescript
// Header updated to include avatar
<div className="flex items-start justify-between mb-3 gap-3">
  <AgentCardAvatar avatar={agent.avatar} rarity={agent.rarity} name={agent.name} level={agent.level} />
  <div className="flex-1">
    <h3 className="text-lg font-bold text-gray-900">{agent.name}</h3>
    <p className="text-sm text-gray-600">Level {agent.level}</p>
  </div>
  <RarityBadge rarity={agent.rarity} />
</div>
```

---

## Part 5: Key Design Patterns Identified

### 5.1 Database Patterns

| Pattern | Location | Notes |
|---------|----------|-------|
| **Multi-DB Support** | `database.py` type decorators | Graceful PostgreSQL/SQLite fallback |
| **JSONB Flexibility** | Agent model `retrieval_config`, `features_config` | Allows schema evolution without migrations |
| **Constraints** | Migration `0011` | CHECK constraints for data integrity |
| **Indexes** | Migration `0011` | GIN index for array queries, descending for coverage |
| **SQLAlchemy Modern** | `database.py` | `Mapped` type hints, async support |

### 5.2 API Patterns

| Pattern | Location | Notes |
|---------|----------|-------|
| **Request/Response Separation** | `agent_schemas.py` | Distinct Create/Read/Update schemas |
| **ConfigDict(from_attributes=True)** | AgentResponse | Auto-mapping from ORM to Pydantic |
| **Field Validation** | Schema definitions | Min/max, constraints in Field() |
| **Async Dependencies** | `agent_router.py` | FastAPI Depends() for session injection |

### 5.3 Frontend Patterns

| Pattern | Location | Notes |
|---------|----------|-------|
| **Component Composition** | AgentCard.tsx | Splits into RarityBadge, ProgressBar, StatDisplay, ActionButtons |
| **Memo with Custom Equality** | AgentCard.tsx | `arePropsEqual` function prevents unnecessary renders |
| **Zod Runtime Validation** | `types.ts` | Type-safe runtime schema validation |
| **Accessibility First** | All components | ARIA labels, roles, semantic HTML |
| **Tailwind v4 JIT** | RarityBadge, LevelUpModal | Explicit class names in conditionals (not dynamic) |
| **Framer Motion** | LevelUpModal.tsx | Spring animations + exit transitions |

---

## Part 6: Integration Checklist for Avatar Feature

### Backend (Python/FastAPI)

- [ ] Create migration `0013_add_agent_avatar_fields.py`
  - [ ] Add avatar_url, avatar_style, avatar_metadata columns
  - [ ] Support PostgreSQL (Text, JSONB) and SQLite (Text, JSON)
  - [ ] Add index on avatar_style for filtering
  
- [ ] Update Agent ORM model in `database.py`
  - [ ] Add avatar_url, avatar_style, avatar_metadata fields
  
- [ ] Create AvatarMetadata Pydantic schema
  - [ ] Include: url, style, traits, colors
  
- [ ] Update AgentResponse schema
  - [ ] Add avatar: Optional[AvatarMetadata] field
  
- [ ] Update AgentCreateRequest
  - [ ] Add avatar fields as optional
  
- [ ] Update AgentUpdateRequest
  - [ ] Add avatar fields as optional
  
- [ ] Create avatar-related endpoints (optional)
  - [ ] POST /agents/{id}/avatar - Upload/set avatar
  - [ ] GET /agents/{id}/avatar - Get avatar metadata
  - [ ] DELETE /agents/{id}/avatar - Remove avatar

### Frontend (React/TypeScript)

- [ ] Create AvatarMetadata Zod schema in `types.ts`
- [ ] Extend AgentCardData schema to include avatar
- [ ] Create `AgentCardAvatar.tsx` component
  - [ ] Image rendering with fallback
  - [ ] Rarity-based frame coloring
  - [ ] Responsive sizing
  - [ ] Error states (broken image, missing URL)
  
- [ ] Update AgentCard.tsx layout
  - [ ] Insert avatar component in header
  - [ ] Adjust grid spacing for new layout
  - [ ] Update test expectations
  
- [ ] Update API client in `agents.ts`
  - [ ] Handle avatar in response validation
  
- [ ] Create AvatarUpload component (optional)
  - [ ] File input with preview
  - [ ] Style selector
  - [ ] Trait picker
  - [ ] Color customizer

---

## Part 7: File Structure Summary

### Backend Critical Files

```
/home/a/projects/dt-rag-standalone/
├── apps/api/
│   ├── database.py                      # Agent ORM model
│   ├── schemas/agent_schemas.py         # Pydantic schemas
│   ├── routers/agent_router.py          # API endpoints
│   ├── agent_dao.py                     # Data access
│   └── services/leveling_service.py     # XP/level logic
├── alembic/
│   └── versions/
│       ├── 0011_add_agents_table.py     # Initial Agent migration
│       └── 0013_add_agent_avatar_fields.py  # [NEW]
└── pyproject.toml                       # Dependencies (FastAPI 0.104+, SQLAlchemy 2.0+)
```

### Frontend Critical Files

```
frontend/src/
├── lib/api/
│   ├── types.ts                         # Zod schemas, TypeScript types
│   └── agents.ts                        # API client functions
├── components/agent-card/
│   ├── AgentCard.tsx                    # Main component
│   ├── AgentCardAvatar.tsx              # [NEW]
│   ├── RarityBadge.tsx                  # Rarity display
│   ├── ProgressBar.tsx                  # XP progress
│   ├── StatDisplay.tsx                  # Stat boxes
│   ├── ActionButtons.tsx                # View/Delete buttons
│   ├── LevelUpModal.tsx                 # Level-up animation
│   └── __tests__/                       # Component tests
└── package.json                         # React 19.1, TypeScript, Tailwind v4
```

---

## Part 8: Rarity-Based Color System

The existing system uses a 4-tier rarity system with consistent color mapping:

| Rarity | Primary Color | Badge Background | Border Color | Text Color |
|--------|---------------|------------------|--------------|------------|
| **Common** | Gray | bg-gray-500 | border-gray-300 | text-gray-600 |
| **Rare** | Blue | bg-blue-500 | border-blue-400 | text-blue-600 |
| **Epic** | Purple | bg-purple-600 | border-purple-500 | text-purple-600 |
| **Legendary** | Gold | bg-accent-gold-500 | border-accent-gold-500 | text-accent-gold-500 |

**Avatar Frame Recommendation**: Use same color system for avatar borders/frames to maintain visual consistency.

---

## Part 9: XP & Level System

### Backend (Pydantic Constraints)
- Level: 1-5 range with CHECK constraint
- current_xp: >= 0
- Coverage: 0-100% with CHECK constraint

### Frontend (Zod Validation)
- Level: 1-10 range (extended display range)
- current_xp: >= 0
- next_level_xp: > current_xp or null
- quality_score: 0-100 as percentage

**Mismatch Note**: Backend uses 1-5 levels, frontend displays 1-10. Confirm mapping during avatar feature implementation.

---

## Part 10: State Management

**Frontend State Strategy**: 
- Uses **Zustand** for global state
- **TanStack React Query** for server state
- Component-level React state with `useState`

**Recommendation**: Avatar state should be managed via React Query cache (part of AgentCardData response).

---

## Conclusion

The dt-rag-standalone codebase is **well-structured and production-ready** for avatar integration:

1. **Flexible Storage**: JSONB fields allow avatar metadata without schema breaking changes
2. **Clear Layering**: Database → Pydantic → API → Frontend types → Components
3. **Modern Stack**: FastAPI 0.104+, React 19, TypeScript, Tailwind CSS v4
4. **Validation**: Zod runtime checks + Pydantic server-side validation
5. **Accessibility**: ARIA attributes, semantic HTML, keyboard support
6. **Testing**: Component tests exist; avatar component should follow same patterns

**Recommended Approach**: 
- Add avatar as optional fields to Agent ORM and schemas
- Store as part of features_config (no migration) OR create dedicated columns (cleaner, requires migration)
- Create AvatarMetadata type, extend AgentCardData
- Build AgentCardAvatar component following existing memo/composition patterns
- Use existing rarity color system for frame borders

