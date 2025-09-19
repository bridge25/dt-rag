"""
Dynamic Taxonomy RAG v1.8.1 - Classification Pipeline
=====================================================

3-stage hybrid classification system with HITL workflow:
- Rule-based classification (fast filtering)
- LLM-based classification (high accuracy)
- Human-in-the-loop validation (quality assurance)

Components:
- RuleBasedClassifier: Pattern matching and heuristics
- LLMClassifier: GPT-4/Claude API integration
- ConfidenceScorer: Multi-signal confidence calculation
- HITLQueue: Human validation workflow
- ClassificationPipeline: Unified orchestration
"""

from .rule_classifier import RuleBasedClassifier
from .llm_classifier import LLMClassifier
from .confidence_scorer import ConfidenceScorer
from .hitl_queue import HITLQueue, HITLManager
from .classification_pipeline import ClassificationPipeline, ClassificationResult

__all__ = [
    'RuleBasedClassifier',
    'LLMClassifier',
    'ConfidenceScorer',
    'HITLQueue',
    'HITLManager',
    'ClassificationPipeline',
    'ClassificationResult'
]

__version__ = "1.8.1"