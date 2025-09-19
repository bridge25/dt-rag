"""
Confidence Scoring Module
========================

Multi-signal confidence calculation combining:
- Rerank score (40%)
- Source agreement (30%)
- Answer consistency (30%)
- Additional quality signals
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import statistics

logger = logging.getLogger(__name__)

@dataclass
class ConfidenceSignals:
    """Individual confidence signals"""
    rerank_score: float
    source_agreement: float
    answer_consistency: float
    path_depth_score: float
    reasoning_quality: float
    provider_reliability: float

@dataclass
class ConfidenceResult:
    """Final confidence result"""
    final_confidence: float
    signals: ConfidenceSignals
    component_scores: Dict[str, float]
    quality_flags: List[str]
    uncertainty_factors: List[str]

class ConfidenceScorer:
    """Advanced confidence scoring with multiple signals"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)

    def _load_config(self, config: Optional[Dict]) -> Dict[str, Any]:
        """Load confidence scoring configuration"""
        default_config = {
            "weights": {
                "rerank_score": 0.40,
                "source_agreement": 0.30,
                "answer_consistency": 0.30
            },
            "bonus_weights": {
                "path_depth": 0.05,
                "reasoning_quality": 0.05,
                "provider_reliability": 0.03
            },
            "thresholds": {
                "high_confidence": 0.85,
                "medium_confidence": 0.70,
                "low_confidence": 0.50,
                "hitl_threshold": 0.70
            },
            "quality_checks": {
                "min_reasoning_length": 15,
                "min_source_count": 2,
                "max_path_depth": 4,
                "consistency_threshold": 0.6
            },
            "provider_reliability": {
                "openai": 0.95,
                "anthropic": 0.93,
                "rule_based": 0.80,
                "fallback": 0.60
            }
        }

        if config:
            for key, value in config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

        return default_config

    def calculate_confidence(self,
                           rule_result: Dict[str, Any],
                           llm_result: Dict[str, Any],
                           final_classification: Dict[str, Any]) -> ConfidenceResult:
        """
        Calculate comprehensive confidence score

        Args:
            rule_result: Results from rule-based classifier
            llm_result: Results from LLM classifier
            final_classification: Final selected classification

        Returns:
            ConfidenceResult with detailed scoring
        """
        try:
            # Calculate individual signals
            signals = self._calculate_signals(rule_result, llm_result, final_classification)

            # Calculate weighted score
            component_scores = self._calculate_component_scores(signals)

            # Apply bonuses and penalties
            final_score = self._apply_adjustments(component_scores, signals)

            # Generate quality flags and uncertainty factors
            quality_flags = self._generate_quality_flags(signals, final_score)
            uncertainty_factors = self._identify_uncertainty_factors(
                rule_result, llm_result, signals
            )

            return ConfidenceResult(
                final_confidence=final_score,
                signals=signals,
                component_scores=component_scores,
                quality_flags=quality_flags,
                uncertainty_factors=uncertainty_factors
            )

        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return self._fallback_confidence(final_classification)

    def _calculate_signals(self, rule_result: Dict, llm_result: Dict,
                          final_classification: Dict) -> ConfidenceSignals:
        """Calculate individual confidence signals"""

        # 1. Rerank Score (40%) - Quality of final classification
        rerank_score = self._calculate_rerank_score(final_classification)

        # 2. Source Agreement (30%) - Agreement between classifiers
        source_agreement = self._calculate_source_agreement(rule_result, llm_result)

        # 3. Answer Consistency (30%) - Consistency across candidates
        answer_consistency = self._calculate_answer_consistency(rule_result, llm_result)

        # Bonus signals
        path_depth_score = self._calculate_path_depth_score(final_classification)
        reasoning_quality = self._calculate_reasoning_quality(final_classification)
        provider_reliability = self._calculate_provider_reliability(final_classification)

        return ConfidenceSignals(
            rerank_score=rerank_score,
            source_agreement=source_agreement,
            answer_consistency=answer_consistency,
            path_depth_score=path_depth_score,
            reasoning_quality=reasoning_quality,
            provider_reliability=provider_reliability
        )

    def _calculate_rerank_score(self, classification: Dict) -> float:
        """Calculate rerank score based on classification quality"""
        base_score = classification.get("confidence", 0.5)

        # Adjust based on source quality
        source = classification.get("source", "unknown")
        if source == "llm":
            base_score *= 1.1  # LLM results generally higher quality
        elif source == "rule_based":
            base_score *= 0.9  # Rule-based slightly lower quality
        elif source == "fallback":
            base_score *= 0.7  # Fallback significantly lower quality

        # Check for reasoning quality
        reasoning = classification.get("reasoning", [])
        if len(reasoning) > 0 and len(' '.join(reasoning)) > 30:
            base_score *= 1.05  # Good reasoning bonus

        return min(1.0, base_score)

    def _calculate_source_agreement(self, rule_result: Dict, llm_result: Dict) -> float:
        """Calculate agreement between rule and LLM classifiers"""
        rule_candidates = rule_result.get("candidates", [])
        llm_candidates = llm_result.get("candidates", [])

        if not rule_candidates or not llm_candidates:
            return 0.5  # Medium score if one source missing

        # Extract paths from both sources
        rule_paths = [tuple(c.get("path", [])) for c in rule_candidates[:3]]
        llm_paths = [tuple(c.get("path", [])) for c in llm_candidates[:3]]

        # Calculate overlap
        rule_set = set(rule_paths)
        llm_set = set(llm_paths)

        if not rule_set and not llm_set:
            return 0.5

        # Jaccard similarity
        intersection = len(rule_set.intersection(llm_set))
        union = len(rule_set.union(llm_set))

        if union == 0:
            return 0.5

        jaccard = intersection / union

        # Weight by confidence of overlapping results
        confidence_weight = 1.0
        for rule_candidate in rule_candidates:
            for llm_candidate in llm_candidates:
                if tuple(rule_candidate.get("path", [])) == tuple(llm_candidate.get("path", [])):
                    avg_confidence = (
                        rule_candidate.get("confidence", 0.5) +
                        llm_candidate.get("confidence", 0.5)
                    ) / 2
                    confidence_weight = max(confidence_weight, avg_confidence)

        return min(1.0, jaccard * confidence_weight)

    def _calculate_answer_consistency(self, rule_result: Dict, llm_result: Dict) -> float:
        """Calculate consistency across all candidates"""
        all_candidates = []

        # Collect all candidates
        all_candidates.extend(rule_result.get("candidates", []))
        all_candidates.extend(llm_result.get("candidates", []))

        if len(all_candidates) < 2:
            return 0.6  # Medium score for single source

        # Group by path
        path_groups = {}
        for candidate in all_candidates:
            path_key = tuple(candidate.get("path", []))
            if path_key not in path_groups:
                path_groups[path_key] = []
            path_groups[path_key].append(candidate.get("confidence", 0.5))

        # Calculate consistency metrics
        if len(path_groups) == 1:
            # All agree on same path - high consistency
            confidences = list(path_groups.values())[0]
            if len(confidences) > 1:
                consistency = 1.0 - (statistics.stdev(confidences) / statistics.mean(confidences))
            else:
                consistency = 1.0
        else:
            # Multiple paths - calculate diversity penalty
            path_counts = [(path, len(confidences)) for path, confidences in path_groups.items()]
            path_counts.sort(key=lambda x: x[1], reverse=True)

            # Dominant path score
            total_candidates = sum(count for _, count in path_counts)
            dominant_ratio = path_counts[0][1] / total_candidates

            consistency = dominant_ratio

        return min(1.0, max(0.0, consistency))

    def _calculate_path_depth_score(self, classification: Dict) -> float:
        """Score based on taxonomy path depth (more specific = higher score)"""
        path = classification.get("path", [])
        depth = len(path)

        if depth <= 1:
            return 0.3  # Too general
        elif depth == 2:
            return 0.8  # Good specificity
        elif depth == 3:
            return 1.0  # Optimal specificity
        else:
            return 0.9  # Very specific but potentially over-fitted

    def _calculate_reasoning_quality(self, classification: Dict) -> float:
        """Score quality of reasoning provided"""
        reasoning = classification.get("reasoning", [])

        if not reasoning:
            return 0.0

        reasoning_text = ' '.join(reasoning)

        # Length score
        length_score = min(1.0, len(reasoning_text) / 50)

        # Technical term score
        technical_terms = [
            "retrieval", "augmented", "generation", "machine learning",
            "classification", "taxonomy", "embedding", "vector", "model"
        ]
        term_score = sum(1 for term in technical_terms if term in reasoning_text.lower())
        term_score = min(1.0, term_score / 3)

        # Structure score (multiple reasoning points)
        structure_score = min(1.0, len(reasoning) / 3)

        return (length_score + term_score + structure_score) / 3

    def _calculate_provider_reliability(self, classification: Dict) -> float:
        """Score based on provider reliability"""
        provider = classification.get("provider", "unknown")
        return self.config["provider_reliability"].get(provider, 0.5)

    def _calculate_component_scores(self, signals: ConfidenceSignals) -> Dict[str, float]:
        """Calculate weighted component scores"""
        weights = self.config["weights"]

        return {
            "rerank_component": signals.rerank_score * weights["rerank_score"],
            "agreement_component": signals.source_agreement * weights["source_agreement"],
            "consistency_component": signals.answer_consistency * weights["answer_consistency"]
        }

    def _apply_adjustments(self, component_scores: Dict[str, float],
                          signals: ConfidenceSignals) -> float:
        """Apply bonuses and calculate final score"""
        # Base score from main components
        base_score = sum(component_scores.values())

        # Apply bonus weights
        bonus_weights = self.config["bonus_weights"]
        bonuses = (
            signals.path_depth_score * bonus_weights["path_depth"] +
            signals.reasoning_quality * bonus_weights["reasoning_quality"] +
            signals.provider_reliability * bonus_weights["provider_reliability"]
        )

        final_score = base_score + bonuses

        # Apply penalties for edge cases
        if signals.rerank_score < 0.3:
            final_score *= 0.8  # Penalty for very low base score

        if signals.source_agreement < 0.2:
            final_score *= 0.9  # Penalty for disagreement

        return min(1.0, max(0.0, final_score))

    def _generate_quality_flags(self, signals: ConfidenceSignals,
                              final_score: float) -> List[str]:
        """Generate quality assessment flags"""
        flags = []

        thresholds = self.config["thresholds"]

        if final_score >= thresholds["high_confidence"]:
            flags.append("HIGH_CONFIDENCE")
        elif final_score >= thresholds["medium_confidence"]:
            flags.append("MEDIUM_CONFIDENCE")
        else:
            flags.append("LOW_CONFIDENCE")

        if final_score < thresholds["hitl_threshold"]:
            flags.append("REQUIRES_HUMAN_REVIEW")

        if signals.source_agreement > 0.8:
            flags.append("STRONG_AGREEMENT")
        elif signals.source_agreement < 0.3:
            flags.append("SOURCE_DISAGREEMENT")

        if signals.answer_consistency > 0.9:
            flags.append("HIGHLY_CONSISTENT")
        elif signals.answer_consistency < 0.4:
            flags.append("INCONSISTENT_RESULTS")

        if signals.reasoning_quality > 0.8:
            flags.append("GOOD_REASONING")
        elif signals.reasoning_quality < 0.3:
            flags.append("POOR_REASONING")

        return flags

    def _identify_uncertainty_factors(self, rule_result: Dict, llm_result: Dict,
                                    signals: ConfidenceSignals) -> List[str]:
        """Identify factors contributing to uncertainty"""
        factors = []

        if signals.source_agreement < 0.5:
            factors.append("Classifiers disagree on category")

        if signals.answer_consistency < 0.6:
            factors.append("Inconsistent confidence scores")

        if signals.reasoning_quality < 0.4:
            factors.append("Insufficient reasoning provided")

        # Check for ambiguous text indicators
        rule_candidates = rule_result.get("candidates", [])
        if len(rule_candidates) > 1:
            top_two = rule_candidates[:2]
            if (len(top_two) == 2 and
                abs(top_two[0].get("confidence", 0) - top_two[1].get("confidence", 0)) < 0.1):
                factors.append("Multiple equally likely categories")

        llm_candidates = llm_result.get("candidates", [])
        if any("uncertainty" in ' '.join(c.get("reasoning", [])).lower()
               for c in llm_candidates):
            factors.append("LLM expressed uncertainty")

        return factors

    def _fallback_confidence(self, classification: Dict) -> ConfidenceResult:
        """Fallback confidence calculation when main calculation fails"""
        base_confidence = classification.get("confidence", 0.5)

        return ConfidenceResult(
            final_confidence=base_confidence,
            signals=ConfidenceSignals(
                rerank_score=base_confidence,
                source_agreement=0.5,
                answer_consistency=0.5,
                path_depth_score=0.5,
                reasoning_quality=0.3,
                provider_reliability=0.5
            ),
            component_scores={
                "rerank_component": base_confidence * 0.4,
                "agreement_component": 0.15,
                "consistency_component": 0.15
            },
            quality_flags=["FALLBACK_CALCULATION"],
            uncertainty_factors=["Confidence calculation failed"]
        )

    def should_route_to_hitl(self, confidence_result: ConfidenceResult) -> bool:
        """Determine if classification should be routed to HITL queue"""
        return (confidence_result.final_confidence < self.config["thresholds"]["hitl_threshold"] or
                "REQUIRES_HUMAN_REVIEW" in confidence_result.quality_flags or
                "SOURCE_DISAGREEMENT" in confidence_result.quality_flags)

    def get_confidence_explanation(self, confidence_result: ConfidenceResult) -> Dict[str, Any]:
        """Generate human-readable confidence explanation"""
        explanation = {
            "overall_assessment": self._get_confidence_level_description(
                confidence_result.final_confidence
            ),
            "key_factors": {
                "classification_quality": f"{confidence_result.signals.rerank_score:.2f}",
                "classifier_agreement": f"{confidence_result.signals.source_agreement:.2f}",
                "result_consistency": f"{confidence_result.signals.answer_consistency:.2f}"
            },
            "quality_indicators": confidence_result.quality_flags,
            "uncertainty_sources": confidence_result.uncertainty_factors,
            "recommendation": self._get_recommendation(confidence_result)
        }

        return explanation

    def _get_confidence_level_description(self, score: float) -> str:
        """Get human-readable confidence level"""
        if score >= 0.85:
            return "Very High - Classification is highly reliable"
        elif score >= 0.70:
            return "High - Classification is reliable with minor uncertainty"
        elif score >= 0.50:
            return "Medium - Classification is reasonable but has some uncertainty"
        else:
            return "Low - Classification is uncertain and should be reviewed"

    def _get_recommendation(self, confidence_result: ConfidenceResult) -> str:
        """Get recommendation based on confidence result"""
        if confidence_result.final_confidence >= 0.85:
            return "Accept classification automatically"
        elif confidence_result.final_confidence >= 0.70:
            return "Accept classification with monitoring"
        elif confidence_result.final_confidence >= 0.50:
            return "Review classification before accepting"
        else:
            return "Require human validation before accepting"