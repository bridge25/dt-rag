# @TEST:REPLAY-001:integration @TEST:SOFTQ-001:0.3
"""
Unit tests for SoftQLearning (SPEC-REPLAY-001, SPEC-SOFTQ-001)

REPLAY-001 Tests:
- TEST-REPLAY-005: Single Q-value update
- TEST-REPLAY-006: Batch learning from buffer
- TEST-REPLAY-007: Insufficient samples handling

SOFTQ-001 Tests:
- Initialize Q-values
- Update Q-value (Bellman equation)
- Reward calculation
- Persistence integration
"""
import pytest
from apps.orchestration.src.bandit.q_learning import SoftQLearning


# ======================================================================
# SOFTQ-001 Tests (Synchronous)
# ======================================================================


@pytest.fixture
def q_learner():
    """Fixture for SOFTQ-001 tests"""
    return SoftQLearning(alpha=0.2, gamma=0.95, temperature=0.5)


def test_initialize_q_values(q_learner):
    """Q-values initialization (6 actions, 0.0)"""
    state_hash = "test_state_001"

    q_values = q_learner.get_q_values(state_hash)

    # First access returns None (not initialized yet in REPLAY-001 version)
    # So we trigger initialization via update
    q_learner.update_q_value(state_hash, 0, 0.0, "next_state")
    q_values = q_learner.get_q_values(state_hash)

    assert len(q_values) == 6
    assert all(isinstance(q, float) for q in q_values)


def test_update_q_value(q_learner):
    """Q-value update (Bellman equation)"""
    state_hash = "test_state_001"
    action_idx = 0
    reward = 0.8
    next_state_hash = "test_state_002"

    # Initialize
    q_learner.update_q_value(state_hash, action_idx, 0.0, next_state_hash)
    q_before = q_learner.get_q_values(state_hash)[action_idx]

    q_learner.update_q_value(state_hash, action_idx, reward, next_state_hash)

    q_after = q_learner.get_q_values(state_hash)[action_idx]

    assert q_after > q_before
    assert 0.0 <= q_after <= 1.0


def test_reward_calculation():
    """Reward calculation (confidence 70% + latency 30%)"""
    q_learner = SoftQLearning()

    confidence = 0.9
    latency = 0.5

    reward = q_learner.calculate_reward(confidence, latency)

    assert 0.0 <= reward <= 1.0
    assert reward > 0.6  # High confidence should give high reward


def test_persistence_integration(q_learner):
    """Q-table persistence (in-memory storage)"""
    state_hash = "test_state_001"
    action_idx = 2
    reward = 0.8

    q_learner.update_q_value(state_hash, action_idx, reward, "next_state")

    q_values = q_learner.get_q_values(state_hash)

    assert q_values[action_idx] > 0.0


# ======================================================================
# REPLAY-001 Tests (Asynchronous)
# ======================================================================


@pytest.mark.asyncio
async def test_q_learning_update_single():
    """TEST-REPLAY-005: Single Q-value update test"""
    q_learning = SoftQLearning()
    q_learning.update_q_value("state1", 0, 0.8, "state2")

    assert "state1" in q_learning.q_table
    assert len(q_learning.q_table["state1"]) == 6


@pytest.mark.asyncio
async def test_batch_update_from_buffer():
    """TEST-REPLAY-006: Batch learning test"""
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=1000)

    # Add 100 experiences
    for i in range(100):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    # Batch update
    updated = await q_learning.batch_update(buffer, batch_size=32)
    assert updated == 32
    assert len(q_learning.q_table) > 0


@pytest.mark.asyncio
async def test_batch_update_insufficient_samples():
    """TEST-REPLAY-007: Insufficient samples handling test"""
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=100)

    # Add only 5 experiences (less than batch_size=32)
    for i in range(5):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    # Should return 0 (not enough samples)
    updated = await q_learning.batch_update(buffer, batch_size=32)
    assert updated == 0
