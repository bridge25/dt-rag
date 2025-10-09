# @TEST:SOFTQ-001:0.3 | SPEC: SPEC-SOFTQ-001.md

import pytest
from apps.orchestration.src.bandit.q_learning import SoftQLearning


@pytest.fixture
def q_learner():
    return SoftQLearning(
        learning_rate=0.2,
        discount_factor=0.95,
        temperature=0.5,
    )


def test_initialize_q_values(q_learner):
    """Q-values 초기화 (6개 action, 0.0)"""
    state_hash = "test_state_001"

    q_values = q_learner.get_q_values(state_hash)

    assert len(q_values) == 6
    assert all(q == 0.0 for q in q_values)


def test_update_q_value(q_learner):
    """Q-value 업데이트 (Bellman equation)"""
    state_hash = "test_state_001"
    action_idx = 0
    reward = 0.8
    next_state_hash = "test_state_002"

    q_before = q_learner.get_q_values(state_hash)[action_idx]

    q_learner.update_q_value(state_hash, action_idx, reward, next_state_hash)

    q_after = q_learner.get_q_values(state_hash)[action_idx]

    assert q_after > q_before
    assert 0.0 <= q_after <= 1.0


def test_reward_calculation():
    """Reward 계산 (confidence 70% + latency 30%)"""
    q_learner = SoftQLearning()

    confidence = 0.9
    latency = 0.5

    reward = q_learner.calculate_reward(confidence, latency)

    assert 0.0 <= reward <= 1.0
    assert reward > 0.6


def test_persistence_integration(q_learner):
    """Q-table 영속성 (메모리 저장)"""
    state_hash = "test_state_001"
    action_idx = 2
    reward = 0.8

    q_learner.update_q_value(state_hash, action_idx, reward, "next_state")

    q_values = q_learner.get_q_values(state_hash)

    assert q_values[action_idx] > 0.0
