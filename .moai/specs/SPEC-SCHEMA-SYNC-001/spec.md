---
id: SCHEMA-SYNC-001
version: 0.1.0
status: draft
created: 2025-10-12
updated: 2025-10-12
author: @Claude
priority: high
category: bugfix
labels:
  - database
  - schema
  - sqlalchemy
  - postgresql
depends_on: []
blocks: []
related_specs: []
scope:
  packages:
    - apps/api
    - apps/ingestion/batch
  files:
    - apps/api/database.py
    - apps/ingestion/batch/job_orchestrator.py
---

# @SPEC:SCHEMA-SYNC-001 DocTaxonomy Schema Synchronization

## HISTORY

### v0.1.0 (2025-10-12)
- **INITIAL**: SQLAlchemy 모델과 PostgreSQL 스키마 불일치 해결
- **AUTHOR**: @Claude
- **ISSUE**: `mapping_id` 필드가 SQLAlchemy 모델에만 존재, PostgreSQL에는 composite PK 사용
- **STRATEGY**: Q1은 DB 쿼리, Q2는 하드코딩 "1.0.0"

---

## Environment (환경 및 가정사항)

### 현재 환경

**PostgreSQL 스키마 (init.sql line 60-69)**:
```sql
CREATE TABLE IF NOT EXISTS doc_taxonomy (
    doc_id UUID NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES taxonomy_nodes(node_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    path TEXT[] NOT NULL,
    confidence FLOAT NOT NULL,
    hitl_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (doc_id, node_id, version)
);
```

**SQLAlchemy 모델 (database.py line 181-191)**:
```python
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    mapping_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[Optional[uuid.UUID]] = mapped_column(get_uuid_type(), ForeignKey('documents.doc_id'))
    node_id: Mapped[Optional[uuid.UUID]] = mapped_column(get_uuid_type(), ForeignKey('taxonomy_nodes.node_id'))
    version: Mapped[Optional[str]] = mapped_column(Text)
    path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    hitl_required: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
```

### 불일치 사항

1. **Primary Key 불일치**:
   - PostgreSQL: `(doc_id, node_id, version)` composite primary key
   - SQLAlchemy: `mapping_id` INTEGER autoincrement

2. **NOT NULL 제약 위반**:
   - PostgreSQL: `doc_id`, `node_id`, `version`, `path`, `confidence` 모두 NOT NULL
   - SQLAlchemy: 모든 필드가 `Optional[...]` 타입

3. **누락 필드**:
   - PostgreSQL: `created_at` TIMESTAMP 필드 존재
   - SQLAlchemy: `created_at` 필드 누락

### 가정사항

- PostgreSQL 스키마가 진실의 원천 (Source of Truth)
- 기존 데이터베이스에 저장된 데이터는 유지되어야 함
- job_orchestrator.py의 DocTaxonomy 생성 로직은 `node_id` 획득이 필요

---

## Assumptions (전제 조건)

### 기술적 전제

1. **SQLAlchemy 2.0** 사용 중 (Mapped, mapped_column)
2. **PostgreSQL 14+** 환경 (UUID, ARRAY, TIMESTAMP WITH TIME ZONE 지원)
3. **Alembic** 마이그레이션 도구 미사용 (직접 스키마 수정)
4. **taxonomy_nodes 테이블 존재** (node_id 참조를 위해)

### 데이터 전제

1. `taxonomy_nodes.canonical_path`는 TEXT[] 타입으로 저장되어 있음
2. `job_orchestrator.py`는 `taxonomy_path` (List[str])를 받아 DocTaxonomy 생성
3. 기존 코드에서 `node_id` 값은 직접 제공되지 않음 (DB 쿼리 필요)

### 비즈니스 전제

1. **version 필드는 초기 구현에서 "1.0.0" 하드코딩** (Q2 전략 채택)
2. **node_id는 taxonomy_nodes 테이블에서 쿼리** (Q1 전략 채택)
3. **backward compatibility 유지**: 기존 API 시그니처 변경 최소화

---

## Requirements (기능 요구사항)

### Ubiquitous Requirements (기본 요구사항)

- 시스템은 SQLAlchemy 모델과 PostgreSQL 스키마를 완전히 일치시켜야 한다
- 시스템은 composite primary key를 정확히 구현해야 한다
- 시스템은 모든 NOT NULL 제약을 준수해야 한다

### Event-driven Requirements (이벤트 기반)

- WHEN `job_orchestrator.py`가 DocTaxonomy 생성 시도하면, 시스템은 taxonomy_nodes에서 node_id를 쿼리해야 한다
- WHEN `taxonomy_path`가 제공되면, 시스템은 `canonical_path = taxonomy_path`인 노드를 검색해야 한다
- WHEN 매칭되는 노드가 없으면, 시스템은 명확한 에러 메시지와 함께 실패해야 한다

### State-driven Requirements (상태 기반)

- WHILE 초기 구현 단계(v0.1.0)일 때, 시스템은 version 필드를 "1.0.0"으로 하드코딩해야 한다
- WHILE `node_id` 쿼리 중일 때, 시스템은 DB 세션을 재사용해야 한다
- WHILE 데이터베이스 세션이 활성화되어 있을 때, 모든 필드는 NOT NULL 검증을 통과해야 한다

### Optional Features (선택적 기능)

- WHERE 향후 버전에서는, 시스템은 동적 version 관리를 지원할 수 있다
- WHERE taxonomy_path가 다중 매칭되면, 시스템은 가장 높은 confidence를 가진 노드를 선택할 수 있다

### Constraints (제약사항)

- SQLAlchemy 모델은 mapping_id 필드를 완전히 제거해야 한다
- 모든 필수 필드(doc_id, node_id, version, path, confidence)는 `Optional` 타입을 제거해야 한다
- `created_at` 필드는 `server_default=text('NOW()')`로 추가되어야 한다

---

## Specifications (상세 명세)

### S1. SQLAlchemy 모델 수정

**@CODE:SCHEMA-SYNC-001:MODEL**

**파일**: `apps/api/database.py`

**변경 전 (line 181-191)**:
```python
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    mapping_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[Optional[uuid.UUID]] = mapped_column(get_uuid_type(), ForeignKey('documents.doc_id'))
    node_id: Mapped[Optional[uuid.UUID]] = mapped_column(get_uuid_type(), ForeignKey('taxonomy_nodes.node_id'))
    version: Mapped[Optional[str]] = mapped_column(Text)
    path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    hitl_required: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
```

**변경 후**:
```python
class DocTaxonomy(Base):
    __tablename__ = "doc_taxonomy"

    # Composite Primary Key (matches PostgreSQL schema)
    doc_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), ForeignKey('documents.doc_id', ondelete='CASCADE'), primary_key=True)
    node_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), ForeignKey('taxonomy_nodes.node_id', ondelete='CASCADE'), primary_key=True)
    version: Mapped[str] = mapped_column(Text, primary_key=True)

    # Required fields (NOT NULL)
    path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional field (DEFAULT FALSE)
    hitl_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))

    # Timestamp field (missing in original model)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('NOW()'))
```

**검증 방법**:
```python
# @TEST:SCHEMA-SYNC-001:MODEL
async def test_doc_taxonomy_composite_key():
    doc_taxonomy = DocTaxonomy(
        doc_id=uuid.uuid4(),
        node_id=uuid.uuid4(),
        version="1.0.0",
        path=["AI", "RAG"],
        confidence=0.95
    )

    # Composite PK 검증
    assert hasattr(doc_taxonomy, '__table__')
    pk_columns = [col.name for col in doc_taxonomy.__table__.primary_key.columns]
    assert pk_columns == ['doc_id', 'node_id', 'version']

    # mapping_id 필드 부재 검증
    assert not hasattr(doc_taxonomy, 'mapping_id')
```

---

### S2. job_orchestrator.py 수정

**@CODE:SCHEMA-SYNC-001:QUERY**

**파일**: `apps/ingestion/batch/job_orchestrator.py`

**변경 전 (line 252-260)**:
```python
taxonomy_path = job_data.get("taxonomy_path")
if taxonomy_path:
    doc_taxonomy = DocTaxonomy(
        doc_id=doc_id,
        path=taxonomy_path,
        confidence=1.0
    )
    session.add(doc_taxonomy)
    logger.info(f"Assigned taxonomy path {taxonomy_path} to document {doc_id}")
```

**변경 후**:
```python
from sqlalchemy import select
from apps.api.database import TaxonomyNode

taxonomy_path = job_data.get("taxonomy_path")
if taxonomy_path:
    # Q1: Query node_id from taxonomy_nodes table
    query = select(TaxonomyNode.node_id).where(
        TaxonomyNode.canonical_path == taxonomy_path
    )
    result = await session.execute(query)
    node_id = result.scalar_one_or_none()

    if not node_id:
        logger.error(f"No taxonomy node found for path {taxonomy_path}")
        raise ValueError(f"Taxonomy path {taxonomy_path} does not exist in taxonomy_nodes table")

    # Q2: Hardcode version "1.0.0"
    doc_taxonomy = DocTaxonomy(
        doc_id=doc_id,
        node_id=node_id,
        version="1.0.0",
        path=taxonomy_path,
        confidence=1.0,
        hitl_required=False
    )
    session.add(doc_taxonomy)
    logger.info(f"Assigned taxonomy (node_id={node_id}, path={taxonomy_path}) to document {doc_id}")
```

**검증 방법**:
```python
# @TEST:SCHEMA-SYNC-001:INTEGRATION
async def test_job_orchestrator_taxonomy_mapping():
    # 1. Taxonomy node 생성
    node = TaxonomyNode(
        node_id=uuid.uuid4(),
        label="RAG",
        canonical_path=["AI", "RAG"],
        version="1.0.0",
        confidence=1.0
    )
    session.add(node)
    await session.commit()

    # 2. Document 업로드
    command = DocumentUploadCommandV1(
        file_name="test.pdf",
        file_content=b"test content",
        file_format="pdf",
        taxonomy_path=["AI", "RAG"]
    )

    job_id = await orchestrator.submit_job(command)

    # 3. DocTaxonomy 검증
    result = await session.execute(
        select(DocTaxonomy).where(DocTaxonomy.doc_id == doc_id)
    )
    doc_tax = result.scalar_one()

    assert doc_tax.node_id == node.node_id
    assert doc_tax.version == "1.0.0"
    assert doc_tax.path == ["AI", "RAG"]
    assert doc_tax.confidence == 1.0
```

---

### S3. 데이터 마이그레이션 전략

**@CODE:SCHEMA-SYNC-001:MIGRATION**

**기존 데이터 처리**:

1. **현재 상황 확인**:
   - `mapping_id` 컬럼이 PostgreSQL에 존재하는지 확인
   - 기존 DocTaxonomy 레코드 개수 확인

2. **마이그레이션 스크립트 (선택적)**:
```sql
-- 기존 doc_taxonomy 테이블에 mapping_id가 있다면 제거
-- (현재 PostgreSQL 스키마에는 없지만, 이전 버전에 있었을 경우)
ALTER TABLE doc_taxonomy DROP COLUMN IF EXISTS mapping_id;

-- created_at 컬럼 추가 (없는 경우)
ALTER TABLE doc_taxonomy ADD COLUMN IF NOT EXISTS
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;
```

3. **롤백 전략**:
   - SQLAlchemy 모델 변경은 코드 레벨이므로 git revert로 롤백
   - PostgreSQL 스키마는 이미 정합성이 있으므로 롤백 불필요

---

## Traceability (추적성 태그)

### TAG Chain

```
@SPEC:SCHEMA-SYNC-001
  ├─ @CODE:SCHEMA-SYNC-001:MODEL (database.py - DocTaxonomy 클래스)
  ├─ @CODE:SCHEMA-SYNC-001:QUERY (job_orchestrator.py - node_id 쿼리 로직)
  ├─ @CODE:SCHEMA-SYNC-001:MIGRATION (마이그레이션 SQL 스크립트)
  ├─ @TEST:SCHEMA-SYNC-001:MODEL (모델 검증 테스트)
  ├─ @TEST:SCHEMA-SYNC-001:INTEGRATION (E2E 통합 테스트)
  └─ @DOC:SCHEMA-SYNC-001:REPORT (스키마 동기화 완료 보고서)
```

---

## Decision Log (의사결정 기록)

### Q1: node_id 획득 방법

**질문**: job_orchestrator가 DocTaxonomy 생성 시 node_id를 어떻게 얻는가?

**옵션**:
1. taxonomy_path를 파라미터로 받아 taxonomy_nodes 테이블 쿼리
2. node_id를 직접 파라미터로 받도록 API 변경
3. 별도의 taxonomy 서비스 레이어 추가

**선택**: **옵션 1 (DB 쿼리)**

**이유**:
- taxonomy_path는 이미 job_data에 존재 (backward compatibility)
- canonical_path는 taxonomy_nodes에서 고유 식별자 역할
- API 시그니처 변경 불필요 (최소 변경 원칙)
- 쿼리 성능: indexed canonical_path 사용 (O(log n))

---

### Q2: version 필드 값 결정

**질문**: DocTaxonomy의 version 필드를 어떻게 채울 것인가?

**옵션**:
1. 하드코딩 "1.0.0" (초기 구현)
2. taxonomy_nodes에서 최신 버전 쿼리
3. 설정 파일에서 로드
4. 동적 버전 관리 시스템 구축

**선택**: **옵션 1 (하드코딩 "1.0.0")**

**이유**:
- 초기 구현 단계 (v0.1.0)에서는 단순성 우선
- 현재 taxonomy_nodes 샘플 데이터도 "1.0.0" 사용 중
- 향후 버전 관리 시스템 추가 시 쉽게 확장 가능
- 명시적 버전 사용으로 디버깅 용이

**향후 확장 계획** (v0.2.0):
```python
# Future enhancement
async def get_latest_taxonomy_version(session: AsyncSession) -> str:
    query = select(func.max(TaxonomyNode.version))
    result = await session.execute(query)
    return result.scalar_one_or_none() or "1.0.0"
```

---

## Risks & Mitigation (리스크 및 대응)

### R1. 기존 데이터 손실 리스크

**리스크**: SQLAlchemy 모델 변경 시 기존 DocTaxonomy 레코드가 손실될 수 있음

**영향도**: Medium

**대응 방안**:
1. **사전 백업**: 배포 전 `pg_dump doc_taxonomy` 실행
2. **점진적 롤아웃**: staging 환경에서 먼저 검증
3. **롤백 계획**: git revert + 백업 복원 절차 준비

---

### R2. taxonomy_path 매칭 실패

**리스크**: job_orchestrator가 제공한 taxonomy_path가 taxonomy_nodes에 없을 경우

**영향도**: High (문서 업로드 실패)

**대응 방안**:
1. **명확한 에러 메시지**: `ValueError` with path details
2. **로깅 강화**: `logger.error(f"Missing taxonomy path: {taxonomy_path}")`
3. **프리로딩 검증**: 애플리케이션 시작 시 필수 taxonomy 경로 확인

```python
# @CODE:SCHEMA-SYNC-001:VALIDATION
async def validate_taxonomy_preload(session: AsyncSession):
    required_paths = [
        ["AI", "RAG"],
        ["AI", "ML"],
        ["AI", "Taxonomy"]
    ]

    for path in required_paths:
        query = select(TaxonomyNode.node_id).where(
            TaxonomyNode.canonical_path == path
        )
        result = await session.execute(query)
        if not result.scalar_one_or_none():
            raise RuntimeError(f"Required taxonomy path {path} not found in database")
```

---

### R3. 성능 저하 (추가 DB 쿼리)

**리스크**: 매 DocTaxonomy 생성 시 taxonomy_nodes 쿼리로 인한 latency 증가

**영향도**: Low

**대응 방안**:
1. **인덱스 활용**: `idx_taxonomy_nodes_canonical_path` GIN 인덱스 (이미 존재)
2. **캐싱 고려** (v0.2.0): 자주 사용되는 taxonomy_path → node_id 매핑 캐시
3. **배치 처리 최적화**: 동일 taxonomy_path 문서는 한 번만 쿼리

---

## Acceptance Criteria (수락 기준)

### AC1. 모델 정합성

- [ ] DocTaxonomy 모델에 `mapping_id` 필드가 없음
- [ ] Composite primary key (doc_id, node_id, version) 구현됨
- [ ] 모든 NOT NULL 필드가 `Optional` 타입 제거됨
- [ ] `created_at` 필드가 추가됨

### AC2. 기능 동작

- [ ] job_orchestrator가 taxonomy_path로 node_id를 쿼리함
- [ ] 존재하지 않는 taxonomy_path에 대해 명확한 에러 발생
- [ ] DocTaxonomy 생성 시 version이 "1.0.0"으로 설정됨
- [ ] 기존 문서 업로드 API가 정상 동작함

### AC3. 테스트 커버리지

- [ ] 모델 필드 검증 테스트 작성됨
- [ ] node_id 쿼리 로직 단위 테스트 작성됨
- [ ] E2E 통합 테스트 작성됨
- [ ] taxonomy_path 누락 케이스 테스트 작성됨

### AC4. 문서화

- [ ] 스키마 변경사항이 문서화됨
- [ ] Q1, Q2 의사결정이 명확히 기록됨
- [ ] 향후 확장 계획이 명시됨

---

**최종 검토**: 이 SPEC은 SQLAlchemy 모델과 PostgreSQL 스키마의 완전한 동기화를 보장하며, Q1(DB 쿼리), Q2(하드코딩)의 실용적 전략을 통해 backward compatibility를 유지합니다.
