"""
ML 기반 텍스트 분류 서비스
Gemini API를 사용한 경량 의미론적 분류 (Railway 배포 최적화)

로컬 ML 모델(sentence-transformers)은 선택적으로 사용 가능
- 로컬 모델 사용: SENTENCE_TRANSFORMERS_AVAILABLE=True (requirements에 추가 필요)
- API 사용: Gemini API로 분류 (기본값, 경량)

@CODE:API-001
"""

import os
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import numpy as np

# Optional imports for local ML (heavy, not available on Railway free tier)
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore
    cosine_similarity = None  # type: ignore

# Gemini API for lightweight classification
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = bool(os.getenv("GEMINI_API_KEY"))
    if GEMINI_AVAILABLE:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None  # type: ignore

logger = logging.getLogger(__name__)


class MLClassifier:
    """
    의미론적 분류기 (Gemini API 기반, 로컬 ML 선택적 지원)

    Railway 무료 티어에서는 Gemini API 사용 (메모리 효율적)
    로컬 환경에서는 sentence-transformers 사용 가능
    """

    TAXONOMY_DEFINITIONS = {
        "AI/RAG": "Retrieval-Augmented Generation systems that combine information retrieval with language generation. Vector databases, embeddings, semantic search, and document retrieval techniques.",
        "AI/ML": "Machine Learning algorithms, model training, neural networks, deep learning architectures, classification, regression, and supervised learning methods.",
        "AI/Taxonomy": "Classification systems, hierarchical structures, ontologies, knowledge organization, category management, and metadata schemas.",
        "AI/General": "General artificial intelligence topics, AI research, ethics, applications, and broad AI concepts not fitting specific subcategories.",
        "AI/NLP": "Natural Language Processing, text analysis, language understanding, tokenization, named entity recognition, and linguistic models.",
        "AI/Computer Vision": "Image processing, object detection, image classification, visual recognition, and computer vision algorithms.",
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Args:
            model_name: Hugging Face 모델 이름 (로컬 ML 사용 시에만 적용)
        """
        self.model_name = model_name
        self.model: Optional[Any] = None
        self.taxonomy_embeddings: Dict[str, np.ndarray] = {}
        self.use_local_ml = SENTENCE_TRANSFORMERS_AVAILABLE and os.getenv("USE_LOCAL_EMBEDDING", "false").lower() == "true"

        if self.use_local_ml:
            logger.info(f"MLClassifier: Using local sentence-transformers ({model_name})")
        elif GEMINI_AVAILABLE:
            logger.info("MLClassifier: Using Gemini API for classification (lightweight mode)")
        else:
            logger.warning("MLClassifier: No ML backend available, using rule-based fallback")

    def load_model(self) -> None:
        """모델 로드 (로컬 ML 사용 시에만)"""
        if self.use_local_ml and self.model is None and SentenceTransformer is not None:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self._precompute_taxonomy_embeddings()
            logger.info("Local ML model loaded successfully")

    def _precompute_taxonomy_embeddings(self) -> None:
        """택소노미 정의 임베딩 사전 계산 (로컬 ML용)"""
        if self.model is None:
            return

        logger.info("Precomputing taxonomy embeddings...")
        for path, definition in self.TAXONOMY_DEFINITIONS.items():
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
        텍스트를 분류 (Gemini API 또는 로컬 ML 사용)

        Args:
            text: 분류할 텍스트
            hint_paths: 힌트 경로 (있을 경우 가중치 부여)
            confidence_threshold: 최소 신뢰도 임계값

        Returns:
            분류 결과 딕셔너리
        """
        # 1. 로컬 ML 사용 가능하면 로컬 사용
        if self.use_local_ml:
            return await self._classify_with_local_ml(text, hint_paths, confidence_threshold)

        # 2. Gemini API 사용 가능하면 Gemini 사용
        if GEMINI_AVAILABLE:
            return await self._classify_with_gemini(text, hint_paths, confidence_threshold)

        # 3. 둘 다 없으면 규칙 기반 폴백
        return self._classify_with_rules(text, hint_paths)

    async def _classify_with_gemini(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None,
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Gemini API를 사용한 분류 (경량, Railway 최적화)"""
        try:
            categories = list(self.TAXONOMY_DEFINITIONS.keys())

            prompt = f"""Classify the following text into ONE of these categories:
{chr(10).join(f'- {cat}: {desc}' for cat, desc in self.TAXONOMY_DEFINITIONS.items())}

Text to classify:
"{text[:500]}"

Respond with ONLY the category path (e.g., "AI/RAG") and a confidence score (0.0-1.0).
Format: CATEGORY|CONFIDENCE
Example: AI/RAG|0.85"""

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

            # Parse response
            result_text = response.text.strip()
            if "|" in result_text:
                parts = result_text.split("|")
                category = parts[0].strip()
                confidence = float(parts[1].strip()) if len(parts) > 1 else 0.7
            else:
                # Fallback parsing
                category = result_text.split()[0] if result_text else "AI/General"
                confidence = 0.6

            # Validate category
            if category not in categories:
                # Find closest match
                for cat in categories:
                    if cat.lower() in category.lower() or category.lower() in cat.lower():
                        category = cat
                        break
                else:
                    category = "AI/General"
                    confidence = 0.5

            canonical = category.split("/")

            return {
                "canonical": canonical,
                "label": canonical[-1] if canonical else "General AI",
                "confidence": min(0.95, confidence),
                "reasoning": [
                    f"Gemini API classification",
                    f"Category: {category}",
                    "Lightweight mode (no local ML)",
                ],
                "node_id": f"gemini_{canonical[-1].lower()}_{hash(text) % 1000:03d}",
                "version": "2.0.0-gemini",
                "backend": "gemini-1.5-flash",
            }

        except Exception as e:
            logger.error(f"Gemini classification failed: {e}")
            return self._classify_with_rules(text, hint_paths)

    async def _classify_with_local_ml(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None,
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """로컬 sentence-transformers를 사용한 분류 (고성능, 메모리 intensive)"""
        if self.model is None:
            self.load_model()

        if self.model is None or cosine_similarity is None:
            return self._classify_with_rules(text, hint_paths)

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

            best_path = max(similarities, key=similarities.get)  # type: ignore[arg-type]
            best_score = similarities[best_path]
            confidence = min(0.95, best_score)

            if hint_paths:
                hint_path_strs = ["/".join(hp) for hp in hint_paths]
                for hint_path in hint_path_strs:
                    if hint_path in similarities:
                        hint_similarity = similarities[hint_path]
                        if hint_similarity > best_score * 0.8:
                            best_path = hint_path
                            confidence = min(0.98, (best_score + hint_similarity) / 2 + 0.1)
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
                reasoning.append(f"Low confidence, defaulting to General AI")

            return {
                "canonical": canonical,
                "label": label,
                "confidence": confidence,
                "reasoning": reasoning,
                "node_id": f"ml_{canonical[-1].lower()}_{hash(text) % 1000:03d}",
                "version": "1.8.1",
                "similarities": similarities,
                "backend": "sentence-transformers",
            }

        except Exception as e:
            logger.error(f"Local ML classification failed: {e}")
            return self._classify_with_rules(text, hint_paths)

    def _classify_with_rules(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None,
    ) -> Dict[str, Any]:
        """규칙 기반 폴백 분류 (ML 없이 동작)"""
        text_lower = text.lower()

        # Simple keyword matching
        keyword_map = {
            "AI/RAG": ["rag", "retrieval", "vector", "embedding", "semantic search", "document retrieval"],
            "AI/ML": ["machine learning", "neural network", "training", "model", "deep learning", "classification"],
            "AI/Taxonomy": ["taxonomy", "classification", "hierarchy", "ontology", "category"],
            "AI/NLP": ["nlp", "natural language", "text analysis", "tokenization", "language model"],
            "AI/Computer Vision": ["vision", "image", "object detection", "visual", "computer vision"],
        }

        scores = {cat: 0 for cat in keyword_map}
        for cat, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[cat] += 1

        best_cat = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_cat]

        if best_score == 0:
            best_cat = "AI/General"
            confidence = 0.5
        else:
            confidence = min(0.7, 0.4 + best_score * 0.1)

        canonical = best_cat.split("/")

        return {
            "canonical": canonical,
            "label": canonical[-1] if canonical else "General AI",
            "confidence": confidence,
            "reasoning": [
                "Rule-based classification (fallback mode)",
                f"Keyword matches: {best_score}",
                "No ML backend available",
            ],
            "node_id": f"rule_{canonical[-1].lower()}_{hash(text) % 1000:03d}",
            "version": "1.0.0-rules",
            "backend": "rule-based",
        }


@lru_cache(maxsize=1)
def get_ml_classifier() -> MLClassifier:
    """싱글톤 ML 분류기 인스턴스"""
    classifier = MLClassifier()
    # Don't auto-load model on Railway (saves memory)
    # Model is loaded on first classify_text() call if needed
    return classifier
