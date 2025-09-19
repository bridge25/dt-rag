#!/usr/bin/env python3
"""
Add test data for hybrid search benchmarking
Create sample documents and chunks for performance testing
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add project root path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def add_sample_documents():
    """Add sample documents and chunks for testing"""
    print("=== Adding Sample Test Data ===")

    try:
        from database import db_manager
        from sqlalchemy import text

        async with db_manager.async_session() as session:
            # Sample documents data
            sample_docs = [
                {
                    "title": "Introduction to Machine Learning",
                    "source_url": "https://example.com/ml-intro",
                    "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms and statistical models to analyze and draw inferences from patterns in data.",
                    "taxonomy": ["AI", "ML"]
                },
                {
                    "title": "Vector Similarity Search Guide",
                    "source_url": "https://example.com/vector-search",
                    "content": "Vector similarity search is a fundamental technique in information retrieval and machine learning. It involves converting documents and queries into high-dimensional vectors and finding the most similar vectors using distance metrics like cosine similarity.",
                    "taxonomy": ["AI", "Search"]
                },
                {
                    "title": "BM25 Algorithm Explained",
                    "source_url": "https://example.com/bm25",
                    "content": "BM25 is a probabilistic ranking function used in information retrieval. It estimates the relevance of documents to a given search query based on term frequency, document frequency, and document length normalization.",
                    "taxonomy": ["Search", "Algorithm"]
                },
                {
                    "title": "Hybrid Search Systems",
                    "source_url": "https://example.com/hybrid-search",
                    "content": "Hybrid search systems combine multiple retrieval methods to improve search accuracy. Common approaches include combining BM25 keyword search with vector similarity search, and using cross-encoder reranking for final result optimization.",
                    "taxonomy": ["Search", "Hybrid"]
                },
                {
                    "title": "Natural Language Processing Fundamentals",
                    "source_url": "https://example.com/nlp",
                    "content": "Natural Language Processing (NLP) is a branch of artificial intelligence that deals with the interaction between computers and humans through natural language. It includes tasks like text classification, sentiment analysis, and language translation.",
                    "taxonomy": ["AI", "NLP"]
                },
                {
                    "title": "Deep Learning Neural Networks",
                    "source_url": "https://example.com/deep-learning",
                    "content": "Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers to model and understand complex patterns in data. It has revolutionized fields like computer vision and natural language processing.",
                    "taxonomy": ["AI", "Deep Learning"]
                },
                {
                    "title": "Information Retrieval Systems",
                    "source_url": "https://example.com/ir-systems",
                    "content": "Information retrieval systems are designed to find relevant information from large collections of data. They use various techniques including indexing, ranking algorithms, and query processing to provide accurate search results.",
                    "taxonomy": ["Search", "IR"]
                },
                {
                    "title": "Embedding Models in AI",
                    "source_url": "https://example.com/embeddings",
                    "content": "Embedding models convert text, images, or other data into dense vector representations that capture semantic meaning. These embeddings are crucial for tasks like similarity search, clustering, and recommendation systems.",
                    "taxonomy": ["AI", "Embeddings"]
                },
                {
                    "title": "Cross-Encoder Reranking",
                    "source_url": "https://example.com/cross-encoder",
                    "content": "Cross-encoder reranking is a technique used to improve search result quality by re-scoring candidate documents using a more sophisticated model. It provides better accuracy than bi-encoder approaches but at higher computational cost.",
                    "taxonomy": ["Search", "Reranking"]
                },
                {
                    "title": "Document Classification Techniques",
                    "source_url": "https://example.com/doc-classification",
                    "content": "Document classification is the task of automatically assigning categories or labels to documents based on their content. It uses machine learning algorithms and natural language processing techniques to analyze text features.",
                    "taxonomy": ["AI", "Classification"]
                }
            ]

            print(f"Adding {len(sample_docs)} sample documents...")

            for i, doc_data in enumerate(sample_docs):
                try:
                    # Insert document
                    doc_id = str(uuid.uuid4())
                    doc_insert = text("""
                        INSERT INTO documents (doc_id, title, source_url, content_type, file_size, chunk_metadata, processed_at)
                        VALUES (:doc_id, :title, :source_url, :content_type, :file_size, :chunk_metadata, :processed_at)
                    """)

                    await session.execute(doc_insert, {
                        "doc_id": doc_id,
                        "title": doc_data["title"],
                        "source_url": doc_data["source_url"],
                        "content_type": "text/plain",
                        "file_size": len(doc_data["content"]),
                        "chunk_metadata": "{}",
                        "processed_at": datetime.utcnow()
                    })

                    # Insert chunks (split content into smaller chunks)
                    content = doc_data["content"]
                    sentences = content.split('. ')

                    for j, sentence in enumerate(sentences):
                        if sentence.strip():
                            chunk_id = str(uuid.uuid4())
                            chunk_text = sentence.strip() + '.'

                            chunk_insert = text("""
                                INSERT INTO chunks (chunk_id, doc_id, text, span, chunk_index, chunk_metadata, created_at)
                                VALUES (:chunk_id, :doc_id, :text, :span, :chunk_index, :chunk_metadata, :created_at)
                            """)

                            await session.execute(chunk_insert, {
                                "chunk_id": chunk_id,
                                "doc_id": doc_id,
                                "text": chunk_text,
                                "span": f"0-{len(chunk_text)}",
                                "chunk_index": j,
                                "chunk_metadata": "{}",
                                "created_at": datetime.utcnow()
                            })

                    # Insert taxonomy relationship
                    tax_path = doc_data["taxonomy"]
                    mapping_id = str(uuid.uuid4())
                    tax_insert = text("""
                        INSERT INTO doc_taxonomy (mapping_id, doc_id, path, confidence, source, assigned_at)
                        VALUES (:mapping_id, :doc_id, :path, :confidence, :source, :assigned_at)
                    """)

                    await session.execute(tax_insert, {
                        "mapping_id": mapping_id,
                        "doc_id": doc_id,
                        "path": str(tax_path),  # Store as string for SQLite compatibility
                        "confidence": 1.0,
                        "source": "test_data",
                        "assigned_at": datetime.utcnow()
                    })

                    print(f"  Added document {i+1}: {doc_data['title']}")

                except Exception as e:
                    print(f"  Error adding document {i+1}: {e}")

            # Commit all changes
            await session.commit()
            print("OK All sample documents added successfully")

            # Verify data insertion
            count_query = text("SELECT COUNT(*) FROM documents")
            result = await session.execute(count_query)
            doc_count = result.scalar()

            chunk_count_query = text("SELECT COUNT(*) FROM chunks")
            result = await session.execute(chunk_count_query)
            chunk_count = result.scalar()

            print(f"Total documents in database: {doc_count}")
            print(f"Total chunks in database: {chunk_count}")

    except Exception as e:
        print(f"ERROR Failed to add sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def generate_embeddings():
    """Generate embeddings for all chunks"""
    print("\n=== Generating Embeddings ===")

    try:
        from database import db_manager, EmbeddingService
        from sqlalchemy import text

        async with db_manager.async_session() as session:
            # Get all chunks without embeddings
            chunks_query = text("""
                SELECT c.chunk_id, c.text
                FROM chunks c
                LEFT JOIN embeddings e ON c.chunk_id = e.chunk_id
                WHERE e.chunk_id IS NULL
                LIMIT 50
            """)

            result = await session.execute(chunks_query)
            chunks = result.fetchall()

            print(f"Generating embeddings for {len(chunks)} chunks...")

            for i, (chunk_id, text_content) in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = await EmbeddingService.generate_embedding(text_content)

                    # Insert embedding
                    embedding_id = str(uuid.uuid4())
                    embedding_insert = text("""
                        INSERT INTO embeddings (embedding_id, chunk_id, vec, model_name, created_at)
                        VALUES (:embedding_id, :chunk_id, :vec, :model_name, :created_at)
                    """)

                    await session.execute(embedding_insert, {
                        "embedding_id": embedding_id,
                        "chunk_id": chunk_id,
                        "vec": str(embedding),  # Store as string for SQLite
                        "model_name": "openai",
                        "created_at": datetime.utcnow()
                    })

                    if (i + 1) % 5 == 0:
                        print(f"  Generated {i + 1}/{len(chunks)} embeddings")

                except Exception as e:
                    print(f"  Error generating embedding for chunk {i+1}: {e}")

            await session.commit()
            print("OK All embeddings generated successfully")

            # Verify embeddings
            embedding_count_query = text("SELECT COUNT(*) FROM embeddings")
            result = await session.execute(embedding_count_query)
            embedding_count = result.scalar()
            print(f"Total embeddings in database: {embedding_count}")

    except Exception as e:
        print(f"ERROR Failed to generate embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def verify_search_functionality():
    """Verify that search works with new data"""
    print("\n=== Verifying Search Functionality ===")

    try:
        from database import SearchDAO

        test_queries = [
            "machine learning",
            "vector similarity",
            "BM25 algorithm",
            "hybrid search",
            "neural networks"
        ]

        for query in test_queries:
            try:
                start_time = asyncio.get_event_loop().time()
                results = await SearchDAO.hybrid_search(
                    query=query,
                    filters=None,
                    topk=3,
                    bm25_topk=5,
                    vector_topk=5,
                    rerank_candidates=10
                )
                search_time = (asyncio.get_event_loop().time() - start_time) * 1000

                print(f"Query: '{query}'")
                print(f"  Results: {len(results)}")
                print(f"  Search time: {search_time:.1f}ms")

                if results:
                    top_result = results[0]
                    score = top_result.get('score', 0)
                    text_preview = str(top_result.get('text', ''))[:60] + '...'
                    print(f"  Top result: {score:.3f} - {text_preview}")

                print()

            except Exception as e:
                print(f"  Search failed for '{query}': {e}")

    except Exception as e:
        print(f"ERROR Search verification failed: {e}")

async def main():
    """Main execution function"""
    print("Dynamic Taxonomy RAG v1.8.1 - Test Data Setup")
    print("="*50)

    # Add sample documents and chunks
    if await add_sample_documents():
        # Generate embeddings for the chunks
        if await generate_embeddings():
            # Verify search functionality
            await verify_search_functionality()

            print("\n" + "="*50)
            print("Test data setup completed successfully!")
            print("You can now run performance benchmarks with real data.")
        else:
            print("Failed to generate embeddings.")
    else:
        print("Failed to add sample documents.")

if __name__ == "__main__":
    asyncio.run(main())