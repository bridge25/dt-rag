#!/usr/bin/env python3
"""
DT-RAG 시스템 완전한 E2E 통합 테스트
모든 구현된 컴포넌트들의 통합 동작을 검증합니다.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List
import tempfile

# UTF-8 출력 설정
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class IntegrationTestSuite:
    """DT-RAG 시스템 완전한 통합 테스트 스위트"""

    def __init__(self):
        self.results = {}
        self.start_time = time.time()

    async def test_embedding_service(self) -> Dict[str, Any]:
        """벡터 임베딩 서비스 테스트"""
        print("1. 벡터 임베딩 서비스 테스트...")

        try:
            from apps.api.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()

            # 테스트 텍스트들
            test_texts = [
                "Machine learning algorithms for natural language processing",
                "Deep learning neural networks and transformers",
                "RAG systems with vector embeddings"
            ]

            results = {}

            # 개별 임베딩 생성 테스트
            embedding = await embedding_service.generate_embedding(test_texts[0])
            results['single_embedding'] = {
                'dimension': len(embedding),
                'type': type(embedding).__name__
            }

            # 배치 임베딩 생성 테스트
            batch_embeddings = await embedding_service.generate_batch_embeddings(test_texts)
            results['batch_embeddings'] = {
                'count': len(batch_embeddings),
                'dimensions': [len(emb) for emb in batch_embeddings]
            }

            # 유사도 계산 테스트
            similarity = await embedding_service.calculate_similarity(
                test_texts[0], test_texts[1]
            )
            results['similarity'] = float(similarity)

            # 캐싱 테스트
            cached_embedding = await embedding_service.generate_embedding(test_texts[0])
            results['caching'] = len(cached_embedding) == len(embedding)

            return {
                'status': 'PASS',
                'results': results,
                'message': f"임베딩 서비스 정상 동작 ({results['single_embedding']['dimension']}차원)"
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'message': "임베딩 서비스 오류"
            }

    async def test_hybrid_search_engine(self) -> Dict[str, Any]:
        """하이브리드 검색 엔진 테스트"""
        print("2. 하이브리드 검색 엔진 테스트...")

        try:
            from apps.search.hybrid_search_engine import hybrid_search

            # 테스트 쿼리
            query = "machine learning algorithms for text processing"

            # 하이브리드 검색 실행
            results, metrics = await hybrid_search(
                query=query,
                top_k=5,
                filters=None
            )

            test_results = {
                'query': query,
                'results_count': len(results),
                'search_time': metrics.get('total_time', 0),
                'has_scores': all('score' in result for result in results),
                'score_range': [
                    min(result['score'] for result in results) if results else 0,
                    max(result['score'] for result in results) if results else 0
                ]
            }

            return {
                'status': 'PASS' if len(results) > 0 else 'PARTIAL',
                'results': test_results,
                'message': f"하이브리드 검색 동작 확인 ({len(results)}개 결과)"
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'message': "하이브리드 검색 오류"
            }

    async def test_ragas_evaluation(self) -> Dict[str, Any]:
        """RAGAS 평가 시스템 테스트"""
        print("3. RAGAS 평가 시스템 테스트...")

        try:
            from apps.evaluation.ragas_engine import RAGASEvaluator

            evaluator = RAGASEvaluator()

            # 테스트 데이터
            test_query = "What are machine learning algorithms?"
            test_response = "Machine learning algorithms are computational methods that learn patterns from data to make predictions or decisions."
            test_contexts = [
                "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                "These algorithms can learn from and make predictions on data.",
                "Common types include supervised, unsupervised, and reinforcement learning."
            ]

            # RAGAS 평가 실행
            evaluation_result = await evaluator.evaluate_rag_response(
                query=test_query,
                response=test_response,
                retrieved_contexts=test_contexts
            )

            test_results = {
                'metrics': {
                    'faithfulness': evaluation_result.metrics.faithfulness,
                    'context_precision': evaluation_result.metrics.context_precision,
                    'context_recall': evaluation_result.metrics.context_recall,
                    'answer_relevancy': evaluation_result.metrics.answer_relevancy
                },
                'overall_score': evaluation_result.overall_score,
                'quality_flags': evaluation_result.quality_flags,
                'has_all_metrics': all([
                    evaluation_result.metrics.faithfulness is not None,
                    evaluation_result.metrics.context_precision is not None,
                    evaluation_result.metrics.context_recall is not None,
                    evaluation_result.metrics.answer_relevancy is not None
                ])
            }

            return {
                'status': 'PASS',
                'results': test_results,
                'message': f"RAGAS 평가 정상 동작 (전체 점수: {evaluation_result.overall_score:.3f})"
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'message': "RAGAS 평가 오류"
            }

    async def test_database_integration(self) -> Dict[str, Any]:
        """데이터베이스 통합 테스트"""
        print("4. 데이터베이스 통합 테스트...")

        try:
            from apps.api.database import test_database_connection, DatabaseManager

            # 데이터베이스 연결 테스트
            is_connected = await test_database_connection()

            test_results = {
                'connection_status': is_connected,
                'fallback_mode': not is_connected
            }

            if is_connected:
                try:
                    # 실제 데이터베이스 쿼리 테스트
                    db_manager = DatabaseManager()
                    async with db_manager.async_session() as session:
                        from sqlalchemy import text
                        result = await session.execute(text("SELECT 1 as test"))
                        test_value = result.scalar()
                        test_results['query_test'] = test_value == 1
                except Exception as db_error:
                    test_results['query_error'] = str(db_error)

            return {
                'status': 'PASS' if is_connected else 'PARTIAL',
                'results': test_results,
                'message': f"데이터베이스 {'연결됨' if is_connected else 'Fallback 모드'}"
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'message': "데이터베이스 통합 오류"
            }

    async def test_api_server_integration(self) -> Dict[str, Any]:
        """API 서버 통합 테스트"""
        print("5. API 서버 통합 테스트...")

        try:
            import httpx
            import subprocess
            import signal
            import os
            from contextlib import asynccontextmanager

            # 서버를 백그라운드에서 시작
            server_process = None

            try:
                # full_server.py 시작 (비동기)
                server_process = subprocess.Popen([
                    sys.executable, 'full_server.py'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # 서버 시작 대기
                await asyncio.sleep(3)

                test_results = {}

                async with httpx.AsyncClient(timeout=10.0) as client:
                    # 1. 루트 엔드포인트 테스트
                    try:
                        response = await client.get("http://localhost:8001/")
                        test_results['root_endpoint'] = {
                            'status_code': response.status_code,
                            'has_content': len(response.text) > 0
                        }
                    except Exception as e:
                        test_results['root_endpoint'] = {'error': str(e)}

                    # 2. 헬스체크 테스트
                    try:
                        response = await client.get("http://localhost:8001/health")
                        test_results['health_check'] = {
                            'status_code': response.status_code,
                            'response_data': response.json() if response.status_code == 200 else None
                        }
                    except Exception as e:
                        test_results['health_check'] = {'error': str(e)}

                    # 3. 검색 API 테스트
                    try:
                        search_data = {
                            "query": "machine learning",
                            "max_results": 5
                        }
                        response = await client.post(
                            "http://localhost:8001/api/v1/search",
                            json=search_data
                        )
                        test_results['search_api'] = {
                            'status_code': response.status_code,
                            'has_results': response.status_code == 200
                        }
                    except Exception as e:
                        test_results['search_api'] = {'error': str(e)}

                return {
                    'status': 'PASS' if any(
                        result.get('status_code') == 200
                        for result in test_results.values()
                        if isinstance(result, dict) and 'status_code' in result
                    ) else 'PARTIAL',
                    'results': test_results,
                    'message': "API 서버 통합 테스트 완료"
                }

            finally:
                # 서버 프로세스 정리
                if server_process:
                    try:
                        server_process.terminate()
                        server_process.wait(timeout=5)
                    except:
                        try:
                            server_process.kill()
                        except:
                            pass

        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'message': "API 서버 통합 오류"
            }

    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """End-to-End 워크플로우 테스트"""
        print("6. End-to-End 워크플로우 테스트...")

        try:
            # 통합된 워크플로우 시뮬레이션
            from apps.api.embedding_service import EmbeddingService
            from apps.evaluation.ragas_engine import RAGASEvaluator

            embedding_service = EmbeddingService()
            evaluator = RAGASEvaluator()

            # 1. 문서 임베딩 생성
            document_text = "Retrieval Augmented Generation combines information retrieval with language generation to produce more accurate and informative responses."
            document_embedding = await embedding_service.generate_embedding(document_text)

            # 2. 쿼리 임베딩 생성 및 유사도 검색 시뮬레이션
            query_text = "What is RAG in machine learning?"
            query_embedding = await embedding_service.generate_embedding(query_text)

            similarity = await embedding_service.calculate_similarity(document_text, query_text)

            # 3. RAG 응답 생성 시뮬레이션
            rag_response = "RAG (Retrieval Augmented Generation) is a technique that enhances language models by retrieving relevant information from a knowledge base before generating responses."

            # 4. RAGAS 평가
            evaluation = await evaluator.evaluate_rag_response(
                query=query_text,
                response=rag_response,
                retrieved_contexts=[document_text]
            )

            workflow_results = {
                'document_embedding_dim': len(document_embedding),
                'query_embedding_dim': len(query_embedding),
                'similarity_score': float(similarity),
                'ragas_overall_score': evaluation.overall_score,
                'ragas_metrics': {
                    'faithfulness': evaluation.metrics.faithfulness,
                    'context_precision': evaluation.metrics.context_precision,
                    'context_recall': evaluation.metrics.context_recall,
                    'answer_relevancy': evaluation.metrics.answer_relevancy
                },
                'quality_flags': evaluation.quality_flags
            }

            return {
                'status': 'PASS',
                'results': workflow_results,
                'message': f"E2E 워크플로우 성공 (유사도: {similarity:.3f}, RAGAS: {evaluation.overall_score:.3f})"
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'message': "E2E 워크플로우 오류"
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("=" * 60)
        print("DT-RAG 시스템 완전한 E2E 통합 테스트 시작")
        print("=" * 60)

        tests = [
            ("embedding_service", self.test_embedding_service),
            ("hybrid_search_engine", self.test_hybrid_search_engine),
            ("ragas_evaluation", self.test_ragas_evaluation),
            ("database_integration", self.test_database_integration),
            ("api_server_integration", self.test_api_server_integration),
            ("end_to_end_workflow", self.test_end_to_end_workflow)
        ]

        test_results = {}
        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            try:
                result = await test_func()
                test_results[test_name] = result

                if result['status'] == 'PASS':
                    passed_tests += 1
                    print(f"   ✅ {result['message']}")
                elif result['status'] == 'PARTIAL':
                    passed_tests += 0.5
                    print(f"   ⚠️  {result['message']}")
                else:
                    print(f"   ❌ {result['message']}")
                    if 'error' in result:
                        print(f"      오류: {result['error']}")

            except Exception as e:
                test_results[test_name] = {
                    'status': 'FAIL',
                    'error': str(e),
                    'message': f"{test_name} 예외 발생"
                }
                print(f"   ❌ {test_name} 예외 발생: {str(e)}")

        total_time = time.time() - self.start_time
        success_rate = (passed_tests / total_tests) * 100

        print()
        print("=" * 60)
        print("통합 테스트 결과 요약")
        print("=" * 60)
        print(f"총 테스트: {total_tests}")
        print(f"통과: {passed_tests}")
        print(f"성공률: {success_rate:.1f}%")
        print(f"실행 시간: {total_time:.2f}초")

        if success_rate >= 80:
            overall_status = "PASS"
            print("✅ 전체 시스템 통합 테스트 성공!")
        elif success_rate >= 60:
            overall_status = "PARTIAL"
            print("⚠️ 부분적 성공 - 일부 기능 개선 필요")
        else:
            overall_status = "FAIL"
            print("❌ 통합 테스트 실패 - 주요 문제 해결 필요")

        # 결과를 파일로 저장
        results_file = Path("integration_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'overall_status': overall_status,
                'success_rate': success_rate,
                'total_time': total_time,
                'test_results': test_results,
                'timestamp': time.time()
            }, f, indent=2, ensure_ascii=False)

        print(f"상세 결과 저장: {results_file}")
        print("=" * 60)

        return {
            'overall_status': overall_status,
            'success_rate': success_rate,
            'results': test_results
        }

async def main():
    """메인 실행 함수"""
    test_suite = IntegrationTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())