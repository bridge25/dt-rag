import asyncio
from apps.classification import SemanticClassifier, TaxonomyDAO
from apps.api.embedding_service import EmbeddingService
from apps.core.db_session import async_session

async def test_classification():
    async with async_session() as session:
        try:
            embedding_service = EmbeddingService()
            taxonomy_dao = TaxonomyDAO(session)
            classifier = SemanticClassifier(
                embedding_service=embedding_service,
                taxonomy_dao=taxonomy_dao,
                confidence_threshold=0.7
            )

            result = await classifier.classify(
                text="machine learning",
                confidence_threshold=0.7,
                top_k=5
            )

            print(f"Classification result: {result}")

        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_classification())
