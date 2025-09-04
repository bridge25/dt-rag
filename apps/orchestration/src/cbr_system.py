"""
B-O4: CBR (Case-Based Reasoning) 시스템
CaseBank read-only 조회 + 유사도 로그/성과 레이블 적재
"""

import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
import os

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
    """케이스 뱅크 관리"""
    
    def __init__(self, case_bank_path: str = "./case_bank"):
        """
        Args:
            case_bank_path: 케이스 뱅크 저장 경로
        """
        self.case_bank_path = case_bank_path
        self.cases_file = os.path.join(case_bank_path, "cases.jsonl")
        self.metadata_file = os.path.join(case_bank_path, "metadata.json")
        
        # 디렉토리 생성
        os.makedirs(case_bank_path, exist_ok=True)
        
        # Mock 데이터 초기화
        self._initialize_mock_cases()
    
    def _initialize_mock_cases(self):
        """Mock 케이스 데이터 초기화"""
        if not os.path.exists(self.cases_file):
            mock_cases = [
                {
                    "case_id": "case_001",
                    "query_vector": [0.8, 0.6, 0.9, 0.7, 0.5],
                    "response_text": "RAG 시스템 구축을 위해서는 먼저 문서를 벡터화하고, 검색 인덱스를 구성한 후, 검색-생성 파이프라인을 연결해야 합니다.",
                    "metadata": {
                        "case_id": "case_001",
                        "category_path": ["AI", "RAG"],
                        "quality_score": 0.9,
                        "usage_count": 15,
                        "success_rate": 0.85,
                        "created_at": "2025-08-01T10:00:00Z",
                        "last_used_at": "2025-09-04T14:30:00Z"
                    }
                },
                {
                    "case_id": "case_002", 
                    "query_vector": [0.7, 0.8, 0.6, 0.9, 0.4],
                    "response_text": "머신러닝 모델 훈련 시에는 데이터 전처리, 특성 선택, 모델 선택, 하이퍼파라미터 튜닝 순서로 진행하는 것이 효과적입니다.",
                    "metadata": {
                        "case_id": "case_002",
                        "category_path": ["AI", "ML"],
                        "quality_score": 0.8,
                        "usage_count": 12,
                        "success_rate": 0.75,
                        "created_at": "2025-08-02T11:00:00Z",
                        "last_used_at": "2025-09-03T16:20:00Z"
                    }
                },
                {
                    "case_id": "case_003",
                    "query_vector": [0.6, 0.5, 0.8, 0.7, 0.9],
                    "response_text": "자연어 처리에서는 토크나이제이션, 임베딩, 어텐션 메커니즘을 통해 문맥을 이해하고 적절한 응답을 생성할 수 있습니다.",
                    "metadata": {
                        "case_id": "case_003", 
                        "category_path": ["AI", "NLP"],
                        "quality_score": 0.85,
                        "usage_count": 8,
                        "success_rate": 0.9,
                        "created_at": "2025-08-03T09:30:00Z",
                        "last_used_at": "2025-09-02T13:45:00Z"
                    }
                },
                {
                    "case_id": "case_004",
                    "query_vector": [0.4, 0.7, 0.5, 0.6, 0.8],
                    "response_text": "딥러닝 모델의 성능을 향상시키려면 배치 정규화, 드롭아웃, 학습률 스케줄링 등의 기법을 적용할 수 있습니다.",
                    "metadata": {
                        "case_id": "case_004",
                        "category_path": ["AI", "Deep Learning"],
                        "quality_score": 0.75,
                        "usage_count": 6,
                        "success_rate": 0.8,
                        "created_at": "2025-08-04T14:15:00Z",
                        "last_used_at": "2025-09-01T11:30:00Z"
                    }
                },
                {
                    "case_id": "case_005",
                    "query_vector": [0.9, 0.4, 0.7, 0.8, 0.6],
                    "response_text": "벡터 데이터베이스는 고차원 벡터의 빠른 유사도 검색을 위해 특별히 최적화된 데이터베이스입니다.",
                    "metadata": {
                        "case_id": "case_005",
                        "category_path": ["AI", "RAG", "Vector DB"],
                        "quality_score": 0.95,
                        "usage_count": 20,
                        "success_rate": 0.92,
                        "created_at": "2025-07-28T16:45:00Z",
                        "last_used_at": "2025-09-04T10:15:00Z"
                    }
                }
            ]
            
            # JSONL 형태로 저장
            with open(self.cases_file, 'w', encoding='utf-8') as f:
                for case in mock_cases:
                    f.write(json.dumps(case, ensure_ascii=False) + '\n')
                    
            logger.info(f"Mock 케이스 데이터 초기화 완료: {len(mock_cases)}개")
    
    def load_cases(self) -> List[Dict[str, Any]]:
        """케이스 데이터 로드"""
        cases = []
        
        if os.path.exists(self.cases_file):
            try:
                with open(self.cases_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            cases.append(json.loads(line.strip()))
                            
                logger.info(f"케이스 로드 완료: {len(cases)}개")
                
            except Exception as e:
                logger.error(f"케이스 로드 실패: {e}")
                
        return cases
    
    def filter_by_category(
        self,
        cases: List[Dict[str, Any]], 
        category_path: List[str]
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
    """CBR 추천 엔진"""
    
    def __init__(self, case_bank_path: str = "./case_bank"):
        self.case_bank = CaseBankManager(case_bank_path)
        self.similarity_calculator = VectorSimilarity()
    
    def find_similar_cases(
        self,
        query_vector: List[float],
        category_path: Optional[List[str]] = None,
        k: int = 5,
        similarity_threshold: float = 0.7,
        similarity_method: str = "cosine"
    ) -> List[SimilarityResult]:
        """
        유사한 케이스 찾기 (k-NN)
        
        Args:
            query_vector: 쿼리 벡터
            category_path: 카테고리 필터
            k: 반환할 케이스 수
            similarity_threshold: 유사도 임계값
            similarity_method: 유사도 계산 방법 (cosine/euclidean)
            
        Returns:
            List[SimilarityResult]: 유사도 순으로 정렬된 케이스 목록
        """
        # 케이스 로드
        all_cases = self.case_bank.load_cases()
        
        # 카테고리 필터 적용
        if category_path:
            filtered_cases = self.case_bank.filter_by_category(all_cases, category_path)
        else:
            filtered_cases = all_cases
        
        # 유사도 계산
        similarities = []
        
        for case in filtered_cases:
            case_vector = case.get("query_vector", [])
            
            if not case_vector:
                continue
                
            # 유사도 계산
            if similarity_method == "cosine":
                score = self.similarity_calculator.cosine_similarity(query_vector, case_vector)
            elif similarity_method == "euclidean":
                score = self.similarity_calculator.euclidean_similarity(query_vector, case_vector)
            else:
                score = self.similarity_calculator.cosine_similarity(query_vector, case_vector)
            
            # 임계값 확인
            if score >= similarity_threshold:
                similarities.append(SimilarityResult(
                    case_id=case["case_id"],
                    similarity_score=score,
                    category_path=case["metadata"]["category_path"],
                    quality_score=case["metadata"]["quality_score"]
                ))
        
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
        user_id: Optional[str] = None
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
            "event_type": "cbr_query"
        }
        
        self._write_log(self.usage_log_file, log_entry)
    
    def log_feedback(
        self,
        request_id: str,
        selected_case_ids: List[str],
        user_rating: int,
        success_flag: bool,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None
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
            "event_type": "cbr_feedback"
        }
        
        self._write_log(self.feedback_log_file, log_entry)
    
    def _write_log(self, file_path: str, log_entry: Dict[str, Any]):
        """로그 파일 쓰기"""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"로그 쓰기 실패: {e}")

def create_query_vector_mock(query: str) -> List[float]:
    """Mock 쿼리 벡터 생성 (실제로는 임베딩 모델 사용)"""
    # 간단한 해시 기반 벡터 생성 (실제 구현에서는 sentence-transformers 등 사용)
    import hashlib
    
    # 쿼리의 해시를 사용하여 일관된 벡터 생성
    hash_obj = hashlib.md5(query.encode('utf-8'))
    hash_bytes = hash_obj.digest()
    
    # 5차원 벡터로 변환 (0~1 범위)
    vector = []
    for i in range(5):
        byte_val = hash_bytes[i % len(hash_bytes)]
        normalized_val = byte_val / 255.0
        vector.append(normalized_val)
    
    return vector