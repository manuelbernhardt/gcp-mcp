import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from google.api_core.exceptions import NotFound

# Import the functions to test
import secret_manager
# Only import helper functions, not tool functions that are defined inside init
from secret_manager import _list_secrets, _delete_secret, _add_secret, _get_secret, secret_manager_mcp


# Renamed for clarity: Tests for the MCP tool endpoints
class TestSecretManagerMCPTools(unittest.IsolatedAsyncioTestCase):
    """Test cases for Secret Manager MCP tool functions"""

    async def asyncSetUp(self):
        self.mcp = secret_manager_mcp

    @patch('secret_manager._get_secret', new_callable=AsyncMock)
    async def test_get_secret_value_tool_successful(self, mock_helper_get_secret):
        """Test get_secret_value tool when successful"""
        from fastmcp import Client
        
        mock_helper_get_secret.return_value = "test-secret-value"
        
        async with Client(self.mcp) as client:
            result = await client.call_tool("get_secret_value", {"secret_name": "test-secret", "project_id": "test-project"})
            
            mock_helper_get_secret.assert_called_once_with("test-secret", "test-project")
            # Parse the result text as it will be JSON
            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data["status"], "success")
            self.assertEqual(result_data["value"], "test-secret-value")

    @patch('secret_manager._get_secret', new_callable=AsyncMock)
    async def test_get_secret_value_tool_error(self, mock_helper_get_secret):
        """Test get_secret_value tool when error occurs"""
        from fastmcp import Client
        
        mock_helper_get_secret.side_effect = Exception("Secret access error")
        
        async with Client(self.mcp) as client:
            result = await client.call_tool("get_secret_value", {"secret_name": "test-secret", "project_id": "test-project"})
            
            mock_helper_get_secret.assert_called_once_with("test-secret", "test-project")
            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data["status"], "error")
            self.assertIn("Secret access error", result_data["message"])

    @patch('secret_manager._list_secrets', new_callable=AsyncMock)
    async def test_list_secrets_tool(self, mock_helper_list_secrets):
        """Test list_secrets tool"""
        from fastmcp import Client
        
        expected_secrets = ["secret1", "secret2"]
        mock_helper_list_secrets.return_value = expected_secrets
        
        async with Client(self.mcp) as client:
            result = await client.call_tool("list_secrets", {"project_id": "test-project", "prefix": "test-"})
            
            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data, expected_secrets)
            mock_helper_list_secrets.assert_called_once_with("test-project", "test-")

    @patch('secret_manager._delete_secret', new_callable=AsyncMock)
    async def test_delete_secret_tool(self, mock_helper_delete_secret):
        """Test delete_secret tool"""
        from fastmcp import Client
        
        # _delete_secret doesn't return a value, the tool wraps it
        mock_helper_delete_secret.return_value = None 

        async with Client(self.mcp) as client:
            result = await client.call_tool("delete_secret", {"secret_name": "test-secret", "project_id": "test-project"})
            
            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data["status"], "success")
            self.assertIn("successfully deleted", result_data["message"])
            mock_helper_delete_secret.assert_called_once_with("test-secret", "test-project")

    @patch('secret_manager._add_secret', new_callable=AsyncMock)
    async def test_add_secret_tool(self, mock_helper_add_secret):
        """Test add_secret tool"""
        from fastmcp import Client
        
        version_name = "projects/test-project/secrets/test-secret/versions/1"
        mock_helper_add_secret.return_value = version_name

        async with Client(self.mcp) as client:
            result = await client.call_tool("add_secret", {
                "secret_name": "test-secret", 
                "project_id": "test-project", 
                "secret_value": "supersecret"
            })

            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data["status"], "success")
            self.assertIn(f"New version: {version_name}", result_data["message"])
            mock_helper_add_secret.assert_called_once_with("test-secret", "test-project", "supersecret")


class TestSecretManagerFunctions(unittest.TestCase):
    """Test cases for Secret Manager functions"""

    @patch('secret_manager.secretmanager.SecretManagerServiceClient')
    def test_get_secret(self, mock_client_class):
        """Test getting a secret value"""
        # Mock setup
        mock_client = mock_client_class.return_value
        
        # Create mock response
        mock_response = MagicMock()
        mock_payload = MagicMock()
        mock_payload.data = b"test-secret-value"
        mock_response.payload = mock_payload
        
        mock_client.access_secret_version.return_value = mock_response
        
        # Call the function
        result = asyncio.run(_get_secret("test-secret", "test-project"))
        
        # Assertions
        mock_client.access_secret_version.assert_called_once_with(
            name="projects/test-project/secrets/test-secret/versions/latest"
        )
        self.assertEqual(result, "test-secret-value")

    @patch('secret_manager.secretmanager.SecretManagerServiceClient')
    def test_list_secrets(self, mock_client_class):
        """Test listing secrets"""
        # Mock setup
        mock_client = mock_client_class.return_value
        mock_client.project_path.return_value = "projects/test-project"
        
        # Mock secret objects
        mock_secret1 = MagicMock()
        mock_secret1.name = "projects/test-project/secrets/test-secret-1"
        mock_secret2 = MagicMock()
        mock_secret2.name = "projects/test-project/secrets/test-secret-2"
        
        # Set up the mock to return our test data
        mock_client.list_secrets.return_value = [mock_secret1, mock_secret2]
        
        # Call the function and get result
        result = asyncio.run(_list_secrets("test-project"))
        
        # Assertions
        mock_client.project_path.assert_called_once_with("test-project")
        mock_client.list_secrets.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertIn("projects/test-project/secrets/test-secret-1", result)
        self.assertIn("projects/test-project/secrets/test-secret-2", result)

    @patch('secret_manager.secretmanager.SecretManagerServiceClient')
    def test_delete_secret(self, mock_client_class):
        """Test deleting a secret"""
        # Mock setup
        mock_client = mock_client_class.return_value
        
        # Call the function
        asyncio.run(_delete_secret("test-secret", "test-project"))
        
        # Assertions
        mock_client.delete_secret.assert_called_once_with(name="projects/test-project/secrets/test-secret")

    @patch('secret_manager.secretmanager.SecretManagerServiceClient')
    def test_add_secret_existing(self, mock_client_class):
        """Test adding a new version to an existing secret"""
        # Mock setup
        mock_client = mock_client_class.return_value
        mock_client.get_secret.return_value = MagicMock()  # Secret exists
        
        mock_version = MagicMock()
        mock_version.name = "projects/test-project/secrets/test-secret/versions/1"
        mock_client.add_secret_version.return_value = mock_version
        
        # Call the function
        result = asyncio.run(_add_secret("test-secret", "test-project", "secret-value"))
        
        # Assertions
        mock_client.get_secret.assert_called_once_with(name="projects/test-project/secrets/test-secret")
        mock_client.add_secret_version.assert_called_once()
        self.assertEqual(result, "projects/test-project/secrets/test-secret/versions/1")

    @patch('secret_manager.secretmanager.SecretManagerServiceClient')
    def test_add_secret_new(self, mock_client_class):
        """Test creating a new secret"""
        # Mock setup
        mock_client = mock_client_class.return_value
        mock_client.get_secret.side_effect = NotFound("Secret not found")
        
        mock_secret = MagicMock()
        mock_secret.name = "projects/test-project/secrets/test-secret"
        mock_client.create_secret.return_value = mock_secret
        
        mock_version = MagicMock()
        mock_version.name = "projects/test-project/secrets/test-secret/versions/1"
        mock_client.add_secret_version.return_value = mock_version
        
        # Call the function
        result = asyncio.run(_add_secret("test-secret", "test-project", "secret-value"))
        
        # Assertions
        mock_client.get_secret.assert_called_once_with(name="projects/test-project/secrets/test-secret")
        mock_client.create_secret.assert_called_once()
        mock_client.add_secret_version.assert_called_once()
        self.assertEqual(result, "projects/test-project/secrets/test-secret/versions/1")


if __name__ == "__main__":
    unittest.main() 