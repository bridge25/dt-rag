# @SPEC:AGENT-GROWTH-001 인수 기준 (Acceptance Criteria)

## 개요

본 문서는 SPEC-AGENT-GROWTH-001 (Agent Growth Platform Phase 0)의 인수 기준을 정의합니다.
모든 시나리오는 **Given-When-Then** 형식으로 작성되었으며, 각 시나리오는 독립적으로 검증 가능합니다.

## 테스트 환경

- **Database**: PostgreSQL 12+ (production), SQLite 3 (testing)
- **Python**: 3.9+
- **Framework**: SQLAlchemy 2.0 (async), NetworkX 3.0+
- **Test Runner**: pytest-asyncio

## 인수 기준 시나리오

### AC-1: agents 테이블 생성 및 제약조건 검증

**Given**:
- Alembic migration script `00XX_add_agents_table.py`가 작성됨
- PostgreSQL 또는 SQLite 데이터베이스가 실행 중

**When**:
- `alembic upgrade head` 명령 실행

**Then**:
- agents 테이블이 생성되어야 함
- 19개 컬럼이 정확한 타입으로 존재해야 함
- PRIMARY KEY 제약조건 (agent_id)이 존재해야 함
- CHECK 제약조건 3개가 존재해야 함:
  - `valid_level`: level >= 1 AND level <= 5
  - `valid_xp`: current_xp >= 0
  - `valid_coverage`: coverage_percent >= 0 AND coverage_percent <= 100
- PostgreSQL: GIN 인덱스 `idx_agents_taxonomy` 존재
- 모든 인덱스: `idx_agents_level`, `idx_agents_coverage` 존재
- Default 값 확인:
  - level = 1
  - current_xp = 0
  - coverage_percent = 0.0
  - retrieval_config = '{"top_k": 5, "strategy": "hybrid"}'

**검증 방법**:
```python
async def test_ac1_agents_table_creation():
    # PostgreSQL 검증
    async with db_manager.async_session() as session:
        # 테이블 존재 확인
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'agents'
            )
        """))
        assert result.scalar() is True

        # 컬럼 개수 확인
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'agents'
        """))
        assert result.scalar() == 19

        # 제약조건 확인
        result = await session.execute(text("""
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_name = 'agents' AND constraint_type = 'CHECK'
        """))
        constraints = [row[0] for row in result.fetchall()]
        assert 'valid_level' in constraints
        assert 'valid_xp' in constraints
        assert 'valid_coverage' in constraints
```

---

### AC-2: Agent ORM 모델 인스턴스 생성

**Given**:
- Agent 클래스가 database.py에 정의됨
- agents 테이블이 생성됨

**When**:
- Agent 인스턴스를 생성하고 기본값 검증

**Then**:
- agent_id가 자동 생성되어야 함 (UUID v4)
- level = 1, current_xp = 0, coverage_percent = 0.0
- created_at, updated_at이 자동 설정되어야 함
- retrieval_config가 기본 dict로 초기화되어야 함
- features_config가 빈 dict로 초기화되어야 함

**검증 방법**:
```python
async def test_ac2_agent_model_instantiation():
    agent = Agent(
        name="Test Agent",
        taxonomy_node_ids=[uuid4(), uuid4()],
        taxonomy_version="1.0.0"
    )

    assert agent.agent_id is not None
    assert isinstance(agent.agent_id, uuid.UUID)
    assert agent.level == 1
    assert agent.current_xp == 0
    assert agent.coverage_percent == 0.0
    assert agent.retrieval_config == {"top_k": 5, "strategy": "hybrid"}
    assert agent.features_config == {}
    assert agent.created_at is not None
    assert agent.updated_at is not None
```

---

### AC-3: CoverageMeterService - 단일 노드 커버리지 계산

**Given**:
- DocTaxonomy 테이블에 테스트 데이터 삽입됨:
  - node_id = 'node-001', doc_id = 'doc-001', confidence = 0.8
  - node_id = 'node-001', doc_id = 'doc-002', confidence = 0.9
- CoverageMeterService 인스턴스 생성됨

**When**:
- `calculate_coverage(agent_id="test", taxonomy_node_ids=["node-001"], version="1.0.0")` 호출

**Then**:
- CoverageResult.overall_coverage = 100.0 (2 docs, target = 2)
- CoverageResult.node_coverage["node-001"] = 100.0
- CoverageResult.document_counts["node-001"] = 2
- CoverageResult.target_counts["node-001"] = 2

**검증 방법**:
```python
async def test_ac3_single_node_coverage():
    # 테스트 데이터 삽입
    async with db_manager.async_session() as session:
        node = TaxonomyNode(node_id=uuid4(), label="Test Node", version="1.0.0")
        session.add(node)
        await session.commit()

        doc1 = Document(doc_id=uuid4())
        doc2 = Document(doc_id=uuid4())
        session.add_all([doc1, doc2])
        await session.commit()

        dt1 = DocTaxonomy(doc_id=doc1.doc_id, node_id=node.node_id, confidence=0.8, version="1.0.0")
        dt2 = DocTaxonomy(doc_id=doc2.doc_id, node_id=node.node_id, confidence=0.9, version="1.0.0")
        session.add_all([dt1, dt2])
        await session.commit()

        # Coverage 계산
        service = CoverageMeterService()
        result = await service.calculate_coverage(
            agent_id="test-agent",
            taxonomy_node_ids=[str(node.node_id)],
            version="1.0.0"
        )

        assert result.overall_coverage == 100.0
        assert result.document_counts[str(node.node_id)] == 2
```

---

### AC-4: CoverageMeterService - 다중 노드 및 하위 노드 포함

**Given**:
- Taxonomy 구조:
  ```
  root-001 (2 docs)
    ├─ child-001 (3 docs)
    └─ child-002 (1 doc)
  ```
- DocTaxonomy 테이블에 6개 문서 매핑됨

**When**:
- `calculate_coverage(taxonomy_node_ids=["root-001"])` 호출

**Then**:
- _get_descendant_nodes()가 ["root-001", "child-001", "child-002"] 반환
- overall_coverage = 전체 6개 문서 기준 계산
- node_coverage에 3개 노드 모두 포함

**검증 방법**:
```python
async def test_ac4_multi_node_with_descendants():
    # Taxonomy 트리 생성
    async with db_manager.async_session() as session:
        root = TaxonomyNode(node_id=uuid4(), label="Root", version="1.0.0")
        child1 = TaxonomyNode(node_id=uuid4(), label="Child 1", version="1.0.0")
        child2 = TaxonomyNode(node_id=uuid4(), label="Child 2", version="1.0.0")

        edge1 = TaxonomyEdge(parent=root.node_id, child=child1.node_id, version="1.0.0")
        edge2 = TaxonomyEdge(parent=root.node_id, child=child2.node_id, version="1.0.0")

        session.add_all([root, child1, child2, edge1, edge2])
        await session.commit()

        # 문서 생성 및 매핑
        # ... (6개 문서 생성 및 DocTaxonomy 매핑)

        # Coverage 계산
        service = CoverageMeterService()
        result = await service.calculate_coverage(
            agent_id="test-agent",
            taxonomy_node_ids=[str(root.node_id)],
            version="1.0.0"
        )

        assert len(result.node_coverage) == 3  # root + 2 children
        assert sum(result.document_counts.values()) == 6
```

---

### AC-5: CoverageMeterService - Confidence 필터링 (>= 0.7)

**Given**:
- DocTaxonomy 테이블에 다양한 confidence 값의 문서:
  - doc-001: confidence = 0.9 (포함)
  - doc-002: confidence = 0.7 (포함)
  - doc-003: confidence = 0.6 (제외)
  - doc-004: confidence = 0.5 (제외)

**When**:
- `calculate_coverage(taxonomy_node_ids=["node-001"])` 호출 (default confidence_threshold=0.7)

**Then**:
- document_counts["node-001"] = 2 (only >= 0.7)
- doc-003, doc-004는 카운트에서 제외되어야 함

**검증 방법**:
```python
async def test_ac5_confidence_filtering():
    async with db_manager.async_session() as session:
        node = TaxonomyNode(node_id=uuid4(), version="1.0.0")
        session.add(node)
        await session.commit()

        docs = [Document(doc_id=uuid4()) for _ in range(4)]
        session.add_all(docs)
        await session.commit()

        mappings = [
            DocTaxonomy(doc_id=docs[0].doc_id, node_id=node.node_id, confidence=0.9, version="1.0.0"),
            DocTaxonomy(doc_id=docs[1].doc_id, node_id=node.node_id, confidence=0.7, version="1.0.0"),
            DocTaxonomy(doc_id=docs[2].doc_id, node_id=node.node_id, confidence=0.6, version="1.0.0"),
            DocTaxonomy(doc_id=docs[3].doc_id, node_id=node.node_id, confidence=0.5, version="1.0.0"),
        ]
        session.add_all(mappings)
        await session.commit()

        service = CoverageMeterService()
        result = await service.calculate_coverage(
            agent_id="test",
            taxonomy_node_ids=[str(node.node_id)],
            version="1.0.0"
        )

        assert result.document_counts[str(node.node_id)] == 2  # Only 0.9 and 0.7
```

---

### AC-6: CoverageMeterService - Gap Detection (임계값 50%)

**Given**:
- 3개 노드의 coverage:
  - node-001: 80% (임계값 이상)
  - node-002: 40% (갭)
  - node-003: 20% (갭)

**When**:
- `detect_gaps(coverage_result, threshold=0.5)` 호출

**Then**:
- 2개의 Gap 반환 (node-002, node-003)
- Gap 정렬: missing_docs DESC (node-003 우선)
- recommendation 문자열 포함: "Collect X more documents"

**검증 방법**:
```python
async def test_ac6_gap_detection():
    # Coverage 결과 생성
    coverage_result = CoverageResult(
        agent_id="test",
        overall_coverage=46.7,
        node_coverage={
            "node-001": 80.0,
            "node-002": 40.0,
            "node-003": 20.0
        },
        document_counts={
            "node-001": 8,
            "node-002": 4,
            "node-003": 2
        },
        target_counts={
            "node-001": 10,
            "node-002": 10,
            "node-003": 10
        },
        version="1.0.0"
    )

    service = CoverageMeterService()
    gaps = await service.detect_gaps(coverage_result, threshold=0.5)

    assert len(gaps) == 2
    assert gaps[0].node_id in ["node-002", "node-003"]
    assert gaps[0].missing_docs == 8  # node-003 (10 - 2)
    assert "Collect 8 more documents" in gaps[0].recommendation
```

---

### AC-7: AgentDAO - 에이전트 생성 및 초기 커버리지

**Given**:
- agents 테이블이 비어있음
- Taxonomy 노드 2개 존재 (각 5개 문서)

**When**:
- `AgentDAO.create_agent(name="Test", taxonomy_node_ids=[node1, node2])`

**Then**:
- Agent 레코드 생성됨
- agent_id는 UUID v4
- level = 1, current_xp = 0
- total_documents = 10 (초기 coverage 계산 결과)
- coverage_percent > 0.0
- last_coverage_update가 설정됨
- created_at, updated_at가 설정됨

**검증 방법**:
```python
async def test_ac7_agent_creation_with_coverage():
    async with db_manager.async_session() as session:
        # Taxonomy 및 문서 준비
        node1 = TaxonomyNode(node_id=uuid4(), version="1.0.0")
        node2 = TaxonomyNode(node_id=uuid4(), version="1.0.0")
        session.add_all([node1, node2])
        await session.commit()

        # 각 노드에 5개 문서 매핑
        # ... (10개 문서 생성 및 DocTaxonomy 매핑)

        # 에이전트 생성
        agent = await AgentDAO.create_agent(
            session,
            name="Test Agent",
            taxonomy_node_ids=[node1.node_id, node2.node_id],
            taxonomy_version="1.0.0"
        )

        assert agent.agent_id is not None
        assert agent.level == 1
        assert agent.current_xp == 0
        assert agent.total_documents == 10
        assert agent.coverage_percent > 0.0
        assert agent.last_coverage_update is not None
```

---

### AC-8: AgentDAO - 존재하지 않는 에이전트 조회

**Given**:
- agents 테이블에 데이터 없음

**When**:
- `AgentDAO.get_agent(session, agent_id=uuid4())`

**Then**:
- None 반환 (예외 발생 안 함)

**검증 방법**:
```python
async def test_ac8_get_nonexistent_agent():
    async with db_manager.async_session() as session:
        result = await AgentDAO.get_agent(session, uuid4())
        assert result is None
```

---

### AC-9: AgentDAO - 에이전트 업데이트 및 updated_at 자동 설정

**Given**:
- Agent 1개 생성됨 (name="Original")

**When**:
- `AgentDAO.update_agent(agent_id, name="Updated")`

**Then**:
- name = "Updated"
- updated_at이 이전 값보다 커야 함
- created_at은 변경되지 않아야 함

**검증 방법**:
```python
async def test_ac9_agent_update_timestamp():
    async with db_manager.async_session() as session:
        # 에이전트 생성
        agent = await AgentDAO.create_agent(
            session, name="Original", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0"
        )
        original_created_at = agent.created_at
        original_updated_at = agent.updated_at

        # 1초 대기
        await asyncio.sleep(1)

        # 업데이트
        updated_agent = await AgentDAO.update_agent(
            session, agent.agent_id, name="Updated"
        )

        assert updated_agent.name == "Updated"
        assert updated_agent.created_at == original_created_at
        assert updated_agent.updated_at > original_updated_at
```

---

### AC-10: AgentDAO - 에이전트 삭제 (Hard Delete)

**Given**:
- Agent 1개 생성됨

**When**:
- `AgentDAO.delete_agent(agent_id)` 호출

**Then**:
- True 반환
- agents 테이블에서 레코드 삭제됨
- 재조회 시 None 반환

**검증 방법**:
```python
async def test_ac10_agent_deletion():
    async with db_manager.async_session() as session:
        # 에이전트 생성
        agent = await AgentDAO.create_agent(
            session, name="To Delete", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0"
        )
        agent_id = agent.agent_id

        # 삭제
        result = await AgentDAO.delete_agent(session, agent_id)
        assert result is True

        # 재조회
        deleted_agent = await AgentDAO.get_agent(session, agent_id)
        assert deleted_agent is None
```

---

### AC-11: AgentDAO - 에이전트 목록 필터링 (level)

**Given**:
- 3개 에이전트 생성:
  - Agent A: level=1
  - Agent B: level=2
  - Agent C: level=1

**When**:
- `AgentDAO.list_agents(level=1)` 호출

**Then**:
- 2개 에이전트 반환 (Agent A, Agent C)
- 정렬: created_at DESC

**검증 방법**:
```python
async def test_ac11_list_agents_by_level():
    async with db_manager.async_session() as session:
        # 3개 에이전트 생성
        agent_a = await AgentDAO.create_agent(session, name="A", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0")
        agent_b = await AgentDAO.create_agent(session, name="B", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0")
        agent_c = await AgentDAO.create_agent(session, name="C", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0")

        # Agent B의 level을 2로 변경
        await AgentDAO.update_agent(session, agent_b.agent_id, level=2)

        # level=1 필터링
        agents = await AgentDAO.list_agents(session, level=1)

        assert len(agents) == 2
        assert all(a.level == 1 for a in agents)
```

---

### AC-12: AgentDAO - 에이전트 목록 필터링 (min_coverage)

**Given**:
- 3개 에이전트:
  - Agent A: coverage_percent=85.0
  - Agent B: coverage_percent=60.0
  - Agent C: coverage_percent=40.0

**When**:
- `AgentDAO.list_agents(min_coverage=50.0)` 호출

**Then**:
- 2개 에이전트 반환 (Agent A, Agent B)

**검증 방법**:
```python
async def test_ac12_list_agents_by_min_coverage():
    async with db_manager.async_session() as session:
        # 3개 에이전트 생성 및 coverage 설정
        agent_a = await AgentDAO.create_agent(session, name="A", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0")
        agent_b = await AgentDAO.create_agent(session, name="B", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0")
        agent_c = await AgentDAO.create_agent(session, name="C", taxonomy_node_ids=[uuid4()], taxonomy_version="1.0.0")

        await AgentDAO.update_agent(session, agent_a.agent_id, coverage_percent=85.0)
        await AgentDAO.update_agent(session, agent_b.agent_id, coverage_percent=60.0)
        await AgentDAO.update_agent(session, agent_c.agent_id, coverage_percent=40.0)

        # min_coverage=50.0 필터링
        agents = await AgentDAO.list_agents(session, min_coverage=50.0)

        assert len(agents) == 2
        assert all(a.coverage_percent >= 50.0 for a in agents)
```

---

### AC-13: 성능 - Agent Creation (10 nodes, 1K docs)

**Given**:
- Taxonomy 구조: 10개 노드
- DocTaxonomy: 1,000개 문서 매핑

**When**:
- `AgentDAO.create_agent()` 호출

**Then**:
- 실행 시간 < 5초
- 초기 커버리지 계산 완료

**검증 방법**:
```python
async def test_ac13_performance_agent_creation():
    import time

    async with db_manager.async_session() as session:
        # 10개 노드 및 1000개 문서 준비
        # ... (테스트 데이터 생성)

        start_time = time.time()
        agent = await AgentDAO.create_agent(
            session,
            name="Performance Test",
            taxonomy_node_ids=node_ids,
            taxonomy_version="1.0.0"
        )
        elapsed = time.time() - start_time

        assert elapsed < 5.0
        assert agent.coverage_percent > 0.0
```

---

### AC-14: 성능 - Coverage Calculation (50 nodes, 10K docs)

**Given**:
- Taxonomy 구조: 50개 노드 (다층 계층)
- DocTaxonomy: 10,000개 문서 매핑

**When**:
- `CoverageMeterService.calculate_coverage()` 호출

**Then**:
- 실행 시간 < 2초
- CoverageResult 반환

**검증 방법**:
```python
async def test_ac14_performance_coverage_calculation():
    import time

    async with db_manager.async_session() as session:
        # 50개 노드 및 10000개 문서 준비
        # ... (테스트 데이터 생성)

        service = CoverageMeterService()
        start_time = time.time()
        result = await service.calculate_coverage(
            agent_id="perf-test",
            taxonomy_node_ids=root_node_ids,
            version="1.0.0"
        )
        elapsed = time.time() - start_time

        assert elapsed < 2.0
        assert result.overall_coverage >= 0.0
```

---

### AC-15: Alembic Downgrade 정상 동작

**Given**:
- agents 테이블이 생성됨 (migration 00XX 적용)

**When**:
- `alembic downgrade -1` 실행

**Then**:
- agents 테이블 삭제됨
- 인덱스 모두 삭제됨
- 제약조건 모두 삭제됨
- 에러 없이 완료

**검증 방법**:
```bash
# 마이그레이션 업그레이드
alembic upgrade head

# 테이블 확인
psql -c "SELECT * FROM agents LIMIT 1"

# 다운그레이드
alembic downgrade -1

# 테이블 삭제 확인
psql -c "SELECT * FROM agents" # 에러 발생해야 함
```

---

## 테스트 커버리지 목표

| 항목 | 목표 커버리지 |
|------|---------------|
| **CoverageMeterService** | 90% |
| **AgentDAO** | 85% |
| **Agent ORM Model** | 95% |
| **Integration Tests** | 80% |
| **전체** | **>= 85%** |

## 성능 벤치마크 목표

| 작업 | 데이터 규모 | 목표 시간 |
|------|-------------|-----------|
| Agent Creation | 10 nodes, 1K docs | < 5 seconds |
| Agent Creation | 50 nodes, 10K docs | < 5 seconds |
| Coverage Calculation | 10 nodes | < 2 seconds |
| Coverage Calculation | 50 nodes, 10K docs | < 2 seconds |
| Graph Traversal | 100-node taxonomy | < 500ms |
| Document Count Query | 50 nodes | < 1 second |

## 인수 완료 체크리스트

### Schema & Migration
- [ ] AC-1: agents 테이블 생성 및 제약조건 검증
- [ ] AC-2: Agent ORM 모델 인스턴스 생성
- [ ] AC-15: Alembic downgrade 정상 동작

### CoverageMeterService
- [ ] AC-3: 단일 노드 커버리지 계산
- [ ] AC-4: 다중 노드 및 하위 노드 포함
- [ ] AC-5: Confidence 필터링 (>= 0.7)
- [ ] AC-6: Gap Detection (임계값 50%)

### AgentDAO
- [ ] AC-7: 에이전트 생성 및 초기 커버리지
- [ ] AC-8: 존재하지 않는 에이전트 조회
- [ ] AC-9: 에이전트 업데이트 및 updated_at
- [ ] AC-10: 에이전트 삭제 (Hard Delete)
- [ ] AC-11: 에이전트 목록 필터링 (level)
- [ ] AC-12: 에이전트 목록 필터링 (min_coverage)

### Performance
- [ ] AC-13: Agent Creation 성능 (< 5초)
- [ ] AC-14: Coverage Calculation 성능 (< 2초)

### Code Quality
- [ ] 전체 테스트 커버리지 >= 85%
- [ ] pytest 전체 통과 (0 failed)
- [ ] ruff 린트 에러 0건
- [ ] mypy 타입 체크 에러 0건

## 추가 확인 사항

### Documentation
- [ ] Docstring 작성 (모든 public 메서드)
- [ ] README 업데이트 (Phase 0 완료 반영)
- [ ] CHANGELOG 업데이트

### Integration
- [ ] TaxonomyDAGManager 그래프 캐시 재사용 확인
- [ ] DocTaxonomy 테이블 호환성 확인
- [ ] PostgreSQL/SQLite 양쪽 백엔드 테스트 통과

### Security
- [ ] SQL Injection 취약점 없음 (parameterized queries)
- [ ] taxonomy_node_ids 검증 (존재 여부)
- [ ] confidence_threshold 범위 검증 (0.0-1.0)

---

## 최종 승인 기준

**Phase 0 완료 승인 조건**:
1. 모든 인수 기준 (AC-1 ~ AC-15) 통과
2. 테스트 커버리지 >= 85%
3. 성능 벤치마크 목표 달성
4. Code quality 체크 통과 (lint, type check)
5. Documentation 업데이트 완료

**승인 후 다음 단계**: Phase 1 - API Integration 시작
