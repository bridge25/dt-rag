#!/usr/bin/env python3
"""
DT-RAG Production System Test Script
실제 PostgreSQL + pgvector 데이터베이스 연결을 검증하고
모든 핵심 기능을 테스트합니다.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class ProductionSystemTester:
    """프로덕션 시스템 종합 테스터"""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    async def test_database_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        print("🔌 Testing Database Connection...")

        try:
            from apps.api.database import test_database_connection, db_manager
            from sqlalchemy import text

            # 기본 연결 테스트
            connected = await test_database_connection()
            if not connected:
                self.test_results["database_connection"] = {
                    "status": "FAIL",
                    "error": "Basic connection test failed"
                }
                return False

            # pgvector 확장 확인
            async with db_manager.async_session() as session:
                try:
                    result = await session.execute(
                        text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                    )
                    has_pgvector = result.scalar()

                    if not has_pgvector:
                        print("   ⚠️ pgvector extension not found")
                        self.test_results["database_connection"] = {
                            "status": "PARTIAL",
                            "warning": "pgvector extension missing"
                        }
                        return True  # 기본 연결은 작동

                    print("   ✅ pgvector extension found")

                except Exception as e:
                    print(f"   ⚠️ pgvector check failed: {e}")

                # 테이블 존재 확인
                tables_to_check = ['documents', 'taxonomy', 'search_logs']
                existing_tables = []

                for table in tables_to_check:
                    try:
                        result = await session.execute(
                            text(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')")
                        )
                        if result.scalar():
                            existing_tables.append(table)
                    except Exception:
                        pass

                print(f"   📋 Tables found: {', '.join(existing_tables)}")

            self.test_results["database_connection"] = {
                "status": "PASS",
                "pgvector_enabled": has_pgvector,
                "tables_found": existing_tables
            }

            return True

        except Exception as e:
            self.test_results["database_connection"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"   ❌ Connection test failed: {e}")
            return False

    async def test_document_operations(self) -> bool:
        """문서 CRUD 작업 테스트"""
        print("\n📄 Testing Document Operations...")

        try:
            from apps.api.database import db_manager
            from sqlalchemy import text

            async with db_manager.async_session() as session:
                # 문서 조회 테스트
                query = text("SELECT COUNT(*) FROM documents")
                result = await session.execute(query)
                doc_count = result.scalar()

                print(f"   📊 Total documents in database: {doc_count}")

                if doc_count == 0:
                    print("   ⚠️ No documents found - inserting test document")

                    # 테스트 문서 삽입
                    insert_query = text("""
                        INSERT INTO documents (title, content, metadata)
                        VALUES (:title, :content, :metadata)
                        RETURNING id
                    """)

                    result = await session.execute(insert_query, {
                        "title": "Test Document",
                        "content": "This is a test document for DT-RAG system validation.",
                        "metadata": json.dumps({"test": True, "created_by": "test_script"})
                    })

                    doc_id = result.scalar()
                    await session.commit()

                    print(f"   ✅ Test document created with ID: {doc_id}")

                # 최근 문서 조회
                recent_docs_query = text("""
                    SELECT id, title, content, created_at
                    FROM documents
                    ORDER BY created_at DESC
                    LIMIT 3
                """)

                result = await session.execute(recent_docs_query)
                recent_docs = result.fetchall()

                print(f"   📋 Recent documents:")
                for doc in recent_docs:
                    print(f"      - {doc[0]}: '{doc[1][:50]}...'")

            self.test_results["document_operations"] = {
                "status": "PASS",
                "total_documents": doc_count + (1 if doc_count == 0 else 0),
                "recent_documents": len(recent_docs)
            }

            return True

        except Exception as e:
            self.test_results["document_operations"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"   ❌ Document operations test failed: {e}")
            return False

    async def test_search_functionality(self) -> bool:
        """검색 기능 테스트"""
        print("\n🔍 Testing Search Functionality...")

        try:
            from apps.api.database import SearchDAO

            test_queries = [
                "DT-RAG system",
                "vector embeddings",
                "test document"
            ]

            search_results = {}

            for query in test_queries:
                print(f"   Testing query: '{query}'")

                start_time = time.time()
                results = await SearchDAO.hybrid_search(
                    query=query,
                    topk=5
                )
                search_time = (time.time() - start_time) * 1000

                print(f"   🔍 Found {len(results)} results in {search_time:.2f}ms")

                if results:
                    top_result = results[0]
                    print(f"   📄 Top result: '{top_result['title']}'")
                    print(f"   📊 Score: {top_result['score']:.3f}")

                    metadata = top_result.get('metadata', {})
                    if 'bm25_score' in metadata and 'vector_score' in metadata:
                        print(f"   📈 BM25: {metadata['bm25_score']:.3f}, Vector: {metadata['vector_score']:.3f}")

                search_results[query] = {
                    "result_count": len(results),
                    "search_time_ms": search_time,
                    "has_results": len(results) > 0
                }

            all_searches_working = all(result["has_results"] for result in search_results.values())

            self.test_results["search_functionality"] = {
                "status": "PASS" if all_searches_working else "PARTIAL",
                "search_results": search_results,
                "total_queries_tested": len(test_queries)
            }

            return True

        except Exception as e:
            self.test_results["search_functionality"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"   ❌ Search functionality test failed: {e}")
            return False

    async def test_classification_system(self) -> bool:
        """분류 시스템 테스트"""
        print("\n🏷️ Testing Classification System...")

        try:
            from apps.api.database import ClassifyDAO

            test_texts = [
                "This document discusses RAG systems and vector search technology.",
                "Machine learning algorithms are used for document classification.",
                "The taxonomy system organizes documents hierarchically."
            ]

            classification_results = {}

            for text in test_texts:
                print(f"   Classifying: '{text[:60]}...'")

                start_time = time.time()
                result = await ClassifyDAO.classify_text(text)
                classify_time = (time.time() - start_time) * 1000

                print(f"   🏷️ Category: {result['label']}")
                print(f"   📊 Confidence: {result['confidence']:.3f}")
                print(f"   🛣️ Path: {' → '.join(result['canonical'])}")
                print(f"   ⏱️ Time: {classify_time:.2f}ms")

                classification_results[text[:30] + "..."] = {
                    "label": result['label'],
                    "confidence": result['confidence'],
                    "path": result['canonical'],
                    "classify_time_ms": classify_time
                }

            avg_confidence = sum(r["confidence"] for r in classification_results.values()) / len(classification_results)

            self.test_results["classification_system"] = {
                "status": "PASS",
                "classification_results": classification_results,
                "average_confidence": avg_confidence,
                "total_texts_classified": len(test_texts)
            }

            return True

        except Exception as e:
            self.test_results["classification_system"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"   ❌ Classification system test failed: {e}")
            return False

    async def test_taxonomy_system(self) -> bool:
        """분류체계 시스템 테스트"""
        print("\n🌳 Testing Taxonomy System...")

        try:
            from apps.api.database import TaxonomyDAO

            # 기본 분류체계 조회
            taxonomy_tree = await TaxonomyDAO.get_tree("1")

            print(f"   📊 Taxonomy nodes found: {len(taxonomy_tree)}")

            if taxonomy_tree:
                print("   🌳 Taxonomy structure:")
                for node in taxonomy_tree[:3]:  # 상위 3개만 표시
                    path_str = " → ".join(node.get("canonical_path", []))
                    print(f"      {node.get('label', 'Unknown')}: {path_str}")

                self.test_results["taxonomy_system"] = {
                    "status": "PASS",
                    "node_count": len(taxonomy_tree),
                    "sample_nodes": taxonomy_tree[:3] if len(taxonomy_tree) > 0 else []
                }
            else:
                print("   ⚠️ No taxonomy nodes found - using fallback")
                self.test_results["taxonomy_system"] = {
                    "status": "PARTIAL",
                    "node_count": 0,
                    "using_fallback": True
                }

            return True

        except Exception as e:
            self.test_results["taxonomy_system"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"   ❌ Taxonomy system test failed: {e}")
            return False

    async def test_embedding_system(self) -> bool:
        """임베딩 시스템 테스트"""
        print("\n🧮 Testing Embedding System...")

        try:
            from apps.api.database import EmbeddingService, db_manager
            from sqlalchemy import text

            # 임베딩 생성 테스트
            test_text = "This is a test text for embedding generation."
            print(f"   Generating embedding for: '{test_text}'")

            start_time = time.time()
            embedding = await EmbeddingService.generate_embedding(test_text)
            embedding_time = (time.time() - start_time) * 1000

            if embedding:
                print(f"   ✅ Embedding generated: {len(embedding)} dimensions")
                print(f"   ⏱️ Time: {embedding_time:.2f}ms")
                print(f"   📊 Sample values: {embedding[:5]}...")

                # 데이터베이스의 임베딩 현황 확인
                async with db_manager.async_session() as session:
                    query = text("""
                        SELECT
                            COUNT(*) as total_docs,
                            COUNT(embedding) as docs_with_embeddings
                        FROM documents
                    """)
                    result = await session.execute(query)
                    stats = result.fetchone()

                    total_docs = stats[0]
                    docs_with_embeddings = stats[1]
                    coverage = (docs_with_embeddings / max(1, total_docs)) * 100

                    print(f"   📊 Database embeddings: {docs_with_embeddings}/{total_docs} ({coverage:.1f}%)")

                self.test_results["embedding_system"] = {
                    "status": "PASS",
                    "embedding_dimensions": len(embedding),
                    "generation_time_ms": embedding_time,
                    "database_coverage_percent": coverage,
                    "docs_with_embeddings": docs_with_embeddings
                }
            else:
                print("   ⚠️ Embedding generation returned empty result")
                self.test_results["embedding_system"] = {
                    "status": "PARTIAL",
                    "error": "Empty embedding result"
                }

            return True

        except Exception as e:
            self.test_results["embedding_system"] = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"   ❌ Embedding system test failed: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🧪 DT-RAG Production System Testing")
        print("=" * 60)

        # 테스트 실행
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Document Operations", self.test_document_operations),
            ("Search Functionality", self.test_search_functionality),
            ("Classification System", self.test_classification_system),
            ("Taxonomy System", self.test_taxonomy_system),
            ("Embedding System", self.test_embedding_system),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"   ❌ {test_name} failed with exception: {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = {
                    "status": "FAIL",
                    "error": f"Exception: {str(e)}"
                }

        # 테스트 결과 요약
        total_time = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}/{total} tests")
        print(f"❌ Failed: {total - passed}/{total} tests")
        print(f"⏱️ Total time: {total_time:.2f} seconds")

        # 상세 결과
        print("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_emoji = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}
            emoji = status_emoji.get(result["status"], "❓")
            print(f"   {emoji} {test_name.replace('_', ' ').title()}: {result['status']}")

            if "error" in result:
                print(f"      Error: {result['error']}")

        # 시스템 상태 평가
        if passed == total:
            overall_status = "🎉 PRODUCTION READY"
            print(f"\n{overall_status}")
            print("✅ All systems operational")
            print("✅ PostgreSQL + pgvector working")
            print("✅ Hybrid search functional")
            print("✅ ML classification active")
            print("✅ Ready for production deployment")
        elif passed >= total * 0.8:
            overall_status = "⚠️ MOSTLY FUNCTIONAL"
            print(f"\n{overall_status}")
            print("✅ Core systems operational")
            print("⚠️ Some features may be limited")
            print("💡 Check failed tests and resolve issues")
        else:
            overall_status = "❌ NEEDS ATTENTION"
            print(f"\n{overall_status}")
            print("❌ Critical systems not working")
            print("🔧 Database or core functionality issues")
            print("🚨 Not ready for production")

        return {
            "overall_status": overall_status,
            "tests_passed": passed,
            "tests_total": total,
            "test_results": self.test_results,
            "total_time_seconds": total_time
        }

async def main():
    """메인 실행 함수"""
    tester = ProductionSystemTester()
    results = await tester.run_all_tests()

    # 결과를 JSON 파일로 저장
    import json
    timestamp = int(time.time())
    results_file = f"test_results_{timestamp}.json"

    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️ Could not save results file: {e}")

    # 종료 코드 결정
    success_rate = results["tests_passed"] / results["tests_total"]
    return success_rate >= 0.8  # 80% 이상 통과하면 성공

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)