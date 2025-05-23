"""
Central MCP server definition using FastMCP composition
"""
from fastmcp import FastMCP
import asyncio
from secret_manager import secret_manager_mcp
from cloud_run import cloud_run_mcp

async def create_composed_server():
    """Create a composed server with all GCP tools"""

    main_server = FastMCP("gcp")
    
    await main_server.import_server("secret", secret_manager_mcp)
    await main_server.import_server("cloudrun", cloud_run_mcp)
    
    return main_server

if __name__ == "__main__":
    main_server = asyncio.run(create_composed_server())
    main_server.run(transport='stdio')