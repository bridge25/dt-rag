# Implementation Plan: SPEC-ROUTER-CONFLICT-001

## 📋 구현 계획 개요

**SPEC ID**: ROUTER-CONFLICT-001
**목표**: FastAPI 라우터 엔드포인트 충돌 해결
**접근 방식**: agent_factory_router 접두사 변경
**우선순위**: High (프로덕션 버그, 테스트 실패)

---

## 🎯 구현 목표

### 주요 목표
1. **라우팅 충돌 제거**: 두 라우터가 서로 다른 고유 경로 사용
2. **테스트 통과**: `test_agent_router.py::test_get_agent_success` 성공
3. **하위 호환성 유지**: `agent_router` 경로는 변경 없음
4. **API 문서 정확성**: Swagger UI에 두 엔드포인트 명확히 구분

### 성공 기준
- ✅ `agent_factory_router`: `GET /api/v1/factory/agents/{agent_id}`
- ✅ `agent_router`: `GET /api/v1/agents/{agent_id}` (기존 유지)
- ✅ 모든 단위 테스트 통과
- ✅ API 문서에서 두 엔드포인트 독립적으로 표시

---

## 📐 기술 접근 방법

### 1단계: 라우터 접두사 변경 (PRIMARY GOAL)

**대상 파일**: `apps/api/routers/agent_factory_router.py`

**변경 내용**:
```python
# Line 43 수정
router = APIRouter(
    prefix="/factory/agents",  # 변경: "/agents" → "/factory/agents"
    tags=["agent-factory"]
)
```

**변경 이유**:
- `agent_factory_router`는 `AgentFactoryService` 기반 에이전트 생성/관리
- `/factory` 접두사로 명확한 의미 구분 (factory pattern)
- `agent_router`는 일반 CRUD 작업으로 `/agents` 유지

**영향 범위**:
- 모든 `agent_factory_router` 엔드포인트 경로 변경
- 예: `GET /agents/{id}` → `GET /factory/agents/{id}`

---

### 2단계: 테스트 검증 및 업데이트 (SECONDARY GOAL)

**대상 테스트**: `tests/unit/test_agent_router.py`

**검증 시나리오**:
```python
# test_get_agent_success 분석
# - 호출 경로: GET /api/v1/agents/{agent_id}
# - 기대 라우터: agent_router (AgentDAO)
# - 기대 응답: 정상 에이전트 정보 반환
```

**실행 명령**:
```bash
# 1. 변경 전 테스트 실패 확인 (RED)
pytest tests/unit/test_agent_router.py::test_get_agent_success -v

# 2. 변경 후 테스트 통과 확인 (GREEN)
pytest tests/unit/test_agent_router.py::test_get_agent_success -v
```

**추가 테스트 필요 여부**:
- `agent_factory_router` 테스트가 있다면 경로 업데이트 필요
- 예: `test_agent_factory_router.py`에서 `/factory/agents/{id}` 사용

---

### 3단계: 통합 테스트 실행 (FINAL GOAL)

**전체 테스트 스위트 실행**:
```bash
# 라우터 관련 모든 테스트 실행
pytest tests/unit/test_agent_router.py -v
pytest tests/unit/test_agent_factory_router.py -v  # 존재 시

# 전체 단위 테스트 실행
pytest tests/unit/ -v

# API 통합 테스트 (존재 시)
pytest tests/integration/ -v
```

**회귀 테스트 체크리스트**:
- [ ] `agent_router` 모든 테스트 통과
- [ ] `agent_factory_router` 모든 테스트 통과 (경로 업데이트 후)
- [ ] 기타 라우터 테스트 영향 없음

---

### 4단계: API 문서 검증 (DOCUMENTATION)

**Swagger UI 확인**:
```bash
# FastAPI 앱 실행
uvicorn apps.api.main:app --reload

# 브라우저에서 확인
# http://localhost:8000/docs
```

**검증 항목**:
1. **agent-factory 태그**:
   - `GET /api/v1/factory/agents/{agent_id}` 엔드포인트 존재
   - 설명: "AgentFactoryService를 통한 에이전트 조회"

2. **agents 태그**:
   - `GET /api/v1/agents/{agent_id}` 엔드포인트 존재
   - 설명: "AgentDAO를 통한 에이전트 조회"

3. **OpenAPI 스펙**:
   - 중복 경로 없음
   - 각 엔드포인트의 operationId 고유

**문서 업데이트 필요 사항**:
- `README.md` 또는 `API_GUIDE.md`에 경로 변경 공지
- 클라이언트 마이그레이션 가이드 (필요 시)

---

## 🏗️ 아키텍처 설계 방향

### 현재 상태 (Before)

```
FastAPI App
├─ /api/v1
│  ├─ /agents/{id} ← agent_factory_router (먼저 등록)
│  └─ /agents/{id} ← agent_router (가려짐, 접근 불가)
```

### 목표 상태 (After)

```
FastAPI App
├─ /api/v1
│  ├─ /factory/agents/{id} ← agent_factory_router
│  └─ /agents/{id}         ← agent_router
```

### 라우터 역할 구분

| 라우터 | 접두사 | 서비스 계층 | 목적 |
|--------|--------|-------------|------|
| `agent_factory_router` | `/factory/agents` | AgentFactoryService | 에이전트 생성/관리 (factory pattern) |
| `agent_router` | `/agents` | AgentDAO | 에이전트 CRUD 작업 |

### 설계 원칙
1. **명확한 책임 분리**: 각 라우터가 서로 다른 비즈니스 로직 담당
2. **의미 있는 경로**: `/factory` 접두사로 factory pattern 명시
3. **하위 호환성**: 기존 `/agents` 경로 유지
4. **확장 가능성**: 향후 `/admin/agents`, `/public/agents` 등 추가 가능

---

## ⚠️ 위험 분석 및 대응 방안

### 위험 1: agent_factory 클라이언트 경로 변경 필요

**영향도**: Medium
**가능성**: High

**완화 전략**:
1. **사전 조사**: `agent_factory_router` 사용 현황 파악
   ```bash
   # 코드베이스에서 /agents 경로 호출 검색
   grep -r "GET /api/v1/agents" --include="*.py" --include="*.ts"
   ```

2. **마이그레이션 가이드**: 변경 사항 문서화
   ```markdown
   # API Migration Guide

   ## Breaking Change: agent_factory_router 경로 변경

   **변경 전**: `GET /api/v1/agents/{agent_id}` (AgentFactoryService)
   **변경 후**: `GET /api/v1/factory/agents/{agent_id}`

   **클라이언트 업데이트 필요**:
   - 모든 agent factory 호출 경로 업데이트
   - 일반 agent CRUD는 기존 경로 유지
   ```

3. **단계적 배포** (선택 사항):
   - 임시로 두 경로 모두 유지 (deprecated 마킹)
   - 마이그레이션 기간 후 구 경로 제거

### 위험 2: 통합 테스트 미반영

**영향도**: Low
**가능성**: Medium

**완화 전략**:
- 단위 테스트 외에 통합 테스트 실행
- API 전체 엔드포인트 smoke test
- Postman/curl로 수동 검증

### 위험 3: API 문서 혼란

**영향도**: Low
**가능성**: Low

**완화 전략**:
- Swagger tag 명확히 구분 (`agent-factory` vs `agents`)
- 각 엔드포인트에 명확한 description 추가
- OpenAPI 스펙 자동 생성 검증

---

## 🔄 롤백 계획

만약 변경 후 예상치 못한 문제 발생 시:

### 롤백 단계
1. **코드 되돌리기**:
   ```bash
   git revert <commit-hash>
   ```

2. **접두사 원복**:
   ```python
   # agent_factory_router.py
   router = APIRouter(
       prefix="/agents",  # 원래대로 복구
       tags=["agent-factory"]
   )
   ```

3. **테스트 재검증**:
   ```bash
   pytest tests/unit/ -v
   ```

### 롤백 조건
- 테스트 통과율 저하
- 프로덕션 API 오류율 증가
- 클라이언트 호환성 문제 발견

---

## 📝 체크리스트

### 구현 전 (Pre-implementation)
- [ ] 기존 테스트 실패 확인 (RED)
- [ ] `agent_factory_router` 사용 현황 조사
- [ ] 변경 영향 범위 파악

### 구현 중 (Implementation)
- [ ] `agent_factory_router.py:43` 접두사 변경
- [ ] 변경 후 테스트 통과 확인 (GREEN)
- [ ] 전체 테스트 스위트 실행

### 구현 후 (Post-implementation)
- [ ] Swagger UI에서 두 엔드포인트 확인
- [ ] API 문서 업데이트 (필요 시)
- [ ] 마이그레이션 가이드 작성 (필요 시)
- [ ] Git 커밋 및 PR 생성

---

## 🚀 다음 단계

1. **즉시 실행**: `/alfred:2-run SPEC-ROUTER-CONFLICT-001`
2. **구현 완료 후**: `/alfred:3-sync` (문서 동기화)
3. **PR 생성**: git-manager를 통한 Draft PR 생성
4. **리뷰 요청**: 팀원에게 변경 사항 검토 요청

---

## 📚 참고 자료

- FastAPI 라우터 우선순위: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- APIRouter 문서: https://fastapi.tiangolo.com/reference/apirouter/
- OpenAPI 스펙: https://swagger.io/specification/
