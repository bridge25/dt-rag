---
id: AGENT-ROUTER-BUGFIX-001
version: 0.0.1
status: draft
created: 2025-11-10
updated: 2025-11-10
---

# @AC:AGENT-ROUTER-BUGFIX-001 - 인수 기준

## 개요

이 문서는 SPEC-AGENT-ROUTER-BUGFIX-001의 구현 완료를 판단하기 위한 명확하고 측정 가능한 인수 기준을 정의합니다.

---

## 전체 인수 조건

**Definition of Done (DoD)**:
- ✅ 5개 버그 관련 테스트가 모두 통과한다
- ✅ 전체 API 테스트 스위트가 통과한다 (회귀 방지)
- ✅ 코드 커버리지가 85% 이상이다
- ✅ 타입 체크 (`mypy --strict`)가 에러 없이 통과한다
- ✅ 코드 품질 검사 (`ruff check`)가 경고 없이 통과한다
- ✅ OpenAPI 문서가 자동 업데이트된다
- ✅ CI/CD 파이프라인이 성공한다

---

## AC-1: Coverage Data 딕셔너리 반환

### Given (사전 조건)

**시스템 상태**:
- MongoDB에 `coverage` 컬렉션이 존재한다
- 특정 `agent_id`에 대한 커버리지 데이터가 존재한다
- Coverage 문서 구조:
  ```json
  {
    "_id": "coverage-001",
    "agent_id": "agent-001",
    "source_id": "source-123",
    "is_covered": true,
    "created_at": "2025-11-10T10:00:00Z"
  }
  ```

**테스트 설정**:
- `CoverageDAO`가 정상적으로 초기화되어 있다
- 테스트 에이전트 ID: `agent-001`
- 예상 커버리지:
  - Total sources: 42
  - Covered sources: 38
  - Coverage percentage: 90.5%

### When (실행 조건)

**API 요청**:
```http
GET /api/v1/agents/agent-001/coverage
Authorization: Bearer {valid_token}
```

**내부 호출**:
```python
coverage_data = await coverage_dao.get_coverage_by_agent_id("agent-001")
```

### Then (예상 결과)

**응답 구조 검증**:
- ✅ HTTP 상태 코드: `200 OK`
- ✅ 응답 타입: `application/json`
- ✅ 응답 Body:
  ```json
  {
    "agent_id": "agent-001",
    "coverage_data": {
      "total_sources": 42,
      "covered_sources": 38,
      "coverage_percentage": 90.5
    }
  }
  ```

**타입 검증**:
- ✅ `coverage_data`가 `dict` 타입이다 (NOT `int`)
- ✅ `total_sources`가 `int` 타입이다
- ✅ `covered_sources`가 `int` 타입이다
- ✅ `coverage_percentage`가 `float` 타입이다

**값 검증**:
- ✅ `total_sources >= 0`
- ✅ `covered_sources >= 0`
- ✅ `covered_sources <= total_sources`
- ✅ `0.0 <= coverage_percentage <= 100.0`
- ✅ `coverage_percentage = round((covered/total) * 100, 2)`

**엣지 케이스**:
- ✅ 커버리지 데이터가 없는 경우:
  ```json
  {
    "coverage_data": {
      "total_sources": 0,
      "covered_sources": 0,
      "coverage_percentage": 0.0
    }
  }
  ```

**테스트 메서드**:
```python
# tests/api/routers/test_agent_router.py
@pytest.mark.asyncio
async def test_get_agent_coverage_success():
    response = client.get("/api/v1/agents/agent-001/coverage")

    assert response.status_code == 200
    data = response.json()

    assert "coverage_data" in data
    assert isinstance(data["coverage_data"], dict)
    assert "total_sources" in data["coverage_data"]
    assert "covered_sources" in data["coverage_data"]
    assert "coverage_percentage" in data["coverage_data"]

    coverage = data["coverage_data"]
    assert coverage["total_sources"] >= 0
    assert coverage["covered_sources"] >= 0
    assert coverage["covered_sources"] <= coverage["total_sources"]
    assert 0.0 <= coverage["coverage_percentage"] <= 100.0
```

**관련 TAG**: `@TEST:AGENT-ROUTER-BUGFIX-001-T01`

---

## AC-2: Rarity 필드 업데이트 성공

### Given (사전 조건)

**시스템 상태**:
- MongoDB에 `agents` 컬렉션이 존재한다
- 업데이트 대상 에이전트가 존재한다:
  ```json
  {
    "_id": "agent-001",
    "name": "Test Agent",
    "description": "Test description",
    "status": "active",
    "rarity": "common"
  }
  ```

**테스트 설정**:
- `AgentDAO`가 정상적으로 초기화되어 있다
- 유효한 인증 토큰이 존재한다

### When (실행 조건)

**API 요청 (rarity 업데이트 포함)**:
```http
PUT /api/v1/agents/agent-001
Content-Type: application/json
Authorization: Bearer {valid_token}

{
  "name": "Updated Agent Name",
  "rarity": "rare"
}
```

**API 요청 (빈 업데이트)**:
```http
PUT /api/v1/agents/agent-001
Content-Type: application/json
Authorization: Bearer {valid_token}

{}
```

### Then (예상 결과)

**시나리오 1: Rarity 포함 업데이트 성공**
- ✅ HTTP 상태 코드: `200 OK`
- ✅ 응답 Body에 업데이트된 에이전트 정보 포함:
  ```json
  {
    "id": "agent-001",
    "name": "Updated Agent Name",
    "rarity": "rare",
    "status": "active",
    "updated_at": "2025-11-10T10:05:00Z"
  }
  ```

**시나리오 2: 빈 업데이트 요청 거부**
- ✅ HTTP 상태 코드: `422 Unprocessable Entity`
- ✅ 에러 메시지:
  ```json
  {
    "detail": "At least one field must be provided for update"
  }
  ```

**시나리오 3: 잘못된 Rarity 값 거부**
- ✅ 요청:
  ```json
  {"rarity": "invalid_rarity"}
  ```
- ✅ HTTP 상태 코드: `422 Unprocessable Entity`
- ✅ Pydantic 검증 에러:
  ```json
  {
    "detail": [
      {
        "type": "literal_error",
        "loc": ["body", "rarity"],
        "msg": "Input should be 'common', 'uncommon', 'rare', 'epic' or 'legendary'"
      }
    ]
  }
  ```

**허용 Rarity 값**:
- ✅ `"common"`
- ✅ `"uncommon"`
- ✅ `"rare"`
- ✅ `"epic"`
- ✅ `"legendary"`

**테스트 메서드**:
```python
# tests/api/routers/test_agent_router.py
@pytest.mark.asyncio
async def test_update_agent_success():
    update_data = {
        "name": "Updated Agent",
        "rarity": "rare"
    }
    response = client.put("/api/v1/agents/agent-001", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Agent"
    assert data["rarity"] == "rare"

@pytest.mark.asyncio
async def test_update_agent_empty_update():
    response = client.put("/api/v1/agents/agent-001", json={})

    assert response.status_code == 422
    assert "At least one field" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_agent_invalid_rarity():
    response = client.put(
        "/api/v1/agents/agent-001",
        json={"rarity": "super_rare"}
    )

    assert response.status_code == 422
    assert "literal_error" in str(response.json())
```

**관련 TAG**: `@TEST:AGENT-ROUTER-BUGFIX-001-T02`, `@TEST:AGENT-ROUTER-BUGFIX-001-T03`

---

## AC-3: Agent 검색 기능 정상 동작

### Given (사전 조건)

**시스템 상태**:
- MongoDB에 `agents` 컬렉션이 존재한다
- 테스트 데이터:
  ```json
  [
    {
      "_id": "agent-001",
      "name": "Router Agent",
      "description": "Handles routing logic"
    },
    {
      "_id": "agent-002",
      "name": "Database Agent",
      "description": "Manages database operations"
    },
    {
      "_id": "agent-003",
      "name": "Auth Agent",
      "description": "Authentication and authorization"
    }
  ]
  ```

**테스트 설정**:
- `AgentDAO`에 `search_agents()` 메서드가 구현되어 있다
- 유효한 인증 토큰이 존재한다

### When (실행 조건)

**시나리오 1: 검색어 포함 요청**
```http
GET /api/v1/agents/search?q=router
Authorization: Bearer {valid_token}
```

**시나리오 2: 검색어 없는 요청 (전체 조회)**
```http
GET /api/v1/agents/search
Authorization: Bearer {valid_token}
```

**시나리오 3: Limit 파라미터 포함**
```http
GET /api/v1/agents/search?q=agent&limit=2
Authorization: Bearer {valid_token}
```

### Then (예상 결과)

**시나리오 1: 검색어 포함 - 관련 에이전트만 반환**
- ✅ HTTP 상태 코드: `200 OK`
- ✅ 응답 타입: `List[AgentResponse]`
- ✅ 반환 에이전트:
  ```json
  [
    {
      "id": "agent-001",
      "name": "Router Agent",
      "description": "Handles routing logic"
    }
  ]
  ```
- ✅ 검색 조건:
  - `"router"` in `name.lower()` OR `"router"` in `description.lower()`

**시나리오 2: 검색어 없음 - 전체 에이전트 반환**
- ✅ HTTP 상태 코드: `200 OK`
- ✅ 반환 에이전트 개수: 3 (모든 에이전트)
- ✅ 응답:
  ```json
  [
    {"id": "agent-001", "name": "Router Agent", ...},
    {"id": "agent-002", "name": "Database Agent", ...},
    {"id": "agent-003", "name": "Auth Agent", ...}
  ]
  ```

**시나리오 3: Limit 적용**
- ✅ HTTP 상태 코드: `200 OK`
- ✅ 반환 에이전트 개수: `<= limit`
- ✅ `len(response) <= 2`

**대소문자 무시 검증**:
- ✅ 요청: `q=ROUTER` → 결과: `[Router Agent]` (동일)
- ✅ 요청: `q=router` → 결과: `[Router Agent]` (동일)

**부분 일치 검증**:
- ✅ 요청: `q=rout` → 결과: `[Router Agent]` (일치)
- ✅ 요청: `q=routing` → 결과: `[Router Agent]` (description 일치)

**엣지 케이스**:
- ✅ 요청: `q=nonexistent` → 결과: `[]` (빈 배열)
- ✅ 요청: `limit=0` → 에러: `422` (최소 1)
- ✅ 요청: `limit=1001` → 에러: `422` (최대 1000)

**테스트 메서드**:
```python
# tests/api/routers/test_agent_router.py
@pytest.mark.asyncio
async def test_search_agents_with_query():
    response = client.get("/api/v1/agents/search?q=router")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # 모든 결과가 검색어를 포함하는지 확인
    for agent in data:
        assert (
            "router" in agent["name"].lower() or
            "router" in agent["description"].lower()
        )

@pytest.mark.asyncio
async def test_search_agents_no_query():
    response = client.get("/api/v1/agents/search")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # 최소 3개 에이전트 존재

@pytest.mark.asyncio
async def test_search_agents_with_limit():
    response = client.get("/api/v1/agents/search?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

@pytest.mark.asyncio
async def test_search_agents_case_insensitive():
    response1 = client.get("/api/v1/agents/search?q=ROUTER")
    response2 = client.get("/api/v1/agents/search?q=router")

    assert response1.json() == response2.json()
```

**관련 TAG**: `@TEST:AGENT-ROUTER-BUGFIX-001-T04`, `@TEST:AGENT-ROUTER-BUGFIX-001-T05`

---

## AC-4: 전체 시스템 통합 및 품질 게이트

### Given (사전 조건)

**환경 설정**:
- 로컬 개발 환경 또는 CI/CD 파이프라인
- Python 3.11+
- MongoDB 8.0.5+ (테스트 DB)
- 모든 의존성 패키지 설치

**코드 상태**:
- 3개 버그 수정 그룹 모두 구현 완료
- Git feature 브랜치: `feature/SPEC-AGENT-ROUTER-BUGFIX-001`

### When (실행 조건)

**테스트 실행**:
```bash
# 버그 관련 테스트만 실행
pytest tests/api/routers/test_agent_router.py::test_get_agent_coverage_success -v
pytest tests/api/routers/test_agent_router.py::test_update_agent_success -v
pytest tests/api/routers/test_agent_router.py::test_update_agent_empty_update -v
pytest tests/api/routers/test_agent_router.py::test_search_agents_with_query -v
pytest tests/api/routers/test_agent_router.py::test_search_agents_no_query -v

# 전체 테스트 스위트 실행
pytest tests/api/ -v --cov=apps/api --cov-report=term-missing
```

**코드 품질 검사**:
```bash
# 타입 체크
mypy apps/api apps/knowledge_builder --strict

# Linting
ruff check apps/api apps/knowledge_builder

# 포맷 검사
ruff format --check apps/api apps/knowledge_builder
```

**CI/CD 파이프라인 트리거**:
```bash
git push origin feature/SPEC-AGENT-ROUTER-BUGFIX-001
```

### Then (예상 결과)

**테스트 통과 기준**:
- ✅ 5개 버그 관련 테스트 모두 `PASSED`
- ✅ 전체 API 테스트 스위트 `PASSED` (회귀 없음)
- ✅ 테스트 커버리지 ≥ 85%
- ✅ 신규 코드 커버리지 = 100%

**테스트 출력 예시**:
```
tests/api/routers/test_agent_router.py::test_get_agent_coverage_success PASSED
tests/api/routers/test_agent_router.py::test_update_agent_success PASSED
tests/api/routers/test_agent_router.py::test_update_agent_empty_update PASSED
tests/api/routers/test_agent_router.py::test_search_agents_with_query PASSED
tests/api/routers/test_agent_router.py::test_search_agents_no_query PASSED

---------- coverage: platform linux, python 3.11.9 -----------
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
apps/api/routers/agent_router.py       120      5    96%   45-49
apps/api/dao/agent_dao.py              180     12    93%   78, 145-152
apps/api/schemas/agent_schema.py        65      0   100%
apps/knowledge_builder/coverage/
  coverage_dao.py                       95      3    97%   67-69
------------------------------------------------------------------
TOTAL                                  460     20    95%
```

**타입 체크 통과**:
```bash
$ mypy apps/api apps/knowledge_builder --strict
Success: no issues found in 45 source files
```

**Linting 통과**:
```bash
$ ruff check apps/api apps/knowledge_builder
All checks passed!
```

**CI/CD 파이프라인 성공**:
- ✅ Linting 단계: 통과
- ✅ Type checking 단계: 통과
- ✅ Unit tests 단계: 통과
- ✅ Integration tests 단계: 통과
- ✅ Coverage report 단계: 85% 이상

**회귀 방지 확인**:
- ✅ ROUTER-CONFLICT-001 관련 테스트 정상 동작
- ✅ 기존 통과 테스트가 여전히 통과
- ✅ Pokemon 카드 시스템 (rarity 필드) 정상 동작

**문서 자동 업데이트**:
- ✅ OpenAPI 스키마 (`/docs`):
  - `GET /agents/{agent_id}/coverage` 응답 스키마 업데이트
  - `PUT /agents/{agent_id}` 요청 스키마에 `rarity` 필드 추가
  - `GET /agents/search` 엔드포인트 문서 추가

**Git 커밋 메시지**:
```bash
fix(api): resolve 5 agent router bugs (SPEC-AGENT-ROUTER-BUGFIX-001)

- Bug #1: Fix coverage_data type mismatch (int → dict)
- Bug #2-3: Add rarity field validation to AgentUpdateRequest
- Bug #4-5: Implement search_agents method in AgentDAO

@SPEC:AGENT-ROUTER-BUGFIX-001
@TEST:AGENT-ROUTER-BUGFIX-001-T01
@TEST:AGENT-ROUTER-BUGFIX-001-T02
@TEST:AGENT-ROUTER-BUGFIX-001-T03
@TEST:AGENT-ROUTER-BUGFIX-001-T04
@TEST:AGENT-ROUTER-BUGFIX-001-T05

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**관련 TAG**: `@AC:AGENT-ROUTER-BUGFIX-001`

---

## 품질 게이트 체크리스트

### 필수 검증 항목 (Mandatory)

- [ ] **T01**: `test_get_agent_coverage_success` 통과
- [ ] **T02**: `test_update_agent_success` 통과
- [ ] **T03**: `test_update_agent_empty_update` 통과
- [ ] **T04**: `test_search_agents_with_query` 통과
- [ ] **T05**: `test_search_agents_no_query` 통과
- [ ] **Regression**: 전체 API 테스트 스위트 통과
- [ ] **Coverage**: 코드 커버리지 ≥ 85%
- [ ] **Type Safety**: `mypy --strict` 에러 없음
- [ ] **Code Quality**: `ruff check` 경고 없음
- [ ] **CI/CD**: GitHub Actions 파이프라인 성공

### 권장 검증 항목 (Recommended)

- [ ] **Performance**: Search 메서드 응답 시간 < 200ms (100 documents)
- [ ] **MongoDB Index**: 텍스트 인덱스 생성 확인
- [ ] **Documentation**: Docstring 모든 신규 메서드 작성
- [ ] **OpenAPI**: `/docs` 엔드포인트에서 수동 확인

### 선택 검증 항목 (Optional)

- [ ] **Load Test**: 1000+ documents로 검색 성능 테스트
- [ ] **Security**: SQL Injection (NoSQL Injection) 취약점 확인
- [ ] **E2E Test**: 전체 워크플로우 수동 테스트

---

## 릴리스 체크리스트

### 구현 완료 후

- [ ] 로컬에서 모든 테스트 통과 확인
- [ ] Git 커밋 메시지에 @TAG 포함
- [ ] Feature 브랜치 push: `git push origin feature/SPEC-AGENT-ROUTER-BUGFIX-001`
- [ ] PR 생성 (ROUTER-CONFLICT-001과 통합 또는 별도)

### PR 리뷰 전

- [ ] 코드 리뷰 체크리스트 작성
- [ ] CI/CD 파이프라인 성공 확인
- [ ] 스크린샷 또는 테스트 결과 첨부

### Merge 전

- [ ] 최소 1명 승인 획득
- [ ] main 브랜치 최신 코드 머지 (충돌 해결)
- [ ] Final CI/CD 통과 확인

### Merge 후

- [ ] SPEC 상태 업데이트: `draft` → `completed`
- [ ] SPEC 버전 업데이트: `v0.0.1` → `v0.1.0`
- [ ] `/alfred:3-sync` 실행 (문서 동기화)
- [ ] 관련 이슈 닫기 (GitHub Issue)

---

## 측정 지표

### 정량적 지표

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 테스트 통과율 | 100% (5/5) | `pytest --tb=short` |
| 코드 커버리지 | ≥ 85% | `pytest --cov` |
| 신규 코드 커버리지 | 100% | `pytest --cov` (신규 파일) |
| 타입 체크 에러 | 0 | `mypy --strict` |
| Linting 경고 | 0 | `ruff check` |
| 검색 응답 시간 | < 200ms | 로그 분석 |

### 정성적 지표

| 지표 | 목표 | 검증 방법 |
|------|------|----------|
| 코드 가독성 | "Good" 이상 | 코드 리뷰 |
| 문서 완성도 | Docstring 100% | 수동 확인 |
| API 일관성 | RESTful 준수 | OpenAPI 스키마 검토 |
| 에러 메시지 명확성 | 사용자 친화적 | 수동 테스트 |

---

## 실패 시나리오 및 롤백 계획

### 시나리오 1: 테스트 실패

**증상**: 5개 중 일부 테스트 실패

**대응**:
1. 실패 로그 분석 (`pytest -vv`)
2. 해당 Phase 재구현
3. 로컬에서 재테스트
4. 통과 후 커밋

### 시나리오 2: 회귀 테스트 실패

**증상**: 기존 통과 테스트가 실패

**대응**:
1. 변경 사항 롤백
2. 영향 범위 분석
3. 최소 변경으로 재구현
4. 회귀 테스트 통과 확인

### 시나리오 3: CI/CD 파이프라인 실패

**증상**: GitHub Actions 워크플로우 실패

**대응**:
1. 파이프라인 로그 확인
2. 환경 차이 분석 (로컬 vs CI)
3. 환경 설정 수정 (requirements.txt, Docker)
4. 재실행

### 시나리오 4: 타입 체크 실패

**증상**: `mypy --strict` 에러 발생

**대응**:
1. 타입 힌트 추가/수정
2. `# type: ignore` 최소 사용
3. Generic 타입 명시 (`List[AgentResponse]`)
4. 재검증

### 롤백 계획

**긴급 롤백**:
```bash
# Feature 브랜치 삭제
git branch -D feature/SPEC-AGENT-ROUTER-BUGFIX-001

# main 브랜치로 복귀
git checkout main
git pull origin main
```

**부분 롤백**:
```bash
# 특정 Phase 커밋 취소
git revert <commit-hash>
git push origin feature/SPEC-AGENT-ROUTER-BUGFIX-001
```

---

## 다음 단계

### 구현 준비 완료

- ✅ SPEC 문서 작성 완료
- ✅ 구현 계획 수립 완료
- ✅ 인수 기준 정의 완료

### 즉시 실행

**Command**: `/alfred:2-run SPEC-AGENT-ROUTER-BUGFIX-001`

**예상 워크플로우**:
1. TDD-implementer가 Phase 1-3 순차 구현
2. Quality-gate가 Phase 4 검증 수행
3. Git-manager가 커밋 및 PR 생성 관리

### 구현 후

**Command**: `/alfred:3-sync`

**목적**:
- OpenAPI 문서 자동 업데이트
- SPEC 상태 `completed`로 변경
- SPEC 버전 `v0.1.0`으로 업그레이드

---

**인수 기준 작성 완료**: 2025-11-10
**다음 Command**: `/alfred:2-run SPEC-AGENT-ROUTER-BUGFIX-001`
**최종 목표**: 5개 버그 테스트 모두 통과 + CI/CD 성공
