# Phase 2 & 3 완료 후 다음 세션 컨텍스트

## 📋 세션 목표
**TaxonomyDAO 데이터 조회 이슈 해결 및 Phase 2/3 통합 테스트 완료**

---

## ✅ 완료된 작업 (Phase 1, 2, 3)

### Phase 1: Taxonomy DB Schema (완료)
**생성한 파일:**
- `alembic/versions/0008_taxonomy_schema.py` - Taxonomy 테이블 마이그레이션

**생성된 DB 테이블 (5개):**
1. `taxonomy_nodes` - UUID PK, label, canonical_path, version, confidence
2. `taxonomy_edges` - 복합 PK (parent, child, version)
3. `doc_taxonomy` - mapping_id PK (auto-increment), doc_id, node_id FK
4. `taxonomy_migrations` - migration_id PK (auto-increment), 버전 이력
5. `case_bank` - case_id PK, 쿼리 응답 케이스

**DB 상태 (확인됨):**
```sql
-- 위치: dt_rag_postgres_test (port 5433)
-- 데이터베이스: dt_rag_test

SELECT DISTINCT version, COUNT(*) FROM taxonomy_nodes GROUP BY version;
-- Result: version='1.0.0', count=9

SELECT node_id, label, canonical_path, version FROM taxonomy_nodes WHERE version = '1.0.0' LIMIT 5;
-- 데이터 존재 확인됨:
-- Technology, Science, Business, AI/ML, Software 등 9개 노드
```

**ORM 모델 수정 (apps/api/database.py):**
- `TaxonomyNode`: node_id UUID, label (node_name→label로 변경), canonical_path, version, confidence
- `TaxonomyEdge`: 복합 PK (parent, child, version)
- `TaxonomyMigration`: migration_id PK 추가
- `DocTaxonomy`: mapping_id PK 추가

---

### Phase 2: Taxonomy Service (구현 완료, 테스트 미완)
**생성한 파일:**
1. `apps/api/services/taxonomy_service.py` - Real TaxonomyService 구현
2. `apps/api/routers/taxonomy_router.py` - Mock 제거, Real 서비스 연결 (수정)

**구현 내용:**
```python
# apps/api/services/taxonomy_service.py
class TaxonomyService:
    async def list_versions(limit, offset) -> List[Dict]:
        # DB에서 DISTINCT version 조회

    async def get_tree(version: str) -> Dict:
        # TaxonomyDAO.get_tree() 호출 → edges 구성

    async def get_statistics(version: str) -> Dict:
        # COUNT, MAX depth 등 통계

    async def validate_taxonomy(version: str) -> Dict:
        # 노드 유효성 검증
```

**라우터 수정 (apps/api/routers/taxonomy_router.py):**
- Mock TaxonomyService 클래스 제거 (line 87-187)
- `from ..services.taxonomy_service import TaxonomyService as RealTaxonomyService` 추가
- `get_taxonomy_service()` → `return RealTaxonomyService()` 변경
- 모든 엔드포인트의 `service: TaxonomyService` → `service: RealTaxonomyService` 변경

**API 엔드포인트 (main.py line 412-416에 등록됨):**
- `GET /api/v1/taxonomy/versions` - 버전 목록
- `GET /api/v1/taxonomy/{version}/tree` - 트리 구조
- `GET /api/v1/taxonomy/{version}/statistics` - 통계
- `GET /api/v1/taxonomy/{version}/validate` - 검증

---

### Phase 3: Classification Pipeline (구현 완료)
**생성한 파일:**
1. `apps/classification/hybrid_classifier.py` - 3단계 분류 파이프라인
2. `apps/classification/hitl_queue.py` - HITL 큐 관리

**HybridClassifier 구현 (hybrid_classifier.py):**
```python
class HybridClassifier:
    async def classify(chunk_id, text, taxonomy_version, correlation_id):
        # Stage 1: Rule-based (sensitivity, keywords)
        rule_result = await _stage1_rule_based(text, taxonomy_version)
        if rule_result["confidence"] >= 0.90:
            return rule_result  # Skip LLM

        # Stage 2: LLM classification (PRD line 277 - 근거≥2, DAG 후보)
        llm_result = await _stage2_llm_classification(text, taxonomy_version, correlation_id)

        # Stage 3: Cross-validation & Confidence 계산
        final_result = await _stage3_cross_validation(chunk_id, text, rule_result, llm_result, taxonomy_version)

        # HITL 플래그 설정
        final_result["hitl_required"] = (
            final_result["confidence"] < 0.70 or  # PRD 임계값
            _detect_drift(rule_result, llm_result)
        )
        return final_result
```

**Confidence 산식 (PRD line 270 - 미결정, 임시 구현):**
- Rule + LLM 일치: `(rule_conf + llm_conf) / 2 * 1.1` (최대 1.0)
- LLM만: `llm_conf * 0.8`
- 불일치: `llm_conf * 0.7`

**HITLQueue 구현 (hitl_queue.py):**
```python
class HITLQueue:
    async def add_task(chunk_id, text, suggested_classification, confidence, alternatives, priority):
        # doc_taxonomy에 hitl_required=true 설정

    async def get_pending_tasks(limit, priority, min_confidence, max_confidence):
        # SELECT FROM doc_taxonomy WHERE hitl_required=true

    async def complete_task(task_id, chunk_id, approved_path, confidence_override, reviewer_notes):
        # UPDATE doc_taxonomy SET path=approved_path, hitl_required=false

    async def get_statistics():
        # COUNT, AVG confidence 등
```

---

## ⚠️ 현재 이슈: TaxonomyDAO 데이터 조회 실패

### 증상
**API 응답:**
```bash
curl -X GET "http://127.0.0.1:8001/api/v1/taxonomy/1.0.0/tree" \
  -H "X-API-Key: 7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"

# Response: 404 Not Found
{
  "detail": "Taxonomy version '1.0.0' not found"
}
```

**근본 원인:**
`TaxonomyDAO.get_tree(version)` 메서드가 빈 결과를 반환함.

### TaxonomyDAO 코드 (apps/api/database.py:262-300)
```python
class TaxonomyDAO:
    @staticmethod
    async def get_tree(version: str) -> List[Dict[str, Any]]:
        """분류체계 트리 조회 - 실제 데이터베이스에서"""
        async with async_session() as session:  # Line 265 - 수정됨 (db_manager.async_session() → async_session())
            try:
                query = text("""
                    SELECT node_id, label, canonical_path, version
                    FROM taxonomy_nodes
                    WHERE version = :version
                    ORDER BY canonical_path
                """)
                result = await session.execute(query, {"version": version})
                rows = result.fetchall()

                if not rows:
                    # 기본 데이터 삽입 시도
                    await TaxonomyDAO._insert_default_taxonomy(session, version)
                    result = await session.execute(query, {"version": version})
                    rows = result.fetchall()

                # 트리 구조로 변환
                tree = []
                for row in rows:
                    node = {
                        "label": row[1],  # label column
                        "version": row[3],
                        "node_id": str(row[0]),
                        "canonical_path": row[2],
                        "children": []
                    }
                    tree.append(node)

                return tree

            except Exception as e:
                logger.error(f"분류체계 조회 실패: {e}")
                return await TaxonomyDAO._get_fallback_tree(version)
```

### 데이터베이스 연결 설정 (apps/core/db_session.py)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag")

# Line 20-33
if "sqlite" in DATABASE_URL.lower():
    if "aiosqlite" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
```

### 시도한 해결 방법
1. ✅ `db_manager.async_session()` → `async_session()` 직접 사용으로 변경
2. ✅ taxonomy_router.py에서 `TaxonomyService` → `RealTaxonomyService` 타입 힌트 수정
3. ❌ 여전히 빈 결과 반환

### 확인된 사실
1. **DB에 데이터 존재**: `docker exec -i dt_rag_postgres_test psql -U postgres -d dt_rag_test -c "SELECT * FROM taxonomy_nodes LIMIT 5;"` → 9개 노드 확인됨
2. **API 서버 실행 중**: `http://127.0.0.1:8001/health` → healthy
3. **Real TaxonomyService 작동**: 404 응답 = 실제 DB 쿼리 실행 중
4. **환경 변수**: `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test` (port 5433)

---

## 🔍 디버깅 체크리스트

### 1. DATABASE_URL 확인
```bash
# API 서버 환경 변수 확인
echo $DATABASE_URL
# Expected: postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test

# apps/core/db_session.py에서 실제 사용되는 URL 확인
# Line 16: DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag")
# ⚠️ 주의: 기본값이 port 5432, 하지만 실제 DB는 5433
```

### 2. async_session 연결 테스트
```python
# apps/api/database.py에 테스트 코드 추가
async def test_taxonomy_query():
    async with async_session() as session:
        query = text("SELECT node_id, label FROM taxonomy_nodes LIMIT 1")
        result = await session.execute(query)
        row = result.fetchone()
        print(f"Test query result: {row}")
```

### 3. 트랜잭션 커밋 확인
```python
# TaxonomyDAO.get_tree()에서 session.commit() 호출 여부 확인
# 현재: SELECT만 수행, commit() 없음
# ⚠️ asyncpg는 autocommit이 기본적으로 꺼져 있을 수 있음
```

### 4. 쿼리 파라미터 바인딩 확인
```python
# Line 274: await session.execute(query, {"version": version})
# version 타입: str
# DB 컬럼 타입: TEXT
# ✅ 타입 일치함
```

### 5. 로깅 추가
```python
# TaxonomyDAO.get_tree() 시작 부분에 추가
logger.info(f"Querying taxonomy for version: {version}")
logger.info(f"Database URL: {DATABASE_URL}")

# 쿼리 결과 확인
logger.info(f"Query returned {len(rows)} rows")
```

---

## 🎯 다음 세션 작업 계획

### 목표
TaxonomyDAO 데이터 조회 이슈 해결 및 Phase 2/3 통합 테스트 완료

### Step 1: 근본 원인 특정
1. DATABASE_URL 환경 변수가 API 서버에 올바르게 전달되는지 확인
2. `async_session()`이 올바른 DB에 연결되는지 확인 (port 5432 vs 5433)
3. 쿼리 실행 전/후 로그 추가하여 실제 실행 여부 확인
4. 트랜잭션 격리 수준 확인 (READ COMMITTED vs SERIALIZABLE)

### Step 2: 해결 방법 적용
**가능한 원인별 해결책:**

**A. DATABASE_URL 불일치:**
```python
# apps/core/db_session.py 수정
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
```

**B. 트랜잭션 커밋 필요:**
```python
# TaxonomyDAO.get_tree() 수정
async with async_session() as session:
    result = await session.execute(query, {"version": version})
    await session.commit()  # 추가
    rows = result.fetchall()
```

**C. 세션 설정 문제:**
```python
# apps/core/db_session.py 수정
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,  # 추가
    autocommit=False  # 명시적으로 설정
)
```

### Step 3: 통합 테스트
```bash
# 1. API 서버 재시작 (환경 변수 확인)
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test
set PYTHONPATH=%CD%
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8001 --reload

# 2. Taxonomy 엔드포인트 테스트
curl -X GET "http://127.0.0.1:8001/api/v1/taxonomy/versions" \
  -H "X-API-Key: 7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"

curl -X GET "http://127.0.0.1:8001/api/v1/taxonomy/1.0.0/tree" \
  -H "X-API-Key: 7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"

# 3. Classification 엔드포인트 테스트 (Phase 3)
curl -X POST "http://127.0.0.1:8001/api/v1/classify" \
  -H "X-API-Key: 7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y" \
  -H "Content-Type: application/json" \
  -d '{
    "chunk_id": "test-chunk-001",
    "text": "This is a document about machine learning and neural networks.",
    "taxonomy_version": "1.0.0"
  }'
```

### Step 4: DoD 확인
- [ ] `GET /api/v1/taxonomy/versions` → 실제 DB 버전 목록 반환
- [ ] `GET /api/v1/taxonomy/1.0.0/tree` → 9개 노드 포함된 트리 반환
- [ ] `POST /api/v1/classify` → confidence, canonical_path, hitl_required 반환
- [ ] confidence < 0.70 → `doc_taxonomy.hitl_required = true` 확인

---

## 📂 핵심 파일 위치

**Phase 1 (DB Schema):**
- `alembic/versions/0008_taxonomy_schema.py` - Taxonomy 마이그레이션
- `apps/api/database.py` (line 115-207) - ORM 모델

**Phase 2 (Taxonomy Service):**
- `apps/api/services/taxonomy_service.py` - Real TaxonomyService
- `apps/api/routers/taxonomy_router.py` - API 엔드포인트
- `apps/api/database.py` (line 259-353) - TaxonomyDAO

**Phase 3 (Classification):**
- `apps/classification/hybrid_classifier.py` - 3단계 파이프라인
- `apps/classification/hitl_queue.py` - HITL 큐 관리

**DB 연결 설정:**
- `apps/core/db_session.py` - async_session, engine, Base
- `apps/api/main.py` (line 412-428) - 라우터 등록

---

## 🔑 환경 설정

**필수 환경 변수:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test
GEMINI_API_KEY=AIzaSyBlEJuO9LGLdCJRfhNU6QIKRUQ-Q22Vl7E
PYTHONPATH=%CD%
```

**Docker 컨테이너:**
- `dt_rag_postgres_test` - PostgreSQL 16 + pgvector (port 5433)
- DB: `dt_rag_test`
- User: `postgres` / Password: `postgres`

**API 서버:**
- URL: `http://127.0.0.1:8001`
- API Key: `7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y`
- Prefix: `/api/v1`

---

## 📝 바이브코딩 준수 사항

본 세션에서도 다음 원칙을 반드시 준수:

1. **추측 금지**: 코드를 직접 읽어서 확인
2. **모든 코드 읽기**: 관련 파일 전체를 tool로 읽기
3. **에러 즉시 해결**: 나중으로 미루지 않음
4. **정석 구현**: 임시방편 금지
5. **Code as SOT**: 주석/문서보다 코드 우선

### 디버깅 시 필수 작업:
1. `apps/core/db_session.py` 전체 읽기
2. `apps/api/database.py`의 TaxonomyDAO 전체 읽기
3. 환경 변수 실제 값 확인 (`echo $DATABASE_URL`)
4. DB 연결 테스트 (`SELECT 1` 쿼리)
5. 로그 추가 후 실제 쿼리 실행 여부 확인

---

## 🚀 빠른 시작 명령어

```bash
# 1. DB 데이터 확인
docker exec -i dt_rag_postgres_test psql -U postgres -d dt_rag_test \
  -c "SELECT version, COUNT(*) FROM taxonomy_nodes GROUP BY version;"

# 2. API 서버 시작
cd C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test
set GEMINI_API_KEY=AIzaSyBlEJuO9LGLdCJRfhNU6QIKRUQ-Q22Vl7E
set PYTHONPATH=%CD%
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8001 --reload

# 3. 헬스 체크
curl http://127.0.0.1:8001/health

# 4. Taxonomy 테스트
curl -X GET "http://127.0.0.1:8001/api/v1/taxonomy/1.0.0/tree" \
  -H "X-API-Key: 7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"
```

---

## 📊 현재 상태 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| Phase 1 (Taxonomy DB) | ✅ 완료 | 5개 테이블, 9개 노드 데이터 존재 |
| Phase 2 (Taxonomy Service) | ⚠️ 구현 완료, 테스트 미완 | TaxonomyDAO 조회 이슈 |
| Phase 3 (Classification Pipeline) | ✅ 구현 완료 | HybridClassifier, HITLQueue |
| API 서버 | ✅ 실행 중 | port 8001 |
| 통합 테스트 | ❌ 미완 | TaxonomyDAO 이슈로 중단 |

**다음 세션 목표: TaxonomyDAO 이슈 해결 → Phase 2/3 통합 테스트 완료 → Phase 4/5 진행**
