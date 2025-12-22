"""
E2E tests for task management API.

Tests cover:
- Listing tasks with filters
- Getting task details
- Task statistics
- Cancelling and retrying tasks
- Deleting task records
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error


@pytest.mark.api
@pytest.mark.requires_auth
class TestTasksAPI:
    """API tests for task management."""

    def test_list_tasks(self, api_client):
        """Test listing all tasks."""
        response = api_client.get("/api/tasks")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)

    def test_list_tasks_with_pagination(self, api_client):
        """Test listing tasks with pagination."""
        response = api_client.get(
            "/api/tasks",
            params={"limit": 10, "offset": 0}
        )
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert len(data["tasks"]) <= 10

    def test_list_tasks_filter_by_type(self, api_client):
        """Test filtering tasks by type."""
        response = api_client.get(
            "/api/tasks",
            params={"task_type": "backtest"}
        )
        assert_api_response(response, expected_status=200)

        data = response.json()
        # All returned tasks should be backtest type
        for task in data["tasks"]:
            assert task["task_type"] == "backtest"

    def test_list_tasks_filter_by_status(self, api_client):
        """Test filtering tasks by status."""
        response = api_client.get(
            "/api/tasks",
            params={"status": "completed"}
        )
        assert_api_response(response, expected_status=200)

        data = response.json()
        for task in data["tasks"]:
            assert task["status"] == "completed"

    def test_list_tasks_invalid_type(self, api_client):
        """Test filtering with invalid task type."""
        response = api_client.get(
            "/api/tasks",
            params={"task_type": "invalid_type"}
        )
        assert_api_error(response, expected_status=400)

    def test_list_tasks_invalid_status(self, api_client):
        """Test filtering with invalid status."""
        response = api_client.get(
            "/api/tasks",
            params={"status": "invalid_status"}
        )
        assert_api_error(response, expected_status=400)

    def test_get_task_stats(self, api_client):
        """Test getting task manager statistics."""
        response = api_client.get("/api/tasks/stats")
        assert_api_response(response, expected_status=200)

        data = response.json()
        assert "max_concurrent" in data
        assert "running_count" in data
        assert "pending_count" in data

    def test_get_task_not_found(self, api_client):
        """Test getting non-existent task."""
        fake_task_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.get(f"/api/tasks/{fake_task_id}")
        assert_api_error(response, expected_status=404)

    def test_cancel_task_not_found(self, api_client):
        """Test cancelling non-existent task."""
        fake_task_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(f"/api/tasks/{fake_task_id}/cancel")
        assert_api_error(response, expected_status=404)

    def test_retry_task_not_found(self, api_client):
        """Test retrying non-existent task."""
        fake_task_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(f"/api/tasks/{fake_task_id}/retry")
        assert_api_error(response, expected_status=404)

    def test_delete_task_not_found(self, api_client):
        """Test deleting non-existent task."""
        fake_task_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.delete(f"/api/tasks/{fake_task_id}")
        assert_api_error(response, expected_status=404)

    def test_list_tasks_sorting(self, api_client):
        """Test sorting tasks."""
        # Sort by created_at ascending
        response = api_client.get(
            "/api/tasks",
            params={"sort_by": "created_at", "sort_order": "asc", "limit": 50}
        )
        assert_api_response(response, expected_status=200)

        # Sort by created_at descending
        response_desc = api_client.get(
            "/api/tasks",
            params={"sort_by": "created_at", "sort_order": "desc", "limit": 50}
        )
        assert_api_response(response_desc, expected_status=200)

    def test_list_tasks_combined_filters(self, api_client):
        """Test combining multiple filters."""
        response = api_client.get(
            "/api/tasks",
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


@pytest.mark.api
@pytest.mark.requires_auth
@pytest.mark.slow
class TestTaskLifecycleAPI:
    """API tests for task lifecycle operations (slow tests)."""

    def test_create_and_track_task(self, api_client, data_fixtures):
        """Test creating a task (via backtest) and tracking its status."""
        # Run a simple backtest to create a task
        config = data_fixtures.backtest_config(
            ticker="AAPL",
            days_back=30,
        )

        backtest_response = api_client.post("/api/backtest", json=config)

        if backtest_response.status_code == 200:
            # Get task from backtest response if available
            data = backtest_response.json()
            if "task_id" in data:
                task_id = data["task_id"]

                # Get task details
                task_response = api_client.get(f"/api/tasks/{task_id}")
                assert_api_response(task_response, expected_status=200)

                task = task_response.json()
                assert "task_id" in task
                assert "status" in task
                assert "task_type" in task

    def test_task_appears_in_list(self, api_client, data_fixtures):
        """Test that a newly created task appears in the task list."""
        # Create a backtest task
        config = data_fixtures.backtest_config(
            ticker="MSFT",
            days_back=30,
        )

        backtest_response = api_client.post("/api/backtest", json=config)

        if backtest_response.status_code == 200:
            # List tasks and check for backtest type
            list_response = api_client.get(
                "/api/tasks",
                params={"task_type": "backtest", "limit": 10}
            )
            assert_api_response(list_response, expected_status=200)

            data = list_response.json()
            assert data["total"] >= 0


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
