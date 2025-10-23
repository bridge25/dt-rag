# Acceptance Criteria: SPEC-AGENT-GROWTH-002

## Overview

본 문서는 Agent Growth Platform Phase 1 REST API Integration의 상세한 수락 기준을 정의합니다. 각 API 엔드포인트별로 Given-When-Then 형식의 테스트 시나리오를 제공하며, 품질 게이트 기준과 검증 방법을 명시합니다.

## Acceptance Criteria

### AC-1: Agent Creation API

**Feature**: POST /api/v1/agents/from-taxonomy

**Scenario 1.1: Create agent with valid taxonomy scope**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블이 존재 (Phase 0 migration 완료)
- taxonomy_nodes 테이블에 노드 ID "550e8400-e29b-41d4-a716-446655440000"이 존재
- API Key "test-api-key"가 유효

**When**:
```http
POST /api/v1/agents/from-taxonomy
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "name": "Breast Cancer Treatment Specialist",
  "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "taxonomy_version": "1.0.0",
  "scope_description": "Agent focused on breast cancer diagnosis and treatment",
  "retrieval_config": {"top_k": 10, "strategy": "hybrid"}
}
```

**Then**:
- HTTP 상태 코드: 201 Created
- 응답 본문에 agent_id (UUID4) 포함
- 응답 본문에 name: "Breast Cancer Treatment Specialist" 포함
- 응답 본문에 taxonomy_node_ids 배열 포함
- 응답 본문에 coverage_percent >= 0.0 포함
- 응답 본문에 level: 1 포함
- 응답 본문에 created_at (ISO 8601 timestamp) 포함
- agents 테이블에 새 행 삽입 확인
- AgentDAO.create_agent() 호출 확인 (로그 검증)
- CoverageMeterService.calculate_coverage() 호출 확인 (로그 검증)

**Scenario 1.2: Create agent with invalid taxonomy node IDs**

**Given**:
- FastAPI 서버가 실행 중
- taxonomy_nodes 테이블에 "00000000-0000-0000-0000-000000000000" 노드가 존재하지 않음
- API Key가 유효

**When**:
```http
POST /api/v1/agents/from-taxonomy
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "name": "Invalid Agent",
  "taxonomy_node_ids": ["00000000-0000-0000-0000-000000000000"]
}
```

**Then**:
- HTTP 상태 코드: 400 Bad Request
- 응답 본문에 "Invalid taxonomy node IDs" 포함
- agents 테이블에 행 삽입 안 됨

**Scenario 1.3: Create agent with empty name**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
```http
POST /api/v1/agents/from-taxonomy
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "name": "",
  "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Then**:
- HTTP 상태 코드: 422 Unprocessable Entity
- 응답 본문에 Pydantic 검증 에러 포함
- 응답 본문에 "name" 필드 에러 포함

**Scenario 1.4: Create agent without API Key**

**Given**:
- FastAPI 서버가 실행 중
- Authorization 헤더 없음

**When**:
```http
POST /api/v1/agents/from-taxonomy
Content-Type: application/json

{
  "name": "Test Agent",
  "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Then**:
- HTTP 상태 코드: 401 Unauthorized
- 응답 본문에 "Invalid or missing API key" 포함

---

### AC-2: Agent Retrieval API

**Feature**: GET /api/v1/agents/{agent_id}

**Scenario 2.1: Get agent by valid ID**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "123e4567-e89b-12d3-a456-426614174000" 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agent_id: "123e4567-e89b-12d3-a456-426614174000" 포함
- 응답 본문에 name, taxonomy_node_ids, level, coverage_percent 포함
- AgentDAO.get_agent() 호출 확인

**Scenario 2.2: Get agent by non-existent ID**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "00000000-0000-0000-0000-000000000000" 존재하지 않음
- API Key가 유효

**When**:
```http
GET /api/v1/agents/00000000-0000-0000-0000-000000000000
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 404 Not Found
- 응답 본문에 "Agent not found" 포함

**Scenario 2.3: Get agent with invalid UUID format**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
```http
GET /api/v1/agents/invalid-uuid
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 422 Unprocessable Entity
- 응답 본문에 UUID 검증 에러 포함

---

### AC-3: Agent List API

**Feature**: GET /api/v1/agents

**Scenario 3.1: List all agents without filters**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 5개 agent 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agents 배열 포함 (길이: 5)
- 응답 본문에 total: 5 포함
- agents 배열이 created_at DESC 순서로 정렬
- AgentDAO.list_agents() 호출 확인

**Scenario 3.2: List agents with level filter**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 level=1 agent 3개, level=2 agent 2개 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents?level=1
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agents 배열 포함 (길이: 3)
- 응답 본문의 모든 agent가 level: 1
- 응답 본문에 filters_applied.level: 1 포함

**Scenario 3.3: List agents with min_coverage filter**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 coverage_percent >= 50.0 agent 2개, < 50.0 agent 3개 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents?min_coverage=50.0
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agents 배열 포함 (길이: 2)
- 응답 본문의 모든 agent가 coverage_percent >= 50.0
- 응답 본문에 filters_applied.min_coverage: 50.0 포함

**Scenario 3.4: List agents with max_results limit**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 100개 agent 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents?max_results=10
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agents 배열 포함 (길이: 10)
- 응답 본문에 total: 100 포함

**Scenario 3.5: List agents with max_results exceeding limit**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
```http
GET /api/v1/agents?max_results=200
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 422 Unprocessable Entity
- 응답 본문에 max_results 검증 에러 포함 (le=100)

---

### AC-4: Agent Coverage API

**Feature**: GET /api/v1/agents/{agent_id}/coverage

**Scenario 4.1: Calculate coverage for valid agent**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "123e4567-e89b-12d3-a456-426614174000" 존재
- agent.taxonomy_node_ids = ["550e8400-e29b-41d4-a716-446655440000"]
- doc_taxonomy 테이블에 해당 노드의 문서 10개 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/coverage
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agent_id 포함
- 응답 본문에 overall_coverage (float, 0.0-100.0) 포함
- 응답 본문에 node_coverage (Dict[str, float]) 포함
- 응답 본문에 document_counts (Dict[str, int]) 포함
- 응답 본문에 target_counts (Dict[str, int]) 포함
- 응답 본문에 version: "1.0.0" 포함
- 응답 본문에 calculated_at (ISO 8601 timestamp) 포함
- CoverageMeterService.calculate_coverage() 호출 확인
- agents 테이블의 coverage_percent 갱신 확인 (SQL 쿼리 검증)
- agents 테이블의 last_coverage_update 갱신 확인

**Scenario 4.2: Calculate coverage for non-existent agent**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "00000000-0000-0000-0000-000000000000" 존재하지 않음
- API Key가 유효

**When**:
```http
GET /api/v1/agents/00000000-0000-0000-0000-000000000000/coverage
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 404 Not Found
- 응답 본문에 "Agent not found" 포함

**Scenario 4.3: Coverage calculation timeout**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent 존재
- CoverageMeterService.calculate_coverage()가 타임아웃 (5초 초과)
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/coverage
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 503 Service Unavailable
- 응답 본문에 "Service unavailable" 또는 "Timeout" 포함

---

### AC-5: Agent Gap Detection API

**Feature**: GET /api/v1/agents/{agent_id}/gaps

**Scenario 5.1: Detect gaps with default threshold**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "123e4567-e89b-12d3-a456-426614174000" 존재
- agent.taxonomy_node_ids에 3개 노드 포함 (coverage: 30%, 60%, 80%)
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/gaps
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agent_id 포함
- 응답 본문에 gaps 배열 포함 (길이: 1, coverage 30% 노드만)
- 응답 본문에 threshold: 0.5 포함
- gaps[0].node_id 포함
- gaps[0].current_coverage: 30.0 포함
- gaps[0].target_coverage: 50.0 포함
- gaps[0].missing_docs (int) 포함
- gaps[0].recommendation (string) 포함
- 응답 본문에 detected_at (ISO 8601 timestamp) 포함
- CoverageMeterService.detect_gaps() 호출 확인

**Scenario 5.2: Detect gaps with custom threshold**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent 존재
- agent.taxonomy_node_ids에 3개 노드 포함 (coverage: 30%, 60%, 80%)
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/gaps?threshold=0.7
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 gaps 배열 포함 (길이: 2, coverage 30%, 60% 노드)
- 응답 본문에 threshold: 0.7 포함

**Scenario 5.3: No gaps detected (all nodes above threshold)**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent 존재
- agent.taxonomy_node_ids의 모든 노드 coverage >= 80%
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/gaps?threshold=0.5
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 gaps: [] (빈 배열) 포함
- 응답 본문에 threshold: 0.5 포함

**Scenario 5.4: Invalid threshold value**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/gaps?threshold=1.5
Authorization: Bearer test-api-key
```

**Then**:
- HTTP 상태 코드: 422 Unprocessable Entity
- 응답 본문에 threshold 검증 에러 포함 (le=1.0)

---

### AC-6: Agent Query API

**Feature**: POST /api/v1/agents/{agent_id}/query

**Scenario 6.1: Query agent with valid request**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "123e4567-e89b-12d3-a456-426614174000" 존재
- agent.taxonomy_node_ids = ["550e8400-e29b-41d4-a716-446655440000"]
- agent.retrieval_config.top_k = 5
- SearchDAO.hybrid_search() returns 5 results
- API Key가 유효

**When**:
```http
POST /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": "What are the latest treatments for HER2-positive breast cancer?",
  "include_metadata": true
}
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 agent_id 포함
- 응답 본문에 query 포함
- 응답 본문에 results 배열 포함 (길이: 5)
- results[0].doc_id (UUID4) 포함
- results[0].chunk_id (UUID4) 포함
- results[0].content (string) 포함
- results[0].score (float) 포함
- results[0].metadata (Dict) 포함
- 응답 본문에 total_results: 5 포함
- 응답 본문에 query_time_ms (float) 포함
- 응답 본문에 retrieval_strategy: "hybrid" 포함
- 응답 본문에 executed_at (ISO 8601 timestamp) 포함
- SearchDAO.hybrid_search() 호출 시 filters.canonical_in = agent.taxonomy_node_ids 확인
- agents 테이블의 total_queries 1 증가 확인
- agents 테이블의 last_query_at 갱신 확인

**Scenario 6.2: Query agent with custom top_k**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent 존재
- agent.retrieval_config.top_k = 5
- SearchDAO.hybrid_search() returns 10 results
- API Key가 유효

**When**:
```http
POST /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": "What is immunotherapy?",
  "top_k": 10
}
```

**Then**:
- HTTP 상태 코드: 200 OK
- 응답 본문에 results 배열 포함 (길이: 10)
- SearchDAO.hybrid_search() 호출 시 top_k=10 확인 (agent.retrieval_config.top_k 무시)

**Scenario 6.3: Query agent with empty query string**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
```http
POST /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": ""
}
```

**Then**:
- HTTP 상태 코드: 422 Unprocessable Entity
- 응답 본문에 query 필드 검증 에러 포함 (min_length=1)

**Scenario 6.4: Query agent with query exceeding max length**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
```http
POST /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": "<1001 characters string>"
}
```

**Then**:
- HTTP 상태 코드: 422 Unprocessable Entity
- 응답 본문에 query 필드 검증 에러 포함 (max_length=1000)

**Scenario 6.5: Query non-existent agent**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent_id "00000000-0000-0000-0000-000000000000" 존재하지 않음
- API Key가 유효

**When**:
```http
POST /api/v1/agents/00000000-0000-0000-0000-000000000000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": "Test query"
}
```

**Then**:
- HTTP 상태 코드: 404 Not Found
- 응답 본문에 "Agent not found" 포함

**Scenario 6.6: Query agent with SearchDAO timeout**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 agent 존재
- SearchDAO.hybrid_search() 타임아웃 (3초 초과)
- API Key가 유효

**When**:
```http
POST /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": "Test query"
}
```

**Then**:
- HTTP 상태 코드: 503 Service Unavailable
- 응답 본문에 "Service unavailable" 또는 "Timeout" 포함

---

### AC-7: OpenAPI Documentation

**Feature**: /docs and /redoc endpoints

**Scenario 7.1: Access Swagger UI**

**Given**:
- FastAPI 서버가 실행 중

**When**:
- 브라우저에서 http://localhost:8000/docs 접속

**Then**:
- Swagger UI 페이지 로드 성공
- "agents" 태그 아래 6개 엔드포인트 표시
- 각 엔드포인트에 summary, description 표시
- 각 엔드포인트에 "Try it out" 버튼 표시
- Request body schema에 예제 포함
- Response schema에 필드 설명 포함

**Scenario 7.2: Access ReDoc**

**Given**:
- FastAPI 서버가 실행 중

**When**:
- 브라우저에서 http://localhost:8000/redoc 접속

**Then**:
- ReDoc 페이지 로드 성공
- "agents" 태그 아래 6개 엔드포인트 표시
- 각 엔드포인트에 상세 설명 표시
- Request/Response schema 시각화

**Scenario 7.3: OpenAPI JSON schema**

**Given**:
- FastAPI 서버가 실행 중

**When**:
```http
GET /openapi.json
```

**Then**:
- HTTP 상태 코드: 200 OK
- JSON schema에 6개 엔드포인트 정의 포함
- 각 엔드포인트에 parameters, requestBody, responses 포함
- components.schemas에 모든 Pydantic 모델 포함
- AgentCreateRequest, AgentResponse, CoverageResponse, GapListResponse, QueryRequest, QueryResponse 스키마 포함

---

### AC-8: Error Handling

**Feature**: Consistent error responses

**Scenario 8.1: Database connection failure**

**Given**:
- FastAPI 서버가 실행 중
- PostgreSQL 데이터베이스가 다운됨
- API Key가 유효

**When**:
```http
POST /api/v1/agents/from-taxonomy
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "name": "Test Agent",
  "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Then**:
- HTTP 상태 코드: 503 Service Unavailable
- 응답 본문에 "Service unavailable" 또는 "Database unavailable" 포함
- 응답 본문에 민감한 정보 (DB 호스트, 포트, 스택 트레이스) 노출 안 됨

**Scenario 8.2: Unexpected exception**

**Given**:
- FastAPI 서버가 실행 중
- AgentDAO.create_agent()에서 예상치 못한 예외 발생
- API Key가 유효

**When**:
```http
POST /api/v1/agents/from-taxonomy
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "name": "Test Agent",
  "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

**Then**:
- HTTP 상태 코드: 500 Internal Server Error
- 응답 본문에 generic error message 포함
- 응답 본문에 스택 트레이스 노출 안 됨
- 서버 로그에 전체 traceback 기록

**Scenario 8.3: RFC 7807 Problem Details format**

**Given**:
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
- 어떤 에러든 발생

**Then**:
- 응답 본문이 RFC 7807 형식 준수 (Optional, 기존 FastAPI 에러 형식 사용 가능)
- type, title, status, detail 필드 포함

---

### AC-9: Performance Requirements

**Feature**: API response time constraints

**Scenario 9.1: POST /agents/from-taxonomy performance**

**Given**:
- FastAPI 서버가 실행 중
- taxonomy_node_ids에 50개 노드 포함 (descendants 포함 총 100개)
- doc_taxonomy 테이블에 5,000개 문서 존재
- API Key가 유효

**When**:
```http
POST /api/v1/agents/from-taxonomy
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "name": "Large Scope Agent",
  "taxonomy_node_ids": ["<50 node IDs>"]
}
```

**Then**:
- 응답 시간 < 10초
- agents 테이블에 행 삽입 성공
- coverage_percent 계산 완료

**Scenario 9.2: GET /agents/{agent_id}/coverage performance**

**Given**:
- FastAPI 서버가 실행 중
- agent.taxonomy_node_ids에 50개 노드 포함
- doc_taxonomy 테이블에 10,000개 문서 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/coverage
Authorization: Bearer test-api-key
```

**Then**:
- 응답 시간 < 5초
- CoverageResponse 반환 성공

**Scenario 9.3: POST /agents/{agent_id}/query performance**

**Given**:
- FastAPI 서버가 실행 중
- agent.retrieval_config.top_k = 20
- SearchDAO.hybrid_search() 실행 시간 2초
- API Key가 유효

**When**:
```http
POST /api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query
Authorization: Bearer test-api-key
Content-Type: application/json

{
  "query": "Test query"
}
```

**Then**:
- 응답 시간 < 3초
- QueryResponse 반환 성공

**Scenario 9.4: GET /agents performance with large dataset**

**Given**:
- FastAPI 서버가 실행 중
- agents 테이블에 1,000개 agent 존재
- API Key가 유효

**When**:
```http
GET /api/v1/agents?max_results=50
Authorization: Bearer test-api-key
```

**Then**:
- 응답 시간 < 1초
- AgentListResponse 반환 성공 (50 agents)

---

### AC-10: Integration with Phase 0

**Feature**: Seamless integration with AgentDAO and CoverageMeterService

**Scenario 10.1: Verify AgentDAO integration**

**Given**:
- Phase 0 구현 완료 (AgentDAO.create_agent, get_agent, list_agents)
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
- POST /agents/from-taxonomy 호출

**Then**:
- AgentDAO.create_agent() 호출 확인 (로그 또는 Mock 검증)
- agents 테이블에 행 삽입 확인

**Scenario 10.2: Verify CoverageMeterService integration**

**Given**:
- Phase 0 구현 완료 (CoverageMeterService.calculate_coverage)
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
- GET /agents/{agent_id}/coverage 호출

**Then**:
- CoverageMeterService.calculate_coverage() 호출 확인
- CoverageResult 반환값을 CoverageResponse로 변환 확인

**Scenario 10.3: Verify SearchDAO integration**

**Given**:
- SearchDAO.hybrid_search() 구현 완료
- FastAPI 서버가 실행 중
- API Key가 유효

**When**:
- POST /agents/{agent_id}/query 호출

**Then**:
- SearchDAO.hybrid_search() 호출 시 filters.canonical_in = agent.taxonomy_node_ids 확인
- SearchDAO 결과를 QueryResponse로 변환 확인

---

## Quality Gates

### Code Quality

**Linting**:
- ✅ pylint score >= 9.0
- ✅ flake8 zero errors
- ✅ black formatting applied

**Type Checking**:
- ✅ mypy zero errors (strict mode)
- ✅ All function signatures have type hints
- ✅ All Pydantic models use proper types (UUID4, datetime, Dict, List)

**Code Review**:
- ✅ No hardcoded credentials or secrets
- ✅ No SQL injection vulnerabilities
- ✅ No XSS vulnerabilities
- ✅ Proper error handling in all endpoints

### Test Coverage

**Unit Tests**:
- ✅ Test coverage >= 90%
- ✅ All 6 endpoints covered
- ✅ All error paths covered
- ✅ All Pydantic validation rules covered

**Integration Tests**:
- ✅ All 6 endpoints tested with real database
- ✅ Transaction rollback working correctly
- ✅ Database constraints enforced

**API Tests**:
- ✅ OpenAPI schema validation passed
- ✅ All endpoints documented in /docs
- ✅ All request/response examples valid

**Performance Tests**:
- ✅ All performance constraints met (AC-9)
- ✅ No N+1 query problems
- ✅ Database queries optimized (EXPLAIN ANALYZE)

### Documentation

**OpenAPI**:
- ✅ All 6 endpoints documented
- ✅ All schemas include examples
- ✅ All parameters include descriptions
- ✅ Response codes documented

**Code Comments**:
- ✅ Complex logic explained (not obvious code)
- ✅ No redundant comments (avoid "code as truth" violations)

### Security

**Authentication**:
- ✅ All endpoints require API Key
- ✅ Invalid API Key returns 401
- ✅ API Key not logged in plain text

**Data Validation**:
- ✅ All user inputs validated (Pydantic)
- ✅ UUID format validated
- ✅ String length limits enforced
- ✅ Numeric range limits enforced

**Error Handling**:
- ✅ No sensitive data in error responses
- ✅ No stack traces in production
- ✅ Generic error messages for unexpected exceptions

## Definition of Done

**Feature Complete**:
- ✅ 6 endpoints implemented and tested
- ✅ Pydantic schemas defined (8 models)
- ✅ Error handling implemented
- ✅ OpenAPI documentation generated

**Tests Pass**:
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All API tests pass
- ✅ All performance tests pass

**Quality Gates Met**:
- ✅ Code quality checks pass (linting, type checking)
- ✅ Test coverage >= 90%
- ✅ Documentation complete
- ✅ Security checks pass

**Integration Verified**:
- ✅ Phase 0 AgentDAO integration working
- ✅ Phase 0 CoverageMeterService integration working
- ✅ SearchDAO integration working
- ✅ API Key authentication working

**Deployment Ready**:
- ✅ Main app integration complete (app.include_router)
- ✅ CORS configured
- ✅ Environment variables documented
- ✅ Database migrations applied (Phase 0 prerequisite)

## Verification Methods

### Manual Testing

**Tools**:
- Postman or Insomnia for manual API testing
- Browser for /docs and /redoc verification
- pgAdmin for database state verification

**Checklist**:
1. Start FastAPI server (`uvicorn apps.api.main:app --reload`)
2. Open http://localhost:8000/docs
3. Test each endpoint with "Try it out" button
4. Verify responses match expected schemas
5. Check database state after each operation

### Automated Testing

**Commands**:
```bash
# Unit tests
pytest tests/unit/test_agent_router.py -v

# Integration tests
pytest tests/integration/test_agent_api.py -v

# API tests
pytest tests/api/test_agent_openapi.py -v

# Performance tests
pytest tests/performance/test_agent_api_performance.py -v

# Full test suite with coverage
pytest --cov=apps.api.routers --cov=apps.api.schemas --cov-report=html
```

**Coverage Report**:
- Open `htmlcov/index.html` in browser
- Verify coverage >= 90%
- Identify uncovered lines

### Load Testing

**Tool**: Locust or Apache Bench

**Scenario**:
```python
# locustfile.py
from locust import HttpUser, task, between

class AgentAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_agents(self):
        self.client.get("/api/v1/agents", headers={"Authorization": "Bearer test-api-key"})

    @task(1)
    def query_agent(self):
        self.client.post("/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query", json={
            "query": "Test query"
        }, headers={"Authorization": "Bearer test-api-key"})
```

**Command**:
```bash
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

**Metrics**:
- Average response time < 1 second
- 95th percentile < 3 seconds
- Error rate < 1%

## Rollback Plan

**Trigger Conditions**:
- Critical bug in production (HTTP 500 error rate > 5%)
- Performance degradation (response time > 10 seconds)
- Security vulnerability discovered

**Rollback Steps**:
1. Revert `apps/api/main.py` (remove `include_router(agent_router)`)
2. Restart FastAPI server
3. Verify /docs no longer shows agent endpoints
4. Verify existing endpoints still working

**Rollback Verification**:
- ✅ No HTTP 500 errors in logs
- ✅ Existing endpoints responding normally
- ✅ Database state unchanged (no data loss)

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/tutorial/testing/
- Pydantic v2 Validation: https://docs.pydantic.dev/latest/concepts/validators/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- RFC 7807 Problem Details: https://datatracker.ietf.org/doc/html/rfc7807
