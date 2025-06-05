"""DROMA MCP Server initialization and state management."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any, Dict, Optional
from fastmcp import FastMCP
import pandas as pd
from pathlib import Path


class DromaState:
    """Manages DROMA datasets and analysis state."""
    
    def __init__(self):
        self.datasets: Dict[str, Any] = {}  # {dataset_id: DromaSet_object}
        self.multidatasets: Dict[str, Any] = {}  # {dataset_id: MultiDromaSet_object}
        self.active_dataset: Optional[str] = None
        self.active_multidataset: Optional[str] = None
        self.analysis_cache: Dict[str, Any] = {}
        self.data_cache: Dict[str, Any] = {}  # Cache for loaded data
        self.metadata: Dict[str, Any] = {}
        
        # R environment setup
        self._setup_r_environment()
    
    def _setup_r_environment(self):
        """Initialize R environment and load DROMA packages."""
        try:
            import rpy2.robjects as robjects
            from rpy2.robjects import pandas2ri
            
            # Activate automatic pandas to R conversion
            pandas2ri.activate()
            
            # Load required R libraries
            robjects.r('''
                library(DROMA.Set)
                library(DROMA.R)
            ''')
            
            self.r = robjects.r
            print("R environment initialized successfully")
            
        except Exception as e:
            print(f"Warning: Could not initialize R environment: {e}")
            self.r = None
    
    def load_dataset(self, dataset_id: str, db_path: str, dataset_type: str = "DromaSet"):
        """Load DROMA dataset by ID."""
        if self.r is None:
            raise RuntimeError("R environment not available")
            
        try:
            if dataset_type == "DromaSet":
                # Load single DromaSet
                self.r(f'''
                    {dataset_id} <- createDromaSetFromDatabase("{dataset_id}", "{db_path}")
                ''')
                self.datasets[dataset_id] = dataset_id  # Store R object name
                
            elif dataset_type == "MultiDromaSet":
                # Load MultiDromaSet (assuming dataset_id is comma-separated project names)
                project_names = dataset_id.split(",")
                project_names_r = 'c("' + '", "'.join(project_names) + '")'
                
                self.r(f'''
                    {dataset_id.replace(",", "_")} <- createMultiDromaSetFromDatabase(
                        {project_names_r}, "{db_path}"
                    )
                ''')
                self.multidatasets[dataset_id] = dataset_id.replace(",", "_")
                
            print(f"Successfully loaded dataset: {dataset_id}")
            return True
            
        except Exception as e:
            print(f"Error loading dataset {dataset_id}: {e}")
            return False
    
    def get_dataset(self, dataset_id: Optional[str] = None) -> Optional[str]:
        """Get active or specified dataset."""
        if dataset_id:
            return self.datasets.get(dataset_id)
        return self.datasets.get(self.active_dataset) if self.active_dataset else None
    
    def get_multidataset(self, dataset_id: Optional[str] = None) -> Optional[str]:
        """Get active or specified multidataset."""
        if dataset_id:
            return self.multidatasets.get(dataset_id)
        return self.multidatasets.get(self.active_multidataset) if self.active_multidataset else None
    
    def cache_data(self, key: str, data: Any, metadata: Optional[Dict] = None):
        """Cache data with optional metadata."""
        self.data_cache[key] = {
            'data': data,
            'metadata': metadata or {},
            'timestamp': pd.Timestamp.now()
        }
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data."""
        cached = self.data_cache.get(key)
        return cached['data'] if cached else None
    
    def list_datasets(self) -> Dict[str, str]:
        """List all loaded datasets."""
        return {
            'datasets': list(self.datasets.keys()),
            'multidatasets': list(self.multidatasets.keys())
        }
    
    def set_active_dataset(self, dataset_id: str, dataset_type: str = "DromaSet"):
        """Set the active dataset."""
        if dataset_type == "DromaSet" and dataset_id in self.datasets:
            self.active_dataset = dataset_id
        elif dataset_type == "MultiDromaSet" and dataset_id in self.multidatasets:
            self.active_multidataset = dataset_id
        else:
            raise ValueError(f"Dataset {dataset_id} not found")


@asynccontextmanager
async def droma_lifespan(server: FastMCP) -> AsyncIterator[DromaState]:
    """Lifespan context manager for DROMA MCP server."""
    print("Initializing DROMA MCP Server...")
    
    # Create DROMA state
    state = DromaState()
    
    # Set up temp directories for exports
    export_dir = Path.home() / ".droma_mcp" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    yield state
    
    print("Shutting down DROMA MCP Server...")


# Create the main FastMCP server instance
droma_mcp = FastMCP("DROMA-MCP-Server", lifespan=droma_lifespan)

# Setup function that can be called before running
async def setup_server():
    """Setup function for server initialization."""
    from ..util import setup_server as util_setup
    await util_setup()

# Module loading based on environment variable
module = os.environ.get('DROMA_MCP_MODULE', 'all')

if module in ['all', 'data_loading']:
    from .data_loading import data_loading_mcp
    droma_mcp.mount("/data", data_loading_mcp)

if module in ['all', 'database_query']:
    from .database_query import database_query_mcp
    droma_mcp.mount("/query", database_query_mcp)

if module in ['all', 'dataset_management']:
    from .dataset_management import dataset_management_mcp
    droma_mcp.mount("/datasets", dataset_management_mcp)

print(f"DROMA MCP Server initialized with module: {module}")

__all__ = ["droma_mcp", "DromaState", "setup_server"] 