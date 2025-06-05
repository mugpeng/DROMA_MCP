#!/usr/bin/env python3
"""Test server for DROMA MCP database query functions."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP
from src.droma_mcp.server.database_query import database_query_mcp

# Create main MCP server
mcp = FastMCP("DROMA-Test-Server")

# Add the database query sub-server
mcp.add_sub_server(database_query_mcp)

if __name__ == "__main__":
    # Set a sample database path for testing (you'll need to update this)
    # os.environ["DROMA_DB_PATH"] = "/path/to/your/droma_database.db"
    
    print("Starting DROMA MCP Test Server...")
    print("Available tools:")
    for tool_name in database_query_mcp._tools.keys():
        print(f"  - {tool_name}")
    
    print("\nTo test with a client, make sure to set DROMA_DB_PATH environment variable")
    print("Example: export DROMA_DB_PATH=/path/to/your/database.db")
    
    mcp.run() 