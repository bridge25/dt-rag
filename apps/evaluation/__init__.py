# @CODE:EVAL-001 | SPEC: .moai/specs/SPEC-EVAL-001/spec.md | TEST: tests/evaluation/

"""
RAGAS Evaluation System for DT-RAG v1.8.1

This module provides comprehensive RAG evaluation using the RAGAS framework:
- Context Precision: Measures relevance of retrieved contexts
- Context Recall: Measures completeness of context retrieval
- Faithfulness: Measures factual accuracy of generated responses
- Answer Relevancy: Measures how well answers address the query

Features:
- Real-time evaluation during search/generation
- Historical evaluation analytics
- Quality threshold monitoring
- A/B testing support for system improvements
"""

__version__ = "1.0.0"
__all__ = [
    "RAGASEvaluator",
    "EvaluationMetrics",
    "EvaluationResult",
    "QualityMonitor",
    "ExperimentTracker",
]
