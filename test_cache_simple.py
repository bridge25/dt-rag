"""
Simple embedding cache test
"""

import asyncio
import time
import numpy as np
import sys
import os

# Add project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

from search.embedding_cache import EmbeddingCache

async def simple_cache_test():
    print("Starting embedding cache test...")

    # Create cache instance
    cache = EmbeddingCache(
        redis_url="redis://localhost:6379",
        memory_cache_size=100,
        memory_ttl=300,
        enable_compression=False
    )

    # Redis will likely fail, so disable it
    cache.redis_client = None

    try:
        # Test embedding
        test_embedding = np.random.rand(768).astype(np.float32)
        test_text = "test embedding text"

        print("1. Testing cache miss...")
        result = await cache.get_embedding(test_text)
        print(f"   Cache miss result: {result is None}")

        print("2. Testing cache set...")
        success = await cache.set_embedding(test_text, test_embedding)
        print(f"   Set success: {success}")

        print("3. Testing cache hit...")
        cached_result = await cache.get_embedding(test_text)
        hit_success = cached_result is not None and np.array_equal(cached_result, test_embedding)
        print(f"   Cache hit success: {hit_success}")

        print("4. Cache statistics...")
        stats = cache.get_stats()
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Hits: {stats['hits']}, Misses: {stats['misses']}")
        print(f"   Hit rate: {stats['hit_rate']:.2%}")

        print("\nCache test completed successfully!")

    except Exception as e:
        print(f"Cache test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cache.close()

if __name__ == "__main__":
    asyncio.run(simple_cache_test())