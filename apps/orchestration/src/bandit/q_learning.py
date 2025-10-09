# @CODE:SOFTQ-001:0.3 | SPEC: SPEC-SOFTQ-001.md | TEST: tests/unit/test_q_learning.py

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class SoftQLearning:
    """
    Soft Q-learning 알고리즘.

    Hyperparameters:
    - Learning Rate (α): 0.2
    - Discount Factor (γ): 0.95
    - Temperature (τ): 0.5

    Update Rule:
    Q(s, a) ← Q(s, a) + α * [R + γ * max(Q(s', a')) - Q(s, a)]
    """

    def __init__(
        self,
        learning_rate: float = 0.2,
        discount_factor: float = 0.95,
        temperature: float = 0.5,
    ):
        """
        Initialize Soft Q-learning.

        Args:
            learning_rate: α (0.0 ~ 1.0)
            discount_factor: γ (0.0 ~ 1.0)
            temperature: τ (0.1 ~ 1.0)
        """
        self.alpha = learning_rate
        self.gamma = discount_factor
        self.temperature = temperature
        self.q_table: Dict[str, List[float]] = {}

        logger.info(
            f"SoftQLearning initialized: α={self.alpha}, γ={self.gamma}, τ={self.temperature}"
        )

    def get_q_values(self, state_hash: str) -> List[float]:
        """
        Q-values 조회 (없으면 초기화).

        Args:
            state_hash: State hash string

        Returns:
            Q-values 리스트 (6개 action)
        """
        if state_hash not in self.q_table:
            self.q_table[state_hash] = [0.0] * 6
            logger.debug(f"Initialized Q-values for state: {state_hash}")
        return self.q_table[state_hash]

    def update_q_value(
        self,
        state_hash: str,
        action_idx: int,
        reward: float,
        next_state_hash: str,
    ) -> None:
        """
        Q-value 업데이트 (Bellman equation).

        Args:
            state_hash: Current state hash
            action_idx: Action index (0~5)
            reward: Reward value (0.0 ~ 1.0)
            next_state_hash: Next state hash
        """
        q_values = self.get_q_values(state_hash)
        next_q_values = self.get_q_values(next_state_hash)

        max_next_q = max(next_q_values)
        old_q = q_values[action_idx]

        q_values[action_idx] = old_q + self.alpha * (
            reward + self.gamma * max_next_q - old_q
        )

        logger.debug(
            f"Q-update: state={state_hash}, action={action_idx}, "
            f"reward={reward:.3f}, Q: {old_q:.3f} -> {q_values[action_idx]:.3f}"
        )

    def calculate_reward(self, confidence: float, latency: float) -> float:
        """
        Reward 계산 (confidence 70% + latency 30%).

        Args:
            confidence: Confidence score (0.0 ~ 1.0)
            latency: Latency in seconds

        Returns:
            Reward value (0.0 ~ 1.0)
        """
        normalized_latency = min(latency, 1.0)
        reward = 0.7 * confidence + 0.3 * (1 - normalized_latency)
        return max(0.0, min(1.0, reward))
