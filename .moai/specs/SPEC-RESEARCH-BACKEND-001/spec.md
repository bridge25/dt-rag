# SPEC-RESEARCH-BACKEND-001: Research Agent Backend API

---
id: SPEC-RESEARCH-BACKEND-001
title: Research Agent Backend API - SSE 기반 실시간 리서치 엔진
version: 1.0.0
status: draft
priority: high
created: 2025-11-24
updated: 2025-11-24
author: spec-builder
tags: [backend, api, sse, research, realtime]
---

## HISTORY

| Version | Date       | Author       | Description                          |
|---------|------------|--------------|--------------------------------------|
| 1.0.0   | 2025-11-24 | spec-builder | 초기 SPEC 생성 (backend-expert 검증 완료) |

---

## 1. Overview

Research Agent Backend API는 SSE(Server-Sent Events) 기반의 실시간 리서치 엔진입니다. 사용자가 리서치 쿼리를 제출하면 백그라운드에서 문서 검색, 분석, 수집을 수행하고 실시간으로 진행 상황을 스트리밍합니다.

### 1.1 Related Specifications

- **선행 작업**: SPEC-FRONTEND-UX-001 (Research Agent 프론트엔드 인터페이스)
- **연관 서비스**: langgraph_service, taxonomy_service

### 1.2 Architecture Overview

```
Client (SSE) <---> FastAPI Router <---> Research Service <---> Session Manager (Redis)
                                              |
                                   +----------+----------+
                                   |          |          |
                             LangGraph   Taxonomy   Background
                              Service    Service      Tasks
```

---

## 2. Environment

### 2.1 기술 스택

| Component        | Technology         | Version    | Purpose                    |
|------------------|--------------------|------------|----------------------------|
| Web Framework    | FastAPI            | >=0.115.0  | REST API 및 SSE 지원       |
| SSE Library      | sse-starlette      | >=2.0.0    | Server-Sent Events 구현    |
| Session Store    | Redis              | >=7.0      | 세션 상태 관리, Pub/Sub    |
| Task Queue       | BackgroundTasks    | (built-in) | 비동기 리서치 작업 처리    |
| Monitoring       | Prometheus Client  | >=0.20.0   | 메트릭 수집                |

### 2.2 구현 파일

```
apps/api/
  routers/
    research_router.py      # API 엔드포인트 정의
  services/
    research_service.py     # 리서치 비즈니스 로직
    research_session_manager.py  # Redis 기반 세션 관리
  schemas/
    research_schemas.py     # Pydantic 요청/응답 스키마
  monitoring/
    research_metrics.py     # Prometheus 메트릭 정의
```

### 2.3 의존성

- 기존 `langgraph_service`: 리서치 쿼리 분석 및 문서 처리
- 기존 `taxonomy_service`: 카테고리 추천 및 문서 임포트
- 프론트엔드 타입: `apps/frontend/types/research.ts`

---

## 3. Assumptions

### 3.1 시스템 가정

1. **A1**: Redis 서버가 가용하며 Pub/Sub 기능을 지원한다
2. **A2**: langgraph_service와 taxonomy_service가 정상 동작한다
3. **A3**: 클라이언트는 SSE 연결을 유지할 수 있다
4. **A4**: 동시 리서치 세션 수는 합리적인 범위 내이다 (< 100)

### 3.2 데이터 가정

1. **A5**: 프론트엔드 타입 정의(`research.ts`)와 백엔드 스키마가 호환된다
2. **A6**: 리서치 쿼리는 UTF-8 인코딩된 텍스트이다

---

## 4. Requirements

### 4.1 Ubiquitous Requirements

> 시스템이 항상 만족해야 하는 요구사항

| ID       | Requirement                                                           |
|----------|-----------------------------------------------------------------------|
| U-REQ-01 | 시스템은 SSE 기반 실시간 리서치 이벤트 스트리밍을 제공해야 한다       |
| U-REQ-02 | 시스템은 Redis 기반 세션 상태 관리를 제공해야 한다                    |
| U-REQ-03 | 모든 API 응답은 RESTful 원칙을 준수해야 한다                          |
| U-REQ-04 | 시스템은 6종류의 SSE 이벤트 타입을 지원해야 한다                      |

### 4.2 Event-Driven Requirements

> 특정 이벤트 발생 시 시스템의 동작

| ID       | Trigger                          | Response                                                          |
|----------|----------------------------------|-------------------------------------------------------------------|
| E-REQ-01 | WHEN 사용자가 리서치를 시작하면  | 시스템은 세션을 생성하고 백그라운드 작업을 시작해야 한다 (201 Created) |
| E-REQ-02 | WHEN 문서가 발견되면             | 시스템은 `document_found` 이벤트를 발행해야 한다                   |
| E-REQ-03 | WHEN 리서치가 완료되면           | 시스템은 `completed` 이벤트와 함께 suggested_categories를 제공해야 한다 |
| E-REQ-04 | WHEN 스테이지가 변경되면         | 시스템은 `stage_change` 이벤트를 발행해야 한다                     |
| E-REQ-05 | WHEN 에러가 발생하면             | 시스템은 `error` 이벤트와 복구 가능 여부를 제공해야 한다           |

### 4.3 State-Driven Requirements

> 특정 상태가 유지되는 동안의 시스템 동작

| ID       | Condition                              | Behavior                                              |
|----------|----------------------------------------|-------------------------------------------------------|
| S-REQ-01 | WHILE 리서치가 진행 중인 동안          | 시스템은 `progress` 이벤트를 주기적으로 발행해야 한다 |
| S-REQ-02 | WHILE SSE 연결이 유지되는 동안         | 시스템은 연결 상태를 모니터링해야 한다                |
| S-REQ-03 | WHILE 세션이 활성 상태인 동안          | 시스템은 Redis에 세션 데이터를 유지해야 한다          |

### 4.4 Optional Requirements

> 특정 조건에서만 활성화되는 선택적 기능

| ID       | Condition                               | Feature                                               |
|----------|-----------------------------------------|-------------------------------------------------------|
| O-REQ-01 | WHERE Last-Event-ID 헤더가 제공되면     | 시스템은 놓친 이벤트를 재생해야 한다                  |
| O-REQ-02 | WHERE taxonomy_id가 제공되면            | 시스템은 문서 임포트 시 택소노미를 업데이트해야 한다  |
| O-REQ-03 | WHERE config 옵션이 제공되면            | 시스템은 리서치 설정을 커스터마이징해야 한다          |

### 4.5 Unwanted Behaviors

> 시스템이 방지해야 하는 원치 않는 동작

| ID       | Condition                                                  | Response                                      |
|----------|------------------------------------------------------------|-----------------------------------------------|
| UW-REQ-01 | IF 세션이 존재하지 않으면                                 | 시스템은 404 Not Found 응답을 반환해야 한다   |
| UW-REQ-02 | IF confirming 단계가 아닌 상태에서 import를 시도하면      | 시스템은 409 Conflict 응답을 반환해야 한다    |
| UW-REQ-03 | IF SSE 연결이 끊어지면                                    | 시스템은 리소스를 정리해야 한다               |
| UW-REQ-04 | IF 유효하지 않은 쿼리가 제공되면                          | 시스템은 422 Unprocessable Entity를 반환해야 한다 |

---

## 5. Specifications

### 5.1 API Endpoints

#### POST /api/v1/research

리서치 세션을 시작합니다.

```http
POST /api/v1/research
Content-Type: application/json

{
  "query": "string",
  "config": {
    "maxDocuments": 50,
    "qualityThreshold": 0.7,
    "sourcesFilter": ["web", "pdf"],
    "depthLevel": "medium"
  }
}
```

**Response (201 Created)**:
```json
{
  "sessionId": "uuid",
  "estimatedDuration": 30
}
```

#### GET /api/v1/research/{id}

리서치 세션 상태를 조회합니다.

**Response (200 OK)**:
```json
{
  "session": {
    "id": "uuid",
    "query": "string",
    "stage": "collecting",
    "progress": 45,
    "metrics": {...},
    "documents": [...],
    "timeline": [...]
  }
}
```

#### GET /api/v1/research/{id}/stream

SSE 스트리밍 엔드포인트입니다.

**Headers**:
- `Accept: text/event-stream`
- `Last-Event-ID: <event_id>` (optional)

**Event Types**:

| Event Type      | Data Schema                                          |
|-----------------|------------------------------------------------------|
| progress        | `{ progress: number, currentSource?: string }`       |
| stage_change    | `{ previousStage: string, newStage: string }`        |
| document_found  | `{ document: DiscoveredDocument, totalCount: number }` |
| metrics_update  | `{ metrics: ResearchMetrics }`                       |
| error           | `{ message: string, recoverable: boolean }`          |
| completed       | `{ totalDocuments: number, suggestedCategories: string[], qualityScore: number }` |

#### POST /api/v1/research/{id}/import

선택한 문서를 시스템에 임포트합니다.

```http
POST /api/v1/research/{id}/import
Content-Type: application/json

{
  "selectedDocumentIds": ["doc1", "doc2"],
  "taxonomyId": "optional-taxonomy-uuid"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "documentsImported": 2,
  "taxonomyUpdated": true
}
```

**Error (409 Conflict)**: 세션이 confirming 단계가 아닌 경우

#### DELETE /api/v1/research/{id}

리서치 세션을 취소하고 삭제합니다.

**Response (204 No Content)**

### 5.2 SSE Event Specifications

| Event          | Frequency           | Payload Size | Priority |
|----------------|---------------------|--------------|----------|
| progress       | 1-2초 간격          | ~100 bytes   | Normal   |
| stage_change   | 스테이지 전환 시    | ~150 bytes   | High     |
| document_found | 문서 발견 시        | ~500 bytes   | Normal   |
| metrics_update | 5초 간격            | ~200 bytes   | Low      |
| error          | 에러 발생 시        | ~300 bytes   | Critical |
| completed      | 리서치 완료 시      | ~400 bytes   | High     |

### 5.3 Session State Machine

```
idle --> analyzing --> searching --> collecting --> organizing --> confirming --> completed
  |                                                                    |
  +--------------------------------------------------------------------> error
```

---

## 6. Constraints

### 6.1 성능 제약

| Metric               | Target              | Rationale                    |
|----------------------|---------------------|------------------------------|
| SSE 지연시간         | < 100ms             | 실시간 UX 보장               |
| 동시 세션 수         | 최대 100            | Redis 메모리 제한            |
| 세션 TTL             | 1시간               | 리소스 정리                  |
| 이벤트 버퍼          | 최대 1000개/세션    | 메모리 효율성                |

### 6.2 보안 제약

1. 세션 ID는 UUID v4 형식이어야 한다
2. 타 사용자의 세션에 접근할 수 없어야 한다
3. 민감한 데이터는 로그에 기록하지 않아야 한다

---

## 7. Traceability

### 7.1 TAG Block

```
@SPEC:RESEARCH-BACKEND-001
  @REQ:U-REQ-01..U-REQ-04
  @REQ:E-REQ-01..E-REQ-05
  @REQ:S-REQ-01..S-REQ-03
  @REQ:O-REQ-01..O-REQ-03
  @REQ:UW-REQ-01..UW-REQ-04

  @IMPL:research_router.py
  @IMPL:research_service.py
  @IMPL:research_session_manager.py
  @IMPL:research_schemas.py
  @IMPL:research_metrics.py

  @TEST:test_research_router.py
  @TEST:test_research_service.py
  @TEST:test_research_session_manager.py

  @REF:SPEC-FRONTEND-UX-001
```

### 7.2 Dependencies

- **Upstream**: langgraph_service, taxonomy_service, Redis
- **Downstream**: SPEC-FRONTEND-UX-001 (프론트엔드 인터페이스)

---

## 8. Appendix

### 8.1 Error Codes

| HTTP Status | Error Code          | Description                           |
|-------------|---------------------|---------------------------------------|
| 400         | INVALID_REQUEST     | 잘못된 요청 형식                      |
| 404         | SESSION_NOT_FOUND   | 세션을 찾을 수 없음                   |
| 409         | INVALID_STATE       | 잘못된 상태에서의 작업 시도           |
| 422         | VALIDATION_ERROR    | 요청 데이터 검증 실패                 |
| 500         | INTERNAL_ERROR      | 서버 내부 오류                        |
| 503         | SERVICE_UNAVAILABLE | 의존 서비스 불가                      |

### 8.2 Frontend Type Compatibility

이 SPEC의 스키마는 `apps/frontend/types/research.ts`와 1:1 호환되도록 설계되었습니다.

---

**End of Specification**
