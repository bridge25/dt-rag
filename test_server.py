"""
간단한 FastAPI 서버 테스트 - 실제 동작 확인용
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api"))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import time

app = FastAPI(
    title="Dynamic Taxonomy RAG API - Test Server",
    description="실제 동작 확인을 위한 테스트 서버",
    version="1.8.1"
)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "Dynamic Taxonomy RAG API - Test Server",
        "version": "1.8.1",
        "status": "✅ 실제 동작 중",
        "timestamp": time.time(),
        "message": "서버가 정상적으로 실행되고 있습니다!",
        "test_endpoints": [
            "GET / - 이 페이지",
            "GET /health - 헬스체크",
            "GET /test - 간단한 테스트",
            "GET /docs - Swagger 문서"
        ]
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "server": "running",
        "message": "✅ 서버가 정상적으로 동작 중입니다"
    }

@app.get("/test")
async def test_endpoint():
    """간단한 테스트 엔드포인트"""
    return {
        "test": "success",
        "message": "✅ API 엔드포인트가 정상적으로 응답합니다",
        "data": {
            "current_time": time.time(),
            "server_info": "FastAPI + Uvicorn",
            "python_version": sys.version,
            "working_directory": str(Path.cwd())
        }
    }

if __name__ == "__main__":
    print("🚀 테스트 서버 시작...")
    print("📡 포트: 8001 (테스트용)")
    print("🌐 URL: http://localhost:8001")
    print("📖 문서: http://localhost:8001/docs")
    print("❤️ 헬스체크: http://localhost:8001/health")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )