import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from google.api_core.exceptions import NotFound

# Import the functions to test
from gcp import _list_secrets, _delete_secret, _add_secret, _list_cloud_run_services, _delete_cloud_run_service, _get_secret, get_secret_value


class TestSecretManagerTools(unittest.TestCase):
    """Test cases for Secret Manager tool functions"""

    @patch('gcp._get_secret')
    def test_get_secret_value_successful(self, mock_get_secret):
        """Test get_secret_value tool when successful"""
        # Mock the underlying get_secret function
        mock_get_secret.return_value = "test-secret-value"
        
        # Call the tool function
        result = asyncio.run(get_secret_value("test-secret", "test-project"))
        
        # Assertions
        mock_get_secret.assert_called_once_with("test-secret", "test-project")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["value"], "test-secret-value")

    @patch('gcp._get_secret')
    def test_get_secret_value_error(self, mock_get_secret):
        """Test get_secret_value tool when error occurs"""
        # Mock the underlying get_secret function to raise an exception
        mock_get_secret.side_effect = Exception("Secret access error")
        
        # Call the tool function
        result = asyncio.run(get_secret_value("test-secret", "test-project"))
        
        # Assertions
        mock_get_secret.assert_called_once_with("test-secret", "test-project")
        self.assertEqual(result["status"], "error")
        self.assertIn("Secret access error", result["message"])


class TestSecretManagerFunctions(unittest.TestCase):
    """Test cases for Secret Manager functions"""

    @patch('gcp.secretmanager.SecretManagerServiceClient')
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

    @patch('gcp.secretmanager.SecretManagerServiceClient')
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

    @patch('gcp.secretmanager.SecretManagerServiceClient')
    def test_delete_secret(self, mock_client_class):
        """Test deleting a secret"""
        # Mock setup
        mock_client = mock_client_class.return_value
        
        # Call the function
        asyncio.run(_delete_secret("test-secret", "test-project"))
        
        # Assertions
        mock_client.delete_secret.assert_called_once_with(name="projects/test-project/secrets/test-secret")

    @patch('gcp.secretmanager.SecretManagerServiceClient')
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

    @patch('gcp.secretmanager.SecretManagerServiceClient')
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


class TestCloudRunFunctions(unittest.TestCase):
    """Test cases for Cloud Run functions"""

    @patch('gcp.run_v2.ServicesClient')
    def test_list_cloud_run_services_valid_region(self, mock_services_client):
        """Test listing Cloud Run services with a valid region"""
        # Mock services
        mock_client = mock_services_client.return_value
        
        # Create mock service
        mock_service = MagicMock()
        mock_service.name = "projects/test-project/locations/us-central1/services/test-service"
        mock_service.uri = "https://test-service-xyz.run.app"
        
        mock_client.list_services.return_value = [mock_service]
        
        # Call the function
        result = asyncio.run(_list_cloud_run_services("test-project", "us-central1"))
        
        # Assertions
        mock_client.list_services.assert_called_once_with(parent="projects/test-project/locations/us-central1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test-service")
        self.assertEqual(result[0]["uri"], "https://test-service-xyz.run.app")


    @patch('gcp.run_v2.ServicesClient')
    def test_delete_cloud_run_service(self, mock_client_class):
        """Test deleting a Cloud Run service"""
        # Mock setup
        mock_client = mock_client_class.return_value
        mock_operation = MagicMock()
        mock_client.delete_service.return_value = mock_operation
        
        # Call the function
        asyncio.run(_delete_cloud_run_service("test-service", "test-project", "us-central1"))
        
        # Assertions
        mock_client.delete_service.assert_called_once_with(
            name="projects/test-project/locations/us-central1/services/test-service"
        )
        mock_operation.result.assert_called_once()


if __name__ == "__main__":
    unittest.main() 