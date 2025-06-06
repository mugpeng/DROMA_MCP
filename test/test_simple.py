#!/usr/bin/env python3
"""Simplified test for DROMA MCP functions - direct function calls."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / ".."))

from src.droma_mcp.server.database_query import list_droma_projects
from src.droma_mcp.schema.database_query import ListProjectsModel


class MockContext:
    """Mock context for testing."""
    
    def __init__(self):
        self.request_context = Mock()
        self.request_context.lifespan_context = {}
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")


async def test_list_projects_direct():
    """Test list_droma_projects function directly."""
    
    print("=== Direct Function Test ===")
    print()
    
    # Check if database path is set
    db_path = os.environ.get('DROMA_DB_PATH')
    if not db_path:
        print("Warning: DROMA_DB_PATH environment variable not set!")
        print("Set it like: export DROMA_DB_PATH=/path/to/your/database.db")
        print()
        
        # For testing purposes, you can set a test database path here:
        # os.environ['DROMA_DB_PATH'] = '/path/to/your/test_database.db'
    
    # Create mock context
    ctx = MockContext()
    
    # Test 1: List all projects
    print("1. Testing: List all projects")
    try:
        request = ListProjectsModel(
            show_names_only=False,
            project_data_types=None
        )
        result = await list_droma_projects(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Test 2: List only project names
    print("2. Testing: List only project names")
    try:
        request = ListProjectsModel(
            show_names_only=True,
            project_data_types=None
        )
        result = await list_droma_projects(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Test 3: Get data types for specific project
    print("3. Testing: Get data types for project 'gCSI'")
    try:
        request = ListProjectsModel(
            show_names_only=False,
            project_data_types="gCSI"
        )
        result = await list_droma_projects(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()


if __name__ == "__main__":
    print("DROMA MCP Direct Function Test")
    print("=" * 50)
    print()
    
    asyncio.run(test_list_projects_direct()) 