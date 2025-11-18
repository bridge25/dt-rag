# Railway PostgreSQL pgvector 수동 설정 가이드

## 개요

Railway 플랫폼에 dt-rag 백엔드 API를 배포하기 위해서는 PostgreSQL에서 pgvector 확장을 수동으로 활성화해야 합니다.

## 배경

### 왜 수동 설정이 필요한가?

1. **권한 제한**: 애플리케이션 컨테이너의 데이터베이스 사용자는 `CREATE EXTENSION` 권한이 없음
2. **서버 레벨 설치**: PostgreSQL 확장은 데이터베이스 서버에서 활성화되어야 하며, 애플리케이션 레벨에서는 불가능
3. **Railway 아키텍처**: Railway CLI는 보안상 PostgreSQL 서비스 직접 접근을 제공하지 않음

### 실패한 자동화 시도

```python
# install_pgvector.py - 권한 부족으로 실패
await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
# ERROR: extension "vector" is not available
```

```toml
# railway.toml - 이 방법도 실패
startCommand = "python3 install_pgvector.py && alembic upgrade heads && ..."
```

## 수동 설정 절차

### 1단계: Railway 대시보드 접속

1. https://railway.app 접속 및 로그인
2. **프로젝트**: dt-rag
3. **환경**: production
4. **서비스**: PostgreSQL (클릭)

### 2단계: pgvector 확장 활성화

PostgreSQL 서비스 페이지에서:

1. **"Data"** 탭 또는 **"Query"** 탭 선택
2. SQL 쿼리 입력창에 아래 명령 입력:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. **"Execute"** 또는 **"Run"** 버튼 클릭

### 3단계: 설치 확인

확인 쿼리 실행:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

**예상 출력**:
```
 extname | extversion
---------+------------
 vector  | 0.5.1
```

### 4단계: 재배포

pgvector 활성화 후:

- **자동 재배포**: Railway가 변경 감지 후 5-10분 내 자동 재배포 (권장)
- **수동 트리거**: `railway up` 명령 실행

## 배포 성공 확인

### 예상되는 로그 순서

1. **빌드 성공**:
```
[INFO] Successfully built image
```

2. **마이그레이션 성공**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial_schema
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, add_metadata_columns
INFO  [alembic.runtime.migration] Running upgrade 0002 -> 0003, add_vector_indexes
INFO  [alembic.runtime.migration] Running upgrade 0003 -> 0004, asyncpg_compatibility_fixes
```

3. **서버 시작**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

4. **헬스체크 통과**:
```
[INFO] Healthcheck passed (GET /health -> 200)
```

### 배포 상태 확인 명령

로컬에서 Railway CLI로 배포 상태 모니터링:

```bash
# 최신 배포 상태 확인
railway status

# 실시간 로그 모니터링
railway logs

# 특정 배포 ID의 로그 확인
railway logs --deployment <deployment-id>
```

## 문제 해결

### pgvector 활성화 후에도 실패하는 경우

1. **확장 버전 확인**:
```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

2. **현재 데이터베이스 확인**:
```sql
SELECT current_database();
```

3. **권한 확인**:
```sql
SELECT * FROM pg_roles WHERE rolname = current_user;
```

### Alembic 마이그레이션 실패

마이그레이션이 실패하면 Railway 대시보드에서:

1. PostgreSQL 서비스 → **Variables** 탭
2. `DATABASE_URL` 값 복사
3. 로컬에서 테스트:
```bash
export DATABASE_URL="<copied-url>"
alembic upgrade heads
```

## 기술적 세부사항

### pgvector란?

- **목적**: PostgreSQL에서 벡터 유사도 검색 지원
- **사용처**: dt-rag의 하이브리드 검색 엔진 (BM25 + Vector Search)
- **데이터 타입**: `vector(dimension)` - 예: `vector(1536)` for OpenAI embeddings

### dt-rag에서의 사용

```python
# apps/database/models.py
class DocumentChunk(Base):
    embedding = Column(Vector(1536))  # pgvector 타입 사용
```

```sql
-- Alembic migration 0004_asyncpg_compatibility_fixes.py:86
CREATE INDEX idx_chunks_embedding
ON document_chunks
USING ivfflat (embedding vector_cosine_ops);
```

### Railway PostgreSQL 버전

- **PostgreSQL 버전**: 17
- **pgvector 지원**: ✅ 기본 제공 (활성화만 필요)
- **Extension 경로**: `/usr/share/postgresql/17/extension/vector.control`

## 일회성 설정

pgvector 확장은 **한 번만 활성화하면 됩니다**:

- ✅ 데이터베이스가 삭제되지 않는 한 영구 유지
- ✅ 모든 이후 배포에서 자동으로 사용 가능
- ✅ 스키마 변경이나 마이그레이션 시 재설정 불필요

## 참고 자료

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Railway PostgreSQL Docs](https://docs.railway.app/databases/postgresql)
- [Railway Extensions](https://docs.railway.app/databases/postgresql#extensions)
