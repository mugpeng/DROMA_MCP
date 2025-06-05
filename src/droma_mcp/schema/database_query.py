"""Pydantic schemas for DROMA database query operations."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class DataType(str, Enum):
    """Supported data types."""
    ALL = "all"
    CELL_LINE = "CellLine"
    PDO = "PDO"
    PDC = "PDC"
    PDX = "PDX"


class GetAnnotationModel(BaseModel):
    """Schema for retrieving annotation data from DROMA database."""
    
    anno_type: Literal["sample", "drug"] = Field(
        description="Type of annotation to retrieve: 'sample' or 'drug'"
    )
    project_name: Optional[str] = Field(
        default=None,
        description="Project name to filter results (None for all projects)"
    )
    ids: Optional[List[str]] = Field(
        default=None,
        description="Specific IDs to retrieve (SampleID for samples, DrugName for drugs)"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type (for sample annotations only)"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type (for sample annotations only)"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of records to return"
    )


class ListSamplesModel(BaseModel):
    """Schema for listing available samples in DROMA database."""
    
    project_name: str = Field(
        description="Name of the project (e.g., 'gCSI', 'CCLE')"
    )
    data_sources: str = Field(
        default="all",
        description="Filter by data sources: 'all' or specific data type (e.g., 'mRNA', 'cnv', 'drug')"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of samples to return"
    )
    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern to filter sample names"
    )


class ListFeaturesModel(BaseModel):
    """Schema for listing available features in DROMA database."""
    
    project_name: str = Field(
        description="Name of the project (e.g., 'gCSI', 'CCLE')"
    )
    data_sources: str = Field(
        description="Type of data to query (e.g., 'mRNA', 'cnv', 'drug', 'mutation_gene')"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of features to return"
    )
    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern to filter feature names"
    )


class ListProjectsModel(BaseModel):
    """Schema for listing available projects in DROMA database."""
    
    show_names_only: bool = Field(
        default=False,
        description="If True returns only a list of project names"
    )
    project_data_types: Optional[str] = Field(
        default=None,
        description="Project name to get specific data types for"
    ) 