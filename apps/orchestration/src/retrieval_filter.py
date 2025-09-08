"""
B-O2: Retriever 스코프 제한 필터
allowed_category_paths 기반 retrieval 필터 (범위 외 접근 차단)
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FilterResult:
    """필터링 결과"""
    filtered_results: List[Dict[str, Any]]
    original_count: int
    filtered_count: int
    blocked_count: int
    applied_paths: List[List[str]]

class CategoryFilter:
    """카테고리 경로 기반 필터"""
    
    def __init__(self, allowed_category_paths: List[List[str]]):
        """
        Args:
            allowed_category_paths: 허용된 카테고리 경로 목록
            예: [["AI", "RAG"], ["AI", "ML"]]
        """
        self.allowed_category_paths = allowed_category_paths
        self.logger = logging.getLogger(__name__)
    
    def is_path_allowed(self, document_path: List[str]) -> bool:
        """
        문서의 canonical_path가 허용된 경로인지 확인
        
        Args:
            document_path: 문서의 canonical_path (예: ["AI", "RAG", "Vector"])
            
        Returns:
            bool: 허용 여부
        """
        if not document_path:
            return False
            
        # 허용된 경로 중 하나라도 문서 경로의 상위 경로면 허용
        for allowed_path in self.allowed_category_paths:
            if self._is_subpath(document_path, allowed_path):
                return True
                
        return False
    
    def _is_subpath(self, document_path: List[str], allowed_path: List[str]) -> bool:
        """
        document_path가 allowed_path의 하위 경로인지 확인
        
        Args:
            document_path: 문서 경로 (예: ["AI", "RAG", "Vector"])
            allowed_path: 허용 경로 (예: ["AI", "RAG"])
            
        Returns:
            bool: 하위 경로 여부
        """
        if len(document_path) < len(allowed_path):
            return False
            
        # 허용된 경로의 모든 요소가 문서 경로 앞부분과 일치하는지 확인
        for i, allowed_segment in enumerate(allowed_path):
            if i >= len(document_path) or document_path[i].lower() != allowed_segment.lower():
                return False
                
        return True
    
    def filter_search_results(self, search_results: List[Dict[str, Any]]) -> FilterResult:
        """
        검색 결과를 필터링
        
        Args:
            search_results: 검색 결과 리스트
            각 결과는 'taxonomy_path' 필드를 가져야 함
            
        Returns:
            FilterResult: 필터링 결과
        """
        original_count = len(search_results)
        filtered_results = []
        blocked_count = 0
        
        for result in search_results:
            taxonomy_path = result.get('taxonomy_path', [])
            
            if self.is_path_allowed(taxonomy_path):
                filtered_results.append(result)
            else:
                blocked_count += 1
                self.logger.info(
                    f"범위 외 문서 차단: {taxonomy_path}, 허용 경로: {self.allowed_category_paths}"
                )
        
        filtered_count = len(filtered_results)
        
        # 필터 적용 로깅
        self.logger.info(
            f"필터 적용 결과: 원본 {original_count}건 → 필터링 {filtered_count}건 "
            f"(차단 {blocked_count}건)"
        )
        
        return FilterResult(
            filtered_results=filtered_results,
            original_count=original_count,
            filtered_count=filtered_count,
            blocked_count=blocked_count,
            applied_paths=self.allowed_category_paths
        )

class SecurityFilter:
    """보안 필터 - 필터 우회 시도 탐지 및 차단"""
    
    @staticmethod
    def detect_bypass_attempt(query: str, filters: Dict[str, Any]) -> bool:
        """
        필터 우회 시도 탐지
        
        Args:
            query: 검색 쿼리
            filters: 적용된 필터
            
        Returns:
            bool: 우회 시도 여부
        """
        # SQL injection 스타일 패턴 탐지
        bypass_patterns = [
            "OR 1=1",
            "UNION SELECT", 
            "'; DROP",
            "../",
            "null",
            "undefined",
            "__proto__"
        ]
        
        query_lower = query.lower()
        for pattern in bypass_patterns:
            if pattern.lower() in query_lower:
                logger.warning(f"필터 우회 시도 탐지: {pattern} in query: {query}")
                return True
        
        # 필터 무력화 시도 탐지
        if isinstance(filters, dict):
            filter_str = str(filters).lower()
            if "canonical_in" in filter_str and "false" in filter_str:
                logger.warning(f"필터 무력화 시도 탐지: {filters}")
                return True
                
        return False
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        쿼리 정화
        
        Args:
            query: 원본 쿼리
            
        Returns:
            str: 정화된 쿼리
        """
        # 위험한 문자열 제거
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', '<', '>', '&', '|']
        sanitized = query
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, " ")
            
        # 연속 공백 정규화
        import re
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized

class AuditLogger:
    """감사 로그 - 누가/언제/어떤 범위로 접근했는지"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
    
    def log_access(
        self,
        user_id: Optional[str],
        query: str,
        allowed_paths: List[List[str]],
        result_count: int,
        blocked_count: int,
        request_id: Optional[str] = None
    ):
        """
        접근 로그 기록
        
        Args:
            user_id: 사용자 ID
            query: 검색 쿼리  
            allowed_paths: 허용된 경로
            result_count: 결과 수
            blocked_count: 차단된 수
            request_id: 요청 ID
        """
        self.logger.info({
            "event": "retrieval_access",
            "user_id": user_id or "anonymous",
            "query": query,
            "allowed_paths": allowed_paths,
            "result_count": result_count,
            "blocked_count": blocked_count,
            "request_id": request_id,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def apply_retrieval_filter(
    search_results: List[Dict[str, Any]],
    allowed_category_paths: List[List[str]],
    query: str = "",
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> FilterResult:
    """
    검색 결과에 retrieval 필터 적용 (메인 함수)
    
    Args:
        search_results: 검색 결과
        allowed_category_paths: 허용된 카테고리 경로
        query: 검색 쿼리 (보안 검사용)
        user_id: 사용자 ID (감사 로그용)
        request_id: 요청 ID (추적용)
        
    Returns:
        FilterResult: 필터링 결과
    """
    # 보안 검사
    if SecurityFilter.detect_bypass_attempt(query, {"canonical_in": True}):
        logger.error(f"필터 우회 시도 차단: query={query}, user={user_id}")
        return FilterResult(
            filtered_results=[],
            original_count=len(search_results),
            filtered_count=0,
            blocked_count=len(search_results),
            applied_paths=allowed_category_paths
        )
    
    # 카테고리 필터 적용
    category_filter = CategoryFilter(allowed_category_paths)
    result = category_filter.filter_search_results(search_results)
    
    # 감사 로그 기록
    audit_logger = AuditLogger()
    audit_logger.log_access(
        user_id=user_id,
        query=SecurityFilter.sanitize_query(query),
        allowed_paths=allowed_category_paths,
        result_count=result.filtered_count,
        blocked_count=result.blocked_count,
        request_id=request_id
    )
    
    return result