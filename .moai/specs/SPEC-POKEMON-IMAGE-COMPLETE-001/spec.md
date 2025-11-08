---
id: POKEMON-IMAGE-COMPLETE-001
version: 0.0.1
status: draft
created: 2025-11-08
updated: 2025-11-08
author: @Goos
priority: critical
category: feature
labels:
  - pokemon-card
  - agent-avatar
  - fullstack
  - ui-enhancement
related_specs:
  - AGENT-CARD-001
scope:
  packages:
    - apps/api/schemas
    - apps/api/database
    - frontend/src/components/agent-card
    - frontend/src/lib/api
  files:
    - apps/api/schemas/agent_schemas.py
    - frontend/src/components/agent-card/AgentCard.tsx
    - frontend/src/lib/api/types.ts
---

<!-- @SPEC:POKEMON-IMAGE-COMPLETE-001 -->

# Pokemon 스타일 Agent 카드 캐릭터 이미지 완성 (Full-stack)

## HISTORY

### v0.0.1 - INITIAL (2025-11-08)
- 초기 SPEC 작성
- 사용자 명시적 요청 분석: Pokemon 스타일 캐릭터 이미지 기능 미구현 확인
- Full-stack 범위 정의: Backend (DB, API, Schema) + Frontend (Component, Type, Asset)
- `.moai/issues/POKEMON_CARD_IMAGE_MISSING.md` 상세 분석 기반 요구사항 도출

---

## Environment

### 시스템 컨텍스트

**현재 상황**:
- Agent 카드는 Pokemon 스타일로 디자인되었으나, **캐릭터 이미지 기능이 전체 스택에서 완전히 누락**
- 사용자는 프론트엔드 개발 당시 "pokemon 스타일로 캐릭터 이미지도 카드안에 삽입되게 주문"했으나 미구현
- 현재 카드 구조: Header (Name, Rarity Badge) → XP Progress → Stats → Actions
- **누락된 영역**: Header와 XP Progress 사이의 캐릭터 이미지 섹션 (200x200px 권장)

**기술 스택**:
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Alembic (PostgreSQL)
- **Frontend**: React 18, TypeScript, Tailwind CSS v4, Zod validation
- **Asset Management**: Static files (`/public/avatars/`), 향후 CDN 확장 가능

**관련 파일 (현재 구현)**:
- Backend: `apps/api/schemas/agent_schemas.py` (AgentResponse 스키마)
- Frontend: `frontend/src/lib/api/types.ts` (AgentCardDataSchema)
- Component: `frontend/src/components/agent-card/AgentCard.tsx`
- Issue Analysis: `.moai/issues/POKEMON_CARD_IMAGE_MISSING.md`

### 사용자 및 이해관계자

**주 사용자**:
- RAG 시스템 관리자 (Agent 카드 시각적 피드백 확인)
- 개발자 (Pokemon 스타일 카드 완성도 검증)

**비즈니스 가치**:
- 사용자 명시적 요청 이행 (완성도 향상)
- Pokemon 카드 디자인 완성 (Rarity별 시각적 구분 강화)
- Agent identity 시각화 (캐릭터 이미지로 Agent 개성 표현)

---

## Assumptions

### 설계 가정

1. **기본 아바타 이미지 제공**:
   - 초기 구현은 12개의 정적 아바타 이미지 사용 (Rarity별 3개씩)
   - AI 생성 아바타 기능은 향후 확장 범위로 분리

2. **Deterministic Avatar Assignment**:
   - Agent ID 해시값 기반으로 결정론적 아바타 할당 (같은 ID → 같은 아바타)
   - 사용자 커스텀 업로드 기능은 Phase 2로 연기

3. **Fallback Icon 시스템**:
   - 이미지 로드 실패 시 Rarity별 이모지 아이콘 표시 (👑/⚡/💎/🤖)
   - 접근성 고려 (alt text, aria-label 필수)

4. **Database Migration 안전성**:
   - 새 컬럼 추가 시 `nullable=True` (기존 Agent 데이터 영향 최소화)
   - Default 값 제공 (`rarity='Common'`)

5. **성능 고려**:
   - 이미지 lazy loading 적용
   - 향후 CDN/이미지 최적화는 별도 SPEC으로 분리

### 제약사항

- **Backend Migration**: Alembic 마이그레이션 실행 필수 (production DB 스키마 변경)
- **Image Assets**: 12개 아바타 이미지는 수동 준비 또는 AI 생성 필요
- **Type Safety**: Zod schema와 Pydantic schema 동기화 필수 (타입 불일치 방지)
- **Browser Compatibility**: 모던 브라우저 기준 (IE 제외)

---

## Requirements

### Ubiquitous Behaviors (항상 적용)

**@REQ:POKEMON-IMAGE-UB-001** - 모든 Agent는 아바타 이미지를 가져야 한다
- **Given**: Agent가 생성되거나 조회될 때
- **When**: 백엔드 API 응답이 반환될 때
- **Then**: 시스템은 `avatar_url` 필드를 포함해야 함 (null 허용, 하지만 기본값 제공)
- **Priority**: CRITICAL

**@REQ:POKEMON-IMAGE-UB-002** - 이미지 로드 실패 시 Fallback 제공
- **Given**: 아바타 이미지 URL이 유효하지 않거나 로드에 실패할 때
- **When**: 프론트엔드가 `<img>` 태그에서 `onError` 이벤트를 감지할 때
- **Then**: 시스템은 Rarity에 맞는 이모지 아이콘을 표시해야 함
- **Priority**: HIGH

**@REQ:POKEMON-IMAGE-UB-003** - Rarity 정보 동기화
- **Given**: Agent의 Rarity가 백엔드에서 관리될 때
- **When**: 프론트엔드가 Agent 데이터를 받을 때
- **Then**: 백엔드와 프론트엔드의 Rarity 값이 일치해야 함
- **Priority**: HIGH

### Event-driven Behaviors (특정 이벤트 시)

**@REQ:POKEMON-IMAGE-EB-001** - Agent 생성 시 기본 아바타 할당
- **Given**: 새로운 Agent가 생성될 때
- **When**: `create_agent()` 함수가 호출될 때
- **Then**: 시스템은 Agent ID 해시 기반으로 결정론적 기본 아바타 URL을 할당해야 함
- **Algorithm**: `avatar_index = int(agent_id.split('-')[0], 16) % 3 + 1`
- **Priority**: CRITICAL

**@REQ:POKEMON-IMAGE-EB-002** - AgentCard 렌더링 시 이미지 섹션 추가
- **Given**: AgentCard 컴포넌트가 렌더링될 때
- **When**: Header와 XP Progress 사이에 도달할 때
- **Then**: 시스템은 200x200px 크기의 캐릭터 이미지 영역을 렌더링해야 함
- **Style**: gradient background (`from-gray-100 to-gray-200`), rounded corners
- **Priority**: CRITICAL

**@REQ:POKEMON-IMAGE-EB-003** - Database Migration 실행
- **Given**: 새로운 컬럼이 필요할 때
- **When**: Alembic migration script가 실행될 때
- **Then**: 시스템은 `agents` 테이블에 `avatar_url`, `rarity`, `character_description` 컬럼을 추가해야 함
- **Constraints**: `nullable=True`, `rarity` default는 `'Common'`
- **Priority**: CRITICAL

### State-driven Behaviors (상태 의존)

**@REQ:POKEMON-IMAGE-SB-001** - Rarity별 기본 아바타 디렉토리 구조
- **Given**: 기본 아바타 에셋이 필요할 때
- **When**: 시스템이 아바타 URL을 생성할 때
- **Then**: `/public/avatars/{rarity}/{default-1|2|3}.png` 경로를 사용해야 함
- **Example**: `/avatars/epic/default-2.png`
- **Priority**: HIGH

**@REQ:POKEMON-IMAGE-SB-002** - AgentResponse Schema 확장
- **Given**: Agent API 응답이 반환될 때
- **When**: Pydantic 스키마가 직렬화될 때
- **Then**: `AgentResponse`는 다음 필드를 포함해야 함:
  - `avatar_url: Optional[str]` (max 500자)
  - `rarity: Literal["Common", "Rare", "Epic", "Legendary"]` (기본값: "Common")
  - `character_description: Optional[str]` (max 500자, 향후 AI 생성용)
- **Priority**: CRITICAL

**@REQ:POKEMON-IMAGE-SB-003** - AgentCardDataSchema 확장
- **Given**: 프론트엔드 타입 정의가 필요할 때
- **When**: Zod 스키마가 파싱될 때
- **Then**: `AgentCardDataSchema`는 다음 필드를 포함해야 함:
  - `avatar_url: z.string().url().optional().nullable()`
  - `character_description: z.string().max(500).optional().nullable()`
- **Note**: `rarity` 필드는 이미 존재
- **Priority**: CRITICAL

### Optional Features (권장 확장)

**@REQ:POKEMON-IMAGE-OF-001** - AI 생성 아바타 인프라 준비
- **Given**: 향후 AI 생성 아바타를 지원해야 할 때
- **When**: Phase 2 구현 시
- **Then**: `AvatarService.generate_ai_avatar()` 스켈레톤 함수를 포함해야 함 (DALL-E/Stable Diffusion 통합 준비)
- **Priority**: LOW (현재는 주석 처리)

**@REQ:POKEMON-IMAGE-OF-002** - 이미지 최적화 및 CDN 통합
- **Given**: 성능 개선이 필요할 때
- **When**: 사용자 수 증가로 이미지 전송 부하가 발생할 때
- **Then**: Cloudinary/AWS S3 + CloudFront 통합을 고려해야 함
- **Priority**: LOW (별도 SPEC 분리)

### Unwanted Behaviors (금지 사항)

**@REQ:POKEMON-IMAGE-UW-001** - 이미지 에셋 없이 배포 금지
- **Given**: 프로덕션 배포 시
- **When**: 12개 기본 아바타 이미지가 준비되지 않았을 때
- **Then**: 시스템은 배포를 차단하거나 경고를 발생해야 함
- **Reason**: 모든 Fallback 경로가 404 에러로 이어짐
- **Priority**: HIGH

**@REQ:POKEMON-IMAGE-UW-002** - Hard-coded 아바타 URL 금지
- **Given**: 아바타 URL을 생성할 때
- **When**: 백엔드 로직이 실행될 때
- **Then**: 시스템은 결정론적 알고리즘을 사용해야 하며, 특정 URL을 하드코딩하지 않아야 함
- **Example (금지)**: `avatar_url = "/avatars/epic/default-1.png"` (모든 Agent에 동일)
- **Priority**: MEDIUM

**@REQ:POKEMON-IMAGE-UW-003** - Rarity 값 프론트엔드 임의 생성 금지
- **Given**: Agent 데이터를 처리할 때
- **When**: 프론트엔드가 Rarity 값을 받을 때
- **Then**: 시스템은 백엔드에서 제공한 Rarity 값을 사용해야 하며, 클라이언트에서 임의로 생성하지 않아야 함
- **Current Issue**: 기존 코드에서 프론트엔드가 독자적으로 Rarity 추가 (백엔드와 불일치)
- **Priority**: HIGH

---

## Specifications

### Backend Implementation

#### 1. Database Migration

**파일**: `alembic/versions/XXXX_add_agent_avatar_fields.py`

**Migration Script**:
```python
"""Add avatar fields to agents table

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-11-08
"""

def upgrade():
    op.add_column('agents', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('agents', sa.Column('rarity', sa.String(20), nullable=True, server_default='Common'))
    op.add_column('agents', sa.Column('character_description', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('agents', 'character_description')
    op.drop_column('agents', 'rarity')
    op.drop_column('agents', 'avatar_url')
```

**실행 명령**:
```bash
cd /home/a/projects/dt-rag-standalone
alembic revision --autogenerate -m "Add avatar fields to agents table"
alembic upgrade head
```

#### 2. Pydantic Schema Update

**파일**: `apps/api/schemas/agent_schemas.py`

**변경사항**:
```python
from typing import Optional, Literal
from pydantic import BaseModel, Field

# Rarity enum 추가
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
        description="Character description for AI-generated avatars (future)"
    )
```

#### 3. Avatar Service

**파일**: `apps/api/services/avatar_service.py` (새 파일)

**구현**:
```python
class AvatarService:
    """Manages agent avatar assignment and generation"""

    @staticmethod
    def get_default_avatar_url(rarity: str, agent_id: str) -> str:
        """Get deterministic default avatar based on rarity and agent_id

        Args:
            rarity: Agent rarity tier (Common/Rare/Epic/Legendary)
            agent_id: UUID string

        Returns:
            Avatar URL path (e.g., "/avatars/epic/default-2.png")
        """
        # Use agent_id hash to deterministically select avatar (1-3)
        avatar_index = int(str(agent_id).split('-')[0], 16) % 3 + 1
        return f"/avatars/{rarity.lower()}/default-{avatar_index}.png"

    @staticmethod
    async def generate_ai_avatar(
        agent_name: str,
        taxonomy_scope: str,
        rarity: str
    ) -> Optional[str]:
        """Generate AI avatar using DALL-E/Stable Diffusion (Future)

        TODO: Implement AI avatar generation
        Prompt example: "Pokemon-style character: {agent_name}, {taxonomy_scope}, {rarity} tier"
        """
        pass
```

#### 4. Agent DAO Update

**파일**: `apps/api/agent_dao.py`

**변경사항** (create_agent 함수):
```python
async def create_agent(
    session: AsyncSession,
    name: str,
    taxonomy_node_ids: List[UUID],
    # ... existing params ...
    avatar_url: Optional[str] = None,
    rarity: Optional[str] = None,
) -> Agent:
    # Calculate initial rarity if not provided
    if not rarity:
        rarity = calculate_initial_rarity(taxonomy_node_ids)

    # Assign default avatar if not provided
    if not avatar_url:
        from apps.api.services.avatar_service import AvatarService
        avatar_url = AvatarService.get_default_avatar_url(rarity, str(uuid4()))

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

### Frontend Implementation

#### 5. Type Definition Update

**파일**: `frontend/src/lib/api/types.ts`

**변경사항**:
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

#### 6. AgentAvatar Component (새 파일)

**파일**: `frontend/src/components/agent-card/AgentAvatar.tsx`

**구현**:
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

#### 7. AgentCard Component Update

**파일**: `frontend/src/components/agent-card/AgentCard.tsx`

**변경사항**:
```tsx
import { getDefaultAvatarUrl } from '@/lib/api/types'
import { AgentAvatar } from './AgentAvatar'

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
      <div className="relative w-full h-48 mb-4 rounded-lg overflow-hidden">
        <AgentAvatar
          avatarUrl={avatarUrl}
          agentName={agent.name}
          rarity={agent.rarity}
          className="rounded-lg"
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

### Asset Management

#### 8. Avatar Image Asset 준비

**디렉토리 구조**: `frontend/public/avatars/`

```
frontend/public/avatars/
├── common/
│   ├── default-1.png
│   ├── default-2.png
│   └── default-3.png
├── rare/
│   ├── default-1.png
│   ├── default-2.png
│   └── default-3.png
├── epic/
│   ├── default-1.png
│   ├── default-2.png
│   └── default-3.png
└── legendary/
    ├── default-1.png
    ├── default-2.png
    └── default-3.png
```

**이미지 사양**:
- **크기**: 200x200px (정사각형)
- **포맷**: PNG (투명 배경 권장) 또는 WebP
- **용량**: 각 50KB 이하 (최적화 필수)
- **스타일**: Pokemon 카드 스타일 (만화풍 캐릭터)

**획득 방법**:
1. **AI 생성**: DALL-E/Midjourney로 Pokemon 스타일 캐릭터 생성
2. **아이콘 라이브러리**: Heroicons, Lucide Icons 조합
3. **수동 디자인**: Figma/Canva로 직접 제작

### Testing Requirements

#### 9. Backend Tests

**파일**: `tests/integration/test_agent_avatar_api.py`

**테스트 케이스**:
```python
async def test_agent_creation_with_default_avatar():
    """Test agent creation assigns default avatar"""
    response = await client.post("/agents/from-taxonomy", json={
        "name": "Test Agent",
        "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    })

    assert response.status_code == 201
    data = response.json()
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("/avatars/")
    assert data["rarity"] in ["Common", "Rare", "Epic", "Legendary"]

async def test_avatar_url_deterministic():
    """Test same agent_id produces same avatar"""
    agent_id = "550e8400-e29b-41d4-a716-446655440000"
    from apps.api.services.avatar_service import AvatarService

    url1 = AvatarService.get_default_avatar_url("Epic", agent_id)
    url2 = AvatarService.get_default_avatar_url("Epic", agent_id)

    assert url1 == url2  # Deterministic
```

#### 10. Frontend Tests

**파일**: `frontend/src/components/agent-card/__tests__/AgentCard.test.tsx`

**테스트 케이스**:
```typescript
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

## Traceability

### TAG Chain

**SPEC → CODE → TEST → DOC** 체인:

```
@SPEC:POKEMON-IMAGE-COMPLETE-001
  ↓
  ├─ @CODE:AGENT-AVATAR-SERVICE-001 (apps/api/services/avatar_service.py)
  ├─ @CODE:AGENT-SCHEMA-UPDATE-001 (apps/api/schemas/agent_schemas.py)
  ├─ @CODE:AGENT-MIGRATION-001 (alembic/versions/XXXX_add_agent_avatar_fields.py)
  ├─ @CODE:AGENT-CARD-AVATAR-001 (frontend/src/components/agent-card/AgentAvatar.tsx)
  ├─ @CODE:AGENT-CARD-UPDATE-001 (frontend/src/components/agent-card/AgentCard.tsx)
  ├─ @CODE:AGENT-TYPE-UPDATE-001 (frontend/src/lib/api/types.ts)
  ↓
  ├─ @TEST:AGENT-AVATAR-API-001 (tests/integration/test_agent_avatar_api.py)
  ├─ @TEST:AGENT-CARD-AVATAR-001 (frontend/src/components/agent-card/__tests__/AgentCard.test.tsx)
  ↓
  ├─ @DOC:POKEMON-CARD-IMAGE-ISSUE-001 (.moai/issues/POKEMON_CARD_IMAGE_MISSING.md)
  └─ @DOC:POKEMON-IMAGE-IMPLEMENTATION-001 (.moai/specs/SPEC-POKEMON-IMAGE-COMPLETE-001/plan.md)
```

### Related Documents

- `.moai/issues/POKEMON_CARD_IMAGE_MISSING.md` - 상세 분석 문서
- `.moai/specs/SPEC-AGENT-CARD-001/` - 기존 Agent 카드 SPEC (참조)
- `screenshots/FINAL_desktop_tall.png` - 현재 상태 스크린샷

---

## 완성 목표 (Pokemon 스타일 카드)

### 현재 구조 (이미지 누락)
```
┌────────────────────────────────┐
│ RAG Assistant Alpha      [EPIC]│
│ Level 8                        │
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

### 목표 구조 (이미지 추가)
```
┌────────────────────────────────┐
│ RAG Assistant Alpha      [EPIC]│
│ Level 8                  (보라)│
├────────────────────────────────┤
│  ╔════════════════════════╗    │
│  ║                        ║    │
│  ║    🧙‍♂️ [Character]      ║    │  ← 🆕 추가
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

**문서 버전**: v0.0.1
**최종 업데이트**: 2025-11-08
**작성자**: @spec-builder (MoAI-ADK Agent)
**다음 단계**: `/alfred:2-run SPEC-POKEMON-IMAGE-COMPLETE-001`
