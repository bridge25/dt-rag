# @SPEC:FOUNDATION-001 @TEST:0.1-feature-flags
"""
Unit tests for Feature Flags (SPEC-FOUNDATION-001)

Tests new feature flags:
- PRD 1.5P flags (4개): neural_case_selector, soft_q_bandit, debate_mode, tools_policy
- Memento flags (3개): meta_planner, mcp_tools, experience_replay
"""

import pytest
from apps.api.env_manager import get_env_manager


pytestmark = pytest.mark.unit


class TestFeatureFlags:
    """Test feature flags functionality"""

    def setup_method(self):
        """Setup for each test - clear env manager cache"""
        global _env_manager
        from apps.api import env_manager as em_module

        em_module._env_manager = None

    def test_new_flags_exist(self):
        """TEST-FLAG-001: 7개 신규 Flag 존재 확인"""
        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        # PRD 1.5P flags (4개)
        assert "neural_case_selector" in flags
        assert "soft_q_bandit" in flags
        assert "debate_mode" in flags
        assert "tools_policy" in flags

        # Memento flags (3개)
        assert "meta_planner" in flags
        assert "mcp_tools" in flags
        assert "experience_replay" in flags

    def test_flags_default_false(self):
        """TEST-FLAG-002: 모든 신규 Flag 기본값 False"""
        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        # PRD 1.5P flags
        assert flags["neural_case_selector"] is False
        assert flags["soft_q_bandit"] is False
        assert flags["debate_mode"] is False
        assert flags["tools_policy"] is False

        # Memento flags
        assert flags["meta_planner"] is False
        assert flags["mcp_tools"] is False
        assert flags["experience_replay"] is False

    def test_env_override_debate_mode(self, monkeypatch):
        """TEST-FLAG-003: 환경 변수 FEATURE_DEBATE_MODE=true 시 Override"""
        monkeypatch.setenv("FEATURE_DEBATE_MODE", "true")

        from apps.api import env_manager as em_module

        em_module._env_manager = None

        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        assert flags["debate_mode"] is True

    def test_env_override_meta_planner(self, monkeypatch):
        """TEST-FLAG-004: 환경 변수 FEATURE_META_PLANNER=1 시 Override"""
        monkeypatch.setenv("FEATURE_META_PLANNER", "1")

        from apps.api import env_manager as em_module

        em_module._env_manager = None

        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        assert flags["meta_planner"] is True

    def test_env_override_false(self, monkeypatch):
        """TEST-FLAG-005: 환경 변수 FEATURE_DEBATE_MODE=false 시 명시적 False"""
        monkeypatch.setenv("FEATURE_DEBATE_MODE", "false")

        from apps.api import env_manager as em_module

        em_module._env_manager = None

        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        assert flags["debate_mode"] is False

    def test_existing_flags_unchanged(self):
        """TEST-FLAG-006: 기존 8개 Flag 값 불변"""
        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        # 기존 flags 존재 확인
        expected_existing = [
            "enable_swagger_ui",
            "enable_redoc",
            "enable_metrics",
            "enable_rate_limiting",
            "enable_request_logging",
            "enable_error_tracking",
            "enable_debug_toolbar",
            "enable_profiling",
        ]

        for flag in expected_existing:
            assert flag in flags

    def test_multiple_env_overrides(self, monkeypatch):
        """TEST-FLAG-007: 여러 환경 변수 동시 Override"""
        monkeypatch.setenv("FEATURE_DEBATE_MODE", "true")
        monkeypatch.setenv("FEATURE_TOOLS_POLICY", "yes")
        monkeypatch.setenv("FEATURE_META_PLANNER", "1")

        from apps.api import env_manager as em_module

        em_module._env_manager = None

        env_mgr = get_env_manager()
        flags = env_mgr.get_feature_flags()

        assert flags["debate_mode"] is True
        assert flags["tools_policy"] is True
        assert flags["meta_planner"] is True

        # 나머지는 여전히 False
        assert flags["neural_case_selector"] is False
        assert flags["soft_q_bandit"] is False
        assert flags["mcp_tools"] is False
        assert flags["experience_replay"] is False
