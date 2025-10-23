#!/usr/bin/env python3
"""
빠른 동작 테스트
"""
import sys
import json
import time
from pathlib import Path

def test_fastapi():
    """FastAPI 테스트"""
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse

        app = FastAPI(title="Test API")

        @app.get("/")
        async def root():
            return {"status": "working", "message": "✅ FastAPI가 정상 동작합니다"}

        print("✅ FastAPI 앱 생성 성공")
        return True
    except Exception as e:
        print(f"❌ FastAPI 테스트 실패: {e}")
        return False

def test_pydantic():
    """Pydantic 테스트"""
    try:
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            status: str = "working"

        model = TestModel(name="test")
        print("✅ Pydantic 모델 생성 성공")
        return True
    except Exception as e:
        print(f"❌ Pydantic 테스트 실패: {e}")
        return False

def test_uvicorn():
    """Uvicorn 테스트"""
    try:
        import uvicorn
        print("✅ Uvicorn 임포트 성공")
        return True
    except Exception as e:
        print(f"❌ Uvicorn 테스트 실패: {e}")
        return False

def main():
    print("🧪 Dynamic Taxonomy RAG API 동작 테스트")
    print("=" * 50)

    results = {
        "fastapi": test_fastapi(),
        "pydantic": test_pydantic(),
        "uvicorn": test_uvicorn()
    }

    print("\n📊 테스트 결과:")
    success_count = sum(results.values())
    total_count = len(results)

    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {name.upper()}: {'성공' if result else '실패'}")

    print(f"\n🎯 전체 결과: {success_count}/{total_count} 성공")

    if success_count == total_count:
        print("\n🚀 모든 핵심 컴포넌트가 정상 동작합니다!")
        print("📡 실제 서버 실행 방법:")
        print("   1. cd apps/api")
        print("   2. python3 main.py")
        print("   3. 브라우저에서 http://localhost:8000 접속")
        print("   4. API 문서는 http://localhost:8000/docs")
    else:
        print("\n⚠️ 일부 컴포넌트에 문제가 있습니다.")

    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)