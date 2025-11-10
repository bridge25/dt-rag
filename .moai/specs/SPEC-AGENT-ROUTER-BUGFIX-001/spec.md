---
id: AGENT-ROUTER-BUGFIX-001
version: 0.0.1
status: draft
created: 2025-11-10
updated: 2025-11-10
author: @bridge25
priority: high
category: bugfix
labels: [api, router, dao, test, type-safety]
depends_on: [ROUTER-CONFLICT-001]
related_specs: [POKEMON-IMAGE-COMPLETE-001]
scope:
  packages:
    - apps/api/routers
    - apps/api
    - apps/api/schemas
    - apps/knowledge_builder/coverage
---

# @SPEC:AGENT-ROUTER-BUGFIX-001 - Agent Router 버그 수정

## HISTORY

### v0.0.1 (2025-11-10)
- **INITIAL**: SPEC 초안 작성
- **AUTHOR**: @bridge25
- **SECTIONS**: Environment, Assumptions, Requirements, Specifications 작성
- **SCOPE**: ROUTER-CONFLICT-001 CI/CD 검증 중 발견된 5개 버그 수정

---

## @TAG:SPEC-ENV-001 Environment (환경)

### 시스템 컨텍스트

**기술 스택**:
- **Framework**: FastAPI 0.118.3+
- **Testing**: pytest 8.3.4+
- **Database**: MongoDB 8.0.5+
- **ORM/ODM**: Motor (async MongoDB driver)
- **Schema Validation**: Pydantic 2.10.6+

**관련 아키텍처**:
```
apps/api/
├── routers/
│   ├── agent_router.py         # Bug #2-3: rarity 검증 오류
│   └── prompt_router.py
├── dao/
│   └── agent_dao.py            # Bug #4-5: search_agents 메서드 누락
├── schemas/
│   └── agent_schema.py         # Bug #2-3: rarity 필드 타입
└── main.py

apps/knowledge_builder/
└── coverage/
    └── coverage_dao.py         # Bug #1: coverage_data 타입 불일치
```

### 발견 경로

**버그 발견 시점**: SPEC-ROUTER-CONFLICT-001 구현 후 CI/CD 파이프라인 실행 중

**영향받은 테스트**:
1. `tests/api/routers/test_agent_router.py::test_get_agent_coverage_success`
2. `tests/api/routers/test_agent_router.py::test_update_agent_success`
3. `tests/api/routers/test_agent_router.py::test_update_agent_empty_update`
4. `tests/api/routers/test_agent_router.py::test_search_agents_with_query`
5. `tests/api/routers/test_agent_router.py::test_search_agents_no_query`

**버그 우선순위**:
- **Critical**: Bug #1 (coverage_data 타입 불일치) - 실패 테스트 1개
- **High**: Bug #4-5 (search_agents 메서드 누락) - 실패 테스트 2개
- **Medium**: Bug #2-3 (rarity 필드 검증 오류) - 실패 테스트 2개

---

## @TAG:SPEC-ASSUME-001 Assumptions (가정)

### 기술 가정

**A1. 기존 아키텍처 유지**
- WHEN 버그를 수정할 때, 기존 라우터-DAO-스키마 구조를 변경하지 않는다.
- WHY: 아키텍처 변경은 회귀 테스트 부담을 증가시킨다.

**A2. 타입 안전성 최우선**
- WHEN DAO 레이어에서 데이터를 반환할 때, Pydantic 스키마를 통한 검증을 수행한다.
- WHY: 런타임 타입 오류를 사전에 방지한다.

**A3. 기존 테스트 커버리지 유지**
- WHEN 버그 수정 후, 기존 통과 테스트가 모두 여전히 통과해야 한다.
- WHY: 회귀 방지 원칙.

**A4. Pokemon 시스템 필드 호환성**
- WHEN rarity 필드를 수정할 때, Pokemon 카드 시스템(SPEC-POKEMON-IMAGE-COMPLETE-001)과의 호환성을 유지한다.
- WHY: rarity는 에이전트 카드의 시각적 표현에 사용된다.

### 제약사항

**C1. 배포 타임라인**
- 이 SPEC은 ROUTER-CONFLICT-001 PR 머지 이전에 완료되어야 한다.

**C2. 데이터 마이그레이션 불필요**
- 버그 수정은 DB 스키마 변경을 포함하지 않는다.
- 기존 MongoDB 문서 구조는 유지된다.

---

## @TAG:SPEC-REQ-001 Requirements (요구사항)

### R01. Coverage Data 타입 불일치 해결

**WHEN** `GET /api/v1/agents/{agent_id}/coverage` 엔드포인트가 호출될 때,
**THEN** 시스템은 `coverage_data` 필드를 정수(int)가 아닌 딕셔너리(dict)로 반환해야 한다.

**근거**:
- 테스트: `test_get_agent_coverage_success`
- 예상 스키마:
  ```python
  {
    "coverage_data": {
      "total_sources": 42,
      "covered_sources": 38,
      "coverage_percentage": 90.5
    }
  }
  ```

**수정 대상**:
- `apps/knowledge_builder/coverage/coverage_dao.py`의 `get_coverage_by_agent_id()` 메서드

**검증 기준**:
- ✅ `test_get_agent_coverage_success` 테스트 통과
- ✅ `response.coverage_data`가 딕셔너리 타입
- ✅ 필수 키 존재: `total_sources`, `covered_sources`, `coverage_percentage`

---

### R02. Rarity 필드 검증 오류 수정

**WHEN** `PUT /api/v1/agents/{agent_id}` 엔드포인트로 `rarity` 필드가 포함된 업데이트 요청이 들어올 때,
**THEN** 시스템은 유효한 rarity 값을 허용하고 스키마 검증 오류를 발생시키지 않아야 한다.

**근거**:
- 테스트: `test_update_agent_success`, `test_update_agent_empty_update`
- 현재 오류: `Field required [type=missing, input_value=..., input_type=dict]`

**수정 대상**:
- `apps/api/schemas/agent_schema.py`의 `AgentUpdateRequest` 스키마
- `apps/api/routers/agent_router.py`의 `update_agent()` 엔드포인트

**허용 rarity 값** (Pokemon 카드 시스템 호환):
- `common`, `uncommon`, `rare`, `epic`, `legendary`

**검증 기준**:
- ✅ `test_update_agent_success` 테스트 통과 (rarity 포함)
- ✅ `test_update_agent_empty_update` 테스트 통과 (rarity 미포함)
- ✅ 잘못된 rarity 값 입력 시 422 Validation Error 반환

---

### R03. Search Agents 메서드 구현

**WHEN** `GET /api/v1/agents/search?q={query}` 엔드포인트가 호출될 때,
**THEN** 시스템은 `agent_dao.search_agents()` 메서드를 호출하여 검색 결과를 반환해야 한다.

**근거**:
- 테스트: `test_search_agents_with_query`, `test_search_agents_no_query`
- 현재 오류: `AttributeError: 'AgentDAO' object has no attribute 'search_agents'`

**수정 대상**:
- `apps/api/dao/agent_dao.py`에 `search_agents()` 메서드 추가

**검색 동작**:
- **WITH query**: `name` 또는 `description` 필드에서 대소문자 무시 부분 일치
- **WITHOUT query**: 모든 에이전트 반환 (limit 적용)

**메서드 시그니처**:
```python
async def search_agents(
    self,
    query: Optional[str] = None,
    limit: int = 100
) -> List[AgentResponse]:
    """
    Search agents by name or description.

    Args:
        query: Search keyword (optional)
        limit: Maximum number of results

    Returns:
        List of matching agents
    """
```

**검증 기준**:
- ✅ `test_search_agents_with_query` 테스트 통과
- ✅ `test_search_agents_no_query` 테스트 통과
- ✅ 검색어 포함 시 관련 에이전트만 반환
- ✅ 검색어 없을 시 전체 에이전트 반환 (limit 적용)

---

### R04. 회귀 방지 및 CI/CD 통합

**WHEN** 모든 버그 수정이 완료된 후,
**THEN** 시스템은 전체 테스트 스위트를 통과하고 CI/CD 파이프라인이 성공해야 한다.

**검증 기준**:
- ✅ 전체 테스트 통과: `pytest tests/api/routers/test_agent_router.py -v`
- ✅ 커버리지 유지: 최소 85% (기존 수준)
- ✅ 타입 체크 통과: `mypy apps/api apps/knowledge_builder`
- ✅ Linting 통과: `ruff check apps/api apps/knowledge_builder`

---

## @TAG:SPEC-SPEC-001 Specifications (세부 명세)

### Bug #1: Coverage Data 타입 불일치

**파일**: `apps/knowledge_builder/coverage/coverage_dao.py`

**현재 구현 문제**:
```python
# 잘못된 구현 (추정)
async def get_coverage_by_agent_id(self, agent_id: str) -> int:
    # 정수 반환
    return 42
```

**수정 후**:
```python
from typing import Dict, Any

async def get_coverage_by_agent_id(self, agent_id: str) -> Dict[str, Any]:
    """
    Get coverage data for a specific agent.

    Returns:
        Dictionary containing:
        - total_sources (int)
        - covered_sources (int)
        - coverage_percentage (float)
    """
    # MongoDB aggregation query
    result = await self.collection.aggregate([
        {"$match": {"agent_id": agent_id}},
        {"$group": {
            "_id": "$agent_id",
            "total_sources": {"$sum": 1},
            "covered_sources": {"$sum": {"$cond": ["$is_covered", 1, 0]}}
        }}
    ]).to_list(length=1)

    if not result:
        return {
            "total_sources": 0,
            "covered_sources": 0,
            "coverage_percentage": 0.0
        }

    data = result[0]
    total = data["total_sources"]
    covered = data["covered_sources"]
    percentage = (covered / total * 100) if total > 0 else 0.0

    return {
        "total_sources": total,
        "covered_sources": covered,
        "coverage_percentage": round(percentage, 2)
    }
```

**스키마 업데이트** (필요시 `apps/api/schemas/agent_schema.py`):
```python
class AgentCoverageResponse(BaseModel):
    agent_id: str
    coverage_data: Dict[str, Any]  # int → Dict 변경

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agent-001",
                "coverage_data": {
                    "total_sources": 42,
                    "covered_sources": 38,
                    "coverage_percentage": 90.5
                }
            }
        }
    )
```

---

### Bug #2-3: Rarity 필드 검증 오류

**파일 1**: `apps/api/schemas/agent_schema.py`

**AgentUpdateRequest 스키마 수정**:
```python
from typing import Optional, Literal

RarityType = Literal["common", "uncommon", "rare", "epic", "legendary"]

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    rarity: Optional[RarityType] = None  # 추가

    model_config = ConfigDict(
        extra="forbid",  # 정의되지 않은 필드 거부
        json_schema_extra={
            "example": {
                "name": "Updated Agent Name",
                "rarity": "rare"
            }
        }
    )
```

**파일 2**: `apps/api/routers/agent_router.py`

**update_agent 엔드포인트 수정**:
```python
@router.put(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK
)
async def update_agent(
    agent_id: str,
    update_data: AgentUpdateRequest,
    agent_dao: AgentDAO = Depends(get_agent_dao)
):
    """
    Update an existing agent.

    Args:
        agent_id: Agent ID to update
        update_data: Fields to update (partial update supported)

    Returns:
        Updated agent data

    Raises:
        HTTPException 404: Agent not found
        HTTPException 422: Invalid rarity value
    """
    # 빈 업데이트 요청 처리
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field must be provided for update"
        )

    # rarity 필드 검증 (Pydantic이 자동 처리하지만 명시적 확인)
    if "rarity" in update_dict:
        valid_rarities = ["common", "uncommon", "rare", "epic", "legendary"]
        if update_dict["rarity"] not in valid_rarities:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid rarity. Must be one of: {valid_rarities}"
            )

    updated_agent = await agent_dao.update_agent(agent_id, update_dict)
    if not updated_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    return updated_agent
```

---

### Bug #4-5: Search Agents 메서드 구현

**파일**: `apps/api/dao/agent_dao.py`

**search_agents 메서드 추가**:
```python
from typing import List, Optional
from apps.api.schemas.agent_schema import AgentResponse

class AgentDAO:
    # ... 기존 코드 ...

    async def search_agents(
        self,
        query: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentResponse]:
        """
        Search agents by name or description.

        Args:
            query: Search keyword (case-insensitive partial match)
            limit: Maximum number of results (default: 100)

        Returns:
            List of agents matching the search criteria

        Example:
            # Search with query
            agents = await dao.search_agents(query="router")

            # Get all agents
            all_agents = await dao.search_agents()
        """
        # Build MongoDB query
        if query:
            # Case-insensitive regex search on name and description
            mongo_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}}
                ]
            }
        else:
            # Return all agents
            mongo_query = {}

        # Execute query with limit
        cursor = self.collection.find(mongo_query).limit(limit)
        agents = await cursor.to_list(length=limit)

        # Convert MongoDB documents to AgentResponse
        return [
            AgentResponse(
                id=str(agent["_id"]),
                name=agent["name"],
                description=agent.get("description", ""),
                status=agent.get("status", "active"),
                rarity=agent.get("rarity", "common"),
                created_at=agent.get("created_at"),
                updated_at=agent.get("updated_at")
            )
            for agent in agents
        ]
```

**라우터 엔드포인트 업데이트** (`apps/api/routers/agent_router.py`):
```python
@router.get(
    "/agents/search",
    response_model=List[AgentResponse],
    status_code=status.HTTP_200_OK
)
async def search_agents(
    q: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    agent_dao: AgentDAO = Depends(get_agent_dao)
):
    """
    Search agents by name or description.

    Query Parameters:
        q: Search keyword (optional)
        limit: Maximum number of results (1-1000, default: 100)

    Returns:
        List of agents matching the search criteria

    Examples:
        GET /agents/search?q=router
        GET /agents/search?q=spec&limit=50
        GET /agents/search  # Returns all agents
    """
    return await agent_dao.search_agents(query=q, limit=limit)
```

---

## @TAG:SPEC-TRACE-001 Traceability (추적성)

### TAG 체인

```
@SPEC:AGENT-ROUTER-BUGFIX-001
  ↓ depends_on
@SPEC:ROUTER-CONFLICT-001 (라우터 충돌 해결)
  ↓ related_to
@SPEC:POKEMON-IMAGE-COMPLETE-001 (rarity 필드 사용)
```

### 테스트 TAG 매핑

| Bug | 테스트 파일 | TAG |
|-----|------------|-----|
| #1 | `test_agent_router.py::test_get_agent_coverage_success` | @TEST:AGENT-ROUTER-BUGFIX-001-T01 |
| #2 | `test_agent_router.py::test_update_agent_success` | @TEST:AGENT-ROUTER-BUGFIX-001-T02 |
| #3 | `test_agent_router.py::test_update_agent_empty_update` | @TEST:AGENT-ROUTER-BUGFIX-001-T03 |
| #4 | `test_agent_router.py::test_search_agents_with_query` | @TEST:AGENT-ROUTER-BUGFIX-001-T04 |
| #5 | `test_agent_router.py::test_search_agents_no_query` | @TEST:AGENT-ROUTER-BUGFIX-001-T05 |

### 코드 TAG 매핑

| 파일 | 수정 사항 | TAG |
|-----|----------|-----|
| `coverage_dao.py` | `get_coverage_by_agent_id()` 반환 타입 수정 | @CODE:AGENT-ROUTER-BUGFIX-001-C01 |
| `agent_schema.py` | `AgentUpdateRequest.rarity` 필드 추가 | @CODE:AGENT-ROUTER-BUGFIX-001-C02 |
| `agent_router.py` | `update_agent()` rarity 검증 추가 | @CODE:AGENT-ROUTER-BUGFIX-001-C03 |
| `agent_dao.py` | `search_agents()` 메서드 구현 | @CODE:AGENT-ROUTER-BUGFIX-001-C04 |

---

## 품질 게이트

### 필수 검증 항목

**테스트 통과**:
- ✅ 5개 버그 관련 테스트 모두 통과
- ✅ 전체 API 테스트 스위트 통과 (`tests/api/`)
- ✅ 커버리지 ≥ 85%

**타입 안전성**:
- ✅ `mypy apps/api apps/knowledge_builder --strict` 통과
- ✅ Pydantic 스키마 검증 정상 동작

**코드 품질**:
- ✅ `ruff check` 위반 사항 없음
- ✅ `ruff format --check` 통과

**문서화**:
- ✅ 모든 신규 메서드에 docstring 작성
- ✅ API 엔드포인트 OpenAPI 스키마 업데이트

---

## 다음 단계

1. **Implementation**: `/alfred:2-run SPEC-AGENT-ROUTER-BUGFIX-001`
2. **Validation**: CI/CD 파이프라인 전체 통과 확인
3. **Documentation**: `/alfred:3-sync` (API 문서 자동 업데이트)
4. **Integration**: ROUTER-CONFLICT-001 PR과 함께 머지

---

**SPEC 작성 완료**: 2025-11-10
**다음 Command**: `/alfred:2-run SPEC-AGENT-ROUTER-BUGFIX-001`
