#!/usr/bin/env python3
"""
Test Rule Classifier Only
========================
"""

import re
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simplified rule classifier for testing
class SimpleRuleClassifier:
    def __init__(self):
        self.rules = {
            "rag": {
                "patterns": [
                    r"\b(retrieval.*augmented.*generation|RAG|vector.*database|embedding)\b",
                    r"\b(document.*retrieval|semantic.*search|knowledge.*base)\b"
                ],
                "keywords": ["retrieval", "augmented", "generation", "vector", "embedding"],
                "path": ["AI", "RAG"]
            },
            "ml": {
                "patterns": [
                    r"\b(machine.*learning|ML|classification|regression|algorithm)\b",
                    r"\b(model|training|prediction)\b"
                ],
                "keywords": ["machine", "learning", "model", "algorithm", "training"],
                "path": ["AI", "ML"]
            },
            "taxonomy": {
                "patterns": [
                    r"\b(taxonomy|classification.*system|hierarchy|ontology)\b",
                    r"\b(categorization|category|structure)\b"
                ],
                "keywords": ["taxonomy", "classification", "hierarchy", "category"],
                "path": ["AI", "Taxonomy"]
            }
        }

    def classify(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        candidates = []

        for domain, config in self.rules.items():
            score = 0.0
            matches = []

            # Pattern matching
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 0.5
                    matches.append(f"Pattern: {pattern}")

            # Keyword matching
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    score += 0.2
                    matches.append(f"Keyword: {keyword}")

            if score > 0.3:  # Minimum threshold
                confidence = min(0.95, score / 2)  # Normalize to confidence
                candidates.append({
                    "path": config["path"],
                    "confidence": confidence,
                    "source": "rule_based",
                    "reasoning": matches
                })

        # Sort by confidence
        candidates.sort(key=lambda x: x["confidence"], reverse=True)

        # If no candidates, default to General AI
        if not candidates:
            candidates.append({
                "path": ["AI", "General"],
                "confidence": 0.6,
                "source": "rule_based",
                "reasoning": ["No specific patterns found, defaulting to General AI"]
            })

        return {
            "candidates": candidates,
            "total_score": sum(c["confidence"] for c in candidates),
            "processing_time": 0.001  # Very fast
        }

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
        "description": "Generic AI content"
    }
]

def main():
    """Test simple rule classifier"""
    logger.info("Testing Simple Rule-Based Classifier")
    logger.info("=" * 50)

    classifier = SimpleRuleClassifier()

    total_tests = 0
    accurate_tests = 0

    for i, test_case in enumerate(TEST_TEXTS):
        text = test_case["text"]
        expected = test_case["expected_path"]
        description = test_case["description"]

        logger.info(f"\nTest {i+1}: {description}")
        logger.info(f"Text: {text[:60]}...")
        logger.info(f"Expected: {expected}")

        result = classifier.classify(text)
        candidates = result["candidates"]

        if candidates:
            top_candidate = candidates[0]
            predicted = top_candidate["path"]
            confidence = top_candidate["confidence"]

            logger.info(f"Predicted: {predicted}")
            logger.info(f"Confidence: {confidence:.3f}")

            # Check accuracy
            is_accurate = predicted == expected
            logger.info(f"Accurate: {is_accurate}")

            if is_accurate:
                accurate_tests += 1

            # Show reasoning
            reasoning = top_candidate.get("reasoning", [])
            if reasoning:
                logger.info(f"Reasoning: {reasoning[:2]}")  # Show first 2 reasons

        else:
            logger.warning("No candidates found!")

        total_tests += 1

    # Summary
    accuracy = accurate_tests / total_tests if total_tests > 0 else 0
    logger.info(f"\n" + "=" * 50)
    logger.info(f"SUMMARY")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Accurate: {accurate_tests}")
    logger.info(f"Accuracy: {accuracy:.1%}")

    if accuracy >= 0.75:
        logger.info("✓ Rule classifier performance acceptable (≥75%)")
    else:
        logger.warning("✗ Rule classifier performance below threshold")

    logger.info(f"Rule-based classification test completed!")

if __name__ == "__main__":
    main()