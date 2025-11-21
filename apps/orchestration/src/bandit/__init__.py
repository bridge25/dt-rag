# @SPEC:REPLAY-001 @SPEC:SOFTQ-001
# @IMPL:REPLAY-001:0.1 @CODE:SOFTQ-001:0.1
"""
Bandit module for Experience Replay and Soft Q-learning (SPEC-REPLAY-001, SPEC-SOFTQ-001)

@CODE:BANDIT-001
"""
from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer
from apps.orchestration.src.bandit.q_learning import SoftQLearning

__all__ = ["ReplayBuffer", "SoftQLearning"]
