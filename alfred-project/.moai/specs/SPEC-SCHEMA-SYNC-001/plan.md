---
id: SCHEMA-SYNC-001-PLAN
version: 0.1.0
parent_spec: SCHEMA-SYNC-001
created: 2025-10-12
updated: 2025-10-12
---

# @SPEC:SCHEMA-SYNC-001 Implementation Plan

## 개요

SQLAlchemy 모델과 PostgreSQL 스키마 동기화를 위한 구현 계획입니다. 우선순위 기반의 마일스톤으로 구성되며, 각 단계는 독립적으로 검증 가능합니다.

---

## 우선순위 기반 마일스톤

### 1차 목표: SQLAlchemy 모델 수정 (Priority: Critical)

**목표**: DocTaxonomy 모델을 PostgreSQL 스키마와 완전히 일치시킵니다.

**작업 항목**:

1. **mapping_id 필드 제거**
   - `apps/api/database.py` line 184 삭제
   - Composite PK로 대체

2. **Composite Primary Key 구현**
   - `doc_id`, `node_id`, `version` 필드에 `primary_key=True` 추가
   - Foreign key constraints 추가: `ondelete='CASCADE'`

3. **NOT NULL 제약 추가**
   - `Optional[...]` 타입을 실제 타입으로 변경
   - `nullable=False` 명시

4. **created_at 필드 추가**
   - `DateTime(timezone=True)` 타입 사용
   - `server_default=text('NOW()')` 설정

**검증 방법**:
```python
# Unit Test
@pytest.mark.asyncio
async def test_doc_taxonomy_model_schema():
    from apps.api.database import DocTaxonomy
    import inspect

    # mapping_id 필드 부재 확인
    assert 'mapping_id' not in [c.name for c in DocTaxonomy.__table__.columns]

    # Composite PK 확인
    pk_cols = [c.name for c in DocTaxonomy.__table__.primary_key.columns]
    assert set(pk_cols) == {'doc_id', 'node_id', 'version'}

    # created_at 필드 존재 확인
    assert 'created_at' in [c.name for c in DocTaxonomy.__table__.columns]

    # NOT NULL 제약 확인
    for col_name in ['doc_id', 'node_id', 'version', 'path', 'confidence']:
        col = DocTaxonomy.__table__.columns[col_name]
        assert not col.nullable, f"{col_name} should be NOT NULL"
```

**완료 조건**:
- [ ] SQLAlchemy 모델이 PostgreSQL 스키마와 100% 일치
- [ ] `mapping_id` 필드가 완전히 제거됨
- [ ] Composite PK가 정확히 구현됨
- [ ] 모든 필드의 nullable 상태가 스키마와 동일

---

### 2차 목표: job_orchestrator.py 수정 (Priority: High)

**목표**: DocTaxonomy 생성 로직에 node_id 쿼리 추가 및 version 하드코딩을 구현합니다.

**작업 항목**:

1. **TaxonomyNode import 추가**
   - `job_orchestrator.py` 상단에 import 구문 추가
   ```python
   from apps.api.database import TaxonomyNode
   from sqlalchemy import select
   ```

2. **node_id 쿼리 로직 구현**
   - `_process_document()` 메서드 내 taxonomy_path 처리 부분 수정 (line 252-260)
   - `canonical_path = taxonomy_path` 조건으로 쿼리
   - 매칭 실패 시 명확한 에러 처리

3. **version 하드코딩**
   - DocTaxonomy 생성 시 `version="1.0.0"` 명시

4. **로깅 강화**
   - node_id 쿼리 성공/실패 로그 추가
   - taxonomy_path와 node_id 매핑 정보 기록

**구현 코드**:
```python
# apps/ingestion/batch/job_orchestrator.py

# Before (line 252-260)
taxonomy_path = job_data.get("taxonomy_path")
if taxonomy_path:
    doc_taxonomy = DocTaxonomy(
        doc_id=doc_id,
        path=taxonomy_path,
        confidence=1.0
    )
    session.add(doc_taxonomy)
    logger.info(f"Assigned taxonomy path {taxonomy_path} to document {doc_id}")

# After
taxonomy_path = job_data.get("taxonomy_path")
if taxonomy_path:
    # Q1: Query node_id from taxonomy_nodes
    query = select(TaxonomyNode.node_id).where(
        TaxonomyNode.canonical_path == taxonomy_path
    )
    result = await session.execute(query)
    node_id = result.scalar_one_or_none()

    if not node_id:
        error_msg = f"Taxonomy path {taxonomy_path} not found in taxonomy_nodes table"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Q2: Hardcode version
    doc_taxonomy = DocTaxonomy(
        doc_id=doc_id,
        node_id=node_id,
        version="1.0.0",
        path=taxonomy_path,
        confidence=1.0,
        hitl_required=False
    )
    session.add(doc_taxonomy)
    logger.info(
        f"Assigned taxonomy to document {doc_id}: "
        f"node_id={node_id}, path={taxonomy_path}, version=1.0.0"
    )
```

**검증 방법**:
```python
# Integration Test
@pytest.mark.asyncio
async def test_job_orchestrator_taxonomy_mapping(async_session):
    from apps.api.database import TaxonomyNode, Document, DocTaxonomy
    import uuid

    # 1. Setup: Taxonomy node 생성
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

    # 2. Execute: Document 업로드 with taxonomy_path
    from apps.ingestion.batch.job_orchestrator import JobOrchestrator
    orchestrator = JobOrchestrator()

    job_data = {
        "file_name": "test.pdf",
        "file_content_hex": b"test content".hex(),
        "file_format": "pdf",
        "taxonomy_path": ["AI", "RAG"],
        "source_url": "https://test.com",
        "metadata": {}
    }

    event = await orchestrator._process_document("cmd-001", job_data)

    # 3. Verify: DocTaxonomy 검증
    query = select(DocTaxonomy).where(DocTaxonomy.doc_id == event.document_id)
    result = await async_session.execute(query)
    doc_tax = result.scalar_one()

    assert doc_tax.node_id == node_id
    assert doc_tax.version == "1.0.0"
    assert doc_tax.path == ["AI", "RAG"]
    assert doc_tax.confidence == 1.0
```

**완료 조건**:
- [ ] taxonomy_path로 node_id를 정확히 쿼리
- [ ] 매칭 실패 시 명확한 에러 발생
- [ ] version이 "1.0.0"으로 설정됨
- [ ] 로그에 node_id 매핑 정보 포함

---

### 3차 목표: 테스트 구현 (Priority: High)

**목표**: 모델 검증, 쿼리 로직, E2E 통합 테스트를 작성합니다.

**작업 항목**:

1. **모델 스키마 테스트**
   - 파일: `tests/unit/test_doc_taxonomy_model.py`
   - Composite PK 검증
   - NOT NULL 제약 검증
   - created_at 필드 검증

2. **node_id 쿼리 로직 테스트**
   - 파일: `tests/unit/test_taxonomy_query.py`
   - 정상 매칭 케이스
   - 매칭 실패 케이스
   - 다중 버전 존재 시 동작

3. **E2E 통합 테스트**
   - 파일: `tests/integration/test_job_orchestrator_taxonomy.py`
   - 전체 문서 업로드 플로우
   - DocTaxonomy 생성 검증
   - 에러 핸들링 검증

**테스트 커버리지 목표**:
- [ ] `DocTaxonomy` 모델: 100% line coverage
- [ ] `job_orchestrator.py` taxonomy 관련 로직: 100%
- [ ] 에러 케이스 포함 모든 경로 테스트

---

### 4차 목표: 에러 핸들링 및 로깅 강화 (Priority: Medium)

**목표**: taxonomy_path 매칭 실패 시 명확한 진단 정보를 제공합니다.

**작업 항목**:

1. **Custom Exception 정의**
   - 파일: `apps/core/exceptions.py`
   ```python
   class TaxonomyNodeNotFoundError(ValueError):
       def __init__(self, taxonomy_path: List[str], available_paths: List[List[str]]):
           self.taxonomy_path = taxonomy_path
           self.available_paths = available_paths
           super().__init__(
               f"Taxonomy path {taxonomy_path} not found. "
               f"Available paths: {available_paths[:5]}"
           )
   ```

2. **진단 정보 로깅**
   - node_id 쿼리 실패 시 taxonomy_nodes 테이블의 상위 5개 경로 출력
   - 유사한 경로 추천 (Levenshtein distance)

3. **Graceful degradation**
   - taxonomy_path가 없을 경우 기본 경로 사용 (선택적)
   - 관리자 알림 전송 (Slack webhook)

**완료 조건**:
- [ ] Custom exception으로 명확한 에러 메시지
- [ ] 로그에 진단 정보 포함
- [ ] 운영 환경에서 디버깅 가능한 정보 제공

---

### 5차 목표: 성능 최적화 (Priority: Low)

**목표**: node_id 쿼리로 인한 latency를 최소화합니다.

**작업 항목**:

1. **인덱스 검증**
   - `idx_taxonomy_nodes_canonical_path` GIN 인덱스 활용 확인
   - EXPLAIN ANALYZE로 쿼리 플랜 검증

2. **캐싱 레이어 추가 (선택적)**
   - 파일: `apps/core/taxonomy_cache.py`
   - LRU 캐시 사용 (최대 1000개 엔트리)
   - TTL 1시간 설정

3. **배치 처리 최적화**
   - 동일 taxonomy_path 문서는 한 번만 쿼리
   - 결과 재사용

**캐싱 구현 예시** (향후 확장):
```python
# apps/core/taxonomy_cache.py
from functools import lru_cache
from typing import List, Optional
import uuid

@lru_cache(maxsize=1000)
def get_taxonomy_node_id(
    canonical_path_tuple: tuple,  # hashable for lru_cache
    version: str = "1.0.0"
) -> Optional[uuid.UUID]:
    """
    Cached taxonomy node_id lookup

    Args:
        canonical_path_tuple: Tuple form of canonical_path (e.g., ("AI", "RAG"))
        version: Taxonomy version

    Returns:
        node_id or None
    """
    # Implementation with Redis or in-memory cache
    pass
```

**완료 조건**:
- [ ] node_id 쿼리 평균 latency < 5ms
- [ ] GIN 인덱스 활용 확인 (EXPLAIN 결과)
- [ ] 캐싱 적중률 > 80% (프로덕션 환경)

---

## 기술적 접근 방법

### 아키텍처 설계

**계층 분리**:
```
┌─────────────────────────────────────────┐
│  job_orchestrator.py (Business Logic)   │
│  - Document processing orchestration     │
│  - Taxonomy path → node_id resolution   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  database.py (Data Layer)                │
│  - SQLAlchemy models (DocTaxonomy)       │
│  - Query execution                        │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  PostgreSQL (Data Storage)               │
│  - doc_taxonomy (composite PK)           │
│  - taxonomy_nodes (canonical_path index) │
└─────────────────────────────────────────┘
```

**쿼리 최적화 전략**:
1. **GIN 인덱스 활용**: `canonical_path` ARRAY 타입에 GIN 인덱스 사용
2. **세션 재사용**: job_orchestrator 내 기존 DB 세션 활용
3. **트랜잭션 경계**: Document + DocTaxonomy를 단일 트랜잭션으로 처리

---

## 리스크 관리

### 리스크 매트릭스

| 리스크                     | 영향도 | 발생 확률 | 완화 전략                          |
|----------------------------|--------|-----------|-----------------------------------|
| 기존 데이터 손실           | High   | Low       | 배포 전 pg_dump 백업               |
| taxonomy_path 매칭 실패    | High   | Medium    | Custom exception + 진단 로그       |
| node_id 쿼리 성능 저하     | Medium | Low       | GIN 인덱스 + 캐싱                  |
| 롤백 필요 시 다운타임      | Low    | Very Low  | git revert + 무중단 배포           |

### 롤백 계획

**단계별 롤백**:
1. **코드 롤백**: `git revert` + 즉시 배포
2. **데이터 롤백**: PostgreSQL 백업 복원 (최대 5분 소요)
3. **검증**: smoke test 실행

**롤백 트리거**:
- DocTaxonomy INSERT 에러율 > 5%
- node_id 쿼리 타임아웃 발생
- 프로덕션 환경에서 치명적 버그 발견

---

## 배포 전략

### 단계적 롤아웃

**Phase 1: Staging 환경** (1일차)
- SQLAlchemy 모델 변경 배포
- job_orchestrator 로직 변경 배포
- 통합 테스트 실행
- 성능 벤치마크 (baseline: 현재 latency)

**Phase 2: Canary 배포** (2일차)
- Production 트래픽의 10%만 새 로직 사용
- 에러율 모니터링 (threshold: 1%)
- 정상 동작 시 50% → 100% 점진적 확대

**Phase 3: Full Rollout** (3일차)
- 전체 트래픽 새 로직 적용
- 24시간 모니터링
- 이상 없으면 배포 완료 선언

### 모니터링 지표

**Success Metrics**:
- DocTaxonomy INSERT 성공률: > 99%
- node_id 쿼리 latency: < 10ms (p95)
- taxonomy_path 매칭 성공률: > 95%

**Failure Metrics**:
- `TaxonomyNodeNotFoundError` 발생 횟수
- DB 연결 실패 횟수
- 트랜잭션 롤백 횟수

---

## 의존성 및 순서

### 작업 순서 (Critical Path)

```
1차 목표 (Model 수정)
    │
    ├─ mapping_id 제거
    ├─ Composite PK 추가
    ├─ NOT NULL 제약 추가
    └─ created_at 필드 추가
    │
    ▼
2차 목표 (Orchestrator 수정)
    │
    ├─ TaxonomyNode import
    ├─ node_id 쿼리 로직
    └─ version 하드코딩
    │
    ▼
3차 목표 (테스트 구현)
    │
    ├─ Unit tests
    ├─ Integration tests
    └─ E2E tests
    │
    ▼
4차 목표 (에러 핸들링)
    │
    └─ Custom exceptions + Logging
    │
    ▼
5차 목표 (성능 최적화) - 선택적
    │
    └─ 캐싱 + 인덱스 튜닝
```

### 병렬 작업 가능 영역

- 1차 목표와 3차 목표의 단위 테스트는 병렬 작업 가능
- 4차 목표는 2차 목표 완료 후 독립적으로 진행 가능
- 5차 목표는 1~3차 목표 완료 후 언제든지 시작 가능

---

## 완료 정의 (Definition of Done)

### 필수 조건

- [ ] SQLAlchemy 모델이 PostgreSQL 스키마와 100% 일치
- [ ] job_orchestrator가 taxonomy_path로 node_id를 정확히 쿼리
- [ ] 모든 테스트가 통과 (unit + integration + E2E)
- [ ] 에러 핸들링이 명확하고 디버깅 가능
- [ ] Staging 환경에서 72시간 무장애 운영
- [ ] 코드 리뷰 완료 (최소 2명 승인)

### 선택 조건 (Nice-to-have)

- [ ] 캐싱 레이어 구현 (성능 개선)
- [ ] 관리자 알림 시스템 통합
- [ ] 자동화된 마이그레이션 스크립트

---

## 다음 단계

이 SPEC 완료 후 다음 작업으로 이어집니다:

1. **SPEC-TAXONOMY-VERSION-001**: 동적 버전 관리 시스템 구축
2. **SPEC-TAXONOMY-CACHE-001**: 고성능 taxonomy 캐싱 레이어
3. **SPEC-TAXONOMY-MIGRATION-001**: 자동화된 taxonomy 마이그레이션 도구

---

**최종 검토**: 이 구현 계획은 우선순위 기반의 점진적 접근을 통해 리스크를 최소화하고, 각 단계에서 명확한 검증 기준을 제공합니다.
