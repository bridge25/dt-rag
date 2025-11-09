---
id: CASEBANK-UNIFY-001
version: 0.0.1
status: draft
created: 2025-11-09
updated: 2025-11-09
---

# Implementation Plan: SPEC-CASEBANK-UNIFY-001

## 개요

이 문서는 CaseBank 스키마 통합 및 필드 정의 표준화 작업의 구현 계획을 정의합니다.

---

## 구현 전략

### 접근 방식

**전략**: Bottom-Up 마이그레이션 (DB 스키마 → 모델 → 비즈니스 로직 → 테스트)

**이유**:
1. 데이터베이스 스키마가 모든 레이어의 기반
2. 모델 정의가 변경되면 비즈니스 로직과 테스트가 자동으로 타입 안전성 확보
3. Migration을 먼저 작성하면 Rollback 시나리오를 조기에 검증 가능

---

## 구현 단계

### Phase 1: 데이터베이스 스키마 정의

**목표**: Alembic Migration 작성 및 검증

**작업 항목**:

1. **새 Migration 파일 생성**:
   - 파일명: `alembic/versions/0009_add_casebank_fields.py`
   - 내용: `query_vector`, `usage_count`, `last_used_at` 필드 추가
   - 인덱스 생성: `idx_casebank_usage_count`, `idx_casebank_last_used`

2. **기존 Migration 수정**:
   - 파일: `alembic/versions/0008_taxonomy_schema.py`
   - 변경: `response_text` → `answer` 필드명 수정

3. **Migration 검증**:
   ```bash
   # Upgrade 테스트
   alembic upgrade head

   # Rollback 테스트
   alembic downgrade -1
   alembic upgrade head
   ```

**완료 기준**:
- ✅ Migration 파일이 정상적으로 생성됨
- ✅ `alembic upgrade head` 실행 시 에러 없음
- ✅ `alembic downgrade -1` 실행 후 재 upgrade 시 정상 동작
- ✅ PostgreSQL에서 테이블 스키마 확인 완료

**예상 작업량**: Phase 1 우선 (Foundation)

---

### Phase 2: Production 모델 업데이트

**목표**: `apps/api/database.py`의 `CaseBankEntry` 클래스 수정

**작업 항목**:

1. **필드 추가**:
   ```python
   query_vector: Mapped[Optional[List[float]]] = mapped_column(
       Vector(1536) if PGVECTOR_AVAILABLE else ArrayType,
       nullable=True
   )
   usage_count: Mapped[int] = mapped_column(
       Integer, nullable=False, default=0, server_default=text('0')
   )
   last_used_at: Mapped[Optional[datetime]] = mapped_column(
       DateTime(timezone=True), nullable=True
   )
   ```

2. **타입 안전성 검증**:
   - mypy 실행: `mypy apps/api/database.py`
   - SQLAlchemy 2.0 Mapped 타입 정상 동작 확인

3. **pgvector 대체 로직 확인**:
   - `PGVECTOR_AVAILABLE` 플래그 동작 검증
   - Fallback ArrayType 정상 동작 확인

**완료 기준**:
- ✅ 모델 클래스에 3개 필드 추가 완료
- ✅ mypy 타입 체크 통과 (0 errors)
- ✅ SQLAlchemy metadata 생성 시 에러 없음

**예상 작업량**: Phase 1 완료 후 (의존성: Migration 선행 필수)

---

### Phase 3: 비즈니스 로직 수정

**목표**: Consolidation 및 Reflection 엔진의 런타임 크래시 제거

**작업 항목**:

#### 3-1. Consolidation Policy 수정

**파일**: `apps/orchestration/src/consolidation_policy.py`

**변경 위치**:

1. **Line 108**: query_vector 안전 접근
   ```python
   if entry.query_vector and candidate.query_vector:
       similarity = calculate_similarity(entry.query_vector, candidate.query_vector)
   else:
       similarity = 0.0
   ```

2. **Line 155**: usage_count 기본값 처리
   ```python
   usage = getattr(entry, 'usage_count', 0)
   if usage > threshold:
       # ...
   ```

3. **Line 241**: last_used_at NULL 허용 처리
   ```python
   last_used = getattr(entry, 'last_used_at', None)
   if last_used and (datetime.now(timezone.utc) - last_used).days > 90:
       # ...
   ```

#### 3-2. Reflection Engine 수정

**파일**: `apps/orchestration/src/reflection_engine.py`

**변경 위치**:

- **Line 195**: 필드명 변경
  ```python
  reflection_data = {
      "query": entry.query,
      "response": entry.answer,  # response_text → answer
      "quality": entry.quality
  }
  ```

**완료 기준**:
- ✅ consolidation_policy.py 3곳 수정 완료
- ✅ reflection_engine.py 1곳 수정 완료
- ✅ 수정된 코드에서 AttributeError 발생하지 않음

**예상 작업량**: Phase 2 완료 후 (의존성: 모델 정의 선행 필수)

---

### Phase 4: 테스트 코드 동기화

**목표**: 모든 테스트가 새 스키마를 반영하고 통과하도록 수정

**작업 항목**:

#### 4-1. Unit 테스트 업데이트

**파일**: `tests/unit/test_consolidation_policy.py`

**변경 내용**:
- 테스트 픽스처에 `query_vector`, `usage_count`, `last_used_at` 추가
- `quality_score` → `quality` 필드명 변경
- 새 필드를 사용하는 함수에 대한 테스트 케이스 추가

**예시**:
```python
@pytest.fixture
def sample_entry():
    return CaseBankEntry(
        query="test query",
        answer="test answer",
        quality=0.95,
        query_vector=[0.1] * 1536,
        usage_count=0,
        last_used_at=None
    )
```

#### 4-2. Integration 테스트 업데이트

**파일**: `tests/integration/test_casebank_crud.py`

**추가 테스트 케이스**:
```python
@pytest.mark.asyncio
async def test_casebank_entry_new_fields(async_session: AsyncSession):
    """Test new fields are properly stored and retrieved"""
    # 새 필드 3개에 대한 CRUD 작업 검증
    # ...
```

#### 4-3. Metadata 테스트 업데이트

**파일**: `tests/integration/test_casebank_metadata.py`

**변경 내용**:
- `quality_score` → `quality` 필드명 변경
- Metadata 검증 로직에 새 필드 포함

**완료 기준**:
- ✅ 모든 Unit 테스트 통과 (0 failures)
- ✅ 모든 Integration 테스트 통과 (0 failures)
- ✅ Test coverage 85% 이상 유지
- ✅ 새 필드에 대한 테스트 케이스 추가 완료

**예상 작업량**: Phase 3 완료 후 (의존성: 비즈니스 로직 수정 선행 필수)

---

### Phase 5: 문서화 및 배포 준비

**목표**: 운영 배포를 위한 문서 및 체크리스트 작성

**작업 항목**:

1. **Migration 실행 가이드**:
   ```markdown
   ## CaseBankEntry 필드 추가 Migration 실행 가이드

   ### Prerequisites
   - PostgreSQL 15+ 설치 확인
   - pgvector extension 설치 확인
   - 전체 DB 백업 완료

   ### Execution Steps
   1. Staging 환경에서 먼저 실행
   2. alembic upgrade head 실행
   3. 데이터 무결성 검증
   4. Production 배포
   ```

2. **Rollback 시나리오 문서**:
   - Downgrade 실행 절차
   - 데이터 복구 방법
   - 긴급 연락망

3. **README 업데이트**:
   - 새 필드 사용법 추가
   - API 스키마 변경 사항 명시
   - 예제 코드 업데이트

**완료 기준**:
- ✅ Migration 가이드 작성 완료
- ✅ Rollback 시나리오 문서화 완료
- ✅ README.md 업데이트 완료
- ✅ Production 배포 체크리스트 작성 완료

**예상 작업량**: Phase 4 완료 후 (최종 단계)

---

## 기술적 고려사항

### pgvector Extension 처리

**문제**: Production DB에 pgvector가 설치되지 않을 수 있음

**해결책**:
```python
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

# 모델 정의 시
query_vector: Mapped[Optional[List[float]]] = mapped_column(
    Vector(1536) if PGVECTOR_AVAILABLE else ArrayType,
    nullable=True
)
```

**장점**:
- 개발 환경에서 pgvector 없이도 테스트 가능
- Production 배포 시 점진적으로 pgvector 활성화 가능

---

### 타임존 처리

**문제**: `last_used_at` 필드의 타임존 일관성

**해결책**:
```python
from datetime import datetime, timezone

# Always use UTC
last_used_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime(timezone=True),  # PostgreSQL TIMESTAMPTZ
    nullable=True
)

# 값 설정 시
entry.last_used_at = datetime.now(timezone.utc)
```

**이유**:
- 글로벌 서비스 대비 UTC 표준 사용
- PostgreSQL TIMESTAMPTZ로 저장하여 타임존 정보 보존

---

### 인덱스 전략

**목표**: 쿼리 성능 최적화

**인덱스 생성**:
```sql
CREATE INDEX idx_casebank_usage_count ON casebank_entry(usage_count DESC);
CREATE INDEX idx_casebank_last_used ON casebank_entry(last_used_at DESC);
```

**사용 시나리오**:
- `usage_count DESC`: 인기 케이스 조회 (`ORDER BY usage_count DESC LIMIT 10`)
- `last_used_at DESC`: 최근 사용 케이스 조회, 비활성 케이스 필터링

---

## 품질 검증 계획

### 자동화된 검증

1. **타입 체크**:
   ```bash
   mypy apps/api/database.py
   mypy apps/orchestration/src/consolidation_policy.py
   mypy apps/orchestration/src/reflection_engine.py
   ```

2. **테스트 실행**:
   ```bash
   pytest tests/unit/ -v
   pytest tests/integration/ -v
   pytest --cov=apps --cov-report=term-missing
   ```

3. **Migration 검증**:
   ```bash
   alembic check  # Pending migrations 확인
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

### 수동 검증

1. **스키마 검증**:
   ```sql
   \d+ casebank_entry  -- PostgreSQL에서 테이블 구조 확인
   ```

2. **데이터 무결성 확인**:
   ```sql
   SELECT COUNT(*) FROM casebank_entry WHERE usage_count IS NULL;  -- 0 expected
   SELECT COUNT(*) FROM casebank_entry WHERE query_vector IS NOT NULL;
   ```

3. **런타임 테스트**:
   - Consolidation 로직 실행 후 크래시 없음 확인
   - Reflection 로직 실행 후 데이터 정상 처리 확인

---

## 위험 관리

### 위험 요소 및 대응 계획

| 위험 요소 | 확률 | 영향도 | 대응 방안 |
|----------|------|--------|----------|
| pgvector 미설치 | Medium | High | Fallback ArrayType 사용, 설치 가이드 제공 |
| Migration 실패 | Low | Critical | 백업 필수, Staging 선행 검증, Rollback 시나리오 준비 |
| 테스트 커버리지 저하 | Low | Medium | 새 필드별 Unit 테스트 추가, Coverage 85% 이상 유지 |
| 기존 데이터 손실 | Very Low | Critical | Blue-Green Deployment, 전체 DB 백업, Rollback 테스트 |

---

## 배포 체크리스트

### Pre-Deployment

- [ ] Staging 환경에서 Migration 실행 및 검증 완료
- [ ] 전체 테스트 통과 (Unit + Integration)
- [ ] Test coverage 85% 이상 확인
- [ ] Code review 완료
- [ ] Production DB 백업 완료
- [ ] Rollback 시나리오 테스트 완료

### Deployment

- [ ] pgvector extension 설치 확인 (`CREATE EXTENSION IF NOT EXISTS vector;`)
- [ ] Migration 실행 (`alembic upgrade head`)
- [ ] 스키마 변경 확인 (`\d+ casebank_entry`)
- [ ] 데이터 무결성 검증 쿼리 실행
- [ ] 애플리케이션 재시작
- [ ] Health check 통과 확인

### Post-Deployment

- [ ] Consolidation 로직 정상 동작 확인
- [ ] Reflection 로직 정상 동작 확인
- [ ] 로그 모니터링 (AttributeError 발생 여부)
- [ ] 성능 지표 확인 (쿼리 속도, 인덱스 사용률)
- [ ] 24시간 모니터링 (이상 징후 감시)

---

## 다음 단계

이 구현 계획이 승인되면 다음 순서로 진행됩니다:

1. **`/alfred:2-run SPEC-CASEBANK-UNIFY-001`** 실행
2. **RED → GREEN → REFACTOR** TDD 사이클 진행
3. **`/alfred:3-sync`**로 문서 동기화
4. **PR 생성 및 Code Review**
5. **Staging 배포 및 검증**
6. **Production 배포**

---

**🎯 이 계획은 spec.md의 요구사항을 구현하기 위한 로드맵입니다.**
