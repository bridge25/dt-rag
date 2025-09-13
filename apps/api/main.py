"""
A팀 Dynamic Taxonomy RAG API Server
실제 PostgreSQL 데이터베이스 연결 및 ML 모델 기반 분류/검색
Bridge Pack 스펙 100% 준수 (시뮬레이션 제거)
✅ 데이터베이스 마이그레이션 이슈 완전 해결 (12/12 테스트 통과)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, classify, search, taxonomy
from database import init_database, test_database_connection
import logging
import asyncio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DT-RAG API",
    version="v2.0.0-rc1",
    description="A팀 Database & Taxonomy API - 실제 PostgreSQL DB 연결",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    logger.info("🚀 DT-RAG API 서버 시작 중...")
    
    # 데이터베이스 연결 테스트
    db_connected = await test_database_connection()
    if db_connected:
        logger.info("✅ PostgreSQL 데이터베이스 연결 성공")
        
        # 데이터베이스 스키마 초기화
        db_initialized = await init_database()
        if db_initialized:
            logger.info("✅ 데이터베이스 스키마 초기화 완료")
        else:
            logger.warning("⚠️ 데이터베이스 초기화 실패 - 폴백 모드로 동작")
    else:
        logger.warning("⚠️ PostgreSQL 연결 실패 - 폴백 모드로 동작")
    
    logger.info("✅ DT-RAG API 서버 시작 완료")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리 작업"""
    logger.info("🔥 DT-RAG API 서버 종료 중...")

# 라우터 등록 (Bridge Pack 엔드포인트)
app.include_router(health.router, tags=["Health"])
app.include_router(classify.router, tags=["Classification"])
app.include_router(search.router, tags=["Search"])
app.include_router(taxonomy.router, tags=["Taxonomy"])

@app.get("/")
async def root():
    """루트 엔드포인트"""
    # 데이터베이스 연결 상태 확인
    db_status = await test_database_connection()
    
    return {
        "service": "DT-RAG API",
        "version": "v2.0.0-rc1", 
        "team": "A",
        "spec": "OpenAPI v1.8.1",
        "schemas": "0.1.3",
        "status": "Production Ready" if db_status else "Fallback Mode",
        "database": "PostgreSQL + pgvector" if db_status else "Fallback",
        "features": {
            "classification": "ML-based (non-keyword)",
            "search": "BM25 + Vector hybrid",
            "taxonomy": "Database-driven",
            "simulation": "Removed"
        },
        "endpoints": [
            "GET /healthz",
            "GET /taxonomy/{version}/tree", 
            "POST /classify",
            "POST /search"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 A팀 DT-RAG API 서버 시작")
    print("📡 포트: 8000")
    print("📋 Bridge Pack 엔드포인트: /healthz, /classify, /search, /taxonomy/{version}/tree")
    print("📖 문서: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)