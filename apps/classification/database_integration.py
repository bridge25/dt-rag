"""
Database Integration Module
==========================

Integrates the classification pipeline with existing database.py ClassifyDAO
Provides backward compatibility while enabling new hybrid pipeline features
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from ..api.database import ClassifyDAO
from .classification_pipeline import ClassificationPipeline, ClassificationResult

logger = logging.getLogger(__name__)

class EnhancedClassifyDAO:
    """Enhanced ClassifyDAO with hybrid classification pipeline"""

    def __init__(self, config: Optional[Dict] = None):
        self.pipeline = ClassificationPipeline(config)
        self.legacy_dao = ClassifyDAO()

    async def classify_text(self, text: str, hint_paths: List[List[str]] = None) -> Dict[str, Any]:
        """
        Enhanced classify_text with hybrid pipeline

        Maintains backward compatibility with existing ClassifyDAO interface
        while using the new 3-stage classification pipeline
        """
        try:
            # Use new hybrid pipeline
            result = await self.pipeline.classify(
                text=text,
                taxonomy_version="1",
                hint_paths=hint_paths,
                metadata={"legacy_compatibility": True}
            )

            # Convert to legacy format for backward compatibility
            legacy_result = self._convert_to_legacy_format(result)

            # Store classification result in database if needed
            await self._store_classification_result(text, result)

            return legacy_result

        except Exception as e:
            logger.error(f"Enhanced classification failed, falling back to legacy: {e}")

            # Fallback to legacy ClassifyDAO
            return await self.legacy_dao.classify_text(text, hint_paths)

    def _convert_to_legacy_format(self, result: ClassificationResult) -> Dict[str, Any]:
        """Convert new classification result to legacy format"""
        classification = result.classification

        return {
            "canonical": classification.get("path", ["AI", "General"]),
            "label": " -> ".join(classification.get("path", ["AI", "General"])),
            "confidence": result.confidence,
            "reasoning": classification.get("reasoning", []),
            "node_id": hash(str(classification.get("path", []))) % 10000,
            "version": 1,
            # Enhanced fields (backward compatible)
            "processing_time": result.processing_time,
            "hitl_required": result.hitl_required,
            "hitl_item_id": result.hitl_item_id,
            "cost_estimate": result.cost_estimate,
            "faithfulness_score": result.faithfulness_score,
            "accuracy_indicators": result.accuracy_indicators,
            "alternatives": result.alternatives
        }

    async def _store_classification_result(self, text: str, result: ClassificationResult):
        """Store detailed classification result for analytics"""
        try:
            # In a full implementation, this would store:
            # 1. Classification history
            # 2. Performance metrics
            # 3. HITL queue items
            # 4. Confidence scoring details

            # For now, just log the result
            logger.info(f"Classification stored: {result.classification['path']}, "
                       f"confidence: {result.confidence:.3f}, "
                       f"HITL: {result.hitl_required}")

        except Exception as e:
            logger.error(f"Failed to store classification result: {e}")

class ClassificationManager:
    """High-level classification management interface"""

    def __init__(self, config: Optional[Dict] = None):
        self.enhanced_dao = EnhancedClassifyDAO(config)
        self.pipeline = self.enhanced_dao.pipeline

    async def classify_document(self, text: str,
                              taxonomy_version: str = "1",
                              business_critical: bool = False) -> Dict[str, Any]:
        """
        Classify a document with full pipeline features

        Args:
            text: Document text to classify
            taxonomy_version: Version of taxonomy to use
            business_critical: Flag for business-critical classifications

        Returns:
            Enhanced classification result
        """
        metadata = {
            "business_critical": business_critical,
            "timestamp": "2025-09-17",  # Would use actual timestamp
            "version": taxonomy_version
        }

        result = await self.pipeline.classify(
            text=text,
            taxonomy_version=taxonomy_version,
            metadata=metadata
        )

        return result.to_dict()

    async def classify_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple documents in batch

        Args:
            documents: List of documents with 'text' and optional metadata

        Returns:
            List of classification results
        """
        texts = [doc.get("text", "") for doc in documents]
        results = await self.pipeline.classify_batch(texts)

        return [result.to_dict() for result in results]

    async def get_hitl_items(self, status: str = "pending") -> List[Dict[str, Any]]:
        """Get HITL queue items for human review"""
        if status == "pending":
            items = self.pipeline.hitl_queue.get_pending_items()
        else:
            # Filter by status
            items = [
                item for item in self.pipeline.hitl_queue.items.values()
                if item.status.value == status
            ]

        return [item.to_dict() for item in items]

    async def submit_human_review(self, item_id: str, reviewer_id: str,
                                human_classification: Dict[str, Any],
                                feedback: Optional[str] = None) -> bool:
        """Submit human review for HITL item"""
        return await self.pipeline.process_human_feedback(
            item_id, reviewer_id, human_classification, feedback
        )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get classification pipeline performance metrics"""
        pipeline_metrics = self.pipeline.get_pipeline_metrics()
        hitl_dashboard = await self.pipeline.get_hitl_dashboard()

        return {
            "pipeline_performance": pipeline_metrics,
            "hitl_status": hitl_dashboard,
            "system_health": self._assess_system_health(pipeline_metrics)
        }

    def _assess_system_health(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Assess overall system health based on metrics"""
        current = metrics["current_metrics"]
        targets = metrics["performance_targets"]
        compliance = metrics["target_compliance"]

        health = {}

        # HITL rate assessment
        if compliance["hitl_rate_ok"]:
            health["hitl_rate"] = "HEALTHY"
        elif current["hitl_rate"] < targets["hitl_rate_target"] * 1.2:
            health["hitl_rate"] = "WARNING"
        else:
            health["hitl_rate"] = "CRITICAL"

        # Latency assessment
        if compliance["latency_ok"]:
            health["latency"] = "HEALTHY"
        elif current["average_latency"] < targets["latency_p95_target"] * 1.5:
            health["latency"] = "WARNING"
        else:
            health["latency"] = "CRITICAL"

        # Cost assessment
        if compliance["cost_ok"]:
            health["cost"] = "HEALTHY"
        elif current["cost_per_classification"] < targets["cost_target"] * 1.3:
            health["cost"] = "WARNING"
        else:
            health["cost"] = "CRITICAL"

        # Overall health
        health_values = list(health.values())
        if all(h == "HEALTHY" for h in health_values):
            health["overall"] = "HEALTHY"
        elif any(h == "CRITICAL" for h in health_values):
            health["overall"] = "CRITICAL"
        else:
            health["overall"] = "WARNING"

        return health

    async def optimize_pipeline(self) -> Dict[str, Any]:
        """Run pipeline optimization based on performance data"""
        metrics = await self.get_performance_metrics()

        optimizations = []

        # HITL rate optimization
        current_hitl_rate = metrics["pipeline_performance"]["current_metrics"]["hitl_rate"]
        if current_hitl_rate > 0.35:  # Above 35%
            optimizations.append({
                "component": "confidence_thresholds",
                "action": "Lower HITL confidence threshold from 0.70 to 0.65",
                "expected_impact": "Reduce HITL rate by 5-10%"
            })

        # Latency optimization
        current_latency = metrics["pipeline_performance"]["current_metrics"]["average_latency"]
        if current_latency > 1.5:  # Above 1.5 seconds
            optimizations.append({
                "component": "parallel_processing",
                "action": "Enable parallel rule and LLM classification",
                "expected_impact": "Reduce latency by 20-30%"
            })

        # Cost optimization
        current_cost = metrics["pipeline_performance"]["current_metrics"]["cost_per_classification"]
        if current_cost > 4.0:  # Above 4 Won
            optimizations.append({
                "component": "llm_usage",
                "action": "Increase rule-based filtering to reduce LLM calls",
                "expected_impact": "Reduce cost by 15-25%"
            })

        return {
            "current_performance": metrics,
            "optimization_recommendations": optimizations,
            "auto_apply": False  # Manual approval required
        }

    async def close(self):
        """Close classification manager and cleanup resources"""
        await self.pipeline.close()

# Convenience function for backward compatibility
async def classify_text_enhanced(text: str, hint_paths: List[List[str]] = None) -> Dict[str, Any]:
    """
    Drop-in replacement for existing classify_text function
    Uses enhanced pipeline while maintaining compatibility
    """
    manager = ClassificationManager()
    try:
        result = await manager.enhanced_dao.classify_text(text, hint_paths)
        return result
    finally:
        await manager.close()

# Factory function for creating classification instances
def create_classification_pipeline(config: Optional[Dict] = None) -> ClassificationManager:
    """
    Factory function to create configured classification pipeline

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured ClassificationManager instance
    """
    return ClassificationManager(config)