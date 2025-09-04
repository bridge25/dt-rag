"""
Dynamic Taxonomy RAG API Server
FastAPI 애플리케이션 - OpenAPI v1.8.1 스펙 구현
"""

import logging
import time
import uuid
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routers import classify, search, taxonomy, ingest
from .middleware.database import DatabaseMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.monitoring import MonitoringMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Dynamic Taxonomy RAG API starting up...")
    
    # Initialize database connections
    try:
        from .services.database_service import DatabaseService
        db_service = DatabaseService()
        await db_service.initialize()
        logger.info("✅ Database connections initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize embedding service
    try:
        from .services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        logger.info("✅ Embedding service initialized")
    except Exception as e:
        logger.error(f"❌ Embedding service initialization failed: {e}")
        raise
    
    yield
    
    logger.info("🔄 Dynamic Taxonomy RAG API shutting down...")
    
    # Cleanup resources
    try:
        await db_service.close()
        await embedding_service.close()
        logger.info("✅ Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")


# Create FastAPI app with OpenAPI v1.8.1 metadata
app = FastAPI(
    title="Dynamic Taxonomy RAG API",
    description="""
    동적 다단계 분류(DAG+버전/롤백)·트리형 UI·카테고리-한정 에이전트 시스템
    
    ## 핵심 NFR 가드
    - 성능: p95≤4s, p50≤1.5s
    - 비용: 평균 비용/쿼리 ≤₩10
    - 품질: Faithfulness ≥ 0.85 (RAGAS 기반)
    - 운영: 롤백 TTR ≤ 15분
    """,
    version="1.8.1",
    contact={
        "name": "A팀 (Taxonomy & Data Platform)",
        "email": "team-a@example.com",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.dt-rag.example.com", "description": "Production server"},
    ],
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(DatabaseMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(MonitoringMiddleware)


@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    """Add request metadata (request_id, processing time)"""
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add taxonomy version (default to latest)
    request.state.taxonomy_version = "1.8.1"
    
    # Start timer
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add headers to response
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Taxonomy-Version"] = request.state.taxonomy_version
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with consistent error format"""
    
    error_response = {
        "error": {
            "type": "http_error",
            "code": exc.status_code,
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "taxonomy_version": getattr(request.state, "taxonomy_version", "1.8.1"),
            "timestamp": time.time()
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = {
        "error": {
            "type": "internal_server_error",
            "code": 500,
            "message": "Internal server error occurred",
            "request_id": getattr(request.state, "request_id", "unknown"),
            "taxonomy_version": getattr(request.state, "taxonomy_version", "1.8.1"),
            "timestamp": time.time()
        }
    }
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """시스템 건강 상태 확인"""
    
    try:
        from .services.database_service import DatabaseService
        db_service = DatabaseService()
        
        # Check database connection
        db_status = await db_service.health_check()
        
        # Check embedding service
        from .services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        embedding_status = await embedding_service.health_check()
        
        return {
            "status": "healthy",
            "version": "1.8.1",
            "components": {
                "database": db_status,
                "embeddings": embedding_status
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Enhanced monitoring endpoints
@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """Prometheus 메트릭 엔드포인트 (통합 시스템)"""
    from .middleware.monitoring import get_prometheus_metrics
    from fastapi.responses import PlainTextResponse
    
    metrics_data = await get_prometheus_metrics()
    return PlainTextResponse(
        content=metrics_data,
        media_type="text/plain"
    )

@app.get("/system/health", tags=["Monitoring"])
async def system_health():
    """시스템 건강 상태 및 알림"""
    from .middleware.monitoring import get_system_health
    return await get_system_health()

@app.get("/system/metrics", tags=["Monitoring"])
async def system_metrics():
    """시스템 메트릭 요약 (JSON)"""
    from .metrics import get_metrics_summary
    return get_metrics_summary()

@app.get("/system/costs", tags=["Monitoring"])
async def cost_status():
    """비용 가드 상태"""
    from .metrics import metrics_collector
    return metrics_collector.get_cost_guard_status()

# Include routers
app.include_router(
    classify.router,
    prefix="/classify",
    tags=["Classification"]
)

app.include_router(
    search.router, 
    prefix="/search",
    tags=["Search"]
)

app.include_router(
    taxonomy.router,
    prefix="/taxonomy",
    tags=["Taxonomy"]
)

app.include_router(
    ingest.router,
    tags=["Ingestion"]
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )