# DT-RAG v1.8.1 Comprehensive Monitoring System

A complete observability and monitoring solution for the Dynamic Taxonomy RAG system, providing comprehensive tracking of LLM operations, system performance, and SLO compliance.

## Features

### 🔍 **Langfuse Integration**
- Complete LLM call tracking and cost analysis
- Request tracing with performance monitoring
- Token usage and cost optimization recommendations
- Quality metrics collection and analysis

### 📊 **Prometheus Metrics Collection**
- Real-time RAG performance metrics
- System resource monitoring
- Custom business metrics
- SLO/SLI compliance tracking

### 🚨 **Intelligent Alerting**
- SLO violation detection and alerts
- Automated degradation strategies
- Configurable notification channels
- Alert suppression and grouping

### 📈 **Real-time Dashboards**
- System overview dashboard
- Performance monitoring
- Cost optimization views
- Quality metrics visualization
- Grafana integration

### 🏥 **Health Monitoring**
- Comprehensive system health checks
- Dependency monitoring
- Automated recovery actions
- Performance trend analysis

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG System   │───▶│   Monitoring    │───▶│   Dashboards    │
│   Components   │    │   Integration   │    │   & Alerts      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Langfuse     │    │   Prometheus    │    │     Grafana     │
│  LLM Tracking   │    │    Metrics      │    │   Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Install monitoring dependencies
pip install -r requirements-monitoring.txt

# Install optional Langfuse integration
pip install langfuse

# Install optional vector database clients (if needed)
pip install qdrant-client  # For Qdrant
```

### 2. Configuration

Set environment variables:

```bash
# Langfuse Configuration
export LANGFUSE_PUBLIC_KEY="pk_..."
export LANGFUSE_SECRET_KEY="sk_..."
export LANGFUSE_HOST="https://cloud.langfuse.com"

# Prometheus Configuration
export PROMETHEUS_PORT="8090"
export PROMETHEUS_EXPORT_INTERVAL="30"

# SLO Configuration
export SLO_P95_LATENCY_SECONDS="4.0"
export SLO_COST_PER_QUERY_WON="10.0"
export SLO_FAITHFULNESS_THRESHOLD="0.85"
export SLO_AVAILABILITY_PERCENT="99.5"

# Alerting Configuration
export ALERT_WEBHOOK_URL="https://hooks.slack.com/..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
```

### 3. Initialize Monitoring

```python
from dt_rag.apps.monitoring import initialize_monitoring_system

# Initialize and start monitoring
obs_manager = await initialize_monitoring_system()

# Monitor RAG operations
async with obs_manager.trace_rag_request(
    query="What is dynamic taxonomy classification?",
    user_id="user123",
    session_id="session456"
) as observer:
    # Your RAG processing logic here
    result = await process_rag_query(query)
```

### 4. Start Monitoring Application

```bash
# Start monitoring web interface
python -m dt_rag.apps.monitoring.app

# Or with uvicorn directly
uvicorn dt_rag.apps.monitoring.app:app --host 0.0.0.0 --port 8080
```

### 5. Access Monitoring

- **Dashboard**: http://localhost:8080/dashboard
- **Metrics**: http://localhost:8090/metrics (Prometheus format)
- **Health**: http://localhost:8080/health
- **API Docs**: http://localhost:8080/docs

## Integration Guide

### Automatic Integration

Use decorators for automatic monitoring:

```python
from dt_rag.apps.monitoring.integration import RAGMonitoringIntegration

# Initialize integration
monitoring = RAGMonitoringIntegration(obs_manager)

# Monitor classification operations
@monitoring.monitor_classification()
async def classify_document(text: str) -> Dict[str, Any]:
    return {
        "category": "technical",
        "confidence": 0.9,
        "model": "bert-classifier",
        "cost_cents": 2.5
    }

# Monitor search operations
@monitoring.monitor_search(search_type="hybrid")
async def search_documents(query: str) -> List[Dict[str, Any]]:
    return [
        {"doc_id": "doc1", "score": 0.9},
        {"doc_id": "doc2", "score": 0.8}
    ]

# Monitor taxonomy operations
@monitoring.monitor_taxonomy_operation(operation_type="add_node")
async def add_taxonomy_node(name: str, parent_id: int) -> Tuple[bool, int]:
    return True, 123  # success, new_node_id
```

### Manual Integration

For fine-grained control:

```python
# Record classification results
await obs_manager.record_classification_result(
    text="Sample document text",
    category="technical/ai",
    confidence=0.92,
    latency_ms=150.0,
    model_used="gpt-4",
    cost_cents=5.0,
    faithfulness_score=0.88
)

# Record search operations
await obs_manager.record_search_operation(
    query="machine learning algorithms",
    results_count=25,
    search_type="hybrid",
    latency_ms=75.0,
    quality_score=0.85
)

# Record taxonomy operations
await obs_manager.record_taxonomy_operation(
    operation_type="create_version",
    nodes_affected=15,
    latency_ms=500.0,
    success=True,
    version_from=5,
    version_to=6
)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGFUSE_PUBLIC_KEY` | - | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | - | Langfuse secret key |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse server URL |
| `PROMETHEUS_PORT` | `8090` | Prometheus metrics port |
| `SLO_P95_LATENCY_SECONDS` | `4.0` | P95 latency SLO target |
| `SLO_COST_PER_QUERY_WON` | `10.0` | Cost per query SLO |
| `SLO_FAITHFULNESS_THRESHOLD` | `0.85` | Faithfulness score SLO |
| `SLO_AVAILABILITY_PERCENT` | `99.5` | Availability SLO |
| `ALERT_WEBHOOK_URL` | - | General webhook for alerts |
| `SLACK_WEBHOOK_URL` | - | Slack webhook URL |
| `ENVIRONMENT` | `development` | Environment name |

### Configuration File

Create `monitoring.yaml`:

```yaml
langfuse:
  enabled: true
  trace_sampling_rate: 0.1  # 10% sampling in production

prometheus:
  enabled: true
  port: 8090
  export_interval_seconds: 30

slo:
  p95_latency_seconds: 4.0
  cost_per_query_won: 10.0
  faithfulness_threshold: 0.85
  availability_percent: 99.5

alerting:
  enabled: true
  suppress_duplicate_minutes: 5

health_check:
  enabled: true
  check_interval_seconds: 30
  cpu_warning_percent: 75.0
  cpu_critical_percent: 90.0

degradation:
  enabled: true
  max_degradation_duration_minutes: 60
```

## Monitoring Metrics

### Core RAG Metrics

- `dt_rag_requests_total` - Total RAG requests
- `dt_rag_request_duration_seconds` - Request latency distribution
- `dt_rag_classification_total` - Classification operations
- `dt_rag_classification_confidence` - Classification confidence scores
- `dt_rag_search_operations_total` - Search operations
- `dt_rag_search_quality_score` - Search quality metrics
- `dt_rag_taxonomy_operations_total` - Taxonomy operations

### Quality Metrics

- `dt_rag_faithfulness_score` - RAG faithfulness scores
- `dt_rag_user_satisfaction_score` - User satisfaction ratings

### Cost Metrics

- `dt_rag_cost_total_won` - Total cost in Korean Won
- `dt_rag_cost_per_query_won` - Cost per query distribution

### System Metrics

- `dt_rag_system_cpu_usage_percent` - CPU usage
- `dt_rag_system_memory_usage_bytes` - Memory usage
- `dt_rag_database_connections_active` - Database connections
- `dt_rag_vector_database_size_entries` - Vector database size

## SLO/SLI Monitoring

### Defined SLOs

1. **Performance SLO**: P95 latency ≤ 4 seconds
2. **Cost SLO**: Average cost ≤ ₩10 per query
3. **Quality SLO**: Faithfulness score ≥ 0.85
4. **Availability SLO**: System availability ≥ 99.5%

### SLO Violations

Automatic alerts triggered when:
- P95 latency exceeds 4 seconds for 2+ minutes
- Cost per query exceeds ₩10 for 5+ minutes
- Faithfulness score below 0.85 for 10+ minutes
- Error rate exceeds 1% for 1+ minute

## Automated Degradation

When SLO violations are detected, the system automatically:

### High Latency Mitigation
- Reduce search complexity (fewer results)
- Disable expensive reranking
- Increase response caching duration

### Cost Optimization
- Switch to more efficient models
- Reduce context length
- Increase caching aggressiveness

### Quality Enhancement
- Enable additional verification steps
- Increase search depth
- Use higher-quality models

### Error Rate Mitigation
- Enable circuit breakers
- Fallback to cached responses
- Reduce concurrent request limits

## Dashboards

### Available Dashboards

1. **System Overview** - High-level system health and performance
2. **RAG Performance** - Detailed RAG operation metrics
3. **SLO Compliance** - SLO tracking and compliance status
4. **Cost Optimization** - Cost analysis and optimization
5. **Quality Metrics** - Quality scores and trends
6. **Taxonomy Operations** - Taxonomy-specific metrics
7. **Alerting Status** - Alert management and status

### Grafana Integration

Export dashboard configurations:

```bash
# Get Grafana JSON for system overview
curl http://localhost:8080/dashboard/grafana/system_overview

# Get all dashboard configurations
curl http://localhost:8080/dashboard/grafana/rag_performance
curl http://localhost:8080/dashboard/grafana/slo_compliance
```

## API Reference

### Health Endpoints

- `GET /health` - System health check
- `GET /status` - Comprehensive system status

### Metrics Endpoints

- `GET /metrics` - Prometheus metrics (requires auth if enabled)
- `GET /metrics/summary` - High-level metrics summary

### SLO Endpoints

- `GET /slo/compliance` - SLO compliance status

### Alert Endpoints

- `GET /alerts` - Active alerts
- `POST /alerts/{alert_id}/resolve` - Resolve alert

### Dashboard Endpoints

- `GET /dashboard` - Real-time HTML dashboard
- `GET /dashboard/data` - Dashboard data API
- `GET /dashboard/grafana/{type}` - Grafana export

## Best Practices

### Sampling Strategy

For production environments:

```python
# Reduce trace sampling to manage costs
config = ObservabilityConfig(
    trace_sampling_rate=0.1  # 10% sampling
)
```

### Cost Optimization

Monitor and optimize costs:

```python
# Track cost metrics
await obs_manager.record_classification_result(
    # ... other params
    cost_cents=cost_calculator.calculate_cost(tokens, model)
)
```

### Quality Monitoring

Implement quality feedback:

```python
# Record faithfulness scores
await obs_manager.record_faithfulness_score(
    score=evaluate_faithfulness(response, context),
    model="gpt-4",
    query_type="factual"
)
```

## Troubleshooting

### Common Issues

1. **Langfuse Connection Failed**
   - Check public/secret keys
   - Verify host URL
   - Check network connectivity

2. **Metrics Not Appearing**
   - Verify Prometheus port accessibility
   - Check metrics collector initialization
   - Review log files for errors

3. **Alerts Not Firing**
   - Verify webhook URLs
   - Check SLO threshold configuration
   - Review alerting manager logs

4. **High Memory Usage**
   - Reduce metrics retention
   - Adjust sampling rates
   - Monitor metric cardinality

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL="DEBUG"
python -m dt_rag.apps.monitoring.app
```

## Performance Impact

### Resource Usage

- **CPU Overhead**: ~3-5% additional CPU usage
- **Memory Overhead**: ~50-100MB for metrics storage
- **Network Overhead**: Minimal (batch exports)
- **Storage**: ~1MB per day for metrics (depends on traffic)

### Optimization Tips

1. **Reduce Sampling**: Lower trace sampling rate in production
2. **Metric Cleanup**: Regular cleanup of old metrics
3. **Batch Processing**: Use batch exports for external systems
4. **Caching**: Enable response caching to reduce monitoring overhead

## Contributing

To extend the monitoring system:

1. Add new metrics in `metrics_collector.py`
2. Create custom health checks in `health_checker.py`
3. Implement new dashboard types in `dashboard_generator.py`
4. Add alert rules in `alerting_manager.py`

## License

Part of the Dynamic Taxonomy RAG v1.8.1 system.