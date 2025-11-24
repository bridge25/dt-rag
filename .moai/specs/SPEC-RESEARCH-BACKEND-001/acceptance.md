# SPEC-RESEARCH-BACKEND-001 Acceptance Criteria

---
spec_id: SPEC-RESEARCH-BACKEND-001
created: 2025-11-24
updated: 2025-11-24
author: spec-builder
---

## Overview

Research Agent Backend API의 인수 기준입니다. Given-When-Then 형식의 테스트 시나리오와 체크리스트를 포함합니다.

---

## 1. API Endpoint Scenarios

### Scenario 1: 리서치 세션 시작 (AC-001)

**Given** 유효한 리서치 쿼리와 설정이 준비되었을 때
**When** 사용자가 `POST /api/v1/research`를 호출하면
**Then** 시스템은 201 Created와 함께 세션 ID를 반환한다
**And** 백그라운드 리서치 작업이 시작된다
**And** Redis에 세션 상태가 저장된다

```python
# Test Implementation
async def test_start_research_success():
    response = await client.post("/api/v1/research", json={
        "query": "AI 기술 동향",
        "config": {"maxDocuments": 50, "depthLevel": "medium"}
    })
    assert response.status_code == 201
    data = response.json()
    assert "sessionId" in data
    assert "estimatedDuration" in data
```

### Scenario 2: 잘못된 쿼리로 리서치 시작 (AC-002)

**Given** 빈 문자열 또는 유효하지 않은 쿼리가 제공되었을 때
**When** 사용자가 `POST /api/v1/research`를 호출하면
**Then** 시스템은 422 Unprocessable Entity를 반환한다
**And** 에러 메시지에 검증 실패 상세가 포함된다

```python
async def test_start_research_invalid_query():
    response = await client.post("/api/v1/research", json={"query": ""})
    assert response.status_code == 422
    assert "query" in response.json()["detail"][0]["loc"]
```

### Scenario 3: 리서치 상태 조회 (AC-003)

**Given** 활성화된 리서치 세션이 존재할 때
**When** 사용자가 `GET /api/v1/research/{id}`를 호출하면
**Then** 시스템은 200 OK와 함께 세션 상세 정보를 반환한다
**And** 현재 스테이지, 진행률, 수집된 문서 목록이 포함된다

```python
async def test_get_research_status():
    # Given: 세션 생성
    create_resp = await client.post("/api/v1/research", json={"query": "test"})
    session_id = create_resp.json()["sessionId"]

    # When: 상태 조회
    response = await client.get(f"/api/v1/research/{session_id}")

    # Then: 상태 정보 반환
    assert response.status_code == 200
    session = response.json()["session"]
    assert "stage" in session
    assert "progress" in session
    assert "documents" in session
```

### Scenario 4: 존재하지 않는 세션 조회 (AC-004)

**Given** 존재하지 않는 세션 ID가 제공되었을 때
**When** 사용자가 `GET /api/v1/research/{id}`를 호출하면
**Then** 시스템은 404 Not Found를 반환한다

```python
async def test_get_research_not_found():
    response = await client.get("/api/v1/research/non-existent-uuid")
    assert response.status_code == 404
```

### Scenario 5: 문서 임포트 성공 (AC-005)

**Given** 리서치 세션이 confirming 스테이지에 있을 때
**When** 사용자가 `POST /api/v1/research/{id}/import`를 호출하면
**Then** 시스템은 200 OK를 반환한다
**And** 선택된 문서가 시스템에 임포트된다
**And** taxonomy_id가 제공되면 택소노미가 업데이트된다

```python
async def test_import_documents_success():
    # Given: confirming 상태의 세션 (fixture로 준비)
    session_id = await create_confirming_session()

    # When: 문서 임포트
    response = await client.post(f"/api/v1/research/{session_id}/import", json={
        "selectedDocumentIds": ["doc-1", "doc-2"],
        "taxonomyId": "taxonomy-uuid"
    })

    # Then: 임포트 성공
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["documentsImported"] == 2
    assert data["taxonomyUpdated"] is True
```

### Scenario 6: 잘못된 상태에서 문서 임포트 (AC-006)

**Given** 리서치 세션이 confirming 스테이지가 아닐 때
**When** 사용자가 `POST /api/v1/research/{id}/import`를 호출하면
**Then** 시스템은 409 Conflict를 반환한다

```python
async def test_import_documents_invalid_state():
    # Given: analyzing 상태의 세션
    create_resp = await client.post("/api/v1/research", json={"query": "test"})
    session_id = create_resp.json()["sessionId"]

    # When: 임포트 시도 (세션은 아직 analyzing 상태)
    response = await client.post(f"/api/v1/research/{session_id}/import", json={
        "selectedDocumentIds": ["doc-1"]
    })

    # Then: Conflict 응답
    assert response.status_code == 409
```

### Scenario 7: 리서치 취소 및 삭제 (AC-007)

**Given** 활성화된 리서치 세션이 존재할 때
**When** 사용자가 `DELETE /api/v1/research/{id}`를 호출하면
**Then** 시스템은 204 No Content를 반환한다
**And** 세션이 Redis에서 삭제된다
**And** 진행 중인 백그라운드 작업이 취소된다

```python
async def test_delete_research_session():
    # Given: 세션 생성
    create_resp = await client.post("/api/v1/research", json={"query": "test"})
    session_id = create_resp.json()["sessionId"]

    # When: 삭제
    response = await client.delete(f"/api/v1/research/{session_id}")

    # Then: 삭제 성공
    assert response.status_code == 204

    # And: 세션 조회 불가
    get_resp = await client.get(f"/api/v1/research/{session_id}")
    assert get_resp.status_code == 404
```

---

## 2. SSE Streaming Scenarios

### Scenario 8: SSE 연결 및 이벤트 수신 (AC-008)

**Given** 활성화된 리서치 세션이 존재할 때
**When** 사용자가 `GET /api/v1/research/{id}/stream`에 SSE 연결하면
**Then** 시스템은 `text/event-stream` 응답을 시작한다
**And** 리서치 진행에 따라 이벤트를 수신한다

```python
async def test_sse_stream_connection():
    # Given: 세션 생성
    create_resp = await client.post("/api/v1/research", json={"query": "test"})
    session_id = create_resp.json()["sessionId"]

    # When: SSE 연결
    async with client.stream("GET", f"/api/v1/research/{session_id}/stream") as response:
        assert response.headers["content-type"] == "text/event-stream"

        # Then: 이벤트 수신
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))
                if len(events) >= 3:
                    break

        assert len(events) >= 1
```

### Scenario 9: 모든 SSE 이벤트 타입 수신 (AC-009)

**Given** 리서치 세션이 진행 중일 때
**When** SSE 스트림을 통해 이벤트를 수신하면
**Then** 6종류의 이벤트 타입을 모두 수신할 수 있다
- progress
- stage_change
- document_found
- metrics_update
- error (에러 발생 시)
- completed (완료 시)

```python
async def test_sse_all_event_types():
    session_id = await create_session_and_wait_for_completion()

    received_events = set()
    async with client.stream("GET", f"/api/v1/research/{session_id}/stream") as response:
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":")[1].strip()
                received_events.add(event_type)

    expected_events = {"progress", "stage_change", "document_found", "metrics_update", "completed"}
    assert expected_events.issubset(received_events)
```

### Scenario 10: Last-Event-ID 기반 이벤트 재생 (AC-010)

**Given** SSE 연결이 끊어졌다가 재연결할 때
**When** Last-Event-ID 헤더와 함께 재연결하면
**Then** 시스템은 놓친 이벤트부터 재생한다

```python
async def test_sse_replay_from_last_event():
    session_id = await create_active_session()

    # First connection - get some events
    last_event_id = None
    async with client.stream("GET", f"/api/v1/research/{session_id}/stream") as response:
        async for line in response.aiter_lines():
            if line.startswith("id:"):
                last_event_id = line.split(":")[1].strip()
                break

    # Reconnect with Last-Event-ID
    headers = {"Last-Event-ID": last_event_id}
    async with client.stream("GET", f"/api/v1/research/{session_id}/stream", headers=headers) as response:
        first_event_id = None
        async for line in response.aiter_lines():
            if line.startswith("id:"):
                first_event_id = line.split(":")[1].strip()
                break

        # Should receive events after last_event_id
        assert int(first_event_id) > int(last_event_id)
```

### Scenario 11: SSE 연결 해제 시 리소스 정리 (AC-011)

**Given** SSE 연결이 활성화되어 있을 때
**When** 클라이언트가 연결을 끊으면
**Then** 시스템은 해당 연결의 리소스를 정리한다
**And** 다른 연결에 영향을 주지 않는다

```python
async def test_sse_cleanup_on_disconnect():
    session_id = await create_active_session()

    # Start SSE connection
    async with client.stream("GET", f"/api/v1/research/{session_id}/stream") as response:
        # Read one event then disconnect
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                break

    # Connection closed - verify cleanup happened
    # (Check metrics or internal state)
    await asyncio.sleep(0.1)

    # New connection should work
    async with client.stream("GET", f"/api/v1/research/{session_id}/stream") as response:
        assert response.status_code == 200
```

---

## 3. Session Management Scenarios

### Scenario 12: 세션 TTL 만료 (AC-012)

**Given** 리서치 세션이 1시간 이상 유휴 상태일 때
**When** TTL이 만료되면
**Then** 세션이 Redis에서 자동 삭제된다

```python
async def test_session_ttl_expiry():
    # This is typically tested with mocked time or short TTL in test config
    session_id = await create_session_with_short_ttl()

    # Wait for TTL to expire
    await asyncio.sleep(TEST_SESSION_TTL + 1)

    # Session should be gone
    response = await client.get(f"/api/v1/research/{session_id}")
    assert response.status_code == 404
```

### Scenario 13: 동시 세션 수 제한 (AC-013)

**Given** 최대 동시 세션 수에 도달했을 때
**When** 새 리서치 세션을 시작하려고 하면
**Then** 시스템은 503 Service Unavailable을 반환한다

```python
async def test_max_concurrent_sessions():
    # Create max number of sessions
    session_ids = []
    for _ in range(MAX_CONCURRENT_SESSIONS):
        resp = await client.post("/api/v1/research", json={"query": f"query-{_}"})
        session_ids.append(resp.json()["sessionId"])

    # Try to create one more
    response = await client.post("/api/v1/research", json={"query": "overflow"})
    assert response.status_code == 503

    # Cleanup
    for sid in session_ids:
        await client.delete(f"/api/v1/research/{sid}")
```

---

## 4. Integration Scenarios

### Scenario 14: langgraph_service 통합 (AC-014)

**Given** 리서치 세션이 시작되었을 때
**When** langgraph_service가 문서를 처리하면
**Then** 문서 결과가 세션에 추가된다
**And** document_found 이벤트가 발행된다

### Scenario 15: taxonomy_service 통합 (AC-015)

**Given** 리서치가 완료되고 문서 임포트가 요청되었을 때
**When** taxonomy_id가 제공되면
**Then** taxonomy_service가 호출되어 택소노미가 업데이트된다

---

## 5. Error Handling Scenarios

### Scenario 16: Redis 연결 실패 (AC-016)

**Given** Redis 연결이 불가능할 때
**When** 리서치 세션을 시작하려고 하면
**Then** 시스템은 503 Service Unavailable을 반환한다
**And** 에러 로그가 기록된다

### Scenario 17: langgraph_service 타임아웃 (AC-017)

**Given** langgraph_service가 응답하지 않을 때
**When** 타임아웃이 발생하면
**Then** error 이벤트가 발행된다
**And** 세션 상태가 error로 변경된다

---

## 6. Test Checklist

### Unit Tests

- [ ] `research_schemas.py`: 모든 스키마 검증 테스트
- [ ] `research_session_manager.py`: CRUD, TTL, Pub/Sub 테스트
- [ ] `research_service.py`: 비즈니스 로직 테스트
- [ ] `research_router.py`: 엔드포인트 테스트

### Integration Tests

- [ ] Redis 연결 및 세션 관리
- [ ] langgraph_service 통합
- [ ] taxonomy_service 통합
- [ ] SSE 스트리밍 전체 플로우

### E2E Tests

- [ ] 전체 리서치 플로우 (시작 -> 스트리밍 -> 완료 -> 임포트)
- [ ] 에러 시나리오 및 복구
- [ ] 동시 세션 처리

---

## 7. Quality Gates

### 코드 품질

- [ ] 테스트 커버리지 90% 이상
- [ ] 타입 힌트 100% 적용
- [ ] Linting 에러 0개 (ruff)
- [ ] 보안 취약점 0개 (bandit)

### 성능 기준

- [ ] SSE 이벤트 지연시간 < 100ms
- [ ] API 응답 시간 < 200ms (P95)
- [ ] 메모리 누수 없음 (24시간 장기 테스트)

### 문서화

- [ ] OpenAPI 스키마 자동 생성
- [ ] 코드 주석 및 docstring
- [ ] README 업데이트

---

## 8. Definition of Done

이 SPEC의 구현이 완료되었다고 판단하기 위한 기준:

1. **기능 완료**: 모든 API 엔드포인트가 명세대로 동작
2. **테스트 통과**: 모든 acceptance 시나리오 테스트 통과
3. **품질 기준 충족**: Quality Gates의 모든 항목 충족
4. **프론트엔드 호환**: `apps/frontend/types/research.ts`와 완전 호환
5. **문서화 완료**: OpenAPI 스키마 및 코드 문서화 완료
6. **코드 리뷰**: 최소 1명의 리뷰어 승인
7. **배포 준비**: 스테이징 환경에서 동작 확인

---

**End of Acceptance Criteria**
