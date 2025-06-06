#!/usr/bin/env python3
"""Comprehensive tests for DROMA MCP dataset management operations."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock
import tempfile

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / ".."))

from src.droma_mcp.server.dataset_management import (
    load_dataset, 
    list_loaded_datasets, 
    set_active_dataset, 
    unload_dataset
)
from src.droma_mcp.schema.dataset_management import (
    LoadDatasetModel, 
    ListDatasetsModel, 
    SetActiveDatasetModel, 
    UnloadDatasetModel
)


class MockContext:
    """Mock context for testing."""
    
    def __init__(self, droma_state):
        self.request_context = Mock()
        self.request_context.lifespan_context = droma_state
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")


class MockRInterface:
    """Mock R interface for testing R commands."""
    
    def __init__(self):
        self.commands_executed = []
    
    def __call__(self, command):
        """Mock R command execution."""
        self.commands_executed.append(command)
        if "rm(" in command:
            # Simulate cleanup command
            return True
        return f"mock_result_for_{command.replace(' ', '_')}"


class MockDromaState:
    """Mock DROMA state for comprehensive testing."""
    
    def __init__(self, simulate_r=True):
        self.datasets = {}
        self.multidatasets = {}
        self.active_dataset = None
        self.active_multidataset = None
        self.analysis_cache = {}
        self.data_cache = {}
        self.metadata = {}
        self.r = MockRInterface() if simulate_r else None
        self._fail_load = False
        self._fail_dataset_id = None
    
    def set_load_failure(self, fail=True, dataset_id=None):
        """Set up failure scenario for testing."""
        self._fail_load = fail
        self._fail_dataset_id = dataset_id
    
    def load_dataset(self, dataset_id: str, db_path: str, dataset_type: str = "DromaSet"):
        """Mock dataset loading with failure scenarios."""
        print(f"Mock: Loading {dataset_type} '{dataset_id}' from {db_path}")
        
        # Simulate failure scenarios
        if self._fail_load and (self._fail_dataset_id is None or self._fail_dataset_id == dataset_id):
            return False
        
        if dataset_type == "DromaSet":
            self.datasets[dataset_id] = f"droma_set_{dataset_id}"
        else:  # MultiDromaSet
            self.multidatasets[dataset_id] = f"multi_droma_set_{dataset_id.replace(',', '_')}"
        
        return True
    
    def get_dataset(self, dataset_id=None):
        """Get dataset R object name."""
        if dataset_id:
            return self.datasets.get(dataset_id)
        return self.datasets.get(self.active_dataset) if self.active_dataset else None
    
    def get_multidataset(self, dataset_id=None):
        """Get multidataset R object name."""
        if dataset_id:
            return self.multidatasets.get(dataset_id)
        return self.multidatasets.get(self.active_multidataset) if self.active_multidataset else None
    
    def list_datasets(self):
        """List all loaded datasets."""
        return {
            'datasets': list(self.datasets.keys()),
            'multidatasets': list(self.multidatasets.keys())
        }
    
    def set_active_dataset(self, dataset_id: str, dataset_type: str = "DromaSet"):
        """Set active dataset with validation."""
        if dataset_type == "DromaSet":
            if dataset_id not in self.datasets:
                raise ValueError(f"Dataset {dataset_id} not found in loaded datasets")
            self.active_dataset = dataset_id
        elif dataset_type == "MultiDromaSet":
            if dataset_id not in self.multidatasets:
                raise ValueError(f"MultiDataset {dataset_id} not found in loaded multidatasets")
            self.active_multidataset = dataset_id
        else:
            raise ValueError(f"Invalid dataset type: {dataset_type}")


async def test_load_dataset():
    """Test dataset loading functionality."""
    print("=== Testing load_dataset ===")
    print()
    
    # Create temporary database file for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        droma_state = MockDromaState()
        ctx = MockContext(droma_state)
        
        # Test 1: Load single dataset successfully
        print("1. Loading single DromaSet (CCLE):")
        request = LoadDatasetModel(
            dataset_id="CCLE",
            dataset_type="DromaSet",
            db_path=db_path,
            set_active=True
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        assert result["status"] == "success"
        assert result["dataset_id"] == "CCLE"
        assert droma_state.active_dataset == "CCLE"
        print("✓ Single dataset loaded successfully\n")
        
        # Test 2: Load MultiDromaSet
        print("2. Loading MultiDromaSet (CCLE,gCSI):")
        request = LoadDatasetModel(
            dataset_id="CCLE,gCSI",
            dataset_type="MultiDromaSet",
            db_path=db_path,
            set_active=True
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        assert result["status"] == "success"
        assert droma_state.active_multidataset == "CCLE,gCSI"
        print("✓ MultiDromaSet loaded successfully\n")
        
        # Test 3: Load without setting active
        print("3. Loading dataset without setting as active:")
        request = LoadDatasetModel(
            dataset_id="gCSI",
            dataset_type="DromaSet",
            db_path=db_path,
            set_active=False
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        assert result["status"] == "success"
        assert droma_state.active_dataset == "CCLE"  # Should remain unchanged
        print("✓ Dataset loaded without changing active status\n")
        
        # Test 4: Load failure scenario
        print("4. Testing load failure scenario:")
        droma_state.set_load_failure(True, "FAILING_DATASET")
        request = LoadDatasetModel(
            dataset_id="FAILING_DATASET",
            dataset_type="DromaSet",
            db_path=db_path,
            set_active=False
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        assert result["status"] == "error"
        print("✓ Load failure handled correctly\n")
        
        # Test 5: Missing database file
        print("5. Testing missing database file:")
        request = LoadDatasetModel(
            dataset_id="TEST",
            dataset_type="DromaSet",
            db_path="/nonexistent/path/database.db",
            set_active=False
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        assert result["status"] == "error"
        print("✓ Missing database file handled correctly\n")
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(db_path)
        except:
            pass


async def test_list_loaded_datasets():
    """Test listing loaded datasets."""
    print("=== Testing list_loaded_datasets ===")
    print()
    
    droma_state = MockDromaState()
    ctx = MockContext(droma_state)
    
    # Test 1: List empty datasets
    print("1. Listing when no datasets are loaded:")
    request = ListDatasetsModel(include_details=False)
    result = await list_loaded_datasets(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert result["total_loaded"] == 0
    print("✓ Empty dataset list handled correctly\n")
    
    # Load some test datasets
    droma_state.datasets["CCLE"] = "droma_set_CCLE"
    droma_state.datasets["gCSI"] = "droma_set_gCSI"
    droma_state.multidatasets["CCLE,gCSI"] = "multi_droma_set_CCLE_gCSI"
    droma_state.active_dataset = "CCLE"
    droma_state.active_multidataset = "CCLE,gCSI"
    
    # Test 2: List datasets without details
    print("2. Listing datasets without details:")
    request = ListDatasetsModel(include_details=False)
    result = await list_loaded_datasets(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert result["total_loaded"] == 3
    assert len(result["datasets"]) == 2
    assert len(result["multidatasets"]) == 1
    print("✓ Dataset list without details correct\n")
    
    # Test 3: List datasets with details
    print("3. Listing datasets with details:")
    request = ListDatasetsModel(include_details=True)
    result = await list_loaded_datasets(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert "dataset_details" in result
    assert "CCLE" in result["dataset_details"]
    assert result["dataset_details"]["CCLE"]["is_active"] == True
    assert result["dataset_details"]["gCSI"]["is_active"] == False
    print("✓ Dataset list with details correct\n")


async def test_set_active_dataset():
    """Test setting active datasets."""
    print("=== Testing set_active_dataset ===")
    print()
    
    droma_state = MockDromaState()
    ctx = MockContext(droma_state)
    
    # Load some test datasets first
    droma_state.datasets["CCLE"] = "droma_set_CCLE"
    droma_state.datasets["gCSI"] = "droma_set_gCSI"
    droma_state.multidatasets["CCLE,gCSI"] = "multi_droma_set_CCLE_gCSI"
    
    # Test 1: Set active DromaSet
    print("1. Setting active DromaSet:")
    request = SetActiveDatasetModel(
        dataset_id="CCLE",
        dataset_type="DromaSet"
    )
    result = await set_active_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert droma_state.active_dataset == "CCLE"
    print("✓ Active DromaSet set correctly\n")
    
    # Test 2: Set active MultiDromaSet
    print("2. Setting active MultiDromaSet:")
    request = SetActiveDatasetModel(
        dataset_id="CCLE,gCSI",
        dataset_type="MultiDromaSet"
    )
    result = await set_active_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert droma_state.active_multidataset == "CCLE,gCSI"
    print("✓ Active MultiDromaSet set correctly\n")
    
    # Test 3: Try to set non-existent dataset as active
    print("3. Trying to set non-existent dataset as active:")
    request = SetActiveDatasetModel(
        dataset_id="NONEXISTENT",
        dataset_type="DromaSet"
    )
    result = await set_active_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "error"
    print("✓ Non-existent dataset error handled correctly\n")


async def test_unload_dataset():
    """Test unloading datasets."""
    print("=== Testing unload_dataset ===")
    print()
    
    droma_state = MockDromaState()
    ctx = MockContext(droma_state)
    
    # Load some test datasets first
    droma_state.datasets["CCLE"] = "droma_set_CCLE"
    droma_state.datasets["gCSI"] = "droma_set_gCSI"
    droma_state.multidatasets["CCLE,gCSI"] = "multi_droma_set_CCLE_gCSI"
    droma_state.active_dataset = "CCLE"
    droma_state.active_multidataset = "CCLE,gCSI"
    
    # Test 1: Unload non-active dataset
    print("1. Unloading non-active DromaSet:")
    request = UnloadDatasetModel(
        dataset_id="gCSI",
        dataset_type="DromaSet"
    )
    result = await unload_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert "gCSI" not in droma_state.datasets
    assert droma_state.active_dataset == "CCLE"  # Should remain unchanged
    print("✓ Non-active dataset unloaded correctly\n")
    
    # Test 2: Unload active dataset
    print("2. Unloading active DromaSet:")
    request = UnloadDatasetModel(
        dataset_id="CCLE",
        dataset_type="DromaSet"
    )
    result = await unload_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert "CCLE" not in droma_state.datasets
    assert droma_state.active_dataset is None  # Should be cleared
    print("✓ Active dataset unloaded and cleared correctly\n")
    
    # Test 3: Unload MultiDromaSet
    print("3. Unloading active MultiDromaSet:")
    request = UnloadDatasetModel(
        dataset_id="CCLE,gCSI",
        dataset_type="MultiDromaSet"
    )
    result = await unload_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "success"
    assert "CCLE,gCSI" not in droma_state.multidatasets
    assert droma_state.active_multidataset is None
    print("✓ MultiDromaSet unloaded correctly\n")
    
    # Test 4: Try to unload non-existent dataset
    print("4. Trying to unload non-existent dataset:")
    request = UnloadDatasetModel(
        dataset_id="NONEXISTENT",
        dataset_type="DromaSet"
    )
    result = await unload_dataset(ctx, request)
    print(f"Result: {result}")
    assert result["status"] == "warning"
    print("✓ Non-existent dataset warning handled correctly\n")


async def test_database_path_validation():
    """Test database path validation."""
    print("=== Testing Database Path Validation ===")
    print()
    
    droma_state = MockDromaState()
    ctx = MockContext(droma_state)
    
    # Clear environment variable for testing
    original_db_path = os.environ.get('DROMA_DB_PATH')
    if 'DROMA_DB_PATH' in os.environ:
        del os.environ['DROMA_DB_PATH']
    
    try:
        # Test 1: No database path provided
        print("1. Testing with no database path:")
        request = LoadDatasetModel(
            dataset_id="TEST",
            dataset_type="DromaSet",
            db_path=None,
            set_active=False
        )
        result = await load_dataset(ctx, request)
        print(f"Result: {result}")
        assert result["status"] == "error"
        assert "No database path configured" in result["message"]
        print("✓ Missing database path handled correctly\n")
        
        # Test 2: Environment variable takes precedence
        print("2. Testing with environment variable:")
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            env_db_path = tmp_db.name
        
        os.environ['DROMA_DB_PATH'] = env_db_path
        
        try:
            request = LoadDatasetModel(
                dataset_id="TEST",
                dataset_type="DromaSet",
                db_path=None,  # Should use environment variable
                set_active=False
            )
            result = await load_dataset(ctx, request)
            print(f"Result: {result}")
            # Should succeed since file exists and state will mock load
            print("✓ Environment variable used correctly\n")
        finally:
            os.unlink(env_db_path)
            del os.environ['DROMA_DB_PATH']
    
    finally:
        # Restore original environment variable
        if original_db_path:
            os.environ['DROMA_DB_PATH'] = original_db_path


async def test_complete_workflow():
    """Test complete dataset management workflow."""
    print("=== Testing Complete Workflow ===")
    print()
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        droma_state = MockDromaState()
        ctx = MockContext(droma_state)
        
        print("1. Initial state - no datasets loaded:")
        list_result = await list_loaded_datasets(ctx, ListDatasetsModel(include_details=False))
        assert list_result["total_loaded"] == 0
        print("✓ Initial state confirmed\n")
        
        print("2. Load first dataset:")
        load_result = await load_dataset(ctx, LoadDatasetModel(
            dataset_id="CCLE", dataset_type="DromaSet", db_path=db_path, set_active=True
        ))
        assert load_result["status"] == "success"
        print("✓ First dataset loaded\n")
        
        print("3. Load second dataset:")
        load_result = await load_dataset(ctx, LoadDatasetModel(
            dataset_id="gCSI", dataset_type="DromaSet", db_path=db_path, set_active=False
        ))
        assert load_result["status"] == "success"
        print("✓ Second dataset loaded\n")
        
        print("4. Load multi-dataset:")
        load_result = await load_dataset(ctx, LoadDatasetModel(
            dataset_id="CCLE,gCSI", dataset_type="MultiDromaSet", db_path=db_path, set_active=True
        ))
        assert load_result["status"] == "success"
        print("✓ Multi-dataset loaded\n")
        
        print("5. List all datasets:")
        list_result = await list_loaded_datasets(ctx, ListDatasetsModel(include_details=True))
        assert list_result["total_loaded"] == 3
        print("✓ All datasets listed correctly\n")
        
        print("6. Change active dataset:")
        set_result = await set_active_dataset(ctx, SetActiveDatasetModel(
            dataset_id="gCSI", dataset_type="DromaSet"
        ))
        assert set_result["status"] == "success"
        assert droma_state.active_dataset == "gCSI"
        print("✓ Active dataset changed\n")
        
        print("7. Unload one dataset:")
        unload_result = await unload_dataset(ctx, UnloadDatasetModel(
            dataset_id="CCLE", dataset_type="DromaSet"
        ))
        assert unload_result["status"] == "success"
        print("✓ Dataset unloaded\n")
        
        print("8. Final state:")
        list_result = await list_loaded_datasets(ctx, ListDatasetsModel(include_details=True))
        assert list_result["total_loaded"] == 2
        assert "CCLE" not in list_result["datasets"]
        print("✓ Final state confirmed\n")
        
    finally:
        os.unlink(db_path)


async def run_all_tests():
    """Run all dataset management tests."""
    print("DROMA MCP Dataset Management Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_load_dataset,
        test_list_loaded_datasets,
        test_set_active_dataset,
        test_unload_dataset,
        test_database_path_validation,
        test_complete_workflow
    ]
    
    for test_func in tests:
        try:
            await test_func()
            print(f"✅ {test_func.__name__} PASSED")
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        print("-" * 60)
        print()


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 