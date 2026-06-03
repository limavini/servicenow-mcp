"""
Tests for the update set tools.

This module contains tests for the update set tools in the ServiceNow MCP server.
"""

import unittest
from unittest.mock import MagicMock, patch

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.update_set_tools import (
    AddFileToUpdateSetParams,
    CommitUpdateSetParams,
    CreateUpdateSetParams,
    GetUpdateSetDetailsParams,
    ListUpdateSetsParams,
    PublishUpdateSetParams,
    UpdateUpdateSetParams,
    add_file_to_update_set,
    commit_update_set,
    create_update_set,
    get_update_set_details,
    list_update_sets,
    publish_update_set,
    update_update_set,
)
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig


class TestUpdateSetTools(unittest.TestCase):
    """Tests for the update set tools."""

    def setUp(self):
        """Set up test fixtures."""
        auth_config = AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(
                username="test_user",
                password="test_password"
            )
        )
        self.server_config = ServerConfig(
            instance_url="https://test.service-now.com",
            auth=auth_config,
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Bearer test"}

    @patch("servicenow_mcp.tools.update_set_tools.requests.get")
    def test_list_update_sets(self, mock_get):
        """Test listing update sets."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "123",
                    "name": "Test Update set",
                    "state": "in_progress",
                    "application": "Test App",
                    "developer": "test.user",
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call the function
        params = {
            "limit": 10,
            "offset": 0,
            "state": "in_progress",
            "application": "Test App",
            "developer": "test.user",
        }
        result = list_update_sets(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["update_sets"]), 1)
        self.assertEqual(result["update_sets"][0]["sys_id"], "123")
        self.assertEqual(result["update_sets"][0]["name"], "Test Update set")

        # Verify the API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://test.service-now.com/api/now/table/sys_update_set")
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer test"})
        self.assertEqual(kwargs["params"]["sysparm_limit"], 10)
        self.assertEqual(kwargs["params"]["sysparm_offset"], 0)
        self.assertIn("sysparm_query", kwargs["params"])
        self.assertIn("state=in_progress", kwargs["params"]["sysparm_query"])
        self.assertIn("application=Test App", kwargs["params"]["sysparm_query"])
        self.assertIn("developer=test.user", kwargs["params"]["sysparm_query"])

    @patch("servicenow_mcp.tools.update_set_tools.requests.get")
    def test_get_update_set_details(self, mock_get):
        """Test getting update set details."""
        # Mock responses
        mock_update_set_response = MagicMock()
        mock_update_set_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Update set",
                "state": "in_progress",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_update_set_response.raise_for_status.return_value = None

        mock_changes_response = MagicMock()
        mock_changes_response.json.return_value = {
            "result": [
                {
                    "sys_id": "456",
                    "name": "test_file.py",
                    "type": "file",
                    "update_set": "123",
                }
            ]
        }
        mock_changes_response.raise_for_status.return_value = None

        # Set up the mock to return different responses for different URLs
        def side_effect(*args, **kwargs):
            url = args[0]
            if "sys_update_set" in url:
                return mock_update_set_response
            elif "sys_update_xml" in url:
                return mock_changes_response
            return None

        mock_get.side_effect = side_effect

        # Call the function
        params = {"update_set_id": "123"}
        result = get_update_set_details(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["update_set"]["sys_id"], "123")
        self.assertEqual(result["update_set"]["name"], "Test Update set")
        self.assertEqual(len(result["changes"]), 1)
        self.assertEqual(result["changes"][0]["sys_id"], "456")
        self.assertEqual(result["changes"][0]["name"], "test_file.py")

        # Verify the API calls
        self.assertEqual(mock_get.call_count, 2)
        first_call_args, first_call_kwargs = mock_get.call_args_list[0]
        self.assertEqual(
            first_call_args[0], "https://test.service-now.com/api/now/table/sys_update_set/123"
        )
        self.assertEqual(first_call_kwargs["headers"], {"Authorization": "Bearer test"})

        second_call_args, second_call_kwargs = mock_get.call_args_list[1]
        self.assertEqual(
            second_call_args[0], "https://test.service-now.com/api/now/table/sys_update_xml"
        )
        self.assertEqual(second_call_kwargs["headers"], {"Authorization": "Bearer test"})
        self.assertEqual(second_call_kwargs["params"]["sysparm_query"], "update_set=123")

    @patch("servicenow_mcp.tools.update_set_tools.requests.post")
    def test_create_update_set(self, mock_post):
        """Test creating an update set."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Update set",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Call the function
        params = {
            "name": "Test Update set",
            "application": "Test App",
            "developer": "test.user",
            "description": "Test description",
        }
        result = create_update_set(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["update_set"]["sys_id"], "123")
        self.assertEqual(result["update_set"]["name"], "Test Update set")
        self.assertEqual(result["message"], "Update set created successfully")

        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://test.service-now.com/api/now/table/sys_update_set")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["json"]["name"], "Test Update set")
        self.assertEqual(kwargs["json"]["application"], "Test App")
        self.assertEqual(kwargs["json"]["developer"], "test.user")
        self.assertEqual(kwargs["json"]["description"], "Test description")

    @patch("servicenow_mcp.tools.update_set_tools.requests.patch")
    def test_update_update_set(self, mock_patch):
        """Test updating an update set."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Updated Update set",
                "state": "in_progress",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        # Call the function
        params = {
            "update_set_id": "123",
            "name": "Updated Update set",
            "state": "in_progress",
        }
        result = update_update_set(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["update_set"]["sys_id"], "123")
        self.assertEqual(result["update_set"]["name"], "Updated Update set")
        self.assertEqual(result["message"], "Update set updated successfully")

        # Verify the API call
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(
            args[0], "https://test.service-now.com/api/now/table/sys_update_set/123"
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["json"]["name"], "Updated Update set")
        self.assertEqual(kwargs["json"]["state"], "in_progress")

    @patch("servicenow_mcp.tools.update_set_tools.requests.patch")
    def test_commit_update_set(self, mock_patch):
        """Test committing an update set."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Update set",
                "state": "complete",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        # Call the function
        params = {
            "update_set_id": "123",
            "commit_message": "Commit message",
        }
        result = commit_update_set(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["update_set"]["sys_id"], "123")
        self.assertEqual(result["update_set"]["state"], "complete")
        self.assertEqual(result["message"], "Update set committed successfully")

        # Verify the API call
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(
            args[0], "https://test.service-now.com/api/now/table/sys_update_set/123"
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["json"]["state"], "complete")
        self.assertEqual(kwargs["json"]["description"], "Commit message")

    @patch("servicenow_mcp.tools.update_set_tools.requests.patch")
    def test_publish_update_set(self, mock_patch):
        """Test publishing an update set."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Update set",
                "state": "published",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        # Call the function
        params = {
            "update_set_id": "123",
            "publish_notes": "Publish notes",
        }
        result = publish_update_set(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["update_set"]["sys_id"], "123")
        self.assertEqual(result["update_set"]["state"], "published")
        self.assertEqual(result["message"], "Update set published successfully")

        # Verify the API call
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        self.assertEqual(
            args[0], "https://test.service-now.com/api/now/table/sys_update_set/123"
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["json"]["state"], "published")
        self.assertEqual(kwargs["json"]["description"], "Publish notes")

    @patch("servicenow_mcp.tools.update_set_tools.requests.post")
    def test_add_file_to_update_set(self, mock_post):
        """Test adding a file to an update set."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "456",
                "name": "test_file.py",
                "type": "file",
                "update_set": "123",
                "payload": "print('Hello, world!')",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Call the function
        params = {
            "update_set_id": "123",
            "file_path": "test_file.py",
            "file_content": "print('Hello, world!')",
        }
        result = add_file_to_update_set(self.auth_manager, self.server_config, params)

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["file"]["sys_id"], "456")
        self.assertEqual(result["file"]["name"], "test_file.py")
        self.assertEqual(result["message"], "File added to update set successfully")

        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://test.service-now.com/api/now/table/sys_update_xml")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["json"]["update_set"], "123")
        self.assertEqual(kwargs["json"]["name"], "test_file.py")
        self.assertEqual(kwargs["json"]["payload"], "print('Hello, world!')")
        self.assertEqual(kwargs["json"]["type"], "file")


class TestUpdateSetToolsParams(unittest.TestCase):
    """Tests for the update set tools parameter classes."""

    def test_list_update_sets_params(self):
        """Test ListUpdateSetsParams."""
        params = ListUpdateSetsParams(
            limit=20,
            offset=10,
            state="in_progress",
            application="Test App",
            developer="test.user",
            timeframe="recent",
            query="name=test",
        )
        self.assertEqual(params.limit, 20)
        self.assertEqual(params.offset, 10)
        self.assertEqual(params.state, "in_progress")
        self.assertEqual(params.application, "Test App")
        self.assertEqual(params.developer, "test.user")
        self.assertEqual(params.timeframe, "recent")
        self.assertEqual(params.query, "name=test")

    def test_get_update_set_details_params(self):
        """Test GetUpdateSetDetailsParams."""
        params = GetUpdateSetDetailsParams(update_set_id="123")
        self.assertEqual(params.update_set_id, "123")

    def test_create_update_set_params(self):
        """Test CreateUpdateSetParams."""
        params = CreateUpdateSetParams(
            name="Test Update set",
            description="Test description",
            application="Test App",
            developer="test.user",
        )
        self.assertEqual(params.name, "Test Update set")
        self.assertEqual(params.description, "Test description")
        self.assertEqual(params.application, "Test App")
        self.assertEqual(params.developer, "test.user")

    def test_update_update_set_params(self):
        """Test UpdateUpdateSetParams."""
        params = UpdateUpdateSetParams(
            update_set_id="123",
            name="Updated Update set",
            description="Updated description",
            state="in_progress",
            developer="test.user",
        )
        self.assertEqual(params.update_set_id, "123")
        self.assertEqual(params.name, "Updated Update set")
        self.assertEqual(params.description, "Updated description")
        self.assertEqual(params.state, "in_progress")
        self.assertEqual(params.developer, "test.user")

    def test_commit_update_set_params(self):
        """Test CommitUpdateSetParams."""
        params = CommitUpdateSetParams(
            update_set_id="123",
            commit_message="Commit message",
        )
        self.assertEqual(params.update_set_id, "123")
        self.assertEqual(params.commit_message, "Commit message")

    def test_publish_update_set_params(self):
        """Test PublishUpdateSetParams."""
        params = PublishUpdateSetParams(
            update_set_id="123",
            publish_notes="Publish notes",
        )
        self.assertEqual(params.update_set_id, "123")
        self.assertEqual(params.publish_notes, "Publish notes")

    def test_add_file_to_update_set_params(self):
        """Test AddFileToUpdateSetParams."""
        params = AddFileToUpdateSetParams(
            update_set_id="123",
            file_path="test_file.py",
            file_content="print('Hello, world!')",
        )
        self.assertEqual(params.update_set_id, "123")
        self.assertEqual(params.file_path, "test_file.py")
        self.assertEqual(params.file_content, "print('Hello, world!')")


if __name__ == "__main__":
    unittest.main() 