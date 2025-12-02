"""
CaseBank Data Access Object

Handles database operations for CaseBank and ExecutionLog models.

@CODE:DATABASE-DAO-CASEBANK
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from ..models.casebank import CaseBank, ExecutionLog


class CaseBankDAO:
    """Data Access Object for CaseBank operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_casebank(
        self,
        query: str,
        answer: str,
        sources: str,
        category_path: Optional[List[str]] = None,
        initial_success_rate: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CaseBank:
        """Create a new CaseBank entry."""
        try:
            casebank = CaseBank(
                query=query,
                answer=answer,
                sources=sources,
                category_path=category_path or [],
                success_rate=initial_success_rate,
                usage_count=0,
                metadata=metadata or {},
                version=1,
                updated_by="search_api",
                status="active"
            )

            self.session.add(casebank)
            await self.session.flush()  # Get the ID without committing
            await self.session.refresh(casebank)

            return casebank

        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Failed to create CaseBank entry: {e}")

    async def create_execution_log(
        self,
        case_id: uuid.UUID,
        success: bool,
        execution_time_ms: int,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionLog:
        """Create a new ExecutionLog entry."""
        try:
            execution_log = ExecutionLog(
                case_id=case_id,
                success=success,
                execution_time_ms=execution_time_ms,
                error_type=error_type,
                metadata=metadata or {}
            )

            self.session.add(execution_log)
            await self.session.flush()
            await self.session.refresh(execution_log)

            return execution_log

        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Failed to create ExecutionLog entry: {e}")

    async def get_casebank_by_id(self, case_id: uuid.UUID) -> Optional[CaseBank]:
        """Get CaseBank entry by ID."""
        try:
            stmt = select(CaseBank).where(
                and_(
                    CaseBank.case_id == case_id,
                    CaseBank.status == "active"
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            raise Exception(f"Failed to get CaseBank entry: {e}")

    async def search_similar_queries(
        self,
        query: str,
        limit: int = 5,
        min_success_rate: float = 0.7
    ) -> List[CaseBank]:
        """Search for similar queries in CaseBank."""
        try:
            # Simple text-based similarity search
            # In a real implementation, you'd use vector similarity
            stmt = select(CaseBank).where(
                and_(
                    CaseBank.status == "active",
                    CaseBank.success_rate >= min_success_rate,
                    CaseBank.query.ilike(f"%{query}%")
                )
            ).order_by(
                CaseBank.success_rate.desc(),
                CaseBank.usage_count.desc()
            ).limit(limit)

            result = await self.session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            raise Exception(f"Failed to search similar queries: {e}")

    async def update_success_rate(
        self,
        case_id: uuid.UUID,
        new_success_rate: float,
        increment_usage: bool = True
    ) -> bool:
        """Update success rate and usage count for a CaseBank entry."""
        try:
            stmt = update(CaseBank).where(
                and_(
                    CaseBank.case_id == case_id,
                    CaseBank.status == "active"
                )
            )

            if increment_usage:
                stmt = stmt.values(
                    success_rate=new_success_rate,
                    usage_count=CaseBank.usage_count + 1,
                    updated_at=datetime.utcnow()
                )
            else:
                stmt = stmt.values(
                    success_rate=new_success_rate,
                    updated_at=datetime.utcnow()
                )

            result = await self.session.execute(stmt)
            await self.session.flush()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Failed to update success rate: {e}")

    async def get_casebank_stats(self) -> Dict[str, Any]:
        """Get overall CaseBank statistics."""
        try:
            from sqlalchemy import func

            # Total cases
            total_stmt = select(func.count(CaseBank.case_id)).where(CaseBank.status == "active")
            total_result = await self.session.execute(total_stmt)
            total_cases = total_result.scalar()

            # Average success rate
            avg_stmt = select(func.avg(CaseBank.success_rate)).where(CaseBank.status == "active")
            avg_result = await self.session.execute(avg_stmt)
            avg_success_rate = float(avg_result.scalar() or 0.0)

            # Total usage count
            usage_stmt = select(func.sum(CaseBank.usage_count)).where(CaseBank.status == "active")
            usage_result = await self.session.execute(usage_stmt)
            total_usage = int(usage_result.scalar() or 0)

            # Successful executions count
            success_stmt = select(func.count(ExecutionLog.log_id)).where(ExecutionLog.success == True)
            success_result = await self.session.execute(success_stmt)
            successful_executions = int(success_result.scalar() or 0)

            # Failed executions count
            fail_stmt = select(func.count(ExecutionLog.log_id)).where(ExecutionLog.success == False)
            fail_result = await self.session.execute(fail_stmt)
            failed_executions = int(fail_result.scalar() or 0)

            return {
                "total_cases": total_cases,
                "average_success_rate": round(avg_success_rate, 3),
                "total_usage": total_usage,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "execution_success_rate": round(
                    successful_executions / max(successful_executions + failed_executions, 1) * 100, 2
                )
            }

        except Exception as e:
            raise Exception(f"Failed to get CaseBank stats: {e}")

    async def delete_casebank(self, case_id: uuid.UUID) -> bool:
        """Soft delete a CaseBank entry by setting status to 'deleted'."""
        try:
            stmt = update(CaseBank).where(CaseBank.case_id == case_id).values(
                status="deleted",
                updated_at=datetime.utcnow()
            )

            result = await self.session.execute(stmt)
            await self.session.flush()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Failed to delete CaseBank entry: {e}")