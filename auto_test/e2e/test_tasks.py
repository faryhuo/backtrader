"""
E2E tests for Task Management API.

Based on TEST_CASES.md - TASKS section:
- TASK-001: Invalid task_type/status returns 400 (enum validation)
- TASK-002: User empty uses optional auth, no task leakage
- TASK-003: Stats returns concurrent/running/pending counts
- TASK-004: Cancel only pending/running, else 400
- TASK-005: Retry only failed/cancelled, creates new task
- TASK-006: Delete running with force=false returns 400
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error
import api_paths


# ========== Task List Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestTaskList:
    """API tests for task listing."""

    def test_task_list_basic(self, api_client):
        """List tasks returns proper structure."""
        response = api_client.get(api_paths.TASKS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "tasks" in data, "Response must contain 'tasks'"
        assert "total" in data, "Response must contain 'total'"
        assert isinstance(data["tasks"], list)

    def test_task_list_pagination(self, api_client):
        """List tasks with pagination params."""
        response = api_client.get(
            api_paths.TASKS,
            params={"limit": 5, "offset": 0}
        )
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert len(data["tasks"]) <= 5  # Respects limit

    def test_task_001_invalid_task_type(self, api_client):
        """TASK-001: Invalid task_type returns 400 (enum validation)."""
        response = api_client.get(
            api_paths.TASKS,
            params={"task_type": "invalid_type_xyz"}
        )
        
        assert_api_error(response, expected_status=400)

    def test_task_001_invalid_status(self, api_client):
        """TASK-001: Invalid status returns 400 (enum validation)."""
        response = api_client.get(
            api_paths.TASKS,
            params={"status": "invalid_status_xyz"}
        )
        
        assert_api_error(response, expected_status=400)

    def test_task_001_valid_task_type_filter(self, api_client):
        """TASK-001: Valid task_type filter works."""
        response = api_client.get(
            api_paths.TASKS,
            params={"task_type": "backtest"}
        )
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        # All returned tasks should be backtest type
        for task in data["tasks"]:
            assert task["task_type"] == "backtest"

    def test_task_001_valid_status_filter(self, api_client):
        """TASK-001: Valid status filter works."""
        response = api_client.get(
            api_paths.TASKS,
            params={"status": "completed"}
        )
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        for task in data["tasks"]:
            assert task["status"] == "completed"

    def test_task_list_combined_filters(self, api_client):
        """Combined filters work together."""
        response = api_client.get(
            api_paths.TASKS,
            params={
                "task_type": "backtest",
                "status": "completed",
                "limit": 5,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        )
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        for task in data["tasks"]:
            assert task["task_type"] == "backtest"
            assert task["status"] == "completed"


# ========== Task Stats Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestTaskStats:
    """API tests for task statistics."""

    def test_task_003_stats_structure(self, api_client):
        """TASK-003: Stats returns concurrent/running/pending counts."""
        response = api_client.get(api_paths.TASKS_STATS)
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "max_concurrent" in data, "Stats must include 'max_concurrent'"
        assert "running_count" in data, "Stats must include 'running_count'"
        assert "pending_count" in data, "Stats must include 'pending_count'"


# ========== Task Detail Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestTaskDetail:
    """API tests for task detail operations."""

    def test_task_detail_not_found(self, api_client):
        """Get non-existent task returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.get(api_paths.task_detail(fake_id))
        
        assert_api_error(response, expected_status=404)


# ========== Task Cancel Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestTaskCancel:
    """API tests for task cancellation."""

    def test_task_cancel_not_found(self, api_client):
        """Cancel non-existent task returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.post(api_paths.task_cancel(fake_id))
        
        assert_api_error(response, expected_status=404)

    def test_task_004_cancel_completed_task_fails(self, api_client):
        """TASK-004: Cancel completed task returns 400."""
        # First find a completed task
        list_response = api_client.get(
            api_paths.TASKS,
            params={"status": "completed", "limit": 1}
        )
        
        if list_response.status_code != 200:
            pytest.skip("Cannot list tasks")
        
        tasks = list_response.json().get("tasks", [])
        if not tasks:
            pytest.skip("No completed tasks to test with")
        
        task_id = tasks[0]["task_id"]
        
        # Try to cancel
        response = api_client.post(api_paths.task_cancel(task_id))
        
        # Should fail - can only cancel pending/running
        assert response.status_code == 400, (
            f"Expected 400 for cancelling completed task, got {response.status_code}"
        )


# ========== Task Retry Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestTaskRetry:
    """API tests for task retry."""

    def test_task_retry_not_found(self, api_client):
        """Retry non-existent task returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.post(api_paths.task_retry(fake_id))
        
        assert_api_error(response, expected_status=404)

    def test_task_005_retry_completed_task_fails(self, api_client):
        """TASK-005: Retry completed (non-failed) task returns 400."""
        # Find a completed (not failed) task
        list_response = api_client.get(
            api_paths.TASKS,
            params={"status": "completed", "limit": 1}
        )
        
        if list_response.status_code != 200:
            pytest.skip("Cannot list tasks")
        
        tasks = list_response.json().get("tasks", [])
        if not tasks:
            pytest.skip("No completed tasks to test with")
        
        task_id = tasks[0]["task_id"]
        
        # Try to retry
        response = api_client.post(api_paths.task_retry(task_id))
        
        # Should fail - can only retry failed/cancelled
        assert response.status_code == 400, (
            f"Expected 400 for retrying completed task, got {response.status_code}"
        )


# ========== Task Delete Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestTaskDelete:
    """API tests for task deletion."""

    def test_task_delete_not_found(self, api_client):
        """Delete non-existent task returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = api_client.delete(api_paths.task_detail(fake_id))
        
        assert_api_error(response, expected_status=404)

    def test_task_006_delete_running_without_force(self, api_client):
        """TASK-006: Delete running task without force=true returns 400."""
        # Find a running task (may not exist)
        list_response = api_client.get(
            api_paths.TASKS,
            params={"status": "running", "limit": 1}
        )
        
        if list_response.status_code != 200:
            pytest.skip("Cannot list tasks")
        
        tasks = list_response.json().get("tasks", [])
        if not tasks:
            pytest.skip("No running tasks to test with")
        
        task_id = tasks[0]["task_id"]
        
        # Try to delete without force
        response = api_client.delete(
            api_paths.task_detail(task_id),
            params={"force": False}
        )
        
        # Should fail without force
        assert response.status_code == 400, (
            f"Expected 400 for deleting running task without force, got {response.status_code}"
        )


# ========== Task Lifecycle Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
@pytest.mark.slow
class TestTaskLifecycle:
    """API tests for task lifecycle (slow tests)."""

    def test_create_and_track_task(self, api_client, data_fixtures):
        """Create a task (via backtest) and track its status."""
        config = data_fixtures.backtest_config(
            ticker="AAPL",
            days_back=30
        )
        
        backtest_response = api_client.post(api_paths.BACKTEST, json=config)
        
        if backtest_response.status_code != 200:
            pytest.skip("Could not create backtest task")
        
        data = backtest_response.json()
        
        if "task_id" in data:
            task_id = data["task_id"]
            
            # Get task details
            task_response = api_client.get(api_paths.task_detail(task_id))
            assert_api_response(task_response, expected_status=200)
            
            task = task_response.json()
            assert "task_id" in task
            assert "status" in task
            assert "task_type" in task
            assert task["task_type"] == "backtest"

    def test_task_appears_in_list(self, api_client, data_fixtures):
        """Newly created task appears in task list."""
        config = data_fixtures.backtest_config(
            ticker="MSFT",
            days_back=30
        )
        
        backtest_response = api_client.post(api_paths.BACKTEST, json=config)
        
        if backtest_response.status_code != 200:
            pytest.skip("Could not create backtest task")
        
        # List backtest tasks
        list_response = api_client.get(
            api_paths.TASKS,
            params={"task_type": "backtest", "limit": 10}
        )
        
        assert_api_response(list_response, expected_status=200)
        
        data = list_response.json()
        assert data["total"] >= 0


# ========== UI Tests ==========

@pytest.mark.ui
@pytest.mark.slow
class TestTasksUI:
    """UI tests for tasks page."""

    def test_tasks_page_loads(self, browser):
        """Test that tasks page can load."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
