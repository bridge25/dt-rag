import pytest
from typing import Dict, Any
from moai.core.flags import FeatureFlags
from moai.core.pipeline import Pipeline
from moai.agents.debate import MultiAgentDebate
from moai.planners.meta_planner import MetaPlanner
from moai.tools.retrieval import AdaptiveRetrieval
from moai.config import load_config

class E2EIntegrationTestSuite:
    """
    End-to-End Integration Test Suite for MoAI Pipeline
    Covers Phase 0-3.2 Scenarios
    """

    @pytest.fixture
    def feature_flags(self) -> FeatureFlags:
        """Default feature flags configuration"""
        return FeatureFlags(
            debate_mode=True,
            adaptive_retrieval=True,
            meta_planner=True,
            tools_enabled=True
        )

    @pytest.mark.e2e
    def test_e2e_001_full_pipeline(self, feature_flags):
        """
        E2E-001: Full 7-step pipeline with all flags ON
        """
        pipeline = Pipeline(flags=feature_flags)
        result = pipeline.execute(input_data={})

        assert result is not None, "Full pipeline execution failed"
        assert len(result.steps) == 7, "Expected 7 pipeline steps"
        assert result.is_complete, "Pipeline did not complete successfully"

    @pytest.mark.e2e
    def test_e2e_002_adaptive_retrieval(self):
        """
        E2E-002: Adaptive Retrieval using Soft Q-learning Bandit
        """
        flags = FeatureFlags(adaptive_retrieval=True)
        adaptive_retrieval = AdaptiveRetrieval(flags)

        # Simulate retrieval scenarios
        test_queries = ["query1", "query2", "query3"]
        for query in test_queries:
            result = adaptive_retrieval.retrieve(query)
            assert result is not None, f"Retrieval failed for query: {query}"

    @pytest.mark.e2e
    def test_e2e_003_debate_mode(self):
        """
        E2E-003: Multi-Agent Debate Mode
        """
        flags = FeatureFlags(debate_mode=True)
        debate = MultiAgentDebate(flags)

        test_scenario = {
            "topic": "AI Ethics",
            "initial_perspectives": ["Pro AI", "Cautious about AI"]
        }

        debate_result = debate.start(test_scenario)
        assert debate_result.is_resolved, "Debate did not reach a conclusion"

    @pytest.mark.e2e
    def test_e2e_004_default_pipeline(self):
        """
        E2E-004: Default pipeline with flags OFF (Backward Compatibility)
        """
        flags = FeatureFlags(
            debate_mode=False,
            adaptive_retrieval=False,
            meta_planner=False,
            tools_enabled=False
        )

        pipeline = Pipeline(flags=flags)
        result = pipeline.execute(input_data={})

        assert result is not None, "Default pipeline execution failed"
        assert result.is_complete, "Default pipeline did not complete"

    @pytest.mark.e2e
    def test_e2e_005_feature_flag_priority(self):
        """
        E2E-005: Feature Flag Priority (Debate > Tools)
        """
        flags = FeatureFlags(
            debate_mode=True,
            tools_enabled=False
        )

        pipeline = Pipeline(flags=flags)
        result = pipeline.execute(input_data={})

        assert result.active_steps[0] == "debate", "Debate mode did not take priority"

    @pytest.mark.e2e
    def test_e2e_006_meta_planner_debate_combination(self):
        """
        E2E-006: Meta-Planner + Debate Combination
        """
        flags = FeatureFlags(
            meta_planner=True,
            debate_mode=True
        )

        meta_planner = MetaPlanner(flags)
        debate = MultiAgentDebate(flags)

        planning_result = meta_planner.plan()
        debate_result = debate.start(planning_result.context)

        assert planning_result is not None, "Meta-Planner failed"
        assert debate_result.is_resolved, "Debate did not resolve"

    def teardown_method(self, method):
        """Reset configurations after each test"""
        load_config(reset=True)

if __name__ == "__main__":
    pytest.main(["-v", "test_phase_integration_e2e.py"])