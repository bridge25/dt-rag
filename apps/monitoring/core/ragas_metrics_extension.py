"""
RAGAS Metrics Extension for MetricsCollector

Extends the existing MetricsCollector with RAGAS-specific evaluation metrics
for comprehensive RAG system quality monitoring.
"""

import logging
from typing import Any, Dict, Optional

try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Use same mock classes as in metrics_collector.py
    class Counter:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def inc(self, *args, **kwargs) -> None:
            pass

        def labels(self, *args, **kwargs) -> None:
            return self

    class Gauge:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def set(self, *args, **kwargs) -> None:
            pass

        def labels(self, *args, **kwargs) -> None:
            return self

    class Histogram:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def observe(self, *args, **kwargs) -> None:
            pass

        def labels(self, *args, **kwargs) -> None:
            return self


logger = logging.getLogger(__name__)


class RAGASMetricsExtension:
    """
    Extension class for RAGAS evaluation metrics

    Adds comprehensive RAGAS metrics to the existing MetricsCollector
    including faithfulness, relevancy, precision, recall, and quality gates.
    """

    def __init__(self, registry: Optional[Any]=None) -> None:
        self.registry = registry
        self.enabled = PROMETHEUS_AVAILABLE and registry is not None

        if not self.enabled:
            logger.warning(
                "RAGAS metrics extension disabled - Prometheus not available or no registry"
            )
            return

        self._initialize_ragas_metrics()
        logger.info("RAGAS metrics extension initialized")

    def _initialize_ragas_metrics(self) -> None:
        """Initialize all RAGAS-specific Prometheus metrics"""

        # Core RAGAS Metrics
        self.ragas_faithfulness_score = Gauge(
            "dt_rag_ragas_faithfulness_score",
            "RAGAS faithfulness metric - measures answer grounding in context",
            registry=self.registry,
        )

        self.ragas_answer_relevancy_score = Gauge(
            "dt_rag_ragas_answer_relevancy_score",
            "RAGAS answer relevancy metric - measures answer relevance to question",
            registry=self.registry,
        )

        self.ragas_context_precision_score = Gauge(
            "dt_rag_ragas_context_precision_score",
            "RAGAS context precision metric - measures retrieval precision",
            registry=self.registry,
        )

        self.ragas_context_recall_score = Gauge(
            "dt_rag_ragas_context_recall_score",
            "RAGAS context recall metric - measures retrieval coverage",
            registry=self.registry,
        )

        self.ragas_overall_score = Gauge(
            "dt_rag_ragas_overall_score",
            "RAGAS overall weighted evaluation score",
            registry=self.registry,
        )

        # RAGAS Evaluation Operations
        self.ragas_evaluations_total = Counter(
            "dt_rag_ragas_evaluations_total",
            "Total number of RAGAS evaluations performed",
            ["evaluation_type", "quality_gate_status"],
            registry=self.registry,
        )

        self.ragas_evaluation_duration_seconds = Histogram(
            "dt_rag_ragas_evaluation_duration_seconds",
            "Duration of RAGAS evaluations in seconds",
            ["evaluation_type"],
            registry=self.registry,
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
        )

        # Quality Gates Status
        self.quality_gate_status = Gauge(
            "dt_rag_quality_gate_status",
            "Quality gate pass/fail status (1=passing, 0=failing)",
            ["metric_name"],
            registry=self.registry,
        )

        self.quality_gate_threshold = Gauge(
            "dt_rag_quality_gate_threshold",
            "Quality gate threshold values",
            ["metric_name"],
            registry=self.registry,
        )

        self.quality_gate_gap = Gauge(
            "dt_rag_quality_gate_gap",
            "Gap between current score and threshold (negative = passing)",
            ["metric_name"],
            registry=self.registry,
        )

        # Taxonomy-specific RAGAS metrics
        self.taxonomy_classification_accuracy = Gauge(
            "dt_rag_taxonomy_classification_accuracy",
            "Taxonomy classification accuracy score",
            registry=self.registry,
        )

        self.taxonomy_consistency_score = Gauge(
            "dt_rag_taxonomy_consistency_score",
            "Taxonomy consistency score across retrieved documents",
            registry=self.registry,
        )

        self.taxonomy_path_precision = Gauge(
            "dt_rag_taxonomy_path_precision",
            "Precision of taxonomy path assignments",
            registry=self.registry,
        )

        self.hierarchical_coherence_score = Gauge(
            "dt_rag_hierarchical_coherence_score",
            "Hierarchical coherence of taxonomy assignments",
            registry=self.registry,
        )

        # RAGAS Distribution Metrics
        self.ragas_score_distribution = Histogram(
            "dt_rag_ragas_score_distribution",
            "Distribution of RAGAS scores for monitoring quality patterns",
            ["metric_name"],
            registry=self.registry,
            buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0),
        )

        # Batch Evaluation Metrics
        self.batch_evaluation_size = Histogram(
            "dt_rag_batch_evaluation_size",
            "Size of batch evaluations",
            registry=self.registry,
            buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000),
        )

        self.batch_evaluation_progress = Gauge(
            "dt_rag_batch_evaluation_progress",
            "Progress of currently running batch evaluations",
            ["batch_id", "status"],
            registry=self.registry,
        )

        # Evaluation Success Rate
        self.evaluation_success_rate = Gauge(
            "dt_rag_evaluation_success_rate",
            "Success rate of evaluations over time window",
            registry=self.registry,
        )

    def record_evaluation_metrics(
        self,
        metrics: Dict[str, float],
        evaluation_type: str = "single",
        duration_seconds: Optional[float] = None,
        quality_gates_passed: bool = False,
    ) -> None:
        """
        Record RAGAS evaluation metrics

        Args:
            metrics: Dictionary of RAGAS metric scores
            evaluation_type: Type of evaluation (single, batch, golden_dataset)
            duration_seconds: Evaluation duration if available
            quality_gates_passed: Whether quality gates passed
        """
        if not self.enabled:
            return

        try:
            # Record core RAGAS metrics
            if "faithfulness" in metrics:
                score = metrics["faithfulness"]
                self.ragas_faithfulness_score.set(score)
                self.ragas_score_distribution.labels(
                    metric_name="faithfulness"
                ).observe(score)

            if "answer_relevancy" in metrics:
                score = metrics["answer_relevancy"]
                self.ragas_answer_relevancy_score.set(score)
                self.ragas_score_distribution.labels(
                    metric_name="answer_relevancy"
                ).observe(score)

            if "context_precision" in metrics:
                score = metrics["context_precision"]
                self.ragas_context_precision_score.set(score)
                self.ragas_score_distribution.labels(
                    metric_name="context_precision"
                ).observe(score)

            if "context_recall" in metrics:
                score = metrics["context_recall"]
                self.ragas_context_recall_score.set(score)
                self.ragas_score_distribution.labels(
                    metric_name="context_recall"
                ).observe(score)

            # Calculate and record overall score
            ragas_scores = [
                metrics.get(m, 0.0)
                for m in [
                    "faithfulness",
                    "answer_relevancy",
                    "context_precision",
                    "context_recall",
                ]
            ]
            if any(score > 0 for score in ragas_scores):
                overall_score = sum(ragas_scores) / len(
                    [s for s in ragas_scores if s > 0]
                )
                self.ragas_overall_score.set(overall_score)

            # Record taxonomy-specific metrics
            if "classification_accuracy" in metrics:
                self.taxonomy_classification_accuracy.set(
                    metrics["classification_accuracy"]
                )

            if "taxonomy_consistency" in metrics:
                self.taxonomy_consistency_score.set(metrics["taxonomy_consistency"])

            if "path_precision" in metrics:
                self.taxonomy_path_precision.set(metrics["path_precision"])

            if "hierarchical_coherence" in metrics:
                self.hierarchical_coherence_score.set(metrics["hierarchical_coherence"])

            # Record evaluation operation
            gate_status = "passing" if quality_gates_passed else "failing"
            self.ragas_evaluations_total.labels(
                evaluation_type=evaluation_type, quality_gate_status=gate_status
            ).inc()

            # Record duration if provided
            if duration_seconds is not None:
                self.ragas_evaluation_duration_seconds.labels(
                    evaluation_type=evaluation_type
                ).observe(duration_seconds)

            logger.debug(f"Recorded RAGAS metrics: {metrics}")

        except Exception as e:
            logger.error(f"Failed to record RAGAS metrics: {e}")

    def update_quality_gates_status(self, quality_gates: Dict[str, Dict[str, float]]) -> None:
        """
        Update quality gates status metrics

        Args:
            quality_gates: Dict with metric_name -> {threshold, current_value, status, gap}
        """
        if not self.enabled:
            return

        try:
            for metric_name, gate_data in quality_gates.items():
                # Set status (1 for passing, 0 for failing)
                status_value = 1.0 if gate_data.get("status") == "passing" else 0.0
                self.quality_gate_status.labels(metric_name=metric_name).set(
                    status_value
                )

                # Set threshold
                if "threshold" in gate_data:
                    self.quality_gate_threshold.labels(metric_name=metric_name).set(
                        gate_data["threshold"]
                    )

                # Set gap (negative = passing, positive = failing)
                if "gap" in gate_data:
                    self.quality_gate_gap.labels(metric_name=metric_name).set(
                        gate_data["gap"]
                    )

            logger.debug(
                f"Updated quality gates status for {len(quality_gates)} metrics"
            )

        except Exception as e:
            logger.error(f"Failed to update quality gates status: {e}")

    def record_batch_evaluation_progress(
        self, batch_id: str, total_queries: int, completed_queries: int, status: str
    ) -> None:
        """
        Record batch evaluation progress

        Args:
            batch_id: Unique batch identifier
            total_queries: Total number of queries in batch
            completed_queries: Number of completed queries
            status: Current batch status (running, completed, failed)
        """
        if not self.enabled:
            return

        try:
            # Record batch size
            self.batch_evaluation_size.observe(total_queries)

            # Record progress
            progress = completed_queries / total_queries if total_queries > 0 else 0.0
            self.batch_evaluation_progress.labels(batch_id=batch_id, status=status).set(
                progress
            )

            logger.debug(
                f"Updated batch {batch_id} progress: {completed_queries}/{total_queries} ({status})"
            )

        except Exception as e:
            logger.error(f"Failed to record batch evaluation progress: {e}")

    def update_evaluation_success_rate(self, success_rate: float) -> None:
        """
        Update overall evaluation success rate

        Args:
            success_rate: Success rate as a float between 0.0 and 1.0
        """
        if not self.enabled:
            return

        try:
            self.evaluation_success_rate.set(success_rate)
            logger.debug(f"Updated evaluation success rate: {success_rate:.3f}")

        except Exception as e:
            logger.error(f"Failed to update evaluation success rate: {e}")

    def get_ragas_summary(self) -> Dict[str, Any]:
        """
        Get summary of current RAGAS metrics

        Returns:
            Dictionary with current RAGAS metric values
        """
        if not self.enabled:
            return {"error": "RAGAS metrics not available"}

        try:
            return {
                "ragas_metrics": {
                    "faithfulness": (
                        self.ragas_faithfulness_score._value._value
                        if hasattr(self.ragas_faithfulness_score, "_value")
                        else 0.0
                    ),
                    "answer_relevancy": (
                        self.ragas_answer_relevancy_score._value._value
                        if hasattr(self.ragas_answer_relevancy_score, "_value")
                        else 0.0
                    ),
                    "context_precision": (
                        self.ragas_context_precision_score._value._value
                        if hasattr(self.ragas_context_precision_score, "_value")
                        else 0.0
                    ),
                    "context_recall": (
                        self.ragas_context_recall_score._value._value
                        if hasattr(self.ragas_context_recall_score, "_value")
                        else 0.0
                    ),
                    "overall_score": (
                        self.ragas_overall_score._value._value
                        if hasattr(self.ragas_overall_score, "_value")
                        else 0.0
                    ),
                },
                "taxonomy_metrics": {
                    "classification_accuracy": (
                        self.taxonomy_classification_accuracy._value._value
                        if hasattr(self.taxonomy_classification_accuracy, "_value")
                        else 0.0
                    ),
                    "consistency_score": (
                        self.taxonomy_consistency_score._value._value
                        if hasattr(self.taxonomy_consistency_score, "_value")
                        else 0.0
                    ),
                    "path_precision": (
                        self.taxonomy_path_precision._value._value
                        if hasattr(self.taxonomy_path_precision, "_value")
                        else 0.0
                    ),
                    "hierarchical_coherence": (
                        self.hierarchical_coherence_score._value._value
                        if hasattr(self.hierarchical_coherence_score, "_value")
                        else 0.0
                    ),
                },
                "success_rate": (
                    self.evaluation_success_rate._value._value
                    if hasattr(self.evaluation_success_rate, "_value")
                    else 0.0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get RAGAS summary: {e}")
            return {"error": f"Failed to get summary: {e}"}


def extend_metrics_collector(metrics_collector: Any) -> None:
    """
    Extend an existing MetricsCollector with RAGAS metrics

    Args:
        metrics_collector: Existing MetricsCollector instance

    Returns:
        RAGASMetricsExtension instance attached to the collector
    """
    if not hasattr(metrics_collector, "registry"):
        logger.warning(
            "MetricsCollector does not have a registry - RAGAS extension disabled"
        )
        return RAGASMetricsExtension(registry=None)

    ragas_extension = RAGASMetricsExtension(registry=metrics_collector.registry)

    # Attach to the original collector for easy access
    metrics_collector.ragas_extension = ragas_extension

    # Add convenience methods to the original collector
    metrics_collector.record_evaluation_metrics = (
        ragas_extension.record_evaluation_metrics
    )
    metrics_collector.update_quality_gates_status = (
        ragas_extension.update_quality_gates_status
    )
    metrics_collector.record_batch_evaluation_progress = (
        ragas_extension.record_batch_evaluation_progress
    )
    metrics_collector.update_evaluation_success_rate = (
        ragas_extension.update_evaluation_success_rate
    )
    metrics_collector.get_ragas_summary = ragas_extension.get_ragas_summary

    logger.info("Successfully extended MetricsCollector with RAGAS metrics")
    return ragas_extension
