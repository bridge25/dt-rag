---
id: CASEBANK-002
version: 0.1.0
status: draft
created: 2025-10-09
updated: 2025-10-09
author: @claude
priority: high
category: feature
labels:
  - casebank
  - schema-extension
  - metadata
  - phase-3
depends_on:
  - FOUNDATION-001
  - NEURAL-001
blocks: []
related_specs:
  - REFLECTION-001
  - CONSOLIDATION-001
scope:
  packages:
    - apps/api
  files:
    - apps/api/database.py
    - db/migrations/
  tests:
    - tests/unit/test_casebank_metadata.py
---

# @SPEC:CASEBANK-002: CaseBank 스키마 확장 - Metadata 및 Lifecycle 관리

@SPEC:CASEBANK-002 @VERSION:0.1.0 @STATUS:draft

## HISTORY

### v0.1.0 (2025-10-09)
- **INITIAL**: CaseBank 스키마 확장 SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: CaseBank 테이블에 메타데이터, 버전 관리, 라이프사이클 필드 추가
- **CONTEXT**: Reflection 및 Consolidation 기능 지원을 위한 데이터 모델 확장
- **BASELINE**: FOUNDATION-001, NEURAL-001 완료 상태

---

## 1. 개요

### 목적
CaseBank 테이블을 확장하여 케이스의 메타데이터, 버전 관리, 라이프사이클 상태를 추적할 수 있도록 스키마를 개선합니다. 이를 통해 Reflection Engine과 Memory Consolidation Policy가 케이스를 효과적으로 관리할 수 있는 기반을 마련합니다.

### 범위
- **메타데이터 추가**: 케이스의 사용 빈도, 성공률, 마지막 접근 시간 등 추적
- **버전 관리**: 케이스 수정 이력 관리 (version, updated_by)
- **라이프사이클 상태**: 케이스의 생명주기 상태 (active, archived, deprecated)
- **성능 메트릭**: 케이스 적용 시 성과 측정 필드

---

## 2. Environment (환경)

### 기술 스택
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy 2.0+ (AsyncSession)
- **Migration**: Alembic or raw SQL scripts

### 기존 구현 상태
- **CaseBank 모델** (database.py):
  - 기본 필드: case_id, query, response_text, category_path, query_vector
  - 임베딩 생성: generate_case_embedding() 메서드
- **검색 기능**:
  - BM25 검색 (SEARCH-001)
  - Neural Vector 검색 (NEURAL-001)

### 제약사항
- 기존 케이스 데이터와 호환성 유지 필수
- NULL 허용 필드로 추가하여 점진적 마이그레이션 지원
- 인덱스 추가 시 성능 영향 최소화

---

## 3. Assumptions (가정)

### 데이터 가정
1. 기존 CaseBank 레코드는 새 필드 값이 NULL로 유지 가능
2. 새로운 케이스는 필드 초기값 자동 설정 (예: usage_count=0, status=active)
3. 타임스탬프 필드는 UTC 기준 자동 기록

### 아키텍처 가정
1. 마이그레이션 스크립트를 통한 스키마 변경
2. 기존 검색 로직에 영향 없음 (백워드 호환)
3. 메타데이터 업데이트는 비동기 태스크로 처리 가능

---

## 4. Requirements (요구사항)

### Ubiquitous Requirements

**@REQ:CASEBANK-002.1** Metadata Fields
- 시스템은 케이스의 사용 빈도(usage_count), 성공률(success_rate), 마지막 접근 시간(last_accessed_at)을 저장해야 한다
- 모든 메타데이터 필드는 NULL 허용이어야 한다

**@REQ:CASEBANK-002.2** Version Management
- 시스템은 케이스 버전(version)과 최종 수정자(updated_by)를 기록해야 한다
- 버전은 정수형이며 케이스 수정 시 자동 증가해야 한다

**@REQ:CASEBANK-002.3** Lifecycle Status
- 시스템은 케이스의 상태(status: active, archived, deprecated)를 관리해야 한다
- 기본 상태는 'active'이어야 한다

### Event-driven Requirements

**@REQ:CASEBANK-002.4** WHEN Case Accessed
- WHEN 케이스가 검색 결과로 반환되면, 시스템은 usage_count를 1 증가시켜야 한다
- WHEN 케이스가 반환되면, 시스템은 last_accessed_at을 현재 시각으로 갱신해야 한다

**@REQ:CASEBANK-002.5** WHEN Case Updated
- WHEN 케이스 내용이 수정되면, 시스템은 version을 1 증가시켜야 한다
- WHEN 케이스가 수정되면, 시스템은 updated_at과 updated_by를 갱신해야 한다

**@REQ:CASEBANK-002.6** WHEN Status Changed
- WHEN 케이스 상태가 변경되면, 시스템은 변경 이력을 로그에 기록해야 한다
- WHEN 케이스가 'archived' 상태가 되면, 시스템은 검색 결과에서 제외해야 한다

### State-driven Requirements

**@REQ:CASEBANK-002.7** WHILE Active Status
- WHILE 케이스가 'active' 상태일 때, 시스템은 검색 결과에 포함시켜야 한다
- WHILE 'active' 상태일 때, 메타데이터 업데이트가 허용되어야 한다

**@REQ:CASEBANK-002.8** WHILE Archived Status
- WHILE 케이스가 'archived' 상태일 때, 시스템은 기본 검색에서 제외해야 한다
- WHILE 'archived' 상태일 때, 명시적 요청 시에만 조회 가능해야 한다

### Constraints

**@REQ:CASEBANK-002.9** Backward Compatibility
- IF 기존 케이스 레코드가 존재하면, 시스템은 NULL 값을 허용해야 한다
- 기존 검색 API의 동작은 변경되지 않아야 한다

**@REQ:CASEBANK-002.10** Performance
- 메타데이터 업데이트는 검색 성능에 영향을 주지 않아야 한다
- 인덱스 추가는 검색 속도를 10% 이상 저하시키지 않아야 한다

---

## 5. Specifications (상세 구현 명세)

### IMPL 0.1: Schema Extension

**@IMPL:CASEBANK-002.0.1** New Columns
```sql
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS success_rate REAL;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
```

**@IMPL:CASEBANK-002.0.2** Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_casebank_status ON case_bank(status);
CREATE INDEX IF NOT EXISTS idx_casebank_last_accessed ON case_bank(last_accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_casebank_usage_count ON case_bank(usage_count DESC);
```

### IMPL 0.2: SQLAlchemy Model Update

**@IMPL:CASEBANK-002.0.2.1** CaseBank Model Extension
```python
from sqlalchemy import Integer, Float, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

class CaseBank(Base):
    __tablename__ = "case_bank"

    # 기존 필드들...
    case_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_path: Mapped[str] = mapped_column(String(255), nullable=True)
    query_vector: Mapped[List[float]] = mapped_column(Vector(1536), nullable=True)

    # 새로운 메타데이터 필드
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    success_rate: Mapped[float] = mapped_column(Float, nullable=True)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # 버전 관리
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=True)

    # 라이프사이클
    status: Mapped[str] = mapped_column(String(50), default='active', nullable=False)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

### IMPL 0.3: Metadata Update Logic

**@IMPL:CASEBANK-002.0.3.1** Update Usage Count
```python
async def increment_case_usage(
    session: AsyncSession,
    case_id: str
) -> None:
    stmt = (
        update(CaseBank)
        .where(CaseBank.case_id == case_id)
        .values(
            usage_count=CaseBank.usage_count + 1,
            last_accessed_at=datetime.now(timezone.utc)
        )
    )
    await session.execute(stmt)
    await session.commit()
```

**@IMPL:CASEBANK-002.0.3.2** Update Success Rate
```python
async def update_case_success_rate(
    session: AsyncSession,
    case_id: str,
    success_rate: float
) -> None:
    stmt = (
        update(CaseBank)
        .where(CaseBank.case_id == case_id)
        .values(success_rate=success_rate)
    )
    await session.execute(stmt)
    await session.commit()
```

### IMPL 0.4: Migration Script

**@IMPL:CASEBANK-002.0.4** Migration File: `002_extend_casebank_metadata.sql`
```sql
-- Migration: CASEBANK-002 Schema Extension
-- Created: 2025-10-09
-- Author: @claude

BEGIN;

-- 1. Add metadata columns
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS success_rate REAL;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE;

-- 2. Add version management
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);

-- 3. Add lifecycle status
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';

-- 4. Add timestamps
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE case_bank ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- 5. Create indexes
CREATE INDEX IF NOT EXISTS idx_casebank_status ON case_bank(status);
CREATE INDEX IF NOT EXISTS idx_casebank_last_accessed ON case_bank(last_accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_casebank_usage_count ON case_bank(usage_count DESC);

-- 6. Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_casebank_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_casebank_update_timestamp ON case_bank;
CREATE TRIGGER trigger_casebank_update_timestamp
    BEFORE UPDATE ON case_bank
    FOR EACH ROW
    EXECUTE FUNCTION update_casebank_timestamp();

COMMIT;
```

---

## 6. Traceability (추적성)

### 상위 SPEC 의존성
- **@SPEC:FOUNDATION-001**: CaseBank 기본 스키마
- **@SPEC:NEURAL-001**: query_vector 필드 활용

### 하위 SPEC 블로킹
- **@SPEC:REFLECTION-001**: Reflection Engine이 메타데이터 활용
- **@SPEC:CONSOLIDATION-001**: Consolidation Policy가 lifecycle 상태 활용

### 관련 SPEC
- **@SPEC:DATABASE-001**: PostgreSQL 스키마 설계
- **@SPEC:SEARCH-001**: 검색 필터링에 status 필드 활용

---

**END OF SPEC**
