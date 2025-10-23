# @SPEC:DEBATE-001 @IMPL:DEBATE-001:0.1
"""
Multi-Agent Debate Module for Answer Quality Enhancement

Provides 2-agent debate structure (Affirmative vs Critical)
with 2-round debate process and synthesis.
"""

from apps.orchestration.src.debate.debate_engine import (
    DebateAgent,
    DebateEngine,
    DebateResult,
)
from apps.orchestration.src.debate.agent_prompts import (
    AFFIRMATIVE_PROMPT_R1,
    CRITICAL_PROMPT_R1,
    CRITIQUE_PROMPT_R2,
    SYNTHESIS_PROMPT,
)

__all__ = [
    "DebateAgent",
    "DebateEngine",
    "DebateResult",
    "AFFIRMATIVE_PROMPT_R1",
    "CRITICAL_PROMPT_R1",
    "CRITIQUE_PROMPT_R2",
    "SYNTHESIS_PROMPT",
]
