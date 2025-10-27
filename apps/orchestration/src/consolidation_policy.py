# @CODE:CONSOLIDATION-001:ENGINE @CODE:TEST-003:CONSOLIDATION-POLICY | SPEC: SPEC-CONSOLIDATION-001.md | TEST: tests/unit/test_consolidation.py
# @CODE:TEST-003 | SPEC: SPEC-TEST-003.md | TEST: tests/performance/
# @CODE:MYPY-001:PHASE2:BATCH5

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from apps.api.database import CaseBank, CaseBankArchive

logger = logging.getLogger(__name__)


class ConsolidationPolicy:
    """
    Memory Consolidation Policy for optimizing case bank storage.

    Implements:
    - Low performance case removal (success_rate < 30%)
    - Duplicate case merging (similarity > 95%)
    - Inactive case archiving (90+ days unused)
    """

    def __init__(self, db_session: AsyncSession, dry_run: bool = False) -> None:
        """
        Initialize Consolidation Policy.

        Args:
            db_session: Async database session
            dry_run: If True, no actual changes are made (simulation mode)
        """
        self.db = db_session
        self.dry_run = dry_run
        self.removed_cases: List[str] = []
        self.merged_cases: List[Dict[str, Any]] = []
        self.archived_cases: List[str] = []

    async def run_consolidation(self) -> Dict[str, Any]:
        """
        Execute full consolidation policy.

        Returns:
            Summary of consolidation results
        """
        logger.info("🔄 Starting consolidation policy execution...")

        # 1. Remove low performance cases
        low_performance_cases = await self.remove_low_performance_cases()
        logger.info(f"  Removed {len(low_performance_cases)} low performance cases")

        # 2. Merge duplicate cases
        duplicate_cases = await self.merge_duplicate_cases()
        logger.info(f"  Merged {len(duplicate_cases)} duplicate case pairs")

        # 3. Archive inactive cases
        inactive_cases = await self.archive_inactive_cases()
        logger.info(f"  Archived {len(inactive_cases)} inactive cases")

        result = {
            "removed_cases": len(low_performance_cases),
            "merged_cases": len(duplicate_cases),
            "archived_cases": len(inactive_cases),
            "dry_run": self.dry_run,
            "details": {
                "removed": low_performance_cases,
                "merged": duplicate_cases,
                "archived": inactive_cases,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"✅ Consolidation policy execution completed: {result}")
        return result

    async def remove_low_performance_cases(
        self, threshold: float = 30.0, min_usage: int = 10
    ) -> List[str]:
        """
        Remove cases with consistently low success rates.

        Args:
            threshold: Success rate threshold (default: 30%)
            min_usage: Minimum usage count to consider (default: 10)

        Returns:
            List of removed case IDs
        """
        stmt = select(CaseBank).where(
            CaseBank.success_rate < threshold, CaseBank.usage_count > min_usage
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        removed_ids = []
        for case in cases:
            if not self.dry_run:
                # Archive case before removing
                await self._archive_case(case, reason="low_performance")
                await self.db.commit()

            removed_ids.append(case.case_id)
            logger.debug(
                f"  Removed low performance case: {case.case_id} (success_rate={case.success_rate:.1f}%)"
            )

        return removed_ids

    async def merge_duplicate_cases(
        self, similarity_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        """
        Merge duplicate cases based on vector similarity.

        Args:
            similarity_threshold: Cosine similarity threshold (default: 0.95)

        Returns:
            List of merged case pairs
        """
        stmt = select(CaseBank).where(CaseBank.query_vector.isnot(None))
        result = await self.db.execute(stmt)
        cases = list(result.scalars().all())

        merged_pairs = []
        processed = set()

        for i, case1 in enumerate(cases):
            if case1.case_id in processed:
                continue

            for case2 in cases[i + 1 :]:
                if case2.case_id in processed:
                    continue

                # Calculate cosine similarity
                similarity = self._calculate_similarity(
                    case1.query_vector, case2.query_vector
                )

                if similarity > similarity_threshold:
                    # Keep case with higher usage count
                    keeper, remover = (
                        (case1, case2)
                        if case1.usage_count >= case2.usage_count
                        else (case2, case1)
                    )

                    if not self.dry_run:
                        # Merge metadata
                        keeper.usage_count += remover.usage_count
                        keeper.success_rate = (
                            keeper.success_rate + remover.success_rate
                        ) / 2

                        # Archive removed case
                        await self._archive_case(remover, reason="duplicate")
                        await self.db.commit()

                    merged_pairs.append(
                        {
                            "keeper": keeper.case_id,
                            "removed": remover.case_id,
                            "similarity": float(similarity),
                        }
                    )
                    processed.add(remover.case_id)

                    logger.debug(
                        f"  Merged duplicate: {remover.case_id} → {keeper.case_id} "
                        f"(similarity={similarity:.3f})"
                    )

        return merged_pairs

    async def archive_inactive_cases(
        self, days: int = 90, max_usage: int = 100
    ) -> List[str]:
        """
        Archive cases that haven't been used for a long time.

        Args:
            days: Inactivity threshold in days (default: 90)
            max_usage: Exclude high-usage cases (default: 100)

        Returns:
            List of archived case IDs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(CaseBank).where(
            CaseBank.last_used_at.isnot(None),
            CaseBank.last_used_at < cutoff_date,
            CaseBank.usage_count < max_usage,
        )
        result = await self.db.execute(stmt)
        cases = result.scalars().all()

        archived_ids = []
        for case in cases:
            if not self.dry_run:
                await self._archive_case(case, reason="inactive")
                await self.db.commit()

            archived_ids.append(case.case_id)
            logger.debug(
                f"  Archived inactive case: {case.case_id} "
                f"(last_used={case.last_used_at.isoformat() if case.last_used_at else 'never'})"
            )

        return archived_ids

    async def _archive_case(self, case: CaseBank, reason: str) -> None:
        """
        Archive a case to the archive table.

        Args:
            case: CaseBank instance to archive
            reason: Reason for archiving
        """
        archive_entry = CaseBankArchive(
            case_id=case.case_id,
            query=case.query,
            response_text=case.response_text,
            category_path=case.category_path,
            query_vector=case.query_vector,
            usage_count=case.usage_count,
            success_rate=case.success_rate,
            archived_reason=reason,
            original_created_at=case.created_at,
            original_updated_at=case.last_used_at,
        )

        self.db.add(archive_entry)

        # Delete from active case_bank
        await self.db.delete(case)

    @staticmethod
    def _calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0

    async def get_consolidation_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for consolidation policy.

        Returns:
            Summary of potential consolidation candidates
        """
        # Count low performance cases
        low_perf_stmt = (
            select(func.count())
            .select_from(CaseBank)
            .where(CaseBank.success_rate < 30.0, CaseBank.usage_count > 10)
        )
        low_perf_result = await self.db.execute(low_perf_stmt)
        low_perf_count = low_perf_result.scalar()

        # Count inactive cases
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
        inactive_stmt = (
            select(func.count())
            .select_from(CaseBank)
            .where(
                CaseBank.last_used_at.isnot(None),
                CaseBank.last_used_at < cutoff_date,
                CaseBank.usage_count < 100,
            )
        )
        inactive_result = await self.db.execute(inactive_stmt)
        inactive_count = inactive_result.scalar()

        # Total active cases
        total_stmt = select(func.count()).select_from(CaseBank)
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar()

        return {
            "total_active_cases": total_count,
            "low_performance_candidates": low_perf_count,
            "inactive_candidates": inactive_count,
            "potential_savings": (low_perf_count or 0) + (inactive_count or 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
