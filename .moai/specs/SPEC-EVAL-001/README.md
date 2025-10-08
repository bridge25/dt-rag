# SPEC-EVAL-001: RAGAS Evaluation System

## Quick Reference

**ID**: EVAL-001  
**Version**: 0.1.0  
**Status**: ✅ Completed  
**Priority**: High  
**Category**: Feature (Evaluation System)

## Overview

완전히 구현된 RAGAS 기반 RAG 평가 시스템의 역공학 문서화입니다.

## 문서 구조

- **spec.md** (960줄): 핵심 명세
  - EARS 요구사항
  - RAGAS 4대 메트릭 상세
  - 데이터 모델 및 아키텍처
  - 검증 방법

- **plan.md** (688줄): 구현 계획
  - 우선순위별 마일스톤
  - 아키텍처 설계
  - 성능 최적화 전략
  - 리스크 대응 방안

- **acceptance.md** (1033줄): 수락 기준
  - Given-When-Then 테스트 시나리오
  - 품질 게이트 기준
  - 성능 임계값
  - Definition of Done

## 핵심 메트릭

| Metric | Target | Minimum | Implementation |
|--------|--------|---------|----------------|
| Faithfulness | ≥ 0.90 | ≥ 0.85 | ✅ LLM + Fallback |
| Context Precision | ≥ 0.85 | ≥ 0.75 | ✅ LLM + Fallback |
| Context Recall | ≥ 0.80 | ≥ 0.70 | ✅ LLM + Fallback |
| Answer Relevancy | ≥ 0.90 | ≥ 0.80 | ✅ LLM + Fallback |

## 구현 완성도

### ✅ Completed Features (100%)

- **Core Evaluation Engine**
  - RAGASEvaluator with 4 metrics
  - Gemini 2.5 Flash API integration (85% cost reduction)
  - Fallback mechanisms
  - Overall score calculation (weighted average)

- **Quality Monitoring**
  - Real-time metric buffering (deque, 100 recent)
  - Threshold-based alerting with cooldown (10min)
  - Trend analysis (linear regression)
  - Quality gates enforcement

- **A/B Testing & Experimentation**
  - Deterministic user assignment (hash-based)
  - Statistical analysis (t-test, Cohen's d, 95% CI)
  - Early stopping (harm detection)
  - Canary deployment with auto-rollback (10% degradation threshold)

- **Golden Dataset Management**
  - RAGAS TestsetGenerator integration
  - Gemini fallback mechanism
  - Dataset validation and quality scoring
  - Query type distribution (simple/reasoning/multi_context)

- **Dashboard & Visualization**
  - WebSocket real-time updates (30s interval)
  - Chart.js visualizations
  - Alert management
  - System recommendations

- **REST API Integration**
  - 15+ endpoints (evaluate, batch, dashboard, experiments, dataset)
  - Middleware integration (auto-evaluation)
  - Database persistence (PostgreSQL)
  - Langfuse LLM tracking

## 파일 구조

```
apps/evaluation/
├── ragas_engine.py           # 650 lines - Core evaluation engine
├── quality_monitor.py        # 495 lines - Quality monitoring
├── integration.py            # 408 lines - Integration utilities
├── models.py                 # 218 lines - Data models
├── experiment_tracker.py     # 522 lines - A/B testing
├── golden_dataset_generator.py # 336 lines - Golden dataset
├── dashboard.py              # 533 lines - Dashboard
└── evaluation_router.py      # 763 lines - REST API

Total: 3,925 lines
```

## 데이터베이스 스키마

**search_logs**: 평가 결과 저장
- RAGAS 4대 메트릭
- 메타데이터 (session, experiment, model version)
- 품질 플래그 및 이슈

**golden_dataset**: 벤치마크 데이터
- Query-Answer-Context 트리플
- 난이도 레벨 및 카테고리
- 품질 점수

**experiment_runs**: A/B 테스트
- 실험 설정 (control/treatment config)
- 통계 파라미터
- 결과 및 유의성

## 성능 메트릭

- **Evaluation Latency**: p95 < 5s
- **Concurrent Throughput**: 100+ req/10s
- **Dashboard Update**: < 1s for 100 clients
- **Database Query**: < 500ms for 24h aggregates

## 비용 최적화

- **Gemini 2.5 Flash**: 85% cost reduction vs gemini-pro
  - Input: $0.075/1M tokens
  - Output: $0.30/1M tokens
- **Sampling**: 10% traffic evaluation (configurable)
- **Fallback**: Heuristic methods when LLM fails

## Quick Start

### API 사용 예시

```python
# Single evaluation
response = await client.post("/evaluation/evaluate", json={
    "query": "What is machine learning?",
    "response": "Machine learning is...",
    "retrieved_contexts": ["Context 1", "Context 2"]
})

# Dashboard access
ws = await websocket_client("/evaluation/dashboard/ws")
data = await ws.receive_json()

# Start A/B test
experiment_id = await client.post("/evaluation/experiments", json={
    "experiment_id": "exp_001",
    "name": "Test new model",
    "control_config": {...},
    "treatment_config": {...}
})
```

## 관련 문서

- **PRD**: `prd_dynamic_taxonomy_rag_v_1_8 최종 (1).md`
- **Master Plan**: `.moai/project/product.md`
- **RAGAS Complete Report**: `RAGAS_EVALUATION_SYSTEM_COMPLETE.md`

## 태그

```
@SPEC:EVAL-001
@IMPL:RAGAS-ENGINE
@IMPL:QUALITY-MONITOR
@IMPL:EXPERIMENT-TRACKER
@IMPL:GOLDEN-DATASET
@IMPL:EVALUATION-API
```

---

**생성일**: 2025-10-07  
**작성자**: @Claude  
**총 문서량**: 2,681줄 (87KB)
