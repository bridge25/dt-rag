---
id: AGENT-ROUTER-BUGFIX-001
version: 0.0.1
status: draft
created: 2025-11-10
updated: 2025-11-10
---

# @PLAN:AGENT-ROUTER-BUGFIX-001 - 구현 계획

## 개요

이 문서는 SPEC-AGENT-ROUTER-BUGFIX-001의 구현 전략, 단계별 계획, 기술적 접근 방법, 그리고 위험 요소를 정의합니다.

---

## 구현 전략

### 접근 방식

**단일 통합 수정 (Unified Bugfix Strategy)**:
- 5개 버그를 4개 논리 그룹으로 분류하여 순차적으로 수정
- 각 그룹은 독립적으로 테스트 가능
- TDD 원칙 준수: RED → GREEN → REFACTOR

### TDD 워크플로우

```
Phase 1: Coverage Data 수정
  RED    → test_get_agent_coverage_success 실패 확인
  GREEN  → coverage_dao.py 수정, 테스트 통과
  REFACTOR → 타입 힌트 강화, docstring 추가

Phase 2: Rarity 필드 검증
  RED    → test_update_agent_success 실패 확인
  GREEN  → agent_schema.py + agent_router.py 수정
  REFACTOR → 검증 로직 간소화

Phase 3: Search Agents 구현
  RED    → test_search_agents_* 실패 확인
  GREEN  → agent_dao.py에 search_agents() 추가
  REFACTOR → 쿼리 최적화, 인덱스 고려

Phase 4: 통합 검증
  VERIFY → 전체 테스트 스위트 실행
  VALIDATE → CI/CD 파이프라인 통과 확인
```

---

## 단계별 구현 계획

### Phase 1: Coverage Data 타입 불일치 해결

**목표**: `get_coverage_by_agent_id()` 메서드가 딕셔너리를 반환하도록 수정

**작업 항목**:

1. **현재 구현 분석**
   - `apps/knowledge_builder/coverage/coverage_dao.py` 읽기
   - 현재 반환 타입 및 로직 확인
   - MongoDB 컬렉션 스키마 이해

2. **테스트 우선 작성/수정**
   - `test_get_agent_coverage_success` 검토
   - 예상 응답 구조 확인:
     ```python
     {
       "coverage_data": {
         "total_sources": int,
         "covered_sources": int,
         "coverage_percentage": float
       }
     }
     ```

3. **DAO 레이어 수정**
   - 반환 타입을 `int` → `Dict[str, Any]`로 변경
   - MongoDB aggregation pipeline 구현:
     - `$match`: agent_id 필터링
     - `$group`: total/covered 집계
     - `$project`: percentage 계산

4. **스키마 업데이트**
   - `apps/api/schemas/agent_schema.py`의 `AgentCoverageResponse` 확인
   - `coverage_data` 필드 타입이 `Dict[str, Any]`인지 검증

5. **라우터 엔드포인트 검증**
   - `apps/api/routers/agent_router.py`의 `get_agent_coverage()` 확인
   - 응답 직렬화 정상 동작 확인

**검증 기준**:
- ✅ `test_get_agent_coverage_success` 통과
- ✅ 타입 체크 통과 (`mypy`)
- ✅ 응답 구조가 OpenAPI 스키마와 일치

**예상 소요 시간**: 우선순위 기준 - **Primary Goal**

---

### Phase 2: Rarity 필드 검증 오류 수정

**목표**: `AgentUpdateRequest`에 `rarity` 필드 추가 및 검증 로직 구현

**작업 항목**:

1. **스키마 확장**
   - `apps/api/schemas/agent_schema.py` 수정
   - `RarityType` Literal 타입 정의:
     ```python
     RarityType = Literal["common", "uncommon", "rare", "epic", "legendary"]
     ```
   - `AgentUpdateRequest`에 `rarity: Optional[RarityType]` 필드 추가
   - Pydantic `model_config`에 example 추가

2. **라우터 검증 로직 추가**
   - `apps/api/routers/agent_router.py`의 `update_agent()` 수정
   - 빈 업데이트 요청 처리:
     ```python
     update_dict = update_data.model_dump(exclude_unset=True)
     if not update_dict:
         raise HTTPException(422, "At least one field required")
     ```
   - rarity 필드 검증 (Pydantic 자동 검증 + 명시적 확인)

3. **테스트 케이스 검증**
   - `test_update_agent_success`: rarity 포함 업데이트
   - `test_update_agent_empty_update`: 빈 업데이트 요청 거부

4. **Pokemon 시스템 통합 확인**
   - SPEC-POKEMON-IMAGE-COMPLETE-001과의 호환성 확인
   - rarity 값이 Pokemon 카드 시스템에서 올바르게 사용되는지 검증

**검증 기준**:
- ✅ `test_update_agent_success` 통과
- ✅ `test_update_agent_empty_update` 통과
- ✅ 잘못된 rarity 값 입력 시 422 에러 반환
- ✅ Pydantic 스키마 검증 정상 동작

**예상 소요 시간**: 우선순위 기준 - **Primary Goal**

---

### Phase 3: Search Agents 메서드 구현

**목표**: `AgentDAO`에 `search_agents()` 메서드 추가

**작업 항목**:

1. **DAO 메서드 구현**
   - `apps/api/dao/agent_dao.py` 수정
   - 메서드 시그니처:
     ```python
     async def search_agents(
         self,
         query: Optional[str] = None,
         limit: int = 100
     ) -> List[AgentResponse]:
     ```

2. **MongoDB 쿼리 로직**
   - **WITH query**: `$or` + `$regex` (대소문자 무시)
     ```python
     {
       "$or": [
         {"name": {"$regex": query, "$options": "i"}},
         {"description": {"$regex": query, "$options": "i"}}
       ]
     }
     ```
   - **WITHOUT query**: 전체 문서 반환 (`{}`)
   - `limit` 적용: `.find().limit(limit)`

3. **응답 변환**
   - MongoDB 문서 → `AgentResponse` Pydantic 모델 변환
   - `_id` 필드를 문자열 `id`로 매핑
   - Optional 필드 기본값 처리

4. **라우터 엔드포인트 추가/수정**
   - `apps/api/routers/agent_router.py`에 `/agents/search` 엔드포인트 확인
   - Query 파라미터:
     - `q`: Optional[str] (검색 키워드)
     - `limit`: int = 100 (1-1000)
   - 응답 모델: `List[AgentResponse]`

5. **인덱스 최적화 고려**
   - MongoDB `name` 및 `description` 필드 텍스트 인덱스
   - 성능 테스트 (1000+ 문서)

**검증 기준**:
- ✅ `test_search_agents_with_query` 통과
- ✅ `test_search_agents_no_query` 통과
- ✅ 검색어 포함 시 관련 에이전트만 반환
- ✅ limit 파라미터 정상 동작

**예상 소요 시간**: 우선순위 기준 - **Primary Goal**

---

### Phase 4: 통합 검증 및 품질 게이트

**목표**: 전체 시스템 테스트 및 CI/CD 파이프라인 통과

**작업 항목**:

1. **로컬 테스트 실행**
   ```bash
   # 버그 수정 관련 테스트
   pytest tests/api/routers/test_agent_router.py::test_get_agent_coverage_success -v
   pytest tests/api/routers/test_agent_router.py::test_update_agent_success -v
   pytest tests/api/routers/test_agent_router.py::test_update_agent_empty_update -v
   pytest tests/api/routers/test_agent_router.py::test_search_agents_with_query -v
   pytest tests/api/routers/test_agent_router.py::test_search_agents_no_query -v

   # 전체 API 라우터 테스트
   pytest tests/api/routers/test_agent_router.py -v

   # 전체 테스트 스위트
   pytest tests/api/ -v --cov=apps/api --cov-report=term-missing
   ```

2. **타입 체크**
   ```bash
   mypy apps/api apps/knowledge_builder --strict
   ```

3. **코드 품질 검사**
   ```bash
   ruff check apps/api apps/knowledge_builder
   ruff format --check apps/api apps/knowledge_builder
   ```

4. **커버리지 분석**
   - 목표: ≥ 85%
   - 신규 코드 커버리지: 100% (모든 버그 수정 코드)

5. **회귀 테스트**
   - 기존 통과 테스트가 여전히 통과하는지 확인
   - ROUTER-CONFLICT-001 관련 테스트 정상 동작 확인

6. **CI/CD 파이프라인 검증**
   - GitHub Actions 워크플로우 트리거
   - 모든 단계 통과 확인:
     - Linting
     - Type checking
     - Unit tests
     - Integration tests

**검증 기준**:
- ✅ 5개 버그 테스트 모두 통과
- ✅ 전체 테스트 스위트 통과
- ✅ 커버리지 ≥ 85%
- ✅ 타입 체크 에러 없음
- ✅ Linting 경고 없음
- ✅ CI/CD 파이프라인 성공

**예상 소요 시간**: 우선순위 기준 - **Secondary Goal**

---

## 기술적 접근 방법

### 아키텍처 패턴

**레이어 분리 유지**:
```
Router (API 엔드포인트)
  ↓
Schema (Pydantic 검증)
  ↓
DAO (데이터 액세스)
  ↓
MongoDB (영속성)
```

**각 레이어의 책임**:

| 레이어 | 책임 | 버그 수정 대상 |
|--------|------|---------------|
| Router | HTTP 요청/응답, 라우팅 | Bug #2-3 (rarity 검증) |
| Schema | 데이터 검증, 직렬화 | Bug #2-3 (rarity 필드) |
| DAO | 데이터베이스 쿼리, 변환 | Bug #1 (coverage), Bug #4-5 (search) |
| MongoDB | 문서 저장, 인덱싱 | (변경 없음) |

### 타입 안전성 강화

**Pydantic 활용**:
- 모든 API 입력/출력에 Pydantic 모델 사용
- `Literal` 타입으로 enum 값 제한 (rarity)
- `Optional` 타입으로 선택적 필드 명시

**mypy 엄격 모드**:
- `--strict` 플래그로 모든 타입 힌트 강제
- `Dict[str, Any]` 대신 구체적 TypedDict 사용 고려

### MongoDB 쿼리 최적화

**인덱스 전략**:
```python
# text index for search
db.agents.create_index([
    ("name", "text"),
    ("description", "text")
])

# compound index for coverage queries
db.coverage.create_index([
    ("agent_id", 1),
    ("is_covered", 1)
])
```

**Aggregation Pipeline**:
- `$match` 단계에서 필터링 (인덱스 활용)
- `$group` 단계에서 집계 연산
- `$project` 단계에서 필드 계산

---

## 위험 요소 및 대응 방안

### 위험 #1: MongoDB 스키마 불일치

**위험 설명**:
- 기존 MongoDB 문서가 예상과 다른 구조를 가질 수 있음
- `coverage_data` 필드가 이미 존재하거나 다른 타입일 가능성

**대응 방안**:
- DAO 레이어에서 방어적 프로그래밍:
  ```python
  result = await self.collection.aggregate(...).to_list(1)
  if not result:
      return default_coverage_data()  # 안전한 기본값
  ```
- 마이그레이션 스크립트 불필요 (신규 계산 로직)

**우선순위**: Medium

---

### 위험 #2: Rarity 필드 기존 데이터 호환성

**위험 설명**:
- 기존 에이전트 문서에 `rarity` 필드가 없을 수 있음
- 잘못된 rarity 값이 이미 저장되어 있을 가능성

**대응 방안**:
- 스키마에서 `rarity` 필드를 Optional로 정의
- DAO에서 기본값 제공:
  ```python
  rarity=agent.get("rarity", "common")
  ```
- 데이터 검증 스크립트 (선택적):
  ```bash
  # 잘못된 rarity 값 찾기
  db.agents.find({
    "rarity": {
      "$nin": ["common", "uncommon", "rare", "epic", "legendary"]
    }
  })
  ```

**우선순위**: Low (기존 데이터 오염 가능성 낮음)

---

### 위험 #3: Search 성능 저하

**위험 설명**:
- 대규모 데이터셋 (1000+ 에이전트)에서 regex 검색 성능 저하
- MongoDB 인덱스 미사용 시 full collection scan

**대응 방안**:
- 텍스트 인덱스 생성 (우선):
  ```python
  db.agents.create_index([("name", "text"), ("description", "text")])
  ```
- 텍스트 인덱스 활용 쿼리:
  ```python
  if query:
      mongo_query = {"$text": {"$search": query}}
  ```
- 페이지네이션 추가 (향후 개선):
  - `skip` 파라미터 추가
  - cursor 기반 페이징 고려

**우선순위**: Medium (현재 데이터 규모 작음)

---

### 위험 #4: 회귀 테스트 실패

**위험 설명**:
- 버그 수정으로 인해 기존 통과 테스트가 실패할 가능성
- ROUTER-CONFLICT-001과의 충돌 가능성

**대응 방안**:
- Phase 4에서 전체 테스트 스위트 실행
- 각 Phase마다 관련 테스트만 먼저 실행
- Git feature branch 전략:
  ```bash
  # ROUTER-CONFLICT-001 브랜치에서 분기
  git checkout feature/SPEC-ROUTER-CONFLICT-001
  git checkout -b feature/SPEC-AGENT-ROUTER-BUGFIX-001
  ```
- PR 전에 main 브랜치 최신 코드 머지

**우선순위**: High

---

## 테스트 전략

### 단위 테스트 (Unit Tests)

**Coverage DAO**:
```python
# test_coverage_dao.py
@pytest.mark.asyncio
async def test_get_coverage_by_agent_id_returns_dict():
    dao = CoverageDAO(...)
    result = await dao.get_coverage_by_agent_id("agent-001")

    assert isinstance(result, dict)
    assert "total_sources" in result
    assert "covered_sources" in result
    assert "coverage_percentage" in result
    assert result["coverage_percentage"] >= 0.0
    assert result["coverage_percentage"] <= 100.0
```

**Agent DAO**:
```python
# test_agent_dao.py
@pytest.mark.asyncio
async def test_search_agents_with_query():
    dao = AgentDAO(...)
    results = await dao.search_agents(query="router", limit=10)

    assert len(results) <= 10
    assert all(
        "router" in agent.name.lower() or "router" in agent.description.lower()
        for agent in results
    )

@pytest.mark.asyncio
async def test_search_agents_without_query():
    dao = AgentDAO(...)
    results = await dao.search_agents(limit=50)

    assert len(results) <= 50
```

### 통합 테스트 (Integration Tests)

**API 엔드포인트**:
- 기존 테스트 (`test_agent_router.py`) 활용
- 실제 MongoDB 연결 사용 (테스트 DB)
- FastAPI TestClient로 HTTP 요청 시뮬레이션

### E2E 테스트 (Optional)

**전체 워크플로우**:
1. 에이전트 생성
2. Coverage 데이터 생성
3. 에이전트 업데이트 (rarity 포함)
4. 검색 수행
5. Coverage 조회

---

## 문서화 요구사항

### API 문서 업데이트

**OpenAPI 스키마**:
- `/agents/{agent_id}/coverage` 응답 스키마 업데이트
- `/agents/{agent_id}` 요청 스키마에 rarity 필드 추가
- `/agents/search` 엔드포인트 파라미터 문서화

**자동 생성**:
- FastAPI가 Pydantic 모델에서 자동 생성
- `/docs` 엔드포인트에서 확인 가능

### 코드 문서화

**Docstring 스타일** (Google 스타일):
```python
def search_agents(self, query: Optional[str] = None) -> List[AgentResponse]:
    """
    Search agents by name or description.

    Args:
        query: Search keyword (case-insensitive partial match).
            If None, returns all agents.

    Returns:
        List of agents matching the search criteria.

    Raises:
        ValueError: If query is empty string.
        DatabaseError: If MongoDB connection fails.

    Example:
        >>> agents = await dao.search_agents(query="router")
        >>> len(agents)
        3
    """
```

### CHANGELOG 업데이트

**`.moai/specs/SPEC-AGENT-ROUTER-BUGFIX-001/spec.md` HISTORY 섹션**:
```markdown
### v0.1.0 (2025-11-10)
- **COMPLETED**: 5개 버그 수정 완료
- **AUTHOR**: @bridge25
- **CHANGES**:
  - Bug #1: coverage_data 타입 int → dict 수정
  - Bug #2-3: rarity 필드 검증 추가
  - Bug #4-5: search_agents 메서드 구현
- **TESTS**: 5개 실패 테스트 모두 통과
```

---

## 다음 단계

### 즉시 실행

1. **구현 시작**: `/alfred:2-run SPEC-AGENT-ROUTER-BUGFIX-001`
2. **Phase 1 수행**: Coverage Data 타입 수정
3. **Phase 2 수행**: Rarity 필드 검증 추가
4. **Phase 3 수행**: Search Agents 메서드 구현
5. **Phase 4 수행**: 통합 검증 및 품질 게이트

### 구현 후

1. **문서 동기화**: `/alfred:3-sync` (API 문서 자동 업데이트)
2. **PR 생성**: ROUTER-CONFLICT-001 PR과 함께 또는 별도 PR
3. **리뷰 요청**: @bridge25 또는 팀 리드
4. **CI/CD 확인**: GitHub Actions 워크플로우 통과
5. **Merge**: main 브랜치 머지

### 향후 개선 사항

**성능 최적화** (Low Priority):
- MongoDB 텍스트 인덱스 생성
- Search 결과 캐싱 (Redis)
- 페이지네이션 구현

**기능 확장** (Optional):
- Advanced search 필터 (status, rarity, created_at 범위)
- Fuzzy search (Levenshtein distance)
- Search 결과 정렬 옵션 (relevance, date, name)

---

**계획 작성 완료**: 2025-11-10
**다음 Command**: `/alfred:2-run SPEC-AGENT-ROUTER-BUGFIX-001`
