# GCP-MCP: Google Cloud Platform Model Control Protocol Server

**⚠️ EXPERIMENTAL PROJECT ⚠️**

This project provides Model Control Protocol (MCP) servers for interacting with Google Cloud Platform resources.

## Overview

GCP-MCP allows AI assistants and other MCP clients to interact with Google Cloud Platform services through standardized interfaces.

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

### Secret Manager
- `list_secrets`: List secrets in a GCP project (optionally filter by prefix)
- `delete_secret`: Delete a secret from Secret Manager
- `add_secret`: Add or update a secret in Secret Manager
- `get_secret_value`: Retrieve the value of a secret

### Cloud Run
- `list_cloud_run_services`: List Cloud Run services in a project and region
- `delete_cloud_run_service`: Delete a Cloud Run service
- `get_cloud_run_service_logs`: Fetch recent logs for a Cloud Run service

## Configuring for Cursor

Create a `mcp.json` file in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/gcp-mcp", "run", "main.py"]
    }
  }
}
```

## Testing

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run Secret Manager tests
python -m unittest test_secret_manager.py

# Run Cloud Run tests
python -m unittest test_cloud_run.py

# Run a specific test class
python -m unittest test_secret_manager.TestSecretManagerFunctions
python -m unittest test_cloud_run.TestCloudRunFunctions

# Run a specific test
python -m unittest test_secret_manager.TestSecretManagerFunctions.test_list_secrets
```
