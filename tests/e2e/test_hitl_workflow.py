"""
E2E test for HITL (Human-in-the-Loop) workflow
Tests the complete flow from task retrieval to review submission
"""

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.api.deps import verify_api_key

# Valid test API key (generated via generate_admin_key())
TEST_API_KEY = "admin_X4RzsowY0qgfwqqwbo1UnP25zQjOoOxX5FUXmDHR9sPc8HT7-a570"


# Override API key verification for testing
async def override_verify_api_key():
    return None


@pytest.fixture(scope="module", autouse=True)
def setup_test_overrides():
    """Setup test dependency overrides"""
    app.dependency_overrides[verify_api_key] = override_verify_api_key
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_hitl_get_tasks():
    """Test retrieving HITL tasks from API"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 10},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)

        if len(tasks) > 0:
            task = tasks[0]
            assert "task_id" in task
            assert "chunk_id" in task
            assert "text" in task
            assert "suggested_classification" in task
            assert "confidence" in task
            assert "priority" in task
            assert "created_at" in task

            # Verify low confidence (HITL threshold < 0.70)
            assert task["confidence"] < 0.70

            print(f"✅ Found {len(tasks)} HITL tasks")
            print(f"   Sample task: {task['text'][:80]}...")
            print(f"   Confidence: {task['confidence']}")
        else:
            print("⚠️ No HITL tasks found (expected if database is clean)")


@pytest.mark.asyncio
async def test_hitl_submit_review():
    """Test submitting HITL review"""
    # First get a task
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 1},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert get_response.status_code == 200
        tasks = get_response.json()

        if len(tasks) == 0:
            pytest.skip("No HITL tasks available for testing")

        task = tasks[0]
        chunk_id = task["chunk_id"]
        approved_path = task["suggested_classification"]

        # Submit review
        review_data = {
            "chunk_id": chunk_id,
            "approved_path": approved_path,
            "reviewer_notes": "E2E test review - approved suggested classification",
        }

        review_response = await client.post(
            "/api/v1/classify/hitl/review",
            json=review_data,
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert review_response.status_code == 200
        result = review_response.json()

        assert "task_id" in result
        assert "status" in result
        assert result["status"] == "approved"
        assert result["updated_classification"] == approved_path

        print("✅ Successfully submitted HITL review")
        print(f"   Chunk ID: {chunk_id}")
        print(f"   Approved path: {approved_path}")

        # Verify task is no longer in queue
        verify_response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 100},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert verify_response.status_code == 200
        remaining_tasks = verify_response.json()

        # Check that the reviewed task is not in the list
        remaining_chunk_ids = [t["chunk_id"] for t in remaining_tasks]
        assert (
            chunk_id not in remaining_chunk_ids
        ), "Reviewed task should be removed from queue"

        print("✅ Verified task removed from queue")


@pytest.mark.asyncio
async def test_hitl_priority_filter():
    """Test filtering HITL tasks by priority"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test without filter
        all_response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 50},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert all_response.status_code == 200

        # Test with priority filter (if supported by backend)
        high_response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 50, "priority": "high"},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert high_response.status_code == 200
        high_tasks = high_response.json()

        # If priority filtering is implemented, high_tasks should be subset
        if len(high_tasks) > 0:
            for task in high_tasks:
                assert task["priority"] == "high"
            print(f"✅ Priority filter working: {len(high_tasks)} high priority tasks")
        else:
            print("⚠️ No high priority tasks found (expected if all are normal/low)")


@pytest.mark.asyncio
async def test_hitl_invalid_chunk_id():
    """Test submitting review with invalid chunk_id"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        review_data = {
            "chunk_id": "00000000-0000-0000-0000-000000000000",
            "approved_path": ["Technology", "AI/ML"],
            "reviewer_notes": "Test with invalid chunk_id",
        }

        response = await client.post(
            "/api/v1/classify/hitl/review",
            json=review_data,
            headers={"X-API-Key": TEST_API_KEY},
        )

        # Should return 500 (database update fails)
        assert response.status_code == 500
        print("✅ Correctly rejected invalid chunk_id")


@pytest.mark.asyncio
async def test_hitl_empty_approved_path():
    """Test submitting review with empty approved_path"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First get a real task
        get_response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 1},
            headers={"X-API-Key": TEST_API_KEY},
        )

        if len(get_response.json()) == 0:
            pytest.skip("No HITL tasks available")

        task = get_response.json()[0]

        review_data = {
            "chunk_id": task["chunk_id"],
            "approved_path": [],  # Empty path
            "reviewer_notes": "Test with empty path",
        }

        response = await client.post(
            "/api/v1/classify/hitl/review",
            json=review_data,
            headers={"X-API-Key": TEST_API_KEY},
        )

        # Should return 400 (validation error)
        assert response.status_code == 400
        print("✅ Correctly rejected empty approved_path")


@pytest.mark.asyncio
async def test_hitl_confidence_threshold():
    """Verify all HITL tasks have confidence below threshold"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/classify/hitl/tasks",
            params={"limit": 100},
            headers={"X-API-Key": TEST_API_KEY},
        )

        assert response.status_code == 200
        tasks = response.json()

        if len(tasks) == 0:
            pytest.skip("No HITL tasks available")

        # All tasks should have confidence < 0.70 (HITL threshold)
        for task in tasks:
            assert (
                task["confidence"] < 0.70
            ), f"Task {task['task_id']} has confidence {task['confidence']} >= 0.70"

        print(f"✅ All {len(tasks)} tasks below confidence threshold (< 0.70)")
        avg_confidence = sum(t["confidence"] for t in tasks) / len(tasks)
        print(f"   Average confidence: {avg_confidence:.3f}")
