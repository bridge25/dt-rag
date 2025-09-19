# RAG Evaluation Framework

Comprehensive evaluation framework for the Dynamic Taxonomy RAG v1.8.1 system, implementing RAGAS metrics, golden dataset management, A/B testing, and automated quality assurance.

## 🎯 Overview

This evaluation framework provides end-to-end evaluation capabilities for RAG systems with a focus on:

- **RAGAS Integration**: Faithfulness ≥ 0.85, Answer Relevancy, Context Precision/Recall
- **Golden Dataset Management**: High-quality evaluation datasets with 95%+ quality
- **A/B Testing**: Statistical significance validation (p < 0.05) for system improvements
- **Automated Quality Gates**: Continuous monitoring with automated rollback triggers
- **Comprehensive Reporting**: Detailed analysis and actionable recommendations

## 🏗️ Architecture

```
dt-rag/apps/evaluation/
├── core/                    # Core evaluation components
│   ├── ragas_engine.py     # RAGAS evaluation implementation
│   ├── golden_dataset.py   # Dataset management and validation
│   └── ab_testing.py       # A/B testing framework
├── orchestrator/           # Evaluation orchestration
│   └── evaluation_orchestrator.py
├── api/                    # REST API interface
│   └── evaluation_api.py
├── scripts/               # CLI tools and utilities
│   └── run_evaluation.py
└── tests/                 # Test suite
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install RAGAS
pip install ragas

# Optional: Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Basic Usage

#### CLI Interface

```bash
# Create a golden dataset
python scripts/run_evaluation.py dataset create "Test Dataset" "Description" data.json

# Run evaluation
python scripts/run_evaluation.py evaluate run "My Evaluation" dataset_id --immediate

# Start API server
python scripts/run_evaluation.py server --port 8002
```

#### API Interface

```bash
# Start the evaluation API
python apps/evaluation/api/evaluation_api.py

# API documentation available at http://localhost:8002/docs
```

#### Python API

```python
from evaluation.core.ragas_engine import RAGASEvaluationEngine
from evaluation.core.golden_dataset import GoldenDatasetManager

# Create evaluation engine
engine = RAGASEvaluationEngine()

# Run evaluation
result = await engine.evaluate_rag_system(
    test_queries=queries,
    rag_responses=responses,
    ground_truths=expected_answers
)

print(f"Faithfulness: {result.metrics['faithfulness']:.3f}")
print(f"Quality gates passed: {result.quality_gates_passed}")
```

## 📊 Core Components

### RAGAS Engine

Implements comprehensive RAGAS evaluation metrics:

```python
from evaluation.core.ragas_engine import RAGASEvaluationEngine, RAGResponse

engine = RAGASEvaluationEngine()

# Evaluate RAG responses
responses = [
    RAGResponse(
        answer="RAG combines retrieval with generation...",
        retrieved_docs=[{"text": "context", "score": 0.8}],
        confidence=0.9
    )
]

result = await engine.evaluate_rag_system(
    test_queries=["What is RAG?"],
    rag_responses=responses,
    ground_truths=["RAG stands for..."]
)

# Metrics: faithfulness, answer_relevancy, context_precision, context_recall
print(result.metrics)
```

### Golden Dataset Management

High-quality dataset creation and validation:

```python
from evaluation.core.golden_dataset import GoldenDatasetManager

manager = GoldenDatasetManager()

# Create dataset
dataset = await manager.create_golden_dataset(
    name="Evaluation Dataset",
    description="High-quality evaluation data",
    raw_data=[
        {
            "query": "What is machine learning?",
            "expected_answer": "ML is a subset of AI...",
            "expected_contexts": ["ML context"],
            "taxonomy_path": ["AI", "ML"],
            "difficulty_level": "medium"
        }
    ]
)

# Validate quality
validation = await manager.validate_dataset(dataset)
print(f"Quality score: {validation.quality_score:.3f}")
```

### A/B Testing Framework

Statistical testing for system improvements:

```python
from evaluation.core.ab_testing import ABTestingFramework, ExperimentMetric, ExperimentVariant

framework = ABTestingFramework()

# Design experiment
experiment = await framework.design_experiment(
    name="RAG System Comparison",
    description="Compare retrieval strategies",
    primary_metric=ExperimentMetric(
        name="faithfulness",
        type=MetricType.CONTINUOUS,
        description="RAGAS faithfulness score",
        minimum_detectable_effect=0.05
    ),
    variants=[
        ExperimentVariant(
            id="control",
            name="Current System",
            traffic_allocation=0.5
        ),
        ExperimentVariant(
            id="treatment",
            name="Improved System",
            traffic_allocation=0.5
        )
    ]
)

# Record observations and analyze
await framework.record_observation(
    experiment_id=experiment.experiment_id,
    variant_id="control",
    randomization_unit_id="user_123",
    metric_values={"faithfulness": 0.85}
)

result = await framework.analyze_experiment(experiment.experiment_id)
print(f"Winning variant: {result.winning_variant}")
```

### Evaluation Orchestrator

Automated evaluation workflows:

```python
from evaluation.orchestrator.evaluation_orchestrator import EvaluationOrchestrator

orchestrator = EvaluationOrchestrator()
await orchestrator.start_scheduler()

# Schedule evaluation
job_id = await orchestrator.schedule_evaluation(
    name="Nightly Evaluation",
    description="Automated quality check",
    golden_dataset_id="dataset_123"
)

# Get results
status = await orchestrator.get_job_status(job_id)
print(f"Status: {status['status']}")
```

## 🛠️ API Reference

### REST API Endpoints

#### Evaluation
- `POST /evaluate` - Schedule evaluation
- `POST /evaluate/immediate` - Run immediate evaluation
- `GET /evaluate/{job_id}` - Get evaluation results
- `GET /evaluate` - List evaluations

#### Golden Datasets
- `POST /datasets` - Create dataset
- `GET /datasets` - List datasets
- `GET /datasets/{id}` - Get dataset details
- `POST /datasets/{id}/validate` - Validate dataset
- `POST /datasets/{id}/split` - Split dataset

#### A/B Testing
- `POST /experiments` - Create experiment
- `POST /experiments/{id}/observations` - Record observation
- `POST /experiments/{id}/analyze` - Analyze results
- `GET /experiments/{id}/status` - Get experiment status

#### Monitoring
- `GET /health` - Health check
- `GET /status` - System status
- `GET /metrics` - Performance metrics

### Example API Usage

```bash
# Create golden dataset
curl -X POST "http://localhost:8002/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Dataset",
    "description": "Evaluation dataset",
    "data_points": [
      {
        "query": "What is RAG?",
        "expected_answer": "RAG is...",
        "taxonomy_path": ["AI", "RAG"],
        "difficulty_level": "easy"
      }
    ]
  }'

# Run evaluation
curl -X POST "http://localhost:8002/evaluate/immediate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Evaluation",
    "description": "Quick test",
    "golden_dataset_id": "dataset_123"
  }'

# Get system status
curl "http://localhost:8002/status"
```

## 📈 Quality Gates

The framework enforces quality gates to ensure system reliability:

### Default Thresholds
- **Faithfulness**: ≥ 0.85 (Critical)
- **Answer Relevancy**: ≥ 0.80 (Critical)
- **Context Precision**: ≥ 0.75 (Warning)
- **Context Recall**: ≥ 0.80 (Warning)
- **Classification Accuracy**: ≥ 0.90 (Critical)

### Quality Gate Configuration

```python
from evaluation.orchestrator.evaluation_orchestrator import QualityGate

# Custom quality gates
gates = [
    QualityGate(
        name="High Faithfulness",
        metric_name="faithfulness",
        threshold=0.90,
        operator="gte",
        severity="critical"
    )
]

orchestrator.quality_gates = gates
```

## 🔬 Advanced Features

### Continuous Evaluation

Set up automated monitoring:

```python
# Setup continuous evaluation
schedule_id = await orchestrator.setup_continuous_evaluation(
    golden_dataset_id="production_dataset",
    schedule_interval_hours=24,
    performance_thresholds={
        "faithfulness": 0.85,
        "answer_relevancy": 0.80
    }
)
```

### Custom Metrics

Extend with domain-specific metrics:

```python
class CustomRAGASEngine(RAGASEvaluationEngine):
    async def evaluate_custom_metric(self, responses):
        # Implement custom evaluation logic
        return custom_scores

engine = CustomRAGASEngine()
```

### Performance Monitoring

Track evaluation performance:

```python
# Get performance metrics
metrics = orchestrator.get_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average evaluation time: {metrics['average_evaluation_time_seconds']:.1f}s")
```

## 📝 Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/dt_rag

# OpenAI API (for embeddings and evaluation)
OPENAI_API_KEY=***MASKED***

# Evaluation settings
EVALUATION_STORAGE_PATH=./evaluation_results
GOLDEN_DATASET_PATH=./golden_datasets
MAX_CONCURRENT_EVALUATIONS=3
```

### Configuration File

```yaml
# evaluation_config.yaml
ragas_engine:
  use_openai: true
  metrics:
    faithfulness:
      threshold: 0.85
      weight: 0.3
    answer_relevancy:
      threshold: 0.80
      weight: 0.25

golden_dataset:
  quality_thresholds:
    min_completeness: 0.95
    min_consistency: 0.90
    min_diversity: 0.70

ab_testing:
  default_significance_level: 0.05
  default_statistical_power: 0.80
  multiple_testing_correction: "benjamini_hochberg"

orchestrator:
  max_concurrent_jobs: 3
  quality_gate_enforcement: true
  alert_channels: ["email", "slack"]
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_ragas_engine.py -v
pytest tests/test_golden_dataset.py -v
pytest tests/test_ab_testing.py -v

# Run with coverage
pytest --cov=evaluation tests/
```

### Example Test Data

```python
# tests/fixtures/sample_data.py
SAMPLE_EVALUATION_DATA = [
    {
        "query": "What is retrieval-augmented generation?",
        "expected_answer": "RAG combines information retrieval with text generation...",
        "expected_contexts": ["RAG is a technique", "Combines retrieval and generation"],
        "taxonomy_path": ["AI", "RAG"],
        "difficulty_level": "medium",
        "domain": "ai_technology"
    }
]
```

## 🚨 Monitoring and Alerts

### Alert Configuration

```python
from evaluation.orchestrator.evaluation_orchestrator import AlertRule

# Configure alerts
alert_rules = [
    AlertRule(
        name="Quality Degradation",
        condition="metrics.get('faithfulness', 1.0) < 0.8",
        severity="critical",
        channels=["email", "slack"]
    ),
    AlertRule(
        name="High Failure Rate",
        condition="failed_evaluations / max(total_evaluations, 1) > 0.2",
        severity="warning",
        channels=["slack"]
    )
]

orchestrator.alert_rules = alert_rules
```

### Monitoring Dashboard

Access real-time monitoring at:
- API Status: `http://localhost:8002/status`
- Health Check: `http://localhost:8002/health`
- Metrics: `http://localhost:8002/metrics`

## 🔄 Integration with dt-rag

The evaluation framework integrates seamlessly with the existing dt-rag system:

```python
# Integration with LangGraph pipeline
from apps.orchestration.src.langgraph_pipeline import get_pipeline

async def evaluate_production_system():
    pipeline = get_pipeline()

    async def rag_callable(query: str):
        request = PipelineRequest(query=query)
        response = await pipeline.execute(request)

        return RAGResponse(
            answer=response.answer,
            retrieved_docs=response.sources,
            confidence=response.confidence
        )

    # Run evaluation
    result = await orchestrator.run_evaluation_now(
        name="Production Evaluation",
        description="Evaluate live RAG system",
        golden_dataset_id="production_dataset",
        rag_system_callable=rag_callable
    )
```

## 📊 Performance Benchmarks

Expected performance characteristics:

- **Evaluation Speed**: 1-5 seconds per query (depending on dataset size)
- **Memory Usage**: ~100MB base + 10MB per 1000 queries
- **Concurrent Evaluations**: Up to 3 simultaneous evaluations
- **API Response Time**: <100ms for status endpoints, <1s for evaluation scheduling

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure quality gates pass for all changes

### Development Setup

```bash
# Clone and setup
git clone <repository>
cd dt-rag/apps/evaluation

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Start development server
python api/evaluation_api.py
```

## 📚 References

- [RAGAS Documentation](https://docs.ragas.io/)
- [Statistical Testing Best Practices](https://en.wikipedia.org/wiki/A/B_testing)
- [RAG Evaluation Methodologies](https://arxiv.org/abs/2312.10997)

## 🏆 Success Metrics

Target performance indicators:
- **Golden Dataset Quality**: > 95% annotation accuracy
- **Evaluation Accuracy**: > 90% correlation with human judgment
- **RAGAS Performance**: Consistent Faithfulness ≥ 0.85
- **A/B Test Reliability**: Statistical significance (p < 0.05)
- **Automation Coverage**: > 90% of evaluation processes automated

## 📄 License

Part of the Dynamic Taxonomy RAG v1.8.1 system. See main project license for details.