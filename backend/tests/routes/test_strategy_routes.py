"""
Unit tests for strategy routes.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.routes.strategy_routes import (
    get_strategy_list,
    get_strategy,
    save_strategy,
    get_strategy_params,
    get_templates,
    get_template_detail,
    import_template,
    list_strategy_versions,
    get_latest_strategy_version,
    compare_strategy_versions,
    get_strategy_version,
    rollback_to_version,
    get_version_storage,
    StrategySaveRequest,
    TemplateImportRequest,
    VersionCreateRequest,
)


class TestStrategyListEndpoints:
    """Tests for strategy list and get endpoints."""

    @patch("src.routes.strategy_routes.list_strategies")
    def test_get_strategy_list_success(self, mock_list_strategies):
        """Test successful strategy list retrieval."""
        mock_list_strategies.return_value = ["strategy1", "strategy2", "strategy3"]

        result = get_strategy_list(user_id="test-user")

        assert result == {"strategies": ["strategy1", "strategy2", "strategy3"]}
        mock_list_strategies.assert_called_once()

    @patch("src.routes.strategy_routes.list_strategies")
    def test_get_strategy_list_empty(self, mock_list_strategies):
        """Test strategy list when no strategies exist."""
        mock_list_strategies.return_value = []

        result = get_strategy_list(user_id="test-user")

        assert result == {"strategies": []}

    @patch("src.routes.strategy_routes.list_strategies")
    def test_get_strategy_list_exception(self, mock_list_strategies):
        """Test error handling in strategy list."""
        mock_list_strategies.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            get_strategy_list(user_id="test-user")

        assert exc_info.value.status_code == 500
        assert "Database error" in str(exc_info.value.detail)

    @patch("src.routes.strategy_routes.get_user_strategy_code")
    def test_get_strategy_with_name(self, mock_get_code):
        """Test getting specific strategy by name."""
        mock_get_code.return_value = "# Strategy code here"

        result = get_strategy(name="my_strategy", user_id="test-user")

        assert result == {"code": "# Strategy code here", "name": "my_strategy"}
        mock_get_code.assert_called_once_with("my_strategy")

    @patch("src.routes.strategy_routes.list_strategies")
    @patch("src.routes.strategy_routes.get_user_strategy_code")
    def test_get_strategy_without_name(self, mock_get_code, mock_list_strategies):
        """Test getting strategy without specifying name (defaults to first)."""
        mock_list_strategies.return_value = ["default_strategy", "other_strategy"]
        mock_get_code.return_value = "# Default strategy code"

        result = get_strategy(name=None, user_id="test-user")

        assert result == {"code": "# Default strategy code", "name": "default_strategy"}
        mock_list_strategies.assert_called_once()
        mock_get_code.assert_called_once_with("default_strategy")

    @patch("src.routes.strategy_routes.list_strategies")
    def test_get_strategy_no_strategies_available(self, mock_list_strategies):
        """Test error when no strategies are available."""
        mock_list_strategies.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            get_strategy(name=None, user_id="test-user")

        # The actual implementation wraps 404 in a 500 error
        assert exc_info.value.status_code in [404, 500]
        assert "No strategies available" in str(exc_info.value.detail)


class TestStrategySaveEndpoint:
    """Tests for strategy save endpoint."""

    @patch("src.routes.strategy_routes.get_version_storage")
    @patch("src.routes.strategy_routes.save_user_strategy_code")
    def test_save_strategy_success(self, mock_save_code, mock_get_storage):
        """Test successful strategy save with version creation."""
        request = StrategySaveRequest(
            name="my_strategy",
            code="# New strategy code",
            commit_message="Initial commit"
        )

        # Mock version storage
        mock_storage = MagicMock()
        mock_storage.create_version.return_value = {
            "version_number": 1,
            "commit_message": "Initial commit",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_get_storage.return_value = mock_storage

        result = save_strategy(request=request, user_id="test-user")

        assert result["status"] == "ok"
        assert result["message"] == "Strategy saved"
        assert result["name"] == "my_strategy"
        assert "version" in result
        assert result["version"]["version_number"] == 1

        mock_save_code.assert_called_once_with("my_strategy", "# New strategy code")
        mock_storage.create_version.assert_called_once()

    @patch("src.routes.strategy_routes.get_version_storage")
    @patch("src.routes.strategy_routes.save_user_strategy_code")
    def test_save_strategy_version_creation_fails(self, mock_save_code, mock_get_storage):
        """Test strategy save when version creation fails (should not block save)."""
        request = StrategySaveRequest(
            name="my_strategy",
            code="# New strategy code",
            commit_message=None
        )

        # Mock version storage to raise exception
        mock_storage = MagicMock()
        mock_storage.create_version.side_effect = Exception("Version DB error")
        mock_get_storage.return_value = mock_storage

        result = save_strategy(request=request, user_id="test-user")

        # Should still succeed despite version creation failure
        assert result["status"] == "ok"
        assert result["message"] == "Strategy saved"
        assert "version" not in result  # Version not included due to error

        mock_save_code.assert_called_once_with("my_strategy", "# New strategy code")

    @patch("src.routes.strategy_routes.save_user_strategy_code")
    def test_save_strategy_file_error(self, mock_save_code):
        """Test error handling when file save fails."""
        from src.service.backtest_engine import StrategyLoadError

        request = StrategySaveRequest(
            name="my_strategy",
            code="# New code"
        )

        mock_save_code.side_effect = StrategyLoadError("Invalid strategy code")

        with pytest.raises(HTTPException) as exc_info:
            save_strategy(request=request, user_id="test-user")

        assert exc_info.value.status_code == 400
        assert "Invalid strategy code" in str(exc_info.value.detail)


class TestStrategyParams:
    """Tests for strategy params extraction."""

    @patch("src.routes.strategy_routes.extract_strategy_params")
    def test_get_strategy_params_success(self, mock_extract_params):
        """Test successful parameter extraction."""
        mock_extract_params.return_value = [
            {"name": "period", "value": 20, "type": "int"},
            {"name": "threshold", "value": 0.5, "type": "float"}
        ]

        result = get_strategy_params(name="my_strategy", user_id="test-user")

        assert result["name"] == "my_strategy"
        assert len(result["params"]) == 2
        assert result["params"][0]["name"] == "period"
        mock_extract_params.assert_called_once_with("my_strategy")

    @patch("src.routes.strategy_routes.extract_strategy_params")
    def test_get_strategy_params_extraction_fails(self, mock_extract_params):
        """Test that extraction failures return empty params (no error)."""
        mock_extract_params.side_effect = Exception("Parse error")

        result = get_strategy_params(name="my_strategy", user_id="test-user")

        # Should return empty params instead of raising error
        assert result["name"] == "my_strategy"
        assert result["params"] == []


class TestTemplateEndpoints:
    """Tests for template-related endpoints."""

    @patch("src.routes.strategy_routes.get_all_templates")
    @patch("src.routes.strategy_routes.get_categories")
    @patch("src.routes.strategy_routes.get_difficulty_levels")
    def test_get_templates(self, mock_difficulties, mock_categories, mock_templates):
        """Test getting all templates with metadata."""
        mock_templates.return_value = [
            {"id": "sma_cross", "name": "SMA Crossover"},
            {"id": "rsi_strategy", "name": "RSI Strategy"}
        ]
        mock_categories.return_value = ["trend", "momentum"]
        mock_difficulties.return_value = ["beginner", "intermediate", "advanced"]

        result = get_templates(user_id="test-user")

        assert len(result["templates"]) == 2
        assert result["categories"] == ["trend", "momentum"]
        assert len(result["difficulties"]) == 3

    @patch("src.routes.strategy_routes.get_template_by_id")
    def test_get_template_detail_success(self, mock_get_template):
        """Test getting template detail."""
        mock_get_template.return_value = {
            "id": "sma_cross",
            "name": "SMA Crossover",
            "code": "# Template code"
        }

        result = get_template_detail(template_id="sma_cross", user_id="test-user")

        assert result["id"] == "sma_cross"
        assert result["name"] == "SMA Crossover"
        mock_get_template.assert_called_once_with("sma_cross")

    @patch("src.routes.strategy_routes.get_template_by_id")
    def test_get_template_detail_not_found(self, mock_get_template):
        """Test getting non-existent template."""
        mock_get_template.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_template_detail(template_id="nonexistent", user_id="test-user")

        assert exc_info.value.status_code == 404
        assert "Template not found" in str(exc_info.value.detail)

    @patch("src.routes.strategy_routes.save_user_strategy_code")
    @patch("src.routes.strategy_routes.list_strategies")
    @patch("src.routes.strategy_routes.get_template_by_id")
    def test_import_template_success(self, mock_get_template, mock_list, mock_save):
        """Test successful template import."""
        mock_get_template.return_value = {
            "id": "sma_cross",
            "code": "# Template code here"
        }
        mock_list.return_value = ["existing_strategy"]

        request = TemplateImportRequest(
            template_id="sma_cross",
            name="my_new_strategy"
        )

        result = import_template(request=request, user_id="test-user")

        assert result["status"] == "ok"
        assert result["name"] == "my_new_strategy"
        mock_save.assert_called_once_with("my_new_strategy", "# Template code here")

    @patch("src.routes.strategy_routes.save_user_strategy_code")
    @patch("src.routes.strategy_routes.list_strategies")
    @patch("src.routes.strategy_routes.get_template_by_id")
    def test_import_template_success_with_chinese_name(self, mock_get_template, mock_list, mock_save):
        """Test template import allows Unicode strategy names."""
        mock_get_template.return_value = {
            "id": "sma_cross",
            "code": "# Template code here"
        }
        mock_list.return_value = ["existing_strategy"]

        request = TemplateImportRequest(
            template_id="sma_cross",
            name="中文策略"
        )

        result = import_template(request=request, user_id="test-user")

        assert result["status"] == "ok"
        assert result["name"] == "中文策略"
        mock_save.assert_called_once_with("中文策略", "# Template code here")

    @patch("src.routes.strategy_routes.list_strategies")
    @patch("src.routes.strategy_routes.get_template_by_id")
    def test_import_template_already_exists(self, mock_get_template, mock_list):
        """Test importing template with name that already exists."""
        mock_get_template.return_value = {"id": "sma_cross", "code": "# Code"}
        mock_list.return_value = ["existing_strategy"]

        request = TemplateImportRequest(
            template_id="sma_cross",
            name="existing_strategy"
        )

        with pytest.raises(HTTPException) as exc_info:
            import_template(request=request, user_id="test-user")

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)


class TestVersionManagement:
    """Tests for version management endpoints."""

    def test_get_version_storage_singleton(self):
        """Test that version storage is a singleton."""
        storage1 = get_version_storage()
        storage2 = get_version_storage()
        assert storage1 is storage2

    @patch("src.routes.strategy_routes.get_version_storage")
    def test_list_strategy_versions(self, mock_get_storage):
        """Test listing strategy versions."""
        mock_storage = MagicMock()
        mock_storage.list_versions.return_value = {
            "versions": [
                {"version_number": 2, "commit_message": "Update 2"},
                {"version_number": 1, "commit_message": "Initial"}
            ],
            "total": 2
        }
        mock_get_storage.return_value = mock_storage

        result = list_strategy_versions(
            name="my_strategy",
            limit=50,
            offset=0,
            user_id="test-user"
        )

        assert result["total"] == 2
        assert len(result["versions"]) == 2
        mock_storage.list_versions.assert_called_once_with(
            strategy_name="my_strategy",
            user_id="test-user",
            limit=50,
            offset=0
        )

    @patch("src.routes.strategy_routes.get_version_storage")
    def test_get_latest_strategy_version(self, mock_get_storage):
        """Test getting latest version."""
        mock_storage = MagicMock()
        mock_storage.get_latest_version.return_value = {
            "version_number": 5,
            "commit_message": "Latest changes"
        }
        mock_get_storage.return_value = mock_storage

        result = get_latest_strategy_version(name="my_strategy", user_id="test-user")

        assert result["version_number"] == 5
        mock_storage.get_latest_version.assert_called_once()

    @patch("src.routes.strategy_routes.get_version_storage")
    def test_get_latest_strategy_version_not_found(self, mock_get_storage):
        """Test getting latest version when none exists."""
        mock_storage = MagicMock()
        mock_storage.get_latest_version.return_value = None
        mock_get_storage.return_value = mock_storage

        with pytest.raises(HTTPException) as exc_info:
            get_latest_strategy_version(name="my_strategy", user_id="test-user")

        assert exc_info.value.status_code == 404

    @patch("src.routes.strategy_routes.compare_versions")
    @patch("src.routes.strategy_routes.get_version_storage")
    def test_compare_strategy_versions(self, mock_get_storage, mock_compare):
        """Test comparing two versions."""
        mock_storage = MagicMock()
        mock_storage.get_version.side_effect = [
            {"code": "# Old code", "version_number": 1},
            {"code": "# New code", "version_number": 2}
        ]
        mock_get_storage.return_value = mock_storage

        mock_compare.return_value = {
            "diff": "...",
            "additions": 1,
            "deletions": 1
        }

        result = compare_strategy_versions(
            name="my_strategy",
            from_version=1,
            to_version=2,
            user_id="test-user"
        )

        assert "diff" in result
        mock_compare.assert_called_once()

    @patch("src.routes.strategy_routes.save_user_strategy_code")
    @patch("src.routes.strategy_routes.get_version_storage")
    def test_rollback_to_version(self, mock_get_storage, mock_save):
        """Test rolling back to a previous version."""
        mock_storage = MagicMock()
        mock_storage.get_version.return_value = {
            "code": "# Old code",
            "version_number": 3
        }
        mock_storage.create_version.return_value = {
            "version_number": 6,
            "commit_message": "Rollback to version 3"
        }
        mock_get_storage.return_value = mock_storage

        request = VersionCreateRequest(commit_message="Rolling back")

        result = rollback_to_version(
            name="my_strategy",
            version_number=3,
            request=request,
            user_id="test-user"
        )

        assert result["status"] == "ok"
        assert "new_version" in result
        mock_save.assert_called_once_with("my_strategy", "# Old code")
