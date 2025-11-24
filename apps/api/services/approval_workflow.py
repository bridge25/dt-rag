"""
Approval Workflow Service

Manages admin approval workflow for taxonomy evolution suggestions.

@CODE:TAXONOMY-EVOLUTION-001
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ApprovalWorkflowService:
    """
    Service for managing approval workflows.

    Provides:
    - Approval request creation
    - Approve/reject actions
    - Pending request management
    - Auto-approval logic
    """

    def __init__(self):
        """Initialize approval workflow service."""
        # In-memory storage (production would use database)
        self._requests: Dict[str, Dict[str, Any]] = {}
        self._by_taxonomy: Dict[str, List[str]] = defaultdict(list)

    # ========================================================================
    # Request Management
    # ========================================================================

    async def create_request(
        self,
        suggestion_id: str,
        taxonomy_id: str,
        request_type: str,
        details: Dict[str, Any],
        requester: str = "system",
    ) -> str:
        """
        Create an approval request.

        Args:
            suggestion_id: Related suggestion ID
            taxonomy_id: Taxonomy ID
            request_type: Type of request (merge, split, new_category)
            details: Request details
            requester: Who created the request

        Returns:
            Request ID
        """
        return await self._store_request(
            suggestion_id, taxonomy_id, request_type, details, requester
        )

    async def _store_request(
        self,
        suggestion_id: str,
        taxonomy_id: str,
        request_type: str,
        details: Dict[str, Any],
        requester: str,
    ) -> str:
        """Store request in storage."""
        request_id = f"req_{uuid.uuid4().hex[:12]}"

        request = {
            "request_id": request_id,
            "suggestion_id": suggestion_id,
            "taxonomy_id": taxonomy_id,
            "request_type": request_type,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "requester": requester,
            "details": details,
            "history": [],
        }

        self._requests[request_id] = request
        self._by_taxonomy[taxonomy_id].append(request_id)
        return request_id

    async def _fetch_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Fetch request from storage."""
        return self._requests.get(request_id)

    async def _update_request(
        self,
        request_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update request in storage."""
        if request_id not in self._requests:
            return False

        self._requests[request_id].update(updates)
        return True

    # ========================================================================
    # Approval Actions
    # ========================================================================

    async def approve(
        self,
        request_id: str,
        approver: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a pending request.

        Args:
            request_id: Request ID
            approver: User who approved
            comment: Optional comment

        Returns:
            Result dict with status
        """
        request = await self._fetch_request(request_id)
        if not request:
            return {"status": "error", "message": "Request not found"}

        if request.get("status") != "pending":
            return {"status": "error", "message": "Request not pending"}

        # Update request
        updates = {
            "status": "approved",
            "approved_at": datetime.utcnow(),
            "approved_by": approver,
        }

        # Add to history
        history_entry = {
            "action": "approved",
            "actor": approver,
            "timestamp": datetime.utcnow(),
            "comment": comment,
        }
        request.get("history", []).append(history_entry)
        updates["history"] = request.get("history", [])

        await self._update_request(request_id, updates)

        return {
            "status": "approved",
            "request_id": request_id,
            "approved_by": approver,
        }

    async def reject(
        self,
        request_id: str,
        rejector: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reject a pending request.

        Args:
            request_id: Request ID
            rejector: User who rejected
            reason: Rejection reason

        Returns:
            Result dict with status
        """
        request = await self._fetch_request(request_id)
        if not request:
            return {"status": "error", "message": "Request not found"}

        if request.get("status") != "pending":
            return {"status": "error", "message": "Request not pending"}

        # Update request
        updates = {
            "status": "rejected",
            "rejected_at": datetime.utcnow(),
            "rejected_by": rejector,
            "rejection_reason": reason,
        }

        # Add to history
        history_entry = {
            "action": "rejected",
            "actor": rejector,
            "timestamp": datetime.utcnow(),
            "reason": reason,
        }
        request.get("history", []).append(history_entry)
        updates["history"] = request.get("history", [])

        await self._update_request(request_id, updates)

        return {
            "status": "rejected",
            "request_id": request_id,
            "rejected_by": rejector,
            "reason": reason,
        }

    # ========================================================================
    # Query Methods
    # ========================================================================

    async def list_pending(
        self,
        taxonomy_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List pending approval requests.

        Args:
            taxonomy_id: Optional filter by taxonomy

        Returns:
            List of pending requests
        """
        return await self._fetch_pending(taxonomy_id)

    async def _fetch_pending(
        self,
        taxonomy_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch pending requests from storage."""
        if taxonomy_id:
            request_ids = self._by_taxonomy.get(taxonomy_id, [])
            requests = [self._requests.get(rid) for rid in request_ids]
        else:
            requests = list(self._requests.values())

        return [r for r in requests if r and r.get("status") == "pending"]

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get request by ID.

        Args:
            request_id: Request ID

        Returns:
            Request dict or None
        """
        return await self._fetch_request(request_id)

    # ========================================================================
    # Auto-Approval Logic
    # ========================================================================

    def should_auto_approve(
        self,
        confidence: float,
        impact_score: float,
        auto_approve_threshold: float = 0.9,
        max_impact_for_auto: float = 0.5,
    ) -> bool:
        """
        Determine if a suggestion should be auto-approved.

        Args:
            confidence: Suggestion confidence score
            impact_score: Impact score
            auto_approve_threshold: Minimum confidence for auto-approval
            max_impact_for_auto: Maximum impact allowed for auto-approval

        Returns:
            True if should auto-approve
        """
        # Only auto-approve high confidence, low impact suggestions
        return (
            confidence >= auto_approve_threshold and
            impact_score <= max_impact_for_auto
        )

    def calculate_priority(
        self,
        request: Dict[str, Any],
    ) -> float:
        """
        Calculate priority score for a request.

        Higher priority = should be reviewed sooner.

        Args:
            request: Request dict

        Returns:
            Priority score (0-1)
        """
        details = request.get("details", {})

        # Factors that increase priority
        impact = details.get("impact", 0)
        age_hours = (datetime.utcnow() - request.get("created_at", datetime.utcnow())).total_seconds() / 3600

        # Impact-based priority (higher impact = higher priority)
        impact_priority = min(1.0, impact / 100)

        # Age-based urgency (older = higher priority)
        age_priority = min(1.0, age_hours / 168)  # Max out at 1 week

        # Combined score
        return (impact_priority * 0.6) + (age_priority * 0.4)


# ============================================================================
# Singleton Instance
# ============================================================================

_approval_service: Optional[ApprovalWorkflowService] = None


def get_approval_service() -> ApprovalWorkflowService:
    """Get or create approval service singleton."""
    global _approval_service

    if _approval_service is None:
        _approval_service = ApprovalWorkflowService()

    return _approval_service
