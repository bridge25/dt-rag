# @CODE:SOFTQ-001:0.2 | SPEC: SPEC-SOFTQ-001.md | TEST: tests/unit/test_policy.py
"""
Soft Q-learning based policy with softmax action selection.

@CODE:BANDIT-001
"""

import logging
import math
import random
# @CODE:MYPY-CONSOLIDATION-002 | Phase 14d: valid-type (Fix 64 - add Any import)
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

ACTIONS = [
    {"retrieval": "bm25_only", "compose": "direct", "weights": (1.0, 0.0)},
    {"retrieval": "bm25_only", "compose": "cot", "weights": (1.0, 0.0)},
    {"retrieval": "hybrid_balanced", "compose": "direct", "weights": (0.5, 0.5)},
    {"retrieval": "hybrid_balanced", "compose": "cot", "weights": (0.5, 0.5)},
    {"retrieval": "vector_heavy", "compose": "direct", "weights": (0.3, 0.7)},
    {"retrieval": "vector_heavy", "compose": "cot", "weights": (0.3, 0.7)},
]


class SoftQPolicy:
    """
    Soft Q-learning 기반 정책 (Softmax).

    Temperature parameter τ로 exploration/exploitation 조절:
    - τ 낮음 (0.1) -> exploitation (Q 높은 action 집중)
    - τ 높음 (1.0) -> exploration (균등 분포)
    """

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 14d: valid-type (Fix 64 - any → Any)
    def select_action(
        self, q_values: List[float], temperature: float = 0.5
    ) -> Dict[str, Any]:
        """
        Softmax 정책으로 action 선택

        Args:
            q_values: Q-value 리스트 (6개 action)
            temperature: Exploration parameter (기본 0.5)

        Returns:
            선택된 action dict (retrieval, compose, weights)
        """
        probs = self._softmax(q_values, temperature)
        action_idx = self._sample_action(probs)

        logger.info(
            f"Soft-Q selected action {action_idx}: {ACTIONS[action_idx]}, "
            f"probs={[round(p, 3) for p in probs]}"
        )

        return ACTIONS[action_idx]

    def _softmax(self, q_values: List[float], temperature: float) -> List[float]:
        """
        Q-values를 softmax 확률 분포로 변환 (log-sum-exp trick 사용)

        Args:
            q_values: Q-value 리스트 (6개 action)
            temperature: Exploration parameter (0.1~1.0)

        Returns:
            확률 분포 (합계 1.0)
        """
        max_q = max(q_values)
        exp_vals = [math.exp((q - max_q) / temperature) for q in q_values]
        sum_exp = sum(exp_vals)
        return [e / sum_exp for e in exp_vals]

    def _sample_action(self, probabilities: List[float]) -> int:
        """
        확률 분포로부터 action 샘플링

        Args:
            probabilities: 확률 분포 (6개)

        Returns:
            선택된 action index (0~5)
        """
        return random.choices(range(len(probabilities)), weights=probabilities, k=1)[0]
