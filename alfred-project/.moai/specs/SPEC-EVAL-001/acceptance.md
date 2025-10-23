# SPEC-EVAL-001 Acceptance Criteria

## 수락 기준 개요

RAGAS 평가 시스템은 이미 프로덕션 환경에서 완전히 구현되어 운영 중입니다. 본 문서는 시스템의 기능적 완성도를 검증하기 위한 상세한 수락 기준과 테스트 시나리오를 정의합니다.

## Given-When-Then 테스트 시나리오

### AC-001: Context Precision 평가

**Given**: 사용자 쿼리와 검색된 컨텍스트 목록이 주어졌을 때
**When**: Context Precision 메트릭을 계산하면
**Then**: 관련 컨텍스트의 비율을 0.0~1.0 사이의 점수로 반환해야 한다

**검증 코드**:
```python
# Test case 1: All relevant contexts
evaluator = RAGASEvaluator()
query = "What is machine learning?"
contexts = [
    "Machine learning is a subset of artificial intelligence...",
    "ML algorithms learn patterns from data...",
    "Common ML techniques include supervised and unsupervised learning..."
]

precision = await evaluator._evaluate_context_precision(query, contexts)
assert precision >= 0.8  # All contexts are relevant

# Test case 2: Mixed relevance
contexts_mixed = [
    "Machine learning is a subset of AI...",  # Relevant
    "The weather is sunny today.",            # Irrelevant
    "ML algorithms learn patterns..."         # Relevant
]

precision_mixed = await evaluator._evaluate_context_precision(query, contexts_mixed)
assert 0.6 <= precision_mixed <= 0.7  # 2/3 ≈ 0.67

# Test case 3: No contexts
precision_empty = await evaluator._evaluate_context_precision(query, [])
assert precision_empty == 0.0
```

**품질 게이트**:
- ✅ Precision ≥ 0.75 (목표)
- ✅ Precision ≥ 0.60 (최소)
- ❌ Precision < 0.60 (실패)

---

### AC-002: Context Recall 평가

**Given**: 쿼리, 응답, 컨텍스트, Ground Truth가 주어졌을 때
**When**: Context Recall 메트릭을 계산하면
**Then**: 필요 정보의 포함 비율을 0.0~1.0 사이의 점수로 반환해야 한다

**검증 시나리오**:

**시나리오 A: Ground Truth 기반 평가**
```python
query = "What are the benefits of RAG?"
ground_truth = "RAG improves accuracy by retrieving relevant information and reduces hallucinations."
contexts = [
    "RAG retrieves relevant information from knowledge base...",     # Covers "retrieves relevant"
    "RAG reduces hallucination by grounding in facts...",           # Covers "reduces hallucinations"
    "RAG improves response accuracy through context..."             # Covers "improves accuracy"
]

recall = await evaluator._evaluate_context_recall(query, "", contexts, ground_truth)
assert recall >= 0.8  # All key information present

# Incomplete coverage
contexts_partial = [
    "RAG retrieves information from knowledge base..."  # Only covers "retrieves"
]

recall_partial = await evaluator._evaluate_context_recall(query, "", contexts_partial, ground_truth)
assert recall_partial < 0.5  # Missing key information
```

**시나리오 B: 응답 기반 평가 (Ground Truth 없음)**
```python
response = "RAG improves accuracy and reduces hallucinations by retrieving relevant context."
contexts = [
    "RAG retrieves relevant information...",
    "RAG reduces hallucination..."
]

recall = await evaluator._evaluate_context_recall(query, response, contexts, None)
assert recall >= 0.7  # Most response claims supported by contexts
```

**품질 게이트**:
- ✅ Recall ≥ 0.70 (목표)
- ✅ Recall ≥ 0.50 (최소)
- ❌ Recall < 0.50 (실패)

---

### AC-003: Faithfulness 평가

**Given**: 생성된 응답과 검색된 컨텍스트가 주어졌을 때
**When**: Faithfulness 메트릭을 계산하면
**Then**: 컨텍스트에 의해 뒷받침되는 주장의 비율을 0.0~1.0 사이의 점수로 반환해야 한다

**검증 시나리오**:

**시나리오 A: 완전히 사실적인 응답**
```python
contexts = [
    "The Eiffel Tower is located in Paris, France.",
    "It was completed in 1889 and stands 330 meters tall."
]

response = "The Eiffel Tower is in Paris and was completed in 1889."

faithfulness = await evaluator._evaluate_faithfulness(response, contexts)
assert faithfulness >= 0.9  # All claims supported
```

**시나리오 B: 부분적으로 사실적인 응답**
```python
response = "The Eiffel Tower is in Paris (✓), was completed in 1889 (✓), and is made of gold (✗)."

faithfulness = await evaluator._evaluate_faithfulness(response, contexts)
assert 0.6 <= faithfulness <= 0.7  # 2/3 claims supported
```

**시나리오 C: 환각(Hallucination) 응답**
```python
response = "The Eiffel Tower is located in London and was built in 1920."

faithfulness = await evaluator._evaluate_faithfulness(response, contexts)
assert faithfulness < 0.3  # Most claims unsupported
```

**품질 게이트** (가장 중요):
- ✅ Faithfulness ≥ 0.85 (목표)
- ⚠️ Faithfulness ≥ 0.70 (경고)
- ❌ Faithfulness < 0.70 (실패)

**알림 발생 조건**:
```python
if metrics.faithfulness < 0.85:
    alert = QualityAlert(
        metric_name="faithfulness",
        current_value=metrics.faithfulness,
        threshold_value=0.85,
        severity="high",  # Critical metric
        message=f"Faithfulness {metrics.faithfulness:.3f} below threshold",
        suggested_actions=[
            "Review response grounding",
            "Check fact verification pipeline",
            "Audit knowledge base quality"
        ]
    )
```

---

### AC-004: Answer Relevancy 평가

**Given**: 사용자 쿼리와 생성된 응답이 주어졌을 때
**When**: Answer Relevancy 메트릭을 계산하면
**Then**: 응답이 쿼리를 얼마나 직접적으로 다루는지를 0.0~1.0 사이의 점수로 반환해야 한다

**검증 시나리오**:

**시나리오 A: 직접적인 응답**
```python
query = "What is the capital of France?"
response = "The capital of France is Paris."

relevancy = await evaluator._evaluate_answer_relevancy(query, response)
assert relevancy >= 0.9  # Directly answers the question
```

**시나리오 B: 부분적으로 관련된 응답**
```python
query = "What is the capital of France?"
response = "France is a beautiful country in Europe. Paris is a major city there."

relevancy = await evaluator._evaluate_answer_relevancy(query, response)
assert 0.5 <= relevancy <= 0.7  # Answers but with extra information
```

**시나리오 C: 무관한 응답**
```python
query = "What is the capital of France?"
response = "Germany is a country in central Europe."

relevancy = await evaluator._evaluate_answer_relevancy(query, response)
assert relevancy < 0.3  # Does not address the query
```

**품질 게이트**:
- ✅ Relevancy ≥ 0.80 (목표)
- ✅ Relevancy ≥ 0.65 (최소)
- ❌ Relevancy < 0.65 (실패)

---

### AC-005: Overall Score 계산

**Given**: 4개 메트릭이 모두 계산되었을 때
**When**: Overall Score를 계산하면
**Then**: 가중 평균을 사용하여 전체 품질 점수를 반환해야 한다

**가중치 구조**:
```python
weights = {
    'faithfulness': 0.3,        # 30% - Most critical
    'answer_relevancy': 0.3,    # 30% - Second most critical
    'context_precision': 0.2,   # 20% - Retrieval quality
    'context_recall': 0.2       # 20% - Completeness
}
```

**검증 시나리오**:
```python
metrics = EvaluationMetrics(
    faithfulness=0.90,
    answer_relevancy=0.85,
    context_precision=0.80,
    context_recall=0.75
)

overall_score = evaluator._calculate_overall_score(metrics)

# Expected: 0.90*0.3 + 0.85*0.3 + 0.80*0.2 + 0.75*0.2 = 0.835
assert 0.83 <= overall_score <= 0.84

# Test with missing metric (should handle gracefully)
metrics_partial = EvaluationMetrics(
    faithfulness=0.90,
    answer_relevancy=0.85,
    context_precision=None,  # Missing
    context_recall=0.75
)

overall_partial = evaluator._calculate_overall_score(metrics_partial)
assert overall_partial > 0  # Should normalize weights
```

**품질 판정**:
```python
if overall_score >= 0.9:
    quality_rating = "excellent"
elif overall_score >= 0.8:
    quality_rating = "good"
elif overall_score >= 0.7:
    quality_rating = "fair"
else:
    quality_rating = "poor"
```

---

### AC-006: Real-time Quality Monitoring

**Given**: 평가가 완료되었을 때
**When**: QualityMonitor에 기록하면
**Then**: 메트릭 버퍼 업데이트, 임계값 확인, 알림 생성(필요 시)이 수행되어야 한다

**검증 시나리오**:

**시나리오 A: 정상 범위 메트릭 (알림 없음)**
```python
evaluation = EvaluationResult(
    evaluation_id="test_001",
    query="Test query",
    metrics=EvaluationMetrics(
        faithfulness=0.90,
        context_precision=0.85,
        context_recall=0.80,
        answer_relevancy=0.88
    ),
    quality_flags=[],
    recommendations=[],
    timestamp=datetime.utcnow()
)

alerts = await quality_monitor.record_evaluation(evaluation)

assert len(alerts) == 0  # No alerts for good metrics
assert len(quality_monitor.metric_buffers['faithfulness']) > 0  # Buffer updated
```

**시나리오 B: 임계값 위반 (알림 발생)**
```python
evaluation_low = EvaluationResult(
    evaluation_id="test_002",
    query="Test query",
    metrics=EvaluationMetrics(
        faithfulness=0.70,  # Below 0.85 threshold
        context_precision=0.60,  # Below 0.75 threshold
        context_recall=0.75,
        answer_relevancy=0.85
    ),
    quality_flags=[],
    recommendations=[],
    timestamp=datetime.utcnow()
)

alerts = await quality_monitor.record_evaluation(evaluation_low)

assert len(alerts) == 2  # Faithfulness + Precision alerts
assert any(alert.metric_name == "faithfulness" for alert in alerts)
assert any(alert.severity == "high" for alert in alerts)
```

**시나리오 C: 알림 쿨다운 (10분)**
```python
# First alert
alerts1 = await quality_monitor.record_evaluation(evaluation_low)
assert len(alerts1) > 0

# Immediate second evaluation (within cooldown)
alerts2 = await quality_monitor.record_evaluation(evaluation_low)
assert len(alerts2) == 0  # Suppressed by cooldown
```

**품질 상태 확인**:
```python
status = await quality_monitor.get_quality_status()

assert "current_metrics" in status
assert "trend_analysis" in status
assert "alert_summary" in status
assert "quality_gates" in status
assert "recommendations" in status
```

---

### AC-007: Quality Dashboard WebSocket

**Given**: 대시보드 클라이언트가 WebSocket에 연결했을 때
**When**: 30초마다 업데이트를 전송하면
**Then**: 최신 품질 메트릭, 트렌드, 알림을 클라이언트가 수신해야 한다

**검증 시나리오**:
```python
async def test_dashboard_realtime_updates():
    async with websocket_client("/evaluation/dashboard/ws") as ws:
        # 1. Initial data upon connection
        initial_data = await ws.receive_json()

        assert "timestamp" in initial_data
        assert "current_metrics" in initial_data
        assert "trends" in initial_data
        assert "active_alerts" in initial_data
        assert "quality_gates" in initial_data

        # 2. Submit new evaluation
        await submit_evaluation(
            query="Test",
            response="Test response",
            contexts=["Test context"]
        )

        # 3. Wait for next update (30 seconds)
        await asyncio.sleep(31)

        # 4. Verify update received
        update_data = await ws.receive_json()

        assert update_data["timestamp"] > initial_data["timestamp"]
        assert "current_metrics" in update_data

        # 5. Verify disconnect handling
        # (Client disconnects)
```

**데이터 구조 검증**:
```python
dashboard_data = {
    "timestamp": "2025-10-07T10:30:00Z",
    "current_metrics": {
        "faithfulness": 0.87,
        "context_precision": 0.82,
        "context_recall": 0.78,
        "answer_relevancy": 0.85,
        "faithfulness_p95": 0.92,
        "faithfulness_trend": 0.02  # Slight upward trend
    },
    "trends": {
        "period_hours": 24,
        "data_points": 24,
        "trends": [
            {"hour": "2025-10-07T10:00:00Z", "faithfulness": 0.88, ...},
            # ...
        ],
        "summary": {
            "faithfulness": {
                "average": 0.87,
                "min": 0.82,
                "max": 0.93,
                "trend": 0.02
            }
        }
    },
    "active_alerts": [
        {
            "alert_id": "context_precision_20251007_103000",
            "metric_name": "context_precision",
            "current_value": 0.68,
            "threshold_value": 0.75,
            "severity": "medium",
            "message": "Context precision 0.680 is below threshold 0.750",
            "timestamp": "2025-10-07T10:30:00Z",
            "suggested_actions": [
                "Improve retrieval ranking",
                "Reduce retrieval count",
                "Optimize query processing"
            ]
        }
    ],
    "quality_gates": {
        "overall_passing": false,
        "gates": {
            "faithfulness_gate": {
                "passing": true,
                "current_value": 0.87,
                "threshold": 0.85,
                "margin": 0.02
            },
            "precision_gate": {
                "passing": false,
                "current_value": 0.68,
                "threshold": 0.75,
                "margin": -0.07
            }
        }
    },
    "recommendations": [
        "Improve retrieval precision by optimizing ranking algorithms",
        "Context coverage is good - maintain current retrieval scope"
    ]
}
```

---

### AC-008: A/B Test Experiment Lifecycle

**Given**: 새로운 RAG 구성을 테스트하려 할 때
**When**: 실험을 생성하고 시작하면
**Then**: 사용자를 그룹에 할당하고 평가 결과를 분리 저장해야 한다

**검증 시나리오**:

**Phase 1: Experiment Creation**
```python
config = ExperimentConfig(
    experiment_id="exp_20251007_001",
    name="Test new embedding model",
    description="Compare text-embedding-3-large vs text-embedding-ada-002",
    control_config={"embedding_model": "text-embedding-ada-002"},
    treatment_config={"embedding_model": "text-embedding-3-large"},
    significance_threshold=0.05,
    minimum_sample_size=100,
    power_threshold=0.8
)

experiment_id = await experiment_tracker.create_experiment(config)

assert experiment_id == "exp_20251007_001"
assert experiment_id in experiment_tracker.active_experiments

# Verify database storage
async with db.session() as session:
    experiment_run = await session.get(ExperimentRun, experiment_id)
    assert experiment_run.status == "planning"
```

**Phase 2: Experiment Start**
```python
success = await experiment_tracker.start_experiment(experiment_id)

assert success == True

# Verify status update
async with db.session() as session:
    experiment_run = await session.get(ExperimentRun, experiment_id)
    assert experiment_run.status == "running"
    assert experiment_run.start_time is not None
```

**Phase 3: User Assignment (Deterministic)**
```python
# User 1: Should be assigned consistently
group1_first = experiment_tracker.assign_user_to_experiment("user_001", experiment_id)
group1_second = experiment_tracker.assign_user_to_experiment("user_001", experiment_id)

assert group1_first == group1_second  # Deterministic

# User 2: Different user might get different group
group2 = experiment_tracker.assign_user_to_experiment("user_002", experiment_id)

# But assignment is consistent for same user
assert group2 in ["control", "treatment"]
```

**Phase 4: Result Recording**
```python
# Record evaluations for both groups
for i in range(60):
    user_id = f"user_{i:03d}"
    group = experiment_tracker.assign_user_to_experiment(user_id, experiment_id)

    # Simulate evaluation result
    evaluation = create_mock_evaluation(
        metrics_boost=0.05 if group == "treatment" else 0.0
    )

    await experiment_tracker.record_experiment_result(
        experiment_id, user_id, evaluation
    )

# Verify data separation
data = experiment_tracker.experiment_data[experiment_id]
assert len(data['control']) > 0
assert len(data['treatment']) > 0
```

**Phase 5: Statistical Analysis**
```python
results = await experiment_tracker.analyze_experiment_results(experiment_id)

assert results is not None
assert results.control_samples >= 50
assert results.treatment_samples >= 50

# Check metric comparisons
assert "faithfulness" in results.metric_comparisons
faithfulness_comp = results.metric_comparisons["faithfulness"]

assert "control_mean" in faithfulness_comp
assert "treatment_mean" in faithfulness_comp
assert "p_value" in faithfulness_comp
assert "effect_size" in faithfulness_comp
assert "is_significant" in faithfulness_comp

# Verify recommendation
assert results.recommendation in [
    "rollout_treatment",
    "rollback_to_control",
    "no_significant_difference",
    "mixed_results_investigate"
]
```

**Phase 6: Experiment Stop**
```python
success = await experiment_tracker.stop_experiment(experiment_id, "manual_stop")

assert success == True

# Verify final state
async with db.session() as session:
    experiment_run = await session.get(ExperimentRun, experiment_id)
    assert experiment_run.status == "completed"
    assert experiment_run.end_time is not None
    assert experiment_run.results is not None
```

---

### AC-009: Canary Deployment Monitoring

**Given**: 새 버전을 카나리 배포할 때
**When**: 품질 저하가 감지되면
**Then**: 자동으로 롤백해야 한다

**검증 시나리오**:

**시나리오 A: 품질 유지 (배포 성공)**
```python
canary_result = await experiment_tracker.monitor_canary_deployment(
    canary_config={"model_version": "v2.0"},
    traffic_percentage=5.0,
    duration_minutes=30  # Reduced for testing
)

assert canary_result["status"] == "monitoring_complete"
assert canary_result["recommendation"] == "proceed_with_rollout"
assert "final_results" in canary_result
```

**시나리오 B: 품질 저하 (자동 롤백)**
```python
# Simulate quality degradation
async def mock_analyze_with_degradation(experiment_id):
    return ExperimentResults(
        experiment_id=experiment_id,
        control_samples=30,
        treatment_samples=30,
        metric_comparisons={
            "faithfulness": {
                "control_mean": 0.85,
                "treatment_mean": 0.70,  # 17.6% degradation
                "p_value": 0.01,
                "effect_size": -0.8,  # Large negative effect
                "is_significant": True,
                "improvement": False
            }
        },
        is_statistically_significant=True,
        confidence_interval={},
        recommendation="rollback_to_control",
        summary="Significant degradation in faithfulness"
    )

# Patch analyzer
experiment_tracker.analyze_experiment_results = mock_analyze_with_degradation

canary_result = await experiment_tracker.monitor_canary_deployment(
    canary_config={"model_version": "v2.0_bad"},
    traffic_percentage=5.0,
    duration_minutes=30
)

assert canary_result["status"] == "rolled_back"
assert canary_result["reason"] == "quality_degradation_detected"
assert canary_result["recommendation"] == "rollback_canary"
```

**품질 저하 감지 기준**:
```python
def _detect_quality_degradation(results: ExperimentResults) -> bool:
    critical_metrics = ['faithfulness', 'answer_relevancy']

    for metric in critical_metrics:
        comparison = results.metric_comparisons.get(metric)
        if not comparison:
            continue

        # Check:
        # 1. Statistically significant
        # 2. Treatment is worse
        # 3. Effect size > 10% degradation threshold
        if (comparison.get('is_significant', False) and
            not comparison.get('improvement', False) and
            abs(comparison.get('effect_size', 0)) > 0.1):
            return True

    return False
```

---

### AC-010: Golden Dataset Generation

**Given**: 데이터베이스에 문서가 존재할 때
**When**: Golden Dataset을 생성하면
**Then**: 질문-답변-컨텍스트 샘플이 자동 생성되어야 한다

**검증 시나리오**:

**시나리오 A: RAGAS 기반 생성**
```python
documents = [
    {
        "doc_id": "doc_001",
        "title": "Machine Learning Basics",
        "text": "Machine learning is a subset of AI that enables systems to learn...",
        "taxonomy_path": ["AI", "ML"]
    },
    # ... more documents
]

generator = GoldenDatasetGenerator()

samples = await generator.generate_from_documents(
    documents=documents,
    testset_size=50,
    query_distribution={
        "simple": 0.5,
        "reasoning": 0.25,
        "multi_context": 0.25
    }
)

assert len(samples) == 50
assert all(isinstance(s, GoldenSample) for s in samples)

# Verify distribution
query_types = [s.query_type for s in samples]
assert query_types.count("simple") >= 20
assert query_types.count("reasoning") >= 10
assert query_types.count("multi_context") >= 10

# Verify sample structure
sample = samples[0]
assert len(sample.question) > 0
assert len(sample.ground_truth_answer) > 0
assert len(sample.retrieved_contexts) > 0
assert sample.query_type in ["simple", "reasoning", "multi_context"]
```

**시나리오 B: Gemini Fallback (RAGAS 실패 시)**
```python
# Simulate RAGAS failure
generator = GoldenDatasetGenerator()
generator._generate_with_ragas = mock_ragas_failure

samples = await generator.generate_from_documents(documents, testset_size=20)

assert len(samples) > 0
assert all(s.metadata.get("generated_by") == "gemini_fallback" for s in samples)
```

**시나리오 C: Dataset Validation**
```python
validation_result = await validate_dataset(samples)

assert validation_result.is_valid == True
assert validation_result.quality_score >= 0.8
assert len(validation_result.validation_errors) == 0

assert "total_entries" in validation_result.statistics
assert "avg_query_length" in validation_result.statistics
assert "avg_answer_length" in validation_result.statistics
```

**시나리오 D: Invalid Dataset Detection**
```python
invalid_samples = [
    DatasetEntry(
        query="",  # Empty query
        ground_truth_answer="Answer",
        expected_contexts=["Context"]
    ),
    DatasetEntry(
        query="Q",  # Too short
        ground_truth_answer="A",  # Too short
        expected_contexts=[]  # No contexts
    )
]

validation_result = await validate_dataset(invalid_samples)

assert validation_result.is_valid == False
assert len(validation_result.validation_errors) >= 3
assert validation_result.quality_score < 0.5
```

---

### AC-011: REST API Integration

**Given**: 클라이언트가 평가 API를 호출할 때
**When**: 유효한 요청을 전송하면
**Then**: 평가 결과를 JSON으로 반환하고 데이터베이스에 저장해야 한다

**검증 시나리오**:

**Endpoint: POST /evaluation/evaluate**
```python
async def test_evaluate_endpoint():
    response = await client.post("/evaluation/evaluate", json={
        "query": "What is machine learning?",
        "response": "Machine learning is a subset of AI that enables systems to learn from data.",
        "retrieved_contexts": [
            "Machine learning is a subset of artificial intelligence...",
            "ML algorithms learn patterns from training data..."
        ],
        "session_id": "session_001",
        "model_version": "v1.8.1"
    })

    assert response.status_code == 200

    result = response.json()
    assert "evaluation_id" in result
    assert "metrics" in result
    assert "overall_score" in result

    # Verify metrics structure
    metrics = result["metrics"]
    assert 0.0 <= metrics["faithfulness"] <= 1.0
    assert 0.0 <= metrics["context_precision"] <= 1.0
    assert 0.0 <= metrics["context_recall"] <= 1.0
    assert 0.0 <= metrics["answer_relevancy"] <= 1.0

    # Verify database storage
    async with db.session() as session:
        log = await session.execute(
            select(SearchLog).where(SearchLog.session_id == "session_001")
        )
        search_log = log.scalar_one()

        assert search_log.query == "What is machine learning?"
        assert search_log.faithfulness is not None
        assert search_log.model_version == "v1.8.1"
```

**Endpoint: POST /evaluation/evaluate/batch**
```python
async def test_batch_evaluate_endpoint():
    response = await client.post("/evaluation/evaluate/batch", json={
        "evaluations": [
            {
                "query": "Query 1",
                "response": "Response 1",
                "retrieved_contexts": ["Context 1"]
            },
            {
                "query": "Query 2",
                "response": "Response 2",
                "retrieved_contexts": ["Context 2"]
            }
        ],
        "async_processing": False
    })

    assert response.status_code == 200

    result = response.json()
    assert result["total_evaluations"] == 2
    assert len(result["results"]) == 2
    assert "summary" in result
```

**Endpoint: GET /evaluation/quality/dashboard**
```python
async def test_quality_dashboard_endpoint():
    response = await client.get("/evaluation/quality/dashboard")

    assert response.status_code == 200

    dashboard = response.json()
    assert "current_status" in dashboard
    assert "recent_trends" in dashboard
    assert "active_alerts" in dashboard
    assert "quality_gates" in dashboard
    assert "recommendations" in dashboard
```

---

## Performance Acceptance Criteria

### PAC-001: Evaluation Latency

**Given**: 단일 평가 요청이 수신되었을 때
**When**: 평가를 수행하면
**Then**: 5초 이내에 완료되어야 한다 (p95)

```python
async def test_evaluation_latency():
    latencies = []

    for _ in range(100):
        start = time.time()

        await evaluator.evaluate_rag_response(
            query="Test query",
            response="Test response",
            retrieved_contexts=["Context 1", "Context 2", "Context 3"]
        )

        duration = time.time() - start
        latencies.append(duration)

    p95_latency = np.percentile(latencies, 95)
    assert p95_latency < 5.0  # 5 seconds

    avg_latency = np.mean(latencies)
    assert avg_latency < 3.0  # 3 seconds average
```

### PAC-002: Concurrent Evaluation Throughput

**Given**: 100개의 동시 평가 요청이 수신되었을 때
**When**: 병렬로 처리하면
**Then**: 모든 요청이 10초 이내에 완료되어야 한다

```python
async def test_concurrent_throughput():
    tasks = [
        evaluator.evaluate_rag_response(
            query=f"Query {i}",
            response=f"Response {i}",
            retrieved_contexts=[f"Context {i}"]
        )
        for i in range(100)
    ]

    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    assert duration < 10.0  # 10 seconds for 100 concurrent
    assert len(results) == 100
    assert all(r.overall_score >= 0 for r in results)
```

### PAC-003: Dashboard WebSocket Load

**Given**: 100개의 클라이언트가 동시에 대시보드에 연결했을 때
**When**: 30초마다 업데이트를 전송하면
**Then**: 모든 클라이언트가 1초 이내에 업데이트를 수신해야 한다

```python
async def test_dashboard_websocket_load():
    clients = []

    # Connect 100 clients
    for i in range(100):
        ws = await websocket_client(f"/evaluation/dashboard/ws?client_id={i}")
        clients.append(ws)

    # Trigger dashboard update
    await trigger_dashboard_update()

    # Measure time to receive update for all clients
    start = time.time()

    updates = await asyncio.gather(*[
        client.receive_json()
        for client in clients
    ])

    duration = time.time() - start

    assert duration < 1.0  # All clients receive within 1 second
    assert len(updates) == 100

    # Cleanup
    for client in clients:
        await client.close()
```

### PAC-004: Database Query Performance

**Given**: 24시간 동안 10,000건의 평가 데이터가 저장되었을 때
**When**: 시간별 집계 쿼리를 실행하면
**Then**: 500ms 이내에 결과를 반환해야 한다

```python
async def test_database_query_performance():
    # Insert 10,000 records
    await populate_test_data(count=10000, hours=24)

    # Query hourly aggregates
    start = time.time()

    trends = await quality_monitor.get_quality_trends(hours=24)

    duration = (time.time() - start) * 1000  # Convert to ms

    assert duration < 500  # 500ms
    assert "trends" in trends
    assert len(trends["trends"]) == 24  # 24 hourly data points
```

---

## Quality Gates Summary

### Critical Thresholds

| Metric | Target | Minimum | Alert | Action |
|--------|--------|---------|-------|--------|
| **Faithfulness** | ≥ 0.90 | ≥ 0.85 | < 0.85 | High severity alert |
| **Context Precision** | ≥ 0.85 | ≥ 0.75 | < 0.75 | Medium severity alert |
| **Context Recall** | ≥ 0.80 | ≥ 0.70 | < 0.70 | Medium severity alert |
| **Answer Relevancy** | ≥ 0.90 | ≥ 0.80 | < 0.80 | Medium severity alert |
| **Overall Score** | ≥ 0.85 | ≥ 0.75 | < 0.75 | Review required |
| **Response Time** | < 3s | < 5s | > 5s | Low severity alert |

### Performance Thresholds

| Metric | Target | Maximum | Alert |
|--------|--------|---------|-------|
| **Evaluation Latency (p95)** | < 3s | < 5s | > 5s |
| **Concurrent Throughput** | 100 req/10s | 100 req/15s | > 15s |
| **Dashboard Update Latency** | < 500ms | < 1s | > 1s |
| **DB Query Performance** | < 200ms | < 500ms | > 500ms |

---

## Definition of Done

시스템이 다음 모든 조건을 만족할 때 완료된 것으로 간주합니다:

### Functional Completeness

- [x] RAGAS 4대 메트릭 모두 구현되어 정확히 작동
- [x] LLM 기반 평가 및 Fallback 메커니즘 모두 동작
- [x] 품질 모니터링 시스템이 실시간으로 알림 생성
- [x] A/B 테스트 전체 라이프사이클 지원
- [x] 카나리 배포 자동 롤백 기능 동작
- [x] Golden Dataset 생성 및 검증 완료
- [x] 대시보드 WebSocket 실시간 업데이트 동작
- [x] REST API 15+ 엔드포인트 모두 동작

### Quality Standards

- [x] 모든 메트릭이 목표 임계값 이상 달성
- [x] 알림 시스템이 정확히 동작 (false positive < 5%)
- [x] 통계 분석이 신뢰 가능 (재현성 > 90%)
- [x] 데이터 저장 및 조회 정확성 100%

### Performance Requirements

- [x] 평가 지연시간 p95 < 5초
- [x] 동시 처리 100+ requests/10초
- [x] 대시보드 업데이트 < 1초
- [x] 데이터베이스 쿼리 < 500ms

### Operational Readiness

- [x] 에러 처리 및 재시도 로직 구현
- [x] 로깅 및 모니터링 통합 (Langfuse, Sentry)
- [x] 문서화 완료 (SPEC, Plan, Acceptance)
- [x] 프로덕션 배포 및 검증 완료

### Test Coverage

- [x] 단위 테스트: 핵심 로직 커버리지 > 80%
- [x] 통합 테스트: End-to-end 플로우 검증
- [x] 성능 테스트: 부하 및 동시성 검증
- [x] 회귀 테스트: 기존 기능 영향 없음

---

**문서 버전**: 0.1.0
**최종 업데이트**: 2025-10-07
**작성자**: @Claude
**검토자**: TBD
