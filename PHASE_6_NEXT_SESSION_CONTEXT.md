# Phase 6 Next Session Context

## Session Starting Point

**Last Completed**: Phase 5 - LangGraph 7-Step RAG Orchestration Integration

**Current Phase**: Phase 6 - Issue Resolution & Performance Optimization

**Session Date**: 2025-10-06

## Phase 5 완료 요약

### 구현된 파일들
1. **apps/api/services/langgraph_service.py** (127줄)
   - LangGraph 파이프라인 래퍼 서비스
   - Singleton 패턴으로 파이프라인 인스턴스 관리
   - API request/response 변환 로직

2. **apps/api/routers/orchestration_router.py** (수정)
   - Mock PipelineService → 실제 LangGraphService 교체
   - Lines 93-170: PipelineService 클래스 완전히 재구현
   - TimeoutError 처리 로직 추가

3. **apps/orchestration/src/langgraph_pipeline.py** (수정)
   - Lines 92-97: STEP_TIMEOUTS 조정
   - intent: 1.0s, retrieve: 15.0s, compose: 20.0s, respond: 1.0s

### 검증 완료 사항
- ✅ LangGraph 파이프라인 초기화 성공
- ✅ Intent 단계 실행 완료 (0.000s)
- ✅ Retrieve 단계 실행 시작 (임베딩 생성 확인)
- ✅ POST /api/v1/pipeline/execute 엔드포인트 작동

## 발견된 이슈 (Phase 6에서 해결 필요)

### 🔴 Critical Issue 1: Circular Import in Hybrid Search

**증상**:
```
WARNING:apps.search:Hybrid search engine components not available:
cannot import name 'SearchDAO' from partially initialized module 'apps.api.database'
(most likely due to a circular import)
```

**영향**:
- Retrieve step이 5초 이상 소요
- Hybrid search engine이 제대로 초기화되지 않음

**근본 원인**:
- `apps/search/hybrid_search_engine.py` → `apps.api.database` 순환 참조
- `apps.api.database.py`에서 SearchDAO 정의, hybrid_search_engine이 이를 import

**해결 방법**:
1. SearchDAO를 별도 모듈로 분리 (`apps/api/dao/search_dao.py`)
2. 또는 hybrid_search_engine에서 lazy import 사용
3. 또는 database.py의 의존성 구조 재설계

### 🟡 Issue 2: Empty Database

**증상**:
- Retrieve step이 결과를 찾지 못함
- Timeout 직전까지 검색 실행

**필요 작업**:
- 테스트 데이터 삽입 스크립트 실행
- 최소 10개 이상의 문서 + 임베딩 데이터 필요

**기존 스크립트**:
- `ingest_sample_docs.py` (존재 확인 필요)
- `sample_docs/` 디렉토리 확인

### 🟡 Issue 3: Timeout Configuration Not Persisting

**증상**:
- `langgraph_pipeline.py` 수정 후 uvicorn --reload가 변경사항 반영 안 함
- 여러 번 재시작해도 5초 timeout이 유지됨

**원인**:
- Python 모듈 캐싱 문제
- uvicorn reload 메커니즘이 apps/orchestration 디렉토리 변경 감지 못함

**해결 방법**:
- 서버 완전 재시작 (kill + start)
- 또는 PYTHONDONTWRITEBYTECODE=1 환경변수 설정

## Phase 6 Implementation Plan

### Step 1: Circular Import 해결 (P0)

**Option A: SearchDAO 분리**
```
apps/
  api/
    dao/
      __init__.py
      search_dao.py     # SearchDAO 클래스 이동
    database.py         # ORM 모델만 유지
```

**Option B: Lazy Import**
```python
# hybrid_search_engine.py
def get_search_dao():
    from apps.api.database import SearchDAO
    return SearchDAO
```

### Step 2: 테스트 데이터 삽입

1. 기존 스크립트 확인:
   ```bash
   ls sample_docs/
   python ingest_sample_docs.py
   ```

2. 없으면 새로 생성:
   ```python
   # create_test_data.py
   - 10개 샘플 문서 생성
   - 각 문서 3-5개 chunk로 분할
   - 임베딩 생성 (OpenAI text-embedding-3-large)
   - taxonomy_nodes에 연결
   ```

3. 검증:
   ```sql
   SELECT COUNT(*) FROM documents;
   SELECT COUNT(*) FROM chunks;
   SELECT COUNT(*) FROM embeddings WHERE vec IS NOT NULL;
   ```

### Step 3: End-to-End 테스트

1. 서버 재시작 (clean start)
2. Pipeline 실행:
   ```bash
   curl -X POST http://127.0.0.1:8001/api/v1/pipeline/execute \
     -H "Content-Type: application/json" \
     -H "X-API-Key: 7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y" \
     -d '{"query":"What is machine learning?"}'
   ```
3. 기대 결과:
   - 200 OK
   - answer: 생성된 답변 텍스트
   - sources: 최소 2개 이상
   - confidence: 0.0 ~ 1.0
   - latency: < 20s

### Step 4: Performance Tuning

실측 기반 timeout 조정:
```python
STEP_TIMEOUTS = {
    "intent": <실측값 + 50% 여유>,
    "retrieve": <실측값 + 50% 여유>,
    "compose": <실측값 + 50% 여유>,
    "respond": <실측값 + 50% 여유>,
}
```

## 현재 시스템 상태

### Running Services
- **PostgreSQL**: localhost:5433/dt_rag_test
- **API Server**: http://127.0.0.1:8001 (여러 프로세스 실행 중 - 정리 필요)
- **Frontend Admin**: http://localhost:3000, http://localhost:3001

### API Key
- `7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y`

### Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test
GEMINI_API_KEY=AIzaSyBlEJuO9LGLdCJRfhNU6QIKRUQ-Q22Vl7E
PYTHONPATH=%CD%
```

## 첫 번째 액션 (Next Session)

**우선순위 1: Circular Import 해결**

1. Read `apps/search/hybrid_search_engine.py` 전체
2. Read `apps/api/database.py` 중 SearchDAO 관련 부분
3. 의존성 다이어그램 그리기 (어떤 모듈이 어떤 모듈을 import하는지)
4. 해결 방안 선택 (SearchDAO 분리 vs Lazy Import)
5. 코드 수정 및 테스트

**우선순위 2: 테스트 데이터 준비**

1. `ls sample_docs/` 확인
2. `cat ingest_sample_docs.py` 확인
3. 스크립트 실행 또는 새로 작성
4. DB 데이터 검증

**우선순위 3: End-to-End 검증**

1. 모든 백그라운드 서버 프로세스 정리
2. 새로운 서버 시작
3. Pipeline 실행 및 응답 확인
4. Latency 측정 및 timeout 조정

## Phase 6 Definition of Done

- ✅ Circular import 문제 해결됨
- ✅ 하이브리드 검색이 정상 작동 (SearchDAO 초기화 성공)
- ✅ DB에 테스트 데이터 최소 10개 문서 + 임베딩
- ✅ `POST /pipeline/execute` → 200 OK with valid response
- ✅ Response 포함: answer, sources(≥2), confidence, latency
- ✅ 실측 기반 timeout 설정 완료
- ✅ p95 latency < 20s 달성

## 참고 파일 경로

### 수정된 파일
- `apps/api/services/langgraph_service.py` (새로 생성)
- `apps/api/routers/orchestration_router.py` (lines 93-170 수정)
- `apps/orchestration/src/langgraph_pipeline.py` (lines 92-97 수정)

### 문제 파일
- `apps/search/hybrid_search_engine.py` (circular import 발생)
- `apps/api/database.py` (SearchDAO 정의)

### 확인 필요 파일
- `sample_docs/` (테스트 데이터)
- `ingest_sample_docs.py` (데이터 삽입 스크립트)
- `apps/api/dao/` (존재 여부 확인)

## 중요 노트

- **바이브코딩 원칙 준수**: 모든 코드 직접 읽기, 가정/추측 금지
- **에러 즉시 해결**: Circular import는 반드시 Phase 6에서 해결
- **Clean Start**: 여러 서버 프로세스 정리 후 단일 인스턴스만 실행
- **실측 기반 조정**: Timeout 값은 실제 실행 시간 측정 후 결정

---

**Ready to begin Phase 6 Issue Resolution**

Start with: "phase 6 시작" or "circular import 해결부터 시작"
