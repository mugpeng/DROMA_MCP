# MCP Architecture Guide for DROMA Project

## 📋 Project Overview

This document provides a comprehensive guide for building a **DROMA MCP (Model Context Protocol)** based on the existing **infercnvpy-mcp** architecture. DROMA (Drug Response Omics association MAp) is a comprehensive database and analysis tool for cancer drug response and multi-omics data integration.

### Target: DROMA MCP Integration
- **Source**: [DROMA GitHub Repository](https://github.com/mugpeng/DROMA)
- **Goal**: Create natural language interface for drug response omics analysis
- **Based on**: infercnvpy-mcp architecture patterns

## 🏗️ MCP Architecture Pattern

### Core Architecture Components

```
droma-mcp/
├── pyproject.toml              # Project configuration
├── README.md                   # Documentation
├── data/                       # Sample datasets
├── src/droma_mcp/
│   ├── __init__.py            # Package version
│   ├── __main__.py            # Entry point
│   ├── cli.py                 # Command-line interface
│   ├── util.py                # Shared utilities
│   ├── schema/                # Pydantic data models
│   │   ├── __init__.py
│   │   ├── db.py             # Database operation schemas
│   │   ├── analysis.py       # Analysis function schemas
│   │   ├── visualization.py  # Plotting schemas
│   │   └── util.py           # Utility schemas
│   └── server/                # MCP server implementation
│       ├── __init__.py       # Server setup & state management
│       ├── db.py             # Database operations
│       ├── analysis.py       # Drug-omics analysis
│       ├── visualization.py  # Plotting functions
│       └── util.py           # Utility functions
```

## 🔗 Component Relationships

### 1. Schema ↔ Server Relationship (Data Contract Pattern)

**Purpose**: Type-safe API contracts using Pydantic validation

```python
# schema/analysis.py
from pydantic import BaseModel, Field
from typing import List, Optional

class DrugResponseAnalysisModel(BaseModel):
    """Schema for drug response analysis."""
    drug_ids: List[str] = Field(description="Drug identifiers to analyze")
    omics_type: str = Field(description="Omics data type (mRNA, CNV, protein, mutation)")
    cancer_type: Optional[str] = Field(default=None, description="Cancer type filter")
    model_type: str = Field(default="PDC", description="Model type: PDC, PDO, PDX, cell_line")
    correlation_method: str = Field(default="pearson", description="Correlation method")

# server/analysis.py
from fastmcp import FastMCP, Context
from ..schema.analysis import DrugResponseAnalysisModel

@analysis_mcp.tool()
async def drug_omics_correlation(
    ctx: Context,
    request: DrugResponseAnalysisModel,
    dataset_id: str = Field(default=None, description="DROMA dataset identifier")
):
    """Analyze correlations between drug response and omics data."""
    # Extract validated parameters
    kwargs = request.model_dump()
    
    # Get DROMA data state
    droma_state = ctx.request_context.lifespan_context
    dataset = droma_state.get_dataset(dataset_id)
    
    # Perform analysis
    result = perform_drug_omics_analysis(dataset, **kwargs)
    
    return {
        "status": "success",
        "correlations": result,
        "drug_count": len(kwargs["drug_ids"]),
        "omics_type": kwargs["omics_type"]
    }
```

### 2. CLI ↔ Server Orchestration

**Purpose**: Application entry point with modular loading

```python
# cli.py
import typer
from enum import Enum

class Module(str, Enum):
    ALL = "all"
    DB = "db"              # Database operations
    ANALYSIS = "analysis"   # Drug-omics analysis  
    VIZ = "visualization"   # Plotting
    UTIL = "util"          # Utilities

@app.command(name="run")
def run(
    module: Module = typer.Option(Module.ALL, "-m", "--module"),
    transport: Transport = typer.Option(Transport.STDIO, "-t", "--transport"),
    port: int = typer.Option(8000, "-p", "--port"),
):
    """Start DROMA MCP Server"""
    os.environ['DROMA_MCP_MODULE'] = module.value
    
    from .server import droma_mcp, setup
    asyncio.run(setup())
    
    if transport == Transport.STDIO:
        droma_mcp.run()
    elif transport == Transport.SHTTP:
        from .util import get_figure, get_data_export
        droma_mcp._additional_http_routes = [
            Route("/figures/{figure_name}", endpoint=get_figure),
            Route("/export/{data_id}", endpoint=get_data_export)
        ]
        droma_mcp.run(transport="streamable-http", host="127.0.0.1", port=port)
```

### 3. State Management Pattern

**Purpose**: Centralized data and session management

```python
# server/__init__.py
class DromaState:
    """Manages DROMA datasets and analysis state."""
    def __init__(self):
        self.datasets = {}  # {dataset_id: DROMASet_object}
        self.active_dataset = None
        self.analysis_cache = {}
        self.metadata = {}
    
    def load_dataset(self, dataset_id, dataset_type="PDC"):
        """Load DROMA dataset by ID."""
        # Implementation would connect to DROMA_DB
        pass
    
    def get_dataset(self, dataset_id=None):
        """Get active or specified dataset."""
        dataset_id = dataset_id or self.active_dataset
        return self.datasets.get(dataset_id)

@asynccontextmanager
async def droma_lifespan(server: FastMCP) -> AsyncIterator[Any]:
    yield DromaState()

droma_mcp = FastMCP("DROMA-MCP-Server", lifespan=droma_lifespan)
```

### 4. Utility Services Pattern

**Purpose**: Shared functionality across modules

```python
# util.py
import pandas as pd
from pathlib import Path

# Global storage for exports
EXPORTS = {}
FIGURES = {}

def save_analysis_result(result_df, name=None):
    """Save analysis results for download."""
    if name is None:
        name = f"droma_analysis_{len(EXPORTS)}.csv"
    
    temp_dir = Path(tempfile.gettempdir()) / "droma_mcp_exports"
    temp_dir.mkdir(exist_ok=True)
    
    filename = temp_dir / name
    result_df.to_csv(filename, index=False)
    
    EXPORTS[name] = str(filename)
    return name

async def get_data_export(request: Request):
    """HTTP endpoint for downloading analysis results."""
    data_id = request.path_params["data_id"]
    
    if data_id in EXPORTS:
        return FileResponse(EXPORTS[data_id])
    else:
        return {"error": f"Export {data_id} not found"}
```

## 🎯 DROMA-Specific Implementation Guide

### 1. Database Operations Module (`server/db.py`)

```python
# Key functions to implement:
@db_mcp.tool()
async def list_datasets():
    """List available DROMA datasets."""
    
@db_mcp.tool()  
async def load_dataset(dataset_id: str, dataset_type: str):
    """Load specific DROMA dataset."""
    
@db_mcp.tool()
async def search_drugs(query: str, dataset_id: str):
    """Search for drugs in dataset."""
    
@db_mcp.tool()
async def get_sample_info(dataset_id: str, sample_filters: dict):
    """Get sample metadata with filtering."""
```

### 2. Analysis Module (`server/analysis.py`)

```python
# Core DROMA analysis functions:
@analysis_mcp.tool()
async def drug_response_correlation(request: DrugResponseModel):
    """Correlate drug sensitivity with omics features."""
    
@analysis_mcp.tool()
async def differential_drug_response(request: DifferentialModel):
    """Compare drug responses between groups."""
    
@analysis_mcp.tool()
async def drug_pathway_enrichment(request: PathwayModel):
    """Pathway enrichment analysis for drug-responsive genes."""
    
@analysis_mcp.tool()
async def multi_omics_integration(request: MultiOmicsModel):
    """Integrate multiple omics types for drug prediction."""
```

### 3. Visualization Module (`server/visualization.py`)

```python
# DROMA-specific plotting functions:
@viz_mcp.tool()
async def plot_drug_response_heatmap(request: HeatmapModel):
    """Plot drug response heatmap across samples."""
    
@viz_mcp.tool()
async def plot_correlation_network(request: NetworkModel):
    """Visualize drug-omics correlation networks."""
    
@viz_mcp.tool()
async def plot_dose_response_curve(request: DoseResponseModel):
    """Plot IC50 dose-response curves."""
```

## 📊 Schema Definitions for DROMA

### Analysis Schemas (`schema/analysis.py`)

```python
class DrugResponseModel(BaseModel):
    drug_ids: List[str] = Field(description="Drug identifiers")
    omics_features: List[str] = Field(description="Omics features to correlate")
    omics_type: Literal["mRNA", "CNV", "protein", "mutation"] = Field(description="Omics data type")
    cancer_types: Optional[List[str]] = Field(default=None, description="Cancer type filters")
    model_types: List[str] = Field(default=["PDC"], description="Model types: PDC, PDO, PDX, cell_line")
    correlation_method: Literal["pearson", "spearman", "kendall"] = Field(default="pearson")
    
class MultiOmicsModel(BaseModel):
    drug_id: str = Field(description="Target drug for prediction")
    omics_types: List[str] = Field(description="Omics types to integrate")
    integration_method: Literal["concatenation", "late_fusion", "intermediate_fusion"] = Field(default="concatenation")
    feature_selection: bool = Field(default=True, description="Apply feature selection")
    cross_validation: bool = Field(default=True, description="Perform cross-validation")
```

### Database Schemas (`schema/db.py`)

```python
class DatasetFilterModel(BaseModel):
    cancer_types: Optional[List[str]] = Field(default=None)
    model_types: Optional[List[str]] = Field(default=None)
    omics_available: Optional[List[str]] = Field(default=None)
    min_samples: Optional[int] = Field(default=None)
    
class DrugSearchModel(BaseModel):
    query: str = Field(description="Drug name or identifier search term")
    search_fields: List[str] = Field(default=["name", "id"], description="Fields to search in")
    exact_match: bool = Field(default=False, description="Require exact match")
```

## 🔄 Development Workflow

### 1. Project Setup
```bash
# Initialize project structure
mkdir droma-mcp
cd droma-mcp

# Create pyproject.toml with dependencies:
# - fastmcp>=2.3.0
# - pandas>=1.5.0  
# - numpy>=1.21.0
# - scipy>=1.7.0
# - matplotlib>=3.5.0
# - seaborn>=0.11.0
# - pydantic>=2.0.0
# - typer>=0.9.0
```

### 2. Integration with DROMA Components
- **DROMA_DB**: SQLite database integration
- **DROMA_Set**: R package bridge (via rpy2 or API)
- **DROMA_R**: Analysis function implementation
- **DROMA_Web**: Web interface patterns

### 3. Key Implementation Priorities

1. **Database Module**: Connect to DROMA_DB SQLite
2. **Basic Analysis**: Drug-omics correlation functions  
3. **Visualization**: Essential plotting capabilities
4. **State Management**: Multi-dataset handling
5. **HTTP Interface**: Data export and figure serving

## 🚀 Deployment Configuration

### MCP Client Configuration
```json
{
  "mcpServers": {
    "droma-mcp": {
      "command": "droma-mcp",
      "args": ["run", "--module", "all", "--transport", "stdio"]
    }
  }
}
```

### HTTP Server Mode
```json
{
  "mcpServers": {
    "droma-mcp-http": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8000/mcp"
      }
    }
  }
}
```

## 🎓 Key Design Principles

1. **Modularity**: Each functional area (db, analysis, viz) is independently loadable
2. **Type Safety**: Comprehensive Pydantic validation for all inputs
3. **State Management**: Centralized data handling with multi-dataset support
4. **Natural Language**: Tools designed for conversational AI interaction
5. **Extensibility**: Easy to add new analysis methods and visualizations
6. **Performance**: Efficient data handling and caching strategies

## 📚 Reference Implementation

This guide is based on the **infercnvpy-mcp** project structure, which successfully implements:
- ✅ Modular MCP architecture  
- ✅ Type-safe API design
- ✅ Multi-transport support
- ✅ State management patterns
- ✅ Natural language interfaces

Adapt these patterns for DROMA's drug response and multi-omics analysis capabilities. 