#!/usr/bin/env python3
"""
Database fixes validation test
스키마 불일치 및 SQLAlchemy 2.0 호환성 수정 검증
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.abspath('.'))

async def test_database_imports():
    """기본 import 테스트"""
    try:
        from apps.api.database import (
            DatabaseManager, TaxonomyDAO, SearchDAO, ClassifyDAO,
            TaxonomyNode, TaxonomyEdge, TaxonomyMigration,
            Document, DocumentChunk, Embedding, DocTaxonomy, CaseBank
        )
        print("✅ 모든 클래스 import 성공")
        return True
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

async def test_taxonomy_dao():
    """TaxonomyDAO 기본 기능 테스트"""
    try:
        from apps.api.database import TaxonomyDAO

        # 폴백 트리 테스트
        fallback_tree = await TaxonomyDAO._get_fallback_tree(1)
        assert isinstance(fallback_tree, list)
        assert len(fallback_tree) > 0
        assert fallback_tree[0]['label'] == 'AI'
        assert isinstance(fallback_tree[0]['node_id'], int)  # 정수형 node_id 확인
        print("✅ TaxonomyDAO 폴백 트리 테스트 성공")
        return True
    except Exception as e:
        print(f"❌ TaxonomyDAO 테스트 실패: {e}")
        return False

async def test_search_dao():
    """SearchDAO 기본 기능 테스트"""
    try:
        from apps.api.database import SearchDAO

        # 폴백 검색 테스트
        fallback_search = await SearchDAO._get_fallback_search("test query")
        assert isinstance(fallback_search, list)
        assert len(fallback_search) > 0
        assert 'metadata' in fallback_search[0]
        assert 'bm25_score' in fallback_search[0]['metadata']  # 메타데이터 업데이트 확인
        print("✅ SearchDAO 폴백 검색 테스트 성공")
        return True
    except Exception as e:
        print(f"❌ SearchDAO 테스트 실패: {e}")
        return False

async def test_classify_dao():
    """ClassifyDAO 기본 기능 테스트"""
    try:
        from apps.api.database import ClassifyDAO

        # 분류 테스트
        result = await ClassifyDAO.classify_text("This is about RAG systems and retrieval")
        assert isinstance(result, dict)
        assert 'canonical' in result
        assert 'node_id' in result
        assert isinstance(result['node_id'], int)  # 정수형 node_id 확인
        assert isinstance(result['version'], int)  # 정수형 version 확인
        print("✅ ClassifyDAO 분류 테스트 성공")
        return True
    except Exception as e:
        print(f"❌ ClassifyDAO 테스트 실패: {e}")
        return False

async def test_database_manager():
    """DatabaseManager 기본 기능 테스트"""
    try:
        from apps.api.database import DatabaseManager

        # 매니저 인스턴스 생성 테스트
        db_manager = DatabaseManager()
        assert db_manager.engine is not None
        assert db_manager.async_session is not None
        print("✅ DatabaseManager 인스턴스 생성 성공")
        return True
    except Exception as e:
        print(f"❌ DatabaseManager 테스트 실패: {e}")
        return False

async def main():
    """메인 테스트 실행기"""
    print("🧪 Database fixes validation test 시작")
    print("=" * 50)

    tests = [
        ("Import 테스트", test_database_imports),
        ("TaxonomyDAO 테스트", test_taxonomy_dao),
        ("SearchDAO 테스트", test_search_dao),
        ("ClassifyDAO 테스트", test_classify_dao),
        ("DatabaseManager 테스트", test_database_manager),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 실행 중...")
        try:
            if await test_func():
                passed += 1
            else:
                print(f"   실패: {test_name}")
        except Exception as e:
            print(f"   오류 발생: {e}")

    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: {passed}/{total} 성공")

    if passed == total:
        print("🎉 모든 테스트 통과! 데이터베이스 수정이 성공적으로 완료되었습니다.")
        return True
    else:
        print("⚠️  일부 테스트 실패. 추가 수정이 필요할 수 있습니다.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)