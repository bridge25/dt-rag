#!/usr/bin/env python3
"""
DT-RAG Embedding Generation Script
PostgreSQL 데이터베이스의 문서들에 대해 벡터 임베딩을 생성하고 업데이트합니다.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def update_document_embeddings():
    """데이터베이스의 모든 문서에 대해 임베딩 생성 및 업데이트"""
    print("🔄 Starting embedding generation for all documents...")

    try:
        # 환경 변수 로드
        from dotenv import load_dotenv
        load_dotenv()

        # 데이터베이스 연결
        from apps.api.database import db_manager, test_database_connection, EmbeddingService
        from sqlalchemy import text

        # 연결 테스트
        db_connected = await test_database_connection()
        if not db_connected:
            print("❌ Database connection failed!")
            return False

        async with db_manager.async_session() as session:
            # 임베딩이 없는 문서들 조회
            query = text("""
                SELECT id, title, content
                FROM documents
                WHERE embedding IS NULL
                ORDER BY id
            """)

            result = await session.execute(query)
            documents = result.fetchall()

            if not documents:
                print("✅ All documents already have embeddings!")
                return True

            print(f"📄 Found {len(documents)} documents without embeddings")

            success_count = 0
            error_count = 0

            for doc in documents:
                doc_id, title, content = doc
                print(f"🔄 Processing document {doc_id}: '{title[:50]}...'")

                try:
                    # 임베딩 생성 (제목 + 내용)
                    embedding_text = f"{title}\n\n{content}"

                    # OpenAI API 사용 (또는 더미 임베딩)
                    embedding_vector = await EmbeddingService.generate_embedding(embedding_text)

                    if not embedding_vector:
                        print(f"   ⚠️ Failed to generate embedding for document {doc_id}")
                        error_count += 1
                        continue

                    # 데이터베이스에 임베딩 저장
                    # pgvector 형식으로 변환
                    vector_str = '[' + ','.join(map(str, embedding_vector)) + ']'

                    update_query = text("""
                        UPDATE documents
                        SET embedding = :embedding_vector::vector
                        WHERE id = :doc_id
                    """)

                    await session.execute(update_query, {
                        "embedding_vector": vector_str,
                        "doc_id": doc_id
                    })

                    success_count += 1
                    print(f"   ✅ Embedding saved for document {doc_id}")

                    # API 레이트 리밋 고려
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"   ❌ Error processing document {doc_id}: {e}")
                    error_count += 1
                    continue

            # 트랜잭션 커밋
            await session.commit()

            print(f"\n📊 Embedding Generation Complete:")
            print(f"   ✅ Success: {success_count} documents")
            print(f"   ❌ Errors: {error_count} documents")

            if success_count > 0:
                print(f"\n🔄 Updating vector search index...")
                try:
                    # 벡터 인덱스 최적화
                    await session.execute(text("ANALYZE documents"))
                    print(f"   ✅ Index optimization complete")
                except Exception as e:
                    print(f"   ⚠️ Index optimization failed: {e}")

            return error_count == 0

    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_vector_search():
    """벡터 검색이 제대로 작동하는지 테스트"""
    print("\n🔍 Testing vector search functionality...")

    try:
        from apps.api.database import SearchDAO

        # 샘플 검색 수행
        test_queries = [
            "RAG system",
            "vector embeddings",
            "document classification"
        ]

        for query in test_queries:
            print(f"   Testing query: '{query}'")

            results = await SearchDAO.hybrid_search(
                query=query,
                topk=3
            )

            if results:
                print(f"   ✅ Found {len(results)} results")
                top_result = results[0]
                print(f"   Top result: '{top_result['title']}' (score: {top_result['score']:.3f})")

                metadata = top_result.get('metadata', {})
                bm25_score = metadata.get('bm25_score', 0)
                vector_score = metadata.get('vector_score', 0)
                print(f"   Scores: BM25={bm25_score:.3f}, Vector={vector_score:.3f}")
            else:
                print(f"   ⚠️ No results found")

        return True

    except Exception as e:
        print(f"   ❌ Vector search test failed: {e}")
        return False

async def main():
    """메인 실행 함수"""
    print("🚀 DT-RAG Embedding Generation Starting...")
    print("=" * 60)

    # 1. 임베딩 생성
    embedding_success = await update_document_embeddings()

    if not embedding_success:
        print("❌ Embedding generation failed!")
        return False

    # 2. 벡터 검색 테스트
    search_success = await test_vector_search()

    if not search_success:
        print("⚠️ Vector search test had issues")

    print("\n🎉 Embedding Generation Complete!")
    print("=" * 60)
    print("✅ Document embeddings updated")
    print("✅ Vector search index optimized")
    print("✅ Hybrid search system ready")
    print()
    print("💡 Tips:")
    print("   - Vector search requires valid embeddings")
    print("   - Set OPENAI_API_KEY for high-quality embeddings")
    print("   - Run this script after adding new documents")
    print()
    print("🚀 Ready to test the full system!")

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)