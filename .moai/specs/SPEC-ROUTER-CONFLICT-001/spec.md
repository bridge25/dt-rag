---
id: ROUTER-CONFLICT-001
version: 0.1.0
status: completed
created: 2025-11-10
updated: 2025-11-10
author: @bridge25
priority: high
category: bugfix
labels: [api, router, fastapi, conflict]
scope: backend
---

# SPEC-ROUTER-CONFLICT-001: API 라우터 엔드포인트 충돌 해결

## HISTORY

### v0.1.0 - 2025-11-10 - COMPLETED
- **작성자**: @bridge25
- **변경 사항**:
  - agent_factory_router 접두사 변경 (`/agents` → `/factory/agents`)
  - 테스트 통과 확인 완료
  - 문서 동기화 완료
- **상태**: completed → 프로덕션 준비 완료
- **Breaking Change**: Yes - agent_factory_router API 경로 변경 (`/api/v1/agents/{agent_id}` → `/api/v1/factory/agents/{agent_id}`)

### v0.0.1 - 2025-11-10 - INITIAL
- **작성자**: @bridge25
- **변경 사항**: 초기 SPEC 문서 작성
- **상태**: draft → 구현 대기 중

---

## @TAG BLOCK

```
@SPEC:ROUTER-CONFLICT-001
├─ @REQUIREMENT:ROUTER-CONFLICT-001-R01 (고유 엔드포인트 경로)
├─ @REQUIREMENT:ROUTER-CONFLICT-001-R02 (agent_factory_router 접두사 변경)
├─ @REQUIREMENT:ROUTER-CONFLICT-001-R03 (agent_router 경로 유지)
└─ @REQUIREMENT:ROUTER-CONFLICT-001-R04 (테스트 통과 보장)
```

---

## Environment (환경)

**WHEN** FastAPI 애플리케이션에서 두 개의 라우터가 동일한 엔드포인트 경로를 사용할 때:

- **현재 상황**:
  - `agent_factory_router`와 `agent_router` 모두 `GET /api/v1/agents/{agent_id}` 경로 사용
  - `main.py:526`에서 `agent_factory_router` 먼저 등록
  - `main.py:528`에서 `agent_router` 두 번째 등록 (접근 불가 상태)

- **발생 문제**:
  - `agent_router`의 엔드포인트가 라우팅 테이블에서 가려짐 (shadowed)
  - 테스트 실패: `tests/unit/test_agent_router.py::test_get_agent_success`
  - API 문서에서 혼란 발생 가능성

- **영향 범위**:
  - Backend API 계층 (FastAPI 라우터)
  - 단위 테스트 (`test_agent_router.py`)
  - API 문서 (Swagger/OpenAPI 스펙)

---

## Assumptions (가정)

**WHILE** 다음 조건들이 참일 때:

1. **라우터 목적 분리**:
   - `agent_factory_router`: `AgentFactoryService`를 통한 에이전트 생성/관리
   - `agent_router`: `AgentDAO`를 통한 에이전트 CRUD 작업
   - 두 라우터는 서로 다른 비즈니스 로직을 수행

2. **하위 호환성 요구사항**:
   - 기존 클라이언트가 `/api/v1/agents/{agent_id}`를 사용 중일 수 있음
   - `agent_router`는 기존 경로를 유지해야 함

3. **라우팅 우선순위**:
   - FastAPI는 먼저 등록된 라우터의 경로를 우선 매칭
   - 경로가 완전히 동일하면 두 번째 라우터는 접근 불가

4. **테스트 중요성**:
   - `test_agent_router.py`는 `agent_router`의 동작 검증
   - 모든 단위 테스트는 통과해야 함

---

## Requirements (요구사항)

### @REQUIREMENT:ROUTER-CONFLICT-001-R01
**고유 엔드포인트 경로 보장**

**THEN** 시스템은 두 라우터가 서로 다른 고유한 API 경로를 가져야 합니다:
- **목적**: 라우팅 충돌 제거, 모든 엔드포인트 접근 가능
- **조건**: 각 라우터의 접두사가 명확히 구분되어야 함
- **검증**: 두 엔드포인트 모두 독립적으로 호출 가능

### @REQUIREMENT:ROUTER-CONFLICT-001-R02
**agent_factory_router 접두사 변경**

**THEN** 시스템은 `agent_factory_router`의 접두사를 `/factory/agents`로 변경해야 합니다:
- **대상 파일**: `apps/api/routers/agent_factory_router.py:43`
- **변경 전**: `prefix="/agents"`
- **변경 후**: `prefix="/factory/agents"`
- **최종 경로**: `GET /api/v1/factory/agents/{agent_id}`

### @REQUIREMENT:ROUTER-CONFLICT-001-R03
**agent_router 경로 유지**

**THEN** 시스템은 `agent_router`의 기존 경로를 유지해야 합니다:
- **경로**: `GET /api/v1/agents/{agent_id}` (변경 없음)
- **이유**: 하위 호환성, 기존 클라이언트 보호
- **대상**: `AgentDAO` 기반 CRUD 작업

### @REQUIREMENT:ROUTER-CONFLICT-001-R04
**테스트 통과 보장**

**THEN** 시스템은 모든 관련 단위 테스트가 통과해야 합니다:
- **대상 테스트**: `tests/unit/test_agent_router.py::test_get_agent_success`
- **검증 방법**: `pytest tests/unit/test_agent_router.py -v`
- **통과 기준**: 모든 assertion 성공, 라우팅 정상 동작

---

## Specifications (상세 명세)

### 1. 라우터 접두사 변경

**파일**: `apps/api/routers/agent_factory_router.py`

**변경 대상 (Line 43)**:
```python
# 변경 전
router = APIRouter(
    prefix="/agents",
    tags=["agent-factory"]
)

# 변경 후
router = APIRouter(
    prefix="/factory/agents",
    tags=["agent-factory"]
)
```

**영향**:
- 기존: `GET /api/v1/agents/{agent_id}` (agent_factory)
- 변경: `GET /api/v1/factory/agents/{agent_id}` (agent_factory)

### 2. 라우터 등록 검증

**파일**: `apps/api/main.py`

**검증 사항 (Line 526-528)**:
```python
# 등록 순서 확인
app.include_router(agent_factory_router, prefix="/api/v1")  # Line 526
app.include_router(agent_router, prefix="/api/v1")          # Line 528
```

**예상 결과**:
- `/api/v1/factory/agents/{agent_id}` → `agent_factory_router`
- `/api/v1/agents/{agent_id}` → `agent_router`

### 3. 테스트 검증

**대상 테스트**: `tests/unit/test_agent_router.py::test_get_agent_success`

**검증 시나리오**:
```python
# test_get_agent_success가 agent_router를 정확히 테스트하는지 확인
# - 호출 경로: GET /api/v1/agents/{agent_id}
# - 라우터: agent_router (AgentDAO 사용)
# - 응답: 정상적인 에이전트 정보 반환
```

**실행 명령**:
```bash
pytest tests/unit/test_agent_router.py::test_get_agent_success -v
```

### 4. API 문서 확인

**Swagger UI 경로**: `http://localhost:8000/docs`

**검증 항목**:
- [ ] `GET /api/v1/factory/agents/{agent_id}` 엔드포인트 존재 (tag: agent-factory)
- [ ] `GET /api/v1/agents/{agent_id}` 엔드포인트 존재 (tag: agents)
- [ ] 두 엔드포인트의 설명/파라미터가 명확히 구분됨
- [ ] OpenAPI 스펙에 중복 경로 없음

---

## Traceability (추적성)

### 코드 연결
- **@CODE:agent_factory_router.py:43** → `@REQUIREMENT:ROUTER-CONFLICT-001-R02` (접두사 변경)
- **@CODE:main.py:526-528** → `@REQUIREMENT:ROUTER-CONFLICT-001-R01` (라우터 등록 검증)

### 테스트 연결
- **@TEST:test_agent_router.py::test_get_agent_success** → `@REQUIREMENT:ROUTER-CONFLICT-001-R04` (테스트 통과)

### 문서 연결
- **@DOC:api-endpoints.md** → `@SPEC:ROUTER-CONFLICT-001` (API 문서 업데이트)

### 이슈 연결
- **@ISSUE:router-conflict** → `@SPEC:ROUTER-CONFLICT-001` (버그 리포트)

---

## Constraints (제약사항)

1. **하위 호환성**:
   - `agent_router`의 경로는 절대 변경하지 않음
   - 기존 클라이언트가 `/api/v1/agents/{agent_id}` 사용 가능해야 함

2. **최소 변경 원칙**:
   - `agent_factory_router` 접두사만 변경
   - 라우터 핸들러 로직은 수정하지 않음

3. **테스트 우선**:
   - 코드 변경 전 실패 테스트 확인 (RED)
   - 변경 후 테스트 통과 확인 (GREEN)

4. **문서 동기화**:
   - API 문서 자동 생성 (Swagger UI)
   - 필요 시 추가 README 업데이트

---

## Risks (위험 요소)

| 위험 | 영향도 | 완화 전략 |
|------|--------|-----------|
| agent_factory 클라이언트 경로 변경 필요 | Medium | 변경 전 사용 현황 조사, 마이그레이션 가이드 제공 |
| 통합 테스트 미반영 | Low | 단위 테스트 외 통합 테스트도 실행 |
| API 문서 혼란 | Low | Swagger tag 명확히 구분, 설명 추가 |

---

## Next Steps (다음 단계)

1. ✅ SPEC 문서 작성 완료
2. ⏭️ `/alfred:2-run SPEC-ROUTER-CONFLICT-001` 실행 (TDD 구현)
3. ⏭️ 테스트 통과 확인 및 리팩토링
4. ⏭️ `/alfred:3-sync` 실행 (문서 동기화)
5. ⏭️ PR 생성 및 리뷰 요청
