"""
Agent Entity - Core Business Model

Represents a knowledge agent with taxonomy scope, coverage metrics,
and configuration for retrieval operations.

Business Rules:
- Agent must have at least one taxonomy node in scope
- Coverage percent must be between 0 and 100
- Level must be positive (1-100)
- XP must be non-negative

@CODE:CLEAN-ARCHITECTURE-AGENT-ENTITY
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID


class AgentStatus(str, Enum):
    """Agent operational status"""
    ACTIVE = "active"
    IDLE = "idle"
    TRAINING = "training"
    DISABLED = "disabled"


class AgentRarity(str, Enum):
    """Agent rarity tier for gamification"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass(frozen=True)
class AgentStats:
    """Agent performance statistics"""
    total_queries: int = 0
    successful_queries: int = 0
    avg_faithfulness: float = 0.0
    avg_response_time_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate query success rate (0-100%)"""
        if self.total_queries == 0:
            return 0.0
        return (self.successful_queries / self.total_queries) * 100

    @property
    def is_performant(self) -> bool:
        """Check if agent meets performance thresholds"""
        return (
            self.success_rate >= 80.0 and
            self.avg_faithfulness >= 0.7 and
            self.avg_response_time_ms < 5000
        )


@dataclass(frozen=True)
class AgentConfig:
    """Agent configuration for retrieval and features"""
    retrieval_config: Dict[str, Any] = field(default_factory=lambda: {
        "strategy": "hybrid",
        "top_k": 5,
        "bm25_weight": 0.5,
        "vector_weight": 0.5,
    })
    features_config: Dict[str, Any] = field(default_factory=lambda: {
        "reranking_enabled": True,
        "casebank_enabled": False,
        "streaming_enabled": True,
    })


@dataclass(frozen=True)
class Agent:
    """
    Agent Entity - Knowledge Domain Expert

    An Agent represents a specialized knowledge worker scoped to
    specific taxonomy nodes. It tracks coverage, performance metrics,
    and configuration for RAG operations.

    Attributes:
        agent_id: Unique identifier
        name: Human-readable agent name
        taxonomy_node_ids: List of taxonomy nodes in agent's scope
        taxonomy_version: Version of taxonomy tree
        coverage_percent: Percentage of scope covered by documents (0-100)
        level: Agent experience level (1-100)
        current_xp: Current experience points
        stats: Performance statistics
        config: Retrieval and feature configuration
        status: Operational status
        avatar_url: Optional avatar image URL
        rarity: Gamification rarity tier
    """
    agent_id: UUID
    name: str
    taxonomy_node_ids: List[UUID]
    taxonomy_version: str
    coverage_percent: float = 0.0
    total_documents: int = 0
    total_chunks: int = 0
    level: int = 1
    current_xp: float = 0.0
    stats: AgentStats = field(default_factory=AgentStats)
    config: AgentConfig = field(default_factory=AgentConfig)
    status: AgentStatus = AgentStatus.ACTIVE
    scope_description: Optional[str] = None
    avatar_url: Optional[str] = None
    rarity: AgentRarity = AgentRarity.COMMON
    character_description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_query_at: Optional[datetime] = None
    last_coverage_update: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate business rules on creation"""
        if not self.taxonomy_node_ids:
            raise ValueError("Agent must have at least one taxonomy node in scope")
        if not 0 <= self.coverage_percent <= 100:
            raise ValueError("Coverage percent must be between 0 and 100")
        if self.level < 1 or self.level > 100:
            raise ValueError("Level must be between 1 and 100")
        if self.current_xp < 0:
            raise ValueError("XP must be non-negative")

    @property
    def health_score(self) -> int:
        """Calculate overall agent health score (0-100)"""
        status_score = 100 if self.status == AgentStatus.ACTIVE else 50
        coverage_score = self.coverage_percent
        performance_score = 100 if self.stats.is_performant else 60
        return round((status_score + coverage_score + performance_score) / 3)

    @property
    def xp_for_next_level(self) -> float:
        """Calculate XP required for next level"""
        # Exponential XP curve: level^2 * 100
        return (self.level ** 2) * 100

    @property
    def level_progress(self) -> float:
        """Calculate progress to next level (0-100%)"""
        required = self.xp_for_next_level
        if required == 0:
            return 100.0
        return min(100.0, (self.current_xp / required) * 100)

    def can_level_up(self) -> bool:
        """Check if agent has enough XP to level up"""
        return self.current_xp >= self.xp_for_next_level and self.level < 100

    def calculate_query_xp(
        self,
        latency_ms: float,
        faithfulness: float = 1.0,
    ) -> float:
        """
        Calculate XP earned from a query.

        Business Logic:
        - Base XP: 10 points per query
        - Speed bonus: Up to 5 points for fast responses (< 1000ms)
        - Faithfulness bonus: Up to 10 points for high faithfulness
        - Coverage bonus: Multiplier based on coverage (1.0 - 1.5x)
        """
        base_xp = 10.0

        # Speed bonus (max 5 points)
        speed_bonus = max(0, 5 * (1 - latency_ms / 5000))

        # Faithfulness bonus (max 10 points)
        faithfulness_bonus = faithfulness * 10

        # Coverage multiplier (1.0 - 1.5x)
        coverage_multiplier = 1.0 + (self.coverage_percent / 200)

        total_xp = (base_xp + speed_bonus + faithfulness_bonus) * coverage_multiplier
        return round(total_xp, 2)


# Business Logic Functions (Pure Functions)

def calculate_agent_health_score(agent: Agent) -> int:
    """Calculate overall health score for an agent"""
    return agent.health_score


def is_agent_ready_for_queries(agent: Agent) -> bool:
    """Check if agent is ready to handle queries"""
    return (
        agent.status == AgentStatus.ACTIVE and
        agent.coverage_percent > 0 and
        len(agent.taxonomy_node_ids) > 0
    )


def get_recommended_actions(agent: Agent) -> List[str]:
    """Get recommended actions to improve agent performance"""
    recommendations = []

    if agent.coverage_percent < 50:
        recommendations.append("Increase document coverage by ingesting more documents")

    if agent.stats.success_rate < 80:
        recommendations.append("Review failed queries and improve retrieval configuration")

    if agent.stats.avg_response_time_ms > 3000:
        recommendations.append("Optimize retrieval strategy for faster responses")

    if agent.level < 5 and agent.stats.total_queries < 10:
        recommendations.append("Run more queries to gain experience and level up")

    if not agent.config.features_config.get("reranking_enabled"):
        recommendations.append("Enable reranking for improved result quality")

    return recommendations
