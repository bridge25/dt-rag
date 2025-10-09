"""
Sample document ingestion script for DT-RAG v1.8.1
Directly inserts documents with chunking and embeddings into the database
"""
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from apps.core.db_session import async_session
from apps.api.embedding_service import EmbeddingService
from sqlalchemy import text

async def chunk_text(text: str, chunk_size: int = 500, overlap: int = 128) -> list[dict]:
    """Simple chunking strategy: split by sentences, group into chunks"""
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_text = ' '.join(words[start:end])
        chunks.append({
            'text': chunk_text,
            'span': f'[{start},{end})',
            'token_count': end - start
        })
        start += chunk_size - overlap

    return chunks

async def ingest_document(file_path: Path):
    """Ingest a single document with chunking and embeddings"""
    print(f"\n[Processing] {file_path.name}")

    # Read document content
    content = file_path.read_text(encoding='utf-8')

    # Initialize embedding service
    embedding_service = EmbeddingService()

    async with async_session() as session:
        # 1. Create document record
        doc_id = uuid.uuid4()
        doc_query = text("""
            INSERT INTO documents (doc_id, source_url, version_tag, license_tag, created_at)
            VALUES (:doc_id, :source_url, :version_tag, :license_tag, NOW())
        """)
        await session.execute(doc_query, {
            'doc_id': doc_id,
            'source_url': f'file:///{file_path}',
            'version_tag': '1.0.0',
            'license_tag': 'sample'
        })
        print(f"  [OK] Document created: {doc_id}")

        # 2. Create chunks
        chunks = await chunk_text(content)
        print(f"  [Chunks] Created {len(chunks)} chunks")

        chunk_ids = []
        for i, chunk_data in enumerate(chunks):
            chunk_id = uuid.uuid4()
            chunk_ids.append(chunk_id)

            chunk_query = text("""
                INSERT INTO chunks (chunk_id, doc_id, text, span, token_count, created_at)
                VALUES (:chunk_id, :doc_id, :text, :span, :token_count, NOW())
            """)
            await session.execute(chunk_query, {
                'chunk_id': chunk_id,
                'doc_id': doc_id,
                'text': chunk_data['text'],
                'span': chunk_data['span'],
                'token_count': chunk_data['token_count']
            })

        # 3. Generate embeddings
        print(f"  [Embeddings] Generating embeddings...")
        for chunk_id, chunk_data in zip(chunk_ids, chunks):
            # Generate embedding
            embedding = await embedding_service.generate_embedding(chunk_data['text'])

            # Convert to PostgreSQL vector format
            vec_str = '[' + ','.join(map(str, embedding)) + ']'

            embedding_query = text("""
                INSERT INTO embeddings (embedding_id, chunk_id, vec, model_name, created_at)
                VALUES (:embedding_id, :chunk_id, CAST(:vec AS vector), :model_name, NOW())
            """)
            await session.execute(embedding_query, {
                'embedding_id': uuid.uuid4(),
                'chunk_id': chunk_id,
                'vec': vec_str,
                'model_name': 'text-embedding-3-large'
            })

        print(f"  [OK] {len(chunk_ids)} embeddings created")

        # 4. Add taxonomy classification
        # Get AI/ML taxonomy node
        tax_query = text("""
            SELECT node_id FROM taxonomy_nodes
            WHERE label = 'AI/ML' AND version = '1.0.0'
            LIMIT 1
        """)
        result = await session.execute(tax_query)
        tax_node = result.fetchone()

        if tax_node:
            doc_tax_query = text("""
                INSERT INTO doc_taxonomy (doc_id, node_id, version, path, confidence, hitl_required, created_at)
                VALUES (:doc_id, :node_id, :version, :path, :confidence, :hitl_required, NOW())
            """)
            await session.execute(doc_tax_query, {
                'doc_id': doc_id,
                'node_id': tax_node[0],
                'version': '1.0.0',
                'path': ['Technology', 'AI/ML'],
                'confidence': 0.95,
                'hitl_required': False
            })
            print(f"  [Taxonomy] Classified as: Technology > AI/ML")

        await session.commit()
        print(f"  [OK] Document ingestion complete!\n")

        return doc_id

async def main():
    """Ingest all sample documents"""
    print("=" * 60)
    print("DT-RAG v1.8.1 - Sample Document Ingestion")
    print("=" * 60)

    # Get sample documents
    sample_dir = Path("sample_docs")
    if not sample_dir.exists():
        print("[ERROR] sample_docs directory not found")
        return

    doc_files = list(sample_dir.glob("*.txt"))
    print(f"\n[Found] {len(doc_files)} documents to ingest\n")

    # Ingest each document
    doc_ids = []
    for doc_file in doc_files:
        try:
            doc_id = await ingest_document(doc_file)
            doc_ids.append(doc_id)
        except Exception as e:
            print(f"  [ERROR] Error ingesting {doc_file.name}: {e}")

    # Summary
    print("=" * 60)
    print(f"[OK] Ingestion Complete!")
    print(f"   Documents processed: {len(doc_ids)}")
    print(f"   Document IDs: {[str(d)[:8] + '...' for d in doc_ids]}")
    print("=" * 60)

    # Verify chunks and embeddings
    async with async_session() as session:
        count_query = text("""
            SELECT
                (SELECT COUNT(*) FROM documents) as docs,
                (SELECT COUNT(*) FROM chunks) as chunks,
                (SELECT COUNT(*) FROM embeddings) as embeddings
        """)
        result = await session.execute(count_query)
        counts = result.fetchone()

        print(f"\n[Statistics] Database Statistics:")
        print(f"   Documents: {counts[0]}")
        print(f"   Chunks: {counts[1]}")
        print(f"   Embeddings: {counts[2]}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
