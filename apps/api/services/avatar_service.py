# @CODE:AVATAR-SERVICE-001
# AvatarService - Pokemon Avatar System
# SPEC: SPEC-POKEMON-IMAGE-COMPLETE-001

"""
AvatarService provides deterministic avatar icon selection and rarity calculation
for Agent Card Pokemon-style avatars.

Key Features:
- Calculate initial rarity based on taxonomy node count
- Select deterministic Lucide Icon based on agent_id hash
- Match Frontend's icon selection algorithm (getDefaultAvatarIcon in types.ts)
"""

from typing import Literal

# Type alias for valid rarity values
Rarity = Literal["Common", "Rare", "Epic", "Legendary"]


class AvatarService:
    """Service for managing Pokemon-style agent avatars"""

    # Rarity icon mapping (must match frontend/src/lib/api/types.ts)
    RARITY_ICONS = {
        "Common": ["User", "UserCircle", "UserSquare"],
        "Rare": ["Star", "Sparkles", "Award"],
        "Epic": ["Crown", "Shield", "Gem"],
        "Legendary": ["Flame", "Zap", "Trophy"],
    }

    @staticmethod
    def calculate_initial_rarity(taxonomy_node_count: int) -> str:
        """
        Calculate agent rarity based on taxonomy node coverage.

        Rarity Tiers:
        - Common: 1-2 nodes
        - Rare: 3-5 nodes
        - Epic: 6-10 nodes
        - Legendary: 11+ nodes

        Args:
            taxonomy_node_count: Number of taxonomy nodes assigned to agent

        Returns:
            Rarity string: "Common" | "Rare" | "Epic" | "Legendary"

        Examples:
            >>> AvatarService.calculate_initial_rarity(1)
            'Common'
            >>> AvatarService.calculate_initial_rarity(15)
            'Legendary'
        """
        if taxonomy_node_count <= 0:
            return "Common"
        elif taxonomy_node_count <= 2:
            return "Common"
        elif taxonomy_node_count <= 5:
            return "Rare"
        elif taxonomy_node_count <= 10:
            return "Epic"
        else:
            return "Legendary"

    @staticmethod
    def get_default_avatar_icon(rarity: str, agent_id: str) -> str:
        """
        Get deterministic Lucide Icon name based on rarity and agent_id.

        Uses hash-based selection to ensure:
        1. Same agent_id + rarity always returns same icon
        2. Different agents get different icons (distributed)
        3. Algorithm matches Frontend implementation

        Args:
            rarity: Agent rarity tier
            agent_id: UUID string (e.g., "a1b2c3d4-5678-90ab-cdef-1234567890ab")

        Returns:
            Lucide Icon name (e.g., "Star", "Crown", "Flame")

        Examples:
            >>> AvatarService.get_default_avatar_icon("Common", "a1b2c3d4-5678-90ab-cdef-1234567890ab")
            'User'  # Deterministic based on hash
        """
        # Validate rarity
        if rarity not in AvatarService.RARITY_ICONS:
            return "User"  # Fallback for invalid rarity

        # Extract first UUID segment for hash (matches frontend algorithm)
        # Frontend: const hash = agentId.split('-')[0] || '0'
        hash_segment = agent_id.split("-")[0] if agent_id else "0"

        # Convert hex to int and modulo 3 to get index 0-2
        # Frontend: const index = (parseInt(hash, 16) % 3)
        try:
            index = int(hash_segment, 16) % 3
        except ValueError:
            index = 0  # Fallback for invalid UUID format

        # Return icon from rarity's icon pool
        icon_pool = AvatarService.RARITY_ICONS[rarity]
        return icon_pool[index]
