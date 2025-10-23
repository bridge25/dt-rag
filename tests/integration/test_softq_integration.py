# @TEST:SOFTQ-001:0.5 | SPEC: SPEC-SOFTQ-001.md

import pytest
import asyncio
from apps.orchestration.src.bandit.state_encoder import StateEncoder
from apps.orchestration.src.bandit.policy import SoftQPolicy
from apps.orchestration.src.bandit.q_learning import SoftQLearning
from apps.api.database import QTableDAO
from apps.orchestration.src.langgraph_pipeline import PipelineState


@pytest.mark.asyncio
async def test_full_softq_cycle():
    """Full Soft-Q cycle: State encoding -> Action selection -> Q-update"""
    encoder = StateEncoder()
    policy = SoftQPolicy()
    q_learner = SoftQLearning()
    dao = QTableDAO()

    state = PipelineState(
        query="What is RAG?",
        intent="question",
        plan={"complexity": "simple"},
        retrieved_chunks=[
            {"chunk_id": 1, "text": "test1"},
            {"chunk_id": 2, "text": "test2"},
        ],
    )

    state_hash = encoder.get_state_hash(state)
    q_values = q_learner.get_q_values(state_hash)

    action = policy.select_action(q_values)

    assert action is not None
    assert "retrieval" in action
    assert "compose" in action

    reward = q_learner.calculate_reward(confidence=0.8, latency=0.5)
    q_learner.update_q_value(state_hash, 0, reward, "next_state_hash")

    await dao.save_q_table(state_hash, q_learner.get_q_values(state_hash))

    loaded_q_values = await dao.load_q_table(state_hash)
    assert loaded_q_values is not None
    assert len(loaded_q_values) == 6


@pytest.mark.asyncio
async def test_multiple_iterations():
    """Multiple iterations: Q-values 수렴 테스트"""
    encoder = StateEncoder()
    policy = SoftQPolicy()
    q_learner = SoftQLearning()

    state = PipelineState(
        query="ML question",
        intent="question",
        plan={"complexity": "simple"},
        retrieved_chunks=[{"chunk_id": 1, "text": "test"}],
    )

    state_hash = encoder.get_state_hash(state)

    for i in range(10):
        q_values = q_learner.get_q_values(state_hash)
        action_idx = policy._sample_action(policy._softmax(q_values, 0.5))

        reward = 0.9
        q_learner.update_q_value(state_hash, action_idx, reward, "next_state")

    final_q_values = q_learner.get_q_values(state_hash)
    assert any(q > 0.5 for q in final_q_values)
