"""
Intent Classification Implementation
sentence-transformers 기반 실제 의도 분류 시스템
PRD v1.8.1 요구사항 충족
"""

import asyncio
import numpy as np
import json
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import pickle

# sentence-transformers 임베딩 모델 (CPU 최적화)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available, using fallback")

# 임베딩 캐시 (기존 시스템 재사용)
try:
    from apps.api.cache.redis_manager import RedisManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logging.warning("Redis cache not available, using memory cache")

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """의도 분류 결과"""
    intent: str
    confidence: float
    candidates: List[Dict[str, float]]
    reasoning: str
    processing_time: float


class IntentCache:
    """Intent 분류 결과 캐시 시스템 (임베딩 캐시 통합)"""

    def __init__(self, use_redis: bool = True):
        self.use_redis = use_redis and CACHE_AVAILABLE
        self.memory_cache: Dict[str, IntentResult] = {}
        self.cache_ttl = 3600  # 1시간

        if self.use_redis:
            try:
                self.redis_manager = RedisManager()
            except Exception as e:
                logger.warning(f"Redis 연결 실패, 메모리 캐시 사용: {e}")
                self.use_redis = False

    def _get_cache_key(self, query: str) -> str:
        """캐시 키 생성"""
        return f"intent_classification:{hash(query.lower().strip())}"

    async def get(self, query: str) -> Optional[IntentResult]:
        """캐시에서 의도 분류 결과 조회"""
        cache_key = self._get_cache_key(query)

        # Redis 캐시 조회
        if self.use_redis:
            try:
                cached_data = await self.redis_manager.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return IntentResult(**data)
            except Exception as e:
                logger.warning(f"Redis 캐시 조회 실패: {e}")

        # 메모리 캐시 조회
        return self.memory_cache.get(cache_key)

    async def set(self, query: str, result: IntentResult):
        """캐시에 의도 분류 결과 저장"""
        cache_key = self._get_cache_key(query)

        # Redis 캐시 저장
        if self.use_redis:
            try:
                data = {
                    "intent": result.intent,
                    "confidence": result.confidence,
                    "candidates": result.candidates,
                    "reasoning": result.reasoning,
                    "processing_time": result.processing_time
                }
                await self.redis_manager.set(
                    cache_key,
                    json.dumps(data),
                    ex=self.cache_ttl
                )
            except Exception as e:
                logger.warning(f"Redis 캐시 저장 실패: {e}")

        # 메모리 캐시 저장
        self.memory_cache[cache_key] = result

        # 메모리 캐시 크기 제한
        if len(self.memory_cache) > 1000:
            # 가장 오래된 50% 제거
            keys_to_remove = list(self.memory_cache.keys())[:500]
            for key in keys_to_remove:
                del self.memory_cache[key]


class EmbeddingIntentClassifier:
    """sentence-transformers 기반 의도 분류기"""

    # 의도 카테고리 정의 (PRD 요구사항 기반)
    INTENT_CATEGORIES = {
        "search": {
            "keywords": ["검색", "찾아", "find", "search", "조회", "탐색", "찾기"],
            "patterns": ["어디에", "무엇을", "찾아줘", "검색해", "조회해"],
            "description": "정보 검색 의도"
        },
        "classify": {
            "keywords": ["분류", "카테고리", "classify", "categorize", "구분", "분류해"],
            "patterns": ["어떤 종류", "분류하면", "카테고리는", "유형은"],
            "description": "분류/카테고리화 의도"
        },
        "explain": {
            "keywords": ["설명", "알려줘", "explain", "describe", "해석", "의미"],
            "patterns": ["무엇인가", "어떤 것", "설명해", "알려줘", "의미는"],
            "description": "설명/해석 요청 의도"
        },
        "analyze": {
            "keywords": ["분석", "평가", "analyze", "evaluate", "검토", "분석해"],
            "patterns": ["분석해", "평가해", "어떻게 생각", "장단점"],
            "description": "분석/평가 의도"
        },
        "compare": {
            "keywords": ["비교", "차이점", "compare", "difference", "vs", "대비"],
            "patterns": ["차이는", "비교하면", "어떤 것이 좋", "vs"],
            "description": "비교/대조 의도"
        },
        "generate": {
            "keywords": ["생성", "만들어", "create", "generate", "작성", "만들기"],
            "patterns": ["만들어줘", "생성해", "작성해", "만드는 방법"],
            "description": "생성/창작 의도"
        },
        "troubleshoot": {
            "keywords": ["문제", "오류", "error", "fix", "해결", "고치"],
            "patterns": ["오류가", "문제가", "안 돼", "해결하는"],
            "description": "문제 해결 의도"
        },
        "general_query": {
            "keywords": ["질문", "궁금", "question", "help", "도움", "문의"],
            "patterns": ["도움이", "질문이", "궁금한"],
            "description": "일반적 질의"
        }
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.intent_embeddings = None
        self.cache = IntentCache()

        # 성능 메트릭
        self.classification_stats = {
            "total_classifications": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_confidence": 0.0,
            "intent_distribution": {intent: 0 for intent in self.INTENT_CATEGORIES.keys()}
        }

    async def initialize(self):
        """분류기 초기화 (모델 로드 및 임베딩 생성)"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers가 설치되지 않았습니다. 키워드 기반 fallback 사용")
            return

        try:
            # 모델 로드 (CPU 최적화)
            logger.info(f"Intent 분류 모델 로드 중: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)

            # 의도별 대표 임베딩 생성
            await self._generate_intent_embeddings()

            logger.info("Intent 분류기 초기화 완료")

        except Exception as e:
            logger.error(f"Intent 분류기 초기화 실패: {str(e)}")
            self.model = None

    async def _generate_intent_embeddings(self):
        """의도별 대표 임베딩 생성"""
        if not self.model:
            return

        self.intent_embeddings = {}

        for intent, config in self.INTENT_CATEGORIES.items():
            # 키워드와 패턴을 결합하여 대표 텍스트 생성
            representative_texts = []
            representative_texts.extend(config["keywords"])
            representative_texts.extend(config["patterns"])

            # 임베딩 생성
            embeddings = self.model.encode(representative_texts)

            # 평균 임베딩으로 의도 대표 벡터 생성
            intent_embedding = np.mean(embeddings, axis=0)
            self.intent_embeddings[intent] = intent_embedding

        logger.info(f"의도별 임베딩 생성 완료: {len(self.intent_embeddings)}개")

    async def classify(self, query: str) -> IntentResult:
        """쿼리의 의도 분류"""
        start_time = datetime.now()

        # 캐시 확인
        cached_result = await self.cache.get(query)
        if cached_result:
            self.classification_stats["cache_hits"] += 1
            self.classification_stats["total_classifications"] += 1
            logger.debug(f"캐시에서 의도 분류 결과 반환: {cached_result.intent}")
            return cached_result

        self.classification_stats["cache_misses"] += 1

        # 실제 분류 수행
        if self.model and self.intent_embeddings:
            result = await self._classify_with_embeddings(query)
        else:
            # Fallback: 키워드 기반 분류
            result = await self._classify_with_keywords(query)

        # 처리 시간 계산
        processing_time = (datetime.now() - start_time).total_seconds()
        result.processing_time = processing_time

        # 통계 업데이트
        self._update_stats(result)

        # 캐시 저장
        await self.cache.set(query, result)

        return result

    async def _classify_with_embeddings(self, query: str) -> IntentResult:
        """임베딩 기반 의도 분류"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.model.encode([query])[0]

            # 의도별 유사도 계산
            similarities = {}
            for intent, intent_embedding in self.intent_embeddings.items():
                similarity = np.dot(query_embedding, intent_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(intent_embedding)
                )
                similarities[intent] = float(similarity)

            # 최고 유사도 의도 선택
            best_intent = max(similarities, key=similarities.get)
            confidence = similarities[best_intent]

            # 후보 목록 생성 (상위 3개)
            candidates = [
                {"intent": intent, "confidence": conf}
                for intent, conf in sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:3]
            ]

            # 신뢰도 기반 최종 결정
            if confidence < 0.3:
                best_intent = "general_query"
                confidence = 0.6
                reasoning = "낮은 유사도로 인한 일반 질의로 분류"
            else:
                reasoning = f"임베딩 유사도 기반 분류 (유사도: {confidence:.3f})"

            return IntentResult(
                intent=best_intent,
                confidence=confidence,
                candidates=candidates,
                reasoning=reasoning,
                processing_time=0.0  # 나중에 설정됨
            )

        except Exception as e:
            logger.error(f"임베딩 기반 분류 실패: {str(e)}")
            return await self._classify_with_keywords(query)

    async def _classify_with_keywords(self, query: str) -> IntentResult:
        """키워드 기반 fallback 분류"""
        query_lower = query.lower()

        intent_scores = {}

        # 키워드 매칭 점수 계산
        for intent, config in self.INTENT_CATEGORIES.items():
            score = 0.0
            matched_keywords = []

            # 키워드 매칭
            for keyword in config["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1.0
                    matched_keywords.append(keyword)

            # 패턴 매칭
            for pattern in config["patterns"]:
                if pattern.lower() in query_lower:
                    score += 1.5  # 패턴은 더 높은 가중치
                    matched_keywords.append(pattern)

            # 정규화
            total_keywords = len(config["keywords"]) + len(config["patterns"])
            intent_scores[intent] = score / total_keywords if total_keywords > 0 else 0.0

        # 최고 점수 의도 선택
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
        else:
            best_intent = "general_query"
            confidence = 0.5

        # 후보 목록 생성
        candidates = [
            {"intent": intent, "confidence": score}
            for intent, score in sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

        # 신뢰도 조정
        if confidence < 0.1:
            best_intent = "general_query"
            confidence = 0.5
            reasoning = "키워드 매칭 실패로 일반 질의로 분류"
        else:
            reasoning = f"키워드 기반 분류 (매칭 점수: {confidence:.3f})"

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            candidates=candidates,
            reasoning=reasoning,
            processing_time=0.0
        )

    def _update_stats(self, result: IntentResult):
        """분류 통계 업데이트"""
        self.classification_stats["total_classifications"] += 1

        # 평균 신뢰도 업데이트
        total_count = self.classification_stats["total_classifications"]
        current_avg = self.classification_stats["average_confidence"]
        new_avg = ((current_avg * (total_count - 1)) + result.confidence) / total_count
        self.classification_stats["average_confidence"] = new_avg

        # 의도 분포 업데이트
        self.classification_stats["intent_distribution"][result.intent] += 1

    def get_stats(self) -> Dict[str, Any]:
        """분류 통계 반환"""
        total = self.classification_stats["total_classifications"]
        cache_hit_rate = (self.classification_stats["cache_hits"] / total * 100) if total > 0 else 0

        return {
            "model_name": self.model_name,
            "model_available": self.model is not None,
            "total_classifications": total,
            "cache_hit_rate_percent": cache_hit_rate,
            "average_confidence": self.classification_stats["average_confidence"],
            "intent_distribution": self.classification_stats["intent_distribution"]
        }


class ConfidenceScorer:
    """신뢰도 점수 계산기"""

    @staticmethod
    def calculate_confidence(
        primary_score: float,
        secondary_scores: List[float],
        query_length: int,
        keyword_matches: int
    ) -> float:
        """다양한 요소를 고려한 종합 신뢰도 계산"""

        # 기본 점수
        confidence = primary_score

        # 차별성 보너스 (1위와 2위 차이가 클수록 더 확실)
        if len(secondary_scores) > 0:
            score_gap = primary_score - max(secondary_scores)
            confidence += score_gap * 0.2

        # 쿼리 길이 보정 (너무 짧거나 긴 쿼리는 신뢰도 감소)
        length_factor = 1.0
        if query_length < 3:
            length_factor = 0.7
        elif query_length > 50:
            length_factor = 0.9

        confidence *= length_factor

        # 키워드 매칭 보너스
        if keyword_matches > 0:
            confidence += min(keyword_matches * 0.1, 0.3)

        # 0~1 범위로 정규화
        return max(0.0, min(1.0, confidence))


class IntentRouter:
    """의도별 라우팅 시스템"""

    ROUTING_CONFIG = {
        "search": {
            "requires_retrieval": True,
            "max_documents": 5,
            "enable_rerank": True,
            "enable_debate": False
        },
        "classify": {
            "requires_retrieval": True,
            "max_documents": 3,
            "enable_rerank": True,
            "enable_debate": False
        },
        "explain": {
            "requires_retrieval": True,
            "max_documents": 8,
            "enable_rerank": True,
            "enable_debate": True
        },
        "analyze": {
            "requires_retrieval": True,
            "max_documents": 10,
            "enable_rerank": True,
            "enable_debate": True
        },
        "compare": {
            "requires_retrieval": True,
            "max_documents": 12,
            "enable_rerank": True,
            "enable_debate": True
        },
        "generate": {
            "requires_retrieval": False,
            "max_documents": 2,
            "enable_rerank": False,
            "enable_debate": False
        },
        "troubleshoot": {
            "requires_retrieval": True,
            "max_documents": 6,
            "enable_rerank": True,
            "enable_debate": True
        },
        "general_query": {
            "requires_retrieval": True,
            "max_documents": 5,
            "enable_rerank": True,
            "enable_debate": False
        }
    }

    @classmethod
    def get_routing_config(cls, intent: str) -> Dict[str, Any]:
        """의도별 라우팅 설정 반환"""
        return cls.ROUTING_CONFIG.get(intent, cls.ROUTING_CONFIG["general_query"])

    @classmethod
    def should_enable_debate(cls, intent: str, confidence: float) -> bool:
        """Debate 활성화 여부 결정"""
        config = cls.get_routing_config(intent)
        base_enable = config.get("enable_debate", False)

        # 신뢰도가 낮으면 debate 활성화
        if confidence < 0.7:
            return True

        return base_enable


# 전역 인스턴스
_classifier_instance: Optional[EmbeddingIntentClassifier] = None

async def get_intent_classifier() -> EmbeddingIntentClassifier:
    """Intent 분류기 싱글톤 인스턴스 반환"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = EmbeddingIntentClassifier()
        await _classifier_instance.initialize()
    return _classifier_instance


# 편의 함수들
async def classify_intent(query: str) -> IntentResult:
    """간편 의도 분류 함수"""
    classifier = await get_intent_classifier()
    return await classifier.classify(query)


async def get_intent_routing_config(query: str) -> Tuple[IntentResult, Dict[str, Any]]:
    """의도 분류 + 라우팅 설정 반환"""
    result = await classify_intent(query)
    routing_config = IntentRouter.get_routing_config(result.intent)
    return result, routing_config


# 사용 예시 및 테스트
if __name__ == "__main__":
    async def main():
        # 분류기 초기화
        classifier = await get_intent_classifier()

        # 테스트 쿼리들
        test_queries = [
            "RAG 시스템에 대해 설명해주세요",
            "AI와 머신러닝의 차이점을 비교해주세요",
            "Python 오류를 해결하는 방법을 찾아주세요",
            "새로운 마케팅 전략을 만들어주세요",
            "이 문서를 기술 카테고리로 분류해주세요"
        ]

        for query in test_queries:
            result = await classifier.classify(query)
            routing_config = IntentRouter.get_routing_config(result.intent)

            print(f"\n쿼리: {query}")
            print(f"의도: {result.intent} (신뢰도: {result.confidence:.3f})")
            print(f"후보: {result.candidates}")
            print(f"라우팅: 검색={routing_config['requires_retrieval']}, "
                  f"최대문서={routing_config['max_documents']}, "
                  f"Debate={routing_config['enable_debate']}")

        # 통계 출력
        stats = classifier.get_stats()
        print(f"\n=== 분류 통계 ===")
        print(f"총 분류: {stats['total_classifications']}")
        print(f"캐시 적중률: {stats['cache_hit_rate_percent']:.1f}%")
        print(f"평균 신뢰도: {stats['average_confidence']:.3f}")
        print(f"의도 분포: {stats['intent_distribution']}")

    asyncio.run(main())