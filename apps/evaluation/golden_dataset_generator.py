# @CODE:EVAL-001 | SPEC: .moai/specs/SPEC-EVAL-001/spec.md | TEST: tests/evaluation/

"""
Golden Dataset Generator for RAG Evaluation

Generates synthetic test data using RAGAS framework with best practices from:
- RAGAS library (explodinggradients/ragas)
- Industry best practices (Microsoft, Google Cloud, Hugging Face)

Key Features:
- Synthetic question generation with diverse query types
- Automatic answer generation from documents
- Quality filtering with critique agents
- Context tracking for retrieval metrics

@CODE:MYPY-001:PHASE2:BATCH4
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GoldenSample:
    """Single golden dataset sample"""

    question: str
    ground_truth_answer: str
    retrieved_contexts: List[str]
    source_doc_ids: List[str]
    query_type: str  # simple, reasoning, multi_context
    taxonomy_path: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GoldenDatasetGenerator:
    """Generate golden dataset for RAG evaluation using RAGAS"""

    def __init__(self, output_dir: str = "golden_datasets") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Check for required API keys
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.gemini_api_key and not self.openai_api_key:
            logger.warning("No API keys found. Set GEMINI_API_KEY or OPENAI_API_KEY")

    async def generate_from_documents(
        self,
        documents: List[Dict[str, Any]],
        testset_size: int = 100,
        query_distribution: Optional[Dict[str, float]] = None,
    ) -> List[GoldenSample]:
        """
        Generate golden dataset from documents using RAGAS

        Args:
            documents: List of document dicts with 'text', 'doc_id', 'title', 'taxonomy_path'
            testset_size: Number of samples to generate
            query_distribution: Query type distribution
                - simple: 0.5 (factual, single-hop)
                - reasoning: 0.25 (requires inference)
                - multi_context: 0.25 (requires multiple documents)

        Returns:
            List of GoldenSample objects
        """
        if query_distribution is None:
            query_distribution = {
                "simple": 0.5,
                "reasoning": 0.25,
                "multi_context": 0.25,
            }

        logger.info(
            f"Generating {testset_size} golden samples from {len(documents)} documents"
        )

        # Use RAGAS if available
        try:
            samples = await self._generate_with_ragas(
                documents, testset_size, query_distribution
            )
        except Exception as e:
            logger.warning(f"RAGAS generation failed: {e}. Using fallback method.")
            samples = await self._generate_fallback(
                documents, testset_size, query_distribution
            )

        return samples

    async def _generate_with_ragas(
        self,
        documents: List[Dict[str, Any]],
        testset_size: int,
        query_distribution: Dict[str, float],
    ) -> List[GoldenSample]:
        """Generate using RAGAS TestsetGenerator"""
        try:
            # Dynamic imports to avoid dependency issues
            from langchain.docstore.document import Document as LangchainDoc
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            from ragas.testset import TestsetGenerator

            # Configure LLMs
            generator_llm = ChatOpenAI(model="gpt-4o-mini")
            critic_llm = ChatOpenAI(model="gpt-4o")
            embeddings = OpenAIEmbeddings()

            # Initialize generator
            generator = TestsetGenerator.from_langchain(
                generator_llm, critic_llm, embeddings
            )

            # Convert documents to Langchain format
            langchain_docs = []
            for doc in documents:
                langchain_docs.append(
                    LangchainDoc(
                        page_content=doc.get("text", ""),
                        metadata={
                            "doc_id": doc.get("doc_id", ""),
                            "title": doc.get("title", ""),
                            "taxonomy_path": doc.get("taxonomy_path", []),
                        },
                    )
                )

            # Generate testset
            logger.info("Generating testset with RAGAS...")
            testset = generator.generate_with_langchain_docs(
                langchain_docs, testset_size=testset_size
            )

            # Convert to GoldenSample format
            samples = []
            eval_dataset = testset.to_evaluation_dataset()

            for item in eval_dataset:
                samples.append(
                    GoldenSample(
                        question=item.user_input,
                        ground_truth_answer=item.reference,
                        retrieved_contexts=(
                            item.retrieved_contexts
                            if hasattr(item, "retrieved_contexts")
                            else []
                        ),
                        source_doc_ids=[],  # Extract from contexts if available
                        query_type="simple",  # RAGAS doesn't expose this, infer later
                        metadata={"generated_by": "ragas"},
                    )
                )

            logger.info(f"Generated {len(samples)} samples with RAGAS")
            return samples

        except ImportError as e:
            logger.error(f"RAGAS dependencies not available: {e}")
            raise

    async def _generate_fallback(
        self,
        documents: List[Dict[str, Any]],
        testset_size: int,
        query_distribution: Dict[str, float],
    ) -> List[GoldenSample]:
        """Fallback method using Gemini API directly"""
        import google.generativeai as genai

        if not self.gemini_api_key:
            raise ValueError("No API key available for fallback generation")

        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel("gemini-pro")

        samples = []

        # Calculate samples per type
        simple_count = int(testset_size * query_distribution.get("simple", 0.5))
        reasoning_count = int(testset_size * query_distribution.get("reasoning", 0.25))
        multi_count = testset_size - simple_count - reasoning_count

        query_types = (
            ["simple"] * simple_count
            + ["reasoning"] * reasoning_count
            + ["multi_context"] * multi_count
        )

        logger.info("Generating samples with Gemini fallback method...")

        for idx, query_type in enumerate(query_types):
            # Select random document(s)
            import random

            if query_type == "multi_context":
                selected_docs = random.sample(documents, min(3, len(documents)))
            else:
                selected_docs = [random.choice(documents)]

            # Generate question and answer
            context_text = "\n\n".join(
                [doc.get("text", "")[:500] for doc in selected_docs]
            )

            prompt = f"""Based on the following context, generate a {query_type} question and its answer.

Context:
{context_text}

Generate:
1. Question: A {query_type} question
2. Answer: The ground truth answer

Format as JSON:
{{"question": "...", "answer": "..."}}
"""

            try:
                response = model.generate_content(prompt)
                result = json.loads(
                    response.text.strip().replace("```json", "").replace("```", "")
                )

                samples.append(
                    GoldenSample(
                        question=result["question"],
                        ground_truth_answer=result["answer"],
                        retrieved_contexts=[
                            doc.get("text", "")[:500] for doc in selected_docs
                        ],
                        source_doc_ids=[doc.get("doc_id", "") for doc in selected_docs],
                        query_type=query_type,
                        taxonomy_path=selected_docs[0].get("taxonomy_path"),
                        metadata={"generated_by": "gemini_fallback"},
                    )
                )

                if (idx + 1) % 10 == 0:
                    logger.info(f"Generated {idx + 1}/{testset_size} samples")

            except Exception as e:
                logger.warning(f"Failed to generate sample {idx}: {e}")
                continue

        logger.info(f"Generated {len(samples)} samples with fallback method")
        return samples

    def save_dataset(self, samples: List[GoldenSample], name: Optional[str] = None) -> str:
        """Save golden dataset to JSON file"""
        if name is None:
            name = f"golden_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        output_path = self.output_dir / f"{name}.json"

        dataset = {
            "metadata": {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "total_samples": len(samples),
                "query_types": self._count_query_types(samples),
            },
            "samples": [sample.to_dict() for sample in samples],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(samples)} samples to {output_path}")
        return str(output_path)

    def load_dataset(self, file_path: str) -> List[GoldenSample]:
        """Load golden dataset from JSON file"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        samples = []
        for sample_dict in data["samples"]:
            samples.append(GoldenSample(**sample_dict))

        logger.info(f"Loaded {len(samples)} samples from {file_path}")
        return samples

    def _count_query_types(self, samples: List[GoldenSample]) -> Dict[str, int]:
        """Count samples by query type"""
        counts: Dict[str, int] = {}
        for sample in samples:
            query_type = sample.query_type
            counts[query_type] = counts.get(query_type, 0) + 1
        return counts


async def create_golden_dataset_from_db(testset_size: int = 100) -> str:
    """
    Create golden dataset from existing database documents

    Returns:
        Path to saved golden dataset
    """
    from sqlalchemy import text

    from ..core.db_session import async_session

    # Fetch documents from database
    async with async_session() as session:
        # Get sample documents
        doc_query = text("SELECT doc_id, title FROM documents LIMIT 10")
        doc_result = await session.execute(doc_query)
        documents = doc_result.fetchall()

        # Convert to generator format
        doc_data = []
        for doc in documents:
            # Get chunks for this document
            chunk_query = text("SELECT text FROM chunks WHERE doc_id = :doc_id LIMIT 5")
            chunk_result = await session.execute(chunk_query, {"doc_id": doc.doc_id})
            chunks = chunk_result.fetchall()

            if chunks:
                combined_text = "\n\n".join([chunk.text for chunk in chunks])
                doc_data.append(
                    {
                        "doc_id": doc.doc_id,
                        "title": doc.title or "Untitled",
                        "text": combined_text,
                        "taxonomy_path": [],
                    }
                )

    # Generate golden dataset
    generator = GoldenDatasetGenerator()
    samples = await generator.generate_from_documents(doc_data, testset_size)

    # Save dataset
    output_path = generator.save_dataset(samples)

    return str(output_path)


if __name__ == "__main__":
    # Example usage
    async def main() -> None:
        # Create golden dataset from database
        output_path = await create_golden_dataset_from_db(testset_size=10)
        print(f"Golden dataset created: {output_path}")

    asyncio.run(main())
