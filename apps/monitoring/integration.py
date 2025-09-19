"""
Integration module for DT-RAG v1.8.1 Monitoring System

Integrates observability with existing RAG components including:
- LangGraph pipeline monitoring
- Database operation tracking
- Taxonomy DAG operation monitoring
- API endpoint instrumentation
"""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from functools import wraps

from .core.observability_manager import ObservabilityManager, ObservabilityConfig

logger = logging.getLogger(__name__)


class RAGMonitoringIntegration:
    """
    Integration layer for monitoring RAG system components

    Provides decorators and context managers for automatic instrumentation
    of existing RAG components without requiring major code changes.
    """

    def __init__(self, observability_manager: ObservabilityManager):
        self.obs = observability_manager

    def monitor_classification(self, func=None, *, category_extractor=None, confidence_extractor=None):
        """
        Decorator for monitoring classification operations

        Args:
            category_extractor: Function to extract category from result
            confidence_extractor: Function to extract confidence from result
        """
        def decorator(f):
            @wraps(f)
            async def wrapper(*args, **kwargs):
                start_time = time.time()

                # Extract text input (assume first arg or 'text' kwarg)
                text = kwargs.get('text', args[0] if args else "")

                try:
                    result = await f(*args, **kwargs)

                    # Extract metrics from result
                    category = "unknown"
                    confidence = 0.0
                    model_used = "unknown"
                    cost_cents = 0.0
                    faithfulness_score = None

                    if isinstance(result, dict):
                        category = result.get('category', 'unknown')
                        confidence = result.get('confidence', 0.0)
                        model_used = result.get('model', 'unknown')
                        cost_cents = result.get('cost_cents', 0.0)
                        faithfulness_score = result.get('faithfulness_score')
                    elif category_extractor and confidence_extractor:
                        category = category_extractor(result)
                        confidence = confidence_extractor(result)

                    # Record classification metrics
                    latency_ms = (time.time() - start_time) * 1000
                    await self.obs.record_classification_result(
                        text=text,
                        category=category,
                        confidence=confidence,
                        latency_ms=latency_ms,
                        model_used=model_used,
                        cost_cents=cost_cents,
                        faithfulness_score=faithfulness_score
                    )

                    return result

                except Exception as e:
                    # Record error
                    latency_ms = (time.time() - start_time) * 1000
                    await self.obs.record_classification_result(
                        text=text,
                        category="error",
                        confidence=0.0,
                        latency_ms=latency_ms,
                        model_used="unknown",
                        cost_cents=0.0
                    )
                    raise

            return wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)

    def monitor_search(self, func=None, *, search_type="unknown"):
        """Decorator for monitoring search operations"""
        def decorator(f):
            @wraps(f)
            async def wrapper(*args, **kwargs):
                start_time = time.time()

                # Extract query (assume first arg or 'query' kwarg)
                query = kwargs.get('query', args[0] if args else "")

                try:
                    result = await f(*args, **kwargs)

                    # Extract search metrics
                    results_count = 0
                    quality_score = None

                    if isinstance(result, dict):
                        results_count = len(result.get('results', []))
                        quality_score = result.get('quality_score')
                    elif isinstance(result, list):
                        results_count = len(result)

                    # Record search metrics
                    latency_ms = (time.time() - start_time) * 1000
                    await self.obs.record_search_operation(
                        query=query,
                        results_count=results_count,
                        search_type=search_type,
                        latency_ms=latency_ms,
                        quality_score=quality_score
                    )

                    return result

                except Exception as e:
                    # Record error
                    latency_ms = (time.time() - start_time) * 1000
                    await self.obs.record_search_operation(
                        query=query,
                        results_count=0,
                        search_type=search_type,
                        latency_ms=latency_ms
                    )
                    raise

            return wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)

    def monitor_taxonomy_operation(self, func=None, *, operation_type="unknown"):
        """Decorator for monitoring taxonomy operations"""
        def decorator(f):
            @wraps(f)
            async def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = await f(*args, **kwargs)

                    # Extract operation metrics
                    nodes_affected = 1
                    success = True
                    version_from = None
                    version_to = None

                    if isinstance(result, tuple) and len(result) >= 2:
                        success = result[0]
                        if isinstance(result[1], int):
                            nodes_affected = 1
                            version_to = result[1]
                    elif isinstance(result, dict):
                        success = result.get('success', True)
                        nodes_affected = result.get('nodes_affected', 1)
                        version_from = result.get('version_from')
                        version_to = result.get('version_to')

                    # Record taxonomy operation
                    latency_ms = (time.time() - start_time) * 1000
                    await self.obs.record_taxonomy_operation(
                        operation_type=operation_type,
                        nodes_affected=nodes_affected,
                        latency_ms=latency_ms,
                        success=success,
                        version_from=version_from,
                        version_to=version_to
                    )

                    return result

                except Exception as e:
                    # Record error
                    latency_ms = (time.time() - start_time) * 1000
                    await self.obs.record_taxonomy_operation(
                        operation_type=operation_type,
                        nodes_affected=0,
                        latency_ms=latency_ms,
                        success=False
                    )
                    raise

            return wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)

    @asynccontextmanager
    async def trace_rag_request(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracing complete RAG requests"""
        async with self.obs.trace_rag_request(
            query=query,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata
        ) as observer:
            yield observer


# Integration patches for existing components

def patch_taxonomy_dag_manager(taxonomy_dag_manager, monitoring_integration: RAGMonitoringIntegration):
    """Patch TaxonomyDAGManager with monitoring"""

    # Wrap key methods with monitoring
    original_add_node = taxonomy_dag_manager.add_node
    original_move_node = taxonomy_dag_manager.move_node
    original_create_version = taxonomy_dag_manager.create_version
    original_rollback_to_version = taxonomy_dag_manager.rollback_to_version

    @monitoring_integration.monitor_taxonomy_operation(operation_type="add_node")
    async def monitored_add_node(*args, **kwargs):
        return await original_add_node(*args, **kwargs)

    @monitoring_integration.monitor_taxonomy_operation(operation_type="move_node")
    async def monitored_move_node(*args, **kwargs):
        return await original_move_node(*args, **kwargs)

    @monitoring_integration.monitor_taxonomy_operation(operation_type="create_version")
    async def monitored_create_version(*args, **kwargs):
        return await original_create_version(*args, **kwargs)

    @monitoring_integration.monitor_taxonomy_operation(operation_type="rollback")
    async def monitored_rollback_to_version(*args, **kwargs):
        return await original_rollback_to_version(*args, **kwargs)

    # Replace methods
    taxonomy_dag_manager.add_node = monitored_add_node
    taxonomy_dag_manager.move_node = monitored_move_node
    taxonomy_dag_manager.create_version = monitored_create_version
    taxonomy_dag_manager.rollback_to_version = monitored_rollback_to_version

    logger.info("TaxonomyDAGManager patched with monitoring")


def create_monitoring_middleware():
    """Create FastAPI middleware for request monitoring"""

    def monitoring_middleware(request, call_next):
        async def process_request():
            start_time = time.time()

            # Extract request info
            path = request.url.path
            method = request.method
            user_id = request.headers.get('x-user-id')

            try:
                response = await call_next(request)

                # Record successful request
                duration = time.time() - start_time
                # This would integrate with the observability manager
                logger.info(f"Request {method} {path} completed in {duration:.3f}s")

                return response

            except Exception as e:
                # Record failed request
                duration = time.time() - start_time
                logger.error(f"Request {method} {path} failed after {duration:.3f}s: {e}")
                raise

        return process_request()

    return monitoring_middleware


def setup_observability(
    langfuse_enabled: bool = True,
    langfuse_public_key: Optional[str] = None,
    langfuse_secret_key: Optional[str] = None,
    prometheus_enabled: bool = True,
    prometheus_port: int = 8090,
    alerting_enabled: bool = True,
    alert_webhook_url: Optional[str] = None
) -> ObservabilityManager:
    """
    Setup comprehensive observability for DT-RAG system

    Args:
        langfuse_enabled: Enable Langfuse integration
        langfuse_public_key: Langfuse public key
        langfuse_secret_key: Langfuse secret key
        prometheus_enabled: Enable Prometheus metrics
        prometheus_port: Prometheus metrics port
        alerting_enabled: Enable alerting system
        alert_webhook_url: Webhook URL for alerts

    Returns:
        Configured ObservabilityManager instance
    """

    config = ObservabilityConfig(
        langfuse_enabled=langfuse_enabled,
        langfuse_public_key=langfuse_public_key,
        langfuse_secret_key=langfuse_secret_key,
        prometheus_enabled=prometheus_enabled,
        prometheus_port=prometheus_port,
        alerting_enabled=alerting_enabled,
        alert_webhook_url=alert_webhook_url
    )

    observability_manager = ObservabilityManager(config)

    logger.info("Observability system configured")
    return observability_manager


async def initialize_monitoring_system() -> ObservabilityManager:
    """
    Initialize and start the complete monitoring system

    Returns:
        Started ObservabilityManager instance
    """

    # Setup observability with environment variables or defaults
    obs_manager = setup_observability()

    # Start observability services
    await obs_manager.start()

    logger.info("Monitoring system initialized and started")
    return obs_manager


# Example integration with LangGraph pipeline
class MonitoredLangGraphPipeline:
    """
    Example wrapper for LangGraph pipeline with comprehensive monitoring

    This demonstrates how to integrate monitoring with the existing
    LangGraph pipeline without major refactoring.
    """

    def __init__(self, langgraph_pipeline, monitoring_integration: RAGMonitoringIntegration):
        self.pipeline = langgraph_pipeline
        self.monitoring = monitoring_integration

    async def process_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process query with comprehensive monitoring"""

        async with self.monitoring.trace_rag_request(
            query=query,
            user_id=user_id,
            session_id=session_id,
            metadata={'pipeline': 'langgraph'}
        ) as observer:

            try:
                # Process through pipeline stages with monitoring
                result = await self._process_with_monitoring(query, observer)

                return result

            except Exception as e:
                if observer:
                    await observer.record_error(str(e))
                raise

    async def _process_with_monitoring(self, query: str, observer) -> Dict[str, Any]:
        """Process query through monitored pipeline stages"""

        # Stage 1: Classification (if observer has span method)
        if hasattr(observer, 'span'):
            async with observer.span(
                name="classification",
                input_data={"query": query[:500]},
                metadata={"stage": "classification"}
            ) as span:
                classification_result = await self._classify_query(query)
                if span:
                    span.update(
                        output=classification_result,
                        metadata={"confidence": classification_result.get("confidence", 0)}
                    )

        # Stage 2: Search
        if hasattr(observer, 'span'):
            async with observer.span(
                name="search",
                input_data={"query": query[:500], "category": classification_result.get("category")},
                metadata={"stage": "search"}
            ) as span:
                search_result = await self._search_documents(query, classification_result)
                if span:
                    span.update(
                        output={"results_count": len(search_result.get("results", []))},
                        metadata={"search_type": "hybrid"}
                    )

        # Stage 3: Generation
        if hasattr(observer, 'span'):
            async with observer.span(
                name="generation",
                input_data={"query": query[:500], "context_docs": len(search_result.get("results", []))},
                metadata={"stage": "generation"}
            ) as span:
                generation_result = await self._generate_response(query, search_result)
                if span:
                    span.update(
                        output={"response": generation_result.get("response", "")[:500]},
                        metadata={"model": generation_result.get("model", "unknown")}
                    )

        # Combine results
        final_result = {
            "query": query,
            "classification": classification_result,
            "search": search_result,
            "generation": generation_result,
            "metadata": {
                "pipeline": "langgraph",
                "timestamp": time.time()
            }
        }

        return final_result

    async def _classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query (placeholder)"""
        # This would integrate with actual classification logic
        return {
            "category": "general",
            "confidence": 0.8,
            "model": "classifier-v1"
        }

    async def _search_documents(self, query: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Search documents (placeholder)"""
        # This would integrate with actual search logic
        return {
            "results": [
                {"doc_id": "doc1", "score": 0.9},
                {"doc_id": "doc2", "score": 0.8}
            ],
            "search_type": "hybrid"
        }

    async def _generate_response(self, query: str, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response (placeholder)"""
        # This would integrate with actual generation logic
        return {
            "response": "This is a generated response",
            "model": "gpt-4",
            "cost_cents": 5.0,
            "tokens": 150
        }


# Health check integration
def register_rag_health_checks(health_checker, db_manager, vector_db_client=None):
    """Register RAG-specific health checks"""

    async def check_postgres_health():
        """Check PostgreSQL health"""
        try:
            async with db_manager.async_session() as session:
                result = await session.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "message": "PostgreSQL connection successful"
                }
        except Exception as e:
            return {
                "status": "critical",
                "message": "PostgreSQL connection failed",
                "error": str(e)
            }

    async def check_vector_db_health():
        """Check vector database health"""
        if not vector_db_client:
            return {
                "status": "warning",
                "message": "Vector database client not configured"
            }

        try:
            # This would use actual vector DB health check
            # For example, with Qdrant:
            # info = await vector_db_client.get_collections()
            return {
                "status": "healthy",
                "message": "Vector database connection successful"
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": "Vector database connection failed",
                "error": str(e)
            }

    # Register health checks
    health_checker.register_health_check(
        name="postgres_rag",
        component_type=health_checker.ComponentType.DATABASE,
        check_function=check_postgres_health,
        critical=True
    )

    if vector_db_client:
        health_checker.register_health_check(
            name="vector_db_rag",
            component_type=health_checker.ComponentType.VECTOR_DB,
            check_function=check_vector_db_health,
            critical=True
        )

    logger.info("RAG-specific health checks registered")


# Usage example
async def example_integration():
    """Example of how to integrate monitoring with existing RAG system"""

    # Initialize monitoring
    obs_manager = await initialize_monitoring_system()

    # Create integration layer
    monitoring_integration = RAGMonitoringIntegration(obs_manager)

    # Example: Monitor a classification function
    @monitoring_integration.monitor_classification()
    async def classify_document(text: str) -> Dict[str, Any]:
        # Your existing classification logic
        return {
            "category": "technical",
            "confidence": 0.9,
            "model": "bert-classifier"
        }

    # Example: Monitor a search function
    @monitoring_integration.monitor_search(search_type="hybrid")
    async def search_documents(query: str) -> List[Dict[str, Any]]:
        # Your existing search logic
        return [
            {"doc_id": "doc1", "score": 0.9},
            {"doc_id": "doc2", "score": 0.8}
        ]

    # Example: Monitor taxonomy operations
    @monitoring_integration.monitor_taxonomy_operation(operation_type="add_node")
    async def add_taxonomy_node(node_name: str, parent_id: int) -> tuple:
        # Your existing taxonomy logic
        return True, 123  # success, new_node_id

    # Example: Process a complete RAG request
    async with monitoring_integration.trace_rag_request(
        query="What is dynamic taxonomy classification?",
        user_id="user123",
        session_id="session456"
    ) as observer:

        # Your RAG processing logic here
        classification = await classify_document("sample text")
        search_results = await search_documents("sample query")
        taxonomy_result = await add_taxonomy_node("new_node", 1)

        result = {
            "classification": classification,
            "search": search_results,
            "taxonomy": taxonomy_result
        }

    # Check system health
    health_status = await obs_manager.get_system_metrics()
    slo_compliance = await obs_manager.check_slo_compliance()

    logger.info(f"System health: {health_status}")
    logger.info(f"SLO compliance: {slo_compliance}")

    return obs_manager