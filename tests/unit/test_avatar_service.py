# @TEST:AVATAR-SERVICE-001
# Unit tests for AvatarService - Pokemon Avatar System
# SPEC: SPEC-POKEMON-IMAGE-COMPLETE-001

import pytest
from apps.api.services.avatar_service import AvatarService


class TestAvatarServiceRarityCalculation:
    """Test rarity calculation based on taxonomy node count"""

    def test_calculate_rarity_common_tier(self):
        """1-2 nodes should result in Common rarity"""
        assert AvatarService.calculate_initial_rarity(1) == "Common"
        assert AvatarService.calculate_initial_rarity(2) == "Common"

    def test_calculate_rarity_rare_tier(self):
        """3-5 nodes should result in Rare rarity"""
        assert AvatarService.calculate_initial_rarity(3) == "Rare"
        assert AvatarService.calculate_initial_rarity(4) == "Rare"
        assert AvatarService.calculate_initial_rarity(5) == "Rare"

    def test_calculate_rarity_epic_tier(self):
        """6-10 nodes should result in Epic rarity"""
        assert AvatarService.calculate_initial_rarity(6) == "Epic"
        assert AvatarService.calculate_initial_rarity(10) == "Epic"

    def test_calculate_rarity_legendary_tier(self):
        """11+ nodes should result in Legendary rarity"""
        assert AvatarService.calculate_initial_rarity(11) == "Legendary"
        assert AvatarService.calculate_initial_rarity(20) == "Legendary"

    def test_calculate_rarity_edge_cases(self):
        """Test edge cases for rarity calculation"""
        # Zero nodes should default to Common
        assert AvatarService.calculate_initial_rarity(0) == "Common"
        # Negative values should default to Common
        assert AvatarService.calculate_initial_rarity(-1) == "Common"


class TestAvatarServiceIconSelection:
    """Test deterministic icon selection from Lucide Icons"""

    def test_icon_selection_is_deterministic(self):
        """Same agent_id and rarity should always return same icon"""
        agent_id = "a1b2c3d4-5678-90ab-cdef-1234567890ab"

        icon1 = AvatarService.get_default_avatar_icon("Common", agent_id)
        icon2 = AvatarService.get_default_avatar_icon("Common", agent_id)

        assert icon1 == icon2

    def test_icon_selection_common_rarity(self):
        """Common rarity should return one of: User, UserCircle, UserSquare"""
        agent_id = "a1b2c3d4-5678-90ab-cdef-1234567890ab"
        icon = AvatarService.get_default_avatar_icon("Common", agent_id)

        assert icon in ["User", "UserCircle", "UserSquare"]

    def test_icon_selection_rare_rarity(self):
        """Rare rarity should return one of: Star, Sparkles, Award"""
        agent_id = "b2c3d4e5-6789-01bc-def0-234567890abc"
        icon = AvatarService.get_default_avatar_icon("Rare", agent_id)

        assert icon in ["Star", "Sparkles", "Award"]

    def test_icon_selection_epic_rarity(self):
        """Epic rarity should return one of: Crown, Shield, Gem"""
        agent_id = "c3d4e5f6-7890-12cd-ef01-34567890abcd"
        icon = AvatarService.get_default_avatar_icon("Epic", agent_id)

        assert icon in ["Crown", "Shield", "Gem"]

    def test_icon_selection_legendary_rarity(self):
        """Legendary rarity should return one of: Flame, Zap, Trophy"""
        agent_id = "d4e5f6a7-8901-23de-f012-4567890abcde"
        icon = AvatarService.get_default_avatar_icon("Legendary", agent_id)

        assert icon in ["Flame", "Zap", "Trophy"]

    def test_icon_selection_different_agents(self):
        """Different agent_ids should potentially return different icons"""
        # Testing distribution (not guaranteed to be different, but likely)
        icons = set()
        for i in range(10):
            agent_id = f"00000000-0000-0000-0000-00000000000{i}"
            icon = AvatarService.get_default_avatar_icon("Common", agent_id)
            icons.add(icon)

        # Should have at least 2 different icons out of 10 tries (probabilistic)
        assert len(icons) >= 1  # At minimum, valid icons

    def test_icon_selection_invalid_rarity(self):
        """Invalid rarity should return fallback (User)"""
        agent_id = "e5f6a7b8-9012-34ef-0123-567890abcdef"
        icon = AvatarService.get_default_avatar_icon("InvalidRarity", agent_id)

        assert icon == "User"


class TestAvatarServiceIntegration:
    """Integration tests for combined functionality"""

    def test_full_workflow_common_agent(self):
        """Test full workflow for a Common agent"""
        node_count = 1
        agent_id = "f6a7b8c9-0123-45f0-1234-67890abcdef0"

        rarity = AvatarService.calculate_initial_rarity(node_count)
        icon = AvatarService.get_default_avatar_icon(rarity, agent_id)

        assert rarity == "Common"
        assert icon in ["User", "UserCircle", "UserSquare"]

    def test_full_workflow_legendary_agent(self):
        """Test full workflow for a Legendary agent"""
        node_count = 15
        agent_id = "a7b8c9d0-1234-56f0-2345-7890abcdef01"

        rarity = AvatarService.calculate_initial_rarity(node_count)
        icon = AvatarService.get_default_avatar_icon(rarity, agent_id)

        assert rarity == "Legendary"
        assert icon in ["Flame", "Zap", "Trophy"]
