#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Fallback Database Testing Script with UTF-8 Support
Dynamic Taxonomy RAG v1.8.1 - Local Database Testing without PostgreSQL
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
import tempfile

# UTF-8 encoding setup
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api"))

# Configure logging with UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_sqlite.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_sqlite_database():
    """Test SQLite database functionality"""
    try:
        logger.info("🔍 SQLite 데이터베이스 테스트 시작...")

        # Create temporary SQLite database
        temp_db_path = tempfile.mktemp(suffix='.db')
        sqlite_url = f"sqlite+aiosqlite:///{temp_db_path}"

        # Override database URL for testing
        os.environ["DATABASE_URL"] = sqlite_url
        logger.info(f"✅ 테스트 SQLite DB 경로: {temp_db_path}")

        # Import after setting environment variable
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy.orm import declarative_base, Mapped, mapped_column
        from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, text
        from datetime import datetime
        import uuid

        # Create test models
        Base = declarative_base()

        class TestDocument(Base):
            __tablename__ = "test_documents"

            id: Mapped[str] = mapped_column(String, primary_key=True)
            title: Mapped[str] = mapped_column(String, nullable=False)
            content: Mapped[str] = mapped_column(Text, nullable=False)
            doc_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
            created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

        class TestChunk(Base):
            __tablename__ = "test_chunks"

            id: Mapped[str] = mapped_column(String, primary_key=True)
            document_id: Mapped[str] = mapped_column(String, nullable=False)
            content: Mapped[str] = mapped_column(Text, nullable=False)
            chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
            created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

        # Create engine and session
        engine = create_async_engine(sqlite_url, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Test table creation
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ SQLite 테이블 생성 완료")

        # Test CRUD operations
        async with async_session() as session:
            # Create test document
            test_doc = TestDocument(
                id=str(uuid.uuid4()),
                title="테스트 문서",
                content="이것은 UTF-8 인코딩 테스트 문서입니다. 한글이 정상적으로 저장되는지 확인합니다.",
                doc_metadata={"source": "test", "language": "ko"},
                created_at=datetime.utcnow()
            )

            session.add(test_doc)
            await session.commit()
            logger.info(f"✅ 테스트 문서 생성 완료: {test_doc.id}")

            # Create test chunk
            test_chunk = TestChunk(
                id=str(uuid.uuid4()),
                document_id=test_doc.id,
                content="테스트 청크 내용입니다. 한글 UTF-8 인코딩 테스트.",
                chunk_metadata={"chunk_index": 0, "token_count": 10},
                created_at=datetime.utcnow()
            )

            session.add(test_chunk)
            await session.commit()
            logger.info(f"✅ 테스트 청크 생성 완료: {test_chunk.id}")

            # Test retrieval
            retrieved_doc = await session.get(TestDocument, test_doc.id)
            if retrieved_doc:
                logger.info(f"✅ 문서 조회 성공: {retrieved_doc.title}")
                logger.info(f"✅ 메타데이터 조회: {retrieved_doc.doc_metadata}")
            else:
                logger.error("❌ 문서 조회 실패")
                return False

            # Test query
            result = await session.execute(text("SELECT COUNT(*) FROM test_documents"))
            doc_count = result.scalar()
            logger.info(f"✅ 문서 개수 조회: {doc_count}개")

            # Cleanup
            await session.delete(test_chunk)
            await session.delete(test_doc)
            await session.commit()
            logger.info("✅ 테스트 데이터 정리 완료")

        # Close engine
        await engine.dispose()

        # Remove temporary file
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
            logger.info("✅ 임시 데이터베이스 파일 삭제")

        return True

    except Exception as e:
        logger.error(f"❌ SQLite 데이터베이스 테스트 실패: {str(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return False

async def test_utf8_encoding():
    """Test UTF-8 encoding specifically"""
    try:
        logger.info("🔍 UTF-8 인코딩 전용 테스트 시작...")

        # Test various Korean texts
        test_strings = [
            "안녕하세요 Dynamic Taxonomy RAG 시스템입니다",
            "문서 분류 및 검색 기능을 테스트합니다",
            "특수문자 테스트: !@#$%^&*()_+{}|:<>?[]\\;',./",
            "이모지 테스트: 🚀🔍✅❌⚠️📊🎉",
            "JSON 데이터: {'한글키': '한글값', 'numbers': [1, 2, 3]}"
        ]

        for i, test_string in enumerate(test_strings):
            logger.info(f"✅ UTF-8 테스트 {i+1}: {test_string}")

            # Test encoding/decoding
            encoded = test_string.encode('utf-8')
            decoded = encoded.decode('utf-8')

            if test_string == decoded:
                logger.info(f"✅ 인코딩/디코딩 성공")
            else:
                logger.error(f"❌ 인코딩/디코딩 실패")
                return False

        logger.info("✅ 모든 UTF-8 인코딩 테스트 통과")
        return True

    except Exception as e:
        logger.error(f"❌ UTF-8 인코딩 테스트 실패: {str(e)}")
        return False

async def test_json_serialization():
    """Test JSON serialization with Korean text"""
    try:
        logger.info("🔍 JSON 직렬화 테스트 시작...")

        import json

        test_data = {
            "제목": "테스트 문서",
            "내용": "한글 내용이 포함된 문서입니다",
            "메타데이터": {
                "언어": "한국어",
                "작성자": "테스트 사용자",
                "태그": ["분류", "검색", "테스트"]
            },
            "생성일시": "2024-01-01T00:00:00Z",
            "숫자": 12345,
            "불린": True
        }

        # Test JSON serialization
        json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
        logger.info(f"✅ JSON 직렬화 성공")

        # Test JSON deserialization
        restored_data = json.loads(json_str)

        if restored_data == test_data:
            logger.info("✅ JSON 역직렬화 성공")
        else:
            logger.error("❌ JSON 역직렬화 실패")
            return False

        # Test with file I/O
        temp_json_path = tempfile.mktemp(suffix='.json')
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        with open(temp_json_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        if file_data == test_data:
            logger.info("✅ 파일 JSON I/O 성공")
        else:
            logger.error("❌ 파일 JSON I/O 실패")
            return False

        # Cleanup
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

        return True

    except Exception as e:
        logger.error(f"❌ JSON 직렬화 테스트 실패: {str(e)}")
        return False

async def main():
    """Run all SQLite and encoding tests"""
    print("🚀 Dynamic Taxonomy RAG v1.8.1 - SQLite 및 인코딩 테스트")
    print("=" * 60)

    test_results = {}

    # Run all tests
    tests = [
        ("UTF-8 인코딩", test_utf8_encoding),
        ("JSON 직렬화", test_json_serialization),
        ("SQLite 데이터베이스", test_sqlite_database)
    ]

    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트 중...")
        result = await test_func()
        test_results[test_name] = result

        if result:
            print(f"✅ {test_name} 테스트 통과")
        else:
            print(f"❌ {test_name} 테스트 실패")

    # Summary
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약:")

    passed = sum(test_results.values())
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  - {test_name}: {status}")

    print(f"\n🏆 전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 모든 SQLite 및 인코딩 테스트 성공!")
        print("💡 PostgreSQL 없이도 기본 데이터베이스 기능 검증 완료")
    else:
        print("⚠️ 일부 테스트 실패 - 로그를 확인하세요.")

    return passed == total

if __name__ == "__main__":
    asyncio.run(main())