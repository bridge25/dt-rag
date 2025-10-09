# @TEST:SOFTQ-001:0.2 | SPEC: SPEC-SOFTQ-001.md

import pytest
from apps.orchestration.src.bandit.policy import SoftQPolicy


def test_softmax_probabilities():
    """Q-values -> 확률 분포 (합계 1.0)"""
    policy = SoftQPolicy()

    q_values = [0.8, 0.6, 0.2, 0.0, 0.0, 0.0]
    temperature = 0.5

    probs = policy._softmax(q_values, temperature)

    assert len(probs) == 6
    assert abs(sum(probs) - 1.0) < 0.01
    assert probs[0] > probs[1] > probs[2]


def test_select_action_sampling():
    """확률 분포 -> 샘플링"""
    policy = SoftQPolicy()

    q_values = [0.8, 0.0, 0.0, 0.0, 0.0, 0.0]
    temperature = 0.1

    counts = [0] * 6
    for _ in range(100):
        action_idx = policy._sample_action(policy._softmax(q_values, temperature))
        counts[action_idx] += 1

    assert counts[0] > 80


def test_temperature_effect():
    """τ 변화 -> exploration 변화"""
    policy = SoftQPolicy()

    q_values = [0.8, 0.6, 0.2, 0.0, 0.0, 0.0]

    probs_low_temp = policy._softmax(q_values, temperature=0.1)
    assert probs_low_temp[0] > 0.85

    probs_high_temp = policy._softmax(q_values, temperature=2.0)
    assert probs_high_temp[0] < 0.4


def test_overflow_prevention():
    """Q=100, Q=-100 극단값 처리"""
    policy = SoftQPolicy()

    q_values_overflow = [100, 0, 0, 0, 0, 0]
    probs = policy._softmax(q_values_overflow, temperature=0.5)
    assert all(0 <= p <= 1 for p in probs)
    assert abs(sum(probs) - 1.0) < 0.01

    q_values_underflow = [-100, 0, 0, 0, 0, 0]
    probs = policy._softmax(q_values_underflow, temperature=0.5)
    assert all(0 <= p <= 1 for p in probs)
    assert abs(sum(probs) - 1.0) < 0.01
