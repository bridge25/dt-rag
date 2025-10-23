---
id: AGENT-GROWTH-005
version: 0.1.0
status: draft
created: 2025-10-13
updated: 2025-10-13
author: @sonheungmin
priority: high
category: feature
labels:
  - agent-growth
  - xp-system
  - leveling
  - gamification
  - feature-unlocking
scope:
  packages:
    - apps/api/services
    - apps/api/database
  files:
    - leveling_service.py
    - agent_dao.py
depends_on:
  - AGENT-GROWTH-001
  - AGENT-GROWTH-002
---

# @SPEC:AGENT-GROWTH-005: Agent XP/Leveling System Phase 2

## HISTORY

### v0.1.0 (2025-10-13)
- **INITIAL**: Agent XP/Leveling System Phase 2 명세 최초 작성
- **AUTHOR**: @sonheungmin
- **SCOPE**: LevelingService, XP 계산 알고리즘, Level Up 로직, Feature Unlocking 시스템
- **CONTEXT**: Phase 0-1 완료 후 에이전트 성장 게임화 시스템 완성
- **DEPENDENCIES**: SPEC-AGENT-GROWTH-001 (agents 테이블 level, current_xp 필드), SPEC-AGENT-GROWTH-002 (POST /agents/{id}/query API)
- **PHASE**: Phase 2 Gamification (2주 예상)

## Environment

- **Backend Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 12+ (agents 테이블 from Phase 0)
- **ORM**: SQLAlchemy 2.0+ (AsyncSession)
- **Python Version**: 3.9+
- **Phase 0-1 Prerequisites**:
  - agents 테이블 생성 완료 (level, current_xp, avg_faithfulness, avg_response_time_ms 필드 존재)
  - POST /agents/{id}/query API 구현 완료 (E-REQ-012 시점에 XP 트리거)
  - AgentDAO.update_agent() 메서드 존재
  - RAGAS 평가 시스템 통합 (faithfulness_score 0.0-1.0)

## Assumptions

1. **Phase 0-1 Complete**: agents 테이블 존재, POST /query API 동작 중
2. **Memento Framework**: avg_faithfulness 필드는 RAGAS 평가 결과로 업데이트됨
3. **XP Calculation Timing**: POST /agents/{id}/query 완료 시점에 XP 계산 트리거 (fire-and-forget 방식)
4. **Level Immutability**: level 필드는 LevelingService.check_level_up() 외에는 수정 불가 (application-level 제약)
5. **Feature Flags Integration**: features_config JSONB 필드는 기존 FEATURE_* flags와 통합 (FEATURE_DEBATE_MODE, FEATURE_MCP_TOOLS 등)
6. **Coverage Tracking**: agents.coverage_percent 필드는 CoverageMeterService에서 업데이트 (XP 계산에 coverage_delta 활용)
7. **Error Isolation**: XP 계산 실패 시 query 응답은 정상 반환 (XP는 부가 기능)

## EARS Requirements

### Ubiquitous Requirements (Core Leveling System)

**U-REQ-001**: System SHALL provide LevelingService class with methods: calculate_xp(agent_id, query_result), check_level_up(agent_id), unlock_features(agent_id, new_level).

**U-REQ-002**: System SHALL implement XP calculation formula:
```
XP = base_xp * (faithfulness_score * 0.5 + speed_bonus * 0.3 + coverage_delta * 0.2)
```
WHERE:
- base_xp = 10 (per successful query)
- faithfulness_score = 0.0-1.0 from RAGAS evaluation (agents.avg_faithfulness)
- speed_bonus = max(0, 1 - latency_seconds / 5.0) (5초 기준, 빠를수록 높음)
- coverage_delta = (new_coverage - old_coverage) / 100.0 (커버리지 개선 시 보너스, 음수 가능)

**U-REQ-003**: System SHALL define level thresholds as follows:
| Level | Min XP | Description |
|-------|--------|-------------|
| 1 | 0 | Beginner (basic retrieval) |
| 2 | 100 | Intermediate (debate mode unlocked) |
| 3 | 300 | Advanced (MCP tools unlocked) |
| 4 | 600 | Expert (soft Q-learning bandit unlocked) |
| 5 | 1000 | Master (all features + priority support) |

**U-REQ-004**: System SHALL define feature unlocking rules:
| Level | Unlocked Features | features_config |
|-------|-------------------|-----------------|
| 1 | Basic retrieval (hybrid search only) | {"debate": false, "tools": false, "bandit": false} |
| 2 | Debate mode | {"debate": true, "tools": false, "bandit": false} |
| 3 | MCP tools | {"debate": true, "tools": true, "bandit": false} |
| 4 | Soft Q-learning bandit | {"debate": true, "tools": true, "bandit": true} |
| 5 | All features + priority support | {"debate": true, "tools": true, "bandit": true, "priority": true} |

**U-REQ-005**: System SHALL provide AgentDAO.update_xp_and_level(agent_id, xp_delta, level) method for atomic updates of current_xp and level fields.

**U-REQ-006**: LevelingService.calculate_xp() SHALL return XPResult dataclass with fields: agent_id (str), xp_earned (float), breakdown (Dict[str, float]), total_xp (float), level_before (int), level_after (int).

**U-REQ-007**: XPResult.breakdown SHALL contain keys: "base_xp", "faithfulness_bonus", "speed_bonus", "coverage_bonus", "total".

**U-REQ-008**: LevelingService.check_level_up() SHALL return LevelUpResult dataclass with fields: agent_id (str), level_before (int), level_after (int), unlocked_features (List[str]).

**U-REQ-009**: System SHALL store XP thresholds in LEVEL_THRESHOLDS constant dictionary: {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}.

**U-REQ-010**: System SHALL store feature mapping in LEVEL_FEATURES constant dictionary: {1: {}, 2: {"debate": true}, 3: {"debate": true, "tools": true}, ...}.

### Event-driven Requirements (XP/Level Events)

**E-REQ-001**: WHEN POST /agents/{id}/query completes successfully, System SHALL call LevelingService.calculate_xp(agent_id, query_result) asynchronously (fire-and-forget).

**E-REQ-002**: WHEN LevelingService.calculate_xp() is invoked, System SHALL retrieve agent from database to get current_xp, avg_faithfulness, avg_response_time_ms, coverage_percent.

**E-REQ-003**: WHEN LevelingService.calculate_xp() computes XP, System SHALL calculate faithfulness_bonus = faithfulness_score * 0.5 * base_xp.

**E-REQ-004**: WHEN LevelingService.calculate_xp() computes XP, System SHALL calculate speed_bonus = max(0, 1 - latency_seconds / 5.0) * 0.3 * base_xp.

**E-REQ-005**: WHEN LevelingService.calculate_xp() computes XP, System SHALL calculate coverage_delta = (query_result.new_coverage - agent.coverage_percent) / 100.0 * 0.2 * base_xp.

**E-REQ-006**: WHEN LevelingService.calculate_xp() completes, System SHALL call AgentDAO.update_xp_and_level(agent_id, xp_earned) to increment current_xp.

**E-REQ-007**: WHEN AgentDAO.update_xp_and_level() is invoked, System SHALL update agents.current_xp and agents.updated_at in single transaction.

**E-REQ-008**: WHEN current_xp >= next level threshold, System SHALL call LevelingService.check_level_up(agent_id) automatically.

**E-REQ-009**: WHEN LevelingService.check_level_up() detects level increase, System SHALL update agents.level to new level value.

**E-REQ-010**: WHEN level increases, System SHALL call LevelingService.unlock_features(agent_id, new_level) to update agents.features_config.

**E-REQ-011**: WHEN LevelingService.unlock_features() is invoked, System SHALL merge new features into existing features_config JSONB field (preserve custom flags).

**E-REQ-012**: WHEN level up occurs, System SHALL update agents.updated_at timestamp automatically.

**E-REQ-013**: WHEN XP calculation fails (database error, invalid agent_id), System SHALL log error but NOT fail query response (isolation principle).

**E-REQ-014**: WHEN level up completes, System SHALL log event with format: "Agent {agent_id} leveled up: {old_level} -> {new_level}, unlocked: {features}".

**E-REQ-015**: WHEN agent reaches level 5 (max level), System SHALL NOT prevent further XP accumulation but level remains at 5.

### State-driven Requirements (Level State)

**S-REQ-001**: WHILE agent level=1, features_config SHALL have {"debate": false, "tools": false, "bandit": false}.

**S-REQ-002**: WHILE agent level=2, features_config SHALL have {"debate": true, "tools": false, "bandit": false}.

**S-REQ-003**: WHILE agent level=3, features_config SHALL have {"debate": true, "tools": true, "bandit": false}.

**S-REQ-004**: WHILE agent level=4, features_config SHALL have {"debate": true, "tools": true, "bandit": true}.

**S-REQ-005**: WHILE agent level=5, features_config SHALL have {"debate": true, "tools": true, "bandit": true, "priority": true}.

**S-REQ-006**: WHILE agent's current_xp is between level thresholds, level SHALL remain unchanged until next threshold reached.

**S-REQ-007**: WHILE XP calculation is in progress, POST /agents/{id}/query response SHALL NOT wait (async fire-and-forget).

**S-REQ-008**: WHILE coverage_delta is negative (coverage decreased), System SHALL apply negative coverage_bonus (XP penalty).

**S-REQ-009**: WHILE faithfulness_score is 0.0 (RAGAS not available), System SHALL use 0.0 for faithfulness_bonus (no penalty to query, just no bonus).

**S-REQ-010**: WHILE agent has custom features_config values (e.g., "custom_flag": true), LevelingService.unlock_features() SHALL preserve them during merge.

### Optional Features (Future Enhancements)

**O-REQ-001**: WHERE user requests leaderboard, GET /agents/leaderboard MAY return top N agents sorted by current_xp DESC.

**O-REQ-002**: WHERE user requests XP history, xp_history table MAY track XP changes over time with columns: agent_id, xp_earned, query_id, timestamp.

**O-REQ-003**: WHERE user requests manual XP adjustment, POST /agents/{id}/xp/adjust MAY allow admin to add/subtract XP (requires admin role).

**O-REQ-004**: WHERE user requests level-up simulation, POST /agents/{id}/level-up-test MAY simulate level up without database changes (dry-run mode).

**O-REQ-005**: WHERE agent queries fail frequently, System MAY implement XP decay (lose XP over time if inactive).

### Constraints (Performance & Data Integrity)

**C-REQ-001**: XP calculation SHALL complete within 500ms (95th percentile).

**C-REQ-002**: Level up check SHALL execute after every successful query (no batching, immediate feedback).

**C-REQ-003**: XP formula SHALL be deterministic (no randomness, same inputs = same XP).

**C-REQ-004**: features_config updates SHALL be atomic (within same transaction as level update).

**C-REQ-005**: Level field SHALL be immutable except via LevelingService.check_level_up() (enforce via application-level validation).

**C-REQ-006**: XP calculation SHALL NOT block query response (fire-and-forget, use asyncio.create_task() or background task queue).

**C-REQ-007**: AgentDAO.update_xp_and_level() SHALL use single UPDATE statement with SET current_xp = current_xp + :xp_delta for race condition safety.

**C-REQ-008**: LevelingService methods SHALL use AsyncSession for non-blocking database operations.

**C-REQ-009**: XPResult and LevelUpResult dataclasses SHALL be JSON-serializable for logging and API responses.

**C-REQ-010**: Level thresholds SHALL be immutable constants (no dynamic threshold changes).

**C-REQ-011**: Feature mapping SHALL be immutable constants (no runtime feature rule changes).

**C-REQ-012**: XP calculation SHALL handle missing avg_faithfulness or avg_response_time_ms gracefully (default to 0.0).

**C-REQ-013**: Coverage delta calculation SHALL handle None coverage_percent (new agent) by using 0.0 as old_coverage.

**C-REQ-014**: LevelingService SHALL log all XP events (calculate, level_up, unlock) at INFO level for observability.

**C-REQ-015**: XP calculation failure SHALL NOT propagate to caller (catch all exceptions, log, return None or default XPResult).

## XP Calculation Algorithm

### Detailed Formula Breakdown

**Step 1: Retrieve Agent Metrics**
```python
agent = await AgentDAO.get_agent(agent_id)
current_xp = agent.current_xp
old_coverage = agent.coverage_percent or 0.0
faithfulness = agent.avg_faithfulness or 0.0
avg_latency_ms = agent.avg_response_time_ms or 0.0
```

**Step 2: Calculate Component Bonuses**
```python
base_xp = 10.0

# Faithfulness Bonus (50% weight)
faithfulness_bonus = faithfulness * 0.5 * base_xp

# Speed Bonus (30% weight, 5초 기준)
latency_seconds = avg_latency_ms / 1000.0
speed_bonus = max(0, 1 - latency_seconds / 5.0) * 0.3 * base_xp

# Coverage Bonus (20% weight)
new_coverage = query_result.coverage_percent  # from query result
coverage_delta = (new_coverage - old_coverage) / 100.0
coverage_bonus = coverage_delta * 0.2 * base_xp
```

**Step 3: Compute Total XP**
```python
total_xp_earned = faithfulness_bonus + speed_bonus + coverage_bonus
# Note: base_xp is implicit in each component

# Example:
# faithfulness = 0.85 → 0.85 * 0.5 * 10 = 4.25
# latency = 2000ms → (1 - 2/5) * 0.3 * 10 = 1.8
# coverage_delta = 0.05 (5% increase) → 0.05 * 0.2 * 10 = 0.1
# total_xp_earned = 4.25 + 1.8 + 0.1 = 6.15
```

**Step 4: Update Agent XP**
```python
await AgentDAO.update_xp_and_level(agent_id, xp_delta=total_xp_earned)
```

**Step 5: Check Level Up**
```python
updated_agent = await AgentDAO.get_agent(agent_id)
if updated_agent.current_xp >= LEVEL_THRESHOLDS[updated_agent.level + 1]:
    await LevelingService.check_level_up(agent_id)
```

## Level Threshold Table

| Level | Min XP | Max XP | XP Range | Feature Tier | Description |
|-------|--------|--------|----------|--------------|-------------|
| 1 | 0 | 99 | 100 XP | Beginner | Basic hybrid search only |
| 2 | 100 | 299 | 200 XP | Intermediate | + Debate Mode |
| 3 | 300 | 599 | 300 XP | Advanced | + MCP Tools |
| 4 | 600 | 999 | 400 XP | Expert | + Soft Q-learning Bandit |
| 5 | 1000 | ∞ | unlimited | Master | + Priority Support |

**XP Growth Pattern**:
- Level 1→2: 100 XP (10 queries @ avg 10 XP)
- Level 2→3: 200 XP (20 queries @ avg 10 XP)
- Level 3→4: 300 XP (30 queries @ avg 10 XP)
- Level 4→5: 400 XP (40 queries @ avg 10 XP)
- **Total to Max Level**: 1000 XP (~100 queries @ avg 10 XP)

## Feature Unlocking Mapping

### Level 1: Beginner (XP 0-99)
**Unlocked Features**:
- Hybrid Search (BM25 + Vector)
- Basic retrieval with top_k=5

**features_config**:
```json
{
  "debate": false,
  "tools": false,
  "bandit": false
}
```

### Level 2: Intermediate (XP 100-299)
**Unlocked Features**:
- All Level 1 features
- Multi-Agent Debate Mode (FEATURE_DEBATE_MODE)

**features_config**:
```json
{
  "debate": true,
  "tools": false,
  "bandit": false
}
```

### Level 3: Advanced (XP 300-599)
**Unlocked Features**:
- All Level 2 features
- MCP Tools (FEATURE_MCP_TOOLS)
- Tool whitelist policy (FEATURE_TOOLS_POLICY)

**features_config**:
```json
{
  "debate": true,
  "tools": true,
  "bandit": false
}
```

### Level 4: Expert (XP 600-999)
**Unlocked Features**:
- All Level 3 features
- Soft Q-learning Bandit (FEATURE_SOFT_Q_BANDIT)
- Adaptive retrieval strategy

**features_config**:
```json
{
  "debate": true,
  "tools": true,
  "bandit": true
}
```

### Level 5: Master (XP 1000+)
**Unlocked Features**:
- All Level 4 features
- Priority support flag
- Advanced meta-planning

**features_config**:
```json
{
  "debate": true,
  "tools": true,
  "bandit": true,
  "priority": true
}
```

## Integration Points

### 1. POST /agents/{id}/query Hook

**Location**: `apps/api/routers/agent_router.py` → `query_agent()` 함수

**Implementation**:
```python
@router.post("/{agent_id}/query", response_model=QueryResponse)
async def query_agent(
    agent_id: UUID4,
    request: QueryRequest,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
) -> QueryResponse:
    # Execute query
    results = await SearchDAO.hybrid_search(...)

    # Build response
    response = QueryResponse(...)

    # Fire-and-forget XP calculation (non-blocking)
    asyncio.create_task(
        LevelingService.calculate_xp_and_level_up(
            session=session,
            agent_id=str(agent_id),
            query_result=results
        )
    )

    return response
```

### 2. LevelingService Architecture

**File**: `apps/api/services/leveling_service.py`

**Class Definition**:
```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

# Constants
LEVEL_THRESHOLDS = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}
LEVEL_FEATURES = {
    1: {"debate": False, "tools": False, "bandit": False},
    2: {"debate": True, "tools": False, "bandit": False},
    3: {"debate": True, "tools": True, "bandit": False},
    4: {"debate": True, "tools": True, "bandit": True},
    5: {"debate": True, "tools": True, "bandit": True, "priority": True},
}

@dataclass
class XPResult:
    agent_id: str
    xp_earned: float
    breakdown: Dict[str, float]
    total_xp: float
    level_before: int
    level_after: int

@dataclass
class LevelUpResult:
    agent_id: str
    level_before: int
    level_after: int
    unlocked_features: List[str]

class LevelingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_xp(
        self,
        agent_id: str,
        query_result: Dict
    ) -> Optional[XPResult]:
        """Calculate XP from query result."""
        try:
            agent = await AgentDAO.get_agent(self.session, agent_id)
            if not agent:
                return None

            # Calculate component bonuses
            base_xp = 10.0
            faithfulness = agent.avg_faithfulness or 0.0
            latency_ms = query_result.get("latency_ms", 0.0)
            new_coverage = query_result.get("coverage_percent", agent.coverage_percent or 0.0)
            old_coverage = agent.coverage_percent or 0.0

            faithfulness_bonus = faithfulness * 0.5 * base_xp
            speed_bonus = max(0, 1 - (latency_ms / 1000.0) / 5.0) * 0.3 * base_xp
            coverage_delta = (new_coverage - old_coverage) / 100.0
            coverage_bonus = coverage_delta * 0.2 * base_xp

            total_xp_earned = faithfulness_bonus + speed_bonus + coverage_bonus

            # Update XP
            await AgentDAO.update_xp_and_level(self.session, agent_id, total_xp_earned)

            breakdown = {
                "base_xp": base_xp,
                "faithfulness_bonus": faithfulness_bonus,
                "speed_bonus": speed_bonus,
                "coverage_bonus": coverage_bonus,
                "total": total_xp_earned
            }

            return XPResult(
                agent_id=agent_id,
                xp_earned=total_xp_earned,
                breakdown=breakdown,
                total_xp=agent.current_xp + total_xp_earned,
                level_before=agent.level,
                level_after=agent.level  # Will be updated by check_level_up
            )
        except Exception as e:
            logger.error(f"XP calculation failed for agent {agent_id}: {e}", exc_info=True)
            return None

    async def check_level_up(self, agent_id: str) -> Optional[LevelUpResult]:
        """Check and execute level up if threshold reached."""
        try:
            agent = await AgentDAO.get_agent(self.session, agent_id)
            if not agent:
                return None

            current_level = agent.level
            current_xp = agent.current_xp

            # Determine new level
            new_level = current_level
            for level, threshold in sorted(LEVEL_THRESHOLDS.items()):
                if current_xp >= threshold:
                    new_level = level

            if new_level > current_level:
                # Update level
                await AgentDAO.update_agent(self.session, agent_id, level=new_level)

                # Unlock features
                unlocked = await self.unlock_features(agent_id, new_level)

                logger.info(f"Agent {agent_id} leveled up: {current_level} -> {new_level}, unlocked: {unlocked}")

                return LevelUpResult(
                    agent_id=agent_id,
                    level_before=current_level,
                    level_after=new_level,
                    unlocked_features=unlocked
                )

            return None
        except Exception as e:
            logger.error(f"Level up check failed for agent {agent_id}: {e}", exc_info=True)
            return None

    async def unlock_features(self, agent_id: str, new_level: int) -> List[str]:
        """Unlock features for new level."""
        try:
            agent = await AgentDAO.get_agent(self.session, agent_id)
            if not agent:
                return []

            new_features = LEVEL_FEATURES.get(new_level, {})
            existing_config = agent.features_config or {}

            # Merge (preserve custom flags)
            merged_config = {**existing_config, **new_features}

            await AgentDAO.update_agent(self.session, agent_id, features_config=merged_config)

            unlocked = [k for k, v in new_features.items() if v and not existing_config.get(k)]
            return unlocked
        except Exception as e:
            logger.error(f"Feature unlock failed for agent {agent_id}: {e}", exc_info=True)
            return []

    async def calculate_xp_and_level_up(
        self,
        session: AsyncSession,
        agent_id: str,
        query_result: Dict
    ):
        """Combined XP calculation and level up check (fire-and-forget)."""
        try:
            xp_result = await self.calculate_xp(agent_id, query_result)
            if xp_result:
                await self.check_level_up(agent_id)
        except Exception as e:
            logger.error(f"XP/Level up pipeline failed for agent {agent_id}: {e}", exc_info=True)
```

### 3. AgentDAO Extension

**File**: `apps/api/database.py` (extend existing AgentDAO)

**New Method**:
```python
@staticmethod
async def update_xp_and_level(
    session: AsyncSession,
    agent_id: UUID,
    xp_delta: float,
    level: Optional[int] = None
) -> Agent:
    """Atomically update XP and optionally level."""
    stmt = (
        update(Agent)
        .where(Agent.agent_id == agent_id)
        .values(
            current_xp=Agent.current_xp + xp_delta,
            updated_at=func.now()
        )
    )

    if level is not None:
        stmt = stmt.values(level=level)

    await session.execute(stmt)
    await session.commit()

    return await AgentDAO.get_agent(session, agent_id)
```

## Test Requirements

### Unit Tests: `tests/unit/test_leveling_service.py`

**Test Cases**:
1. Test calculate_xp() with high faithfulness (0.9) → high XP
2. Test calculate_xp() with low faithfulness (0.3) → low XP
3. Test calculate_xp() with fast latency (1000ms) → high speed_bonus
4. Test calculate_xp() with slow latency (10000ms) → zero speed_bonus
5. Test calculate_xp() with coverage increase (5%) → positive coverage_bonus
6. Test calculate_xp() with coverage decrease (-2%) → negative coverage_bonus
7. Test check_level_up() with XP=50 (level 1) → no level up
8. Test check_level_up() with XP=100 (level 1→2) → level up to 2
9. Test check_level_up() with XP=300 (level 2→3) → level up to 3
10. Test check_level_up() with XP=1000 (level 4→5) → level up to 5
11. Test unlock_features() for level 2 → debate=true
12. Test unlock_features() for level 5 → all features true
13. Test XP formula determinism (same inputs = same XP)
14. Test XPResult dataclass serialization

### Integration Tests: `tests/integration/test_agent_xp_integration.py`

**End-to-End Tests**:
1. Create agent → query 10 times → verify XP accumulated
2. Create agent → query until XP=100 → verify level up to 2
3. Level up to 2 → verify features_config.debate = true
4. Level up to 5 → verify all features unlocked
5. Query with high quality (faithfulness=0.9) → verify high XP earned
6. Query with low quality (faithfulness=0.3) → verify low XP earned
7. Coverage increase during query → verify coverage_bonus positive
8. XP calculation failure → verify query response still succeeds

### Performance Tests: `tests/performance/test_leveling_performance.py`

**Latency Benchmarks**:
1. calculate_xp() → < 500ms (p95)
2. check_level_up() → < 300ms (p95)
3. unlock_features() → < 200ms (p95)
4. Full XP pipeline (calculate + level_up) → < 1 second (p95)
5. Concurrent XP updates (10 agents) → no race conditions

## Related Files

### Source Code
- @CODE:AGENT-GROWTH-005:DOMAIN: apps/api/services/leveling_service.py (LevelingService)
- @CODE:AGENT-GROWTH-005:DATA: apps/api/database.py (AgentDAO.update_xp_and_level)
- @CODE:AGENT-GROWTH-005:API: apps/api/routers/agent_router.py (POST /query XP hook)

### Dependencies
- @CODE:AGENT-GROWTH-001:DATA: apps/api/database.py (Agent ORM, agents table)
- @CODE:AGENT-GROWTH-002:API: apps/api/routers/agent_router.py (POST /query endpoint)
- @CODE:EXISTING: apps/evaluation/ragas_evaluator.py (RAGAS faithfulness score)

### Test Files
- @TEST:AGENT-GROWTH-005:UNIT: tests/unit/test_leveling_service.py
- @TEST:AGENT-GROWTH-005:INTEGRATION: tests/integration/test_agent_xp_integration.py
- @TEST:AGENT-GROWTH-005:PERFORMANCE: tests/performance/test_leveling_performance.py

## Future Enhancements (Phase 3+)

### Leaderboard API (Optional)
```python
@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    top_n: int = 10,
    session: AsyncSession = Depends(get_session)
):
    """Get top N agents by XP."""
    agents = await AgentDAO.list_agents(
        session=session,
        order_by="current_xp DESC",
        limit=top_n
    )
    return LeaderboardResponse(agents=agents)
```

### XP History Table (Optional)
```sql
CREATE TABLE xp_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
    xp_earned FLOAT NOT NULL,
    query_id UUID,
    breakdown JSONB,
    timestamp TIMESTAMP DEFAULT now()
);
```

### Manual XP Adjustment (Optional)
```python
@router.post("/{agent_id}/xp/adjust", response_model=AgentResponse)
async def adjust_xp(
    agent_id: UUID4,
    adjustment: XPAdjustmentRequest,
    session: AsyncSession = Depends(get_session),
    admin: bool = Depends(require_admin)
):
    """Admin-only: manually adjust XP."""
    await AgentDAO.update_xp_and_level(session, agent_id, adjustment.xp_delta)
    return await AgentDAO.get_agent(session, agent_id)
```

## Revision History

- v0.1.0 (2025-10-13): Initial specification for Phase 2 XP/Leveling System
  - LevelingService with calculate_xp(), check_level_up(), unlock_features()
  - XP formula: base_xp * (faithfulness * 0.5 + speed * 0.3 + coverage * 0.2)
  - 5 level thresholds: 0, 100, 300, 600, 1000 XP
  - Feature unlocking: debate (L2), tools (L3), bandit (L4), priority (L5)
  - Fire-and-forget XP calculation (non-blocking query response)
  - Integration with POST /agents/{id}/query API
  - AgentDAO.update_xp_and_level() for atomic XP updates
