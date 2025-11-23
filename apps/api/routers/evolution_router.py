"""
Taxonomy Evolution Router

API endpoints for ML-powered taxonomy generation, evolution suggestions,
and analytics.

@CODE:TAXONOMY-EVOLUTION-001
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends

from ..models.evolution_models import (
    GenerateRequest,
    GeneratorConfig,
    GenerationAlgorithm,
    Granularity,
    ProposalStatus,
    SuggestionType,
    ProposedCategory,
    TaxonomyProposal,
    TaxonomyProposalResponse,
    ProposedCategoryResponse,
    GenerateStatusResponse,
    EvolutionSuggestion,
    EvolutionSuggestionResponse,
    SuggestionsListResponse,
    AcceptProposalRequest,
    AcceptSuggestionRequest,
    RejectSuggestionRequest,
    AnalyticsResponse,
)
from ..services.taxonomy_evolution_service import (
    TaxonomyEvolutionService,
    get_evolution_service,
)
from ..embedding_service import embedding_service
from ..database import db_manager, text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/taxonomy/evolution", tags=["Taxonomy Evolution"])


# ============================================================================
# In-memory storage for proposals and suggestions (temporary)
# In production, these would be stored in the database
# ============================================================================

_proposals: Dict[str, TaxonomyProposal] = {}
_suggestions: Dict[str, List[EvolutionSuggestion]] = {}


# ============================================================================
# Helper Functions
# ============================================================================


def get_proposal_by_id(proposal_id: str) -> Optional[TaxonomyProposal]:
    """Get a proposal by ID from storage"""
    return _proposals.get(proposal_id)


def get_suggestions_for_taxonomy(taxonomy_id: str) -> List[EvolutionSuggestion]:
    """Get suggestions for a taxonomy"""
    return _suggestions.get(taxonomy_id, [])


def get_suggestion_by_id(
    taxonomy_id: str, suggestion_id: str
) -> Optional[EvolutionSuggestion]:
    """Get a specific suggestion by ID"""
    suggestions = _suggestions.get(taxonomy_id, [])
    for sug in suggestions:
        if sug.id == suggestion_id:
            return sug
    return None


async def apply_proposal(
    proposal: TaxonomyProposal,
    modifications: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply a proposal to create a new taxonomy"""
    # In production, this would:
    # 1. Create taxonomy nodes in the database
    # 2. Apply any modifications
    # 3. Set the version
    taxonomy_id = f"tax_{proposal.proposal_id.split('_')[1]}"
    return {
        "taxonomy_id": taxonomy_id,
        "success": True,
        "categories_created": len(proposal.categories),
    }


async def apply_suggestion(
    suggestion: EvolutionSuggestion,
) -> Dict[str, Any]:
    """Apply a suggestion to modify taxonomy"""
    return {
        "applied": True,
        "affected_documents": suggestion.affected_documents,
    }


async def reject_suggestion(
    suggestion: EvolutionSuggestion,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Reject a suggestion"""
    suggestion.status = "rejected"
    return {"acknowledged": True, "reason": reason}


async def get_taxonomy_analytics(
    taxonomy_id: str,
    period: str,
) -> Dict[str, Any]:
    """Get analytics for a taxonomy using metrics service"""
    from ..services.taxonomy_metrics_service import get_metrics_service
    from ..models.metrics_models import AggregationPeriod

    try:
        metrics_service = get_metrics_service()

        # Map string period to enum
        period_enum = AggregationPeriod(period)

        # Get dashboard summary
        summary = await metrics_service.get_dashboard_summary(taxonomy_id, period_enum)

        # Get health metrics
        health = await metrics_service.get_taxonomy_health(taxonomy_id, period_enum)

        # Get zero result patterns
        zero_patterns = await metrics_service.get_zero_result_patterns(taxonomy_id, min_occurrences=3)

        return {
            "taxonomy_id": taxonomy_id,
            "period": period,
            "usage_stats": {
                "total_queries": summary.get("total_searches", 0),
                "total_events": summary.get("total_events", 0),
                "category_views": summary.get("total_category_views", 0),
                "unique_users": summary.get("unique_users", 0),
            },
            "effectiveness_metrics": {
                "hit_rate": 1.0 - health.zero_result_rate,
                "zero_result_rate": health.zero_result_rate,
                "avg_response_time_ms": summary.get("avg_response_time_ms", 0.0),
                "active_categories": health.active_categories,
            },
            "evolution_history": [],
            "suggestions_summary": {
                "pending": len(_suggestions.get(taxonomy_id, [])),
                "potential_categories": len(zero_patterns),
            },
        }

    except Exception as e:
        logger.warning(f"Failed to get analytics: {e}")
        return {
            "taxonomy_id": taxonomy_id,
            "period": period,
            "usage_stats": {"total_queries": 0},
            "effectiveness_metrics": {"hit_rate": 0.0},
            "evolution_history": [],
            "suggestions_summary": {"pending": 0},
        }


async def get_documents_for_generation(
    document_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Fetch documents from database for taxonomy generation"""
    try:
        async with db_manager.async_session() as session:
            if document_ids:
                ids_str = ", ".join([f"'{doc_id}'" for doc_id in document_ids])
                query = text(
                    f"""
                    SELECT doc_id, title, content
                    FROM documents
                    WHERE doc_id IN ({ids_str})
                """
                )
            else:
                query = text(
                    """
                    SELECT doc_id, title, content
                    FROM documents
                    LIMIT 1000
                """
                )

            result = await session.execute(query)
            rows = result.fetchall()

            return [
                {
                    "doc_id": row[0],
                    "title": row[1] or "",
                    "content": row[2] or "",
                }
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Failed to fetch documents: {e}")
        return []


def convert_category_to_response(
    category: ProposedCategory,
) -> ProposedCategoryResponse:
    """Convert ProposedCategory to response model"""
    return ProposedCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        parent_id=category.parent_id,
        confidence_score=category.confidence_score,
        document_count=category.document_count,
        sample_document_ids=category.sample_document_ids,
        keywords=category.keywords,
        children=[convert_category_to_response(c) for c in category.children],
    )


def convert_proposal_to_response(
    proposal: TaxonomyProposal,
) -> TaxonomyProposalResponse:
    """Convert TaxonomyProposal to response model"""
    return TaxonomyProposalResponse(
        proposal_id=proposal.proposal_id,
        status=proposal.status,
        categories=[convert_category_to_response(c) for c in proposal.categories],
        total_documents=proposal.total_documents,
        processing_time_seconds=proposal.processing_time_seconds,
        created_at=proposal.created_at,
        completed_at=proposal.completed_at,
        error_message=proposal.error_message,
        config={
            "max_depth": proposal.config.max_depth,
            "min_documents_per_category": proposal.config.min_documents_per_category,
            "granularity": proposal.config.granularity.value,
            "algorithm": proposal.config.algorithm.value,
        },
    )


def convert_suggestion_to_response(
    suggestion: EvolutionSuggestion,
) -> EvolutionSuggestionResponse:
    """Convert EvolutionSuggestion to response model"""
    return EvolutionSuggestionResponse(
        id=suggestion.id,
        suggestion_type=suggestion.suggestion_type,
        confidence=suggestion.confidence,
        impact_score=suggestion.impact_score,
        affected_documents=suggestion.affected_documents,
        details=suggestion.details,
        created_at=suggestion.created_at,
        expires_at=suggestion.expires_at,
        status=suggestion.status,
    )


# ============================================================================
# API Endpoints
# ============================================================================


class AnalyticsPeriod(str, Enum):
    """Valid analytics periods"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@router.post(
    "/generate",
    response_model=TaxonomyProposalResponse,
    summary="Generate taxonomy from documents",
    description="Analyze documents and generate a taxonomy proposal using ML clustering.",
)
async def generate_taxonomy(
    request: GenerateRequest,
) -> TaxonomyProposalResponse:
    """
    Generate a taxonomy proposal from documents.

    Uses document embeddings and clustering to automatically discover
    category structures from document content.
    """
    # Build config from request
    config = GeneratorConfig(
        max_depth=request.max_depth,
        min_documents_per_category=request.min_documents_per_category,
        granularity=request.granularity,
        domain_hints=request.domain_hints,
        algorithm=request.algorithm,
        n_clusters=request.n_clusters,
    )

    # Fetch documents
    documents = await get_documents_for_generation(request.document_ids)

    # Get or create evolution service
    evolution_service = get_evolution_service(embedding_service)

    # Generate taxonomy
    proposal = await evolution_service.generate_taxonomy(
        documents=documents,
        config=config,
    )

    # Store proposal
    _proposals[proposal.proposal_id] = proposal

    return convert_proposal_to_response(proposal)


@router.get(
    "/generate/{proposal_id}",
    response_model=TaxonomyProposalResponse,
    summary="Get taxonomy proposal",
    description="Get details of a taxonomy generation proposal.",
)
async def get_proposal(
    proposal_id: str,
) -> TaxonomyProposalResponse:
    """Get a taxonomy proposal by ID"""
    proposal = get_proposal_by_id(proposal_id)

    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return convert_proposal_to_response(proposal)


@router.post(
    "/generate/{proposal_id}/accept",
    summary="Accept taxonomy proposal",
    description="Accept and apply a taxonomy proposal to create a new taxonomy.",
)
async def accept_proposal(
    proposal_id: str,
    request: AcceptProposalRequest,
) -> Dict[str, Any]:
    """Accept and apply a taxonomy proposal"""
    proposal = get_proposal_by_id(proposal_id)

    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal.status != ProposalStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot accept proposal with status: {proposal.status}",
        )

    result = await apply_proposal(
        proposal=proposal,
        modifications=request.modifications,
        version=request.taxonomy_version,
    )

    # Update proposal status
    proposal.status = ProposalStatus.ACCEPTED

    return result


@router.get(
    "/{taxonomy_id}/suggestions",
    response_model=SuggestionsListResponse,
    summary="List evolution suggestions",
    description="Get list of evolution suggestions for a taxonomy.",
)
async def list_suggestions(
    taxonomy_id: str,
) -> SuggestionsListResponse:
    """Get evolution suggestions for a taxonomy"""
    suggestions = get_suggestions_for_taxonomy(taxonomy_id)

    pending_count = sum(1 for s in suggestions if s.status == "pending")

    return SuggestionsListResponse(
        suggestions=[convert_suggestion_to_response(s) for s in suggestions],
        total_count=len(suggestions),
        pending_count=pending_count,
        summary={
            "by_type": {},
            "avg_confidence": 0.0,
        },
    )


@router.post(
    "/{taxonomy_id}/suggestions/{suggestion_id}/accept",
    summary="Accept evolution suggestion",
    description="Accept and apply an evolution suggestion.",
)
async def accept_suggestion_endpoint(
    taxonomy_id: str,
    suggestion_id: str,
    request: AcceptSuggestionRequest,
) -> Dict[str, Any]:
    """Accept and apply an evolution suggestion"""
    suggestion = get_suggestion_by_id(taxonomy_id, suggestion_id)

    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    result = await apply_suggestion(suggestion)

    suggestion.status = "accepted"

    return result


@router.post(
    "/{taxonomy_id}/suggestions/{suggestion_id}/reject",
    summary="Reject evolution suggestion",
    description="Reject an evolution suggestion.",
)
async def reject_suggestion_endpoint(
    taxonomy_id: str,
    suggestion_id: str,
    request: RejectSuggestionRequest,
) -> Dict[str, Any]:
    """Reject an evolution suggestion"""
    suggestion = get_suggestion_by_id(taxonomy_id, suggestion_id)

    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    result = await reject_suggestion(suggestion, request.reason)

    return result


@router.get(
    "/{taxonomy_id}/analytics",
    response_model=AnalyticsResponse,
    summary="Get taxonomy analytics",
    description="Get usage analytics and effectiveness metrics for a taxonomy.",
)
async def get_analytics(
    taxonomy_id: str,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.WEEK, description="Analytics period"),
) -> AnalyticsResponse:
    """Get analytics for a taxonomy"""
    analytics = await get_taxonomy_analytics(taxonomy_id, period.value)

    return AnalyticsResponse(
        taxonomy_id=analytics["taxonomy_id"],
        period=analytics["period"],
        usage_stats=analytics["usage_stats"],
        effectiveness_metrics=analytics["effectiveness_metrics"],
        evolution_history=analytics["evolution_history"],
        suggestions_summary=analytics["suggestions_summary"],
    )
