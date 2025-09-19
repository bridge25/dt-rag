#!/usr/bin/env python3
"""
Classification Pipeline Test Suite
=================================

Tests the complete 3-stage hybrid classification pipeline:
1. Rule-based classification
2. LLM classification
3. Confidence scoring and HITL workflow

Performance targets:
- Faithfulness ≥ 0.85
- Classification accuracy ≥ 90%
- HITL queue rate ≤ 30%
- p95 latency ≤ 2s
- Cost ≤ ₩5/classification
"""

import asyncio
import time
import logging
from typing import List, Dict, Any
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import classification components
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.classification.rule_classifier import RuleBasedClassifier
from apps.classification.llm_classifier import LLMClassifier
from apps.classification.confidence_scorer import ConfidenceScorer
from apps.classification.hitl_queue import HITLQueue
from apps.classification.classification_pipeline import ClassificationPipeline, ClassificationResult
from apps.classification.database_integration import ClassificationManager

# Test data
TEST_TEXTS = [
    {
        "text": "This paper presents a novel approach to retrieval-augmented generation using dense vector representations and semantic search.",
        "expected_path": ["AI", "RAG"],
        "description": "Clear RAG content"
    },
    {
        "text": "We implement a machine learning model for predicting customer behavior using ensemble methods and feature engineering.",
        "expected_path": ["AI", "ML"],
        "description": "Clear ML content"
    },
    {
        "text": "Our taxonomy system organizes documents into hierarchical categories with automated classification and human validation.",
        "expected_path": ["AI", "Taxonomy"],
        "description": "Clear taxonomy content"
    },
    {
        "text": "The system uses artificial intelligence to process data.",
        "expected_path": ["AI", "General"],
        "description": "Generic AI content - should have lower confidence"
    },
    {
        "text": "This document discusses various machine learning approaches including neural networks for retrieval systems.",
        "expected_path": ["AI", "RAG"], # Could be ML too - good test for confidence
        "description": "Ambiguous content - may require HITL"
    },
    {
        "text": "Database performance optimization techniques for query processing.",
        "expected_path": ["AI", "General"], # Non-AI content - edge case
        "description": "Non-AI content - should have low confidence"
    }
]

class ClassificationTester:
    """Comprehensive classification pipeline tester"""

    def __init__(self):
        self.manager = ClassificationManager()
        self.results = []
        self.performance_metrics = {
            "total_tests": 0,
            "accuracy_count": 0,
            "high_confidence_count": 0,
            "hitl_count": 0,
            "total_latency": 0.0,
            "total_cost": 0.0,
            "faithfulness_scores": []
        }

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("Starting Classification Pipeline Test Suite")
        logger.info("=" * 60)

        try:
            # Test 1: Individual component tests
            await self.test_rule_classifier()
            await self.test_llm_classifier()
            await self.test_confidence_scorer()

            # Test 2: End-to-end pipeline tests
            await self.test_classification_pipeline()

            # Test 3: HITL workflow tests
            await self.test_hitl_workflow()

            # Test 4: Performance and metrics tests
            await self.test_performance_targets()

            # Test 5: Batch processing tests
            await self.test_batch_processing()

            # Generate final report
            await self.generate_test_report()

        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise

        finally:
            await self.manager.close()

    async def test_rule_classifier(self):
        """Test rule-based classifier component"""
        logger.info("\n1. Testing Rule-Based Classifier")
        logger.info("-" * 40)

        classifier = RuleBasedClassifier()

        for test_case in TEST_TEXTS[:3]:  # Test first 3 cases
            text = test_case["text"]
            expected = test_case["expected_path"]

            start_time = time.time()
            result = classifier.classify(text)
            processing_time = time.time() - start_time

            # Check if expected path is in candidates
            found_expected = any(
                c.get("path") == expected for c in result.candidates
            )

            logger.info(f"Text: {text[:50]}...")
            logger.info(f"Expected: {expected}")
            logger.info(f"Candidates: {len(result.candidates)}")
            logger.info(f"Found expected: {found_expected}")
            logger.info(f"Processing time: {processing_time:.3f}s")

            if result.candidates:
                top_candidate = result.candidates[0]
                logger.info(f"Top candidate: {top_candidate['path']} "
                           f"(confidence: {top_candidate['confidence']:.3f})")

            logger.info("")

        # Test rule statistics
        stats = classifier.get_rule_statistics()
        logger.info(f"Rule Statistics: {json.dumps(stats, indent=2)}")

        # Test rule validation
        issues = classifier.validate_rules()
        logger.info(f"Rule validation issues: {len(issues)}")
        if issues:
            for issue in issues:
                logger.warning(f"  - {issue}")

    async def test_llm_classifier(self):
        """Test LLM classifier component"""
        logger.info("\n2. Testing LLM Classifier")
        logger.info("-" * 40)

        classifier = LLMClassifier()

        for test_case in TEST_TEXTS[:2]:  # Test fewer cases to save cost
            text = test_case["text"]
            expected = test_case["expected_path"]

            start_time = time.time()
            result = await classifier.classify(text)
            processing_time = time.time() - start_time

            logger.info(f"Text: {text[:50]}...")
            logger.info(f"Expected: {expected}")
            logger.info(f"Provider: {result.provider}")
            logger.info(f"Model: {result.model}")
            logger.info(f"Candidates: {len(result.candidates)}")
            logger.info(f"Overall confidence: {result.confidence:.3f}")
            logger.info(f"Processing time: {processing_time:.3f}s")

            if result.tokens_used:
                logger.info(f"Tokens used: {result.tokens_used}")

            if result.candidates:
                top_candidate = result.candidates[0]
                logger.info(f"Top candidate: {top_candidate['path']} "
                           f"(confidence: {top_candidate['confidence']:.3f})")

            # Validate response
            is_valid, issues = await classifier.validate_response(result)
            logger.info(f"Response valid: {is_valid}")
            if issues:
                for issue in issues:
                    logger.warning(f"  - {issue}")

            logger.info("")

        await classifier.close()

    async def test_confidence_scorer(self):
        """Test confidence scoring component"""
        logger.info("\n3. Testing Confidence Scorer")
        logger.info("-" * 40)

        scorer = ConfidenceScorer()

        # Mock results for testing
        rule_result = {
            "candidates": [
                {"path": ["AI", "RAG"], "confidence": 0.8, "source": "rule_based"},
                {"path": ["AI", "ML"], "confidence": 0.6, "source": "rule_based"}
            ],
            "total_score": 1.4
        }

        llm_result = {
            "candidates": [
                {"path": ["AI", "RAG"], "confidence": 0.9, "source": "llm", "provider": "openai"},
                {"path": ["AI", "General"], "confidence": 0.7, "source": "llm", "provider": "openai"}
            ],
            "confidence": 0.9,
            "provider": "openai"
        }

        final_classification = {
            "path": ["AI", "RAG"],
            "confidence": 0.85,
            "source": "llm",
            "reasoning": ["Strong RAG indicators found", "Technical depth is high"],
            "provider": "openai"
        }

        confidence_result = scorer.calculate_confidence(
            rule_result, llm_result, final_classification
        )

        logger.info(f"Final confidence: {confidence_result.final_confidence:.3f}")
        logger.info(f"Rerank score: {confidence_result.signals.rerank_score:.3f}")
        logger.info(f"Source agreement: {confidence_result.signals.source_agreement:.3f}")
        logger.info(f"Answer consistency: {confidence_result.signals.answer_consistency:.3f}")
        logger.info(f"Quality flags: {confidence_result.quality_flags}")
        logger.info(f"Uncertainty factors: {confidence_result.uncertainty_factors}")

        # Test HITL routing decision
        should_route = scorer.should_route_to_hitl(confidence_result)
        logger.info(f"Should route to HITL: {should_route}")

        # Test explanation generation
        explanation = scorer.get_confidence_explanation(confidence_result)
        logger.info(f"Confidence explanation: {json.dumps(explanation, indent=2)}")

    async def test_classification_pipeline(self):
        """Test end-to-end classification pipeline"""
        logger.info("\n4. Testing Classification Pipeline")
        logger.info("-" * 40)

        for i, test_case in enumerate(TEST_TEXTS):
            text = test_case["text"]
            expected = test_case["expected_path"]
            description = test_case["description"]

            logger.info(f"\nTest {i+1}: {description}")
            logger.info(f"Text: {text[:60]}...")

            start_time = time.time()
            result = await self.manager.classify_document(text)
            processing_time = time.time() - start_time

            # Extract key metrics
            classification = result["classification"]
            confidence = result["confidence"]
            hitl_required = result["hitl_required"]
            cost_estimate = result["cost_estimate"]
            faithfulness_score = result.get("faithfulness_score", 0.0)

            # Check accuracy
            predicted_path = classification["path"]
            is_accurate = predicted_path == expected

            # Update metrics
            self.performance_metrics["total_tests"] += 1
            if is_accurate:
                self.performance_metrics["accuracy_count"] += 1
            if confidence >= 0.85:
                self.performance_metrics["high_confidence_count"] += 1
            if hitl_required:
                self.performance_metrics["hitl_count"] += 1
            self.performance_metrics["total_latency"] += processing_time
            self.performance_metrics["total_cost"] += cost_estimate
            self.performance_metrics["faithfulness_scores"].append(faithfulness_score)

            # Log results
            logger.info(f"Expected: {expected}")
            logger.info(f"Predicted: {predicted_path}")
            logger.info(f"Accurate: {is_accurate}")
            logger.info(f"Confidence: {confidence:.3f}")
            logger.info(f"HITL required: {hitl_required}")
            logger.info(f"Processing time: {processing_time:.3f}s")
            logger.info(f"Cost estimate: ₩{cost_estimate:.2f}")
            logger.info(f"Faithfulness: {faithfulness_score:.3f}")

            # Store detailed result
            self.results.append({
                "test_case": test_case,
                "result": result,
                "metrics": {
                    "accurate": is_accurate,
                    "processing_time": processing_time,
                    "cost_estimate": cost_estimate,
                    "faithfulness_score": faithfulness_score
                }
            })

    async def test_hitl_workflow(self):
        """Test HITL workflow functionality"""
        logger.info("\n5. Testing HITL Workflow")
        logger.info("-" * 40)

        hitl_queue = self.manager.pipeline.hitl_queue

        # Get current HITL items
        hitl_items = await self.manager.get_hitl_items("pending")
        logger.info(f"Current HITL queue size: {len(hitl_items)}")

        if hitl_items:
            # Test human review submission
            sample_item = hitl_items[0]
            item_id = sample_item["item_id"]

            # Mock human review
            human_classification = {
                "path": ["AI", "RAG"],
                "confidence": 0.95,
                "source": "human_review"
            }

            feedback = "Classification looks correct, high confidence in RAG categorization."

            success = await self.manager.submit_human_review(
                item_id, "test_reviewer", human_classification, feedback
            )

            logger.info(f"Human review submission: {success}")

        # Get queue status
        queue_status = hitl_queue.get_queue_status()
        logger.info(f"Queue status: {json.dumps(queue_status, indent=2)}")

        # Test reviewer performance
        if hitl_items:
            performance = hitl_queue.get_reviewer_performance("test_reviewer")
            logger.info(f"Reviewer performance: {json.dumps(performance, indent=2)}")

    async def test_performance_targets(self):
        """Test performance against target thresholds"""
        logger.info("\n6. Testing Performance Targets")
        logger.info("-" * 40)

        # Calculate performance metrics
        total_tests = self.performance_metrics["total_tests"]
        if total_tests == 0:
            logger.warning("No tests completed for performance evaluation")
            return

        accuracy_rate = self.performance_metrics["accuracy_count"] / total_tests
        hitl_rate = self.performance_metrics["hitl_count"] / total_tests
        avg_latency = self.performance_metrics["total_latency"] / total_tests
        avg_cost = self.performance_metrics["total_cost"] / total_tests
        avg_faithfulness = (
            sum(self.performance_metrics["faithfulness_scores"]) /
            len(self.performance_metrics["faithfulness_scores"])
        )

        # Performance targets
        targets = {
            "faithfulness": 0.85,
            "accuracy": 0.90,
            "hitl_rate": 0.30,
            "latency": 2.0,
            "cost": 5.0
        }

        # Check compliance
        results = {
            "faithfulness": {
                "current": avg_faithfulness,
                "target": targets["faithfulness"],
                "compliant": avg_faithfulness >= targets["faithfulness"]
            },
            "accuracy": {
                "current": accuracy_rate,
                "target": targets["accuracy"],
                "compliant": accuracy_rate >= targets["accuracy"]
            },
            "hitl_rate": {
                "current": hitl_rate,
                "target": targets["hitl_rate"],
                "compliant": hitl_rate <= targets["hitl_rate"]
            },
            "latency": {
                "current": avg_latency,
                "target": targets["latency"],
                "compliant": avg_latency <= targets["latency"]
            },
            "cost": {
                "current": avg_cost,
                "target": targets["cost"],
                "compliant": avg_cost <= targets["cost"]
            }
        }

        logger.info("Performance Target Compliance:")
        for metric, data in results.items():
            status = "✓" if data["compliant"] else "✗"
            logger.info(f"{status} {metric}: {data['current']:.3f} "
                       f"(target: {data['target']})")

        # Overall compliance
        compliant_count = sum(1 for r in results.values() if r["compliant"])
        overall_compliance = compliant_count / len(results)
        logger.info(f"\nOverall compliance: {overall_compliance:.1%} "
                   f"({compliant_count}/{len(results)} targets met)")

    async def test_batch_processing(self):
        """Test batch processing functionality"""
        logger.info("\n7. Testing Batch Processing")
        logger.info("-" * 40)

        # Prepare batch of documents
        batch_docs = [
            {"text": test_case["text"], "metadata": {"test_id": i}}
            for i, test_case in enumerate(TEST_TEXTS[:3])
        ]

        start_time = time.time()
        batch_results = await self.manager.classify_batch(batch_docs)
        batch_time = time.time() - start_time

        logger.info(f"Batch of {len(batch_docs)} documents processed in {batch_time:.3f}s")
        logger.info(f"Average time per document: {batch_time/len(batch_docs):.3f}s")

        for i, result in enumerate(batch_results):
            classification = result["classification"]
            confidence = result["confidence"]
            logger.info(f"Doc {i+1}: {classification['path']} "
                       f"(confidence: {confidence:.3f})")

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("CLASSIFICATION PIPELINE TEST REPORT")
        logger.info("=" * 60)

        # Get system metrics
        system_metrics = await self.manager.get_performance_metrics()

        logger.info("\n📊 Performance Summary:")
        current = system_metrics["pipeline_performance"]["current_metrics"]
        compliance = system_metrics["pipeline_performance"]["target_compliance"]

        logger.info(f"Total Classifications: {current['total_classifications']}")
        logger.info(f"HITL Rate: {current['hitl_rate']:.1%} "
                   f"{'✓' if compliance['hitl_rate_ok'] else '✗'}")
        logger.info(f"Average Latency: {current['average_latency']:.3f}s "
                   f"{'✓' if compliance['latency_ok'] else '✗'}")
        logger.info(f"Cost per Classification: ₩{current['cost_per_classification']:.2f} "
                   f"{'✓' if compliance['cost_ok'] else '✗'}")

        # System health assessment
        health = system_metrics.get("system_health", {})
        logger.info(f"\n🏥 System Health: {health.get('overall', 'UNKNOWN')}")
        for component, status in health.items():
            if component != 'overall':
                logger.info(f"  {component}: {status}")

        # Optimization recommendations
        optimization = await self.manager.optimize_pipeline()
        recommendations = optimization.get("optimization_recommendations", [])

        if recommendations:
            logger.info(f"\n🔧 Optimization Recommendations:")
            for rec in recommendations:
                logger.info(f"  - {rec['component']}: {rec['action']}")
                logger.info(f"    Expected impact: {rec['expected_impact']}")

        logger.info(f"\n✅ Test Suite Completed Successfully!")
        logger.info(f"   Total test cases: {len(TEST_TEXTS)}")
        logger.info(f"   Components tested: 5 (Rule, LLM, Confidence, Pipeline, HITL)")
        logger.info(f"   Performance targets evaluated: 5")

async def main():
    """Run the classification pipeline test suite"""
    tester = ClassificationTester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\nTest suite interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())