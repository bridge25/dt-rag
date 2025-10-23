# @SPEC:AGENT-GROWTH-005: Acceptance Criteria

## Overview

본 문서는 Agent XP/Leveling System Phase 2 구현 완료를 검증하기 위한 상세한 수락 기준을 정의합니다. 모든 시나리오는 Given-When-Then 형식으로 작성되며, 자동화된 테스트로 검증 가능해야 합니다.

---

## Scenario 1: First Query Earns XP (Level 1 → Level 1 + XP)

### Given
- Agent exists with:
  - agent_id: `test-agent-001`
  - level: 1
  - current_xp: 0
  - avg_faithfulness: 0.85
  - avg_response_time_ms: 2000.0
  - coverage_percent: 50.0

### When
- User sends POST /agents/test-agent-001/query with:
  - query: "What is breast cancer treatment?"
  - Query completes successfully with:
    - latency_ms: 2000.0
    - new_coverage_percent: 50.0 (no change)

### Then
- **Query Response**:
  - HTTP status: 200 OK
  - Response contains search results
  - Response time: < 3 seconds (XP calculation does not block)

- **XP Calculation** (background):
  - Base XP: 10.0
  - Faithfulness bonus: 0.85 * 0.5 * 10 = 4.25
  - Speed bonus: (1 - 2.0/5.0) * 0.3 * 10 = 1.8
  - Coverage bonus: (50 - 50) / 100.0 * 0.2 * 10 = 0.0
  - **Total XP earned**: 4.25 + 1.8 + 0.0 = 6.05

- **Database State** (after background task completes):
  - agents.current_xp = 6.05 (± 0.01)
  - agents.level = 1 (no level up yet)
  - agents.updated_at = now()

- **Logging**:
  - INFO log: "Agent test-agent-001 earned 6.05 XP (faithfulness: 4.25, speed: 1.8, coverage: 0.0)"

---

## Scenario 2: Level Up from 1 to 2 (100 XP Threshold)

### Given
- Agent exists with:
  - agent_id: `test-agent-002`
  - level: 1
  - current_xp: 96.0
  - avg_faithfulness: 0.80
  - avg_response_time_ms: 2500.0
  - coverage_percent: 60.0
  - features_config: {"debate": false, "tools": false, "bandit": false}

### When
- User sends POST /agents/test-agent-002/query
- Query completes with:
  - latency_ms: 2500.0
  - new_coverage_percent: 60.0

### Then
- **XP Calculation**:
  - Faithfulness bonus: 0.80 * 0.5 * 10 = 4.0
  - Speed bonus: (1 - 2.5/5.0) * 0.3 * 10 = 1.5
  - Coverage bonus: 0.0
  - **Total XP earned**: 5.5
  - **New total XP**: 96.0 + 5.5 = 101.5

- **Level Up Detection**:
  - current_xp (101.5) >= LEVEL_THRESHOLDS[2] (100) → **Level up to 2**

- **Database State**:
  - agents.current_xp = 101.5 (± 0.01)
  - agents.level = 2 (level up occurred)
  - agents.features_config = {"debate": true, "tools": false, "bandit": false}
  - agents.updated_at = now()

- **Logging**:
  - INFO log: "Agent test-agent-002 leveled up: 1 -> 2, unlocked: ['debate']"

---

## Scenario 3: Feature Unlock (Debate Mode at Level 2)

### Given
- Agent exists with:
  - agent_id: `test-agent-003`
  - level: 2
  - features_config: {"debate": true, "tools": false, "bandit": false}

### When
- User sends POST /agents/test-agent-003/query with:
  - query: "Compare treatment A vs treatment B"
  - Agent's features_config.debate = true

### Then
- **Query Execution**:
  - System detects features_config.debate = true
  - Multi-Agent Debate Mode is enabled
  - Query executes with 2-agent debate (Affirmative vs Critical)

- **Response**:
  - HTTP status: 200 OK
  - Response contains debate results:
    - affirmative_response
    - critical_response
    - synthesis_response

- **Feature Verification**:
  - Debate mode was actually used (not just flag set)
  - Response time: < 8 seconds (debate mode is slower)

---

## Scenario 4: Max Level (Level 5, All Features)

### Given
- Agent exists with:
  - agent_id: `test-agent-004`
  - level: 4
  - current_xp: 998.0
  - features_config: {"debate": true, "tools": true, "bandit": true}

### When
- User sends POST /agents/test-agent-004/query
- Query earns 5.0 XP

### Then
- **XP Calculation**:
  - **New total XP**: 998.0 + 5.0 = 1003.0

- **Level Up Detection**:
  - current_xp (1003.0) >= LEVEL_THRESHOLDS[5] (1000) → **Level up to 5**

- **Database State**:
  - agents.current_xp = 1003.0
  - agents.level = 5 (max level)
  - agents.features_config = {"debate": true, "tools": true, "bandit": true, "priority": true}

- **Logging**:
  - INFO log: "Agent test-agent-004 leveled up: 4 -> 5, unlocked: ['priority']"

- **Further XP Accumulation**:
  - Agent can continue earning XP (no cap)
  - Level remains at 5 (max level)

---

## Scenario 5: Low Quality Query (Low Faithfulness = Low XP)

### Given
- Agent exists with:
  - agent_id: `test-agent-005`
  - level: 1
  - current_xp: 0
  - avg_faithfulness: 0.30 (low quality)
  - avg_response_time_ms: 6000.0 (slow)
  - coverage_percent: 40.0

### When
- User sends POST /agents/test-agent-005/query
- Query completes with:
  - latency_ms: 6000.0 (over 5 seconds)
  - new_coverage_percent: 40.0 (no change)

### Then
- **XP Calculation**:
  - Faithfulness bonus: 0.30 * 0.5 * 10 = 1.5
  - Speed bonus: max(0, 1 - 6.0/5.0) * 0.3 * 10 = **0.0** (penalty for slow response)
  - Coverage bonus: 0.0
  - **Total XP earned**: 1.5

- **Database State**:
  - agents.current_xp = 1.5 (low XP due to poor quality)
  - agents.level = 1 (no level up)

- **Interpretation**:
  - Low faithfulness (0.30) → low XP
  - Slow response (6s) → no speed bonus
  - Agent needs to improve quality to earn more XP

---

## Scenario 6: Coverage Improvement Bonus

### Given
- Agent exists with:
  - agent_id: `test-agent-006`
  - level: 1
  - current_xp: 0
  - avg_faithfulness: 0.80
  - avg_response_time_ms: 2000.0
  - coverage_percent: 50.0

### When
- User uploads new documents to agent's taxonomy scope
- Coverage calculation updates coverage_percent to 55.0 (5% increase)
- User sends POST /agents/test-agent-006/query

### Then
- **XP Calculation**:
  - Faithfulness bonus: 0.80 * 0.5 * 10 = 4.0
  - Speed bonus: (1 - 2.0/5.0) * 0.3 * 10 = 1.8
  - Coverage bonus: (55.0 - 50.0) / 100.0 * 0.2 * 10 = **0.1** (bonus for coverage increase)
  - **Total XP earned**: 4.0 + 1.8 + 0.1 = 5.9

- **Database State**:
  - agents.current_xp = 5.9
  - agents.coverage_percent = 55.0

- **Interpretation**:
  - Coverage improvement (50% → 55%) earns bonus XP
  - Incentivizes agents to expand knowledge scope

---

## Scenario 7: Coverage Decrease Penalty

### Given
- Agent exists with:
  - agent_id: `test-agent-007`
  - level: 2
  - current_xp: 150.0
  - avg_faithfulness: 0.85
  - avg_response_time_ms: 2000.0
  - coverage_percent: 70.0

### When
- Documents are deleted from agent's taxonomy scope
- Coverage calculation updates coverage_percent to 65.0 (5% decrease)
- User sends POST /agents/test-agent-007/query

### Then
- **XP Calculation**:
  - Faithfulness bonus: 0.85 * 0.5 * 10 = 4.25
  - Speed bonus: (1 - 2.0/5.0) * 0.3 * 10 = 1.8
  - Coverage bonus: (65.0 - 70.0) / 100.0 * 0.2 * 10 = **-0.1** (penalty for coverage decrease)
  - **Total XP earned**: 4.25 + 1.8 - 0.1 = 5.95

- **Database State**:
  - agents.current_xp = 150.0 + 5.95 = 155.95
  - agents.coverage_percent = 65.0

- **Interpretation**:
  - Coverage decrease (70% → 65%) applies XP penalty
  - Still earns net positive XP due to high faithfulness and speed
  - Discourages knowledge scope reduction

---

## Scenario 8: XP Calculation Failure Does Not Block Query

### Given
- Agent exists with:
  - agent_id: `test-agent-008`
  - level: 1
  - current_xp: 0
- Database connection is unstable (simulated failure)

### When
- User sends POST /agents/test-agent-008/query
- XP calculation fails with exception: "Database connection timeout"

### Then
- **Query Response**:
  - HTTP status: 200 OK
  - Response contains search results (query succeeded)
  - Response time: < 3 seconds (XP failure does not block)

- **XP Calculation** (background):
  - Exception caught: "Database connection timeout"
  - ERROR log: "XP calculation failed for agent test-agent-008: Database connection timeout"
  - XP calculation returns None (graceful failure)

- **Database State**:
  - agents.current_xp = 0 (unchanged, XP not updated)
  - agents.level = 1 (unchanged)

- **Interpretation**:
  - XP calculation failure is isolated (does not affect query)
  - User receives query response normally
  - Error is logged for monitoring/debugging

---

## Scenario 9: Concurrent XP Updates (Race Condition Test)

### Given
- Agent exists with:
  - agent_id: `test-agent-009`
  - level: 1
  - current_xp: 0

### When
- 10 concurrent POST /agents/test-agent-009/query requests are sent simultaneously
- Each query earns 5.0 XP

### Then
- **Expected Outcome**:
  - All 10 queries succeed (HTTP 200 OK)
  - XP updates are atomic (no race condition)
  - **Final current_xp**: 50.0 (± 0.01) (10 queries * 5.0 XP)

- **Database Integrity**:
  - No XP loss due to race condition
  - No duplicate XP accumulation
  - agents.updated_at reflects last update timestamp

- **Test Method**:
  - Use asyncio.gather() to send concurrent requests
  - Verify final XP matches expected value

---

## Scenario 10: Custom Features Preserved During Level Up

### Given
- Agent exists with:
  - agent_id: `test-agent-010`
  - level: 1
  - current_xp: 98.0
  - features_config: {"debate": false, "tools": false, "bandit": false, "custom_flag": true}

### When
- User sends POST /agents/test-agent-010/query
- Query earns 5.0 XP
- Agent levels up to 2

### Then
- **Level Up**:
  - New level: 2
  - New features from LEVEL_FEATURES[2]: {"debate": true, "tools": false, "bandit": false}

- **Database State**:
  - agents.level = 2
  - agents.features_config = {"debate": true, "tools": false, "bandit": false, "custom_flag": true}

- **Interpretation**:
  - Custom flag "custom_flag": true is preserved during merge
  - Level-based features (debate, tools, bandit) are updated
  - JSONB merge strategy: {**existing, **new}

---

## Quality Gates

### Functional Requirements
- [ ] All 10 scenarios pass (100% success rate)
- [ ] XP calculation accuracy: ± 0.01 XP tolerance
- [ ] Level up threshold detection: 100% accuracy
- [ ] Feature unlocking: 100% accuracy (each level verified)

### Performance Requirements
- [ ] XP calculation latency: < 500ms (p95)
- [ ] Query response not blocked by XP calculation (fire-and-forget verified)
- [ ] Concurrent XP updates: no race condition (10 concurrent requests test)

### Error Handling
- [ ] XP calculation failure does not block query response
- [ ] Exception is logged with ERROR level
- [ ] Graceful degradation (XP not updated, but query succeeds)

### Data Integrity
- [ ] Atomic XP updates (no race condition)
- [ ] Custom features_config preserved during level up
- [ ] Level field only updated via LevelingService (application-level enforcement)

---

## Definition of Done

### Code Completion
- [ ] LevelingService implemented with calculate_xp(), check_level_up(), unlock_features()
- [ ] AgentDAO.update_xp_and_level() implemented
- [ ] POST /agents/{id}/query hook implemented (fire-and-forget)
- [ ] Unit tests: ≥ 90% coverage
- [ ] Integration tests: all 10 scenarios pass
- [ ] Performance tests: latency targets met

### Documentation
- [ ] Code docstrings complete (class, methods)
- [ ] SPEC-AGENT-GROWTH-005 acceptance criteria verified
- [ ] API documentation updated (if optional endpoints added)

### Deployment
- [ ] Smoke test passed (single query → XP increase)
- [ ] Monitoring dashboard configured (XP calculation success rate, latency)
- [ ] Alert configured (XP calculation failure rate > 1%)

---

**Acceptance Criteria Version**: 0.1.0
**Last Updated**: 2025-10-13
**Author**: @sonheungmin
