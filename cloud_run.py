"""
Cloud Run MCP tools for Google Cloud Platform.
"""

from google.cloud import run_v2
from google.api_core.exceptions import NotFound
from fastmcp import FastMCP

cloud_run_mcp = FastMCP("gcp-cloud-run")

@cloud_run_mcp.tool()
async def list_cloud_run_services(project_id: str, region: str) -> list[dict[str, str]]:
    """List all Cloud Run services in the specified project and region"""
    services = await _list_cloud_run_services(project_id, region)
    return services

@cloud_run_mcp.tool()
async def delete_cloud_run_service(service_name: str, project_id: str, region: str) -> dict[str, str]:
    """Delete a Cloud Run service from Google Cloud Run"""
    result = await _delete_cloud_run_service(service_name, project_id, region)
    return result

@cloud_run_mcp.tool()
async def get_cloud_run_service_logs(service_name: str, project_id: str, region: str, limit: int = 100) -> list[dict]:
    """Get the latest logs for a Cloud Run service (default 100 lines)"""
    logs = await _get_cloud_run_service_logs(service_name, project_id, region, limit)
    return logs


#
# Helper functions for Cloud Run services
#
async def _list_cloud_run_services(project_id: str, region: str) -> list[dict[str, str]]:
    """List all Cloud Run services in a project and region"""
    try:
        client = run_v2.ServicesClient()
        parent = f"projects/{project_id}/locations/{region}"
        
        services = []
        for service in client.list_services(parent=parent):
            service_info = {
                "name": service.name.split("/")[-1],
                "uri": service.uri if hasattr(service, 'uri') else "N/A",
            }
            services.append(service_info)
        
        return services
    except Exception as e:
        return [{"error": f"Error listing Cloud Run services: {str(e)}"}]

async def _delete_cloud_run_service(service_name: str, project_id: str, region: str) -> dict[str, str]:
    """Delete a Cloud Run service"""
    try:
        client = run_v2.ServicesClient()
        name = f"projects/{project_id}/locations/{region}/services/{service_name}"
        
        # First check if the service exists
        try:
            client.get_service(name=name)
        except NotFound:
            return {"status": "error", "message": f"Service '{service_name}' not found in project '{project_id}' region '{region}'"}
        
        # If service exists, delete it
        operation = client.delete_service(name=name)
        # Wait for the operation to complete
        operation.result()
        return {"status": "success", "message": f"Service '{service_name}' successfully deleted"}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting service: {str(e)}"}

async def _get_cloud_run_service_logs(service_name: str, project_id: str, region: str, limit: int = 100) -> list[dict]:
    """Fetch the latest logs for a Cloud Run service using Cloud Logging API"""
    from google.cloud import logging_v2
    import datetime
    client = logging_v2.Client(project=project_id)
    # Filter for logs from the specific Cloud Run service
    filter_str = (
        f'resource.type="cloud_run_revision" '
        f'AND resource.labels.service_name="{service_name}" '
        f'AND resource.labels.location="{region}"'
    )
    try:
        entries = client.list_entries(
            filter_=filter_str,
            order_by=logging_v2.DESCENDING,
            page_size=limit
        )
        logs = []
        for entry in entries:
            logs.append({
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "severity": entry.severity,
                "log_name": entry.log_name,
                "text_payload": getattr(entry, 'text_payload', None),
                "json_payload": getattr(entry, 'json_payload', None),
                "labels": getattr(entry, 'labels', None),
            })
        return logs
    except Exception as e:
        return [{"error": f"Error fetching logs: {str(e)}"}]


if __name__ == "__main__":
    cloud_run_mcp.run(transport='stdio') 