"""
Cross-Encoder 기반 리랭킹 시스템
BERT 기반 쌍대 비교 모델을 활용한 정확도 향상
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json
import time

logger = logging.getLogger(__name__)

@dataclass
class RerankingCandidate:
    """리랭킹 후보"""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    initial_score: float
    rerank_score: Optional[float] = None
    rank_change: Optional[int] = None

class CrossEncoderReranker:
    """Cross-Encoder 기반 리랭커"""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
        batch_size: int = 32,
        max_length: int = 512,
        use_cache: bool = True
    ):
        """
        Args:
            model_name: HuggingFace 모델명
            batch_size: 배치 크기
            max_length: 최대 토큰 길이
            use_cache: 캐시 사용 여부
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self.use_cache = use_cache
        self.model = None
        self.tokenizer = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cache = {} if use_cache else None

    async def initialize_model(self):
        """모델 초기화 (비동기)"""
        if self.model is not None:
            return

        try:
            def _load_model():
                try:
                    from sentence_transformers import CrossEncoder
                    model = CrossEncoder(self.model_name)
                    return model
                except ImportError:
                    logger.error("sentence-transformers not installed")
                    return None
                except Exception as e:
                    logger.error(f"Failed to load cross-encoder model: {e}")
                    return None

            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(self.executor, _load_model)

            if self.model:
                logger.info(f"Cross-encoder model loaded: {self.model_name}")
            else:
                logger.warning("Cross-encoder model not available, using fallback")

        except Exception as e:
            logger.error(f"Model initialization failed: {e}")

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """후보 재랭킹"""
        if not candidates:
            return []

        try:
            # 모델 초기화
            await self.initialize_model()

            # 후보 변환
            reranking_candidates = self._prepare_candidates(candidates)

            # 리랭킹 수행
            if self.model:
                scored_candidates = await self._cross_encoder_rerank(query, reranking_candidates)
            else:
                # 폴백: 간단한 텍스트 매칭 기반 리랭킹
                scored_candidates = await self._fallback_rerank(query, reranking_candidates)

            # 점수순 정렬
            scored_candidates.sort(key=lambda x: x.rerank_score or 0, reverse=True)

            # 결과 변환
            results = []
            for i, candidate in enumerate(scored_candidates[:top_k]):
                result = {
                    'chunk_id': candidate.chunk_id,
                    'text': candidate.text,
                    'score': candidate.rerank_score,
                    'metadata': candidate.metadata.copy()
                }
                result['metadata']['initial_score'] = candidate.initial_score
                result['metadata']['rank_change'] = candidate.rank_change
                result['metadata']['source'] = 'reranked'
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # 원본 결과 반환
            return candidates[:top_k]

    def _prepare_candidates(self, candidates: List[Dict[str, Any]]) -> List[RerankingCandidate]:
        """후보 준비"""
        reranking_candidates = []
        for i, candidate in enumerate(candidates):
            rerank_candidate = RerankingCandidate(
                chunk_id=candidate.get('chunk_id', ''),
                text=candidate.get('text', ''),
                metadata=candidate.get('metadata', {}),
                initial_score=candidate.get('score', 0.0)
            )
            reranking_candidates.append(rerank_candidate)

        return reranking_candidates

    async def _cross_encoder_rerank(
        self,
        query: str,
        candidates: List[RerankingCandidate]
    ) -> List[RerankingCandidate]:
        """Cross-encoder 기반 리랭킹"""
        try:
            # 쿼리-문서 쌍 생성
            query_doc_pairs = []
            for candidate in candidates:
                # 텍스트 길이 제한
                text = candidate.text[:2000]  # 대략 512 토큰
                query_doc_pairs.append([query, text])

            # 배치 처리
            scores = []
            for i in range(0, len(query_doc_pairs), self.batch_size):
                batch = query_doc_pairs[i:i + self.batch_size]
                batch_scores = await self._predict_batch(batch)
                scores.extend(batch_scores)

            # 점수 할당
            for candidate, score in zip(candidates, scores):
                candidate.rerank_score = float(score)

            # 순위 변화 계산
            initial_order = {candidate.chunk_id: i for i, candidate in enumerate(candidates)}
            candidates.sort(key=lambda x: x.rerank_score or 0, reverse=True)

            for new_rank, candidate in enumerate(candidates):
                initial_rank = initial_order[candidate.chunk_id]
                candidate.rank_change = initial_rank - new_rank

            return candidates

        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            return candidates

    async def _predict_batch(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """배치 예측"""
        if not self.model or not query_doc_pairs:
            return [0.0] * len(query_doc_pairs)

        try:
            def _predict():
                return self.model.predict(query_doc_pairs)

            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(self.executor, _predict)
            return scores.tolist() if hasattr(scores, 'tolist') else list(scores)

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            return [0.0] * len(query_doc_pairs)

    async def _fallback_rerank(
        self,
        query: str,
        candidates: List[RerankingCandidate]
    ) -> List[RerankingCandidate]:
        """폴백 리랭킹 (간단한 텍스트 매칭)"""
        try:
            query_terms = query.lower().split()

            for candidate in candidates:
                text_lower = candidate.text.lower()

                # 단순 매칭 점수 계산
                match_score = 0.0
                text_terms = text_lower.split()

                # 정확한 구문 매칭
                if query.lower() in text_lower:
                    match_score += 2.0

                # 개별 단어 매칭
                for term in query_terms:
                    if term in text_lower:
                        match_score += 1.0
                        # 제목에 있으면 가점
                        if candidate.metadata.get('title', '').lower().find(term) >= 0:
                            match_score += 0.5

                # TF-IDF 스타일 정규화
                match_score = match_score / (1 + np.log(1 + len(text_terms)))

                # 초기 점수와 결합
                candidate.rerank_score = 0.7 * candidate.initial_score + 0.3 * match_score

            return candidates

        except Exception as e:
            logger.error(f"Fallback reranking failed: {e}")
            return candidates


class MultiStageReranker:
    """다단계 리랭킹 시스템"""

    def __init__(self):
        self.fast_reranker = FastReranker()
        self.cross_encoder = CrossEncoderReranker()
        self.diversity_reranker = DiversityReranker()

    async def multi_stage_rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        final_k: int = 5,
        stage1_k: int = 50,
        stage2_k: int = 20
    ) -> List[Dict[str, Any]]:
        """다단계 리랭킹"""
        try:
            if len(candidates) <= final_k:
                return candidates

            # Stage 1: 빠른 필터링
            stage1_results = await self.fast_reranker.rerank(query, candidates, stage1_k)

            # Stage 2: Cross-encoder 정밀 랭킹
            stage2_results = await self.cross_encoder.rerank(query, stage1_results, stage2_k)

            # Stage 3: 다양성 보장
            final_results = self.diversity_reranker.diversify(stage2_results, final_k)

            return final_results

        except Exception as e:
            logger.error(f"Multi-stage reranking failed: {e}")
            return candidates[:final_k]


class FastReranker:
    """빠른 1차 리랭커"""

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """빠른 리랭킹 (휴리스틱 기반)"""
        try:
            query_terms = set(query.lower().split())

            for candidate in candidates:
                text = candidate.get('text', '').lower()
                title = candidate.get('metadata', {}).get('title', '').lower()

                # 빠른 점수 계산
                text_terms = set(text.split())
                title_terms = set(title.split())

                # Jaccard 유사도
                text_jaccard = len(query_terms & text_terms) / len(query_terms | text_terms) if query_terms | text_terms else 0
                title_jaccard = len(query_terms & title_terms) / len(query_terms | title_terms) if query_terms | title_terms else 0

                # 가중 점수
                fast_score = 0.7 * text_jaccard + 0.3 * title_jaccard

                # 기존 점수와 결합
                original_score = candidate.get('score', 0.0)
                candidate['fast_rerank_score'] = 0.6 * original_score + 0.4 * fast_score

            # 정렬
            candidates.sort(key=lambda x: x.get('fast_rerank_score', 0), reverse=True)
            return candidates[:top_k]

        except Exception as e:
            logger.error(f"Fast reranking failed: {e}")
            return candidates[:top_k]


class DiversityReranker:
    """다양성 기반 리랭커"""

    def diversify(
        self,
        candidates: List[Dict[str, Any]],
        final_k: int = 5,
        diversity_lambda: float = 0.3
    ) -> List[Dict[str, Any]]:
        """MMR(Maximal Marginal Relevance) 기반 다양성 보장"""
        try:
            if len(candidates) <= final_k:
                return candidates

            selected = []
            remaining = candidates.copy()

            # 첫 번째 문서 선택 (최고 점수)
            if remaining:
                selected.append(remaining.pop(0))

            # MMR 기반 선택
            while len(selected) < final_k and remaining:
                best_candidate = None
                best_mmr_score = -1

                for candidate in remaining:
                    # 관련성 점수
                    relevance = candidate.get('score', 0.0)

                    # 다양성 점수 (기선택 문서들과의 유사도 최소화)
                    max_similarity = 0.0
                    for selected_doc in selected:
                        similarity = self._calculate_text_similarity(
                            candidate.get('text', ''),
                            selected_doc.get('text', '')
                        )
                        max_similarity = max(max_similarity, similarity)

                    # MMR 점수
                    mmr_score = diversity_lambda * relevance - (1 - diversity_lambda) * max_similarity

                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_candidate = candidate

                if best_candidate:
                    selected.append(best_candidate)
                    remaining.remove(best_candidate)
                else:
                    break

            return selected

        except Exception as e:
            logger.error(f"Diversity reranking failed: {e}")
            return candidates[:final_k]

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """간단한 텍스트 유사도 계산"""
        try:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = words1 & words2
            union = words1 | words2

            return len(intersection) / len(union) if union else 0.0

        except Exception as e:
            return 0.0


class LearningToRankReranker:
    """Learning-to-Rank 기반 리랭커"""

    def __init__(self):
        self.feature_extractors = [
            QueryDocumentFeatures(),
            StatisticalFeatures(),
            SemanticFeatures()
        ]

    async def rerank_with_features(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """특징 기반 리랭킹"""
        try:
            # 특징 추출
            features_list = []
            for candidate in candidates:
                features = {}
                for extractor in self.feature_extractors:
                    features.update(extractor.extract(query, candidate))
                features_list.append(features)

            # 간단한 선형 조합 스코어링 (실제 ML 모델로 대체 가능)
            for i, candidate in enumerate(candidates):
                features = features_list[i]

                # 휴리스틱 기반 가중치
                ltr_score = (
                    0.3 * features.get('query_term_coverage', 0) +
                    0.2 * features.get('tf_idf_score', 0) +
                    0.2 * features.get('doc_length_normalized', 0) +
                    0.3 * features.get('semantic_similarity', 0)
                )

                candidate['ltr_score'] = ltr_score

            # 정렬 및 반환
            candidates.sort(key=lambda x: x.get('ltr_score', 0), reverse=True)
            return candidates[:top_k]

        except Exception as e:
            logger.error(f"LTR reranking failed: {e}")
            return candidates[:top_k]


class QueryDocumentFeatures:
    """쿼리-문서 특징 추출기"""

    def extract(self, query: str, document: Dict[str, Any]) -> Dict[str, float]:
        """쿼리-문서 특징 추출"""
        text = document.get('text', '')
        title = document.get('metadata', {}).get('title', '')

        query_terms = query.lower().split()
        text_terms = text.lower().split()
        title_terms = title.lower().split()

        features = {}

        # 쿼리 용어 커버리지
        covered_terms = sum(1 for term in query_terms if term in text.lower())
        features['query_term_coverage'] = covered_terms / len(query_terms) if query_terms else 0

        # 제목 매칭
        title_covered = sum(1 for term in query_terms if term in title.lower())
        features['title_term_coverage'] = title_covered / len(query_terms) if query_terms else 0

        # 정확한 구문 매칭
        features['exact_phrase_match'] = 1.0 if query.lower() in text.lower() else 0.0

        return features


class StatisticalFeatures:
    """통계적 특징 추출기"""

    def extract(self, query: str, document: Dict[str, Any]) -> Dict[str, float]:
        """통계적 특징 추출"""
        text = document.get('text', '')

        features = {}

        # 문서 길이 정규화
        doc_length = len(text.split())
        features['doc_length'] = doc_length
        features['doc_length_normalized'] = min(doc_length / 500, 1.0)  # 500단어 기준 정규화

        # 초기 검색 점수
        features['initial_score'] = document.get('score', 0.0)

        return features


class SemanticFeatures:
    """의미적 특징 추출기"""

    def extract(self, query: str, document: Dict[str, Any]) -> Dict[str, float]:
        """의미적 특징 추출"""
        features = {}

        # 간단한 의미적 유사도 (실제로는 임베딩 기반으로 계산)
        text = document.get('text', '')

        # 공통 단어 비율
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())

        if query_words and text_words:
            features['semantic_similarity'] = len(query_words & text_words) / len(query_words | text_words)
        else:
            features['semantic_similarity'] = 0.0

        return features