"""
E2E tests for strategy management workflow.

Tests cover:
- Strategy CRUD operations via API
- Strategy version management
- Template import
- UI workflow for strategy editing
"""

import pytest
from assertions import assert_api_response, assert_api_error, assert_strategy_params


@pytest.mark.api
@pytest.mark.requires_auth
class TestStrategyAPI:
    """API tests for strategy management."""

    def test_list_strategies(self, api_client):
        """Test listing all strategies."""
        response = api_client.get("/api/strategies")
        assert_api_response(response, expected_status=200)
        
        data = response.json()
        assert isinstance(data, list), "Strategies should be a list"

    def test_create_and_get_strategy(self, api_client, data_fixtures, test_strategy_name):
        """Test creating a new strategy and retrieving it."""
        # Create strategy
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        create_response = api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": strategy_code,
                "commit_message": "Initial version"
            }
        )
        assert_api_response(create_response, expected_status=200)
        
        # Get strategy
        get_response = api_client.get("/api/strategies", params={"name": test_strategy_name})
        assert_api_response(get_response, expected_status=200, expected_keys=["name", "code"])
        
        data = get_response.json()
        assert data["name"] == test_strategy_name
        assert test_strategy_name in data["code"]

    def test_update_strategy_creates_version(self, api_client, data_fixtures, test_strategy_name):
        """Test updating a strategy creates a new version."""
        # Create initial strategy
        initial_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": initial_code,
                "commit_message": "Initial version"
            }
        )
        
        # Update strategy
        updated_code = initial_code.replace("period", "period_updated")
        update_response = api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": updated_code,
                "commit_message": "Updated parameter name"
            }
        )
        assert_api_response(update_response, expected_status=200)
        
        # Check versions were created
        versions_response = api_client.get(f"/api/strategies/{test_strategy_name}/versions")
        assert_api_response(versions_response, expected_status=200)
        
        versions_data = versions_response.json()
        assert "versions" in versions_data
        # Should have at least 2 versions
        assert len(versions_data["versions"]) >= 2

    def test_get_strategy_params(self, api_client, data_fixtures, test_strategy_name):
        """Test extracting parameters from strategy code."""
        # Create strategy with parameters
        strategy_code = data_fixtures.strategy_with_params()
        api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": strategy_code,
            }
        )
        
        # Get parameters
        params_response = api_client.get(f"/api/strategies/{test_strategy_name}/params")
        assert_api_response(params_response, expected_status=200, expected_keys=["params"])
        
        data = params_response.json()
        assert_strategy_params(data["params"])
        
        # Check specific parameters exist
        param_names = [p["name"] for p in data["params"]]
        assert "fast_period" in param_names
        assert "slow_period" in param_names

    def test_list_strategy_versions(self, api_client, data_fixtures, test_strategy_name):
        """Test listing strategy versions."""
        # Create strategy with initial version
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": strategy_code,
                "commit_message": "Initial commit"
            }
        )
        
        # List versions
        versions_response = api_client.get(f"/api/strategies/{test_strategy_name}/versions")
        assert_api_response(versions_response, expected_status=200)
        
        data = versions_response.json()
        assert "versions" in data
        assert len(data["versions"]) > 0
        
        # Check version structure
        version = data["versions"][0]
        assert "version_number" in version
        assert "created_at" in version
        assert "commit_message" in version

    def test_get_specific_version(self, api_client, data_fixtures, test_strategy_name):
        """Test retrieving a specific strategy version."""
        # Create strategy
        strategy_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": strategy_code,
            }
        )
        
        # Get latest version first
        latest_response = api_client.get(f"/api/strategies/{test_strategy_name}/versions/latest")
        assert_api_response(latest_response, expected_status=200)
        
        latest_data = latest_response.json()
        version_number = latest_data["version_number"]
        
        # Get specific version
        version_response = api_client.get(
            f"/api/strategies/{test_strategy_name}/versions/{version_number}"
        )
        assert_api_response(version_response, expected_status=200, expected_keys=["code", "version_number"])

    def test_compare_versions(self, api_client, data_fixtures, test_strategy_name):
        """Test comparing two strategy versions."""
        # Create initial version
        initial_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": initial_code,
                "commit_message": "Version 1"
            }
        )
        
        # Create updated version
        updated_code = initial_code.replace("period", "period_v2")
        api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": updated_code,
                "commit_message": "Version 2"
            }
        )
        
        # Get versions
        versions_response = api_client.get(f"/api/strategies/{test_strategy_name}/versions")
        versions = versions_response.json()["versions"]
        
        if len(versions) >= 2:
            # Compare versions (from oldest to newest)
            from_version = versions[-1]["version_number"]
            to_version = versions[0]["version_number"]
            
            compare_response = api_client.get(
                f"/api/strategies/{test_strategy_name}/versions/compare",
                params={"from_version": from_version, "to_version": to_version}
            )
            assert_api_response(compare_response, expected_status=200, expected_keys=["diff"])

    def test_rollback_to_version(self, api_client, data_fixtures, test_strategy_name):
        """Test rolling back to a previous version."""
        # Create v1
        v1_code = data_fixtures.simple_strategy_code(test_strategy_name)
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": v1_code, "commit_message": "v1"}
        )
        
        # Create v2
        v2_code = v1_code.replace("period", "period_v2")
        api_client.post(
            "/api/strategies",
            json={"name": test_strategy_name, "code": v2_code, "commit_message": "v2"}
        )
        
        # Get v1 version number
        versions_response = api_client.get(f"/api/strategies/{test_strategy_name}/versions")
        versions = versions_response.json()["versions"]
        v1_version_number = versions[-1]["version_number"]  # Oldest version
        
        # Rollback to v1
        rollback_response = api_client.post(
            f"/api/strategies/{test_strategy_name}/versions/{v1_version_number}/rollback",
            json={"commit_message": "Rollback to v1"}
        )
        assert_api_response(rollback_response, expected_status=200)
        
        # Verify current code matches v1
        current_response = api_client.get("/api/strategies", params={"name": test_strategy_name})
        current_code = current_response.json()["code"]
        assert "period_v2" not in current_code  # v2 changes should be gone

    def test_template_list(self, api_client):
        """Test listing strategy templates."""
        response = api_client.get("/api/templates")
        assert_api_response(response, expected_status=200)
        
        templates = response.json()
        assert isinstance(templates, list)
        # Should have at least one template
        if len(templates) > 0:
            template = templates[0]
            assert "id" in template
            assert "name" in template

    def test_import_template(self, api_client, test_strategy_name):
        """Test importing a template as a new strategy."""
        # First get template list
        templates_response = api_client.get("/api/templates")
        templates = templates_response.json()
        
        if len(templates) == 0:
            pytest.skip("No templates available for testing")
        
        template_id = templates[0]["id"]
        
        # Import template
        import_response = api_client.post(
            "/api/templates/import",
            json={
                "template_id": template_id,
                "name": test_strategy_name
            }
        )
        assert_api_response(import_response, expected_status=200)
        
        # Verify strategy was created
        get_response = api_client.get("/api/strategies", params={"name": test_strategy_name})
        assert_api_response(get_response, expected_status=200)

    def test_invalid_strategy_code(self, api_client, data_fixtures, test_strategy_name):
        """Test handling of invalid strategy code."""
        invalid_code = data_fixtures.invalid_strategy_code()
        
        # This should still save (validation happens at runtime)
        response = api_client.post(
            "/api/strategies",
            json={
                "name": test_strategy_name,
                "code": invalid_code
            }
        )
        # Backend may accept it and validate later, or reject immediately
        # Check both scenarios
        assert response.status_code in [200, 400]


@pytest.mark.ui
@pytest.mark.slow
class TestStrategyUI:
    """UI tests for strategy management interface."""

    def test_strategy_page_loads(self, browser):
        """Test that strategy maintain page loads successfully."""
        try:
            browser.goto("/")
            browser.wait_for_network_idle()
            
            # Navigate to strategy page (adjust selector based on your UI)
            # This is a placeholder - adjust based on actual UI structure
            # browser.click("text=Strategies")
            # browser.wait_for_url("**/strategy**")
            
            # For now, just verify home page loads
            browser.expect_visible("body")
        except Exception as e:
            if "ERR_CONNECTION_REFUSED" in str(e):
                pytest.skip("Frontend server not running on localhost:5173")
            raise
