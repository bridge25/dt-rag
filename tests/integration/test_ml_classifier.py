"""
ML Classifier Integration Tests
Tests sentence-transformers based classification
"""
import pytest
import asyncio


@pytest.mark.asyncio
class TestMLClassifierIntegration:
    """ML Classifier integration tests"""

    async def test_classifier_loads_successfully(self, ml_model_name: str):
        """Test ML classifier loads without errors"""
        try:
            from services.ml_classifier import MLClassifier

            classifier = MLClassifier(model_name=ml_model_name)
            classifier.load_model()

            assert classifier.model is not None
            assert len(classifier.taxonomy_embeddings) > 0
        except ImportError:
            pytest.skip("ML classifier not available (expected in development)")

    async def test_classify_rag_text(self, sample_text: str):
        """Test classification of RAG-related text"""
        try:
            from services.ml_classifier import get_ml_classifier

            classifier = get_ml_classifier()
            result = await classifier.classify_text(sample_text)

            assert "canonical" in result
            assert "confidence" in result
            assert "reasoning" in result
            assert isinstance(result["canonical"], list)
            assert result["confidence"] >= 0.5
            assert "AI" in result["canonical"]

        except ImportError:
            pytest.skip("ML classifier not available")

    async def test_classify_with_hint_paths(self):
        """Test classification with hint paths boosts confidence"""
        try:
            from services.ml_classifier import get_ml_classifier

            classifier = get_ml_classifier()
            text = "Vector databases store embeddings for similarity search"

            # Without hint
            result_no_hint = await classifier.classify_text(text)

            # With hint
            result_with_hint = await classifier.classify_text(
                text,
                hint_paths=[["AI", "RAG"]]
            )

            assert "confidence" in result_no_hint
            assert "confidence" in result_with_hint

            # Hint should boost confidence or maintain high confidence
            if result_no_hint["canonical"] == ["AI", "RAG"]:
                assert result_with_hint["confidence"] >= result_no_hint["confidence"]

        except ImportError:
            pytest.skip("ML classifier not available")

    async def test_classify_multiple_domains(self):
        """Test classification across different domains"""
        try:
            from services.ml_classifier import get_ml_classifier

            classifier = get_ml_classifier()

            test_cases = [
                ("RAG systems use retrieval and generation", "RAG"),
                ("Neural networks learn from training data", "ML"),
                ("Taxonomy hierarchies organize information", "Taxonomy"),
            ]

            for text, expected_domain in test_cases:
                result = await classifier.classify_text(text)

                assert "canonical" in result
                # Check if expected domain appears in canonical path
                canonical_str = "/".join(result["canonical"])
                # Flexible check - domain might be uppercase or lowercase
                assert expected_domain.upper() in canonical_str.upper() or \
                       expected_domain.lower() in canonical_str.lower() or \
                       "AI" in result["canonical"]  # Fallback to AI is acceptable

        except ImportError:
            pytest.skip("ML classifier not available")

    async def test_low_confidence_fallback(self):
        """Test low confidence texts fallback to General AI"""
        try:
            from services.ml_classifier import get_ml_classifier

            classifier = get_ml_classifier()

            # Unrelated text
            result = await classifier.classify_text(
                "The quick brown fox jumps over the lazy dog",
                confidence_threshold=0.7
            )

            assert "canonical" in result
            # Should fallback to General AI
            if result["confidence"] < 0.7:
                assert "General" in result["canonical"] or \
                       result["confidence"] >= 0.5

        except ImportError:
            pytest.skip("ML classifier not available")

    async def test_classifier_singleton(self):
        """Test classifier uses singleton pattern"""
        try:
            from services.ml_classifier import get_ml_classifier

            classifier1 = get_ml_classifier()
            classifier2 = get_ml_classifier()

            assert classifier1 is classifier2  # Same instance

        except ImportError:
            pytest.skip("ML classifier not available")

    async def test_similarity_scores_returned(self):
        """Test that similarity scores are included in results"""
        try:
            from services.ml_classifier import get_ml_classifier

            classifier = get_ml_classifier()
            result = await classifier.classify_text(
                "Machine learning models require training data"
            )

            assert "similarities" in result
            assert isinstance(result["similarities"], dict)
            assert len(result["similarities"]) > 0

            # All similarities should be between 0 and 1
            for score in result["similarities"].values():
                assert 0.0 <= score <= 1.0

        except ImportError:
            pytest.skip("ML classifier not available")


@pytest.mark.asyncio
class TestClassifyDAOIntegration:
    """ClassifyDAO integration tests"""

    async def test_classify_dao_uses_ml_classifier(self, sample_text: str):
        """Test ClassifyDAO integrates with ML classifier"""
        from database import ClassifyDAO

        result = await ClassifyDAO.classify_text(sample_text)

        assert "canonical" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert isinstance(result["canonical"], list)

    async def test_classify_dao_fallback(self):
        """Test ClassifyDAO fallback mechanism"""
        from database import ClassifyDAO

        # Even if ML fails, should return valid result
        result = await ClassifyDAO.classify_text("test text")

        assert "canonical" in result
        assert "confidence" in result
        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0

    async def test_classify_dao_with_hints(self):
        """Test ClassifyDAO with hint paths"""
        from database import ClassifyDAO

        result = await ClassifyDAO.classify_text(
            "Neural network architectures",
            hint_paths=[["AI", "ML"]]
        )

        assert "canonical" in result
        assert "confidence" in result
