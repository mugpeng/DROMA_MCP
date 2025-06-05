"""DROMA MCP server for data loading operations."""

from fastmcp import FastMCP, Context
from typing import Dict, Optional, Any, Union
import pandas as pd
from pathlib import Path

from ..schema.data_loading import (
    LoadMolecularProfilesModel,
    LoadTreatmentResponseModel,
    MultiProjectMolecularProfilesModel,
    MultiProjectTreatmentResponseModel
)

# Create sub-MCP server for data loading
data_loading_mcp = FastMCP("DROMA-Data-Loading")


def _convert_r_to_python(r_result, state) -> Union[pd.DataFrame, Dict[str, Any]]:
    """Convert R result to Python data structures."""
    try:
        import rpy2.robjects as robjects
        from rpy2.robjects import pandas2ri
        
        # Convert R object to pandas if possible
        if hasattr(r_result, 'rclass') and 'matrix' in str(r_result.rclass):
            # Convert R matrix to pandas DataFrame
            pandas_df = pandas2ri.rpy2py(r_result)
            return pandas_df
        elif hasattr(r_result, 'rclass') and 'data.frame' in str(r_result.rclass):
            # Convert R data.frame to pandas DataFrame
            pandas_df = pandas2ri.rpy2py(r_result)
            return pandas_df
        else:
            # Return as dictionary for other R objects
            return {"r_object": str(r_result), "type": str(type(r_result))}
            
    except Exception as e:
        print(f"Error converting R result: {e}")
        return {"error": str(e), "r_result": str(r_result)}


@data_loading_mcp.tool()
async def load_molecular_profiles_normalized(
    ctx: Context,
    request: LoadMolecularProfilesModel
) -> Dict[str, Any]:
    """
    Load molecular profiles with optional z-score normalization.
    
    Equivalent to R function: loadMolecularProfilesNormalized()
    """
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    # Check if dataset exists
    dataset_r_name = droma_state.get_dataset(request.dataset_name)
    if not dataset_r_name:
        return {
            "status": "error",
            "message": f"Dataset {request.dataset_name} not found. Please load it first."
        }
    
    try:
        # Build R command
        features_str = "NULL"
        if request.features:
            features_str = 'c("' + '", "'.join(request.features) + '")'
        
        r_command = f'''
        result <- loadMolecularProfilesNormalized(
            {dataset_r_name},
            molecular_type = "{request.molecular_type.value}",
            features = {features_str},
            data_type = "{request.data_type.value}",
            tumor_type = "{request.tumor_type}",
            zscore = {str(request.z_score).upper()},
            verbose = {str(request.verbose).upper()}
        )
        '''
        
        await ctx.info(f"Executing R command for molecular profiles: {request.molecular_type.value}")
        
        # Execute R command
        droma_state.r(r_command)
        r_result = droma_state.r('result')
        
        # Convert result to Python
        python_result = _convert_r_to_python(r_result, droma_state)
        
        # Cache the result
        cache_key = f"mol_profiles_{request.dataset_name}_{request.molecular_type.value}"
        droma_state.cache_data(cache_key, python_result, {
            "molecular_type": request.molecular_type.value,
            "zscore_normalized": request.z_score,
            "features": request.features,
            "data_type": request.data_type.value,
            "tumor_type": request.tumor_type
        })
        
        # Get basic stats
        if isinstance(python_result, pd.DataFrame):
            stats = {
                "shape": python_result.shape,
                "features_count": len(python_result.index),
                "samples_count": len(python_result.columns),
                "has_missing_values": python_result.isnull().any().any()
            }
        else:
            stats = {"result_type": "non_matrix"}
        
        await ctx.info(f"Successfully loaded molecular profiles: {stats}")
        
        return {
            "status": "success",
            "cache_key": cache_key,
            "molecular_type": request.molecular_type.value,
            "zscore_normalized": request.z_score,
            "stats": stats,
            "message": f"Loaded {request.molecular_type.value} data for {request.dataset_name}"
        }
        
    except Exception as e:
        await ctx.error(f"Error loading molecular profiles: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to load molecular profiles: {str(e)}"
        }


@data_loading_mcp.tool()
async def load_treatment_response_normalized(
    ctx: Context,
    request: LoadTreatmentResponseModel
) -> Dict[str, Any]:
    """
    Load treatment response data with optional z-score normalization.
    
    Equivalent to R function: loadTreatmentResponseNormalized()
    """
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    # Check if dataset exists
    dataset_r_name = droma_state.get_dataset(request.dataset_name)
    if not dataset_r_name:
        return {
            "status": "error",
            "message": f"Dataset {request.dataset_name} not found. Please load it first."
        }
    
    try:
        # Build R command
        drugs_str = "NULL"
        if request.drugs:
            drugs_str = 'c("' + '", "'.join(request.drugs) + '")'
        
        r_command = f'''
        result <- loadTreatmentResponseNormalized(
            {dataset_r_name},
            drugs = {drugs_str},
            data_type = "{request.data_type.value}",
            tumor_type = "{request.tumor_type}",
            zscore = {str(request.z_score).upper()},
            verbose = {str(request.verbose).upper()}
        )
        '''
        
        await ctx.info(f"Executing R command for treatment response data")
        
        # Execute R command
        droma_state.r(r_command)
        r_result = droma_state.r('result')
        
        # Convert result to Python
        python_result = _convert_r_to_python(r_result, droma_state)
        
        # Cache the result
        cache_key = f"treatment_response_{request.dataset_name}"
        droma_state.cache_data(cache_key, python_result, {
            "drugs": request.drugs,
            "zscore_normalized": request.z_score,
            "data_type": request.data_type.value,
            "tumor_type": request.tumor_type
        })
        
        # Get basic stats
        if isinstance(python_result, pd.DataFrame):
            stats = {
                "shape": python_result.shape,
                "drugs_count": len(python_result.index),
                "samples_count": len(python_result.columns),
                "has_missing_values": python_result.isnull().any().any()
            }
        else:
            stats = {"result_type": "non_matrix"}
        
        await ctx.info(f"Successfully loaded treatment response data: {stats}")
        
        return {
            "status": "success",
            "cache_key": cache_key,
            "drugs": request.drugs,
            "zscore_normalized": request.z_score,
            "stats": stats,
            "message": f"Loaded treatment response data for {request.dataset_name}"
        }
        
    except Exception as e:
        await ctx.error(f"Error loading treatment response: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to load treatment response: {str(e)}"
        }


@data_loading_mcp.tool()
async def load_multi_project_molecular_profiles_normalized(
    ctx: Context,
    request: MultiProjectMolecularProfilesModel
) -> Dict[str, Any]:
    """
    Load multi-project molecular profiles with optional z-score normalization.
    
    Equivalent to R function: loadMultiProjectMolecularProfilesNormalized()
    """
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    # Check if multidataset exists
    multidataset_r_name = droma_state.get_multidataset(request.multidromaset_id)
    if not multidataset_r_name:
        return {
            "status": "error",
            "message": f"MultiDataset {request.multidromaset_id} not found. Please load it first."
        }
    
    try:
        # Build R command
        features_str = "NULL"
        if request.features:
            features_str = 'c("' + '", "'.join(request.features) + '")'
        
        r_command = f'''
        result <- loadMultiProjectMolecularProfilesNormalized(
            {multidataset_r_name},
            molecular_type = "{request.molecular_type.value}",
            features = {features_str},
            overlap_only = {str(request.overlap_only).upper()},
            data_type = "{request.data_type.value}",
            tumor_type = "{request.tumor_type}",
            zscore = {str(request.zscore).upper()}
        )
        '''
        
        await ctx.info(f"Executing R command for multi-project molecular profiles")
        
        # Execute R command
        droma_state.r(r_command)
        r_result = droma_state.r('result')
        
        # Convert result to Python (should be a list of matrices)
        python_result = _convert_r_to_python(r_result, droma_state)
        
        # Cache the result
        cache_key = f"multi_mol_profiles_{request.multidromaset_id}_{request.molecular_type.value}"
        droma_state.cache_data(cache_key, python_result, {
            "molecular_type": request.molecular_type.value,
            "zscore_normalized": request.zscore,
            "features": request.features,
            "overlap_only": request.overlap_only,
            "data_type": request.data_type.value,
            "tumor_type": request.tumor_type
        })
        
        # Get basic stats for multi-project data
        if isinstance(python_result, dict):
            project_stats = {}
            for project, data in python_result.items():
                if isinstance(data, pd.DataFrame):
                    project_stats[project] = {
                        "shape": data.shape,
                        "features_count": len(data.index),
                        "samples_count": len(data.columns)
                    }
            stats = {"projects": project_stats}
        else:
            stats = {"result_type": "unknown"}
        
        await ctx.info(f"Successfully loaded multi-project molecular profiles: {stats}")
        
        return {
            "status": "success",
            "cache_key": cache_key,
            "molecular_type": request.molecular_type.value,
            "zscore_normalized": request.zscore,
            "overlap_only": request.overlap_only,
            "stats": stats,
            "message": f"Loaded multi-project {request.molecular_type.value} data"
        }
        
    except Exception as e:
        await ctx.error(f"Error loading multi-project molecular profiles: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to load multi-project molecular profiles: {str(e)}"
        }


@data_loading_mcp.tool()
async def load_multi_project_treatment_response_normalized(
    ctx: Context,
    request: MultiProjectTreatmentResponseModel
) -> Dict[str, Any]:
    """
    Load multi-project treatment response data with optional z-score normalization.
    
    Equivalent to R function: loadMultiProjectTreatmentResponseNormalized()
    """
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    # Check if multidataset exists
    multidataset_r_name = droma_state.get_multidataset(request.multidromaset_id)
    if not multidataset_r_name:
        return {
            "status": "error",
            "message": f"MultiDataset {request.multidromaset_id} not found. Please load it first."
        }
    
    try:
        # Build R command
        drugs_str = "NULL"
        if request.drugs:
            drugs_str = 'c("' + '", "'.join(request.drugs) + '")'
        
        r_command = f'''
        result <- loadMultiProjectTreatmentResponseNormalized(
            {multidataset_r_name},
            drugs = {drugs_str},
            overlap_only = {str(request.overlap_only).upper()},
            data_type = "{request.data_type.value}",
            tumor_type = "{request.tumor_type}",
            zscore = {str(request.zscore).upper()}
        )
        '''
        
        await ctx.info(f"Executing R command for multi-project treatment response")
        
        # Execute R command
        droma_state.r(r_command)
        r_result = droma_state.r('result')
        
        # Convert result to Python
        python_result = _convert_r_to_python(r_result, droma_state)
        
        # Cache the result
        cache_key = f"multi_treatment_response_{request.multidromaset_id}"
        droma_state.cache_data(cache_key, python_result, {
            "drugs": request.drugs,
            "zscore_normalized": request.zscore,
            "overlap_only": request.overlap_only,
            "data_type": request.data_type.value,
            "tumor_type": request.tumor_type
        })
        
        # Get basic stats for multi-project data
        if isinstance(python_result, dict):
            project_stats = {}
            for project, data in python_result.items():
                if isinstance(data, pd.DataFrame):
                    project_stats[project] = {
                        "shape": data.shape,
                        "drugs_count": len(data.index),
                        "samples_count": len(data.columns)
                    }
            stats = {"projects": project_stats}
        else:
            stats = {"result_type": "unknown"}
        
        await ctx.info(f"Successfully loaded multi-project treatment response: {stats}")
        
        return {
            "status": "success",
            "cache_key": cache_key,
            "drugs": request.drugs,
            "zscore_normalized": request.zscore,
            "overlap_only": request.overlap_only,
            "stats": stats,
            "message": f"Loaded multi-project treatment response data"
        }
        
    except Exception as e:
        await ctx.error(f"Error loading multi-project treatment response: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to load multi-project treatment response: {str(e)}"
        }


@data_loading_mcp.tool()
async def check_zscore_normalization(
    ctx: Context,
    cache_key: str
) -> Dict[str, Any]:
    """
    Check if cached data has been z-score normalized.
    
    Equivalent to R function: isZscoreNormalized()
    """
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    cached_data = droma_state.get_cached_data(cache_key)
    if not cached_data:
        return {
            "status": "error",
            "message": f"No cached data found for key: {cache_key}"
        }
    
    try:
        # Check if data has normalization metadata
        cached_entry = droma_state.data_cache[cache_key]
        metadata = cached_entry.get('metadata', {})
        
        is_normalized = metadata.get('zscore_normalized', False)
        
        # Additional validation for pandas DataFrames
        data = cached_entry['data']
        validation_info = {}
        
        if isinstance(data, pd.DataFrame):
            # Check data characteristics
            validation_info = {
                "data_type": "DataFrame",
                "shape": data.shape,
                "mean_close_to_zero": abs(data.values.mean()) < 0.1,
                "std_close_to_one": abs(data.values.std() - 1.0) < 0.1,
                "has_negative_values": (data.values < 0).any(),
                "sample_statistics": {
                    "mean": float(data.values.mean()),
                    "std": float(data.values.std()),
                    "min": float(data.values.min()),
                    "max": float(data.values.max())
                }
            }
        
        return {
            "status": "success",
            "cache_key": cache_key,
            "is_normalized": is_normalized,
            "validation_info": validation_info,
            "metadata": metadata
        }
        
    except Exception as e:
        await ctx.error(f"Error checking normalization status: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to check normalization status: {str(e)}"
        }


@data_loading_mcp.tool()
async def get_cached_data_info(
    ctx: Context,
    cache_key: Optional[str] = None
) -> Dict[str, Any]:
    """Get information about cached data."""
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    if cache_key:
        # Get info for specific cached data
        cached_entry = droma_state.data_cache.get(cache_key)
        if not cached_entry:
            return {
                "status": "error",
                "message": f"No cached data found for key: {cache_key}"
            }
        
        data = cached_entry['data']
        metadata = cached_entry.get('metadata', {})
        timestamp = cached_entry.get('timestamp')
        
        data_info = {
            "cache_key": cache_key,
            "timestamp": str(timestamp),
            "metadata": metadata,
            "data_type": str(type(data)),
        }
        
        if isinstance(data, pd.DataFrame):
            data_info.update({
                "shape": data.shape,
                "columns": list(data.columns),
                "index_count": len(data.index)
            })
        
        return {
            "status": "success",
            "data_info": data_info
        }
    else:
        # List all cached data
        cache_summary = {}
        for key, entry in droma_state.data_cache.items():
            cache_summary[key] = {
                "timestamp": str(entry.get('timestamp')),
                "data_type": str(type(entry['data'])),
                "metadata": entry.get('metadata', {})
            }
        
        return {
            "status": "success",
            "cached_items": cache_summary,
            "total_items": len(cache_summary)
        }


@data_loading_mcp.tool()
async def export_cached_data(
    ctx: Context,
    cache_key: str,
    file_format: str = "csv",
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """Export cached data to file."""
    # Get DROMA state
    droma_state = ctx.request_context.lifespan_context
    
    cached_data = droma_state.get_cached_data(cache_key)
    if not cached_data:
        return {
            "status": "error",
            "message": f"No cached data found for key: {cache_key}"
        }
    
    try:
        # Use utility function for saving
        from ..util import save_analysis_result
        
        if isinstance(cached_data, pd.DataFrame):
            export_id = save_analysis_result(cached_data, filename, file_format)
            
            return {
                "status": "success",
                "export_id": export_id,
                "filename": filename,
                "file_format": file_format,
                "data_shape": cached_data.shape,
                "message": f"Data exported successfully as {export_id}"
            }
        else:
            return {
                "status": "error",
                "message": "Only pandas DataFrame can be exported to structured files"
            }
            
    except Exception as e:
        await ctx.error(f"Error exporting data: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to export data: {str(e)}"
        } 