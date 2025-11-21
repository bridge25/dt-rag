# @SPEC:REPLAY-001 @SPEC:SOFTQ-001
# @IMPL:REPLAY-001:0.2 @CODE:SOFTQ-001:0.3
"""
Soft Q-learning with Experience Replay (SPEC-REPLAY-001, SPEC-SOFTQ-001)

@CODE:BANDIT-001
"""
import logging
from typing import Dict, List, Optional
from apps.orchestration.src.bandit.replay_buffer import ReplayBuffer

logger = logging.getLogger(__name__)


class SoftQLearning:
    """
    Soft Q-learning with batch update support.

    Implements temporal difference learning with:
    - Q-table based value storage
    - Batch learning from replay buffer
    - TD-error based updates
    """

    def __init__(
        self, alpha: float = 0.1, gamma: float = 0.9, temperature: float = 1.0
    ):
        """
        Initialize Soft Q-learning agent.

        Args:
            alpha: Learning rate (default: 0.1)
            gamma: Discount factor (default: 0.9)
            temperature: Softmax temperature for exploration (default: 1.0)

        Raises:
            ValueError: If hyperparameters are invalid
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")
        if not (0.0 <= gamma <= 1.0):
            raise ValueError(f"gamma must be in [0, 1], got {gamma}")
        if temperature <= 0:
            raise ValueError(f"temperature must be positive, got {temperature}")

        self.q_table: Dict[str, List[float]] = {}
        self.alpha = alpha
        self.gamma = gamma
        self.temperature = temperature
        logger.debug(
            f"SoftQLearning initialized: alpha={alpha}, "
            f"gamma={gamma}, temperature={temperature}"
        )

    def update_q_value(
        self, state_hash: str, action_idx: int, reward: float, next_state_hash: str
    ) -> float:
        """
        Update Q-value for single experience using TD-learning.

        Args:
            state_hash: Hash of current state
            action_idx: Action index (0-5 for 6-arm bandit)
            reward: Reward received
            next_state_hash: Hash of next state

        Returns:
            TD error magnitude for monitoring

        Raises:
            ValueError: If inputs are invalid
        """
        if not isinstance(state_hash, str) or not state_hash:
            raise ValueError("state_hash must be non-empty string")
        if not (0 <= action_idx <= 5):
            raise ValueError(f"action_idx must be 0-5, got {action_idx}")
        if not isinstance(reward, (int, float)):
            raise ValueError("reward must be numeric")
        if not isinstance(next_state_hash, str) or not next_state_hash:
            raise ValueError("next_state_hash must be non-empty string")

        if state_hash not in self.q_table:
            self.q_table[state_hash] = [0.0] * 6

        max_next_q = max(self.q_table.get(next_state_hash, [0.0] * 6))
        td_target = reward + self.gamma * max_next_q
        current_q = self.q_table[state_hash][action_idx]
        td_error = td_target - current_q

        self.q_table[state_hash][action_idx] += self.alpha * td_error

        logger.debug(
            f"Q-update: state={state_hash[:20]}..., action={action_idx}, "
            f"reward={reward:.3f}, td_error={td_error:.3f}"
        )

        return abs(td_error)

    async def batch_update(
        self, replay_buffer: ReplayBuffer, batch_size: int = 32
    ) -> int:
        """
        Batch update from replay buffer.

        Args:
            replay_buffer: ReplayBuffer instance to sample from
            batch_size: Number of experiences to sample (default: 32)

        Returns:
            Number of experiences updated (0 if buffer too small)

        Raises:
            ValueError: If batch_size is invalid
            RuntimeError: If batch update fails
        """
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")

        if len(replay_buffer) < batch_size:
            logger.debug(
                f"Buffer too small for batch: {len(replay_buffer)} < {batch_size}, "
                "skipping batch update"
            )
            return 0

        try:
            batch = await replay_buffer.sample(batch_size)
            td_errors = []

            for state_hash, action_idx, reward, next_state_hash in batch:
                td_error = self.update_q_value(
                    state_hash, action_idx, reward, next_state_hash
                )
                td_errors.append(td_error)

            avg_td_error = sum(td_errors) / len(td_errors)
            logger.info(
                f"Batch update: {len(batch)} samples, Q-table: {len(self.q_table)}, "
                f"avg_td_error={avg_td_error:.3f}"
            )

            return len(batch)

        except Exception as e:
            logger.error(f"Batch update failed: {e}", exc_info=True)
            raise RuntimeError(f"Batch update failed: {e}") from e

    def get_q_values(self, state_hash: str) -> Optional[List[float]]:
        """
        Get Q-values for given state.

        Args:
            state_hash: Hash of state

        Returns:
            List of Q-values for all actions, or None if state not seen
        """
        return self.q_table.get(state_hash)

    def calculate_reward(self, confidence: float, latency: float) -> float:
        """
        Calculate reward from confidence and latency (SOFTQ-001).

        Weighted combination: confidence 70% + latency 30%

        Args:
            confidence: Confidence score (0.0 ~ 1.0)
            latency: Latency in seconds

        Returns:
            Reward value (0.0 ~ 1.0)
        """
        normalized_latency = min(latency, 1.0)
        reward = 0.7 * confidence + 0.3 * (1 - normalized_latency)
        return max(0.0, min(1.0, reward))
