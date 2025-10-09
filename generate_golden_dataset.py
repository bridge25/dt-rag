"""
Generate Golden Dataset from Database Documents

This script:
1. Fetches documents from PostgreSQL database
2. Generates synthetic test data using RAGAS or Gemini
3. Saves golden dataset for RAG evaluation
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main execution function"""

    # Import after setting up path
    from apps.evaluation.golden_dataset_generator import (
        GoldenDatasetGenerator,
        create_golden_dataset_from_db
    )

    logger.info("=" * 60)
    logger.info("Golden Dataset Generation for DT-RAG v1.8.1")
    logger.info("=" * 60)

    # Check API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not gemini_key and not openai_key:
        logger.error("ERROR: No API keys found!")
        logger.error("Please set GEMINI_API_KEY or OPENAI_API_KEY environment variable")
        logger.error("Example: export GEMINI_API_KEY='your-key-here'")
        return

    if gemini_key:
        logger.info("✓ GEMINI_API_KEY found")
    if openai_key:
        logger.info("✓ OPENAI_API_KEY found")

    logger.info("")
    logger.info("Configuration:")
    logger.info(f"  Target samples: 100")
    logger.info(f"  Query distribution:")
    logger.info(f"    - Simple (factual): 50%")
    logger.info(f"    - Reasoning: 25%")
    logger.info(f"    - Multi-context: 25%")
    logger.info("")

    try:
        # Generate golden dataset from database
        logger.info("Step 1: Fetching documents from database...")
        output_path = await create_golden_dataset_from_db(testset_size=100)

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Golden Dataset Generated Successfully!")
        logger.info("=" * 60)
        logger.info(f"Output file: {output_path}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Review the generated dataset")
        logger.info("2. Run RAGAS evaluation: python evaluate_rag_system.py")
        logger.info("3. Analyze results and iterate")

    except Exception as e:
        logger.error(f"Failed to generate golden dataset: {e}", exc_info=True)
        return

if __name__ == "__main__":
    asyncio.run(main())
