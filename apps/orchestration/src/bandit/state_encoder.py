# @CODE:SOFTQ-001:0.1 | SPEC: SPEC-SOFTQ-001.md | TEST: tests/unit/test_state_encoder.py

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class StateEncoder:
    """
    파이프라인 state를 Soft-Q에 필요한 feature로 인코딩합니다.

    State 구성:
    - complexity: simple/medium/complex (Meta-Planner 제공)
    - intent: question/explanation/search/general
    - bm25_bin: BM25 검색 결과 개수 (0 / 1-5 / 6-12)
    - vector_bin: Vector 검색 결과 개수 (0 / 1-5 / 6-12)
    """

    def encode_state(self, pipeline_state: Any) -> Dict[str, str]:
        """
        PipelineState를 state dict로 변환합니다.

        Args:
            pipeline_state: LangGraph PipelineState 객체

        Returns:
            state dict (complexity, intent, bm25_bin, vector_bin)
        """
        complexity = pipeline_state.plan.get("complexity", "simple")
        intent = pipeline_state.intent
        chunks_count = len(pipeline_state.retrieved_chunks)

        logger.debug(
            f"Encoding state: complexity={complexity}, intent={intent}, "
            f"chunks={chunks_count}"
        )

        return {
            "complexity": complexity,
            "intent": intent,
            "bm25_bin": self._discretize_count(chunks_count),
            "vector_bin": self._discretize_count(chunks_count),
        }

    def get_state_hash(self, pipeline_state: Any) -> str:
        """
        State를 hash로 변환합니다 (Q-table 조회용).

        Args:
            pipeline_state: LangGraph PipelineState 객체

        Returns:
            state hash 문자열
        """
        encoded = self.encode_state(pipeline_state)
        state_tuple = (
            encoded["complexity"],
            encoded["intent"],
            encoded["bm25_bin"],
            encoded["vector_bin"],
        )
        return str(hash(state_tuple))

    def _discretize_count(self, count: int) -> str:
        """
        Count를 bin으로 변환합니다.

        Args:
            count: 검색 결과 개수

        Returns:
            bin 문자열 ("0" / "1-5" / "6-12")
        """
        if count == 0:
            return "0"
        elif 1 <= count <= 5:
            return "1-5"
        else:
            return "6-12"
