# @SPEC:AGENT-GROWTH-005: Implementation Plan

## Overview

본 문서는 Agent XP/Leveling System Phase 2 구현 계획을 정의합니다. Phase 0-1이 완료된 상태에서 게임화 시스템을 추가하여 에이전트 성장 플랫폼을 완성합니다.

## Milestones (우선순위 기반)

### Phase 5-1: LevelingService Core Implementation
**Priority**: 1차 목표 (High)
**Scope**: XP 계산 로직, Level Up 체크, Feature Unlocking 구현

**Tasks**:
1. `apps/api/services/leveling_service.py` 생성
   - LevelingService 클래스 정의
   - calculate_xp() 메서드 구현 (XP formula)
   - check_level_up() 메서드 구현 (level threshold check)
   - unlock_features() 메서드 구현 (features_config merge)
2. XPResult, LevelUpResult dataclass 정의
3. LEVEL_THRESHOLDS, LEVEL_FEATURES 상수 정의
4. Unit tests 작성 (tests/unit/test_leveling_service.py)
   - XP 계산 정확성 검증 (faithfulness, speed, coverage 보너스)
   - Level up 로직 검증 (threshold 비교)
   - Feature unlocking 검증 (JSONB merge)

**Acceptance Criteria**:
- XP formula 계산 정확도: 100% (manual calculation과 일치)
- Level threshold 체크 정확도: 100% (경계값 테스트 통과)
- Feature unlocking 검증: 각 레벨별 features_config 정확성
- Unit test coverage: ≥ 90%

**Dependencies**:
- SPEC-AGENT-GROWTH-001 (agents 테이블 level, current_xp 필드)
- AgentDAO.get_agent(), update_agent() 메서드

---

### Phase 5-2: AgentDAO XP Update Extension
**Priority**: 1차 목표 (High)
**Scope**: AgentDAO에 XP/Level 업데이트 메서드 추가

**Tasks**:
1. `apps/api/database.py`에 AgentDAO.update_xp_and_level() 추가
   - UPDATE 문으로 current_xp = current_xp + xp_delta 구현
   - level 업데이트 (optional 파라미터)
   - updated_at 자동 갱신
2. Race condition 방지 (atomic update)
3. Unit tests 작성 (tests/unit/test_agent_dao.py)
   - XP 누적 테스트 (여러 번 호출 시 정확한 합산)
   - Concurrent update 테스트 (동시성 검증)

**Acceptance Criteria**:
- Atomic update 보장: concurrent updates에서 XP 손실 없음
- Transaction isolation: rollback 시 XP 변경 없음
- Performance: < 100ms (p95)

**Dependencies**:
- SPEC-AGENT-GROWTH-001 (AgentDAO 기존 구현)

---

### Phase 5-3: POST /query API XP Hook Integration
**Priority**: 2차 목표 (High)
**Scope**: POST /agents/{id}/query 완료 시점에 XP 계산 트리거

**Tasks**:
1. `apps/api/routers/agent_router.py` 수정
   - query_agent() 함수에 XP 계산 hook 추가
   - asyncio.create_task()로 fire-and-forget 구현
   - LevelingService.calculate_xp_and_level_up() 호출
2. query_result에 필요한 메타데이터 추가
   - latency_ms (쿼리 응답 시간)
   - coverage_percent (쿼리 후 커버리지)
3. Error isolation 구현 (XP 실패해도 query 응답은 성공)
4. Integration tests 작성 (tests/integration/test_agent_xp_integration.py)
   - Query 완료 후 XP 증가 검증
   - Query 10회 후 level up 검증
   - XP 계산 실패 시 query 응답 정상 반환 검증

**Acceptance Criteria**:
- Fire-and-forget 검증: query 응답 시간에 XP 계산 시간 미포함
- Error isolation: XP 계산 exception이 query 응답에 영향 없음
- XP 누적 정확도: 10회 query 후 expected XP ± 0.1 오차 범위

**Dependencies**:
- Phase 5-1 (LevelingService 구현)
- Phase 5-2 (AgentDAO.update_xp_and_level)
- SPEC-AGENT-GROWTH-002 (POST /query API)

---

### Phase 5-4: Optional API Endpoints (선택)
**Priority**: 3차 목표 (Medium)
**Scope**: Leaderboard, XP Adjustment, Level-up Test 엔드포인트

**Tasks**:
1. GET /agents/leaderboard 구현 (Optional)
   - AgentDAO.list_agents(order_by="current_xp DESC", limit=top_n)
   - LeaderboardResponse schema 정의
2. POST /agents/{id}/xp/adjust 구현 (Optional, Admin-only)
   - XPAdjustmentRequest schema 정의
   - Admin authentication 추가
3. POST /agents/{id}/level-up-test 구현 (Optional, Dry-run)
   - Simulation mode (no database changes)
   - LevelUpSimulationResponse schema 정의

**Acceptance Criteria**:
- Leaderboard: top N agents 정확성 (XP 내림차순)
- XP Adjustment: admin role 검증 (unauthorized 시 401)
- Level-up Test: dry-run mode 동작 (database 변경 없음)

**Dependencies**:
- Phase 5-1~5-3 완료

---

## Technical Approach

### 1. XP Calculation Algorithm

**Design Decision**: Weighted sum of 3 components (faithfulness, speed, coverage)

**Rationale**:
- Faithfulness (50%): 가장 중요한 지표 (답변 품질)
- Speed (30%): 사용자 경험에 직접적 영향
- Coverage (20%): 장기적 지식 확장 인센티브

**Implementation**:
```python
base_xp = 10.0
faithfulness_bonus = agent.avg_faithfulness * 0.5 * base_xp
speed_bonus = max(0, 1 - latency_seconds / 5.0) * 0.3 * base_xp
coverage_bonus = (new_coverage - old_coverage) / 100.0 * 0.2 * base_xp
total_xp = faithfulness_bonus + speed_bonus + coverage_bonus
```

**Edge Cases**:
- Faithfulness = 0.0 (RAGAS not available) → faithfulness_bonus = 0.0
- Latency > 5초 → speed_bonus = 0.0
- Coverage 감소 → coverage_bonus < 0 (penalty)

### 2. Level Up Logic

**Design Decision**: Threshold-based level system (5 levels, exponential XP curve)

**Rationale**:
- Level 1→2 쉬움 (100 XP, ~10 queries) → 초기 사용자 동기 부여
- Level 4→5 어려움 (400 XP, ~40 queries) → 장기적 목표

**Implementation**:
```python
LEVEL_THRESHOLDS = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}

def get_level_from_xp(xp: float) -> int:
    for level in range(5, 0, -1):
        if xp >= LEVEL_THRESHOLDS[level]:
            return level
    return 1
```

### 3. Feature Unlocking

**Design Decision**: JSONB merge (preserve custom flags)

**Rationale**:
- 기존 custom features 보존 (예: "custom_flag": true)
- Level 기반 features 덮어쓰기 (debate, tools, bandit)

**Implementation**:
```python
new_features = LEVEL_FEATURES[new_level]
existing_config = agent.features_config or {}
merged_config = {**existing_config, **new_features}
await AgentDAO.update_agent(agent_id, features_config=merged_config)
```

### 4. Asynchronous XP Calculation

**Design Decision**: Fire-and-forget with asyncio.create_task()

**Rationale**:
- Query 응답 속도에 영향 없음 (XP 계산은 부가 기능)
- Error isolation (XP 실패해도 query는 성공)

**Implementation**:
```python
# In query_agent() endpoint
asyncio.create_task(
    LevelingService.calculate_xp_and_level_up(
        session=session,
        agent_id=agent_id,
        query_result=results
    )
)
```

**Alternative Considered**: Background task queue (Redis Queue)
- **Rejected**: XP 계산은 latency-sensitive하지 않음 (즉시 실행 필요 없음)
- **Future**: 대규모 트래픽 시 Redis Queue로 전환 고려

---

## Architecture Design

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  POST /agents/{id}/query  (agent_router.py)         │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ 1. Execute hybrid search                       │ │   │
│  │  │ 2. Build QueryResponse                         │ │   │
│  │  │ 3. Fire-and-forget XP calculation (async)      │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                  │
│                            │ asyncio.create_task()            │
│                            ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LevelingService  (leveling_service.py)             │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ calculate_xp()                                 │ │   │
│  │  │  - Retrieve agent metrics                      │ │   │
│  │  │  - Calculate faithfulness_bonus                │ │   │
│  │  │  - Calculate speed_bonus                       │ │   │
│  │  │  - Calculate coverage_bonus                    │ │   │
│  │  │  - Update agent.current_xp                     │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ check_level_up()                               │ │   │
│  │  │  - Compare current_xp with thresholds          │ │   │
│  │  │  - Update agent.level if threshold reached     │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ unlock_features()                              │ │   │
│  │  │  - Merge level features into features_config   │ │   │
│  │  │  - Update agent.features_config                │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                  │
│                            │ AgentDAO                         │
│                            ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AgentDAO  (database.py)                            │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ update_xp_and_level(agent_id, xp_delta, level) │ │   │
│  │  │  UPDATE agents                                  │ │   │
│  │  │  SET current_xp = current_xp + :xp_delta,       │ │   │
│  │  │      level = :level,                            │ │   │
│  │  │      updated_at = now()                         │ │   │
│  │  │  WHERE agent_id = :agent_id                     │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                  │
│                            ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL Database                                 │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │ agents table                                   │ │   │
│  │  │  - current_xp (INTEGER)                        │ │   │
│  │  │  - level (INTEGER, 1-5)                        │ │   │
│  │  │  - features_config (JSONB)                     │ │   │
│  │  │  - avg_faithfulness (FLOAT)                    │ │   │
│  │  │  - avg_response_time_ms (FLOAT)                │ │   │
│  │  │  - coverage_percent (FLOAT)                    │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**XP Calculation Flow**:
1. User sends POST /agents/{id}/query
2. Router executes hybrid search
3. Router builds QueryResponse
4. Router fires asyncio.create_task(calculate_xp_and_level_up) (non-blocking)
5. LevelingService retrieves agent from database
6. LevelingService calculates XP components (faithfulness, speed, coverage)
7. LevelingService updates current_xp via AgentDAO
8. LevelingService checks level threshold
9. If level up: LevelingService updates level and features_config
10. Background task completes (error logged if failure)

---

## Risk Management

### Risk 1: XP Calculation Race Condition
**Severity**: Medium
**Probability**: Medium
**Impact**: XP 손실 또는 중복 계산

**Mitigation**:
- AgentDAO.update_xp_and_level() 사용 시 atomic UPDATE 문 활용
- `SET current_xp = current_xp + :xp_delta` (절대값 대신 증분 사용)
- Database transaction isolation level 검증 (READ COMMITTED 이상)

**Fallback**:
- XP history 테이블 추가 (모든 XP 변경 이력 저장)
- Reconciliation job으로 주기적 검증

---

### Risk 2: XP 계산 실패로 인한 Query 응답 지연
**Severity**: Low
**Probability**: Low
**Impact**: Query latency 증가 (사용자 경험 저하)

**Mitigation**:
- Fire-and-forget 패턴 사용 (asyncio.create_task)
- XP 계산 exception이 query response에 전파되지 않도록 try-except

**Fallback**:
- XP 계산 실패 시 재시도 로직 없음 (단일 시도만)
- Monitoring으로 XP 계산 실패율 추적 (threshold: < 1%)

---

### Risk 3: Feature Unlocking 버그로 인한 잘못된 features_config
**Severity**: High
**Probability**: Low
**Impact**: 사용자에게 잘못된 기능 노출 (보안/성능 문제)

**Mitigation**:
- LEVEL_FEATURES 상수를 immutable dictionary로 정의
- unlock_features() 로직에 대한 엄격한 unit test (각 레벨별 검증)
- Database constraint로 features_config validation (application-level)

**Fallback**:
- Manual features_config override API (admin-only)
- Rollback script for features_config reset

---

## Testing Strategy

### Unit Tests (apps/api/services/leveling_service.py)
**Coverage Target**: ≥ 90%

**Test Scenarios**:
1. **XP Calculation Accuracy**:
   - High faithfulness (0.9) → faithfulness_bonus = 4.5
   - Low faithfulness (0.3) → faithfulness_bonus = 1.5
   - Fast latency (1000ms) → speed_bonus = 1.8
   - Slow latency (10000ms) → speed_bonus = 0.0
   - Coverage increase (5%) → coverage_bonus = 0.1
   - Coverage decrease (-2%) → coverage_bonus = -0.04
2. **Level Up Logic**:
   - XP=50 (level 1) → no level up
   - XP=100 (level 1→2) → level up
   - XP=300 (level 2→3) → level up
   - XP=1000 (level 4→5) → level up
3. **Feature Unlocking**:
   - Level 2 → debate=true, tools=false
   - Level 5 → all features=true
   - Custom flags preserved during merge

### Integration Tests (tests/integration/test_agent_xp_integration.py)
**Database Required**: Yes (PostgreSQL test instance)

**Test Scenarios**:
1. Query 10 times → verify XP accumulated (~100 XP)
2. Query until XP=100 → verify level up to 2
3. Level up to 2 → verify features_config.debate = true
4. XP calculation failure (mock exception) → verify query response succeeds
5. Concurrent queries (10 agents) → verify no XP race condition

### Performance Tests (tests/performance/test_leveling_performance.py)
**Latency Targets**:
- calculate_xp() → < 500ms (p95)
- check_level_up() → < 300ms (p95)
- unlock_features() → < 200ms (p95)

**Load Tests**:
- 100 concurrent XP updates → < 2 seconds total
- 1000 queries → verify XP calculation keeps up (no queue buildup)

---

## Documentation Requirements

### Code Documentation
1. LevelingService docstrings (class, methods)
2. XP formula documentation (inline comments)
3. LEVEL_THRESHOLDS, LEVEL_FEATURES 상수 설명

### API Documentation
1. OpenAPI schema 업데이트 (optional endpoints)
2. Swagger UI examples 추가 (Leaderboard, XP Adjustment)

### Developer Guide
1. XP 계산 알고리즘 설명
2. Level up 로직 설명
3. Feature unlocking 규칙 설명
4. Troubleshooting guide (XP 계산 실패 시 대응)

---

## Deployment Checklist

### Pre-deployment
- [ ] Unit tests 통과 (≥ 90% coverage)
- [ ] Integration tests 통과
- [ ] Performance tests 통과 (latency < targets)
- [ ] Code review 완료
- [ ] SPEC-AGENT-GROWTH-005 acceptance criteria 검증

### Deployment
- [ ] agents 테이블 백업 (rollback 준비)
- [ ] LevelingService 배포
- [ ] AgentDAO 업데이트 배포
- [ ] POST /query API 업데이트 배포
- [ ] Smoke test (단일 query → XP 증가 확인)

### Post-deployment
- [ ] Monitoring dashboard 설정 (XP 계산 성공률, latency)
- [ ] Alert 설정 (XP 계산 실패율 > 1%)
- [ ] 1주일 후 성능 리뷰 (XP 계산 latency, level up 빈도)

---

## Success Metrics

### Functional Metrics
- XP 계산 정확도: 100% (manual calculation과 일치)
- Level up 정확도: 100% (threshold 기준)
- Feature unlocking 정확도: 100% (각 레벨별 검증)

### Performance Metrics
- XP 계산 latency: < 500ms (p95)
- XP 계산 성공률: ≥ 99%
- Query latency 영향: 0ms (fire-and-forget)

### Business Metrics
- Agent level up rate: ≥ 10% of agents reach level 2 within 1 week
- Average XP per agent: ≥ 50 XP within 1 week
- Feature adoption: ≥ 50% of level 2+ agents use debate mode

---

**Plan Version**: 0.1.0
**Last Updated**: 2025-10-13
**Author**: @sonheungmin
