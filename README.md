# GCP-MCP: Google Cloud Platform Model Control Protocol Server

**⚠️ EXPERIMENTAL PROJECT ⚠️**

This project provides a Model Control Protocol (MCP) server for interacting with Google Cloud Platform resources.

## Overview

GCP-MCP allows AI assistants and other MCP clients to interact with Google Cloud Platform services through a standardized interface.

## Installation

### Prerequisites

- [uv](https://github.com/astral-sh/uv)
- Access to Google Cloud Platform with appropriate permissions
- Google Cloud SDK (for authentication)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/manuelbernhardt/gcp-mcp.git
   cd gcp-mcp
   ```

2. Install dependencies using `uv`:
   ```
   uv sync
   ```

3. Authenticate with Google Cloud:
   ```
   gcloud auth application-default login
   ```

## Available Tools

### Secret Manager Tools

The server provides the following tools for interacting with Google Cloud Secret Manager:

#### list_secrets

Lists all secrets in a specified GCP project.

**Parameters:**
- `project_id` (string, required): The ID of the GCP project to list secrets from
- `prefix` (string, optional): Filter secrets by prefix

**Example:**
```
list_secrets(project_id="my-gcp-project", prefix="api-")
```

#### delete_secret

Deletes a secret from Google Cloud Secret Manager.

**Parameters:**
- `secret_name` (string, required): The name of the secret to delete
- `project_id` (string, required): The ID of the GCP project containing the secret

**Example:**
```
delete_secret(secret_name="my-api-key", project_id="my-gcp-project")
```

#### add_secret

Adds a new secret or a new version to an existing secret in Google Cloud Secret Manager.

**Parameters:**
- `secret_name` (string, required): The name of the secret to add or update
- `project_id` (string, required): The ID of the GCP project
- `secret_value` (string, required): The value of the secret

**Example:**
```
add_secret(secret_name="my-new-api-key", project_id="my-gcp-project", secret_value="supersecretvalue")
```

### Cloud Run Tools

The server provides the following tools for interacting with Google Cloud Run:

#### list_cloud_run_services

Lists all Cloud Run services in a specified GCP project and region.

**Parameters:**
- `project_id` (string, required): The ID of the GCP project
- `region` (string, required): The region where services are deployed (e.g., "us-central1", "europe-west3")

**Example:**
```
list_cloud_run_services(project_id="my-gcp-project", region="us-central1")
```

**Response:**
```
[
  {
    "name": "my-service",
    "uri": "https://my-service-xyz123-uc.a.run.app"
  },
  ...
]
```

#### delete_cloud_run_service

Deletes a Cloud Run service from a specified GCP project and region.

**Parameters:**
- `service_name` (string, required): The name of the service to delete
- `project_id` (string, required): The ID of the GCP project
- `region` (string, required): The region where the service is deployed

**Example:**
```
delete_cloud_run_service(service_name="my-service", project_id="my-gcp-project", region="us-central1")
```

**Response:**
```
{
  "status": "success",
  "message": "Cloud Run service 'my-service' successfully deleted from project 'my-gcp-project' in region 'us-central1'"
}
```

## Configuring for Cursor

Create a `mcp.json` file in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gcp-tools": {
      "command": "uv",
      "args": ["--directory", "/path/to/gcp-mcp", "run", "gcp.py"]
    }
  }
}
```

## Testing

### Running Tests

```bash
# Run all tests
python -m unittest test_gcp.py

# Run specific test class
python -m unittest test_gcp.TestSecretManagerFunctions
python -m unittest test_gcp.TestCloudRunFunctions

# Run a specific test
python -m unittest test_gcp.TestSecretManagerFunctions.test_list_secrets
```
