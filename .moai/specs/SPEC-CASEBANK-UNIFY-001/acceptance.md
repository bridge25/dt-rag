---
id: CASEBANK-UNIFY-001
version: 0.0.1
status: draft
created: 2025-11-09
updated: 2025-11-09
---

# Acceptance Criteria: SPEC-CASEBANK-UNIFY-001

## 개요

이 문서는 CaseBank 스키마 통합 및 필드 정의 표준화 작업의 인수 기준을 정의합니다.

---

## 전체 품질 게이트

### 필수 통과 기준

| 항목 | 기준 | 검증 방법 |
|------|------|----------|
| **테스트 통과율** | 100% (0 failures, 0 errors) | `pytest tests/ -v` |
| **코드 커버리지** | 85% 이상 | `pytest --cov=apps --cov-report=term-missing` |
| **타입 체크** | 0 errors | `mypy apps/` |
| **Migration 성공** | Upgrade/Downgrade 정상 동작 | `alembic upgrade head && alembic downgrade -1` |
| **런타임 크래시** | 0건 (AttributeError 없음) | 수동 실행 검증 |

---

## AC-001: Production 모델 필드 추가

### Given-When-Then 시나리오

#### Scenario 1: query_vector 필드 정상 동작

**Given**:
- PostgreSQL 데이터베이스가 실행 중이고 pgvector extension이 활성화되어 있음
- CaseBankEntry 모델이 정의되어 있음

**When**:
- 새로운 CaseBankEntry를 생성하면서 `query_vector=[0.5] * 1536`를 할당함
- 데이터베이스에 저장하고 다시 조회함

**Then**:
- `entry.query_vector`가 NULL이 아니어야 함
- `len(entry.query_vector)`가 1536이어야 함
- Vector 타입으로 저장되어 유사도 검색이 가능해야 함

**검증 코드**:
```python
@pytest.mark.asyncio
async def test_query_vector_storage(async_session: AsyncSession):
    entry = CaseBankEntry(
        taxonomy_id=1,
        query="test query",
        answer="test answer",
        quality=0.9,
        query_vector=[0.5] * 1536
    )
    async_session.add(entry)
    await async_session.commit()
    await async_session.refresh(entry)

    assert entry.query_vector is not None
    assert len(entry.query_vector) == 1536
```

---

#### Scenario 2: usage_count 기본값 처리

**Given**:
- CaseBankEntry 모델에 `usage_count` 필드가 정의되어 있음
- 기본값이 0으로 설정되어 있음

**When**:
- `usage_count`를 명시하지 않고 CaseBankEntry를 생성함
- 데이터베이스에 저장함

**Then**:
- `entry.usage_count`가 0이어야 함
- NULL이 아니어야 함 (NOT NULL 제약)

**검증 코드**:
```python
@pytest.mark.asyncio
async def test_usage_count_default(async_session: AsyncSession):
    entry = CaseBankEntry(
        taxonomy_id=1,
        query="test query",
        answer="test answer",
        quality=0.9
        # usage_count 명시하지 않음
    )
    async_session.add(entry)
    await async_session.commit()
    await async_session.refresh(entry)

    assert entry.usage_count == 0
    assert entry.usage_count is not None
```

---

#### Scenario 3: last_used_at NULL 허용

**Given**:
- CaseBankEntry 모델에 `last_used_at` 필드가 정의되어 있음
- 필드가 nullable=True로 설정되어 있음

**When**:
- `last_used_at`을 명시하지 않고 CaseBankEntry를 생성함
- 이후 특정 시각으로 업데이트함

**Then**:
- 초기 값은 NULL이어야 함
- 업데이트 후 datetime 객체가 저장되어야 함
- 타임존 정보가 보존되어야 함 (TIMESTAMPTZ)

**검증 코드**:
```python
@pytest.mark.asyncio
async def test_last_used_at_nullable(async_session: AsyncSession):
    from datetime import datetime, timezone

    # Initial: NULL
    entry = CaseBankEntry(
        taxonomy_id=1,
        query="test query",
        answer="test answer",
        quality=0.9
    )
    async_session.add(entry)
    await async_session.commit()
    await async_session.refresh(entry)

    assert entry.last_used_at is None

    # Update: Set timestamp
    now = datetime.now(timezone.utc)
    entry.last_used_at = now
    await async_session.commit()
    await async_session.refresh(entry)

    assert entry.last_used_at is not None
    assert (entry.last_used_at - now).total_seconds() < 1
```

---

## AC-002: 필드명 통일

### Given-When-Then 시나리오

#### Scenario 1: quality_score → quality 변경

**Given**:
- 모든 테스트 코드에서 `quality_score` 필드를 참조하고 있었음
- Production 모델은 `quality` 필드를 사용함

**When**:
- 테스트 픽스처를 `quality_score` → `quality`로 변경함
- 모든 assertion을 업데이트함

**Then**:
- 모든 Unit 테스트가 통과해야 함
- `quality_score` 참조가 코드베이스에 존재하지 않아야 함

**검증 명령어**:
```bash
# quality_score 참조가 없어야 함
rg "quality_score" tests/ apps/ --type py
# 결과: No matches found
```

---

#### Scenario 2: response_text → answer 변경

**Given**:
- `reflection_engine.py`에서 `entry.response_text`를 참조하고 있었음
- Production 모델은 `answer` 필드를 사용함

**When**:
- `reflection_engine.py:195`를 `entry.answer`로 변경함
- 관련 테스트 코드를 업데이트함

**Then**:
- Reflection 로직이 정상 동작해야 함
- AttributeError가 발생하지 않아야 함
- `response_text` 참조가 코드베이스에 존재하지 않아야 함 (Migration 제외)

**검증 명령어**:
```bash
# response_text 참조가 Migration을 제외하고 없어야 함
rg "response_text" apps/ --type py --glob "!alembic/**"
# 결과: No matches found
```

---

## AC-003: 런타임 크래시 제거

### Given-When-Then 시나리오

#### Scenario 1: consolidation_policy.py 크래시 해결

**Given**:
- `consolidation_policy.py:108, 155, 241`에서 AttributeError가 발생하고 있었음
- 누락된 필드: `query_vector`, `usage_count`, `last_used_at`

**When**:
- 각 위치에 안전한 필드 접근 로직을 추가함
- 기본값 처리 및 NULL 체크를 구현함

**Then**:
- Consolidation 로직 실행 시 AttributeError가 발생하지 않아야 함
- `query_vector`가 None일 때 similarity가 0.0으로 처리되어야 함
- `usage_count`가 없을 때 기본값 0으로 처리되어야 함
- `last_used_at`이 None일 때 조건 검사를 건너뛰어야 함

**검증 코드**:
```python
@pytest.mark.asyncio
async def test_consolidation_with_missing_fields():
    """Test consolidation logic handles missing fields gracefully"""
    from apps.orchestration.src.consolidation_policy import consolidate_entries

    # Case 1: No query_vector
    entry1 = CaseBankEntry(
        query="test 1",
        answer="answer 1",
        quality=0.9,
        query_vector=None  # Missing
    )

    # Case 2: No usage_count (should default to 0)
    entry2 = CaseBankEntry(
        query="test 2",
        answer="answer 2",
        quality=0.8
    )

    # Should not raise AttributeError
    result = consolidate_entries([entry1, entry2])
    assert result is not None
```

---

#### Scenario 2: reflection_engine.py 크래시 해결

**Given**:
- `reflection_engine.py:195`에서 `entry.response_text` 접근 시 AttributeError 발생
- Production 모델에는 `answer` 필드만 존재함

**When**:
- `response_text` → `answer`로 필드명 변경함

**Then**:
- Reflection 로직 실행 시 AttributeError가 발생하지 않아야 함
- Reflection 데이터에 `response` 키가 정상적으로 포함되어야 함

**검증 코드**:
```python
@pytest.mark.asyncio
async def test_reflection_engine_field_access():
    """Test reflection engine uses correct field name"""
    from apps.orchestration.src.reflection_engine import create_reflection_data

    entry = CaseBankEntry(
        query="test query",
        answer="test answer",  # Not response_text
        quality=0.95
    )

    # Should not raise AttributeError
    reflection_data = create_reflection_data(entry)

    assert "response" in reflection_data
    assert reflection_data["response"] == "test answer"
```

---

## AC-004: 데이터베이스 마이그레이션

### Given-When-Then 시나리오

#### Scenario 1: Migration Upgrade 성공

**Given**:
- Alembic migration 파일 `0009_add_casebank_fields.py`가 작성되어 있음
- 현재 DB 버전은 `0008_taxonomy_schema`임

**When**:
- `alembic upgrade head`를 실행함

**Then**:
- Migration이 성공적으로 완료되어야 함
- `casebank_entry` 테이블에 3개 컬럼이 추가되어야 함:
  - `query_vector` (ARRAY 또는 Vector 타입)
  - `usage_count` (INTEGER, NOT NULL, DEFAULT 0)
  - `last_used_at` (TIMESTAMP WITH TIME ZONE, NULL 허용)
- 2개 인덱스가 생성되어야 함:
  - `idx_casebank_usage_count`
  - `idx_casebank_last_used`

**검증 명령어**:
```sql
-- PostgreSQL에서 실행
\d+ casebank_entry

-- 예상 출력:
-- query_vector    | anyarray                    |           |          |
-- usage_count     | integer                     |           | not null | 0
-- last_used_at    | timestamp with time zone    |           |          |

-- 인덱스 확인
\di idx_casebank_*
```

---

#### Scenario 2: Migration Rollback 성공

**Given**:
- Migration `0009_add_casebank_fields`가 적용되어 있음

**When**:
- `alembic downgrade -1`을 실행함

**Then**:
- Rollback이 성공적으로 완료되어야 함
- 추가된 3개 컬럼이 제거되어야 함
- 생성된 2개 인덱스가 제거되어야 함
- 데이터 손실이 없어야 함 (기존 컬럼 데이터 보존)

**검증 명령어**:
```sql
-- PostgreSQL에서 실행
\d+ casebank_entry

-- 예상 출력: query_vector, usage_count, last_used_at 존재하지 않음
```

---

#### Scenario 3: 멱등성 보장

**Given**:
- Migration `0009_add_casebank_fields`가 이미 적용되어 있음

**When**:
- `alembic upgrade head`를 다시 실행함

**Then**:
- "Already at latest version" 메시지가 출력되어야 함
- 에러가 발생하지 않아야 함
- 테이블 스키마가 변경되지 않아야 함

---

## AC-005: 테스트 코드 동기화

### Given-When-Then 시나리오

#### Scenario 1: Unit 테스트 전체 통과

**Given**:
- 모든 Unit 테스트가 새 스키마를 반영하도록 업데이트되어 있음

**When**:
- `pytest tests/unit/ -v`를 실행함

**Then**:
- 모든 테스트가 통과해야 함 (0 failures, 0 errors)
- 테스트 실행 시간이 기존 대비 2배 이상 증가하지 않아야 함

**검증 명령어**:
```bash
pytest tests/unit/ -v --tb=short
# 예상 결과: ===== X passed in Y.YYs =====
```

---

#### Scenario 2: Integration 테스트 전체 통과

**Given**:
- Integration 테스트에 새 필드 검증 로직이 추가되어 있음

**When**:
- `pytest tests/integration/ -v`를 실행함

**Then**:
- 모든 테스트가 통과해야 함
- DB 연결 에러가 발생하지 않아야 함
- Transaction rollback이 정상 동작해야 함

---

#### Scenario 3: 테스트 커버리지 유지

**Given**:
- 기존 코드 커버리지가 85% 이상이었음

**When**:
- 새 필드를 추가하고 테스트를 실행함
- `pytest --cov=apps --cov-report=term-missing`를 실행함

**Then**:
- 전체 커버리지가 85% 이상이어야 함
- 새로 추가된 필드 접근 로직이 테스트에 포함되어야 함

**검증 명령어**:
```bash
pytest --cov=apps --cov-report=term-missing --cov-fail-under=85
# 예상 결과: TOTAL coverage >= 85%
```

---

## AC-006: 문서화 완료

### Given-When-Then 시나리오

#### Scenario 1: Migration 가이드 작성

**Given**:
- CaseBankEntry 스키마 변경이 완료되어 있음

**When**:
- Migration 실행 가이드 문서를 작성함

**Then**:
- 다음 내용이 포함되어야 함:
  - Prerequisites (pgvector 설치 확인)
  - Staging 환경 실행 절차
  - Production 배포 절차
  - Rollback 시나리오

---

#### Scenario 2: README 업데이트

**Given**:
- CaseBankEntry 모델에 새 필드가 추가되어 있음

**When**:
- README.md를 업데이트함

**Then**:
- 새 필드 사용법이 예제 코드와 함께 설명되어야 함:
  - `query_vector`: 유사도 검색 예제
  - `usage_count`: 인기 케이스 조회 예제
  - `last_used_at`: 비활성 케이스 필터링 예제

---

## 통합 검증 시나리오

### End-to-End 시나리오

**Given**:
- 모든 AC-001 ~ AC-006이 개별적으로 통과했음
- Staging 환경이 준비되어 있음

**When**:
1. Alembic migration을 실행함
2. 애플리케이션을 재시작함
3. 새 CaseBankEntry를 생성함
4. Consolidation 로직을 실행함
5. Reflection 로직을 실행함

**Then**:
- 모든 단계가 에러 없이 완료되어야 함
- Consolidation 결과에 `query_vector` 유사도 점수가 포함되어야 함
- Reflection 데이터에 `answer` 필드가 정상 포함되어야 함
- `usage_count`가 자동으로 증가해야 함
- `last_used_at`이 현재 시각으로 업데이트되어야 함

---

## 성능 검증

### 성능 기준

| 항목 | 기준 | 측정 방법 |
|------|------|----------|
| **CaseBankEntry 생성 속도** | 기존 대비 5% 이내 차이 | Benchmark 테스트 |
| **Consolidation 실행 시간** | 기존 대비 10% 이내 차이 | 100개 케이스 병합 측정 |
| **인덱스 쿼리 속도** | `usage_count DESC` 쿼리 100ms 이내 | EXPLAIN ANALYZE |

---

## Definition of Done

### 최종 체크리스트

- [ ] **AC-001**: Production 모델 필드 추가 완료 (3개 시나리오 통과)
- [ ] **AC-002**: 필드명 통일 완료 (2개 시나리오 통과)
- [ ] **AC-003**: 런타임 크래시 제거 완료 (2개 시나리오 통과)
- [ ] **AC-004**: 데이터베이스 마이그레이션 완료 (3개 시나리오 통과)
- [ ] **AC-005**: 테스트 코드 동기화 완료 (3개 시나리오 통과)
- [ ] **AC-006**: 문서화 완료 (2개 시나리오 통과)
- [ ] **통합 검증**: End-to-End 시나리오 통과
- [ ] **성능 검증**: 모든 성능 기준 충족
- [ ] **Code Review**: 2인 이상 승인
- [ ] **Staging 배포**: 검증 완료

---

**🎯 모든 Acceptance Criteria가 충족되면 이 SPEC은 완료(completed)로 표시됩니다.**
