# 새 세션 작업: search.py Phase 2 API 마이그레이션 (21개 에러)

> **복붙용 세션 시작 프롬프트** - 이 문서 전체를 새 세션에 붙여넣으세요

---

## 작업 목표

**파일**: `apps/api/routers/search.py`
**에러 수**: 21개 (Phase 2: call-arg + attr-defined)
**작업 유형**: API 마이그레이션 (복잡한 리팩토링 필요)
**현재 상태**: Batch 8b - 미착수

### 작업 난이도: 🔴 HIGH

- **단순 Pydantic 필드 누락이 아님**
- **SearchConfig API 변경**: 12개 Unexpected keyword argument 에러
- **HybridSearchEngine signature 변경**: 2개 Unexpected keyword argument 에러
- **튜플 반환값을 객체로 사용**: 7개 attr-defined 에러
- **근본 원인**: API 버전 불일치, 코드 마이그레이션 필요

---

## 현재 프로젝트 상태

### Git 정보
- **브랜치**: `feature/SPEC-MYPY-CONSOLIDATION-002`
- **최신 커밋**: `0cde6d02` - Phase 2 Batch 8a 완료
- **작업 디렉토리**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone`

### Phase 2 진행 현황
- **전체 Phase 2 에러**: 61개 (call-arg + attr-defined)
- **search.py**: 21개 (이번 세션 목표)
- **search_router.py**: 40개 (별도 처리 중/완료)

### 완료된 Batch
- ✅ Batch 7a: evaluation 모듈 (33 errors) - commit 3c29bbeb
- ✅ Batch 7b: router 파일 (32 errors) - commit ea6f77bb
- ✅ Batch 8a: agent_task_worker.py (7 errors) - commit 0cde6d02
- 🔄 Batch 8b: **search.py (21 errors) ← 이번 세션**
- ⏳ Batch 8c: search_router.py (40 errors) - 별도 처리

---

## 에러 상세 분석

### 검증 명령어
```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone
mypy apps/api/routers/search.py --config-file=pyproject.toml 2>&1 | grep "^apps/api/routers/search.py:" | grep -E "(call-arg|attr-defined)"
```

### 21개 에러 목록

#### 그룹 1: SearchConfig API 불일치 (12 errors - Line 698)
**문제**: 구버전 SearchConfig 필드 사용
```
apps/api/routers/search.py:698: error: Unexpected keyword argument "bm25_k1" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "bm25_b" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "bm25_topk" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "vector_topk" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "vector_similarity_threshold" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "enable_reranking" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "rerank_candidates" for "SearchConfig"; did you mean "max_candidates"?  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "final_topk" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "use_optimized_engines" for "SearchConfig"  [call-arg]
apps/api/routers/search.py:698: error: Unexpected keyword argument "max_query_time" for "SearchConfig"  [call-arg]
```

**기존 코드 (Line 698)**:
```python
search_config = SearchConfig(
    # BM25 설정
    bm25_k1=request.bm25_k1,
    bm25_b=request.bm25_b,
    bm25_topk=request.bm25_topk,
    # Vector 설정
    vector_topk=request.vector_topk,
    vector_similarity_threshold=request.vector_similarity_threshold,
    embedding_model=request.embedding_model,
    # Fusion 설정
    bm25_weight=request.bm25_weight,
    vector_weight=request.vector_weight,
    # Reranking 설정
    enable_reranking=request.enable_reranking,
    rerank_candidates=request.rerank_candidates,
    rerank_threshold=request.rerank_threshold,
    # 결과 설정
    final_topk=request.final_topk,
    # 최적화 설정
    use_optimized_engines=request.use_optimized_engines,
    max_query_time=request.max_query_time,
)
```

**SearchConfig 실제 정의 위치**: `apps/api/routers/search_router.py`에 정의되어 있음

**필요한 작업**: SearchConfig 정의를 확인하고 필드 매핑 수정

#### 그룹 2: HybridSearchEngine API 불일치 (2 errors - Line 742)
**문제**: search() 메소드 signature 변경
```
apps/api/routers/search.py:742: error: Unexpected keyword argument "session" for "search" of "HybridSearchEngine"  [call-arg]
apps/api/routers/search.py:742: error: Unexpected keyword argument "query_id" for "search" of "HybridSearchEngine"; did you mean "query"?  [call-arg]
```

**기존 코드 (Line 742)**:
```python
result = await hybrid_engine.search(
    session=session,           # ← Unexpected
    query_id=query_id,         # ← Unexpected (did you mean "query"?)
    ...
)
```

**필요한 작업**: HybridSearchEngine.search() signature 확인 및 인자 수정

#### 그룹 3: 튜플 반환값을 객체로 사용 (7 errors - Line 751-787)
**문제**: search() 메소드가 `tuple[list[SearchResult], SearchMetrics]`를 반환하는데 객체의 속성으로 접근
```
apps/api/routers/search.py:751: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "results"  [attr-defined]
apps/api/routers/search.py:774: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "total_time"  [attr-defined]
apps/api/routers/search.py:779: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "total_time"  [attr-defined]
apps/api/routers/search.py:783: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "bm25_time"  [attr-defined]
apps/api/routers/search.py:784: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "vector_time"  [attr-defined]
apps/api/routers/search.py:785: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "fusion_time"  [attr-defined]
apps/api/routers/search.py:786: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "rerank_time"  [attr-defined]
apps/api/routers/search.py:787: error: "tuple[list[SearchResult], SearchMetrics]" has no attribute "total_candidates"  [attr-defined]
```

**기존 코드 (Line 751-787 추정)**:
```python
result = await hybrid_engine.search(...)  # Returns tuple[list, metrics]

# 잘못된 사용
for hit in result.results:  # ← tuple에는 .results 없음
    ...

# 메트릭 접근
total_time = result.total_time      # ← tuple에는 .total_time 없음
bm25_time = result.bm25_time        # ← tuple에는 .bm25_time 없음
...
```

**필요한 작업**: 튜플 언패킹 또는 반환값 구조 변경
```python
# 올바른 사용
results, metrics = await hybrid_engine.search(...)
for hit in results:
    ...
total_time = metrics.total_time
```

#### 기타 에러 (2 errors)
```
apps/api/routers/search.py:70: error: Module "apps.api.routers" has no attribute "monitoring"  [attr-defined]
apps/api/routers/search.py:420: error: "type[SearchDAO]" has no attribute "create_embeddings_for_chunks"  [attr-defined]
```

---

## 작업 전 필수 확인 사항

### 1. SearchConfig 정의 확인
```bash
rg "class SearchConfig" apps/api/routers/search_router.py -A 20
```

**예상되는 필드**:
- `bm25_weight`, `vector_weight`, `rerank_threshold`, `max_candidates` (새 API)
- ~~`bm25_k1`, `bm25_b`, `bm25_topk`~~ (구 API - 제거됨)

### 2. HybridSearchEngine.search() signature 확인
```bash
rg "async def search" apps/search/ -A 5
# 또는
rg "class HybridSearchEngine" apps/search/ -A 50
```

**예상되는 signature**:
```python
async def search(
    self,
    query: str,  # query_id가 아닌 query
    config: SearchConfig,
    # session 인자 없음
    ...
) -> tuple[list[SearchResult], SearchMetrics]:
    ...
```

### 3. SearchResult, SearchMetrics 정의 확인
```bash
rg "class SearchResult" apps/
rg "class SearchMetrics" apps/
```

---

## 수정 전략

### Phase 1: SearchConfig API 마이그레이션 (Line 698)
**목표**: 구버전 필드를 신버전 필드로 매핑

**단계**:
1. SearchConfig 실제 정의 읽기 (search_router.py)
2. 필드 매핑 테이블 작성:
   ```
   구버전 → 신버전
   bm25_k1, bm25_b, bm25_topk → (삭제 또는 기본값)
   vector_topk → max_candidates?
   enable_reranking → (boolean → threshold?)
   ...
   ```
3. Line 698 SearchConfig 인스턴스 수정
4. 검증: `mypy apps/api/routers/search.py --config-file=pyproject.toml 2>&1 | grep "698:"`

### Phase 2: HybridSearchEngine.search() 호출 수정 (Line 742)
**목표**: 올바른 signature로 호출

**단계**:
1. HybridSearchEngine.search() 실제 signature 확인
2. Line 742 호출 수정:
   ```python
   # Before
   result = await hybrid_engine.search(
       session=session,    # ← 제거
       query_id=query_id,  # ← query로 변경
       ...
   )

   # After
   result = await hybrid_engine.search(
       query=query,
       config=search_config,
       ...
   )
   ```
3. 검증: `mypy apps/api/routers/search.py --config-file=pyproject.toml 2>&1 | grep "742:"`

### Phase 3: 튜플 반환값 언패킹 (Line 751-787)
**목표**: 튜플을 올바르게 언패킹

**단계**:
1. search() 호출 결과 언패킹:
   ```python
   # Before
   result = await hybrid_engine.search(...)

   # After
   results, metrics = await hybrid_engine.search(...)
   ```
2. result.results → results 변경
3. result.{metric} → metrics.{metric} 변경
4. 검증: `mypy apps/api/routers/search.py --config-file=pyproject.toml 2>&1 | grep -E "751:|774:|779:|783:|784:|785:|786:|787:"`

### Phase 4: 기타 에러 해결
- Line 70: import 문제
- Line 420: SearchDAO 메소드 문제

---

## Git 워크플로우

### 작업 전 확인
```bash
git status
git log --oneline -5
mypy apps/ --config-file=pyproject.toml 2>&1 | grep -E "(call-arg|attr-defined)" | wc -l
# 예상: 61 errors (search.py 21 + search_router.py 40)
```

### 커밋 전략
```bash
# Phase 1-3 완료 후 중간 커밋
git add apps/api/routers/search.py
git commit -m "feat: SPEC-MYPY-CONSOLIDATION-002 Phase 2 Batch 8b - search.py API 마이그레이션 (21개 에러 해결)

해결된 파일 (1개):
- apps/api/routers/search.py (21 errors)

해결된 에러 유형:
- call-arg: 14개 (SearchConfig + HybridSearchEngine API 변경)
- attr-defined: 7개 (tuple 언패킹)

패턴:
- SearchConfig 구버전 필드 → 신버전 필드 매핑
- HybridSearchEngine.search() signature 수정
- tuple[list, metrics] 반환값 언패킹

Phase 2 진행 상황: 61 → 40 errors (21개 감소)
남은 Phase 2 에러: search_router.py (40개)

@CODE:MYPY-CONSOLIDATION-002 | Phase 2: API migration
"

# 검증
mypy apps/api/routers/search.py --config-file=pyproject.toml 2>&1 | grep -E "(call-arg|attr-defined)"
# 예상: (empty - no errors)

mypy apps/ --config-file=pyproject.toml 2>&1 | grep -E "(call-arg|attr-defined)" | wc -l
# 예상: 40 errors (search_router.py만 남음)
```

---

## 예상 소요 시간

- **Phase 1 (SearchConfig)**: 30분 (API 문서 확인 + 필드 매핑)
- **Phase 2 (HybridSearchEngine)**: 15분 (signature 확인 + 수정)
- **Phase 3 (Tuple 언패킹)**: 20분 (여러 위치 수정)
- **Phase 4 (기타)**: 15분
- **검증 + 커밋**: 10분
- **총 예상**: 90분 (1.5시간)

---

## 참고 파일 위치

### 핵심 파일
- **타겟**: `apps/api/routers/search.py` (수정 대상)
- **SearchConfig**: `apps/api/routers/search_router.py` (정의 확인)
- **HybridSearchEngine**: `apps/search/hybrid_search_engine.py` (signature 확인)
- **Models**: `packages/common_schemas/common_schemas/models.py` (SearchResult, SearchMetrics)

### 참고 Batch (유사 패턴)
- **Batch 7b**: `apps/api/routers/{evaluation,batch_search,orchestration_router}.py`
- **커밋**: `ea6f77bb`
- **패턴**: Pydantic Field defaults (이번에는 API 마이그레이션)

---

## 체크리스트

### 작업 전
- [ ] Git 상태 확인 (`git status`)
- [ ] 브랜치 확인 (`git branch` - feature/SPEC-MYPY-CONSOLIDATION-002)
- [ ] Phase 2 에러 수 확인 (61개)
- [ ] SearchConfig 정의 확인
- [ ] HybridSearchEngine.search() signature 확인

### Phase 1: SearchConfig (12 errors)
- [ ] SearchConfig 클래스 정의 읽기
- [ ] 필드 매핑 테이블 작성
- [ ] Line 698 수정
- [ ] 검증 (12개 에러 해결 확인)

### Phase 2: HybridSearchEngine (2 errors)
- [ ] search() signature 확인
- [ ] Line 742 수정
- [ ] 검증 (2개 에러 해결 확인)

### Phase 3: Tuple 언패킹 (7 errors)
- [ ] search() 반환값 구조 확인
- [ ] Line 742 결과 언패킹
- [ ] Line 751-787 속성 접근 수정
- [ ] 검증 (7개 에러 해결 확인)

### Phase 4: 기타 (2 errors)
- [ ] Line 70 import 수정
- [ ] Line 420 SearchDAO 수정
- [ ] 검증 (2개 에러 해결 확인)

### 최종 검증
- [ ] search.py Phase 2 에러 0개 확인
- [ ] 전체 Phase 2 에러 40개 확인 (search_router.py만 남음)
- [ ] Git 커밋 생성
- [ ] 커밋 메시지 검증

---

## 세션 시작 프롬프트 (복붙용)

```
SPEC-MYPY-CONSOLIDATION-002 Phase 2 Batch 8b 작업을 시작합니다.

**작업 파일**: apps/api/routers/search.py
**에러 수**: 21개 (call-arg 14개 + attr-defined 7개)
**작업 유형**: API 마이그레이션 (복잡한 리팩토링)

**현재 상태**:
- 브랜치: feature/SPEC-MYPY-CONSOLIDATION-002
- 최신 커밋: 0cde6d02 (Batch 8a 완료)
- Phase 2 총 에러: 61개 (search.py 21 + search_router.py 40)

**작업 계획**:
Phase 1: SearchConfig API 마이그레이션 (12 errors)
Phase 2: HybridSearchEngine.search() 호출 수정 (2 errors)
Phase 3: tuple 반환값 언패킹 (7 errors)
Phase 4: 기타 에러 해결 (2 errors)

상세한 작업 지침은 `.moai/session-handoff/search-py-phase2-refactoring.md` 파일을 참조하세요.

작업을 시작하겠습니다.
```

---

**문서 작성일**: 2025-10-28
**작성자**: Alfred (SPEC-MYPY-CONSOLIDATION-002)
**상태**: 준비 완료 ✅
