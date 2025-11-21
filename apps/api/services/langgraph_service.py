"""
LangGraph Service - Wrapper for 7-Step RAG Pipeline

Integrates existing LangGraph pipeline from apps/orchestration into main API.
This service provides a thin wrapper to convert between API models and pipeline models.

@CODE:API-001
"""

import logging
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add orchestration module to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from apps.orchestration.src.langgraph_pipeline import (
    LangGraphPipeline,
    PipelineRequest as LangGraphRequest,
    PipelineResponse as LangGraphResponse,
    get_pipeline,
)

logger = logging.getLogger(__name__)


class LangGraphService:
    """
    Service wrapper for LangGraph 7-step RAG pipeline

    Provides integration between FastAPI orchestration router and
    the standalone LangGraph pipeline implementation.
    """

    def __init__(self) -> None:
        """Initialize LangGraph service with pipeline instance"""
        self.pipeline: LangGraphPipeline = get_pipeline()
        logger.info("LangGraphService initialized with 7-step pipeline")

    async def execute_pipeline(
        self,
        query: str,
        taxonomy_version: Optional[str] = None,
        canonical_filter: Optional[List[List[str]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the 7-step RAG pipeline

        Args:
            query: User query string
            taxonomy_version: Taxonomy version to use (default: "1.0.0")
            canonical_filter: List of canonical paths for filtering
            options: Additional pipeline options

        Returns:
            Dictionary with answer, sources, confidence, latency, cost, etc.

        Raises:
            TimeoutError: If pipeline exceeds timeout
            Exception: For other pipeline execution errors
        """
        try:
            # Build pipeline request
            pipeline_request = LangGraphRequest(
                query=query,
                taxonomy_version=taxonomy_version or "1.0.0",
                canonical_filter=canonical_filter,
                options=options or {},
            )

            # Execute pipeline
            logger.info(f"Executing pipeline for query: {query[:100]}...")
            result: LangGraphResponse = await self.pipeline.execute(pipeline_request)

            # Convert to dict for API response
            response_dict = {
                "answer": result.answer,
                "sources": result.sources,
                "confidence": result.confidence,
                "cost": result.cost,
                "latency": result.latency,
                "taxonomy_version": result.taxonomy_version,
                "intent": result.intent,
                "pipeline_metadata": {
                    "step_timings": result.step_timings,
                    "steps_executed": list(result.step_timings.keys()),
                },
            }

            logger.info(
                f"Pipeline completed: latency={result.latency:.3f}s, "
                f"confidence={result.confidence:.3f}, sources={len(result.sources)}"
            )

            return response_dict

        except TimeoutError as e:
            logger.error(f"Pipeline timeout: {e}")
            raise

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            raise


# Singleton instance
_langgraph_service: Optional[LangGraphService] = None


def get_langgraph_service() -> LangGraphService:
    """
    Get singleton instance of LangGraphService

    Returns:
        LangGraphService instance
    """
    global _langgraph_service

    if _langgraph_service is None:
        _langgraph_service = LangGraphService()

    return _langgraph_service
