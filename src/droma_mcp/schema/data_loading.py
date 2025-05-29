"""Pydantic schemas for DROMA data loading operations."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Any
from enum import Enum


class MolecularType(str, Enum):
    """Supported molecular data types."""
    MRNA = "mRNA"
    CNV = "cnv"
    METH = "meth"
    PROTEIN_RPPA = "proteinrppa"
    PROTEIN_MS = "proteinms"
    MUTATION_GENE = "mutation_gene"
    MUTATION_SITE = "mutation_site"
    FUSION = "fusion"


class DataType(str, Enum):
    """Supported data types."""
    ALL = "all"
    CELL_LINE = "CellLine"
    PDO = "PDO"
    PDC = "PDC"
    PDX = "PDX"


class LoadMolecularProfilesModel(BaseModel):
    """Schema for loading molecular profiles with z-score normalization."""
    
    dromaset_id: str = Field(
        description="DromaSet object identifier"
    )
    molecular_type: MolecularType = Field(
        description="Type of molecular data to load"
    )
    features: Optional[List[str]] = Field(
        default=None,
        description="Specific features to load. If None, loads all features"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type ('all' or specific tumor types)"
    )
    zscore: bool = Field(
        default=True,
        description="Whether to apply z-score normalization"
    )
    return_data: bool = Field(
        default=True,
        description="Whether to return the data directly"
    )


class LoadTreatmentResponseModel(BaseModel):
    """Schema for loading treatment response data with z-score normalization."""
    
    dromaset_id: str = Field(
        description="DromaSet object identifier"
    )
    drugs: Optional[List[str]] = Field(
        default=None,
        description="Specific drugs to load. If None, loads all drugs"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type ('all' or specific tumor types)"
    )
    zscore: bool = Field(
        default=True,
        description="Whether to apply z-score normalization"
    )
    return_data: bool = Field(
        default=True,
        description="Whether to return the data directly"
    )


class MultiProjectMolecularProfilesModel(BaseModel):
    """Schema for loading multi-project molecular profiles with z-score normalization."""
    
    multidromaset_id: str = Field(
        description="MultiDromaSet object identifier"
    )
    molecular_type: MolecularType = Field(
        description="Type of molecular data to load"
    )
    features: Optional[List[str]] = Field(
        default=None,
        description="Specific features to load"
    )
    overlap_only: bool = Field(
        default=False,
        description="Whether to use only overlapping samples"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type"
    )
    zscore: bool = Field(
        default=True,
        description="Whether to apply z-score normalization"
    )


class MultiProjectTreatmentResponseModel(BaseModel):
    """Schema for loading multi-project treatment response data with z-score normalization."""
    
    multidromaset_id: str = Field(
        description="MultiDromaSet object identifier"
    )
    drugs: Optional[List[str]] = Field(
        default=None,
        description="Specific drugs to load"
    )
    overlap_only: bool = Field(
        default=False,
        description="Whether to use only overlapping samples"
    )
    data_type: DataType = Field(
        default=DataType.ALL,
        description="Filter by data type"
    )
    tumor_type: str = Field(
        default="all",
        description="Filter by tumor type"
    )
    zscore: bool = Field(
        default=True,
        description="Whether to apply z-score normalization"
    )


class ZscoreNormalizationModel(BaseModel):
    """Schema for z-score normalization operations."""
    
    data_id: str = Field(
        description="Identifier for the data to normalize"
    )
    check_type: bool = Field(
        default=True,
        description="Whether to check if data appears to be continuous"
    )


class DataValidationModel(BaseModel):
    """Schema for data validation responses."""
    
    is_normalized: bool = Field(
        description="Whether data has been z-score normalized"
    )
    data_shape: tuple = Field(
        description="Shape of the data matrix (rows, columns)"
    )
    feature_count: int = Field(
        description="Number of features in the dataset"
    )
    sample_count: int = Field(
        description="Number of samples in the dataset"
    )
    data_type: str = Field(
        description="Type of data (continuous, discrete, etc.)"
    )
    normalization_applicable: bool = Field(
        description="Whether z-score normalization is applicable to this data type"
    )


class BatchLoadModel(BaseModel):
    """Schema for batch loading operations."""
    
    dromaset_ids: List[str] = Field(
        description="List of DromaSet identifiers to load"
    )
    molecular_types: List[MolecularType] = Field(
        description="Molecular data types to load"
    )
    features: Optional[List[str]] = Field(
        default=None,
        description="Specific features to load across all datasets"
    )
    normalize_separately: bool = Field(
        default=True,
        description="Whether to normalize each dataset separately"
    )
    merge_strategy: Literal["intersect", "union", "separate"] = Field(
        default="separate",
        description="How to handle features across datasets"
    )


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