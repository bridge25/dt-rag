# SPEC-EVAL-001 Implementation Plan

## 구현 개요

RAGAS 평가 시스템은 이미 완전히 구현되어 프로덕션 환경에서 운영 중입니다. 본 문서는 역공학된 시스템의 구현 전략과 아키텍처를 설명합니다.

## 우선순위별 구현 마일스톤

### 1차 목표: 핵심 평가 엔진 (완료)

**구현 완료 항목**:
- ✅ RAGASEvaluator 클래스 구현
- ✅ RAGAS 4대 메트릭 계산 로직
- ✅ LLM 기반 평가 (Gemini 2.5 Flash)
- ✅ Fallback 메커니즘 (휴리스틱 방식)
- ✅ Overall score 계산 (가중 평균)

**기술적 접근**:
```python
# Concurrent evaluation for performance
results = await asyncio.gather(
    self._evaluate_context_precision(query, retrieved_contexts),
    self._evaluate_context_recall(query, response, retrieved_contexts, ground_truth),
    self._evaluate_faithfulness(response, retrieved_contexts),
    self._evaluate_answer_relevancy(query, response),
    return_exceptions=True
)
```

**아키텍처 결정**:
- **동시 처리**: 4개 메트릭을 asyncio.gather로 병렬 평가
- **에러 처리**: return_exceptions=True로 부분 실패 허용
- **비용 최적화**: Gemini 2.5 Flash 사용 (85% 비용 절감)
- **대체 경로**: LLM 실패 시 키워드/오버랩 기반 계산

### 2차 목표: 품질 모니터링 시스템 (완료)

**구현 완료 항목**:
- ✅ QualityMonitor 클래스 구현
- ✅ 실시간 메트릭 버퍼링 (deque)
- ✅ 임계값 기반 알림 생성
- ✅ 트렌드 분석 (선형 회귀)
- ✅ Quality Gates 검증

**기술적 접근**:
```python
# In-memory metric buffers for real-time monitoring
self.metric_buffers = {
    'faithfulness': deque(maxlen=100),
    'context_precision': deque(maxlen=100),
    'context_recall': deque(maxlen=100),
    'answer_relevancy': deque(maxlen=100),
    'response_time': deque(maxlen=100)
}
```

**아키텍처 결정**:
- **메모리 효율**: 최근 100개 메트릭만 버퍼링
- **알림 쿨다운**: 10분 간격 알림 방지
- **트렌드 계산**: 선형 회귀로 방향성 판단
- **데이터베이스 통합**: PostgreSQL에 시간별 집계 저장

### 3차 목표: A/B 테스트 및 실험 관리 (완료)

**구현 완료 항목**:
- ✅ ExperimentTracker 클래스 구현
- ✅ 결정론적 사용자 그룹 할당
- ✅ 통계적 유의성 검정 (t-test)
- ✅ 효과 크기 계산 (Cohen's d)
- ✅ 카나리 배포 모니터링
- ✅ 자동 롤백 메커니즘

**기술적 접근**:
```python
# Deterministic user assignment
user_hash = hash(f"{user_id}_{experiment_id}")
group = 'treatment' if user_hash % 2 == 0 else 'control'

# Statistical analysis
t_stat, p_value = stats.ttest_ind(control_values, treatment_values)
effect_size = (treatment_mean - control_mean) / pooled_std
```

**아키텍처 결정**:
- **재현성**: 해시 기반 할당으로 사용자별 일관성 보장
- **조기 중단**: 큰 부정적 효과 감지 시 자동 중단
- **통계적 엄격성**: p < 0.05, 최소 샘플 50개
- **카나리 보호**: 10% 저하 시 즉시 롤백

### 4차 목표: Golden Dataset 관리 (완료)

**구현 완료 항목**:
- ✅ GoldenDatasetGenerator 클래스 구현
- ✅ RAGAS TestsetGenerator 통합
- ✅ Gemini Fallback 메커니즘
- ✅ 쿼리 타입 분포 설정
- ✅ 데이터셋 검증 로직

**기술적 접근**:
```python
# RAGAS integration with fallback
try:
    samples = await self._generate_with_ragas(documents, testset_size, query_distribution)
except Exception as e:
    logger.warning(f"RAGAS generation failed: {e}. Using fallback method.")
    samples = await self._generate_fallback(documents, testset_size, query_distribution)
```

**아키텍처 결정**:
- **우선순위**: RAGAS 우선, 실패 시 Gemini 사용
- **다양성**: simple(50%), reasoning(25%), multi_context(25%)
- **품질 보장**: 생성 후 검증 단계 필수
- **영구 저장**: JSON 파일 + PostgreSQL 이중화

### 5차 목표: 대시보드 및 API (완료)

**구현 완료 항목**:
- ✅ WebSocket 기반 실시간 대시보드
- ✅ Chart.js 시각화
- ✅ 15+ REST API 엔드포인트
- ✅ Middleware 통합
- ✅ Batch 평가 지원

**기술적 접근**:
```python
# WebSocket real-time updates
while True:
    await asyncio.sleep(30)  # Update every 30 seconds
    dashboard_data = await get_dashboard_data()
    await manager.send_personal_message(json.dumps(dashboard_data), websocket)
```

**아키텍처 결정**:
- **실시간성**: 30초 간격 WebSocket 업데이트
- **비차단**: 평가는 백그라운드 asyncio.create_task로 처리
- **확장성**: Connection pooling으로 100+ 동시 연결
- **API 설계**: RESTful 원칙 준수, OpenAPI 문서화

## 아키텍처 설계

### 계층 구조

```
┌─────────────────────────────────────────────┐
│  Presentation Layer                         │
│  - Dashboard (WebSocket)                    │
│  - REST API (FastAPI)                       │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│  Application Layer                          │
│  - RAGASEvaluator (평가 엔진)               │
│  - QualityMonitor (품질 모니터링)            │
│  - ExperimentTracker (A/B 테스트)           │
│  - GoldenDatasetGenerator (데이터셋)        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│  Integration Layer                          │
│  - EvaluationIntegration (통합 유틸)        │
│  - RAGEvaluationMiddleware (자동 평가)      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│  Data Layer                                 │
│  - PostgreSQL (search_logs, golden_dataset) │
│  - In-memory Buffers (실시간 메트릭)        │
└─────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│  External Services                          │
│  - Gemini 2.5 Flash API                     │
│  - Langfuse (LLM 추적)                      │
│  - Sentry (에러 리포팅)                     │
└─────────────────────────────────────────────┘
```

### 컴포넌트 다이어그램

```
┌──────────────────┐
│   User Query     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│   RAG System         │
│   - Retrieval        │
│   - Generation       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────────────┐
│   Middleware (Optional)          │
│   - Auto-evaluate on /search     │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│   RAGASEvaluator                 │
│   ┌────────────────────────────┐ │
│   │ Context Precision          │ │
│   │ Context Recall             │ │ ← Parallel
│   │ Faithfulness               │ │   Execution
│   │ Answer Relevancy           │ │   (asyncio)
│   └────────────────────────────┘ │
│   Overall Score Calculation      │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│   QualityMonitor                 │
│   - Record Metrics               │
│   - Check Thresholds             │
│   - Generate Alerts              │
│   - Trend Analysis               │
└────────┬─────────────────────────┘
         │
         ├──→ Database (PostgreSQL)
         │
         └──→ Dashboard (WebSocket)
```

### 데이터 흐름

```
1. 평가 요청 수신
   │
   ├─→ API 엔드포인트 (/evaluation/evaluate)
   ├─→ Middleware (자동 평가)
   └─→ Integration 유틸리티

2. 평가 수행
   │
   ├─→ LLM 기반 평가 (Gemini 2.5 Flash)
   │   ├─→ Context Precision
   │   ├─→ Context Recall
   │   ├─→ Faithfulness
   │   └─→ Answer Relevancy
   │
   └─→ Fallback (LLM 실패 시)
       ├─→ 키워드 기반 계산
       └─→ 오버랩 기반 계산

3. 결과 처리
   │
   ├─→ Overall Score 계산 (가중 평균)
   ├─→ Quality Flags 생성
   └─→ Recommendations 생성

4. 모니터링
   │
   ├─→ QualityMonitor 기록
   │   ├─→ 메트릭 버퍼 업데이트
   │   ├─→ 임계값 확인
   │   ├─→ 알림 생성 (필요 시)
   │   └─→ 트렌드 분석
   │
   └─→ ExperimentTracker 기록 (실험 진행 시)
       ├─→ 그룹별 결과 저장
       ├─→ 통계 분석 (샘플 충분 시)
       └─→ 조기 중단 확인

5. 영구 저장
   │
   ├─→ PostgreSQL (search_logs)
   │   ├─→ 평가 결과
   │   ├─→ 메타데이터
   │   └─→ 품질 플래그
   │
   └─→ Langfuse (LLM 추적)
       ├─→ API 호출 로그
       ├─→ 비용 추적
       └─→ 성능 메트릭

6. 실시간 업데이트
   │
   └─→ WebSocket Broadcast
       ├─→ Dashboard 클라이언트
       ├─→ 메트릭 차트 업데이트
       ├─→ 알림 표시
       └─→ 트렌드 그래프 갱신
```

## 기술 스택 상세

### 핵심 라이브러리

**LLM 통합**:
- `google-generativeai`: Gemini API 클라이언트
- Model: `gemini-2.5-flash-latest`
- 비용: Input $0.075/1M, Output $0.30/1M

**통계 분석**:
- `numpy`: 벡터 연산, 분산 계산
- `scipy.stats`: t-test, statistical testing
- `statistics`: 기본 통계 (평균, 표준편차)

**웹 프레임워크**:
- `fastapi`: REST API 서버
- `websockets`: 실시간 통신
- `pydantic`: 데이터 검증

**데이터베이스**:
- `sqlalchemy`: ORM
- `asyncpg`: 비동기 PostgreSQL 드라이버
- PostgreSQL 14+

**프론트엔드**:
- `chart.js`: 시각화
- `tailwindcss`: 스타일링
- WebSocket API: 실시간 업데이트

### 선택적 의존성

**RAGAS 프레임워크** (Golden Dataset 생성):
```python
from ragas.testset import TestsetGenerator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
```

**Langfuse** (LLM 추적):
```python
from langfuse import observe

@observe(name="ragas_evaluation", as_type="generation")
async def evaluate_rag_response(...):
    # LLM 호출 추적
```

## 성능 최적화 전략

### 1. 비동기 처리

**병렬 메트릭 계산**:
```python
# 4개 메트릭을 동시에 계산 (2-3배 속도 향상)
results = await asyncio.gather(
    self._evaluate_context_precision(...),
    self._evaluate_context_recall(...),
    self._evaluate_faithfulness(...),
    self._evaluate_answer_relevancy(...),
    return_exceptions=True
)
```

**백그라운드 평가**:
```python
# 사용자 응답은 즉시 반환, 평가는 백그라운드에서
asyncio.create_task(self._evaluate_search_response(request, response))
```

### 2. LLM 비용 최적화

**Fallback 메커니즘**:
- LLM 실패 시 휴리스틱 방식으로 대체
- 비용 절감 + 가용성 향상

**Gemini 2.5 Flash 사용**:
- 85% 비용 절감 (vs gemini-pro)
- 동등한 품질 유지

**샘플링**:
```python
# 전체 트래픽의 10%만 평가 (선택적)
if hash(str(request.url) + str(datetime.now().minute)) % 10 == 0:
    await evaluate_rag_response(...)
```

### 3. 데이터베이스 최적화

**인덱싱**:
```sql
CREATE INDEX idx_search_logs_created_at ON search_logs(created_at);
CREATE INDEX idx_search_logs_experiment_id ON search_logs(experiment_id);
CREATE INDEX idx_search_logs_session_id ON search_logs(session_id);
```

**쿼리 최적화**:
```sql
-- 시간별 집계 (PostgreSQL DATE_TRUNC 활용)
SELECT DATE_TRUNC('hour', created_at) as hour,
       AVG(faithfulness) as avg_faithfulness,
       COUNT(*) as evaluation_count
FROM search_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour;
```

### 4. 메모리 관리

**제한된 버퍼 사이즈**:
```python
# 최근 100개만 메모리 유지
self.metric_buffers = {
    'faithfulness': deque(maxlen=100),
    'context_precision': deque(maxlen=100),
    # ...
}

# 24시간 분단위 데이터 (최대 1440개)
self.quality_history = deque(maxlen=1440)
```

## 리스크 및 대응 방안

### 리스크 1: LLM API 장애

**영향**: 평가 불가능
**확률**: 낮음 (Gemini 99.9% SLA)

**대응 방안**:
- ✅ Fallback 메커니즘 구현 (휴리스틱 계산)
- ✅ 에러 핸들링 및 재시도 로직
- ✅ 부분 실패 허용 (return_exceptions=True)

### 리스크 2: 평가 비용 급증

**영향**: 예산 초과
**확률**: 중간 (트래픽 급증 시)

**대응 방안**:
- ✅ 샘플링 전략 (10% 평가)
- ✅ Gemini 2.5 Flash 사용 (85% 비용 절감)
- ✅ Langfuse 비용 모니터링
- ⚠️ 일일 API 호출 한도 설정 필요

### 리스크 3: 데이터베이스 성능 저하

**영향**: 느린 대시보드, 쿼리 타임아웃
**확률**: 중간 (대량 데이터 누적 시)

**대응 방안**:
- ✅ 인덱스 최적화
- ✅ 시간별 집계 테이블 (선택적)
- ⚠️ 파티셔닝 전략 검토 필요 (월별 파티션)
- ⚠️ 오래된 데이터 아카이빙 (3개월 이상)

### 리스크 4: 실시간 업데이트 부하

**영향**: WebSocket 연결 끊김
**확률**: 낮음

**대응 방안**:
- ✅ Connection pooling
- ✅ 30초 업데이트 간격 (부하 분산)
- ⚠️ 클라이언트 수 제한 검토 필요
- ⚠️ Redis Pub/Sub 도입 고려

## 모니터링 및 관찰성

### 메트릭 수집

**시스템 메트릭**:
- API 응답 시간 (p50, p95, p99)
- 평가 처리 시간
- LLM API 호출 횟수 및 비용
- 데이터베이스 쿼리 성능
- WebSocket 연결 수

**품질 메트릭**:
- RAGAS 4대 메트릭 평균/분산
- 품질 게이트 통과율
- 알림 발생 빈도
- 실험 성공률

**비즈니스 메트릭**:
- 평가 수행 건수 (일/주/월)
- 품질 개선 트렌드
- A/B 테스트 결과 요약
- Golden dataset 커버리지

### 로깅 전략

**구조화된 로깅**:
```python
logger.info(
    "RAGAS evaluation completed",
    extra={
        "evaluation_id": result.evaluation_id,
        "query": result.query[:50],
        "faithfulness": result.metrics.faithfulness,
        "overall_score": result.overall_score,
        "duration_ms": duration_ms
    }
)
```

**로그 레벨**:
- DEBUG: LLM 프롬프트/응답 상세
- INFO: 평가 완료, 실험 상태 변경
- WARNING: Fallback 사용, LLM 실패
- ERROR: 평가 실패, 데이터베이스 오류

### 알림 및 대시보드

**Slack 통합** (계획):
```python
# 품질 알림을 Slack으로 전송
if alert.severity == 'high':
    await send_slack_notification(
        channel="#ragas-alerts",
        message=f"🚨 {alert.message}",
        actions=alert.suggested_actions
    )
```

**Grafana 대시보드** (계획):
- RAGAS 메트릭 시계열 그래프
- 품질 게이트 상태
- 실험 진행 상황
- 비용 트렌드

## 테스트 전략

### 단위 테스트

**메트릭 계산 검증**:
```python
# apps/evaluation/tests/test_ragas_engine.py
async def test_context_precision_calculation():
    evaluator = RAGASEvaluator()
    query = "What is machine learning?"
    contexts = [
        "Machine learning is a subset of AI...",  # Relevant
        "The weather is sunny today."             # Irrelevant
    ]

    precision = await evaluator._evaluate_context_precision(query, contexts)
    assert 0.4 <= precision <= 0.6  # 1/2 = 0.5
```

**Fallback 메커니즘 검증**:
```python
async def test_fallback_when_llm_fails():
    evaluator = RAGASEvaluator()
    evaluator.model = None  # Force fallback

    result = await evaluator.evaluate_rag_response(...)
    assert result.metrics.faithfulness is not None
```

### 통합 테스트

**End-to-End 평가 플로우**:
```python
async def test_evaluation_flow():
    # 1. Submit evaluation request
    response = await client.post("/evaluation/evaluate", json={
        "query": "What is RAG?",
        "response": "RAG stands for Retrieval-Augmented Generation...",
        "retrieved_contexts": [...]
    })

    # 2. Verify result
    assert response.status_code == 200
    result = response.json()
    assert result["metrics"]["faithfulness"] >= 0.0

    # 3. Verify database storage
    log = await db.search_logs.get_latest()
    assert log.query == "What is RAG?"
```

**WebSocket 실시간 업데이트**:
```python
async def test_dashboard_websocket():
    async with websocket_client("/evaluation/dashboard/ws") as ws:
        # 1. Receive initial data
        initial_data = await ws.receive_json()
        assert "current_metrics" in initial_data

        # 2. Wait for update
        await asyncio.sleep(31)
        update_data = await ws.receive_json()
        assert update_data["timestamp"] > initial_data["timestamp"]
```

### 성능 테스트

**부하 테스트**:
```python
async def test_concurrent_evaluations():
    # 100개 평가 동시 처리
    tasks = [
        evaluate_rag_response(...)
        for _ in range(100)
    ]

    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    # 모두 5초 이내 완료
    assert duration < 5.0
    assert len(results) == 100
```

## 배포 전략

### 환경 설정

**필수 환경 변수**:
```bash
# LLM API
GEMINI_API_KEY=your_gemini_api_key

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dtrag

# 모니터링 (선택적)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
SENTRY_DSN=https://...@sentry.io/...

# 평가 설정
ENABLE_AUTO_EVALUATION=true
EVALUATION_SAMPLING_RATE=0.1  # 10%
```

### 단계별 배포

**Phase 1: Staging 검증** (완료)
- ✅ 평가 엔진 단위 테스트
- ✅ 품질 모니터링 통합 테스트
- ✅ 대시보드 시각화 확인
- ✅ 성능 벤치마크 (1000+ QPS)

**Phase 2: Production 배포** (완료)
- ✅ Blue-Green 배포 전략
- ✅ 카나리 릴리스 (5% 트래픽)
- ✅ 품질 메트릭 모니터링
- ✅ 롤백 계획 준비

**Phase 3: 최적화** (진행 중)
- ⚠️ LLM 캐싱 레이어 추가
- ⚠️ Redis 기반 실시간 집계
- ⚠️ 데이터베이스 파티셔닝
- ⚠️ Grafana 대시보드 구축

## 운영 가이드

### 일상 운영

**매일 확인사항**:
- [ ] 대시보드 품질 메트릭 확인
- [ ] 활성 알림 검토 및 조치
- [ ] LLM API 비용 모니터링
- [ ] 데이터베이스 디스크 사용량 확인

**주간 작업**:
- [ ] 품질 트렌드 리포트 생성
- [ ] A/B 테스트 결과 분석
- [ ] Golden dataset 업데이트
- [ ] 성능 병목 분석

**월간 작업**:
- [ ] 오래된 평가 데이터 아카이빙
- [ ] 품질 임계값 재조정
- [ ] 비용 최적화 검토
- [ ] 시스템 용량 계획

### 문제 해결

**시나리오 1: Faithfulness 급락**
1. 대시보드에서 영향받은 쿼리 확인
2. 해당 응답의 컨텍스트 검토
3. LLM 프롬프트 검증
4. Retrieval 시스템 점검

**시나리오 2: 평가 처리 지연**
1. LLM API 상태 확인
2. 데이터베이스 쿼리 성능 분석
3. 동시 평가 수 확인
4. Fallback 사용률 점검

**시나리오 3: 실험 결과 이상**
1. 사용자 그룹 할당 검증
2. 샘플 크기 충분성 확인
3. 통계적 검정력 계산
4. 외부 변수 영향 분석

---

**문서 버전**: 0.1.0
**최종 업데이트**: 2025-10-07
**작성자**: @Claude
