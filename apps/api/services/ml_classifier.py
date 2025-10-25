"""
ML 기반 텍스트 분류 서비스
BERT/RoBERTa를 사용한 의미론적 유사도 기반 분류
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class MLClassifier:
    """Sentence-BERT 기반 의미론적 분류기"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Args:
            model_name: Hugging Face 모델 이름
                - all-MiniLM-L6-v2: 경량, 빠름 (384차원)
                - all-mpnet-base-v2: 고성능 (768차원)
                - paraphrase-multilingual-MiniLM-L12-v2: 다국어 지원
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.taxonomy_embeddings: Dict[str, np.ndarray] = {}
        self.taxonomy_definitions = self._get_taxonomy_definitions()

    def _get_taxonomy_definitions(self) -> Dict[str, str]:
        """택소노미 노드별 정의 (의미론적 임베딩용)"""
        return {
            "AI/RAG": "Retrieval-Augmented Generation systems that combine information retrieval with language generation. Vector databases, embeddings, semantic search, and document retrieval techniques.",
            "AI/ML": "Machine Learning algorithms, model training, neural networks, deep learning architectures, classification, regression, and supervised learning methods.",
            "AI/Taxonomy": "Classification systems, hierarchical structures, ontologies, knowledge organization, category management, and metadata schemas.",
            "AI/General": "General artificial intelligence topics, AI research, ethics, applications, and broad AI concepts not fitting specific subcategories.",
            "AI/NLP": "Natural Language Processing, text analysis, language understanding, tokenization, named entity recognition, and linguistic models.",
            "AI/Computer Vision": "Image processing, object detection, image classification, visual recognition, and computer vision algorithms.",
        }

    def load_model(self) -> None:
        """모델 로드 (lazy loading)"""
        if self.model is None:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self._precompute_taxonomy_embeddings()
            logger.info("Model loaded successfully")

    def _precompute_taxonomy_embeddings(self) -> None:
        """택소노미 정의 임베딩 사전 계산"""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        logger.info("Precomputing taxonomy embeddings...")
        for path, definition in self.taxonomy_definitions.items():
            self.taxonomy_embeddings[path] = self.model.encode(
                definition, convert_to_numpy=True, show_progress_bar=False
            )
        logger.info(f"Precomputed {len(self.taxonomy_embeddings)} taxonomy embeddings")

    async def classify_text(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None,
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        텍스트를 의미론적 유사도 기반으로 분류

        Args:
            text: 분류할 텍스트
            hint_paths: 힌트 경로 (있을 경우 가중치 부여)
            confidence_threshold: 최소 신뢰도 임계값

        Returns:
            분류 결과 딕셔너리
        """
        if self.model is None:
            self.load_model()

        try:
            text_embedding = self.model.encode(
                text, convert_to_numpy=True, show_progress_bar=False
            )

            similarities = {}
            for path, tax_embedding in self.taxonomy_embeddings.items():
                similarity = cosine_similarity(
                    text_embedding.reshape(1, -1), tax_embedding.reshape(1, -1)
                )[0][0]
                similarities[path] = float(similarity)

            best_path = max(similarities, key=similarities.get)
            best_score = similarities[best_path]

            confidence = min(0.95, best_score)

            if hint_paths:
                hint_path_strs = ["/".join(hp) for hp in hint_paths]
                for hint_path in hint_path_strs:
                    if hint_path in similarities:
                        hint_similarity = similarities[hint_path]
                        if hint_similarity > best_score * 0.8:
                            best_path = hint_path
                            confidence = min(
                                0.98, (best_score + hint_similarity) / 2 + 0.1
                            )
                            break

            canonical = best_path.split("/")
            label = canonical[-1] if canonical else "General AI"

            reasoning = [
                f"Semantic similarity score: {best_score:.3f}",
                f"Best match: {best_path}",
                f"Model: {self.model_name}",
            ]

            if confidence < confidence_threshold:
                canonical = ["AI", "General"]
                label = "General AI"
                confidence = 0.6
                reasoning.append(
                    f"Low confidence ({best_score:.3f} < {confidence_threshold}), "
                    f"defaulting to General AI"
                )

            if hint_paths:
                reasoning.append(f"Hint paths considered: {hint_path_strs}")

            return {
                "canonical": canonical,
                "label": label,
                "confidence": confidence,
                "reasoning": reasoning,
                "node_id": f"ml_{canonical[-1].lower()}_{hash(text) % 1000:03d}",
                "version": "1.8.1",
                "similarities": similarities,
            }

        except Exception as e:
            logger.error(f"ML classification failed: {e}")
            return {
                "canonical": ["AI", "General"],
                "label": "General AI",
                "confidence": 0.5,
                "reasoning": [f"ML classification error: {str(e)}"],
                "node_id": f"fallback_{hash(text) % 1000:03d}",
                "version": "1.8.1",
            }


@lru_cache(maxsize=1)
def get_ml_classifier() -> MLClassifier:
    """싱글톤 ML 분류기 인스턴스"""
    classifier = MLClassifier()
    classifier.load_model()
    return classifier
