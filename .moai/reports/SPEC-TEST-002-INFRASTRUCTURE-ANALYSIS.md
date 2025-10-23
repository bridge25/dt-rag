# SPEC-TEST-002 Test Infrastructure & Patterns Exploration Report

**Date**: 2025-10-23
**Exploration Depth**: Medium (focused scan with detailed analysis)
**Scope**: Existing test infrastructure for Phase 3 API endpoints

---

## Executive Summary

This exploration identifies the complete test infrastructure and patterns already established in the dt-rag project for SPEC-TEST-002 (Phase 3 API endpoint integration tests). The codebase has:

- **Mature async testing patterns** with pytest-asyncio and AsyncClient
- **Real database testing** using PostgreSQL + asyncpg (not mocked)
- **Transaction isolation patterns** for test independence
- **24 integration tests** already written for background task APIs (test_agent_api_phase3.py)
- **Comprehensive conftest.py** with async session management
- **Pydantic models** for request/response validation in both Reflection and Consolidation routers

---

## 1. Test Environment Configuration

### 1.1 Python Test Configuration (`tests/conftest.py`)

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/conftest.py`

**Key Features**:
- Session-scoped async event loop
- Function-scoped async database session with automatic rollback
- TestClient fixture with module scope
- Sample data fixtures (sample_text, ml_model_name)

**Code Pattern**:
```python
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Database session fixture with rollback"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

**Key Insight**: The rollback pattern ensures **transaction isolation** - each test runs in its own transaction that's automatically rolled back, preventing test data pollution.

---

### 1.2 Database Configuration

**Database URL Pattern**: `postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test`

**Key Points**:
- Uses **asyncpg** (async PostgreSQL driver)
- Explicit asyncpg protocol: `postgresql+asyncpg://` (not just `postgresql://`)
- Environment variable: `DATABASE_URL` or `TEST_DATABASE_URL`

**Database Models** (apps/api/database.py):
- `CaseBank`: Core case data with vectors and metadata
- `ExecutionLog`: Execution trace for Reflection analysis
- `CaseBankArchive`: Archived cases from Consolidation
- `TaxonomyNode`: Classification hierarchy
- `DocumentChunk`: Document fragments with embeddings

---

### 1.3 Dependencies & Versions

**Critical Testing Dependencies** (pyproject.toml):
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-xdist>=3.3.0
httpx>=0.25.0  # For async HTTP client in tests
```

**Production Dependencies**:
- `sqlalchemy[asyncio]>=2.0.0`
- `asyncpg>=0.29.0`
- `fastapi>=0.104.0`
- `pydantic>=2.5.0`

---

## 2. Existing Integration Test Patterns

### 2.1 SPEC-TEST-001 Reference: `test_api_endpoints.py`

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/integration/test_api_endpoints.py`

**Test Classes** (28 tests total):
1. **TestHealthEndpoint** (2 tests)
   - `test_health_check_returns_200`: Basic endpoint accessibility
   - `test_health_check_returns_json`: Response format validation

2. **TestClassifyEndpoint** (4 tests)
   - `test_classify_endpoint_exists`: Endpoint accessibility
   - `test_classify_rag_text`: Domain-specific classification
   - `test_classify_ml_text`: Domain-specific classification
   - `test_classify_with_hint_paths`: Parameter handling

3. **TestSearchEndpoint** (3 tests)
   - `test_search_endpoint_exists`: Endpoint accessibility
   - `test_search_returns_hits`: Response structure validation
   - `test_search_with_filters`: Parameter handling

4. **TestTaxonomyEndpoint** (2 tests)
   - `test_get_taxonomy_tree`: Data structure validation
   - `test_taxonomy_version_format`: Version parameter handling

5. **TestErrorHandling** (3 tests)
   - `test_classify_missing_text`: 422 Validation error
   - `test_search_missing_query`: 422 Validation error
   - `test_invalid_endpoint`: 404 Not Found

**Pattern Notes**:
- Uses `api_client: TestClient` fixture (sync TestClient)
- Tests handle both 200 and 422 responses (graceful degradation)
- No authentication enforcement in these older tests
- Simple assertions on response codes and JSON structure

---

### 2.2 Phase 3-4 API Tests: `test_agent_api_phase3.py`

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/integration/test_agent_api_phase3.py`

**Advanced Features** (19 tests):

1. **Async Test Pattern**:
```python
@pytest.mark.asyncio
async def test_refresh_coverage_background_creates_task(self, test_agent, client):
    response = await client.post(
        f"/api/v1/agents/{test_agent.agent_id}/coverage/refresh?background=true",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 202
```

2. **AsyncClient Pattern**:
```python
@pytest.fixture
async def client(self):
    """Create async HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

3. **Agent Test Fixture**:
```python
@pytest.fixture
async def test_agent(self):
    """Create test agent"""
    async with async_session() as session:
        agent = await AgentDAO.create_agent(...)
        yield agent
        # Cleanup
        await AgentDAO.delete_agent(session, agent.agent_id)
```

4. **Test Categories**:
   - **Task Creation**: 202 Accepted response validation
   - **Status Queries**: Real database state verification
   - **History Queries**: Time-series data with filtering
   - **Cancellation**: State transitions (pending → cancelled, running → cancellation_requested)
   - **Error Cases**: 404, 400 responses

**Key Assertion Patterns**:
```python
# Response format validation
assert data["task_id"].startswith("agent-coverage-")
assert data["agent_id"] == str(test_agent.agent_id)
assert data["task_type"] == "coverage_refresh"

# Database verification
async with async_session() as session:
    task = await session.get(BackgroundTask, data["task_id"])
    assert task is not None
    assert task.status == "pending"

# Date filtering
assert len(data["history"]) >= 1
assert history_items[0]["overall_coverage"] >= history_items[1]["overall_coverage"]
```

---

### 2.3 Reflection Workflow Tests: `test_reflection_workflow.py`

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/integration/test_reflection_workflow.py`

**Pattern Highlights**:
- Uses **SQLite in-memory** for isolated workflow testing
- Direct engine/session management without conftest
- Multi-step execution flow with state verification

```python
@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(CaseBank.metadata.create_all)
        await conn.run_sync(ExecutionLog.metadata.create_all)
    yield
    # Cleanup with drop_all
```

---

### 2.4 Consolidation Workflow Tests: `test_consolidation_workflow.py`

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/integration/test_consolidation_workflow.py`

**Pattern Highlights**:
- **TestCaseBank model** defined inline for test isolation
- Fixture-based data setup with automatic cleanup
- Test isolation via `cleanup_cases` autouse fixture

```python
@pytest.fixture(autouse=True)
async def cleanup_cases():
    yield
    async with test_async_session() as session:
        from sqlalchemy import delete
        stmt = delete(TestCaseBank)
        await session.execute(stmt)
        await session.commit()
```

---

## 3. Phase 3 API Implementations

### 3.1 Reflection Router

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/api/routers/reflection_router.py`

**8 Endpoints** (4 distinct operations):

1. **POST /reflection/analyze** (Pydantic models defined)
   - `ReflectionAnalysisRequest`: case_id (str), limit (int, default=100)
   - `ReflectionAnalysisResponse`: case_id, total_executions, successful_executions, failed_executions, success_rate, avg_execution_time_ms, common_errors, timestamp
   - Authentication: `api_key: APIKeyInfo = Depends(verify_api_key)`
   - Dependency: `get_reflection_engine()` async context manager

2. **POST /reflection/batch** 
   - No request parameters
   - `ReflectionBatchResponse`: analyzed_cases, low_performance_cases, suggestions, timestamp

3. **POST /reflection/suggestions**
   - `ImprovementSuggestionsRequest`: case_id
   - `ImprovementSuggestionsResponse`: case_id, suggestions, confidence, timestamp

4. **GET /reflection/health**
   - (Partial visible, likely returns service status)

**Key Code Pattern**:
```python
@router.post("/analyze", response_model=ReflectionAnalysisResponse)
async def analyze_case_performance(
    request: ReflectionAnalysisRequest,
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    try:
        async with db_manager.get_session() as session:
            engine = ReflectionEngine(db_session=session)
            performance = await engine.analyze_case_performance(...)
        return ReflectionAnalysisResponse(**performance)
    except Exception as e:
        raise HTTPException(...)
```

---

### 3.2 Consolidation Router

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/api/routers/consolidation_router.py`

**8 Endpoints** (4 distinct operations):

1. **POST /consolidation/run**
   - `ConsolidationRequest`: dry_run (bool), threshold (float, 0-100), similarity_threshold (float, 0-1), inactive_days (int, ≥1)
   - `ConsolidationResponse`: removed_cases, merged_cases, archived_cases, dry_run, details, timestamp

2. **POST /consolidation/dry-run**
   - No request body
   - Same response as /run (with dry_run=true)

3. **GET /consolidation/summary**
   - `ConsolidationSummaryResponse`: total_active_cases, low_performance_candidates, inactive_candidates, potential_savings, timestamp

4. **GET /consolidation/health**
   - (Partial visible)

**Key Code Pattern**:
```python
@router.post("/run", response_model=ConsolidationResponse)
async def run_consolidation(
    request: ConsolidationRequest,
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    try:
        async with db_manager.get_session() as session:
            policy = ConsolidationPolicy(db_session=session, dry_run=request.dry_run)
            results = await policy.run_consolidation()
        return ConsolidationResponse(**results)
    except Exception as e:
        raise HTTPException(...)
```

---

## 4. Authentication & Dependencies

### 4.1 API Key Verification

**Pattern**:
```python
from ..deps import verify_api_key
from ..security.api_key_storage import APIKeyInfo

@router.post("/analyze")
async def endpoint(
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    # Endpoint code
```

**Test Usage**:
```python
headers={"X-API-Key": "test-key"}
```

**Environment**:
```
DT_RAG_API_KEY = os.getenv('DT_RAG_API_KEY', 'test_api_key_for_testing')
```

---

### 4.2 Database Session Management

**Pattern 1** (Router-level, recommended):
```python
async with db_manager.get_session() as session:
    engine = ReflectionEngine(db_session=session)
    result = await engine.analyze_case_performance(...)
```

**Pattern 2** (Fixture-level, for isolated tests):
```python
async with async_session() as session:
    agent = await AgentDAO.create_agent(session=session, ...)
    yield agent
    # Cleanup in finally block
```

---

## 5. Error Handling & Assertions

### 5.1 Response Code Patterns

**Standard HTTP Codes Used**:
- **200 OK**: Successful query/analysis
- **202 Accepted**: Async task created (background jobs)
- **204 No Content**: Task cancelled successfully
- **400 Bad Request**: Invalid state transition (e.g., cannot cancel completed task)
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation error (Pydantic)
- **500 Internal Server Error**: Unhandled exceptions

### 5.2 Assertion Patterns

**Structure Validation**:
```python
assert "success_rate" in data
assert "total_executions" in data
assert isinstance(data["history"], list)
```

**Value Range Validation**:
```python
assert data["success_rate"] >= 0.0
assert data["success_rate"] <= 100.0
assert data["confidence"] >= 0.0
assert data["confidence"] <= 1.0
```

**Database State Verification**:
```python
async with async_session() as session:
    task = await session.get(BackgroundTask, task_id)
    assert task is not None
    assert task.status == "completed"
    assert task.completed_at is not None
```

**Time-Series Ordering**:
```python
history_items = data["history"]
assert history_items[0]["overall_coverage"] >= history_items[1]["overall_coverage"]
```

---

## 6. Performance Testing Patterns

### 6.1 Existing Performance Test Setup

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/performance/conftest.py`

**Minimal Setup** (can be extended):
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    yield

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
```

### 6.2 Performance Test Pattern (from SPEC-TEST-002 plan)

**SLA Requirements**:
- Health endpoints: < 100ms response time
- Batch operations: < 10 seconds completion

**Benchmark Pattern** (to be implemented):
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_batch_performance_under_10s(api_client):
    import time
    start = time.time()
    
    response = await api_client.post(
        "/api/v1/reflection/batch",
        headers={"X-API-Key": "test-key"}
    )
    
    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 10.0, f"Batch took {elapsed:.2f}s, expected < 10s"
```

---

## 7. Test Data & Fixtures

### 7.1 CaseBank Test Data Pattern

**Real Data Model**:
```python
class CaseBank(Base):
    __tablename__ = "case_bank"
    case_id: str  # Primary key
    query: str
    response_text: str
    category_path: List[str]  # ARRAY type in PostgreSQL
    query_vector: List[float]  # 1536-dimensional embeddings
    quality_score: float
    usage_count: int
    success_rate: float
    created_at: datetime
    last_used_at: Optional[datetime]
```

**Test Data Creation Pattern** (from test_consolidation_workflow.py):
```python
TestCaseBank(
    case_id="workflow-low-perf-001",
    query="low performance query",
    response_text="response",
    category_path='["AI", "Test"]',
    query_vector="[0.1, 0.2, 0.3]",
    success_rate=15.0,
    usage_count=20
)
```

### 7.2 ExecutionLog Test Data Pattern

**Real Data Model**:
```python
class ExecutionLog(Base):
    __tablename__ = "execution_log"
    log_id: int  # Auto-increment primary key
    case_id: str
    success: bool
    error_type: Optional[str]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    context: Optional[Dict[str, Any]]
    created_at: datetime
```

**Test Data Creation Pattern** (from test_reflection_workflow.py):
```python
for i in range(15):
    log = ExecutionLog(
        case_id="test-workflow-001",
        success=(i < 5),  # 33.3% success rate
        error_type="ValidationError" if i >= 5 else None,
        error_message=f"Error {i}" if i >= 5 else None,
        execution_time_ms=100 + i * 10,
    )
    session.add(log)
```

---

## 8. Docker & CI/CD Configuration

### 8.1 Current Docker Setup

**Location**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/docker-compose.test.yml`

**Current Minimal Setup**:
```yaml
services:
  test:
    image: nginx:alpine
    ports:
      - "9999:80"
```

**⚠️ NOTE**: This is a placeholder. For SPEC-TEST-002, should be expanded with PostgreSQL service.

### 8.2 Recommended PostgreSQL Service (to implement)

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dt_rag_test
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

## 9. Key Insights for SPEC-TEST-002

### 9.1 What's Already In Place

1. ✅ **Async test infrastructure** (pytest-asyncio, AsyncClient)
2. ✅ **Database session fixtures** with transaction isolation
3. ✅ **API authentication** (X-API-Key header)
4. ✅ **Pydantic response models** for both Reflection and Consolidation
5. ✅ **Database models** (CaseBank, ExecutionLog, CaseBankArchive)
6. ✅ **28 reference tests** in test_api_endpoints.py
7. ✅ **19 advanced async tests** in test_agent_api_phase3.py

### 9.2 What Needs Implementation for SPEC-TEST-002

1. ⚠️ **Docker PostgreSQL service** (placeholder in docker-compose.test.yml)
2. ⚠️ **Async fixtures specific to Reflection/Consolidation** (test_case_bank, test_execution_logs)
3. ⚠️ **24 integration tests** (12 Reflection, 12 Consolidation)
4. ⚠️ **Performance benchmarks** (pytest-benchmark integration)
5. ⚠️ **Coverage measurement** (pytest-cov with 95% target)

### 9.3 Reusable Patterns from Existing Tests

**From test_agent_api_phase3.py** (directly applicable):
```python
# Agent fixture pattern → Use for CaseBank
@pytest.fixture
async def test_agent(self):
    async with async_session() as session:
        agent = await AgentDAO.create_agent(...)
        yield agent
        await AgentDAO.delete_agent(session, agent.agent_id)

# AsyncClient pattern → Use for Reflection/Consolidation tests
@pytest.fixture
async def client(self):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Database verification pattern → Use for assertion checks
async with async_session() as session:
    task = await session.get(BackgroundTask, task_id)
    assert task.status == "completed"
```

---

## 10. Detailed File Reference

| File | Purpose | Key Components | Tests |
|------|---------|-----------------|-------|
| `tests/conftest.py` | Root pytest config | event_loop, db_engine, db_session, api_client | — |
| `tests/integration/test_api_endpoints.py` | Phase 1 API tests | 5 test classes | 28 tests |
| `tests/integration/test_agent_api_phase3.py` | Phase 3 background task API tests | 1 test class | 19 tests |
| `tests/integration/test_reflection_workflow.py` | Reflection engine workflow | setup_database, cleanup | 1+ tests |
| `tests/integration/test_consolidation_workflow.py` | Consolidation engine workflow | setup_database, cleanup_cases | 1+ tests |
| `apps/api/routers/reflection_router.py` | Reflection API endpoints | 4 endpoints (8 + health) | — |
| `apps/api/routers/consolidation_router.py` | Consolidation API endpoints | 4 endpoints (8 + health) | — |
| `apps/api/database.py` | SQLAlchemy models | 9 models (CaseBank, ExecutionLog, etc.) | — |
| `pyproject.toml` | Project config & dependencies | test deps, coverage config | — |

---

## 11. Environment Variables for Testing

**Required**:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test
NODE_ENV=test
DT_RAG_API_KEY=test_api_key_for_testing
ML_MODEL_NAME=all-MiniLM-L6-v2
```

---

## 12. Coverage Configuration (pyproject.toml)

```toml
[tool.coverage.run]
source = ["apps"]
omit = [
    "tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "@(abc\.)?abstractmethod",
]
```

**Command to measure coverage**:
```bash
pytest tests/integration/test_phase3_reflection.py tests/integration/test_phase3_consolidation.py --cov=apps --cov-report=html
```

---

## 13. Recommendations for SPEC-TEST-002

### 13.1 Fixture Strategy

**Create in conftest.py (or new conftest in tests/integration/)**:

```python
@pytest.fixture
async def test_case_bank(db_session):
    """Create test case with execution logs"""
    case = CaseBank(
        case_id=f"test-{uuid.uuid4()}",
        query="test query",
        response_text="test response",
        category_path=["AI", "Test"],
        query_vector=[0.1] * 1536,  # 1536-dim OpenAI embedding
        quality_score=0.85,
        usage_count=10,
        success_rate=85.0
    )
    db_session.add(case)
    await db_session.flush()
    
    # Add execution logs
    for i in range(10):
        log = ExecutionLog(
            case_id=case.case_id,
            success=True,
            execution_time_ms=100 + i * 10
        )
        db_session.add(log)
    await db_session.flush()
    
    yield case
```

### 13.2 Test File Organization

```
tests/integration/
├── conftest.py  # Common fixtures
├── test_api_endpoints.py  # SPEC-TEST-001 (existing)
├── test_phase3_reflection.py  # 12 tests (new)
└── test_phase3_consolidation.py  # 12 tests (new)
```

### 13.3 Critical Success Factors

1. **Use AsyncClient**, not TestClient (for actual async execution)
2. **Verify database changes**, not just response codes
3. **Test transaction isolation** with parallel fixtures
4. **Mock LLM calls** in Reflection.suggestions (to avoid API costs)
5. **Use @pytest.mark.asyncio** decorator on all async tests
6. **Measure SLA compliance** (< 100ms for health checks, < 10s for batch)

---

## 14. Implementation Checklist for SPEC-TEST-002

- [ ] Update `docker-compose.test.yml` with PostgreSQL service
- [ ] Create test fixtures in `tests/integration/conftest.py`
- [ ] Implement Phase 2: 12 Reflection API tests
- [ ] Implement Phase 3: 12 Consolidation API tests
- [ ] Add performance benchmarks (pytest-benchmark)
- [ ] Generate coverage report (target: 95% for Phase 3 APIs)
- [ ] Integrate with CI/CD pipeline (GitHub Actions)
- [ ] Document test patterns in project CLAUDE.md

---

**Report Generated**: 2025-10-23
**Last Updated**: conftest.py, test_api_endpoints.py, SPEC-TEST-002/plan.md
**Absolute Paths**: All file paths are absolute from `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag`

