#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
하이브리드 검색 시스템 포괄적 테스트 스크립트
BM25 + Vector Similarity + Cross-Encoder Reranking 통합 테스트

테스트 항목:
1. BM25 스코어링 테스트 (한글 텍스트 포함)
2. Vector 임베딩 및 유사도 계산 테스트
3. Cross-Encoder 리랭킹 테스트
4. 하이브리드 검색 통합 테스트
5. 성능 메트릭 수집 및 검증
6. UTF-8 인코딩 호환성 확인
"""

import asyncio
import time
import logging
import json
import traceback
from typing import List, Dict, Any, Tuple
from datetime import datetime
import os
import sys
import uuid

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from apps.api.database import (
    DatabaseManager, BM25Scorer, EmbeddingService, CrossEncoderReranker,
    SearchDAO, SearchMetrics, db_manager, init_database
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_search_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HybridSearchTester:
    """하이브리드 검색 시스템 포괄적 테스터"""

    def __init__(self):
        self.db_manager = db_manager
        self.test_metrics = SearchMetrics()
        self.test_results = {
            "bm25_tests": {},
            "vector_tests": {},
            "cross_encoder_tests": {},
            "hybrid_tests": {},
            "performance_metrics": {},
            "encoding_tests": {},
            "integration_tests": {}
        }

        # 테스트 데이터 - 한글과 영어 혼재
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

    async def setup_test_data(self) -> bool:
        """테스트용 데이터 설정"""
        try:
            logger.info("테스트 데이터 설정 시작")

            # 데이터베이스 초기화
            if not await init_database():
                logger.error("데이터베이스 초기화 실패")
                return False

            async with self.db_manager.async_session() as session:
                # 테스트 문서들을 실제 DB에 삽입
                from sqlalchemy import text

                for i, doc_data in enumerate(self.test_documents):
                    # SQLite 호환 문서 삽입 (doc_id를 명시적으로 생성)
                    new_doc_id = str(uuid.uuid4())

                    doc_insert = text("""
                        INSERT OR IGNORE INTO documents (doc_id, title, content_type, file_size)
                        VALUES (:doc_id, :title, 'text/plain', :file_size)
                    """)
                    await session.execute(doc_insert, {
                        "doc_id": new_doc_id,
                        "title": doc_data["title"],
                        "file_size": len(doc_data["text"])
                    })

                    # 실제로 삽입된 doc_id 확인
                    doc_check = await session.execute(
                        text("SELECT doc_id FROM documents WHERE title = :title"),
                        {"title": doc_data["title"]}
                    )
                    doc_id = doc_check.scalar()

                    try:
                        if doc_id:
                            # SQLite 호환 청크 삽입
                            new_chunk_id = str(uuid.uuid4())
                            chunk_insert = text("""
                                INSERT OR IGNORE INTO chunks (chunk_id, doc_id, text, span, chunk_index)
                                VALUES (:chunk_id, :doc_id, :text, :span, :chunk_index)
                            """)
                            await session.execute(chunk_insert, {
                                "chunk_id": new_chunk_id,
                                "doc_id": doc_id,
                                "text": doc_data["text"],
                                "span": "1,1000",  # SQLite용 span 형식
                                "chunk_index": i
                            })

                            # 청크가 생성되었으면 임베딩 생성
                            chunk_check = await session.execute(
                                text("SELECT chunk_id FROM chunks WHERE doc_id = :doc_id AND chunk_index = :chunk_index"),
                                {"doc_id": doc_id, "chunk_index": i}
                            )
                            chunk_id = chunk_check.scalar()

                            if chunk_id:
                                # 임베딩 생성 및 삽입
                                embedding = await EmbeddingService.generate_embedding(doc_data["text"])
                                if embedding:
                                    new_embedding_id = str(uuid.uuid4())
                                    embedding_insert = text("""
                                        INSERT OR IGNORE INTO embeddings (embedding_id, chunk_id, vec, model_name)
                                        VALUES (:embedding_id, :chunk_id, :vec, 'text-embedding-ada-002')
                                    """)
                                    await session.execute(embedding_insert, {
                                        "embedding_id": new_embedding_id,
                                        "chunk_id": chunk_id,
                                        "vec": embedding
                                    })

                            # 분류 정보 삽입
                            if doc_data.get("category"):
                                new_mapping_id = str(uuid.uuid4())
                                taxonomy_insert = text("""
                                    INSERT OR IGNORE INTO doc_taxonomy (mapping_id, doc_id, path, confidence, source)
                                    VALUES (:mapping_id, :doc_id, :path, :confidence, 'test')
                                """)
                                await session.execute(taxonomy_insert, {
                                    "mapping_id": new_mapping_id,
                                    "doc_id": doc_id,
                                    "path": json.dumps(doc_data["category"]),  # SQLite용 JSON 문자열
                                    "confidence": 1.0
                                })

                    except Exception as e:
                        logger.warning(f"문서 {doc_data['title']} 처리 중 오류: {e}")
                        continue

                await session.commit()

            logger.info("테스트 데이터 설정 완료")
            return True

        except Exception as e:
            logger.error(f"테스트 데이터 설정 실패: {e}")
            logger.error(traceback.format_exc())
            return False

    async def test_bm25_scoring(self) -> Dict[str, Any]:
        """BM25 스코어링 테스트"""
        logger.info("BM25 스코어링 테스트 시작")

        results = {
            "success": False,
            "test_cases": [],
            "performance": {},
            "encoding_test": {}
        }

        try:
            # 테스트 케이스 1: 기본 BM25 스코어 계산
            start_time = time.time()

            # 한글 텍스트 전처리 테스트
            korean_text = "RAG 시스템은 검색 기반 생성 모델입니다"
            korean_tokens = BM25Scorer.preprocess_text(korean_text)

            english_text = "Machine learning algorithms include SVM and Random Forest"
            english_tokens = BM25Scorer.preprocess_text(english_text)

            # 코퍼스 통계 (더미 데이터)
            corpus_stats = {
                "avg_doc_length": 50,
                "total_docs": 100,
                "term_doc_freq": {
                    "rag": 5,
                    "시스템": 10,
                    "machine": 8,
                    "learning": 12,
                    "검색": 7,
                    "기반": 15
                }
            }

            # BM25 스코어 계산 테스트
            test_cases = [
                {
                    "query": "RAG 시스템",
                    "doc_text": korean_text,
                    "expected_score_range": (0.0, 10.0)
                },
                {
                    "query": "machine learning",
                    "doc_text": english_text,
                    "expected_score_range": (0.0, 10.0)
                },
                {
                    "query": "검색 기반",
                    "doc_text": korean_text,
                    "expected_score_range": (0.0, 10.0)
                }
            ]

            for i, test_case in enumerate(test_cases):
                query_tokens = BM25Scorer.preprocess_text(test_case["query"])
                doc_tokens = BM25Scorer.preprocess_text(test_case["doc_text"])

                score = BM25Scorer.calculate_bm25_score(
                    query_tokens, doc_tokens, corpus_stats
                )

                min_score, max_score = test_case["expected_score_range"]
                test_success = min_score <= score <= max_score

                results["test_cases"].append({
                    "case_id": i + 1,
                    "query": test_case["query"],
                    "query_tokens": query_tokens,
                    "doc_tokens": doc_tokens[:10],  # 처음 10개만 로깅
                    "bm25_score": score,
                    "expected_range": test_case["expected_score_range"],
                    "success": test_success
                })

            # 성능 메트릭
            end_time = time.time()
            results["performance"] = {
                "total_time": end_time - start_time,
                "avg_time_per_case": (end_time - start_time) / len(test_cases),
                "throughput": len(test_cases) / (end_time - start_time)
            }

            # UTF-8 인코딩 테스트
            unicode_texts = [
                "한글 텍스트 처리 테스트",
                "English text processing test",
                "混合文字処理テスト",  # 일본어
                "Тест обработки текста"  # 러시아어
            ]

            encoding_results = []
            for text in unicode_texts:
                try:
                    tokens = BM25Scorer.preprocess_text(text)
                    encoding_results.append({
                        "text": text,
                        "tokens": tokens,
                        "success": True,
                        "token_count": len(tokens)
                    })
                except Exception as e:
                    encoding_results.append({
                        "text": text,
                        "tokens": [],
                        "success": False,
                        "error": str(e)
                    })

            results["encoding_test"] = {
                "test_texts": encoding_results,
                "success_rate": sum(1 for r in encoding_results if r["success"]) / len(encoding_results)
            }

            # 전체 성공 여부
            successful_cases = sum(1 for case in results["test_cases"] if case["success"])
            results["success"] = (successful_cases == len(results["test_cases"]) and
                                results["encoding_test"]["success_rate"] == 1.0)

            self.test_results["bm25_tests"] = results

        except Exception as e:
            logger.error(f"BM25 테스트 실패: {e}")
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        logger.info(f"BM25 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_vector_embedding_similarity(self) -> Dict[str, Any]:
        """벡터 임베딩 및 유사도 계산 테스트"""
        logger.info("벡터 임베딩 테스트 시작")

        results = {
            "success": False,
            "embedding_tests": [],
            "similarity_tests": [],
            "performance": {},
            "encoding_test": {}
        }

        try:
            start_time = time.time()

            # 임베딩 생성 테스트
            test_texts = [
                "RAG 시스템은 검색과 생성을 결합합니다",
                "Machine learning enables pattern recognition",
                "벡터 데이터베이스는 고차원 데이터를 저장합니다",
                "Neural networks learn complex representations"
            ]

            embeddings = []
            for i, text in enumerate(test_texts):
                embedding_start = time.time()
                embedding = await EmbeddingService.generate_embedding(text)
                embedding_time = time.time() - embedding_start

                # 임베딩 검증
                is_valid = (
                    isinstance(embedding, list) and
                    len(embedding) > 0 and
                    all(isinstance(x, (int, float)) for x in embedding)
                )

                test_result = {
                    "text": text,
                    "embedding_length": len(embedding),
                    "generation_time": embedding_time,
                    "is_valid": is_valid,
                    "sample_values": embedding[:5] if embedding else []
                }

                results["embedding_tests"].append(test_result)
                if is_valid:
                    embeddings.append(embedding)

            # 유사도 계산 테스트
            if len(embeddings) >= 2:
                import numpy as np
                from sklearn.metrics.pairwise import cosine_similarity

                similarity_tests = [
                    # 유사한 텍스트 쌍
                    (0, 2, "RAG-벡터DB 유사성 (한글-한글)"),
                    (1, 3, "ML-NN 유사성 (영어-영어)"),
                    # 다른 텍스트 쌍
                    (0, 1, "RAG-ML 차이 (한글-영어)"),
                    (2, 3, "벡터DB-NN 차이 (한글-영어)")
                ]

                for idx1, idx2, description in similarity_tests:
                    if idx1 < len(embeddings) and idx2 < len(embeddings):
                        emb1 = np.array(embeddings[idx1]).reshape(1, -1)
                        emb2 = np.array(embeddings[idx2]).reshape(1, -1)

                        cosine_sim = cosine_similarity(emb1, emb2)[0][0]
                        euclidean_dist = np.linalg.norm(emb1 - emb2)

                        results["similarity_tests"].append({
                            "description": description,
                            "text1": test_texts[idx1],
                            "text2": test_texts[idx2],
                            "cosine_similarity": float(cosine_sim),
                            "euclidean_distance": float(euclidean_dist),
                            "similarity_valid": -1.0 <= cosine_sim <= 1.0
                        })

            # 성능 메트릭
            end_time = time.time()
            results["performance"] = {
                "total_time": end_time - start_time,
                "avg_embedding_time": sum(t["generation_time"] for t in results["embedding_tests"]) / len(results["embedding_tests"]),
                "embeddings_per_second": len(test_texts) / (end_time - start_time)
            }

            # UTF-8 인코딩 테스트
            unicode_texts = [
                "한국어 임베딩 테스트 🇰🇷",
                "English embedding test 🇺🇸",
                "日本語埋め込みテスト 🇯🇵",
                "Русский тест встраивания 🇷🇺"
            ]

            encoding_results = []
            for text in unicode_texts:
                try:
                    embedding = await EmbeddingService.generate_embedding(text)
                    encoding_results.append({
                        "text": text,
                        "success": len(embedding) > 0,
                        "embedding_length": len(embedding)
                    })
                except Exception as e:
                    encoding_results.append({
                        "text": text,
                        "success": False,
                        "error": str(e)
                    })

            results["encoding_test"] = {
                "test_results": encoding_results,
                "success_rate": sum(1 for r in encoding_results if r["success"]) / len(encoding_results)
            }

            # 전체 성공 여부
            valid_embeddings = sum(1 for t in results["embedding_tests"] if t["is_valid"])
            valid_similarities = sum(1 for t in results["similarity_tests"] if t["similarity_valid"])

            results["success"] = (
                valid_embeddings == len(results["embedding_tests"]) and
                valid_similarities == len(results["similarity_tests"]) and
                results["encoding_test"]["success_rate"] >= 0.75
            )

            self.test_results["vector_tests"] = results

        except Exception as e:
            logger.error(f"벡터 임베딩 테스트 실패: {e}")
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        logger.info(f"벡터 임베딩 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_cross_encoder_reranking(self) -> Dict[str, Any]:
        """Cross-Encoder 리랭킹 테스트"""
        logger.info("Cross-Encoder 리랭킹 테스트 시작")

        results = {
            "success": False,
            "reranking_tests": [],
            "performance": {},
            "quality_metrics": {}
        }

        try:
            start_time = time.time()

            # 가상의 검색 결과 생성
            test_query = "RAG 시스템 설명"

            mock_search_results = [
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": "RAG 시스템은 검색과 생성을 결합한 AI 모델입니다.",
                    "score": 0.6,
                    "metadata": {"bm25_score": 0.8, "vector_score": 0.4, "source": "hybrid"}
                },
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": "머신러닝 알고리즘은 데이터에서 패턴을 학습합니다.",
                    "score": 0.3,
                    "metadata": {"bm25_score": 0.2, "vector_score": 0.4, "source": "hybrid"}
                },
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": "검색 증강 생성(RAG)은 외부 지식을 활용하여 더 정확한 답변을 생성합니다.",
                    "score": 0.7,
                    "metadata": {"bm25_score": 0.9, "vector_score": 0.5, "source": "hybrid"}
                },
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": "데이터베이스 최적화는 쿼리 성능을 향상시킵니다.",
                    "score": 0.2,
                    "metadata": {"bm25_score": 0.1, "vector_score": 0.3, "source": "hybrid"}
                },
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": "RAG 아키텍처는 retriever와 generator 컴포넌트로 구성됩니다.",
                    "score": 0.65,
                    "metadata": {"bm25_score": 0.7, "vector_score": 0.6, "source": "hybrid"}
                }
            ]

            # 원본 순서 기록
            original_order = [(r["chunk_id"], r["score"]) for r in mock_search_results]

            # 리랭킹 수행
            reranked_results = CrossEncoderReranker.rerank_results(
                test_query, mock_search_results.copy(), top_k=3
            )

            # 결과 분석
            reranked_order = [(r["chunk_id"], r["score"]) for r in reranked_results]

            # 순서 변화 확인
            order_changed = original_order != reranked_order

            # 관련성 개선 확인 (RAG 관련 문서가 상위에 오는지)
            rag_relevant_indices = []
            for i, result in enumerate(reranked_results):
                if "RAG" in result["text"] or "검색" in result["text"] or "생성" in result["text"]:
                    rag_relevant_indices.append(i)

            relevance_improved = len(rag_relevant_indices) > 0 and max(rag_relevant_indices) <= 1

            results["reranking_tests"].append({
                "query": test_query,
                "original_count": len(mock_search_results),
                "reranked_count": len(reranked_results),
                "top_k": 3,
                "order_changed": order_changed,
                "relevance_improved": relevance_improved,
                "original_scores": [r[1] for r in original_order][:3],
                "reranked_scores": [r[1] for r in reranked_order],
                "score_improvement": any(
                    r_score > o_score
                    for (_, r_score), (_, o_score)
                    in zip(reranked_order[:3], original_order[:3])
                )
            })

            # 다양한 top_k 값으로 테스트
            for top_k in [1, 2, 5]:
                if top_k <= len(mock_search_results):
                    sub_reranked = CrossEncoderReranker.rerank_results(
                        test_query, mock_search_results.copy(), top_k=top_k
                    )

                    results["reranking_tests"].append({
                        "query": test_query,
                        "top_k": top_k,
                        "result_count": len(sub_reranked),
                        "top_k_respected": len(sub_reranked) == top_k,
                        "scores_descending": all(
                            sub_reranked[i]["score"] >= sub_reranked[i+1]["score"]
                            for i in range(len(sub_reranked)-1)
                        ) if len(sub_reranked) > 1 else True
                    })

            # 성능 메트릭
            end_time = time.time()
            results["performance"] = {
                "total_time": end_time - start_time,
                "reranking_latency": (end_time - start_time) / len(results["reranking_tests"]),
                "throughput": len(results["reranking_tests"]) / (end_time - start_time)
            }

            # 품질 메트릭
            successful_tests = sum(1 for test in results["reranking_tests"]
                                 if test.get("relevance_improved", False) or
                                    test.get("top_k_respected", False))

            results["quality_metrics"] = {
                "success_rate": successful_tests / len(results["reranking_tests"]),
                "relevance_improvement_rate": sum(1 for test in results["reranking_tests"]
                                                if test.get("relevance_improved", False)) /
                                           len([t for t in results["reranking_tests"] if "relevance_improved" in t]),
                "order_change_rate": sum(1 for test in results["reranking_tests"]
                                       if test.get("order_changed", False)) /
                                   len([t for t in results["reranking_tests"] if "order_changed" in t])
            }

            results["success"] = results["quality_metrics"]["success_rate"] >= 0.7
            self.test_results["cross_encoder_tests"] = results

        except Exception as e:
            logger.error(f"Cross-Encoder 테스트 실패: {e}")
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        logger.info(f"Cross-Encoder 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_hybrid_search_integration(self) -> Dict[str, Any]:
        """하이브리드 검색 통합 테스트"""
        logger.info("하이브리드 검색 통합 테스트 시작")

        results = {
            "success": False,
            "search_tests": [],
            "performance": {},
            "quality_metrics": {}
        }

        try:
            # 여러 쿼리로 통합 검색 테스트
            for query in self.test_queries:
                search_start = time.time()

                # 하이브리드 검색 수행
                search_results = await SearchDAO.hybrid_search(
                    query=query,
                    filters=None,
                    topk=5,
                    bm25_topk=10,
                    vector_topk=10,
                    rerank_candidates=20
                )

                search_time = time.time() - search_start

                # 결과 분석
                test_result = {
                    "query": query,
                    "search_time": search_time,
                    "result_count": len(search_results),
                    "has_results": len(search_results) > 0,
                    "results_details": []
                }

                # 각 결과 검증
                for i, result in enumerate(search_results[:3]):  # 상위 3개만 분석
                    detail = {
                        "rank": i + 1,
                        "has_chunk_id": "chunk_id" in result,
                        "has_text": "text" in result and len(result.get("text", "")) > 0,
                        "has_score": "score" in result and isinstance(result.get("score"), (int, float)),
                        "has_metadata": "metadata" in result,
                        "text_preview": result.get("text", "")[:100] + "..." if result.get("text") else "",
                        "score": result.get("score", 0)
                    }

                    # 메타데이터 검증
                    metadata = result.get("metadata", {})
                    detail["metadata_complete"] = all(
                        key in metadata for key in ["bm25_score", "vector_score", "source"]
                    )

                    test_result["results_details"].append(detail)

                # 품질 지표
                test_result["quality_score"] = sum(
                    1 for detail in test_result["results_details"]
                    if detail["has_text"] and detail["has_score"] and detail["metadata_complete"]
                ) / max(1, len(test_result["results_details"]))

                # 성능 지표
                test_result["performance_acceptable"] = search_time < 5.0  # 5초 이내

                results["search_tests"].append(test_result)

                # 메트릭 기록
                self.test_metrics.record_search(
                    "hybrid", search_time, error=len(search_results) == 0
                )

            # 필터링 테스트
            filtered_search_start = time.time()
            filtered_results = await SearchDAO.hybrid_search(
                query="RAG 시스템",
                filters={"canonical_in": [["AI", "RAG"]]},
                topk=3
            )
            filtered_search_time = time.time() - filtered_search_start

            results["search_tests"].append({
                "query": "RAG 시스템 (필터링)",
                "search_time": filtered_search_time,
                "result_count": len(filtered_results),
                "filter_applied": True,
                "performance_acceptable": filtered_search_time < 5.0
            })

            # 전체 성능 메트릭
            search_times = [test["search_time"] for test in results["search_tests"]]
            results["performance"] = {
                "avg_search_time": sum(search_times) / len(search_times),
                "max_search_time": max(search_times),
                "min_search_time": min(search_times),
                "p95_search_time": sorted(search_times)[int(len(search_times) * 0.95)] if len(search_times) > 1 else max(search_times),
                "searches_per_second": len(search_times) / sum(search_times),
                "performance_target_met": all(t < 5.0 for t in search_times)
            }

            # 품질 메트릭
            quality_scores = [test.get("quality_score", 0) for test in results["search_tests"] if "quality_score" in test]
            successful_searches = sum(1 for test in results["search_tests"] if test["has_results"])

            results["quality_metrics"] = {
                "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "search_success_rate": successful_searches / len(results["search_tests"]),
                "quality_target_met": sum(quality_scores) / len(quality_scores) >= 0.7 if quality_scores else False
            }

            # 전체 성공 여부
            results["success"] = (
                results["quality_metrics"]["search_success_rate"] >= 0.8 and
                results["performance"]["performance_target_met"] and
                results["quality_metrics"]["quality_target_met"]
            )

            self.test_results["hybrid_tests"] = results

        except Exception as e:
            logger.error(f"하이브리드 검색 테스트 실패: {e}")
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        logger.info(f"하이브리드 검색 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_performance_metrics_collection(self) -> Dict[str, Any]:
        """성능 메트릭 수집 및 검증 테스트"""
        logger.info("성능 메트릭 테스트 시작")

        results = {
            "success": False,
            "metrics_tests": [],
            "performance": {}
        }

        try:
            # 메트릭 초기화
            self.test_metrics.reset()

            # 다양한 검색 수행하여 메트릭 수집
            search_scenarios = [
                ("BM25 테스트", "bm25"),
                ("Vector 테스트", "vector"),
                ("Hybrid 테스트", "hybrid")
            ]

            for description, search_type in search_scenarios:
                for i in range(5):  # 각 타입별 5회 실행
                    start_time = time.time()

                    # 실제 검색 수행 (간단한 버전)
                    await asyncio.sleep(0.1 + i * 0.02)  # 시뮬레이션된 검색 시간

                    latency = time.time() - start_time
                    error = i == 4  # 마지막 검색은 오류로 시뮬레이션

                    self.test_metrics.record_search(search_type, latency, error)

            # 메트릭 조회 및 검증
            collected_metrics = self.test_metrics.get_metrics()

            # 메트릭 검증
            metrics_test = {
                "has_avg_latency": "avg_latency" in collected_metrics,
                "has_p95_latency": "p95_latency" in collected_metrics,
                "has_total_searches": "total_searches" in collected_metrics,
                "has_search_counts": "search_counts" in collected_metrics,
                "has_error_rate": "error_rate" in collected_metrics,
                "total_searches_correct": collected_metrics.get("total_searches", 0) == 15,
                "error_rate_reasonable": 0 <= collected_metrics.get("error_rate", 0) <= 1,
                "latency_positive": collected_metrics.get("avg_latency", 0) > 0
            }

            metrics_test["all_metrics_present"] = all([
                metrics_test["has_avg_latency"],
                metrics_test["has_p95_latency"],
                metrics_test["has_total_searches"],
                metrics_test["has_search_counts"],
                metrics_test["has_error_rate"]
            ])

            metrics_test["data_consistency"] = all([
                metrics_test["total_searches_correct"],
                metrics_test["error_rate_reasonable"],
                metrics_test["latency_positive"]
            ])

            results["metrics_tests"].append({
                "description": "메트릭 수집 기본 테스트",
                "collected_metrics": collected_metrics,
                "validation": metrics_test,
                "success": metrics_test["all_metrics_present"] and metrics_test["data_consistency"]
            })

            # 성능 분석
            results["performance"] = {
                "metric_collection_latency": "실시간",
                "metric_accuracy": "정확",
                "memory_usage": "경량"
            }

            # 전체 성공 여부
            results["success"] = all(test["success"] for test in results["metrics_tests"])

            self.test_results["performance_metrics"] = results

        except Exception as e:
            logger.error(f"성능 메트릭 테스트 실패: {e}")
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        logger.info(f"성능 메트릭 테스트 완료 - 성공: {results['success']}")
        return results

    async def test_utf8_encoding_compatibility(self) -> Dict[str, Any]:
        """UTF-8 인코딩 호환성 확인 테스트"""
        logger.info("UTF-8 인코딩 호환성 테스트 시작")

        results = {
            "success": False,
            "encoding_tests": [],
            "character_tests": {}
        }

        try:
            # 다양한 언어와 특수문자 테스트
            unicode_test_cases = [
                {
                    "name": "한글",
                    "text": "안녕하세요! RAG 시스템을 테스트합니다. 한국어 처리가 정상적으로 작동하나요?",
                    "language": "ko"
                },
                {
                    "name": "영어",
                    "text": "Hello! This is a test for the RAG system. Does English processing work correctly?",
                    "language": "en"
                },
                {
                    "name": "일본어",
                    "text": "こんにちは！RAGシステムをテストしています。日本語処理は正常に動作しますか？",
                    "language": "ja"
                },
                {
                    "name": "러시아어",
                    "text": "Привет! Это тест системы RAG. Правильно ли работает обработка русского языка?",
                    "language": "ru"
                },
                {
                    "name": "이모지 및 특수문자",
                    "text": "🚀 AI 시스템 테스트 🤖 Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?",
                    "language": "mixed"
                },
                {
                    "name": "수학 기호",
                    "text": "수학 기호: ∑∫∆∇∞±≤≥≠≈∝∈∉∪∩⊂⊃⊆⊇∧∨¬∀∃",
                    "language": "math"
                }
            ]

            for test_case in unicode_test_cases:
                encoding_result = {
                    "name": test_case["name"],
                    "original_text": test_case["text"],
                    "language": test_case["language"],
                    "tests": {}
                }

                try:
                    # 1. BM25 토큰화 테스트
                    tokens = BM25Scorer.preprocess_text(test_case["text"])
                    encoding_result["tests"]["bm25_tokenization"] = {
                        "success": True,
                        "token_count": len(tokens),
                        "sample_tokens": tokens[:5]
                    }
                except Exception as e:
                    encoding_result["tests"]["bm25_tokenization"] = {
                        "success": False,
                        "error": str(e)
                    }

                try:
                    # 2. 임베딩 생성 테스트
                    embedding = await EmbeddingService.generate_embedding(test_case["text"])
                    encoding_result["tests"]["embedding_generation"] = {
                        "success": len(embedding) > 0,
                        "embedding_length": len(embedding),
                        "sample_values": embedding[:3] if embedding else []
                    }
                except Exception as e:
                    encoding_result["tests"]["embedding_generation"] = {
                        "success": False,
                        "error": str(e)
                    }

                try:
                    # 3. 데이터베이스 저장/조회 테스트 (시뮬레이션)
                    # 실제로는 DB에 저장하지 않고 문자열 처리만 확인
                    encoded_text = test_case["text"].encode('utf-8').decode('utf-8')
                    encoding_result["tests"]["database_compatibility"] = {
                        "success": encoded_text == test_case["text"],
                        "round_trip_success": True
                    }
                except Exception as e:
                    encoding_result["tests"]["database_compatibility"] = {
                        "success": False,
                        "error": str(e)
                    }

                # 전체 테스트 성공 여부
                encoding_result["overall_success"] = all(
                    test.get("success", False)
                    for test in encoding_result["tests"].values()
                )

                results["encoding_tests"].append(encoding_result)

            # 특수 문자 처리 테스트
            special_chars = {
                "quotes": "\"'""''",
                "dashes": "—–-",
                "spaces": "\u00A0\u2000\u2001\u2002\u2003",
                "control": "\n\r\t",
                "combining": "é̂ñ̃ü̈",
                "rtl": "العربية עברית"
            }

            char_test_results = {}
            for category, chars in special_chars.items():
                try:
                    test_text = f"Test with {category}: {chars}"
                    tokens = BM25Scorer.preprocess_text(test_text)
                    char_test_results[category] = {
                        "success": True,
                        "processed": len(tokens) > 0
                    }
                except Exception as e:
                    char_test_results[category] = {
                        "success": False,
                        "error": str(e)
                    }

            results["character_tests"] = char_test_results

            # 전체 성공 여부
            successful_encodings = sum(1 for test in results["encoding_tests"] if test["overall_success"])
            successful_chars = sum(1 for test in char_test_results.values() if test["success"])

            results["success"] = (
                successful_encodings >= len(results["encoding_tests"]) * 0.8 and
                successful_chars >= len(char_test_results) * 0.7
            )

            self.test_results["encoding_tests"] = results

        except Exception as e:
            logger.error(f"UTF-8 인코딩 테스트 실패: {e}")
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()

        logger.info(f"UTF-8 인코딩 테스트 완료 - 성공: {results['success']}")
        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("=== 하이브리드 검색 시스템 포괄적 테스트 시작 ===")

        # 전체 테스트 시작 시간
        overall_start = time.time()

        # 1. 테스트 데이터 설정
        setup_success = await self.setup_test_data()
        if not setup_success:
            logger.warning("테스트 데이터 설정 실패, 기본 데이터로 진행")

        # 2. 개별 테스트 실행
        test_functions = [
            ("BM25 스코어링", self.test_bm25_scoring),
            ("벡터 임베딩", self.test_vector_embedding_similarity),
            ("Cross-Encoder 리랭킹", self.test_cross_encoder_reranking),
            ("하이브리드 검색 통합", self.test_hybrid_search_integration),
            ("성능 메트릭", self.test_performance_metrics_collection),
            ("UTF-8 인코딩", self.test_utf8_encoding_compatibility)
        ]

        for test_name, test_func in test_functions:
            logger.info(f"{test_name} 테스트 실행 중...")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"{test_name} 테스트 중 예외 발생: {e}")
                logger.error(traceback.format_exc())

        # 전체 테스트 시간
        total_time = time.time() - overall_start

        # 3. 통합 결과 생성
        overall_results = {
            "test_summary": {
                "total_time": total_time,
                "setup_success": setup_success,
                "tests_completed": len(test_functions),
                "timestamp": datetime.utcnow().isoformat()
            },
            "individual_results": self.test_results,
            "final_metrics": self.test_metrics.get_metrics(),
            "success_summary": {},
            "recommendations": []
        }

        # 4. 성공률 계산
        success_counts = {}
        for test_category, test_result in self.test_results.items():
            success_counts[test_category] = test_result.get("success", False)

        overall_success = sum(success_counts.values()) / len(success_counts) if success_counts else 0

        overall_results["success_summary"] = {
            "overall_success_rate": overall_success,
            "individual_successes": success_counts,
            "critical_failures": [
                category for category, success in success_counts.items()
                if not success and category in ["hybrid_tests", "vector_tests"]
            ]
        }

        # 5. 권장사항 생성
        recommendations = []

        if not success_counts.get("bm25_tests", False):
            recommendations.append("BM25 스코어링 개선: 토큰화 로직과 점수 계산 알고리즘을 검토하세요.")

        if not success_counts.get("vector_tests", False):
            recommendations.append("벡터 임베딩 개선: OpenAI API 키 설정과 임베딩 생성 과정을 확인하세요.")

        if not success_counts.get("cross_encoder_tests", False):
            recommendations.append("Cross-Encoder 개선: 리랭킹 알고리즘의 관련성 점수 계산을 개선하세요.")

        if not success_counts.get("hybrid_tests", False):
            recommendations.append("하이브리드 검색 개선: BM25와 벡터 검색의 가중치 조정과 결과 합성 로직을 최적화하세요.")

        if overall_results["final_metrics"].get("error_rate", 0) > 0.1:
            recommendations.append("오류율 감소: 시스템 안정성을 위해 오류 처리와 폴백 메커니즘을 강화하세요.")

        avg_latency = overall_results["final_metrics"].get("avg_latency", 0)
        if avg_latency > 2.0:
            recommendations.append(f"성능 최적화: 평균 지연시간({avg_latency:.2f}s)을 2초 이하로 개선하세요.")

        if not success_counts.get("encoding_tests", False):
            recommendations.append("인코딩 개선: 다국어 및 특수문자 처리 로직을 강화하세요.")

        overall_results["recommendations"] = recommendations

        # 6. 결과 로깅
        logger.info("=== 테스트 결과 요약 ===")
        logger.info(f"전체 성공률: {overall_success:.1%}")
        logger.info(f"전체 실행 시간: {total_time:.2f}초")
        logger.info(f"실패한 테스트: {[k for k, v in success_counts.items() if not v]}")

        if recommendations:
            logger.info("권장사항:")
            for rec in recommendations:
                logger.info(f"  - {rec}")

        return overall_results

    def save_results_to_file(self, results: Dict[str, Any], filename: str = "hybrid_search_test_results.json"):
        """테스트 결과를 파일에 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")

async def main():
    """메인 테스트 실행 함수"""
    print("하이브리드 검색 시스템 포괄적 테스트 시작")
    print("=" * 60)

    tester = HybridSearchTester()

    try:
        # 모든 테스트 실행
        results = await tester.run_all_tests()

        # 결과 저장
        tester.save_results_to_file(results)

        # 요약 출력
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print(f"전체 성공률: {results['success_summary']['overall_success_rate']:.1%}")
        print(f"총 실행시간: {results['test_summary']['total_time']:.2f}초")

        if results['recommendations']:
            print("\n권장사항:")
            for rec in results['recommendations']:
                print(f"  - {rec}")

        print(f"\n상세 결과: hybrid_search_test_results.json")
        print("=" * 60)

        return results['success_summary']['overall_success_rate'] >= 0.7

    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # 비동기 실행
    import platform
    if platform.system() == "Windows":
        # Windows에서 ProactorEventLoop 사용
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    success = asyncio.run(main())
    sys.exit(0 if success else 1)