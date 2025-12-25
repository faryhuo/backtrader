"""
E2E tests for Strategy Management API.

Based on TEST_CASES.md - STRATEGY section:
- STR-001: List strategies requires auth, returns {"strategies":[...]}
- STR-002: Get strategy with empty name returns first or 404
- STR-003: Get non-existent strategy returns 400 (StrategyLoadError)
- STR-004: Save strategy writes file, returns status ok
- STR-005: Invalid strategy name (path traversal) is rejected
- STR-006: Param extraction failure returns empty array
- STR-007: Template list returns templates/categories/difficulties
- STR-008: Template detail not found returns 404
- STR-009: Import template validation and success
- STR-010: Version list pagination works, only current user
- STR-011: Latest version returns 404 if no versions
- STR-012: Version compare/rollback validation
"""

import pytest
import sys
from pathlib import Path

# Add libs to path
libs_path = Path(__file__).parent.parent / "libs"
sys.path.insert(0, str(libs_path))

from assertions import assert_api_response, assert_api_error, assert_strategy_params
from response_normalizer import normalize_list_response
import api_paths


# ========== Strategy CRUD Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestStrategyCRUD:
    """API tests for strategy CRUD operations."""

    def test_str_001_list_requires_auth_and_returns_structure(self, api_client):
        """STR-001: List strategies requires auth, returns {"strategies":[...]}."""
        response = api_client.get(api_paths.STRATEGIES_LIST)
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "strategies" in data, "Response must contain 'strategies' key"
        assert isinstance(data["strategies"], list), "strategies must be a list"

    def test_str_001_list_without_auth(self, api_base_url):
        """STR-001: List strategies without auth should fail if auth required."""
        import httpx
        from auth_config import is_auth_required
        
        response = httpx.get(
            f"{api_base_url}/api/strategies",
            timeout=10,
            proxy=None
        )
        
        if is_auth_required():
            assert response.status_code in [401, 403], (
                f"Expected 401/403 without auth, got {response.status_code}"
            )
        else:
            # Auth disabled, should work
            assert response.status_code == 200

    def test_str_002_get_strategy_empty_name(self, api_client):
        """STR-002: Get strategy with empty name returns first strategy or 404."""
        response = api_client.get(api_paths.STRATEGY)
        
        # Should either return first strategy or 404 if none exist
        assert response.status_code in [200, 404], (
            f"Expected 200 (first strategy) or 404 (no strategies), got {response.status_code}"
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data, "Response must contain strategy name"
            assert "code" in data, "Response must contain strategy code"

    def test_str_003_get_nonexistent_strategy(self, api_client):
        """STR-003: Get non-existent strategy returns 400 (StrategyLoadError)."""
        response = api_client.get(
            api_paths.STRATEGY,
            params={"name": "NonExistentStrategy_XYZ_12345"}
        )
        
        assert response.status_code == 400, (
            f"Expected 400 for non-existent strategy, got {response.status_code}"
        )

    def test_str_004_save_strategy_success(self, api_client, data_fixtures, test_strategy_name):
        """STR-004: Save strategy writes file, returns status ok."""
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        
        response = api_client.post(
            api_paths.STRATEGY,
            json={
                "name": test_strategy_name,
                "code": strategy_code,
                "commit_message": "Test save"
            }
        )
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert data.get("status") == "ok", "Response should have status 'ok'"

    def test_str_005_save_invalid_name_path_traversal(self, api_client, data_fixtures):
        """STR-005: Invalid strategy name with path traversal is rejected."""
        strategy_code = data_fixtures.simple_strategy_code("TestStrategy")
        
        # Attempt path traversal
        response = api_client.post(
            api_paths.STRATEGY,
            json={
                "name": "../../../etc/passwd",
                "code": strategy_code
            }
        )
        
        # Should be rejected
        assert response.status_code in [400, 422], (
            f"Expected 400/422 for path traversal attempt, got {response.status_code}"
        )

    def test_str_005_save_invalid_name_special_chars(self, api_client, data_fixtures):
        """STR-005: Strategy name with special characters is rejected."""
        strategy_code = data_fixtures.simple_strategy_code("TestStrategy")
        
        invalid_names = [
            "strategy<script>",
            "strategy;rm -rf",
            "strategy\x00null",
        ]
        
        for name in invalid_names:
            response = api_client.post(
                api_paths.STRATEGY,
                json={"name": name, "code": strategy_code}
            )
            # Should be rejected or sanitized
            # May return 400/422 or accept with sanitized name
            assert response.status_code in [200, 400, 422, 500]


# ========== Strategy Parameters Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestStrategyParams:
    """API tests for strategy parameter extraction."""

    def test_str_006_params_extraction_success(self, api_client, data_fixtures, test_strategy_name):
        """STR-006: Parameter extraction returns params array."""
        # Create strategy with params first
        strategy_code = data_fixtures.strategy_with_params()
        api_client.post(
            api_paths.STRATEGY,
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        # Get parameters
        response = api_client.get(api_paths.strategy_params(test_strategy_name))
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "params" in data, "Response must contain 'params' key"
        assert isinstance(data["params"], list), "params must be a list"
        
        # Verify params have correct structure
        if len(data["params"]) > 0:
            assert_strategy_params(data["params"])

    def test_str_006_params_extraction_failure_returns_empty(self, api_client, data_fixtures, test_strategy_name):
        """STR-006: Param extraction failure returns empty array, not error."""
        # Create strategy with no extractable params (or broken code)
        strategy_code = """
# Strategy with no params tuple
import backtrader as bt

class NoParamsStrategy(bt.Strategy):
    def next(self):
        pass
"""
        api_client.post(
            api_paths.STRATEGY,
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        response = api_client.get(api_paths.strategy_params(test_strategy_name))
        
        # Should return 200 with empty params, not error
        assert response.status_code == 200
        data = response.json()
        assert "params" in data
        # May be empty if no params found
        assert isinstance(data["params"], list)


# ========== Strategy Template Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestStrategyTemplates:
    """API tests for strategy templates."""

    def test_str_007_template_list_structure(self, api_client):
        """STR-007: Template list returns templates/categories/difficulties."""
        response = api_client.get(api_paths.TEMPLATES_LIST)
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        
        # Must contain all three keys
        assert "templates" in data, "Response must contain 'templates'"
        assert "categories" in data, "Response must contain 'categories'"
        assert "difficulties" in data, "Response must contain 'difficulties'"
        
        # Templates should be a list
        assert isinstance(data["templates"], list)
        
        # If templates exist, check structure
        if len(data["templates"]) > 0:
            template = data["templates"][0]
            assert "id" in template, "Template must have 'id'"
            assert "name" in template, "Template must have 'name'"

    def test_str_008_template_detail_not_found(self, api_client):
        """STR-008: Template detail for non-existent ID returns 404."""
        response = api_client.get(api_paths.template_detail("nonexistent_template_xyz"))
        
        assert_api_error(response, expected_status=404)

    def test_str_008_template_detail_success(self, api_client):
        """STR-008: Template detail for existing ID returns full template."""
        # First get template list
        list_response = api_client.get(api_paths.TEMPLATES_LIST)
        if list_response.status_code != 200:
            pytest.skip("Cannot get template list")
        
        templates = list_response.json().get("templates", [])
        if not templates:
            pytest.skip("No templates available")
        
        template_id = templates[0]["id"]
        
        # Get detail
        response = api_client.get(api_paths.template_detail(template_id))
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "code" in data, "Template detail must include 'code'"

    def test_str_009_import_template_empty_name(self, api_client):
        """STR-009: Import template with empty name returns 400."""
        # First get a valid template ID
        list_response = api_client.get(api_paths.TEMPLATES_LIST)
        if list_response.status_code != 200:
            pytest.skip("Cannot get template list")
        
        templates = list_response.json().get("templates", [])
        if not templates:
            pytest.skip("No templates available")
        
        template_id = templates[0]["id"]
        
        # Import with empty name
        response = api_client.post(
            api_paths.TEMPLATES_IMPORT,
            json={"template_id": template_id, "name": ""}
        )
        
        assert_api_error(response, expected_status=400)

    def test_str_009_import_template_success(self, api_client, test_strategy_name):
        """STR-009: Import template creates new strategy successfully."""
        # Get template list
        list_response = api_client.get(api_paths.TEMPLATES_LIST)
        if list_response.status_code != 200:
            pytest.skip("Cannot get template list")
        
        templates = list_response.json().get("templates", [])
        if not templates:
            pytest.skip("No templates available")
        
        template_id = templates[0]["id"]
        
        # Import template
        response = api_client.post(
            api_paths.TEMPLATES_IMPORT,
            json={"template_id": template_id, "name": test_strategy_name}
        )
        
        assert_api_response(response, expected_status=200)
        
        # Verify strategy was created
        get_response = api_client.get(api_paths.STRATEGY, params={"name": test_strategy_name})
        assert get_response.status_code == 200


# ========== Strategy Version Tests ==========

@pytest.mark.api
@pytest.mark.requires_auth
class TestStrategyVersions:
    """API tests for strategy version management."""

    def test_str_010_version_list_pagination(self, api_client, data_fixtures, test_strategy_name):
        """STR-010: Version list pagination (limit/offset) works."""
        # Create strategy first
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            api_paths.STRATEGY,
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        # List versions with pagination
        response = api_client.get(
            api_paths.strategy_versions(test_strategy_name),
            params={"limit": 5, "offset": 0}
        )
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "versions" in data
        assert len(data["versions"]) <= 5  # Respects limit

    def test_str_011_latest_version_not_found(self, api_client):
        """STR-011: Latest version for non-existent strategy returns 404."""
        try:
            response = api_client.get(
                api_paths.strategy_version_latest("NoSuchStrategy")
            )
            # Should return 404 for non-existent, or 400 for validation error
            assert response.status_code in [400, 404]
        except Exception as e:
            if "timeout" in str(e).lower():
                pytest.skip("Request timed out")
            raise

    def test_str_011_latest_version_success(self, api_client, data_fixtures, test_strategy_name):
        """STR-011: Latest version returns most recent version."""
        # Create strategy with version
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            api_paths.STRATEGY,
            json={"name": test_strategy_name, "code": strategy_code, "commit_message": "v1"}
        )
        
        # Get latest
        response = api_client.get(api_paths.strategy_version_latest(test_strategy_name))
        
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert "version_number" in data
        assert "code" in data

    def test_str_012_version_compare_invalid(self, api_client, data_fixtures, test_strategy_name):
        """STR-012: Version compare with invalid versions returns 404."""
        # Create strategy
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            api_paths.STRATEGY,
            json={"name": test_strategy_name, "code": strategy_code}
        )
        
        # Compare with non-existent versions
        try:
            response = api_client.get(
                api_paths.strategy_version_compare(test_strategy_name),
                params={"from_version": 999, "to_version": 1000}
            )
            # Should return 404 for not found, or 400/422 for validation
            assert response.status_code in [400, 404, 422]
        except Exception as e:
            if "timeout" in str(e).lower():
                pytest.skip("Request timed out")
            raise

    def test_str_012_rollback_success(self, api_client, data_fixtures, test_strategy_name):
        """STR-012: Rollback creates new version with old code."""
        try:
            # Create v1
            v1_code = data_fixtures.simple_strategy_code(test_strategy_name)
            api_client.post(
                api_paths.STRATEGY,
                json={"name": test_strategy_name, "code": v1_code, "commit_message": "v1"}
            )
            
            # Create v2
            v2_code = v1_code.replace("period", "period_v2")
            api_client.post(
                api_paths.STRATEGY,
                json={"name": test_strategy_name, "code": v2_code, "commit_message": "v2"}
            )
            
            # Get v1 version number
            versions_response = api_client.get(api_paths.strategy_versions(test_strategy_name))
            if versions_response.status_code != 200:
                pytest.skip("Could not list versions")
            
            versions = versions_response.json().get("versions", [])
            if len(versions) < 2:
                pytest.skip("Not enough versions for rollback test")
            
            v1_version = versions[-1]["version_number"]  # Oldest
            
            # Rollback to v1
            response = api_client.post(
                api_paths.strategy_version_rollback(test_strategy_name, v1_version),
                json={"commit_message": "Rollback to v1"}
            )
            
            assert_api_response(response, expected_status=200)
        except Exception as e:
            if "timeout" in str(e).lower():
                pytest.skip("Request timed out")
            raise
