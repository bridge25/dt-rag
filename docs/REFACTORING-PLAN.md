# Norade 체계적 리팩토링 계획서

**프로젝트**: Norade (구 DT-RAG) v1.8.1
**작성일**: 2025-11-30
**기반 문서**: [CODE-REVIEW-REPORT.md](./CODE-REVIEW-REPORT.md)
**총 예상 기간**: 5주 (25 영업일)
**목표**: 1인 개발자 지속 가능한 운영을 위한 자동화율 90%+ 달성

---

## 목차

1. [리팩토링 원칙](#1-리팩토링-원칙)
2. [Phase 0: 사전 준비](#2-phase-0-사전-준비)
3. [Phase 1: Critical 이슈 해결](#3-phase-1-critical-이슈-해결)
4. [Phase 2: High 이슈 해결](#4-phase-2-high-이슈-해결)
5. [Phase 3: 구조 개선](#5-phase-3-구조-개선)
6. [Phase 4: 품질 강화](#6-phase-4-품질-강화)
7. [**🤖 자동화 트랙: 1인 개발자 생존 전략**](#7-자동화-트랙-1인-개발자-생존-전략) ← NEW!
8. [롤백 전략](#8-롤백-전략)
9. [체크리스트](#9-체크리스트)

---

## 1. 리팩토링 원칙

### 1.1 안전한 리팩토링 원칙

```
┌─────────────────────────────────────────────────────────┐
│              Safe Refactoring Principles                 │
├─────────────────────────────────────────────────────────┤
│  1. 테스트 먼저 (Test First)                             │
│     → 변경 전 테스트 커버리지 확보                        │
│                                                          │
│  2. 작은 단위 커밋 (Small Commits)                       │
│     → 단일 책임 원칙 적용, 롤백 용이                      │
│                                                          │
│  3. 기능 동결 (Feature Freeze)                           │
│     → 리팩토링 중 신규 기능 추가 금지                     │
│                                                          │
│  4. 점진적 변경 (Incremental Changes)                    │
│     → Big Bang 금지, 단계별 검증                         │
│                                                          │
│  5. 문서화 우선 (Documentation First)                    │
│     → 변경 전 영향 범위 문서화                           │
└─────────────────────────────────────────────────────────┘
```

### 1.2 브랜치 전략

```
master
  │
  ├── feature/refactor-phase-1-critical
  │   ├── fix/qtable-persistence
  │   ├── fix/import-paths
  │   └── fix/reranker-spec
  │
  ├── feature/refactor-phase-2-high
  │   ├── fix/postgres-test-env
  │   ├── fix/search-service-naming
  │   └── feat/frontend-tests
  │
  └── feature/refactor-phase-3-structure
      ├── refactor/database-split
      └── chore/branding-cleanup
```

### 1.3 위험도 분류

| 위험도 | 기준 | 대응 |
|--------|------|------|
| 🔴 High | DB 스키마 변경, 핵심 로직 수정 | 스테이징 필수, 롤백 계획 |
| 🟡 Medium | 인터페이스 변경, 모듈 분리 | 로컬 테스트 후 배포 |
| 🟢 Low | 명칭 변경, 문서 수정 | 즉시 배포 가능 |

---

## 2. Phase 0: 사전 준비 (Day 1)

### 2.1 현재 상태 스냅샷

```bash
# 현재 테스트 커버리지 기록
pytest apps/api --cov=apps/api --cov-report=html
# 결과: coverage_baseline.html

# 현재 기능 테스트 기록
./scripts/e2e-test.sh > baseline_e2e_results.txt

# DB 스키마 덤프
pg_dump -s dt_rag > schema_baseline.sql
```

### 2.2 테스트 환경 확인

| 항목 | 상태 | 조치 |
|------|------|------|
| Unit Tests | ✅ 42개 | 기존 유지 |
| Integration Tests | ✅ 33개 | 기존 유지 |
| E2E Tests | ⚠️ 확인 필요 | 커버리지 측정 |
| PostgreSQL 테스트 | ❌ 부재 | Docker Compose 추가 |

### 2.3 Feature Flag 준비

```python
# apps/api/env_manager.py에 추가
REFACTORING_FLAGS = {
    "use_persistent_qtable": False,     # Phase 1
    "use_new_import_paths": False,      # Phase 1
    "use_cross_encoder_reranker": False, # Phase 1 (선택)
    "use_postgres_test": False,         # Phase 2
}
```

### 📋 Phase 0 체크리스트

> **완료 조건**: 모든 항목 체크 시 Phase 1 진행 가능

#### 준비 작업
- [ ] 테스트 커버리지 기준선 기록 (`pytest --cov` 실행 → `coverage_baseline.html`)
- [ ] E2E 테스트 결과 스냅샷 저장
- [ ] DB 스키마 백업 완료 (`pg_dump -s dt_rag > schema_baseline.sql`)

#### 환경 구성
- [ ] Feature Flag 환경 변수 설정 (`.env`에 `REFACTORING_FLAGS` 추가)
- [ ] 테스트용 Docker Compose 확인 (`docker-compose.test.yml`)
- [ ] 리팩토링 브랜치 생성 (`feature/refactor-phase-1-critical`)

#### 자동화 병행 (Week 1)
- [ ] Pre-commit hooks 설치 (`pre-commit install`)
- [ ] `.pre-commit-config.yaml` 생성 및 테스트

**다음 단계**: → Phase 1로 이동

---

## 3. Phase 1: Critical 이슈 해결 (Day 2-8)

### 3.1 🔴 Task 1: Import 경로 오류 수정

**위험도**: 🟢 Low | **예상 소요**: 1시간 | **담당**: Backend

#### 현재 상태
```python
# main.py:243 - 오류
from cache.redis_manager import get_redis_manager

# main.py:340 - 오류
from routers.monitoring import track_request_metrics
```

#### 수정 계획
```python
# 옵션 A: 절대 경로 사용 (권장)
from apps.api.cache.redis_manager import get_redis_manager
from apps.api.routers.monitoring import track_request_metrics

# 옵션 B: 상대 경로 사용
from .cache.redis_manager import get_redis_manager
from .routers.monitoring import track_request_metrics
```

#### 검증 방법
```bash
# 서버 구동 테스트
cd apps/api && python -c "import main"

# 전체 임포트 검증
python -m py_compile apps/api/**/*.py
```

#### 롤백 계획
```bash
git revert <commit-hash>  # 단일 커밋으로 롤백 가능
```

---

### 3.2 🔴 Task 2: Q-Table 영속성 마이그레이션

**위험도**: 🔴 High | **예상 소요**: 2-3일 | **담당**: Backend

#### 현재 상태 (문제)
```python
# database.py:1893
class QTableDAO:
    def __init__(self) -> None:
        self.q_table_storage: Dict[str, List[float]] = {}  # 인메모리!
```

#### 마이그레이션 옵션

| 옵션 | 장점 | 단점 | 복잡도 |
|------|------|------|--------|
| **A. PostgreSQL JSON** | 기존 DB 활용, 트랜잭션 | 쿼리 복잡 | 중 |
| **B. Redis** | 빠른 접근, TTL 지원 | 추가 인프라 | 중 |
| **C. 파일 기반** | 단순, 추가 의존성 없음 | 동시성 이슈 | 낮 |

#### 권장: 옵션 A (PostgreSQL JSON)

```python
# 새로운 테이블 스키마
class QTableEntry(Base):
    __tablename__ = "q_table_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    q_values: Mapped[dict] = mapped_column(JSON)  # List[float]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(Integer, default=0)
```

#### 마이그레이션 단계

```
Day 2:
├── 1. QTableEntry 모델 생성
├── 2. Alembic 마이그레이션 작성
└── 3. QTableDAO 인터페이스 유지, 구현 변경

Day 3:
├── 4. Feature Flag로 새 구현 활성화
├── 5. 기존 인메모리 데이터 마이그레이션 스크립트
└── 6. 통합 테스트

Day 4:
├── 7. 스테이징 배포 및 검증
└── 8. 프로덕션 롤아웃
```

#### Alembic 마이그레이션
```python
# alembic/versions/xxxx_add_qtable_persistence.py
def upgrade():
    op.create_table(
        'q_table_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('state_hash', sa.String(64), unique=True, index=True),
        sa.Column('q_values', sa.JSON()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('access_count', sa.Integer(), default=0),
    )

def downgrade():
    op.drop_table('q_table_entries')
```

#### 새로운 QTableDAO 구현
```python
class PersistentQTableDAO:
    """PostgreSQL 기반 Q-Table DAO"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_q_table(self, state_hash: str, q_values: List[float]) -> None:
        entry = await self.session.get(QTableEntry, state_hash)
        if entry:
            entry.q_values = q_values
            entry.updated_at = datetime.now(timezone.utc)
            entry.access_count += 1
        else:
            entry = QTableEntry(
                state_hash=state_hash,
                q_values=q_values,
                updated_at=datetime.now(timezone.utc)
            )
            self.session.add(entry)
        await self.session.commit()

    async def load_q_table(self, state_hash: str) -> Optional[List[float]]:
        entry = await self.session.get(QTableEntry, state_hash)
        return entry.q_values if entry else None
```

#### 롤백 계획
```bash
# DB 롤백
alembic downgrade -1

# 코드 롤백
git revert <commit-range>

# Feature Flag로 즉시 비활성화
REFACTORING_FLAGS["use_persistent_qtable"] = False
```

---

### 3.3 🔴 Task 3: HybridScoreReranker 명세 정렬

**위험도**: 🟡 Medium | **예상 소요**: 3-5일 | **담당**: ML/Backend

#### 현재 상태 (문제)
```python
class HybridScoreReranker:
    """Heuristic-based reranking"""  # 명세: Cross-Encoder

    def rerank(self, ...):
        return self._heuristic_rerank(...)  # 휴리스틱 사용
```

#### 해결 옵션

| 옵션 | 설명 | 검색 품질 | 비용 |
|------|------|-----------|------|
| **A. 명세 수정** | 문서를 현재 구현에 맞춤 | 유지 | 낮음 |
| **B. Cross-Encoder 구현** | sentence-transformers 연동 | 향상 | 높음 |
| **C. 하이브리드** | 휴리스틱 + 선택적 CE | 유연 | 중간 |

#### 권장: 옵션 C (하이브리드 접근)

```python
class HybridScoreReranker:
    """
    Hybrid reranking strategy:
    - Default: Fast heuristic scoring
    - Optional: Cross-Encoder for high-precision queries
    """

    def __init__(self, use_cross_encoder: bool = False):
        self.use_cross_encoder = use_cross_encoder
        self._cross_encoder = None

        if use_cross_encoder:
            self._load_cross_encoder()

    def _load_cross_encoder(self):
        from sentence_transformers import CrossEncoder
        self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def rerank(self, query: str, results: List[SearchResult], top_k: int = 5):
        if self.use_cross_encoder and self._cross_encoder:
            return self._cross_encoder_rerank(query, results, top_k)
        return self._heuristic_rerank(query, results, top_k)
```

#### 명세 수정 (옵션 A 선택 시)
```markdown
## 검색 아키텍처

### Reranking 전략
- **기본**: 휴리스틱 기반 품질 점수 (term overlap, length penalty, diversity)
- **고급** (선택적): Cross-Encoder 모델 지원 (v2.0 예정)
```

### 📋 Phase 1 체크리스트

> **완료 조건**: 모든 Critical 이슈 해결 및 테스트 통과

#### Task 1: Import 경로 수정
- [ ] `main.py:243` → `from apps.api.cache.redis_manager import get_redis_manager`
- [ ] `main.py:340` → `from apps.api.routers.monitoring import track_request_metrics`
- [ ] `python -c "import main"` 성공 확인
- [ ] 전체 임포트 검증 통과 (`python -m py_compile apps/api/**/*.py`)
- [ ] 커밋 생성 (`fix: correct import paths in main.py`)

#### Task 2: Q-Table 영속성
- [ ] `QTableEntry` 모델 생성 (`apps/api/database.py`)
- [ ] Alembic 마이그레이션 작성 (`alembic revision -m "add_qtable_persistence"`)
- [ ] 마이그레이션 적용 (`alembic upgrade head`)
- [ ] `PersistentQTableDAO` 구현 완료
- [ ] Feature Flag 연동 (`use_persistent_qtable`)
- [ ] 통합 테스트 통과
- [ ] 스테이징 배포 및 검증
- [ ] 기존 인메모리 데이터 마이그레이션 (필요시)
- [ ] 커밋 생성 (`feat: add Q-Table PostgreSQL persistence`)

#### Task 3: Reranker 명세 정렬
- [ ] 구현 방향 결정: [ ] 옵션 A (명세 수정) / [ ] 옵션 B (CE 구현) / [ ] 옵션 C (하이브리드)
- [ ] 선택한 옵션 구현 완료
- [ ] 관련 테스트 작성 및 통과
- [ ] 문서 업데이트 (SPEC 또는 README)
- [ ] 커밋 생성 (`feat/docs: align reranker spec with implementation`)

#### 자동화 병행 (Week 1-2)
- [ ] CI Pipeline (`ci.yml`) 구현 및 활성화
- [ ] Dependabot 설정 (`.github/dependabot.yml`)
- [ ] 첫 PR에서 CI 테스트 통과 확인

#### Phase 1 완료 검증
- [ ] 모든 테스트 통과 (`pytest apps/api -v`)
- [ ] 커버리지 기준선 유지 또는 향상
- [ ] 서버 정상 구동 확인 (`uvicorn main:app`)
- [ ] Feature Flag 롤백 테스트 완료

**다음 단계**: → Phase 2로 이동 (브랜치: `feature/refactor-phase-2-high`)

---

## 4. Phase 2: High 이슈 해결 (Day 9-14)

### 4.1 ⚠️ Task 4: PostgreSQL 테스트 환경 통일

**위험도**: 🟡 Medium | **예상 소요**: 2일

#### docker-compose.test.yml 추가
```yaml
version: '3.8'

services:
  postgres_test:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: dt_rag_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis_test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
```

#### 테스트 실행 스크립트
```bash
#!/bin/bash
# scripts/test-with-postgres.sh

docker-compose -f docker-compose.test.yml up -d
sleep 5

export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test
export REDIS_URL=redis://localhost:6380

pytest apps/api -v --cov=apps/api

docker-compose -f docker-compose.test.yml down
```

---

### 4.2 ⚠️ Task 5: SearchService 명칭 충돌 해결

**위험도**: 🟡 Medium | **예상 소요**: 3일

#### 현재 구조 (문제)
```
apps/api/
├── routers/search_router.py    → class SearchService (1,094 LOC)
└── services/search_service.py  → class SearchService (449 LOC)
```

#### 목표 구조
```
apps/api/
├── routers/search_router.py    → SearchRouter (라우터 로직만)
├── services/
│   ├── search_service.py       → SearchService (비즈니스 로직)
│   └── search_orchestrator.py  → SearchOrchestrator (복잡한 검색 조합)
```

#### 마이그레이션 단계

```
Day 9:
├── 1. routers/search_router.py의 SearchService → ProductionSearchHandler 로 이름 변경
├── 2. 기존 호출부 업데이트
└── 3. 테스트

Day 10:
├── 4. services/search_service.py 역할 명확화
├── 5. SearchOrchestrator 분리 (필요시)
└── 6. 통합 테스트

Day 11:
└── 7. 문서 업데이트
```

---

### 4.3 ⚠️ Task 6: 프론트엔드 테스트 추가

**위험도**: 🟢 Low | **예상 소요**: 1주

#### Jest 설정
```javascript
// apps/frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
  ],
};
```

#### 우선 테스트 대상
```
1. stores/ (Zustand 스토어) - 상태 관리 로직
2. lib/api/ - API 클라이언트 함수
3. components/ui/ - 기본 UI 컴포넌트
4. components/chat/ - 채팅 인터페이스
```

### 📋 Phase 2 체크리스트

> **완료 조건**: High 이슈 해결 및 테스트 환경 통일

#### Task 4: PostgreSQL 테스트 환경
- [ ] `docker-compose.test.yml` 생성/수정
- [ ] PostgreSQL 테스트 컨테이너 설정 (port: 5433)
- [ ] Redis 테스트 컨테이너 설정 (port: 6380)
- [ ] `scripts/test-with-postgres.sh` 스크립트 작성
- [ ] 로컬 테스트 통과 확인
- [ ] GitHub Actions CI에 PostgreSQL 서비스 추가
- [ ] CI 테스트 통과 확인
- [ ] 커밋 생성 (`feat: add PostgreSQL test environment`)

#### Task 5: SearchService 명칭 분리
- [ ] `routers/search_router.py` 내 `SearchService` → `ProductionSearchHandler` 리네임
- [ ] 모든 호출부 업데이트 확인 (grep으로 검증)
- [ ] `services/search_service.py` 역할 문서화
- [ ] 필요시 `SearchOrchestrator` 분리
- [ ] 관련 테스트 업데이트 및 통과
- [ ] 커밋 생성 (`refactor: rename SearchService to clarify roles`)

#### Task 6: 프론트엔드 테스트 추가
- [ ] Jest 설정 (`jest.config.js` 생성)
- [ ] `jest.setup.js` 생성
- [ ] `stores/` 테스트 3개 이상 작성
- [ ] `lib/api/` 테스트 3개 이상 작성
- [ ] `components/ui/` 테스트 2개 이상 작성
- [ ] 전체 프론트엔드 테스트 통과 (`npm test`)
- [ ] 커밋 생성 (`test: add frontend Jest tests`)

#### 자동화 병행 (Week 2)
- [ ] CD Pipeline (`deploy.yml`) 구현
- [ ] Railway/Vercel 배포 webhook 설정
- [ ] Staging 환경 배포 테스트
- [ ] Slack 알림 연동

#### Phase 2 완료 검증
- [ ] Backend 테스트 전체 통과 (PostgreSQL 환경)
- [ ] Frontend 테스트 전체 통과
- [ ] Staging 배포 성공
- [ ] SearchService 분리로 인한 regression 없음

**다음 단계**: → Phase 3로 이동 (브랜치: `feature/refactor-phase-3-structure`)

---

## 5. Phase 3: 구조 개선 (Day 15-18)

### 5.1 🟡 Task 7: database.py God Object 분리

**위험도**: 🔴 High | **예상 소요**: 3일

#### 현재 구조 (1,936 LOC)
```python
# apps/api/database.py
- ORM 모델 (Document, Chunk, Agent, Taxonomy...)
- DAO 클래스 (SearchDAO, QTableDAO...)
- 유틸리티 (BM25Scorer...)
- 연결 관리 (engine, session...)
```

#### 목표 구조
```
apps/api/
├── database/
│   ├── __init__.py          # 공개 인터페이스
│   ├── connection.py        # 엔진, 세션 관리
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py      # Document, Chunk
│   │   ├── agent.py         # Agent
│   │   └── taxonomy.py      # Taxonomy
│   ├── daos/
│   │   ├── __init__.py
│   │   ├── search_dao.py    # SearchDAO
│   │   └── q_table_dao.py   # QTableDAO (새 영속성 포함)
│   └── utils/
│       └── bm25_scorer.py   # BM25Scorer
```

#### 마이그레이션 전략

```
1. 기존 database.py 유지 (하위 호환성)
2. 새 패키지 구조 생성
3. 점진적으로 import 변경
4. 기존 database.py를 facade로 유지
5. 충분한 테스트 후 레거시 제거
```

#### Facade 패턴 적용
```python
# apps/api/database.py (레거시 호환)
"""
DEPRECATED: 이 모듈은 레거시 호환성을 위해 유지됩니다.
새로운 코드는 apps.api.database 패키지를 직접 사용하세요.
"""
from apps.api.database.connection import engine, async_session, get_async_session
from apps.api.database.models import Document, Chunk, Agent, Taxonomy
from apps.api.database.daos import SearchDAO, QTableDAO
from apps.api.database.utils import BM25Scorer

__all__ = [
    "engine", "async_session", "get_async_session",
    "Document", "Chunk", "Agent", "Taxonomy",
    "SearchDAO", "QTableDAO", "BM25Scorer",
]
```

### 📋 Phase 3 체크리스트

> **완료 조건**: 구조 개선 완료, 레거시 호환성 유지

#### Task 7: database.py 분리
- [ ] `apps/api/database/` 패키지 디렉토리 생성
- [ ] `database/__init__.py` 생성
- [ ] `database/connection.py` 생성 (engine, session 관련)
- [ ] `database/models/` 디렉토리 생성
  - [ ] `models/__init__.py`
  - [ ] `models/document.py` (Document, Chunk)
  - [ ] `models/agent.py` (Agent)
  - [ ] `models/taxonomy.py` (Taxonomy)
- [ ] `database/daos/` 디렉토리 생성
  - [ ] `daos/__init__.py`
  - [ ] `daos/search_dao.py` (SearchDAO)
  - [ ] `daos/q_table_dao.py` (QTableDAO + PersistentQTableDAO)
- [ ] `database/utils/` 디렉토리 생성
  - [ ] `utils/bm25_scorer.py` (BM25Scorer)
- [ ] 기존 `database.py` → Facade 패턴 적용 (하위 호환)
- [ ] 모든 import 경로 업데이트
- [ ] 전체 테스트 통과 확인
- [ ] 커밋 생성 (`refactor: split database.py into modular package`)

#### 자동화 병행 (Week 3)
- [ ] Health monitoring workflow (`monitoring.yml`) 구현
- [ ] Backup workflow (`backup.yml`) 구현
- [ ] Slack/PagerDuty 알림 연동 테스트

#### Phase 3 완료 검증
- [ ] 모든 기존 테스트 통과 (regression 없음)
- [ ] 새 패키지 구조로 import 가능 확인
- [ ] 레거시 `database.py` import도 여전히 동작
- [ ] 서버 정상 구동 확인

**다음 단계**: → Phase 4로 이동 (브랜치: `feature/refactor-phase-4-quality`)

---

## 6. Phase 4: 품질 강화 (Day 19-20)

### 6.1 브랜딩 통일

```bash
# DT-RAG → Norade 변경 대상
grep -r "DT-RAG\|dt-rag\|dt_rag" --include="*.md" --include="*.py" --include="*.tsx"
```

| 위치 | 변경 전 | 변경 후 |
|------|---------|---------|
| config.py | `dt-rag.com` | `norade.ai` |
| package.json | `dt-rag` | `norade` |
| README.md | DT-RAG | Norade |

### 6.2 프론트엔드 코드 정리 (NEW!)

#### 6.2.1 현재 구조 분석

```
apps/frontend/
├── src/                    # 🆕 NEW - Clean Architecture (미사용!)
│   ├── domain/            # 엔티티, 리포지토리 인터페이스, 유스케이스
│   ├── data/              # 데이터소스, 매퍼, 리포지토리 구현
│   ├── presentation/      # 훅, 스토어, 컨테이너
│   └── shared/            # DI 컨테이너, 설정
│
├── lib/                    # ⚠️ LEGACY - 현재 사용 중
│   └── api/               # agents.ts, client.ts, research.ts, types.ts
│
├── hooks/                  # ⚠️ LEGACY - 현재 사용 중
│   ├── useAgents.ts
│   ├── useAgent.ts
│   └── useCoverageHistory.ts
│
├── stores/                 # ⚠️ LEGACY - 현재 사용 중
│   ├── researchStore.ts
│   └── useTaxonomyStore.ts
│
├── components/             # ⚠️ LEGACY - 현재 사용 중
│   ├── agent-card/
│   ├── agent-detail/
│   ├── chat/
│   ├── constellation/
│   └── ui/
│
└── public/
    └── avatars/robots/     # 🗑️ DEPRECATED (DEPRECATED.md 확인됨)
```

#### 6.2.2 Clean Architecture 마이그레이션 전략

**결정 필요**: Clean Architecture(`src/`) 활성화 여부

| 옵션 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **A. 활성화** | src/ 구조를 실제 사용으로 전환 | 깔끔한 구조, 테스트 용이 | 대규모 변경, 위험 |
| **B. 제거** | src/ 삭제, 기존 구조 유지 | 안정적, 빠름 | 기술 부채 유지 |
| **C. 점진적** | 새 기능만 src/에, 기존은 유지 | 안전, 점진적 전환 | 구조 혼재 |

**권장: 옵션 C (점진적 전환)**

```
Phase 1: src/를 실제 프로덕션에서 사용할 수 있도록 설정
├── tsconfig.json path alias 확인
├── DI 컨테이너 초기화 연결
└── 테스트로 동작 확인

Phase 2: 새 기능은 src/에 작성
├── 새 API 연동 → src/data/datasources/
├── 새 상태관리 → src/presentation/stores/
└── 새 훅 → src/presentation/hooks/

Phase 3: 기존 레거시 점진적 마이그레이션
├── lib/api/ → src/data/
├── hooks/ → src/presentation/hooks/
└── stores/ → src/presentation/stores/
```

#### 6.2.3 레거시 → 신규 매핑

| Legacy 경로 | New 경로 | 마이그레이션 우선순위 |
|-------------|----------|----------------------|
| `lib/api/client.ts` | `src/data/datasources/api-client.ts` | 🔴 높음 (핵심) |
| `lib/api/agents.ts` | `src/data/repositories/agent-repository.ts` | 🟡 중간 |
| `hooks/useAgents.ts` | `src/presentation/hooks/use-agents.ts` | 🟡 중간 |
| `stores/researchStore.ts` | `src/presentation/stores/research-store.ts` | 🔴 높음 |
| `stores/useTaxonomyStore.ts` | `src/presentation/stores/taxonomy-store.ts` | 🟡 중간 |

#### 6.2.4 DEPRECATED 리소스 정리

```bash
# 확인됨: public/avatars/robots/DEPRECATED.md
# → SVG 아바타가 PNG 로봇으로 대체됨

# 삭제 대상
rm -rf apps/frontend/public/avatars/robots/*.svg

# 새로운 에셋 위치 확인
ls apps/frontend/public/assets/agents/nobg/  # 새 로봇 PNG 파일
```

#### 6.2.5 로고 파일 정리

```bash
# 현재 public/ 내 로고 파일들 (정리 필요)
apps/frontend/public/
├── norade-logo-final.png    # ✅ 최종 로고 (유지)
├── norade-logo-main-v2.png  # ❓ 버전 정리 필요
├── norade-logo-main.png     # ❓ 중복 확인
└── unnamed.png              # 🗑️ 삭제 대상

# 정리 후 구조
apps/frontend/public/
├── logo.png                 # 메인 로고 (1개만 유지)
├── logo-dark.png            # 다크모드용 (필요시)
└── favicon.ico              # 파비콘
```

#### 6.2.6 테스트 아티팩트 정리

```bash
# 삭제 대상 (개발 중 생성된 임시 파일)
rm -rf apps/frontend/screenshots/
rm -rf apps/frontend/test-results/
rm apps/frontend/design-compliance-test.spec.ts  # 일회성 테스트
rm apps/frontend/e2e-visual-test.spec.ts          # 일회성 테스트
rm apps/frontend/take-final-screenshots.mjs       # 스크립트

# .gitignore에 추가 (향후 방지)
echo "screenshots/" >> apps/frontend/.gitignore
echo "test-results/" >> apps/frontend/.gitignore
```

### 6.3 루트 디렉토리 정리

```bash
# 이동 대상
mv CODE-REVIEW-REPORT.md docs/
mv REFACTORING-PLAN.md docs/
mv SECURITY-AUDIT-REPORT.md docs/
mv DESIGN-COMPLIANCE-REPORT.md docs/

# 삭제 대상 (생성된 임시 파일)
rm -rf nanobanana-output/
rm 뉴디자인*.png
```

### 📋 Phase 4 체크리스트

> **완료 조건**: 품질 강화 완료, 프로덕션 준비 상태

#### 브랜딩 통일
- [ ] `grep -r "DT-RAG\|dt-rag\|dt_rag"` 실행하여 대상 파일 목록 확보
- [ ] `config.py`: `dt-rag.com` → `norade.ai`
- [ ] `package.json`: `dt-rag` → `norade`
- [ ] `README.md`: DT-RAG → Norade
- [ ] 기타 파일들 브랜딩 업데이트
- [ ] 커밋 생성 (`chore: complete branding from DT-RAG to Norade`)

#### 프론트엔드 정리
- [ ] **구조 결정**: [ ] 옵션 A (src/ 활성화) / [ ] 옵션 B (삭제) / [ ] 옵션 C (점진적)
- [ ] DEPRECATED 리소스 삭제 (`public/avatars/robots/*.svg`)
- [ ] 로고 파일 정리 (최종 1개만 유지 → `logo.png`)
- [ ] 임시 파일 삭제 (`unnamed.png`, 중복 로고들)
- [ ] 테스트 아티팩트 삭제 (`screenshots/`, `test-results/`)
- [ ] 일회성 테스트 파일 삭제 (`design-compliance-test.spec.ts`, `e2e-visual-test.spec.ts`)
- [ ] `.gitignore` 업데이트 (screenshots/, test-results/ 추가)
- [ ] 커밋 생성 (`chore: cleanup frontend deprecated resources`)

#### 루트 디렉토리 정리
- [ ] `docs/` 디렉토리 생성 (없는 경우)
- [ ] `CODE-REVIEW-REPORT.md` → `docs/` 이동
- [ ] `REFACTORING-PLAN.md` → `docs/` 이동
- [ ] `SECURITY-AUDIT-REPORT.md` → `docs/` 이동
- [ ] `DESIGN-COMPLIANCE-REPORT.md` → `docs/` 이동
- [ ] `nanobanana-output/` 삭제
- [ ] `뉴디자인*.png` 삭제
- [ ] 커밋 생성 (`chore: organize root directory`)

#### 자동화 병행 (Week 4-5)
- [ ] Self-healing 미들웨어 구현 (`middleware/self_healing.py`)
- [ ] Circuit Breaker 적용 및 테스트
- [ ] 부하 테스트 실행 (k6 또는 locust)
- [ ] Runbook 문서 작성

#### Phase 4 완료 검증
- [ ] 모든 브랜딩이 Norade로 통일됨
- [ ] 불필요한 파일 없음 (깔끔한 루트 디렉토리)
- [ ] 프론트엔드 구조 정리 완료
- [ ] 프로덕션 배포 준비 완료
- [ ] 최종 테스트 통과

**🎉 리팩토링 완료!** → 프로덕션 배포 및 모니터링 전환

---

## 7. 🤖 자동화 트랙: 1인 개발자 생존 전략

> **핵심 원칙**: "내가 자고 있을 때도 시스템이 스스로 돌아가야 한다"

### 7.1 자동화 철학

```
┌─────────────────────────────────────────────────────────────────┐
│           1인 개발자 자동화 피라미드 (우선순위)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 5: 🎯 Self-Healing (자가 치유)                            │
│           └─ Auto-restart, Circuit Breaker, Chaos Testing       │
│                                                                  │
│  Level 4: 📊 Observability (관측성)                              │
│           └─ 모니터링, 알람, 로그 집계, APM                       │
│                                                                  │
│  Level 3: 🚀 CD - Continuous Deployment (자동 배포)              │
│           └─ 스테이징 자동 배포, 프로덕션 원클릭                   │
│                                                                  │
│  Level 2: 🔒 CI - Quality Gates (품질 검증)                      │
│           └─ 테스트, 린팅, 보안 스캔, 타입 체크                    │
│                                                                  │
│  Level 1: 🔧 Dev Automation (개발 자동화)                        │
│           └─ Pre-commit, 의존성 업데이트, 포맷팅                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 현재 상태 분석

| 영역 | 현재 상태 | 자동화율 | 목표 |
|------|----------|---------|------|
| **CI (테스트)** | ❌ 없음 | 0% | 100% |
| **CD (배포)** | ⚠️ 릴리즈만 | 30% | 90% |
| **모니터링** | ⚠️ Sentry 설정만 | 20% | 95% |
| **백업** | ❌ 없음 | 0% | 100% |
| **의존성** | ❌ 수동 | 0% | 100% |
| **보안 스캔** | ❌ 없음 | 0% | 100% |

**현재 총 자동화율: ~12%** → **목표: 90%+**

### 7.3 자동화 구현 계획

#### 🔧 Tier 1: 필수 (Week 1과 병행)

##### 7.3.1 CI Pipeline - 테스트 자동화

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [main, develop]

jobs:
  # Job 1: Backend 테스트
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: dt_rag_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test-secret-key
        run: |
          uv run pytest apps/api tests/ \
            --cov=apps/api \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=80 \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  # Job 2: Frontend 테스트
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: apps/frontend/package-lock.json

      - name: Install dependencies
        working-directory: apps/frontend
        run: npm ci

      - name: Run lint
        working-directory: apps/frontend
        run: npm run lint

      - name: Run type check
        working-directory: apps/frontend
        run: npx tsc --noEmit

      - name: Run tests (when added)
        working-directory: apps/frontend
        run: npm test --passWithNoTests

      - name: Build check
        working-directory: apps/frontend
        run: npm run build

  # Job 3: Security Scan
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Python security scan (bandit)
        run: |
          pip install bandit
          bandit -r apps/api -ll -ii

  # Job 4: Lint and Format
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Run ruff
        run: uv run ruff check apps/ tests/

      - name: Run ruff format check
        run: uv run ruff format --check apps/ tests/

      - name: Run mypy
        run: uv run mypy apps/api --ignore-missing-imports
```

##### 7.3.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: detect-private-key
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: uv run pytest apps/api -x -q --tb=short
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

#### 🚀 Tier 2: 중요 (Week 2와 병행)

##### 7.3.3 CD Pipeline - 자동 배포

```yaml
# .github/workflows/deploy.yml
name: Deploy Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch

      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.api
          push: true
          tags: ${{ steps.meta.outputs.tags }}-api
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push Frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./apps/frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-frontend
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Deploy to Railway/Render (staging)
        run: |
          # Railway 또는 Render webhook 호출
          curl -X POST "${{ secrets.STAGING_DEPLOY_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d '{"image": "${{ needs.build-and-push.outputs.image_tag }}"}'

      - name: Health check
        run: |
          for i in {1..30}; do
            if curl -s "${{ secrets.STAGING_URL }}/health" | grep -q "ok"; then
              echo "✅ Staging deployment healthy"
              exit 0
            fi
            sleep 10
          done
          echo "❌ Staging health check failed"
          exit 1

      - name: Notify on Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Staging Deploy: ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "${{ job.status == 'success' && '✅' || '❌' }} Staging deployment ${{ job.status }}\nCommit: ${{ github.sha }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

  deploy-production:
    needs: [build-and-push, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    if: github.event.inputs.environment == 'production' || github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to Railway/Render (production)
        run: |
          curl -X POST "${{ secrets.PRODUCTION_DEPLOY_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d '{"image": "${{ needs.build-and-push.outputs.image_tag }}"}'

      - name: Health check
        run: |
          for i in {1..30}; do
            if curl -s "${{ secrets.PRODUCTION_URL }}/health" | grep -q "ok"; then
              echo "✅ Production deployment healthy"
              exit 0
            fi
            sleep 10
          done
          echo "❌ Production health check failed"
          exit 1
```

##### 7.3.4 의존성 자동 업데이트

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"
    groups:
      production-deps:
        patterns:
          - "fastapi*"
          - "sqlalchemy*"
          - "pydantic*"
      dev-deps:
        patterns:
          - "pytest*"
          - "ruff*"
          - "mypy*"

  # npm dependencies
  - package-ecosystem: "npm"
    directory: "/apps/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "javascript"
    groups:
      next-ecosystem:
        patterns:
          - "next*"
          - "react*"

  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "github-actions"
```

#### 📊 Tier 3: 운영 안정화 (Week 3와 병행)

##### 7.3.5 모니터링 & 알람

```yaml
# .github/workflows/monitoring.yml
name: Health Monitoring

on:
  schedule:
    - cron: '*/5 * * * *'  # 5분마다
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest

    steps:
      - name: Check API Health
        id: api_health
        continue-on-error: true
        run: |
          RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            "${{ secrets.PRODUCTION_URL }}/health" \
            --max-time 30)

          if [ "$RESPONSE" = "200" ]; then
            echo "status=healthy" >> $GITHUB_OUTPUT
          else
            echo "status=unhealthy" >> $GITHUB_OUTPUT
            echo "http_code=$RESPONSE" >> $GITHUB_OUTPUT
          fi

      - name: Check Frontend Health
        id: frontend_health
        continue-on-error: true
        run: |
          RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
            "${{ secrets.FRONTEND_URL }}" \
            --max-time 30)

          if [ "$RESPONSE" = "200" ]; then
            echo "status=healthy" >> $GITHUB_OUTPUT
          else
            echo "status=unhealthy" >> $GITHUB_OUTPUT
          fi

      - name: Check Database Connection
        id: db_health
        continue-on-error: true
        run: |
          RESPONSE=$(curl -s "${{ secrets.PRODUCTION_URL }}/health/db" \
            --max-time 30)

          if echo "$RESPONSE" | grep -q "connected"; then
            echo "status=healthy" >> $GITHUB_OUTPUT
          else
            echo "status=unhealthy" >> $GITHUB_OUTPUT
          fi

      - name: Alert on Failure
        if: |
          steps.api_health.outputs.status == 'unhealthy' ||
          steps.frontend_health.outputs.status == 'unhealthy' ||
          steps.db_health.outputs.status == 'unhealthy'
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚨 ALERT: Service Health Check Failed!",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "🚨 *Service Health Check Failed*\n\n• API: ${{ steps.api_health.outputs.status }}\n• Frontend: ${{ steps.frontend_health.outputs.status }}\n• Database: ${{ steps.db_health.outputs.status }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_ALERT_WEBHOOK }}

      - name: Send PagerDuty Alert (Critical)
        if: steps.api_health.outputs.status == 'unhealthy'
        run: |
          curl -X POST "https://events.pagerduty.com/v2/enqueue" \
            -H "Content-Type: application/json" \
            -d '{
              "routing_key": "${{ secrets.PAGERDUTY_KEY }}",
              "event_action": "trigger",
              "payload": {
                "summary": "Norade API is down",
                "severity": "critical",
                "source": "GitHub Actions Health Monitor"
              }
            }'
```

##### 7.3.6 자동 백업

```yaml
# .github/workflows/backup.yml
name: Database Backup

on:
  schedule:
    - cron: '0 3 * * *'  # 매일 오전 3시 (KST 12시)
  workflow_dispatch:

jobs:
  backup:
    runs-on: ubuntu-latest

    steps:
      - name: Create database backup
        run: |
          # PostgreSQL 백업 생성
          PGPASSWORD=${{ secrets.DB_PASSWORD }} pg_dump \
            -h ${{ secrets.DB_HOST }} \
            -U postgres \
            -d dt_rag \
            -F c \
            -f backup_$(date +%Y%m%d_%H%M%S).dump

      - name: Upload to S3/R2
        run: |
          # Cloudflare R2 또는 AWS S3에 업로드
          aws s3 cp backup_*.dump \
            s3://${{ secrets.BACKUP_BUCKET }}/db-backups/ \
            --endpoint-url ${{ secrets.R2_ENDPOINT }}

      - name: Cleanup old backups (30일 이상)
        run: |
          aws s3 ls s3://${{ secrets.BACKUP_BUCKET }}/db-backups/ \
            --endpoint-url ${{ secrets.R2_ENDPOINT }} | \
          while read -r line; do
            createDate=$(echo "$line" | awk '{print $1}')
            if [[ $(date -d "$createDate" +%s) -lt $(date -d "30 days ago" +%s) ]]; then
              fileName=$(echo "$line" | awk '{print $4}')
              aws s3 rm "s3://${{ secrets.BACKUP_BUCKET }}/db-backups/$fileName" \
                --endpoint-url ${{ secrets.R2_ENDPOINT }}
            fi
          done

      - name: Notify on completion
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Daily database backup completed successfully"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

#### 🎯 Tier 4: Self-Healing (Week 4 이후)

##### 7.3.7 자가 치유 시스템

```python
# apps/api/middleware/self_healing.py
"""
Self-Healing Middleware for Production Stability
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit Breaker Pattern Implementation"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.half_open_requests:
                self.state = "CLOSED"
                self.failures = 0
                logger.info("Circuit breaker CLOSED - service recovered")
        else:
            self.failures = 0

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN after {self.failures} failures")

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return datetime.now() > self.last_failure_time + timedelta(seconds=self.recovery_timeout)


class HealthMonitor:
    """Continuous Health Monitoring with Auto-Recovery"""

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_history = deque(maxlen=100)
        self.is_healthy = True

    async def start_monitoring(self):
        while True:
            try:
                health = await self._check_health()
                self.health_history.append({
                    "timestamp": datetime.now(),
                    "healthy": health,
                })

                if not health and self.is_healthy:
                    await self._trigger_recovery()
                    self.is_healthy = False
                elif health and not self.is_healthy:
                    logger.info("Service recovered")
                    self.is_healthy = True

            except Exception as e:
                logger.error(f"Health check failed: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_health(self) -> bool:
        # DB, Redis, 외부 서비스 체크
        checks = await asyncio.gather(
            self._check_db(),
            self._check_redis(),
            self._check_memory(),
            return_exceptions=True
        )
        return all(c is True for c in checks if not isinstance(c, Exception))

    async def _trigger_recovery(self):
        """Auto-recovery actions"""
        logger.warning("Triggering auto-recovery...")

        # 1. 캐시 클리어
        await self._clear_caches()

        # 2. 커넥션 풀 리셋
        await self._reset_connection_pools()

        # 3. 외부 알림
        await self._send_alert("Service degradation detected, auto-recovery initiated")
```

### 7.4 인프라 권장 사항 (1인 개발자용)

#### 7.4.1 호스팅 플랫폼 비교

| 플랫폼 | 비용 (월) | 자동화 수준 | 관리 부담 | 추천 |
|--------|----------|------------|----------|------|
| **Railway** | $5-20 | ⭐⭐⭐⭐⭐ | 최소 | ✅ 1순위 |
| **Render** | $7-25 | ⭐⭐⭐⭐ | 낮음 | ✅ 2순위 |
| **Fly.io** | $5-15 | ⭐⭐⭐⭐ | 낮음 | 옵션 |
| **Vercel** (Frontend) | $0-20 | ⭐⭐⭐⭐⭐ | 최소 | ✅ 프론트엔드 |
| AWS/GCP | $50+ | ⭐⭐ | 높음 | ❌ 비추천 |

#### 7.4.2 권장 스택

```
┌─────────────────────────────────────────────────────┐
│              1인 개발자 권장 스택                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Frontend: Vercel (무료 ~ $20)                       │
│  ├─ 자동 배포 (git push)                             │
│  ├─ Edge Functions                                   │
│  └─ Analytics 내장                                   │
│                                                      │
│  Backend: Railway ($5 ~ $20)                         │
│  ├─ Docker 자동 배포                                  │
│  ├─ PostgreSQL 관리형                                 │
│  ├─ Redis 내장                                        │
│  └─ 자동 스케일링                                     │
│                                                      │
│  Monitoring: 무료 조합                                │
│  ├─ Sentry (에러 트래킹, 무료 5K)                     │
│  ├─ Better Uptime (상태 모니터링, 무료)              │
│  ├─ Langfuse (LLM 옵저버빌리티, 무료)                │
│  └─ GitHub Actions (CI/CD, 무료 2000분)              │
│                                                      │
│  Backup: Cloudflare R2 ($0.015/GB)                   │
│                                                      │
│  월 예상 비용: $10-50                                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 7.5 자동화 구현 일정

```
Week 1 (Phase 0-1과 병행):
├── Day 1: Pre-commit hooks 설정
├── Day 2-3: CI Pipeline (ci.yml) 구현
└── Day 4-5: Dependabot 설정

Week 2 (Phase 1-2와 병행):
├── Day 6-7: CD Pipeline (deploy.yml) 구현
├── Day 8-9: Railway/Vercel 배포 설정
└── Day 10: Staging 환경 구성

Week 3 (Phase 2-3와 병행):
├── Day 11-12: Monitoring workflow 구현
├── Day 13-14: Backup workflow 구현
└── Day 15: Slack/PagerDuty 알림 연동

Week 4 (Phase 3-4와 병행):
├── Day 16-18: Self-healing 미들웨어 구현
├── Day 19: Circuit Breaker 적용
└── Day 20: 전체 자동화 테스트

Week 5 (마무리):
├── Day 21-22: 부하 테스트 및 튜닝
├── Day 23-24: 문서화 및 Runbook 작성
└── Day 25: 프로덕션 검증
```

### 7.6 자동화 체크리스트

#### Tier 1: 필수 (Week 1)
- [ ] Pre-commit hooks 설치 및 설정
- [ ] CI Pipeline (테스트) 구현
- [ ] 코드 커버리지 80% 이상 게이트
- [ ] Dependabot 설정

#### Tier 2: 중요 (Week 2)
- [ ] CD Pipeline (자동 배포) 구현
- [ ] Staging 환경 구성
- [ ] Production 환경 구성
- [ ] 배포 알림 (Slack) 연동

#### Tier 3: 운영 (Week 3)
- [ ] Health check monitoring 구현
- [ ] 알람 시스템 (Slack/PagerDuty)
- [ ] 자동 백업 구현
- [ ] 백업 복구 테스트

#### Tier 4: 고급 (Week 4-5)
- [ ] Circuit Breaker 구현
- [ ] Self-healing 미들웨어
- [ ] Chaos Engineering 테스트
- [ ] Runbook 문서화

---

## 8. 롤백 전략

### 8.1 즉각 롤백 (30분 이내)

```bash
# Feature Flag 비활성화
export REFACTORING_FLAGS='{"use_persistent_qtable": false}'

# 서버 재시작
docker-compose restart api
```

### 8.2 코드 롤백 (1시간 이내)

```bash
# 특정 커밋으로 롤백
git log --oneline -10
git revert <commit-hash>

# 또는 브랜치 전체 롤백
git checkout master
git branch -D feature/refactor-phase-X
```

### 8.3 데이터베이스 롤백 (2시간 이내)

```bash
# Alembic 다운그레이드
alembic downgrade -1

# 백업에서 복원 (최악의 경우)
pg_restore -d dt_rag backup_before_refactor.sql
```

---

## 9. 체크리스트

### Phase 0: 사전 준비
- [ ] 테스트 커버리지 기준선 기록
- [ ] E2E 테스트 결과 기록
- [ ] DB 스키마 백업
- [ ] Feature Flag 환경 설정

### Phase 1: Critical 이슈
- [ ] Import 경로 수정 완료
- [ ] Import 테스트 통과
- [ ] Q-Table 마이그레이션 스키마 작성
- [ ] Q-Table 마이그레이션 테스트
- [ ] Q-Table 프로덕션 배포
- [ ] Reranker 전략 결정 (명세 수정 or 구현)
- [ ] Reranker 변경 완료

### Phase 2: High 이슈
- [ ] PostgreSQL 테스트 환경 구성
- [ ] CI/CD에 PostgreSQL 테스트 추가
- [ ] SearchService 명칭 분리 완료
- [ ] 프론트엔드 Jest 설정
- [ ] 핵심 컴포넌트 테스트 10개 이상

### Phase 3: 구조 개선
- [ ] database.py 패키지 분리
- [ ] 레거시 facade 유지
- [ ] import 경로 업데이트

### Phase 4: 품질 강화
- [ ] 브랜딩 통일 (DT-RAG → Norade)
- [ ] 프론트엔드 구조 결정 (src/ Clean Architecture 활성화 방식)
- [ ] DEPRECATED 리소스 정리 (avatars/robots/)
- [ ] 로고 파일 정리 및 표준화
- [ ] 테스트 아티팩트 삭제 (screenshots/, test-results/)
- [ ] .gitignore 업데이트
- [ ] 루트 디렉토리 정리
- [ ] 문서 최종 검토

---

## 타임라인 요약

```
Week 1 (Day 1-5):
├── Day 1: Phase 0 - 사전 준비
├── Day 2-4: Phase 1 - Q-Table 마이그레이션
└── Day 5: Phase 1 - Import 수정, Reranker 결정

Week 2 (Day 6-10):
├── Day 6-8: Phase 1 - Reranker 작업 완료
├── Day 9-10: Phase 2 - PostgreSQL 테스트 환경
└── Day 10: Phase 2 - SearchService 명칭 분리 시작

Week 3 (Day 11-15):
├── Day 11-12: Phase 2 - SearchService 완료
├── Day 13-14: Phase 2 - 프론트엔드 테스트
└── Day 15: Phase 3 - database.py 분리 시작

Week 4 (Day 16-20):
├── Day 16-18: Phase 3 - database.py 분리 완료
├── Day 19: Phase 4 - 브랜딩, 정리
└── Day 20: 최종 검토 및 문서화
```

---

**작성**: Claude (Alfred)
**검토 필요**: 팀 리드
**승인 상태**: 대기 중

*Last Updated: 2025-11-30*
