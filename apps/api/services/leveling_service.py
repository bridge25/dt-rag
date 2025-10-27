# @CODE:AGENT-GROWTH-005:DOMAIN | SPEC: SPEC-AGENT-GROWTH-005.md | TEST: tests/unit/test_leveling_service.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from apps.api.agent_dao import AgentDAO

logger = logging.getLogger(__name__)

LEVEL_THRESHOLDS = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}

LEVEL_FEATURES = {
    1: {"debate": False, "tools": False, "bandit": False},
    2: {"debate": True, "tools": False, "bandit": False},
    3: {"debate": True, "tools": True, "bandit": False},
    4: {"debate": True, "tools": True, "bandit": True},
    5: {"debate": True, "tools": True, "bandit": True, "priority": True},
}


@dataclass
class XPResult:
    agent_id: str
    xp_earned: float
    breakdown: Dict[str, float]
    total_xp: float
    level_before: int
    level_after: int


@dataclass
class LevelUpResult:
    agent_id: str
    level_before: int
    level_after: int
    unlocked_features: List[str]


class LevelingService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_xp(
        self, agent_id: str, query_result: Dict
    ) -> Optional[XPResult]:
        try:
            agent = await AgentDAO.get_agent(self.session, UUID(agent_id))
            if not agent:
                logger.warning(f"Agent {agent_id} not found for XP calculation")
                return None

            base_xp = 10.0

            faithfulness = agent.avg_faithfulness or 0.0
            faithfulness_bonus = faithfulness * 0.5 * base_xp

            latency_ms = query_result.get("latency_ms", 0.0)
            latency_seconds = latency_ms / 1000.0
            speed_bonus = max(0, 1 - latency_seconds / 5.0) * 0.3 * base_xp

            new_coverage = query_result.get(
                "coverage_percent", agent.coverage_percent or 0.0
            )
            old_coverage = agent.coverage_percent or 0.0
            coverage_delta = (new_coverage - old_coverage) / 100.0
            coverage_bonus = coverage_delta * 0.2 * base_xp

            total_xp_earned = faithfulness_bonus + speed_bonus + coverage_bonus

            breakdown = {
                "base_xp": base_xp,
                "faithfulness_bonus": faithfulness_bonus,
                "speed_bonus": speed_bonus,
                "coverage_bonus": coverage_bonus,
                "total": total_xp_earned,
            }

            await AgentDAO.update_xp_and_level(
                self.session, UUID(agent_id), xp_delta=total_xp_earned
            )

            updated_agent = await AgentDAO.get_agent(self.session, UUID(agent_id))
            new_total_xp = (
                updated_agent.current_xp
                if updated_agent
                else agent.current_xp + total_xp_earned
            )

            logger.debug(
                f"Agent {agent_id} earned {total_xp_earned:.2f} XP "
                f"(faithfulness: {faithfulness_bonus:.2f}, speed: {speed_bonus:.2f}, "
                f"coverage: {coverage_bonus:.2f})"
            )

            return XPResult(
                agent_id=agent_id,
                xp_earned=total_xp_earned,
                breakdown=breakdown,
                total_xp=new_total_xp,
                level_before=agent.level,
                level_after=agent.level,
            )

        except Exception as e:
            logger.error(
                f"XP calculation failed for agent {agent_id}: {e}", exc_info=True
            )
            return None

    async def check_level_up(self, agent_id: str) -> Optional[LevelUpResult]:
        try:
            agent = await AgentDAO.get_agent(self.session, UUID(agent_id))
            if not agent:
                logger.warning(f"Agent {agent_id} not found for level up check")
                return None

            current_level = agent.level
            current_xp = agent.current_xp

            new_level = current_level
            for level, threshold in sorted(LEVEL_THRESHOLDS.items()):
                if current_xp >= threshold:
                    new_level = level

            if new_level > current_level:
                await AgentDAO.update_xp_and_level(
                    self.session, UUID(agent_id), xp_delta=0.0, level=new_level
                )

                unlocked = await self.unlock_features(agent_id, new_level)

                logger.info(
                    f"Agent {agent_id} leveled up: {current_level} -> {new_level}, "
                    f"unlocked: {unlocked}"
                )

                return LevelUpResult(
                    agent_id=agent_id,
                    level_before=current_level,
                    level_after=new_level,
                    unlocked_features=unlocked,
                )

            return None

        except Exception as e:
            logger.error(
                f"Level up check failed for agent {agent_id}: {e}", exc_info=True
            )
            return None

    async def unlock_features(self, agent_id: str, new_level: int) -> List[str]:
        try:
            agent = await AgentDAO.get_agent(self.session, UUID(agent_id))
            if not agent:
                logger.warning(f"Agent {agent_id} not found for feature unlocking")
                return []

            new_features = LEVEL_FEATURES.get(new_level, {})
            existing_config = agent.features_config or {}

            merged_config = {**existing_config, **new_features}

            await AgentDAO.update_agent(
                self.session, UUID(agent_id), features_config=merged_config
            )

            unlocked = [
                k for k, v in new_features.items() if v and not existing_config.get(k)
            ]

            logger.debug(f"Agent {agent_id} unlocked features: {unlocked}")

            return unlocked

        except Exception as e:
            logger.error(
                f"Feature unlock failed for agent {agent_id}: {e}", exc_info=True
            )
            return []

    async def calculate_xp_and_level_up(
        self, session: AsyncSession, agent_id: str, query_result: Dict
    ):
        try:
            xp_result = await self.calculate_xp(agent_id, query_result)
            if xp_result:
                await self.check_level_up(agent_id)
        except Exception as e:
            logger.error(
                f"XP/Level up pipeline failed for agent {agent_id}: {e}", exc_info=True
            )
