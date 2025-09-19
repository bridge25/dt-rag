"""
RAGAS Evaluation Engine Implementation

Implements comprehensive RAGAS evaluation framework including:
- Faithfulness: Answer consistency with retrieved context
- Answer Relevancy: Answer relevance to the question
- Context Precision: Precision of retrieved context
- Context Recall: Recall of retrieved context
- Custom metrics for taxonomy-specific evaluation
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import json

# RAGAS imports
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness,
        answer_similarity
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    logging.warning("RAGAS library not available. Using fallback implementations.")
    RAGAS_AVAILABLE = False

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class RAGASMetrics(Enum):
    """Enumeration of RAGAS metrics"""
    FAITHFULNESS = 'faithfulness'
    ANSWER_RELEVANCY = 'answer_relevancy'
    CONTEXT_PRECISION = 'context_precision'
    CONTEXT_RECALL = 'context_recall'

@dataclass
class RAGResponse:
    """RAG system response structure"""
    answer: str
    retrieved_docs: List[Dict[str, Any]]
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EvaluationResult:
    """Evaluation result structure"""
    metrics: Dict[str, float]
    analysis: Dict[str, Any]
    quality_gates_passed: bool
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RAGASMetricResult:
    """Individual RAGAS metric result"""
    metric_name: str
    score: float
    threshold: float
    passed: bool
    explanation: str
    confidence_interval: Optional[Tuple[float, float]] = None

class RAGASEvaluationEngine:
    """RAGAS-based evaluation engine for RAG systems"""

    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        self.metrics_config = {
            'faithfulness': {
                'threshold': 0.85,
                'weight': 0.3,
                'description': 'Answer consistency with retrieved context'
            },
            'answer_relevancy': {
                'threshold': 0.80,
                'weight': 0.25,
                'description': 'Answer relevance to the question'
            },
            'context_precision': {
                'threshold': 0.75,
                'weight': 0.25,
                'description': 'Precision of retrieved context'
            },
            'context_recall': {
                'threshold': 0.80,
                'weight': 0.20,
                'description': 'Recall of retrieved context'
            }
        }

        # Taxonomy-specific thresholds
        self.taxonomy_thresholds = {
            'classification_accuracy': 0.90,
            'taxonomy_consistency': 0.85,
            'path_precision': 0.80,
            'hierarchical_coherence': 0.75
        }

        # Performance tracking
        self.evaluation_history = []
        self.performance_trends = {}

    async def evaluate_rag_system(
        self,
        test_queries: List[str],
        rag_responses: List[RAGResponse],
        ground_truths: Optional[List[str]] = None,
        expected_contexts: Optional[List[List[str]]] = None
    ) -> EvaluationResult:
        """
        Comprehensive RAG system evaluation using RAGAS framework

        Args:
            test_queries: List of test questions
            rag_responses: List of RAG system responses
            ground_truths: Optional list of expected answers
            expected_contexts: Optional list of expected context documents

        Returns:
            EvaluationResult containing metrics, analysis, and recommendations
        """
        start_time = time.time()
        logger.info(f"Starting RAGAS evaluation for {len(test_queries)} queries")

        try:
            # Prepare evaluation dataset
            evaluation_data = self._prepare_evaluation_dataset(
                test_queries, rag_responses, ground_truths, expected_contexts
            )

            # Run RAGAS evaluation
            if RAGAS_AVAILABLE and self.use_openai:
                ragas_results = await self._run_ragas_evaluation(evaluation_data)
            else:
                ragas_results = await self._run_fallback_evaluation(evaluation_data)

            # Run taxonomy-specific evaluation
            taxonomy_results = await self._evaluate_taxonomy_performance(
                test_queries, rag_responses
            )

            # Combine results
            combined_metrics = {**ragas_results, **taxonomy_results}

            # Analyze results
            analysis = self._analyze_results(combined_metrics, evaluation_data)

            # Check quality gates
            quality_gates_passed = self._check_quality_gates(combined_metrics)

            # Generate recommendations
            recommendations = self._generate_recommendations(combined_metrics, analysis)

            # Record evaluation
            eval_duration = time.time() - start_time
            self._record_evaluation(combined_metrics, eval_duration)

            result = EvaluationResult(
                metrics=combined_metrics,
                analysis=analysis,
                quality_gates_passed=quality_gates_passed,
                recommendations=recommendations
            )

            logger.info(f"RAGAS evaluation completed in {eval_duration:.2f}s")
            logger.info(f"Quality gates passed: {quality_gates_passed}")

            return result

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {str(e)}")
            raise

    def _prepare_evaluation_dataset(
        self,
        queries: List[str],
        responses: List[RAGResponse],
        ground_truths: Optional[List[str]] = None,
        expected_contexts: Optional[List[List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare dataset for RAGAS evaluation"""

        evaluation_data = []

        for i, (query, response) in enumerate(zip(queries, responses)):
            # Extract contexts from retrieved documents
            contexts = [doc.get('text', '') for doc in response.retrieved_docs]

            data_point = {
                'question': query,
                'answer': response.answer,
                'contexts': contexts,
                'ground_truth': ground_truths[i] if ground_truths and i < len(ground_truths) else None,
                'expected_contexts': expected_contexts[i] if expected_contexts and i < len(expected_contexts) else None,
                'metadata': response.metadata
            }

            evaluation_data.append(data_point)

        return evaluation_data

    async def _run_ragas_evaluation(self, evaluation_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Run RAGAS evaluation using the official library"""

        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(evaluation_data)

            # Create Hugging Face Dataset
            dataset = Dataset.from_pandas(df)

            # Select metrics based on available data
            metrics_to_use = []

            if 'contexts' in df.columns and df['contexts'].notna().any():
                metrics_to_use.extend([faithfulness, context_precision, context_recall])

            if 'answer' in df.columns and df['answer'].notna().any():
                metrics_to_use.append(answer_relevancy)

            if 'ground_truth' in df.columns and df['ground_truth'].notna().any():
                metrics_to_use.extend([answer_correctness, answer_similarity])

            if not metrics_to_use:
                logger.warning("No suitable metrics found for RAGAS evaluation")
                return {}

            # Run evaluation
            logger.info(f"Running RAGAS evaluation with {len(metrics_to_use)} metrics")
            result = evaluate(dataset, metrics=metrics_to_use)

            # Convert to dict with proper names
            metrics_dict = {}
            for metric in metrics_to_use:
                metric_name = metric.__class__.__name__.lower()
                if hasattr(result, metric_name):
                    metrics_dict[metric_name] = float(getattr(result, metric_name))

            return metrics_dict

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {str(e)}")
            # Fallback to custom implementation
            return await self._run_fallback_evaluation(evaluation_data)

    async def _run_fallback_evaluation(self, evaluation_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Fallback evaluation implementation when RAGAS is not available"""

        logger.info("Running fallback evaluation implementation")

        metrics = {}

        # Faithfulness evaluation (answer consistency with context)
        faithfulness_scores = []
        for data in evaluation_data:
            score = self._calculate_faithfulness_score(data['answer'], data['contexts'])
            faithfulness_scores.append(score)

        if faithfulness_scores:
            metrics['faithfulness'] = np.mean(faithfulness_scores)

        # Answer relevancy evaluation
        relevancy_scores = []
        for data in evaluation_data:
            score = self._calculate_relevancy_score(data['question'], data['answer'])
            relevancy_scores.append(score)

        if relevancy_scores:
            metrics['answer_relevancy'] = np.mean(relevancy_scores)

        # Context precision evaluation
        precision_scores = []
        for data in evaluation_data:
            if data.get('ground_truth'):
                score = self._calculate_context_precision(
                    data['question'], data['contexts'], data['ground_truth']
                )
                precision_scores.append(score)

        if precision_scores:
            metrics['context_precision'] = np.mean(precision_scores)

        # Context recall evaluation
        recall_scores = []
        for data in evaluation_data:
            if data.get('expected_contexts'):
                score = self._calculate_context_recall(
                    data['contexts'], data['expected_contexts']
                )
                recall_scores.append(score)

        if recall_scores:
            metrics['context_recall'] = np.mean(recall_scores)

        return metrics

    def _calculate_faithfulness_score(self, answer: str, contexts: List[str]) -> float:
        """Calculate faithfulness score using semantic similarity"""

        if not answer or not contexts:
            return 0.0

        try:
            # Combine all contexts
            combined_context = ' '.join(contexts)

            # Use TF-IDF for similarity calculation
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

            try:
                tfidf_matrix = vectorizer.fit_transform([answer, combined_context])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return float(similarity)
            except ValueError:
                # Fallback for empty vocabulary
                return 0.5

        except Exception as e:
            logger.warning(f"Faithfulness calculation failed: {str(e)}")
            return 0.0

    def _calculate_relevancy_score(self, question: str, answer: str) -> float:
        """Calculate answer relevancy score"""

        if not question or not answer:
            return 0.0

        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

            try:
                tfidf_matrix = vectorizer.fit_transform([question, answer])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return float(similarity)
            except ValueError:
                return 0.5

        except Exception as e:
            logger.warning(f"Relevancy calculation failed: {str(e)}")
            return 0.0

    def _calculate_context_precision(self, question: str, contexts: List[str], ground_truth: str) -> float:
        """Calculate context precision score"""

        if not contexts or not ground_truth:
            return 0.0

        try:
            # Calculate how many retrieved contexts are relevant to the ground truth
            relevant_count = 0

            for context in contexts:
                similarity = self._calculate_semantic_similarity(context, ground_truth)
                if similarity > 0.5:  # Threshold for relevance
                    relevant_count += 1

            precision = relevant_count / len(contexts) if contexts else 0.0
            return float(precision)

        except Exception as e:
            logger.warning(f"Context precision calculation failed: {str(e)}")
            return 0.0

    def _calculate_context_recall(self, retrieved_contexts: List[str], expected_contexts: List[str]) -> float:
        """Calculate context recall score"""

        if not expected_contexts:
            return 1.0  # Perfect recall if no expected contexts

        if not retrieved_contexts:
            return 0.0

        try:
            # Calculate how many expected contexts were retrieved
            found_count = 0

            for expected in expected_contexts:
                for retrieved in retrieved_contexts:
                    similarity = self._calculate_semantic_similarity(expected, retrieved)
                    if similarity > 0.5:  # Threshold for match
                        found_count += 1
                        break

            recall = found_count / len(expected_contexts)
            return float(recall)

        except Exception as e:
            logger.warning(f"Context recall calculation failed: {str(e)}")
            return 0.0

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""

        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)

            try:
                tfidf_matrix = vectorizer.fit_transform([text1, text2])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return float(similarity)
            except ValueError:
                return 0.0

        except Exception as e:
            logger.warning(f"Similarity calculation failed: {str(e)}")
            return 0.0

    async def _evaluate_taxonomy_performance(
        self,
        queries: List[str],
        responses: List[RAGResponse]
    ) -> Dict[str, float]:
        """Evaluate taxonomy-specific performance metrics"""

        logger.info("Evaluating taxonomy-specific performance")

        taxonomy_metrics = {}

        # Classification accuracy
        classification_scores = []
        for response in responses:
            score = self._evaluate_classification_accuracy(response)
            classification_scores.append(score)

        if classification_scores:
            taxonomy_metrics['classification_accuracy'] = np.mean(classification_scores)

        # Taxonomy consistency
        consistency_scores = []
        for response in responses:
            score = self._evaluate_taxonomy_consistency(response)
            consistency_scores.append(score)

        if consistency_scores:
            taxonomy_metrics['taxonomy_consistency'] = np.mean(consistency_scores)

        # Path precision (hierarchical accuracy)
        path_scores = []
        for response in responses:
            score = self._evaluate_path_precision(response)
            path_scores.append(score)

        if path_scores:
            taxonomy_metrics['path_precision'] = np.mean(path_scores)

        # Hierarchical coherence
        coherence_scores = []
        for response in responses:
            score = self._evaluate_hierarchical_coherence(response)
            coherence_scores.append(score)

        if coherence_scores:
            taxonomy_metrics['hierarchical_coherence'] = np.mean(coherence_scores)

        return taxonomy_metrics

    def _evaluate_classification_accuracy(self, response: RAGResponse) -> float:
        """Evaluate classification accuracy for taxonomy-related queries"""

        # Check if response contains classification information
        metadata = response.metadata

        # Look for classification confidence and correctness indicators
        classification_confidence = metadata.get('classification_confidence', 0.0)
        classification_labels = metadata.get('classification_labels', [])

        # Basic scoring based on confidence and presence of labels
        if classification_labels and classification_confidence > 0:
            return min(1.0, classification_confidence)

        return 0.6  # Default score for non-classification queries

    def _evaluate_taxonomy_consistency(self, response: RAGResponse) -> float:
        """Evaluate consistency of taxonomy usage"""

        # Check consistency of taxonomy paths in retrieved documents
        retrieved_docs = response.retrieved_docs
        taxonomy_paths = []

        for doc in retrieved_docs:
            path = doc.get('taxonomy_path', [])
            if path:
                taxonomy_paths.append(tuple(path))

        if not taxonomy_paths:
            return 0.5  # Neutral score if no taxonomy information

        # Calculate consistency (how similar the paths are)
        if len(set(taxonomy_paths)) == 1:
            return 1.0  # Perfect consistency

        # Calculate similarity between paths
        similarity_scores = []
        for i, path1 in enumerate(taxonomy_paths):
            for j, path2 in enumerate(taxonomy_paths[i+1:], i+1):
                similarity = self._calculate_path_similarity(list(path1), list(path2))
                similarity_scores.append(similarity)

        return np.mean(similarity_scores) if similarity_scores else 0.5

    def _evaluate_path_precision(self, response: RAGResponse) -> float:
        """Evaluate precision of taxonomy path assignments"""

        retrieved_docs = response.retrieved_docs
        path_scores = []

        for doc in retrieved_docs:
            path = doc.get('taxonomy_path', [])
            content = doc.get('text', '')

            if path and content:
                # Calculate how well the path matches the content
                score = self._calculate_path_content_alignment(path, content)
                path_scores.append(score)

        return np.mean(path_scores) if path_scores else 0.5

    def _evaluate_hierarchical_coherence(self, response: RAGResponse) -> float:
        """Evaluate hierarchical coherence of taxonomy assignments"""

        retrieved_docs = response.retrieved_docs
        paths = []

        for doc in retrieved_docs:
            path = doc.get('taxonomy_path', [])
            if path:
                paths.append(path)

        if not paths:
            return 0.5

        # Check if paths follow proper hierarchical structure
        coherence_scores = []

        for path in paths:
            # Check if each level is more specific than the previous
            specificity_score = self._calculate_hierarchical_specificity(path)
            coherence_scores.append(specificity_score)

        return np.mean(coherence_scores) if coherence_scores else 0.5

    def _calculate_path_similarity(self, path1: List[str], path2: List[str]) -> float:
        """Calculate similarity between two taxonomy paths"""

        if not path1 or not path2:
            return 0.0

        # Calculate Jaccard similarity
        set1 = set(path1)
        set2 = set(path2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _calculate_path_content_alignment(self, path: List[str], content: str) -> float:
        """Calculate how well taxonomy path aligns with content"""

        if not path or not content:
            return 0.0

        content_lower = content.lower()
        matches = 0

        for term in path:
            if term.lower() in content_lower:
                matches += 1

        return matches / len(path) if path else 0.0

    def _calculate_hierarchical_specificity(self, path: List[str]) -> float:
        """Calculate hierarchical specificity score"""

        if len(path) < 2:
            return 1.0  # Single level is always coherent

        # Simple heuristic: longer paths are more specific
        # In practice, this would use domain knowledge or ML models
        specificity_scores = []

        for i in range(1, len(path)):
            # Each subsequent level should be more specific
            parent = path[i-1]
            child = path[i]

            # Simple heuristic: child should be longer or contain parent terms
            if len(child) >= len(parent) or parent.lower() in child.lower():
                specificity_scores.append(1.0)
            else:
                specificity_scores.append(0.5)

        return np.mean(specificity_scores) if specificity_scores else 1.0

    def _analyze_results(self, metrics: Dict[str, float], evaluation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze evaluation results and generate insights"""

        analysis = {
            'overall_score': 0.0,
            'strengths': [],
            'weaknesses': [],
            'trends': {},
            'performance_distribution': {},
            'quality_insights': []
        }

        # Calculate overall score using weighted average
        weighted_scores = []
        total_weight = 0

        for metric_name, score in metrics.items():
            if metric_name in self.metrics_config:
                weight = self.metrics_config[metric_name]['weight']
                weighted_scores.append(score * weight)
                total_weight += weight

        if total_weight > 0:
            analysis['overall_score'] = sum(weighted_scores) / total_weight
        else:
            analysis['overall_score'] = np.mean(list(metrics.values())) if metrics else 0.0

        # Identify strengths and weaknesses
        for metric_name, score in metrics.items():
            threshold = self.metrics_config.get(metric_name, {}).get('threshold') or \
                       self.taxonomy_thresholds.get(metric_name, 0.7)

            if score >= threshold + 0.05:  # 5% above threshold
                analysis['strengths'].append({
                    'metric': metric_name,
                    'score': score,
                    'threshold': threshold,
                    'status': 'excellent',
                    'improvement': score - threshold
                })
            elif score < threshold:
                analysis['weaknesses'].append({
                    'metric': metric_name,
                    'score': score,
                    'threshold': threshold,
                    'gap': threshold - score,
                    'priority': 'high' if threshold - score > 0.1 else 'medium'
                })

        # Performance distribution analysis
        for metric_name, score in metrics.items():
            if score >= 0.9:
                category = 'excellent'
            elif score >= 0.8:
                category = 'good'
            elif score >= 0.7:
                category = 'fair'
            else:
                category = 'poor'

            analysis['performance_distribution'][metric_name] = category

        # Generate quality insights
        insights = []

        if metrics.get('faithfulness', 0) < 0.8:
            insights.append("Low faithfulness indicates answers may not be well-grounded in retrieved context")

        if metrics.get('context_precision', 0) < 0.7:
            insights.append("Low context precision suggests retrieval is returning irrelevant documents")

        if metrics.get('answer_relevancy', 0) < 0.8:
            insights.append("Low answer relevancy indicates answers may not directly address the questions")

        if metrics.get('classification_accuracy', 0) < 0.85:
            insights.append("Taxonomy classification accuracy needs improvement")

        analysis['quality_insights'] = insights

        # Historical trend analysis
        if len(self.evaluation_history) > 1:
            analysis['trends'] = self._calculate_performance_trends(metrics)

        return analysis

    def _calculate_performance_trends(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calculate performance trends from historical data"""

        trends = {}

        if len(self.evaluation_history) < 2:
            return trends

        # Compare with previous evaluation
        previous_metrics = self.evaluation_history[-1]['metrics']

        for metric_name, current_score in current_metrics.items():
            if metric_name in previous_metrics:
                previous_score = previous_metrics[metric_name]
                change = current_score - previous_score

                trends[metric_name] = {
                    'change': change,
                    'direction': 'improving' if change > 0.01 else 'declining' if change < -0.01 else 'stable',
                    'magnitude': abs(change),
                    'current': current_score,
                    'previous': previous_score
                }

        return trends

    def _check_quality_gates(self, metrics: Dict[str, float]) -> bool:
        """Check if all quality gates pass"""

        # Check RAGAS metrics
        for metric_name, config in self.metrics_config.items():
            if metric_name in metrics:
                if metrics[metric_name] < config['threshold']:
                    logger.warning(f"Quality gate failed: {metric_name} = {metrics[metric_name]:.3f} < {config['threshold']}")
                    return False

        # Check taxonomy-specific metrics
        for metric_name, threshold in self.taxonomy_thresholds.items():
            if metric_name in metrics:
                if metrics[metric_name] < threshold:
                    logger.warning(f"Taxonomy quality gate failed: {metric_name} = {metrics[metric_name]:.3f} < {threshold}")
                    return False

        return True

    def _generate_recommendations(self, metrics: Dict[str, float], analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on evaluation results"""

        recommendations = []

        # Recommendations based on weaknesses
        for weakness in analysis.get('weaknesses', []):
            metric_name = weakness['metric']
            gap = weakness['gap']

            if metric_name == 'faithfulness':
                recommendations.append(
                    f"Improve faithfulness (gap: {gap:.3f}) by enhancing answer grounding in retrieved context. "
                    "Consider implementing citation mechanisms and fact-checking pipelines."
                )
            elif metric_name == 'answer_relevancy':
                recommendations.append(
                    f"Improve answer relevancy (gap: {gap:.3f}) by fine-tuning answer generation to better "
                    "address specific question aspects. Consider query understanding improvements."
                )
            elif metric_name == 'context_precision':
                recommendations.append(
                    f"Improve context precision (gap: {gap:.3f}) by enhancing retrieval ranking and filtering. "
                    "Consider re-ranking models and relevance thresholds."
                )
            elif metric_name == 'context_recall':
                recommendations.append(
                    f"Improve context recall (gap: {gap:.3f}) by expanding retrieval coverage. "
                    "Consider increasing retrieval k-values and improving indexing."
                )
            elif metric_name == 'classification_accuracy':
                recommendations.append(
                    f"Improve classification accuracy (gap: {gap:.3f}) by retraining classification models "
                    "with more taxonomy-specific data."
                )

        # General recommendations
        overall_score = analysis.get('overall_score', 0.0)

        if overall_score < 0.7:
            recommendations.append(
                "Overall performance is below target. Consider comprehensive system review and "
                "implementation of priority improvements."
            )
        elif overall_score < 0.8:
            recommendations.append(
                "Performance is fair but has room for improvement. Focus on top weaknesses identified."
            )

        # Trend-based recommendations
        trends = analysis.get('trends', {})
        declining_metrics = [name for name, trend in trends.items() if trend['direction'] == 'declining']

        if declining_metrics:
            recommendations.append(
                f"Monitor declining metrics: {', '.join(declining_metrics)}. "
                "Investigate recent changes that may have caused performance degradation."
            )

        return recommendations

    def _record_evaluation(self, metrics: Dict[str, float], duration: float):
        """Record evaluation results for historical tracking"""

        record = {
            'timestamp': datetime.utcnow(),
            'metrics': metrics.copy(),
            'duration': duration,
            'quality_gates_passed': self._check_quality_gates(metrics)
        }

        self.evaluation_history.append(record)

        # Keep only last 50 evaluations for memory management
        if len(self.evaluation_history) > 50:
            self.evaluation_history = self.evaluation_history[-50:]

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of recent evaluations"""

        if not self.evaluation_history:
            return {"message": "No evaluation history available"}

        recent_evaluations = self.evaluation_history[-10:]  # Last 10 evaluations

        # Calculate averages
        avg_metrics = {}
        all_metrics = set()

        for eval_record in recent_evaluations:
            all_metrics.update(eval_record['metrics'].keys())

        for metric in all_metrics:
            scores = [eval_rec['metrics'].get(metric, 0) for eval_rec in recent_evaluations if metric in eval_rec['metrics']]
            avg_metrics[metric] = np.mean(scores) if scores else 0.0

        # Calculate success rate
        successful_evals = sum(1 for eval_rec in recent_evaluations if eval_rec['quality_gates_passed'])
        success_rate = successful_evals / len(recent_evaluations)

        # Average duration
        avg_duration = np.mean([eval_rec['duration'] for eval_rec in recent_evaluations])

        return {
            'recent_evaluations_count': len(recent_evaluations),
            'average_metrics': avg_metrics,
            'success_rate': success_rate,
            'average_duration_seconds': avg_duration,
            'latest_evaluation': recent_evaluations[-1]['timestamp'].isoformat(),
            'trends_available': len(self.evaluation_history) > 1
        }