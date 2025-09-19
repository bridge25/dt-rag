#!/usr/bin/env python3
"""
Quick test of the hybrid search system with fixed column names
"""
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from apps.search.hybrid_search_engine import HybridSearchEngine
from apps.api.database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Quick test of hybrid search system"""
    try:
        print("Starting quick hybrid search test...")

        # Create search engine
        search_engine = HybridSearchEngine()

        # Get database session
        async with db_manager.async_session() as session:
            # Test search
            query = "machine learning algorithms"
            response = await search_engine.search(
                session=session,
                query=query,
                filters={}
            )

            results = response.results
            print(f"Search for '{query}' returned {len(results)} results")
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"  {i+1}. Score: {result.score:.4f}, Text: {result.text[:100]}...")

        print("[OK] Quick hybrid search test completed successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        logging.exception("Test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)