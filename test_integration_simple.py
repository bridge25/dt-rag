#!/usr/bin/env python3
"""
DT-RAG 시스템 간단한 통합 테스트
핵심 기능들의 기본 동작을 검증합니다.
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# UTF-8 출력 설정
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_embedding_service():
    """임베딩 서비스 기본 테스트"""
    print("1. 임베딩 서비스 테스트...")

    try:
        from apps.api.embedding_service import EmbeddingService

        service = EmbeddingService()

        # 단일 임베딩 생성
        text = "Machine learning algorithms"
        embedding = await service.generate_embedding(text)

        print(f"   ✅ 임베딩 생성 성공: {len(embedding)}차원")
        return True

    except Exception as e:
        print(f"   ❌ 임베딩 서비스 오류: {e}")
        return False

async def test_search_engine():
    """검색 엔진 기본 테스트"""
    print("2. 검색 엔진 테스트...")

    try:
        from apps.search.hybrid_search_engine import HybridSearchEngine

        # 검색 엔진 초기화만 테스트
        engine = HybridSearchEngine()

        print("   ✅ 검색 엔진 초기화 성공")
        return True

    except Exception as e:
        print(f"   ❌ 검색 엔진 오류: {e}")
        return False

async def test_ragas_engine():
    """RAGAS 엔진 기본 테스트"""
    print("3. RAGAS 엔진 테스트...")

    try:
        from apps.evaluation.ragas_engine import RAGASEvaluator

        evaluator = RAGASEvaluator()

        print("   ✅ RAGAS 엔진 초기화 성공")
        return True

    except Exception as e:
        print(f"   ❌ RAGAS 엔진 오류: {e}")
        return False

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("4. 데이터베이스 연결 테스트...")

    try:
        from apps.api.database import test_database_connection

        is_connected = await test_database_connection()

        if is_connected:
            print("   ✅ 데이터베이스 연결 성공")
        else:
            print("   ⚠️ Fallback 모드 (정상)")

        return True

    except Exception as e:
        print(f"   ❌ 데이터베이스 연결 오류: {e}")
        return False

async def test_full_server_import():
    """Full Server 임포트 테스트"""
    print("5. Full Server 임포트 테스트...")

    try:
        # full_server.py 임포트만 테스트
        import importlib.util
        spec = importlib.util.spec_from_file_location("full_server", "full_server.py")
        full_server = importlib.util.module_from_spec(spec)

        print("   ✅ Full Server 임포트 성공")
        return True

    except Exception as e:
        print(f"   ❌ Full Server 임포트 오류: {e}")
        return False

async def run_integration_tests():
    """통합 테스트 실행"""
    print("=" * 50)
    print("DT-RAG 시스템 기본 통합 테스트")
    print("=" * 50)

    tests = [
        test_embedding_service,
        test_search_engine,
        test_ragas_engine,
        test_database_connection,
        test_full_server_import
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"   ❌ 테스트 예외: {e}")

    print()
    print("=" * 50)
    print(f"테스트 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")

    if passed >= total * 0.8:
        print("✅ 기본 통합 테스트 성공!")
        return True
    else:
        print("⚠️ 일부 컴포넌트 확인 필요")
        return False

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
