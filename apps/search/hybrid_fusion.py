"""
고급 하이브리드 검색 스코어 융합 시스템
다양한 정규화 및 융합 기법 구현
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class FusionMethod(Enum):
    """스코어 융합 방법"""
    WEIGHTED_SUM = "weighted_sum"
    RRF = "reciprocal_rank_fusion"  # Reciprocal Rank Fusion
    CombSUM = "comb_sum"
    CombMNZ = "comb_mnz"
    BORDA_COUNT = "borda_count"
    CONDORCET = "condorcet"

class NormalizationMethod(Enum):
    """점수 정규화 방법"""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    RANK_BASED = "rank_based"
    RECIPROCAL_RANK = "reciprocal_rank"
    SIGMOID = "sigmoid"

@dataclass
class SearchCandidate:
    """검색 후보"""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    bm25_score: Optional[float] = None
    vector_score: Optional[float] = None
    bm25_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    final_score: Optional[float] = None
    sources: List[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []

class HybridScoreFusion:
    """하이브리드 검색 스코어 융합 엔진"""

    def __init__(
        self,
        fusion_method: FusionMethod = FusionMethod.WEIGHTED_SUM,
        normalization_method: NormalizationMethod = NormalizationMethod.MIN_MAX,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ):
        """
        Args:
            fusion_method: 융합 방법
            normalization_method: 정규화 방법
            bm25_weight: BM25 가중치
            vector_weight: Vector 가중치
        """
        self.fusion_method = fusion_method
        self.normalization_method = normalization_method
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    def fuse_results(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        max_candidates: int = 100
    ) -> List[SearchCandidate]:
        """결과 융합 수행"""
        try:
            # 후보 생성 및 중복 제거
            candidates = self._create_candidates(bm25_results, vector_results)

            # 점수 정규화
            candidates = self._normalize_scores(candidates)

            # 융합 수행
            candidates = self._apply_fusion(candidates)

            # 점수순 정렬
            candidates.sort(key=lambda x: x.final_score or 0, reverse=True)

            return candidates[:max_candidates]

        except Exception as e:
            logger.error(f"Score fusion failed: {e}")
            return []

    def _create_candidates(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]]
    ) -> List[SearchCandidate]:
        """후보 생성 및 중복 제거"""
        candidates_dict = {}

        # BM25 결과 처리
        for rank, result in enumerate(bm25_results):
            chunk_id = result.get('chunk_id')
            if not chunk_id:
                continue

            candidate = SearchCandidate(
                chunk_id=chunk_id,
                text=result.get('text', ''),
                metadata=result.get('metadata', {}),
                bm25_score=result.get('bm25_score', 0.0),
                bm25_rank=rank + 1,
                sources=['bm25']
            )
            candidates_dict[chunk_id] = candidate

        # Vector 결과 처리
        for rank, result in enumerate(vector_results):
            chunk_id = result.get('chunk_id')
            if not chunk_id:
                continue

            vector_score = result.get('score', 0.0)

            if chunk_id in candidates_dict:
                # 기존 후보 업데이트
                candidate = candidates_dict[chunk_id]
                candidate.vector_score = vector_score
                candidate.vector_rank = rank + 1
                candidate.sources.append('vector')
            else:
                # 새 후보 생성
                candidate = SearchCandidate(
                    chunk_id=chunk_id,
                    text=result.get('text', ''),
                    metadata=result.get('metadata', {}),
                    vector_score=vector_score,
                    vector_rank=rank + 1,
                    sources=['vector']
                )
                candidates_dict[chunk_id] = candidate

        return list(candidates_dict.values())

    def _normalize_scores(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """점수 정규화"""
        try:
            # BM25 점수 정규화
            bm25_scores = [c.bm25_score for c in candidates if c.bm25_score is not None]
            if bm25_scores:
                normalized_bm25 = self._normalize_score_list(bm25_scores)
                bm25_idx = 0
                for candidate in candidates:
                    if candidate.bm25_score is not None:
                        candidate.bm25_score = normalized_bm25[bm25_idx]
                        bm25_idx += 1

            # Vector 점수 정규화
            vector_scores = [c.vector_score for c in candidates if c.vector_score is not None]
            if vector_scores:
                normalized_vector = self._normalize_score_list(vector_scores)
                vector_idx = 0
                for candidate in candidates:
                    if candidate.vector_score is not None:
                        candidate.vector_score = normalized_vector[vector_idx]
                        vector_idx += 1

            return candidates

        except Exception as e:
            logger.error(f"Score normalization failed: {e}")
            return candidates

    def _normalize_score_list(self, scores: List[float]) -> List[float]:
        """점수 리스트 정규화"""
        if not scores:
            return scores

        scores_array = np.array(scores)

        if self.normalization_method == NormalizationMethod.MIN_MAX:
            min_score = scores_array.min()
            max_score = scores_array.max()
            if max_score == min_score:
                return [1.0] * len(scores)
            return ((scores_array - min_score) / (max_score - min_score)).tolist()

        elif self.normalization_method == NormalizationMethod.Z_SCORE:
            mean = scores_array.mean()
            std = scores_array.std()
            if std == 0:
                return [0.0] * len(scores)
            z_scores = (scores_array - mean) / std
            # Z-score를 0-1 범위로 변환 (sigmoid)
            return (1 / (1 + np.exp(-z_scores))).tolist()

        elif self.normalization_method == NormalizationMethod.RANK_BASED:
            # 순위 기반 정규화
            sorted_indices = np.argsort(scores_array)[::-1]
            ranks = np.empty_like(sorted_indices)
            ranks[sorted_indices] = np.arange(len(scores))
            return (1 - ranks / len(scores)).tolist()

        elif self.normalization_method == NormalizationMethod.RECIPROCAL_RANK:
            # 역순위 정규화
            sorted_indices = np.argsort(scores_array)[::-1]
            ranks = np.empty_like(sorted_indices)
            ranks[sorted_indices] = np.arange(1, len(scores) + 1)
            return (1 / ranks).tolist()

        elif self.normalization_method == NormalizationMethod.SIGMOID:
            # Sigmoid 정규화
            return (1 / (1 + np.exp(-scores_array))).tolist()

        else:
            return scores

    def _apply_fusion(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """융합 적용"""
        try:
            if self.fusion_method == FusionMethod.WEIGHTED_SUM:
                return self._weighted_sum_fusion(candidates)
            elif self.fusion_method == FusionMethod.RRF:
                return self._reciprocal_rank_fusion(candidates)
            elif self.fusion_method == FusionMethod.CombSUM:
                return self._comb_sum_fusion(candidates)
            elif self.fusion_method == FusionMethod.CombMNZ:
                return self._comb_mnz_fusion(candidates)
            elif self.fusion_method == FusionMethod.BORDA_COUNT:
                return self._borda_count_fusion(candidates)
            elif self.fusion_method == FusionMethod.CONDORCET:
                return self._condorcet_fusion(candidates)
            else:
                return self._weighted_sum_fusion(candidates)

        except Exception as e:
            logger.error(f"Fusion application failed: {e}")
            return candidates

    def _weighted_sum_fusion(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """가중합 융합"""
        for candidate in candidates:
            bm25_contrib = (candidate.bm25_score or 0) * self.bm25_weight
            vector_contrib = (candidate.vector_score or 0) * self.vector_weight

            candidate.final_score = bm25_contrib + vector_contrib

        return candidates

    def _reciprocal_rank_fusion(self, candidates: List[SearchCandidate], k: int = 60) -> List[SearchCandidate]:
        """Reciprocal Rank Fusion (RRF)"""
        for candidate in candidates:
            rrf_score = 0.0

            if candidate.bm25_rank is not None:
                rrf_score += self.bm25_weight / (k + candidate.bm25_rank)

            if candidate.vector_rank is not None:
                rrf_score += self.vector_weight / (k + candidate.vector_rank)

            candidate.final_score = rrf_score

        return candidates

    def _comb_sum_fusion(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """CombSUM 융합"""
        for candidate in candidates:
            score = 0.0
            count = 0

            if candidate.bm25_score is not None:
                score += candidate.bm25_score * self.bm25_weight
                count += 1

            if candidate.vector_score is not None:
                score += candidate.vector_score * self.vector_weight
                count += 1

            candidate.final_score = score

        return candidates

    def _comb_mnz_fusion(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """CombMNZ 융합 (점수 × 검색 시스템 수)"""
        for candidate in candidates:
            score = 0.0
            system_count = 0

            if candidate.bm25_score is not None:
                score += candidate.bm25_score * self.bm25_weight
                system_count += 1

            if candidate.vector_score is not None:
                score += candidate.vector_score * self.vector_weight
                system_count += 1

            candidate.final_score = score * system_count

        return candidates

    def _borda_count_fusion(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """Borda Count 융합"""
        total_candidates = len(candidates)

        for candidate in candidates:
            borda_score = 0.0

            if candidate.bm25_rank is not None:
                borda_score += (total_candidates - candidate.bm25_rank) * self.bm25_weight

            if candidate.vector_rank is not None:
                borda_score += (total_candidates - candidate.vector_rank) * self.vector_weight

            candidate.final_score = borda_score

        return candidates

    def _condorcet_fusion(self, candidates: List[SearchCandidate]) -> List[SearchCandidate]:
        """Condorcet 융합 (쌍대 비교)"""
        # 간단화된 Condorcet: 각 후보에 대해 다른 후보들과 비교
        for i, candidate in enumerate(candidates):
            wins = 0
            total_comparisons = 0

            for j, other in enumerate(candidates):
                if i == j:
                    continue

                bm25_wins = 0
                vector_wins = 0

                # BM25 비교
                if (candidate.bm25_score is not None and other.bm25_score is not None and
                    candidate.bm25_score > other.bm25_score):
                    bm25_wins = 1

                # Vector 비교
                if (candidate.vector_score is not None and other.vector_score is not None and
                    candidate.vector_score > other.vector_score):
                    vector_wins = 1

                # 가중 승수
                weighted_wins = bm25_wins * self.bm25_weight + vector_wins * self.vector_weight
                if weighted_wins > 0.5:  # 과반수 승리
                    wins += 1

                total_comparisons += 1

            candidate.final_score = wins / total_comparisons if total_comparisons > 0 else 0.0

        return candidates


class AdaptiveFusion:
    """적응형 융합 시스템"""

    def __init__(self):
        self.query_history = []
        self.performance_metrics = defaultdict(list)

    def adaptive_fuse(
        self,
        query: str,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        query_type: str = "general"
    ) -> List[SearchCandidate]:
        """쿼리 특성에 따른 적응형 융합"""
        try:
            # 쿼리 특성 분석
            query_features = self._analyze_query(query)

            # 최적 융합 방법 선택
            fusion_config = self._select_fusion_method(query_features, query_type)

            # 융합 수행
            fusion_engine = HybridScoreFusion(**fusion_config)
            results = fusion_engine.fuse_results(bm25_results, vector_results)

            return results

        except Exception as e:
            logger.error(f"Adaptive fusion failed: {e}")
            # 기본 가중합 폴백
            default_fusion = HybridScoreFusion()
            return default_fusion.fuse_results(bm25_results, vector_results)

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """쿼리 특성 분석"""
        features = {
            'length': len(query.split()),
            'has_quotes': '"' in query,
            'has_boolean': any(op in query.lower() for op in ['and', 'or', 'not']),
            'is_question': query.strip().endswith('?'),
            'has_technical_terms': self._has_technical_terms(query),
            'language': 'en' if query.isascii() else 'ko'
        }
        return features

    def _has_technical_terms(self, query: str) -> bool:
        """기술 용어 포함 여부 확인"""
        technical_keywords = [
            'api', 'algorithm', 'database', 'machine learning', 'ai',
            'neural network', 'deep learning', 'nlp', 'embedding'
        ]
        query_lower = query.lower()
        return any(term in query_lower for term in technical_keywords)

    def _select_fusion_method(
        self,
        query_features: Dict[str, Any],
        query_type: str
    ) -> Dict[str, Any]:
        """최적 융합 방법 선택"""
        config = {
            'fusion_method': FusionMethod.WEIGHTED_SUM,
            'normalization_method': NormalizationMethod.MIN_MAX,
            'bm25_weight': 0.5,
            'vector_weight': 0.5
        }

        # 쿼리 길이에 따른 가중치 조정
        if query_features['length'] <= 2:
            # 짧은 쿼리: BM25 우선
            config['bm25_weight'] = 0.7
            config['vector_weight'] = 0.3
        elif query_features['length'] >= 6:
            # 긴 쿼리: Vector 우선
            config['bm25_weight'] = 0.3
            config['vector_weight'] = 0.7

        # 기술 용어 포함 시 Vector 우선
        if query_features['has_technical_terms']:
            config['bm25_weight'] = 0.4
            config['vector_weight'] = 0.6
            config['fusion_method'] = FusionMethod.RRF

        # 정확한 구문 검색 시 BM25 우선
        if query_features['has_quotes']:
            config['bm25_weight'] = 0.8
            config['vector_weight'] = 0.2

        # 질문 형태 시 Vector 우선
        if query_features['is_question']:
            config['bm25_weight'] = 0.4
            config['vector_weight'] = 0.6

        return config

    def update_performance(
        self,
        query: str,
        fusion_method: str,
        performance_score: float
    ):
        """성능 피드백 업데이트"""
        self.performance_metrics[fusion_method].append(performance_score)
        # 최근 100개 기록만 유지
        if len(self.performance_metrics[fusion_method]) > 100:
            self.performance_metrics[fusion_method] = \
                self.performance_metrics[fusion_method][-100:]