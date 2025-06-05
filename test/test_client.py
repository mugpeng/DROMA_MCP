#!/usr/bin/env python3
"""Test client for DROMA MCP database query functions."""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import Client


async def test_list_droma_projects():
    """Test the list_droma_projects function with different parameters."""
    
    # Make sure database path is set
    if not os.environ.get('DROMA_DB_PATH'):
        print("Warning: DROMA_DB_PATH environment variable not set!")
        print("Set it like: export DROMA_DB_PATH=/path/to/your/database.db")
        print("Continuing with test anyway...\n")
    
    client = Client("test_server.py")
    
    async with client:
        print("=== Testing list_droma_projects ===\n")
        
        # Test 1: List all projects (full information)
        print("1. Listing all projects (full information):")
        try:
            result = await client.call_tool("list_droma_projects", {
                "show_names_only": False,
                "project_data_types": None
            })
            print(f"Result: {result}")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
        
        # Test 2: List only project names
        print("2. Listing only project names:")
        try:
            result = await client.call_tool("list_droma_projects", {
                "show_names_only": True,
                "project_data_types": None
            })
            print(f"Result: {result}")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
        
        # Test 3: Get data types for a specific project
        print("3. Getting data types for a specific project (example: 'gCSI'):")
        try:
            result = await client.call_tool("list_droma_projects", {
                "show_names_only": False,
                "project_data_types": "gCSI"
            })
            print(f"Result: {result}")
            print()
        except Exception as e:
            print(f"Error: {e}\n")


async def test_other_functions():
    """Test other database query functions."""
    
    client = Client("test_server.py")
    
    async with client:
        print("=== Testing other database query functions ===\n")
        
        # Test get_droma_annotation
        print("4. Testing get_droma_annotation (sample annotations):")
        try:
            result = await client.call_tool("get_droma_annotation", {
                "anno_type": "sample",
                "project_name": None,
                "ids": None,
                "data_type": "all",
                "tumor_type": "all",
                "limit": 5
            })
            print(f"Result: {result}")
            print()
        except Exception as e:
            print(f"Error: {e}\n")
        
        # Test list_droma_samples
        print("5. Testing list_droma_samples:")
        try:
            result = await client.call_tool("list_droma_samples", {
                "project_name": "gCSI",
                "data_sources": "all",
                "data_type": "all",
                "tumor_type": "all",
                "limit": 5,
                "pattern": None
            })
            print(f"Result: {result}")
            print()
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    print("DROMA MCP Client Test")
    print("=" * 50)
    print()
    
    # Run the main test
    asyncio.run(test_list_droma_projects())
    
    # Uncomment below to test other functions as well
    # asyncio.run(test_other_functions()) 