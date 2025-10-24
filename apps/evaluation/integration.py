"""
Integration utilities for RAGAS evaluation system

Provides integration hooks and middleware for automatic evaluation:
- Search request/response interception
- Automatic evaluation triggering
- Quality monitoring integration
- Performance tracking
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .experiment_tracker import ExperimentTracker
from .models import EvaluationRequest, EvaluationResult
from .quality_monitor import QualityMonitor
from .ragas_engine import RAGASEvaluator

logger = logging.getLogger(__name__)


class RAGEvaluationMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically evaluate RAG responses"""

    def __init__(self, app, enable_evaluation: bool = True):
        super().__init__(app)
        self.enable_evaluation = enable_evaluation
        self.evaluator = RAGASEvaluator()
        self.quality_monitor = QualityMonitor()
        self.experiment_tracker = ExperimentTracker()

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only evaluate search endpoints
        if (
            self.enable_evaluation
            and request.url.path.startswith("/search")
            and request.method == "POST"
            and response.status_code == 200
        ):

            # Schedule evaluation in background
            asyncio.create_task(self._evaluate_search_response(request, response))

        return response

    async def _evaluate_search_response(self, request: Request, response: Response):
        """Evaluate search response in background"""
        try:
            # Extract query and response data
            request_body = await self._extract_request_body(request)
            response_data = await self._extract_response_data(response)

            if not request_body or not response_data:
                return

            # Create evaluation request
            eval_request = self._create_evaluation_request(
                request_body, response_data, request
            )

            if eval_request:
                # Perform evaluation
                result = await self.evaluator.evaluate_rag_response(
                    query=eval_request.query,
                    response=eval_request.response,
                    retrieved_contexts=eval_request.retrieved_contexts,
                )

                # Record for quality monitoring
                await self.quality_monitor.record_evaluation(result)

                # Record for any active experiments
                if eval_request.experiment_id:
                    user_id = self._extract_user_id(request)
                    if user_id:
                        await self.experiment_tracker.record_experiment_result(
                            eval_request.experiment_id, user_id, result
                        )

        except Exception as e:
            logger.error(f"Background evaluation failed: {e}")

    async def _extract_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract request body data"""
        try:
            # Note: This is simplified - in practice, you'd need to handle
            # request body reading more carefully
            if hasattr(request, "_body"):
                import json

                return json.loads(request._body)
        except Exception as e:
            logger.warning(f"Failed to extract request body: {e}")
        return None

    async def _extract_response_data(
        self, response: Response
    ) -> Optional[Dict[str, Any]]:
        """Extract response data"""
        try:
            # Note: This is simplified - response body extraction in middleware
            # is complex and may require custom handling
            return {}
        except Exception as e:
            logger.warning(f"Failed to extract response data: {e}")
        return None

    def _create_evaluation_request(
        self,
        request_body: Dict[str, Any],
        response_data: Dict[str, Any],
        request: Request,
    ) -> Optional[EvaluationRequest]:
        """Create evaluation request from search data"""
        try:
            query = request_body.get("q", "")
            if not query:
                return None

            # Extract search results to form response text
            hits = response_data.get("hits", [])
            if not hits:
                return None

            # Create response text from search hits
            response_text = self._synthesize_response_from_hits(hits)
            contexts = [hit.get("text", "") for hit in hits]

            # Extract session/experiment info
            session_id = request.headers.get("X-Session-ID")
            experiment_id = request.headers.get("X-Experiment-ID")

            return EvaluationRequest(
                query=query,
                response=response_text,
                retrieved_contexts=contexts,
                session_id=session_id,
                experiment_id=experiment_id,
            )

        except Exception as e:
            logger.warning(f"Failed to create evaluation request: {e}")
            return None

    def _synthesize_response_from_hits(self, hits: List[Dict[str, Any]]) -> str:
        """Synthesize response text from search hits"""
        # Simple concatenation - in practice, this would use the actual
        # response generation system
        top_hits = hits[:3]  # Use top 3 hits
        response_parts = []

        for hit in top_hits:
            text = hit.get("text", "")
            if text and len(text) > 50:
                response_parts.append(text[:200] + "...")

        return " ".join(response_parts)

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Check headers, session, JWT token, etc.
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            # Could extract from session or JWT
            user_id = f"anon_{hash(request.client.host) % 10000}"

        return user_id


class EvaluationIntegration:
    """Integration utilities for evaluation system"""

    def __init__(self):
        self.evaluator = RAGASEvaluator()
        self.quality_monitor = QualityMonitor()
        self.experiment_tracker = ExperimentTracker()

    async def evaluate_search_interaction(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        generated_response: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate a complete search interaction

        This is the main integration point for evaluating RAG responses
        outside of the middleware approach.
        """

        # Extract contexts from search results
        contexts = []
        for result in search_results[:5]:  # Top 5 results
            if "text" in result:
                contexts.append(result["text"])

        # Generate response if not provided
        if not generated_response:
            generated_response = self._generate_response_from_contexts(query, contexts)

        # Create evaluation request
        eval_request = EvaluationRequest(
            query=query,
            response=generated_response,
            retrieved_contexts=contexts,
            session_id=session_id,
            experiment_id=experiment_id,
        )

        # Perform evaluation
        result = await self.evaluator.evaluate_rag_response(
            query=eval_request.query,
            response=eval_request.response,
            retrieved_contexts=eval_request.retrieved_contexts,
        )

        # Record for quality monitoring
        await self.quality_monitor.record_evaluation(result)

        # Record for experiments if applicable
        if experiment_id and user_id:
            await self.experiment_tracker.record_experiment_result(
                experiment_id, user_id, result
            )

        return result

    def _generate_response_from_contexts(self, query: str, contexts: List[str]) -> str:
        """
        Generate response from contexts

        This is a placeholder - in practice, this would call your
        actual response generation system.
        """
        if not contexts:
            return "I don't have enough information to answer that question."

        # Simple extractive approach
        relevant_sentences = []
        query_words = set(query.lower().split())

        for context in contexts:
            sentences = context.split(". ")
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words.intersection(sentence_words))
                if overlap >= 2:  # At least 2 word overlap
                    relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            return ". ".join(relevant_sentences[:3]) + "."
        else:
            return contexts[0][:200] + "..."

    async def setup_quality_monitoring(
        self,
        faithfulness_threshold: float = 0.85,
        precision_threshold: float = 0.75,
        recall_threshold: float = 0.70,
        relevancy_threshold: float = 0.80,
    ):
        """Setup quality monitoring with custom thresholds"""
        from .models import QualityThresholds

        thresholds = QualityThresholds(
            faithfulness_min=faithfulness_threshold,
            context_precision_min=precision_threshold,
            context_recall_min=recall_threshold,
            answer_relevancy_min=relevancy_threshold,
        )

        await self.quality_monitor.update_thresholds(thresholds)

    async def start_ab_test(
        self,
        experiment_name: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        target_sample_size: int = 200,
    ) -> str:
        """Start A/B testing experiment"""
        from .models import ExperimentConfig

        config = ExperimentConfig(
            experiment_id=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=experiment_name,
            control_config=control_config,
            treatment_config=treatment_config,
            minimum_sample_size=target_sample_size,
        )

        experiment_id = await self.experiment_tracker.create_experiment(config)
        await self.experiment_tracker.start_experiment(experiment_id)

        return experiment_id

    async def get_quality_summary(self) -> Dict[str, Any]:
        """Get current quality monitoring summary"""
        return await self.quality_monitor.get_quality_status()

    async def get_experiment_results(
        self, experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get experiment results"""
        results = await self.experiment_tracker.analyze_experiment_results(
            experiment_id
        )
        return results.dict() if results else None


# Global integration instance
evaluation_integration = EvaluationIntegration()


def get_evaluation_integration() -> EvaluationIntegration:
    """Get global evaluation integration instance"""
    return evaluation_integration


# Utility functions for common integration patterns


async def evaluate_rag_response(
    query: str,
    response: str,
    contexts: List[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> EvaluationResult:
    """
    Quick evaluation function for immediate use

    This is a convenience function for one-off evaluations.
    """
    return await evaluation_integration.evaluator.evaluate_rag_response(
        query=query, response=response, retrieved_contexts=contexts
    )


async def check_quality_gates(
    evaluation_result: EvaluationResult, thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, bool]:
    """
    Check if evaluation result passes quality gates

    Returns dict of gate_name -> passed status
    """
    if not thresholds:
        thresholds = {
            "faithfulness": 0.85,
            "context_precision": 0.75,
            "context_recall": 0.70,
            "answer_relevancy": 0.80,
        }

    metrics = evaluation_result.metrics
    gates = {}

    gates["faithfulness"] = (metrics.faithfulness or 0) >= thresholds["faithfulness"]
    gates["context_precision"] = (metrics.context_precision or 0) >= thresholds[
        "context_precision"
    ]
    gates["context_recall"] = (metrics.context_recall or 0) >= thresholds[
        "context_recall"
    ]
    gates["answer_relevancy"] = (metrics.answer_relevancy or 0) >= thresholds[
        "answer_relevancy"
    ]

    return gates


def should_record_evaluation(request: Request) -> bool:
    """
    Determine if a request should trigger evaluation

    Use this for conditional evaluation to avoid overhead.
    """
    # Skip evaluation for health checks, monitoring, etc.
    if request.url.path in ["/health", "/status", "/metrics"]:
        return False

    # Skip for internal requests
    user_agent = request.headers.get("user-agent", "").lower()
    if any(bot in user_agent for bot in ["bot", "crawler", "spider", "monitor"]):
        return False

    # Sample evaluation (e.g., 10% of requests)
    return hash(str(request.url) + str(datetime.now().minute)) % 10 == 0


async def run_evaluation_batch(
    evaluation_requests: List[EvaluationRequest], max_concurrent: int = 5
) -> List[EvaluationResult]:
    """
    Run batch evaluation with concurrency control

    Useful for processing multiple evaluations efficiently.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def evaluate_one(request: EvaluationRequest) -> EvaluationResult:
        async with semaphore:
            return await evaluation_integration.evaluator.evaluate_rag_response(
                query=request.query,
                response=request.response,
                retrieved_contexts=request.retrieved_contexts,
                ground_truth=request.ground_truth,
            )

    # Run evaluations concurrently
    tasks = [evaluate_one(req) for req in evaluation_requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and return valid results
    valid_results = [r for r in results if isinstance(r, EvaluationResult)]

    return valid_results
