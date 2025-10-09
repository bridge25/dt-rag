"""
Quick Golden Dataset Generation (Small Scale Demo)

Generates 10 samples for demonstration
"""

import asyncio
import logging
from apps.evaluation.golden_dataset_generator import create_golden_dataset_from_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Generating small golden dataset (10 samples)...")

    try:
        output_path = await create_golden_dataset_from_db(testset_size=10)
        logger.info(f"✅ Success! Dataset saved to: {output_path}")
    except Exception as e:
        logger.error(f"❌ Failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
