"""Utility functions for DROMA MCP server."""

import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
import pandas as pd

# Global storage for exports and figures
EXPORTS: Dict[str, str] = {}
FIGURES: Dict[str, str] = {}


def save_analysis_result(result_df: pd.DataFrame, name: Optional[str] = None) -> str:
    """
    Save analysis results for download.
    
    Args:
        result_df: DataFrame to save
        name: Optional filename (auto-generated if None)
    
    Returns:
        Export identifier for retrieval
    """
    if name is None:
        name = f"droma_analysis_{len(EXPORTS)}.csv"
    
    # Ensure name ends with .csv
    if not name.endswith('.csv'):
        name += '.csv'
    
    # Create temp directory
    temp_dir = Path(tempfile.gettempdir()) / "droma_mcp_exports"
    temp_dir.mkdir(exist_ok=True)
    
    # Save file
    filepath = temp_dir / name
    result_df.to_csv(filepath, index=False)
    
    # Store in global registry
    export_id = name.replace('.csv', '')
    EXPORTS[export_id] = str(filepath)
    
    return export_id


def save_figure(figure_obj: Any, name: Optional[str] = None, format: str = "png") -> str:
    """
    Save matplotlib figure for download.
    
    Args:
        figure_obj: Matplotlib figure object
        name: Optional filename (auto-generated if None)
        format: File format (png, pdf, svg)
    
    Returns:
        Figure identifier for retrieval
    """
    if name is None:
        name = f"droma_figure_{len(FIGURES)}.{format}"
    
    # Ensure proper extension
    if not name.endswith(f'.{format}'):
        name += f'.{format}'
    
    # Create temp directory
    temp_dir = Path(tempfile.gettempdir()) / "droma_mcp_figures"
    temp_dir.mkdir(exist_ok=True)
    
    # Save figure
    filepath = temp_dir / name
    figure_obj.savefig(filepath, format=format, dpi=300, bbox_inches='tight')
    
    # Store in global registry
    figure_id = name.replace(f'.{format}', '')
    FIGURES[figure_id] = str(filepath)
    
    return figure_id


async def get_data_export(request: Request) -> FileResponse:
    """
    HTTP endpoint for downloading analysis results.
    
    URL: /export/{data_id}
    """
    data_id = request.path_params["data_id"]
    
    if data_id in EXPORTS:
        filepath = EXPORTS[data_id]
        if Path(filepath).exists():
            return FileResponse(
                filepath,
                media_type='text/csv',
                filename=Path(filepath).name
            )
        else:
            return JSONResponse(
                {"error": f"Export file not found: {data_id}"},
                status_code=404
            )
    else:
        return JSONResponse(
            {"error": f"Export {data_id} not found"},
            status_code=404
        )


async def get_figure(request: Request) -> FileResponse:
    """
    HTTP endpoint for downloading figures.
    
    URL: /figures/{figure_name}
    """
    figure_name = request.path_params["figure_name"]
    
    if figure_name in FIGURES:
        filepath = FIGURES[figure_name]
        if Path(filepath).exists():
            # Determine media type from file extension
            ext = Path(filepath).suffix.lower()
            media_types = {
                '.png': 'image/png',
                '.pdf': 'application/pdf',
                '.svg': 'image/svg+xml',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg'
            }
            media_type = media_types.get(ext, 'application/octet-stream')
            
            return FileResponse(
                filepath,
                media_type=media_type,
                filename=Path(filepath).name
            )
        else:
            return JSONResponse(
                {"error": f"Figure file not found: {figure_name}"},
                status_code=404
            )
    else:
        return JSONResponse(
            {"error": f"Figure {figure_name} not found"},
            status_code=404
        )


def list_exports() -> Dict[str, Any]:
    """List all available exports."""
    exports_info = {}
    for export_id, filepath in EXPORTS.items():
        if Path(filepath).exists():
            stat = Path(filepath).stat()
            exports_info[export_id] = {
                "filepath": filepath,
                "size_bytes": stat.st_size,
                "created": stat.st_ctime,
                "filename": Path(filepath).name
            }
    return exports_info


def list_figures() -> Dict[str, Any]:
    """List all available figures."""
    figures_info = {}
    for figure_id, filepath in FIGURES.items():
        if Path(filepath).exists():
            stat = Path(filepath).stat()
            figures_info[figure_id] = {
                "filepath": filepath,
                "size_bytes": stat.st_size,
                "created": stat.st_ctime,
                "filename": Path(filepath).name,
                "format": Path(filepath).suffix[1:]  # Remove the dot
            }
    return figures_info


def cleanup_temp_files(max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than specified age.
    
    Args:
        max_age_hours: Maximum age in hours before deletion
    
    Returns:
        Number of files deleted
    """
    import time
    
    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    # Clean exports
    to_remove = []
    for export_id, filepath in EXPORTS.items():
        if Path(filepath).exists():
            file_age = current_time - Path(filepath).stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    Path(filepath).unlink()
                    to_remove.append(export_id)
                    deleted_count += 1
                except Exception:
                    pass
    
    for export_id in to_remove:
        del EXPORTS[export_id]
    
    # Clean figures
    to_remove = []
    for figure_id, filepath in FIGURES.items():
        if Path(filepath).exists():
            file_age = current_time - Path(filepath).stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    Path(filepath).unlink()
                    to_remove.append(figure_id)
                    deleted_count += 1
                except Exception:
                    pass
    
    for figure_id in to_remove:
        del FIGURES[figure_id]
    
    return deleted_count


def format_data_size(size_bytes: int) -> str:
    """Format data size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_cache_key(cache_key: str) -> bool:
    """Validate cache key format."""
    # Basic validation - alphanumeric and underscores only
    import re
    return bool(re.match(r'^[a-zA-Z0-9_]+$', cache_key))


def generate_cache_key(prefix: str, dataset_id: str, data_type: str) -> str:
    """Generate a standardized cache key."""
    # Remove any problematic characters and create a clean key
    clean_dataset = "".join(c for c in dataset_id if c.isalnum() or c in ['_', '-'])
    clean_type = "".join(c for c in data_type if c.isalnum() or c in ['_', '-'])
    
    return f"{prefix}_{clean_dataset}_{clean_type}"


class DataValidator:
    """Utility class for data validation."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, min_rows: int = 1, min_cols: int = 1) -> Dict[str, Any]:
        """Validate pandas DataFrame."""
        validation_result = {
            "valid": True,
            "issues": [],
            "info": {
                "shape": df.shape,
                "dtypes": df.dtypes.to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "null_counts": df.isnull().sum().to_dict()
            }
        }
        
        # Check dimensions
        if df.shape[0] < min_rows:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Too few rows: {df.shape[0]} < {min_rows}")
        
        if df.shape[1] < min_cols:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Too few columns: {df.shape[1]} < {min_cols}")
        
        # Check for all-null columns
        all_null_cols = df.columns[df.isnull().all()].tolist()
        if all_null_cols:
            validation_result["issues"].append(f"All-null columns: {all_null_cols}")
        
        # Check for duplicate columns
        duplicate_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicate_cols:
            validation_result["issues"].append(f"Duplicate columns: {duplicate_cols}")
        
        return validation_result
    
    @staticmethod
    def check_normalization_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """Check quality of z-score normalization."""
        values = df.values.flatten()
        values = values[~pd.isna(values)]  # Remove NaN values
        
        if len(values) == 0:
            return {"valid": False, "reason": "No valid values found"}
        
        mean_val = values.mean()
        std_val = values.std()
        
        quality_check = {
            "mean": float(mean_val),
            "std": float(std_val),
            "min": float(values.min()),
            "max": float(values.max()),
            "is_well_normalized": abs(mean_val) < 0.1 and 0.8 < std_val < 1.2,
            "mean_centered": abs(mean_val) < 0.1,
            "unit_variance": 0.8 < std_val < 1.2
        }
        
        return quality_check


# Async setup function for server initialization
async def setup_server() -> None:
    """Setup function called during server initialization."""
    # Create temp directories
    temp_base = Path(tempfile.gettempdir()) / "droma_mcp"
    (temp_base / "exports").mkdir(parents=True, exist_ok=True)
    (temp_base / "figures").mkdir(parents=True, exist_ok=True)
    
    # Clean up old files
    cleanup_temp_files(max_age_hours=24)
    
    print("DROMA MCP utility services initialized") 