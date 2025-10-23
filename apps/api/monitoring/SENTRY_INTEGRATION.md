# Sentry Monitoring Integration - DT-RAG v1.8.1

## Overview

Comprehensive error tracking and reporting following **바이브코딩 report format** with 5-field structured error reports.

## 바이브코딩 Report Format

Every error report includes these 5 essential fields:

1. **Reproduction Steps**: Query, filters, timestamp, error context
2. **Expected vs Actual**: What should happen vs what happened
3. **Logs/Metrics**: Performance metrics (bm25_time, vector_time, etc.)
4. **Hypothesis**: Possible causes list based on error patterns
5. **Next Steps**: Actionable debugging steps

## Installation

```bash
pip install sentry-sdk[fastapi]>=1.40.0
```

## Configuration

### Environment Variables

Set your Sentry DSN in `.env`:

```bash
SENTRY_DSN=https://your-key@sentry.io/your-project-id
```

### Initialization

Sentry is automatically initialized in `apps/api/main.py` during application startup:

```python
from monitoring.sentry_reporter import init_sentry

sentry_initialized = init_sentry(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    release="1.8.1",
    traces_sample_rate=0.1,  # 10% performance monitoring
    profiles_sample_rate=0.1  # 10% profiling
)
```

## Integration Points

### 1. Hybrid Search Engine

Located in `apps/search/hybrid_search_engine.py`:

- Main search failure reporting
- Score normalization errors
- Cross-encoder reranking errors
- Search breadcrumb tracking

### 2. Search Failure Reporting

Comprehensive error context for all search failures:

```python
from monitoring.sentry_reporter import report_search_failure

report_search_failure(
    error=exception,
    query="AI machine learning",
    filters={"taxonomy_paths": [["tech", "ai"]]},
    metrics={
        "total_time": 2.5,
        "bm25_time": 0.8,
        "vector_time": 1.2,
        "cache_hit": False
    },
    search_type="hybrid",
    error_boundary="hybrid_search_engine"
)
```

### 3. Score Normalization Errors

Specialized reporting for score normalization failures:

```python
from monitoring.sentry_reporter import report_score_normalization_error

report_score_normalization_error(
    error=exception,
    scores=[0.5, 0.7, 0.9],
    normalization_method="min_max",
    context={"operation": "min_max_normalize"}
)
```

### 4. Reranker Errors

Cross-encoder reranking error reporting:

```python
from monitoring.sentry_reporter import report_reranker_error

report_reranker_error(
    error=exception,
    query="AI technology",
    results_count=50,
    rerank_config={
        "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "top_k": 5
    }
)
```

### 5. Search Breadcrumbs

Track search operations for debugging context:

```python
from monitoring.sentry_reporter import add_search_breadcrumb

add_search_breadcrumb(
    query="machine learning",
    search_type="hybrid",
    top_k=5,
    has_filters=True
)
```

## Error Report Structure

### Example Sentry Error Report

```json
{
  "error": "DatabaseError: connection pool exhausted",
  "contexts": {
    "reproduction_steps": {
      "query": "AI machine learning",
      "filters": {"taxonomy_paths": [["tech", "ai"]]},
      "search_type": "hybrid",
      "timestamp": "2025-10-01T10:30:00Z",
      "error_type": "DatabaseError"
    },
    "expected_vs_actual": {
      "expected": "Expected successful hybrid search combining BM25 and vector results",
      "actual": "Search failed with DatabaseError: connection pool exhausted"
    },
    "metrics": {
      "total_time": 5.2,
      "bm25_time": 0.0,
      "vector_time": 0.0,
      "bm25_candidates": 0,
      "vector_candidates": 0,
      "cache_hit": false
    },
    "hypothesis": {
      "possible_causes": [
        "Database connection lost or unavailable",
        "PostgreSQL service not running",
        "Connection pool exhausted",
        "Query timeout exceeded"
      ]
    },
    "next_steps": {
      "actions": [
        "Verify PostgreSQL service is running: pg_ctl status",
        "Check database connection parameters in .env",
        "Test connection with: psql -U user -d database",
        "Review PostgreSQL logs for errors",
        "Increase connection pool size if exhausted"
      ]
    }
  },
  "tags": {
    "error_boundary": "hybrid_search_engine",
    "search_type": "hybrid",
    "has_metrics": true,
    "has_filters": true
  }
}
```

## Error Patterns and Hypothesis Generation

### Database Errors

**Error Types**: `DatabaseError`, `OperationalError`, `InterfaceError`

**Hypothesis**:
- Database connection lost or unavailable
- PostgreSQL service not running
- Connection pool exhausted
- Query timeout exceeded
- Invalid SQL syntax or schema mismatch

**Next Steps**:
- Verify PostgreSQL service status
- Check database connection parameters
- Test direct database connection
- Review PostgreSQL logs
- Increase connection pool size

### Vector Search Errors

**Error Types**: Contains "vector" or "pgvector"

**Hypothesis**:
- pgvector extension not installed or enabled
- Embedding dimension mismatch
- Embeddings table missing or empty
- Vector similarity operator not supported

**Next Steps**:
- Verify pgvector extension installation
- Check embeddings table exists
- Verify embedding dimensions match model
- Regenerate embeddings if corrupted

### BM25 Search Errors

**Error Types**: Contains "fts" or "full-text search"

**Hypothesis**:
- Full-text search index not created
- Text search configuration missing
- Query syntax invalid for PostgreSQL FTS
- FTS column not properly indexed

**Next Steps**:
- Check FTS indexes existence
- Verify text search configuration
- Rebuild FTS index if corrupted
- Test with simplified query syntax

## Performance Monitoring

Sentry automatically tracks:

- **Request Performance**: p50, p75, p95, p99 latencies
- **Database Queries**: Slow query detection
- **Search Operations**: Search latency distribution
- **Error Rates**: Real-time error frequency

### Performance Dashboards

Access in Sentry web interface:

1. **Performance** → View transaction latencies
2. **Issues** → Filter by `error_boundary:hybrid_search_engine`
3. **Discover** → Custom queries on search metrics
4. **Releases** → Compare performance across versions

## Filtering and Alerting

### Recommended Alerts

1. **High Error Rate**
   - Condition: Error rate > 5% for 5 minutes
   - Notification: Email + Slack

2. **Slow Search Performance**
   - Condition: p95 latency > 4s
   - Notification: Email

3. **Database Connection Issues**
   - Condition: DatabaseError count > 10 in 5 minutes
   - Notification: PagerDuty

### Custom Filters

In Sentry interface:

```
error_boundary:hybrid_search_engine
search_type:hybrid
has_metrics:true
```

## Privacy and Data Protection

### PII Handling

Sentry integration is configured with `send_default_pii=False` to protect sensitive data:

- Query text is truncated to 200 characters
- User identifiers are hashed
- Filters are sanitized
- Full text content is excluded

### Data Retention

Configure in Sentry project settings:

- **90 days**: Default retention
- **30 days**: Recommended for GDPR compliance
- **Custom**: Per organization policy

## Testing

### Local Testing

Test Sentry integration without sending to production:

```python
import os
os.environ["SENTRY_DSN"] = ""  # Disable Sentry

# Or use test DSN
os.environ["SENTRY_DSN"] = "https://test-key@sentry.io/test-project"
```

### Trigger Test Error

```python
from monitoring.sentry_reporter import report_search_failure

try:
    raise Exception("Test Sentry integration")
except Exception as e:
    report_search_failure(
        error=e,
        query="test query",
        search_type="test",
        error_boundary="test"
    )
```

## Troubleshooting

### Sentry Not Reporting

1. Check DSN configuration
2. Verify network connectivity to Sentry
3. Check before_send hook (may filter errors)
4. Review Sentry SDK logs

### Missing Context

1. Ensure `SENTRY_AVAILABLE` flag is True
2. Verify all context fields are populated
3. Check error not filtered by before_send

### High Volume Issues

1. Reduce traces_sample_rate (default: 0.1)
2. Add error filtering in before_send hook
3. Use Sentry rate limiting

## Best Practices

### 1. Structured Errors

Always provide complete context:

```python
report_search_failure(
    error=e,
    query=query,
    filters=filters,
    metrics=metrics,
    search_type=search_type,
    error_boundary="component_name"
)
```

### 2. Meaningful Tags

Use tags for filtering:

```python
scope.set_tag("error_boundary", "hybrid_search_engine")
scope.set_tag("search_type", "vector")
scope.set_tag("environment", "production")
```

### 3. Breadcrumbs

Add breadcrumbs for debugging context:

```python
add_search_breadcrumb(
    query=query,
    search_type="hybrid",
    results=10,
    cache_hit=True
)
```

### 4. Error Sampling

Use before_send hook to skip expected errors:

```python
def before_send(event, hint):
    if 'exc_info' in hint:
        exc_type = hint['exc_info'][0]
        if exc_type.__name__ == 'ValidationError':
            return None  # Don't send to Sentry
    return event
```

## Support

For issues or questions:

1. Check Sentry documentation: https://docs.sentry.io/
2. Review DT-RAG monitoring documentation
3. Contact observability team

## Version History

- **v1.8.1** (2025-10-01): Initial Sentry integration with 바이브코딩 format
- Future: Enhanced ML-based error classification and auto-remediation
