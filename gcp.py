from mcp.server.fastmcp import FastMCP
from google.cloud import secretmanager, run_v2
from google.cloud import resourcemanager_v3
from google.api_core.exceptions import NotFound

mcp = FastMCP("gcp")


@mcp.tool()
async def list_secrets(project_id: str, prefix: str = "") -> list[str]:
    """List all secrets in the project"""
    return await _list_secrets(project_id, prefix)

@mcp.tool()
async def delete_secret(secret_name: str, project_id: str) -> dict[str, str]:
    """Delete a secret from Google Cloud Secret Manager"""
    await _delete_secret(secret_name, project_id)
    return {"status": "success", "message": f"Secret '{secret_name}' successfully deleted from project '{project_id}'"}

@mcp.tool()
async def add_secret(secret_name: str, project_id: str, secret_value: str) -> dict[str, str]:
    """Add a new secret or a new version to an existing secret in Google Cloud Secret Manager"""
    version_name = await _add_secret(secret_name, project_id, secret_value)
    return {"status": "success", "message": f"Secret '{secret_name}' added/updated in project '{project_id}'. New version: {version_name}"}

@mcp.tool()
async def get_secret_value(secret_name: str, project_id: str) -> dict[str, str]:
    """Get a secret value from Google Cloud Secret Manager"""
    try:
        value = await _get_secret(secret_name, project_id)
        return {"status": "success", "value": value}
    except Exception as e:
        return {"status": "error", "message": f"Error retrieving secret: {str(e)}"}

@mcp.tool()
async def list_cloud_run_services(project_id: str, region: str) -> list[dict[str, str]]:
    """List all Cloud Run services in the specified project and region"""
    services = await _list_cloud_run_services(project_id, region)
    return services

@mcp.tool()
async def delete_cloud_run_service(service_name: str, project_id: str, region: str) -> dict[str, str]:
    """Delete a Cloud Run service from Google Cloud Run"""
    result = await _delete_cloud_run_service(service_name, project_id, region)
    return result


#
# Helper functions for GCP projects
#
async def _list_projects() -> list[str]:
    """List all GCP projects the user has access to"""
    client = resourcemanager_v3.ProjectsClient()
    projects = client.list_projects()
    return [{"name": project.display_name, "id": project.project_id} for project in projects]

#
# Helper functions for secret management
#
async def _get_secret(secret_name: str, project_id: str) -> str:
    """Get a secret from Google Cloud Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")
    
async def _list_secrets(project_id: str, prefix: str = "") -> list[str]:
    """List all secrets in the project"""
    client = secretmanager.SecretManagerServiceClient()
    parent = client.project_path(project_id)
    filter_str = f"name:{prefix}*" if prefix else ""
    return [secret.name for secret in client.list_secrets(parent=parent, filter=filter_str)]
    
async def _delete_secret(secret_name: str, project_id: str) -> None:
    """Delete a secret from Google Cloud Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}"
    client.delete_secret(name=name)
    
async def _add_secret(secret_name: str, project_id: str, secret_value: str) -> str:
    """Adds a new secret or a new version to an existing secret."""
    client = secretmanager.SecretManagerServiceClient()
    project_path = f"projects/{project_id}"
    secret_path = f"{project_path}/secrets/{secret_name}"

    try:
        # Check if secret exists
        client.get_secret(name=secret_path)
        # If secret exists, add a new version
        payload = secret_value.encode("UTF-8")
        version = client.add_secret_version(
            parent=secret_path, payload={"data": payload}
        )
        return version.name
    except NotFound:
        # If secret does not exist, create it and add a version
        secret = client.create_secret(
            parent=project_path,
            secret_id=secret_name,
            secret={"replication": {"automatic": {}}},
        )
        payload = secret_value.encode("UTF-8")
        version = client.add_secret_version(
            parent=secret.name, payload={"data": payload}
        )
        return version.name

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

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')