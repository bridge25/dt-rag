---
id: REPLAY-001
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
priority: medium
category: enhancement
labels:
  - experience-replay
  - reinforcement-learning
  - soft-q-learning
  - phase-3
depends_on:
  - SOFTQ-001
  - FOUNDATION-001
related_specs:
  - DEBATE-001
  - ORCHESTRATION-001
scope:
  packages:
    - apps/orchestration
  files:
    - apps/orchestration/src/bandit/replay_buffer.py
    - apps/orchestration/src/bandit/q_learning.py
  tests:
    - tests/unit/test_replay_buffer.py
    - tests/integration/test_replay_learning.py
---

## HISTORY

### v0.1.0 (2025-10-09)
- **INITIAL**: Experience Replay Buffer SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: Replay Buffer 구현, Batch Learning 통합, Feature Flag 연결
- **CONTEXT**: SOFTQ-001 완료 후 Sample Efficiency 향상을 위한 경험 재사용 메커니즘

---

# @SPEC:REPLAY-001: Experience Replay Buffer for Soft Q-learning Reinforcement Learning

## Environment (환경)

- Python 3.11+, asyncio
- PostgreSQL 15+ (선택적, 영구 저장용)
- 기존 Soft Q-learning Bandit (SOFTQ-001)
  - State Space: 108 states (4-feature)
  - Action Space: 6 actions
  - Q-table: In-memory dictionary
- Feature Flag 시스템 (FOUNDATION-001)
- LangGraph 7-Step Pipeline

## Assumptions (가정)

- Soft Q-learning Bandit이 이미 구현되어 동작 중
- Q-table 업데이트는 현재 단일 (state, action, reward, next_state) 기반
- PostgreSQL은 선택적 (Phase 1에서는 in-memory 우선)
- Feature Flag `experience_replay`가 기본값 false로 설정되어 있음
- 기존 Q-learning 동작은 변경하지 않음 (backward compatibility)

## Requirements (요구사항)

### Ubiquitous Requirements
- 시스템은 (state, action, reward, next_state) tuple을 Replay Buffer에 저장해야 한다
- 시스템은 Replay Buffer에서 랜덤 샘플링하여 배치 Q-learning 학습을 수행해야 한다
- 시스템은 Replay Buffer 크기 제한(max_size)을 관리해야 한다
- 시스템은 FIFO (First-In-First-Out) 정책으로 오래된 경험을 제거해야 한다

### Event-driven Requirements
- WHEN step7_respond 완료 시, 시스템은 (state, action, reward, next_state) tuple을 Buffer에 추가해야 한다
- WHEN Replay Buffer가 min_samples 이상 시, 시스템은 배치 학습을 트리거할 수 있어야 한다
- WHEN Replay Buffer가 max_size 초과 시, 시스템은 가장 오래된 tuple을 제거해야 한다
- WHEN experience_replay=False 시, 시스템은 Buffer 저장을 스킵하고 기존 동작을 유지해야 한다

### State-driven Requirements
- WHILE experience_replay=True 일 때, 시스템은 Replay Buffer를 활성화해야 한다
- WHILE Buffer.size >= min_samples 일 때, 시스템은 배치 학습을 수행할 수 있어야 한다
- WHILE 배치 학습 진행 중일 때, 시스템은 메인 파이프라인을 차단하지 않아야 한다 (비동기)

### Constraints
- IF Replay Buffer 저장 실패 시, 시스템은 에러 로그를 기록하고 파이프라인을 계속 진행해야 한다 (비차단)
- IF 배치 학습 실패 시, 시스템은 경고 로그를 기록하고 다음 배치를 시도해야 한다
- Buffer 크기: max_size=10000 (기본값, 환경 변수로 override 가능)
- 배치 크기: batch_size=32 (기본값, 환경 변수로 override 가능)
- 최소 샘플 수: min_samples=100 (기본값, 환경 변수로 override 가능)

## Specifications

### 0.1 Replay Buffer 구현

**목표**: Past experience를 저장하고 랜덤 샘플링하는 Replay Buffer 클래스 구현

**파일**: `apps/orchestration/src/bandit/replay_buffer.py` (신규, ~120 LOC)

**클래스 설계**:
```python
# @IMPL:REPLAY-001:0.1
class ReplayBuffer:
    """
    Experience Replay Buffer for Off-Policy Learning.

    Features:
    - FIFO eviction policy (deque with maxlen)
    - Random sampling for decorrelated batch learning
    - Thread-safe operations (asyncio.Lock)
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize Replay Buffer.

        Args:
            max_size: Maximum buffer size (FIFO eviction)
        """
        self.buffer = deque(maxlen=max_size)
        self.lock = asyncio.Lock()

    async def add(
        self,
        state_hash: str,
        action_idx: int,
        reward: float,
        next_state_hash: str
    ) -> None:
        """
        Add experience tuple to buffer.

        Args:
            state_hash: Current state hash
            action_idx: Action index (0~5)
            reward: Reward value (0.0 ~ 1.0)
            next_state_hash: Next state hash
        """
        async with self.lock:
            self.buffer.append((state_hash, action_idx, reward, next_state_hash))

    async def sample(self, batch_size: int = 32) -> List[Tuple]:
        """
        Random sample from buffer.

        Args:
            batch_size: Number of samples

        Returns:
            List of (state, action, reward, next_state) tuples
        """
        async with self.lock:
            if len(self.buffer) < batch_size:
                return list(self.buffer)
            return random.sample(self.buffer, batch_size)

    def __len__(self) -> int:
        """Return buffer size."""
        return len(self.buffer)
```

**에러 처리**:
- `add()` 실패 시: 로그 기록 후 계속 진행 (비차단)
- `sample()` 실패 시: 빈 리스트 반환

**로깅**:
- Buffer 추가 시: DEBUG 레벨
- FIFO eviction 시: INFO 레벨
- 배치 샘플링 시: DEBUG 레벨

### 0.2 Batch Learning 통합

**목표**: Replay Buffer에서 배치 샘플링하여 Q-table 업데이트하는 메서드 추가

**파일**: `apps/orchestration/src/bandit/q_learning.py` (수정, +50 LOC)

**변경사항**:
```python
# @IMPL:REPLAY-001:0.2
class SoftQLearning:
    # 기존 메서드들...

    async def batch_update(
        self,
        replay_buffer: ReplayBuffer,
        batch_size: int = 32
    ) -> int:
        """
        Batch learning from Replay Buffer.

        Args:
            replay_buffer: ReplayBuffer instance
            batch_size: Batch size

        Returns:
            Number of updated samples
        """
        if len(replay_buffer) < batch_size:
            logger.debug(
                f"Buffer too small for batch learning: "
                f"{len(replay_buffer)} < {batch_size}"
            )
            return 0

        batch = await replay_buffer.sample(batch_size)

        for state_hash, action_idx, reward, next_state_hash in batch:
            self.update_q_value(state_hash, action_idx, reward, next_state_hash)

        logger.info(
            f"Batch update completed: {len(batch)} samples, "
            f"Q-table size: {len(self.q_table)}"
        )

        return len(batch)
```

**특징**:
- 기존 `update_q_value()` 메서드 재사용
- 비동기 메서드 (async/await)
- 배치 크기 미달 시 graceful degradation

### 0.3 Feature Flag 통합

**목표**: `experience_replay` Feature Flag를 통한 Replay Buffer 활성화

**파일**: `apps/orchestration/src/langgraph_pipeline.py` (수정, +30 LOC)

**변경사항**:
```python
# @IMPL:REPLAY-001:0.3
from bandit.replay_buffer import ReplayBuffer

class LangGraphPipeline:
    def __init__(self, ...):
        # 기존 코드...
        self.replay_buffer = ReplayBuffer(max_size=10000)

    async def step7_respond(self, state: PipelineState) -> PipelineState:
        """
        Step 7: Response generation + Replay Buffer 저장
        """
        # 기존 step7 로직...

        # Experience Replay Buffer 저장
        flags = get_feature_flags()
        if flags.get("experience_replay", False):
            try:
                state_hash = self.state_encoder.get_state_hash(state)
                # next_state_hash는 현재 state_hash로 근사 (terminal state)
                await self.replay_buffer.add(
                    state_hash=state_hash,
                    action_idx=state.selected_action_idx,
                    reward=self.q_learning.calculate_reward(
                        confidence=state.confidence,
                        latency=state.latency
                    ),
                    next_state_hash=state_hash
                )
                logger.debug(
                    f"Experience added to Replay Buffer: "
                    f"size={len(self.replay_buffer)}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to add experience to Replay Buffer: {e}",
                    exc_info=True
                )

        return state
```

**주기적 배치 학습** (선택적):
```python
# @IMPL:REPLAY-001:0.3
async def periodic_batch_learning(self):
    """
    백그라운드에서 주기적 배치 학습 수행 (옵션).
    """
    while True:
        await asyncio.sleep(60)  # 1분마다

        flags = get_feature_flags()
        if flags.get("experience_replay", False):
            try:
                updated = await self.q_learning.batch_update(
                    self.replay_buffer,
                    batch_size=32
                )
                if updated > 0:
                    logger.info(f"Periodic batch learning: {updated} samples")
            except Exception as e:
                logger.warning(f"Periodic batch learning failed: {e}")
```

### 0.4 TDD 테스트

**목표**: Replay Buffer 동작 및 통합 검증

**파일 1**: `tests/unit/test_replay_buffer.py` (~150 LOC)

```python
# @TEST:REPLAY-001:unit
import pytest
from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

@pytest.mark.asyncio
async def test_replay_buffer_add():
    """Test adding experiences to buffer."""
    buffer = ReplayBuffer(max_size=100)

    await buffer.add("state1", 0, 0.8, "state2")
    await buffer.add("state2", 1, 0.6, "state3")

    assert len(buffer) == 2

@pytest.mark.asyncio
async def test_replay_buffer_sample():
    """Test random sampling from buffer."""
    buffer = ReplayBuffer(max_size=100)

    for i in range(50):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    batch = await buffer.sample(batch_size=10)

    assert len(batch) == 10
    assert all(isinstance(exp, tuple) for exp in batch)
    assert all(len(exp) == 4 for exp in batch)

@pytest.mark.asyncio
async def test_replay_buffer_fifo_eviction():
    """Test FIFO eviction when buffer is full."""
    buffer = ReplayBuffer(max_size=10)

    # Fill buffer
    for i in range(10):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    assert len(buffer) == 10

    # Add one more (should evict first)
    await buffer.add("state10", 0, 0.5, "state11")

    assert len(buffer) == 10
    batch = await buffer.sample(batch_size=10)

    # "state0" should be evicted
    assert all(exp[0] != "state0" for exp in batch)

@pytest.mark.asyncio
async def test_replay_buffer_min_samples():
    """Test behavior when buffer has fewer samples than batch_size."""
    buffer = ReplayBuffer(max_size=100)

    # Add only 5 samples
    for i in range(5):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    batch = await buffer.sample(batch_size=10)

    # Should return all 5 samples
    assert len(batch) == 5
```

**파일 2**: `tests/integration/test_replay_learning.py` (~100 LOC)

```python
# @TEST:REPLAY-001:integration
import pytest
from apps.orchestration.src.bandit.q_learning import SoftQLearning
from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

@pytest.mark.asyncio
async def test_batch_learning_from_buffer():
    """Test batch Q-learning from Replay Buffer."""
    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=1000)

    # Add 100 experiences
    for i in range(100):
        await buffer.add(f"state{i}", i % 6, 0.5 + (i % 3) * 0.1, f"state{i+1}")

    # Batch update
    updated = await q_learning.batch_update(buffer, batch_size=32)

    assert updated == 32
    assert len(q_learning.q_table) > 0

@pytest.mark.asyncio
async def test_experience_replay_flag_integration(mocker):
    """Test Replay Buffer integration with feature flag."""
    # Mock feature flag
    mocker.patch(
        "apps.api.env_manager.get_feature_flags",
        return_value={"experience_replay": True}
    )

    # Test pipeline integration
    # (구현 시 실제 PipelineState와 통합 테스트)
    pass

@pytest.mark.asyncio
async def test_async_batch_learning():
    """Test that batch learning doesn't block main pipeline."""
    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=1000)

    # Add experiences
    for i in range(200):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    # Run batch learning asynchronously
    import asyncio
    task = asyncio.create_task(q_learning.batch_update(buffer, batch_size=50))

    # Simulate main pipeline work
    await asyncio.sleep(0.01)

    # Wait for batch learning
    updated = await task

    assert updated == 50
```

## Traceability (@TAG)

- **SPEC**: @SPEC:REPLAY-001
- **DEPENDS**: @SPEC:SOFTQ-001, @SPEC:FOUNDATION-001
- **RELATES**: @SPEC:DEBATE-001, @SPEC:ORCHESTRATION-001
- **IMPL**:
  - @IMPL:REPLAY-001:0.1 - Replay Buffer 클래스
  - @IMPL:REPLAY-001:0.2 - Batch Learning 메서드
  - @IMPL:REPLAY-001:0.3 - Feature Flag 통합
- **TEST**:
  - @TEST:REPLAY-001:unit - Replay Buffer 단위 테스트
  - @TEST:REPLAY-001:integration - Batch Learning 통합 테스트
- **CODE**:
  - apps/orchestration/src/bandit/replay_buffer.py
  - apps/orchestration/src/bandit/q_learning.py (수정)
  - apps/orchestration/src/langgraph_pipeline.py (수정)
- **TEST FILES**:
  - tests/unit/test_replay_buffer.py
  - tests/integration/test_replay_learning.py
