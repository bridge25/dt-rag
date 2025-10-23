---
id: SOFTQ-001
version: 0.2.0
status: completed
created: 2025-10-09
updated: 2025-10-22
author: @spec-builder
priority: high
category: ml
labels:
  - reinforcement-learning
  - soft-q-learning
  - bandit
  - reverse-engineered
scope:
  packages:
    - apps/orchestration/src/bandit
  files:
    - apps/orchestration/src/bandit/q_learning.py (104 LOC)
    - apps/orchestration/src/bandit/replay_buffer.py (73 LOC)
    - apps/orchestration/src/bandit/policy.py
    - apps/orchestration/src/bandit/state_encoder.py
---

# SPEC-SOFTQ-001: Soft Q-learning Bandit System for Adaptive Strategy Selection

## HISTORY

### v0.2.0 (2025-10-22)
- **REVERSE_ENGINEERING_COMPLETED**: Git 커밋 fc89415, d17ff55에서 실제 구현 확인
- **IMPLEMENTATION**:
  - Soft Q-learning 알고리즘 완전 구현
  - Experience Replay Buffer 통합 (SPEC-REPLAY-001)
  - Batch update 지원
  - Q-table 기반 value storage
  - Temperature-based exploration
- **FILES_RESTORED**: Git checkout으로 복원 완료
- **STATUS_CHANGE**: draft → completed

### v0.1.0 (2025-10-09)
- **INITIAL**: Soft Q-learning Bandit SPEC 초안 작성
- **AUTHOR**: @spec-builder

---

## 0. Version History

- **ID**: SPEC-SOFTQ-001
- **Version**: 0.2.0
- **Status**: COMPLETED
- **Created**: 2025-10-09
- **Updated**: 2025-10-22
- **Author**: @spec-builder

## 1. Overview

### Purpose
Implement an adaptive Soft Q-learning Bandit strategy for dynamic selection of Retrieval and Compose actions in the DT-RAG system, enabling intelligent, context-aware pipeline optimization.

### Key Performance Indicators (KPIs)
- **Latency**: < 50ms for Q-learning action selection
- **Adaptability**: 70% improvement in strategy selection confidence
- **Exploration**: Soft Q-learning with temperature τ=0.5 for balanced exploration

## 2. State Space Definition

### Features (4)
1. **Complexity Score**
   - Range: 0-1
   - Representation: Input query complexity
   - Extraction: NLP complexity metrics

2. **Intent Alignment**
   - Range: 0-1
   - Representation: Semantic alignment with task
   - Extraction: Cosine similarity of embeddings

3. **BM25 Match Count**
   - Range: 0-10
   - Representation: Keyword match frequency
   - Extraction: BM25 retrieval match statistics

4. **Vector Similarity Count**
   - Range: 0-10
   - Representation: Semantic match frequency
   - Extraction: Vector search match statistics

### State Calculation
- Total States: 4^2 = 108 discrete states
- Quantization: Divide each feature into 3 bins (Low, Medium, High)
- State Encoding: Combination of feature bin values

## 3. Action Space

### Retrieval Strategies (3)
1. **BM25 Retrieval**
   - Focus: Keyword-based, precise matching
   - Best for: Factual, structured queries

2. **Vector Retrieval**
   - Focus: Semantic similarity
   - Best for: Conceptual, abstract queries

3. **Hybrid Retrieval**
   - Focus: Combined keyword and semantic
   - Best for: Complex, nuanced queries

### Compose Strategies (2)
1. **Extractive Composition**
   - Focus: Direct text extraction
   - Best for: Factual, summarization tasks

2. **Generative Composition**
   - Focus: AI-generated synthesis
   - Best for: Creative, analytical tasks

## 4. Reward Function

### Reward Components
- **Confidence** (70%): Quality of retrieved/composed content
  - Metrics: Relevance score, semantic similarity
  - Calculation: Weighted score from retrieval and composition

- **Latency** (30%): System response time
  - Metrics: Total pipeline execution time
  - Calculation: Inverse of execution duration

### Reward Equation
```python
R = 0.7 * confidence_score + 0.3 * (1 - normalized_latency)
```

## 5. Soft Q-learning Parameters

### Hyperparameters
- **Learning Rate (α)**: 0.2
- **Discount Factor (γ)**: 0.95
- **Temperature (τ)**: 0.5 (Exploration-Exploitation Balance)

### Update Rule
```python
Q(s, a) ← Q(s, a) + α * [R + γ * max(Q(s', a')) - Q(s, a)]
```

## 6. Storage & Persistence

### Q-table Management
- **Storage**: PostgreSQL with async updates
- **Serialization**: JSON-based state representation
- **Concurrency**: Non-blocking atomic updates

### Versioning
- Automatic versioning of Q-table snapshots
- Periodic model drift detection
- Automatic retraining triggers

## 7. Integration Points

### LangGraph Integration
- Inject Q-learning policy into steps:
  1. Query preprocessing
  2. Retrieval strategy selection
  3. Composition strategy selection
  4. Response generation
  5. Feedback collection

## 8. Monitoring & Observability

### Metrics Tracking
- Action selection probability
- Reward distribution
- Exploration vs. exploitation ratio
- Model convergence indicators

### Logging
- Structured logging of state transitions
- Performance impact tracking
- Anomaly detection

## 9. Error Handling & Fallbacks

### Failure Modes
1. **Cold Start**: Default to hybrid strategies
2. **Model Drift**: Automatic retraining
3. **Performance Degradation**: Fallback to static policies

## 10. Ethical Considerations

### Bias Mitigation
- Regular bias audits
- Diverse training data
- Explainable AI principles

### Privacy
- No PII storage in Q-table
- Aggregated, anonymized learning

## 11. Future Extensions

- Multi-agent Q-learning
- Cross-pipeline strategy transfer
- Reinforcement learning ensemble

## References

- Haarnoja et al. (2018). Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning
- Sutton & Barto (2018). Reinforcement Learning: An Introduction
- Silver et al. (2016). Mastering the Game of Go with Deep Neural Networks
