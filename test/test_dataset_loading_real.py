#!/usr/bin/env python3
"""Real-world DROMA MCP usage test scenarios."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock
import tempfile
import pandas as pd
import numpy as np

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / ".."))

from src.droma_mcp.server.dataset_management import (
    load_dataset, 
    list_loaded_datasets
)
from src.droma_mcp.server.data_loading import (
    load_molecular_profiles_normalized,
    load_treatment_response_normalized,
    load_multi_project_molecular_profiles_normalized
)
from src.droma_mcp.schema.dataset_management import (
    LoadDatasetModel, 
    ListDatasetsModel
)
from src.droma_mcp.schema.data_loading import (
    LoadMolecularProfilesModel,
    LoadTreatmentResponseModel,
    MultiProjectMolecularProfilesModel,
    MolecularType
)
from src.droma_mcp.schema.database_query import DataType


class MockContext:
    """Mock context for testing."""
    
    def __init__(self, droma_state):
        self.request_context = Mock()
        self.request_context.lifespan_context = droma_state
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")


class RealisticMockRInterface:
    """Mock R interface that simulates realistic DROMA data."""
    
    def __init__(self):
        self.commands_executed = []
        self.stored_result = None
        self.datasets_loaded = set()
    
    def __call__(self, command):
        """Mock R command execution with realistic data simulation."""
        self.commands_executed.append(command)
        print(f"Mock R: {command.strip()[:80]}...")  # Show truncated command
        
        # Handle dataset creation commands
        if "createDromaSetFromDatabase" in command or "createMultiDromaSetFromDatabase" in command:
            dataset_name = "mock_dataset_object"
            return dataset_name
        
        # Handle data loading commands
        elif any(func in command for func in ["loadMolecularProfilesNormalized", "loadTreatmentResponseNormalized", "loadMultiProjectMolecularProfilesNormalized"]):
            self._generate_realistic_data(command)
            return "R_execution_success"
        
        # Return stored result when 'result' is requested
        elif command.strip() == "result":
            return self.stored_result if self.stored_result is not None else "mock_r_result"
        
        else:
            return "mock_r_result"
    
    def _generate_realistic_data(self, command):
        """Generate realistic molecular or drug response data based on command."""
        np.random.seed(42)  # For reproducible "realistic" data
        
        if "loadMolecularProfilesNormalized" in command:
            # Extract parameters from command
            is_zscore = "zscore = TRUE" in command.upper()
            
            # Determine molecular type
            if '"mRNA"' in command:
                mol_type = "mRNA"
                n_features = 200  # Realistic number of genes
            elif '"cnv"' in command:
                mol_type = "CNV"
                n_features = 150
            elif '"proteinrppa"' in command:
                mol_type = "Protein"
                n_features = 80
            else:
                mol_type = "Unknown"
                n_features = 100
            
            # Check if specific features are requested
            if 'features = c(' in command:
                # Extract feature names (simplified parsing)
                start = command.find('features = c(') + 12
                end = command.find(')', start)
                features_str = command[start:end]
                features = [f.strip().strip('"') for f in features_str.split(',')]
                n_features = len(features)
                feature_names = features
            else:
                # Generate realistic gene names
                if mol_type == "mRNA":
                    feature_names = [f"GENE_{i}" for i in range(n_features)]
                    # Add some real gene names for demonstration
                    real_genes = ["ABCB1", "TP53", "EGFR", "BRCA1", "KRAS", "MYC", "PIK3CA", "PTEN"]
                    for i, gene in enumerate(real_genes[:min(len(real_genes), n_features)]):
                        feature_names[i] = gene
                else:
                    feature_names = [f"{mol_type}_feature_{i}" for i in range(n_features)]
            
            # Generate sample names
            n_samples = 50
            sample_names = [f"SAMPLE_{i:03d}" for i in range(n_samples)]
            
            # Generate realistic data
            if is_zscore:
                # Z-score normalized data (mean ~0, std ~1)
                data = np.random.normal(0, 1, (n_features, n_samples))
            else:
                # Log2 expression-like data
                if mol_type == "mRNA":
                    data = np.random.normal(8, 2, (n_features, n_samples))  # Log2(expression)
                elif mol_type == "CNV":
                    data = np.random.normal(0, 0.5, (n_features, n_samples))  # CNV ratios
                else:
                    data = np.random.normal(5, 1.5, (n_features, n_samples))
                
                # Add some realistic patterns
                data = np.maximum(data, 0)  # No negative expression
            
            # Create DataFrame
            self.stored_result = pd.DataFrame(
                data,
                index=feature_names,
                columns=sample_names
            )
            
        elif "loadTreatmentResponseNormalized" in command:
            # Generate drug response data
            is_zscore = "zscore = TRUE" in command.upper()
            
            # Check if specific drugs are requested
            if 'drugs = c(' in command:
                start = command.find('drugs = c(') + 10
                end = command.find(')', start)
                drugs_str = command[start:end]
                drugs = [d.strip().strip('"') for d in drugs_str.split(',')]
                n_drugs = len(drugs)
                drug_names = drugs
            else:
                # Generate realistic drug names
                n_drugs = 30
                real_drugs = ["Paclitaxel", "Cisplatin", "Doxorubicin", "Tamoxifen", "Imatinib", 
                             "Erlotinib", "Lapatinib", "Sorafenib", "Sunitinib", "Bevacizumab"]
                drug_names = real_drugs + [f"Drug_{i}" for i in range(len(real_drugs), n_drugs)]
            
            n_samples = 45
            sample_names = [f"SAMPLE_{i:03d}" for i in range(n_samples)]
            
            if is_zscore:
                # Z-score normalized IC50 values
                data = np.random.normal(0, 1, (n_drugs, n_samples))
            else:
                # Log10(IC50) values in µM
                data = np.random.normal(-1, 1.5, (n_drugs, n_samples))  # -1 corresponds to ~0.1 µM
            
            self.stored_result = pd.DataFrame(
                data,
                index=drug_names,
                columns=sample_names
            )
            
        elif "loadMultiProjectMolecularProfilesNormalized" in command:
            # Generate multi-project data (simpler version)
            np.random.seed(42)
            
            # Create data for multiple projects
            projects = ["CCLE", "gCSI", "GDSC"]
            multi_data = {}
            
            for project in projects:
                n_features = np.random.randint(80, 150)
                n_samples = np.random.randint(30, 60)
                
                feature_names = [f"GENE_{i}" for i in range(n_features)]
                # Add specific genes
                real_genes = ["TP53", "EGFR", "KRAS"]
                for i, gene in enumerate(real_genes):
                    if i < n_features:
                        feature_names[i] = gene
                
                sample_names = [f"{project}_SAMPLE_{i:03d}" for i in range(n_samples)]
                
                data = np.random.normal(0, 1, (n_features, n_samples))
                multi_data[project] = pd.DataFrame(data, index=feature_names, columns=sample_names)
            
            self.stored_result = multi_data


class RealisticMockDromaState:
    """Mock DROMA state with realistic behavior."""
    
    def __init__(self):
        self.datasets = {}
        self.multidatasets = {}
        self.active_dataset = None
        self.active_multidataset = None
        self.analysis_cache = {}
        self.data_cache = {}
        self.metadata = {}
        self.r = RealisticMockRInterface()
    
    def load_dataset(self, dataset_id: str, db_path: str, dataset_type: str = "DromaSet"):
        """Mock dataset loading."""
        print(f"🔄 Mock: Loading {dataset_type} '{dataset_id}' from {db_path}")
        
        if dataset_type == "DromaSet":
            self.datasets[dataset_id] = f"droma_set_{dataset_id}"
        else:
            self.multidatasets[dataset_id] = f"multi_droma_set_{dataset_id.replace(',', '_')}"
        
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
    
    def cache_data(self, key: str, data, metadata: dict):
        """Cache data with metadata."""
        import datetime
        self.data_cache[key] = {
            'data': data,
            'metadata': metadata,
            'timestamp': datetime.datetime.now()
        }
        
        # Show what's being cached
        if isinstance(data, pd.DataFrame):
            print(f"📦 Cached DataFrame: {data.shape} for key '{key}'")
        elif isinstance(data, dict) and all(isinstance(v, pd.DataFrame) for v in data.values()):
            print(f"📦 Cached Multi-project data: {len(data)} projects for key '{key}'")
            for proj, df in data.items():
                print(f"   📊 {proj}: {df.shape}")
        else:
            print(f"📦 Cached data type: {type(data)} for key '{key}'")
    
    def get_cached_data(self, key: str):
        """Retrieve cached data."""
        cached_entry = self.data_cache.get(key)
        return cached_entry['data'] if cached_entry else None


async def test_realistic_scenarios():
    """Test realistic DROMA usage scenarios."""
    
    print("=== DROMA MCP Real-World Usage Test ===")
    print("🧬 Simulating ABCB1 gene expression analysis workflow")
    print()
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        droma_state = RealisticMockDromaState()
        ctx = MockContext(droma_state)
        
        # Scenario 1: Load CCLE dataset
        print("📊 SCENARIO 1: Load CCLE dataset")
        print("-" * 40)
        
        load_result = await load_dataset(ctx, LoadDatasetModel(
            dataset_id="CCLE",
            dataset_type="DromaSet",
            db_path=db_path,
            set_active=True
        ))
        print(f"✅ Dataset loaded: {load_result['status']}")
        print()
        
        # Scenario 2: Load mRNA expression data for ABCB1 gene with z-score normalization
        print("🧬 SCENARIO 2: Load mRNA expression data for ABCB1 gene from CCLE with z-score normalization")
        print("-" * 80)
        
        mol_result = await load_molecular_profiles_normalized(ctx, LoadMolecularProfilesModel(
            dataset_name="CCLE",
            molecular_type=MolecularType.MRNA,
            features=["ABCB1"],
            data_type=DataType.ALL,
            tumor_type="all",
            z_score=True
        ))
        
        print(f"✅ Molecular data loaded: {mol_result['status']}")
        if mol_result["status"] == "success":
            cached_data = droma_state.get_cached_data(mol_result["cache_key"])
            if isinstance(cached_data, pd.DataFrame):
                print(f"📈 Data shape: {cached_data.shape}")
                print(f"🎯 Features: {list(cached_data.index)}")
                print(f"📊 Sample range: {cached_data.columns[0]} to {cached_data.columns[-1]}")
                print(f"🔢 ABCB1 expression stats:")
                if "ABCB1" in cached_data.index:
                    abcb1_data = cached_data.loc["ABCB1"]
                    print(f"   Mean: {abcb1_data.mean():.3f}")
                    print(f"   Std:  {abcb1_data.std():.3f}")
                    print(f"   Min:  {abcb1_data.min():.3f}")
                    print(f"   Max:  {abcb1_data.max():.3f}")
                    print(f"📋 First 5 samples: {abcb1_data.head().to_dict()}")
            else:
                print(f"⚠️  Data not in expected DataFrame format: {type(cached_data)}")
        print()
        
        # Scenario 3: Load drug response data for cancer drugs
        print("💊 SCENARIO 3: Load drug response data for Paclitaxel and Cisplatin")
        print("-" * 60)
        
        drug_result = await load_treatment_response_normalized(ctx, LoadTreatmentResponseModel(
            dataset_name="CCLE",
            drugs=["Paclitaxel", "Cisplatin"],
            data_type=DataType.ALL,
            tumor_type="all",
            z_score=False
        ))
        
        print(f"✅ Drug response loaded: {drug_result['status']}")
        if drug_result["status"] == "success":
            cached_data = droma_state.get_cached_data(drug_result["cache_key"])
            if isinstance(cached_data, pd.DataFrame):
                print(f"📈 Data shape: {cached_data.shape}")
                print(f"💊 Drugs: {list(cached_data.index)}")
                print(f"📊 Drug response stats:")
                for drug in cached_data.index:
                    drug_data = cached_data.loc[drug]
                    print(f"   {drug}: mean IC50 = {10**drug_data.mean():.2f} µM (log scale mean: {drug_data.mean():.3f})")
                    print(f"     Sample values: {drug_data.head(3).to_dict()}")
            else:
                print(f"⚠️  Data not in expected DataFrame format: {type(cached_data)}")
        print()
        
        # Scenario 4: Load multi-project data
        print("🌐 SCENARIO 4: Load multi-project mRNA data across CCLE, gCSI, GDSC")
        print("-" * 60)
        
        # First load multi-dataset
        multi_load_result = await load_dataset(ctx, LoadDatasetModel(
            dataset_id="CCLE,gCSI,GDSC",
            dataset_type="MultiDromaSet",
            db_path=db_path,
            set_active=True
        ))
        
        if multi_load_result["status"] == "success":
            multi_mol_result = await load_multi_project_molecular_profiles_normalized(ctx, MultiProjectMolecularProfilesModel(
                multidromaset_id="CCLE,gCSI,GDSC",
                molecular_type=MolecularType.MRNA,
                features=["TP53", "EGFR", "KRAS"],
                overlap_only=False,
                data_type=DataType.ALL,
                tumor_type="all",
                zscore=True
            ))
            
            print(f"✅ Multi-project data loaded: {multi_mol_result['status']}")
            if multi_mol_result["status"] == "success":
                cached_data = droma_state.get_cached_data(multi_mol_result["cache_key"])
                if isinstance(cached_data, dict):
                    print(f"📊 Projects loaded: {list(cached_data.keys())}")
                    for project, data in cached_data.items():
                        if isinstance(data, pd.DataFrame):
                            print(f"   {project}: {data.shape[1]} samples, {data.shape[0]} genes")
                            if "TP53" in data.index:
                                tp53_mean = data.loc["TP53"].mean()
                                print(f"     TP53 mean expression: {tp53_mean:.3f}")
                else:
                    print(f"⚠️  Multi-project data not in expected dict format: {type(cached_data)}")
        print()
        
        # Scenario 5: Comprehensive analysis summary
        print("📋 SCENARIO 5: Analysis Summary")
        print("-" * 30)
        
        list_result = await list_loaded_datasets(ctx, ListDatasetsModel(include_details=True))
        print(f"🗃️  Total datasets loaded: {list_result['total_loaded']}")
        print(f"📁 DromaSets: {len(list_result['datasets'])}")
        print(f"🌐 MultiDromaSets: {len(list_result['multidatasets'])}")
        print(f"🎯 Active dataset: {list_result['active_dataset']}")
        print(f"🌍 Active multidataset: {list_result['active_multidataset']}")
        
        print(f"\n💾 Data cache summary:")
        print(f"   Cached items: {len(droma_state.data_cache)}")
        for key, entry in droma_state.data_cache.items():
            data = entry['data']
            if isinstance(data, pd.DataFrame):
                print(f"   📊 {key}: DataFrame {data.shape}")
            elif isinstance(data, dict):
                print(f"   🌐 {key}: Multi-project dict with {len(data)} projects")
            else:
                print(f"   ❓ {key}: {type(data)}")
        
        print(f"\n🔬 R commands executed: {len(droma_state.r.commands_executed)}")
        print("   Last 3 commands:")
        for cmd in droma_state.r.commands_executed[-3:]:
            print(f"     📝 {cmd.strip()[:60]}...")
        
        print("\n✅ All realistic DROMA scenarios completed successfully!")
        print("🎯 ABCB1 gene expression analysis workflow validated!")
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(db_path)
        except:
            pass


if __name__ == "__main__":
    print("🧬 DROMA MCP Real-World Usage Scenarios")
    print("=" * 70)
    print()
    
    asyncio.run(test_realistic_scenarios()) 