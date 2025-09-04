"""
HITL (Human-in-the-Loop) Worker
저신뢰도 분류 큐 처리 워커
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

import asyncpg
from pgvector.asyncpg import register_vector

logger = logging.getLogger(__name__)


class HITLWorker:
    """HITL 큐 처리 워커"""
    
    def __init__(self):
        self.connection_string = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/dt_rag"
        )
        self.pool: Optional[asyncpg.Pool] = None
        self.running = False
        
        # Worker configuration
        self.polling_interval = float(os.getenv("HITL_POLLING_INTERVAL", "5.0"))  # seconds
        self.batch_size = int(os.getenv("HITL_BATCH_SIZE", "10"))
        self.max_processing_time = int(os.getenv("HITL_MAX_PROCESSING_TIME", "300"))  # 5 minutes
        
        # Metrics
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
    
    async def initialize(self):
        """워커 초기화"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=5,
                command_timeout=30,
                server_settings={
                    'application_name': 'hitl_worker',
                }
            )
            
            # Register pgvector types
            async with self.pool.acquire() as conn:
                await register_vector(conn)
            
            logger.info("✅ HITL worker initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ HITL worker initialization failed: {e}")
            raise
    
    async def close(self):
        """워커 종료"""
        self.running = False
        if self.pool:
            await self.pool.close()
            logger.info("HITL worker closed")
    
    async def start(self):
        """워커 시작"""
        if not self.pool:
            await self.initialize()
        
        self.running = True
        logger.info("🚀 HITL worker started")
        
        try:
            while self.running:
                await self._process_batch()
                await asyncio.sleep(self.polling_interval)
                
        except KeyboardInterrupt:
            logger.info("HITL worker stopped by user")
        except Exception as e:
            logger.error(f"HITL worker error: {e}")
            raise
        finally:
            await self.close()
    
    async def _process_batch(self):
        """배치 단위로 HITL 항목 처리"""
        
        async with self.pool.acquire() as conn:
            
            # Get pending items from queue
            pending_items = await conn.fetch("""
                SELECT 
                    queue_id,
                    text,
                    suggested_path,
                    confidence,
                    priority,
                    created_at,
                    metadata
                FROM hitl_queue
                WHERE status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT $1
            """, self.batch_size)
            
            if not pending_items:
                return  # No items to process
            
            logger.info(f"Processing HITL batch: {len(pending_items)} items")
            
            for item in pending_items:
                try:
                    await self._process_item(conn, item)
                    self.processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process HITL item {item['queue_id']}: {e}")
                    await self._handle_processing_error(conn, item, str(e))
                    self.error_count += 1
    
    async def _process_item(self, conn: asyncpg.Connection, item: Dict[str, Any]):
        """개별 HITL 항목 처리"""
        
        queue_id = item["queue_id"]
        text = item["text"]
        suggested_path = item["suggested_path"]
        confidence = item["confidence"]
        
        # Mark as assigned (in processing)
        await conn.execute("""
            UPDATE hitl_queue
            SET status = 'assigned', 
                assigned_at = NOW(),
                assigned_to = 'hitl_worker'
            WHERE queue_id = $1
        """, queue_id)
        
        logger.debug(f"Processing HITL item {queue_id}: confidence={confidence:.3f}")
        
        # Simulate automatic resolution for very low confidence items
        # In production, this would involve more sophisticated logic
        auto_resolution = await self._attempt_auto_resolution(
            conn, text, suggested_path, confidence
        )
        
        if auto_resolution:
            # Auto-resolve with improved classification
            await self._resolve_item(
                conn, queue_id, auto_resolution["resolved_path"], 
                auto_resolution["new_confidence"], "auto_resolved",
                auto_resolution["resolution_reason"]
            )
        else:
            # Keep in queue for human review (change priority)
            await conn.execute("""
                UPDATE hitl_queue
                SET status = 'pending',
                    priority = GREATEST(priority - 1, 1),  -- Increase priority
                    attempts = attempts + 1,
                    last_attempt = NOW()
                WHERE queue_id = $1
            """, queue_id)
            
            logger.debug(f"HITL item {queue_id} kept for human review")
    
    async def _attempt_auto_resolution(
        self, 
        conn: asyncpg.Connection,
        text: str,
        suggested_path: List[str],
        confidence: float
    ) -> Optional[Dict[str, Any]]:
        """자동 해결 시도"""
        
        # Strategy 1: Check if there are very similar texts with high confidence
        similar_classifications = await conn.fetch("""
            SELECT 
                dt.path,
                dt.confidence,
                similarity(dt.text_hash, $1) as text_similarity
            FROM doc_taxonomy dt
            WHERE dt.confidence > 0.8
            AND similarity(dt.text_hash, $1) > 0.9  -- Very similar text
            ORDER BY text_similarity DESC, dt.confidence DESC
            LIMIT 3
        """, hash(text))  # Simple text hash for similarity
        
        if similar_classifications:
            best_match = similar_classifications[0]
            if best_match["text_similarity"] > 0.95:
                return {
                    "resolved_path": best_match["path"],
                    "new_confidence": min(best_match["confidence"], 0.85),
                    "resolution_reason": f"Similar text match (similarity: {best_match['text_similarity']:.3f})"
                }
        
        # Strategy 2: Check consensus among similar confidence items
        if confidence > 0.5:  # Only for medium confidence items
            consensus = await self._check_consensus(conn, suggested_path)
            if consensus and consensus["agreement"] > 0.8:
                return {
                    "resolved_path": suggested_path,
                    "new_confidence": min(confidence + 0.1, 0.8),
                    "resolution_reason": f"Consensus validation (agreement: {consensus['agreement']:.3f})"
                }
        
        return None  # Cannot auto-resolve
    
    async def _check_consensus(
        self, 
        conn: asyncpg.Connection, 
        path: List[str]
    ) -> Optional[Dict[str, Any]]:
        """동일 경로에 대한 합의 확인"""
        
        # Check recent classifications for the same path
        consensus_data = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_count,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN confidence > 0.7 THEN 1 END) as high_conf_count
            FROM doc_taxonomy
            WHERE path = $1
            AND created_at > NOW() - INTERVAL '7 days'
        """, path)
        
        if consensus_data and consensus_data["total_count"] > 5:
            agreement = consensus_data["high_conf_count"] / consensus_data["total_count"]
            return {
                "agreement": agreement,
                "avg_confidence": consensus_data["avg_confidence"]
            }
        
        return None
    
    async def _resolve_item(
        self,
        conn: asyncpg.Connection,
        queue_id: int,
        resolved_path: List[str],
        new_confidence: float,
        resolution_type: str,
        resolution_reason: str
    ):
        """HITL 항목 해결"""
        
        # Update HITL queue status
        await conn.execute("""
            UPDATE hitl_queue
            SET status = 'resolved',
                resolved_at = NOW(),
                resolved_path = $2,
                final_confidence = $3,
                resolution_type = $4,
                resolution_reason = $5
            WHERE queue_id = $1
        """, queue_id, resolved_path, new_confidence, resolution_type, resolution_reason)
        
        # Create or update doc_taxonomy entry
        # (This would depend on your specific data model)
        
        # Record audit log
        await conn.execute("""
            INSERT INTO audit_log (action, user_id, details, created_at)
            VALUES ($1, $2, $3, NOW())
        """, 
        "hitl_resolution",
        "hitl_worker",
        {
            "queue_id": queue_id,
            "resolved_path": resolved_path,
            "confidence": new_confidence,
            "resolution_type": resolution_type,
            "resolution_reason": resolution_reason
        })
        
        logger.info(
            f"HITL item {queue_id} resolved: path={resolved_path}, "
            f"confidence={new_confidence:.3f}, type={resolution_type}"
        )
    
    async def _handle_processing_error(
        self,
        conn: asyncpg.Connection,
        item: Dict[str, Any],
        error_message: str
    ):
        """처리 오류 핸들링"""
        
        queue_id = item["queue_id"]
        
        await conn.execute("""
            UPDATE hitl_queue
            SET status = 'error',
                error_message = $2,
                last_error = NOW(),
                attempts = attempts + 1
            WHERE queue_id = $1
        """, queue_id, error_message)
        
        # Record error in audit log
        await conn.execute("""
            INSERT INTO audit_log (action, user_id, details, created_at)
            VALUES ($1, $2, $3, NOW())
        """,
        "hitl_processing_error",
        "hitl_worker",
        {
            "queue_id": queue_id,
            "error": error_message,
            "item": dict(item)
        })
    
    async def get_statistics(self) -> Dict[str, Any]:
        """워커 통계 조회"""
        
        uptime = time.time() - self.start_time
        
        if self.pool:
            async with self.pool.acquire() as conn:
                
                queue_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'assigned' THEN 1 END) as assigned,
                        COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as error,
                        AVG(CASE WHEN resolved_at IS NOT NULL 
                            THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) END) as avg_resolution_time
                    FROM hitl_queue
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                
                return {
                    "worker_stats": {
                        "uptime_seconds": uptime,
                        "processed_count": self.processed_count,
                        "error_count": self.error_count,
                        "processing_rate": self.processed_count / uptime if uptime > 0 else 0,
                        "error_rate": self.error_count / max(self.processed_count, 1)
                    },
                    "queue_stats": dict(queue_stats) if queue_stats else {},
                    "configuration": {
                        "polling_interval": self.polling_interval,
                        "batch_size": self.batch_size,
                        "max_processing_time": self.max_processing_time
                    }
                }
        
        return {"worker_stats": {"uptime_seconds": uptime}}


async def main():
    """HITL 워커 메인 실행"""
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    worker = HITLWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("HITL worker shutdown requested")
    except Exception as e:
        logger.error(f"HITL worker failed: {e}")
        raise
    finally:
        await worker.close()


if __name__ == "__main__":
    asyncio.run(main())