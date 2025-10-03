"""
Generate Golden Dataset from PostgreSQL Database

Retrieves documents and chunks from the database and generates
50+ golden dataset samples using RAGAS framework.
"""

import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main function to generate golden dataset from database"""

    from apps.core.db_session import async_session
    from apps.api.database import Document, DocumentChunk
    from apps.evaluation.golden_dataset_generator import GoldenDatasetGenerator, GoldenSample
    from sqlalchemy import select

    logger.info("Starting golden dataset generation from database...")

    async with async_session() as session:
        result = await session.execute(select(DocumentChunk).limit(200))
        chunks = result.scalars().all()

        logger.info(f"Retrieved {len(chunks)} chunks from database")

        if len(chunks) == 0:
            logger.error("No chunks found in database. Please run document ingestion first.")
            logger.info("To ingest documents, use: POST /api/v1/ingestion/upload")
            return

        documents = []
        for chunk in chunks:
            doc_dict = {
                "text": chunk.text,
                "doc_id": str(chunk.doc_id),
                "chunk_id": str(chunk.chunk_id),
                "title": f"Document {chunk.doc_id}",
                "taxonomy_path": chunk.chunk_metadata.get("taxonomy_path") if chunk.chunk_metadata else None
            }
            documents.append(doc_dict)

        logger.info(f"Prepared {len(documents)} document chunks for generation")

        generator = GoldenDatasetGenerator(output_dir="golden_datasets")

        target_size = max(50, min(100, len(documents) // 2))
        logger.info(f"Generating {target_size} golden samples...")

        samples = await generator.generate_from_documents(
            documents=documents,
            testset_size=target_size,
            query_distribution={
                "simple": 0.5,
                "reasoning": 0.25,
                "multi_context": 0.25
            }
        )

        if not samples:
            logger.warning("No samples generated. Falling back to manual sample creation...")
            samples = []
            for i, chunk in enumerate(chunks[:50]):
                sample = GoldenSample(
                    question=f"What information is provided about: {chunk.text[:50]}?",
                    ground_truth_answer=chunk.text[:200],
                    retrieved_contexts=[chunk.text],
                    source_doc_ids=[str(chunk.doc_id)],
                    query_type="simple",
                    taxonomy_path=chunk.chunk_metadata.get("taxonomy_path") if chunk.chunk_metadata else None,
                    metadata={
                        "generated_method": "fallback",
                        "chunk_index": chunk.chunk_index
                    }
                )
                samples.append(sample)

        output_file = Path("golden_datasets") / f"golden_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)

        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [sample.to_dict() for sample in samples],
                f,
                indent=2,
                ensure_ascii=False
            )

        logger.info(f"Golden dataset saved to: {output_file}")
        logger.info(f"Generated {len(samples)} samples:")
        logger.info(f"  - Simple queries: {sum(1 for s in samples if s.query_type == 'simple')}")
        logger.info(f"  - Reasoning queries: {sum(1 for s in samples if s.query_type == 'reasoning')}")
        logger.info(f"  - Multi-context queries: {sum(1 for s in samples if s.query_type == 'multi_context')}")

if __name__ == "__main__":
    asyncio.run(main())
