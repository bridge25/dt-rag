# SQLite ↔ PostgreSQL 데이터베이스 상태 분석 보고서

**분석일**: 2025-10-09
**분석자**: Claude (MoAI-ADK v0.2.13)
**목적**: SQLite와 PostgreSQL 사용 현황 및 전환 이력 파악

---

## 🎯 핵심 결론

**현재 상태**: ⚠️ **이중 데이터베이스 구성** (PostgreSQL + SQLite 동시 존재)

### 요약
1. ✅ **PostgreSQL 완전 구성됨** - Docker 컨테이너 실행 중, 14개 테이블, 데이터 존재
2. ⚠️  **프로덕션 배포는 SQLite 사용** - 빠른 테스트를 위한 임시 설정
3. ⚠️  **코드 기본값과 실제 사용의 불일치** - 혼란 가능성 있음

---

## 📊 현재 데이터베이스 상태

### 1. PostgreSQL (포트 5432)

#### 컨테이너 상태
```
이름: dt_rag_postgres
상태: Up 26 hours (healthy)
포트: 0.0.0.0:5432->5432/tcp
```

#### 테이블 현황
```
총 14개 테이블:
1. alembic_version
2. api_key_audit_log
3. api_key_usage
4. api_keys
5. case_bank
6. chunks
7. doc_taxonomy
8. documents
9. embeddings
10. ingestion_jobs
11. search_logs
12. taxonomy_edges
13. taxonomy_migrations
14. taxonomy_nodes
```

#### 데이터 현황
```
Documents: 3
Chunks: 3
Taxonomy Nodes: 6
API Keys: 6
```

**평가**: ✅ **완전히 작동 가능한 프로덕션 환경**

---

### 2. SQLite (dt_rag_production.db)

#### 파일 상태
```
파일명: dt_rag_production.db
크기: 128KB
최종 수정: 2025-10-09 20:27
```

#### 데이터 현황
```
Documents: 3
Chunks: 3
Taxonomy Nodes: 6
```

**평가**: ✅ **PostgreSQL과 동일한 데이터 보유**

---

## 🔍 코드 레벨 분석

### 1. db_session.py (기본 설정)

**파일**: `apps/core/db_session.py:16`

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag"  # 기본값
)
```

**의미**:
- 환경 변수가 없으면 **PostgreSQL 사용**
- 이는 개발자가 PostgreSQL을 프로덕션 기본값으로 의도했음을 나타냄

---

### 2. 프로덕션 환경 스크립트

**파일**: `/tmp/production_env.sh:6`

```bash
# 데이터베이스 (SQLite - 프로덕션에서는 PostgreSQL 권장)
export DATABASE_URL=sqlite+aiosqlite:///./dt_rag_production.db
```

**의미**:
- 최근 프로덕션 배포 작업에서 **SQLite로 설정**
- 주석으로 "PostgreSQL 권장"이라고 명시
- **임시 설정으로 추정**

---

### 3. 배포 보고서 분석

#### 최근 배포 이력 (2025-10-09)

**17:41** - `production-readiness-assessment.md`
- 프로덕션 준비도 평가 시작

**20:14** - `deployment-preparation-complete.md`
```markdown
DATABASE_URL=sqlite+aiosqlite:///./dt_rag_test.db  # 테스트용
```

**20:20** - `production-deployment-ready.md`
```markdown
DATABASE_URL=sqlite+aiosqlite:///./dt_rag_production.db
```

**20:29** - `production-deployment-complete.md`
```markdown
export DATABASE_URL=sqlite+aiosqlite:///./dt_rag_production.db
```

**분석**:
- 2025-10-09 저녁 배포 작업 중 SQLite로 전환
- GEMINI_API_KEY를 찾아 적용하는 작업과 동시 진행
- **빠른 테스트를 위한 임시 조치로 추정**

---

## 🤔 왜 SQLite로 전환했을까?

### 추정 원인

#### 1. GEMINI_API_KEY 통합 작업 (2025-10-09 20:00~20:30)
```
이전 대화 맥락:
- 사용자: "gemini api는 내가 이미 여러번 제공했었어 그 키를 찾아서 입력해줘"
- 작업: .env에서 실제 키 찾아서 프로덕션 환경에 적용
- 목적: 빠른 테스트 및 검증
```

**SQLite 선택 이유**:
- ✅ **즉시 실행 가능** (PostgreSQL 연결 설정 불필요)
- ✅ **간단한 설정** (파일 하나로 완결)
- ✅ **빠른 검증** (API 키 테스트가 주 목적)

#### 2. API Key 생성 및 테스트 작업
```
작업 순서:
1. 프로덕션 데이터베이스 초기화
2. API Keys 테이블 생성
3. Admin/Write API Key 생성
4. API 엔드포인트 테스트
```

**SQLite 선택 이유**:
- ✅ **격리된 테스트 환경** (PostgreSQL 데이터에 영향 없음)
- ✅ **빠른 초기화** (새 DB 파일 생성만으로 완료)

---

## 📈 데이터 동기화 상태

### 데이터 비교

| 항목 | PostgreSQL | SQLite | 일치 여부 |
|------|-----------|--------|----------|
| Documents | 3 | 3 | ✅ |
| Chunks | 3 | 3 | ✅ |
| Taxonomy Nodes | 6 | 6 | ✅ |
| API Keys | 6 | ? | ❓ |

**결론**:
- 기본 데이터는 동일 (문서, 청크, 분류체계)
- API Keys는 각 데이터베이스에서 독립적으로 생성됨

---

## ⚠️ 현재 문제점

### 1. 이중 데이터베이스 운영의 혼란
```
문제:
- 코드 기본값: PostgreSQL
- 프로덕션 스크립트: SQLite
- README 문서: PostgreSQL 강조
```

**영향**:
- 개발자가 어느 DB를 사용하는지 혼란
- 데이터 불일치 가능성
- 배포 시 환경 변수 누락 위험

### 2. README vs 실제 구현 불일치
```
README 강조:
"✅ PostgreSQL + pgvector 연결 - 실제 벡터 검색"

실제 프로덕션:
SQLite 사용 중 (dt_rag_production.db)
```

### 3. API Key 데이터 분리
```
PostgreSQL API Keys: 6개
SQLite API Keys: ?개 (아마 1-2개)
```

**문제**:
- PostgreSQL로 전환 시 API Key 재생성 필요
- 또는 데이터 마이그레이션 작업 필요

---

## 💡 권장 조치

### 즉시 조치 (우선순위: 높음)

#### 1. 프로덕션 데이터베이스 명확화

**Option A: PostgreSQL로 통일 (권장)**
```bash
# /tmp/production_env.sh 수정
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag

# API 서버 재시작
source /tmp/production_env.sh
python -m apps.api.main
```

**장점**:
- ✅ README 문서와 일치
- ✅ 확장성 우수
- ✅ pgvector 벡터 검색 활용
- ✅ 이미 26시간 동안 안정적으로 실행 중

**단점**:
- ⚠️  API Key 재생성 필요 (또는 마이그레이션)

**Option B: SQLite 유지 + 문서 수정**
```markdown
README에 명시:
## 데이터베이스 선택
- **현재 프로덕션**: SQLite (빠른 시작, 간단한 설정)
- **확장 가능**: PostgreSQL + pgvector (권장)
```

**장점**:
- ✅ 현재 작동 중인 환경 유지
- ✅ 빠른 배포 가능

**단점**:
- ❌ 확장성 제한
- ❌ pgvector 미사용
- ❌ README와 불일치

#### 2. 환경 변수 관리 개선

**현재 문제**:
```bash
/tmp/production_env.sh  # 임시 파일 위치
```

**권장 방법**:
```bash
# 프로젝트 루트에 .env.production 생성
cp .env.example .env.production

# .env.production 편집
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag
GEMINI_API_KEY=AIzaSyCKmR4jxB8Gg2TfCBqmz7k850YwplS9EhY
ENVIRONMENT=production
```

---

### 중기 조치 (우선순위: 중간)

#### 1. 데이터 마이그레이션 스크립트 작성

**목적**: SQLite → PostgreSQL 안전한 전환

```python
# scripts/migrate_sqlite_to_postgres.py

async def migrate_api_keys():
    """API Keys를 SQLite에서 PostgreSQL로 마이그레이션"""
    # SQLite에서 읽기
    sqlite_engine = create_async_engine("sqlite+aiosqlite:///./dt_rag_production.db")
    async with AsyncSession(sqlite_engine) as sqlite_session:
        result = await sqlite_session.execute(select(APIKey))
        api_keys = result.scalars().all()

    # PostgreSQL에 쓰기
    pg_engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag")
    async with AsyncSession(pg_engine) as pg_session:
        for key in api_keys:
            pg_session.add(key)
        await pg_session.commit()
```

#### 2. README 명확화

**추가할 섹션**:
```markdown
## 🗄️ 데이터베이스 선택

### 개발/테스트
- **SQLite**: 빠른 시작, 제로 설정
- 파일: `dt_rag_test.db`, `dt_rag_production.db`

### 프로덕션 (권장)
- **PostgreSQL + pgvector**: 확장성, 고성능
- Docker: `docker-compose up -d`
- 포트: 5432

### 전환 가이드
```bash
# SQLite → PostgreSQL 마이그레이션
python scripts/migrate_sqlite_to_postgres.py

# 환경 변수 변경
export DATABASE_URL=postgresql+asyncpg://...
```
```

---

## 📊 통계 요약

### 데이터베이스 현황
```
PostgreSQL:
  - 상태: ✅ 실행 중 (26시간)
  - 테이블: 14개
  - 데이터: 3 documents, 6 taxonomy nodes
  - 사용: 코드 기본값, 테스트 스크립트

SQLite:
  - 상태: ✅ 파일 존재 (128KB)
  - 데이터: PostgreSQL과 동일
  - 사용: 프로덕션 배포 스크립트
```

### 최근 변경 이력
```
2025-10-09 17:41  프로덕션 준비도 평가
2025-10-09 20:14  배포 준비 (SQLite 테스트)
2025-10-09 20:20  GEMINI_API_KEY 적용
2025-10-09 20:27  프로덕션 배포 완료 (SQLite)
```

---

## 🎯 최종 권고안

### 즉시 실행 권장: PostgreSQL로 통일

**실행 계획**:
```bash
# 1. API Key를 PostgreSQL에 생성
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag
python create_admin_api_key.py

# 2. 프로덕션 환경 스크립트 업데이트
vim /tmp/production_env.sh
# DATABASE_URL을 PostgreSQL로 변경

# 3. API 서버 재시작
pkill -f uvicorn
source /tmp/production_env.sh
python -m apps.api.main

# 4. 테스트
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "X-API-Key: <new-postgres-key>" \
  -d '{"q":"test","final_topk":1}'
```

**소요 시간**: 5-10분

**리스크**: 낮음 (PostgreSQL은 이미 26시간 동안 안정적으로 실행 중)

---

## 📝 결론

**질문에 대한 답변**:
> "SQLite에서 PostgreSQL로의 확장은 이미 작업한 것으로 기억하는데 그 이후 수정을 여러번 거듭하며 다시 SQLite로 되어있는거 아닌가?"

**답변**: ✅ **정확한 추측입니다.**

1. ✅ **PostgreSQL은 완전히 구성되어 있음**
   - Docker 컨테이너 실행 중 (26시간)
   - 14개 테이블 모두 생성됨
   - 데이터 존재 (3 documents, 6 taxonomy nodes)

2. ✅ **최근 프로덕션 배포에서 SQLite로 전환**
   - 날짜: 2025-10-09 20:00~20:30
   - 목적: GEMINI_API_KEY 빠른 테스트
   - 방법: `/tmp/production_env.sh`에 SQLite 설정

3. ⚠️  **의도치 않은 이중 구성 상태**
   - PostgreSQL: 설정되어 있지만 미사용
   - SQLite: 프로덕션 배포에 사용 중
   - 혼란 가능성 높음

**권장 사항**: PostgreSQL로 즉시 통일 (5-10분 소요)

---

**보고서 생성**: 2025-10-09 21:10 (KST)
**분석 방법**:
- Docker 컨테이너 상태 확인
- 데이터베이스 데이터 비교
- 코드 및 환경 변수 분석
- Git 이력 및 배포 보고서 검토
