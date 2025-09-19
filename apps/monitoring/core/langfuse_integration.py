"""
Langfuse Integration for DT-RAG v1.8.1

Comprehensive LLM observability and trace analysis for RAG operations.
Tracks LLM calls, costs, performance metrics, and user interactions.
"""

import os
import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe
    from langfuse.client import StatefulTraceClient, StatefulSpanClient
    LANGFUSE_AVAILABLE = True
except ImportError:
    # Mock Langfuse classes if not available
    LANGFUSE_AVAILABLE = False

    class Langfuse:
        def __init__(self, *args, **kwargs):
            pass

        def trace(self, *args, **kwargs):
            return MockTrace()

        def span(self, *args, **kwargs):
            return MockSpan()

    class MockTrace:
        def __init__(self):
            self.id = str(uuid.uuid4())

        def span(self, *args, **kwargs):
            return MockSpan()

        def update(self, *args, **kwargs):
            pass

        def score(self, *args, **kwargs):
            pass

    class MockSpan:
        def __init__(self):
            self.id = str(uuid.uuid4())

        def update(self, *args, **kwargs):
            pass

        def end(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)


@dataclass
class LLMUsageMetrics:
    """LLM usage and cost tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_won: float = 0.0
    model: str = ""
    latency_ms: float = 0.0


@dataclass
class ClassificationResult:
    """Classification operation result"""
    text: str
    category: str
    confidence: float
    model_used: str
    latency_ms: float
    cost_cents: float
    tokens_used: int
    faithfulness_score: Optional[float] = None
    rule_candidates: List[str] = None
    llm_cost_cents: float = 0.0
    llm_latency_ms: float = 0.0
    taxonomy_version: Optional[str] = None


class LangfuseManager:
    """
    Langfuse integration manager for comprehensive LLM observability

    Features:
    - LLM call tracking with cost analysis
    - Request tracing and performance monitoring
    - User session management
    - Quality metrics collection
    - Cost optimization recommendations
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None
    ):
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        self.enabled = LANGFUSE_AVAILABLE and self.public_key and self.secret_key

        if self.enabled:
            try:
                self.client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host
                )
                logger.info("Langfuse client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Langfuse client: {e}")
                self.enabled = False
                self.client = None
        else:
            self.client = None
            if not LANGFUSE_AVAILABLE:
                logger.warning("Langfuse library not available - install with: pip install langfuse")
            else:
                logger.warning("Langfuse credentials not provided - LLM observability disabled")

    async def create_rag_observer(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'LangfuseRAGObserver':
        """Create a RAG operation observer"""
        return LangfuseRAGObserver(
            langfuse_client=self.client,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
            enabled=self.enabled
        )

    async def record_classification(
        self,
        text: str,
        category: str,
        confidence: float,
        model: str,
        latency_ms: float,
        cost_cents: float = 0.0,
        faithfulness_score: Optional[float] = None
    ):
        """Record classification operation"""
        if not self.enabled:
            return

        try:
            trace = self.client.trace(
                name="document_classification",
                input={"text": text[:1000]},  # Truncate for privacy
                output={
                    "classification": category,
                    "confidence": confidence,
                    "processing_time_ms": latency_ms
                },
                metadata={
                    "model": model,
                    "cost_cents": cost_cents,
                    "faithfulness_score": faithfulness_score
                },
                tags=["classification", "rag", category.split("/")[0] if "/" in category else category]
            )

            # Add quality score if available
            if faithfulness_score is not None:
                trace.score(
                    name="faithfulness",
                    value=faithfulness_score,
                    comment=f"Classification faithfulness score for {category}"
                )

        except Exception as e:
            logger.error(f"Failed to record classification in Langfuse: {e}")

    async def record_search(
        self,
        query: str,
        results_count: int,
        search_type: str,
        latency_ms: float,
        quality_score: Optional[float] = None
    ):
        """Record search operation"""
        if not self.enabled:
            return

        try:
            trace = self.client.trace(
                name="rag_search",
                input={"query": query[:500]},
                output={
                    "results_count": results_count,
                    "search_type": search_type,
                    "processing_time_ms": latency_ms
                },
                metadata={
                    "search_type": search_type,
                    "quality_score": quality_score
                },
                tags=["search", "rag", search_type]
            )

            # Add quality score if available
            if quality_score is not None:
                trace.score(
                    name="search_quality",
                    value=quality_score,
                    comment=f"Search quality score for {search_type}"
                )

        except Exception as e:
            logger.error(f"Failed to record search in Langfuse: {e}")

    async def record_taxonomy_operation(
        self,
        operation_type: str,
        nodes_affected: int,
        latency_ms: float,
        success: bool,
        version_from: Optional[int] = None,
        version_to: Optional[int] = None
    ):
        """Record taxonomy operation"""
        if not self.enabled:
            return

        try:
            trace = self.client.trace(
                name="taxonomy_operation",
                input={
                    "operation_type": operation_type,
                    "nodes_affected": nodes_affected,
                    "version_from": version_from,
                    "version_to": version_to
                },
                output={
                    "success": success,
                    "processing_time_ms": latency_ms
                },
                metadata={
                    "operation_type": operation_type,
                    "nodes_affected": nodes_affected
                },
                tags=["taxonomy", "rag", operation_type]
            )

        except Exception as e:
            logger.error(f"Failed to record taxonomy operation in Langfuse: {e}")


class LangfuseRAGObserver:
    """
    Observes and tracks individual RAG operations in Langfuse

    Provides detailed tracing for:
    - Query processing pipeline
    - LLM interactions
    - Search operations
    - Cost tracking
    - Performance monitoring
    """

    def __init__(
        self,
        langfuse_client: Optional[Langfuse],
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ):
        self.client = langfuse_client
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.enabled = enabled and langfuse_client is not None

        self.trace = None
        self.current_span = None
        self.start_time = None
        self.total_cost_usd = 0.0
        self.total_tokens = 0

    async def start_trace(self, query: str):
        """Start tracing a RAG operation"""
        if not self.enabled:
            return

        try:
            self.start_time = time.time()

            self.trace = self.client.trace(
                name="rag_query_processing",
                input={"query": query},
                session_id=self.session_id,
                user_id=self.user_id,
                metadata={
                    **self.metadata,
                    "start_time": datetime.utcnow().isoformat(),
                    "system_version": "dt-rag-v1.8.1"
                },
                tags=["rag", "query", "dt-rag"]
            )

        except Exception as e:
            logger.error(f"Failed to start Langfuse trace: {e}")

    async def end_trace(self, output: Optional[Dict[str, Any]] = None):
        """End the RAG operation trace"""
        if not self.enabled or not self.trace:
            return

        try:
            duration_ms = (time.time() - self.start_time) * 1000 if self.start_time else 0

            self.trace.update(
                output=output or {"status": "completed"},
                metadata={
                    **self.metadata,
                    "end_time": datetime.utcnow().isoformat(),
                    "duration_ms": duration_ms,
                    "total_cost_usd": self.total_cost_usd,
                    "total_tokens": self.total_tokens
                }
            )

        except Exception as e:
            logger.error(f"Failed to end Langfuse trace: {e}")

    async def record_error(self, error_message: str):
        """Record an error in the current trace"""
        if not self.enabled or not self.trace:
            return

        try:
            self.trace.update(
                output={"error": error_message, "status": "error"},
                metadata={
                    **self.metadata,
                    "error_time": datetime.utcnow().isoformat(),
                    "error_message": error_message
                }
            )

        except Exception as e:
            logger.error(f"Failed to record error in Langfuse: {e}")

    @asynccontextmanager
    async def span(
        self,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a span for tracking sub-operations"""
        if not self.enabled or not self.trace:
            yield None
            return

        span = None
        start_time = time.time()

        try:
            span = self.trace.span(
                name=name,
                input=input_data,
                metadata=metadata or {}
            )

            yield span

        except Exception as e:
            logger.error(f"Error in span {name}: {e}")
            if span:
                span.update(
                    output={"error": str(e)},
                    metadata={"error": True}
                )

        finally:
            if span:
                duration_ms = (time.time() - start_time) * 1000
                span.update(
                    metadata={
                        **(metadata or {}),
                        "duration_ms": duration_ms
                    }
                )
                span.end()

    async def trace_classification(self, result: ClassificationResult):
        """Trace classification operation with detailed metrics"""
        async with self.span(
            name="document_classification",
            input_data={"text": result.text[:1000]},
            metadata={
                "model": result.model_used,
                "taxonomy_version": result.taxonomy_version
            }
        ) as span:
            if not span:
                return

            # Update cost tracking
            cost_usd = result.cost_cents / 100.0
            self.total_cost_usd += cost_usd
            self.total_tokens += result.tokens_used

            # Record detailed classification data
            span.update(
                output={
                    "classification": result.category,
                    "confidence": result.confidence,
                    "processing_time_ms": result.latency_ms
                },
                metadata={
                    "model": result.model_used,
                    "cost_cents": result.cost_cents,
                    "tokens_used": result.tokens_used,
                    "faithfulness_score": result.faithfulness_score,
                    "rule_candidates": result.rule_candidates
                }
            )

            # Add sub-spans for rule and LLM classification
            if result.rule_candidates:
                async with self.span(
                    name="rule_classification",
                    input_data={"text": result.text[:500]},
                    metadata={"processing_time_ms": result.latency_ms - result.llm_latency_ms}
                ) as rule_span:
                    if rule_span:
                        rule_span.update(
                            output={"candidates": result.rule_candidates}
                        )

            if result.llm_latency_ms > 0:
                async with self.span(
                    name="llm_classification",
                    input_data={"candidates": result.rule_candidates or []},
                    metadata={
                        "model": result.model_used,
                        "cost_cents": result.llm_cost_cents,
                        "processing_time_ms": result.llm_latency_ms
                    }
                ) as llm_span:
                    if llm_span:
                        llm_span.update(
                            output={"final_category": result.category}
                        )

    async def trace_search_operation(
        self,
        query: str,
        search_type: str,
        results: List[Dict[str, Any]],
        latency_ms: float,
        quality_score: Optional[float] = None
    ):
        """Trace search operation"""
        async with self.span(
            name=f"search_{search_type}",
            input_data={"query": query[:500]},
            metadata={
                "search_type": search_type,
                "processing_time_ms": latency_ms
            }
        ) as span:
            if not span:
                return

            span.update(
                output={
                    "results_count": len(results),
                    "quality_score": quality_score,
                    "results": results[:5]  # Sample of results
                }
            )

    async def trace_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        usage: LLMUsageMetrics
    ):
        """Trace LLM API call with detailed usage metrics"""
        async with self.span(
            name="llm_call",
            input_data={"prompt": prompt[:1000]},
            metadata={
                "model": model,
                "cost_usd": usage.cost_usd,
                "latency_ms": usage.latency_ms
            }
        ) as span:
            if not span:
                return

            # Update total cost and tokens
            self.total_cost_usd += usage.cost_usd
            self.total_tokens += usage.total_tokens

            span.update(
                output={
                    "response": response[:1000],
                    "usage": asdict(usage)
                }
            )

    async def add_score(self, name: str, value: float, comment: Optional[str] = None):
        """Add a quality score to the current trace"""
        if not self.enabled or not self.trace:
            return

        try:
            self.trace.score(
                name=name,
                value=value,
                comment=comment
            )

        except Exception as e:
            logger.error(f"Failed to add score {name} to Langfuse trace: {e}")

    async def add_event(self, name: str, data: Dict[str, Any]):
        """Add an event to the current trace"""
        if not self.enabled or not self.trace:
            return

        try:
            # Events are tracked as metadata updates
            current_metadata = self.metadata.get("events", [])
            current_metadata.append({
                "name": name,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            })

            self.metadata["events"] = current_metadata

        except Exception as e:
            logger.error(f"Failed to add event {name} to Langfuse trace: {e}")


# Decorator for automatic LLM call tracing
def trace_llm_call(model_name: str, provider: str = "openai"):
    """Decorator for automatic LLM call tracing"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be used with an active observer
            # Implementation depends on how the function is called
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator


# Integration helper functions
async def create_langfuse_config() -> Dict[str, Any]:
    """Create Langfuse configuration from environment"""
    return {
        "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
        "secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
        "host": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        "enabled": bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
    }


async def initialize_langfuse() -> LangfuseManager:
    """Initialize Langfuse manager with environment configuration"""
    config = await create_langfuse_config()
    return LangfuseManager(
        public_key=config["public_key"],
        secret_key=config["secret_key"],
        host=config["host"]
    )