---
id: SCHEMA-SYNC-001-ACCEPTANCE
version: 0.1.0
parent_spec: SCHEMA-SYNC-001
created: 2025-10-12
updated: 2025-10-12
---

# @SPEC:SCHEMA-SYNC-001 Acceptance Criteria & Test Scenarios

## 개요

DocTaxonomy 스키마 동기화의 수락 기준과 Given-When-Then 형식의 테스트 시나리오를 정의합니다. 모든 시나리오는 자동화된 테스트로 구현되어야 합니다.

---

## 품질 게이트 (Quality Gates)

### Gate 1: 모델 정합성 (Model Integrity)

**기준**:
- DocTaxonomy 모델이 PostgreSQL 스키마와 100% 일치
- mapping_id 필드가 완전히 제거됨
- Composite primary key가 정확히 구현됨
- 모든 NOT NULL 제약이 준수됨

**검증 방법**:
```python
# @TEST:SCHEMA-SYNC-001:GATE-1
def test_model_schema_integrity():
    from apps.api.database import DocTaxonomy
    from sqlalchemy import inspect

    inspector = inspect(DocTaxonomy)

    # 1. mapping_id 부재 확인
    assert 'mapping_id' not in [c.name for c in inspector.columns]

    # 2. Composite PK 확인
    pk_names = [c.name for c in inspector.primary_key]
    assert set(pk_names) == {'doc_id', 'node_id', 'version'}

    # 3. NOT NULL 제약 확인
    nullable_map = {c.name: c.nullable for c in inspector.columns}
    assert nullable_map['doc_id'] == False
    assert nullable_map['node_id'] == False
    assert nullable_map['version'] == False
    assert nullable_map['path'] == False
    assert nullable_map['confidence'] == False

    # 4. created_at 필드 존재 확인
    assert 'created_at' in [c.name for c in inspector.columns]
```

**통과 조건**: 100% 테스트 통과

---

### Gate 2: 기능 동작 (Functional Behavior)

**기준**:
- job_orchestrator가 taxonomy_path로 node_id를 쿼리함
- 존재하지 않는 taxonomy_path에 대해 명확한 에러 발생
- version이 "1.0.0"으로 설정됨
- 기존 문서 업로드 플로우가 정상 동작함

**검증 방법**:
```python
# @TEST:SCHEMA-SYNC-001:GATE-2
@pytest.mark.asyncio
async def test_functional_behavior(async_session):
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    from apps.ingestion.batch.job_orchestrator import JobOrchestrator

    # Setup: Taxonomy node 생성
    node = TaxonomyNode(
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    async_session.add(node)
    await async_session.commit()

    # Execute: Document 업로드
    orchestrator = JobOrchestrator()
    job_data = {
        "file_name": "test.pdf",
        "file_content_hex": b"content".hex(),
        "file_format": "pdf",
        "taxonomy_path": ["AI", "RAG"]
    }

    event = await orchestrator._process_document("cmd-001", job_data)

    # Verify: DocTaxonomy 검증
    doc_tax = await async_session.get(
        DocTaxonomy,
        {"doc_id": event.document_id, "node_id": node.node_id, "version": "1.0.0"}
    )

    assert doc_tax is not None
    assert doc_tax.version == "1.0.0"
    assert doc_tax.path == ["AI", "RAG"]
```

**통과 조건**: 모든 기능 테스트 통과

---

### Gate 3: 에러 핸들링 (Error Handling)

**기준**:
- taxonomy_path 매칭 실패 시 명확한 에러 메시지
- 필수 필드 누락 시 적절한 검증 에러
- DB 트랜잭션 실패 시 롤백 동작

**검증 방법**:
```python
# @TEST:SCHEMA-SYNC-001:GATE-3
@pytest.mark.asyncio
async def test_error_handling(async_session):
    from apps.ingestion.batch.job_orchestrator import JobOrchestrator

    orchestrator = JobOrchestrator()
    job_data = {
        "file_name": "test.pdf",
        "file_content_hex": b"content".hex(),
        "file_format": "pdf",
        "taxonomy_path": ["NonExistent", "Path"]  # 존재하지 않는 경로
    }

    # Verify: 명확한 에러 발생
    with pytest.raises(ValueError) as exc_info:
        await orchestrator._process_document("cmd-001", job_data)

    assert "Taxonomy path" in str(exc_info.value)
    assert "not found" in str(exc_info.value)
```

**통과 조건**: 모든 에러 케이스 처리 확인

---

### Gate 4: 성능 (Performance)

**기준**:
- node_id 쿼리 latency < 10ms (p95)
- DocTaxonomy INSERT latency < 50ms (p95)
- GIN 인덱스 활용 확인

**검증 방법**:
```python
# @TEST:SCHEMA-SYNC-001:GATE-4
@pytest.mark.asyncio
async def test_performance_benchmarks(async_session):
    import time
    from apps.api.database import TaxonomyNode
    from sqlalchemy import select

    # Setup: 1000개 taxonomy nodes 생성
    nodes = [
        TaxonomyNode(
            label=f"Node{i}",
            canonical_path=["AI", f"Category{i}"],
            version="1.0.0",
            confidence=1.0
        )
        for i in range(1000)
    ]
    async_session.add_all(nodes)
    await async_session.commit()

    # Benchmark: node_id 쿼리 성능
    latencies = []
    for i in range(100):
        start = time.perf_counter()
        query = select(TaxonomyNode.node_id).where(
            TaxonomyNode.canonical_path == ["AI", f"Category{i}"]
        )
        await async_session.execute(query)
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

    # Verify: p95 latency < 10ms
    p95_latency = sorted(latencies)[95]
    assert p95_latency < 10.0, f"p95 latency {p95_latency:.2f}ms exceeds 10ms"
```

**통과 조건**: p95 latency < 10ms

---

## Given-When-Then 테스트 시나리오

### 시나리오 1: 정상 DocTaxonomy 생성

**Given**:
- PostgreSQL에 taxonomy_nodes 테이블에 `["AI", "RAG"]` 경로의 노드가 존재함
- job_orchestrator가 실행 중임

**When**:
- 사용자가 `taxonomy_path=["AI", "RAG"]`로 문서를 업로드함

**Then**:
- DocTaxonomy 레코드가 생성됨
- `node_id`가 taxonomy_nodes에서 쿼리된 값과 일치함
- `version`이 "1.0.0"으로 설정됨
- `path`가 `["AI", "RAG"]`로 저장됨
- `confidence`가 1.0으로 설정됨
- `created_at`이 현재 시각으로 기록됨

**테스트 코드**:
```python
# @TEST:SCHEMA-SYNC-001:SCENARIO-1
@pytest.mark.asyncio
async def test_scenario_1_normal_doc_taxonomy_creation(async_session):
    """
    Given: taxonomy_nodes에 ["AI", "RAG"] 경로 노드 존재
    When: taxonomy_path=["AI", "RAG"]로 문서 업로드
    Then: DocTaxonomy 레코드가 정확히 생성됨
    """
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    from apps.ingestion.batch.job_orchestrator import JobOrchestrator
    import uuid

    # Given
    node_id = uuid.uuid4()
    node = TaxonomyNode(
        node_id=node_id,
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    async_session.add(node)
    await async_session.commit()

    orchestrator = JobOrchestrator()

    # When
    job_data = {
        "file_name": "rag_guide.pdf",
        "file_content_hex": b"RAG content".hex(),
        "file_format": "pdf",
        "taxonomy_path": ["AI", "RAG"],
        "source_url": "https://example.com/rag"
    }

    event = await orchestrator._process_document("cmd-001", job_data)
    doc_id = uuid.UUID(event.document_id)

    # Then
    doc_tax = await async_session.get(
        DocTaxonomy,
        {"doc_id": doc_id, "node_id": node_id, "version": "1.0.0"}
    )

    assert doc_tax is not None, "DocTaxonomy 레코드가 생성되지 않음"
    assert doc_tax.node_id == node_id, "node_id 불일치"
    assert doc_tax.version == "1.0.0", "version 불일치"
    assert doc_tax.path == ["AI", "RAG"], "path 불일치"
    assert doc_tax.confidence == 1.0, "confidence 불일치"
    assert doc_tax.created_at is not None, "created_at 누락"
```

---

### 시나리오 2: taxonomy_path 매칭 실패

**Given**:
- PostgreSQL taxonomy_nodes에 `["AI", "RAG"]` 경로만 존재함
- `["AI", "ML"]` 경로는 존재하지 않음

**When**:
- 사용자가 `taxonomy_path=["AI", "ML"]`로 문서 업로드 시도함

**Then**:
- `ValueError` 예외가 발생함
- 에러 메시지에 "Taxonomy path"와 "not found"가 포함됨
- DocTaxonomy 레코드가 생성되지 않음
- Document 레코드도 롤백됨 (트랜잭션 실패)

**테스트 코드**:
```python
# @TEST:SCHEMA-SYNC-001:SCENARIO-2
@pytest.mark.asyncio
async def test_scenario_2_taxonomy_path_not_found(async_session):
    """
    Given: taxonomy_nodes에 ["AI", "ML"] 경로 없음
    When: taxonomy_path=["AI", "ML"]로 문서 업로드 시도
    Then: ValueError 발생, DocTaxonomy 생성 안됨
    """
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    from apps.ingestion.batch.job_orchestrator import JobOrchestrator
    from sqlalchemy import select

    # Given: AI/RAG만 존재, AI/ML은 없음
    node = TaxonomyNode(
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    async_session.add(node)
    await async_session.commit()

    orchestrator = JobOrchestrator()

    # When
    job_data = {
        "file_name": "ml_guide.pdf",
        "file_content_hex": b"ML content".hex(),
        "file_format": "pdf",
        "taxonomy_path": ["AI", "ML"],  # 존재하지 않는 경로
        "source_url": "https://example.com/ml"
    }

    # Then
    with pytest.raises(ValueError) as exc_info:
        await orchestrator._process_document("cmd-001", job_data)

    assert "Taxonomy path" in str(exc_info.value)
    assert "not found" in str(exc_info.value)

    # Verify: DocTaxonomy가 생성되지 않았는지 확인
    result = await async_session.execute(select(DocTaxonomy))
    doc_taxonomies = result.scalars().all()
    assert len(doc_taxonomies) == 0, "DocTaxonomy가 롤백되지 않음"
```

---

### 시나리오 3: Composite Primary Key 충돌

**Given**:
- 동일한 `(doc_id, node_id, version)` 조합의 DocTaxonomy가 이미 존재함

**When**:
- 동일한 조합으로 중복 INSERT 시도함

**Then**:
- `IntegrityError` 예외가 발생함
- 기존 레코드는 변경되지 않음

**테스트 코드**:
```python
# @TEST:SCHEMA-SYNC-001:SCENARIO-3
@pytest.mark.asyncio
async def test_scenario_3_composite_pk_conflict(async_session):
    """
    Given: DocTaxonomy 레코드 존재
    When: 동일한 (doc_id, node_id, version)으로 INSERT 시도
    Then: IntegrityError 발생
    """
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    from sqlalchemy.exc import IntegrityError
    import uuid

    # Given
    doc_id = uuid.uuid4()
    node_id = uuid.uuid4()

    node = TaxonomyNode(
        node_id=node_id,
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    async_session.add(node)

    doc = Document(doc_id=doc_id, title="Test Doc")
    async_session.add(doc)

    doc_tax1 = DocTaxonomy(
        doc_id=doc_id,
        node_id=node_id,
        version="1.0.0",
        path=["AI", "RAG"],
        confidence=0.95,
        hitl_required=False
    )
    async_session.add(doc_tax1)
    await async_session.commit()

    # When: 동일한 composite key로 INSERT 시도
    doc_tax2 = DocTaxonomy(
        doc_id=doc_id,
        node_id=node_id,
        version="1.0.0",  # 동일한 버전
        path=["AI", "RAG"],
        confidence=0.90,  # confidence만 다름
        hitl_required=False
    )
    async_session.add(doc_tax2)

    # Then
    with pytest.raises(IntegrityError):
        await async_session.commit()
```

---

### 시나리오 4: NOT NULL 제약 위반

**Given**:
- DocTaxonomy 모델이 올바르게 정의됨

**When**:
- 필수 필드(doc_id, node_id, version, path, confidence) 중 하나가 누락된 채로 INSERT 시도함

**Then**:
- `IntegrityError` 또는 `InvalidRequestError` 발생
- 레코드가 생성되지 않음

**테스트 코드**:
```python
# @TEST:SCHEMA-SYNC-001:SCENARIO-4
@pytest.mark.asyncio
async def test_scenario_4_not_null_constraint_violation(async_session):
    """
    Given: DocTaxonomy 필수 필드 정의
    When: path 필드 누락하고 INSERT 시도
    Then: IntegrityError 발생
    """
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    from sqlalchemy.exc import IntegrityError
    import uuid

    # Given
    doc_id = uuid.uuid4()
    node_id = uuid.uuid4()

    node = TaxonomyNode(
        node_id=node_id,
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    async_session.add(node)

    doc = Document(doc_id=doc_id, title="Test Doc")
    async_session.add(doc)
    await async_session.commit()

    # When: path 필드 누락
    doc_tax = DocTaxonomy(
        doc_id=doc_id,
        node_id=node_id,
        version="1.0.0",
        # path=["AI", "RAG"],  # 누락
        confidence=0.95,
        hitl_required=False
    )
    async_session.add(doc_tax)

    # Then
    with pytest.raises((IntegrityError, TypeError)):
        await async_session.commit()
```

---

### 시나리오 5: node_id 쿼리 성능

**Given**:
- taxonomy_nodes 테이블에 1000개의 노드가 존재함
- `idx_taxonomy_nodes_canonical_path` GIN 인덱스가 존재함

**When**:
- 100번의 node_id 쿼리를 연속으로 실행함

**Then**:
- p95 latency가 10ms 미만임
- 쿼리 플랜에서 Index Scan이 사용됨

**테스트 코드**:
```python
# @TEST:SCHEMA-SYNC-001:SCENARIO-5
@pytest.mark.asyncio
async def test_scenario_5_node_id_query_performance(async_session):
    """
    Given: 1000개의 taxonomy nodes 존재
    When: 100번의 node_id 쿼리 실행
    Then: p95 latency < 10ms
    """
    from apps.api.database import TaxonomyNode
    from sqlalchemy import select, text
    import time

    # Given: 1000개 노드 생성
    nodes = [
        TaxonomyNode(
            label=f"Node{i}",
            canonical_path=["AI", f"Category{i}"],
            version="1.0.0",
            confidence=1.0
        )
        for i in range(1000)
    )
    async_session.add_all(nodes)
    await async_session.commit()

    # When: 100번 쿼리
    latencies = []
    for i in range(100):
        path = ["AI", f"Category{i}"]
        start = time.perf_counter()

        query = select(TaxonomyNode.node_id).where(
            TaxonomyNode.canonical_path == path
        )
        await async_session.execute(query)

        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

    # Then: p95 < 10ms
    p95_latency = sorted(latencies)[95]
    assert p95_latency < 10.0, f"p95 latency {p95_latency:.2f}ms > 10ms"

    # Verify: Index Scan 사용 확인 (PostgreSQL만)
    explain_query = text("""
        EXPLAIN (FORMAT JSON)
        SELECT node_id FROM taxonomy_nodes
        WHERE canonical_path = ARRAY['AI', 'Category0']
    """)
    result = await async_session.execute(explain_query)
    explain_json = result.scalar()

    # GIN 인덱스 사용 확인
    assert "Index Scan" in str(explain_json) or "Bitmap Index Scan" in str(explain_json)
```

---

### 시나리오 6: created_at 자동 설정

**Given**:
- DocTaxonomy 모델에 `created_at` 필드가 `server_default=NOW()` 설정됨

**When**:
- `created_at` 값을 명시하지 않고 DocTaxonomy INSERT함

**Then**:
- `created_at`이 현재 시각(UTC)으로 자동 설정됨
- Timezone-aware datetime 타입임

**테스트 코드**:
```python
# @TEST:SCHEMA-SYNC-001:SCENARIO-6
@pytest.mark.asyncio
async def test_scenario_6_created_at_auto_timestamp(async_session):
    """
    Given: created_at 필드에 server_default=NOW() 설정
    When: created_at 명시하지 않고 INSERT
    Then: 자동으로 현재 시각 설정
    """
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    from datetime import datetime, timezone
    import uuid

    # Given
    doc_id = uuid.uuid4()
    node_id = uuid.uuid4()

    node = TaxonomyNode(
        node_id=node_id,
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    async_session.add(node)

    doc = Document(doc_id=doc_id, title="Test Doc")
    async_session.add(doc)

    # When: created_at 명시하지 않음
    before_insert = datetime.now(timezone.utc)

    doc_tax = DocTaxonomy(
        doc_id=doc_id,
        node_id=node_id,
        version="1.0.0",
        path=["AI", "RAG"],
        confidence=0.95,
        hitl_required=False
        # created_at 누락 - server_default로 자동 설정되어야 함
    )
    async_session.add(doc_tax)
    await async_session.commit()

    after_insert = datetime.now(timezone.utc)

    # Then: created_at이 현재 시각으로 설정됨
    await async_session.refresh(doc_tax)
    assert doc_tax.created_at is not None
    assert before_insert <= doc_tax.created_at <= after_insert
    assert doc_tax.created_at.tzinfo is not None  # Timezone-aware
```

---

## 완료 조건 (Definition of Done)

### 필수 조건 (Must Have)

- [ ] **시나리오 1**: 정상 DocTaxonomy 생성 테스트 통과
- [ ] **시나리오 2**: taxonomy_path 매칭 실패 테스트 통과
- [ ] **시나리오 3**: Composite PK 충돌 테스트 통과
- [ ] **시나리오 4**: NOT NULL 제약 위반 테스트 통과
- [ ] **시나리오 5**: 성능 벤치마크 통과 (p95 < 10ms)
- [ ] **시나리오 6**: created_at 자동 설정 테스트 통과
- [ ] **Gate 1~4**: 모든 품질 게이트 통과
- [ ] 코드 커버리지 > 95% (database.py, job_orchestrator.py 해당 부분)

### 선택 조건 (Should Have)

- [ ] 성능 프로파일링 리포트 생성 (p50, p95, p99 latency)
- [ ] Staging 환경에서 72시간 무장애 운영
- [ ] 부하 테스트 (100 req/s for 10 minutes)

### 문서화 조건 (Documentation)

- [ ] 모든 테스트 시나리오가 문서화됨
- [ ] 실패 케이스 디버깅 가이드 작성됨
- [ ] 운영 환경 모니터링 대시보드 구성됨

---

## 검증 방법 (Verification Method)

### 자동화된 테스트 실행

```bash
# 전체 테스트 실행
pytest tests/unit/test_doc_taxonomy_model.py -v
pytest tests/unit/test_taxonomy_query.py -v
pytest tests/integration/test_job_orchestrator_taxonomy.py -v

# 시나리오별 테스트 실행
pytest tests/acceptance/test_schema_sync_scenarios.py::test_scenario_1 -v
pytest tests/acceptance/test_schema_sync_scenarios.py::test_scenario_2 -v
pytest tests/acceptance/test_schema_sync_scenarios.py::test_scenario_3 -v
pytest tests/acceptance/test_schema_sync_scenarios.py::test_scenario_4 -v
pytest tests/acceptance/test_schema_sync_scenarios.py::test_scenario_5 -v
pytest tests/acceptance/test_schema_sync_scenarios.py::test_scenario_6 -v

# 커버리지 리포트
pytest --cov=apps.api.database --cov=apps.ingestion.batch.job_orchestrator \
       --cov-report=html --cov-report=term
```

### 수동 검증

```sql
-- PostgreSQL에서 스키마 검증
\d doc_taxonomy

-- Composite PK 확인
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    a.attname AS column_name
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE c.conrelid = 'doc_taxonomy'::regclass
  AND c.contype = 'p';

-- NOT NULL 제약 확인
SELECT
    column_name,
    is_nullable,
    data_type
FROM information_schema.columns
WHERE table_name = 'doc_taxonomy'
ORDER BY ordinal_position;

-- 인덱스 확인
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'taxonomy_nodes';
```

---

## 롤백 기준 (Rollback Criteria)

다음 조건 중 하나라도 발생 시 즉시 롤백:

1. **시나리오 1 실패**: 정상 DocTaxonomy 생성 불가
2. **시나리오 5 실패**: p95 latency > 20ms (2배 초과)
3. **Production 에러율 > 5%**: 1시간 동안 지속
4. **데이터 손실**: 기존 DocTaxonomy 레코드 삭제 발견
5. **치명적 보안 취약점**: SQL Injection 등 발견

---

**최종 검토**: 이 수락 기준은 모든 시나리오를 Given-When-Then 형식으로 정의하고, 자동화된 테스트로 검증할 수 있도록 구체적인 테스트 코드를 포함합니다.
