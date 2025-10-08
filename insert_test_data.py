"""
간단한 테스트 데이터 삽입 스크립트
바이브코딩 원칙: 최소한의 데이터로 시스템 작동 확인
"""
import asyncio
import os
from sqlalchemy import text
from apps.core.db_session import async_session
from apps.api.embedding_service import embedding_service

async def insert_test_data():
    """3개의 테스트 문서와 임베딩 삽입"""
    async with async_session() as session:
        try:
            # 1. 문서 3개 삽입
            doc_insert_sql = text("""
                INSERT INTO documents (source_url, version_tag, license_tag)
                VALUES
                    ('https://example.com/ml', 'v1.0', 'MIT'),
                    ('https://example.com/rag', 'v1.0', 'MIT'),
                    ('https://example.com/python', 'v1.0', 'MIT')
                RETURNING doc_id
            """)

            result = await session.execute(doc_insert_sql)
            doc_ids = [row[0] for row in result.fetchall()]
            print(f"[OK] 문서 3개 삽입 완료: {doc_ids}")

            # 2. 각 문서에 chunk 삽입
            test_texts = [
                "Machine learning is a method of data analysis that automates analytical model building.",
                "RAG (Retrieval-Augmented Generation) combines retrieval systems with language models.",
                "Python is a high-level programming language widely used for data science and machine learning."
            ]

            chunk_ids = []
            for doc_id, content_text in zip(doc_ids, test_texts):
                chunk_insert_sql = text("""
                    INSERT INTO chunks (doc_id, text, span, token_count)
                    VALUES (:doc_id, :text, '[0,100)', :token_count)
                    RETURNING chunk_id
                """)

                result = await session.execute(
                    chunk_insert_sql,
                    {"doc_id": doc_id, "text": content_text, "token_count": len(content_text.split())}
                )
                chunk_id = result.scalar()
                chunk_ids.append(chunk_id)

            print(f"[OK] Chunk 3개 삽입 완료: {chunk_ids}")

            # 3. 각 chunk에 임베딩 생성 및 삽입
            for chunk_id, content_text in zip(chunk_ids, test_texts):
                # 임베딩 생성
                embedding = await embedding_service.generate_embedding(content_text)

                # PostgreSQL vector 형식으로 변환
                vec_str = '[' + ','.join(map(str, embedding)) + ']'

                # asyncpg는 named parameter 사용할 수 없으므로 f-string 사용
                embedding_insert_sql = text(f"""
                    INSERT INTO embeddings (chunk_id, vec, model_name)
                    VALUES ('{chunk_id}', '{vec_str}'::vector, 'text-embedding-3-large')
                """)

                await session.execute(embedding_insert_sql)

            print(f"[OK] 임베딩 3개 삽입 완료")

            # 4. Taxonomy 매핑 (선택적)
            tech_node_sql = text("""
                SELECT node_id FROM taxonomy_nodes
                WHERE label = 'AI/ML' AND version = '1.0.0'
                LIMIT 1
            """)
            result = await session.execute(tech_node_sql)
            tech_node_id = result.scalar()

            if tech_node_id:
                for doc_id in doc_ids[:2]:  # 처음 2개 문서만 AI/ML 카테고리로
                    taxonomy_insert_sql = text("""
                        INSERT INTO doc_taxonomy (doc_id, node_id, version, path, confidence)
                        VALUES (:doc_id, :node_id, '1.0.0', ARRAY['Technology', 'AI/ML'], 0.95)
                        ON CONFLICT DO NOTHING
                    """)
                    await session.execute(
                        taxonomy_insert_sql,
                        {"doc_id": doc_id, "node_id": tech_node_id}
                    )
                print(f"[OK] Taxonomy 매핑 완료")

            await session.commit()

            # 5. 검증
            count_sql = text("""
                SELECT
                    (SELECT COUNT(*) FROM documents) as docs,
                    (SELECT COUNT(*) FROM chunks) as chunks,
                    (SELECT COUNT(*) FROM embeddings WHERE vec IS NOT NULL) as embeddings
            """)
            result = await session.execute(count_sql)
            row = result.fetchone()

            print(f"\n[DATA] 최종 데이터 개수:")
            print(f"   - 문서: {row[0]}")
            print(f"   - Chunks: {row[1]}")
            print(f"   - 임베딩: {row[2]}")

            return True

        except Exception as e:
            print(f"[ERROR] 오류 발생: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    print("[START] 테스트 데이터 삽입 시작...")
    asyncio.run(insert_test_data())
    print("[DONE] 완료!")
