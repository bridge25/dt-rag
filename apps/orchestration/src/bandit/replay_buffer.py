# @SPEC:REPLAY-001 @IMPL:REPLAY-001:0.1
"""
Experience Replay Buffer for Soft Q-learning Bandit (SPEC-REPLAY-001)
"""
import asyncio
import logging
import random
from collections import deque
from typing import List, Tuple

logger = logging.getLogger(__name__)


class ReplayBuffer:
    """
    FIFO Replay Buffer with thread-safe operations.

    Stores experiences (state, action, reward, next_state) and supports:
    - Thread-safe async add/sample operations
    - FIFO eviction when max_size is reached
    - Random batch sampling for experience replay
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize replay buffer.

        Args:
            max_size: Maximum number of experiences to store (default: 10000)

        Raises:
            ValueError: If max_size is not positive
        """
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")

        self.buffer = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
        logger.debug(f"ReplayBuffer initialized with max_size={max_size}")

    async def add(
        self,
        state_hash: str,
        action_idx: int,
        reward: float,
        next_state_hash: str,
    ) -> None:
        """
        Add experience to buffer with thread-safe operation.

        Args:
            state_hash: Hash of current state
            action_idx: Action index (0-5 for 6-arm bandit)
            reward: Reward received
            next_state_hash: Hash of next state

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

        async with self.lock:
            evicted = len(self.buffer) == self.buffer.maxlen
            self.buffer.append((state_hash, action_idx, reward, next_state_hash))

            if evicted:
                logger.info(
                    f"Buffer full, FIFO eviction occurred (size={len(self.buffer)})"
                )
            else:
                logger.debug(f"Experience added (buffer_size={len(self.buffer)})")

    async def sample(self, batch_size: int = 32) -> List[Tuple[str, int, float, str]]:
        """
        Sample random batch from buffer.

        Args:
            batch_size: Number of experiences to sample (default: 32)

        Returns:
            List of sampled experiences (state, action, reward, next_state)
            Returns all experiences if buffer size < batch_size

        Raises:
            ValueError: If batch_size is not positive
        """
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")

        async with self.lock:
            if len(self.buffer) < batch_size:
                logger.debug(
                    f"Buffer too small ({len(self.buffer)} < {batch_size}), "
                    f"returning all {len(self.buffer)} samples"
                )
                return list(self.buffer)

            samples = random.sample(list(self.buffer), batch_size)
            logger.debug(f"Sampled {batch_size} experiences from buffer")
            return samples

    def __len__(self) -> int:
        """Return current buffer size"""
        return len(self.buffer)
