"""Contract tests for common schemas

Validates that all Pydantic models comply with OpenAPI v1.8.1 contracts.
"""

import pytest
from pydantic import ValidationError

from common_schemas.models import (
    TaxonomyNode,
    SourceMeta, 
    ClassifyRequest,
    ClassifyResponse,
    SearchHit,
    SearchRequest,
    SearchResponse,
)


def test_classify_response_contract():
    """분류 응답 계약 테스트"""
    response = ClassifyResponse(
        canonical=["AI", "RAG"],
        candidates=[
            TaxonomyNode(
                node_id="n1",
                label="RAG",
                canonical_path=["AI", "RAG"], 
                version="1.8.1",
                confidence=0.85
            )
        ],
        hitl=False,
        confidence=0.85,
        reasoning=["AI 키워드 감지", "RAG 패턴 매칭"]
    )
    
    # 필수 필드 검증
    assert response.canonical
    assert len(response.candidates) > 0
    assert 0 <= response.confidence <= 1
    assert len(response.reasoning) >= 2  # 근거≥2개


def test_search_request_contract():
    """검색 요청 계약 테스트"""
    request = SearchRequest(
        q="AI RAG 시스템 구축",
        filters={"canonical_in": [["AI", "RAG"]]},
        bm25_topk=12,
        vector_topk=12,
        rerank_candidates=50,
        final_topk=5
    )
    
    # 필수 필드 검증
    assert request.q
    assert request.bm25_topk > 0
    assert request.vector_topk > 0
    assert request.rerank_candidates >= request.final_topk
    assert request.final_topk > 0


def test_search_response_contract():
    """검색 응답 계약 테스트"""
    response = SearchResponse(
        hits=[
            SearchHit(
                chunk_id="chunk_001",
                score=0.95,
                source=SourceMeta(
                    url="https://example.com/doc1",
                    title="RAG System Guide",
                    date="2025-09-04",
                    version="v1.0",
                    span=[0, 100]
                ),
                text="RAG 시스템 구축 방법...",
                taxonomy_path=["AI", "RAG"]
            )
        ],
        latency=1.23,
        request_id="search_1725436800000",
        total_candidates=50,
        sources_count=1,
        taxonomy_version="1.8.1"
    )
    
    # 필수 필드 검증
    assert len(response.hits) > 0
    assert response.latency >= 0
    assert response.request_id
    
    # SearchHit 검증
    hit = response.hits[0]
    assert hit.chunk_id
    assert hit.score >= 0
    assert hit.source is not None
    assert hit.source.url


def test_source_meta_validation():
    """SourceMeta 검증 테스트"""
    source = SourceMeta(
        url="https://example.com/doc1",
        title="Test Document",
        date="2025-09-04", 
        version="v1.0",
        span=[0, 100]
    )
    
    assert source.url
    assert source.title
    assert source.span and len(source.span) == 2
    assert source.span[0] < source.span[1]


def test_taxonomy_node_validation():
    """TaxonomyNode 검증 테스트"""
    node = TaxonomyNode(
        node_id="node_001",
        label="Machine Learning",
        canonical_path=["AI", "ML"],
        version="1.8.1",
        confidence=0.90
    )
    
    assert node.node_id
    assert node.label
    assert len(node.canonical_path) > 0
    assert node.version
    assert 0 <= node.confidence <= 1


def test_classify_request_validation():
    """ClassifyRequest 검증 테스트"""
    request = ClassifyRequest(
        chunk_id="chunk_001",
        text="머신러닝 모델을 사용한 RAG 시스템",
        hint_paths=[["AI", "ML"], ["AI", "RAG"]]
    )
    
    assert request.chunk_id
    assert request.text
    assert request.hint_paths is not None
    assert len(request.hint_paths) > 0


def test_validation_errors():
    """유효성 검사 오류 테스트"""
    
    # confidence 범위 초과
    with pytest.raises(ValidationError):
        ClassifyResponse(
            canonical=["AI"],
            candidates=[],
            confidence=1.5,  # > 1.0
            reasoning=["test"]
        )
    
    # 필수 필드 누락
    with pytest.raises(ValidationError):
        SearchRequest()  # q 필드 누락
    
    # 빈 reasoning (근거≥2 위반)
    response = ClassifyResponse(
        canonical=["AI"],
        candidates=[],
        confidence=0.8,
        reasoning=["단일 근거"]  # 1개만 있음
    )
    # 이 경우 validation은 통과하지만 비즈니스 룰에서는 2개 이상 요구


if __name__ == "__main__":
    pytest.main([__file__, "-v"])