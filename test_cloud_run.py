import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from google.api_core.exceptions import NotFound

# Import the functions to test
import cloud_run
from cloud_run import _list_cloud_run_services, _delete_cloud_run_service, _get_cloud_run_service_logs, cloud_run_mcp


class TestCloudRunHelperFunctions(unittest.TestCase):
    """Test cases for Cloud Run helper functions"""

    @patch('cloud_run.run_v2.ServicesClient')
    def test_list_cloud_run_services_valid_region(self, mock_services_client):
        """Test listing Cloud Run services with a valid region"""
        mock_client = mock_services_client.return_value
        mock_service = MagicMock()
        mock_service.name = "projects/test-project/locations/us-central1/services/test-service"
        mock_service.uri = "https://test-service-xyz.run.app"
        mock_client.list_services.return_value = [mock_service]
        
        result = asyncio.run(_list_cloud_run_services("test-project", "us-central1"))
        
        mock_client.list_services.assert_called_once_with(parent="projects/test-project/locations/us-central1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test-service")
        self.assertEqual(result[0]["uri"], "https://test-service-xyz.run.app")

    @patch('cloud_run.run_v2.ServicesClient')
    def test_delete_cloud_run_service(self, mock_client_class):
        """Test deleting a Cloud Run service"""
        mock_client = mock_client_class.return_value
        mock_operation = MagicMock()
        mock_client.delete_service.return_value = mock_operation
        
        result = asyncio.run(_delete_cloud_run_service("test-service", "test-project", "us-central1"))
        
        mock_client.delete_service.assert_called_once_with(
            name="projects/test-project/locations/us-central1/services/test-service"
        )
        mock_operation.result.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch('cloud_run.run_v2.ServicesClient')
    def test_delete_cloud_run_service_not_found(self, mock_client_class):
        """Test deleting a nonexistent Cloud Run service"""
        mock_client = mock_client_class.return_value
        mock_client.get_service.side_effect = NotFound("Service not found")
        
        result = asyncio.run(_delete_cloud_run_service("nonexistent-service", "test-project", "us-central1"))
        
        mock_client.get_service.assert_called_once_with(
            name="projects/test-project/locations/us-central1/services/nonexistent-service"
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])

    @patch('google.cloud.logging_v2.Client')
    def test_get_cloud_run_service_logs(self, mock_logging_client):
        """Test fetching logs for a Cloud Run service"""
        mock_client = mock_logging_client.return_value
        mock_entry = MagicMock()
        mock_entry.timestamp = None
        mock_entry.severity = "INFO"
        mock_entry.log_name = "projects/test-project/logs/run.googleapis.com%2Fstdout"
        mock_entry.text_payload = "Test log entry"
        mock_entry.json_payload = None
        mock_entry.labels = {"test": "label"}
        mock_client.list_entries.return_value = [mock_entry]

        result = asyncio.run(_get_cloud_run_service_logs("test-service", "test-project", "us-central1", 10))
        mock_client.list_entries.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text_payload"], "Test log entry")
        self.assertEqual(result[0]["severity"], "INFO")
        self.assertIsNone(result[0]["timestamp"])

    @patch('google.cloud.logging_v2.Client')
    def test_get_cloud_run_service_logs_error(self, mock_logging_client):
        """Test error handling when fetching logs"""
        mock_client = mock_logging_client.return_value
        mock_client.list_entries.side_effect = Exception("Logging error")
        result = asyncio.run(_get_cloud_run_service_logs("test-service", "test-project", "us-central1", 10))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["error"], "Error fetching logs: Logging error")


class TestCloudRunMCPTools(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mcp = cloud_run_mcp

    @patch('cloud_run._list_cloud_run_services', new_callable=AsyncMock)
    async def test_list_cloud_run_services_tool(self, mock_helper_list_services):
        """Test list_cloud_run_services tool"""
        from fastmcp import Client
        
        expected_services = [{"name": "service1", "uri": "uri1"}]
        mock_helper_list_services.return_value = expected_services
        
        async with Client(self.mcp) as client:
            result = await client.call_tool("list_cloud_run_services", {"project_id": "test-project", "region": "us-central1"})
            
            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data, expected_services)
            mock_helper_list_services.assert_called_once_with("test-project", "us-central1")

    @patch('cloud_run._delete_cloud_run_service', new_callable=AsyncMock)
    async def test_delete_cloud_run_service_tool(self, mock_helper_delete_service):
        """Test delete_cloud_run_service tool"""
        from fastmcp import Client
        
        expected_response = {"status": "success", "message": "Service 'test-service' successfully deleted"}
        mock_helper_delete_service.return_value = expected_response

        async with Client(self.mcp) as client:
            result = await client.call_tool("delete_cloud_run_service", {
                "service_name": "test-service", 
                "project_id": "test-project", 
                "region": "us-central1"
            })

            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data, expected_response)
            mock_helper_delete_service.assert_called_once_with("test-service", "test-project", "us-central1")

    @patch('cloud_run._get_cloud_run_service_logs', new_callable=AsyncMock)
    async def test_get_cloud_run_service_logs_tool(self, mock_helper_get_logs):
        """Test get_cloud_run_service_logs tool"""
        from fastmcp import Client
        
        expected_logs = [{"timestamp": "sometime", "text_payload": "log message"}]
        mock_helper_get_logs.return_value = expected_logs

        async with Client(self.mcp) as client:
            result = await client.call_tool("get_cloud_run_service_logs", {
                "service_name": "test-service", 
                "project_id": "test-project", 
                "region": "us-central1", 
                "limit": 50
            })
            
            import json
            result_data = json.loads(result[0].text)
            self.assertEqual(result_data, expected_logs)
            mock_helper_get_logs.assert_called_once_with("test-service", "test-project", "us-central1", 50)


if __name__ == "__main__":
    unittest.main() 