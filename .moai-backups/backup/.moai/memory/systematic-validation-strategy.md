# 체계적 검증 전략 (Systematic Validation Strategy)

> "아키텍처 맵 없이는 수정 없다. 계층별 검증 없이는 배포 없다."

## 문제 정의

**안티패턴**: 전략 없는 디버깅
- ❌ 국소적 수정 → 전체 영향 파악 안됨
- ❌ 코드 읽기만 → 실제 실행 경로 확인 안함
- ❌ 문서 기반 검증 → 실제 작동 여부 확인 안함
- 결과: **스파게티 코드, 부정확한 수정, 새로운 버그 유발**

**해결책**: MoAI-ADK 기반 체계적 검증

## Phase 1: Architecture Discovery (아키텍처 발견)

### 목표
실제 호출 경로와 사용되는 코드를 정확히 파악

### 도구
```bash
# 1. Import 체인 추적
rg "^from|^import" apps/api/main.py -A 2

# 2. 실제 라우터 등록 확인
rg "app.include_router|router.include_router" apps/api/main.py -n

# 3. 함수 호출 체인 추적
rg "def search|async def search" apps/ -n
rg "\.search\(" apps/ -n | head -20

# 4. Dead code 식별 (import되지 않는 파일)
find apps/ -name "*.py" | while read f; do
  filename=$(basename "$f" .py)
  if ! rg "import.*$filename|from.*$filename" apps/ > /dev/null; then
    echo "Dead code candidate: $f"
  fi
done
```

### 산출물
**Architecture Map 문서**:
```markdown
## 실제 호출 경로

### Search API 호출 체인
1. Nginx (8001:8000) → FastAPI (main.py)
2. main.py → search_router.py (Line 462)
3. search_router.py → SearchService._legacy_hybrid_search (Line 131)
4. SearchService → hybrid_search_engine.hybrid_search (Line 144)
5. hybrid_search_engine → _perform_bm25_search + _perform_vector_search (Lines 576-577)
6. hybrid_search_engine → database (async_session)

### 사용되는 코드 vs 미사용 코드
✅ 사용됨:
- apps/search/hybrid_search_engine.py (실제 검색 엔진)
- apps/api/routers/search_router.py (API 엔드포인트)

❌ 미사용:
- apps/api/database.py:SearchDAO (호출되지 않음)
```

## Phase 2: Layer-by-Layer Validation (계층별 검증)

### L1: Database Layer
```bash
# 스키마 검증
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "\d documents"
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "\d chunks"
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "\d embeddings"

# 데이터 존재 확인
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "SELECT COUNT(*) FROM documents"
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "SELECT COUNT(*) FROM chunks"
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "SELECT COUNT(*) FROM embeddings"

# JOIN 쿼리 직접 실행
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "
  SELECT c.chunk_id, LEFT(c.text, 30)
  FROM chunks c
  JOIN embeddings e ON c.chunk_id = e.chunk_id
  LIMIT 3
"
```

**결과 기록**: ✅ PASS / ❌ FAIL + 에러 메시지

### L2: DAO/Engine Layer
```python
# Python REPL에서 직접 호출
docker exec -it dt_rag_api python3
>>> from apps.search.hybrid_search_engine import HybridSearchEngine
>>> import asyncio
>>> engine = HybridSearchEngine()
>>> results, metrics = asyncio.run(engine.search("test", top_k=3))
>>> print(f"Results: {len(results)}, Time: {metrics.total_time}")
```

**결과 기록**: ✅ PASS / ❌ FAIL + 스택 트레이스

### L3: Service Layer
```bash
# pytest로 서비스 로직 검증
docker exec dt_rag_api pytest tests/test_search_service.py -v
```

**결과 기록**: ✅ PASS / ❌ FAIL + 실패한 테스트 목록

### L4: API Layer
```bash
# curl로 실제 API 호출
curl -X POST http://127.0.0.1:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <VALID_KEY>" \
  -d '{"q":"test","max_results":3}' \
  --max-time 5 -v
```

**결과 기록**:
- Status Code: 200 / 403 / 500 / Timeout
- Response Time: XXX ms
- Error Message: (if any)

## Phase 3: Failure Point Isolation (실패 지점 격리)

### Top-Down 추적
```bash
# 1. API 로그 실시간 모니터링
docker logs -f dt_rag_api 2>&1 | grep -E "ERROR|WARNING|search"

# 2. 각 계층에 디버그 로깅 추가
# hybrid_search_engine.py Line 520 이후에 추가:
logger.info(f"[DEBUG] Search query: {query}, filters: {filters}")
logger.info(f"[DEBUG] BM25 results: {len(bm25_results)}")
logger.info(f"[DEBUG] Vector results: {len(vector_results)}")
```

### Bottom-Up 검증
```bash
# L1부터 시작해서 각 계층이 독립적으로 작동하는지 확인
# L1 ✅ → L2 ✅ → L3 ✅ → L4 ❌
# 결론: L3과 L4 사이에 문제 있음 (API 인증 등)
```

## Phase 4: Systematic Fix with Impact Analysis

### 변경 전 분석
```bash
# 1. 영향받는 파일 식별
rg "SearchDAO|hybrid_search" apps/ tests/ -l

# 2. 테스트 파일 확인
find tests/ -name "*search*.py"

# 3. SPEC 문서 확인
rg "@SPEC:SEARCH" .moai/specs/ -l
```

### 변경 적용
```bash
# 1. SPEC 우선 확인
cat .moai/specs/SPEC-SEARCH-001/spec.md

# 2. 테스트 먼저 수정 (RED)
# tests/test_hybrid_search.py 수정

# 3. 코드 수정 (GREEN)
# apps/search/hybrid_search_engine.py 수정

# 4. 리팩토링 (REFACTOR)
# 품질 개선
```

### 변경 후 검증
```bash
# 1. 단위 테스트
pytest tests/test_hybrid_search.py -v

# 2. 통합 테스트
pytest tests/integration/test_search_integration.py -v

# 3. E2E 테스트
curl -X POST http://127.0.0.1:8001/api/v1/search/ ...

# 4. 성능 검증
# 응답 시간 < 1s 확인
```

## MoAI-ADK 통합

### @agent-debug-helper 활용
```markdown
디버깅 시 다음과 같이 호출:

"@agent-debug-helper
문제: Search API가 403 Forbidden 반환
증상: curl 호출 시 타임아웃 아닌 즉시 403
컨텍스트:
- Docker 컨테이너 모두 실행 중
- Database에 데이터 존재 확인
- PostgreSQL 쿼리 직접 실행 시 정상 작동

체계적 분석 요청"
```

### TAG 시스템 활용
```bash
# 1. 관련 SPEC 찾기
rg "@SPEC:SEARCH|@SPEC:DATABASE" .moai/specs/ -l

# 2. 구현 코드 추적
rg "@CODE:SEARCH-001" apps/ -n

# 3. 테스트 코드 확인
rg "@TEST:SEARCH-001" tests/ -n

# 4. 변경 이력 확인
rg "## HISTORY" .moai/specs/SPEC-SEARCH-001/spec.md -A 30
```

## 체크리스트

### Phase 1: Architecture Discovery
- [ ] Import 체인 추적 완료
- [ ] 실제 호출 경로 문서화
- [ ] Dead code 식별
- [ ] Architecture Map 작성

### Phase 2: Layer Validation
- [ ] L1 (Database): 스키마, 데이터, 쿼리 검증
- [ ] L2 (DAO/Engine): 직접 호출 테스트
- [ ] L3 (Service): pytest 실행
- [ ] L4 (API): curl 테스트

### Phase 3: Failure Isolation
- [ ] Top-down 로그 분석
- [ ] Bottom-up 계층별 검증
- [ ] 정확한 실패 지점 식별

### Phase 4: Systematic Fix
- [ ] SPEC 문서 확인
- [ ] 영향 분석 완료
- [ ] TDD로 수정 (RED → GREEN → REFACTOR)
- [ ] 전체 테스트 통과

## 예시: Search API 검증

### 1. Architecture Discovery
```bash
# 호출 체인 확인
rg "search_router" apps/api/main.py -B 2 -A 2
# 결과: Line 462 app.include_router(search_router)

rg "hybrid_search" apps/api/routers/search_router.py -n
# 결과: Line 144 await hybrid_search(...)

rg "class HybridSearchEngine" apps/search/ -n
# 결과: hybrid_search_engine.py:490
```

**결론**: search_router → hybrid_search_engine (SearchDAO는 미사용)

### 2. Layer Validation

**L1 Database**:
```bash
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c "
SELECT COUNT(*) as chunks FROM chunks;
"
# 결과: 3 chunks ✅
```

**L2 Engine**:
```python
# hybrid_search_engine.py가 올바른 스키마 사용 확인
# Line 672-692: chunks c JOIN documents d ✅
# Line 764-780: chunks c JOIN embeddings e ✅
```

**L3 Service**:
```bash
# SearchService 로직 확인
# Line 131-181: hybrid_search 호출 ✅
```

**L4 API**:
```bash
curl -X POST http://127.0.0.1:8001/api/v1/search/ ...
# 결과: 403 Forbidden ❌
# 원인: API Key 검증 실패
```

### 3. Failure Isolation

**Top-down**:
```bash
docker logs dt_rag_api | grep "API_KEY_SECURITY_EVENT"
# 발견: "INVALID_FORMAT | key contains weak patterns"
```

**결론**: L4 (API 인증)에서 실패, 스키마 문제 아님

### 4. Systematic Fix

**변경 불필요**: hybrid_search_engine.py는 이미 올바른 스키마 사용

**실제 문제**: API Key 보안 검증이 테스트 키를 거부

**해결책**: 올바른 API Key 사용 또는 보안 검증 완화 (개발 환경)

---

## 원칙

1. **아키텍처 맵 우선**: 실제 호출 경로를 파악하기 전에는 코드 수정하지 않는다
2. **계층별 독립 검증**: 각 계층이 독립적으로 작동하는지 확인 후 다음 계층으로
3. **Bottom-up + Top-down**: 양방향 검증으로 실패 지점 정확히 식별
4. **SPEC 기반 수정**: 모든 변경은 SPEC 문서 기반으로
5. **영향 분석 필수**: 한 파일 수정 전에 영향받는 모든 파일 식별

이 전략은 **명확한 상황 파악 → 정확한 수정 → 검증 완료**의 체계적 흐름을 보장한다.
