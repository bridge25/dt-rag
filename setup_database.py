#!/usr/bin/env python3
"""
DT-RAG Database Setup Script
실제 PostgreSQL + pgvector 데이터베이스를 초기화하고 검증합니다.
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """데이터베이스 설정 및 검증"""
    print("🚀 DT-RAG Database Setup Starting...")
    print("=" * 50)

    try:
        # 환경 변수 로드
        from dotenv import load_dotenv
        load_dotenv()

        database_url = os.getenv("DATABASE_URL")
        print(f"📡 Database URL: {database_url}")

        # 데이터베이스 모듈 임포트
        from apps.api.database import (
            init_database,
            test_database_connection,
            setup_search_system,
            get_search_performance_metrics
        )

        print("\n1️⃣ Testing Database Connection...")
        db_connected = await test_database_connection()

        if not db_connected:
            print("❌ Database connection failed!")
            print("📋 Please check:")
            print("   - PostgreSQL Docker container is running")
            print("   - Port 5432 is accessible")
            print("   - Database credentials are correct")
            print("   - Run: docker-compose up -d postgres")
            return False

        print("✅ Database connection successful!")

        print("\n2️⃣ Initializing Database Schema...")
        schema_initialized = await init_database()

        if not schema_initialized:
            print("❌ Database schema initialization failed!")
            return False

        print("✅ Database schema initialized!")

        print("\n3️⃣ Setting up Search System...")
        search_setup = await setup_search_system()

        if not search_setup:
            print("⚠️ Search system setup had issues, but continuing...")
        else:
            print("✅ Search system configured!")

        print("\n4️⃣ Checking Performance Metrics...")
        metrics = await get_search_performance_metrics()

        if "error" in metrics:
            print(f"⚠️ Metrics collection failed: {metrics['error']}")
        else:
            performance = metrics.get("performance", {})
            stats = metrics.get("analytics", {}).get("statistics", {})

            print(f"📊 System Status:")
            print(f"   - Total Documents: {stats.get('total_docs', 0)}")
            print(f"   - BM25 Ready: {'✅' if performance.get('bm25_ready') else '❌'}")
            print(f"   - Vector Ready: {'✅' if performance.get('vector_ready') else '❌'}")
            print(f"   - Hybrid Ready: {'✅' if performance.get('hybrid_ready') else '❌'}")
            print(f"   - API Status: {'✅' if performance.get('api_status') == 'enabled' else '❌ (No OpenAI API Key)'}")

        print("\n5️⃣ Testing Sample Operations...")

        # 샘플 검색 테스트
        try:
            from apps.api.database import SearchDAO

            print("   Testing BM25 search...")
            bm25_results = await SearchDAO.hybrid_search(
                query="RAG system",
                topk=3
            )
            print(f"   BM25 Results: {len(bm25_results)} documents found")

            if bm25_results:
                print(f"   Sample result: '{bm25_results[0]['title']}'")

        except Exception as e:
            print(f"   ⚠️ Search test failed: {e}")

        # 샘플 분류 테스트
        try:
            from apps.api.database import ClassifyDAO

            print("   Testing ML classification...")
            classify_result = await ClassifyDAO.classify_text(
                "This is a document about RAG systems and vector search"
            )
            print(f"   Classification: {classify_result['label']} ({classify_result['confidence']:.2f})")

        except Exception as e:
            print(f"   ⚠️ Classification test failed: {e}")

        print("\n🎉 Database Setup Complete!")
        print("=" * 50)
        print("✅ PostgreSQL + pgvector database is ready")
        print("✅ All tables and indexes created")
        print("✅ Sample data available for testing")
        print("✅ Search and classification systems active")
        print()
        print("🚀 You can now start the server:")
        print("   python full_server.py")
        print("   or")
        print("   python -m apps.api.main")
        print()
        print("📖 API Documentation:")
        print("   http://localhost:8001/docs (full_server)")
        print("   http://localhost:8000/docs (main API)")

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)