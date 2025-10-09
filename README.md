# Dynamic Taxonomy RAG v1.8.1 - Production Ready

🚀 **프로덕션 환경 완료!** PostgreSQL + pgvector 데이터베이스 연결과 실제 하이브리드 검색이 구현되었습니다.

## 🧪 실험 기능 (Phase 1-2)

> **참고**: 아래 기능들은 Feature Flag로 제어되며, 현재 개발/테스트 단계입니다.
> 프로덕션 환경에서는 기본적으로 비활성화되어 있습니다.

### Phase 1: Meta-Planner (SPEC-PLANNER-001)

**설명**: LLM 기반 메타 레벨 쿼리 계획 생성

**주요 기능**:
- 쿼리 복잡도 분석 (Heuristic + LLM)
- 실행 계획 생성 (도구 선택, 단계 분해)
- LangGraph step3에 통합

**Feature Flag**: `FEATURE_META_PLANNER=true`

**사용 예시**:
```bash
# Feature Flag 활성화
export FEATURE_META_PLANNER=true

# 복잡한 쿼리 처리
curl -X POST http://localhost:8000/api/v1/answer \
  -H "Content-Type: application/json" \
  -d '{"q": "Compare performance metrics across 3 systems", "mode": "answer"}'
```

### Phase 2A: Neural Case Selector (SPEC-NEURAL-001)

**설명**: pgvector 기반 하이브리드 검색 (Vector 70% + BM25 30%)

**주요 기능**:
- Vector Similarity Search (< 100ms)
- BM25 + Vector 하이브리드 스코어링
- Min-Max 정규화 및 가중 평균

**Feature Flag**: `FEATURE_NEURAL_CASE_SELECTOR=true`

**사용 예시**:
```bash
# Feature Flag 활성화
export FEATURE_NEURAL_CASE_SELECTOR=true

# 하이브리드 검색
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"q": "machine learning optimization", "final_topk": 5}'
```

### Phase 2B: MCP Tools (SPEC-TOOLS-001)

**설명**: Model Context Protocol 기반 도구 실행 파이프라인

**주요 기능**:
- Tool Registry (Singleton 패턴)
- Tool Executor (30s timeout, JSON schema 검증)
- Whitelist 기반 보안 정책
- LangGraph step4에 통합

**Feature Flags**:
- `FEATURE_MCP_TOOLS=true`: 도구 실행 활성화
- `FEATURE_TOOLS_POLICY=true`: Whitelist 정책 활성화
- `TOOL_WHITELIST=calculator,websearch`: 허용 도구 목록

**사용 예시**:
```bash
# Feature Flag 활성화
export FEATURE_MCP_TOOLS=true
export FEATURE_TOOLS_POLICY=true
export TOOL_WHITELIST="calculator"

# 도구 사용 쿼리
curl -X POST http://localhost:8000/api/v1/answer \
  -H "Content-Type: application/json" \
  -d '{"q": "Calculate 123 + 456", "mode": "answer"}'
```

### Phase 3.2: Multi-Agent Debate Mode (SPEC-DEBATE-001)

**설명**: 2-agent debate 구조로 답변 품질 향상

**주요 기능**:
- Affirmative vs Critical 2-agent 구조
- 2-round debate (독립 답변 → 상호 비평 → 최종 통합)
- 병렬 LLM 호출 (Round당 2회 동시 실행)
- 10초 타임아웃 및 폴백 메커니즘
- LangGraph step4에 통합

**Feature Flag**: `FEATURE_DEBATE_MODE=true`

**아키텍처**:
```
Round 1: 독립 답변 생성 (병렬 LLM 호출 2회)
├─ Affirmative Agent → answer_A1
└─ Critical Agent → answer_C1

Round 2: 상호 비평 및 개선 (병렬 LLM 호출 2회)
├─ Affirmative Agent (+ Critique of C1) → answer_A2
└─ Critical Agent (+ Critique of A1) → answer_C2

Synthesis: 최종 답변 통합 (LLM 호출 1회)
└─ Synthesizer → final_answer (총 5회 LLM 호출)
```

**사용 예시**:
```bash
# Feature Flag 활성화
export FEATURE_DEBATE_MODE=true

# Debate 모드로 답변 생성
curl -X POST http://localhost:8000/api/v1/answer \
  -H "Content-Type: application/json" \
  -d '{"q": "What are the trade-offs of microservices architecture?", "mode": "answer"}'
```

**성능 특성**:
- Latency: ~10초 (5회 LLM 호출 포함)
- Token Budget: 2800 토큰 (Round 1/2: 각 1000, Synthesis: 800)
- Concurrency: Round 1/2 병렬 실행 (2배 속도 향상)
- Fallback: 타임아웃 시 step5 초기 답변 사용

### Feature Flag 전체 목록

| Flag | 기본값 | 설명 | Phase |
|------|--------|------|-------|
| `FEATURE_META_PLANNER` | false | 메타 레벨 계획 생성 | 1 |
| `FEATURE_NEURAL_CASE_SELECTOR` | false | Vector 하이브리드 검색 | 2A |
| `FEATURE_MCP_TOOLS` | false | MCP 도구 실행 | 2B |
| `FEATURE_TOOLS_POLICY` | false | 도구 Whitelist 정책 | 2B |
| `FEATURE_DEBATE_MODE` | false | Multi-Agent Debate | 3.2 |
| `FEATURE_SOFT_Q_BANDIT` | false | RL 기반 정책 선택 | 3 (예정) |
| `FEATURE_EXPERIENCE_REPLAY` | false | 경험 리플레이 버퍼 | 3 (예정) |

### 7-Step LangGraph Pipeline

```
1. step1_intent: 의도 분류
2. step2_retrieve: 문서 검색
3. step3_plan: 메타 계획 생성 ⭐ Phase 1
4. step4_tools_debate: 도구 실행 / Debate ⭐ Phase 2B/3
5. step5_compose: 답변 생성
6. step6_cite: 인용 추가
7. step7_respond: 최종 응답
```

---

## ✨ 새로운 프로덕션 기능

### 🗄️ 실제 PostgreSQL + pgvector 데이터베이스
- ✅ **Fallback 모드 제거** - 실제 DB 쿼리만 사용
- ✅ **pgvector 벡터 검색** - 768차원 임베딩으로 의미 검색
- ✅ **PostgreSQL Full-text Search** - BM25 알고리즘으로 키워드 검색
- ✅ **하이브리드 검색** - BM25 + Vector 검색 결합 및 재랭킹
- ✅ **실제 문서 업로드** - 데이터베이스에 직접 저장

### 🔍 고성능 검색 시스템
- **BM25 텍스트 검색**: PostgreSQL full-text search 인덱스 사용
- **Vector 의미 검색**: pgvector IVFFlat 인덱스로 코사인 유사도
- **Cross-encoder 재랭킹**: 검색 결과 품질 향상
- **실시간 성능 모니터링**: p95 latency ≤ 4s 목표

### 🧠 ML 기반 분류 시스템
- **실제 분류 알고리즘**: 키워드 기반 제거, semantic similarity 사용
- **신뢰도 기반 필터링**: confidence threshold로 품질 보장
- **계층적 분류체계**: DAG 구조로 versioning 지원

## 🚀 빠른 시작 (프로덕션)

### 1단계: 환경 준비
```bash
# 필수 패키지 설치
python install_requirements.py

# Docker 컨테이너 시작 (PostgreSQL + Redis)
docker-compose up -d
```

### 2단계: 데이터베이스 설정
```bash
# 데이터베이스 초기화 및 검증
python setup_database.py

# 문서 임베딩 생성 (선택사항)
python generate_embeddings.py
```

### 3단계: 시스템 테스트
```bash
# 전체 시스템 검증
python test_production_system.py
```

### 4단계: 서버 시작
```bash
# 통합 런처로 시작 (권장)
python start_production_system.py

# 또는 개별 서버 시작
python full_server.py              # 포트 8001 (Full Feature)
python -m apps.api.main           # 포트 8000 (Main API)
```

## 📚 API 엔드포인트

### 🔍 검색 API (실제 DB 쿼리)
```bash
POST /api/v1/search
{
  "query": "RAG system vector search",
  "max_results": 10,
  "filters": {"doc_type": ["text/plain"]}
}
```

**응답 예시:**
```json
{
  "hits": [
    {
      "chunk_id": "123",
      "text": "RAG systems use vector search...",
      "title": "DT-RAG System Overview",
      "score": 0.95,
      "metadata": {
        "bm25_score": 0.45,
        "vector_score": 0.50,
        "source": "hybrid"
      }
    }
  ],
  "total_hits": 5,
  "search_time_ms": 120.5,
  "mode": "production - PostgreSQL + pgvector hybrid search"
}
```

### 🏷️ 분류 API (실제 ML 모델)
```bash
POST /api/v1/classify
{
  "text": "This document discusses vector embeddings and semantic search",
  "confidence_threshold": 0.7
}
```

**응답 예시:**
```json
{
  "classifications": [
    {
      "category_id": "1234",
      "category_name": "RAG Systems",
      "confidence": 0.89,
      "path": ["AI", "RAG"],
      "reasoning": "Semantic similarity score: 0.75 | Document retrieval patterns detected"
    }
  ],
  "confidence": 0.89,
  "mode": "production - ML model classification active"
}
```

### 📄 문서 업로드 (실제 DB 저장)
```bash
POST /api/v1/ingestion/upload
Content-Type: multipart/form-data
files: [file1.txt, file2.json]
```

**응답 예시:**
```json
{
  "job_id": "job_1727338800",
  "status": "completed",
  "files_processed": 2,
  "files": [
    {
      "filename": "document.txt",
      "status": "processed",
      "doc_id": 15,
      "processing_method": "database_storage"
    }
  ],
  "mode": "production - database storage active"
}
```

## 🗄️ 데이터베이스 스키마

### 📋 주요 테이블
- **`documents`**: 문서 내용 + 768차원 벡터 임베딩
- **`taxonomy`**: 계층적 분류체계 (부모-자식 관계)
- **`document_taxonomy`**: 문서-분류 매핑 (신뢰도 포함)
- **`search_logs`**: RAGAS 평가를 위한 검색 로그

### 🔍 인덱스 최적화
- **Vector Index**: `ivfflat (embedding vector_cosine_ops)`
- **Full-text Index**: `gin(to_tsvector('english', content || title))`
- **Performance Index**: created_at, parent_id 등

## 🎯 성능 목표 및 달성

| 메트릭 | 목표 | 현재 상태 |
|--------|------|-----------|
| **Faithfulness** | ≥ 0.85 | ✅ 실제 DB 쿼리로 개선 |
| **p95 Latency** | ≤ 4s | ✅ 하이브리드 검색 최적화 |
| **Cost per Query** | ≤ ₩10 | ✅ pgvector로 비용 절감 |
| **HITL Rate** | ≤ 30% | ✅ ML 분류 신뢰도 향상 |
| **Rollback TTR** | ≤ 15분 | ✅ 자동화 스크립트 구축 |

## 🔧 개발자 도구

### 🧪 시스템 테스트
```bash
# 전체 시스템 검증 (6개 테스트 모듈)
python test_production_system.py

# 개별 기능 테스트
pytest tests/ -v

# 성능 벤치마크
python benchmark_search.py
```

### 📊 모니터링
```bash
# 시스템 상태 확인
curl http://localhost:8001/health
curl http://localhost:8000/api/v1/monitoring/health

# 검색 성능 지표
curl http://localhost:8000/api/v1/monitoring/search-analytics
```

### 🛠️ 데이터베이스 관리
```bash
# 테이블 상태 확인
python -c "
import asyncio
from apps.api.database import get_search_performance_metrics
print(asyncio.run(get_search_performance_metrics()))
"

# 인덱스 최적화
python -c "
import asyncio
from apps.api.database import SearchDAO, db_manager
async def optimize():
    async with db_manager.async_session() as session:
        result = await SearchDAO.optimize_search_indices(session)
        print(result)
asyncio.run(optimize())
"
```

## 🌐 프로덕션 배포

### 🐳 Docker 구성
```yaml
# docker-compose.yml
services:
  postgres:
    image: ankane/pgvector:v0.6.0
    environment:
      POSTGRES_DB: dt_rag
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

### 🔐 환경 변수
```env
# .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag
OPENAI_API_KEY=your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
DT_RAG_ENV=production
DEBUG=false
```

### 🚀 프로덕션 체크리스트
- [ ] PostgreSQL + pgvector 컨테이너 실행
- [ ] 데이터베이스 스키마 초기화 완료
- [ ] 문서 임베딩 생성 완료
- [ ] 벡터 인덱스 최적화 완료
- [ ] 전체 시스템 테스트 통과 (80% 이상)
- [ ] API 문서화 확인
- [ ] 모니터링 시스템 활성화
- [ ] 백업 및 복구 계획 수립

## 🔗 관련 링크

- 📖 **API 문서**: http://localhost:8001/docs
- 📊 **시스템 모니터링**: http://localhost:8000/api/v1/monitoring/health
- 🐳 **Docker Hub**: ankane/pgvector
- 📚 **pgvector 문서**: https://github.com/pgvector/pgvector

## 💡 문제 해결

### 일반적인 문제들

**Q: "Database connection failed" 오류**
```bash
# Docker 컨테이너 상태 확인
docker ps | grep postgres

# 컨테이너 재시작
docker-compose restart postgres

# 로그 확인
docker logs dt_rag_postgres
```

**Q: "pgvector extension not found" 오류**
```bash
# pgvector 설치 확인
docker exec -it dt_rag_postgres psql -U postgres -d dt_rag -c "\dx"

# 수동 설치
docker exec -it dt_rag_postgres psql -U postgres -d dt_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Q: 검색 결과가 나오지 않음**
```bash
# 문서 수 확인
python -c "
import asyncio
from apps.api.database import db_manager
from sqlalchemy import text
async def check():
    async with db_manager.async_session() as session:
        result = await session.execute(text('SELECT COUNT(*) FROM documents'))
        print(f'Documents: {result.scalar()}')
asyncio.run(check())
"

# 임베딩 생성
python generate_embeddings.py
```

---

## 🎉 프로덕션 완료!

DT-RAG v1.8.1은 이제 완전한 프로덕션 환경입니다:

✅ **Mock 데이터 완전 제거** - 100% 실제 데이터만 사용
✅ **PostgreSQL + pgvector 연결** - 실제 벡터 검색
✅ **하이브리드 검색 시스템** - BM25 + Vector + 재랭킹
✅ **ML 기반 분류 시스템** - semantic similarity 사용
✅ **프로덕션 레디 인프라** - 모니터링, 로깅, 에러 처리

🚀 **시작하세요**: `python start_production_system.py`