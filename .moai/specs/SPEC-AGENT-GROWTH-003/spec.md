---
id: AGENT-GROWTH-003
version: 0.1.0
status: completed
created: 2025-10-12
updated: 2025-10-12
author: @sonheungmin
priority: high
category: feature
labels:
  - api
  - management
  - streaming
  - background-processing
depends_on:
  - AGENT-GROWTH-002
scope:
  packages:
    - apps/api/routers
    - apps/api/schemas
  files:
    - agent_router.py
    - agent_schemas.py
---

# @SPEC:AGENT-GROWTH-003: Agent Growth Platform Phase 2 - Advanced API Features

## HISTORY

### v0.1.0 (2025-10-12)
- **INITIAL**: Phase 2 REST API 고급 기능 명세 작성 (구현 완료 기준)
- **AUTHOR**: @sonheungmin
- **SCOPE**: 7개 Advanced API (Management, Background, History, Streaming)
- **CONTEXT**: Phase 1 기본 CRUD 확장, 프로덕션 워크플로우 지원
- **DEPENDENCIES**: SPEC-AGENT-GROWTH-002 (6개 기본 엔드포인트)
- **IMPLEMENTATION**: 구현 완료 상태 (apps/api/routers/agent_router.py line 367-722)

## Environment

- **Backend Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 12+ (agents 테이블)
- **Authentication**: API Key (기존 `apps/api/security.py` 활용)
- **Streaming**: Server-Sent Events (SSE)
- **Background Tasks**: asyncio-based mock implementation
- **Python Version**: 3.9+
- **Phase 1 Prerequisites**:
  - POST /agents/from-taxonomy (agent 생성)
  - GET /agents/{agent_id} (agent 조회)
  - GET /agents (agent 목록)
  - GET /agents/{agent_id}/coverage (coverage 계산)
  - GET /agents/{agent_id}/gaps (gap 감지)
  - POST /agents/{agent_id}/query (query 실행)

## Assumptions

1. **Phase 1 Complete**: SPEC-AGENT-GROWTH-002 구현 완료 (6개 기본 엔드포인트 운영 중)
2. **Management Endpoints**: PATCH, DELETE, Search는 프로덕션 운영 필수 기능
3. **Background Processing**: 대규모 coverage 계산은 비동기 처리 필요 (200+ nodes)
4. **Coverage History**: 시간 경과에 따른 커버리지 추적 필요 (향후 확장용)
5. **Streaming Query**: 실시간 결과 전달로 UX 개선 (50+ results)
6. **AgentDAO Extensions**: search_agents() 메서드 추가 구현 완료
7. **Schema Extensions**: AgentUpdateRequest, BackgroundTaskResponse, CoverageHistoryResponse, CoverageHistoryItem 추가 완료

## EARS Requirements

### Ubiquitous Requirements (Core Advanced Features)

**U-REQ-001**: System SHALL provide PATCH /api/v1/agents/{agent_id} endpoint accepting AgentUpdateRequest returning AgentResponse with 200 OK status.

**U-REQ-002**: System SHALL provide DELETE /api/v1/agents/{agent_id} endpoint accepting UUID agent_id returning 204 No Content status.

**U-REQ-003**: System SHALL provide GET /api/v1/agents/search endpoint accepting query parameter q returning AgentListResponse with 200 OK status.

**U-REQ-004**: System SHALL provide POST /api/v1/agents/{agent_id}/coverage/refresh endpoint accepting background boolean parameter returning BackgroundTaskResponse with 202 Accepted status.

**U-REQ-005**: System SHALL provide GET /api/v1/agents/{agent_id}/coverage/status/{task_id} endpoint accepting UUID agent_id and string task_id returning BackgroundTaskResponse with 200 OK status.

**U-REQ-006**: System SHALL provide GET /api/v1/agents/{agent_id}/coverage/history endpoint accepting optional datetime parameters start_date and end_date returning CoverageHistoryResponse with 200 OK status.

**U-REQ-007**: System SHALL provide POST /api/v1/agents/{agent_id}/query/stream endpoint accepting QueryRequest returning Server-Sent Events stream with 200 OK status.

**U-REQ-008**: System SHALL support partial updates via PATCH endpoint allowing selective field updates (name, scope_description, retrieval_config, features_config).

**U-REQ-009**: System SHALL implement case-insensitive name search using SQL ILIKE operator for search endpoint.

**U-REQ-010**: System SHALL stream search results using SSE format with JSON data events for streaming query endpoint.

### Event-driven Requirements (Advanced API Lifecycle)

**E-REQ-001**: WHEN PATCH /agents/{agent_id} receives AgentUpdateRequest with valid fields, System SHALL call AgentDAO.update_agent() with only provided fields and return 200 OK with updated AgentResponse body.

**E-REQ-002**: WHEN PATCH /agents/{agent_id} receives request with non-existent agent_id, System SHALL return 404 Not Found with error message "Agent not found: {agent_id}".

**E-REQ-003**: WHEN PATCH /agents/{agent_id} receives request with empty update fields, System SHALL return 200 OK without modifying database (idempotent).

**E-REQ-004**: WHEN DELETE /agents/{agent_id} receives valid UUID, System SHALL call AgentDAO.delete_agent(agent_id) and return 204 No Content with empty body.

**E-REQ-005**: WHEN DELETE /agents/{agent_id} receives non-existent agent_id, System SHALL return 404 Not Found with error message "Agent not found: {agent_id}".

**E-REQ-006**: WHEN GET /agents/search receives query parameter q, System SHALL call AgentDAO.search_agents(query=q, max_results) and return 200 OK with AgentListResponse body.

**E-REQ-007**: WHEN GET /agents/search receives empty or missing q parameter, System SHALL return all agents (no filtering applied).

**E-REQ-008**: WHEN POST /agents/{agent_id}/coverage/refresh receives background=true, System SHALL generate task_id, return 202 Accepted immediately, and execute coverage calculation asynchronously.

**E-REQ-009**: WHEN POST /agents/{agent_id}/coverage/refresh receives background=false, System SHALL execute coverage calculation synchronously and return 200 OK with BackgroundTaskResponse containing completed status and result.

**E-REQ-010**: WHEN GET /agents/{agent_id}/coverage/status/{task_id} is invoked, System SHALL return BackgroundTaskResponse with current task status (pending, running, completed, failed).

**E-REQ-011**: WHEN GET /agents/{agent_id}/coverage/history is invoked, System SHALL return CoverageHistoryResponse with time-series coverage data filtered by optional start_date and end_date parameters.

**E-REQ-012**: WHEN GET /agents/{agent_id}/coverage/history receives no date filters, System SHALL return all available history entries for the agent.

**E-REQ-013**: WHEN POST /agents/{agent_id}/query/stream is invoked, System SHALL return StreamingResponse with text/event-stream media type and stream search results as SSE events.

**E-REQ-014**: WHEN streaming query completes, System SHALL send final SSE event with status=completed and close connection.

**E-REQ-015**: WHEN streaming query encounters error, System SHALL send error SSE event with error details and close connection gracefully.

### State-driven Requirements (Advanced API Behavior)

**S-REQ-001**: WHILE agent exists in database, PATCH /agents/{agent_id} SHALL allow updates to name, scope_description, retrieval_config, features_config fields only.

**S-REQ-002**: WHILE agent does not exist, PATCH /agents/{agent_id} SHALL return 404 Not Found.

**S-REQ-003**: WHILE agent exists in database, DELETE /agents/{agent_id} SHALL permanently remove agent and return 204 No Content.

**S-REQ-004**: WHILE agent has been deleted, subsequent GET /agents/{agent_id} SHALL return 404 Not Found.

**S-REQ-005**: WHILE search query q contains spaces, System SHALL match agents with names containing any substring matching q (case-insensitive).

**S-REQ-006**: WHILE background task is pending, GET /coverage/status/{task_id} SHALL return status=pending with null started_at.

**S-REQ-007**: WHILE background task is running, GET /coverage/status/{task_id} SHALL return status=running with non-null started_at.

**S-REQ-008**: WHILE background task has completed, GET /coverage/status/{task_id} SHALL return status=completed with result data.

**S-REQ-009**: WHILE agent has no coverage history, GET /coverage/history SHALL return empty history array with total_entries=0.

**S-REQ-010**: WHILE streaming query is active, System SHALL send SSE events with status=started, individual result events, and final status=completed event.

**S-REQ-011**: WHILE SSE connection is open, System SHALL set Cache-Control=no-cache, Connection=keep-alive, X-Accel-Buffering=no headers.

**S-REQ-012**: WHILE processing streaming results, System SHALL yield individual result events with 50ms delay between events for controlled streaming.

### Optional Features (Future Enhancements)

**O-REQ-001**: WHERE user requests persistent task storage, Background task status MAY be stored in background_tasks database table instead of in-memory mock.

**O-REQ-002**: WHERE user requests coverage history tracking, CoverageHistoryItem MAY be stored in coverage_history table with automated tracking on each coverage calculation.

**O-REQ-003**: WHERE user requests WebSocket support, Alternative streaming protocol MAY be implemented alongside SSE.

**O-REQ-004**: WHERE user requests bulk operations, Bulk update/delete endpoints MAY be added (PATCH /agents/bulk, DELETE /agents/bulk).

**O-REQ-005**: WHERE user requests agent cloning, POST /agents/{agent_id}/clone MAY create duplicate agent with new ID.

### Constraints (Performance & Security)

**C-REQ-001**: PATCH /agents/{agent_id} SHALL complete within 1 second for field updates.

**C-REQ-002**: DELETE /agents/{agent_id} SHALL complete within 2 seconds including cascade deletion of related data.

**C-REQ-003**: GET /agents/search SHALL complete within 1 second for queries on < 10,000 agents.

**C-REQ-004**: POST /agents/{agent_id}/coverage/refresh with background=true SHALL return 202 Accepted within 500ms.

**C-REQ-005**: POST /agents/{agent_id}/query/stream SHALL start streaming first result within 1 second.

**C-REQ-006**: Streaming query SHALL maintain connection for maximum 5 minutes before timeout.

**C-REQ-007**: AgentUpdateRequest SHALL NOT allow updates to agent_id, taxonomy_node_ids, taxonomy_version, created_at fields (immutable).

**C-REQ-008**: DELETE operation SHALL be idempotent (deleting non-existent agent returns 404, not 500).

**C-REQ-009**: Search query q parameter SHALL have maximum length of 255 characters.

**C-REQ-010**: Background task_id SHALL be unique UUID4 string prefixed with "task-".

**C-REQ-011**: SSE events SHALL use JSON format with "data: {json}\n\n" structure.

**C-REQ-012**: Coverage history SHALL return maximum 1000 entries per request.

**C-REQ-013**: All Phase 2 endpoints SHALL require API Key authentication via Depends(verify_api_key).

**C-REQ-014**: Error responses SHALL follow RFC 7807 Problem Details format with type, title, status, detail fields.

**C-REQ-015**: Streaming responses SHALL set appropriate headers to prevent buffering by proxies/load balancers.

## API Specification

### Endpoint Summary

| Method | Endpoint | Description | Auth | Status Codes |
|--------|----------|-------------|------|--------------|
| PATCH | /api/v1/agents/{agent_id} | Update agent configuration | API Key | 200, 404, 422, 500 |
| DELETE | /api/v1/agents/{agent_id} | Delete agent permanently | API Key | 204, 404, 500 |
| GET | /api/v1/agents/search | Search agents by name | API Key | 200, 422, 500 |
| POST | /api/v1/agents/{agent_id}/coverage/refresh | Async coverage calculation | API Key | 202, 404, 500 |
| GET | /api/v1/agents/{agent_id}/coverage/status/{task_id} | Get task status | API Key | 200, 404, 500 |
| GET | /api/v1/agents/{agent_id}/coverage/history | Get coverage history | API Key | 200, 404, 500 |
| POST | /api/v1/agents/{agent_id}/query/stream | Streaming query (SSE) | API Key | 200, 404, 503 |

### 1. PATCH /api/v1/agents/{agent_id}

**Purpose**: Update agent configuration fields (name, scope_description, retrieval_config, features_config).

**Path Parameters**:
- `agent_id`: UUID4 (validated by Pydantic)

**Request Schema**: `AgentUpdateRequest`
```python
class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scope_description: Optional[str] = Field(None, max_length=500)
    retrieval_config: Optional[Dict[str, Any]] = Field(None)
    features_config: Optional[Dict[str, Any]] = Field(None)
```

**Response Schema**: `AgentResponse` (200 OK)

**Behavior**:
- Only provided fields are updated (partial update semantics)
- Immutable fields: agent_id, taxonomy_node_ids, taxonomy_version, created_at
- Empty request body (no fields) returns 200 OK without changes

**Error Responses**:
- 404 Not Found: Agent does not exist
- 422 Unprocessable Entity: Validation errors (name too long, invalid types)
- 500 Internal Server Error: Database error

**Implementation**: `apps/api/routers/agent_router.py` line 367-406

### 2. DELETE /api/v1/agents/{agent_id}

**Purpose**: Permanently delete agent and all associated data.

**Path Parameters**:
- `agent_id`: UUID4

**Response**: 204 No Content (empty body)

**Behavior**:
- Deletes agent row from agents table
- Cascade deletion of related data (if any)
- Idempotent operation (404 if agent doesn't exist)

**Error Responses**:
- 404 Not Found: Agent does not exist
- 500 Internal Server Error: Database error

**Implementation**: `apps/api/routers/agent_router.py` line 409-437

### 3. GET /api/v1/agents/search

**Purpose**: Search agents by name using case-insensitive pattern matching.

**Query Parameters**:
- `q`: Optional[str] - Search query (matches agent name with ILIKE)
- `max_results`: int = 50 (default) - Maximum results (max 100)

**Response Schema**: `AgentListResponse` (200 OK)
```python
class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    filters_applied: Dict[str, Any]
```

**Behavior**:
- If q is provided: returns agents with name ILIKE '%q%'
- If q is empty/null: returns all agents (no filter)
- Case-insensitive search (ILIKE operator)
- Limited by max_results parameter

**Error Responses**:
- 422 Unprocessable Entity: max_results > 100
- 500 Internal Server Error: Database error

**Implementation**: `apps/api/routers/agent_router.py` line 440-475

### 4. POST /api/v1/agents/{agent_id}/coverage/refresh

**Purpose**: Trigger coverage calculation with optional background processing.

**Path Parameters**:
- `agent_id`: UUID4

**Query Parameters**:
- `background`: bool = True (default) - Enable background processing

**Response Schema**: `BackgroundTaskResponse` (202 Accepted if background=true, 200 OK if background=false)
```python
class BackgroundTaskResponse(BaseModel):
    task_id: str                          # Format: "task-{uuid4}"
    agent_id: UUID4
    task_type: str                        # "coverage_refresh"
    status: str                           # "pending"|"running"|"completed"|"failed"
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]      # {"coverage_percent": 85.5}
    error: Optional[str]
```

**Behavior**:
- background=true: Returns 202 immediately, calculates coverage asynchronously
- background=false: Calculates coverage synchronously, returns 200 with result
- Task ID format: "task-{uuid4}" (unique)
- Mock implementation: No persistent task storage (in-memory only)

**Error Responses**:
- 404 Not Found: Agent does not exist
- 500 Internal Server Error: Task creation failed

**Implementation**: `apps/api/routers/agent_router.py` line 478-547

### 5. GET /api/v1/agents/{agent_id}/coverage/status/{task_id}

**Purpose**: Retrieve background task status and result.

**Path Parameters**:
- `agent_id`: UUID4
- `task_id`: str

**Response Schema**: `BackgroundTaskResponse` (200 OK)

**Status Transitions**:
- pending → running → completed
- pending → running → failed

**Behavior**:
- Returns current task status with progress info
- Mock implementation: Always returns completed status with agent's current coverage_percent
- Real implementation: Query background_tasks table

**Error Responses**:
- 404 Not Found: Agent or task does not exist
- 500 Internal Server Error: Query failed

**Implementation**: `apps/api/routers/agent_router.py` line 550-587

### 6. GET /api/v1/agents/{agent_id}/coverage/history

**Purpose**: Retrieve time-series coverage data for trend analysis.

**Path Parameters**:
- `agent_id`: UUID4

**Query Parameters**:
- `start_date`: Optional[datetime] - Filter start date (ISO 8601)
- `end_date`: Optional[datetime] - Filter end date (ISO 8601)

**Response Schema**: `CoverageHistoryResponse` (200 OK)
```python
class CoverageHistoryItem(BaseModel):
    timestamp: datetime
    overall_coverage: float
    total_documents: int
    total_chunks: int

class CoverageHistoryResponse(BaseModel):
    agent_id: UUID4
    history: List[CoverageHistoryItem]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    total_entries: int
```

**Behavior**:
- Returns list of coverage measurements over time
- Mock implementation: Returns single entry with current coverage data
- Real implementation: Query coverage_history table with date filters
- Ordered by timestamp DESC (newest first)

**Error Responses**:
- 404 Not Found: Agent does not exist
- 500 Internal Server Error: Query failed

**Implementation**: `apps/api/routers/agent_router.py` line 590-634

### 7. POST /api/v1/agents/{agent_id}/query/stream

**Purpose**: Execute query with real-time streaming results using Server-Sent Events.

**Path Parameters**:
- `agent_id`: UUID4

**Request Schema**: `QueryRequest` (same as Phase 1 POST /query)
```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(None, ge=1, le=50)
    streaming: bool = Field(default=False)  # Ignored in /stream endpoint
    include_metadata: bool = Field(default=True)
```

**Response**: StreamingResponse (200 OK)
- Media Type: text/event-stream
- Headers: Cache-Control=no-cache, Connection=keep-alive, X-Accel-Buffering=no

**SSE Event Format**:
```json
data: {"status": "started", "agent_id": "123e4567-..."}

data: {"index": 0, "doc_id": "...", "content": "...", "score": 0.95}

data: {"index": 1, "doc_id": "...", "content": "...", "score": 0.89}

data: {"status": "completed", "total_results": 10, "query_time_ms": 1250.5}
```

**Behavior**:
- Streams results as individual SSE events
- 50ms delay between result events (controlled streaming)
- Final event with status=completed and metadata
- Error event if query execution fails
- Increments total_queries and updates last_query_at (same as Phase 1)

**Error Responses**:
- 404 Not Found: Agent does not exist (sent as SSE error event)
- 503 Service Unavailable: Search service timeout

**Implementation**: `apps/api/routers/agent_router.py` line 637-722

## Implementation Details

### File Structure

```
apps/api/
├── routers/
│   └── agent_router.py          # Phase 1 (line 1-365) + Phase 2 (line 367-722)
├── schemas/
│   └── agent_schemas.py         # Phase 1 schemas + Phase 2 schemas (line 209-290)
├── agent_dao.py                 # AgentDAO with search_agents() method
└── deps.py                      # verify_api_key() dependency
```

### Phase 2 Schema Additions

**Added Schemas** (`apps/api/schemas/agent_schemas.py` line 209-290):
1. `AgentUpdateRequest`: Partial update fields (name, scope_description, retrieval_config, features_config)
2. `BackgroundTaskResponse`: Task status and result tracking
3. `CoverageHistoryItem`: Single coverage measurement point
4. `CoverageHistoryResponse`: Time-series coverage data container

### AgentDAO Extensions

**New Method**: `search_agents(session, query, max_results)` (`apps/api/agent_dao.py`)
```python
async def search_agents(
    session: AsyncSession,
    query: Optional[str],
    max_results: int = 50
) -> List[Agent]:
    stmt = select(Agent)
    if query:
        stmt = stmt.where(Agent.name.ilike(f"%{query}%"))
    stmt = stmt.limit(max_results)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Streaming Implementation Pattern

**SSE Generator** (`agent_router.py` line 651-713):
```python
async def event_generator():
    # 1. Validate agent
    agent = await AgentDAO.get_agent(session, agent_id)
    if not agent:
        yield f"data: {json.dumps({'error': 'Agent not found'})}\n\n"
        return

    # 2. Send start event
    yield f"data: {json.dumps({'status': 'started', 'agent_id': str(agent_id)})}\n\n"

    # 3. Execute search
    search_results = await SearchDAO.hybrid_search(...)

    # 4. Stream individual results
    for i, result in enumerate(search_results):
        result_item = {...}
        yield f"data: {json.dumps(result_item)}\n\n"
        await asyncio.sleep(0.05)  # 50ms delay

    # 5. Send completion event
    final_data = {'status': 'completed', 'total_results': len(search_results)}
    yield f"data: {json.dumps(final_data)}\n\n"
```

### Background Task Mock Implementation

**Current**: In-memory mock without persistence
```python
# background=true: Generate task_id, return 202 immediately
task_id = f"task-{uuid4()}"
return BackgroundTaskResponse(
    task_id=task_id,
    status="pending",
    created_at=datetime.utcnow(),
    ...
)
```

**Future**: Persistent task storage
```sql
CREATE TABLE background_tasks (
    task_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    task_type VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error TEXT
);
```

## Integration Points

### Phase 1 Dependencies

Phase 2 extends Phase 1 endpoints without breaking changes:
- PATCH, DELETE, Search work independently
- Background coverage refresh uses same CoverageMeterService as GET /coverage
- Streaming query uses same SearchDAO.hybrid_search as POST /query
- Coverage history uses same agents.coverage_percent field

### External Dependencies

1. **AgentDAO** (Phase 0): create_agent(), get_agent(), update_agent(), delete_agent(), list_agents(), search_agents()
2. **CoverageMeterService** (Phase 0): calculate_coverage(), detect_gaps()
3. **SearchDAO** (Phase 0): hybrid_search()
4. **verify_api_key()** (existing): API Key authentication

## Test Requirements

### Unit Tests: `tests/unit/test_agent_router_phase2.py`

**Mock Dependencies**:
1. Mock AgentDAO.update_agent(), delete_agent(), search_agents()
2. Mock CoverageMeterService.calculate_coverage()
3. Mock SearchDAO.hybrid_search()
4. Mock verify_api_key() dependency

**Test Cases**:
1. PATCH /agents/{agent_id} with valid fields returns 200
2. PATCH /agents/{agent_id} with non-existent ID returns 404
3. PATCH /agents/{agent_id} with empty body returns 200 (no changes)
4. DELETE /agents/{agent_id} with valid ID returns 204
5. DELETE /agents/{agent_id} with non-existent ID returns 404
6. GET /agents/search with query returns filtered list
7. GET /agents/search without query returns all agents
8. POST /coverage/refresh with background=true returns 202
9. POST /coverage/refresh with background=false returns 200 with result
10. GET /coverage/status/{task_id} returns task status
11. GET /coverage/history returns history list
12. POST /query/stream returns SSE stream with multiple events

### Integration Tests: `tests/integration/test_agent_api_phase2.py`

**Real Database Required**: Use pytest fixtures with test PostgreSQL database.

**End-to-End Tests**:
1. PATCH agent → verify agents table updated
2. DELETE agent → verify agents table row deleted
3. Search agents → verify ILIKE query works
4. Background refresh → verify coverage_percent updated
5. Coverage history → verify time-series data correct
6. Streaming query → verify SSE events received in order

### API Tests: `tests/api/test_agent_openapi_phase2.py`

**OpenAPI Validation**:
1. Verify Phase 2 endpoints documented in /docs
2. Verify request/response schemas for new endpoints
3. Verify SSE streaming documented correctly
4. Verify background task flow documented

### Performance Tests: `tests/performance/test_agent_api_phase2_performance.py`

**Latency Benchmarks**:
1. PATCH /agents/{agent_id} → < 1 second
2. DELETE /agents/{agent_id} → < 2 seconds
3. GET /agents/search → < 1 second (1000 agents)
4. POST /coverage/refresh (background=true) → < 500ms
5. POST /query/stream → first event within 1 second

## Related Files

### Source Code
- @CODE:AGENT-GROWTH-003:API: apps/api/routers/agent_router.py (line 367-722)
- @CODE:AGENT-GROWTH-003:SCHEMA: apps/api/schemas/agent_schemas.py (line 209-290)
- @CODE:AGENT-GROWTH-003:DAO: apps/api/agent_dao.py (search_agents method)

### Dependencies
- @CODE:AGENT-GROWTH-002:API: apps/api/routers/agent_router.py (line 1-365, Phase 1 endpoints)
- @CODE:AGENT-GROWTH-001:DATA: apps/api/agent_dao.py (AgentDAO)
- @CODE:AGENT-GROWTH-001:DOMAIN: apps/knowledge_builder/coverage/meter.py (CoverageMeterService)
- @CODE:EXISTING: apps/api/deps.py (verify_api_key)
- @CODE:EXISTING: apps/api/database.py (SearchDAO)

### Test Files
- @TEST:AGENT-GROWTH-003:UNIT: tests/unit/test_agent_router_phase2.py
- @TEST:AGENT-GROWTH-003:INTEGRATION: tests/integration/test_agent_api_phase2.py
- @TEST:AGENT-GROWTH-003:API: tests/api/test_agent_openapi_phase2.py
- @TEST:AGENT-GROWTH-003:PERFORMANCE: tests/performance/test_agent_api_phase2_performance.py

### Documentation
- @DOC:AGENT-GROWTH-003:OPENAPI: /docs (Swagger UI - Phase 2 endpoints)
- @DOC:AGENT-GROWTH-003:REDOC: /redoc (ReDoc - Phase 2 endpoints)

## Implementation Phases (Completed)

### Phase 2-1: Management Endpoints (Completed)
- ✅ PATCH /agents/{agent_id} - Update agent configuration
- ✅ DELETE /agents/{agent_id} - Delete agent
- ✅ GET /agents/search - Search agents by name
- ✅ AgentUpdateRequest schema
- ✅ AgentDAO.search_agents() method

### Phase 2-2: Background Processing (Completed)
- ✅ POST /agents/{agent_id}/coverage/refresh?background=true - Async coverage calculation
- ✅ GET /agents/{agent_id}/coverage/status/{task_id} - Task status
- ✅ BackgroundTaskResponse schema
- ✅ Mock task management (in-memory)

### Phase 2-3: Coverage History (Completed)
- ✅ GET /agents/{agent_id}/coverage/history - Time-series coverage data
- ✅ CoverageHistoryItem schema
- ✅ CoverageHistoryResponse schema
- ✅ Mock history implementation (single entry)

### Phase 2-4: Streaming Query (Completed)
- ✅ POST /agents/{agent_id}/query/stream - SSE streaming
- ✅ SSE event generator with status events
- ✅ StreamingResponse with proper headers
- ✅ Error handling in streaming context

## Future Enhancements (Phase 3)

### Persistent Background Tasks
1. background_tasks table schema
2. Celery/RQ integration for distributed task processing
3. Task progress updates (0-100%)
4. Task cancellation endpoint

### Enhanced Coverage History
1. coverage_history table schema
2. Automated history tracking on each coverage calculation
3. Trend analysis endpoints
4. Coverage change alerts

### Advanced Features
1. Bulk operations (bulk update/delete)
2. Agent cloning (POST /agents/{agent_id}/clone)
3. WebSocket streaming (alternative to SSE)
4. Webhook notifications for background tasks

## Revision History

- v0.1.0 (2025-10-12): Initial Phase 2 specification (implementation completed)
  - 7 new endpoints (Management, Background, History, Streaming)
  - 4 new Pydantic schemas (AgentUpdateRequest, BackgroundTaskResponse, CoverageHistoryItem, CoverageHistoryResponse)
  - AgentDAO.search_agents() method
  - SSE streaming implementation
  - Mock background task and history implementations
