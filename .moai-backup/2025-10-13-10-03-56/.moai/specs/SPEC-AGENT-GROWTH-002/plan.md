# Implementation Plan: SPEC-AGENT-GROWTH-002

## Overview

본 문서는 Agent Growth Platform Phase 1 REST API Integration의 구현 계획을 정의합니다. Phase 0에서 구현된 AgentDAO와 CoverageMeterService를 FastAPI REST API로 노출하여 프론트엔드와 통합 가능한 HTTP 엔드포인트를 제공합니다.

## Prerequisites

**Phase 0 완료 필수**:
- ✅ agents 테이블 생성 완료 (Alembic migration 실행)
- ✅ AgentDAO.create_agent(), get_agent(), update_agent(), list_agents() 구현
- ✅ CoverageMeterService.calculate_coverage(), detect_gaps() 구현
- ✅ Agent ORM model with 19 columns

**기존 코드 확인 필수**:
- apps/api/security.py: get_api_key() 의존성 확인
- apps/api/database.py: get_session() 의존성 확인
- apps/api/exceptions.py: 기존 HTTPException 패턴 확인
- apps/api/main.py: include_router() 패턴 확인

## Implementation Strategy

### Phase 1-1: Pydantic Schema 정의

**목표**: Request/Response 스키마 정의 및 OpenAPI 문서화 준비

**작업 항목**:
1. `apps/api/schemas/agent_schemas.py` 파일 생성
2. AgentCreateRequest 스키마 구현 (name, taxonomy_node_ids, taxonomy_version, scope_description, retrieval_config, features_config)
3. AgentResponse 스키마 구현 (Agent ORM 모델의 모든 필드)
4. AgentListResponse 스키마 구현 (agents 배열, total, filters_applied)
5. CoverageResponse 스키마 구현 (overall_coverage, node_coverage, document_counts, target_counts)
6. GapResponse 및 GapListResponse 스키마 구현
7. QueryRequest 및 QueryResponse 스키마 구현 (query, top_k, streaming, results)
8. SearchResultItem 스키마 구현 (doc_id, chunk_id, content, score, metadata)
9. 모든 스키마에 model_config with json_schema_extra 예제 추가
10. Pydantic Field 검증 규칙 추가 (min_length, max_length, ge, le)

**검증 기준**:
- 모든 스키마가 Pydantic BaseModel 상속
- UUID 필드는 UUID4 타입 사용
- datetime 필드는 자동 ISO 8601 직렬화
- 각 스키마에 OpenAPI 예제 포함

**우선순위**: High

**의존성**: 없음

---

### Phase 1-2: FastAPI Router 생성

**목표**: 6개 엔드포인트를 포함한 FastAPI Router 구현

**작업 항목**:
1. `apps/api/routers/agent_router.py` 파일 생성
2. FastAPI APIRouter 인스턴스 생성 (prefix="/agents", tags=["agents"])
3. POST /from-taxonomy 엔드포인트 구현
   - AgentCreateRequest 스키마 사용
   - AgentDAO.create_agent() 호출
   - 201 Created 응답
4. GET /{agent_id} 엔드포인트 구현
   - UUID4 path parameter 검증
   - AgentDAO.get_agent() 호출
   - 404 Not Found 처리
5. GET / 엔드포인트 구현
   - Query parameters: level, min_coverage, max_results
   - AgentDAO.list_agents() 호출
   - AgentListResponse 반환
6. GET /{agent_id}/coverage 엔드포인트 구현
   - CoverageMeterService.calculate_coverage() 호출
   - AgentDAO.update_agent() 호출 (coverage_percent, last_coverage_update 갱신)
   - CoverageResponse 반환
7. GET /{agent_id}/gaps 엔드포인트 구현
   - Query parameter: threshold (default 0.5)
   - CoverageMeterService.detect_gaps() 호출
   - GapListResponse 반환
8. POST /{agent_id}/query 엔드포인트 구현
   - QueryRequest 스키마 사용
   - SearchDAO.hybrid_search() 호출 (filters: canonical_in, version)
   - AgentDAO.update_agent() 호출 (total_queries, last_query_at 갱신)
   - QueryResponse 반환

**검증 기준**:
- 모든 엔드포인트가 async def 함수
- 모든 엔드포인트에 Depends(get_api_key) 의존성 적용
- 모든 엔드포인트에 Depends(get_session) 의존성 적용
- 모든 엔드포인트에 response_model, status_code, summary, description 설정
- 에러 처리: try-except with HTTPException
- 로깅: logging.info/error 사용

**우선순위**: High

**의존성**: Phase 1-1 완료 (스키마 정의)

---

### Phase 1-3: Error Handling & Validation

**목표**: 견고한 에러 처리 및 입력 검증 구현

**작업 항목**:
1. taxonomy_node_ids 검증 함수 구현 (validate_taxonomy_nodes)
   - taxonomy_nodes 테이블 조회
   - 존재하지 않는 node_id → ValueError 발생
2. POST /from-taxonomy 에러 처리
   - 400 Bad Request: 잘못된 taxonomy_node_ids
   - 422 Unprocessable Entity: Pydantic 검증 실패
   - 503 Service Unavailable: 데이터베이스 연결 실패
3. GET /{agent_id} 에러 처리
   - 404 Not Found: 존재하지 않는 agent_id
4. GET /{agent_id}/coverage 에러 처리
   - 404 Not Found: 존재하지 않는 agent_id
   - 503 Service Unavailable: 커버리지 계산 타임아웃
5. POST /{agent_id}/query 에러 처리
   - 404 Not Found: 존재하지 않는 agent_id
   - 503 Service Unavailable: SearchDAO 타임아웃
6. 전역 예외 핸들러 추가 (main.py)
   - 500 Internal Server Error: 예상치 못한 예외 (민감 정보 노출 방지)
7. RFC 7807 Problem Details 형식 준수
   - type, title, status, detail 필드 포함

**검증 기준**:
- 모든 에러 응답이 적절한 HTTP 상태 코드 사용
- 프로덕션 환경에서 스택 트레이스 노출 안 됨
- 로그에는 전체 traceback 기록

**우선순위**: High

**의존성**: Phase 1-2 완료 (Router 구현)

---

### Phase 1-4: Main App 통합

**목표**: agent_router를 main FastAPI app에 통합

**작업 항목**:
1. `apps/api/main.py` 수정
2. agent_router import 추가
3. app.include_router(agent_router, prefix="/api/v1", tags=["agents"]) 추가
4. CORS 설정 확인 (기존 설정 유지)
5. OpenAPI 문서 설정 확인 (/docs, /redoc)

**검증 기준**:
- /docs 접속 시 agent 엔드포인트 표시
- /redoc 접속 시 문서화 확인
- CORS 설정으로 프론트엔드 접근 가능

**우선순위**: Medium

**의존성**: Phase 1-2 완료 (Router 구현)

---

### Phase 1-5: Unit Test 작성

**목표**: Router 로직의 단위 테스트 작성

**작업 항목**:
1. `tests/unit/test_agent_router.py` 파일 생성
2. pytest fixtures 설정 (mock_session, mock_agent_dao, mock_coverage_service)
3. POST /from-taxonomy 테스트
   - 유효한 요청 → 201 Created
   - 잘못된 taxonomy_node_ids → 400 Bad Request
   - 빈 name → 422 Unprocessable Entity
4. GET /{agent_id} 테스트
   - 유효한 ID → 200 OK
   - 존재하지 않는 ID → 404 Not Found
5. GET / 테스트
   - 필터 없음 → 전체 목록 반환
   - level 필터 → 필터링된 목록 반환
   - min_coverage 필터 → 필터링된 목록 반환
6. GET /{agent_id}/coverage 테스트
   - 유효한 ID → 200 OK with CoverageResponse
   - agents.coverage_percent 갱신 확인
7. GET /{agent_id}/gaps 테스트
   - threshold 0.5 → gaps 반환
   - threshold 1.0 → 빈 gaps 반환
8. POST /{agent_id}/query 테스트
   - 유효한 요청 → 200 OK with QueryResponse
   - agents.total_queries 증가 확인
9. 인증 테스트
   - API Key 없음 → 401 Unauthorized

**검증 기준**:
- 모든 테스트가 독립적으로 실행 가능
- Mock 객체 사용으로 실제 데이터베이스 불필요
- 테스트 커버리지 > 90%

**우선순위**: High

**의존성**: Phase 1-3 완료 (Error Handling)

---

### Phase 1-6: Integration Test 작성

**목표**: 실제 데이터베이스를 사용한 통합 테스트 작성

**작업 항목**:
1. `tests/integration/test_agent_api.py` 파일 생성
2. pytest fixtures 설정 (test_db, test_session, test_app)
3. E2E 테스트: Agent 생성 → 조회 → 커버리지 계산 → 갭 감지 → 쿼리 실행
4. Agent 생성 후 agents 테이블 검증
5. 커버리지 계산 후 coverage_percent 갱신 확인
6. 쿼리 실행 후 total_queries 증가 확인
7. 필터링 동작 검증 (level, min_coverage)
8. 갭 감지 로직 검증 (threshold 변화)

**검증 기준**:
- 실제 PostgreSQL 테스트 데이터베이스 사용
- 트랜잭션 롤백으로 테스트 격리
- 모든 엔드포인트가 실제 데이터베이스와 통합 동작

**우선순위**: Medium

**의존성**: Phase 1-5 완료 (Unit Test)

---

### Phase 1-7: OpenAPI Documentation

**목표**: OpenAPI 문서 품질 개선 및 예제 추가

**작업 항목**:
1. 모든 엔드포인트에 상세한 description 추가
2. 모든 스키마에 json_schema_extra 예제 추가
3. Path parameters에 description 추가
4. Query parameters에 description 추가
5. Response 예제 추가 (responses parameter)
6. /docs 페이지 직접 확인 및 개선

**검증 기준**:
- /docs 페이지가 사용자 친화적
- 모든 엔드포인트에 Try it out 기능 동작
- 예제 요청/응답이 실제 사용 가능한 형식

**우선순위**: Low

**의존성**: Phase 1-4 완료 (Main App 통합)

---

### Phase 1-8: Performance Test 작성

**목표**: API 성능 벤치마크 테스트 작성

**작업 항목**:
1. `tests/performance/test_agent_api_performance.py` 파일 생성
2. POST /from-taxonomy 성능 테스트
   - 10 nodes, 1K documents → < 10초
3. GET /{agent_id}/coverage 성능 테스트
   - 50 nodes, 10K documents → < 5초
4. POST /{agent_id}/query 성능 테스트
   - top_k=20 → < 3초
5. GET / 성능 테스트
   - 50 agents → < 1초

**검증 기준**:
- 모든 성능 테스트가 제약 조건 충족
- 성능 저하 시 경고 로그 출력

**우선순위**: Low

**의존성**: Phase 1-6 완료 (Integration Test)

---

## Technical Approach

### 1. Pydantic Schema Design

**원칙**:
- 모든 필드에 명시적 타입 힌트 사용
- Field(...) 사용으로 검증 규칙 명시
- model_config with json_schema_extra로 OpenAPI 예제 제공
- Optional[T] 사용으로 nullable 필드 명시
- UUID4 타입 사용으로 자동 UUID 검증

**예제**:
```python
class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent display name")
    taxonomy_node_ids: List[UUID4] = Field(..., min_length=1, description="Taxonomy node IDs")
    taxonomy_version: str = Field(default="1.0.0", description="Taxonomy version")
    scope_description: Optional[str] = Field(None, max_length=500)
    retrieval_config: Optional[Dict[str, Any]] = Field(default={"top_k": 5, "strategy": "hybrid"})
    features_config: Optional[Dict[str, Any]] = Field(default={})

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "name": "Breast Cancer Specialist",
                "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "taxonomy_version": "1.0.0",
                "scope_description": "Agent focused on breast cancer treatment"
            }]
        }
    )
```

### 2. Router Structure

**원칙**:
- 각 엔드포인트는 독립적인 async def 함수
- Depends(get_api_key), Depends(get_session) 의존성 주입
- try-except 블록으로 에러 처리
- logging 모듈로 요청/응답 로깅
- response_model, status_code, summary, description 명시

**예제**:
```python
@router.post(
    "/from-taxonomy",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent from taxonomy scope",
    description="Creates a new agent with specified taxonomy scope."
)
async def create_agent_from_taxonomy(
    request: AgentCreateRequest,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
) -> AgentResponse:
    logger.info(f"Creating agent: {request.name}")

    try:
        await validate_taxonomy_nodes(session, request.taxonomy_node_ids)
        agent = await AgentDAO.create_agent(session=session, **request.model_dump())
        logger.info(f"Agent created: {agent.agent_id}")
        return AgentResponse.model_validate(agent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unavailable")
```

### 3. Error Handling Strategy

**원칙**:
- 400 Bad Request: 클라이언트 입력 오류 (잘못된 taxonomy_node_ids)
- 404 Not Found: 리소스 존재하지 않음 (agent_id)
- 422 Unprocessable Entity: Pydantic 검증 실패 (자동 처리)
- 503 Service Unavailable: 백엔드 서비스 오류 (DB, SearchDAO)
- 500 Internal Server Error: 예상치 못한 예외 (전역 핸들러)

**예제**:
```python
try:
    agent = await AgentDAO.get_agent(session, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return AgentResponse.model_validate(agent)
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 4. Integration with Phase 0

**AgentDAO 호출**:
```python
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

**CoverageMeterService 호출**:
```python
coverage_service = CoverageMeterService(session=session)
coverage_result = await coverage_service.calculate_coverage(
    agent_id=str(agent.agent_id),
    taxonomy_node_ids=[str(nid) for nid in agent.taxonomy_node_ids],
    version=agent.taxonomy_version
)
```

**SearchDAO 호출**:
```python
results = await SearchDAO.hybrid_search(
    query=request.query,
    filters={
        "canonical_in": agent.taxonomy_node_ids,
        "version": agent.taxonomy_version
    },
    top_k=request.top_k or agent.retrieval_config.get("top_k", 5)
)
```

### 5. Testing Strategy

**Unit Test (Mock Dependencies)**:
```python
@pytest.fixture
def mock_agent_dao(mocker):
    mock = mocker.patch("apps.api.routers.agent_router.AgentDAO")
    return mock

async def test_create_agent_success(mock_agent_dao, test_client):
    mock_agent_dao.create_agent.return_value = Agent(
        agent_id=uuid4(),
        name="Test Agent",
        # ... other fields
    )

    response = test_client.post("/api/v1/agents/from-taxonomy", json={
        "name": "Test Agent",
        "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
    })

    assert response.status_code == 201
    assert response.json()["name"] == "Test Agent"
```

**Integration Test (Real Database)**:
```python
@pytest.fixture
async def test_session(test_db):
    async with AsyncSession(test_db) as session:
        yield session
        await session.rollback()

async def test_create_agent_e2e(test_session, test_client):
    response = test_client.post("/api/v1/agents/from-taxonomy", json={
        "name": "E2E Test Agent",
        "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
    })

    assert response.status_code == 201
    agent_id = response.json()["agent_id"]

    # Verify database row exists
    result = await test_session.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    )
    agent = result.scalar_one()
    assert agent.name == "E2E Test Agent"
```

## Risk Assessment

### 1. Phase 0 의존성
**리스크**: Phase 0 (SPEC-AGENT-GROWTH-001) 미완료 시 Phase 1 시작 불가
**대응**: Phase 0 완료 상태 확인 후 Phase 1 시작

### 2. API Key 인증 변경
**리스크**: 기존 `get_api_key()` 함수가 변경되면 모든 엔드포인트 수정 필요
**대응**: 의존성 주입 패턴 사용으로 변경 영향 최소화

### 3. SearchDAO 타임아웃
**리스크**: hybrid_search() 호출이 느린 경우 503 에러 발생
**대응**: 적절한 타임아웃 설정 및 에러 핸들링

### 4. 커버리지 계산 성능
**리스크**: 대규모 taxonomy scope에서 coverage 계산이 10초 초과
**대응**: 성능 테스트로 병목 지점 식별 및 최적화

### 5. OpenAPI 문서 품질
**리스크**: 자동 생성 문서가 사용자 친화적이지 않을 수 있음
**대응**: json_schema_extra 예제 추가 및 description 상세화

## Success Criteria

### Definition of Done

1. ✅ 6개 엔드포인트 구현 완료 (POST /from-taxonomy, GET /{id}, GET /, GET /coverage, GET /gaps, POST /query)
2. ✅ Pydantic 스키마 정의 완료 (8개 스키마)
3. ✅ API Key 인증 통합 완료
4. ✅ 에러 처리 구현 완료 (400, 404, 422, 503, 500)
5. ✅ Unit Test 작성 완료 (커버리지 > 90%)
6. ✅ Integration Test 작성 완료
7. ✅ OpenAPI 문서 생성 완료 (/docs, /redoc)
8. ✅ 성능 테스트 통과 (모든 제약 조건 충족)
9. ✅ Main app 통합 완료 (app.include_router)
10. ✅ Phase 0 AgentDAO, CoverageMeterService와 통합 동작 확인

### Quality Gates

**코드 품질**:
- Linting: pylint, flake8 통과
- Type checking: mypy 통과
- Code formatting: black 적용

**테스트**:
- Unit test coverage > 90%
- All integration tests pass
- All performance tests pass

**문서**:
- OpenAPI 문서에 모든 엔드포인트 포함
- 모든 스키마에 예제 포함

## Next Steps

**Phase 1 완료 후**:
1. `/alfred:2-build SPEC-AGENT-GROWTH-002` 실행으로 구현 시작
2. Phase 2: Agent Query 성능 최적화 및 XP 시스템 통합 검토
3. Frontend 통합: React 대시보드에서 Agent API 호출 구현
4. Phase 3: Agent Growth 시스템 고도화 (레벨링, 기능 잠금 해제)

## References

- SPEC-AGENT-GROWTH-001: Phase 0 Foundation (AgentDAO, CoverageMeterService)
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic v2 Documentation: https://docs.pydantic.dev/latest/
- RFC 7807 Problem Details: https://datatracker.ietf.org/doc/html/rfc7807
