import asyncio
from apps.search.hybrid_search_engine import hybrid_search

async def main():
    query = "What is RAG system?"
    print(f"Searching for: {query}\n")

    results, metrics = await hybrid_search(
        query=query,
        top_k=5,
        filters={}
    )

    print(f"Found {len(results)} results in {metrics['total_time']:.2f}s\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.get('score', 0):.3f}")
        print(f"   Text: {result.get('text', '')[:80]}...")
        print(f"   Source: {result.get('source_url', 'N/A')}\n")

asyncio.run(main())
