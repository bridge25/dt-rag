# @SPEC:DEBATE-001 @IMPL:DEBATE-001:0.1
"""
Multi-Agent Debate Engine Implementation

Provides:
- DebateAgent: Individual agent (Affirmative/Critical) for answer generation
- DebateEngine: Orchestrator for 2-round debate process
- DebateResult: Result dataclass with metadata

Architecture:
- Round 1: Parallel independent answer generation (2 LLM calls)
- Round 2: Parallel critique and improvement (2 LLM calls)
- Synthesis: Final answer integration (1 LLM call)

@CODE:MYPY-001:PHASE2:BATCH4
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from apps.api.llm_service import GeminiLLMService

from apps.orchestration.src.debate.agent_prompts import (
    AFFIRMATIVE_PROMPT_R1,
    CRITICAL_PROMPT_R1,
    CRITIQUE_PROMPT_R2,
    SYNTHESIS_PROMPT,
)

logger = logging.getLogger(__name__)


def get_llm_service_cached() -> "GeminiLLMService":
    """Lazy load LLM service"""
    from apps.api.llm_service import get_llm_service

    return get_llm_service()


@dataclass
class DebateResult:
    """Result from multi-agent debate"""

    final_answer: str
    rounds: int
    llm_calls: int
    affirmative_answers: List[str]
    critical_answers: List[str]
    elapsed_time: float


class DebateAgent:
    """
    Individual debate agent (Affirmative or Critical)

    Args:
        role: "affirmative" or "critical"
        max_tokens: Maximum tokens for answer generation (default: 500)
    """

    def __init__(self, role: str, max_tokens: int = 500) -> None:
        self.role = role
        self.max_tokens = max_tokens

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context chunks for prompt"""
        context_parts = []
        for idx, chunk in enumerate(context, 1):
            text = chunk.get("text", "")
            title = chunk.get("title", "Unknown")
            source = chunk.get("source_url", "")
            score = chunk.get("score", 0.0)

            context_parts.append(
                f"[Document {idx}] (Score: {score:.2f})\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Content: {text}\n"
            )

        return "\n".join(context_parts)

    def _trim_to_token_limit(self, text: str, max_tokens: int) -> str:
        """Trim text to maximum token count (approximation: 1 token ~ 1 word)"""
        words = text.split()
        if len(words) <= max_tokens:
            return text
        return " ".join(words[:max_tokens])

    async def generate_answer(
        self,
        query: str,
        context: List[Dict[str, Any]],
        own_previous_answer: Optional[str] = None,
        opponent_answer: Optional[str] = None,
    ) -> str:
        """
        Generate answer for the given query

        Args:
            query: User question
            context: Retrieved chunks
            own_previous_answer: Own answer from previous round (for Round 2)
            opponent_answer: Opponent's answer from previous round (for Round 2)

        Returns:
            Generated answer string
        """
        llm_service = get_llm_service_cached()
        context_text = self._format_context(context)

        if opponent_answer is None:
            if self.role == "affirmative":
                prompt = AFFIRMATIVE_PROMPT_R1.format(query=query, context=context_text)
            else:
                prompt = CRITICAL_PROMPT_R1.format(query=query, context=context_text)
        else:
            prompt = CRITIQUE_PROMPT_R2.format(
                role=self.role,
                own_answer=own_previous_answer or "",
                opponent_answer=opponent_answer,
            )

        try:
            response = llm_service.model.generate_content(prompt)
            answer = response.text

            answer = self._trim_to_token_limit(answer, self.max_tokens)

            logger.info(
                f"{self.role.capitalize()} agent generated answer ({len(answer.split())} tokens)"
            )
            return answer

        except Exception as e:
            logger.error(f"Agent {self.role} failed to generate answer: {e}")
            raise


class DebateEngine:
    """
    Multi-Agent Debate Orchestrator

    Executes a 2-round debate between Affirmative and Critical agents,
    followed by synthesis of final answer.
    """

    def __init__(self) -> None:
        self.affirmative_agent = DebateAgent(role="affirmative", max_tokens=500)
        self.critical_agent = DebateAgent(role="critical", max_tokens=500)

    async def _run_round1(
        self, query: str, context: List[Dict[str, Any]]
    ) -> "tuple[str, str]":
        """
        Round 1: Independent answer generation (parallel)

        Returns:
            Tuple of (affirmative_answer, critical_answer)
        """
        round_start = time.time()
        logger.info("Round 1: Generating independent answers (parallel)...")

        affirmative_task = self.affirmative_agent.generate_answer(
            query=query, context=context
        )
        critical_task = self.critical_agent.generate_answer(
            query=query, context=context
        )

        affirmative_answer, critical_answer = await asyncio.gather(
            affirmative_task, critical_task
        )

        elapsed = time.time() - round_start
        logger.info(
            f"Round 1 completed in {elapsed:.2f}s: "
            f"Affirmative={len(affirmative_answer)} chars ({len(affirmative_answer.split())} tokens), "
            f"Critical={len(critical_answer)} chars ({len(critical_answer.split())} tokens)"
        )

        return affirmative_answer, critical_answer

    async def _run_round2(
        self,
        query: str,
        context: List[Dict[str, Any]],
        affirmative_r1: str,
        critical_r1: str,
    ) -> "tuple[str, str]":
        """
        Round 2: Mutual critique and improvement (parallel)

        Returns:
            Tuple of (affirmative_answer_r2, critical_answer_r2)
        """
        round_start = time.time()
        logger.info("Round 2: Critiquing and improving answers (parallel)...")

        affirmative_task = self.affirmative_agent.generate_answer(
            query=query,
            context=context,
            own_previous_answer=affirmative_r1,
            opponent_answer=critical_r1,
        )
        critical_task = self.critical_agent.generate_answer(
            query=query,
            context=context,
            own_previous_answer=critical_r1,
            opponent_answer=affirmative_r1,
        )

        affirmative_answer_r2, critical_answer_r2 = await asyncio.gather(
            affirmative_task, critical_task
        )

        elapsed = time.time() - round_start
        logger.info(
            f"Round 2 completed in {elapsed:.2f}s: "
            f"Affirmative={len(affirmative_answer_r2)} chars ({len(affirmative_answer_r2.split())} tokens), "
            f"Critical={len(critical_answer_r2)} chars ({len(critical_answer_r2.split())} tokens)"
        )

        return affirmative_answer_r2, critical_answer_r2

    async def _synthesize(self, affirmative_answer: str, critical_answer: str) -> str:
        """
        Synthesize final answer from both perspectives

        Args:
            affirmative_answer: Final affirmative answer from Round 2
            critical_answer: Final critical answer from Round 2

        Returns:
            Synthesized final answer (max 800 tokens)
        """
        synth_start = time.time()
        logger.info("Synthesizing final answer from both perspectives...")

        llm_service = get_llm_service_cached()

        prompt = SYNTHESIS_PROMPT.format(
            affirmative_answer=affirmative_answer, critical_answer=critical_answer
        )

        try:
            response = llm_service.model.generate_content(prompt)
            final_answer: str = response.text

            words = final_answer.split()
            original_tokens = len(words)
            if len(words) > 800:
                final_answer = " ".join(words[:800])
                logger.warning(
                    f"Synthesis answer trimmed from {original_tokens} to 800 tokens"
                )

            elapsed = time.time() - synth_start
            logger.info(
                f"Synthesis completed in {elapsed:.2f}s: "
                f"{len(final_answer.split())} tokens, {len(final_answer)} chars"
            )
            return final_answer

        except Exception as e:
            logger.error(
                f"Synthesis failed after {time.time() - synth_start:.2f}s: {e}"
            )
            raise

    async def run_debate(
        self,
        query: str,
        context: List[Dict[str, Any]],
        max_rounds: int = 2,
        timeout: float = 10.0,
    ) -> DebateResult:
        """
        Execute multi-round debate

        Args:
            query: User question
            context: Retrieved chunks
            max_rounds: Maximum debate rounds (default: 2)
            timeout: Total timeout in seconds (default: 10.0)

        Returns:
            DebateResult with final answer and metadata

        Raises:
            asyncio.TimeoutError: If debate exceeds timeout
            Exception: If LLM calls fail
        """
        start_time = time.time()

        async def _execute_debate() -> DebateResult:
            affirmative_r1, critical_r1 = await self._run_round1(query, context)

            affirmative_r2, critical_r2 = await self._run_round2(
                query, context, affirmative_r1, critical_r1
            )

            final_answer = await self._synthesize(affirmative_r2, critical_r2)

            return DebateResult(
                final_answer=final_answer,
                rounds=2,
                llm_calls=5,
                affirmative_answers=[affirmative_r1, affirmative_r2],
                critical_answers=[critical_r1, critical_r2],
                elapsed_time=time.time() - start_time,
            )

        result = await asyncio.wait_for(_execute_debate(), timeout=timeout)

        logger.info(
            f"Debate completed in {result.elapsed_time:.2f}s ({result.llm_calls} LLM calls)"
        )
        return result
