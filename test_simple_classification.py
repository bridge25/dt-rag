#!/usr/bin/env python3
"""
Simple Classification Test
=========================

Basic test of the classification components without full pipeline complexity
"""

import asyncio
import time
import logging
import sys
import os

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    }
]

async def test_rule_classifier():
    """Test rule-based classifier"""
    logger.info("Testing Rule-Based Classifier")
    logger.info("-" * 40)

    try:
        from apps.classification.rule_classifier import RuleBasedClassifier

        classifier = RuleBasedClassifier()

        for i, test_case in enumerate(TEST_TEXTS):
            text = test_case["text"]
            expected = test_case["expected_path"]

            logger.info(f"\nTest {i+1}: {test_case['description']}")
            logger.info(f"Text: {text[:60]}...")

            start_time = time.time()
            result = classifier.classify(text)
            processing_time = time.time() - start_time

            logger.info(f"Expected: {expected}")
            logger.info(f"Candidates found: {len(result.candidates)}")
            logger.info(f"Processing time: {processing_time:.3f}s")

            if result.candidates:
                top_candidate = result.candidates[0]
                logger.info(f"Top candidate: {top_candidate['path']} "
                           f"(confidence: {top_candidate['confidence']:.3f})")

                # Check if expected path is in candidates
                found_expected = any(
                    c.get("path") == expected for c in result.candidates
                )
                logger.info(f"Found expected path: {found_expected}")
            else:
                logger.warning("No candidates found!")

    except Exception as e:
        logger.error(f"Rule classifier test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_confidence_scorer():
    """Test confidence scorer with mock data"""
    logger.info("\nTesting Confidence Scorer")
    logger.info("-" * 40)

    try:
        from apps.classification.confidence_scorer import ConfidenceScorer

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
                {"path": ["AI", "RAG"], "confidence": 0.9, "source": "llm", "provider": "fallback"},
                {"path": ["AI", "General"], "confidence": 0.7, "source": "llm", "provider": "fallback"}
            ],
            "confidence": 0.9,
            "provider": "fallback"
        }

        final_classification = {
            "path": ["AI", "RAG"],
            "confidence": 0.85,
            "source": "llm",
            "reasoning": ["Strong RAG indicators found", "Technical depth is high"],
            "provider": "fallback"
        }

        confidence_result = scorer.calculate_confidence(
            rule_result, llm_result, final_classification
        )

        logger.info(f"Final confidence: {confidence_result.final_confidence:.3f}")
        logger.info(f"Rerank score: {confidence_result.signals.rerank_score:.3f}")
        logger.info(f"Source agreement: {confidence_result.signals.source_agreement:.3f}")
        logger.info(f"Answer consistency: {confidence_result.signals.answer_consistency:.3f}")
        logger.info(f"Quality flags: {confidence_result.quality_flags}")

        # Test HITL routing decision
        should_route = scorer.should_route_to_hitl(confidence_result)
        logger.info(f"Should route to HITL: {should_route}")

    except Exception as e:
        logger.error(f"Confidence scorer test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_hitl_queue():
    """Test HITL queue functionality"""
    logger.info("\nTesting HITL Queue")
    logger.info("-" * 40)

    try:
        from apps.classification.hitl_queue import HITLQueue

        queue = HITLQueue()

        # Test enqueueing items
        test_text = "Sample text for classification"
        test_classification = {
            "path": ["AI", "General"],
            "confidence": 0.6,
            "source": "test"
        }

        item_id = await queue.enqueue(
            test_text, test_classification, 0.6, {"test": True}
        )

        logger.info(f"Enqueued item: {item_id}")

        # Get queue status
        status = queue.get_queue_status()
        logger.info(f"Queue status: {status}")

        # Get pending items
        pending = queue.get_pending_items()
        logger.info(f"Pending items: {len(pending)}")

        if pending:
            item = pending[0]
            logger.info(f"First pending item: {item.item_id}, priority: {item.priority.name}")

    except Exception as e:
        logger.error(f"HITL queue test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_fallback_llm():
    """Test LLM classifier with fallback only"""
    logger.info("\nTesting LLM Classifier (Fallback Mode)")
    logger.info("-" * 40)

    try:
        from apps.classification.llm_classifier import LLMClassifier

        classifier = LLMClassifier()

        test_text = TEST_TEXTS[0]["text"]
        logger.info(f"Classifying: {test_text[:60]}...")

        start_time = time.time()
        result = await classifier.classify(test_text)
        processing_time = time.time() - start_time

        logger.info(f"Provider: {result.provider}")
        logger.info(f"Model: {result.model}")
        logger.info(f"Candidates: {len(result.candidates)}")
        logger.info(f"Overall confidence: {result.confidence:.3f}")
        logger.info(f"Processing time: {processing_time:.3f}s")

        if result.candidates:
            top_candidate = result.candidates[0]
            logger.info(f"Top candidate: {top_candidate['path']} "
                       f"(confidence: {top_candidate['confidence']:.3f})")

        await classifier.close()

    except Exception as e:
        logger.error(f"LLM classifier test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_basic_integration():
    """Test basic integration without full pipeline"""
    logger.info("\nTesting Basic Integration")
    logger.info("-" * 40)

    try:
        # Test legacy compatibility
        from apps.api.database import ClassifyDAO

        legacy_dao = ClassifyDAO()

        test_text = TEST_TEXTS[0]["text"]
        logger.info(f"Testing legacy DAO with: {test_text[:60]}...")

        start_time = time.time()
        result = await legacy_dao.classify_text(test_text)
        processing_time = time.time() - start_time

        logger.info(f"Legacy result: {result['canonical']}")
        logger.info(f"Confidence: {result['confidence']:.3f}")
        logger.info(f"Processing time: {processing_time:.3f}s")

    except Exception as e:
        logger.error(f"Basic integration test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run simple classification tests"""
    logger.info("Starting Simple Classification Tests")
    logger.info("=" * 50)

    # Test individual components
    await test_rule_classifier()
    await test_confidence_scorer()
    await test_hitl_queue()
    await test_fallback_llm()
    await test_basic_integration()

    logger.info("\n" + "=" * 50)
    logger.info("Simple Classification Tests Completed")

if __name__ == "__main__":
    asyncio.run(main())