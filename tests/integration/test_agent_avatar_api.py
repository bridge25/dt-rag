# @TEST:AGENT-AVATAR-API-001
# Integration tests for Agent Avatar API
# SPEC: SPEC-POKEMON-IMAGE-COMPLETE-001

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.agent_dao import AgentDAO
from apps.api.database import Agent
from apps.api.services.avatar_service import AvatarService


@pytest.mark.asyncio
class TestAgentAvatarCreation:
    """Test agent creation with avatar auto-assignment (using mocks)"""

    @patch("apps.api.agent_dao.CoverageMeterService")
    async def test_create_agent_auto_assigns_rarity_common(self, mock_coverage_service):
        """Agent with 1-2 nodes should get Common rarity"""
        # Mock session and coverage service
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            uuid.uuid4(),
            uuid.uuid4(),
        ]
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock coverage metrics
        mock_metrics = MagicMock()
        mock_metrics.total_documents = 10
        mock_metrics.total_chunks = 100
        mock_metrics.coverage_percent = 80.0
        mock_coverage_service.return_value.calculate_coverage = AsyncMock(
            return_value=mock_metrics
        )

        taxonomy_node_ids = [uuid.uuid4(), uuid.uuid4()]

        # Create agent
        agent = await AgentDAO.create_agent(
            session=mock_session,
            name="Test Common Agent",
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version="1.0.0",
        )

        # Assertions - will fail in RED phase
        assert agent.rarity == "Common"
        assert agent.avatar_url is not None
        assert agent.avatar_url in ["User", "UserCircle", "UserSquare"]

    @patch("apps.api.agent_dao.CoverageMeterService")
    async def test_create_agent_auto_assigns_rarity_legendary(
        self, mock_coverage_service
    ):
        """Agent with 11+ nodes should get Legendary rarity"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            uuid.uuid4() for _ in range(15)
        ]
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_metrics = MagicMock()
        mock_metrics.total_documents = 50
        mock_metrics.total_chunks = 500
        mock_metrics.coverage_percent = 95.0
        mock_coverage_service.return_value.calculate_coverage = AsyncMock(
            return_value=mock_metrics
        )

        taxonomy_node_ids = [uuid.uuid4() for _ in range(15)]

        agent = await AgentDAO.create_agent(
            session=mock_session,
            name="Test Legendary Agent",
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version="1.0.0",
        )

        assert agent.rarity == "Legendary"
        assert agent.avatar_url is not None
        assert agent.avatar_url in ["Flame", "Zap", "Trophy"]

    @patch("apps.api.agent_dao.CoverageMeterService")
    async def test_create_agent_avatar_all_rarity_tiers(self, mock_coverage_service):
        """Test all rarity tiers based on node count"""
        mock_metrics = MagicMock()
        mock_metrics.total_documents = 10
        mock_metrics.total_chunks = 100
        mock_metrics.coverage_percent = 80.0
        mock_coverage_service.return_value.calculate_coverage = AsyncMock(
            return_value=mock_metrics
        )

        test_cases = [
            (1, "Common", ["User", "UserCircle", "UserSquare"]),
            (2, "Common", ["User", "UserCircle", "UserSquare"]),
            (3, "Rare", ["Star", "Sparkles", "Award"]),
            (5, "Rare", ["Star", "Sparkles", "Award"]),
            (6, "Epic", ["Crown", "Shield", "Gem"]),
            (10, "Epic", ["Crown", "Shield", "Gem"]),
            (11, "Legendary", ["Flame", "Zap", "Trophy"]),
            (20, "Legendary", ["Flame", "Zap", "Trophy"]),
        ]

        for node_count, expected_rarity, expected_icons in test_cases:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.execute.return_value.scalars.return_value.all.return_value = [
                uuid.uuid4() for _ in range(node_count)
            ]
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            taxonomy_node_ids = [uuid.uuid4() for _ in range(node_count)]

            agent = await AgentDAO.create_agent(
                session=mock_session,
                name=f"Test Agent {node_count} nodes",
                taxonomy_node_ids=taxonomy_node_ids,
                taxonomy_version="1.0.0",
            )

            assert (
                agent.rarity == expected_rarity
            ), f"Node count {node_count} should result in {expected_rarity}"
            assert agent.avatar_url is not None
            assert (
                agent.avatar_url in expected_icons
            ), f"Avatar icon should be one of {expected_icons}"
