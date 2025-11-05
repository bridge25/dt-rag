# @SPEC:CONSOLIDATION-001 @IMPL:CONSOLIDATION-001:0.1

import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import json
import numpy as np

logger = logging.getLogger(__name__)


class ConsolidationPolicy:
    """
    Memory Consolidation Policy for automatic CaseBank management.

    Implements:
    - Low-performance case removal
    - Duplicate case merging
    - Inactive case archiving
    - Dry-run mode
    """

    def __init__(self, db_session: AsyncSession, dry_run: bool = False):
        """
        Initialize Consolidation Policy.

        Args:
            db_session: Async database session
            dry_run: If True, simulate without actual changes
        """
        self.db = db_session
        self.dry_run = dry_run
        self.removed_cases: list[str] = []
        self.merged_cases: list[str] = []
        self.archived_cases: list[str] = []

    async def run_consolidation(
        self,
        low_perf_threshold: float = 30.0,
        similarity_threshold: float = 0.95,
        inactive_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Run full consolidation policy.

        Args:
            low_perf_threshold: Success rate threshold for removal (default: 30%)
            similarity_threshold: Vector similarity for duplicate detection (default: 0.95)
            inactive_days: Days of inactivity for archiving (default: 90)

        Returns:
            Consolidation results dict
        """
        logger.info(
            f"Starting consolidation (dry_run={self.dry_run}): "
            f"low_perf={low_perf_threshold}%, similarity={similarity_threshold}, "
            f"inactive={inactive_days} days"
        )

        removed = await self.remove_low_performance_cases(low_perf_threshold)
        merged = await self.merge_duplicate_cases(similarity_threshold)
        archived = await self.archive_inactive_cases(inactive_days)

        results = {
            "removed_cases": len(removed),
            "merged_cases": len(merged),
            "archived_cases": len(archived),
            "dry_run": self.dry_run,
            "details": {
                "removed": removed,
                "merged": merged,
                "archived": archived,
            },
        }

        logger.info(
            f"Consolidation complete: removed={len(removed)}, "
            f"merged={len(merged)}, archived={len(archived)}"
        )

        return results

    async def remove_low_performance_cases(self, threshold: float = 30.0) -> List[str]:
        """
        Remove (archive) low-performance cases.

        Criteria:
        - success_rate < threshold
        - usage_count > 10 (has sufficient data)
        - usage_count < 500 (not heavily used)
        - status = 'active'

        Args:
            threshold: Success rate threshold (default: 30%)

        Returns:
            List of archived case IDs
        """
        from apps.api.database import CaseBank

        stmt = select(CaseBank).where(
            and_(
                CaseBank.status == "active",
                CaseBank.success_rate < threshold,
                CaseBank.usage_count > 10,
                CaseBank.usage_count < 500,
            )
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        removed_ids = []
        for case in cases:
            if not self.dry_run:
                case.status = "archived"
                await self.db.commit()
                logger.info(
                    f"Archived low-performance case: {case.case_id} "
                    f"(success_rate={case.success_rate}%)"
                )
            else:
                logger.info(
                    f"[DRY-RUN] Would archive: {case.case_id} "
                    f"(success_rate={case.success_rate}%)"
                )

            removed_ids.append(str(case.case_id))

        return removed_ids

    async def merge_duplicate_cases(
        self, similarity_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        """
        Merge duplicate cases based on vector similarity.

        Criteria:
        - Vector similarity > threshold
        - Keep case with higher usage_count
        - Archive the duplicate

        Args:
            similarity_threshold: Cosine similarity threshold (default: 0.95)

        Returns:
            List of merge result dicts
        """
        from apps.api.database import CaseBank

        stmt = select(CaseBank).where(
            and_(
                CaseBank.status == "active",
                CaseBank.query_vector.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        cases = list(result.scalars().all())

        merged_pairs = []
        processed = set()

        for i, case1 in enumerate(cases):
            if case1.case_id in processed:
                continue

            vec1 = self._parse_vector(case1.query_vector)
            if not vec1:
                continue

            for case2 in cases[i + 1 :]:
                if case2.case_id in processed:
                    continue

                vec2 = self._parse_vector(case2.query_vector)
                if not vec2:
                    continue

                similarity = self._calculate_similarity(vec1, vec2)

                if similarity > similarity_threshold:
                    keeper, remover = (
                        (case1, case2)
                        if case1.usage_count >= case2.usage_count
                        else (case2, case1)
                    )

                    if not self.dry_run:
                        keeper.usage_count += remover.usage_count
                        # Handle Optional success_rate
                        keeper_rate = keeper.success_rate or 0.0
                        remover_rate = remover.success_rate or 0.0
                        keeper.success_rate = (keeper_rate + remover_rate) / 2
                        remover.status = "archived"
                        await self.db.commit()
                        logger.info(
                            f"Merged duplicate: kept={keeper.case_id}, "
                            f"removed={remover.case_id}, similarity={similarity:.3f}"
                        )
                    else:
                        logger.info(
                            f"[DRY-RUN] Would merge: kept={keeper.case_id}, "
                            f"removed={remover.case_id}, similarity={similarity:.3f}"
                        )

                    merged_pairs.append(
                        {
                            "keeper": keeper.case_id,
                            "removed": remover.case_id,
                            "similarity": round(similarity, 3),
                        }
                    )
                    processed.add(remover.case_id)
                    break

        return merged_pairs

    async def archive_inactive_cases(self, days: int = 90) -> List[str]:
        """
        Archive inactive cases (not accessed for X days).

        Criteria:
        - last_used_at < (now - days)
        - usage_count < 100 (not frequently used)
        - status = 'active'

        Args:
            days: Number of days of inactivity (default: 90)

        Returns:
            List of archived case IDs
        """
        from apps.api.database import CaseBank

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(CaseBank).where(
            and_(
                CaseBank.status == "active",
                CaseBank.last_used_at.isnot(None),
                CaseBank.last_used_at < cutoff_date,
                CaseBank.usage_count < 100,
            )
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        archived_ids = []
        for case in cases:
            if not self.dry_run:
                case.status = "archived"
                await self.db.commit()
                logger.info(
                    f"Archived inactive case: {case.case_id} "
                    f"(last_used={case.last_used_at})"
                )
            else:
                logger.info(
                    f"[DRY-RUN] Would archive: {case.case_id} "
                    f"(last_used={case.last_used_at})"
                )

            archived_ids.append(str(case.case_id))

        return archived_ids

    def _parse_vector(self, vector_str: Union[str, List[float]]) -> Optional[List[float]]:
        """
        Parse vector from string format to list of floats.

        Args:
            vector_str: Vector in JSON string format or already parsed list

        Returns:
            List of floats or None if parsing fails
        """
        try:
            if isinstance(vector_str, str):
                vec = json.loads(vector_str)
            else:  # isinstance(vector_str, list)
                vec = vector_str

            return [float(v) for v in vec]
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning(f"Failed to parse vector: {vector_str}")
            return None

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        if not vec1 or not vec2:
            return 0.0

        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)

            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0

            return float(dot_product / (norm_v1 * norm_v2))
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0

    async def restore_archived_case(self, case_id: str) -> bool:
        """
        Restore an archived case back to active status.

        Args:
            case_id: Case ID to restore

        Returns:
            True if restored, False if not found or not archived
        """
        from apps.api.database import CaseBank

        case = await self.db.get(CaseBank, case_id)
        if not case or case.status != "archived":
            logger.warning(
                f"Cannot restore case {case_id}: "
                f"not found or not archived (status={case.status if case else 'N/A'})"
            )
            return False

        case.status = "active"
        await self.db.commit()
        logger.info(f"Restored archived case: {case_id}")
        return True
