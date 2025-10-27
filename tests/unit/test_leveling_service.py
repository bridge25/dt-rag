# @TEST:AGENT-GROWTH-005:UNIT | SPEC: SPEC-AGENT-GROWTH-005.md
import pytest
import uuid
from unittest.mock import AsyncMock, patch
from apps.api.services.leveling_service import (
    LevelingService,
    XPResult,
    LEVEL_THRESHOLDS,
    LEVEL_FEATURES,
)
from apps.api.database import Agent


class TestLevelingServiceXPCalculation:

    @pytest.mark.asyncio
    async def test_calculate_xp_high_faithfulness(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-high-faithfulness",
            level=1,
            current_xp=0.0,
            avg_faithfulness=0.85,
            avg_response_time_ms=2000.0,
            coverage_percent=50.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            query_result = {
                "latency_ms": 2000.0,
                "coverage_percent": 50.0,
            }

            result = await service.calculate_xp(str(agent_id), query_result)

        assert result is not None
        assert result.agent_id == str(agent_id)
        assert abs(result.xp_earned - 6.05) < 0.01
        assert result.breakdown["faithfulness_bonus"] == 0.85 * 0.5 * 10.0
        assert result.breakdown["speed_bonus"] == (1 - 2.0 / 5.0) * 0.3 * 10.0
        assert result.breakdown["coverage_bonus"] == 0.0
        assert result.level_before == 1
        assert result.level_after == 1

    @pytest.mark.asyncio
    async def test_calculate_xp_low_faithfulness(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-low-faithfulness",
            level=1,
            current_xp=0.0,
            avg_faithfulness=0.30,
            avg_response_time_ms=6000.0,
            coverage_percent=40.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            query_result = {
                "latency_ms": 6000.0,
                "coverage_percent": 40.0,
            }

            result = await service.calculate_xp(str(agent_id), query_result)

        assert result is not None
        assert abs(result.xp_earned - 1.5) < 0.01
        assert result.breakdown["faithfulness_bonus"] == 0.30 * 0.5 * 10.0
        assert result.breakdown["speed_bonus"] == 0.0
        assert result.breakdown["coverage_bonus"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_xp_fast_latency(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-fast",
            level=1,
            current_xp=0.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=1000.0,
            coverage_percent=60.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            query_result = {
                "latency_ms": 1000.0,
                "coverage_percent": 60.0,
            }

            result = await service.calculate_xp(str(agent_id), query_result)

        assert result is not None
        expected_speed_bonus = (1 - 1.0 / 5.0) * 0.3 * 10.0
        assert abs(result.breakdown["speed_bonus"] - expected_speed_bonus) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_xp_slow_latency(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-slow",
            level=1,
            current_xp=0.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=10000.0,
            coverage_percent=60.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            query_result = {
                "latency_ms": 10000.0,
                "coverage_percent": 60.0,
            }

            result = await service.calculate_xp(str(agent_id), query_result)

        assert result is not None
        assert result.breakdown["speed_bonus"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_xp_coverage_increase(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-coverage-increase",
            level=1,
            current_xp=0.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=2000.0,
            coverage_percent=50.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            query_result = {
                "latency_ms": 2000.0,
                "coverage_percent": 55.0,
            }

            result = await service.calculate_xp(str(agent_id), query_result)

        assert result is not None
        expected_coverage_bonus = (55.0 - 50.0) / 100.0 * 0.2 * 10.0
        assert abs(result.breakdown["coverage_bonus"] - expected_coverage_bonus) < 0.01
        assert abs(result.breakdown["coverage_bonus"] - 0.1) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_xp_coverage_decrease(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-coverage-decrease",
            level=2,
            current_xp=150.0,
            avg_faithfulness=0.85,
            avg_response_time_ms=2000.0,
            coverage_percent=70.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            query_result = {
                "latency_ms": 2000.0,
                "coverage_percent": 65.0,
            }

            result = await service.calculate_xp(str(agent_id), query_result)

        assert result is not None
        expected_coverage_penalty = (65.0 - 70.0) / 100.0 * 0.2 * 10.0
        assert (
            abs(result.breakdown["coverage_bonus"] - expected_coverage_penalty) < 0.01
        )
        assert result.breakdown["coverage_bonus"] < 0


class TestLevelingServiceLevelUp:

    @pytest.mark.asyncio
    async def test_check_level_up_no_level_change(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-no-level-up",
            level=1,
            current_xp=50.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=2000.0,
            coverage_percent=60.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.return_value = mock_agent

            result = await service.check_level_up(str(agent_id))

        assert result is None

    @pytest.mark.asyncio
    async def test_check_level_up_to_level_2(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-level-up-2",
            level=1,
            current_xp=100.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=2000.0,
            coverage_percent=60.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
            features_config={"debate": False, "tools": False, "bandit": False},
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            result = await service.check_level_up(str(agent_id))

        assert result is not None
        assert result.level_before == 1
        assert result.level_after == 2
        assert "debate" in result.unlocked_features

    @pytest.mark.asyncio
    async def test_check_level_up_to_level_3(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-level-up-3",
            level=2,
            current_xp=300.0,
            avg_faithfulness=0.85,
            avg_response_time_ms=2000.0,
            coverage_percent=65.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
            features_config={"debate": True, "tools": False, "bandit": False},
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            result = await service.check_level_up(str(agent_id))

        assert result is not None
        assert result.level_before == 2
        assert result.level_after == 3
        assert "tools" in result.unlocked_features

    @pytest.mark.asyncio
    async def test_check_level_up_to_max_level(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-level-up-5",
            level=4,
            current_xp=1000.0,
            avg_faithfulness=0.90,
            avg_response_time_ms=1500.0,
            coverage_percent=75.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
            features_config={"debate": True, "tools": True, "bandit": True},
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            result = await service.check_level_up(str(agent_id))

        assert result is not None
        assert result.level_before == 4
        assert result.level_after == 5
        assert "priority" in result.unlocked_features


class TestLevelingServiceFeatureUnlocking:

    @pytest.mark.asyncio
    async def test_unlock_features_level_2(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent_before = Agent(
            agent_id=agent_id,
            name="test-agent-features-2",
            level=2,
            current_xp=100.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=2000.0,
            coverage_percent=60.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
            features_config={"debate": False, "tools": False, "bandit": False},
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent_before
            mock_update_agent.return_value = mock_agent_before

            unlocked = await service.unlock_features(str(agent_id), 2)

        assert "debate" in unlocked
        assert "tools" not in unlocked
        assert "bandit" not in unlocked

    @pytest.mark.asyncio
    async def test_unlock_features_level_5(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent_before = Agent(
            agent_id=agent_id,
            name="test-agent-features-5",
            level=5,
            current_xp=1000.0,
            avg_faithfulness=0.90,
            avg_response_time_ms=1500.0,
            coverage_percent=75.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
            features_config={"debate": True, "tools": True, "bandit": True},
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent_before
            mock_update_agent.return_value = mock_agent_before

            unlocked = await service.unlock_features(str(agent_id), 5)

        assert "priority" in unlocked

    @pytest.mark.asyncio
    async def test_unlock_features_preserves_custom_flags(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent_before = Agent(
            agent_id=agent_id,
            name="test-agent-custom-flags",
            level=2,
            current_xp=100.0,
            avg_faithfulness=0.80,
            avg_response_time_ms=2000.0,
            coverage_percent=60.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
            features_config={
                "debate": False,
                "tools": False,
                "bandit": False,
                "custom_flag": True,
            },
        )

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent_before
            mock_update_agent.return_value = mock_agent_before

            unlocked = await service.unlock_features(str(agent_id), 2)

        assert "debate" in unlocked
        mock_update_agent.assert_called_once()
        call_args = mock_update_agent.call_args
        assert call_args.kwargs["features_config"]["custom_flag"] is True


class TestLevelingServiceEdgeCases:

    @pytest.mark.asyncio
    async def test_calculate_xp_agent_not_found(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.return_value = None

            query_result = {
                "latency_ms": 2000.0,
                "coverage_percent": 50.0,
            }

            result = await service.calculate_xp(agent_id, query_result)

        assert result is None

    @pytest.mark.asyncio
    async def test_xp_formula_determinism(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()
        mock_agent = Agent(
            agent_id=agent_id,
            name="test-agent-determinism",
            level=1,
            current_xp=0.0,
            avg_faithfulness=0.75,
            avg_response_time_ms=2500.0,
            coverage_percent=55.0,
            taxonomy_node_ids=[uuid.uuid4()],
            taxonomy_version="1.0.0",
        )

        query_result = {
            "latency_ms": 2500.0,
            "coverage_percent": 55.0,
        }

        with (
            patch(
                "apps.api.services.leveling_service.AgentDAO.get_agent",
                new_callable=AsyncMock,
            ) as mock_get_agent,
            patch(
                "apps.api.services.leveling_service.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ) as mock_update_agent,
        ):
            mock_get_agent.return_value = mock_agent
            mock_update_agent.return_value = mock_agent

            result1 = await service.calculate_xp(str(agent_id), query_result)
            result2 = await service.calculate_xp(str(agent_id), query_result)

        assert result1 is not None
        assert result2 is not None
        assert result1.xp_earned == result2.xp_earned
        assert result1.breakdown == result2.breakdown

    @pytest.mark.asyncio
    async def test_calculate_xp_exception_handling(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.side_effect = Exception("Database error")

            query_result = {
                "latency_ms": 2000.0,
                "coverage_percent": 50.0,
            }

            result = await service.calculate_xp(agent_id, query_result)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_level_up_exception_handling(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.side_effect = Exception("Database error")

            result = await service.check_level_up(agent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_unlock_features_exception_handling(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.side_effect = Exception("Database error")

            unlocked = await service.unlock_features(agent_id, 2)

        assert unlocked == []

    @pytest.mark.asyncio
    async def test_check_level_up_agent_not_found(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.return_value = None

            result = await service.check_level_up(agent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_unlock_features_agent_not_found(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        with patch(
            "apps.api.services.leveling_service.AgentDAO.get_agent",
            new_callable=AsyncMock,
        ) as mock_get_agent:
            mock_get_agent.return_value = None

            unlocked = await service.unlock_features(agent_id, 2)

        assert unlocked == []

    @pytest.mark.asyncio
    async def test_calculate_xp_and_level_up_success(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = uuid.uuid4()

        query_result = {
            "latency_ms": 2000.0,
            "coverage_percent": 60.0,
        }

        with (
            patch.object(
                service, "calculate_xp", new_callable=AsyncMock
            ) as mock_calc_xp,
            patch.object(
                service, "check_level_up", new_callable=AsyncMock
            ) as mock_level_up,
        ):
            mock_calc_xp.return_value = XPResult(
                agent_id=str(agent_id),
                xp_earned=10.0,
                breakdown={"total": 10.0},
                total_xp=105.0,
                level_before=1,
                level_after=1,
            )

            await service.calculate_xp_and_level_up(
                session, str(agent_id), query_result
            )

        mock_calc_xp.assert_called_once()
        mock_level_up.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_xp_and_level_up_xp_calculation_failed(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        query_result = {
            "latency_ms": 2000.0,
            "coverage_percent": 60.0,
        }

        with (
            patch.object(
                service, "calculate_xp", new_callable=AsyncMock
            ) as mock_calc_xp,
            patch.object(
                service, "check_level_up", new_callable=AsyncMock
            ) as mock_level_up,
        ):
            mock_calc_xp.return_value = None

            await service.calculate_xp_and_level_up(session, agent_id, query_result)

        mock_calc_xp.assert_called_once()
        mock_level_up.assert_not_called()

    @pytest.mark.asyncio
    async def test_calculate_xp_and_level_up_exception_handling(self):
        session = AsyncMock()
        service = LevelingService(session)

        agent_id = str(uuid.uuid4())

        query_result = {
            "latency_ms": 2000.0,
            "coverage_percent": 60.0,
        }

        with patch.object(
            service, "calculate_xp", new_callable=AsyncMock
        ) as mock_calc_xp:
            mock_calc_xp.side_effect = Exception("Unexpected error")

            await service.calculate_xp_and_level_up(session, agent_id, query_result)

        mock_calc_xp.assert_called_once()


class TestConstants:

    def test_level_thresholds_defined(self):
        assert LEVEL_THRESHOLDS == {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}

    def test_level_features_defined(self):
        assert LEVEL_FEATURES[1] == {"debate": False, "tools": False, "bandit": False}
        assert LEVEL_FEATURES[2] == {"debate": True, "tools": False, "bandit": False}
        assert LEVEL_FEATURES[3] == {"debate": True, "tools": True, "bandit": False}
        assert LEVEL_FEATURES[4] == {"debate": True, "tools": True, "bandit": True}
        assert LEVEL_FEATURES[5] == {
            "debate": True,
            "tools": True,
            "bandit": True,
            "priority": True,
        }
