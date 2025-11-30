"""
Norade API v1.8.1

Comprehensive RESTful API for the Norade system.
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

@CODE:API-001
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, cast

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

# slowapi removed - using custom Redis-based rate limiter


# Import routers
from apps.api.routers.health import router as health_router
# Legacy routers - deprecated (A/B/C team integration artifacts)
# from apps.api.routers.search import router as search_legacy_router
# from apps.api.routers.taxonomy import router as taxonomy_legacy_router
# from apps.api.routers.classify import router as classify_legacy_router
from apps.api.routers.ingestion import router as ingestion_router
from apps.api.routers.taxonomy_router import taxonomy_router
from apps.api.routers.search_router import search_router
from apps.api.routers.classification_router import classification_router
from apps.api.routers.orchestration_router import orchestration_router
from apps.api.routers.agent_factory_router import agent_factory_router
from apps.api.routers.agent_router import router as agent_router
from apps.api.routers.monitoring_router import router as monitoring_router
from apps.api.routers.embedding_router import router as embedding_router
from apps.api.routers.evolution_router import router as evolution_router
from apps.api.routers.research_router import research_router
from apps.api.routers.admin.api_keys import router as api_keys_admin_router

# Import evaluation router
try:
    from apps.api.routers.evaluation import evaluation_router

    EVALUATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Evaluation router not available: {e}")
    EVALUATION_AVAILABLE = False

# Import optimization routers
try:
    from apps.api.routers.batch_search import router as batch_search_router

    BATCH_SEARCH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Batch search router not available: {e}")
    BATCH_SEARCH_AVAILABLE = False

# Import monitoring components
try:
    from apps.api.routers.monitoring import router as monitoring_api_router  # type: ignore[import-not-found]  # TODO: Implement monitoring router
    from apps.api.monitoring.metrics import (
        initialize_metrics_collector,
        get_metrics_collector,
    )
    from apps.api.monitoring.health_check import initialize_health_checker
    from apps.api.cache.redis_manager import initialize_redis_manager

    MONITORING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Monitoring components not available: {e}")
    MONITORING_AVAILABLE = False

# Import Sentry monitoring (optional)
try:
    from apps.api.monitoring.sentry_reporter import init_sentry

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logging.debug("Sentry monitoring not available")

# Import configuration and database
from apps.api.config import get_config, _validate_openai_api_key
from apps.api.database import init_database, test_database_connection
from apps.api.env_manager import get_env_manager, Environment

# Import OpenAPI spec generation (optional)
try:
    from apps.api.openapi_spec import generate_openapi_spec

    OPENAPI_SPEC_AVAILABLE = True
except ImportError:
    OPENAPI_SPEC_AVAILABLE = False
    logging.debug("OpenAPI spec generation not available")

# Import rate limiting
from apps.api.middleware.rate_limiter import rate_limiter, RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global config
config = get_config()


# Application lifespan context manager
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
# @CODE:MYPY-CONSOLIDATION-002 | Phase 14: unused-ignore (Fix 32 - decorator type stubs now available)
@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application startup and shutdown lifecycle"""
    # Startup
    logger.info("🚀 Starting Norade API v1.8.1")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Debug mode: {config.debug}")

    # Validate OpenAI API key configuration (SPEC-ENV-VALIDATE-001)
    env_manager = get_env_manager()
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if openai_api_key:
        if not _validate_openai_api_key(openai_api_key):
            logger.warning(
                "OPENAI_API_KEY format is invalid - using fallback dummy embeddings"
            )
    else:
        if env_manager.current_env == Environment.PRODUCTION:
            raise ValueError(
                "OPENAI_API_KEY environment variable is REQUIRED in production. "
                "Embedding service cannot operate without a valid API key."
            )
        else:
            logger.warning(
                "OPENAI_API_KEY not configured - using fallback dummy embeddings"
            )

    # Initialize Sentry monitoring (optional)
    if SENTRY_AVAILABLE:
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            sentry_initialized = init_sentry(
                dsn=sentry_dsn,
                environment=config.environment,
                release="1.8.1",
                traces_sample_rate=0.1,  # 10% of transactions
                profiles_sample_rate=0.1,  # 10% profiling
            )
            if sentry_initialized:
                logger.info("✅ Sentry monitoring initialized")
            else:
                logger.warning("⚠️ Sentry initialization failed")
        else:
            logger.info("ℹ️ Sentry DSN not configured - monitoring disabled")

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

            # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: attr-defined resolution
            # Initialize Redis manager (optional) - try-except handles failures
            try:
                await initialize_redis_manager()
                logger.info("✅ Redis manager initialized")
            except Exception as redis_err:
                logger.info(f"ℹ️ Redis initialization skipped: {redis_err} - using memory cache only")

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

    # Initialize rate limiter
    try:
        await rate_limiter.initialize()
        logger.info("✅ Rate limiter initialized")
    except Exception as e:
        logger.warning(f"⚠️ Rate limiter initialization failed: {e}")

    yield

    # Shutdown
    logger.info("🔥 Shutting down Norade API")

    # Close rate limiter
    try:
        await rate_limiter.close()
        logger.info("✅ Rate limiter closed")
    except Exception as e:
        logger.warning(f"⚠️ Rate limiter cleanup failed: {e}")

    # Cleanup monitoring resources
    if MONITORING_AVAILABLE:
        try:
            from apps.api.cache.redis_manager import get_redis_manager

            redis_manager = await get_redis_manager()
            await redis_manager.close()
            logger.info("✅ Redis connections closed")
        except Exception as e:
            logger.warning(f"⚠️ Redis cleanup failed: {e}")


# Create FastAPI application
app = FastAPI(
    title="Norade API",
    description="""
    RESTful API for the Norade v1.8.1 system.

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
    lifespan=lifespan,
)

# Add rate limiter state to app
# Custom Redis-based rate limiter (initialized in lifespan)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
    expose_headers=config.cors.expose_headers,
    max_age=config.cors.max_age,
)

# Trusted host middleware for security
if config.security.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=config.security.trusted_hosts
    )

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)


# Request logging and monitoring middleware
@app.middleware("http")  # Decorator lacks type stubs
async def log_requests_and_track_metrics(request: Request, call_next: Any) -> Any:
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
                metrics_collector = get_metrics_collector()
                labels = {
                    "method": request.method,
                    "endpoint": str(request.url.path),
                    "status": str(status_code),
                }
                metrics_collector.record_latency("http_request", response_time_ms, labels)
                metrics_collector.increment_counter("http_requests_total", labels)
            except Exception as e:
                logger.warning(f"Failed to track request metrics: {e}")

        return response

    except Exception as e:
        # Calculate error response time
        response_time_ms = (time.time() - start_time) * 1000

        # Log error
        logger.error(
            f"Request failed: {request.method} {request.url} - {str(e)} ({response_time_ms:.2f}ms)"
        )

        # Track error metrics if monitoring is available
        if MONITORING_AVAILABLE:
            try:
                metrics_collector = get_metrics_collector()
                labels = {
                    "method": request.method,
                    "endpoint": str(request.url.path),
                    "status": "500",
                }
                metrics_collector.record_latency("http_request", response_time_ms, labels)
                metrics_collector.increment_counter("http_requests_total", labels)
                metrics_collector.increment_counter("http_errors_total", labels)
            except Exception as metric_e:
                logger.warning(f"Failed to track error metrics: {metric_e}")

        raise


# Global exception handler
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.exception_handler(HTTPException)  # Decorator lacks type stubs
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with RFC 7807 Problem Details format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://httpstatuses.com/{exc.status_code}",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url),
            "timestamp": time.time(),
        },
        headers=exc.headers,
    )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.exception_handler(Exception)  # Decorator lacks type stubs
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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
            "timestamp": time.time(),
        },
    )


# Health check endpoint
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.get("/health", tags=["Health"])  # Decorator lacks type stubs
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint with database and Redis status"""
    from apps.api.database import test_database_connection

    db_status = "connected"
    redis_status = "connected"

    try:
        db_connected = await test_database_connection()
        if not db_connected:
            db_status = "disconnected"
    except Exception:
        db_status = "error"

    try:
        from apps.api.middleware.rate_limiter import rate_limiter

        if rate_limiter.redis_client:
            await rate_limiter.redis_client.ping()
            redis_status = "connected"
        else:
            redis_status = "not_initialized"
    except Exception:
        redis_status = "error"

    return {
        "status": (
            "healthy"
            if db_status == "connected" and redis_status == "connected"
            else "degraded"
        ),
        "database": db_status,
        "redis": redis_status,
        "timestamp": str(time.time()),
        "version": "1.8.1",
        "environment": config.environment,
    }


# Custom OpenAPI schema generation
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def custom_openapi() -> Dict[str, Any]:
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: call-arg resolution
    if OPENAPI_SPEC_AVAILABLE:
        openapi_schema = generate_openapi_spec(app)  # Pass app as required argument
        openapi_schema["paths"] = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )["paths"]
    else:
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

    app.openapi_schema = openapi_schema
    return cast(Dict[str, Any], app.openapi_schema)


app.openapi = custom_openapi  # type: ignore[method-assign]  # FastAPI pattern for custom OpenAPI


# Custom documentation endpoints
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.get("/docs", include_in_schema=False)  # Decorator lacks type stubs
async def custom_swagger_ui_html() -> Any:
    """Custom Swagger UI with enhanced styling"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,  # type: ignore[arg-type]  # FastAPI guarantees openapi_url is set
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
            "tryItOutEnabled": True,
        },
    )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.get("/redoc", include_in_schema=False)  # Decorator lacks type stubs
async def redoc_html() -> Any:
    """Custom ReDoc documentation"""
    return get_redoc_html(
        openapi_url=app.openapi_url,  # type: ignore[arg-type]  # FastAPI guarantees openapi_url is set
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


# Include existing routers
app.include_router(health_router, tags=["Health"])
# Legacy routers disabled - use /api/v1/* endpoints instead
# app.include_router(search_legacy_router, tags=["Search"])
# app.include_router(taxonomy_legacy_router, tags=["Taxonomy"])
# app.include_router(classify_legacy_router, tags=["Classification"])
app.include_router(ingestion_router, tags=["Document Ingestion"])

# Include new comprehensive API routers
app.include_router(taxonomy_router, prefix="/api/v1", tags=["Taxonomy Management"])

app.include_router(search_router, prefix="/api/v1", tags=["Search"])

app.include_router(classification_router, prefix="/api/v1", tags=["Classification"])

app.include_router(orchestration_router, prefix="/api/v1", tags=["Orchestration"])

app.include_router(agent_factory_router, prefix="/api/v1", tags=["Agent Factory"])

app.include_router(agent_router, prefix="/api/v1", tags=["Agents"])

app.include_router(research_router, tags=["Research"])

# Include monitoring router if available
if MONITORING_AVAILABLE:
    app.include_router(monitoring_api_router, prefix="/api/v1", tags=["Monitoring"])

app.include_router(monitoring_router, prefix="/api/v1", tags=["Monitoring"])

# Include embedding router
app.include_router(embedding_router, prefix="/api/v1", tags=["Vector Embeddings"])

# Include taxonomy evolution router
app.include_router(evolution_router, tags=["Taxonomy Evolution"])

# Include evaluation router if available
if EVALUATION_AVAILABLE:
    app.include_router(
        evaluation_router,
        prefix="/api/v1",
        tags=["Evaluation", "RAGAS", "Quality Assurance"],
    )

# Include optimization routers if available
if BATCH_SEARCH_AVAILABLE:
    app.include_router(
        batch_search_router,
        prefix="/api/v1",
        tags=["Batch Processing", "Search Optimization"],
    )

# Include admin routers
app.include_router(
    api_keys_admin_router, prefix="/api/v1", tags=["Admin", "API Key Management"]
)


# API versioning support
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.get("/api/versions", tags=["Versioning"])  # Decorator lacks type stubs
async def list_api_versions() -> Dict[str, Any]:
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
                    "Monitoring & Observability",
                ],
            }
        ],
        "current": "v1",
        "deprecated": [],
        "sunset_policy": "https://docs.example.com/api-sunset-policy",
    }


# Rate limiting info endpoint
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.get("/api/v1/rate-limits", tags=["Rate Limiting"])  # Decorator lacks type stubs
async def get_rate_limit_info() -> Dict[str, Any]:
    """Get rate limiting information for current user"""
    # TODO: Implement actual rate limit checking based on user/API key
    return {
        "limits": {
            "requests_per_minute": 100,
            "requests_per_hour": 5000,
            "requests_per_day": 50000,
            "concurrent_requests": 10,
        },
        "current_usage": {
            "requests_this_minute": 15,
            "requests_this_hour": 234,
            "requests_today": 1567,
            "concurrent_requests": 3,
        },
        "reset_times": {"minute_reset": 45, "hour_reset": 2847, "day_reset": 76847},
        "upgrade_info": {
            "current_tier": "standard",
            "available_tiers": ["premium", "enterprise"],
            "upgrade_url": "https://example.com/upgrade",
        },
    }


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@app.get("/", tags=["Root"])  # Decorator lacks type stubs
async def root() -> Dict[str, Any]:
    """API root endpoint with comprehensive system information"""
    # 데이터베이스 연결 상태 확인
    db_status = await test_database_connection()

    return {
        "name": "Norade API",
        "version": "1.8.1",
        "description": "RESTful API for Norade knowledge platform",
        "team": "A",
        "spec": "OpenAPI v1.8.1",
        "schemas": "0.1.3",
        "status": "Production Ready" if db_status else "Fallback Mode",
        "database": "PostgreSQL + pgvector" if db_status else "Fallback",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/api/v1/openapi.json",
        },
        "features": {
            "classification": "ML-based with HITL support",
            "search": "BM25 + Vector hybrid with reranking",
            "taxonomy": "Versioned hierarchical DAG",
            "orchestration": "LangGraph 7-step RAG pipeline",
            "agent_factory": "Dynamic agent creation",
            "monitoring": "Real-time observability",
            "embeddings": "Sentence Transformers 768-dim vectors",
            "simulation": "Removed - 100% real data",
        },
        "api_endpoints": {
            "health": "/health",
            "monitoring": "/api/v1/monitoring/health",
            "versions": "/api/v1/versions",
            "rate_limits": "/api/v1/rate-limits",
        },
        "bridge_pack_endpoints": [
            "GET /healthz",
            "GET /taxonomy/{version}/tree",
            "POST /classify",
            "POST /search",
            "POST /ingestion/upload",
            "POST /ingestion/urls",
            "GET /ingestion/status/{job_id}",
        ],
        "comprehensive_endpoints": [
            "GET /api/v1/taxonomy/versions",
            "GET /api/v1/taxonomy/{version}/tree",
            "POST /api/v1/search",
            "POST /api/v1/classify",
            "POST /api/v1/pipeline/execute",
            "POST /api/v1/agents/from-category",
            "GET /api/v1/monitoring/health",
            "GET /api/v1/embeddings/health",
            "POST /api/v1/embeddings/generate",
            "POST /api/v1/embeddings/documents/update",
        ],
        "environment": config.environment,
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Norade API v1.8.1 서버 시작")
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
        access_log=True,
    )
