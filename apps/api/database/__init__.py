"""
Database Package - Modular database layer for Norade.

This package provides a clean, modular structure for database operations:
- connection: Database connection and type utilities
- models: ORM models
- daos: Data Access Objects
- utils: Utility classes (BM25, Embedding, Reranking)

@CODE:DATABASE-PKG-000

Usage:
    from apps.api.database import (
        # Connection
        engine, async_session, Base, DATABASE_URL, get_async_session,

        # Models
        Document, DocumentChunk, Embedding, DocTaxonomy,
        TaxonomyNode, TaxonomyEdge, TaxonomyMigration,
        Agent, BackgroundTask, CoverageHistory,
        CaseBank, CaseBankArchive, ExecutionLog,
        QTableEntry,

        # DAOs
        SearchDAO, TaxonomyDAO, ClassifyDAO, QTableDAO,
        DatabaseManager, db_manager,

        # Utils
        BM25Scorer, EmbeddingService, CrossEncoderReranker,
    )
"""

# Connection exports
from .connection import (
    engine,
    async_session,
    Base,
    DATABASE_URL,
    get_async_session,
    text,
    JSONType,
    ArrayType,
    UUIDType,
    get_json_type,
    get_array_type,
    get_vector_type,
    get_uuid_type,
    PGVECTOR_AVAILABLE,
)

# Model exports
from .models import (
    # Document models
    Document,
    DocumentChunk,
    Embedding,
    DocTaxonomy,
    # Taxonomy models
    TaxonomyNode,
    TaxonomyEdge,
    TaxonomyMigration,
    # Agent models
    Agent,
    BackgroundTask,
    CoverageHistory,
    # CaseBank models
    CaseBank,
    CaseBankArchive,
    ExecutionLog,
    # Q-Table models
    QTableEntry,
)

# DAO exports
from .daos import (
    SearchDAO,
    TaxonomyDAO,
    ClassifyDAO,
    QTableDAO,
    DatabaseManager,
    db_manager,
)

# Utility exports
from .utils import (
    BM25Scorer,
    EmbeddingService,
    CrossEncoderReranker,
)

# BM25 constants for backward compatibility
from .utils.bm25_scorer import BM25_K1, BM25_B
from .utils.reranker import BM25_WEIGHT, VECTOR_WEIGHT

# Additional exports for backward compatibility
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536

# Feature flag for persistent Q-Table
USE_PERSISTENT_QTABLE = os.getenv("USE_PERSISTENT_QTABLE", "false").lower() == "true"


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

async def init_database() -> bool:
    """Initialize database."""
    return await db_manager.init_database()


async def test_database_connection() -> bool:
    """Test database connection."""
    return await db_manager.test_connection()


async def setup_search_system() -> bool:
    """Setup search system."""
    try:
        async with db_manager.async_session() as session:
            init_result = await init_database()
            if not init_result:
                return False

            optimize_result = await SearchDAO.optimize_search_indices(session)
            if not optimize_result.get("success"):
                logger.warning(f"Index optimization failed: {optimize_result.get('error')}")

            stats = await SearchDAO.get_search_analytics(session)
            if stats.get("statistics", {}).get("total_chunks", 0) == 0:
                logger.info("No chunks found. Consider ingesting documents.")

            logger.info("Search system setup complete")
            return True

    except Exception as e:
        logger.error(f"Search system setup failed: {e}")
        return False


async def get_search_performance_metrics() -> Dict[str, Any]:
    """Get search performance metrics."""
    try:
        async with db_manager.async_session() as session:
            analytics = await SearchDAO.get_search_analytics(session)
            stats = analytics.get("statistics", {})
            total_chunks = stats.get("total_chunks", 0)
            embedded_chunks = stats.get("embedded_chunks", 0)

            performance = {
                "embedding_coverage": (
                    (embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0
                ),
                "search_readiness": embedded_chunks > 0 and total_chunks > 0,
                "bm25_ready": total_chunks > 0,
                "vector_ready": embedded_chunks > 0,
                "hybrid_ready": embedded_chunks > 0 and total_chunks > 0,
                "index_status": "optimized" if total_chunks > 0 else "empty",
                "api_status": "enabled" if OPENAI_API_KEY else "disabled",
            }

            recommendations = []
            if performance["embedding_coverage"] < 100:
                recommendations.append("Some chunks are missing embeddings.")
            if not performance["api_status"] == "enabled":
                recommendations.append("Set OpenAI API key for high-quality embeddings.")
            if total_chunks == 0:
                recommendations.append("Add documents to build searchable content.")

            return {
                "performance": performance,
                "analytics": analytics,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        return {"error": str(e), "performance": {}, "analytics": {}, "recommendations": []}


async def optimize_execution_log_indices(session: Any) -> Dict[str, Any]:
    """ExecutionLog table index optimization."""
    from sqlalchemy import text as sql_text
    try:
        optimization_queries = [
            "CREATE INDEX IF NOT EXISTS idx_execution_log_case_id ON execution_log(case_id)",
            "CREATE INDEX IF NOT EXISTS idx_execution_log_created_at ON execution_log(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_execution_log_success ON execution_log(success)",
        ]
        created_indices = []
        for query in optimization_queries:
            try:
                await session.execute(sql_text(query))
                index_name = query.split("idx_")[1].split(" ")[0] if "idx_" in query else "unknown"
                created_indices.append(index_name)
            except Exception as e:
                logger.warning(f"ExecutionLog index creation failed: {e}")
        await session.commit()
        return {"success": True, "indices_created": created_indices}
    except Exception as e:
        logger.error(f"ExecutionLog index optimization failed: {e}")
        return {"success": False, "error": str(e), "indices_created": []}


async def optimize_casebank_indices(session: Any) -> Dict[str, Any]:
    """CaseBank table index optimization."""
    from sqlalchemy import text as sql_text
    try:
        optimization_queries = [
            "CREATE INDEX IF NOT EXISTS idx_casebank_status ON case_bank(status)",
            "CREATE INDEX IF NOT EXISTS idx_casebank_version ON case_bank(version DESC)",
            "CREATE INDEX IF NOT EXISTS idx_casebank_updated_at ON case_bank(updated_at DESC)",
        ]
        created_indices = []
        for query in optimization_queries:
            try:
                await session.execute(sql_text(query))
                index_name = query.split("idx_")[1].split(" ")[0] if "idx_" in query else "unknown"
                created_indices.append(index_name)
            except Exception as e:
                logger.warning(f"CaseBank index creation failed: {e}")
        await session.commit()
        return {"success": True, "indices_created": created_indices}
    except Exception as e:
        logger.error(f"CaseBank index optimization failed: {e}")
        return {"success": False, "error": str(e), "indices_created": []}


# ─────────────────────────────────────────────────────────────────────────────
# Search Metrics
# ─────────────────────────────────────────────────────────────────────────────

class SearchMetrics:
    """Search performance metrics collection."""

    def __init__(self) -> None:
        self.search_latencies: List[float] = []
        self.search_counts: Dict[str, int] = {"bm25": 0, "vector": 0, "hybrid": 0}
        self.error_counts: int = 0
        self.last_reset: datetime = datetime.utcnow()

    def record_search(self, search_type: str, latency: float, error: bool = False) -> None:
        self.search_latencies.append(latency)
        self.search_counts[search_type] = self.search_counts.get(search_type, 0) + 1
        if error:
            self.error_counts += 1
        if len(self.search_latencies) > 1000:
            self.search_latencies = self.search_latencies[-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        if not self.search_latencies:
            return {"no_data": True}
        return {
            "avg_latency": sum(self.search_latencies) / len(self.search_latencies),
            "p95_latency": sorted(self.search_latencies)[int(len(self.search_latencies) * 0.95)]
                if len(self.search_latencies) > 20 else max(self.search_latencies),
            "total_searches": sum(self.search_counts.values()),
            "search_counts": self.search_counts,
            "error_rate": self.error_counts / max(1, sum(self.search_counts.values())),
            "period_start": self.last_reset.isoformat(),
        }

    def reset(self) -> None:
        self.search_latencies = []
        self.search_counts = {"bm25": 0, "vector": 0, "hybrid": 0}
        self.error_counts = 0
        self.last_reset = datetime.utcnow()


# Global metrics collector
search_metrics = SearchMetrics()


__all__ = [
    # Connection
    "engine",
    "async_session",
    "Base",
    "DATABASE_URL",
    "get_async_session",
    "text",
    "JSONType",
    "ArrayType",
    "UUIDType",
    "get_json_type",
    "get_array_type",
    "get_vector_type",
    "get_uuid_type",
    "PGVECTOR_AVAILABLE",
    # Document models
    "Document",
    "DocumentChunk",
    "Embedding",
    "DocTaxonomy",
    # Taxonomy models
    "TaxonomyNode",
    "TaxonomyEdge",
    "TaxonomyMigration",
    # Agent models
    "Agent",
    "BackgroundTask",
    "CoverageHistory",
    # CaseBank models
    "CaseBank",
    "CaseBankArchive",
    "ExecutionLog",
    # Q-Table models
    "QTableEntry",
    # DAOs
    "SearchDAO",
    "TaxonomyDAO",
    "ClassifyDAO",
    "QTableDAO",
    "DatabaseManager",
    "db_manager",
    # Utils
    "BM25Scorer",
    "EmbeddingService",
    "CrossEncoderReranker",
    # Constants
    "BM25_K1",
    "BM25_B",
    "BM25_WEIGHT",
    "VECTOR_WEIGHT",
    "OPENAI_API_KEY",
    "OPENAI_EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS",
    "USE_PERSISTENT_QTABLE",
    # Functions
    "init_database",
    "test_database_connection",
    "setup_search_system",
    "get_search_performance_metrics",
    "optimize_execution_log_indices",
    "optimize_casebank_indices",
    # Metrics
    "SearchMetrics",
    "search_metrics",
]
