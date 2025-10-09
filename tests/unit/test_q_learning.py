# @TEST:REPLAY-001:integration
"""
Unit tests for SoftQLearning (SPEC-REPLAY-001)

Tests:
- TEST-REPLAY-005: Single Q-value update
- TEST-REPLAY-006: Batch learning from buffer
- TEST-REPLAY-007: Insufficient samples handling
"""
import pytest


@pytest.mark.asyncio
async def test_q_learning_update_single():
    """TEST-REPLAY-005: Single Q-value update test"""
    from apps.orchestration.src.bandit.q_learning import SoftQLearning

    q_learning = SoftQLearning()
    q_learning.update_q_value("state1", 0, 0.8, "state2")

    assert "state1" in q_learning.q_table
    assert len(q_learning.q_table["state1"]) == 6


@pytest.mark.asyncio
async def test_batch_update_from_buffer():
    """TEST-REPLAY-006: Batch learning test"""
    from apps.orchestration.src.bandit.q_learning import SoftQLearning
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=1000)

    for i in range(100):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    updated = await q_learning.batch_update(buffer, batch_size=32)
    assert updated == 32
    assert len(q_learning.q_table) > 0


@pytest.mark.asyncio
async def test_batch_update_insufficient_samples():
    """TEST-REPLAY-007: Insufficient samples handling test"""
    from apps.orchestration.src.bandit.q_learning import SoftQLearning
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=100)

    for i in range(5):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    updated = await q_learning.batch_update(buffer, batch_size=32)
    assert updated == 0
