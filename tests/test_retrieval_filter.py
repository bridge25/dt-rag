"""
B-O2 Retrieval Filter 테스트
"""

import pytest
import sys
import os

# 상위 디렉토리의 모듈들을 import 할 수 있도록 경로 추가
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "apps", "orchestration", "src")
)

from retrieval_filter import CategoryFilter, SecurityFilter, apply_retrieval_filter


class TestCategoryFilter:
    """CategoryFilter 테스트"""

    def test_basic_filtering(self):
        """기본 필터링 테스트"""
        # 허용된 경로: AI/RAG, AI/ML
        allowed_paths = [["AI", "RAG"], ["AI", "ML"]]
        category_filter = CategoryFilter(allowed_paths)

        # 테스트 데이터
        search_results = [
            {
                "chunk_id": "chunk_001",
                "score": 0.95,
                "text": "RAG 시스템 구축...",
                "taxonomy_path": ["AI", "RAG", "Vector"],  # AI/RAG 하위 - 허용
            },
            {
                "chunk_id": "chunk_002",
                "score": 0.87,
                "text": "머신러닝 모델...",
                "taxonomy_path": ["AI", "ML", "Deep Learning"],  # AI/ML 하위 - 허용
            },
            {
                "chunk_id": "chunk_003",
                "score": 0.72,
                "text": "블록체인 기술...",
                "taxonomy_path": ["Blockchain", "Basics"],  # 허용되지 않음
            },
        ]

        # 필터링 실행
        result = category_filter.filter_search_results(search_results)

        # 검증
        assert result.original_count == 3
        assert result.filtered_count == 2  # AI/RAG, AI/ML만 허용
        assert result.blocked_count == 1  # Blockchain 차단
        assert len(result.filtered_results) == 2

        # 허용된 결과만 남아있는지 확인
        filtered_paths = [r["taxonomy_path"] for r in result.filtered_results]
        assert ["AI", "RAG", "Vector"] in filtered_paths
        assert ["AI", "ML", "Deep Learning"] in filtered_paths
        assert ["Blockchain", "Basics"] not in filtered_paths

    def test_case_insensitive_matching(self):
        """대소문자 무관 매칭 테스트"""
        allowed_paths = [["ai", "rag"]]  # 소문자
        category_filter = CategoryFilter(allowed_paths)

        search_results = [
            {
                "chunk_id": "chunk_001",
                "taxonomy_path": ["AI", "RAG", "Vector"],  # 대문자
            }
        ]

        result = category_filter.filter_search_results(search_results)

        # 대소문자 무관하게 매칭되어야 함
        assert result.filtered_count == 1
        assert result.blocked_count == 0

    def test_exact_path_matching(self):
        """정확한 경로 매칭 테스트"""
        allowed_paths = [["AI", "RAG"]]
        category_filter = CategoryFilter(allowed_paths)

        search_results = [
            {"chunk_id": "chunk_001", "taxonomy_path": ["AI", "RAG"]},  # 정확히 일치
            {
                "chunk_id": "chunk_002",
                "taxonomy_path": ["AI"],  # 상위 경로 - 차단되어야 함
            },
        ]

        result = category_filter.filter_search_results(search_results)

        # AI/RAG는 허용, AI는 차단 (상위 경로이므로)
        assert result.filtered_count == 1
        assert result.blocked_count == 1

    def test_empty_allowed_paths(self):
        """빈 허용 경로 테스트"""
        allowed_paths = []
        category_filter = CategoryFilter(allowed_paths)

        search_results = [{"chunk_id": "chunk_001", "taxonomy_path": ["AI", "RAG"]}]

        result = category_filter.filter_search_results(search_results)

        # 허용된 경로가 없으므로 모든 결과 차단
        assert result.filtered_count == 0
        assert result.blocked_count == 1

    def test_empty_document_path(self):
        """빈 문서 경로 테스트"""
        allowed_paths = [["AI", "RAG"]]
        category_filter = CategoryFilter(allowed_paths)

        search_results = [{"chunk_id": "chunk_001", "taxonomy_path": []}]  # 빈 경로

        result = category_filter.filter_search_results(search_results)

        # 빈 경로는 차단되어야 함
        assert result.filtered_count == 0
        assert result.blocked_count == 1


class TestSecurityFilter:
    """SecurityFilter 테스트"""

    def test_sql_injection_detection(self):
        """SQL 인젝션 패턴 탐지 테스트"""
        # 위험한 쿼리들
        dangerous_queries = [
            "SELECT * FROM docs OR 1=1",
            "search query'; DROP TABLE users;--",
            "normal query UNION SELECT password FROM users",
        ]

        for query in dangerous_queries:
            assert SecurityFilter.detect_bypass_attempt(query, {}) is True

    def test_filter_bypass_detection(self):
        """필터 우회 시도 탐지 테스트"""
        normal_query = "AI RAG system"

        # 정상적인 필터
        normal_filters = {"canonical_in": True}
        assert (
            SecurityFilter.detect_bypass_attempt(normal_query, normal_filters) is False
        )

        # 필터 무력화 시도
        bypass_filters = {"canonical_in": False}
        assert (
            SecurityFilter.detect_bypass_attempt(normal_query, bypass_filters) is True
        )

    def test_query_sanitization(self):
        """쿼리 정화 테스트"""
        dangerous_query = "search'; DROP TABLE--/* comment */"
        sanitized = SecurityFilter.sanitize_query(dangerous_query)

        # 위험한 문자들이 제거되어야 함
        assert "'" not in sanitized
        assert ";" not in sanitized
        assert "--" not in sanitized
        assert "/*" not in sanitized
        assert "*/" not in sanitized


class TestIntegrationFilter:
    """통합 필터 테스트"""

    def test_full_filter_pipeline(self):
        """전체 필터 파이프라인 테스트"""
        search_results = [
            {
                "chunk_id": "chunk_001",
                "score": 0.95,
                "text": "RAG 시스템...",
                "taxonomy_path": ["AI", "RAG"],
            },
            {
                "chunk_id": "chunk_002",
                "score": 0.72,
                "text": "블록체인...",
                "taxonomy_path": ["Blockchain", "Basics"],
            },
        ]

        allowed_paths = [["AI", "RAG"]]
        query = "RAG system guide"

        # 전체 필터 적용
        result = apply_retrieval_filter(
            search_results=search_results,
            allowed_category_paths=allowed_paths,
            query=query,
            user_id="test_user",
            request_id="test_request_001",
        )

        # 결과 검증
        assert result.original_count == 2
        assert result.filtered_count == 1  # AI/RAG만 허용
        assert result.blocked_count == 1  # Blockchain 차단
        assert len(result.filtered_results) == 1
        assert result.filtered_results[0]["taxonomy_path"] == ["AI", "RAG"]

    def test_security_bypass_blocking(self):
        """보안 우회 시도 차단 테스트"""
        search_results = [{"chunk_id": "chunk_001", "taxonomy_path": ["AI", "RAG"]}]

        allowed_paths = [["AI", "RAG"]]
        malicious_query = "search OR 1=1; DROP TABLE docs;--"

        # 악성 쿼리로 필터 적용
        result = apply_retrieval_filter(
            search_results=search_results,
            allowed_category_paths=allowed_paths,
            query=malicious_query,
            user_id="malicious_user",
        )

        # 모든 결과가 차단되어야 함
        assert result.filtered_count == 0
        assert result.blocked_count == len(search_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
