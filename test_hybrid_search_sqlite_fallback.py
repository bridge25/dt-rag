#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하이브리드 검색 시스템 SQLite 폴백 테스트
PostgreSQL 연결이 없는 환경에서도 모든 기능을 테스트

실제 데이터베이스 대신 SQLite 메모리 DB를 사용하여
BM25 + Vector Similarity + Cross-Encoder Reranking 기능을 검증
"""

import asyncio
import time
import logging
import json
import traceback
import sqlite3
import tempfile
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime
import uuid
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from apps.api.database import BM25Scorer, EmbeddingService, CrossEncoderReranker

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_search_sqlite_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SQLiteSearchDAO:
    """SQLite 기반 검색 DAO (테스트용)"""

    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # 테이블 생성
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                source_url TEXT,
                content_type TEXT DEFAULT 'text/plain',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT,
                text TEXT NOT NULL,
                chunk_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                embedding_id TEXT PRIMARY KEY,
                chunk_id TEXT,
                vec TEXT,  -- JSON 문자열로 저장
                model_name TEXT DEFAULT 'text-embedding-ada-002',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chunk_id) REFERENCES chunks (chunk_id)
            );

            CREATE TABLE IF NOT EXISTS doc_taxonomy (
                mapping_id TEXT PRIMARY KEY,
                doc_id TEXT,
                path TEXT,  -- JSON 문자열로 저장
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'manual',
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
            );

            -- 인덱스 생성
            CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks(text);
            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
            CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
        """)
        self.conn.commit()

    async def insert_test_data(self, test_documents: List[Dict]):
        """테스트 데이터 삽입"""
        try:
            for i, doc_data in enumerate(test_documents):
                doc_id = str(uuid.uuid4())
                chunk_id = str(uuid.uuid4())

                # 문서 삽입
                self.conn.execute("""
                    INSERT OR REPLACE INTO documents (doc_id, title, source_url)
                    VALUES (?, ?, ?)
                """, (doc_id, doc_data["title"], f"https://example.com/{i}"))

                # 청크 삽입
                self.conn.execute("""
                    INSERT OR REPLACE INTO chunks (chunk_id, doc_id, text, chunk_index)
                    VALUES (?, ?, ?, ?)
                """, (chunk_id, doc_id, doc_data["text"], i))

                # 임베딩 생성 및 삽입
                embedding = await EmbeddingService.generate_embedding(doc_data["text"])
                if embedding:
                    self.conn.execute("""
                        INSERT OR REPLACE INTO embeddings (embedding_id, chunk_id, vec)
                        VALUES (?, ?, ?)
                    """, (str(uuid.uuid4()), chunk_id, json.dumps(embedding)))

                # 분류 정보 삽입
                if "category" in doc_data:
                    self.conn.execute("""
                        INSERT OR REPLACE INTO doc_taxonomy (mapping_id, doc_id, path, confidence)
                        VALUES (?, ?, ?, ?)
                    """, (str(uuid.uuid4()), doc_id, json.dumps(doc_data["category"]), 0.9))

            self.conn.commit()
            logger.info(f"{len(test_documents)}개 테스트 문서 삽입 완료")
            return True

        except Exception as e:
            logger.error(f"테스트 데이터 삽입 실패: {e}")
            return False

    async def bm25_search(self, query: str, topk: int = 10) -> List[Dict[str, Any]]:
        """BM25 기반 검색 (SQLite FTS 사용)"""
        try:
            # 쿼리 토큰화
            query_tokens = BM25Scorer.preprocess_text(query)
            if not query_tokens:
                return []

            # 모든 청크 조회 및 BM25 스코어 계산
            cursor = self.conn.execute("""
                SELECT c.chunk_id, c.text, d.title, d.source_url
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
            """)

            results = []
            all_docs = []

            # 코퍼스 통계 수집
            for row in cursor.fetchall():
                doc_tokens = BM25Scorer.preprocess_text(row['text'])
                all_docs.append(doc_tokens)

            # 코퍼스 통계 계산
            total_docs = len(all_docs)
            avg_doc_length = sum(len(doc) for doc in all_docs) / max(1, total_docs)
            term_doc_freq = {}

            for doc_tokens in all_docs:
                unique_terms = set(doc_tokens)
                for term in unique_terms:
                    term_doc_freq[term] = term_doc_freq.get(term, 0) + 1

            corpus_stats = {
                "total_docs": total_docs,
                "avg_doc_length": avg_doc_length,
                "term_doc_freq": term_doc_freq
            }

            # 다시 쿼리 실행하여 스코어 계산
            cursor = self.conn.execute("""
                SELECT c.chunk_id, c.text, d.title, d.source_url
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
            """)

            for row in cursor.fetchall():
                doc_tokens = BM25Scorer.preprocess_text(row['text'])
                score = BM25Scorer.calculate_bm25_score(query_tokens, doc_tokens, corpus_stats)

                if score > 0:  # 0점 초과인 것만 포함
                    results.append({
                        "chunk_id": row['chunk_id'],
                        "text": row['text'],
                        "title": row['title'],
                        "source_url": row['source_url'],
                        "taxonomy_path": [],
                        "score": score,
                        "metadata": {
                            "bm25_score": score,
                            "vector_score": 0.0,
                            "source": "bm25"
                        }
                    })

            # 점수순 정렬 및 상위 k개 반환
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:topk]

        except Exception as e:
            logger.error(f"BM25 검색 실패: {e}")
            return []

    async def vector_search(self, query: str, topk: int = 10) -> List[Dict[str, Any]]:
        """벡터 유사도 검색"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = await EmbeddingService.generate_embedding(query)
            if not query_embedding:
                return []

            query_vec = np.array(query_embedding).reshape(1, -1)

            # 모든 임베딩 조회
            cursor = self.conn.execute("""
                SELECT e.chunk_id, e.vec, c.text, d.title, d.source_url
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.chunk_id
                JOIN documents d ON c.doc_id = d.doc_id
            """)

            results = []
            for row in cursor.fetchall():
                try:
                    # JSON에서 벡터 복원
                    doc_embedding = json.loads(row['vec'])
                    doc_vec = np.array(doc_embedding).reshape(1, -1)

                    # 코사인 유사도 계산
                    similarity = cosine_similarity(query_vec, doc_vec)[0][0]

                    results.append({
                        "chunk_id": row['chunk_id'],
                        "text": row['text'],
                        "title": row['title'],
                        "source_url": row['source_url'],
                        "taxonomy_path": [],
                        "score": float(similarity),
                        "metadata": {
                            "bm25_score": 0.0,
                            "vector_score": float(similarity),
                            "source": "vector"
                        }
                    })
                except Exception as e:
                    logger.warning(f"임베딩 처리 오류: {e}")
                    continue

            # 유사도순 정렬 및 상위 k개 반환
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:topk]

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []

    async def hybrid_search(
        self,
        query: str,
        filters: Dict = None,
        topk: int = 5,
        bm25_topk: int = 12,
        vector_topk: int = 12,
        rerank_candidates: int = 50
    ) -> List[Dict[str, Any]]:
        """하이브리드 검색 (BM25 + Vector + Cross-encoder Reranking)"""
        try:
            logger.info(f"하이브리드 검색 시작: '{query}'")

            # 1. BM25 검색
            bm25_results = await self.bm25_search(query, bm25_topk)
            logger.info(f"BM25 결과: {len(bm25_results)}개")

            # 2. Vector 검색
            vector_results = await self.vector_search(query, vector_topk)
            logger.info(f"Vector 결과: {len(vector_results)}개")

            # 3. 결과 합성 (중복 제거 및 하이브리드 스코어 계산)
            combined_results = self._combine_search_results(
                bm25_results, vector_results, rerank_candidates
            )
            logger.info(f"합성 결과: {len(combined_results)}개")

            # 4. Cross-encoder 재랭킹
            if combined_results:
                final_results = CrossEncoderReranker.rerank_results(
                    query, combined_results, topk
                )
                logger.info(f"재랭킹 결과: {len(final_results)}개")
                return final_results

            return []

        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return []

    def _combine_search_results(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        max_candidates: int
    ) -> List[Dict]:
        """BM25와 Vector 검색 결과 합성"""
        BM25_WEIGHT = 0.5
        VECTOR_WEIGHT = 0.5

        combined = {}

        # BM25 결과 추가
        for result in bm25_results:
            chunk_id = result["chunk_id"]
            combined[chunk_id] = result.copy()

        # Vector 결과 추가/업데이트
        for result in vector_results:
            chunk_id = result["chunk_id"]
            if chunk_id in combined:
                # 기존 결과에 vector 정보 추가
                combined[chunk_id]["metadata"]["vector_score"] = result["metadata"]["vector_score"]
                # 하이브리드 스코어 계산
                bm25_score = combined[chunk_id]["metadata"]["bm25_score"]
                vector_score = result["metadata"]["vector_score"]
                combined[chunk_id]["score"] = BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score
                combined[chunk_id]["metadata"]["source"] = "hybrid"
            else:
                # 새로운 vector 전용 결과
                combined[chunk_id] = result.copy()

        # 점수순 정렬 및 상위 후보 선택
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        return sorted_results[:max_candidates]

    def get_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        try:
            stats = {}

            # 기본 통계
            cursor = self.conn.execute("SELECT COUNT(*) FROM documents")
            stats["total_docs"] = cursor.fetchone()[0]

            cursor = self.conn.execute("SELECT COUNT(*) FROM chunks")
            stats["total_chunks"] = cursor.fetchone()[0]

            cursor = self.conn.execute("SELECT COUNT(*) FROM embeddings")
            stats["embedded_chunks"] = cursor.fetchone()[0]

            cursor = self.conn.execute("SELECT COUNT(*) FROM doc_taxonomy")
            stats["taxonomy_mappings"] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}

class HybridSearchSQLiteTester:
    """SQLite 기반 하이브리드 검색 테스터"""

    def __init__(self):
        self.search_dao = SQLiteSearchDAO()
        self.test_results = {}

        # 테스트 문서 데이터
        self.test_documents = [
            {
                "title": "RAG 시스템 개요",
                "text": "RAG(Retrieval-Augmented Generation)는 검색 기반 생성 모델입니다. 이 시스템은 외부 데이터베이스에서 관련 정보를 검색하고, 이를 기반으로 답변을 생성합니다. 벡터 임베딩과 유사도 계산을 통해 관련 문서를 찾습니다.",
                "category": ["AI", "RAG"]
            },
            {
                "title": "Machine Learning Classification",
                "text": "Machine learning classification algorithms include Support Vector Machines (SVM), Random Forest, and Neural Networks. These algorithms learn patterns from training data to classify new instances. Feature engineering and model selection are crucial for performance.",
                "category": ["AI", "ML"]
            },
            {
                "title": "벡터 데이터베이스 활용",
                "text": "벡터 데이터베이스는 고차원 벡터 데이터를 효율적으로 저장하고 검색할 수 있습니다. pgvector와 같은 확장을 통해 PostgreSQL에서도 벡터 연산이 가능합니다. 코사인 유사도, 유클리드 거리 등 다양한 거리 측정 방법을 지원합니다.",
                "category": ["AI", "Database"]
            },
            {
                "title": "Cross-Encoder Reranking",
                "text": "Cross-encoder models use BERT-like architectures to score query-document pairs directly. Unlike bi-encoders that create separate embeddings, cross-encoders process both inputs together for more accurate relevance scoring. This approach is commonly used for reranking search results.",
                "category": ["AI", "NLP"]
            },
            {
                "title": "하이브리드 검색 시스템",
                "text": "하이브리드 검색은 키워드 기반 검색(BM25)과 의미 기반 검색(벡터 유사도)을 결합합니다. 각 방법의 장점을 활용하여 더 정확한 검색 결과를 제공할 수 있습니다. 가중치 조정과 재랭킹 과정을 통해 최종 결과를 도출합니다.",
                "category": ["AI", "Search"]
            }
        ]

        # 테스트 쿼리
        self.test_queries = [
            "RAG 시스템 설명",
            "machine learning algorithms",
            "벡터 검색 방법",
            "What is retrieval augmented generation?",
            "인공지능 분류 기법",
            "neural network architecture",
            "데이터베이스 최적화",
            "embedding model comparison"
        ]

    async def setup_test_data(self) -> bool:
        """테스트 데이터 설정"""
        logger.info("SQLite 테스트 데이터 설정 시작")
        return await self.search_dao.insert_test_data(self.test_documents)

    async def test_bm25_component(self) -> Dict[str, Any]:
        """BM25 컴포넌트 개별 테스트"""
        logger.info("BM25 컴포넌트 테스트 시작")

        results = {"success": False, "test_cases": [], "performance": {}}

        try:
            start_time = time.time()

            for query in self.test_queries[:4]:  # 처음 4개 쿼리로 테스트
                search_start = time.time()
                bm25_results = await self.search_dao.bm25_search(query, topk=5)
                search_time = time.time() - search_start

                test_case = {
                    "query": query,
                    "result_count": len(bm25_results),
                    "search_time": search_time,
                    "has_results": len(bm25_results) > 0,
                    "top_score": bm25_results[0]["score"] if bm25_results else 0,
                    "performance_acceptable": search_time < 1.0
                }

                # 결과 품질 검증
                if bm25_results:
                    # 스코어가 내림차순인지 확인
                    scores = [r["score"] for r in bm25_results]
                    test_case["scores_descending"] = all(
                        scores[i] >= scores[i+1] for i in range(len(scores)-1)
                    )
                    # 모든 결과가 필수 필드를 가지는지 확인
                    test_case["results_valid"] = all(
                        "chunk_id" in r and "text" in r and "score" in r
                        for r in bm25_results
                    )
                else:
                    test_case["scores_descending"] = True
                    test_case["results_valid"] = True

                results["test_cases"].append(test_case)

            # 성능 메트릭
            total_time = time.time() - start_time
            results["performance"] = {
                "total_time": total_time,
                "avg_search_time": total_time / len(results["test_cases"]),
                "searches_per_second": len(results["test_cases"]) / total_time
            }

            # 성공 여부 판단
            successful_tests = sum(
                1 for test in results["test_cases"]
                if test["has_results"] and test["scores_descending"] and test["results_valid"]
            )
            results["success"] = successful_tests >= len(results["test_cases"]) * 0.75

        except Exception as e:
            logger.error(f"BM25 테스트 실패: {e}")
            results["error"] = str(e)

        self.test_results["bm25_component"] = results
        logger.info(f"BM25 컴포넌트 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_vector_component(self) -> Dict[str, Any]:
        """벡터 검색 컴포넌트 개별 테스트"""
        logger.info("벡터 검색 컴포넌트 테스트 시작")

        results = {"success": False, "test_cases": [], "performance": {}}

        try:
            start_time = time.time()

            for query in self.test_queries[:4]:
                search_start = time.time()
                vector_results = await self.search_dao.vector_search(query, topk=5)
                search_time = time.time() - search_start

                test_case = {
                    "query": query,
                    "result_count": len(vector_results),
                    "search_time": search_time,
                    "has_results": len(vector_results) > 0,
                    "top_score": vector_results[0]["score"] if vector_results else 0,
                    "performance_acceptable": search_time < 2.0
                }

                # 유사도 점수 검증 (0~1 범위)
                if vector_results:
                    scores = [r["score"] for r in vector_results]
                    test_case["scores_valid"] = all(0 <= score <= 1 for score in scores)
                    test_case["scores_descending"] = all(
                        scores[i] >= scores[i+1] for i in range(len(scores)-1)
                    )
                    test_case["results_valid"] = all(
                        "chunk_id" in r and "text" in r and "score" in r
                        for r in vector_results
                    )
                else:
                    test_case["scores_valid"] = True
                    test_case["scores_descending"] = True
                    test_case["results_valid"] = True

                results["test_cases"].append(test_case)

            # 성능 메트릭
            total_time = time.time() - start_time
            results["performance"] = {
                "total_time": total_time,
                "avg_search_time": total_time / len(results["test_cases"]),
                "searches_per_second": len(results["test_cases"]) / total_time
            }

            # 성공 여부 판단
            successful_tests = sum(
                1 for test in results["test_cases"]
                if test["has_results"] and test["scores_valid"] and
                   test["scores_descending"] and test["results_valid"]
            )
            results["success"] = successful_tests >= len(results["test_cases"]) * 0.75

        except Exception as e:
            logger.error(f"벡터 검색 테스트 실패: {e}")
            results["error"] = str(e)

        self.test_results["vector_component"] = results
        logger.info(f"벡터 검색 컴포넌트 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_hybrid_integration(self) -> Dict[str, Any]:
        """하이브리드 검색 통합 테스트"""
        logger.info("하이브리드 검색 통합 테스트 시작")

        results = {"success": False, "test_cases": [], "performance": {}}

        try:
            start_time = time.time()

            for query in self.test_queries:
                search_start = time.time()
                hybrid_results = await self.search_dao.hybrid_search(
                    query, topk=5, bm25_topk=10, vector_topk=10
                )
                search_time = time.time() - search_start

                test_case = {
                    "query": query,
                    "result_count": len(hybrid_results),
                    "search_time": search_time,
                    "has_results": len(hybrid_results) > 0,
                    "performance_acceptable": search_time < 3.0,
                    "source_diversity": {}
                }

                # 결과 품질 분석
                if hybrid_results:
                    # 소스 다양성 (BM25, Vector, Hybrid)
                    sources = [r["metadata"]["source"] for r in hybrid_results]
                    test_case["source_diversity"] = {
                        source: sources.count(source) for source in set(sources)
                    }

                    # 스코어 검증
                    scores = [r["score"] for r in hybrid_results]
                    test_case["scores_descending"] = all(
                        scores[i] >= scores[i+1] for i in range(len(scores)-1)
                    )

                    # 메타데이터 완성도
                    test_case["metadata_complete"] = all(
                        "bm25_score" in r["metadata"] and
                        "vector_score" in r["metadata"] and
                        "source" in r["metadata"]
                        for r in hybrid_results
                    )

                    # 하이브리드 스코어가 존재하는지 (hybrid 소스인 경우)
                    hybrid_results_exist = any(
                        r["metadata"]["source"] == "hybrid" for r in hybrid_results
                    )
                    test_case["hybrid_scoring_works"] = hybrid_results_exist

                else:
                    test_case["scores_descending"] = True
                    test_case["metadata_complete"] = True
                    test_case["hybrid_scoring_works"] = False

                results["test_cases"].append(test_case)

            # 성능 메트릭
            total_time = time.time() - start_time
            search_times = [test["search_time"] for test in results["test_cases"]]

            results["performance"] = {
                "total_time": total_time,
                "avg_search_time": sum(search_times) / len(search_times),
                "p95_search_time": sorted(search_times)[int(len(search_times) * 0.95)],
                "searches_per_second": len(results["test_cases"]) / total_time,
                "latency_target_met": all(t < 3.0 for t in search_times)
            }

            # 성공 여부 판단
            successful_tests = sum(
                1 for test in results["test_cases"]
                if test["has_results"] and test["scores_descending"] and
                   test["metadata_complete"] and test["performance_acceptable"]
            )
            results["success"] = successful_tests >= len(results["test_cases"]) * 0.8

        except Exception as e:
            logger.error(f"하이브리드 통합 테스트 실패: {e}")
            results["error"] = str(e)

        self.test_results["hybrid_integration"] = results
        logger.info(f"하이브리드 통합 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 테스트"""
        logger.info("성능 메트릭 테스트 시작")

        results = {"success": False, "metrics": {}, "benchmarks": {}}

        try:
            # 벤치마크 쿼리들
            benchmark_queries = [
                "단순 키워드",
                "complex machine learning algorithm optimization",
                "한국어와 영어가 혼재된 복합 쿼리 multilingual",
                "매우 긴 쿼리문으로 시스템의 처리 능력을 테스트하는 케이스입니다 very long query to test system processing capabilities"
            ]

            # 각 검색 타입별 성능 측정
            for search_type in ["bm25", "vector", "hybrid"]:
                search_times = []

                for query in benchmark_queries:
                    start_time = time.time()

                    if search_type == "bm25":
                        await self.search_dao.bm25_search(query, topk=10)
                    elif search_type == "vector":
                        await self.search_dao.vector_search(query, topk=10)
                    else:  # hybrid
                        await self.search_dao.hybrid_search(query, topk=5)

                    search_times.append(time.time() - start_time)

                results["benchmarks"][search_type] = {
                    "avg_latency": sum(search_times) / len(search_times),
                    "min_latency": min(search_times),
                    "max_latency": max(search_times),
                    "p95_latency": sorted(search_times)[int(len(search_times) * 0.95)],
                    "throughput": len(search_times) / sum(search_times)
                }

            # 데이터베이스 통계
            db_stats = self.search_dao.get_stats()
            results["metrics"]["database"] = db_stats

            # 성능 목표 달성 여부
            targets = {
                "bm25_avg_latency": 0.5,  # 500ms
                "vector_avg_latency": 1.0,  # 1s
                "hybrid_avg_latency": 2.0,  # 2s
                "hybrid_p95_latency": 3.0   # 3s
            }

            results["metrics"]["target_achievement"] = {
                "bm25_target_met": results["benchmarks"]["bm25"]["avg_latency"] < targets["bm25_avg_latency"],
                "vector_target_met": results["benchmarks"]["vector"]["avg_latency"] < targets["vector_avg_latency"],
                "hybrid_avg_target_met": results["benchmarks"]["hybrid"]["avg_latency"] < targets["hybrid_avg_latency"],
                "hybrid_p95_target_met": results["benchmarks"]["hybrid"]["p95_latency"] < targets["hybrid_p95_latency"]
            }

            # 전체 성공 여부
            targets_met = sum(results["metrics"]["target_achievement"].values())
            results["success"] = targets_met >= 3  # 4개 중 3개 이상 달성

        except Exception as e:
            logger.error(f"성능 메트릭 테스트 실패: {e}")
            results["error"] = str(e)

        self.test_results["performance_metrics"] = results
        logger.info(f"성능 메트릭 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_encoding_compatibility(self) -> Dict[str, Any]:
        """UTF-8 인코딩 호환성 테스트"""
        logger.info("UTF-8 인코딩 호환성 테스트 시작")

        results = {"success": False, "test_cases": [], "character_tests": {}}

        try:
            # 다국어 테스트 케이스
            multilingual_queries = [
                "한글 검색 테스트",
                "English search test",
                "日本語検索テスト",
                "Русский поиск тест",
                "Búsqueda en español",
                "Recherche française",
                "한글과 English 혼합 query",
                "특수문자 @#$%^&*() 포함",
                "이모지 😀🚀🔍 포함 검색"
            ]

            for query in multilingual_queries:
                test_case = {
                    "query": query,
                    "encoding": "utf-8",
                    "tests": {}
                }

                try:
                    # BM25 토큰화 테스트
                    tokens = BM25Scorer.preprocess_text(query)
                    test_case["tests"]["tokenization"] = {
                        "success": True,
                        "token_count": len(tokens),
                        "sample_tokens": tokens[:3]
                    }
                except Exception as e:
                    test_case["tests"]["tokenization"] = {
                        "success": False,
                        "error": str(e)
                    }

                try:
                    # 임베딩 생성 테스트
                    embedding = await EmbeddingService.generate_embedding(query)
                    test_case["tests"]["embedding"] = {
                        "success": len(embedding) > 0,
                        "embedding_length": len(embedding)
                    }
                except Exception as e:
                    test_case["tests"]["embedding"] = {
                        "success": False,
                        "error": str(e)
                    }

                try:
                    # 실제 검색 테스트
                    search_results = await self.search_dao.hybrid_search(query, topk=3)
                    test_case["tests"]["search"] = {
                        "success": True,
                        "result_count": len(search_results)
                    }
                except Exception as e:
                    test_case["tests"]["search"] = {
                        "success": False,
                        "error": str(e)
                    }

                # 전체 성공 여부
                test_case["overall_success"] = all(
                    test.get("success", False)
                    for test in test_case["tests"].values()
                )

                results["test_cases"].append(test_case)

            # 특수 문자 처리 테스트
            special_chars = {
                "punctuation": ",.!?;:\"'",
                "math_symbols": "∑∫∆∇∞±",
                "currency": "$€¥₩",
                "emoji": "😀🚀🔍💡",
                "cjk": "中文 日本語 한글"
            }

            for category, chars in special_chars.items():
                try:
                    test_query = f"Test {category}: {chars}"
                    tokens = BM25Scorer.preprocess_text(test_query)
                    results["character_tests"][category] = {
                        "success": True,
                        "processed_tokens": len(tokens)
                    }
                except Exception as e:
                    results["character_tests"][category] = {
                        "success": False,
                        "error": str(e)
                    }

            # 전체 성공률 계산
            successful_cases = sum(1 for case in results["test_cases"] if case["overall_success"])
            successful_chars = sum(1 for test in results["character_tests"].values() if test["success"])

            case_success_rate = successful_cases / len(results["test_cases"])
            char_success_rate = successful_chars / len(results["character_tests"])

            results["success"] = case_success_rate >= 0.8 and char_success_rate >= 0.8

        except Exception as e:
            logger.error(f"인코딩 호환성 테스트 실패: {e}")
            results["error"] = str(e)

        self.test_results["encoding_compatibility"] = results
        logger.info(f"인코딩 호환성 테스트 완료 - 성공: {results['success']}")
        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("=== SQLite 하이브리드 검색 테스트 시작 ===")

        overall_start = time.time()

        # 테스트 데이터 설정
        setup_success = await self.setup_test_data()
        if not setup_success:
            logger.error("테스트 데이터 설정 실패")
            return {"error": "테스트 데이터 설정 실패"}

        # 개별 테스트 실행
        test_functions = [
            ("BM25 컴포넌트", self.test_bm25_component),
            ("벡터 검색 컴포넌트", self.test_vector_component),
            ("하이브리드 통합", self.test_hybrid_integration),
            ("성능 메트릭", self.test_performance_metrics),
            ("인코딩 호환성", self.test_encoding_compatibility)
        ]

        for test_name, test_func in test_functions:
            logger.info(f"{test_name} 테스트 실행 중...")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"{test_name} 테스트 중 예외 발생: {e}")
                logger.error(traceback.format_exc())

        # 전체 결과 생성
        total_time = time.time() - overall_start

        # 성공률 계산
        success_counts = {}
        for test_category, test_result in self.test_results.items():
            success_counts[test_category] = test_result.get("success", False)

        overall_success_rate = sum(success_counts.values()) / len(success_counts) if success_counts else 0

        # 데이터베이스 통계
        db_stats = self.search_dao.get_stats()

        final_results = {
            "test_summary": {
                "total_time": total_time,
                "setup_success": setup_success,
                "tests_completed": len(test_functions),
                "overall_success_rate": overall_success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "database_stats": db_stats,
            "individual_results": self.test_results,
            "success_summary": success_counts,
            "recommendations": self._generate_recommendations(success_counts)
        }

        # 결과 로깅
        logger.info("=== 테스트 결과 요약 ===")
        logger.info(f"전체 성공률: {overall_success_rate:.1%}")
        logger.info(f"전체 실행 시간: {total_time:.2f}초")
        logger.info(f"데이터베이스 통계: {db_stats}")

        return final_results

    def _generate_recommendations(self, success_counts: Dict[str, bool]) -> List[str]:
        """테스트 결과 기반 권장사항 생성"""
        recommendations = []

        if not success_counts.get("bm25_component", False):
            recommendations.append("BM25 컴포넌트 개선: 토큰화 로직과 스코어링 알고리즘을 최적화하세요.")

        if not success_counts.get("vector_component", False):
            recommendations.append("벡터 검색 개선: 임베딩 생성과 유사도 계산 로직을 점검하세요.")

        if not success_counts.get("hybrid_integration", False):
            recommendations.append("하이브리드 통합 개선: BM25와 벡터 검색의 가중치 조정을 최적화하세요.")

        if not success_counts.get("performance_metrics", False):
            recommendations.append("성능 최적화: 검색 지연시간을 줄이기 위해 인덱싱과 캐싱을 개선하세요.")

        if not success_counts.get("encoding_compatibility", False):
            recommendations.append("인코딩 호환성 개선: 다국어 텍스트 처리 로직을 강화하세요.")

        if not recommendations:
            recommendations.append("모든 테스트가 성공했습니다! 시스템이 올바르게 구현되었습니다.")

        return recommendations

    def save_results(self, results: Dict[str, Any], filename: str = "sqlite_hybrid_search_results.json"):
        """테스트 결과 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")

async def main():
    """메인 테스트 실행 함수"""
    print("SQLite 하이브리드 검색 시스템 테스트 시작")
    print("=" * 60)

    tester = HybridSearchSQLiteTester()

    try:
        # 모든 테스트 실행
        results = await tester.run_all_tests()

        # 결과 저장
        tester.save_results(results)

        # 요약 출력
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print(f"전체 성공률: {results['test_summary']['overall_success_rate']:.1%}")
        print(f"총 실행시간: {results['test_summary']['total_time']:.2f}초")

        if results.get('recommendations'):
            print("\n권장사항:")
            for rec in results['recommendations']:
                print(f"  - {rec}")

        print(f"\n상세 결과: sqlite_hybrid_search_results.json")
        print("=" * 60)

        return results['test_summary']['overall_success_rate'] >= 0.7

    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # 비동기 실행
    import platform
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    success = asyncio.run(main())
    sys.exit(0 if success else 1)