"""
@TEST:POKEMON-IMAGE-COMPLETE-001-SCHEMA-001 | Phase 2-1 Pydantic Schema Tests

RED Phase: Tests for avatar_url, rarity, character_description fields in AgentResponse schema.
Tests Pydantic schema validation for Pokemon avatar feature.
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import ValidationError
from apps.api.schemas.agent_schemas import AgentResponse, AgentCreateRequest, AgentUpdateRequest


class TestPokemonAvatarSchemas:
    """Test suite for SPEC-POKEMON-IMAGE-COMPLETE-001 Phase 2-1 Pydantic Schemas"""

    def test_agent_response_has_avatar_fields(self):
        """
        RED Test: Verify AgentResponse schema includes avatar_url, rarity, character_description

        Expected:
        - avatar_url: Optional[str] (max 500 characters)
        - rarity: Literal["Common", "Rare", "Epic", "Legendary"] (default="Common")
        - character_description: Optional[str] (max 500 characters)
        """
        # Create valid agent response data
        agent_data = {
            "agent_id": str(uuid4()),
            "name": "Test Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "scope_description": "Test scope",
            "total_documents": 100,
            "total_chunks": 500,
            "coverage_percent": 75.5,
            "last_coverage_update": datetime.utcnow().isoformat(),
            "level": 3,
            "current_xp": 1500,
            "total_queries": 50,
            "successful_queries": 48,
            "avg_faithfulness": 0.92,
            "avg_response_time_ms": 250.5,
            "retrieval_config": {"top_k": 10, "strategy": "hybrid"},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_query_at": datetime.utcnow().isoformat(),
            # NEW FIELDS
            "avatar_url": "/avatars/epic/default-2.png",
            "rarity": "Epic",
            "character_description": "A powerful Epic-tier agent with advanced capabilities",
        }

        # Should parse successfully
        agent_response = AgentResponse(**agent_data)

        # Verify new fields exist
        assert hasattr(agent_response, "avatar_url"), "AgentResponse should have avatar_url field"
        assert hasattr(agent_response, "rarity"), "AgentResponse should have rarity field"
        assert hasattr(agent_response, "character_description"), "AgentResponse should have character_description field"

        # Verify field values
        assert agent_response.avatar_url == "/avatars/epic/default-2.png"
        assert agent_response.rarity == "Epic"
        assert agent_response.character_description == "A powerful Epic-tier agent with advanced capabilities"

    def test_agent_response_avatar_url_optional(self):
        """
        RED Test: Verify avatar_url is optional (nullable)

        Expected:
        - avatar_url=None should be valid
        - Missing avatar_url should be valid
        """
        agent_data_minimal = {
            "agent_id": str(uuid4()),
            "name": "Minimal Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "total_documents": 0,
            "total_chunks": 0,
            "coverage_percent": 0.0,
            "level": 1,
            "current_xp": 0,
            "total_queries": 0,
            "successful_queries": 0,
            "avg_faithfulness": 0.0,
            "avg_response_time_ms": 0.0,
            "retrieval_config": {},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            # avatar_url NOT provided
        }

        agent_response = AgentResponse(**agent_data_minimal)
        assert agent_response.avatar_url is None, "avatar_url should default to None if not provided"

    def test_agent_response_rarity_default(self):
        """
        RED Test: Verify rarity defaults to 'Common' if not provided

        Expected:
        - rarity="Common" when not specified
        """
        agent_data_no_rarity = {
            "agent_id": str(uuid4()),
            "name": "Default Rarity Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "total_documents": 10,
            "total_chunks": 50,
            "coverage_percent": 25.0,
            "level": 1,
            "current_xp": 100,
            "total_queries": 5,
            "successful_queries": 5,
            "avg_faithfulness": 0.85,
            "avg_response_time_ms": 200.0,
            "retrieval_config": {},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            # rarity NOT provided
        }

        agent_response = AgentResponse(**agent_data_no_rarity)
        assert agent_response.rarity == "Common", "rarity should default to 'Common' if not provided"

    def test_agent_response_rarity_validation(self):
        """
        RED Test: Verify rarity field rejects invalid values

        Expected:
        - Only accepts: "Common", "Rare", "Epic", "Legendary"
        - Rejects: "Ultra", "Mythic", "bronze", etc.
        """
        agent_data_invalid_rarity = {
            "agent_id": str(uuid4()),
            "name": "Invalid Rarity Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "total_documents": 10,
            "total_chunks": 50,
            "coverage_percent": 25.0,
            "level": 2,
            "current_xp": 500,
            "total_queries": 10,
            "successful_queries": 9,
            "avg_faithfulness": 0.88,
            "avg_response_time_ms": 220.0,
            "retrieval_config": {},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "rarity": "Ultra",  # INVALID
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentResponse(**agent_data_invalid_rarity)

        # Verify error mentions rarity field
        error_details = exc_info.value.errors()
        rarity_error = next((e for e in error_details if e["loc"] == ("rarity",)), None)
        assert rarity_error is not None, "ValidationError should mention 'rarity' field"

    def test_agent_response_avatar_url_max_length(self):
        """
        RED Test: Verify avatar_url enforces 500 character limit

        Expected:
        - Strings ≤ 500 characters: valid
        - Strings > 500 characters: rejected
        """
        long_url = "https://example.com/avatars/" + "a" * 500  # 528 characters total

        agent_data_long_url = {
            "agent_id": str(uuid4()),
            "name": "Long URL Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "total_documents": 10,
            "total_chunks": 50,
            "coverage_percent": 25.0,
            "level": 1,
            "current_xp": 100,
            "total_queries": 5,
            "successful_queries": 5,
            "avg_faithfulness": 0.85,
            "avg_response_time_ms": 200.0,
            "retrieval_config": {},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "avatar_url": long_url,
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentResponse(**agent_data_long_url)

        # Verify error mentions avatar_url field
        error_details = exc_info.value.errors()
        url_error = next((e for e in error_details if "avatar_url" in str(e["loc"])), None)
        assert url_error is not None, "ValidationError should mention 'avatar_url' field"

    def test_agent_response_character_description_max_length(self):
        """
        RED Test: Verify character_description enforces 500 character limit

        Expected:
        - Strings ≤ 500 characters: valid
        - Strings > 500 characters: rejected
        """
        long_description = "A" * 501  # 501 characters

        agent_data_long_desc = {
            "agent_id": str(uuid4()),
            "name": "Long Description Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "total_documents": 10,
            "total_chunks": 50,
            "coverage_percent": 25.0,
            "level": 1,
            "current_xp": 100,
            "total_queries": 5,
            "successful_queries": 5,
            "avg_faithfulness": 0.85,
            "avg_response_time_ms": 200.0,
            "retrieval_config": {},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "character_description": long_description,
        }

        with pytest.raises(ValidationError) as exc_info:
            AgentResponse(**agent_data_long_desc)

        # Verify error mentions character_description field
        error_details = exc_info.value.errors()
        desc_error = next((e for e in error_details if "character_description" in str(e["loc"])), None)
        assert desc_error is not None, "ValidationError should mention 'character_description' field"

    def test_agent_create_request_no_avatar_fields(self):
        """
        RED Test: Verify AgentCreateRequest does NOT require avatar fields (backend assigns defaults)

        Expected:
        - avatar_url, rarity, character_description are NOT in AgentCreateRequest
        - Backend handles avatar assignment automatically
        """
        create_data = {
            "name": "New Agent",
            "taxonomy_node_ids": [uuid4()],
        }

        # Should parse successfully without avatar fields
        create_request = AgentCreateRequest(**create_data)
        assert create_request.name == "New Agent"

        # Verify avatar fields are NOT in schema
        assert not hasattr(create_request, "avatar_url"), (
            "AgentCreateRequest should NOT have avatar_url field (backend assigns automatically)"
        )

    def test_agent_update_request_supports_avatar_fields(self):
        """
        RED Test: Verify AgentUpdateRequest allows updating avatar fields (optional)

        Expected:
        - avatar_url: Optional[str]
        - rarity: Optional[Literal["Common", "Rare", "Epic", "Legendary"]]
        - character_description: Optional[str]
        """
        update_data = {
            "name": "Updated Agent Name",
            "avatar_url": "/avatars/rare/default-3.png",
            "rarity": "Rare",
            "character_description": "Updated character description",
        }

        update_request = AgentUpdateRequest(**update_data)

        # Verify avatar fields exist and are updatable
        assert hasattr(update_request, "avatar_url"), "AgentUpdateRequest should have avatar_url field"
        assert hasattr(update_request, "rarity"), "AgentUpdateRequest should have rarity field"
        assert hasattr(update_request, "character_description"), "AgentUpdateRequest should have character_description field"

        assert update_request.avatar_url == "/avatars/rare/default-3.png"
        assert update_request.rarity == "Rare"
        assert update_request.character_description == "Updated character description"

    def test_all_rarity_values_valid(self):
        """
        RED Test: Verify all 4 rarity values are accepted

        Expected:
        - "Common" → valid
        - "Rare" → valid
        - "Epic" → valid
        - "Legendary" → valid
        """
        base_data = {
            "agent_id": str(uuid4()),
            "name": "Rarity Test Agent",
            "taxonomy_node_ids": [str(uuid4())],
            "taxonomy_version": "1.0.0",
            "total_documents": 10,
            "total_chunks": 50,
            "coverage_percent": 25.0,
            "level": 1,
            "current_xp": 100,
            "total_queries": 5,
            "successful_queries": 5,
            "avg_faithfulness": 0.85,
            "avg_response_time_ms": 200.0,
            "retrieval_config": {},
            "features_config": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        for rarity in ["Common", "Rare", "Epic", "Legendary"]:
            agent_data = {**base_data, "rarity": rarity}
            agent_response = AgentResponse(**agent_data)
            assert agent_response.rarity == rarity, f"Rarity '{rarity}' should be valid"
