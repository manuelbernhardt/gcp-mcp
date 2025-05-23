"""
Secret Manager MCP tools for Google Cloud Platform.
"""

from google.cloud import secretmanager
from google.api_core.exceptions import NotFound
from fastmcp import FastMCP

secret_manager_mcp = FastMCP("gcp-secret-manager")

@secret_manager_mcp.tool()
async def list_secrets(project_id: str, prefix: str = "") -> list[str]:
    """List all secrets in the project"""
    return await _list_secrets(project_id, prefix)

@secret_manager_mcp.tool()
async def delete_secret(secret_name: str, project_id: str) -> dict[str, str]:
    """Delete a secret from Google Cloud Secret Manager"""
    await _delete_secret(secret_name, project_id)
    return {"status": "success", "message": f"Secret '{secret_name}' successfully deleted from project '{project_id}'"}

@secret_manager_mcp.tool()
async def add_secret(secret_name: str, project_id: str, secret_value: str) -> dict[str, str]:
    """Add a new secret or a new version to an existing secret in Google Cloud Secret Manager"""
    version_name = await _add_secret(secret_name, project_id, secret_value)
    return {"status": "success", "message": f"Secret '{secret_name}' added/updated in project '{project_id}'. New version: {version_name}"}

@secret_manager_mcp.tool()
async def get_secret_value(secret_name: str, project_id: str) -> dict[str, str]:
    """Get a secret value from Google Cloud Secret Manager"""
    try:
        value = await _get_secret(secret_name, project_id)
        return {"status": "success", "value": value}
    except Exception as e:
        return {"status": "error", "message": f"Error retrieving secret: {str(e)}"}


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


if __name__ == "__main__":
    secret_manager_mcp.run(transport='stdio') 