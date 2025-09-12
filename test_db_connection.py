#!/usr/bin/env python3
"""
Quick DB connection test script for debugging GitHub Actions failures
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_connection():
    """직접 psycopg2 연결 테스트"""
    try:
        db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/dt_rag_test')
        logger.info(f"Testing direct connection to: {db_url}")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # 기본 연결 테스트
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"PostgreSQL version: {version}")
        
        # 확장 기능 테스트
        cursor.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'btree_gist', 'pg_trgm');")
        extensions = cursor.fetchall()
        logger.info(f"Available extensions: {[ext[0] for ext in extensions]}")
        
        conn.close()
        logger.info("✅ Direct psycopg2 connection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """SQLAlchemy 연결 테스트"""
    try:
        db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/dt_rag_test')
        logger.info(f"Testing SQLAlchemy connection to: {db_url}")
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_val = result.fetchone()[0]
            logger.info(f"SQLAlchemy test query result: {test_val}")
        
        logger.info("✅ SQLAlchemy connection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLAlchemy connection failed: {e}")
        return False

def test_table_creation():
    """간단한 테이블 생성 테스트"""
    try:
        db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/dt_rag_test')
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # 테스트 테이블 생성
        cursor.execute("""
            DROP TABLE IF EXISTS test_migration;
            CREATE TABLE test_migration (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # 데이터 삽입
        cursor.execute("INSERT INTO test_migration (name) VALUES ('test');")
        
        # 데이터 조회
        cursor.execute("SELECT * FROM test_migration;")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Table creation test successful: {result}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table creation test failed: {e}")
        return False

def main():
    logger.info("=== DB Connection Test Suite ===")
    
    # 환경 변수 확인
    db_url = os.environ.get('DATABASE_URL')
    test_db_url = os.environ.get('TEST_DATABASE_URL')
    
    logger.info(f"DATABASE_URL: {db_url}")
    logger.info(f"TEST_DATABASE_URL: {test_db_url}")
    
    # 테스트 실행
    tests = [
        ("Direct Connection", test_direct_connection),
        ("SQLAlchemy Connection", test_sqlalchemy_connection),
        ("Table Creation", test_table_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
    
    # 결과 요약
    logger.info("\n=== Test Results ===")
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()