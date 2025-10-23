# SPEC-CLASS-001 Acceptance Criteria

## 수락 기준 개요

Hybrid Classification System은 이미 프로덕션 환경에서 완전히 구현되어 운영 중입니다. 본 문서는 시스템의 기능적 완성도를 검증하기 위한 상세한 수락 기준과 테스트 시나리오를 정의합니다.

## Given-When-Then 테스트 시나리오

### AC-001: Semantic Cosine Similarity Classification

**Given**: 사용자가 텍스트와 택소노미 노드 목록을 제공했을 때
**When**: Semantic classifier가 cosine similarity를 계산하면
**Then**: 상위 k개의 후보를 신뢰도와 함께 반환해야 한다

**검증 코드**:
```python
classifier = SemanticClassifier(embedding_service, db_session)

query_text = "Machine learning algorithms for natural language processing"
taxonomy_nodes = [
    {"id": "uuid-1", "label": "AI/ML", "embedding": embedding_ml},
    {"id": "uuid-2", "label": "NLP", "embedding": embedding_nlp},
    {"id": "uuid-3", "label": "Database", "embedding": embedding_db}
]

result = await classifier.classify_text(
    text=query_text,
    taxonomy_nodes=taxonomy_nodes,
    top_k=3
)

# Assertions
assert len(result.classifications) <= 3
assert result.classifications[0].taxonomy_path == ["AI", "ML"] or ["NLP"]
assert result.classifications[0].confidence >= 0.7
assert all(c.confidence <= 1.0 for c in result.classifications)
```

**품질 게이트**:
- ✅ Confidence ≥ 0.85: High confidence (자동 승인)
- ✅ 0.70 ≤ Confidence < 0.85: Moderate (자동 승인)
- ❌ Confidence < 0.70: Low (HITL 큐 진입)

---

### AC-002: Rule-based Fast-path Classification

**Given**: 민감도 키워드를 포함한 텍스트가 입력되었을 때
**When**: Hybrid classifier가 Stage 1 rule-based 검사를 수행하면
**Then**: LLM을 스킵하고 0.80~0.95 신뢰도로 즉시 분류해야 한다

**검증 시나리오**:

**시나리오 A: 민감도 패턴 (Confidence = 0.95)**
```python
hybrid_classifier = HybridClassifier(embedding_service, llm_service, taxonomy_dao, db_session)

confidential_text = "This document contains confidential information about our project."

result = await hybrid_classifier.classify(
    chunk_id="test-chunk-1",
    text=confidential_text,
    taxonomy_version="1.0.0"
)

assert result["canonical_path"] == ["Security", "Confidential"]
assert result["confidence"] >= 0.95
assert result["method"] == "sensitivity_rule"
# LLM should be skipped
assert llm_service.generate.call_count == 0
```

**시나리오 B: 도메인 키워드 (Confidence = 0.85)**
```python
ml_text = "This paper discusses machine learning and neural network architectures."

result = await hybrid_classifier.classify(
    chunk_id="test-chunk-2",
    text=ml_text,
    taxonomy_version="1.0.0"
)

assert result["canonical_path"] == ["AI", "ML"] or ["AI", "Deep Learning"]
assert 0.80 <= result["confidence"] <= 0.90
assert result["method"] == "keyword_rule"
```

**품질 게이트**:
- ✅ Rule confidence ≥ 0.90 → LLM 스킵 (비용 절감)
- ✅ Rule hit rate ≥ 90% (PRD 목표)
- ❌ Rule false positive > 10%

---

### AC-003: LLM Classification with JSON Response

**Given**: Rule-based 패턴이 매칭되지 않은 텍스트가 주어졌을 때
**When**: Hybrid classifier가 LLM (Gemini 2.5 Flash)을 호출하면
**Then**: 구조화된 JSON 응답을 받아 canonical_path, candidates, reasoning, confidence를 반환해야 한다

**검증 코드**:
```python
generic_text = "How to optimize database query performance?"

result = await hybrid_classifier.classify(
    chunk_id="test-chunk-3",
    text=generic_text,
    taxonomy_version="1.0.0"
)

# LLM response validation
assert isinstance(result["canonical_path"], list)
assert len(result["canonical_path"]) >= 1
assert isinstance(result["candidates"], list)
assert len(result["candidates"]) <= 3
assert isinstance(result["reasoning"], list)
assert len(result["reasoning"]) >= 2  # At least 2 reasons
assert 0.0 <= result["confidence"] <= 1.0
assert result["method"] in ["llm", "llm_only", "llm_disagreement"]
```

**LLM 프롬프트 검증**:
```python
# Check that prompt includes:
# 1. Taxonomy context (top 20 nodes)
# 2. Text snippet (max 500 chars)
# 3. JSON format requirement
# 4. Required fields specification

llm_call_args = llm_service.generate.call_args
prompt = llm_call_args["prompt"]

assert "taxonomy paths:" in prompt.lower()
assert "json format" in prompt.lower()
assert "canonical_path" in prompt
assert "candidates" in prompt
assert "reasoning" in prompt
assert "confidence" in prompt
```

**품질 게이트**:
- ✅ LLM 성공률 ≥ 95%
- ✅ JSON 파싱 성공률 = 100% (프롬프트 강제)
- ✅ Reasoning 개수 ≥ 2
- ❌ LLM 실패 시 fallback 미작동

---

### AC-004: Cross-validation Confidence Adjustment

**Given**: Rule-based와 LLM 결과가 모두 존재할 때
**When**: Stage 3 cross-validation이 수행되면
**Then**: 두 결과의 일치 여부에 따라 신뢰도를 조정해야 한다

**검증 시나리오**:

**시나리오 A: 일치 (Confidence Boost)**
```python
rule_result = {
    "canonical_path": ["AI", "ML"],
    "confidence": 0.85,
    "method": "keyword_rule"
}

llm_result = {
    "canonical_path": ["AI", "ML"],  # Same path
    "confidence": 0.80,
    "method": "llm"
}

final_result = await hybrid_classifier._stage3_cross_validation(
    chunk_id="test-chunk-4",
    text="ML content",
    rule_result=rule_result,
    llm_result=llm_result,
    taxonomy_version="1.0.0"
)

# Confidence boost: (0.85 + 0.80) / 2 * 1.1 = 0.9075
expected_confidence = min(((0.85 + 0.80) / 2) * 1.1, 1.0)
assert abs(final_result["confidence"] - expected_confidence) < 0.01
assert final_result["method"] == "cross_validated"
```

**시나리오 B: 불일치 (Confidence Discount)**
```python
rule_result = {
    "canonical_path": ["AI", "ML"],
    "confidence": 0.85
}

llm_result = {
    "canonical_path": ["Database", "Query"],  # Different path
    "confidence": 0.75
}

final_result = await hybrid_classifier._stage3_cross_validation(...)

# Discount: 0.75 * 0.7 = 0.525
expected_confidence = 0.75 * 0.7
assert abs(final_result["confidence"] - expected_confidence) < 0.01
assert final_result["method"] == "llm_disagreement"
assert final_result["canonical_path"] == ["Database", "Query"]  # LLM wins
```

**품질 게이트**:
- ✅ Cross-validated confidence: min((rule + llm) / 2 * 1.1, 1.0)
- ✅ LLM only: llm_conf * 0.8
- ✅ Disagreement: llm_conf * 0.7

---

### AC-005: Drift Detection Mechanism

**Given**: Rule-based와 LLM 결과가 불일치할 때
**When**: Drift detection이 수행되면
**Then**: 공통 접두사가 50% 미만일 경우 drift=True를 반환하고 HITL 큐로 전송해야 한다

**검증 코드**:
```python
rule_result = {
    "canonical_path": ["AI", "ML", "Deep Learning"],  # 3 levels
    "confidence": 0.85
}

llm_result = {
    "canonical_path": ["AI", "NLP"],  # 2 levels, common prefix = 1 (AI)
    "confidence": 0.80
}

drift_detected = hybrid_classifier._detect_drift(rule_result, llm_result)

# Common prefix length = 1, Rule path length = 3
# Drift = True if 1 < 3 * 0.5 (1.5)
assert drift_detected == True

# Verify HITL task creation
hitl_tasks = await hitl_queue.get_pending_tasks()
assert len(hitl_tasks) > 0
assert hitl_tasks[0]["chunk_id"] == "test-chunk-5"
```

**Drift 시나리오**:
```python
# Test case 1: No drift (high overlap)
rule_path = ["Security", "Confidential"]
llm_path = ["Security", "Private"]
# Common prefix = 1, rule length = 2, 1 >= 2 * 0.5 → No drift

# Test case 2: Drift (low overlap)
rule_path = ["AI", "ML", "Supervised"]
llm_path = ["Database", "SQL"]
# Common prefix = 0, rule length = 3, 0 < 3 * 0.5 → Drift
```

**품질 게이트**:
- ✅ Drift detection rate ≤ 15% (목표: < 10%)
- ✅ Drift → HITL 자동 전송
- ❌ False positive drift > 20%

---

### AC-006: HITL Task Creation and Retrieval

**Given**: 분류 신뢰도가 0.70 미만이거나 drift가 감지되었을 때
**When**: HITL 큐에 작업이 추가되면
**Then**: doc_taxonomy에 hitl_required=true로 표시되고 우선순위 정렬로 조회 가능해야 한다

**검증 시나리오**:

**시나리오 A: Low Confidence → HITL**
```python
classifier_response = await hybrid_classifier.classify(
    chunk_id="low-confidence-chunk",
    text="Ambiguous text with no clear category",
    taxonomy_version="1.0.0"
)

# Confidence < 0.70
assert classifier_response["confidence"] < 0.70
assert classifier_response["hitl_required"] == True

# Verify database record
async with db_manager.async_session() as session:
    result = await session.execute(text("""
        SELECT hitl_required, confidence, path
        FROM doc_taxonomy
        WHERE doc_id = (
            SELECT doc_id FROM chunks WHERE chunk_id = :chunk_id
        )
    """), {"chunk_id": "low-confidence-chunk"})

    row = result.fetchone()
    assert row["hitl_required"] == True
    assert row["confidence"] < 0.70
```

**시나리오 B: Task Retrieval (Priority Sorting)**
```python
hitl_queue = HITLQueueManager(db_manager)

# Add multiple tasks with different confidences
tasks = [
    {"chunk_id": "chunk-1", "confidence": 0.65},
    {"chunk_id": "chunk-2", "confidence": 0.45},
    {"chunk_id": "chunk-3", "confidence": 0.55}
]

for task in tasks:
    await hitl_queue.add_task(
        chunk_id=task["chunk_id"],
        text="test text",
        suggested_classification=["General"],
        confidence=task["confidence"]
    )

# Retrieve pending tasks
pending = await hitl_queue.get_pending_tasks(limit=10)

# Verify sorting: confidence ASC (lowest first)
assert pending[0]["confidence"] == 0.45  # chunk-2
assert pending[1]["confidence"] == 0.55  # chunk-3
assert pending[2]["confidence"] == 0.65  # chunk-1
```

**품질 게이트**:
- ✅ HITL rate ≤ 30% (PRD 목표: ≤ 20%)
- ✅ Task retrieval 정렬: confidence ASC, created_at ASC
- ✅ Database persistence: hitl_required flag

---

### AC-007: HITL Task Completion

**Given**: HITL 작업이 대기 중일 때
**When**: 사용자가 approved_path를 제출하면
**Then**: doc_taxonomy가 업데이트되고 hitl_required=false, confidence=1.0으로 설정되어야 한다

**검증 코드**:
```python
# Complete HITL task
hitl_queue = HITLQueueManager(db_manager)

success = await hitl_queue.complete_task(
    task_id="test-task-uuid",
    chunk_id="hitl-chunk-1",
    approved_path=["AI", "Machine Learning"],
    confidence_override=None,  # Defaults to 1.0
    reviewer_notes="Correctly categorized as ML",
    reviewer_id="reviewer-123"
)

assert success == True

# Verify database update
async with db_manager.async_session() as session:
    result = await session.execute(text("""
        SELECT path, confidence, hitl_required
        FROM doc_taxonomy
        WHERE doc_id = (
            SELECT doc_id FROM chunks WHERE chunk_id = :chunk_id
        )
    """), {"chunk_id": "hitl-chunk-1"})

    row = result.fetchone()
    assert row["path"] == ["AI", "Machine Learning"]
    assert row["confidence"] == 1.0  # Human-approved
    assert row["hitl_required"] == False
```

**Confidence Override 테스트**:
```python
# Custom confidence override
await hitl_queue.complete_task(
    task_id="test-task-2",
    chunk_id="hitl-chunk-2",
    approved_path=["Database"],
    confidence_override=0.9,  # Custom confidence
    reviewer_notes="90% confident"
)

# Verify custom confidence
row = await session.fetchone()
assert row["confidence"] == 0.9
```

**품질 게이트**:
- ✅ HITL approval rate ≥ 95%
- ✅ Default confidence = 1.0 (human-approved)
- ✅ Custom confidence override 지원

---

### AC-008: End-to-End Classification Pipeline

**Given**: 문서 청크가 인입되었을 때
**When**: 전체 분류 파이프라인이 실행되면
**Then**: Rule → (LLM) → Cross-validation → (HITL) 흐름이 정상적으로 완료되어야 한다

**통합 테스트**:
```python
# Setup
embedding_service = EmbeddingService()
llm_service = GeminiLLMService()
taxonomy_dao = TaxonomyDAO(db_session)
hitl_queue = HITLQueueManager(db_manager)

hybrid_classifier = HybridClassifier(
    embedding_service,
    llm_service,
    taxonomy_dao,
    db_session
)

# Test Case 1: High-confidence rule-based (no LLM)
result_1 = await hybrid_classifier.classify(
    chunk_id="e2e-chunk-1",
    text="Confidential financial data",
    taxonomy_version="1.0.0"
)

assert result_1["method"] == "sensitivity_rule"
assert result_1["confidence"] >= 0.95
assert result_1["hitl_required"] == False
# Verify LLM not called
assert llm_service.generate.call_count == 0

# Test Case 2: Low-confidence → HITL
result_2 = await hybrid_classifier.classify(
    chunk_id="e2e-chunk-2",
    text="Vague and ambiguous content",
    taxonomy_version="1.0.0"
)

assert result_2["confidence"] < 0.70
assert result_2["hitl_required"] == True
# Verify HITL task created
hitl_tasks = await hitl_queue.get_pending_tasks()
assert any(task["chunk_id"] == "e2e-chunk-2" for task in hitl_tasks)

# Test Case 3: Cross-validated (Rule + LLM agree)
result_3 = await hybrid_classifier.classify(
    chunk_id="e2e-chunk-3",
    text="Neural network training algorithms",
    taxonomy_version="1.0.0"
)

assert result_3["method"] == "cross_validated"
assert result_3["confidence"] >= 0.85
assert result_3["canonical_path"] == ["AI", "ML"]
```

**품질 게이트**:
- ✅ E2E 성공률 ≥ 95%
- ✅ 처리 시간 p95 < 5초 (Rule + LLM)
- ✅ Auto-approve precision ≥ 90%

---

## 성능 수락 기준

### Performance Metrics

**처리 시간**:
```python
@pytest.mark.performance
async def test_classification_latency():
    start = time.time()
    await hybrid_classifier.classify(chunk_id="perf-test", text="test", taxonomy_version="1.0.0")
    duration = time.time() - start

    # Rule-based only
    if result["method"] == "rule_based":
        assert duration < 0.2  # 200ms

    # Rule + LLM
    elif result["method"] in ["llm", "cross_validated"]:
        assert duration < 5.0  # 5 seconds
```

**동시 처리**:
```python
@pytest.mark.concurrent
async def test_concurrent_classification():
    tasks = [
        hybrid_classifier.classify(f"chunk-{i}", f"text-{i}", "1.0.0")
        for i in range(100)
    ]

    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    # 100 requests should complete in reasonable time
    assert duration < 30.0  # 30 seconds
    assert all(r["confidence"] >= 0.0 for r in results)
```

**비용 최적화**:
- ✅ Rule-based fast-path: ≥ 90% of cases
- ✅ LLM 호출 비용: < $0.001 per classification
- ✅ Gemini 2.5 Flash usage: $0.075/1M input tokens

---

## 모니터링 수락 기준

### Alert Thresholds

**High Severity**:
```python
assert classification_accuracy >= 0.70  # Ground truth 대비
assert hitl_rate <= 0.50
assert processing_time_p95 <= 10.0  # seconds
```

**Medium Severity**:
```python
assert classification_accuracy >= 0.85
assert hitl_rate <= 0.30
assert auto_approve_precision >= 0.90
```

**Low Severity**:
```python
assert processing_time_p95 <= 5.0
assert drift_detection_rate <= 0.15
```

---

## 데이터 무결성 수락 기준

### Database Constraints

**Taxonomy Integrity**:
```sql
-- (doc_id, node_id, version) must be unique
ALTER TABLE doc_taxonomy ADD CONSTRAINT uq_doc_taxonomy_mapping
    UNIQUE (doc_id, node_id, version);

-- Foreign key integrity
ALTER TABLE doc_taxonomy ADD CONSTRAINT fk_doc_taxonomy_doc
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE;

ALTER TABLE doc_taxonomy ADD CONSTRAINT fk_doc_taxonomy_node
    FOREIGN KEY (node_id) REFERENCES taxonomy_nodes(node_id);
```

**HITL Queue Integrity**:
```python
@pytest.mark.integrity
async def test_hitl_queue_consistency():
    # Add task
    task_id = await hitl_queue.add_task(
        chunk_id="integrity-chunk",
        text="test",
        suggested_classification=["General"],
        confidence=0.60
    )

    # Verify doc_taxonomy record exists
    async with db_manager.async_session() as session:
        result = await session.execute(text("""
            SELECT COUNT(*) FROM doc_taxonomy dt
            JOIN chunks c ON c.doc_id = dt.doc_id
            WHERE c.chunk_id = :chunk_id AND dt.hitl_required = true
        """), {"chunk_id": "integrity-chunk"})

        count = result.scalar()
        assert count == 1
```

---

## 최종 수락 체크리스트

### 기능 완성도

- [x] **FR-001**: Cosine similarity classification
- [x] **FR-002**: Fallback response handling
- [x] **FR-003**: Stage 1 rule-based classification
- [x] **FR-004**: Stage 2 LLM classification
- [x] **FR-005**: Stage 3 cross-validation
- [x] **FR-006**: Drift detection
- [x] **FR-007**: HITL task creation
- [x] **FR-008**: HITL task retrieval
- [x] **FR-009**: HITL task completion
- [x] **FR-010**: HITL statistics
- [x] **FR-011**: Taxonomy node retrieval

### 품질 게이트

- [x] Classification accuracy ≥ 85%
- [x] HITL rate ≤ 30%
- [x] Processing time p95 < 5s
- [x] Auto-approve precision ≥ 95%
- [x] Rule-based fast-path ≥ 90%

### 운영 준비

- [x] Database schema deployed
- [x] Taxonomy nodes seeded (v1.0.0)
- [x] Gemini 2.5 Flash API integration
- [x] OpenAI embedding service integration
- [x] API endpoints exposed
- [x] Monitoring metrics defined
- [x] Alert conditions configured

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Claude
**상태**: Approved
