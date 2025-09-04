"""
HITL State Machine
HITL 큐 상태 전이 관리
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)


class HITLStatus(str, Enum):
    """HITL 항목 상태"""
    PENDING = "pending"         # 대기 중
    ASSIGNED = "assigned"       # 할당됨 (처리 중)
    REVIEWING = "reviewing"     # 사람이 검토 중  
    RESOLVED = "resolved"       # 해결됨
    REJECTED = "rejected"       # 거부됨
    ERROR = "error"             # 오류 발생


class HITLPriority(int, Enum):
    """HITL 우선순위"""
    URGENT = 1      # 긴급 (즉시 처리)
    HIGH = 2        # 높음
    MEDIUM = 3      # 보통 (기본값)
    LOW = 4         # 낮음
    BACKLOG = 5     # 백로그


class HITLStateMachine:
    """HITL 상태 전이 관리자"""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        HITLStatus.PENDING: [HITLStatus.ASSIGNED, HITLStatus.REVIEWING, HITLStatus.REJECTED],
        HITLStatus.ASSIGNED: [HITLStatus.REVIEWING, HITLStatus.RESOLVED, HITLStatus.ERROR, HITLStatus.PENDING],
        HITLStatus.REVIEWING: [HITLStatus.RESOLVED, HITLStatus.REJECTED, HITLStatus.PENDING],
        HITLStatus.RESOLVED: [],  # Terminal state
        HITLStatus.REJECTED: [],  # Terminal state  
        HITLStatus.ERROR: [HITLStatus.PENDING, HITLStatus.REJECTED]
    }
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def transition_to(
        self,
        queue_id: int,
        new_status: HITLStatus,
        user_id: str = "system",
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """상태 전이 실행"""
        
        async with self.db_pool.acquire() as conn:
            
            # Get current status
            current_item = await conn.fetchrow("""
                SELECT queue_id, status, assigned_to, attempts
                FROM hitl_queue
                WHERE queue_id = $1
            """, queue_id)
            
            if not current_item:
                logger.error(f"HITL item not found: {queue_id}")
                return False
            
            current_status = HITLStatus(current_item["status"])
            
            # Validate transition
            if not self._is_valid_transition(current_status, new_status):
                logger.error(
                    f"Invalid state transition: {current_status} -> {new_status} "
                    f"for item {queue_id}"
                )
                return False
            
            # Execute transition
            success = await self._execute_transition(
                conn, queue_id, current_status, new_status,
                user_id, reason, metadata
            )
            
            if success:
                logger.info(
                    f"HITL state transition: item={queue_id}, "
                    f"{current_status} -> {new_status}, user={user_id}"
                )
                
                # Record audit log
                await self._record_state_change(
                    conn, queue_id, current_status, new_status,
                    user_id, reason, metadata
                )
            
            return success
    
    def _is_valid_transition(
        self, 
        current_status: HITLStatus, 
        new_status: HITLStatus
    ) -> bool:
        """상태 전이 유효성 검증"""
        return new_status in self.VALID_TRANSITIONS.get(current_status, [])
    
    async def _execute_transition(
        self,
        conn: asyncpg.Connection,
        queue_id: int,
        current_status: HITLStatus,
        new_status: HITLStatus,
        user_id: str,
        reason: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """상태 전이 실행"""
        
        try:
            # Build update query based on new status
            update_fields = ["status = $2", "updated_at = NOW()"]
            params = [queue_id, new_status.value]
            param_idx = 3
            
            # Status-specific updates
            if new_status == HITLStatus.ASSIGNED:
                update_fields.extend([
                    f"assigned_at = NOW()",
                    f"assigned_to = ${param_idx}"
                ])
                params.append(user_id)
                param_idx += 1
                
            elif new_status == HITLStatus.REVIEWING:
                update_fields.extend([
                    f"reviewing_at = NOW()",
                    f"reviewer_id = ${param_idx}"
                ])
                params.append(user_id)
                param_idx += 1
                
            elif new_status == HITLStatus.RESOLVED:
                update_fields.extend([
                    f"resolved_at = NOW()",
                    f"resolved_by = ${param_idx}"
                ])
                params.append(user_id)
                param_idx += 1
                
                # Set resolved path and confidence if provided
                if metadata:
                    if "resolved_path" in metadata:
                        update_fields.append(f"resolved_path = ${param_idx}")
                        params.append(metadata["resolved_path"])
                        param_idx += 1
                    
                    if "final_confidence" in metadata:
                        update_fields.append(f"final_confidence = ${param_idx}")
                        params.append(metadata["final_confidence"])
                        param_idx += 1
                        
            elif new_status == HITLStatus.REJECTED:
                update_fields.extend([
                    f"rejected_at = NOW()",
                    f"rejected_by = ${param_idx}"
                ])
                params.append(user_id)
                param_idx += 1
                
            elif new_status == HITLStatus.ERROR:
                update_fields.extend([
                    f"last_error = NOW()",
                    f"attempts = attempts + 1"
                ])
                
                if reason:
                    update_fields.append(f"error_message = ${param_idx}")
                    params.append(reason)
                    param_idx += 1
                    
            elif new_status == HITLStatus.PENDING:
                # Reset to pending (retry)
                update_fields.extend([
                    f"assigned_at = NULL",
                    f"assigned_to = NULL",
                    f"attempts = attempts + 1"
                ])
            
            # Add reason if provided
            if reason and new_status not in [HITLStatus.ERROR]:
                update_fields.append(f"resolution_reason = ${param_idx}")
                params.append(reason)
                param_idx += 1
            
            # Execute update
            query = f"""
                UPDATE hitl_queue
                SET {', '.join(update_fields)}
                WHERE queue_id = $1
            """
            
            result = await conn.execute(query, *params)
            
            # Update doc_taxonomy if resolved
            if new_status == HITLStatus.RESOLVED and metadata:
                await self._update_doc_taxonomy(conn, queue_id, metadata)
            
            return "UPDATE 1" in result
            
        except Exception as e:
            logger.error(f"Failed to execute state transition: {e}")
            return False
    
    async def _update_doc_taxonomy(
        self,
        conn: asyncpg.Connection,
        queue_id: int,
        metadata: Dict[str, Any]
    ):
        """doc_taxonomy 테이블 업데이트"""
        
        try:
            # Get queue item details
            item = await conn.fetchrow("""
                SELECT text, text_hash, resolved_path, final_confidence
                FROM hitl_queue
                WHERE queue_id = $1
            """, queue_id)
            
            if not item:
                return
            
            # Insert or update doc_taxonomy
            # This is a simplified version - you might need to handle document IDs
            await conn.execute("""
                INSERT INTO doc_taxonomy (text_hash, path, confidence, created_at, source)
                VALUES ($1, $2, $3, NOW(), 'hitl_resolved')
                ON CONFLICT (text_hash) DO UPDATE SET
                    path = EXCLUDED.path,
                    confidence = EXCLUDED.confidence,
                    updated_at = NOW()
            """, 
            hash(item["text"]),  # Simple hash
            item["resolved_path"],
            item["final_confidence"]
            )
            
            logger.debug(f"Updated doc_taxonomy for HITL item {queue_id}")
            
        except Exception as e:
            logger.error(f"Failed to update doc_taxonomy: {e}")
    
    async def _record_state_change(
        self,
        conn: asyncpg.Connection,
        queue_id: int,
        old_status: HITLStatus,
        new_status: HITLStatus,
        user_id: str,
        reason: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ):
        """상태 변경 감사 로그 기록"""
        
        try:
            await conn.execute("""
                INSERT INTO audit_log (action, user_id, details, created_at)
                VALUES ($1, $2, $3, NOW())
            """,
            "hitl_state_transition",
            user_id,
            {
                "queue_id": queue_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason,
                "metadata": metadata or {}
            })
            
        except Exception as e:
            logger.warning(f"Failed to record audit log: {e}")
    
    async def assign_to_user(
        self,
        queue_id: int,
        user_id: str,
        priority: Optional[HITLPriority] = None
    ) -> bool:
        """사용자에게 HITL 항목 할당"""
        
        metadata = {"assigned_by": "manual"}
        if priority:
            metadata["priority"] = priority.value
        
        # Also update priority if specified
        if priority:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE hitl_queue 
                    SET priority = $2
                    WHERE queue_id = $1
                """, queue_id, priority.value)
        
        return await self.transition_to(
            queue_id, HITLStatus.ASSIGNED, user_id,
            f"Manually assigned to {user_id}", metadata
        )
    
    async def resolve_item(
        self,
        queue_id: int,
        user_id: str,
        resolved_path: List[str],
        confidence: float,
        resolution_reason: str
    ) -> bool:
        """HITL 항목 해결"""
        
        metadata = {
            "resolved_path": resolved_path,
            "final_confidence": confidence,
            "resolution_method": "manual"
        }
        
        return await self.transition_to(
            queue_id, HITLStatus.RESOLVED, user_id,
            resolution_reason, metadata
        )
    
    async def reject_item(
        self,
        queue_id: int,
        user_id: str,
        rejection_reason: str
    ) -> bool:
        """HITL 항목 거부"""
        
        return await self.transition_to(
            queue_id, HITLStatus.REJECTED, user_id,
            rejection_reason
        )
    
    async def get_queue_summary(self) -> Dict[str, Any]:
        """HITL 큐 요약 통계"""
        
        async with self.db_pool.acquire() as conn:
            
            # Status distribution
            status_dist = await conn.fetch("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM hitl_queue
                GROUP BY status
                ORDER BY count DESC
            """)
            
            # Priority distribution
            priority_dist = await conn.fetch("""
                SELECT 
                    priority,
                    COUNT(*) as count
                FROM hitl_queue
                WHERE status IN ('pending', 'assigned', 'reviewing')
                GROUP BY priority
                ORDER BY priority
            """)
            
            # Processing metrics
            processing_metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'assigned' THEN 1 END) as assigned,
                    COUNT(CASE WHEN status = 'reviewing' THEN 1 END) as reviewing,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as error,
                    AVG(CASE WHEN resolved_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) END) as avg_resolution_time,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as created_today
                FROM hitl_queue
            """)
            
            return {
                "status_distribution": [dict(row) for row in status_dist],
                "priority_distribution": [dict(row) for row in priority_dist],
                "processing_metrics": dict(processing_metrics) if processing_metrics else {},
                "valid_transitions": {
                    status.value: [t.value for t in transitions]
                    for status, transitions in self.VALID_TRANSITIONS.items()
                }
            }