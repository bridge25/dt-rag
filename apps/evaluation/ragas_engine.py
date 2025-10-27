# @CODE:MYPY-001:PHASE2:BATCH2
"""
RAGAS evaluation engine implementation

Provides comprehensive RAG evaluation using RAGAS framework metrics:
- Context Precision: Relevance of retrieved contexts to the query
- Context Recall: Coverage of necessary context for answering the query
- Faithfulness: Factual consistency between answer and retrieved contexts
- Answer Relevancy: How well the answer addresses the user's query

Uses LLM-based evaluation with Gemini API for accurate assessment.
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
import numpy as np

from .models import EvaluationMetrics, EvaluationResult, QualityThresholds

logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class ContextAnalysis:
    """Analysis of a single context chunk"""

    chunk_id: str
    text: str
    relevance_score: float
    importance_score: float
    factual_claims: List[str]
    supports_answer: bool


class RAGASEvaluator:
    """RAGAS evaluation engine with Gemini-powered assessments"""

    def __init__(self) -> None:
        self.model = None
        if GEMINI_API_KEY:
            try:
                self.model = genai.GenerativeModel("gemini-pro")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini model: {e}")

        # Quality thresholds
        self.thresholds = QualityThresholds(
            faithfulness_min=0.85,
            context_precision_min=0.75,
            context_recall_min=0.70,
            answer_relevancy_min=0.80,
            response_time_max=5.0,
        )

    async def evaluate_rag_response(
        self,
        query: str,
        response: str,
        retrieved_contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Comprehensive RAGAS evaluation of a RAG response

        Args:
            query: User query
            response: Generated response
            retrieved_contexts: List of retrieved context chunks
            ground_truth: Expected correct answer (optional)

        Returns:
            EvaluationResult with all RAGAS metrics and analysis
        """
        evaluation_id = (
            f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}"
        )

        try:
            # Run all RAGAS evaluations concurrently
            results = await asyncio.gather(
                self._evaluate_context_precision(query, retrieved_contexts),
                self._evaluate_context_recall(
                    query, response, retrieved_contexts, ground_truth
                ),
                self._evaluate_faithfulness(response, retrieved_contexts),
                self._evaluate_answer_relevancy(query, response),
                return_exceptions=True,
            )

            # Parse results - ensure all values are float, not Exception
            context_precision: Optional[float] = None
            if not isinstance(results[0], Exception) and isinstance(results[0], float):
                context_precision = results[0]

            context_recall: Optional[float] = None
            if not isinstance(results[1], Exception) and isinstance(results[1], float):
                context_recall = results[1]

            faithfulness: Optional[float] = None
            if not isinstance(results[2], Exception) and isinstance(results[2], float):
                faithfulness = results[2]

            answer_relevancy: Optional[float] = None
            if not isinstance(results[3], Exception) and isinstance(results[3], float):
                answer_relevancy = results[3]

            # Create metrics object
            metrics = EvaluationMetrics(
                context_precision=context_precision,
                context_recall=context_recall,
                faithfulness=faithfulness,
                answer_relevancy=answer_relevancy,
                response_time=0.0,  # Placeholder, should be measured separately
                retrieval_score=0.0,  # Placeholder, should be provided by retrieval system
            )

            # Generate quality flags and recommendations
            quality_flags = self._generate_quality_flags(metrics)
            recommendations = self._generate_recommendations(metrics, quality_flags)

            # Detailed analysis
            detailed_analysis = {
                "query_analysis": self._analyze_query_complexity(query),
                "context_analysis": [
                    self._analyze_context_chunk(ctx, i)
                    for i, ctx in enumerate(retrieved_contexts)
                ],
                "response_analysis": self._analyze_response_quality(response),
                "overall_assessment": self._generate_overall_assessment(metrics),
            }

            return EvaluationResult(
                evaluation_id=evaluation_id,
                query=query,
                metrics=metrics,
                quality_flags=quality_flags,
                recommendations=recommendations,
                timestamp=datetime.now(),
                detailed_analysis=detailed_analysis,
            )

        except Exception as e:
            logger.error(f"RAGAS evaluation failed for query '{query[:50]}...': {e}")

            # Return fallback evaluation
            return EvaluationResult(
                evaluation_id=evaluation_id,
                query=query,
                metrics=EvaluationMetrics(
                    context_precision=None,
                    context_recall=None,
                    faithfulness=None,
                    answer_relevancy=None,
                    response_time=0.0,
                    retrieval_score=0.0,
                ),
                quality_flags=["evaluation_error"],
                recommendations=["Manual review required due to evaluation error"],
                timestamp=datetime.now(),
                detailed_analysis={"error": str(e)},
            )

    async def _evaluate_context_precision(
        self, query: str, contexts: List[str]
    ) -> float:
        """
        Evaluate Context Precision: What proportion of retrieved contexts are relevant to the query?

        Context Precision = (Number of relevant contexts) / (Total retrieved contexts)
        """
        if not contexts:
            return 0.0

        try:
            if self.model:
                # LLM-based evaluation
                relevant_count = 0
                for context in contexts:
                    is_relevant = await self._is_context_relevant_to_query(
                        query, context
                    )
                    if is_relevant:
                        relevant_count += 1

                return relevant_count / len(contexts)
            else:
                # Fallback: keyword-based relevance
                return self._calculate_keyword_based_precision(query, contexts)

        except Exception as e:
            logger.error(f"Context precision evaluation failed: {e}")
            return 0.0

    async def _evaluate_context_recall(
        self,
        query: str,
        response: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> float:
        """
        Evaluate Context Recall: What proportion of necessary information for answering
        the query is present in the retrieved contexts?
        """
        if not contexts:
            return 0.0

        try:
            if self.model and ground_truth:
                # LLM-based evaluation with ground truth
                return await self._llm_based_context_recall(
                    query, contexts, ground_truth
                )
            elif self.model:
                # LLM-based evaluation using response
                return await self._llm_based_context_recall_from_response(
                    query, response, contexts
                )
            else:
                # Fallback: overlap-based recall
                return self._calculate_overlap_based_recall(query, response, contexts)

        except Exception as e:
            logger.error(f"Context recall evaluation failed: {e}")
            return 0.0

    async def _evaluate_faithfulness(self, response: str, contexts: List[str]) -> float:
        """
        Evaluate Faithfulness: Are the claims in the response supported by the retrieved contexts?

        Faithfulness = (Number of claims supported by context) / (Total claims in response)
        """
        if not response or not contexts:
            return 0.0

        try:
            if self.model:
                return await self._llm_based_faithfulness(response, contexts)
            else:
                # Fallback: fact extraction and verification
                return self._calculate_fact_based_faithfulness(response, contexts)

        except Exception as e:
            logger.error(f"Faithfulness evaluation failed: {e}")
            return 0.0

    async def _evaluate_answer_relevancy(self, query: str, response: str) -> float:
        """
        Evaluate Answer Relevancy: How relevant is the response to the user's query?
        """
        if not query or not response:
            return 0.0

        try:
            if self.model:
                return await self._llm_based_answer_relevancy(query, response)
            else:
                # Fallback: semantic overlap
                return self._calculate_semantic_overlap_relevancy(query, response)

        except Exception as e:
            logger.error(f"Answer relevancy evaluation failed: {e}")
            return 0.0

    async def _is_context_relevant_to_query(self, query: str, context: str) -> bool:
        """Check if a context is relevant to the query using LLM"""
        if not self.model:
            return False

        prompt = f"""
        Evaluate if the given context is relevant to answering the user's query.

        Query: {query}

        Context: {context}

        Instructions:
        - Return "RELEVANT" if the context contains information that could help answer the query
        - Return "NOT_RELEVANT" if the context is unrelated or doesn't provide useful information
        - Consider partial relevance as RELEVANT

        Response (RELEVANT or NOT_RELEVANT):
        """

        try:
            result = await self._generate_text(prompt)
            return "RELEVANT" in result.upper()
        except:
            return False

    async def _llm_based_context_recall(
        self, query: str, contexts: List[str], ground_truth: str
    ) -> float:
        """Evaluate context recall using ground truth"""
        prompt = f"""
        Evaluate how well the retrieved contexts cover the necessary information to answer the query correctly.

        Query: {query}

        Ground Truth Answer: {ground_truth}

        Retrieved Contexts:
        {chr(10).join(f"{i+1}. {ctx}" for i, ctx in enumerate(contexts))}

        Instructions:
        - Identify key information points needed to provide the ground truth answer
        - Check what percentage of these key points are covered by the retrieved contexts
        - Return a score from 0.0 to 1.0

        Response format: {{
            "coverage_score": 0.X,
            "missing_information": ["point 1", "point 2"],
            "covered_information": ["point 1", "point 2"]
        }}
        """

        try:
            result = await self._generate_text(prompt)
            # Parse JSON response
            import json

            parsed = json.loads(result.strip())
            score: float = parsed.get("coverage_score", 0.0)
            return min(1.0, max(0.0, score))
        except:
            return 0.0

    async def _llm_based_context_recall_from_response(
        self, query: str, response: str, contexts: List[str]
    ) -> float:
        """Evaluate context recall using the generated response"""
        prompt = f"""
        Evaluate how well the retrieved contexts support the information provided in the response.

        Query: {query}

        Generated Response: {response}

        Retrieved Contexts:
        {chr(10).join(f"{i+1}. {ctx}" for i, ctx in enumerate(contexts))}

        Instructions:
        - Identify key information points mentioned in the response
        - Check what percentage of these points are supported by the retrieved contexts
        - Return a score from 0.0 to 1.0

        Response format: {{
            "coverage_score": 0.X,
            "supported_claims": ["claim 1", "claim 2"],
            "unsupported_claims": ["claim 1", "claim 2"]
        }}
        """

        try:
            result = await self._generate_text(prompt)
            import json

            parsed = json.loads(result.strip())
            score: float = parsed.get("coverage_score", 0.0)
            return min(1.0, max(0.0, score))
        except:
            return 0.0

    async def _llm_based_faithfulness(
        self, response: str, contexts: List[str]
    ) -> float:
        """Evaluate faithfulness using LLM to verify claims"""
        prompt = f"""
        Evaluate the factual consistency of the response with the provided contexts.

        Response to verify: {response}

        Supporting Contexts:
        {chr(10).join(f"{i+1}. {ctx}" for i, ctx in enumerate(contexts))}

        Instructions:
        - Identify all factual claims in the response
        - For each claim, check if it's supported by the contexts
        - Calculate the percentage of claims that are supported
        - Return a score from 0.0 to 1.0

        Response format: {{
            "faithfulness_score": 0.X,
            "total_claims": N,
            "supported_claims": M,
            "unsupported_claims": ["claim 1", "claim 2"]
        }}
        """

        try:
            result = await self._generate_text(prompt)
            import json

            parsed = json.loads(result.strip())
            score: float = parsed.get("faithfulness_score", 0.0)
            return min(1.0, max(0.0, score))
        except:
            return 0.0

    async def _llm_based_answer_relevancy(self, query: str, response: str) -> float:
        """Evaluate answer relevancy using LLM"""
        prompt = f"""
        Evaluate how well the response addresses the user's query.

        User Query: {query}

        Response: {response}

        Instructions:
        - Check if the response directly addresses the query
        - Consider completeness, accuracy, and specificity
        - Return a relevancy score from 0.0 to 1.0

        Response format: {{
            "relevancy_score": 0.X,
            "addresses_query": true/false,
            "completeness": "partial/complete",
            "issues": ["issue 1", "issue 2"]
        }}
        """

        try:
            result = await self._generate_text(prompt)
            import json

            parsed = json.loads(result.strip())
            score: float = parsed.get("relevancy_score", 0.0)
            return min(1.0, max(0.0, score))
        except:
            return 0.0

    async def _generate_text(self, prompt: str) -> str:
        """Generate text using Gemini model"""
        if not self.model:
            return ""

        try:
            response = self.model.generate_content(prompt)
            return str(response.text)  # Explicit cast to str
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return ""

    def _calculate_keyword_based_precision(
        self, query: str, contexts: List[str]
    ) -> float:
        """Fallback precision calculation using keyword overlap"""
        query_words = set(query.lower().split())
        relevant_contexts = 0

        for context in contexts:
            context_words = set(context.lower().split())
            overlap = len(query_words.intersection(context_words))
            if overlap > 0:
                relevant_contexts += 1

        return relevant_contexts / len(contexts) if contexts else 0.0

    def _calculate_overlap_based_recall(
        self, query: str, response: str, contexts: List[str]
    ) -> float:
        """Fallback recall calculation using text overlap"""
        response_words = set(response.lower().split())
        context_words = set()

        for context in contexts:
            context_words.update(context.lower().split())

        overlap = len(response_words.intersection(context_words))
        return overlap / len(response_words) if response_words else 0.0

    def _calculate_fact_based_faithfulness(
        self, response: str, contexts: List[str]
    ) -> float:
        """Fallback faithfulness calculation using simple fact extraction"""
        # Extract sentences as potential claims
        sentences = re.split(r"[.!?]+", response)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 1.0

        supported_claims = 0
        combined_context = " ".join(contexts).lower()

        for sentence in sentences:
            # Simple check: if key words from the sentence appear in contexts
            sentence_words = set(sentence.lower().split())
            if len(sentence_words) > 2:  # Skip very short sentences
                context_matches = sum(
                    1 for word in sentence_words if word in combined_context
                )
                if context_matches >= len(sentence_words) * 0.5:  # 50% word overlap
                    supported_claims += 1

        return supported_claims / len(sentences)

    def _calculate_semantic_overlap_relevancy(self, query: str, response: str) -> float:
        """Fallback relevancy calculation using semantic overlap"""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(response_words))
        return overlap / len(query_words)

    def _generate_quality_flags(self, metrics: EvaluationMetrics) -> List[str]:
        """Generate quality flags based on metrics"""
        flags = []

        if (
            metrics.faithfulness is not None
            and metrics.faithfulness < self.thresholds.faithfulness_min
        ):
            flags.append("low_faithfulness")

        if (
            metrics.context_precision is not None
            and metrics.context_precision < self.thresholds.context_precision_min
        ):
            flags.append("low_precision")

        if (
            metrics.context_recall is not None
            and metrics.context_recall < self.thresholds.context_recall_min
        ):
            flags.append("low_recall")

        if (
            metrics.answer_relevancy is not None
            and metrics.answer_relevancy < self.thresholds.answer_relevancy_min
        ):
            flags.append("low_relevancy")

        return flags

    def _generate_recommendations(
        self, metrics: EvaluationMetrics, quality_flags: List[str]
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if "low_faithfulness" in quality_flags:
            recommendations.append("Improve fact verification in response generation")
            recommendations.append("Use stricter grounding techniques")

        if "low_precision" in quality_flags:
            recommendations.append(
                "Improve retrieval ranking to prioritize relevant contexts"
            )
            recommendations.append("Consider reducing the number of retrieved contexts")

        if "low_recall" in quality_flags:
            recommendations.append("Increase the number of retrieved contexts")
            recommendations.append("Improve query expansion or semantic search")

        if "low_relevancy" in quality_flags:
            recommendations.append(
                "Improve response generation to better address the query"
            )
            recommendations.append("Consider query intent classification")

        return recommendations

    def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and characteristics"""
        words = query.split()

        return {
            "length": len(query),
            "word_count": len(words),
            "has_question_words": any(
                word.lower() in ["what", "why", "how", "when", "where", "who"]
                for word in words
            ),
            "complexity": (
                "simple"
                if len(words) < 5
                else "medium" if len(words) < 12 else "complex"
            ),
        }

    def _analyze_context_chunk(self, context: str, index: int) -> Dict[str, Any]:
        """Analyze individual context chunk"""
        return {
            "chunk_index": index,
            "length": len(context),
            "word_count": len(context.split()),
            "has_numerical_data": bool(re.search(r"\d+", context)),
            "estimated_relevance": min(
                1.0, len(context.split()) / 100
            ),  # Simple heuristic
        }

    def _analyze_response_quality(self, response: str) -> Dict[str, Any]:
        """Analyze response quality characteristics"""
        sentences = re.split(r"[.!?]+", response)
        sentences = [s.strip() for s in sentences if s.strip()]

        return {
            "length": len(response),
            "word_count": len(response.split()),
            "sentence_count": len(sentences),
            "avg_sentence_length": len(response) / max(1, len(sentences)),
            "has_specific_info": bool(
                re.search(r"\d+|[A-Z][a-z]+ [A-Z][a-z]+", response)
            ),  # Numbers or proper nouns
        }

    def _generate_overall_assessment(
        self, metrics: EvaluationMetrics
    ) -> Dict[str, Any]:
        """Generate overall assessment of the RAG response"""
        scores = [
            metrics.context_precision or 0.0,
            metrics.context_recall or 0.0,
            metrics.faithfulness or 0.0,
            metrics.answer_relevancy or 0.0,
        ]

        avg_score = sum(scores) / len(scores)

        if avg_score >= 0.9:
            quality = "excellent"
        elif avg_score >= 0.8:
            quality = "good"
        elif avg_score >= 0.7:
            quality = "fair"
        else:
            quality = "poor"

        return {
            "overall_score": avg_score,
            "quality_rating": quality,
            "strengths": self._identify_strengths(metrics),
            "weaknesses": self._identify_weaknesses(metrics),
        }

    def _identify_strengths(self, metrics: EvaluationMetrics) -> List[str]:
        """Identify strengths based on metrics"""
        strengths = []

        if metrics.faithfulness and metrics.faithfulness >= 0.9:
            strengths.append("High factual accuracy")
        if metrics.answer_relevancy and metrics.answer_relevancy >= 0.85:
            strengths.append("Highly relevant response")
        if metrics.context_precision and metrics.context_precision >= 0.8:
            strengths.append("Good context relevance")
        if metrics.context_recall and metrics.context_recall >= 0.8:
            strengths.append("Comprehensive information coverage")

        return strengths

    def _identify_weaknesses(self, metrics: EvaluationMetrics) -> List[str]:
        """Identify weaknesses based on metrics"""
        weaknesses = []

        if metrics.faithfulness and metrics.faithfulness < 0.7:
            weaknesses.append("Low factual accuracy")
        if metrics.answer_relevancy and metrics.answer_relevancy < 0.7:
            weaknesses.append("Response not well-targeted to query")
        if metrics.context_precision and metrics.context_precision < 0.6:
            weaknesses.append("Many irrelevant contexts retrieved")
        if metrics.context_recall and metrics.context_recall < 0.6:
            weaknesses.append("Incomplete information coverage")

        return weaknesses
