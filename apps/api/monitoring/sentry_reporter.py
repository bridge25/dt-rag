"""
Sentry Monitoring Integration for Dynamic Taxonomy RAG v1.8.1

Comprehensive error tracking and reporting following 바이브코딩 report format.
Provides structured error reporting with 5-field format for all critical failures.

바이브코딩 Report Format:
1. Reproduction steps (query, filters, timestamp)
2. Expected vs Actual (what should happen vs what happened)
3. Logs/Metrics (bm25_time, vector_time, total_time, cache_hit)
4. Hypothesis (possible causes list)
5. Next steps (actions to take)
"""

import logging
import time
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SentryReport:
    """Structured Sentry report following 바이브코딩 format"""

    # Field 1: Reproduction steps
    reproduction_steps: Dict[str, Any] = field(default_factory=dict)

    # Field 2: Expected vs Actual
    expected_behavior: str = ""
    actual_behavior: str = ""

    # Field 3: Logs/Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Field 4: Hypothesis
    possible_causes: List[str] = field(default_factory=list)

    # Field 5: Next steps
    next_steps: List[str] = field(default_factory=list)

    # Additional context
    error_boundary: str = ""
    search_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def init_sentry(dsn: Optional[str] = None,
                environment: str = "production",
                release: str = "1.8.1",
                traces_sample_rate: float = 0.1,
                profiles_sample_rate: float = 0.1) -> bool:
    """
    Initialize Sentry monitoring with FastAPI integration.

    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (production, staging, development)
        release: Application version
        traces_sample_rate: Performance tracing sample rate (0.0 to 1.0)
        profiles_sample_rate: Profiling sample rate (0.0 to 1.0)

    Returns:
        True if initialization successful, False otherwise
    """
    if not SENTRY_AVAILABLE:
        logger.warning(
            "Sentry SDK not available. Install with: pip install sentry-sdk"
        )
        return False

    if not dsn:
        logger.warning(
            "Sentry DSN not provided. Set SENTRY_DSN environment variable."
        )
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=f"dt-rag@{release}",
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                AsyncioIntegration()
            ],
            # Enable breadcrumbs for better context
            max_breadcrumbs=100,
            # Attach stacktrace to messages
            attach_stacktrace=True,
            # Send default PII (can be disabled for privacy)
            send_default_pii=False,
            # Custom error sampling
            before_send=_before_send_hook,
            # Performance monitoring
            _experiments={
                "profiles_sample_rate": profiles_sample_rate,
            }
        )

        logger.info(
            f"✅ Sentry initialized: environment={environment}, "
            f"release={release}, traces_sample_rate={traces_sample_rate}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def _before_send_hook(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook to filter or modify events before sending to Sentry.
    Can be used to add custom tags, filter sensitive data, or skip certain errors.
    """
    # Example: Skip certain error types
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        # Skip expected errors (e.g., validation errors)
        if exc_type.__name__ in ['ValidationError', 'HTTPException']:
            return None

    return event


def report_search_failure(
    error: Exception,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    search_type: str = "hybrid",
    error_boundary: str = "search_engine"
) -> None:
    """
    Report search failure to Sentry with comprehensive 바이브코딩 format.

    Args:
        error: Exception that occurred
        query: Search query that failed
        filters: Search filters applied
        metrics: Performance metrics collected
        search_type: Type of search (hybrid, bm25, vector)
        error_boundary: Component where error occurred
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry not available - logging error locally")
        logger.error(
            f"Search failure: {error}",
            extra={
                "query": query,
                "filters": filters,
                "metrics": metrics,
                "search_type": search_type
            }
        )
        return

    # Create structured report
    report = SentryReport(
        error_boundary=error_boundary,
        search_type=search_type
    )

    # Field 1: Reproduction steps
    report.reproduction_steps = {
        "query": query[:200],  # Truncate for privacy
        "filters": filters or {},
        "search_type": search_type,
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error)
    }

    # Field 2: Expected vs Actual
    if search_type == "hybrid":
        report.expected_behavior = (
            "Expected successful hybrid search combining BM25 and vector results "
            "with proper score normalization and reranking"
        )
    elif search_type == "bm25":
        report.expected_behavior = (
            "Expected successful BM25 keyword search with PostgreSQL FTS"
        )
    elif search_type == "vector":
        report.expected_behavior = (
            "Expected successful vector similarity search with pgvector"
        )

    report.actual_behavior = (
        f"Search failed with {type(error).__name__}: {str(error)}"
    )

    # Field 3: Logs/Metrics
    if metrics:
        report.metrics = {
            "total_time": metrics.get("total_time", 0.0),
            "bm25_time": metrics.get("bm25_time", 0.0),
            "vector_time": metrics.get("vector_time", 0.0),
            "embedding_time": metrics.get("embedding_time", 0.0),
            "fusion_time": metrics.get("fusion_time", 0.0),
            "rerank_time": metrics.get("rerank_time", 0.0),
            "bm25_candidates": metrics.get("bm25_candidates", 0),
            "vector_candidates": metrics.get("vector_candidates", 0),
            "final_results": metrics.get("final_results", 0),
            "cache_hit": metrics.get("cache_hit", False)
        }

    # Field 4: Hypothesis (possible causes)
    report.possible_causes = _generate_hypothesis(error, search_type, metrics)

    # Field 5: Next steps
    report.next_steps = _generate_next_steps(error, search_type, metrics)

    # Send to Sentry with structured context
    with sentry_sdk.push_scope() as scope:
        # Set tags for filtering
        scope.set_tag("error_boundary", error_boundary)
        scope.set_tag("search_type", search_type)
        scope.set_tag("has_metrics", bool(metrics))
        scope.set_tag("has_filters", bool(filters))

        # Set contexts for all 5 fields
        scope.set_context("reproduction_steps", report.reproduction_steps)
        scope.set_context("expected_vs_actual", {
            "expected": report.expected_behavior,
            "actual": report.actual_behavior
        })
        scope.set_context("metrics", report.metrics)
        scope.set_context("hypothesis", {
            "possible_causes": report.possible_causes
        })
        scope.set_context("next_steps", {
            "actions": report.next_steps
        })

        # Add breadcrumbs for better debugging
        sentry_sdk.add_breadcrumb(
            category="search",
            message=f"Search initiated: {search_type}",
            level="info",
            data={"query_length": len(query)}
        )

        # Capture exception with full context
        sentry_sdk.capture_exception(error)

    logger.error(
        f"Search failure reported to Sentry: {type(error).__name__}",
        extra={
            "search_type": search_type,
            "query_preview": query[:50],
            "error_boundary": error_boundary
        }
    )


def report_score_normalization_error(
    error: Exception,
    scores: List[float],
    normalization_method: str,
    context: Dict[str, Any]
) -> None:
    """
    Report score normalization errors to Sentry.

    Args:
        error: Exception that occurred
        scores: Scores being normalized
        normalization_method: Normalization method used
        context: Additional context
    """
    if not SENTRY_AVAILABLE:
        logger.error(f"Score normalization error: {error}")
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_boundary", "score_normalizer")
        scope.set_tag("normalization_method", normalization_method)

        scope.set_context("score_normalization", {
            "scores_count": len(scores),
            "scores_preview": scores[:10] if scores else [],
            "normalization_method": normalization_method,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None,
            "has_zero_variance": len(set(scores)) == 1 if scores else None
        })

        scope.set_context("hypothesis", {
            "possible_causes": [
                "Empty score list provided",
                "All scores are identical (zero variance)",
                "Scores contain NaN or Inf values",
                "Invalid normalization method specified",
                "Numerical overflow/underflow in calculations"
            ]
        })

        sentry_sdk.capture_exception(error)

    logger.error(
        f"Score normalization error reported: {type(error).__name__}",
        extra={"method": normalization_method}
    )


def report_reranker_error(
    error: Exception,
    query: str,
    results_count: int,
    rerank_config: Dict[str, Any]
) -> None:
    """
    Report cross-encoder reranking errors to Sentry.

    Args:
        error: Exception that occurred
        query: Search query
        results_count: Number of results to rerank
        rerank_config: Reranker configuration
    """
    if not SENTRY_AVAILABLE:
        logger.error(f"Reranker error: {error}")
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_boundary", "cross_encoder_reranker")
        scope.set_tag("results_count", str(results_count))

        scope.set_context("reranking", {
            "query_length": len(query),
            "results_count": results_count,
            "model_name": rerank_config.get("model_name", "unknown"),
            "top_k": rerank_config.get("top_k", 5)
        })

        scope.set_context("hypothesis", {
            "possible_causes": [
                "Model failed to load or initialize",
                "Input format incompatible with model",
                "Memory exhausted during reranking",
                "Model inference timeout",
                "Results contain invalid text data"
            ]
        })

        scope.set_context("next_steps", {
            "actions": [
                "Check model availability and version",
                "Verify input text encoding and format",
                "Review memory usage and limits",
                "Test with smaller result sets",
                "Enable fallback to hybrid score sorting"
            ]
        })

        sentry_sdk.capture_exception(error)

    logger.error(
        f"Reranker error reported: {type(error).__name__}",
        extra={"results_count": results_count}
    )


def _generate_hypothesis(
    error: Exception,
    search_type: str,
    metrics: Optional[Dict[str, Any]]
) -> List[str]:
    """Generate hypothesis about error causes based on error type and metrics."""
    hypotheses = []
    error_name = type(error).__name__

    # Common database-related errors
    if error_name in ["DatabaseError", "OperationalError", "InterfaceError"]:
        hypotheses.extend([
            "Database connection lost or unavailable",
            "PostgreSQL service not running",
            "Connection pool exhausted",
            "Query timeout exceeded",
            "Invalid SQL syntax or schema mismatch"
        ])

    # Vector search specific errors
    if search_type in ["vector", "hybrid"] and "vector" in str(error).lower():
        hypotheses.extend([
            "pgvector extension not installed or enabled",
            "Embedding dimension mismatch",
            "Embeddings table missing or empty",
            "Vector similarity operator not supported"
        ])

    # BM25 search specific errors
    if search_type in ["bm25", "hybrid"] and "fts" in str(error).lower():
        hypotheses.extend([
            "Full-text search index not created",
            "Text search configuration missing",
            "Query syntax invalid for PostgreSQL FTS",
            "FTS column not properly indexed"
        ])

    # Performance-related issues
    if metrics:
        total_time = metrics.get("total_time", 0.0)
        if total_time > 5.0:
            hypotheses.append("Search timeout due to slow database queries")

        if metrics.get("bm25_candidates", 0) == 0 and metrics.get("vector_candidates", 0) == 0:
            hypotheses.append("No results found - possible data indexing issue")

    # Generic fallback
    if not hypotheses:
        hypotheses.extend([
            "Unexpected error in search pipeline",
            "System resource exhaustion",
            "Invalid input parameters",
            "Internal logic error"
        ])

    return hypotheses


def _generate_next_steps(
    error: Exception,
    search_type: str,
    metrics: Optional[Dict[str, Any]]
) -> List[str]:
    """Generate next steps for debugging based on error type and metrics."""
    steps = []
    error_name = type(error).__name__

    # Database connection issues
    if error_name in ["DatabaseError", "OperationalError", "InterfaceError"]:
        steps.extend([
            "Verify PostgreSQL service is running: pg_ctl status",
            "Check database connection parameters in .env",
            "Test connection with: psql -U <user> -d <database>",
            "Review PostgreSQL logs for errors",
            "Increase connection pool size if exhausted"
        ])

    # Vector search issues
    if search_type in ["vector", "hybrid"]:
        steps.extend([
            "Verify pgvector extension: SELECT * FROM pg_extension WHERE extname='vector'",
            "Check embeddings table exists: \\dt embeddings",
            "Verify embedding dimensions match model output",
            "Regenerate embeddings if corruption suspected"
        ])

    # BM25 search issues
    if search_type in ["bm25", "hybrid"]:
        steps.extend([
            "Check FTS indexes: \\di chunks_text_idx",
            "Verify text search configuration: \\dF+",
            "Rebuild FTS index if corrupted",
            "Test query syntax with simplified version"
        ])

    # Performance optimization
    if metrics and metrics.get("total_time", 0.0) > 3.0:
        steps.extend([
            "Review query execution plan: EXPLAIN ANALYZE",
            "Check for missing indexes on filtered columns",
            "Optimize candidate retrieval limits",
            "Enable query result caching"
        ])

    # Generic debugging steps
    steps.extend([
        "Enable debug logging for detailed error context",
        "Check system resource usage (CPU, memory, disk)",
        "Review recent schema or configuration changes",
        "Test with minimal query to isolate issue"
    ])

    return steps


def capture_message(message: str, level: str = "info", **kwargs) -> None:
    """
    Capture informational message to Sentry.

    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context to attach
    """
    if not SENTRY_AVAILABLE:
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
        return

    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_context(key, value)

        sentry_sdk.capture_message(message, level=level)


def add_search_breadcrumb(query: str, search_type: str, correlation_id: Optional[str] = None, **data) -> None:
    """Add search operation breadcrumb for debugging context with correlation tracking."""
    if not SENTRY_AVAILABLE:
        return

    breadcrumb_data = {
        "query_preview": query[:100],
        "search_type": search_type,
        **data
    }

    if correlation_id:
        breadcrumb_data["correlation_id"] = correlation_id

    sentry_sdk.add_breadcrumb(
        category="search",
        message=f"Search executed: {search_type}",
        level="info",
        data=breadcrumb_data
    )
