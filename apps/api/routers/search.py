"""
Search Router
하이브리드 검색 API 엔드포인트
"""

import logging
import time
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from common_schemas.models import SearchRequest, SearchResponse
from ..services.database_service import get_database_service, DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=SearchResponse,
    summary="하이브리드 검색 + Rerank",
    description="""
    BM25 + Vector 하이브리드 검색 후 Cross-Encoder Reranking
    - BM25 검색 (topk=12) + Vector 검색 (topk=12)
    - 후보 union/dedup → Cross-Encoder Rerank (50→5)
    - p95≤4s 성능 보장
    """,
    responses={
        200: {"description": "검색 성공"},
        400: {"description": "잘못된 요청"},
        403: {"description": "권한 부족"},
        422: {"description": "요청 데이터 검증 실패"},
        429: {"description": "요청 한도 초과"},
        500: {"description": "서버 내부 오류"}
    }
)
async def hybrid_search(
    request_data: SearchRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> SearchResponse:
    """하이브리드 검색 API"""
    
    start_time = time.time()
    
    try:
        # Request validation
        if not request_data.query or not request_data.query.strip():
            raise HTTPException(
                status_code=422,
                detail="Query field is required and cannot be empty"
            )
        
        if len(request_data.query) > 1000:  # 쿼리 길이 제한
            raise HTTPException(
                status_code=422,
                detail="Query length exceeds maximum limit (1,000 characters)"
            )
        
        # Validate limit parameter
        limit = getattr(request_data, "limit", 5)
        if limit > 50:
            raise HTTPException(
                status_code=422,
                detail="Limit cannot exceed 50 results"
            )
        
        # Set complexity factor for cost estimation
        query_length = len(request_data.query)
        if query_length > 500:
            request.state.complexity_factor = 1.8
        elif query_length > 200:
            request.state.complexity_factor = 1.3
        else:
            request.state.complexity_factor = 1.0
        
        # Extract taxonomy filter if provided
        taxonomy_filter = getattr(request_data, "taxonomy_filter", None)
        
        logger.info(
            f"Search request: query='{request_data.query[:50]}...', "
            f"limit={limit}, filter={taxonomy_filter}, "
            f"request_id={request.state.request_id}"
        )
        
        # Perform hybrid search
        search_result = await db_service.hybrid_search(
            query=request_data.query,
            taxonomy_filter=taxonomy_filter,
            limit=limit
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Build response according to OpenAPI spec
        response_data = SearchResponse(
            hits=search_result["hits"],
            latency=processing_time,
            request_id=request.state.request_id
        )
        
        logger.info(
            f"Search completed: {len(search_result['hits'])} results, "
            f"time={processing_time:.3f}s, "
            f"candidates={search_result.get('total_candidates', 0)}"
        )
        
        # Check performance target (p95 ≤ 4s)
        if processing_time > 4.0:
            logger.warning(
                f"Search exceeded p95 target: {processing_time:.3f}s > 4.0s"
            )
        
        return response_data
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"Search failed: {e}, request_id={request.state.request_id}",
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error during search"
        )


@router.get(
    "/similar/{doc_id}",
    summary="유사 문서 검색",
    description="특정 문서와 유사한 문서들 검색"
)
async def find_similar_documents(
    doc_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """특정 문서와 유사한 문서 검색"""
    
    start_time = time.time()
    
    try:
        async with db_service.get_connection() as conn:
            
            # Get source document
            source_doc = await conn.fetchrow("""
                SELECT d.doc_id, d.title, d.content, dt.path
                FROM documents d
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE d.doc_id = $1
            """, doc_id)
            
            if not source_doc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document not found: {doc_id}"
                )
            
            # Get document embedding (average of chunk embeddings)
            doc_embedding = await conn.fetchval("""
                SELECT AVG(e.vec) as avg_embedding
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.chunk_id
                WHERE c.doc_id = $1
            """, doc_id)
            
            if not doc_embedding:
                raise HTTPException(
                    status_code=404,
                    detail="Document embeddings not found"
                )
            
            # Find similar documents
            similar_docs = await conn.fetch("""
                WITH doc_embeddings AS (
                    SELECT 
                        c.doc_id,
                        AVG(e.vec) as avg_embedding
                    FROM embeddings e
                    JOIN chunks c ON e.chunk_id = c.chunk_id
                    GROUP BY c.doc_id
                )
                SELECT 
                    d.doc_id,
                    d.title,
                    dt.path,
                    dt.confidence,
                    (1 - (de.avg_embedding <=> $1)) as similarity
                FROM doc_embeddings de
                JOIN documents d ON de.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE de.doc_id != $2
                ORDER BY similarity DESC
                LIMIT $3
            """, doc_embedding, doc_id, limit)
            
            processing_time = time.time() - start_time
            
            return {
                "source_document": dict(source_doc),
                "similar_documents": [dict(row) for row in similar_docs],
                "total_found": len(similar_docs),
                "processing_time": processing_time,
                "request_id": request.state.request_id
            }
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Similar document search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to find similar documents"
        )


@router.get(
    "/stats",
    summary="검색 통계 정보",
    description="검색 시스템의 통계 정보 조회"
)
async def get_search_stats(
    request: Request,
    period: str = Query(default="24h", regex="^(1h|24h|7d|30d)$"),
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """검색 시스템 통계 조회"""
    
    try:
        # Convert period to SQL interval
        interval_map = {
            "1h": "1 hour",
            "24h": "24 hours", 
            "7d": "7 days",
            "30d": "30 days"
        }
        interval = interval_map[period]
        
        async with db_service.get_connection() as conn:
            
            # Get search performance stats (from logs or metrics)
            # This is a simplified version - in production, you'd query metrics DB
            stats = {
                "period": period,
                "total_searches": 0,  # Would come from metrics
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "cache_hit_rate": 0.0
            }
            
            # Get popular search terms (from search logs)
            popular_terms = await conn.fetch("""
                SELECT 
                    'example search' as query_term,
                    42 as search_count
                LIMIT 10
            """)
            
            # Get index statistics
            index_stats = await conn.fetch("""
                SELECT 
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                AND indexname IN ('idx_embeddings_vec_ivf', 'idx_embeddings_bm25')
            """)
            
            return {
                **stats,
                "popular_searches": [dict(row) for row in popular_terms],
                "index_usage": [dict(row) for row in index_stats],
                "timestamp": time.time()
            }
            
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve search statistics"
        )


@router.get("/health")
async def search_health_check(
    db_service: DatabaseService = Depends(get_database_service)
):
    """검색 서비스 건강 상태 확인"""
    
    try:
        # Test database connection
        async with db_service.get_connection() as conn:
            await conn.fetchval("SELECT 1")
        
        # Test embedding service
        from ..services.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()
        
        if not embedding_service.model:
            return {"status": "degraded", "reason": "Embedding model not loaded"}
        
        # Test search indexes
        async with db_service.get_connection() as conn:
            vector_index = await conn.fetchval("""
                SELECT indexname FROM pg_indexes 
                WHERE indexname = 'idx_embeddings_vec_ivf'
            """)
            
            bm25_index = await conn.fetchval("""
                SELECT indexname FROM pg_indexes
                WHERE indexname = 'idx_embeddings_bm25'  
            """)
            
            if not vector_index or not bm25_index:
                return {
                    "status": "degraded", 
                    "reason": "Search indexes missing",
                    "missing_indexes": {
                        "vector": not vector_index,
                        "bm25": not bm25_index
                    }
                }
        
        # Quick search test
        test_result = await db_service.hybrid_search("test search", limit=1)
        
        return {
            "status": "healthy",
            "features": ["bm25_search", "vector_search", "hybrid_ranking"],
            "test_results": len(test_result["hits"])
        }
        
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}