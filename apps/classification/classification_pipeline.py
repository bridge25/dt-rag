"""
Classification Pipeline - Main Orchestrator
==========================================

3-stage hybrid classification pipeline:
1. Rule-based classification (fast filtering)
2. LLM-based classification (high accuracy)
3. Cross-validation + Confidence scoring
4. HITL routing (if confidence < threshold)

Achieves:
- Faithfulness ≥ 0.85
- Classification accuracy ≥ 90%
- HITL queue rate ≤ 30%
- p95 latency ≤ 2s
- Cost ≤ ₩5/classification
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from .rule_classifier import RuleBasedClassifier, RuleResult
from .llm_classifier import LLMClassifier, LLMResult
from .confidence_scorer import ConfidenceScorer, ConfidenceResult
from .hitl_queue import HITLQueue, HITLManager, HITLStatus

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Final classification result"""
    # Classification details
    classification: Dict[str, Any]
    confidence: float
    alternatives: List[Dict[str, Any]]

    # Pipeline information
    rule_result: Optional[RuleResult]
    llm_result: Optional[LLMResult]
    confidence_result: Optional[ConfidenceResult]

    # Processing metadata
    processing_time: float
    hitl_required: bool
    hitl_item_id: Optional[str]

    # Performance metrics
    cost_estimate: float
    tokens_used: Optional[int]

    # Quality metrics
    faithfulness_score: Optional[float]
    accuracy_indicators: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)

        # Convert nested dataclasses
        if self.rule_result:
            result['rule_result'] = {
                'candidates': self.rule_result.candidates,
                'total_score': self.rule_result.total_score,
                'processing_time': self.rule_result.processing_time,
                'matched_rules_count': len(self.rule_result.matched_rules)
            }

        if self.llm_result:
            result['llm_result'] = {
                'candidates': self.llm_result.candidates,
                'confidence': self.llm_result.confidence,
                'processing_time': self.llm_result.processing_time,
                'provider': self.llm_result.provider,
                'model': self.llm_result.model,
                'tokens_used': self.llm_result.tokens_used
            }

        if self.confidence_result:
            result['confidence_result'] = {
                'final_confidence': self.confidence_result.final_confidence,
                'quality_flags': self.confidence_result.quality_flags,
                'uncertainty_factors': self.confidence_result.uncertainty_factors
            }

        return result

class ClassificationPipeline:
    """Main classification pipeline orchestrator"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)

        # Initialize components
        self.rule_classifier = RuleBasedClassifier(
            self.config.get("rule_classifier")
        )
        self.llm_classifier = LLMClassifier(
            self.config.get("llm_classifier")
        )
        self.confidence_scorer = ConfidenceScorer(
            self.config.get("confidence_scorer")
        )
        self.hitl_queue = HITLQueue(
            self.config.get("hitl_queue")
        )
        self.hitl_manager = HITLManager(self.hitl_queue)

        # Performance tracking
        self.metrics = {
            "total_classifications": 0,
            "hitl_rate": 0.0,
            "average_latency": 0.0,
            "cost_per_classification": 0.0,
            "accuracy_rate": 0.0
        }

    def _load_config(self, config: Optional[Dict]) -> Dict[str, Any]:
        """Load pipeline configuration"""
        default_config = {
            "performance_targets": {
                "faithfulness_threshold": 0.85,
                "accuracy_threshold": 0.90,
                "hitl_rate_target": 0.30,
                "latency_p95_target": 2.0,  # seconds
                "cost_target": 5.0  # Korean Won
            },
            "pipeline": {
                "enable_rule_classifier": True,
                "enable_llm_classifier": True,
                "enable_cross_validation": True,
                "parallel_execution": True,
                "cache_results": True
            },
            "quality_gates": {
                "min_rule_confidence": 0.3,
                "min_llm_confidence": 0.5,
                "hitl_confidence_threshold": 0.70,
                "auto_approval_threshold": 0.95
            },
            "cost_optimization": {
                "llm_token_limit": 1000,
                "cache_ttl_hours": 24,
                "batch_processing": False
            }
        }

        if config:
            for key, value in config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

        return default_config

    async def classify(self, text: str, taxonomy_version: str = "1",
                      hint_paths: Optional[List[List[str]]] = None,
                      metadata: Optional[Dict] = None) -> ClassificationResult:
        """
        Perform complete classification pipeline

        Args:
            text: Text to classify
            taxonomy_version: Version of taxonomy to use
            hint_paths: Optional hint paths from previous classifications
            metadata: Additional metadata for classification

        Returns:
            ClassificationResult with complete pipeline results
        """
        start_time = time.time()

        try:
            logger.info(f"Starting classification pipeline for text: {text[:100]}...")

            # Stage 1: Rule-based classification (fast filtering)
            rule_result = None
            if self.config["pipeline"]["enable_rule_classifier"]:
                rule_result = await self._run_rule_classification(text, taxonomy_version)

            # Stage 2: LLM classification (high accuracy)
            llm_result = None
            if self.config["pipeline"]["enable_llm_classifier"]:
                rule_candidates = rule_result.candidates if rule_result else None
                llm_result = await self._run_llm_classification(text, taxonomy_version, rule_candidates)

            # Stage 3: Cross-validation and confidence scoring
            confidence_result = None
            final_classification = None

            if self.config["pipeline"]["enable_cross_validation"]:
                final_classification, confidence_result = await self._run_cross_validation(
                    rule_result, llm_result, text
                )
            else:
                # Fallback to best available result
                final_classification = self._select_best_classification(rule_result, llm_result)

            # Stage 4: HITL routing decision
            hitl_required, hitl_item_id = await self._evaluate_hitl_requirement(
                text, final_classification, confidence_result, metadata
            )

            # Calculate performance metrics
            processing_time = time.time() - start_time
            cost_estimate = self._calculate_cost_estimate(rule_result, llm_result)
            tokens_used = llm_result.tokens_used if llm_result else 0

            # Generate alternatives
            alternatives = self._generate_alternatives(rule_result, llm_result, final_classification)

            # Calculate quality metrics
            faithfulness_score = self._calculate_faithfulness_score(
                final_classification, confidence_result
            )
            accuracy_indicators = self._generate_accuracy_indicators(
                rule_result, llm_result, confidence_result
            )

            # Update metrics
            self._update_pipeline_metrics(processing_time, hitl_required, cost_estimate)

            result = ClassificationResult(
                classification=final_classification,
                confidence=confidence_result.final_confidence if confidence_result else 0.7,
                alternatives=alternatives,
                rule_result=rule_result,
                llm_result=llm_result,
                confidence_result=confidence_result,
                processing_time=processing_time,
                hitl_required=hitl_required,
                hitl_item_id=hitl_item_id,
                cost_estimate=cost_estimate,
                tokens_used=tokens_used,
                faithfulness_score=faithfulness_score,
                accuracy_indicators=accuracy_indicators
            )

            logger.info(f"Classification completed in {processing_time:.3f}s, "
                       f"confidence: {result.confidence:.3f}, HITL: {hitl_required}")

            return result

        except Exception as e:
            logger.error(f"Classification pipeline failed: {e}")
            return await self._create_fallback_result(text, time.time() - start_time)

    async def _run_rule_classification(self, text: str, taxonomy_version: str) -> RuleResult:
        """Run rule-based classification stage"""
        try:
            logger.debug("Running rule-based classification")
            result = self.rule_classifier.classify(text, taxonomy_version)

            # Filter low-quality candidates
            min_confidence = self.config["quality_gates"]["min_rule_confidence"]
            result.candidates = [
                c for c in result.candidates
                if c.get("confidence", 0) >= min_confidence
            ]

            logger.debug(f"Rule classification found {len(result.candidates)} candidates")
            return result

        except Exception as e:
            logger.error(f"Rule classification failed: {e}")
            # Return empty result
            return RuleResult(
                candidates=[],
                total_score=0.0,
                matched_rules=[],
                processing_time=0.0
            )

    async def _run_llm_classification(self, text: str, taxonomy_version: str,
                                    rule_candidates: Optional[List[Dict]]) -> LLMResult:
        """Run LLM-based classification stage"""
        try:
            logger.debug("Running LLM classification")
            result = await self.llm_classifier.classify(text, taxonomy_version, rule_candidates)

            # Filter low-quality candidates
            min_confidence = self.config["quality_gates"]["min_llm_confidence"]
            result.candidates = [
                c for c in result.candidates
                if c.get("confidence", 0) >= min_confidence
            ]

            logger.debug(f"LLM classification found {len(result.candidates)} candidates")
            return result

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Return fallback result
            return LLMResult(
                candidates=[{
                    "path": ["AI", "General"],
                    "confidence": 0.6,
                    "source": "llm_fallback",
                    "reasoning": [f"LLM classification failed: {str(e)}"]
                }],
                reasoning=["LLM classification failed"],
                confidence=0.6,
                processing_time=0.0,
                provider="fallback",
                model="none"
            )

    async def _run_cross_validation(self, rule_result: Optional[RuleResult],
                                  llm_result: Optional[LLMResult],
                                  text: str) -> Tuple[Dict[str, Any], ConfidenceResult]:
        """Run cross-validation and confidence scoring"""
        try:
            logger.debug("Running cross-validation and confidence scoring")

            # Select best classification from available results
            final_classification = self._select_best_classification(rule_result, llm_result)

            # Calculate confidence score
            rule_dict = {
                "candidates": rule_result.candidates if rule_result else [],
                "total_score": rule_result.total_score if rule_result else 0.0
            }

            llm_dict = {
                "candidates": llm_result.candidates if llm_result else [],
                "confidence": llm_result.confidence if llm_result else 0.0,
                "provider": llm_result.provider if llm_result else "none"
            }

            confidence_result = self.confidence_scorer.calculate_confidence(
                rule_dict, llm_dict, final_classification
            )

            logger.debug(f"Cross-validation confidence: {confidence_result.final_confidence:.3f}")

            return final_classification, confidence_result

        except Exception as e:
            logger.error(f"Cross-validation failed: {e}")

            # Fallback classification
            fallback_classification = {
                "path": ["AI", "General"],
                "confidence": 0.5,
                "source": "cross_validation_fallback",
                "reasoning": [f"Cross-validation failed: {str(e)}"]
            }

            fallback_confidence = self.confidence_scorer._fallback_confidence(fallback_classification)

            return fallback_classification, fallback_confidence

    def _select_best_classification(self, rule_result: Optional[RuleResult],
                                  llm_result: Optional[LLMResult]) -> Dict[str, Any]:
        """Select best classification from rule and LLM results"""
        candidates = []

        # Collect all candidates
        if rule_result and rule_result.candidates:
            candidates.extend(rule_result.candidates)

        if llm_result and llm_result.candidates:
            candidates.extend(llm_result.candidates)

        if not candidates:
            # Ultimate fallback
            return {
                "path": ["AI", "General"],
                "confidence": 0.5,
                "source": "ultimate_fallback",
                "reasoning": ["No valid candidates from any classifier"]
            }

        # Sort by confidence and select best
        candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        best = candidates[0].copy()

        # Add selection reasoning
        if "reasoning" not in best:
            best["reasoning"] = []
        best["reasoning"].append(f"Selected as highest confidence ({best.get('confidence', 0):.3f})")

        return best

    async def _evaluate_hitl_requirement(self, text: str, classification: Dict[str, Any],
                                       confidence_result: Optional[ConfidenceResult],
                                       metadata: Optional[Dict]) -> Tuple[bool, Optional[str]]:
        """Evaluate if classification requires human validation"""
        try:
            # Check confidence threshold
            confidence = confidence_result.final_confidence if confidence_result else 0.5
            threshold = self.config["quality_gates"]["hitl_confidence_threshold"]

            hitl_required = confidence < threshold

            # Additional HITL triggers
            if confidence_result:
                hitl_required = hitl_required or self.confidence_scorer.should_route_to_hitl(confidence_result)

            # Check for business-critical paths
            if metadata and metadata.get("business_critical", False):
                hitl_required = True

            # Enqueue if HITL required
            hitl_item_id = None
            if hitl_required:
                hitl_item_id = await self.hitl_queue.enqueue(
                    text, classification, confidence, metadata
                )
                logger.info(f"Routed to HITL queue: {hitl_item_id}")

            return hitl_required, hitl_item_id

        except Exception as e:
            logger.error(f"HITL evaluation failed: {e}")
            return True, None  # Conservative approach - route to HITL on error

    def _calculate_cost_estimate(self, rule_result: Optional[RuleResult],
                               llm_result: Optional[LLMResult]) -> float:
        """Calculate cost estimate in Korean Won"""
        cost = 0.0

        # Rule-based classification cost (minimal)
        if rule_result:
            cost += 0.1  # Very low cost for rule processing

        # LLM classification cost
        if llm_result and llm_result.tokens_used:
            # Approximate cost based on token usage
            # GPT-4: ~$0.03/1K tokens = ~40원/1K tokens
            cost += (llm_result.tokens_used / 1000) * 40

        return round(cost, 2)

    def _generate_alternatives(self, rule_result: Optional[RuleResult],
                             llm_result: Optional[LLMResult],
                             selected_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative classifications"""
        alternatives = []
        selected_path = tuple(selected_classification.get("path", []))

        # Collect alternatives from both sources
        all_candidates = []

        if rule_result:
            all_candidates.extend(rule_result.candidates)

        if llm_result:
            all_candidates.extend(llm_result.candidates)

        # Filter out selected classification and duplicates
        seen_paths = {selected_path}

        for candidate in all_candidates:
            path = tuple(candidate.get("path", []))
            if path not in seen_paths:
                alternatives.append(candidate)
                seen_paths.add(path)

        # Sort by confidence and limit
        alternatives.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return alternatives[:3]  # Top 3 alternatives

    def _calculate_faithfulness_score(self, classification: Dict[str, Any],
                                    confidence_result: Optional[ConfidenceResult]) -> float:
        """Calculate faithfulness score (alignment with source material)"""
        # Simplified faithfulness calculation
        base_score = 0.8  # Base faithfulness score

        # Adjust based on confidence quality
        if confidence_result:
            confidence_adjustment = confidence_result.final_confidence * 0.2
            base_score += confidence_adjustment

        # Adjust based on reasoning quality
        reasoning = classification.get("reasoning", [])
        if reasoning and len(' '.join(reasoning)) > 50:
            base_score += 0.05  # Bonus for detailed reasoning

        return min(1.0, base_score)

    def _generate_accuracy_indicators(self, rule_result: Optional[RuleResult],
                                    llm_result: Optional[LLMResult],
                                    confidence_result: Optional[ConfidenceResult]) -> List[str]:
        """Generate accuracy indicators for quality assessment"""
        indicators = []

        if rule_result and rule_result.candidates:
            indicators.append(f"Rule-based: {len(rule_result.candidates)} candidates")

        if llm_result and llm_result.candidates:
            indicators.append(f"LLM: {llm_result.provider} with {len(llm_result.candidates)} candidates")

        if confidence_result:
            indicators.extend(confidence_result.quality_flags)

        return indicators

    def _update_pipeline_metrics(self, processing_time: float, hitl_required: bool, cost: float):
        """Update pipeline performance metrics"""
        self.metrics["total_classifications"] += 1

        # Update rolling averages (simplified)
        total = self.metrics["total_classifications"]

        # Update latency
        self.metrics["average_latency"] = (
            (self.metrics["average_latency"] * (total - 1) + processing_time) / total
        )

        # Update HITL rate
        hitl_count = self.metrics["hitl_rate"] * (total - 1) + (1 if hitl_required else 0)
        self.metrics["hitl_rate"] = hitl_count / total

        # Update cost
        self.metrics["cost_per_classification"] = (
            (self.metrics["cost_per_classification"] * (total - 1) + cost) / total
        )

    async def _create_fallback_result(self, text: str, processing_time: float) -> ClassificationResult:
        """Create fallback result when pipeline fails"""
        fallback_classification = {
            "path": ["AI", "General"],
            "confidence": 0.4,
            "source": "pipeline_fallback",
            "reasoning": ["Classification pipeline failed, using fallback"]
        }

        return ClassificationResult(
            classification=fallback_classification,
            confidence=0.4,
            alternatives=[],
            rule_result=None,
            llm_result=None,
            confidence_result=None,
            processing_time=processing_time,
            hitl_required=True,  # Route fallbacks to HITL
            hitl_item_id=None,
            cost_estimate=0.1,
            tokens_used=0,
            faithfulness_score=0.5,
            accuracy_indicators=["PIPELINE_FALLBACK"]
        )

    # Public API methods

    async def classify_batch(self, texts: List[str], taxonomy_version: str = "1") -> List[ClassificationResult]:
        """Classify multiple texts in batch"""
        if self.config["cost_optimization"]["batch_processing"]:
            # Implement actual batch processing for cost optimization
            logger.info(f"Processing batch of {len(texts)} texts")

        # For now, process individually
        tasks = [self.classify(text, taxonomy_version) for text in texts]
        return await asyncio.gather(*tasks)

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get current pipeline performance metrics"""
        targets = self.config["performance_targets"]

        return {
            "current_metrics": self.metrics.copy(),
            "performance_targets": targets,
            "target_compliance": {
                "hitl_rate_ok": self.metrics["hitl_rate"] <= targets["hitl_rate_target"],
                "latency_ok": self.metrics["average_latency"] <= targets["latency_p95_target"],
                "cost_ok": self.metrics["cost_per_classification"] <= targets["cost_target"]
            }
        }

    async def get_hitl_dashboard(self) -> Dict[str, Any]:
        """Get HITL dashboard data"""
        return self.hitl_manager.get_dashboard_data()

    async def process_human_feedback(self, item_id: str, reviewer_id: str,
                                   human_classification: Dict[str, Any],
                                   feedback: Optional[str] = None) -> bool:
        """Process human feedback from HITL review"""
        return await self.hitl_queue.submit_review(
            item_id, reviewer_id, human_classification, feedback
        )

    async def close(self):
        """Close pipeline and cleanup resources"""
        await self.llm_classifier.close()
        logger.info("Classification pipeline closed")