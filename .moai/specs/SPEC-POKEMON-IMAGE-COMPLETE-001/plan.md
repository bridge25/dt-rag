<!-- @DOC:POKEMON-IMAGE-IMPLEMENTATION-001 -->

# Pokemon 카드 캐릭터 이미지 완성 - 구현 계획

**SPEC ID**: POKEMON-IMAGE-COMPLETE-001
**버전**: v0.1.0
**작성일**: 2025-11-08
**업데이트**: 2025-11-08
**우선순위**: CRITICAL

---

## 📊 Executive Summary

### 구현 목표

Pokemon 스타일 Agent 카드에 **캐릭터 이미지 기능 추가** (Full-stack):
- **Backend**: Database migration, API schema 확장, 기본 아바타 할당 로직
- **Frontend**: 타입 정의 업데이트, AgentAvatar 컴포넌트 생성, AgentCard 레이아웃 수정
- **Assets**: 12개 기본 아바타 이미지 (Rarity별 3개씩)

### 현재 상태

- ❌ 백엔드 API에 이미지 필드 없음 (`avatar_url`, `rarity`)
- ❌ 프론트엔드 타입에 이미지 필드 없음
- ❌ AgentCard 컴포넌트에 이미지 렌더링 로직 없음
- ❌ 기본 아바타 에셋 없음

### 완성 후 상태 (v0.0.2 기준)

- ✅ Backend: `avatar_url`, `rarity`, `character_description` 컬럼 추가
- ✅ Frontend: AgentCardAvatar 컴포넌트, Lucide Icons 기반 Fallback 시스템
- ⚠️ Assets: PNG 이미지 대신 Lucide Icons 사용 (설계 변경)
- ✅ Tests: Backend migration tests (6개), Pydantic schema tests (9개)

### 목표 상태 (v0.1.0)

- 🎯 Backend: Avatar Service 구현 + Agent DAO 자동 할당 로직
- 🎯 Frontend: 기존 컴포넌트 활용 (추가 수정 불필요)
- 🎯 Tests: E2E 통합 테스트 추가, 커버리지 85% 달성

---

## 🗺️ 구현 단계 (Priority-based Milestones)

### Phase 1: Backend Core (PRIMARY GOAL)

**목표**: Database 스키마 및 API 응답 구조 확장

#### 1.1 Database Migration
- **파일**: `alembic/versions/XXXX_add_agent_avatar_fields.py`
- **작업**:
  - `agents` 테이블에 3개 컬럼 추가:
    - `avatar_url` (VARCHAR 500, nullable)
    - `rarity` (VARCHAR 20, nullable, default='Common')
    - `character_description` (TEXT, nullable)
  - Migration script 생성 및 테스트
- **완료 기준**:
  - `alembic upgrade head` 성공 (로컬 DB)
  - 기존 Agent 데이터 영향 없음 (nullable 컬럼)

#### 1.2 Pydantic Schema Update
- **파일**: `apps/api/schemas/agent_schemas.py`
- **작업**:
  - `Rarity` Literal 타입 추가 (`Common|Rare|Epic|Legendary`)
  - `AgentResponse`에 3개 필드 추가:
    - `avatar_url: Optional[str]`
    - `rarity: Rarity = "Common"`
    - `character_description: Optional[str]`
- **완료 기준**:
  - OpenAPI schema 업데이트 확인 (`/docs`)
  - 타입 힌트 에러 없음 (mypy/pyright)

#### 1.3 Avatar Service 구현
- **파일**: `apps/api/services/avatar_service.py` (새 파일)
- **작업**:
  - `AvatarService` 클래스 생성:
    - `get_default_avatar_url(rarity, agent_id)` - 결정론적 아바타 할당
    - `generate_ai_avatar()` - 스켈레톤 함수 (향후 확장)
- **알고리즘**:
  ```python
  avatar_index = int(agent_id.split('-')[0], 16) % 3 + 1
  return f"/avatars/{rarity.lower()}/default-{avatar_index}.png"
  ```
- **완료 기준**:
  - 같은 `agent_id` → 항상 같은 아바타 URL (deterministic)
  - Rarity별 3개 아바타 고르게 분배

#### 1.4 Agent DAO Update
- **파일**: `apps/api/agent_dao.py`
- **작업**:
  - `create_agent()` 함수 수정:
    - `rarity` 파라미터 추가 (optional)
    - `calculate_initial_rarity()` 호출 (taxonomy 노드 수 기반)
    - `AvatarService.get_default_avatar_url()` 호출
  - `calculate_initial_rarity()` 함수 추가:
    - 10+ 노드 → Legendary
    - 5-9 노드 → Epic
    - 2-4 노드 → Rare
    - 1 노드 → Common
- **완료 기준**:
  - 새 Agent 생성 시 자동으로 `avatar_url`, `rarity` 할당
  - 기존 API 엔드포인트 호환성 유지

---

### Phase 2: Frontend Core (PRIMARY GOAL)

**목표**: 타입 정의 및 UI 컴포넌트 구현

#### 2.1 Type Definition Update
- **파일**: `frontend/src/lib/api/types.ts`
- **작업**:
  - `AgentCardDataSchema`에 필드 추가:
    - `avatar_url: z.string().url().optional().nullable()`
    - `character_description: z.string().max(500).optional().nullable()`
  - `getDefaultAvatarUrl()` 헬퍼 함수 추가 (백엔드와 동일 알고리즘)
- **완료 기준**:
  - Zod 파싱 에러 없음
  - TypeScript 타입 체크 통과

#### 2.2 AgentAvatar Component
- **파일**: `frontend/src/components/agent-card/AgentAvatar.tsx` (새 파일)
- **작업**:
  - Props: `avatarUrl`, `agentName`, `rarity`, `className`
  - Fallback 아이콘 시스템:
    - Legendary: 👑
    - Epic: ⚡
    - Rare: 💎
    - Common: 🤖
  - 이미지 로드 실패 시 자동 Fallback (`onError` 핸들러)
  - 접근성: `alt` text, `aria-label`, `role="img"`
- **완료 기준**:
  - 이미지 로드 성공 시 정상 표시
  - 이미지 404 에러 시 Fallback 아이콘 표시
  - `loading="lazy"` 적용

#### 2.3 AgentCard Component Update
- **파일**: `frontend/src/components/agent-card/AgentCard.tsx`
- **작업**:
  - `AgentAvatar` 컴포넌트 import 및 삽입
  - Header와 XP Progress 사이에 이미지 섹션 추가:
    - 크기: `h-48` (192px, 약 200px)
    - 스타일: `rounded-lg`, gradient background
  - `avatar_url` Fallback 로직:
    - `agent.avatar_url || getDefaultAvatarUrl(agent.rarity, agent.agent_id)`
- **완료 기준**:
  - Pokemon 카드 레이아웃 완성 (Header → Image → XP → Stats → Actions)
  - 반응형 디자인 유지 (mobile/tablet/desktop)

---

### Phase 3: Asset Management (SECONDARY GOAL)

**목표**: 기본 아바타 이미지 에셋 준비

#### 3.1 Avatar Directory 구조 생성
- **디렉토리**: `frontend/public/avatars/`
- **작업**:
  ```bash
  mkdir -p frontend/public/avatars/{common,rare,epic,legendary}
  ```
- **완료 기준**:
  - 4개 Rarity 디렉토리 생성 완료

#### 3.2 Avatar Image 획득 및 배치
- **작업**:
  - 12개 이미지 생성 또는 획득 (Rarity별 3개씩)
  - **옵션 1**: AI 생성 (DALL-E/Midjourney)
    - Prompt 예시: "Pokemon-style character, [rarity] tier, cute mascot, 200x200px, transparent background"
  - **옵션 2**: 아이콘 라이브러리 조합 (Heroicons, Lucide)
  - **옵션 3**: 수동 디자인 (Figma/Canva)
- **이미지 사양**:
  - 크기: 200x200px
  - 포맷: PNG (투명 배경) 또는 WebP
  - 용량: 각 50KB 이하
- **완료 기준**:
  - 12개 이미지 파일 배치 완료
  - 브라우저에서 `/avatars/epic/default-1.png` 접근 가능

---

### Phase 4: Backend Avatar Service (v0.1.0 NEW)

**목표**: Backend avatar 자동 할당 로직 완성

#### 4.1 Avatar Service 구현
- **파일**: `apps/api/services/avatar_service.py` (새 파일 생성)
- **작업**:
  - `AvatarService` 클래스 생성
  - `get_default_avatar_icon(rarity, agent_id)` 메서드 구현
    - Frontend `getDefaultAvatarIcon()`와 동일한 알고리즘
    - 결정론적 Lucide Icon 선택 (agent_id 해시 기반)
  - `calculate_initial_rarity(taxonomy_node_count)` 메서드 구현
    - 노드 수 기반 Rarity 계산 (1→Common, 2-4→Rare, 5-9→Epic, 10+→Legendary)
  - `RARITY_ICONS` 상수 정의 (Frontend와 동일한 매핑)
- **완료 기준**:
  - Unit tests 통과 (deterministic icon selection, rarity calculation)
  - Frontend icon 매핑과 100% 일치
  - 타입 힌트 에러 없음

**코드 예시**:
```python
# apps/api/services/avatar_service.py
from typing import Literal

Rarity = Literal["Common", "Rare", "Epic", "Legendary"]

RARITY_ICONS = {
    "Legendary": ["Crown", "Trophy", "Sparkles"],
    "Epic": ["Zap", "Star", "Flame"],
    "Rare": ["Gem", "Award", "Target"],
    "Common": ["User", "Circle", "Square"]
}

class AvatarService:
    @staticmethod
    def get_default_avatar_icon(rarity: Rarity, agent_id: str) -> str:
        """Get deterministic Lucide Icon name"""
        hash_value = int(str(agent_id).split('-')[0], 16)
        icon_index = hash_value % 3
        icons = RARITY_ICONS.get(rarity, RARITY_ICONS["Common"])
        return icons[icon_index]

    @staticmethod
    def calculate_initial_rarity(taxonomy_node_count: int) -> Rarity:
        """Calculate rarity based on taxonomy scope"""
        if taxonomy_node_count >= 10:
            return "Legendary"
        elif taxonomy_node_count >= 5:
            return "Epic"
        elif taxonomy_node_count >= 2:
            return "Rare"
        else:
            return "Common"
```

#### 4.2 Agent DAO 통합
- **파일**: `apps/api/agent_dao.py` (기존 파일 수정)
- **작업**:
  - `create_agent()` 함수 시그니처 확장:
    - `avatar_url: Optional[str] = None` 파라미터 추가
    - `rarity: Optional[str] = None` 파라미터 추가
  - Auto-assignment 로직 추가:
    ```python
    # Generate agent_id first
    agent_id = uuid4()

    # Calculate rarity if not provided
    if not rarity:
        rarity = AvatarService.calculate_initial_rarity(len(taxonomy_node_ids))

    # Assign Lucide Icon if avatar_url not provided
    if not avatar_url:
        avatar_url = AvatarService.get_default_avatar_icon(rarity, str(agent_id))
    ```
  - Agent 모델에 avatar_url, rarity 값 설정
- **완료 기준**:
  - Agent 생성 시 자동으로 avatar_url, rarity 할당
  - 기존 API 엔드포인트 호환성 유지 (Breaking change 없음)
  - Integration tests 통과

**코드 예시**:
```python
# apps/api/agent_dao.py (수정 부분)
from apps.api.services.avatar_service import AvatarService

async def create_agent(
    session: AsyncSession,
    name: str,
    taxonomy_node_ids: List[UUID],
    # ... existing params ...
    avatar_url: Optional[str] = None,
    rarity: Optional[str] = None,
) -> Agent:
    agent_id = uuid4()

    # Auto-calculate rarity
    if not rarity:
        rarity = AvatarService.calculate_initial_rarity(len(taxonomy_node_ids))

    # Auto-assign Lucide Icon
    if not avatar_url:
        avatar_url = AvatarService.get_default_avatar_icon(rarity, str(agent_id))

    agent = Agent(
        agent_id=agent_id,
        name=name,
        avatar_url=avatar_url,
        rarity=rarity,
        # ... existing fields ...
    )
    session.add(agent)
    await session.commit()
    return agent
```

#### 4.3 Backend Integration Tests
- **파일**: `tests/integration/test_agent_avatar_api.py` (새 파일 생성)
- **테스트 케이스**:
  1. **Agent 생성 시 avatar 자동 할당 테스트**
     - POST `/agents/from-taxonomy` → avatar_url, rarity 포함 확인
     - avatar_url이 유효한 Lucide Icon 이름인지 검증
  2. **Rarity 계산 로직 테스트**
     - 노드 수 1, 2, 5, 10에 대해 각각 Common, Rare, Epic, Legendary 확인
  3. **Deterministic icon 선택 테스트**
     - 같은 agent_id → 항상 같은 avatar_url
- **완료 기준**:
  - 모든 테스트 통과
  - Coverage 90% 이상 (avatar_service.py, agent_dao.py avatar 로직)

**테스트 코드 예시**:
```python
# tests/integration/test_agent_avatar_api.py
@pytest.mark.asyncio
async def test_agent_creation_auto_assigns_avatar(async_client: AsyncClient):
    response = await async_client.post("/agents/from-taxonomy", json={
        "name": "Test Agent",
        "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    })

    assert response.status_code == 201
    data = response.json()
    assert "avatar_url" in data
    assert data["avatar_url"] in ["User", "Circle", "Square"]  # Common icons
    assert data["rarity"] == "Common"

@pytest.mark.asyncio
async def test_agent_creation_rarity_calculation(async_client: AsyncClient):
    test_cases = [(1, "Common"), (2, "Rare"), (5, "Epic"), (10, "Legendary")]
    for node_count, expected_rarity in test_cases:
        taxonomy_ids = [str(uuid4()) for _ in range(node_count)]
        response = await async_client.post("/agents/from-taxonomy", json={
            "name": f"Test Agent {node_count}",
            "taxonomy_node_ids": taxonomy_ids,
        })
        assert response.json()["rarity"] == expected_rarity
```

---

### Phase 5: E2E Testing & Coverage (v0.1.0 NEW)

**목표**: 85% 테스트 커버리지 달성 및 E2E 통합 검증

#### 5.1 Frontend Component Tests
- **파일**: `frontend/src/components/agent-card/__tests__/AgentCard.test.tsx` (확장)
- **테스트 케이스 추가**:
  1. **Lucide Icon avatar 렌더링 테스트**
     - avatar_url이 Lucide Icon 이름일 때 (e.g., "Sparkles") 정상 렌더링 확인
  2. **Null avatar_url fallback 테스트**
     - avatar_url이 null일 때 기본 User icon 표시 확인
  3. **Deterministic icon 선택 테스트**
     - 같은 agent_id → 같은 icon 렌더링 (Frontend getDefaultAvatarIcon 검증)
- **완료 기준**:
  - 모든 테스트 통과 (Jest/Vitest)
  - Accessibility 검증 (role="img", aria-label)
  - Component coverage 85% 이상

**테스트 코드 예시**:
```typescript
// frontend/src/components/agent-card/__tests__/AgentCard.test.tsx
describe('AgentCard - Avatar Integration (v0.1.0)', () => {
  it('renders Lucide Icon avatar when avatar_url is icon name', () => {
    const mockAgent: AgentCardData = {
      agent_id: '123e4567-e89b-12d3-a456-426614174000',
      name: 'Test Agent',
      avatar_url: 'Sparkles',  // Lucide Icon name
      rarity: 'Legendary',
      level: 10,
      current_xp: 9500,
      next_level_xp: 10000,
      total_documents: 500,
      total_queries: 1500,
      quality_score: 95,
      status: 'active',
      created_at: '2025-11-08T00:00:00Z',
    }

    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

    const avatarSection = screen.getByTestId('agent-card-avatar')
    expect(avatarSection).toBeInTheDocument()

    const icon = screen.getByRole('img', { name: /sparkles/i })
    expect(icon).toBeInTheDocument()
  })

  it('falls back to User icon when avatar_url is null', () => {
    const mockAgent: AgentCardData = {
      ...mockAgentBase,
      avatar_url: null,
      rarity: 'Common',
    }

    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

    const icon = screen.getByRole('img', { name: /user/i })
    expect(icon).toBeInTheDocument()
  })
})
```

#### 5.2 Test Coverage Verification
- **목표**: 85% 이상 테스트 커버리지
- **실행 명령**:
  ```bash
  # Backend unit + integration tests
  pytest tests/unit/test_avatar_service.py tests/integration/test_agent_avatar_api.py \
    --cov=apps.api.services.avatar_service \
    --cov=apps.api.agent_dao \
    --cov-report=term \
    --cov-report=html

  # Frontend component tests
  npm test -- AgentCard.test.tsx AgentCardAvatar.test.tsx --coverage

  # Expected Coverage:
  # - apps/api/services/avatar_service.py: 90%+
  # - apps/api/agent_dao.py (avatar logic): 85%+
  # - frontend/src/components/agent-card/: 85%+
  ```
- **완료 기준**:
  - Backend coverage ≥ 85%
  - Frontend coverage ≥ 85%
  - Coverage report 생성 (HTML)

#### 5.3 Integration Smoke Test
- **목표**: End-to-end 통합 검증 (Backend ↔ Frontend)
- **시나리오**:
  1. Backend에서 Agent 생성 (POST `/agents/from-taxonomy`)
  2. API 응답에서 avatar_url, rarity 확인
  3. Frontend에서 동일한 Agent 조회 (GET `/agents/{id}`)
  4. AgentCard 컴포넌트에서 avatar 렌더링 확인
- **완료 기준**:
  - Backend와 Frontend icon 매핑 100% 일치
  - Deterministic icon 선택 동작 확인 (같은 agent_id → 같은 icon)

---

### Phase 6: Testing & Validation (FINAL GOAL)

**목표**: 품질 보증 및 회귀 방지 (기존 Phase 4를 Phase 6으로 이동)
- **도구**: Percy, Chromatic, 또는 Playwright screenshots
- **작업**:
  - Pokemon 카드 스크린샷 촬영 (Rarity별 4종)
  - Baseline 이미지 생성 및 비교
- **완료 기준**:
  - 디자인 의도와 일치
  - Tailwind CSS v4 호환성 확인

---

## 🛠️ 기술적 접근 방법

### Database Migration 전략

**안전한 스키마 변경**:
1. **Additive Change**: 새 컬럼만 추가 (기존 컬럼 수정 없음)
2. **Nullable Columns**: `nullable=True` 설정 (기존 Agent 데이터 보호)
3. **Default Values**: `rarity` 컬럼에 `server_default='Common'` 설정
4. **Rollback Plan**: `downgrade()` 함수 구현

**Migration 실행 순서**:
```bash
# 1. Migration script 생성
alembic revision --autogenerate -m "Add avatar fields to agents table"

# 2. Migration 검토 (생성된 script 확인)
cat alembic/versions/XXXX_add_agent_avatar_fields.py

# 3. 로컬 DB 적용
alembic upgrade head

# 4. Rollback 테스트
alembic downgrade -1
alembic upgrade head
```

### Deterministic Avatar Assignment

**알고리즘 설계 원칙**:
- **결정론적 (Deterministic)**: 같은 입력 → 항상 같은 출력
- **균등 분포 (Uniform Distribution)**: 3개 아바타 고르게 사용
- **Collision-Free**: UUID 해시 사용으로 충돌 방지

**구현 코드**:
```python
def get_default_avatar_url(rarity: str, agent_id: str) -> str:
    # UUID 첫 번째 세그먼트 (16진수)를 정수로 변환
    # 예: "550e8400-..." → 0x550e8400 → 1426937856
    hash_value = int(agent_id.split('-')[0], 16)

    # 3으로 나눈 나머지 + 1 → 1, 2, 3
    avatar_index = (hash_value % 3) + 1

    # /avatars/epic/default-2.png
    return f"/avatars/{rarity.lower()}/default-{avatar_index}.png"
```

**검증**:
```python
# Test determinism
agent_id = "550e8400-e29b-41d4-a716-446655440000"
url1 = get_default_avatar_url("Epic", agent_id)
url2 = get_default_avatar_url("Epic", agent_id)
assert url1 == url2  # Always same result
```

### Rarity Calculation Logic

**비즈니스 규칙**:
- Taxonomy 노드 범위가 넓을수록 높은 Rarity (Agent 전문성 반영)
- 초기 Rarity는 자동 할당, 향후 수동 조정 가능

**구현**:
```python
def calculate_initial_rarity(taxonomy_node_ids: List[UUID]) -> str:
    node_count = len(taxonomy_node_ids)
    if node_count >= 10:
        return "Legendary"  # 매우 광범위한 Agent
    elif node_count >= 5:
        return "Epic"       # 광범위한 Agent
    elif node_count >= 2:
        return "Rare"       # 중간 범위 Agent
    else:
        return "Common"     # 단일 도메인 Agent
```

### Fallback Icon System

**다층 방어 전략**:
1. **Primary**: `avatar_url` 필드 (백엔드 제공)
2. **Secondary**: `getDefaultAvatarUrl()` (클라이언트 계산)
3. **Tertiary**: Rarity별 이모지 아이콘 (이미지 로드 실패 시)

**React 컴포넌트 구조**:
```tsx
const AgentAvatar = ({ avatarUrl, rarity, agentName }) => {
  const [imageError, setImageError] = useState(false)

  if (imageError) {
    // Tertiary: Fallback 아이콘
    return <FallbackIcon rarity={rarity} />
  }

  // Primary/Secondary: 이미지
  return (
    <img
      src={avatarUrl}
      onError={() => setImageError(true)}
      alt={`${agentName} character`}
    />
  )
}
```

---

## 🎨 Architecture Design

### Backend Architecture

```
┌─────────────────────────────────────────┐
│         Agent Router                     │
│  POST /agents/from-taxonomy              │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Agent DAO                        │
│  - create_agent()                        │
│  - calculate_initial_rarity()            │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Avatar Service                      │
│  - get_default_avatar_url()              │
│  - generate_ai_avatar() (future)         │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Database (PostgreSQL)               │
│  agents table:                           │
│  - avatar_url (VARCHAR 500)              │
│  - rarity (VARCHAR 20)                   │
│  - character_description (TEXT)          │
└─────────────────────────────────────────┘
```

### Frontend Architecture

```
┌─────────────────────────────────────────┐
│          AgentCard                       │
│  - Orchestrates card layout              │
│  - Passes avatar data to AgentAvatar     │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│       AgentAvatar                        │
│  - Handles image loading                 │
│  - Fallback to emoji icons               │
│  - Accessibility (alt, aria-label)       │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Static Assets                       │
│  /public/avatars/{rarity}/default-X.png  │
└─────────────────────────────────────────┘
```

### Data Flow

```
[User Creates Agent]
        ↓
[Backend: calculate_initial_rarity(taxonomy_nodes)]
        ↓
[Backend: AvatarService.get_default_avatar_url(rarity, agent_id)]
        ↓
[Database: INSERT agent (avatar_url, rarity)]
        ↓
[API Response: AgentResponse {..., avatar_url, rarity}]
        ↓
[Frontend: Parse AgentCardData with Zod]
        ↓
[Frontend: Render AgentAvatar component]
        ↓
[Browser: Load image from /avatars/{rarity}/default-X.png]
        ↓
[If 404 → onError → Show Fallback Icon]
```

---

## ⚠️ 위험 요소 및 대응 계획

### 위험 1: 이미지 에셋 미준비로 인한 배포 지연

**위험도**: HIGH
**영향**: 모든 Agent 카드에서 Fallback 아이콘만 표시 (완성도 저하)

**대응 계획**:
1. **사전 준비**: Phase 3 (Asset Management)를 Phase 1, 2와 병렬 진행
2. **AI 생성 도구 활용**: DALL-E API를 통한 자동화된 아바타 생성 스크립트 작성
3. **임시 아이콘 사용**: Heroicons/Lucide로 임시 아바타 생성 (PNG 변환)
4. **배포 전 체크리스트**: 12개 이미지 파일 존재 여부 검증 스크립트

**검증 스크립트**:
```bash
#!/bin/bash
# check_avatars.sh
for rarity in common rare epic legendary; do
  for i in 1 2 3; do
    file="frontend/public/avatars/$rarity/default-$i.png"
    if [ ! -f "$file" ]; then
      echo "❌ Missing: $file"
      exit 1
    fi
  done
done
echo "✅ All 12 avatar images present"
```

### 위험 2: Backend/Frontend 타입 불일치

**위험도**: MEDIUM
**영향**: 런타임 에러, Zod 파싱 실패

**대응 계획**:
1. **타입 생성 자동화**: OpenAPI schema → TypeScript 타입 자동 생성 도구 사용 (openapi-typescript)
2. **통합 테스트**: API 응답을 Zod schema로 파싱하는 테스트 추가
3. **CI/CD 검증**: Pre-commit hook에서 타입 체크 (tsc, mypy)

**자동화 예시**:
```bash
# Generate TypeScript types from OpenAPI spec
npx openapi-typescript http://localhost:8000/openapi.json -o frontend/src/lib/api/generated-types.ts
```

### 위험 3: Database Migration 실패 (Production)

**위험도**: HIGH
**영향**: 서비스 중단, 데이터 손실 위험

**대응 계획**:
1. **Staging 환경 테스트**: Production과 동일한 데이터로 Migration 검증
2. **Rollback 시나리오**: `alembic downgrade` 테스트 및 문서화
3. **Blue-Green Deployment**: Migration 실행 중 트래픽 분산
4. **Backup**: Migration 전 DB 스냅샷 생성

**Rollback 절차**:
```bash
# Rollback command
alembic downgrade -1

# Verify rollback
psql -c "SELECT column_name FROM information_schema.columns WHERE table_name='agents';"
# avatar_url, rarity, character_description should be absent
```

### 위험 4: Avatar URL 결정론적 알고리즘 충돌

**위험도**: LOW
**영향**: 특정 아바타만 과다 사용 (분포 불균형)

**대응 계획**:
1. **단위 테스트**: 10,000개 UUID 샘플로 분포 검증 (각 아바타 33% ± 2%)
2. **Monitoring**: Agent 생성 시 아바타 할당 통계 수집
3. **알고리즘 개선**: 필요 시 SHA256 해시 사용으로 전환

**분포 검증 테스트**:
```python
def test_avatar_distribution():
    from uuid import uuid4
    from collections import Counter

    results = []
    for _ in range(10000):
        agent_id = str(uuid4())
        url = AvatarService.get_default_avatar_url("Epic", agent_id)
        results.append(url)

    counts = Counter(results)
    for avatar, count in counts.items():
        ratio = count / 10000
        assert 0.31 <= ratio <= 0.36  # 33% ± 3%
```

---

## 📦 Deliverables

### Code Deliverables

1. **Backend**:
   - ✅ `alembic/versions/XXXX_add_agent_avatar_fields.py`
   - ✅ `apps/api/schemas/agent_schemas.py` (updated)
   - ✅ `apps/api/services/avatar_service.py` (new)
   - ✅ `apps/api/agent_dao.py` (updated)

2. **Frontend**:
   - ✅ `frontend/src/lib/api/types.ts` (updated)
   - ✅ `frontend/src/components/agent-card/AgentAvatar.tsx` (new)
   - ✅ `frontend/src/components/agent-card/AgentCard.tsx` (updated)

3. **Assets**:
   - ✅ `frontend/public/avatars/{common,rare,epic,legendary}/default-{1,2,3}.png` (12 files)

4. **Tests**:
   - ✅ `tests/integration/test_agent_avatar_api.py` (new)
   - ✅ `frontend/src/components/agent-card/__tests__/AgentCard.test.tsx` (updated)

### Documentation Deliverables

1. **API Documentation**:
   - ✅ OpenAPI schema 업데이트 (`/docs` 페이지)
   - ✅ `AgentResponse` 스키마 필드 설명 추가

2. **Frontend Documentation**:
   - ✅ `AgentAvatar` 컴포넌트 JSDoc 주석
   - ✅ Storybook 스토리 추가 (optional)

3. **Migration Guide**:
   - ✅ Database migration 실행 가이드
   - ✅ Avatar 에셋 준비 가이드

---

## 🔧 Implementation Checklist

### Backend

- [ ] Database Migration 생성 (`alembic revision`)
- [ ] Migration 로컬 테스트 (`alembic upgrade head`)
- [ ] Rollback 테스트 (`alembic downgrade -1`)
- [ ] `AgentResponse` 스키마 업데이트 (3개 필드 추가)
- [ ] `AvatarService` 클래스 구현
- [ ] `calculate_initial_rarity()` 함수 구현
- [ ] `create_agent()` DAO 수정 (아바타 할당 로직)
- [ ] API 통합 테스트 작성 및 통과

### Frontend

- [ ] `AgentCardDataSchema` 업데이트 (Zod)
- [ ] `getDefaultAvatarUrl()` 헬퍼 함수 구현
- [ ] `AgentAvatar` 컴포넌트 생성
- [ ] Fallback 아이콘 시스템 구현
- [ ] `AgentCard` 레이아웃 수정 (이미지 섹션 추가)
- [ ] 접근성 검증 (alt text, aria-label)
- [ ] 컴포넌트 단위 테스트 작성 및 통과

### Assets

- [ ] Avatar 디렉토리 구조 생성 (`mkdir -p`)
- [ ] 12개 아바타 이미지 생성/획득
- [ ] 이미지 최적화 (50KB 이하)
- [ ] 브라우저 접근 테스트 (`http://localhost:3000/avatars/epic/default-1.png`)

### Testing

- [ ] Backend API 테스트 (pytest)
- [ ] Frontend 컴포넌트 테스트 (Jest/Vitest)
- [ ] E2E 테스트 (Playwright/Cypress)
- [ ] Visual regression 테스트 (Percy/Chromatic)
- [ ] Coverage 85% 이상 확인

### Documentation

- [ ] OpenAPI schema 업데이트
- [ ] Migration 실행 가이드 작성
- [ ] Avatar 에셋 준비 가이드 작성
- [ ] `AgentAvatar` 컴포넌트 문서화

---

## 🚀 다음 단계 (After Implementation)

### 1. Phase 1 완료 후
- Database migration 실행 (Production)
- API 응답 검증 (`/agents/search` 엔드포인트)

### 2. Phase 2 완료 후
- 프론트엔드 빌드 및 배포
- Agent 카드 UI 검증 (스크린샷 촬영)

### 3. Phase 3 완료 후
- 12개 아바타 이미지 CDN 업로드 (optional)
- 이미지 로드 성능 모니터링

### 4. Phase 4 완료 후
- `/alfred:3-sync` 실행 (문서 동기화)
- SPEC status: `draft` → `completed`
- GitHub Issue 종료 (`.moai/issues/POKEMON_CARD_IMAGE_MISSING.md` 참조)

---

**문서 버전**: v0.0.1
**최종 업데이트**: 2025-11-08
**작성자**: @spec-builder (MoAI-ADK Agent)
