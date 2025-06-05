#!/usr/bin/env python3
"""Test dataset loading workflow for DROMA MCP."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.droma_mcp.server.dataset_management import load_dataset, list_loaded_datasets
from src.droma_mcp.server.data_loading import load_molecular_profiles_normalized
from src.droma_mcp.schema.dataset_management import LoadDatasetModel, ListDatasetsModel
from src.droma_mcp.schema.data_loading import LoadMolecularProfilesModel


class MockContext:
    """Mock context for testing."""
    
    def __init__(self, droma_state):
        self.request_context = Mock()
        self.request_context.lifespan_context = droma_state
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")


class MockDromaState:
    """Mock DROMA state for testing without full R setup."""
    
    def __init__(self):
        self.datasets = {}
        self.multidatasets = {}
        self.active_dataset = None
        self.active_multidataset = None
        self.analysis_cache = {}
        self.data_cache = {}
        self.metadata = {}
        self.r = None  # Simulate no R environment for testing
    
    def load_dataset(self, dataset_id: str, db_path: str, dataset_type: str = "DromaSet"):
        """Mock dataset loading."""
        print(f"Mock: Loading {dataset_type} '{dataset_id}' from {db_path}")
        
        if dataset_type == "DromaSet":
            self.datasets[dataset_id] = dataset_id
        else:
            self.multidatasets[dataset_id] = dataset_id.replace(",", "_")
        
        return True
    
    def get_dataset(self, dataset_id=None):
        if dataset_id:
            return self.datasets.get(dataset_id)
        return self.datasets.get(self.active_dataset) if self.active_dataset else None
    
    def get_multidataset(self, dataset_id=None):
        if dataset_id:
            return self.multidatasets.get(dataset_id)
        return self.multidatasets.get(self.active_multidataset) if self.active_multidataset else None
    
    def list_datasets(self):
        return {
            'datasets': list(self.datasets.keys()),
            'multidatasets': list(self.multidatasets.keys())
        }
    
    def set_active_dataset(self, dataset_id: str, dataset_type: str = "DromaSet"):
        if dataset_type == "DromaSet" and dataset_id in self.datasets:
            self.active_dataset = dataset_id
        elif dataset_type == "MultiDromaSet" and dataset_id in self.multidatasets:
            self.active_multidataset = dataset_id
        else:
            raise ValueError(f"Dataset {dataset_id} not found")


async def test_dataset_workflow():
    """Test the complete workflow: load dataset -> use data loading functions."""
    
    print("=== DROMA Dataset Loading Workflow Test ===")
    print()
    
    # Check if database path is set
    db_path = os.environ.get('DROMA_DB_PATH')
    if not db_path:
        print("Warning: DROMA_DB_PATH environment variable not set!")
        print("Set it like: export DROMA_DB_PATH=/path/to/your/database.db")
        print("Using mock state for demonstration...\n")
        
        # Use a dummy path for mock testing
        db_path = "/path/to/mock/database.db"
    
    # Create mock DROMA state
    droma_state = MockDromaState()
    ctx = MockContext(droma_state)
    
    # Step 1: Check what datasets are loaded initially
    print("1. Checking initially loaded datasets:")
    try:
        request = ListDatasetsModel(include_details=True)
        result = await list_loaded_datasets(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Step 2: Load CCLE dataset
    print("2. Loading CCLE dataset:")
    try:
        request = LoadDatasetModel(
            dataset_id="CCLE",
            dataset_type="DromaSet",
            db_path=db_path,
            set_active=True
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Step 3: Load gCSI dataset
    print("3. Loading gCSI dataset:")
    try:
        request = LoadDatasetModel(
            dataset_id="gCSI",
            dataset_type="DromaSet",
            db_path=db_path,
            set_active=False
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Step 4: List all loaded datasets
    print("4. Listing all loaded datasets:")
    try:
        request = ListDatasetsModel(include_details=True)
        result = await list_loaded_datasets(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Step 5: Now try to use data loading function (this should work)
    print("5. Now using load_molecular_profiles_normalized (should work since CCLE is loaded):")
    try:
        request = LoadMolecularProfilesModel(
            dataset_name="CCLE",  # This dataset is now loaded
            molecular_type="mRNA",
            z_score=False,
            verbose=True
        )
        result = await load_molecular_profiles_normalized(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Step 6: Try with multi-dataset
    print("6. Loading multi-dataset (CCLE + gCSI):")
    try:
        request = LoadDatasetModel(
            dataset_id="CCLE,gCSI",
            dataset_type="MultiDromaSet",
            db_path=db_path,
            set_active=True
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    print("DROMA MCP Dataset Loading Workflow Test")
    print("=" * 60)
    print()
    
    asyncio.run(test_dataset_workflow()) 