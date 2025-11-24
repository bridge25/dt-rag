"""
Evolution History Service

Manages taxonomy version history, snapshots, rollback,
rate limiting, and background job management.

@CODE:TAXONOMY-EVOLUTION-001
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class EvolutionHistoryService:
    """
    Service for managing taxonomy evolution history.

    Provides:
    - Event recording and history retrieval
    - Snapshot and version management
    - Rollback functionality
    - Rate limiting for suggestions
    - Background job management
    """

    def __init__(self):
        """Initialize evolution history service."""
        # In-memory storage (production would use database)
        self._events: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._versions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self._jobs: Dict[str, Dict[str, Any]] = {}

    # ========================================================================
    # Event Recording
    # ========================================================================

    async def record_event(self, event: Dict[str, Any]) -> bool:
        """
        Record an evolution event to history.

        Args:
            event: Event dict with event_id, taxonomy_id, event_type, etc.

        Returns:
            True if successfully recorded
        """
        return await self._store_event(event)

    async def _store_event(self, event: Dict[str, Any]) -> bool:
        """Store event in storage."""
        taxonomy_id = event.get("taxonomy_id")
        if not taxonomy_id:
            return False

        event["recorded_at"] = datetime.utcnow()
        self._events[taxonomy_id].append(event)
        return True

    async def get_history(
        self,
        taxonomy_id: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve history for a taxonomy.

        Args:
            taxonomy_id: Taxonomy ID
            limit: Maximum events to return
            start_date: Filter events after this date
            end_date: Filter events before this date

        Returns:
            List of events
        """
        return await self._fetch_events(taxonomy_id, limit, start_date, end_date)

    async def _fetch_events(
        self,
        taxonomy_id: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch events from storage."""
        events = self._events.get(taxonomy_id, [])

        # Filter by date
        if start_date:
            events = [e for e in events if e.get("timestamp", datetime.min) >= start_date]
        if end_date:
            events = [e for e in events if e.get("timestamp", datetime.max) <= end_date]

        # Sort by timestamp descending
        events = sorted(events, key=lambda e: e.get("timestamp", datetime.min), reverse=True)

        return events[:limit]

    # ========================================================================
    # Snapshot Management
    # ========================================================================

    async def create_snapshot(
        self,
        taxonomy_id: str,
        categories: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a taxonomy snapshot.

        Args:
            taxonomy_id: Taxonomy ID
            categories: Current category list
            metadata: Additional metadata

        Returns:
            Snapshot ID
        """
        return await self._store_snapshot(taxonomy_id, categories, metadata)

    async def _store_snapshot(
        self,
        taxonomy_id: str,
        categories: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store snapshot in storage."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"

        snapshot = {
            "snapshot_id": snapshot_id,
            "taxonomy_id": taxonomy_id,
            "categories": categories,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
        }

        self._snapshots[snapshot_id] = snapshot
        return snapshot_id

    # ========================================================================
    # Version Management
    # ========================================================================

    async def create_version(
        self,
        taxonomy_id: str,
        categories: List[Dict[str, Any]],
        version_number: str,
        created_by: str,
    ) -> str:
        """
        Create a new taxonomy version.

        Args:
            taxonomy_id: Taxonomy ID
            categories: Category list for this version
            version_number: Semantic version number
            created_by: User who created the version

        Returns:
            Version ID
        """
        return await self._store_version(taxonomy_id, categories, version_number, created_by)

    async def _store_version(
        self,
        taxonomy_id: str,
        categories: List[Dict[str, Any]],
        version_number: str,
        created_by: str,
    ) -> str:
        """Store version in storage."""
        version_id = f"v_{uuid.uuid4().hex[:8]}"

        version = {
            "version_id": version_id,
            "taxonomy_id": taxonomy_id,
            "version_number": version_number,
            "categories": categories,
            "created_at": datetime.utcnow(),
            "created_by": created_by,
        }

        self._versions[taxonomy_id].append(version)
        return version_id

    async def get_version(
        self,
        taxonomy_id: str,
        version_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific version.

        Args:
            taxonomy_id: Taxonomy ID
            version_id: Version ID

        Returns:
            Version dict or None
        """
        return await self._fetch_version(taxonomy_id, version_id)

    async def _fetch_version(
        self,
        taxonomy_id: str,
        version_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch version from storage."""
        versions = self._versions.get(taxonomy_id, [])
        for v in versions:
            if v.get("version_id") == version_id:
                return v
        return None

    async def list_versions(self, taxonomy_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of a taxonomy.

        Args:
            taxonomy_id: Taxonomy ID

        Returns:
            List of version summaries
        """
        return await self._fetch_versions(taxonomy_id)

    async def _fetch_versions(self, taxonomy_id: str) -> List[Dict[str, Any]]:
        """Fetch all versions from storage."""
        versions = self._versions.get(taxonomy_id, [])
        return [
            {
                "version_id": v.get("version_id"),
                "version_number": v.get("version_number"),
                "created_at": v.get("created_at"),
                "created_by": v.get("created_by"),
            }
            for v in versions
        ]

    async def compare_versions(
        self,
        taxonomy_id: str,
        version_a: str,
        version_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two versions.

        Args:
            taxonomy_id: Taxonomy ID
            version_a: First version ID
            version_b: Second version ID

        Returns:
            Diff with added, removed, modified categories
        """
        v1 = await self._fetch_version(taxonomy_id, version_a)
        v2 = await self._fetch_version(taxonomy_id, version_b)

        if not v1 or not v2:
            return {"error": "Version not found"}

        cats_a = {c.get("id"): c for c in v1.get("categories", [])}
        cats_b = {c.get("id"): c for c in v2.get("categories", [])}

        added = [c for id, c in cats_b.items() if id not in cats_a]
        removed = [c for id, c in cats_a.items() if id not in cats_b]
        modified = [
            {"old": cats_a[id], "new": cats_b[id]}
            for id in cats_a
            if id in cats_b and cats_a[id] != cats_b[id]
        ]

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
        }

    # ========================================================================
    # Rollback
    # ========================================================================

    async def rollback_to_version(
        self,
        taxonomy_id: str,
        target_version: str,
        reason: Optional[str] = None,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """
        Rollback taxonomy to a previous version.

        Args:
            taxonomy_id: Taxonomy ID
            target_version: Version to rollback to
            reason: Reason for rollback
            create_backup: Whether to create backup before rollback

        Returns:
            Result dict with success status
        """
        # Get target version
        target = await self._fetch_version(taxonomy_id, target_version)
        if not target:
            return {"success": False, "error": "Version not found"}

        result = {
            "success": True,
            "rolled_back_to": target_version,
            "reason": reason,
        }

        # Create backup if requested
        if create_backup:
            # Get current state (latest version)
            versions = await self._fetch_versions(taxonomy_id)
            if versions:
                current = await self._fetch_version(taxonomy_id, versions[-1].get("version_id"))
                if current:
                    backup_id = await self.create_snapshot(
                        taxonomy_id,
                        current.get("categories", []),
                        {"reason": "pre-rollback backup"},
                    )
                    result["backup_snapshot"] = backup_id

        # Apply version
        await self._apply_version(taxonomy_id, target)

        # Record rollback event
        await self.record_event({
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "taxonomy_id": taxonomy_id,
            "event_type": "rollback",
            "timestamp": datetime.utcnow(),
            "actor": "system",
            "changes": {
                "target_version": target_version,
                "reason": reason,
            },
        })

        return result

    async def _apply_version(
        self,
        taxonomy_id: str,
        version: Dict[str, Any],
    ) -> bool:
        """Apply a version to become current state."""
        # In production, this would update the database
        return True

    # ========================================================================
    # Rate Limiting
    # ========================================================================

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if action is allowed under rate limit.

        Args:
            key: Rate limit key (e.g., "suggestions:tax_main")
            limit: Maximum requests in window
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old entries
        self._rate_limits[key] = [
            ts for ts in self._rate_limits[key]
            if ts > window_start
        ]

        # Check limit
        if len(self._rate_limits[key]) >= limit:
            return False

        # Record this request
        self._rate_limits[key].append(now)
        return True

    def get_rate_limit_status(self, key: str) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Args:
            key: Rate limit key

        Returns:
            Status dict with remaining count and reset time
        """
        timestamps = self._rate_limits.get(key, [])
        now = datetime.utcnow()

        # Assume 1 hour window
        window_start = now - timedelta(hours=1)
        recent = [ts for ts in timestamps if ts > window_start]

        oldest = min(recent) if recent else now
        reset_at = oldest + timedelta(hours=1)

        return {
            "remaining": max(0, 10 - len(recent)),  # Assume limit of 10
            "used": len(recent),
            "reset_at": reset_at,
        }

    # ========================================================================
    # Background Jobs
    # ========================================================================

    async def queue_generation_job(
        self,
        taxonomy_id: str,
        document_ids: List[str],
        config: Dict[str, Any],
    ) -> str:
        """
        Queue a taxonomy generation job.

        Args:
            taxonomy_id: Taxonomy ID
            document_ids: Documents to process
            config: Generation configuration

        Returns:
            Job ID
        """
        return await self._enqueue_job({
            "type": "generation",
            "taxonomy_id": taxonomy_id,
            "document_ids": document_ids,
            "config": config,
        })

    async def _enqueue_job(self, job_data: Dict[str, Any]) -> str:
        """Enqueue job to storage."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        job = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "created_at": datetime.utcnow(),
            **job_data,
        }

        self._jobs[job_id] = job
        return job_id

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job status dict
        """
        return await self._fetch_job_status(job_id)

    async def _fetch_job_status(self, job_id: str) -> Dict[str, Any]:
        """Fetch job status from storage."""
        return self._jobs.get(job_id, {"job_id": job_id, "status": "not_found"})

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled
        """
        return await self._cancel_job(job_id)

    async def _cancel_job(self, job_id: str) -> bool:
        """Cancel job in storage."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "cancelled"
            return True
        return False


# ============================================================================
# Singleton Instance
# ============================================================================

_history_service: Optional[EvolutionHistoryService] = None


def get_history_service() -> EvolutionHistoryService:
    """Get or create history service singleton."""
    global _history_service

    if _history_service is None:
        _history_service = EvolutionHistoryService()

    return _history_service
