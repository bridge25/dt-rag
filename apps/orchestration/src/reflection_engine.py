# @SPEC:REFLECTION-001 @IMPL:REFLECTION-001:0.2

import logging
from typing import List, Dict, Any, Optional, cast
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
import os

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from apps.api.database import CaseBank, ExecutionLog

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available, LLM suggestions disabled")


class ReflectionEngine:
    """
    Reflection Engine for analyzing case performance and generating improvements.

    Implements:
    - Success rate calculation
    - Error pattern analysis
    - LLM-based improvement suggestions
    - Batch reflection processing
    """

    def __init__(self, db_session: AsyncSession, llm_client: Optional[Any] = None):
        """
        Initialize Reflection Engine.

        Args:
            db_session: Async database session
            llm_client: Optional OpenAI client for LLM suggestions
        """
        self.db = db_session
        self.llm = llm_client
        if llm_client is None and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.llm = AsyncOpenAI(api_key=api_key)

    async def get_execution_logs(
        self, case_id: str, limit: int = 100
    ) -> List[ExecutionLog]:
        """
        Get recent execution logs for a case.

        Args:
            case_id: Case ID
            limit: Maximum number of logs

        Returns:
            List of ExecutionLog records
        """
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.case_id == case_id)
            .order_by(ExecutionLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def analyze_case_performance(
        self, case_id: str, limit: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze case performance from execution logs.

        Args:
            case_id: Case ID to analyze
            limit: Number of recent logs to analyze

        Returns:
            Performance analysis dict with:
            - case_id
            - total_executions
            - success_rate
            - common_errors
            - avg_execution_time_ms
        """
        logs = await self.get_execution_logs(case_id, limit)

        if not logs:
            logger.warning(f"No execution logs found for case {case_id}")
            return {
                "case_id": case_id,
                "total_executions": 0,
                "successful_executions": 0,
                "success_rate": 0.0,
                "common_errors": [],
                "avg_execution_time_ms": 0.0,
            }

        total_executions = len(logs)
        successful_executions = sum(1 for log in logs if log.success)
        success_rate = (
            (successful_executions / total_executions) * 100
            if total_executions > 0
            else 0.0
        )

        error_types = [
            log.error_type for log in logs if not log.success and log.error_type
        ]
        common_errors = self._analyze_error_patterns(error_types)

        execution_times = [
            log.execution_time_ms for log in logs if log.execution_time_ms is not None
        ]
        avg_execution_time = (
            sum(execution_times) / len(execution_times) if execution_times else 0.0
        )

        return {
            "case_id": case_id,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(success_rate, 2),
            "common_errors": common_errors,
            "avg_execution_time_ms": round(avg_execution_time, 2),
        }

    def _analyze_error_patterns(self, error_types: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze error patterns from error types.

        Args:
            error_types: List of error type strings

        Returns:
            List of error pattern dicts sorted by frequency
        """
        if not error_types:
            return []

        error_counts: Dict[str, int] = {}
        for error_type in error_types:
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        total_errors = len(error_types)
        patterns = [
            {
                "error_type": error_type,
                "count": count,
                "percentage": round((count / total_errors) * 100, 2),
            }
            for error_type, count in error_counts.items()
        ]

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 13: arg-type resolution (Fix 26 - cast to int for comparison)
        patterns.sort(key=lambda x: cast(int, x["count"]), reverse=True)
        return patterns

    async def generate_improvement_suggestions(self, case_id: str) -> List[str]:
        """
        Generate LLM-based improvement suggestions for low-performance cases.

        Args:
            case_id: Case ID

        Returns:
            List of improvement suggestion strings
        """
        performance = await self.analyze_case_performance(case_id)

        if performance["success_rate"] >= 80:
            logger.info(
                f"Case {case_id} has high success rate ({performance['success_rate']}%), "
                "skipping LLM suggestions"
            )
            return []

        if not self.llm:
            logger.warning("LLM not available, returning basic suggestions")
            return self._generate_fallback_suggestions(performance)

        case = await self.db.get(CaseBank, case_id)
        if not case:
            logger.error(f"Case {case_id} not found")
            return []

        prompt = f"""Analyze the following case and suggest improvements:

Case ID: {case_id}
Query: {case.query}
Response: {case.answer[:500]}...
Success Rate: {performance['success_rate']}%
Common Errors: {performance['common_errors']}
Avg Execution Time: {performance['avg_execution_time_ms']}ms

Provide 3 specific, actionable suggestions to improve this case's success rate.
Format: One suggestion per line, numbered 1-3."""

        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()
            suggestions = [line.strip() for line in content.split("\n") if line.strip()]

            logger.info(
                f"Generated {len(suggestions)} LLM suggestions for case {case_id}"
            )
            return suggestions[:5]

        except Exception as e:
            logger.error(f"LLM suggestion generation failed for {case_id}: {e}")
            return self._generate_fallback_suggestions(performance)

    def _generate_fallback_suggestions(self, performance: Dict[str, Any]) -> List[str]:
        """
        Generate basic suggestions without LLM.

        Args:
            performance: Performance analysis dict

        Returns:
            List of fallback suggestions
        """
        suggestions = []

        if performance["success_rate"] < 30:
            suggestions.append(
                f"Critical: Success rate is only {performance['success_rate']}%. "
                "Consider reviewing case query and response for accuracy."
            )

        if performance["common_errors"]:
            top_error = performance["common_errors"][0]
            suggestions.append(
                f"Address most frequent error: {top_error['error_type']} "
                f"({top_error['percentage']}% of failures)"
            )

        if performance["avg_execution_time_ms"] > 5000:
            suggestions.append(
                f"Optimize execution time (currently {performance['avg_execution_time_ms']}ms). "
                "Consider caching or simplifying logic."
            )

        return suggestions

    async def update_case_success_rate(self, case_id: str, success_rate: float) -> None:
        """
        Update CaseBank.success_rate field.

        Args:
            case_id: Case ID
            success_rate: New success rate value
        """
        stmt = (
            update(CaseBank)
            .where(CaseBank.case_id == case_id)
            .values(success_rate=success_rate)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        logger.debug(f"Updated success_rate for {case_id}: {success_rate}")

    async def run_reflection_batch(self, min_logs: int = 10) -> Dict[str, Any]:
        """
        Run batch reflection analysis on all active cases.

        Args:
            min_logs: Minimum number of logs required for analysis

        Returns:
            Batch results dict with analyzed cases and suggestions
        """
        stmt = (
            select(CaseBank.case_id, func.count(ExecutionLog.log_id).label("log_count"))
            .join(ExecutionLog, CaseBank.case_id == ExecutionLog.case_id)
            .where(CaseBank.status == "active")
            .group_by(CaseBank.case_id)
            .having(func.count(ExecutionLog.log_id) >= min_logs)
        )
        result = await self.db.execute(stmt)
        cases_with_logs = result.all()

        results = []
        for case_id, log_count in cases_with_logs:
            try:
                performance = await self.analyze_case_performance(case_id)

                await self.update_case_success_rate(
                    case_id, performance["success_rate"]
                )

                suggestions = []
                if performance["success_rate"] < 50:
                    suggestions = await self.generate_improvement_suggestions(case_id)

                if suggestions:
                    results.append(
                        {
                            "case_id": case_id,
                            "performance": performance,
                            "suggestions": suggestions,
                        }
                    )

            except Exception as e:
                logger.error(f"Batch reflection failed for {case_id}: {e}")

        return {
            "analyzed_cases": len(cases_with_logs),
            "low_performance_cases": len(results),
            "suggestions": results,
        }
