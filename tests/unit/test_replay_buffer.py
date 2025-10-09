# @TEST:REPLAY-001:unit
"""
Unit tests for ReplayBuffer (SPEC-REPLAY-001)

Tests:
- TEST-REPLAY-001: Experience addition
- TEST-REPLAY-002: Random sampling
- TEST-REPLAY-003: FIFO eviction policy
- TEST-REPLAY-004: Thread-safe concurrent operations
"""
import pytest


@pytest.mark.asyncio
async def test_replay_buffer_add():
    """TEST-REPLAY-001: Experience addition test"""
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    buffer = ReplayBuffer(max_size=100)
    await buffer.add("state1", 0, 0.8, "state2")
    assert len(buffer) == 1


@pytest.mark.asyncio
async def test_replay_buffer_sample():
    """TEST-REPLAY-002: Random sampling test"""
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    buffer = ReplayBuffer(max_size=100)
    for i in range(50):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    batch = await buffer.sample(batch_size=10)
    assert len(batch) == 10


@pytest.mark.asyncio
async def test_replay_buffer_fifo_eviction():
    """TEST-REPLAY-003: FIFO eviction policy test"""
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    buffer = ReplayBuffer(max_size=10)
    for i in range(11):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    assert len(buffer) == 10
    batch = await buffer.sample(batch_size=10)
    assert all(exp[0] != "state0" for exp in batch)


@pytest.mark.asyncio
async def test_replay_buffer_thread_safety():
    """TEST-REPLAY-004: Thread-safe concurrent operations test"""
    import asyncio
    from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

    buffer = ReplayBuffer(max_size=100)

    async def concurrent_add(id):
        await buffer.add(f"state{id}", 0, 0.5, f"state{id+1}")

    await asyncio.gather(*[concurrent_add(i) for i in range(50)])
    assert len(buffer) == 50
