"""
Embedding Service
텍스트 임베딩 생성 및 벡터 검색 지원
"""

import os
import logging
from typing import List, Dict, Any, Optional
import asyncio
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class EmbeddingService:
    """텍스트 임베딩 생성 서비스"""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.model_name = os.getenv(
            "EMBEDDING_MODEL", 
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
    async def initialize(self):
        """임베딩 모델 초기화"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            
            # Load model in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self.model_name, device=self.device)
            )
            
            logger.info(f"✅ Embedding model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Embedding model loading failed: {e}")
            raise
    
    async def close(self):
        """리소스 정리"""
        if self.model:
            del self.model
            self.model = None
            
            # Clear GPU memory if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Embedding service closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """임베딩 서비스 건강 상태 확인"""
        try:
            if not self.model:
                return {"status": "unhealthy", "error": "Model not loaded"}
            
            # Test embedding generation
            test_embedding = await self.get_embedding("test")
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "device": self.device,
                "dimension": len(test_embedding),
                "test_embedding_norm": float(np.linalg.norm(test_embedding))
            }
            
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @lru_cache(maxsize=1000)
    def _cached_embedding(self, text: str) -> np.ndarray:
        """캐시된 임베딩 생성 (동기)"""
        return self.model.encode([text])[0]
    
    async def get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성"""
        try:
            if not self.model:
                raise RuntimeError("Embedding model not initialized")
            
            # Normalize text
            text = text.strip()[:512]  # Limit length
            if not text:
                text = "empty"
            
            # Generate embedding in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self._cached_embedding,
                text
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Embedding generation failed for text: {text[:50]}... Error: {e}")
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩 생성"""
        try:
            if not self.model:
                raise RuntimeError("Embedding model not initialized")
            
            # Normalize texts
            normalized_texts = []
            for text in texts:
                normalized = text.strip()[:512]
                if not normalized:
                    normalized = "empty"
                normalized_texts.append(normalized)
            
            # Generate embeddings in executor
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(normalized_texts)
            )
            
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise
    
    async def compute_similarity(
        self, 
        text1: str, 
        text2: str
    ) -> float:
        """두 텍스트 간 유사도 계산"""
        try:
            emb1 = await self.get_embedding(text1)
            emb2 = await self.get_embedding(text2)
            
            # Cosine similarity
            emb1_np = np.array(emb1)
            emb2_np = np.array(emb2)
            
            similarity = np.dot(emb1_np, emb2_np) / (
                np.linalg.norm(emb1_np) * np.linalg.norm(emb2_np)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            raise
    
    async def find_most_similar(
        self, 
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """가장 유사한 텍스트들 찾기"""
        try:
            query_embedding = await self.get_embedding(query_text)
            candidate_embeddings = await self.get_embeddings_batch(candidate_texts)
            
            query_np = np.array(query_embedding)
            similarities = []
            
            for i, candidate_emb in enumerate(candidate_embeddings):
                candidate_np = np.array(candidate_emb)
                similarity = np.dot(query_np, candidate_np) / (
                    np.linalg.norm(query_np) * np.linalg.norm(candidate_np)
                )
                
                similarities.append({
                    "index": i,
                    "text": candidate_texts[i],
                    "similarity": float(similarity)
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Most similar search failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension,
            "is_loaded": self.model is not None
        }


# Singleton instance  
_embedding_service_instance = None

def get_embedding_service() -> EmbeddingService:
    """임베딩 서비스 싱글톤 인스턴스 반환"""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance