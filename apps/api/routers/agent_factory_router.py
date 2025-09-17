"""
Agent Factory API Router for DT-RAG v1.8.1

Provides REST endpoints for dynamic agent creation and management including:
- Agent creation from taxonomy categories
- Agent configuration and customization
- Agent lifecycle management
- Agent performance monitoring
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import common schemas
import sys
from pathlib import Path as PathLib
sys.path.append(str(PathLib(__file__).parent.parent.parent.parent))

from packages.common_schemas.common_schemas.models import (
    FromCategoryRequest, AgentManifest, RetrievalConfig, FeaturesConfig
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
agent_factory_router = APIRouter(prefix="/agents", tags=["Agent Factory"])

# Additional models for agent operations

class AgentCreateResponse(BaseModel):
    """Response for agent creation"""
    agent_id: str
    name: str
    status: str
    capabilities: List[str]
    created_at: datetime

class AgentStatus(BaseModel):
    """Agent status information"""
    agent_id: str
    name: str
    status: str
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    performance_metrics: Dict[str, float]

class AgentMetrics(BaseModel):
    """Agent performance metrics"""
    total_requests: int
    avg_response_time_ms: float
    success_rate: float
    user_satisfaction: float
    cost_efficiency: float

class AgentListResponse(BaseModel):
    """Response for listing agents"""
    agents: List[AgentStatus]
    total: int
    active: int
    inactive: int

class AgentUpdateRequest(BaseModel):
    """Request to update agent configuration"""
    name: Optional[str] = None
    retrieval: Optional[RetrievalConfig] = None
    features: Optional[FeaturesConfig] = None
    mcp_tools_allowlist: Optional[List[str]] = None

# Mock agent factory service

class AgentFactoryService:
    """Mock agent factory service"""

    async def create_agent_from_category(self, request: FromCategoryRequest) -> AgentCreateResponse:
        """Create agent from taxonomy categories"""
        agent_id = str(uuid.uuid4())

        # Generate agent name from categories
        category_names = ["/".join(path) for path in request.node_paths]
        agent_name = f"Agent-{'-'.join(category_names[0].split('/')[:2])}"

        capabilities = [
            "document_search",
            "question_answering",
            "information_extraction",
            "content_summarization"
        ]

        return AgentCreateResponse(
            agent_id=agent_id,
            name=agent_name,
            status="created",
            capabilities=capabilities,
            created_at=datetime.utcnow()
        )

    async def list_agents(self, status_filter: Optional[str] = None) -> AgentListResponse:
        """List all agents"""
        agents = [
            AgentStatus(
                agent_id="agent-123",
                name="Agent-Technology-AI",
                status="active",
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=245,
                performance_metrics={
                    "avg_response_time": 1.89,
                    "success_rate": 0.94,
                    "user_satisfaction": 4.2
                }
            ),
            AgentStatus(
                agent_id="agent-456",
                name="Agent-Science-Biology",
                status="inactive",
                created_at=datetime.utcnow(),
                usage_count=67,
                performance_metrics={
                    "avg_response_time": 2.15,
                    "success_rate": 0.91,
                    "user_satisfaction": 4.0
                }
            )
        ]

        if status_filter:
            agents = [agent for agent in agents if agent.status == status_filter]

        return AgentListResponse(
            agents=agents,
            total=len(agents),
            active=sum(1 for a in agents if a.status == "active"),
            inactive=sum(1 for a in agents if a.status == "inactive")
        )

    async def get_agent(self, agent_id: str) -> Optional[AgentStatus]:
        """Get specific agent"""
        if agent_id == "agent-123":
            return AgentStatus(
                agent_id=agent_id,
                name="Agent-Technology-AI",
                status="active",
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=245,
                performance_metrics={
                    "avg_response_time": 1.89,
                    "success_rate": 0.94,
                    "user_satisfaction": 4.2
                }
            )
        return None

    async def update_agent(self, agent_id: str, update: AgentUpdateRequest) -> AgentStatus:
        """Update agent configuration"""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        # Update agent with new configuration
        if update.name:
            agent.name = update.name

        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent"""
        agent = await self.get_agent(agent_id)
        return agent is not None

    async def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get detailed agent metrics"""
        if agent_id == "agent-123":
            return AgentMetrics(
                total_requests=2456,
                avg_response_time_ms=1890.5,
                success_rate=0.943,
                user_satisfaction=4.2,
                cost_efficiency=0.85
            )
        return None

    async def get_factory_status(self) -> Dict[str, Any]:
        """Get agent factory status"""
        return {
            "status": "healthy",
            "total_agents": 12,
            "active_agents": 8,
            "requests_today": 1456,
            "avg_creation_time_seconds": 15.4,
            "resource_usage": {
                "cpu_percent": 45.2,
                "memory_mb": 1024.5
            }
        }

# Dependency injection
async def get_agent_factory_service() -> AgentFactoryService:
    """Get agent factory service instance"""
    return AgentFactoryService()

# API Endpoints

@agent_factory_router.post("/from-category", response_model=AgentCreateResponse)
async def create_agent_from_category(
    request: FromCategoryRequest,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Create specialized agent from taxonomy categories

    Creates an agent optimized for specific taxonomy categories with:
    - Customized retrieval configuration
    - Category-specific knowledge base
    - Tailored response generation
    - Performance optimization for domain
    """
    try:
        # Validate request
        if not request.node_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one node path is required"
            )

        # Validate taxonomy version exists
        # In real implementation, would check against taxonomy service

        # Create agent
        agent = await service.create_agent_from_category(request)

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )

@agent_factory_router.get("/", response_model=AgentListResponse)
async def list_agents(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum agents to return"),
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    List all agents with optional filtering

    Returns paginated list of agents with:
    - Basic agent information
    - Status and usage statistics
    - Performance metrics overview
    """
    try:
        agents_response = await service.list_agents(status)

        # Apply limit
        if len(agents_response.agents) > limit:
            agents_response.agents = agents_response.agents[:limit]

        return agents_response

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents"
        )

@agent_factory_router.get("/{agent_id}", response_model=AgentStatus)
async def get_agent(
    agent_id: str,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Get detailed information about specific agent

    Returns comprehensive agent information including:
    - Configuration and capabilities
    - Usage statistics and metrics
    - Performance data and trends
    """
    try:
        agent = await service.get_agent(agent_id)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found"
            )

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent"
        )

@agent_factory_router.put("/{agent_id}", response_model=AgentStatus)
async def update_agent(
    agent_id: str,
    update: AgentUpdateRequest,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Update agent configuration

    Allows modification of:
    - Agent name and description
    - Retrieval parameters
    - Feature settings
    - Tool allowlist
    """
    try:
        agent = await service.update_agent(agent_id, update)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found"
            )

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )

@agent_factory_router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Delete agent

    Permanently removes agent and all associated data.
    This action cannot be undone.
    """
    try:
        success = await service.delete_agent(agent_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found"
            )

        return {"message": f"Agent '{agent_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )

@agent_factory_router.get("/{agent_id}/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: str,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Get detailed performance metrics for agent

    Returns comprehensive metrics including:
    - Request volume and success rates
    - Response time analysis
    - User satisfaction scores
    - Cost efficiency metrics
    """
    try:
        metrics = await service.get_agent_metrics(agent_id)

        if metrics is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found or no metrics available"
            )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent metrics"
        )

@agent_factory_router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: str,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Activate agent for use

    Makes agent available for processing requests.
    Agent must be in 'inactive' or 'created' status.
    """
    try:
        agent = await service.get_agent(agent_id)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found"
            )

        if agent.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is already active"
            )

        # Activate agent (mock implementation)
        return {
            "message": f"Agent '{agent_id}' activated successfully",
            "status": "active"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate agent"
        )

@agent_factory_router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: str,
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Deactivate agent

    Stops agent from processing new requests.
    Existing requests will complete normally.
    """
    try:
        agent = await service.get_agent(agent_id)

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found"
            )

        if agent.status == "inactive":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is already inactive"
            )

        # Deactivate agent (mock implementation)
        return {
            "message": f"Agent '{agent_id}' deactivated successfully",
            "status": "inactive"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate agent"
        )

@agent_factory_router.get("/factory/status")
async def get_factory_status(
    service: AgentFactoryService = Depends(get_agent_factory_service)
):
    """
    Get agent factory system status

    Returns:
    - Factory health and capacity
    - Agent creation statistics
    - Resource usage information
    """
    try:
        status = await service.get_factory_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get factory status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve factory status"
        )

# Export router
__all__ = ["agent_factory_router"]