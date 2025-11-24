# SPEC-RESEARCH-BACKEND-001 Implementation Plan

---
spec_id: SPEC-RESEARCH-BACKEND-001
created: 2025-11-24
updated: 2025-11-24
author: spec-builder
---

## Overview

Research Agent Backend API의 구현 계획입니다. SSE 기반 실시간 리서치 엔진을 4개 Phase로 나누어 구현합니다.

---

## Phase 1: Foundation - 스키마 및 세션 관리

**우선순위**: Critical
**의존성**: 없음

### 목표

- Pydantic 스키마 정의
- Redis 기반 세션 매니저 구현
- 기본 테스트 인프라 구축

### 작업 항목

| Task ID | Task Description                          | File                              | Dependencies |
|---------|-------------------------------------------|-----------------------------------|--------------|
| P1-T01  | Pydantic 요청/응답 스키마 정의            | `schemas/research_schemas.py`     | -            |
| P1-T02  | 프론트엔드 타입과 스키마 호환성 검증      | -                                 | P1-T01       |
| P1-T03  | Redis 세션 매니저 인터페이스 설계         | `services/research_session_manager.py` | -        |
| P1-T04  | 세션 CRUD 작업 구현                       | `services/research_session_manager.py` | P1-T03   |
| P1-T05  | 세션 TTL 및 자동 정리 로직 구현           | `services/research_session_manager.py` | P1-T04   |
| P1-T06  | 세션 매니저 단위 테스트 작성              | `tests/test_research_session_manager.py` | P1-T04 |

### 산출물

- `apps/api/schemas/research_schemas.py`
- `apps/api/services/research_session_manager.py`
- `tests/api/test_research_session_manager.py`

### 완료 기준

- [ ] 모든 스키마가 프론트엔드 타입과 호환
- [ ] 세션 CRUD 작업 테스트 통과
- [ ] 세션 TTL 자동 만료 테스트 통과

---

## Phase 2: Core - 리서치 서비스 및 라우터

**우선순위**: Critical
**의존성**: Phase 1

### 목표

- 핵심 리서치 서비스 로직 구현
- REST API 엔드포인트 구현
- langgraph_service 통합

### 작업 항목

| Task ID | Task Description                          | File                              | Dependencies |
|---------|-------------------------------------------|-----------------------------------|--------------|
| P2-T01  | 리서치 서비스 인터페이스 설계             | `services/research_service.py`    | P1-T04       |
| P2-T02  | 리서치 시작 로직 구현                     | `services/research_service.py`    | P2-T01       |
| P2-T03  | langgraph_service 통합                    | `services/research_service.py`    | P2-T02       |
| P2-T04  | taxonomy_service 통합                     | `services/research_service.py`    | P2-T02       |
| P2-T05  | 문서 임포트 로직 구현                     | `services/research_service.py`    | P2-T04       |
| P2-T06  | API 라우터 기본 구조 설정                 | `routers/research_router.py`      | P2-T01       |
| P2-T07  | POST /research 엔드포인트 구현            | `routers/research_router.py`      | P2-T02       |
| P2-T08  | GET /research/{id} 엔드포인트 구현        | `routers/research_router.py`      | P2-T06       |
| P2-T09  | POST /research/{id}/import 엔드포인트 구현 | `routers/research_router.py`     | P2-T05       |
| P2-T10  | DELETE /research/{id} 엔드포인트 구현     | `routers/research_router.py`      | P2-T06       |
| P2-T11  | 라우터 단위 테스트 작성                   | `tests/test_research_router.py`   | P2-T07..P2-T10 |

### 산출물

- `apps/api/services/research_service.py`
- `apps/api/routers/research_router.py`
- `tests/api/test_research_router.py`
- `tests/api/test_research_service.py`

### 완료 기준

- [ ] 모든 REST 엔드포인트 구현 완료
- [ ] 상태 코드 (201, 404, 409, 422) 정확히 반환
- [ ] langgraph_service 통합 테스트 통과

---

## Phase 3: Streaming - SSE 이벤트 스트리밍

**우선순위**: High
**의존성**: Phase 2

### 목표

- SSE 스트리밍 엔드포인트 구현
- 6종류 이벤트 타입 구현
- Last-Event-ID 기반 이벤트 재생

### 작업 항목

| Task ID | Task Description                          | File                              | Dependencies |
|---------|-------------------------------------------|-----------------------------------|--------------|
| P3-T01  | SSE 이벤트 생성기 구현                    | `services/research_service.py`    | P2-T02       |
| P3-T02  | Redis Pub/Sub 이벤트 발행 구현            | `services/research_session_manager.py` | P1-T04   |
| P3-T03  | Redis Pub/Sub 이벤트 구독 구현            | `services/research_session_manager.py` | P3-T02   |
| P3-T04  | GET /research/{id}/stream 엔드포인트 구현 | `routers/research_router.py`      | P3-T03       |
| P3-T05  | progress 이벤트 발행 로직                 | `services/research_service.py`    | P3-T01       |
| P3-T06  | stage_change 이벤트 발행 로직             | `services/research_service.py`    | P3-T01       |
| P3-T07  | document_found 이벤트 발행 로직           | `services/research_service.py`    | P3-T01       |
| P3-T08  | metrics_update 이벤트 발행 로직           | `services/research_service.py`    | P3-T01       |
| P3-T09  | error 이벤트 발행 로직                    | `services/research_service.py`    | P3-T01       |
| P3-T10  | completed 이벤트 발행 로직                | `services/research_service.py`    | P3-T01       |
| P3-T11  | Last-Event-ID 기반 이벤트 재생 구현       | `routers/research_router.py`      | P3-T04       |
| P3-T12  | SSE 연결 해제 시 리소스 정리 구현         | `routers/research_router.py`      | P3-T04       |
| P3-T13  | SSE 스트리밍 통합 테스트 작성             | `tests/test_research_sse.py`      | P3-T04..P3-T12 |

### 산출물

- SSE 스트리밍이 추가된 라우터 및 서비스
- `tests/api/test_research_sse.py`

### 완료 기준

- [ ] 6종류 SSE 이벤트 모두 정상 발행
- [ ] Last-Event-ID 재생 기능 동작
- [ ] 연결 해제 시 리소스 정리 확인

---

## Phase 4: Monitoring & Polish

**우선순위**: Medium
**의존성**: Phase 3

### 목표

- Prometheus 메트릭 구현
- 에러 처리 강화
- 성능 최적화 및 문서화

### 작업 항목

| Task ID | Task Description                          | File                              | Dependencies |
|---------|-------------------------------------------|-----------------------------------|--------------|
| P4-T01  | Prometheus 메트릭 정의                    | `monitoring/research_metrics.py`  | -            |
| P4-T02  | 세션 수 메트릭 구현                       | `monitoring/research_metrics.py`  | P4-T01       |
| P4-T03  | 리서치 시간 히스토그램 구현               | `monitoring/research_metrics.py`  | P4-T01       |
| P4-T04  | SSE 연결 수 게이지 구현                   | `monitoring/research_metrics.py`  | P4-T01       |
| P4-T05  | 에러 발생 카운터 구현                     | `monitoring/research_metrics.py`  | P4-T01       |
| P4-T06  | 라우터에 메트릭 통합                      | `routers/research_router.py`      | P4-T02..P4-T05 |
| P4-T07  | 에러 핸들러 개선                          | `routers/research_router.py`      | P2-T06       |
| P4-T08  | 상세 로깅 추가                            | 전체 파일                         | -            |
| P4-T09  | API 문서화 (OpenAPI)                      | `routers/research_router.py`      | P2-T06       |
| P4-T10  | 엔드투엔드 통합 테스트                    | `tests/test_research_e2e.py`      | All          |

### 산출물

- `apps/api/monitoring/research_metrics.py`
- 업데이트된 라우터 (메트릭, 에러 처리, 문서화)
- `tests/api/test_research_e2e.py`

### 완료 기준

- [ ] Prometheus /metrics 엔드포인트에서 메트릭 노출
- [ ] 모든 에러 케이스에 적절한 응답 반환
- [ ] OpenAPI 문서 자동 생성 확인
- [ ] E2E 테스트 통과

---

## Technical Approach

### 아키텍처 결정

1. **SSE vs WebSocket**: SSE 선택 (단방향 스트리밍에 적합, 브라우저 호환성 우수)
2. **Redis Pub/Sub**: 다중 인스턴스 환경에서 이벤트 브로드캐스팅 지원
3. **BackgroundTasks**: 리서치 작업을 비동기로 처리하여 API 응답 지연 방지

### 핵심 패턴

```python
# SSE 이벤트 생성 패턴
async def event_generator(session_id: str):
    async for event in session_manager.subscribe(session_id):
        yield {
            "event": event.type,
            "id": event.id,
            "data": event.data.json()
        }
```

### 테스트 전략

| 테스트 유형   | 커버리지 목표 | 도구                    |
|---------------|---------------|-------------------------|
| 단위 테스트   | 90%           | pytest, pytest-asyncio  |
| 통합 테스트   | 80%           | pytest, httpx, TestClient |
| E2E 테스트    | 주요 시나리오 | pytest, httpx-sse       |

---

## Risk Mitigation

### 식별된 위험

| Risk                          | Probability | Impact | Mitigation                                   |
|-------------------------------|-------------|--------|----------------------------------------------|
| Redis 연결 불안정             | Medium      | High   | 연결 풀링, 재연결 로직, 폴백 전략            |
| SSE 연결 메모리 누수          | Low         | High   | 연결 타임아웃, 주기적 정리, 모니터링          |
| langgraph_service 응답 지연   | Medium      | Medium | 타임아웃 설정, 비동기 처리, 진행률 표시      |
| 동시 세션 과부하              | Low         | Medium | 세션 수 제한, 큐잉, 우아한 거부              |

---

## Dependencies Summary

```
Phase 1 (Foundation)
    |
    v
Phase 2 (Core) <-- langgraph_service, taxonomy_service
    |
    v
Phase 3 (Streaming)
    |
    v
Phase 4 (Monitoring & Polish)
```

---

**End of Implementation Plan**
