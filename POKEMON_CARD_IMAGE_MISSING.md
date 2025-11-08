# Pokemon-Style Agent Card: Character Image Feature Missing

**생성일**: 2025-11-07
**상태**: 🔴 미구현 (Full-Stack)
**우선순위**: HIGH
**관련 이슈**: Screenshot 작업 중 발견

---

## 📋 Executive Summary

프론트엔드 Agent 카드는 Pokemon 스타일로 디자인되었으나, **캐릭터 이미지 기능이 백엔드-프론트엔드 전체 스택에서 완전히 누락**되어 있습니다. 이것은 Tailwind CSS v4 이슈가 아니라, 기능 자체가 구현되지 않은 상태입니다.

---

## 🔍 발견 경위

사용자가 스크린샷 검토 중 다음과 같이 지적:
> "프론트엔드 개발 작업 당시 이 카드 부분은 pokemon 스타일로 캐릭터 이미지도 카드안에 삽입되게 주문하여 작업한거로 기억하는데 스크린샷에서는 그것을 확인하지 못했어"

## 🎴 Pokemon 카드 구조 vs 현재 구현

### 전형적인 Pokemon 카드 레이아웃:
```
┌─────────────────────────────┐
│ [Name]         [Rarity Badge]│  ← Header
├─────────────────────────────┤
│                             │
│    🧙 [Character Image]      │  ← 🚨 MISSING!
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

### 현재 구현된 카드:
```
┌─────────────────────────────┐
│ RAG Assistant Alpha    [EPIC]│
│ Level 8                     │
├─────────────────────────────┤
│ [XP: 8500 / 10000 XP]       │
│ ███████████░░░░░ 85%        │
├─────────────────────────────┤
│ Docs    Queries   Quality   │
│ 1250    3420      92        │
├─────────────────────────────┤
│         [Delete]            │
└─────────────────────────────┘
```

**캐릭터 이미지 영역이 완전히 빠져있음!**

---

## 📊 기술 스택 전체 분석

### 1. 백엔드 API - 이미지 필드 없음

**파일**: `apps/api/schemas/agent_schemas.py`
**클래스**: `AgentResponse` (lines 43-80)

```python
class AgentResponse(BaseModel):
    """Agent response schema - used for frontend AgentCardData"""

    agent_id: UUID4
    name: str
    taxonomy_node_ids: List[UUID4]
    taxonomy_version: str
    total_documents: int
    total_chunks: int
    coverage_percent: float

    # Growth/Leveling fields ✓
    level: int  # 1-5
    current_xp: int
    total_queries: int
    successful_queries: int
    avg_faithfulness: float
    avg_response_time_ms: float

    # Timestamps ✓
    created_at: datetime
    updated_at: datetime
    last_query_at: Optional[datetime]

    # ❌ MISSING IMAGE FIELDS:
    # avatar_url: Optional[str] = None
    # character_image_url: Optional[str] = None
    # icon_url: Optional[str] = None
    # rarity: Optional[str] = None  (프론트엔드에만 있음)
```

**문제점**:
- Pokemon 스타일 카드에 필수인 캐릭터 이미지 URL 필드가 없음
- Rarity 정보도 백엔드에 없음 (프론트엔드에서 임의로 추가한 듯)

### 2. 프론트엔드 타입 정의 - 이미지 필드 없음

**파일**: `frontend/src/lib/api/types.ts`
**스키마**: `AgentCardDataSchema` (lines 423-444)

```typescript
export const AgentCardDataSchema = z.object({
  agent_id: z.string().uuid(),
  name: z.string().min(1).max(100),
  level: z.number().int().min(1).max(10),
  current_xp: z.number().int().min(0),
  next_level_xp: z.number().int().min(0).nullable(),
  rarity: RaritySchema,  // ✓ 프론트엔드 전용
  total_documents: z.number().int().min(0),
  total_queries: z.number().int().min(0),
  quality_score: z.number().min(0).max(100),
  status: z.string().min(1),
  created_at: z.string().datetime(),
  last_used: z.string().datetime().optional(),

  // ❌ MISSING IMAGE FIELDS:
  // avatar_url: z.string().url().optional(),
  // character_image_url: z.string().url().optional(),
})
```

**문제점**:
- 백엔드 API 응답과 매핑되는 타입이지만, 이미지 필드 없음
- `rarity` 필드는 프론트엔드에서 독자적으로 추가 (백엔드에 없음)

### 3. 프론트엔드 컴포넌트 - 이미지 렌더링 로직 없음

**파일**: `frontend/src/components/agent-card/AgentCard.tsx`
**컴포넌트**: `AgentCard` (lines 28-73)

```tsx
export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent, onView, onDelete, className
}) {
  return (
    <article className={...}>
      {/* Header: Name + Rarity Badge */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-900">
            {agent.name}
          </h3>
          <p className="text-sm text-gray-600">
            Level {agent.level}
          </p>
        </div>
        <RarityBadge rarity={agent.rarity} />
      </div>

      {/* ❌ CHARACTER IMAGE SECTION COMPLETELY MISSING */}

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

**문제점**:
- Header와 XP Progress 사이에 있어야 할 캐릭터 이미지 영역이 완전히 누락
- `<img>` 태그나 이미지 컴포넌트가 전혀 없음
- Fallback 아이콘(🤖, 📦 등)도 없음

### 4. 데이터베이스 스키마 (추정)

**파일**: `apps/api/database.py` (추정 위치)

Database `Agent` 모델에도 이미지 URL 컬럼이 없을 가능성이 높음:

```python
class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(UUID, primary_key=True)
    name = Column(String(255))
    level = Column(Integer)
    current_xp = Column(Integer)
    # ...

    # ❌ MISSING:
    # avatar_url = Column(String(500), nullable=True)
    # character_image_url = Column(String(500), nullable=True)
```

---

## 🎯 완전한 구현을 위한 작업 계획

### Phase 1: 백엔드 - 데이터베이스 & API

#### 1.1 데이터베이스 마이그레이션

**파일**: `alembic/versions/XXXX_add_agent_avatar_fields.py`

```python
"""Add avatar fields to agents table

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-11-07
"""

def upgrade():
    op.add_column('agents', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('agents', sa.Column('rarity', sa.String(20), nullable=True, default='Common'))
    op.add_column('agents', sa.Column('character_description', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('agents', 'character_description')
    op.drop_column('agents', 'rarity')
    op.drop_column('agents', 'avatar_url')
```

**실행**:
```bash
cd /home/a/projects/dt-rag-standalone
alembic revision --autogenerate -m "Add avatar fields to agents table"
alembic upgrade head
```

#### 1.2 Pydantic 스키마 업데이트

**파일**: `apps/api/schemas/agent_schemas.py`

```python
from typing import Optional, Literal

# Rarity enum
Rarity = Literal["Common", "Rare", "Epic", "Legendary"]

class AgentResponse(BaseModel):
    # ... existing fields ...

    # 🆕 Image fields
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
        description="Character description for AI-generated avatars"
    )
```

#### 1.3 Agent 생성 로직 수정

**파일**: `apps/api/agent_dao.py`

```python
async def create_agent(
    session: AsyncSession,
    name: str,
    taxonomy_node_ids: List[UUID],
    # ... existing params ...
    avatar_url: Optional[str] = None,  # 🆕
    rarity: Optional[str] = None,      # 🆕
) -> Agent:
    # Assign default rarity based on coverage/level
    if not rarity:
        rarity = calculate_initial_rarity(taxonomy_node_ids)

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

### Phase 2: 이미지 에셋 관리

#### 2.1 기본 아바타 이미지 세트 준비

**디렉토리**: `frontend/public/avatars/`

```
frontend/public/avatars/
├── common/
│   ├── default-1.png
│   ├── default-2.png
│   └── default-3.png
├── rare/
│   ├── rare-1.png
│   └── rare-2.png
├── epic/
│   ├── epic-1.png
│   └── epic-2.png
└── legendary/
    ├── legendary-1.png
    └── legendary-2.png
```

**대안**:
- **AI 생성 아바타**: DALL-E/Midjourney로 Pokemon 스타일 캐릭터 생성
- **아이콘 라이브러리**: Heroicons, Lucide Icons로 Fallback
- **사용자 업로드**: S3/Cloudinary에 업로드 기능 추가

#### 2.2 Avatar URL 생성 로직

**파일**: `apps/api/services/avatar_service.py`

```python
import random
from typing import Optional

class AvatarService:
    """Manages agent avatar assignment and generation"""

    @staticmethod
    def get_default_avatar_url(rarity: str, agent_id: str) -> str:
        """Get deterministic default avatar based on rarity and agent_id"""
        # Use agent_id hash to deterministically select avatar
        avatar_index = int(str(agent_id).split('-')[0], 16) % 3 + 1
        return f"/avatars/{rarity.lower()}/default-{avatar_index}.png"

    @staticmethod
    async def generate_ai_avatar(
        agent_name: str,
        taxonomy_scope: str,
        rarity: str
    ) -> Optional[str]:
        """Generate AI avatar using DALL-E/Stable Diffusion (Future)"""
        # TODO: Implement AI avatar generation
        # prompt = f"Pokemon-style character: {agent_name}, {taxonomy_scope}, {rarity} tier"
        # image_url = await dall_e_generate(prompt)
        # return image_url
        pass
```

### Phase 3: 프론트엔드 - 타입 & 컴포넌트

#### 3.1 타입 정의 업데이트

**파일**: `frontend/src/lib/api/types.ts`

```typescript
export const AgentCardDataSchema = z.object({
  // ... existing fields ...

  // 🆕 Image fields
  avatar_url: z.string().url().optional().nullable(),
  rarity: RaritySchema,  // Already exists
  character_description: z.string().max(500).optional().nullable(),
})

export type AgentCardData = z.infer<typeof AgentCardDataSchema>

// Helper function for default avatars
export function getDefaultAvatarUrl(rarity: Rarity, agentId: string): string {
  const hash = agentId.split('-')[0]
  const index = (parseInt(hash, 16) % 3) + 1
  return `/avatars/${rarity.toLowerCase()}/default-${index}.png`
}
```

#### 3.2 AgentCard 컴포넌트 업데이트

**파일**: `frontend/src/components/agent-card/AgentCard.tsx`

```tsx
import { getDefaultAvatarUrl } from '@/lib/api/types'

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent, onView, onDelete, className
}) {
  // Generate avatar URL with fallback
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

      {/* 🆕 CHARACTER IMAGE SECTION */}
      <div className="relative w-full h-48 mb-4 rounded-lg overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
        <img
          src={avatarUrl}
          alt={`${agent.name} character`}
          className="w-full h-full object-cover"
          onError={(e) => {
            // Fallback to emoji icon if image fails to load
            e.currentTarget.style.display = 'none'
            e.currentTarget.nextElementSibling?.classList.remove('hidden')
          }}
        />
        <div className="hidden flex items-center justify-center h-full text-6xl">
          {agent.rarity === 'Legendary' && '👑'}
          {agent.rarity === 'Epic' && '⚡'}
          {agent.rarity === 'Rare' && '💎'}
          {agent.rarity === 'Common' && '🤖'}
        </div>
      </div>

      {/* XP Progress */}
      <div className="mb-4">
        <ProgressBar ... />
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

#### 3.3 반응형 이미지 처리

**파일**: `frontend/src/components/agent-card/AgentAvatar.tsx` (새 파일)

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
          'flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200',
          className
        )}
        role="img"
        aria-label={`${agentName} avatar`}
      >
        <span className="text-6xl" role="img">
          {FALLBACK_ICONS[rarity]}
        </span>
      </div>
    )
  }

  return (
    <img
      src={avatarUrl}
      alt={`${agentName} character`}
      className={cn('w-full h-full object-cover', className)}
      onError={() => setImageError(true)}
      loading="lazy"
    />
  )
})
```

### Phase 4: 테스트 & 검증

#### 4.1 백엔드 API 테스트

**파일**: `tests/integration/test_agent_avatar_api.py`

```python
import pytest
from apps.api.schemas.agent_schemas import AgentResponse

async def test_agent_creation_with_avatar():
    """Test agent creation includes avatar_url"""
    response = await client.post("/agents/from-taxonomy", json={
        "name": "Test Agent",
        "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
        "avatar_url": "/avatars/common/default-1.png",
    })

    assert response.status_code == 201
    data = response.json()
    assert "avatar_url" in data
    assert data["rarity"] in ["Common", "Rare", "Epic", "Legendary"]

async def test_agent_list_includes_avatars():
    """Test agent list endpoint returns avatar URLs"""
    response = await client.get("/agents/search")

    assert response.status_code == 200
    agents = response.json()["agents"]
    for agent in agents:
        assert "avatar_url" in agent
        assert "rarity" in agent
```

#### 4.2 프론트엔드 컴포넌트 테스트

**파일**: `frontend/src/components/agent-card/__tests__/AgentCard.test.tsx`

```typescript
import { render, screen } from '@testing-library/react'
import { AgentCard } from '../AgentCard'
import type { AgentCardData } from '@/lib/api/types'

describe('AgentCard', () => {
  it('renders character avatar image', () => {
    const mockAgent: AgentCardData = {
      agent_id: '123e4567-e89b-12d3-a456-426614174000',
      name: 'Test Agent',
      avatar_url: '/avatars/epic/default-1.png',
      rarity: 'Epic',
      level: 5,
      // ... other fields
    }

    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

    const avatar = screen.getByAlt('Test Agent character')
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveAttribute('src', '/avatars/epic/default-1.png')
  })

  it('shows fallback icon when image fails to load', async () => {
    const mockAgent: AgentCardData = {
      agent_id: '123e4567-e89b-12d3-a456-426614174000',
      name: 'Test Agent',
      avatar_url: '/invalid-url.png',
      rarity: 'Legendary',
      level: 10,
      // ... other fields
    }

    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

    const avatar = screen.getByAlt('Test Agent character')
    fireEvent.error(avatar)  // Simulate image load error

    expect(screen.getByText('👑')).toBeInTheDocument()  // Legendary fallback
  })
})
```

---

## 📊 현재 스크린샷 vs 구현 목표

### 현재 (2025-11-07)
![Current Screenshot](../screenshots/FINAL_desktop_tall.png)

**누락된 요소**:
- ❌ 캐릭터 이미지
- ❌ 이미지 배경 그라데이션
- ❌ Rarity별 시각적 구분 (border만 있음)

### 구현 목표 (Pokemon 스타일)

```
┌────────────────────────────────┐
│ RAG Assistant Alpha      [EPIC]│
│ Level 8                  (보라)│
├────────────────────────────────┤
│  ╔════════════════════════╗    │
│  ║                        ║    │
│  ║    🧙‍♂️ [Character]      ║    │  ← 추가 필요
│  ║    (200x200px)         ║    │
│  ║                        ║    │
│  ╚════════════════════════╝    │
│  (Gradient Background)         │
├────────────────────────────────┤
│ [XP: 8500 / 10000 XP]          │
│ ████████████████░░░░ 85%       │
├────────────────────────────────┤
│ Docs    Queries   Quality      │
│ 1250    3420      92           │
├────────────────────────────────┤
│        [View] [Delete]         │
└────────────────────────────────┘
```

---

## 🚨 우선순위 & 타임라인 제안

### Critical Path (필수):
1. **Phase 1**: 백엔드 스키마 업데이트 (2-3일)
   - Database migration
   - API schema update
   - Default avatar assignment logic

2. **Phase 3**: 프론트엔드 UI 구현 (2-3일)
   - AgentAvatar component
   - Fallback icon system
   - Image error handling

3. **Phase 4**: 테스트 & 검증 (1일)
   - API integration test
   - Component unit tests
   - Visual regression test

### Optional (향상):
- **Phase 2**: AI 생성 아바타 시스템 (1-2주)
- **Advanced**: 사용자 커스텀 업로드 (1주)

---

## 🔗 관련 파일 참조

### 백엔드:
- `apps/api/schemas/agent_schemas.py:43-80` - AgentResponse 스키마
- `apps/api/routers/agent_router.py` - Agent CRUD endpoints
- `apps/api/agent_dao.py` - Agent database operations
- `apps/api/database.py` - Agent ORM model (확인 필요)

### 프론트엔드:
- `frontend/src/lib/api/types.ts:423-444` - AgentCardData 타입
- `frontend/src/components/agent-card/AgentCard.tsx:28-73` - AgentCard 컴포넌트
- `frontend/src/components/agent-card/RarityBadge.tsx` - Rarity badge 컴포넌트
- `frontend/src/app/page.tsx` - HomePage (Agent 카드 리스트)

### 스크린샷:
- `/home/a/projects/dt-rag-standalone/screenshots/FINAL_desktop_tall.png`

---

## ✅ 작업 체크리스트

```markdown
### 백엔드 개발
- [ ] Database migration: Add avatar_url, rarity columns
- [ ] Update AgentResponse schema with image fields
- [ ] Update Agent ORM model
- [ ] Implement default avatar assignment logic
- [ ] Update AgentDAO.create_agent()
- [ ] Update AgentDAO.get_agent() to include new fields
- [ ] API integration tests

### 이미지 에셋
- [ ] Design/acquire 12 default avatar images (3 per rarity)
- [ ] Create avatar directory structure
- [ ] Implement avatar selection algorithm (deterministic hash)
- [ ] (Optional) Set up AI avatar generation service
- [ ] (Optional) Set up image CDN/storage

### 프론트엔드 개발
- [ ] Update AgentCardDataSchema with avatar_url field
- [ ] Create AgentAvatar component with fallback
- [ ] Update AgentCard to include character image section
- [ ] Implement image error handling
- [ ] Add loading skeleton for images
- [ ] Component unit tests
- [ ] Visual regression tests

### 통합 테스트
- [ ] End-to-end test: Create agent → Verify avatar in UI
- [ ] Test fallback icons for each rarity
- [ ] Test image error scenarios
- [ ] Test responsive design (mobile/tablet/desktop)
- [ ] Cross-browser testing (Chrome/Firefox/Safari)

### 문서화
- [ ] Update API documentation (OpenAPI/Swagger)
- [ ] Update frontend component documentation
- [ ] Add avatar management guide to README
- [ ] Document default avatar selection algorithm
```

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-11-07
**작성자**: Alfred (MoAI-ADK SuperAgent)
**다음 리뷰**: Pokemon 카드 이미지 기능 구현 완료 후
