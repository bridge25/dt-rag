# Phase 1: Taxonomy DB Schema — Context Sheet

**Phase**: Phase 1 - Taxonomy DB
**우선순위**: P0 (필수)
**담당 Subagent**: database-architect
**의존성**: None
**예상 파일 수**: 3개
**출처**: phase1~5.txt 라인 8-29

---

## 1. Scope

### 1.1 목표
PRD Annex C.4 (282-341줄)의 Taxonomy 관련 5개 테이블을 PostgreSQL에 생성

**테이블 목록:**
1. `taxonomy_nodes`
2. `taxonomy_edges`
3. `doc_taxonomy`
4. `taxonomy_migrations`
5. `case_bank`

### 1.2 비범위
- Taxonomy Service 로직
- 프론트엔드
- 분류 파이프라인

### 1.3 제약
- PostgreSQL only
- Alembic migration 형식 준수
- 기존 `documents`, `chunks`, `embeddings` 테이블과 무결성 유지

### 1.4 DoD (Definition of Done)
- [ ] `alembic upgrade head` 실행 성공
- [ ] `psql \d taxonomy_nodes` 등 5개 테이블 확인
- [ ] FK 제약 확인
- [ ] Lint/Type 통과

---

## 2. IG 확보 항목

### 2.1 필수 확인 사항
1. ✓ PRD 282-341줄 DDL 정확히 읽음
2. ✓ 기존 database.py Base 확인
3. ✓ 기존 마이그레이션 패턴 확인
4. ⚠️ FK 무결성 제약 명시 필요

### 2.2 필수 읽기 파일 (Main)
```bash
# 반드시 Read tool로 읽어야 함
1. prd_dynamic_taxonomy_rag_v_1_8 최종 (1).md (라인 282-341)
2. apps/core/db_session.py (Base 클래스)
3. apps/api/database.py (기존 테이블 FK 확인)
4. alembic/versions/0004_asyncpg_compatibility_fixes.py (마이그레이션 패턴)
```

### 2.3 파일 존재 확인
```bash
ls alembic/versions/
test -f alembic/env.py && echo "exists"
echo $DATABASE_URL  # postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test
```

---

## 3. Context Load

### 3.1 Main (수정 대상)
- `alembic/versions/` (신규 파일 생성)
- `apps/api/models/` (신규 파일 생성)

### 3.2 Reference (읽기만)
- PRD 282-341줄 (DDL 샘플, 복사 금지)
- `apps/api/database.py` (documents 테이블 구조만 확인)

---

## 4. Plan (≤5파일)

### 4.1 생성할 파일
1. **alembic/versions/0008_taxonomy_schema.py** (신규)
   - `upgrade()`: 5개 테이블 생성
   - `downgrade()`: 역순 삭제

2. **apps/api/models/taxonomy.py** (신규)
   - SQLAlchemy ORM 모델 5개 클래스

3. **tests/test_taxonomy_migration.py** (신규)
   - upgrade/downgrade/FK 테스트

**파일 수**: 3개 ✓

---

## 5. Explain 형식 (승인 대기)

```markdown
## Explain

### 파일 1: alembic/versions/0008_taxonomy_schema.py
- `upgrade()`: taxonomy_nodes, taxonomy_edges, doc_taxonomy, taxonomy_migrations, case_bank 생성
- 인덱스 6개 생성 (GIN for ARRAY, WHERE for hitl)
- `downgrade()`: 역순 DROP TABLE

### 파일 2: apps/api/models/taxonomy.py
- `class TaxonomyNode(Base)`: 5개 컬럼 정의
- `class TaxonomyEdge(Base)`: 복합 PK
- (나머지 3개 클래스)

### 파일 3: tests/test_taxonomy_migration.py
- `test_upgrade()`: alembic upgrade → psql 확인
- `test_fk_constraint()`: FK 위반 확인

승인 요청: 위 구조로 진행해도 되는지 확인 부탁드립니다.
```

---

## 6. Verify

### DoD 체크리스트
```bash
# Lint
flake8 alembic/versions/0008_taxonomy_schema.py

# Migration
alembic upgrade head

# 테이블 확인
psql -U postgres -d dt_rag_test -c "\d taxonomy_nodes"

# Test
pytest tests/test_taxonomy_migration.py -v
```

---

## 7. 다음 Phase 인터페이스

**Phase 2, 3에게 전달:**
- Output: 5개 테이블 생성 완료
- Verification: `psql -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'taxonomy%';"`

---

## 8. Abstain 트리거

**즉시 중단 상황:**
1. PRD 282-341줄 읽지 않고 스키마 작성
2. documents 테이블 확인 없이 FK 정의
3. 기존 마이그레이션 패턴 확인 없이 새 파일 작성

**Abstain 메시지 예시:**
> "IG 부족: documents.doc_id 컬럼 타입 미확인. apps/api/database.py를 읽겠습니다."

---

**End of Phase 1 Context**
