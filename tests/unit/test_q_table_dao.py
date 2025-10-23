# @TEST:SOFTQ-001:0.4 | SPEC: SPEC-SOFTQ-001.md

import pytest
import asyncio
from apps.api.database import QTableDAO


@pytest.fixture
async def q_dao():
    return QTableDAO()


@pytest.mark.asyncio
async def test_save_q_table(q_dao):
    """Q-table 저장 (state_hash, q_values)"""
    state_hash = "test_state_001"
    q_values = [0.8, 0.6, 0.2, 0.0, 0.0, 0.0]

    await q_dao.save_q_table(state_hash, q_values)

    loaded = await q_dao.load_q_table(state_hash)

    assert loaded is not None
    assert len(loaded) == 6
    assert loaded[0] == pytest.approx(0.8, abs=0.01)


@pytest.mark.asyncio
async def test_load_nonexistent_state(q_dao):
    """존재하지 않는 state -> None"""
    loaded = await q_dao.load_q_table("nonexistent_state")

    assert loaded is None


@pytest.mark.asyncio
async def test_update_q_table(q_dao):
    """Q-table 업데이트 (덮어쓰기)"""
    state_hash = "test_state_002"
    q_values_v1 = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    q_values_v2 = [0.8, 0.6, 0.2, 0.0, 0.0, 0.0]

    await q_dao.save_q_table(state_hash, q_values_v1)
    await q_dao.save_q_table(state_hash, q_values_v2)

    loaded = await q_dao.load_q_table(state_hash)

    assert loaded[0] == pytest.approx(0.8, abs=0.01)
