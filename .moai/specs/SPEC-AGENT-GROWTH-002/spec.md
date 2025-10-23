---
id: AGENT-GROWTH-002
version: 1.0.0
status: completed
created: 2025-10-12
updated: 2025-10-23
author: @sonheungmin
priority: high
category: feature
labels:
  - api
  - rest
  - fastapi
  - agent-growth
depends_on:
  - AGENT-GROWTH-001
scope:
  packages:
    - apps/api/routers
    - apps/api/schemas
  files:
    - agent_router.py
    - agent_schemas.py
---

# @SPEC:AGENT-GROWTH-002: Agent Growth Platform Phase 1 - REST API Integration

## HISTORY

### v0.1.0 (2025-10-12)
- **INITIAL**: REST API 엔드포인트 명세 최초 작성
- **AUTHOR**: @sonheungmin
- **SCOPE**: 4개 Agent API (Creation, Coverage, Gap Detection, Query)
- **CONTEXT**: Phase 0 백엔드 로직을 FastAPI REST API로 노출
- **DEPENDENCIES**: SPEC-AGENT-GROWTH-001 (AgentDAO, CoverageMeterService, Agent ORM)

## Environment

- **Backend Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 12+ (agents 테이블 from Phase 0)
- **Authentication**: API Key (기존 `apps/api/security.py` 활용)
- **Documentation**: OpenAPI 3.0 (Swagger UI 자동 생성)
- **Python Version**: 3.9+
- **Phase 0 Prerequisites**:
  - agents 테이블 생성 완료 (Alembic migration 실행)
  - AgentDAO.create_agent(), get_agent(), update_agent(), list_agents()
  - CoverageMeterService.calculate_coverage(), detect_gaps()
  - Agent ORM model with 19 columns

## Assumptions

1. **Phase 0 Complete**: SPEC-AGENT-GROWTH-001 구현 완료 (AgentDAO, CoverageMeterService, agents 테이블)
2. **FastAPI Router Pattern**: `apps/api/routers/` 디렉터리 구조 활용, include_router() 방식
3. **API Key Authentication**: 기존 `apps/api/security.py`의 `get_api_key()` 의존성 재사용
4. **Error Handling**: 기존 `apps/api/exceptions.py`의 HTTPException 패턴 준수
5. **Pydantic Validation**: Request/Response schema는 Pydantic v2 BaseModel 사용
6. **Async Database**: AsyncSession 기반 비동기 DB 호출 (기존 패턴 유지)
7. **CORS**: 기존 CORS 설정 유지 (`app.add_middleware(CORSMiddleware)`)

## EARS Requirements

### Ubiquitous Requirements (Core API Structure)

**U-REQ-001**: System SHALL provide POST /api/v1/agents/from-taxonomy endpoint accepting AgentCreateRequest returning AgentResponse with 201 Created status.

**U-REQ-002**: System SHALL provide GET /api/v1/agents/{agent_id} endpoint accepting UUID agent_id returning AgentResponse with 200 OK status.

**U-REQ-003**: System SHALL provide GET /api/v1/agents endpoint accepting optional query parameters (level, min_coverage, max_results) returning AgentListResponse with 200 OK status.

**U-REQ-004**: System SHALL provide GET /api/v1/agents/{agent_id}/coverage endpoint accepting UUID agent_id returning CoverageResponse with 200 OK status.

**U-REQ-005**: System SHALL provide GET /api/v1/agents/{agent_id}/gaps endpoint accepting UUID agent_id and optional float threshold query parameter returning GapListResponse with 200 OK status.

**U-REQ-006**: System SHALL provide POST /api/v1/agents/{agent_id}/query endpoint accepting UUID agent_id and QueryRequest returning QueryResponse with 200 OK status.

**U-REQ-007**: System SHALL require API Key authentication for all endpoints via `Depends(get_api_key)` dependency.

**U-REQ-008**: System SHALL use Pydantic BaseModel for all request/response schemas with strict validation.

**U-REQ-009**: System SHALL generate OpenAPI 3.0 documentation accessible at /docs (Swagger UI) and /redoc (ReDoc).

**U-REQ-010**: System SHALL follow RESTful naming convention: resource plural nouns (`/agents`), action verbs in POST endpoint names (`/from-taxonomy`, `/query`).

### Event-driven Requirements (API Lifecycle)

**E-REQ-001**: WHEN POST /agents/from-taxonomy receives valid AgentCreateRequest, System SHALL call AgentDAO.create_agent() with parameters (name, taxonomy_node_ids, taxonomy_version, scope_description, retrieval_config, features_config) and return 201 Created with AgentResponse body.

**E-REQ-002**: WHEN POST /agents/from-taxonomy receives request with non-existent taxonomy_node_ids, System SHALL return 400 Bad Request with error message "Invalid taxonomy node IDs: {invalid_ids}".

**E-REQ-003**: WHEN POST /agents/from-taxonomy receives request with empty name or taxonomy_node_ids, System SHALL return 422 Unprocessable Entity with Pydantic validation errors.

**E-REQ-004**: WHEN GET /agents/{agent_id} receives valid UUID, System SHALL call AgentDAO.get_agent(agent_id) and return 200 OK with AgentResponse body.

**E-REQ-005**: WHEN GET /agents/{agent_id} receives non-existent agent_id, System SHALL return 404 Not Found with error message "Agent not found: {agent_id}".

**E-REQ-006**: WHEN GET /agents receives query parameters, System SHALL call AgentDAO.list_agents(level, min_coverage, max_results) and return 200 OK with AgentListResponse body containing agents array.

**E-REQ-007**: WHEN GET /agents/{agent_id}/coverage is invoked, System SHALL call CoverageMeterService.calculate_coverage(agent_id, agent.taxonomy_node_ids, agent.taxonomy_version) and return 200 OK with CoverageResponse body.

**E-REQ-008**: WHEN GET /agents/{agent_id}/coverage completes, System SHALL call AgentDAO.update_agent() to refresh cached coverage_percent and last_coverage_update fields in agents table.

**E-REQ-009**: WHEN GET /agents/{agent_id}/gaps receives threshold query parameter, System SHALL call CoverageMeterService.detect_gaps(coverage_result, threshold) and return 200 OK with GapListResponse body.

**E-REQ-010**: WHEN GET /agents/{agent_id}/gaps receives no threshold, System SHALL use default threshold 0.5 (50% coverage).

**E-REQ-011**: WHEN POST /agents/{agent_id}/query receives QueryRequest, System SHALL call SearchDAO.hybrid_search(query, filters={"canonical_in": agent.taxonomy_node_ids, "version": agent.taxonomy_version}, top_k=agent.retrieval_config.get("top_k", 5)) and return 200 OK with QueryResponse body.

**E-REQ-012**: WHEN POST /agents/{agent_id}/query completes, System SHALL call AgentDAO.update_agent() to increment total_queries and update last_query_at timestamp.

**E-REQ-013**: WHEN any endpoint encounters database connection error, System SHALL return 503 Service Unavailable with error message "Database temporarily unavailable".

**E-REQ-014**: WHEN any endpoint encounters unexpected exception, System SHALL log full traceback and return 500 Internal Server Error with generic error message (no sensitive data exposure).

**E-REQ-015**: WHEN API Key is missing or invalid, System SHALL return 401 Unauthorized with error message "Invalid or missing API key".

### State-driven Requirements (API Behavior)

**S-REQ-001**: WHILE agent exists in database, GET /agents/{agent_id} SHALL return agent data with 200 status.

**S-REQ-002**: WHILE agent does not exist, GET /agents/{agent_id} SHALL return 404 Not Found.

**S-REQ-003**: WHILE coverage is being calculated, GET /agents/{agent_id}/coverage SHALL execute synchronously (no background task) and block until completion.

**S-REQ-004**: WHILE gaps list is empty (all nodes above threshold), GET /agents/{agent_id}/gaps SHALL return 200 OK with empty gaps array (not 404).

**S-REQ-005**: WHILE query is being processed, POST /agents/{agent_id}/query SHALL stream results if streaming=true in QueryRequest, otherwise return complete response.

**S-REQ-006**: WHILE agent has retrieval_config.top_k set, POST /agents/{agent_id}/query SHALL use that value for SearchDAO.hybrid_search(), otherwise default to 5.

**S-REQ-007**: WHILE agent has taxonomy_node_ids, POST /agents/{agent_id}/query SHALL filter SearchDAO results to only include documents within agent scope.

**S-REQ-008**: WHILE using OpenAPI documentation, /docs SHALL display all endpoint schemas with example requests/responses generated from Pydantic models.

**S-REQ-009**: WHILE using CORS, System SHALL allow origins configured in CORS_ORIGINS environment variable (default: ["http://localhost:3000"]).

**S-REQ-010**: WHILE validating UUIDs, System SHALL use Pydantic UUID4 type for automatic validation (invalid UUIDs return 422 before DAO call).

### Optional Features (Future Enhancements)

**O-REQ-001**: WHERE user requests background coverage calculation, POST /agents/{agent_id}/coverage/refresh MAY accept background=true parameter to return 202 Accepted immediately.

**O-REQ-002**: WHERE user requests agent update, PATCH /agents/{agent_id} MAY be implemented to allow field updates (name, scope_description, retrieval_config, features_config).

**O-REQ-003**: WHERE user requests agent deletion, DELETE /agents/{agent_id} MAY be implemented to call AgentDAO.delete_agent().

**O-REQ-004**: WHERE user requests agent search, GET /agents/search MAY accept query parameter to search agents by name using ILIKE.

**O-REQ-005**: WHERE user requests coverage history, GET /agents/{agent_id}/coverage/history MAY return time-series coverage data (requires coverage_history table).

### Constraints (Performance & Security)

**C-REQ-001**: POST /agents/from-taxonomy including initial coverage calculation SHALL complete within 10 seconds for taxonomies with < 100 nodes.

**C-REQ-002**: GET /agents/{agent_id}/coverage SHALL complete within 5 seconds for agent scopes with < 50 nodes and < 10,000 documents.

**C-REQ-003**: POST /agents/{agent_id}/query SHALL complete within 3 seconds for hybrid_search with top_k <= 20.

**C-REQ-004**: GET /agents SHALL limit max_results to 100 (enforce via Pydantic Field(le=100)).

**C-REQ-005**: All endpoints SHALL use async def and AsyncSession for non-blocking database operations.

**C-REQ-006**: Error responses SHALL follow RFC 7807 Problem Details format with type, title, status, detail fields.

**C-REQ-007**: API responses SHALL NOT expose internal details (no raw SQL errors, file paths, or stack traces in production).

**C-REQ-008**: agent_id path parameters SHALL be validated as UUID4 format (Pydantic automatic validation).

**C-REQ-009**: AgentCreateRequest.name SHALL be validated as non-empty string with max length 255 characters.

**C-REQ-010**: AgentCreateRequest.taxonomy_node_ids SHALL be validated as non-empty list of UUID4 values.

**C-REQ-011**: QueryRequest.query SHALL be validated as non-empty string with max length 1000 characters.

**C-REQ-012**: GET /agents/{agent_id}/gaps threshold parameter SHALL be validated as float between 0.0 and 1.0.

**C-REQ-013**: OpenAPI schema SHALL include examples for all request/response models (Pydantic model_config examples).

**C-REQ-014**: Router SHALL be included in main FastAPI app via app.include_router(agent_router, prefix="/api/v1", tags=["agents"]).

**C-REQ-015**: All endpoints SHALL log request start, completion, and errors using Python logging module with INFO/ERROR levels.

## API Specification

### Endpoint Summary

| Method | Endpoint | Description | Auth | Status Codes |
|--------|----------|-------------|------|--------------|
| POST | /api/v1/agents/from-taxonomy | Create agent from taxonomy scope | API Key | 201, 400, 422, 503 |
| GET | /api/v1/agents/{agent_id} | Get agent by ID | API Key | 200, 404 |
| GET | /api/v1/agents | List agents with filters | API Key | 200 |
| GET | /api/v1/agents/{agent_id}/coverage | Calculate agent coverage | API Key | 200, 404, 503 |
| GET | /api/v1/agents/{agent_id}/gaps | Detect coverage gaps | API Key | 200, 404 |
| POST | /api/v1/agents/{agent_id}/query | Query agent's knowledge scope | API Key | 200, 404, 503 |

### 1. POST /api/v1/agents/from-taxonomy

**Purpose**: Create new agent from taxonomy scope selection.

**Request Schema**: `AgentCreateRequest`
```python
class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent display name")
    taxonomy_node_ids: List[UUID4] = Field(..., min_length=1, description="Selected taxonomy node IDs")
    taxonomy_version: str = Field(default="1.0.0", description="Taxonomy version")
    scope_description: Optional[str] = Field(None, max_length=500, description="Human-readable scope description")
    retrieval_config: Optional[Dict[str, Any]] = Field(default={"top_k": 5, "strategy": "hybrid"})
    features_config: Optional[Dict[str, Any]] = Field(default={})

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "name": "Breast Cancer Treatment Specialist",
                "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "taxonomy_version": "1.0.0",
                "scope_description": "Agent focused on breast cancer diagnosis and treatment protocols",
                "retrieval_config": {"top_k": 10, "strategy": "hybrid"},
                "features_config": {}
            }]
        }
    )
```

**Response Schema**: `AgentResponse` (201 Created)
```python
class AgentResponse(BaseModel):
    agent_id: UUID4
    name: str
    taxonomy_node_ids: List[UUID4]
    taxonomy_version: str
    scope_description: Optional[str]
    total_documents: int
    total_chunks: int
    coverage_percent: float
    last_coverage_update: Optional[datetime]
    level: int
    current_xp: int
    total_queries: int
    successful_queries: int
    avg_faithfulness: float
    avg_response_time_ms: float
    retrieval_config: Dict[str, Any]
    features_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_query_at: Optional[datetime]
```

**Error Responses**:
- 400 Bad Request: Invalid taxonomy_node_ids (nodes do not exist)
- 422 Unprocessable Entity: Pydantic validation errors (empty name, invalid UUID format)
- 503 Service Unavailable: Database connection error

### 2. GET /api/v1/agents/{agent_id}

**Purpose**: Retrieve agent details by ID.

**Path Parameters**:
- `agent_id`: UUID4 (validated by Pydantic)

**Response Schema**: `AgentResponse` (200 OK)

**Error Responses**:
- 404 Not Found: Agent does not exist

### 3. GET /api/v1/agents

**Purpose**: List agents with optional filters.

**Query Parameters**:
- `level`: Optional[int] - Filter by agent level (1-5)
- `min_coverage`: Optional[float] - Minimum coverage percentage (0.0-100.0)
- `max_results`: int = Field(default=50, le=100) - Maximum number of results

**Response Schema**: `AgentListResponse` (200 OK)
```python
class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    filters_applied: Dict[str, Any]
```

### 4. GET /api/v1/agents/{agent_id}/coverage

**Purpose**: Calculate and retrieve agent coverage metrics.

**Path Parameters**:
- `agent_id`: UUID4

**Response Schema**: `CoverageResponse` (200 OK)
```python
class CoverageResponse(BaseModel):
    agent_id: UUID4
    overall_coverage: float = Field(..., ge=0.0, le=100.0, description="Overall coverage percentage")
    node_coverage: Dict[str, float] = Field(..., description="Per-node coverage {node_id: percentage}")
    document_counts: Dict[str, int] = Field(..., description="Per-node document count")
    target_counts: Dict[str, int] = Field(..., description="Per-node target count")
    version: str
    calculated_at: datetime
```

**Side Effects**:
- Updates `agents.coverage_percent` and `agents.last_coverage_update` in database

**Error Responses**:
- 404 Not Found: Agent does not exist
- 503 Service Unavailable: Coverage calculation timeout or database error

### 5. GET /api/v1/agents/{agent_id}/gaps

**Purpose**: Detect coverage gaps below threshold.

**Path Parameters**:
- `agent_id`: UUID4

**Query Parameters**:
- `threshold`: float = Field(default=0.5, ge=0.0, le=1.0) - Coverage threshold (0.0-1.0)

**Response Schema**: `GapListResponse` (200 OK)
```python
class GapResponse(BaseModel):
    node_id: UUID4
    current_coverage: float
    target_coverage: float
    missing_docs: int
    recommendation: str

class GapListResponse(BaseModel):
    agent_id: UUID4
    gaps: List[GapResponse]
    threshold: float
    detected_at: datetime
```

**Error Responses**:
- 404 Not Found: Agent does not exist

### 6. POST /api/v1/agents/{agent_id}/query

**Purpose**: Query agent's knowledge scope using hybrid search.

**Path Parameters**:
- `agent_id`: UUID4

**Request Schema**: `QueryRequest`
```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User query text")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="Override agent's retrieval_config.top_k")
    streaming: bool = Field(default=False, description="Enable streaming response")
    include_metadata: bool = Field(default=True, description="Include document metadata in results")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "query": "What are the latest treatments for HER2-positive breast cancer?",
                "top_k": 10,
                "streaming": False,
                "include_metadata": True
            }]
        }
    )
```

**Response Schema**: `QueryResponse` (200 OK)
```python
class SearchResultItem(BaseModel):
    doc_id: UUID4
    chunk_id: UUID4
    content: str
    score: float
    metadata: Optional[Dict[str, Any]]

class QueryResponse(BaseModel):
    agent_id: UUID4
    query: str
    results: List[SearchResultItem]
    total_results: int
    query_time_ms: float
    retrieval_strategy: str
    executed_at: datetime
```

**Side Effects**:
- Increments `agents.total_queries` by 1
- Updates `agents.last_query_at` to current timestamp

**Error Responses**:
- 404 Not Found: Agent does not exist
- 503 Service Unavailable: Search service timeout or database error

## Implementation Details

### File Structure

```
apps/api/
├── routers/
│   └── agent_router.py          # FastAPI router with 6 endpoints
├── schemas/
│   └── agent_schemas.py         # Pydantic request/response models
├── database.py                  # AgentDAO (from Phase 0)
└── security.py                  # get_api_key() dependency (existing)

apps/knowledge_builder/
└── coverage/
    └── meter.py                 # CoverageMeterService (from Phase 0)
```

### Router Implementation: `apps/api/routers/agent_router.py`

**Key Components**:
1. FastAPI APIRouter instance with prefix="/agents", tags=["agents"]
2. Dependency injection: `session = Depends(get_session)`, `api_key = Depends(get_api_key)`
3. Error handling: try-except blocks with HTTPException
4. Logging: Python logging module for request/response tracking
5. OpenAPI customization: response_model, status_code, summary, description parameters

**Example Endpoint**:
```python
@router.post(
    "/from-taxonomy",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent from taxonomy scope",
    description="Creates a new agent with specified taxonomy scope and calculates initial coverage."
)
async def create_agent_from_taxonomy(
    request: AgentCreateRequest,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
) -> AgentResponse:
    logger.info(f"Creating agent: {request.name}")

    try:
        # Validate taxonomy_node_ids exist
        await validate_taxonomy_nodes(session, request.taxonomy_node_ids)

        # Create agent via DAO
        agent = await AgentDAO.create_agent(
            session=session,
            name=request.name,
            taxonomy_node_ids=request.taxonomy_node_ids,
            taxonomy_version=request.taxonomy_version,
            scope_description=request.scope_description,
            retrieval_config=request.retrieval_config,
            features_config=request.features_config
        )

        logger.info(f"Agent created: {agent.agent_id}")
        return AgentResponse.from_orm(agent)

    except ValueError as e:
        logger.error(f"Invalid taxonomy nodes: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

### Schema Implementation: `apps/api/schemas/agent_schemas.py`

**Design Principles**:
1. All schemas inherit from Pydantic BaseModel
2. Use Field(...) for validation constraints (min_length, max_length, ge, le)
3. Include model_config with json_schema_extra for OpenAPI examples
4. Use UUID4 type for automatic UUID validation
5. Use Optional[T] for nullable fields
6. Use datetime for timestamp fields (automatic ISO 8601 serialization)

**Example Schema**:
```python
from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    taxonomy_node_ids: List[UUID4] = Field(..., min_length=1)
    taxonomy_version: str = Field(default="1.0.0")
    scope_description: Optional[str] = Field(None, max_length=500)
    retrieval_config: Optional[Dict[str, Any]] = Field(default={"top_k": 5, "strategy": "hybrid"})
    features_config: Optional[Dict[str, Any]] = Field(default={})

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "name": "Cancer Research Agent",
                "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "taxonomy_version": "1.0.0",
                "scope_description": "Specializes in cancer research papers",
                "retrieval_config": {"top_k": 10, "strategy": "hybrid"}
            }]
        }
    )
```

### Integration Points

#### 1. AgentDAO Integration (from Phase 0)
```python
from apps.api.database import AgentDAO

agent = await AgentDAO.create_agent(
    session=session,
    name=request.name,
    taxonomy_node_ids=request.taxonomy_node_ids,
    taxonomy_version=request.taxonomy_version,
    scope_description=request.scope_description,
    retrieval_config=request.retrieval_config,
    features_config=request.features_config
)
```

#### 2. CoverageMeterService Integration (from Phase 0)
```python
from apps.knowledge_builder.coverage.meter import CoverageMeterService

coverage_service = CoverageMeterService(session=session)
coverage_result = await coverage_service.calculate_coverage(
    agent_id=str(agent.agent_id),
    taxonomy_node_ids=[str(nid) for nid in agent.taxonomy_node_ids],
    version=agent.taxonomy_version
)
```

#### 3. SearchDAO Integration (existing)
```python
from apps.api.database import SearchDAO

results = await SearchDAO.hybrid_search(
    query=request.query,
    filters={
        "canonical_in": agent.taxonomy_node_ids,
        "version": agent.taxonomy_version
    },
    top_k=request.top_k or agent.retrieval_config.get("top_k", 5)
)
```

#### 4. API Key Authentication (existing)
```python
from apps.api.security import get_api_key

@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: UUID4,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
):
    # api_key automatically validated by get_api_key()
    ...
```

## Test Requirements

### Unit Tests: `tests/unit/test_agent_router.py`

**Mock Dependencies**:
1. Mock AgentDAO.create_agent(), get_agent(), list_agents(), update_agent()
2. Mock CoverageMeterService.calculate_coverage(), detect_gaps()
3. Mock SearchDAO.hybrid_search()
4. Mock get_api_key() dependency

**Test Cases**:
1. POST /agents/from-taxonomy with valid request returns 201
2. POST /agents/from-taxonomy with invalid taxonomy_node_ids returns 400
3. POST /agents/from-taxonomy with empty name returns 422
4. GET /agents/{agent_id} with valid ID returns 200
5. GET /agents/{agent_id} with non-existent ID returns 404
6. GET /agents with filters returns filtered list
7. GET /agents/{agent_id}/coverage returns coverage data
8. GET /agents/{agent_id}/gaps with threshold returns gaps
9. POST /agents/{agent_id}/query with valid request returns results
10. All endpoints with missing API key return 401

### Integration Tests: `tests/integration/test_agent_api.py`

**Real Database Required**: Use pytest fixtures with test PostgreSQL database.

**End-to-End Tests**:
1. Create agent → verify agents table row exists
2. Create agent → verify initial coverage calculated
3. Get agent → verify response matches database row
4. List agents → verify filtering works correctly
5. Calculate coverage → verify agents.coverage_percent updated
6. Detect gaps → verify gap detection logic correct
7. Query agent → verify results filtered by taxonomy scope
8. Query agent → verify total_queries incremented

### API Tests: `tests/api/test_agent_openapi.py`

**OpenAPI Validation**:
1. Verify /docs endpoint accessible
2. Verify all 6 endpoints documented
3. Verify request/response schemas include examples
4. Verify path parameters documented
5. Verify query parameters documented
6. Verify authentication requirement documented

### Performance Tests: `tests/performance/test_agent_api_performance.py`

**Latency Benchmarks**:
1. POST /agents/from-taxonomy → < 10 seconds
2. GET /agents/{agent_id} → < 500ms
3. GET /agents → < 1 second (50 results)
4. GET /agents/{agent_id}/coverage → < 5 seconds
5. GET /agents/{agent_id}/gaps → < 2 seconds
6. POST /agents/{agent_id}/query → < 3 seconds

## Related Files

### Source Code
- @CODE:AGENT-GROWTH-002:API: apps/api/routers/agent_router.py (FastAPI router)
- @CODE:AGENT-GROWTH-002:SCHEMA: apps/api/schemas/agent_schemas.py (Pydantic models)

### Dependencies
- @CODE:AGENT-GROWTH-001:DATA: apps/api/database.py (AgentDAO)
- @CODE:AGENT-GROWTH-001:DOMAIN: apps/knowledge_builder/coverage/meter.py (CoverageMeterService)
- @CODE:EXISTING: apps/api/security.py (get_api_key)
- @CODE:EXISTING: apps/api/database.py (SearchDAO)

### Test Files
- @TEST:AGENT-GROWTH-002:UNIT: tests/unit/test_agent_router.py
- @TEST:AGENT-GROWTH-002:INTEGRATION: tests/integration/test_agent_api.py
- @TEST:AGENT-GROWTH-002:API: tests/api/test_agent_openapi.py
- @TEST:AGENT-GROWTH-002:PERFORMANCE: tests/performance/test_agent_api_performance.py

### Documentation
- @DOC:AGENT-GROWTH-002:OPENAPI: /docs (Swagger UI)
- @DOC:AGENT-GROWTH-002:REDOC: /redoc (ReDoc)

## Future Enhancements (Phase 2)

### Agent Management Endpoints (Optional)
1. PATCH /agents/{agent_id} - Update agent fields
2. DELETE /agents/{agent_id} - Delete agent
3. GET /agents/search?q={query} - Search agents by name

### Background Processing (Optional)
1. POST /agents/{agent_id}/coverage/refresh?background=true - Async coverage calculation
2. GET /agents/{agent_id}/coverage/status - Check background task status

### Coverage History (Optional)
1. GET /agents/{agent_id}/coverage/history - Time-series coverage data
2. GET /agents/{agent_id}/coverage/history?start_date={date}&end_date={date} - Filtered history

### Streaming Query (Optional)
1. POST /agents/{agent_id}/query with streaming=true - SSE streaming response

## Revision History

- v0.1.0 (2025-10-12): Initial specification for Phase 1 REST API Integration
  - 6 RESTful endpoints (POST /from-taxonomy, GET /{id}, GET /, GET /coverage, GET /gaps, POST /query)
  - Pydantic request/response schemas with validation
  - API Key authentication integration
  - OpenAPI 3.0 documentation
  - Integration with Phase 0 AgentDAO and CoverageMeterService
  - Test requirements (unit, integration, API, performance)
