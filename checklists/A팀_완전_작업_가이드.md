# 🅰️ A팀 (Taxonomy & Data Platform) 완전 작업 가이드

> **프로젝트**: Dynamic Taxonomy RAG v1.8.1  
> **기간**: 2025-09-02 ~ 2025-09-09 18:00 (KST) - Week-1  
> **최종 출시**: 2025-09-16 10:00 (KST)  
> **담당**: A팀 (Taxonomy & Data Platform)

## 🎯 프로젝트 핵심 개요

### 비전
"**동적으로 심화되는 다단계 카테고리화(DAG+버전/롤백)**로 지식을 정리하고, **트리형 UI**를 통해 사용자에게 투명하게 노출하며, **선택한 카테고리 범위만 사용하는 전문 에이전트**를 몇 클릭으로 만들고 운영할 수 있는 안전한 지식 운영 제품."

### 핵심 성공 지표 (NFR 가드)
- **성능**: p95≤4s, p50≤1.5s
- **비용**: 평균 비용/쿼리 ≤₩10
- **품질**: Faithfulness ≥ 0.85 (RAGAS 기반)
- **운영**: 롤백 TTR ≤ 15분
- **사용성**: CSAT ≥ 4.3/5.0

## 🅰️ A팀 핵심 역할 및 책임

### 📊 주요 책임 영역
1. **TRS (Taxonomy Registry Service)** - 분류 시스템의 핵심 엔진
2. **데이터 인입/정제/색인 파이프라인** - 문서 처리 전 과정
3. **하이브리드 검색 시스템** - BM25 + Vector 검색 + Reranking
4. **버전 관리 및 롤백 시스템** - 택소노미 변경사항 관리

### 🎯 핵심 API 엔드포인트 (A팀 담당)
- `POST /classify` - 혼합 분류 파이프라인 (룰→LLM→교차검증)
- `GET /taxonomy/{version}/tree` - 노드/엣지 JSON 반환
- `GET /taxonomy/{version}/diff/{base}` - 버전간 차이점 분석
- `POST /taxonomy/{version}/rollback` - 트랜잭션 기반 롤백
- `POST /search` - 하이브리드 검색 + Rerank(50→5)

## 🎯 A팀 핵심 4개 이슈 (Week-1 필수 완료)

### **A-T1: DDL 생성 및 마이그레이션 스크립트** ⚡ 최우선
**목표**: v1.8 스키마 완성 + Alembic 마이그레이션 + 롤백 TTR≤15분

#### 필수 테이블 스키마
```sql
-- 문서 관리
CREATE TABLE documents (
    doc_id UUID PRIMARY KEY,
    source_url TEXT,
    version_tag TEXT,
    license_tag TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 문서 청크
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(doc_id),
    text TEXT,
    span int4range,  -- 문서 내 위치 범위 (시작, 끝)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 임베딩 및 검색 인덱스
CREATE TABLE embeddings (
    chunk_id UUID PRIMARY KEY REFERENCES chunks(chunk_id),
    vec VECTOR(1536),  -- pgvector 확장 필요
    bm25_tokens TSVECTOR
);

-- 택소노미 노드
CREATE TABLE taxonomy_nodes (
    node_id UUID PRIMARY KEY,
    label TEXT,
    canonical_path TEXT[],
    version TEXT,
    confidence FLOAT
);

-- 택소노미 엣지 (복합키)
CREATE TABLE taxonomy_edges (
    parent UUID REFERENCES taxonomy_nodes(node_id),
    child UUID REFERENCES taxonomy_nodes(node_id),
    version TEXT,
    PRIMARY KEY (parent, child, version)
);

-- 문서-택소노미 매핑
CREATE TABLE doc_taxonomy (
    doc_id UUID REFERENCES documents(doc_id),
    node_id UUID REFERENCES taxonomy_nodes(node_id),
    version TEXT,
    path TEXT[],
    confidence FLOAT,
    hitl_required BOOLEAN DEFAULT FALSE,
    UNIQUE (doc_id, node_id, version)
);

-- 택소노미 버전 마이그레이션 이력
CREATE TABLE taxonomy_migrations (
    from_version TEXT,
    to_version TEXT,
    from_path TEXT[],
    to_path TEXT[],
    rationale TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CBR 케이스 뱅크 (1.5P 준비)
CREATE TABLE case_bank (
    case_id UUID PRIMARY KEY,
    query TEXT,
    answer TEXT,
    sources JSONB,
    category_path TEXT[],
    quality FLOAT
);

-- 감사 로그 (롤백, 버전 변경 추적)
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    action TEXT NOT NULL,
    actor TEXT DEFAULT current_user,
    target TEXT,
    detail JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HITL 큐 (사람 검토 대기열)
CREATE TABLE hitl_queue (
    id BIGSERIAL PRIMARY KEY,
    doc_id UUID NOT NULL,
    node_id UUID,
    reason TEXT,
    confidence FLOAT,
    status TEXT CHECK (status IN ('queued','reviewing','resolved','rejected')) DEFAULT 'queued',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 필수 인덱스
```sql
-- pgvector 확장 및 btree_gist 확장 (int4range 인덱스용)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 벡터 검색 인덱스 (ivfflat with lists 파라미터)
CREATE INDEX idx_embeddings_vec_ivf ON embeddings 
USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);

-- BM25 토큰 검색 인덱스 (GIN)
CREATE INDEX idx_embeddings_bm25 ON embeddings USING GIN (bm25_tokens);

-- 문서 span 범위 검색 (GiST)
CREATE INDEX idx_chunks_span_gist ON chunks USING gist (span);

-- 택소노미 경로 검색
CREATE INDEX idx_taxonomy_canonical ON taxonomy_nodes USING GIN (canonical_path);
CREATE INDEX idx_doc_taxonomy_path ON doc_taxonomy USING GIN (path);
```

#### 체크리스트
- [ ] `taxonomy_nodes/edges/doc_taxonomy/taxonomy_migrations` 생성
- [ ] `canonical_path text[]` 강제 제약, FK/인덱스 존재
- [ ] Alembic 업/다운 스크립트 동작 확인
- [ ] 롤백 TTR ≤ 15분 달성 (실제 측정)
- [ ] `pytest -q` 스키마 smoke 테스트 통과
- [ ] `make seed` 후 조회 성공

### **A-T2: `/classify` 체인 (룰→LLM→교차검증) 구현**
**목표**: 혼합 분류 파이프라인 + Conf<0.7 HITL 처리

#### 분류 파이프라인 플로우
```python
# 1단계: 룰 기반 1차 분류 (민감도/패턴 매칭)
def rule_based_classify(text: str, hint_paths: List[List[str]] = None) -> List[str]:
    """
    - 민감도 키워드 매칭
    - 정규식 패턴 인식
    - 문서 형태 분류 (PDF/URL/코드 등)
    """
    pass

# 2단계: LLM 2차 분류 (후보 경로 + 근거≥2)
def llm_classify(text: str, rule_candidates: List[str]) -> Dict:
    """
    - LLM에게 후보 경로 제시
    - 근거≥2개 요구
    - JSON 구조화된 응답
    """
    pass

# 3단계: 교차검증 로직 (룰 vs LLM 결과 비교)
def cross_validation(rule_result: List[str], llm_result: Dict) -> Dict:
    """
    - 룰 vs LLM 일치도 계산
    - 신뢰도 점수 산출
    - 모순 감지 및 해결
    """
    pass

# 4단계: Confidence 점수 계산
def calculate_confidence(cross_val_result: Dict) -> float:
    """
    - 다중 신호 통합 (rule_match, llm_certainty, source_agreement)
    - 0.0-1.0 범위 정규화
    - 임계값 기반 HITL 판단
    """
    pass
```

#### Request/Response 모델 (common-schemas 준수)
```python
class ClassifyRequest(BaseModel):
    chunk_id: str
    text: str
    hint_paths: Optional[List[List[str]]] = None

class ClassifyResponse(BaseModel):
    canonical: List[str]
    candidates: List[TaxonomyNode]
    hitl: bool = False
    confidence: float
    reasoning: List[str]  # 근거≥2개
```

#### 체크리스트
- [ ] 룰 기반 1차 분류 구현 (민감도/패턴 매칭)
- [ ] LLM 2차 분류 구현 (후보 경로 + 근거≥2)
- [ ] 교차검증 로직 구현 (룰 vs LLM 결과 비교)
- [ ] Confidence 점수 계산 알고리즘 구현
- [ ] HITL 큐 처리 (Conf<0.7 시 `hitl=true` 반환)
- [ ] ClassifyRequest/ClassifyResponse Pydantic 모델 준수
- [ ] 로깅: 후보/근거/판단 과정 상세 기록
- [ ] 샘플 50건 배치 분류 실행 성공
- [ ] HITL 요구율 ≤30% 달성

### **A-T3: 택소노미 버전/롤백 API 구현**
**목표**: `/taxonomy/{version}/tree|diff/{base}|rollback` 완전 구현

#### API 엔드포인트 상세
```python
@app.get("/taxonomy/{version}/tree")
def get_tree(version: str):
    """
    노드/엣지 구조 JSON 반환
    - nodes: [{ node_id, label, canonical_path, confidence }]
    - edges: [{ parent, child, version }]
    """
    pass

@app.get("/taxonomy/{version}/diff/{base}")
def get_diff(version: str, base: str):
    """
    버전간 차이점 분석
    - added: 새로 추가된 노드/엣지
    - moved: 경로 변경된 노드
    - removed: 삭제된 노드/엣지
    - modified: 라벨/메타데이터 변경
    """
    pass

@app.post("/taxonomy/{version}/rollback")
def rollback_taxonomy(version: str):
    """
    트랜잭션 기반 롤백
    - taxonomy_migrations 테이블 참조
    - 역방향 매핑 적용
    - 감사로그 기록
    """
    pass
```

#### 롤백 프로시저 (PL/pgSQL)
```sql
CREATE OR REPLACE PROCEDURE rollback_taxonomy(to_v TEXT)
LANGUAGE plpgsql AS $$
DECLARE 
    r RECORD; 
    rollback_count INTEGER := 0;
BEGIN
    -- 트랜잭션 시작 (자동)
    
    -- 매핑 테이블 롤백
    FOR r IN SELECT * FROM taxonomy_migrations WHERE to_version = to_v ORDER BY created_at DESC LOOP
        UPDATE doc_taxonomy 
        SET path = r.from_path, version = r.from_version 
        WHERE path = r.to_path AND version = to_v;
        
        GET DIAGNOSTICS rollback_count = ROW_COUNT;
        
        -- 롤백 성공 로깅
        INSERT INTO audit_log (action, actor, target, detail) 
        VALUES (
            'taxonomy_rollback_mapping',
            current_user,
            to_v,
            jsonb_build_object(
                'from_path', r.from_path,
                'to_path', r.to_path,
                'affected_rows', rollback_count
            )
        );
    END LOOP;
    
    -- 노드/엣지 삭제
    DELETE FROM taxonomy_edges WHERE version = to_v;
    GET DIAGNOSTICS rollback_count = ROW_COUNT;
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback_edges', current_user, to_v, 
           jsonb_build_object('deleted_edges', rollback_count));
    
    DELETE FROM taxonomy_nodes WHERE version = to_v;
    GET DIAGNOSTICS rollback_count = ROW_COUNT;
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback_nodes', current_user, to_v, 
           jsonb_build_object('deleted_nodes', rollback_count));
    
    -- 최종 롤백 완료 로그
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback_completed', current_user, to_v, 
           jsonb_build_object('rollback_target', to_v, 'status', 'success'));
    
    -- 커밋은 호출자에서 처리
EXCEPTION
    WHEN OTHERS THEN
        -- 에러 로깅
        INSERT INTO audit_log (action, actor, target, detail) 
        VALUES ('taxonomy_rollback_failed', current_user, to_v, 
               jsonb_build_object('error', SQLERRM, 'sqlstate', SQLSTATE));
        RAISE;
END $$;
```

#### 체크리스트
- [ ] `GET /taxonomy/{version}/tree` - 노드/엣지 JSON 반환
- [ ] `GET /taxonomy/{version}/diff/{base}` - 추가/이동/삭제 diff JSON
- [ ] `POST /taxonomy/{version}/rollback` - 트랜잭션 기반 롤백
- [ ] 버전 매핑 테이블 적용 (`taxonomy_migrations` 활용)
- [ ] 감사로그 기록 (누가/언제/무엇을 롤백했는지)
- [ ] 에러 처리: 404 (버전 없음), 409 (충돌), 500 (시스템 오류)
- [ ] v1.4.2→v1.5.0 diff 생성 및 조회 테스트
- [ ] v1.5.0→v1.4.2 롤백 실행 및 검증

### **A-T4: 검색/재순위 통합 (p95 가드)**
**목표**: BM25+Vector 하이브리드 검색 + Rerank(50→5) + p95≤4s

#### 검색 파이프라인 아키텍처
```python
async def hybrid_search(query: str, filters: Dict = None) -> SearchResponse:
    """
    1. BM25 검색 (topk=12)
    2. Vector 검색 (topk=12)  
    3. 후보 union/dedup
    4. Cross-Encoder Rerank (50→5)
    5. 메타데이터 추가 (sources≥2, latency)
    """
    import time
    start_time = time.time()   # ← 누락 보강
    
    # 1. BM25 검색
    bm25_results = await bm25_search(
        query=query, 
        topk=12,
        filters=filters
    )
    
    # 2. Vector 검색
    vector_results = await vector_search(
        query_embedding=embed_query(query),
        topk=12,
        filters=filters
    )
    
    # 3. 후보 합집합 및 중복 제거
    candidates = union_dedup(bm25_results, vector_results)
    
    # 4. Cross-Encoder Reranking
    if len(candidates) > 5:
        reranked = await cross_encoder_rerank(
            query=query,
            candidates=candidates,
            final_topk=5
        )
    else:
        reranked = candidates
        
    # 5. 응답 구성
    return SearchResponse(
        hits=reranked,
        latency=time.time() - start_time,
        request_id=f"search_{int(time.time() * 1000)}",
        total_candidates=len(candidates),  # Optional으로 변경됨
        sources_count=len([hit for hit in reranked if hit.source]),  # Optional으로 변경됨
        taxonomy_version="1.8.1"  # Optional 메타로 변경됨
    )
```

#### 성능 최적화 전략
- **인덱스 전략**: ivfflat (벡터), GIN (BM25), B-tree (필터)
- **캐싱 전략**: Redis L2 캐시 (top-hits TTL 10분)
- **병렬 처리**: BM25/Vector 검색 동시 실행
- **배치 처리**: Reranking 벡터화 연산

#### 체크리스트
- [ ] BM25 인덱스 생성 및 topk=12 조회 구현
- [ ] Vector 인덱스 생성 및 topk=12 조회 구현
- [ ] 후보 union/dedup 로직 구현
- [ ] Cross-Encoder Rerank 50→5 최종 선별 구현
- [ ] `/search` API 구현 (SearchRequest/SearchResponse 준수)
- [ ] 응답에 sources≥2, latency 메타데이터 포함
- [ ] 1k 샘플 부하 테스트 p95≤4s 달성
- [ ] 동시 요청 100건 처리 성공
- [ ] 에러율 <1% 달성

## 📁 모노레포 구조 및 파일 조직

### 프로젝트 구조
```
dynamic-taxonomy-rag/
├─ apps/
│  ├─ taxonomy/              # 👈 A팀 담당 영역
│  │  ├─ main.py            # FastAPI 앱
│  │  ├─ models/            # SQLAlchemy 모델
│  │  ├─ services/          # 비즈니스 로직
│  │  ├─ migrations/        # Alembic 마이그레이션
│  │  ├─ tests/             # 단위/통합 테스트
│  │  └─ Dockerfile
│  ├─ orchestration/         # B팀 (LangGraph)
│  └─ frontend-admin/        # C팀 (Next.js)
├─ packages/
│  ├─ common-schemas/        # 🤝 공통 계약
│  │  ├─ models.py          # Pydantic 모델
│  │  └─ tests/contract_test.py
│  └─ clients/               # 자동 생성 SDK
├─ infra/
│  ├─ docker-compose.yml    # 개발환경
│  └─ seed.py              # 테스트 데이터
└─ .github/workflows/       # CI/CD
```

### A팀 앱 구조 (`apps/taxonomy/`)
```
apps/taxonomy/
├─ main.py                  # FastAPI 앱 엔트리포인트
├─ models/
│  ├─ __init__.py
│  ├─ document.py          # Document, Chunk 모델
│  ├─ taxonomy.py          # TaxonomyNode, Edge 모델
│  └─ embedding.py         # Embedding 모델
├─ services/
│  ├─ __init__.py
│  ├─ classifier.py        # 분류 서비스
│  ├─ taxonomy_service.py  # 버전/롤백 서비스
│  └─ search_service.py    # 검색 서비스
├─ migrations/              # Alembic 마이그레이션
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions/
│     └─ 0001_init.py      # 초기 스키마
├─ tests/
│  ├─ test_classifier.py
│  ├─ test_taxonomy.py
│  └─ test_search.py
├─ pyproject.toml
└─ Dockerfile
```

## 🛠️ 개발 환경 설정

### 퀵스타트 (10분)
```bash
# 1. 기본 의존성 (WSL Ubuntu)
sudo apt update && sudo apt install -y git make docker.io docker-compose-plugin python3.11 python3.11-venv

# 2. 프로젝트 초기화
mkdir dynamic-taxonomy-rag && cd dynamic-taxonomy-rag
git init

# 3. 모노레포 구조 생성
mkdir -p apps/{taxonomy,orchestration,frontend-admin}
mkdir -p packages/{common-schemas,clients}  
mkdir -p infra .github/workflows

# 4. 환경변수 설정
cat > .env << EOF
APP_ENV=dev
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=rag
POSTGRES_USER=rag
POSTGRES_PASSWORD=***MASKED***
OPENAI_API_KEY=***MASKED***
EOF

# 5. 컨테이너 기동
make up && make seed && make contract-test
```

### Docker Compose 설정
```yaml
# infra/docker-compose.yml
version: "3.9"
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER} 
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports: ["5432:5432"]
    volumes: [dbdata:/var/lib/postgresql/data]

  taxonomy:
    build: ../apps/taxonomy
    environment:
      DATABASE_URL: postgresql+psycopg://rag:rag@db:5432/rag
    depends_on: [db]
    ports: ["8000:8000"]

volumes:
  dbdata:
```

### Makefile
```makefile
.PHONY: up down logs seed lint test contract-test
up:; docker compose -f infra/docker-compose.yml up -d --build
down:; docker compose -f infra/docker-compose.yml down -v
logs:; docker compose -f infra/docker-compose.yml logs -f --tail=100
seed:; python3 infra/seed.py
lint:; ruff check apps packages && mypy apps packages  
test:; pytest -q
contract-test:; python3 packages/common-schemas/tests/contract_test.py
```

## 📋 작업 일정 및 우선순위

### Week-1 일별 계획 (2025-09-02 ~ 09-09)

#### **Day 1 (2025-09-02): A-T1 DDL & 마이그레이션**
```bash
# 브랜치 생성 및 이슈 생성
git switch -c feat/A-T1-ddl
gh issue create --title "A‑T1: DDL 생성 및 마이그레이션" \
  --body "스키마 DDL/Alembic 업다운, 롤백 TTR≤15m" \
  --label feature,A-tax,schema
```

**목표**: 
- [ ] 8개 핵심 테이블 스키마 완성
- [ ] pgvector 확장 설치 및 인덱스 생성
- [ ] Alembic 초기화 및 마이그레이션 스크립트
- [ ] 롤백 프로시저 구현

#### **Day 2-3 (2025-09-03~04): A-T2 분류 파이프라인**
```bash
git switch -c feat/A-T2-classify
```

**목표**:
- [ ] 룰 기반 1차 분류 로직
- [ ] LLM 2차 분류 + 근거 수집
- [ ] 교차검증 및 Confidence 계산
- [ ] HITL 큐 처리 로직

#### **Day 4-5 (2025-09-05~06): A-T3 버전 관리 API**
```bash  
git switch -c feat/A-T3-taxonomy-api
```

**목표**:
- [ ] `/taxonomy/{version}/tree` 구현
- [ ] `/taxonomy/{version}/diff/{base}` 구현  
- [ ] `/taxonomy/{version}/rollback` 구현
- [ ] 버전 마이그레이션 로직

#### **Day 6-7 (2025-09-07~09): A-T4 검색 최적화**
```bash
git switch -c feat/A-T4-search-performance  
```

**목표**:
- [ ] BM25 + Vector 하이브리드 검색
- [ ] Cross-Encoder Reranking 구현
- [ ] 성능 최적화 (p95≤4s)
- [ ] 부하 테스트 및 튜닝

## 🤝 팀 간 협업 인터페이스

### B팀과의 API 계약
```python
# A팀 → B팀 제공 API
POST /classify → ClassifyResponse
GET /taxonomy/{version}/tree → TreeResponse
POST /search → SearchResponse

# B팀 → A팀 요청사항  
- canonical_path 기반 필터링 지원
- 응답에 confidence, sources≥2 포함
- 버전 정보 메타데이터 제공
```

### C팀과의 API 계약
```python
# A팀 → C팀 제공 API
GET /taxonomy/{version}/tree → UI 렌더링용 JSON
GET /taxonomy/{version}/diff/{base} → 버전 비교 UI
POST /taxonomy/{version}/rollback → 롤백 버튼 연동

# C팀 → A팀 요청사항
- 1만 노드 트리 구조 최적화
- 메타데이터 (문서수, 신뢰도, 변경일) 제공
- 에러 상태 및 로딩 상태 고려
```

### 공통 스키마 (packages/common-schemas)
```python
# packages/common-schemas/models.py (문서의 공통 스키마 예시 블록을 아래로 교체)

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TaxonomyNode(BaseModel):
    node_id: str
    label: str
    canonical_path: List[str]
    version: str
    confidence: float = 0.0

class SourceMeta(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    version: Optional[str] = None
    span: Optional[List[int]] = None  # [start, end]

class ClassifyRequest(BaseModel):
    chunk_id: str
    text: str
    hint_paths: Optional[List[List[str]]] = None

class ClassifyResponse(BaseModel):
    canonical: List[str]
    candidates: List[TaxonomyNode]
    hitl: bool = False
    confidence: float
    reasoning: List[str]          # 근거≥2

class SearchHit(BaseModel):
    chunk_id: str
    score: float
    source: Optional[SourceMeta] = None
    text: Optional[str] = None
    taxonomy_path: Optional[List[str]] = None

class SearchRequest(BaseModel):
    q: str
    filters: Optional[Dict] = None     # 예: {"canonical_in":[["AI","RAG"]]}
    bm25_topk: int = 12
    vector_topk: int = 12
    rerank_candidates: int = 50
    final_topk: int = 5

class SearchResponse(BaseModel):
    hits: List[SearchHit]
    latency: float
    request_id: str
    total_candidates: Optional[int] = None
    sources_count: Optional[int] = None
    taxonomy_version: Optional[str] = None
```

### OpenAPI 스키마 정의 (v1.8.1 계약 준수)
```yaml
# openapi.yaml - components.schemas
SourceMeta:
  type: object
  properties:
    url: { type: string, format: uri }
    title: { type: string }
    date: { type: string, format: date }
    version: { type: string }
    span:
      type: array
      items: { type: integer }
      minItems: 2
      maxItems: 2

SearchHit:
  type: object
  required: [chunk_id, score]
  properties:
    chunk_id: { type: string }
    score: { type: number }
    source: { $ref: '#/components/schemas/SourceMeta' }
    text: { type: string }
    taxonomy_path:
      type: array
      items: { type: string }

SearchRequest:
  type: object
  required: [q]
  properties:
    q: { type: string }
    filters: { type: object, additionalProperties: true }
    bm25_topk: { type: integer, default: 12 }
    vector_topk: { type: integer, default: 12 }
    rerank_candidates: { type: integer, default: 50 }  # ← 계약 준수 추가
    final_topk: { type: integer, default: 5 }

SearchResponse:
  type: object
  required: [hits, latency, request_id]
  properties:
    hits: { type: array, items: { $ref: '#/components/schemas/SearchHit' } }
    latency: { type: number }
    request_id: { type: string }
    total_candidates: { type: integer }      # Optional
    sources_count: { type: integer }         # Optional
    taxonomy_version: { type: string }       # Optional

ClassifyRequest:
  type: object
  required: [chunk_id, text]
  properties:
    chunk_id: { type: string }
    text: { type: string }
    hint_paths:
      type: array
      items:
        type: array
        items: { type: string }

ClassifyResponse:
  type: object
  required: [canonical, candidates, hitl, confidence, reasoning]
  properties:
    canonical: { type: array, items: { type: string } }
    candidates: { type: array, items: { $ref: '#/components/schemas/TaxonomyNode' } }
    hitl: { type: boolean, default: false }
    confidence: { type: number, minimum: 0, maximum: 1 }
    reasoning: { type: array, items: { type: string }, minItems: 2 }

TaxonomyNode:
  type: object
  required: [node_id, label, canonical_path, version]
  properties:
    node_id: { type: string }
    label: { type: string }
    canonical_path: { type: array, items: { type: string } }
    version: { type: string }
    confidence: { type: number, minimum: 0, maximum: 1, default: 0 }
```

## 🗄️ Alembic 마이그레이션 관리

### 초기 마이그레이션 스크립트
```python
# migrations/versions/0001_init.py
"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2025-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # pgvector 및 btree_gist 확장 생성
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    
    # 문서 관리 테이블
    op.create_table(
        'documents',
        sa.Column('doc_id', postgresql.UUID(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('version_tag', sa.Text(), nullable=True),
        sa.Column('license_tag', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                 server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('doc_id')
    )
    
    # 문서 청크 테이블
    op.create_table(
        'chunks',
        sa.Column('chunk_id', postgresql.UUID(), nullable=False),
        sa.Column('doc_id', postgresql.UUID(), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('span', postgresql.INT4RANGE(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                 server_default=sa.text('NOW()'), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.doc_id']),
        sa.PrimaryKeyConstraint('chunk_id')
    )
    
    # 임베딩 및 검색 인덱스 테이블
    op.create_table(
        'embeddings',
        sa.Column('chunk_id', postgresql.UUID(), nullable=False),
        sa.Column('vec', postgresql.VECTOR(1536), nullable=True),
        sa.Column('bm25_tokens', postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.chunk_id']),
        sa.PrimaryKeyConstraint('chunk_id')
    )
    
    # 택소노미 노드 테이블
    op.create_table(
        'taxonomy_nodes',
        sa.Column('node_id', postgresql.UUID(), nullable=False),
        sa.Column('label', sa.Text(), nullable=True),
        sa.Column('canonical_path', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('version', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('node_id')
    )
    
    # 택소노미 엣지 테이블
    op.create_table(
        'taxonomy_edges',
        sa.Column('parent', postgresql.UUID(), nullable=False),
        sa.Column('child', postgresql.UUID(), nullable=False),
        sa.Column('version', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['child'], ['taxonomy_nodes.node_id']),
        sa.ForeignKeyConstraint(['parent'], ['taxonomy_nodes.node_id']),
        sa.PrimaryKeyConstraint('parent', 'child', 'version')
    )
    
    # 문서-택소노미 매핑 테이블
    op.create_table(
        'doc_taxonomy',
        sa.Column('doc_id', postgresql.UUID(), nullable=True),
        sa.Column('node_id', postgresql.UUID(), nullable=True),
        sa.Column('version', sa.Text(), nullable=True),
        sa.Column('path', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('hitl_required', sa.Boolean(), 
                 server_default=sa.text('false'), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.doc_id']),
        sa.ForeignKeyConstraint(['node_id'], ['taxonomy_nodes.node_id']),
        sa.UniqueConstraint('doc_id', 'node_id', 'version')
    )
    
    # 택소노미 버전 마이그레이션 이력 테이블
    op.create_table(
        'taxonomy_migrations',
        sa.Column('from_version', sa.Text(), nullable=True),
        sa.Column('to_version', sa.Text(), nullable=True),
        sa.Column('from_path', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('to_path', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                 server_default=sa.text('NOW()'), nullable=True)
    )
    
    # CBR 케이스 뱅크 테이블
    op.create_table(
        'case_bank',
        sa.Column('case_id', postgresql.UUID(), nullable=False),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('sources', postgresql.JSONB(), nullable=True),
        sa.Column('category_path', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('quality', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('case_id')
    )
    
    # 감사 로그 테이블
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('actor', sa.Text(), server_default=sa.text('current_user'), nullable=True),
        sa.Column('target', sa.Text(), nullable=True),
        sa.Column('detail', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                 server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # HITL 큐 테이블
    op.create_table(
        'hitl_queue',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('doc_id', postgresql.UUID(), nullable=False),
        sa.Column('node_id', postgresql.UUID(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.Text(), server_default=sa.text("'queued'"), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                 server_default=sa.text('NOW()'), nullable=True),
        sa.CheckConstraint("status IN ('queued','reviewing','resolved','rejected')"),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 인덱스 생성
    # 벡터 검색 인덱스 (ivfflat with lists 파라미터)
    op.execute('CREATE INDEX idx_embeddings_vec_ivf ON embeddings USING ivfflat (vec vector_cosine_ops) WITH (lists = 100)')
    
    # BM25 토큰 검색 인덱스 (GIN)
    op.create_index('idx_embeddings_bm25', 'embeddings', ['bm25_tokens'], postgresql_using='gin')
    
    # 문서 span 범위 검색 (GiST)
    op.create_index('idx_chunks_span_gist', 'chunks', ['span'], postgresql_using='gist')
    
    # 택소노미 경로 검색
    op.create_index('idx_taxonomy_canonical', 'taxonomy_nodes', ['canonical_path'], postgresql_using='gin')
    op.create_index('idx_doc_taxonomy_path', 'doc_taxonomy', ['path'], postgresql_using='gin')

def downgrade() -> None:
    # 인덱스 삭제
    op.drop_index('idx_doc_taxonomy_path')
    op.drop_index('idx_taxonomy_canonical')
    op.drop_index('idx_chunks_span_gist')
    op.drop_index('idx_embeddings_bm25')
    op.execute('DROP INDEX IF EXISTS idx_embeddings_vec_ivf')
    
    # 테이블 삭제 (역순)
    op.drop_table('hitl_queue')
    op.drop_table('audit_log')
    op.drop_table('case_bank')
    op.drop_table('taxonomy_migrations')
    op.drop_table('doc_taxonomy')
    op.drop_table('taxonomy_edges')
    op.drop_table('taxonomy_nodes')
    op.drop_table('embeddings')
    op.drop_table('chunks')
    op.drop_table('documents')
    
    # 확장 제거 (선택사항 - 다른 앱에서 사용할 수 있음)
    # op.execute('DROP EXTENSION IF EXISTS btree_gist')
    # op.execute('DROP EXTENSION IF EXISTS vector')
```

### Alembic 환경 설정
```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from apps.taxonomy.models import Base  # 모든 모델 import

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 마이그레이션 실행 명령어
```bash
# 마이그레이션 초기화
alembic init migrations

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial schema"

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1  # 1단계 뒤로
alembic downgrade base  # 전체 롤백

# 마이그레이션 히스토리 확인
alembic history --verbose
```

## 🔍 품질 보증 및 테스트

### 테스트 전략
```python
# tests/test_classifier.py
def test_classify_basic():
    """기본 분류 기능 테스트"""
    req = ClassifyRequest(chunk_id="test1", text="AI 관련 문서")
    resp = classify(req)
    assert resp.canonical
    assert len(resp.candidates) > 0
    assert 0 <= resp.confidence <= 1

def test_classify_hitl_threshold():
    """HITL 임계값 테스트""" 
    req = ClassifyRequest(chunk_id="test2", text="애매한 문서")
    resp = classify(req)
    if resp.confidence < 0.7:
        assert resp.hitl is True

# tests/test_performance.py  
def test_search_performance():
    """검색 성능 테스트 (p95≤4s)"""
    import time
    latencies = []
    
    for _ in range(100):
        start = time.time()
        result = search("test query")
        latencies.append(time.time() - start)
    
    p95 = sorted(latencies)[94]  # 95번째 백분위수
    assert p95 <= 4.0, f"p95 latency {p95}s exceeds 4s limit"
```

### 계약 테스트
```python
# packages/common-schemas/tests/contract_test.py
def test_classify_response_contract():
    """분류 응답 계약 테스트"""
    response = ClassifyResponse(
        canonical=["AI", "RAG"],
        candidates=[
            TaxonomyNode(
                node_id="n1",
                label="RAG",
                canonical_path=["AI", "RAG"], 
                version="1.4.2",
                confidence=0.85
            )
        ],
        hitl=False,
        confidence=0.85,
        reasoning=["AI 키워드 감지", "RAG 패턴 매칭"]
    )
    
    # 필수 필드 검증
    assert response.canonical
    assert len(response.candidates) > 0
    assert 0 <= response.confidence <= 1
    assert len(response.reasoning) >= 2  # 근거≥2개
```

### 성능 모니터링 및 로깅
```python
# utils/performance.py - 간단한 타이머 로깅
import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def timer_log(operation_name: str):
    """함수 실행 시간을 로깅하는 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# 사용 예시
@timer_log("Hybrid Search")
async def hybrid_search(query: str) -> SearchResponse:
    # 검색 로직...
    pass

@timer_log("Classify Document")
def classify_document(text: str) -> ClassifyResponse:
    # 분류 로직...
    pass
```

### 품질 가드 체크리스트
- [ ] `ruff check apps packages` 통과 (코드 스타일)
- [ ] `mypy apps packages` 통과 (타입 체크)
- [ ] `pytest -q` 통과 (단위 테스트)
- [ ] `contract-test` 통과 (계약 준수)
- [ ] 성능 테스트 p95≤4s 달성
- [ ] HITL 요구율 ≤30% 달성
- [ ] 롤백 TTR ≤15분 달성
- [ ] 타이머 로깅으로 모든 주요 작업 성능 추적

## 🚨 위험 관리 및 대응

### 기술적 위험
1. **pgvector 성능 이슈**: ivfflat 인덱스 튜닝, 벡터 차원 최적화
2. **Alembic 마이그레이션 실패**: 철저한 백업, 단계별 테스트
3. **LLM API 지연**: 타임아웃 설정, 재시도 로직, 폴백 모델
4. **동시성 문제**: DB 트랜잭션 격리, 락 전략

### 운영적 위험  
1. **팀 간 API 계약 위반**: contract-test 강제, 버전 관리
2. **성능 목표 미달**: 지속적 모니터링, 조기 최적화
3. **데이터 품질 저하**: 검증 파이프라인, HITL 피드백

### 대응 계획
- **일일 스탠드업**: 블로커 이슈 즉시 공유
- **코드 리뷰**: 최소 1명 승인 필수
- **CI/CD 파이프라인**: 모든 품질 가드 자동화

## 📊 완료 기준 (Definition of Done)

### A팀 Week-1 완료 조건
- [ ] **A-T1**: DDL/마이그레이션 완성, 롤백 TTR≤15분 검증
- [ ] **A-T2**: 분류 API 구현, HITL≤30% 달성  
- [ ] **A-T3**: 버전 관리 API 완성, diff/rollback 동작 확인
- [ ] **A-T4**: 검색 API 구현, p95≤4s 성능 달성

### 품질 기준
- [ ] 모든 contract-test 통과
- [ ] 코드 커버리지 ≥80%
- [ ] 정적 분석 도구 통과 (ruff, mypy)
- [ ] 메모리 누수 검사 통과

### 통합 검증
- [ ] B팀 orchestration 서비스와 연동 테스트 성공
- [ ] C팀 frontend와 API 통신 테스트 성공  
- [ ] 전체 시스템 E2E 시나리오 1회 이상 성공

## 🎯 Claude Code 컨텍스트 (작업 시 참조)

```
[팀 A 브리핑]
목표: TRS(분류/버전/롤백)와 인입/색인 파이프라인, 관측을 1P로 완성.
DoD: /classify 혼합체인·/taxonomy diff/rollback·/search 하이브리드+rerank p95≤4s·DDL/인덱스·런북.
우선순위: A‑T1 DDL→A‑T2 classify→A‑T3 diff/rollback→A‑T4 search/perf.
주의: canonical path 일원화, HITL<0.70, Alembic 업/다운, 롤백 TTR≤15m.
현재 작업: [작업별로 업데이트]
```

### 핵심 준수사항
1. **NFR 가드**: p95≤4s, cost≤₩10/req, 롤백 TTR≤15m  
2. **계약 준수**: common-schemas의 Pydantic 모델 엄격 준수
3. **품질 가드**: ruff/mypy/pytest/contract-test 모두 통과
4. **보안 원칙**: PII 마스킹, RBAC/ABAC 적용

---

**마지막 업데이트**: 2025-09-04  
**문서 버전**: v1.3 (최종 Go/No-Go 게이트 통과 완료)  
**담당팀**: A팀 (Taxonomy & Data Platform)  
**주요 수정사항**: 
- chunks.span을 int4range로 수정
- audit_log, hitl_queue 테이블 추가
- ivfflat 인덱스에 lists=100 파라미터 추가
- ClassifyResponse에 confidence, reasoning 필드 추가
- SearchRequest/Response 모델 상세화
- 완전한 Alembic 마이그레이션 스크립트 추가
- 롤백 프로시저에 상세한 감사로그 추가
- 성능 모니터링을 위한 타이머 로깅 유틸리티 추가
**최종 검수 Must-fix 4건 (계약 충돌 방지)**:
- SearchRequest에 rerank_candidates=50 추가
- SearchHit에 SourceMeta 객체 사용, taxonomy_path 옵션화
- SearchResponse 필드들 옵션으로 완화, request_id 추가
- allowed_category_paths → filters.canonical_in 구조로 바뀌ㅡ
- OpenAPI v1.8.1 스키마 정의 추가
- Nitpick: Dict import, start_time 선언, JSONB ::jsonb 타입 커스팅 수정

> 이 문서는 A팀의 모든 작업 맥락과 상세 구현 가이드를 담고 있습니다. 작업 시작 전 반드시 숙지하고, 작업 중에도 지속적으로 참조하세요.