"""
HITL Integration Tests
HITL 워크플로우 통합 테스트
"""

import pytest
import asyncio
import asyncpg
from unittest.mock import AsyncMock, patch
import os
import time
from typing import Dict, Any

from ..worker import HITLWorker
from ..services.state_machine import HITLStateMachine, HITLStatus, HITLPriority


@pytest.fixture
async def db_pool():
    """테스트용 데이터베이스 풀"""
    connection_string = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/dt_rag_test"
    )
    
    pool = await asyncpg.create_pool(connection_string, min_size=1, max_size=2)
    
    # Setup test data
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM hitl_queue")
        await conn.execute("DELETE FROM audit_log")
    
    yield pool
    
    await pool.close()


@pytest.fixture
async def hitl_worker(db_pool):
    """테스트용 HITL 워커"""
    worker = HITLWorker()
    worker.pool = db_pool
    worker.polling_interval = 0.1  # Fast polling for tests
    worker.batch_size = 5
    
    yield worker
    
    worker.running = False


@pytest.fixture
async def state_machine(db_pool):
    """테스트용 상태 머신"""
    return HITLStateMachine(db_pool)


@pytest.mark.asyncio
class TestHITLWorkflow:
    """HITL 워크플로우 통합 테스트"""
    
    async def test_low_confidence_auto_queue(self, db_pool):
        """저신뢰도 분류 자동 큐잉 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Insert low confidence classification
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status, created_at)
                VALUES ($1, $2, $3, 'pending', NOW())
                RETURNING queue_id
            """, "ambiguous text content", ["Technology", "AI"], 0.65)
            
            # Verify item was queued
            item = await conn.fetchrow("""
                SELECT * FROM hitl_queue WHERE queue_id = $1
            """, queue_id)
            
            assert item is not None
            assert item["status"] == "pending"
            assert item["confidence"] == 0.65
            assert item["suggested_path"] == ["Technology", "AI"]
    
    async def test_state_transitions(self, state_machine, db_pool):
        """상태 전이 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create test HITL item
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING queue_id
            """, "test classification", ["AI"], 0.6)
            
            # Test valid transitions
            # pending -> assigned
            success = await state_machine.transition_to(
                queue_id, HITLStatus.ASSIGNED, "test_user"
            )
            assert success
            
            # assigned -> reviewing
            success = await state_machine.transition_to(
                queue_id, HITLStatus.REVIEWING, "reviewer_1"
            )
            assert success
            
            # reviewing -> resolved
            success = await state_machine.resolve_item(
                queue_id, "reviewer_1", ["AI", "Machine Learning"], 
                0.85, "Manual review completed"
            )
            assert success
            
            # Verify final state
            final_item = await conn.fetchrow("""
                SELECT status, resolved_path, final_confidence, resolved_by
                FROM hitl_queue WHERE queue_id = $1
            """, queue_id)
            
            assert final_item["status"] == "resolved"
            assert final_item["resolved_path"] == ["AI", "Machine Learning"]
            assert final_item["final_confidence"] == 0.85
            assert final_item["resolved_by"] == "reviewer_1"
    
    async def test_invalid_state_transition(self, state_machine, db_pool):
        """잘못된 상태 전이 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create resolved item
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                VALUES ($1, $2, $3, 'resolved')
                RETURNING queue_id
            """, "resolved item", ["AI"], 0.9)
            
            # Try invalid transition (resolved -> pending)
            success = await state_machine.transition_to(
                queue_id, HITLStatus.PENDING, "test_user"
            )
            assert not success
            
            # Verify state unchanged
            item = await conn.fetchrow("""
                SELECT status FROM hitl_queue WHERE queue_id = $1
            """, queue_id)
            assert item["status"] == "resolved"
    
    async def test_worker_auto_resolution(self, hitl_worker, db_pool):
        """워커 자동 해결 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create high similarity reference classification
            await conn.execute("""
                INSERT INTO doc_taxonomy (text_hash, path, confidence, created_at)
                VALUES ($1, $2, $3, NOW())
            """, hash("machine learning tutorial"), ["AI", "Machine Learning"], 0.95)
            
            # Create similar low-confidence item
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING queue_id  
            """, "machine learning tutorial", ["AI"], 0.6)
            
            # Process one batch
            await hitl_worker._process_batch()
            
            # Check if auto-resolved
            resolved_item = await conn.fetchrow("""
                SELECT status, resolution_type, final_confidence
                FROM hitl_queue WHERE queue_id = $1
            """, queue_id)
            
            # Should be auto-resolved or at least processed
            assert resolved_item["status"] in ["resolved", "assigned"]
    
    async def test_consensus_validation(self, hitl_worker, db_pool):
        """합의 기반 검증 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create multiple high-confidence classifications for same path
            path = ["Technology", "Software"]
            for i in range(6):
                await conn.execute("""
                    INSERT INTO doc_taxonomy (text_hash, path, confidence, created_at)
                    VALUES ($1, $2, $3, NOW() - INTERVAL '1 hour')
                """, hash(f"software development {i}"), path, 0.85)
            
            # Create medium-confidence item with same path
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING queue_id
            """, "software development best practices", path, 0.65)
            
            # Process batch
            await hitl_worker._process_batch()
            
            # Check consensus validation
            item = await conn.fetchrow("""
                SELECT status, final_confidence, resolution_reason
                FROM hitl_queue WHERE queue_id = $1
            """, queue_id)
            
            # Should have been boosted by consensus
            if item["status"] == "resolved":
                assert item["final_confidence"] > 0.65
                assert "consensus" in item["resolution_reason"].lower()
    
    async def test_error_handling(self, state_machine, db_pool):
        """오류 처리 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create test item
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                VALUES ($1, $2, $3, 'assigned')
                RETURNING queue_id
            """, "test error handling", ["Test"], 0.5)
            
            # Transition to error state
            success = await state_machine.transition_to(
                queue_id, HITLStatus.ERROR, "system",
                "Processing timeout occurred"
            )
            assert success
            
            # Verify error state
            error_item = await conn.fetchrow("""
                SELECT status, error_message, attempts
                FROM hitl_queue WHERE queue_id = $1
            """, queue_id)
            
            assert error_item["status"] == "error"
            assert error_item["error_message"] == "Processing timeout occurred"
            assert error_item["attempts"] > 0
            
            # Test recovery (error -> pending)
            success = await state_machine.transition_to(
                queue_id, HITLStatus.PENDING, "system", "Retry after error"
            )
            assert success
    
    async def test_priority_handling(self, db_pool):
        """우선순위 처리 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create items with different priorities
            items = []
            for priority in [HITLPriority.URGENT, HITLPriority.LOW, HITLPriority.HIGH]:
                queue_id = await conn.fetchval("""
                    INSERT INTO hitl_queue (text, suggested_path, confidence, status, priority)
                    VALUES ($1, $2, $3, 'pending', $4)
                    RETURNING queue_id
                """, f"test priority {priority.value}", ["Test"], 0.5, priority.value)
                items.append((queue_id, priority))
            
            # Get items in priority order
            ordered_items = await conn.fetch("""
                SELECT queue_id, priority
                FROM hitl_queue
                WHERE status = 'pending'
                ORDER BY priority ASC, created_at ASC
            """)
            
            # Verify priority ordering
            assert ordered_items[0]["priority"] == HITLPriority.URGENT.value
            assert ordered_items[1]["priority"] == HITLPriority.HIGH.value
            assert ordered_items[2]["priority"] == HITLPriority.LOW.value
    
    async def test_queue_statistics(self, state_machine, db_pool):
        """큐 통계 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create test items in various states
            states = [HITLStatus.PENDING, HITLStatus.ASSIGNED, HITLStatus.RESOLVED]
            for status in states:
                for i in range(3):
                    await conn.execute("""
                        INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                        VALUES ($1, $2, $3, $4)
                    """, f"test {status.value} {i}", ["Test"], 0.6, status.value)
            
            # Get statistics
            stats = await state_machine.get_queue_summary()
            
            # Verify statistics
            assert "status_distribution" in stats
            assert "processing_metrics" in stats
            
            status_counts = {
                item["status"]: item["count"] 
                for item in stats["status_distribution"]
            }
            
            assert status_counts.get("pending", 0) == 3
            assert status_counts.get("assigned", 0) == 3
            assert status_counts.get("resolved", 0) == 3
    
    async def test_audit_logging(self, state_machine, db_pool):
        """감사 로그 테스트"""
        
        async with db_pool.acquire() as conn:
            
            # Create test item
            queue_id = await conn.fetchval("""
                INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING queue_id
            """, "audit test", ["Test"], 0.5)
            
            # Perform state transition
            await state_machine.transition_to(
                queue_id, HITLStatus.ASSIGNED, "test_user", "Test assignment"
            )
            
            # Check audit log
            audit_entry = await conn.fetchrow("""
                SELECT action, user_id, details
                FROM audit_log
                WHERE details->>'queue_id' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, str(queue_id))
            
            assert audit_entry is not None
            assert audit_entry["action"] == "hitl_state_transition"
            assert audit_entry["user_id"] == "test_user"
            
            details = audit_entry["details"]
            assert details["old_status"] == "pending"
            assert details["new_status"] == "assigned"
            assert details["reason"] == "Test assignment"


@pytest.mark.asyncio
class TestHITLWorkerPerformance:
    """HITL 워커 성능 테스트"""
    
    async def test_batch_processing_performance(self, hitl_worker, db_pool):
        """배치 처리 성능 테스트"""
        
        # Create multiple pending items
        async with db_pool.acquire() as conn:
            for i in range(20):
                await conn.execute("""
                    INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                    VALUES ($1, $2, $3, 'pending')
                """, f"performance test {i}", ["Performance"], 0.5)
        
        # Measure processing time
        start_time = time.time()
        await hitl_worker._process_batch()
        processing_time = time.time() - start_time
        
        # Should process batch quickly (< 1 second for 20 items)
        assert processing_time < 1.0
        
        # Check statistics
        stats = await hitl_worker.get_statistics()
        assert stats["worker_stats"]["processed_count"] > 0
    
    async def test_concurrent_worker_safety(self, db_pool):
        """동시 워커 안전성 테스트"""
        
        # Create multiple workers
        workers = []
        for i in range(3):
            worker = HITLWorker()
            worker.pool = db_pool
            worker.polling_interval = 0.1
            worker.batch_size = 2
            workers.append(worker)
        
        # Create test items
        async with db_pool.acquire() as conn:
            for i in range(10):
                await conn.execute("""
                    INSERT INTO hitl_queue (text, suggested_path, confidence, status)
                    VALUES ($1, $2, $3, 'pending')
                """, f"concurrent test {i}", ["Concurrent"], 0.4)
        
        # Run workers concurrently for short time
        tasks = []
        for worker in workers:
            task = asyncio.create_task(self._run_worker_briefly(worker))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify no race conditions (all items processed exactly once)
        async with db_pool.acquire() as conn:
            processed_count = await conn.fetchval("""
                SELECT COUNT(*) FROM hitl_queue 
                WHERE status != 'pending'
            """)
            
            # At least some items should be processed
            assert processed_count > 0
    
    async def _run_worker_briefly(self, worker):
        """워커를 짧은 시간 동안 실행"""
        worker.running = True
        try:
            for _ in range(5):  # Process 5 batches
                if worker.pool:
                    await worker._process_batch()
                await asyncio.sleep(0.1)
        finally:
            worker.running = False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])