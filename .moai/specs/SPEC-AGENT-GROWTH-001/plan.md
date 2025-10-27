# @SPEC:AGENT-GROWTH-001 구현 계획서

## 개요

**SPEC ID**: AGENT-GROWTH-001
**Phase**: Phase 0 Foundation
**예상 기간**: 5-7일
**우선순위**: High
**담당자**: @sonheungmin

## 목표

Agent Growth Platform의 기반 계층을 구축합니다:
1. **agents 테이블** 생성 (Alembic migration)
2. **CoverageMeterService** 구현 (Taxonomy 기반 커버리지 계산)
3. **AgentDAO** 구현 (CRUD 메서드)

## 전제 조건

### 완료된 사항
- ✅ SPEC-DATABASE-001: 기본 database schema 구현 완료
- ✅ SPEC-SCHEMA-SYNC-001: DocTaxonomy 복합 PK 구현 완료
- ✅ TaxonomyDAGManager: NetworkX 기반 그래프 검증 완료
- ✅ DocTaxonomy: 문서-분류 매핑 완료
- ✅ SearchDAO._build_filter_clause(): `canonical_in` 필터 구현 완료

### 필요한 사항
- PostgreSQL 12+ with pgvector extension
- Python 3.9+
- SQLAlchemy 2.0+ (async)
- NetworkX 3.0+
- pytest (테스트 실행)

## 구현 단계

### Phase 0-1: Database Schema (1-2일)

#### Task 1.1: Alembic Migration Script 작성
**파일**: `alembic/versions/00XX_add_agents_table.py`

**작업 내용**:
1. PostgreSQL/SQLite 감지 로직
2. agents 테이블 생성 (19 columns)
3. 인덱스 생성 (GIN, B-tree)
4. 제약조건 추가 (CHECK constraints)
5. RAISE NOTICE 로깅 (PostgreSQL)

**산출물**:
```python
# alembic/versions/00XX_add_agents_table.py
revision = '00XX'
down_revision = '0009'

def upgrade():
    # PostgreSQL: native UUID[], JSONB, GIN index
    # SQLite: String(36), TEXT with JSON, B-tree index
    ...

def downgrade():
    op.drop_table('agents')
```

**검증**:
```bash
# 마이그레이션 실행
alembic upgrade head

# 테이블 확인
psql -c "\d agents"

# 인덱스 확인
psql -c "\di agents*"
```

#### Task 1.2: Agent ORM Model 추가
**파일**: `apps/api/database.py`

**작업 내용**:
1. Agent class 정의 (Base 상속)
2. mapped_column with Mapped type hints
3. get_uuid_type(), get_array_type(), get_json_type() 사용
4. __repr__() 메서드 구현

**산출물**:
```python
class Agent(Base):
    __tablename__ = "agents"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    taxonomy_node_ids: Mapped[List[uuid.UUID]] = mapped_column(
        get_array_type(get_uuid_type()), nullable=False
    )
    ...
```

**검증**:
```python
# tests/unit/test_database.py
async def test_agent_model_creation():
    agent = Agent(
        name="Test Agent",
        taxonomy_node_ids=[uuid4(), uuid4()],
        taxonomy_version="1.0.0"
    )
    assert agent.level == 1
    assert agent.current_xp == 0
```

### Phase 0-2: CoverageMeterService 구현 (2-3일)

#### Task 2.1: 디렉터리 구조 생성
```bash
mkdir -p apps/knowledge_builder/coverage
touch apps/knowledge_builder/coverage/__init__.py
touch apps/knowledge_builder/coverage/meter.py
touch apps/knowledge_builder/coverage/models.py
```

#### Task 2.2: Dataclass 모델 정의
**파일**: `apps/knowledge_builder/coverage/models.py`

**작업 내용**:
```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class CoverageResult:
    agent_id: str
    overall_coverage: float
    node_coverage: Dict[str, float]
    document_counts: Dict[str, int]
    target_counts: Dict[str, int]
    version: str

@dataclass
class Gap:
    node_id: str
    current_coverage: float
    target_coverage: float
    missing_docs: int
    recommendation: str
```

#### Task 2.3: CoverageMeterService 구현
**파일**: `apps/knowledge_builder/coverage/meter.py`

**작업 내용**:
1. `__init__()`: confidence_threshold 파라미터 (기본 0.7)
2. `calculate_coverage()`: 메인 로직
3. `_get_descendant_nodes()`: NetworkX 그래프 탐색
4. `_count_documents_per_node()`: SQL GROUP BY 쿼리
5. `_get_target_document_counts()`: coverage_targets 조회 (선택 사항)
6. `detect_gaps()`: 임계값 기반 갭 탐지

**핵심 로직**:
```python
class CoverageMeterService:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold

    async def calculate_coverage(
        self,
        agent_id: str,
        taxonomy_node_ids: List[str],
        version: str = "1.0.0"
    ) -> CoverageResult:
        async with db_manager.async_session() as session:
            # 1. 하위 노드 재귀 조회
            all_node_ids = await self._get_descendant_nodes(
                session, taxonomy_node_ids, version
            )

            # 2. 노드별 문서 개수 집계
            doc_counts = await self._count_documents_per_node(
                session, all_node_ids, version
            )

            # 3. 타깃 개수 조회
            targets = await self._get_target_document_counts(
                session, all_node_ids
            )

            # 4. 커버리지 % 계산
            node_coverage = {}
            for node_id, doc_count in doc_counts.items():
                target = targets.get(node_id, doc_count)
                node_coverage[node_id] = (doc_count / max(target, 1)) * 100

            # 5. 전체 커버리지 계산
            total_docs = sum(doc_counts.values())
            total_target = sum(targets.values())
            overall_coverage = (total_docs / max(total_target, 1)) * 100

            return CoverageResult(
                agent_id=agent_id,
                overall_coverage=overall_coverage,
                node_coverage=node_coverage,
                document_counts=doc_counts,
                target_counts=targets,
                version=version
            )
```

**_get_descendant_nodes() 구현**:
```python
async def _get_descendant_nodes(
    self,
    session: AsyncSession,
    root_node_ids: List[str],
    version: str
) -> List[str]:
    """
    TaxonomyDAGManager의 캐시된 그래프 재사용
    """
    from apps.api.taxonomy_dag import taxonomy_dag_manager

    graph = await taxonomy_dag_manager._build_networkx_graph(version)

    descendants = set(root_node_ids)
    for root_id in root_node_ids:
        descendants.update(nx.descendants(graph, root_id))

    return list(descendants)
```

**_count_documents_per_node() 구현**:
```python
async def _count_documents_per_node(
    self,
    session: AsyncSession,
    node_ids: List[str],
    version: str
) -> Dict[str, int]:
    """
    단일 GROUP BY 쿼리로 N+1 문제 방지
    """
    query = text("""
        SELECT node_id, COUNT(DISTINCT doc_id) as doc_count
        FROM doc_taxonomy
        WHERE node_id = ANY(:node_ids)
          AND version = :version
          AND confidence >= :confidence_threshold
        GROUP BY node_id
    """)

    result = await session.execute(query, {
        "node_ids": node_ids,
        "version": version,
        "confidence_threshold": self.confidence_threshold
    })

    return {str(row[0]): row[1] for row in result.fetchall()}
```

**detect_gaps() 구현**:
```python
async def detect_gaps(
    self,
    coverage_result: CoverageResult,
    threshold: float = 0.5
) -> List[Gap]:
    """
    임계값 미만 노드 탐지
    """
    gaps = []

    for node_id, coverage_pct in coverage_result.node_coverage.items():
        if coverage_pct < threshold * 100:
            missing = int(
                coverage_result.target_counts[node_id]
                - coverage_result.document_counts[node_id]
            )
            gaps.append(Gap(
                node_id=node_id,
                current_coverage=coverage_pct,
                target_coverage=threshold * 100,
                missing_docs=missing,
                recommendation=f"Collect {missing} more documents for this topic"
            ))

    # 우선순위 정렬 (missing_docs DESC)
    gaps.sort(key=lambda g: g.missing_docs, reverse=True)

    return gaps
```

**검증**:
```python
# tests/unit/test_coverage_meter.py
async def test_calculate_coverage():
    service = CoverageMeterService()
    result = await service.calculate_coverage(
        agent_id="test-agent-001",
        taxonomy_node_ids=["node-001", "node-002"],
        version="1.0.0"
    )
    assert result.overall_coverage >= 0.0
    assert result.overall_coverage <= 100.0
```

### Phase 0-3: AgentDAO 구현 (1-2일)

#### Task 3.1: AgentDAO 클래스 생성
**파일**: `apps/api/agent_dao.py` (또는 `apps/api/database.py`에 추가)

**작업 내용**:
1. `create_agent()`: 에이전트 생성 + 초기 커버리지 계산
2. `get_agent()`: 에이전트 조회 (None 반환)
3. `update_agent()`: 에이전트 업데이트 (updated_at 자동)
4. `delete_agent()`: 에이전트 삭제 (hard delete)
5. `list_agents()`: 필터링 + 정렬

**create_agent() 구현**:
```python
class AgentDAO:
    @staticmethod
    async def create_agent(
        session: AsyncSession,
        name: str,
        taxonomy_node_ids: List[UUID],
        taxonomy_version: str = "1.0.0",
        scope_description: str = None,
        retrieval_config: Dict = None,
        features_config: Dict = None
    ) -> Agent:
        """
        에이전트 생성 + 초기 커버리지 계산
        """
        # 1. Taxonomy 노드 존재 확인
        query = text("""
            SELECT COUNT(*) FROM taxonomy_nodes
            WHERE node_id = ANY(:node_ids) AND version = :version
        """)
        result = await session.execute(query, {
            "node_ids": [str(nid) for nid in taxonomy_node_ids],
            "version": taxonomy_version
        })
        count = result.scalar()

        if count != len(taxonomy_node_ids):
            raise ValueError("Some taxonomy_node_ids do not exist")

        # 2. 초기 커버리지 계산
        from apps.knowledge_builder.coverage.meter import CoverageMeterService

        coverage_service = CoverageMeterService()
        agent_id = str(uuid4())

        coverage_result = await coverage_service.calculate_coverage(
            agent_id=agent_id,
            taxonomy_node_ids=[str(nid) for nid in taxonomy_node_ids],
            version=taxonomy_version
        )

        # 3. Agent 인스턴스 생성
        agent = Agent(
            agent_id=uuid.UUID(agent_id),
            name=name,
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version=taxonomy_version,
            scope_description=scope_description,
            total_documents=sum(coverage_result.document_counts.values()),
            total_chunks=0,  # Phase 0에서는 0으로 설정
            coverage_percent=coverage_result.overall_coverage,
            last_coverage_update=datetime.utcnow(),
            retrieval_config=retrieval_config or {"top_k": 5, "strategy": "hybrid"},
            features_config=features_config or {}
        )

        # 4. 데이터베이스 삽입
        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        return agent
```

**get_agent() 구현**:
```python
@staticmethod
async def get_agent(
    session: AsyncSession,
    agent_id: UUID
) -> Optional[Agent]:
    """
    에이전트 조회 (None 반환, 예외 발생 안 함)
    """
    query = select(Agent).where(Agent.agent_id == agent_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()
```

**update_agent() 구현**:
```python
@staticmethod
async def update_agent(
    session: AsyncSession,
    agent_id: UUID,
    **kwargs
) -> Agent:
    """
    에이전트 업데이트 (updated_at 자동 설정)
    """
    agent = await AgentDAO.get_agent(session, agent_id)

    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    for key, value in kwargs.items():
        if hasattr(agent, key):
            setattr(agent, key, value)

    agent.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(agent)

    return agent
```

**delete_agent() 구현**:
```python
@staticmethod
async def delete_agent(
    session: AsyncSession,
    agent_id: UUID
) -> bool:
    """
    에이전트 삭제 (hard delete)
    """
    agent = await AgentDAO.get_agent(session, agent_id)

    if not agent:
        return False

    await session.delete(agent)
    await session.commit()

    return True
```

**list_agents() 구현**:
```python
@staticmethod
async def list_agents(
    session: AsyncSession,
    status: Optional[str] = None,
    level: Optional[int] = None,
    min_coverage: Optional[float] = None,
    max_results: int = 50
) -> List[Agent]:
    """
    에이전트 목록 조회 (필터링 + 정렬)
    """
    query = select(Agent)

    # 필터 적용
    if level is not None:
        query = query.where(Agent.level == level)

    if min_coverage is not None:
        query = query.where(Agent.coverage_percent >= min_coverage)

    # 정렬 및 제한
    query = query.order_by(Agent.created_at.desc()).limit(max_results)

    result = await session.execute(query)
    return list(result.scalars().all())
```

**검증**:
```python
# tests/unit/test_agent_dao.py
async def test_create_agent():
    async with db_manager.async_session() as session:
        agent = await AgentDAO.create_agent(
            session,
            name="Test Agent",
            taxonomy_node_ids=[uuid4(), uuid4()],
            taxonomy_version="1.0.0"
        )
        assert agent.agent_id is not None
        assert agent.level == 1
        assert agent.coverage_percent >= 0.0
```

## 테스트 전략

### Unit Tests (70% coverage 목표)

**파일 구조**:
```
tests/unit/
├── test_coverage_meter.py     # CoverageMeterService 단위 테스트
├── test_agent_dao.py           # AgentDAO 단위 테스트
└── test_database.py            # Agent ORM 모델 테스트
```

**주요 테스트 케이스**:
1. **CoverageMeterService**:
   - calculate_coverage() 기본 동작
   - _get_descendant_nodes() 그래프 탐색
   - _count_documents_per_node() SQL 쿼리
   - detect_gaps() 임계값 테스트
   - 빈 Taxonomy 처리
   - Zero document 처리

2. **AgentDAO**:
   - create_agent() 성공 케이스
   - create_agent() 실패 케이스 (invalid node_ids)
   - get_agent() 존재/미존재
   - update_agent() 필드 업데이트
   - delete_agent() 삭제 검증
   - list_agents() 필터링 및 정렬

3. **Agent ORM Model**:
   - 모델 인스턴스 생성
   - 기본값 설정 확인
   - 제약조건 검증 (level 1-5, xp >= 0, coverage 0-100)

### Integration Tests (20% coverage 목표)

**파일**: `tests/integration/test_agent_growth_foundation.py`

**주요 테스트 케이스**:
1. End-to-End: 에이전트 생성 → 커버리지 계산 → DB 저장
2. 실제 Taxonomy 데이터로 커버리지 계산 정확도 검증
3. 다중 에이전트 생성 및 list_agents() 정렬 확인
4. Gap detection과 실제 문서 개수 비교

### Performance Tests (10% coverage 목표)

**파일**: `tests/performance/test_coverage_performance.py`

**성능 목표**:
- Agent creation: < 5 seconds (10 nodes, 1K docs)
- Coverage calculation: < 2 seconds (50 nodes, 10K docs)
- Graph traversal: < 500ms (100-node taxonomy)
- Document count query: < 1 second (50 nodes)

## 검증 체크리스트

### Phase 0-1 완료 기준
- [ ] agents 테이블 마이그레이션 성공 (PostgreSQL/SQLite)
- [ ] 인덱스 생성 확인 (`\di agents*`)
- [ ] Agent ORM 모델 import 가능
- [ ] Agent 인스턴스 생성 테스트 통과

### Phase 0-2 완료 기준
- [ ] CoverageMeterService import 가능
- [ ] calculate_coverage() 단위 테스트 통과
- [ ] detect_gaps() 단위 테스트 통과
- [ ] TaxonomyDAGManager 그래프 재사용 확인
- [ ] DocTaxonomy 쿼리 실행 확인

### Phase 0-3 완료 기준
- [ ] AgentDAO import 가능
- [ ] create_agent() 통합 테스트 통과
- [ ] CRUD 메서드 단위 테스트 통과
- [ ] list_agents() 필터링 테스트 통과
- [ ] 초기 커버리지 계산 정확도 검증

### 최종 검증
- [ ] 전체 테스트 커버리지 >= 85%
- [ ] pytest 전체 통과 (0 failed)
- [ ] 성능 테스트 목표 달성
- [ ] Alembic downgrade 정상 동작
- [ ] 문서화 완료 (docstring, README 업데이트)

## 리스크 및 대응 방안

### 리스크 1: NetworkX 그래프 캐시 미스
**증상**: _get_descendant_nodes()에서 그래프 재구축으로 성능 저하
**대응**:
- TaxonomyDAGManager._build_networkx_graph(version) 캐싱 확인
- 필요 시 LRU cache 추가

### 리스크 2: DocTaxonomy 문서 개수 0건
**증상**: coverage_percent = 0.0, Gap detection 실패
**대응**:
- 초기 데이터 시드 스크립트 실행
- 테스트 픽스처에 샘플 DocTaxonomy 데이터 추가

### 리스크 3: PostgreSQL/SQLite 타입 호환성
**증상**: SQLite에서 UUID[] 직렬화 실패
**대응**:
- ArrayType TypeDecorator 적용 확인
- 단위 테스트에서 양쪽 백엔드 검증

### 리스크 4: 성능 목표 미달성
**증상**: Coverage 계산 > 2초
**대응**:
- SQL 쿼리 EXPLAIN ANALYZE 분석
- GIN 인덱스 사용 확인
- Batch 처리 고려 (chunk 단위 계산)

## 다음 단계 (Phase 1)

Phase 0 완료 후 다음 작업:
1. **Coverage API**: GET /agents/{agent_id}/coverage
2. **Agent Creation API**: POST /agents/from-taxonomy
3. **Gap Detection API**: GET /agents/{agent_id}/gaps
4. **Agent Query API**: POST /agents/{agent_id}/query (with scope filtering)
5. **UI: Taxonomy Tree Selector**: React 컴포넌트 구현

## 참고 자료

- **TaxonomySystem_Analysis_v1.0.md**: 전체 설계 문서
- **SPEC-DATABASE-001**: 데이터베이스 스키마 명세
- **SPEC-SCHEMA-SYNC-001**: DocTaxonomy 설계
- **apps/api/taxonomy_dag.py**: TaxonomyDAGManager 구현
- **apps/api/database.py**: 기존 ORM 모델 참조
