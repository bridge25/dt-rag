# @TEST:RESEARCH-BACKEND-001:SCHEMA
"""
Tests for Research Session Schema Models

This test module validates:
1. Pydantic model validation and serialization
2. Field aliasing for frontend compatibility
3. Enum validation
4. Default values
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from apps.api.schemas.research_schemas import (
    ResearchConfig,
    StartResearchRequest,
    ConfirmResearchRequest,
    StartResearchResponse,
    ResearchStage,
    ResearchSession,
)


class TestResearchConfig:
    """Test ResearchConfig model validation"""

    def test_create_with_defaults(self):
        """Test creating ResearchConfig with default values"""
        config = ResearchConfig()
        assert config.max_documents == 50
        assert config.quality_threshold == 0.7
        assert config.sources_filter is None
        assert config.depth_level == "medium"

    def test_create_with_custom_values(self):
        """Test creating ResearchConfig with custom values"""
        config = ResearchConfig(
            max_documents=100,
            quality_threshold=0.8,
            sources_filter=["web", "pdf"],
            depth_level="deep"
        )
        assert config.max_documents == 100
        assert config.quality_threshold == 0.8
        assert config.sources_filter == ["web", "pdf"]
        assert config.depth_level == "deep"

    def test_field_alias_camel_case(self):
        """Test field aliasing for camelCase input"""
        config = ResearchConfig.model_validate({
            "maxDocuments": 75,
            "qualityThreshold": 0.9,
            "sourcesFilter": ["api"],
            "depthLevel": "shallow"
        })
        assert config.max_documents == 75
        assert config.quality_threshold == 0.9
        assert config.sources_filter == ["api"]
        assert config.depth_level == "shallow"

    def test_json_serialization_uses_aliases(self):
        """Test that JSON serialization uses camelCase aliases"""
        config = ResearchConfig(
            max_documents=60,
            quality_threshold=0.75
        )
        data = config.model_dump(by_alias=True)
        assert "maxDocuments" in data
        assert "qualityThreshold" in data
        assert data["maxDocuments"] == 60

    def test_invalid_quality_threshold(self):
        """Test validation of quality_threshold range"""
        with pytest.raises(ValidationError):
            ResearchConfig(quality_threshold=1.5)

    def test_invalid_depth_level(self):
        """Test validation of depth_level enum"""
        with pytest.raises(ValidationError):
            ResearchConfig(depth_level="invalid")


class TestStartResearchRequest:
    """Test StartResearchRequest model"""

    def test_create_minimal(self):
        """Test creating request with only required fields"""
        request = StartResearchRequest(query="cancer treatment")
        assert request.query == "cancer treatment"
        assert request.config is None

    def test_create_with_config(self):
        """Test creating request with config"""
        config = ResearchConfig(max_documents=100)
        request = StartResearchRequest(
            query="cancer treatment",
            config=config
        )
        assert request.query == "cancer treatment"
        assert request.config.max_documents == 100

    def test_query_required(self):
        """Test that query is required"""
        with pytest.raises(ValidationError):
            StartResearchRequest()

    def test_empty_query_rejected(self):
        """Test that empty query is rejected"""
        with pytest.raises(ValidationError):
            StartResearchRequest(query="")


class TestConfirmResearchRequest:
    """Test ConfirmResearchRequest model"""

    def test_create_minimal(self):
        """Test creating request with required fields"""
        request = ConfirmResearchRequest(
            selected_document_ids=["doc1", "doc2"]
        )
        assert request.selected_document_ids == ["doc1", "doc2"]
        assert request.taxonomy_id is None

    def test_field_alias_camel_case(self):
        """Test camelCase alias for selectedDocumentIds"""
        request = ConfirmResearchRequest.model_validate({
            "selectedDocumentIds": ["doc1", "doc2"],
            "taxonomyId": "tax-123"
        })
        assert request.selected_document_ids == ["doc1", "doc2"]
        assert request.taxonomy_id == "tax-123"

    def test_selected_documents_required(self):
        """Test that selected_document_ids is required"""
        with pytest.raises(ValidationError):
            ConfirmResearchRequest()

    def test_empty_documents_rejected(self):
        """Test that empty document list is rejected"""
        with pytest.raises(ValidationError):
            ConfirmResearchRequest(selected_document_ids=[])


class TestStartResearchResponse:
    """Test StartResearchResponse model"""

    def test_create_response(self):
        """Test creating response"""
        response = StartResearchResponse(
            session_id="sess-123",
            estimated_duration=300
        )
        assert response.session_id == "sess-123"
        assert response.estimated_duration == 300

    def test_json_serialization_uses_aliases(self):
        """Test that JSON uses camelCase aliases"""
        response = StartResearchResponse(
            session_id="sess-123",
            estimated_duration=300
        )
        data = response.model_dump(by_alias=True)
        assert "sessionId" in data
        assert "estimatedDuration" in data
        assert data["sessionId"] == "sess-123"


class TestResearchStageEnum:
    """Test ResearchStage enum"""

    def test_all_stages_defined(self):
        """Test that all required stages are defined"""
        assert hasattr(ResearchStage, "IDLE")
        assert hasattr(ResearchStage, "ANALYZING")
        assert hasattr(ResearchStage, "SEARCHING")
        assert hasattr(ResearchStage, "COLLECTING")
        assert hasattr(ResearchStage, "ORGANIZING")
        assert hasattr(ResearchStage, "CONFIRMING")
        assert hasattr(ResearchStage, "COMPLETED")
        assert hasattr(ResearchStage, "ERROR")

    def test_stage_values(self):
        """Test stage enum values"""
        assert ResearchStage.IDLE.value == "idle"
        assert ResearchStage.ANALYZING.value == "analyzing"
        assert ResearchStage.SEARCHING.value == "searching"
        assert ResearchStage.COLLECTING.value == "collecting"
        assert ResearchStage.ORGANIZING.value == "organizing"
        assert ResearchStage.CONFIRMING.value == "confirming"
        assert ResearchStage.COMPLETED.value == "completed"
        assert ResearchStage.ERROR.value == "error"


class TestResearchSession:
    """Test ResearchSession model"""

    def test_create_session(self):
        """Test creating a research session"""
        now = datetime.now()
        session = ResearchSession(
            id="sess-123",
            query="cancer treatment",
            stage=ResearchStage.ANALYZING,
            progress=0.5,
            documents=[],
            events=[]
        )
        assert session.id == "sess-123"
        assert session.query == "cancer treatment"
        assert session.stage == ResearchStage.ANALYZING
        assert session.progress == 0.5
        assert session.documents == []
        assert session.events == []

    def test_session_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValidationError):
            ResearchSession()

    def test_session_progress_validation(self):
        """Test progress field is between 0 and 1"""
        with pytest.raises(ValidationError):
            ResearchSession(
                id="sess-123",
                query="test",
                stage=ResearchStage.IDLE,
                progress=1.5,
                documents=[],
                events=[]
            )

    def test_session_progress_zero_allowed(self):
        """Test that progress=0 is valid"""
        session = ResearchSession(
            id="sess-123",
            query="test",
            stage=ResearchStage.IDLE,
            progress=0.0,
            documents=[],
            events=[]
        )
        assert session.progress == 0.0

    def test_session_progress_one_allowed(self):
        """Test that progress=1 is valid"""
        session = ResearchSession(
            id="sess-123",
            query="test",
            stage=ResearchStage.IDLE,
            progress=1.0,
            documents=[],
            events=[]
        )
        assert session.progress == 1.0
