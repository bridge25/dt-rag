"""
Database Service
PostgreSQL + pgvector 연결 및 쿼리 관리
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from contextlib import asynccontextmanager

import asyncpg
import asyncio
from pgvector.asyncpg import register_vector

logger = logging.getLogger(__name__)


class DatabaseService:
    """PostgreSQL + pgvector 데이터베이스 서비스"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_string = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/dt_rag"
        )
    
    async def initialize(self):
        """데이터베이스 연결 풀 초기화"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30,
                server_settings={
                    'application_name': 'dt_rag_api',
                }
            )
            
            # Register pgvector types
            async with self.pool.acquire() as conn:
                await register_vector(conn)
                
            logger.info("✅ Database pool initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def close(self):
        """연결 풀 종료"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """데이터베이스 건강 상태 확인"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                
                # Check critical tables
                tables = await conn.fetch("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('taxonomy_nodes', 'chunks', 'embeddings', 'doc_taxonomy')
                """)
                
                return {
                    "status": "healthy",
                    "tables_count": len(tables),
                    "connection_pool": {
                        "size": self.pool.get_size(),
                        "idle": self.pool.get_idle_size()
                    }
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @asynccontextmanager
    async def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        async with self.pool.acquire() as conn:
            yield conn
    
    async def classify_text(
        self, 
        text: str, 
        taxonomy_version: str = "1.8.1"
    ) -> Dict[str, Any]:
        """텍스트 분류 수행"""
        
        async with self.get_connection() as conn:
            
            # 1. Rule-based classification (1단계)
            rule_result = await self._rule_based_classify(conn, text)
            
            # 2. Get embedding for text
            from .embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            embedding = await embedding_service.get_embedding(text)
            
            # 3. Vector similarity search
            similar_chunks = await conn.fetch("""
                SELECT 
                    c.text,
                    dt.path,
                    dt.confidence,
                    e.vec <=> $1 as similarity
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.chunk_id
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                ORDER BY similarity
                LIMIT 5
            """, embedding)
            
            # 4. Confidence calculation
            confidence = await self._calculate_confidence(
                conn, rule_result, similar_chunks, text
            )
            
            # 5. Get canonical path
            canonical_path = rule_result.get("path", ["Unknown"])
            
            # 6. HITL queue if low confidence
            if confidence < 0.7:
                await self._add_to_hitl_queue(
                    conn, text, canonical_path, confidence
                )
            
            # 7. Store classification result
            await self._store_classification(
                conn, text, canonical_path, confidence, taxonomy_version
            )
            
            return {
                "canonical": canonical_path,
                "candidates": [row["path"] for row in similar_chunks if row["path"]],
                "confidence": confidence,
                "reasoning": [
                    f"Rule-based match: {rule_result.get('reason', 'No match')}",
                    f"Vector similarity: {len(similar_chunks)} similar chunks found"
                ]
            }
    
    async def hybrid_search(
        self, 
        query: str,
        taxonomy_filter: Optional[List[str]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """하이브리드 검색 (BM25 + Vector)"""
        
        async with self.get_connection() as conn:
            
            # Get query embedding
            from .embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            query_embedding = await embedding_service.get_embedding(query)
            
            # BM25 search
            bm25_query = """
                SELECT DISTINCT
                    c.chunk_id,
                    c.text,
                    d.title,
                    dt.path,
                    dt.confidence,
                    ts_rank_cd(e.bm25_tokens, plainto_tsquery($1)) as bm25_score,
                    'bm25' as search_type
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.chunk_id
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE e.bm25_tokens @@ plainto_tsquery($1)
            """
            
            # Vector search  
            vector_query = """
                SELECT DISTINCT
                    c.chunk_id,
                    c.text,
                    d.title,
                    dt.path,
                    dt.confidence,
                    (1 - (e.vec <=> $1)) as vector_score,
                    'vector' as search_type
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.chunk_id
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                ORDER BY e.vec <=> $1
            """
            
            # Add taxonomy filter if provided
            taxonomy_condition = ""
            if taxonomy_filter:
                taxonomy_condition = " AND dt.path && $2"
            
            # Execute searches
            bm25_results = await conn.fetch(
                bm25_query + taxonomy_condition + " ORDER BY bm25_score DESC LIMIT 12",
                query, taxonomy_filter if taxonomy_filter else None
            )
            
            vector_results = await conn.fetch(
                vector_query + taxonomy_condition + " LIMIT 12",
                query_embedding, taxonomy_filter if taxonomy_filter else None
            )
            
            # Merge and deduplicate results
            merged_results = await self._merge_search_results(
                bm25_results, vector_results, limit
            )
            
            return {
                "hits": [dict(row) for row in merged_results],
                "total_candidates": len(bm25_results) + len(vector_results),
                "search_strategy": "hybrid_bm25_vector"
            }
    
    async def get_taxonomy_tree(self, version: str) -> Dict[str, Any]:
        """택소노미 트리 구조 조회"""
        
        async with self.get_connection() as conn:
            
            # Get nodes
            nodes = await conn.fetch("""
                SELECT node_id, canonical_path, node_name, version, created_at
                FROM taxonomy_nodes
                WHERE version = $1
                ORDER BY canonical_path
            """, version)
            
            # Get edges
            edges = await conn.fetch("""
                SELECT parent_id, child_id, version
                FROM taxonomy_edges  
                WHERE version = $1
            """, version)
            
            return {
                "nodes": [dict(row) for row in nodes],
                "edges": [dict(row) for row in edges],
                "version": version,
                "total_nodes": len(nodes)
            }
    
    async def _rule_based_classify(self, conn: asyncpg.Connection, text: str) -> Dict[str, Any]:
        """규칙 기반 분류"""
        
        # Simple keyword-based rules (확장 가능)
        rules = {
            "AI": ["artificial intelligence", "machine learning", "ai", "ml"],
            "Technology": ["software", "hardware", "programming", "code"],
            "Business": ["revenue", "profit", "customer", "market"],
        }
        
        text_lower = text.lower()
        
        for category, keywords in rules.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return {
                        "path": [category],
                        "reason": f"Keyword match: '{keyword}'"
                    }
        
        return {
            "path": ["Unknown"],
            "reason": "No rule matches found"
        }
    
    async def _calculate_confidence(
        self, 
        conn: asyncpg.Connection,
        rule_result: Dict[str, Any],
        similar_chunks: List[Dict[str, Any]],
        text: str
    ) -> float:
        """신뢰도 계산"""
        
        # Simple confidence calculation (개선 가능)
        base_confidence = 0.5
        
        # Rule match boost
        if rule_result.get("path") != ["Unknown"]:
            base_confidence += 0.2
        
        # Vector similarity boost
        if similar_chunks:
            avg_similarity = sum(1 - row["similarity"] for row in similar_chunks) / len(similar_chunks)
            base_confidence += min(avg_similarity * 0.3, 0.3)
        
        return min(base_confidence, 1.0)
    
    async def _add_to_hitl_queue(
        self,
        conn: asyncpg.Connection,
        text: str,
        path: List[str],
        confidence: float
    ):
        """HITL 큐에 추가"""
        
        await conn.execute("""
            INSERT INTO hitl_queue (text, suggested_path, confidence, status, created_at)
            VALUES ($1, $2, $3, 'pending', NOW())
        """, text, path, confidence)
        
        logger.info(f"Added to HITL queue: confidence={confidence:.2f}")
    
    async def _store_classification(
        self,
        conn: asyncpg.Connection,
        text: str,
        path: List[str], 
        confidence: float,
        taxonomy_version: str
    ):
        """분류 결과 저장"""
        
        # This would typically involve more complex logic
        # For now, just log the classification
        logger.info(f"Classification stored: {path}, confidence={confidence:.2f}")
    
    async def _merge_search_results(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """검색 결과 병합 및 순위 조정"""
        
        # Simple merging strategy (개선 가능)
        all_results = {}
        
        # Add BM25 results
        for result in bm25_results:
            chunk_id = result["chunk_id"]
            all_results[chunk_id] = dict(result)
            all_results[chunk_id]["combined_score"] = result.get("bm25_score", 0)
        
        # Add vector results
        for result in vector_results:
            chunk_id = result["chunk_id"]
            if chunk_id in all_results:
                # Combine scores
                all_results[chunk_id]["combined_score"] += result.get("vector_score", 0)
                all_results[chunk_id]["search_type"] = "hybrid"
            else:
                all_results[chunk_id] = dict(result)
                all_results[chunk_id]["combined_score"] = result.get("vector_score", 0)
        
        # Sort by combined score and limit
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["combined_score"],
            reverse=True
        )
        
        return sorted_results[:limit]


# Singleton instance
_db_service_instance = None

def get_database_service() -> DatabaseService:
    """데이터베이스 서비스 싱글톤 인스턴스 반환"""
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DatabaseService()
    return _db_service_instance