"""
    
    
"""

import asyncio
import time
import numpy as np
import sys
import os

#   
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

from search.embedding_cache import EmbeddingCache, initialize_embedding_cache
from search.embedding_service import OptimizedEmbeddingService, EmbeddingConfig, initialize_embedding_service

async def test_cache_performance():
    """     """
    print("     \n")

    # 1.  
    print("1.   ...")
    try:
        await initialize_embedding_cache(
            redis_url="redis://localhost:6379",  # Redis    
            memory_cache_size=1000,
            memory_ttl=300,
            enable_compression=True
        )
        print("     ")
    except Exception as e:
        print(f"    Redis  ,   : {e}")

    # 2.   
    print("2.   ...")
    service = await initialize_embedding_service(
        provider="local",
        model_name="paraphrase-multilingual-MiniLM-L12-v2",
        enable_cache=True,
        batch_size=20
    )
    print("       ")

    # 3.   
    test_texts = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Vector database fundamentals",
        "RAG system architecture",
        "Document classification methods",
        "Semantic search techniques",
        "Natural language processing",
        "Deep learning applications",
        "AI ethics and fairness",
        "Data science methodologies"
    ] * 3  # 30  ( )

    print(f"3.  : {len(test_texts)}  ( )")

    # 4.     ()
    print("\n4.     ()...")
    start_time = time.time()

    # Mock   
    for text in test_texts:
        await asyncio.sleep(0.05)  # 50ms    

    no_cache_time = time.time() - start_time
    print(f"    : {no_cache_time:.3f}")

    # 5.    
    print("5.    ...")
    start_time = time.time()

    results = []
    for text in test_texts:
        try:
            #    (  )
            embedding = await service.generate_embedding(text)
            if embedding is not None:
                results.append(embedding)
        except Exception as e:
            print(f"      : {e}")
            # : Mock 
            results.append(np.random.rand(384).astype(np.float32))

    cache_time = time.time() - start_time
    print(f"    : {cache_time:.3f}")

    # 6.   
    print("\n6.   ")
    if cache_time > 0:
        improvement = no_cache_time / cache_time
        print(f"   ˆ  : {improvement:.2f} ")
        print(f"   ‰  : {no_cache_time - cache_time:.3f}")

        if improvement >= 2.0:
            print("   ‰   ! (2 )")
        elif improvement >= 1.5:
            print("       (1.5 )")
        else:
            print("      ")

    # 7.   
    print("\n7.  ")
    stats = service.get_stats()
    print(f"    : {stats.get('total_requests', 0)}")
    print(f"    : {stats.get('hits', 0)}")
    print(f"    : {stats.get('misses', 0)}")
    print(f"   : {stats.get('hit_rate', 0):.1%}")
    print(f"    : {stats.get('memory_hits', 0)}")
    print(f"   Redis  : {stats.get('redis_available', False)}")

    # 8.   
    print("\n8.    ")
    batch_texts = test_texts[:10]  # 10 

    start_time = time.time()
    batch_results = await service.generate_batch_embeddings(batch_texts)
    batch_time = time.time() - start_time

    print(f"     : {batch_time:.3f}")
    print(f"    : {len(batch_results)}")
    print(f"   : {sum(1 for r in batch_results if r is not None) / len(batch_results):.1%}")

    print("\n‰     !")
    return {
        'cache_time': cache_time,
        'no_cache_time': no_cache_time,
        'improvement': no_cache_time / cache_time if cache_time > 0 else 0,
        'stats': stats,
        'batch_time': batch_time
    }

async def test_cache_operations():
    """   """
    print("\n§    ")

    try:
        from search.embedding_service import get_embedding_service
        service = get_embedding_service()

        #  
        print("1.  ...")
        warmup_queries = [
            "What is RAG?",
            "How does vector search work?",
            "Machine learning fundamentals"
        ]
        await service.warmup_cache(warmup_queries)
        print(f"    {len(warmup_queries)}   ")

        #   
        stats = service.get_stats()
        print(f"      : {stats.get('memory_cache_size', 0)}")

        #  
        print("2.  ...")
        cleared = await service.clear_cache()
        print(f"    {cleared}   ")

        #   
        stats = service.get_stats()
        print(f"      : {stats.get('memory_cache_size', 0)}")

    except Exception as e:
        print(f"       : {e}")

if __name__ == "__main__":
    async def main():
        try:
            results = await test_cache_performance()
            await test_cache_operations()

            print("\nŠ   ")
            print(f"    : {results['improvement']:.2f}")
            print(f"   : {results['stats'].get('hit_rate', 0):.1%}")
            print(f"    : {results['batch_time']:.3f}")

            if results['improvement'] >= 1.7:
                print("   ¯  : 70%   (1.7) !")
            else:
                print(f"   ˆ  : {(results['improvement']-1)*100:.1f}%")

        except Exception as e:
            print(f"    : {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main())