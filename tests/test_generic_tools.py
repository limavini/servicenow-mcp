import unittest
from unittest.mock import MagicMock, patch

from servicenow_mcp.tools.generic_tools import query_table, QueryTableParams
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig
from servicenow_mcp.auth.auth_manager import AuthManager


class TestGenericTools(unittest.TestCase):

    def setUp(self):
        self.auth_config = AuthConfig(
            type=AuthType.BASIC, basic=BasicAuthConfig(username="test", password="test")
        )
        self.config = ServerConfig(
            instance_url="https://dev12345.service-now.com", auth=self.auth_config
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Bearer FAKE_TOKEN"}

    @patch("requests.get")
    def test_query_table_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {"sys_id": "abc123", "name": "Web Server 01"},
                {"sys_id": "def456", "name": "Web Server 02"},
            ]
        }
        mock_get.return_value = mock_response

        params = QueryTableParams(
            table="cmdb_ci",
            query="nameLIKEWeb",
            fields=["sys_id", "name"],
            limit=5,
        )
        result = query_table(self.config, self.auth_manager, params)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["table"], "cmdb_ci")
        self.assertEqual(result["records"][0]["name"], "Web Server 01")

        # URL targets the requested table on the Table API
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://dev12345.service-now.com/api/now/table/cmdb_ci")
        # Encoded query and field selection are forwarded as sysparm_*
        self.assertEqual(kwargs["params"]["sysparm_query"], "nameLIKEWeb")
        self.assertEqual(kwargs["params"]["sysparm_fields"], "sys_id,name")
        self.assertEqual(kwargs["params"]["sysparm_limit"], 5)

    @patch("requests.get")
    def test_query_table_http_error(self, mock_get):
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        mock_get.return_value = mock_response

        params = QueryTableParams(table="sys_user")
        result = query_table(self.config, self.auth_manager, params)

        self.assertFalse(result["success"])
        self.assertIn("Error querying table", result["message"])
        self.assertEqual(result["records"], [])

    @patch.dict("os.environ", {"SERVICENOW_QUERY_TABLE_DENYLIST": "sys_user,sys_secret"})
    @patch("requests.get")
    def test_query_table_denylist_blocks(self, mock_get):
        params = QueryTableParams(table="sys_user")
        result = query_table(self.config, self.auth_manager, params)

        self.assertFalse(result["success"])
        self.assertIn("blocked", result["message"])
        mock_get.assert_not_called()

    @patch.dict("os.environ", {"SERVICENOW_QUERY_TABLE_ALLOWLIST": "cmdb_ci"})
    @patch("requests.get")
    def test_query_table_allowlist_blocks_others(self, mock_get):
        params = QueryTableParams(table="incident")
        result = query_table(self.config, self.auth_manager, params)

        self.assertFalse(result["success"])
        self.assertIn("not in", result["message"])
        mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
