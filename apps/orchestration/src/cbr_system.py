"""
B-O4: CBR (Case-Based Reasoning) 시스템
A팀 case_bank 테이블 연동 + 유사도 로그/성과 레이블 적재 (PRD 준수)
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """유사도 계산 결과"""

    case_id: str
    similarity_score: float
    category_path: List[str]
    quality_score: float


class VectorSimilarity:
    """벡터 유사도 계산"""

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        코사인 유사도 계산

        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터

        Returns:
            float: 코사인 유사도 (0.0 ~ 1.0)
        """
        try:
            # numpy 배열로 변환
            a = np.array(vec1)
            b = np.array(vec2)

            # 영벡터 처리
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            # 코사인 유사도 계산
            similarity = np.dot(a, b) / (norm_a * norm_b)

            # 0~1 범위로 정규화 (코사인 유사도는 -1~1 범위)
            normalized_similarity = (similarity + 1) / 2

            return float(np.clip(normalized_similarity, 0.0, 1.0))

        except Exception as e:
            logger.error(f"코사인 유사도 계산 오류: {e}")
            return 0.0

    @staticmethod
    def euclidean_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        유클리드 유사도 계산 (거리의 역수)

        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터

        Returns:
            float: 유클리드 유사도 (0.0 ~ 1.0)
        """
        try:
            a = np.array(vec1)
            b = np.array(vec2)

            # 유클리드 거리 계산
            distance = np.linalg.norm(a - b)

            # 유사도로 변환 (거리가 작을수록 유사도가 높음)
            # 1 / (1 + distance) 공식 사용
            similarity = 1.0 / (1.0 + distance)

            return float(np.clip(similarity, 0.0, 1.0))

        except Exception as e:
            logger.error(f"유클리드 유사도 계산 오류: {e}")
            return 0.0


class CaseBankManager:
    """A팀 case_bank 테이블 연동 매니저 (PRD 준수)"""

    def __init__(self, a_team_base_url: str = "http://localhost:8001"):
        """
        Args:
            a_team_base_url: A팀 API 기본 URL
        """
        self.a_team_base_url = a_team_base_url
        # HTTP client configuration from environment
        env_base = os.getenv("ORCH_A_TEAM_BASE_URL") or os.getenv("A_TEAM_BASE_URL")
        if env_base:
            self.a_team_base_url = env_base
        max_keepalive = int(os.getenv("ORCH_HTTP_MAX_KEEPALIVE", "20"))
        max_connections = int(os.getenv("ORCH_HTTP_MAX_CONNECTIONS", "100"))
        limits = httpx.Limits(
            max_keepalive_connections=max_keepalive, max_connections=max_connections
        )
        generic_t = os.getenv("HTTP_TIMEOUT")
        connect_t = (
            float(os.getenv("ORCH_HTTP_TIMEOUT_CONNECT", "5.0"))
            if generic_t is None
            else float(generic_t)
        )
        read_t = (
            float(os.getenv("ORCH_HTTP_TIMEOUT_READ", "10.0"))
            if generic_t is None
            else float(generic_t)
        )
        write_t = (
            float(os.getenv("ORCH_HTTP_TIMEOUT_WRITE", "10.0"))
            if generic_t is None
            else float(generic_t)
        )
        pool_t = (
            float(os.getenv("ORCH_HTTP_TIMEOUT_POOL", "10.0"))
            if generic_t is None
            else float(generic_t)
        )
        timeout = httpx.Timeout(
            connect=connect_t, read=read_t, write=write_t, pool=pool_t
        )
        self.client = httpx.AsyncClient(limits=limits, timeout=timeout)

    async def get_case_bank_data(
        self, category_path: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        A팀 case_bank 테이블에서 케이스 데이터 조회 (PRD 준수)

        Args:
            category_path: 카테고리 경로 필터

        Returns:
            List[Dict[str, Any]]: 케이스 데이터 목록
        """
        try:
            # A팀 case_bank API 호출
            params = {}
            if category_path:
                params["category_path"] = ",".join(category_path)

            response = await self.client.get(
                f"{self.a_team_base_url}/case_bank", params=params
            )
            response.raise_for_status()
            try:
                cases_data = response.json()
            except ValueError:
                logger.error("Invalid JSON from A-team /case_bank response")
                cases_data = []
                logger.info(f"A팀 case_bank 조회 완료: {len(cases_data)}개")
                return cases_data
            else:
                logger.error(f"A팀 case_bank API 호출 실패: {response.status_code}")

        except Exception as e:
            logger.error(f"A팀 case_bank 조회 실패: {str(e)}")

        # A팀 API 호출 실패 시 빈 목록 반환
        logger.warning("A팀 case_bank 연동 실패, 빈 목록 반환")
        return []

    async def load_cases(
        self, category_path: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        A팀 case_bank 테이블에서 케이스 데이터 로드 (PRD 준수)

        Args:
            category_path: 카테고리 경로 필터

        Returns:
            List[Dict[str, Any]]: 케이스 데이터 목록
        """
        return await self.get_case_bank_data(category_path)

    def filter_by_category(
        self, cases: List[Dict[str, Any]], category_path: List[str]
    ) -> List[Dict[str, Any]]:
        """카테고리 경로로 케이스 필터링"""
        if not category_path:
            return cases

        filtered_cases = []
        for case in cases:
            case_category = case.get("metadata", {}).get("category_path", [])

            # 카테고리 경로가 요청된 경로의 하위인지 확인
            if self._is_subcategory(case_category, category_path):
                filtered_cases.append(case)

        return filtered_cases

    def _is_subcategory(self, case_path: List[str], filter_path: List[str]) -> bool:
        """케이스 경로가 필터 경로의 하위 카테고리인지 확인"""
        if len(case_path) < len(filter_path):
            return False

        for i, filter_segment in enumerate(filter_path):
            if i >= len(case_path) or case_path[i].lower() != filter_segment.lower():
                return False

        return True


class CBRRecommendationEngine:
    """CBR 추천 엔진 (A팀 case_bank 연동)"""

    def __init__(self, a_team_base_url: str = "http://localhost:8001"):
        self.case_bank = CaseBankManager(a_team_base_url)
        self.similarity_calculator = VectorSimilarity()

    async def find_similar_cases(
        self,
        query_vector: List[float],
        category_path: Optional[List[str]] = None,
        k: int = 5,
        similarity_threshold: float = 0.7,
        similarity_method: str = "cosine",
    ) -> List[SimilarityResult]:
        """
        A팀 case_bank에서 유사한 케이스 찾기 (k-NN) (PRD 준수)

        Args:
            query_vector: 쿼리 벡터
            category_path: 카테고리 필터
            k: 반환할 케이스 수
            similarity_threshold: 유사도 임계값
            similarity_method: 유사도 계산 방법 (cosine/euclidean)

        Returns:
            List[SimilarityResult]: 유사도 순으로 정렬된 케이스 목록
        """
        # A팀 case_bank에서 케이스 로드 (카테고리 필터 적용)
        all_cases = await self.case_bank.load_cases(category_path)

        # 유사도 계산
        similarities = []

        for case in all_cases:
            case_vector = case.get("query_vector", [])

            if not case_vector:
                continue

            # 유사도 계산
            if similarity_method == "cosine":
                score = self.similarity_calculator.cosine_similarity(
                    query_vector, case_vector
                )
            elif similarity_method == "euclidean":
                score = self.similarity_calculator.euclidean_similarity(
                    query_vector, case_vector
                )
            else:
                score = self.similarity_calculator.cosine_similarity(
                    query_vector, case_vector
                )

            # 임계값 확인
            if score >= similarity_threshold:
                similarities.append(
                    SimilarityResult(
                        case_id=case["case_id"],
                        similarity_score=score,
                        category_path=case["metadata"]["category_path"],
                        quality_score=case["metadata"]["quality_score"],
                    )
                )

        # 유사도 순으로 정렬 (높은 순)
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)

        # 상위 k개 반환
        return similarities[:k]


class CBRUsageLogger:
    """CBR 사용 로그 수집"""

    def __init__(self, log_path: str = "./cbr_logs"):
        self.log_path = log_path
        self.usage_log_file = os.path.join(log_path, "usage_log.jsonl")
        self.feedback_log_file = os.path.join(log_path, "feedback_log.jsonl")

        # 디렉토리 생성
        os.makedirs(log_path, exist_ok=True)

    def log_query(
        self,
        request_id: str,
        query: str,
        category_path: Optional[List[str]],
        picked_case_ids: List[str],
        similarity_scores: List[float],
        user_id: Optional[str] = None,
    ):
        """쿼리 로그 기록"""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "category_path": category_path,
            "picked_case_ids": picked_case_ids,
            "similarity_scores": similarity_scores,
            "user_id": user_id,
            "event_type": "cbr_query",
        }

        self._write_log(self.usage_log_file, log_entry)

    def log_feedback(
        self,
        request_id: str,
        selected_case_ids: List[str],
        user_rating: int,
        success_flag: bool,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """피드백 로그 기록"""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "selected_case_ids": selected_case_ids,
            "user_rating": user_rating,
            "success_flag": success_flag,
            "feedback_text": feedback_text,
            "user_id": user_id,
            "event_type": "cbr_feedback",
        }

        self._write_log(self.feedback_log_file, log_entry)

    def _write_log(self, file_path: str, log_entry: Dict[str, Any]):
        """로그 파일 쓰기"""
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"로그 쓰기 실패: {e}")


import numpy as np

# 실제 임베딩 모델 초기화
from sentence_transformers import SentenceTransformer

# 전역 임베딩 모델 (한번만 로드)
_embedding_model = None


def get_embedding_model():
    """싱글톤 패턴으로 임베딩 모델 반환"""
    global _embedding_model
    if _embedding_model is None:
        # 경량 다국어 모델 사용 (한국어 지원)
        _embedding_model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    return _embedding_model


def create_query_vector_real(query: str) -> List[float]:
    """실제 임베딩 모델 기반 쿼리 벡터 생성"""
    try:
        model = get_embedding_model()
        # 실제 임베딩 생성
        embedding = model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        # 실패 시 에러 발생 (시뮬레이션으로 폴백하지 않음)
        raise ValueError(f"임베딩 생성 실패: {e}")
