# @TEST:SOFTQ-001:0.1 | SPEC: SPEC-SOFTQ-001.md

import pytest
from apps.orchestration.src.bandit.state_encoder import StateEncoder
from apps.orchestration.src.langgraph_pipeline import PipelineState


def test_encode_state_basic():
    """PipelineState -> state dict 변환"""
    encoder = StateEncoder()

    # Given: PipelineState with complexity, intent, search results
    state = PipelineState(
        query="What is machine learning?",
        intent="question",
        plan={"complexity": "simple"},
        retrieved_chunks=[
            {"chunk_id": 1, "text": "test1"},
            {"chunk_id": 2, "text": "test2"},
            {"chunk_id": 3, "text": "test3"},
        ],
    )

    # When: encode_state 호출
    encoded = encoder.encode_state(state)

    # Then: state dict 반환
    assert encoded["complexity"] == "simple"
    assert encoded["intent"] == "question"
    assert encoded["bm25_bin"] == "1-5"  # 3 -> 1-5 bin
    assert encoded["vector_bin"] == "1-5"  # 3 -> 1-5 bin


def test_state_hashing_consistency():
    """동일 state -> 동일 hash"""
    encoder = StateEncoder()

    state1 = PipelineState(
        query="Test",
        intent="question",
        plan={"complexity": "simple"},
        retrieved_chunks=[
            {"chunk_id": 1, "text": "test1"},
            {"chunk_id": 2, "text": "test2"},
        ],
    )

    state2 = PipelineState(
        query="Different query but same features",
        intent="question",
        plan={"complexity": "simple"},
        retrieved_chunks=[
            {"chunk_id": 3, "text": "test3"},
            {"chunk_id": 4, "text": "test4"},
        ],
    )

    hash1 = encoder.get_state_hash(state1)
    hash2 = encoder.get_state_hash(state2)

    assert hash1 == hash2


def test_feature_discretization():
    """bm25/vector count -> bins"""
    encoder = StateEncoder()

    # 0개 -> "0"
    assert encoder._discretize_count(0) == "0"

    # 1-5개 -> "1-5"
    assert encoder._discretize_count(1) == "1-5"
    assert encoder._discretize_count(5) == "1-5"

    # 6-12개 -> "6-12"
    assert encoder._discretize_count(6) == "6-12"
    assert encoder._discretize_count(12) == "6-12"

    # 13개 이상 -> "6-12" (clip)
    assert encoder._discretize_count(20) == "6-12"
