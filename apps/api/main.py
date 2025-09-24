"""
Dynamic Taxonomy RAG API v1.8.1

Comprehensive RESTful API for the Dynamic Taxonomy RAG system.
Provides endpoints for taxonomy management, search, classification,
orchestration, agent factory, and monitoring.

Features:
- PostgreSQL + pgvector for scalable data storage
- Hybrid BM25 + vector search with semantic reranking
- ML-based classification with HITL support
- LangGraph 7-step RAG pipeline orchestration
- Dynamic agent creation and management
- Real-time monitoring and observability
- Comprehensive authentication and authorization
- OpenAPI 3.0.3 specification with interactive documentation
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# Import existing routers
from routers import health, classify, search, taxonomy, ingestion

# Import new comprehensive routers
from routers.taxonomy_router import taxonomy_router
from routers.search_router import search_router
from routers.classification_router import classification_router
from routers.orchestration_router import orchestration_router
from routers.agent_factory_router import agent_factory_router
from routers.monitoring_router import monitoring_router

# Import evaluation router
try:
    from routers.evaluation import router as evaluation_router
    EVALUATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Evaluation router not available: {e}")
    EVALUATION_AVAILABLE = False

# Import optimization routers
try:
    from routers.batch_search import router as batch_search_router
    BATCH_SEARCH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Batch search router not available: {e}")
    BATCH_SEARCH_AVAILABLE = False

# Import monitoring components
try:
    from routers.monitoring import router as monitoring_api_router
    from monitoring.metrics import initialize_metrics_collector, get_metrics_collector
    from monitoring.health_check import initialize_health_checker
    from cache.redis_manager import initialize_redis_manager
    MONITORING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Monitoring components not available: {e}")
    MONITORING_AVAILABLE = False

# Import configuration and database
from config import get_config
from openapi_spec import generate_openapi_spec
from database import init_database, test_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global config
config = get_config()

# Application lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    # Startup
    logger.info("🚀 Starting Dynamic Taxonomy RAG API v1.8.1")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Debug mode: {config.debug}")

    # Initialize monitoring systems
    if MONITORING_AVAILABLE:
        logger.info("Initializing monitoring systems...")
        try:
            # Initialize metrics collector
            initialize_metrics_collector(enable_prometheus=True)
            logger.info("✅ Metrics collector initialized")

            # Initialize health checker
            initialize_health_checker()
            logger.info("✅ Health checker initialized")

            # Initialize Redis manager (optional)
            if config.redis_enabled:
                await initialize_redis_manager()
                logger.info("✅ Redis manager initialized")
            else:
                logger.info("ℹ️ Redis disabled - using memory cache only")

        except Exception as e:
            logger.warning(f"⚠️ Monitoring initialization failed: {e}")

    # Initialize database
    logger.info("Initializing database connection...")
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

    # Initialize system metrics
    if MONITORING_AVAILABLE:
        try:
            metrics_collector = get_metrics_collector()
            metrics_collector.update_system_metrics()
            logger.info("✅ System metrics initialized")
        except Exception as e:
            logger.warning(f"⚠️ System metrics initialization failed: {e}")

    yield

    # Shutdown
    logger.info("🔥 Shutting down Dynamic Taxonomy RAG API")

    # Cleanup monitoring resources
    if MONITORING_AVAILABLE:
        try:
            from cache.redis_manager import get_redis_manager
            redis_manager = await get_redis_manager()
            await redis_manager.close()
            logger.info("✅ Redis connections closed")
        except Exception as e:
            logger.warning(f"⚠️ Redis cleanup failed: {e}")

# Create FastAPI application
app = FastAPI(
    title="Dynamic Taxonomy RAG API",
    description="""
    RESTful API for the Dynamic Taxonomy RAG v1.8.1 system.

    This API provides comprehensive endpoints for:

    ## Core Features
    - **Taxonomy Management**: Hierarchical taxonomy operations with versioning
    - **Hybrid Search**: BM25 + vector search with semantic reranking
    - **Classification Pipeline**: Document classification with HITL support
    - **RAG Orchestration**: LangGraph-based 7-step RAG pipeline
    - **Agent Factory**: Dynamic agent creation and management
    - **Monitoring & Observability**: Real-time system monitoring and analytics

    ## Authentication
    - **JWT Bearer Tokens**: For user authentication
    - **API Keys**: For service-to-service communication
    - **OAuth 2.0**: For third-party integrations

    ## Performance Features
    - **Rate Limiting**: Tiered limits based on user type
    - **Caching**: Redis-based response caching
    - **Async Processing**: Background job processing for heavy operations
    - **Real-time Monitoring**: Performance metrics and health checks

    ## Security & Compliance
    - **GDPR/CCPA Compliance**: Privacy controls and data management
    - **PII Detection**: Automatic sensitive data identification
    - **Audit Logging**: Comprehensive request and action logging
    - **OWASP Security**: Following API security best practices
    """,
    version="1.8.1",
    openapi_url="/api/v1/openapi.json",
    docs_url=None,  # We'll create custom docs
    redoc_url=None,  # We'll create custom redoc
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
    expose_headers=config.cors.expose_headers,
    max_age=config.cors.max_age
)

# Trusted host middleware for security
if config.security.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.security.trusted_hosts
    )

# Request logging and monitoring middleware
@app.middleware("http")
async def log_requests_and_track_metrics(request: Request, call_next):
    """Log all HTTP requests and track performance metrics"""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")

    try:
        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        status_code = response.status_code

        # Log response
        logger.info(f"Response: {status_code} ({response_time_ms:.2f}ms)")

        # Track metrics if monitoring is available
        if MONITORING_AVAILABLE:
            try:
                from routers.monitoring import track_request_metrics
                await track_request_metrics(request, response_time_ms, status_code)
            except Exception as e:
                logger.warning(f"Failed to track request metrics: {e}")

        return response

    except Exception as e:
        # Calculate error response time
        response_time_ms = (time.time() - start_time) * 1000

        # Log error
        logger.error(f"Request failed: {request.method} {request.url} - {str(e)} ({response_time_ms:.2f}ms)")

        # Track error metrics if monitoring is available
        if MONITORING_AVAILABLE:
            try:
                from routers.monitoring import track_request_metrics
                await track_request_metrics(request, response_time_ms, 500)
            except Exception as metric_e:
                logger.warning(f"Failed to track error metrics: {metric_e}")

        raise

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with RFC 7807 Problem Details format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://httpstatuses.com/{exc.status_code}",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url),
            "timestamp": time.time()
        },
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "type": "https://httpstatuses.com/500",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url),
            "timestamp": time.time()
        }
    )

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.8.1",
        "environment": config.environment
    }

# Custom OpenAPI schema generation
def custom_openapi():
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    # Use our comprehensive OpenAPI specification
    openapi_schema = generate_openapi_spec()

    # Override with actual path operations from FastAPI
    openapi_schema["paths"] = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )["paths"]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "alpha",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True
        }
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc documentation"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )

# Include existing routers (Bridge Pack compatibility)
app.include_router(health.router, tags=["Health"])
app.include_router(classify.router, tags=["Classification"])
app.include_router(search.router, tags=["Search"])
app.include_router(taxonomy.router, tags=["Taxonomy"])
app.include_router(ingestion.router, tags=["Document Ingestion"])

# Include new comprehensive API routers
app.include_router(
    taxonomy_router,
    prefix="/api/v1",
    tags=["Taxonomy Management"]
)

app.include_router(
    search_router,
    prefix="/api/v1",
    tags=["Search"]
)

app.include_router(
    classification_router,
    prefix="/api/v1",
    tags=["Classification"]
)

app.include_router(
    orchestration_router,
    prefix="/api/v1",
    tags=["Orchestration"]
)

app.include_router(
    agent_factory_router,
    prefix="/api/v1",
    tags=["Agent Factory"]
)

# Include monitoring router if available
if MONITORING_AVAILABLE:
    app.include_router(
        monitoring_api_router,
        prefix="/api/v1",
        tags=["Monitoring"]
    )

app.include_router(
    monitoring_router,
    prefix="/api/v1",
    tags=["Monitoring"]
)

# Include evaluation router if available
if EVALUATION_AVAILABLE:
    app.include_router(
        evaluation_router,
        prefix="/api/v1",
        tags=["Evaluation", "RAGAS", "Quality Assurance"]
    )

# Include optimization routers if available
if BATCH_SEARCH_AVAILABLE:
    app.include_router(
        batch_search_router,
        prefix="/api/v1",
        tags=["Batch Processing", "Search Optimization"]
    )

# API versioning support
@app.get("/api/versions", tags=["Versioning"])
async def list_api_versions():
    """List available API versions"""
    return {
        "versions": [
            {
                "version": "v1",
                "status": "current",
                "base_url": "/api/v1",
                "documentation": "/docs",
                "features": [
                    "Taxonomy Management",
                    "Hybrid Search",
                    "Classification Pipeline",
                    "RAG Orchestration",
                    "Agent Factory",
                    "Monitoring & Observability"
                ]
            }
        ],
        "current": "v1",
        "deprecated": [],
        "sunset_policy": "https://docs.example.com/api-sunset-policy"
    }

# Rate limiting info endpoint
@app.get("/api/v1/rate-limits", tags=["Rate Limiting"])
async def get_rate_limit_info():
    """Get rate limiting information for current user"""
    # TODO: Implement actual rate limit checking based on user/API key
    return {
        "limits": {
            "requests_per_minute": 100,
            "requests_per_hour": 5000,
            "requests_per_day": 50000,
            "concurrent_requests": 10
        },
        "current_usage": {
            "requests_this_minute": 15,
            "requests_this_hour": 234,
            "requests_today": 1567,
            "concurrent_requests": 3
        },
        "reset_times": {
            "minute_reset": 45,
            "hour_reset": 2847,
            "day_reset": 76847
        },
        "upgrade_info": {
            "current_tier": "standard",
            "available_tiers": ["premium", "enterprise"],
            "upgrade_url": "https://example.com/upgrade"
        }
    }

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with comprehensive system information"""
    # 데이터베이스 연결 상태 확인
    db_status = await test_database_connection()

    return {
        "name": "Dynamic Taxonomy RAG API",
        "version": "1.8.1",
        "description": "RESTful API for dynamic taxonomy RAG system",
        "team": "A",
        "spec": "OpenAPI v1.8.1",
        "schemas": "0.1.3",
        "status": "Production Ready" if db_status else "Fallback Mode",
        "database": "PostgreSQL + pgvector" if db_status else "Fallback",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/api/v1/openapi.json"
        },
        "features": {
            "classification": "ML-based with HITL support",
            "search": "BM25 + Vector hybrid with reranking",
            "taxonomy": "Versioned hierarchical DAG",
            "orchestration": "LangGraph 7-step RAG pipeline",
            "agent_factory": "Dynamic agent creation",
            "monitoring": "Real-time observability",
            "simulation": "Removed - 100% real data"
        },
        "api_endpoints": {
            "health": "/health",
            "monitoring": "/api/v1/monitoring/health",
            "versions": "/api/v1/versions",
            "rate_limits": "/api/v1/rate-limits"
        },
        "bridge_pack_endpoints": [
            "GET /healthz",
            "GET /taxonomy/{version}/tree",
            "POST /classify",
            "POST /search",
            "POST /ingestion/upload",
            "POST /ingestion/urls",
            "GET /ingestion/status/{job_id}"
        ],
        "comprehensive_endpoints": [
            "GET /api/v1/taxonomy/versions",
            "GET /api/v1/taxonomy/{version}/tree",
            "POST /api/v1/search",
            "POST /api/v1/classify",
            "POST /api/v1/pipeline/execute",
            "POST /api/v1/agents/from-category",
            "GET /api/v1/monitoring/health"
        ],
        "environment": config.environment,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn

    print("🚀 Dynamic Taxonomy RAG API v1.8.1 서버 시작")
    print("📡 포트: 8000")
    print("🌍 환경:", config.environment)
    print("🔧 디버그 모드:", config.debug)
    print()
    print("📋 Bridge Pack 호환 엔드포인트:")
    print("   GET /healthz")
    print("   POST /classify")
    print("   POST /search")
    print("   GET /taxonomy/{version}/tree")
    print("   POST /ingestion/upload")
    print()
    print("🆕 새로운 포괄적 API 엔드포인트:")
    print("   GET /api/v1/taxonomy/versions")
    print("   POST /api/v1/search")
    print("   POST /api/v1/classify")
    print("   POST /api/v1/pipeline/execute")
    print("   POST /api/v1/agents/from-category")
    print("   GET /api/v1/monitoring/health")
    print()
    print("📖 문서:")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc: http://localhost:8000/redoc")
    print("   OpenAPI 스펙: http://localhost:8000/api/v1/openapi.json")
    print()
    print("🔍 모니터링:")
    print("   Health Check: http://localhost:8000/health")
    print("   API Monitoring: http://localhost:8000/api/v1/monitoring/health")
    print("   Rate Limits: http://localhost:8000/api/v1/rate-limits")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level="info" if not config.debug else "debug",
        access_log=True
    )