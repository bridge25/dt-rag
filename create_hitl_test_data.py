"""
Create test data for HITL (Human-in-the-Loop) system testing
Creates documents and chunks with low-confidence classifications
"""
import asyncio
import uuid
from datetime import datetime
from sqlalchemy import text
from apps.core.db_session import engine


async def create_hitl_test_data():
    """Create test documents and chunks requiring HITL review"""

    async with engine.begin() as conn:
        print("Creating HITL test data...")

        # Create test document 1: Ambiguous AI/ML content
        doc_id_1 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO documents (doc_id, source_url, created_at)
            VALUES (:doc_id, :source_url, :created_at)
        """), {
            "doc_id": doc_id_1,
            "source_url": "https://example.com/ai-ml-article",
            "created_at": datetime.utcnow()
        })
        print(f"✅ Created document 1: {doc_id_1}")

        # Create chunk 1 with low confidence
        chunk_id_1 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO chunks (chunk_id, doc_id, text, span, token_count, created_at)
            VALUES (:chunk_id, :doc_id, :text, :span, :token_count, :created_at)
        """), {
            "chunk_id": chunk_id_1,
            "doc_id": doc_id_1,
            "text": "This article discusses quantum machine learning algorithms for neural network optimization. The intersection of quantum computing and artificial intelligence presents unique challenges.",
            "span": "0,180",
            "token_count": 25,
            "created_at": datetime.utcnow()
        })
        print(f"✅ Created chunk 1: {chunk_id_1}")

        # Get a taxonomy node for classification
        result = await conn.execute(text("""
            SELECT node_id FROM taxonomy_nodes
            WHERE label = 'AI/ML' AND version = '1.0.0'
            LIMIT 1
        """))
        node = result.fetchone()

        if node:
            node_id = node[0]

            # Create doc_taxonomy entry with HITL required (low confidence)
            await conn.execute(text("""
                INSERT INTO doc_taxonomy (doc_id, node_id, version, path, confidence, hitl_required, created_at)
                VALUES (:doc_id, :node_id, :version, :path, :confidence, :hitl_required, :created_at)
                ON CONFLICT (doc_id, node_id, version) DO UPDATE
                SET confidence = EXCLUDED.confidence,
                    hitl_required = EXCLUDED.hitl_required
            """), {
                "doc_id": doc_id_1,
                "node_id": str(node_id),
                "version": "1.0.0",
                "path": ["Technology", "AI/ML"],
                "confidence": 0.62,  # Low confidence requiring HITL
                "hitl_required": True,
                "created_at": datetime.utcnow()
            })
            print("✅ Created doc_taxonomy entry with HITL required (confidence: 0.62)")

        # Create test document 2: Business/Technology ambiguity
        doc_id_2 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO documents (doc_id, source_url, created_at)
            VALUES (:doc_id, :source_url, :created_at)
        """), {
            "doc_id": doc_id_2,
            "source_url": "https://example.com/tech-business",
            "created_at": datetime.utcnow()
        })
        print(f"✅ Created document 2: {doc_id_2}")

        chunk_id_2 = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO chunks (chunk_id, doc_id, text, span, token_count, created_at)
            VALUES (:chunk_id, :doc_id, :text, :span, :token_count, :created_at)
        """), {
            "chunk_id": chunk_id_2,
            "doc_id": doc_id_2,
            "text": "Software development lifecycle management in enterprise environments requires both technical expertise and business acumen to align IT strategies with organizational goals.",
            "span": "0,175",
            "token_count": 24,
            "created_at": datetime.utcnow()
        })
        print(f"✅ Created chunk 2: {chunk_id_2}")

        # Get Software taxonomy node
        result = await conn.execute(text("""
            SELECT node_id FROM taxonomy_nodes
            WHERE label = 'Software' AND version = '1.0.0'
            LIMIT 1
        """))
        node = result.fetchone()

        if node:
            node_id = node[0]

            await conn.execute(text("""
                INSERT INTO doc_taxonomy (doc_id, node_id, version, path, confidence, hitl_required, created_at)
                VALUES (:doc_id, :node_id, :version, :path, :confidence, :hitl_required, :created_at)
                ON CONFLICT (doc_id, node_id, version) DO UPDATE
                SET confidence = EXCLUDED.confidence,
                    hitl_required = EXCLUDED.hitl_required
            """), {
                "doc_id": doc_id_2,
                "node_id": str(node_id),
                "version": "1.0.0",
                "path": ["Technology", "Software"],
                "confidence": 0.58,  # Low confidence requiring HITL
                "hitl_required": True,
                "created_at": datetime.utcnow()
            })
            print("✅ Created doc_taxonomy entry with HITL required (confidence: 0.58)")

        # Verify HITL tasks created
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM doc_taxonomy WHERE hitl_required = true
        """))
        count = result.scalar()
        print(f"\n✅ Total HITL tasks in database: {count}")

        # Show sample HITL tasks
        result = await conn.execute(text("""
            SELECT
                dt.doc_id,
                dt.path,
                dt.confidence,
                c.text,
                c.chunk_id
            FROM doc_taxonomy dt
            JOIN chunks c ON c.doc_id = dt.doc_id
            WHERE dt.hitl_required = true
            LIMIT 5
        """))

        print("\n📋 Sample HITL tasks created:")
        for row in result.fetchall():
            print(f"  - Chunk: {row[4]}")
            print(f"    Path: {row[1]}")
            print(f"    Confidence: {row[2]:.2f}")
            print(f"    Text: {row[3][:80]}...")
            print()


async def main():
    """Main entry point"""
    try:
        await create_hitl_test_data()
        print("✅ HITL test data creation completed successfully!")
    except Exception as e:
        print(f"❌ Error creating HITL test data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
