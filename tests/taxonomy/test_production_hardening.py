"""
Tests for Production Hardening Components

Tests for evolution history, rollback, rate limiting,
and admin approval workflow.
TDD RED phase - tests written before implementation.

@TEST:TAXONOMY-EVOLUTION-001
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_taxonomy_version() -> Dict[str, Any]:
    """Sample taxonomy version for testing"""
    return {
        "version_id": "v_001",
        "taxonomy_id": "tax_main",
        "version_number": "1.0.0",
        "created_at": datetime.utcnow() - timedelta(days=7),
        "created_by": "user_admin",
        "categories": [
            {"id": "cat_1", "name": "Technology", "parent_id": None},
            {"id": "cat_2", "name": "Software", "parent_id": "cat_1"},
            {"id": "cat_3", "name": "Hardware", "parent_id": "cat_1"},
        ],
        "metadata": {
            "document_count": 150,
            "source": "manual",
        },
    }


@pytest.fixture
def sample_evolution_event() -> Dict[str, Any]:
    """Sample evolution event"""
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "taxonomy_id": "tax_main",
        "event_type": "category_added",
        "timestamp": datetime.utcnow(),
        "actor": "system",
        "changes": {
            "category_id": "cat_4",
            "category_name": "Cloud Computing",
            "parent_id": "cat_2",
        },
        "previous_state": None,
        "new_state": {"id": "cat_4", "name": "Cloud Computing"},
    }


@pytest.fixture
def sample_approval_request() -> Dict[str, Any]:
    """Sample approval request"""
    return {
        "request_id": f"req_{uuid.uuid4().hex[:12]}",
        "suggestion_id": "sug_merge_001",
        "taxonomy_id": "tax_main",
        "request_type": "merge",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "requester": "system",
        "details": {
            "source_categories": ["cat_ml", "cat_dl"],
            "suggested_name": "Machine Learning",
            "impact": 95,
        },
    }


# ============================================================================
# Test: Evolution History
# ============================================================================


class TestEvolutionHistory:
    """Tests for taxonomy evolution history tracking"""

    @pytest.mark.asyncio
    async def test_record_evolution_event(self, sample_evolution_event):
        """Should record evolution event to history"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_store_event", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = True

            result = await service.record_event(sample_evolution_event)

            assert result is True
            mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_by_taxonomy(self):
        """Should retrieve history for a taxonomy"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_events", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"event_id": "evt_1", "event_type": "category_added"},
                {"event_id": "evt_2", "event_type": "category_merged"},
            ]

            history = await service.get_history(
                taxonomy_id="tax_main",
                limit=100,
            )

            assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_history_by_date_range(self):
        """Should filter history by date range"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_events", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()

            history = await service.get_history(
                taxonomy_id="tax_main",
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_create_snapshot(self, sample_taxonomy_version):
        """Should create taxonomy snapshot"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_store_snapshot", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = "snap_001"

            snapshot_id = await service.create_snapshot(
                taxonomy_id="tax_main",
                categories=sample_taxonomy_version["categories"],
                metadata={"reason": "pre-evolution backup"},
            )

            assert snapshot_id is not None
            assert snapshot_id.startswith("snap_")


# ============================================================================
# Test: Versioning
# ============================================================================


class TestVersioning:
    """Tests for taxonomy versioning"""

    @pytest.mark.asyncio
    async def test_create_version(self, sample_taxonomy_version):
        """Should create new taxonomy version"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_store_version", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = "v_002"

            version_id = await service.create_version(
                taxonomy_id="tax_main",
                categories=sample_taxonomy_version["categories"],
                version_number="1.1.0",
                created_by="user_admin",
            )

            assert version_id is not None

    @pytest.mark.asyncio
    async def test_get_version(self, sample_taxonomy_version):
        """Should retrieve specific version"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_version", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_taxonomy_version

            version = await service.get_version(
                taxonomy_id="tax_main",
                version_id="v_001",
            )

            assert version is not None
            assert version["version_number"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_list_versions(self):
        """Should list all versions of a taxonomy"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_versions", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"version_id": "v_001", "version_number": "1.0.0"},
                {"version_id": "v_002", "version_number": "1.1.0"},
            ]

            versions = await service.list_versions(taxonomy_id="tax_main")

            assert len(versions) >= 1

    @pytest.mark.asyncio
    async def test_compare_versions(self, sample_taxonomy_version):
        """Should compare two versions"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        v1 = sample_taxonomy_version.copy()
        v2 = sample_taxonomy_version.copy()
        v2["categories"].append({"id": "cat_4", "name": "New Category"})

        with patch.object(service, "_fetch_version", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [v1, v2]

            diff = await service.compare_versions(
                taxonomy_id="tax_main",
                version_a="v_001",
                version_b="v_002",
            )

            assert "added" in diff or "removed" in diff or "modified" in diff


# ============================================================================
# Test: Rollback
# ============================================================================


class TestRollback:
    """Tests for taxonomy rollback functionality"""

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, sample_taxonomy_version):
        """Should rollback taxonomy to previous version"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_version", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_taxonomy_version

            with patch.object(service, "_apply_version", new_callable=AsyncMock) as mock_apply:
                mock_apply.return_value = True

                result = await service.rollback_to_version(
                    taxonomy_id="tax_main",
                    target_version="v_001",
                    reason="Reverting due to errors",
                )

                assert result["success"] is True
                assert result["rolled_back_to"] == "v_001"

    @pytest.mark.asyncio
    async def test_rollback_creates_backup(self, sample_taxonomy_version):
        """Should create backup before rollback"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "create_snapshot", new_callable=AsyncMock) as mock_snap:
            mock_snap.return_value = "snap_backup"

            with patch.object(service, "_fetch_version", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = sample_taxonomy_version

                with patch.object(service, "_fetch_versions", new_callable=AsyncMock) as mock_versions:
                    mock_versions.return_value = [{"version_id": "v_current"}]

                    with patch.object(service, "_apply_version", new_callable=AsyncMock):
                        result = await service.rollback_to_version(
                            taxonomy_id="tax_main",
                            target_version="v_001",
                            create_backup=True,
                        )

                        assert "backup_snapshot" in result

    @pytest.mark.asyncio
    async def test_rollback_records_event(self, sample_taxonomy_version):
        """Should record rollback in history"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_version", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_taxonomy_version

            with patch.object(service, "_apply_version", new_callable=AsyncMock):
                with patch.object(service, "record_event", new_callable=AsyncMock) as mock_record:
                    mock_record.return_value = True

                    await service.rollback_to_version(
                        taxonomy_id="tax_main",
                        target_version="v_001",
                    )

                    mock_record.assert_called_once()


# ============================================================================
# Test: Rate Limiting
# ============================================================================


class TestRateLimiting:
    """Tests for suggestion rate limiting"""

    @pytest.mark.asyncio
    async def test_check_rate_limit(self):
        """Should check if rate limit allows action"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        # First request should be allowed
        allowed = service.check_rate_limit(
            key="suggestions:tax_main",
            limit=10,
            window_seconds=3600,
        )

        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Should block when rate limit exceeded"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        # Simulate hitting limit
        for _ in range(10):
            service.check_rate_limit("suggestions:tax_main", limit=10, window_seconds=3600)

        # Next request should be blocked
        allowed = service.check_rate_limit(
            key="suggestions:tax_main",
            limit=10,
            window_seconds=3600,
        )

        assert allowed is False

    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self):
        """Should return current rate limit status"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        # Make some requests
        for _ in range(5):
            service.check_rate_limit("suggestions:tax_main", limit=10, window_seconds=3600)

        status = service.get_rate_limit_status("suggestions:tax_main")

        assert status["remaining"] <= 10
        assert "reset_at" in status


# ============================================================================
# Test: Admin Approval Workflow
# ============================================================================


class TestApprovalWorkflow:
    """Tests for admin approval workflow"""

    @pytest.mark.asyncio
    async def test_create_approval_request(self, sample_approval_request):
        """Should create approval request"""
        from apps.api.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService()

        with patch.object(service, "_store_request", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = sample_approval_request["request_id"]

            request_id = await service.create_request(
                suggestion_id="sug_merge_001",
                taxonomy_id="tax_main",
                request_type="merge",
                details=sample_approval_request["details"],
            )

            assert request_id is not None

    @pytest.mark.asyncio
    async def test_approve_request(self, sample_approval_request):
        """Should approve pending request"""
        from apps.api.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService()

        with patch.object(service, "_fetch_request", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_approval_request

            with patch.object(service, "_update_request", new_callable=AsyncMock) as mock_update:
                mock_update.return_value = True

                result = await service.approve(
                    request_id=sample_approval_request["request_id"],
                    approver="admin_user",
                    comment="Looks good",
                )

                assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_reject_request(self, sample_approval_request):
        """Should reject pending request"""
        from apps.api.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService()

        with patch.object(service, "_fetch_request", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_approval_request

            with patch.object(service, "_update_request", new_callable=AsyncMock) as mock_update:
                mock_update.return_value = True

                result = await service.reject(
                    request_id=sample_approval_request["request_id"],
                    rejector="admin_user",
                    reason="Not enough evidence",
                )

                assert result["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_list_pending_requests(self):
        """Should list pending approval requests"""
        from apps.api.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService()

        with patch.object(service, "_fetch_pending", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {"request_id": "req_1", "status": "pending"},
                {"request_id": "req_2", "status": "pending"},
            ]

            pending = await service.list_pending(taxonomy_id="tax_main")

            assert len(pending) == 2
            assert all(r["status"] == "pending" for r in pending)

    @pytest.mark.asyncio
    async def test_auto_approve_high_confidence(self):
        """Should auto-approve high confidence suggestions"""
        from apps.api.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService()

        result = service.should_auto_approve(
            confidence=0.95,
            impact_score=0.3,
            auto_approve_threshold=0.9,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_no_auto_approve_low_confidence(self):
        """Should not auto-approve low confidence suggestions"""
        from apps.api.services.approval_workflow import ApprovalWorkflowService

        service = ApprovalWorkflowService()

        result = service.should_auto_approve(
            confidence=0.7,
            impact_score=0.3,
            auto_approve_threshold=0.9,
        )

        assert result is False


# ============================================================================
# Test: Background Job Management
# ============================================================================


class TestBackgroundJobs:
    """Tests for background job management"""

    @pytest.mark.asyncio
    async def test_queue_generation_job(self):
        """Should queue taxonomy generation job"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_enqueue_job", new_callable=AsyncMock) as mock_enqueue:
            mock_enqueue.return_value = "job_001"

            job_id = await service.queue_generation_job(
                taxonomy_id="tax_main",
                document_ids=["doc_1", "doc_2"],
                config={"n_clusters": 5},
            )

            assert job_id is not None

    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Should get job status"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_fetch_job_status", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "job_id": "job_001",
                "status": "running",
                "progress": 0.5,
            }

            status = await service.get_job_status("job_001")

            assert status["status"] == "running"
            assert status["progress"] == 0.5

    @pytest.mark.asyncio
    async def test_cancel_job(self):
        """Should cancel running job"""
        from apps.api.services.evolution_history import EvolutionHistoryService

        service = EvolutionHistoryService()

        with patch.object(service, "_cancel_job", new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = True

            result = await service.cancel_job("job_001")

            assert result is True
