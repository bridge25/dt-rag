---
id: CASEBANK-UNIFY-001
version: 0.0.1
status: draft
created: 2025-11-09
updated: 2025-11-09
author: @a
priority: critical
category: bugfix
labels:
  - database
  - schema
  - casebank
  - consolidation
depends_on:
  - CASEBANK-002
related_specs:
  - SCHEMA-SYNC-001
  - CONSOLIDATION-001
  - REFLECTION-001
scope:
  packages:
    - apps/api
    - apps/orchestration/src
    - tests/unit
    - tests/integration
  files:
    - apps/api/database.py
    - apps/orchestration/src/consolidation_policy.py
    - apps/orchestration/src/reflection_engine.py
    - tests/unit/test_consolidation_policy.py
    - tests/integration/test_casebank_crud.py
    - alembic/versions/0008_taxonomy_schema.py
---

# SPEC-CASEBANK-UNIFY-001: CaseBank 스키마 통합 및 필드 정의 표준화

## HISTORY

### v0.0.1 (2025-11-09)
- **INITIAL**: SPEC 초안 작성
- **AUTHOR**: @a
- **SECTIONS**: Environment, Assumptions, Requirements, Specifications 전체
- **CONTEXT**: Production 모델과 Test 모델 간 필드 불일치로 인한 런타임 충돌 해결

---

## @SPEC:CASEBANK-UNIFY-001 개요

### 목적

Production 환경의 `CaseBankEntry` 모델과 Test 환경의 모델 간 스키마 불일치를 해결하고, consolidation/reflection 엔진에서 발생하는 AttributeError 런타임 크래시를 제거합니다.

### 배경

현재 시스템은 다음과 같은 문제를 가지고 있습니다:

1. **Production 모델 누락 필드** (apps/api/database.py):
   - `query_vector`: 유사도 계산에 필요하지만 현재 누락됨
   - `usage_count`: 쿼리 매칭 빈도 추적용 필드 누락 (기본값: 0)
   - `last_used_at`: 비활성 케이스 추적용 타임스탬프 누락

2. **필드명 불일치**:
   - Test 모델: `quality_score` ↔ Production 모델: `quality`
   - Migration/Reflection: `response_text` ↔ Production 모델: `answer`

3. **런타임 크래시**:
   - `consolidation_policy.py:108, 155, 241` - `AttributeError: 'CaseBankEntry' object has no attribute 'query_vector'`
   - `reflection_engine.py:195` - `AttributeError: 'CaseBankEntry' object has no attribute 'response_text'`

### 성공 기준

- ✅ Production 모델에 3개 필수 필드 추가 완료
- ✅ 필드명 불일치 8개 파일에서 모두 해결
- ✅ consolidation_policy.py 런타임 크래시 0건
- ✅ reflection_engine.py 런타임 크래시 0건
- ✅ 모든 unit/integration 테스트 통과
- ✅ Alembic migration 정상 실행 및 rollback 가능

---

## Environment (환경)

### 시스템 환경

- **데이터베이스**: PostgreSQL 15+ (pgvector extension 활성화)
- **ORM**: SQLAlchemy 2.0 (async mode)
- **Migration**: Alembic
- **Python 버전**: 3.11+
- **테스트 프레임워크**: pytest, pytest-asyncio

### 관련 컴포넌트

| 컴포넌트 | 파일 경로 | 역할 |
|---------|----------|------|
| Production Model | `apps/api/database.py` | CaseBankEntry 스키마 정의 |
| Consolidation Engine | `apps/orchestration/src/consolidation_policy.py` | 케이스 병합 로직 (query_vector 사용) |
| Reflection Engine | `apps/orchestration/src/reflection_engine.py` | 품질 평가 로직 (answer 필드 사용) |
| Unit Tests | `tests/unit/test_consolidation_policy.py` | Consolidation 로직 검증 |
| Integration Tests | `tests/integration/test_casebank_crud.py` | CRUD 작업 E2E 검증 |
| Migration | `alembic/versions/0008_taxonomy_schema.py` | 기존 스키마 마이그레이션 |

### 종속성

- **선행 완료 필수**: @SPEC:CASEBANK-002 (CaseBank 기본 CRUD 구현)
- **관련 SPEC**: @SPEC:SCHEMA-SYNC-001, @SPEC:CONSOLIDATION-001, @SPEC:REFLECTION-001

---

## Assumptions (가정)

### 기술적 가정

1. **pgvector 확장 사용 가능**:
   - Production DB에 pgvector extension이 이미 설치되어 있음
   - Vector 타입을 사용한 유사도 검색이 가능함

2. **Embedding 차원 고정**:
   - OpenAI `text-embedding-ada-002` 모델 사용 (1536 차원)
   - 모든 query_vector는 1536 크기의 float 배열

3. **기존 데이터 호환성**:
   - 기존 CaseBankEntry 레코드는 새 필드에 NULL 허용
   - Migration 실행 시 기본값 자동 적용 (`usage_count=0`, `last_used_at=NULL`, `query_vector=NULL`)

4. **Backward Compatibility**:
   - 새 필드 추가는 기존 코드 동작에 영향을 주지 않음
   - Optional 필드로 설계하여 점진적 마이그레이션 가능

### 비즈니스 가정

1. **사용 빈도 추적 필요성**:
   - `usage_count`를 통해 인기 케이스 분석 가능
   - 향후 캐싱 전략 및 우선순위 결정에 활용

2. **비활성 케이스 관리**:
   - `last_used_at`을 기반으로 90일 이상 미사용 케이스 아카이빙 가능
   - 스토리지 최적화 전략의 기반 데이터

3. **품질 점수 통합**:
   - `quality_score` → `quality`로 통일하여 일관성 확보
   - 향후 A/B 테스트 및 품질 모니터링에 활용

---

## Requirements (요구사항)

### @REQ:CASEBANK-UNIFY-PROD-FIELDS-001 Production 모델 필드 추가

**WHEN** Production 환경에서 CaseBankEntry가 생성/조회될 때, **the system shall** 다음 3개 필드를 제공해야 한다:

1. **query_vector**:
   - 타입: `Mapped[Optional[List[float]]]`
   - 용도: 유사도 계산용 임베딩 벡터
   - 제약: pgvector 타입 (1536 차원), NULL 허용

2. **usage_count**:
   - 타입: `Mapped[int]`
   - 용도: 쿼리 매칭 횟수 추적
   - 제약: 기본값 0, NOT NULL

3. **last_used_at**:
   - 타입: `Mapped[Optional[datetime]]`
   - 용도: 마지막 사용 시각 기록
   - 제약: DateTime 타입, NULL 허용

**파일**: `apps/api/database.py`

---

### @REQ:CASEBANK-UNIFY-FIELD-RENAME-001 필드명 통일

**WHEN** 모든 CaseBankEntry 관련 코드가 실행될 때, **the system shall** 다음 필드명을 사용해야 한다:

1. **quality_score → quality**:
   - 영향 파일: `tests/unit/test_consolidation_policy.py`, `tests/integration/test_casebank_metadata.py`
   - 변경 위치: 모든 테스트 픽스처 및 assertion

2. **response_text → answer**:
   - 영향 파일: `apps/orchestration/src/reflection_engine.py`, `alembic/versions/0008_taxonomy_schema.py`
   - 변경 위치: 모든 필드 참조 및 SQL 쿼리

**제약**: 필드명 변경 후 모든 unit/integration 테스트가 통과해야 한다.

---

### @REQ:CASEBANK-UNIFY-CRASH-FIX-001 런타임 크래시 제거

**WHEN** consolidation_policy.py 또는 reflection_engine.py가 실행될 때, **the system shall** AttributeError를 발생시키지 않아야 한다.

**수정 위치**:

1. **consolidation_policy.py**:
   - Line 108: `entry.query_vector` 접근 전 필드 존재 검증
   - Line 155: `entry.usage_count` 접근 전 기본값 0 처리
   - Line 241: `entry.last_used_at` 접근 전 NULL 허용 처리

2. **reflection_engine.py**:
   - Line 195: `entry.response_text` → `entry.answer`로 변경

**검증 방법**: pytest 실행 시 모든 테스트 케이스 통과 (0 failures, 0 errors)

---

### @REQ:CASEBANK-UNIFY-MIGRATION-001 데이터베이스 마이그레이션

**WHEN** `alembic upgrade head`가 실행될 때, **the system shall** 다음 작업을 수행해야 한다:

1. **새 필드 추가**:
   - `ALTER TABLE casebank_entry ADD COLUMN query_vector vector(1536)`
   - `ALTER TABLE casebank_entry ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 0`
   - `ALTER TABLE casebank_entry ADD COLUMN last_used_at TIMESTAMP`

2. **필드명 변경**:
   - `ALTER TABLE casebank_entry RENAME COLUMN response_text TO answer` (기존 migration 수정)

3. **인덱스 생성**:
   - `CREATE INDEX idx_casebank_usage_count ON casebank_entry(usage_count DESC)`
   - `CREATE INDEX idx_casebank_last_used ON casebank_entry(last_used_at DESC)`

**제약**:
- Migration은 멱등성을 보장해야 함 (여러 번 실행 시 에러 없음)
- Rollback(`alembic downgrade -1`) 실행 시 정상 복구되어야 함

---

### @REQ:CASEBANK-UNIFY-TEST-UPDATE-001 테스트 코드 동기화

**WHEN** 테스트 스위트가 실행될 때, **the system shall** 업데이트된 스키마를 반영해야 한다.

**업데이트 대상**:

1. **tests/unit/test_consolidation_policy.py**:
   - 테스트 픽스처에 `query_vector`, `usage_count`, `last_used_at` 추가
   - `quality_score` → `quality` 변경

2. **tests/integration/test_casebank_crud.py**:
   - CRUD 작업 테스트에 새 필드 검증 추가
   - `answer` 필드 사용 확인

3. **tests/integration/test_casebank_metadata.py**:
   - Metadata 검증 로직에 새 필드 포함

**검증 기준**: 전체 테스트 coverage 85% 이상 유지

---

## Specifications (상세 설계)

### @CODE:CASEBANK-UNIFY-PROD-MODEL-001 Production 모델 업데이트

**파일**: `apps/api/database.py`

**변경 내용**:

```python
class CaseBankEntry(Base):
    __tablename__ = "casebank_entry"

    # 기존 필드들...
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)  # response_text에서 변경
    quality: Mapped[float] = mapped_column(Float, nullable=False)  # quality_score에서 변경

    # 🔥 신규 필드 추가
    query_vector: Mapped[Optional[List[float]]] = mapped_column(
        Vector(1536) if PGVECTOR_AVAILABLE else ArrayType,
        nullable=True,
        comment="Query embedding vector for similarity search"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text('0'),
        comment="Number of times this case was matched"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this case was used in a query"
    )
```

**타입 안전성**:
- `Vector(1536)` 타입은 pgvector extension 활성화 시에만 사용
- Fallback으로 `ArrayType` 사용 (pgvector 미사용 환경 대응)

---

### @CODE:CASEBANK-UNIFY-CONSOLIDATION-FIX-001 Consolidation 엔진 수정

**파일**: `apps/orchestration/src/consolidation_policy.py`

**변경 위치 1**: Line 108 (query_vector 접근)

```python
# 🔥 Before
similarity = calculate_similarity(entry.query_vector, candidate.query_vector)

# ✅ After
if entry.query_vector and candidate.query_vector:
    similarity = calculate_similarity(entry.query_vector, candidate.query_vector)
else:
    similarity = 0.0  # Fallback: no vector available
```

**변경 위치 2**: Line 155 (usage_count 접근)

```python
# 🔥 Before
if entry.usage_count > threshold:

# ✅ After
usage = getattr(entry, 'usage_count', 0)
if usage > threshold:
```

**변경 위치 3**: Line 241 (last_used_at 접근)

```python
# 🔥 Before
if (datetime.now() - entry.last_used_at).days > 90:

# ✅ After
last_used = getattr(entry, 'last_used_at', None)
if last_used and (datetime.now(timezone.utc) - last_used).days > 90:
```

---

### @CODE:CASEBANK-UNIFY-REFLECTION-FIX-001 Reflection 엔진 수정

**파일**: `apps/orchestration/src/reflection_engine.py`

**변경 위치**: Line 195 (response_text → answer)

```python
# 🔥 Before
reflection_data = {
    "query": entry.query,
    "response": entry.response_text,  # ❌ AttributeError
    "quality": entry.quality
}

# ✅ After
reflection_data = {
    "query": entry.query,
    "response": entry.answer,  # ✅ Correct field name
    "quality": entry.quality
}
```

---

### @CODE:CASEBANK-UNIFY-MIGRATION-001 Alembic Migration 생성

**새 Migration 파일**: `alembic/versions/0009_add_casebank_fields.py`

```python
"""Add query_vector, usage_count, last_used_at to casebank_entry

Revision ID: 0009_add_casebank_fields
Revises: 0008_taxonomy_schema
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0009_add_casebank_fields'
down_revision = '0008_taxonomy_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('casebank_entry',
        sa.Column('query_vector', postgresql.ARRAY(sa.Float()), nullable=True,
                  comment='Query embedding vector for similarity search'))
    op.add_column('casebank_entry',
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of times this case was matched'))
    op.add_column('casebank_entry',
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Last time this case was used in a query'))

    # Create indexes for performance
    op.create_index('idx_casebank_usage_count', 'casebank_entry', ['usage_count'],
                    postgresql_using='btree', postgresql_order_by='DESC')
    op.create_index('idx_casebank_last_used', 'casebank_entry', ['last_used_at'],
                    postgresql_using='btree', postgresql_order_by='DESC')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_casebank_last_used', table_name='casebank_entry')
    op.drop_index('idx_casebank_usage_count', table_name='casebank_entry')

    # Drop columns
    op.drop_column('casebank_entry', 'last_used_at')
    op.drop_column('casebank_entry', 'usage_count')
    op.drop_column('casebank_entry', 'query_vector')
```

**기존 Migration 수정**: `alembic/versions/0008_taxonomy_schema.py`

```python
# 🔥 Before (Line 45)
sa.Column('response_text', sa.Text(), nullable=False)

# ✅ After (Line 45)
sa.Column('answer', sa.Text(), nullable=False)
```

---

### @TEST:CASEBANK-UNIFY-UNIT-001 Unit 테스트 업데이트

**파일**: `tests/unit/test_consolidation_policy.py`

**변경 내용**:

```python
# 🔥 Before
@pytest.fixture
def sample_entry():
    return CaseBankEntry(
        query="test query",
        answer="test answer",
        quality_score=0.95  # ❌ Old field name
    )

# ✅ After
@pytest.fixture
def sample_entry():
    return CaseBankEntry(
        query="test query",
        answer="test answer",
        quality=0.95,  # ✅ Correct field name
        query_vector=[0.1] * 1536,  # ✅ New field
        usage_count=0,  # ✅ New field
        last_used_at=None  # ✅ New field
    )
```

---

### @TEST:CASEBANK-UNIFY-INTEGRATION-001 Integration 테스트 업데이트

**파일**: `tests/integration/test_casebank_crud.py`

**추가 테스트 케이스**:

```python
@pytest.mark.asyncio
async def test_casebank_entry_new_fields(async_session: AsyncSession):
    """Test new fields (query_vector, usage_count, last_used_at) are properly stored"""
    from datetime import datetime, timezone

    # Arrange
    entry = CaseBankEntry(
        taxonomy_id=1,
        query="test query",
        answer="test answer",
        quality=0.9,
        query_vector=[0.5] * 1536,
        usage_count=5,
        last_used_at=datetime.now(timezone.utc)
    )

    # Act
    async_session.add(entry)
    await async_session.commit()
    await async_session.refresh(entry)

    # Assert
    assert entry.query_vector is not None
    assert len(entry.query_vector) == 1536
    assert entry.usage_count == 5
    assert entry.last_used_at is not None
```

---

## Traceability (추적성)

### TAG Chain

```
@SPEC:CASEBANK-UNIFY-001
  ├─ @REQ:CASEBANK-UNIFY-PROD-FIELDS-001
  │   └─ @CODE:CASEBANK-UNIFY-PROD-MODEL-001
  │       └─ @TEST:CASEBANK-UNIFY-UNIT-001
  │
  ├─ @REQ:CASEBANK-UNIFY-FIELD-RENAME-001
  │   ├─ @CODE:CASEBANK-UNIFY-REFLECTION-FIX-001
  │   └─ @TEST:CASEBANK-UNIFY-INTEGRATION-001
  │
  ├─ @REQ:CASEBANK-UNIFY-CRASH-FIX-001
  │   ├─ @CODE:CASEBANK-UNIFY-CONSOLIDATION-FIX-001
  │   └─ @CODE:CASEBANK-UNIFY-REFLECTION-FIX-001
  │
  └─ @REQ:CASEBANK-UNIFY-MIGRATION-001
      └─ @CODE:CASEBANK-UNIFY-MIGRATION-001
```

### 의존성 그래프

```
CASEBANK-002 (완료)
    ↓
CASEBANK-UNIFY-001 (현재)
    ↓
┌─────────────┬─────────────┬─────────────┐
│             │             │             │
CONSOLIDATION-001  REFLECTION-001  SCHEMA-SYNC-001
```

---

## Risks & Mitigation (위험 요소 및 대응)

### 위험 1: pgvector Extension 미설치

**시나리오**: Production DB에 pgvector extension이 설치되지 않은 경우

**영향도**: High (유사도 검색 기능 동작 불가)

**대응 방안**:
1. Migration 실행 전 pgvector 설치 여부 확인
2. Fallback으로 ARRAY 타입 사용 (성능 저하 감수)
3. 설치 가이드 문서화 (`CREATE EXTENSION IF NOT EXISTS vector;`)

---

### 위험 2: 기존 데이터 손실

**시나리오**: Migration 중 `response_text → answer` 변경 시 데이터 유실

**영향도**: Critical (비즈니스 데이터 손실)

**대응 방안**:
1. Migration 실행 전 전체 DB 백업 필수
2. Staging 환경에서 먼저 검증
3. Rollback 시나리오 테스트 완료 후 Production 적용
4. Blue-Green Deployment 고려

---

### 위험 3: 테스트 커버리지 저하

**시나리오**: 새 필드 추가 후 기존 테스트가 불충분한 경우

**영향도**: Medium (숨겨진 버그 발생 가능)

**대응 방안**:
1. 새 필드를 사용하는 모든 함수에 대한 Unit 테스트 추가
2. Integration 테스트에서 E2E 시나리오 검증
3. pytest-cov 실행하여 85% 이상 유지 확인

---

## Definition of Done (완료 기준)

### Code Complete

- [ ] `apps/api/database.py`에 3개 필드 추가 완료
- [ ] `consolidation_policy.py` 3곳 수정 완료
- [ ] `reflection_engine.py` 1곳 수정 완료
- [ ] `0008_taxonomy_schema.py` 필드명 변경 완료
- [ ] 새 Migration 파일 `0009_add_casebank_fields.py` 생성 완료

### Test Complete

- [ ] Unit 테스트 전체 통과 (0 failures)
- [ ] Integration 테스트 전체 통과 (0 failures)
- [ ] Test coverage 85% 이상 유지
- [ ] 새 필드에 대한 테스트 케이스 추가 완료

### Documentation Complete

- [ ] Migration 실행 가이드 작성
- [ ] Rollback 시나리오 문서화
- [ ] 새 필드 사용법 README 업데이트

### Deployment Ready

- [ ] `alembic upgrade head` 정상 실행 확인
- [ ] `alembic downgrade -1` 정상 실행 확인
- [ ] Staging 환경 배포 및 검증 완료
- [ ] Production 배포 체크리스트 작성

---

## References (참고 자료)

### 관련 문서

- [SQLAlchemy 2.0 Mapped Types](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html)
- [pgvector Extension Documentation](https://github.com/pgvector/pgvector)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

### 관련 SPEC

- @SPEC:CASEBANK-002 - CaseBank CRUD 구현
- @SPEC:SCHEMA-SYNC-001 - 스키마 동기화 전략
- @SPEC:CONSOLIDATION-001 - 케이스 병합 정책
- @SPEC:REFLECTION-001 - 품질 반영 시스템

---

**🎯 이 SPEC은 `/alfred:2-run SPEC-CASEBANK-UNIFY-001` 실행 시 TDD 구현의 기준이 됩니다.**
