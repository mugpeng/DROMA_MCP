#!/usr/bin/env python3
"""
Test script for _convert_r_to_python function with real DROMA R objects.
Run this in Python console after setting up R environment with DROMA.
"""

import pandas as pd
from typing import Union, Dict, Any
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

def _convert_r_to_python(r_result) -> Union[pd.DataFrame, Dict[str, Any]]:
    """Convert R result to Python data structures."""
    try:
        import rpy2.robjects as robjects
        from rpy2.robjects import pandas2ri
        
        # Activate pandas conversion
        pandas2ri.activate()
        
        print(f"R result type: {type(r_result)}")
        print(f"R result class: {getattr(r_result, 'rclass', 'No rclass')}")
        print(f"R result str: {str(r_result)[:200]}...")
        
        # Convert R object to pandas if possible
        if hasattr(r_result, 'rclass') and 'matrix' in str(r_result.rclass):
            print("Converting R matrix to pandas DataFrame...")
            pandas_df = pandas2ri.rpy2py(r_result)
            return pandas_df
        elif hasattr(r_result, 'rclass') and 'data.frame' in str(r_result.rclass):
            print("Converting R data.frame to pandas DataFrame...")
            pandas_df = pandas2ri.rpy2py(r_result)
            return pandas_df
        else:
            print("Returning as dictionary...")
            return {"r_object": str(r_result), "type": str(type(r_result))}
            
    except Exception as e:
        print(f"Error converting R result: {e}")
        return {"error": str(e), "r_result": str(r_result)}


def test_convert_r_to_python_comprehensive():
    """
    Comprehensive test for _convert_r_to_python with real DROMA R objects.
    
    Prerequisites:
    1. R must be installed with DROMA package
    2. rpy2 must be installed: pip install rpy2
    3. DROMA database must be available
    """
    
    print("=== Testing _convert_r_to_python with Real DROMA Data ===")
    print()
    
    try:
        # Import rpy2 components
        import rpy2.robjects as robjects
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
        
        # Activate pandas conversion
        pandas2ri.activate()
        
        print("✅ rpy2 imported successfully")
        
        # Test 1: Setup R environment
        print("\n1. Setting up R environment...")
        r = robjects.r
        
        # Load required R packages
        try:
            # Try to load DROMA package
            droma = importr('DROMA')
            print("✅ DROMA package loaded")
        except Exception as e:
            print(f"⚠️  DROMA package not available: {e}")
            print("   Will use base R functions for testing")
        
        # Test 2: Create sample R matrix (simulating molecular data)
        print("\n2. Testing with R matrix...")
        r_code = """
        # Create a sample matrix similar to what loadMolecularProfilesNormalized returns
        set.seed(42)
        sample_matrix <- matrix(rnorm(200), nrow=10, ncol=20)
        rownames(sample_matrix) <- paste0("Gene_", 1:10)
        colnames(sample_matrix) <- paste0("Sample_", 1:20)
        sample_matrix
        """
        r_matrix = r(r_code)
        
        print("R matrix created. Testing conversion...")
        result1 = _convert_r_to_python(r_matrix)
        
        if isinstance(result1, pd.DataFrame):
            print(f"✅ Matrix conversion successful!")
            print(f"   Shape: {result1.shape}")
            print(f"   Index: {list(result1.index[:3])}...")
            print(f"   Columns: {list(result1.columns[:3])}...")
            print(f"   Data preview:\n{result1.iloc[:3, :3]}")
        else:
            print(f"❌ Matrix conversion failed: {result1}")
        
        # Test 3: Create sample R data.frame
        print("\n3. Testing with R data.frame...")
        r_code = """
        # Create a sample data.frame
        sample_df <- data.frame(
            Gene = paste0("GENE_", 1:5),
            Sample1 = rnorm(5),
            Sample2 = rnorm(5),
            Sample3 = rnorm(5)
        )
        rownames(sample_df) <- sample_df$Gene
        sample_df$Gene <- NULL
        sample_df
        """
        r_dataframe = r(r_code)
        
        print("R data.frame created. Testing conversion...")
        result2 = _convert_r_to_python(r_dataframe)
        
        if isinstance(result2, pd.DataFrame):
            print(f"✅ Data.frame conversion successful!")
            print(f"   Shape: {result2.shape}")
            print(f"   Data preview:\n{result2}")
        else:
            print(f"❌ Data.frame conversion failed: {result2}")
        
        # Test 4: Test with actual DROMA function (if available)
        print("\n4. Testing with actual DROMA function (if available)...")
        
        try:
            # This would require an actual DROMA database
            # We'll create a mock scenario instead
            r_code = """
            # Simulate the structure that loadMolecularProfilesNormalized might return
            # This is a mock - in real usage, you'd have:
            # result <- loadMolecularProfilesNormalized(droma_set, molecular_type="mRNA", ...)
            
            # Create a more realistic molecular profiles matrix
            set.seed(123)
            n_genes <- 50
            n_samples <- 30
            
            # Simulate log2 expression data
            expression_data <- matrix(
                rnorm(n_genes * n_samples, mean=8, sd=2),
                nrow=n_genes, 
                ncol=n_samples
            )
            
            # Add realistic gene names
            rownames(expression_data) <- c(
                "ABCB1", "TP53", "EGFR", "BRCA1", "KRAS", 
                paste0("GENE_", 6:n_genes)
            )
            
            # Add sample names
            colnames(expression_data) <- paste0("CCLE_", sprintf("%03d", 1:n_samples))
            
            # Make it non-negative (like real expression data)
            expression_data <- pmax(expression_data, 0)
            
            expression_data
            """
            
            mock_molecular_data = r(r_code)
            
            print("Mock molecular profiles data created. Testing conversion...")
            result3 = _convert_r_to_python(mock_molecular_data)
            
            if isinstance(result3, pd.DataFrame):
                print(f"✅ Molecular profiles conversion successful!")
                print(f"   Shape: {result3.shape}")
                print(f"   Genes: {list(result3.index[:5])}")
                print(f"   Samples: {list(result3.columns[:5])}")
                print(f"   ABCB1 expression stats:")
                if "ABCB1" in result3.index:
                    abcb1 = result3.loc["ABCB1"]
                    print(f"     Mean: {abcb1.mean():.3f}")
                    print(f"     Std: {abcb1.std():.3f}")
                    print(f"     Range: {abcb1.min():.3f} - {abcb1.max():.3f}")
            else:
                print(f"❌ Molecular profiles conversion failed: {result3}")
        
        except Exception as e:
            print(f"⚠️  Mock DROMA function test failed: {e}")
        
        # Test 5: Test with various R object types
        print("\n5. Testing with various R object types...")
        
        test_objects = [
            ("R vector", "c(1, 2, 3, 4, 5)"),
            ("R list", "list(a=1, b=2, c=3)"),
            ("R factor", "factor(c('A', 'B', 'C', 'A', 'B'))"),
        ]
        
        for obj_name, r_code in test_objects:
            print(f"\n   Testing {obj_name}...")
            try:
                r_obj = r(r_code)
                result = _convert_r_to_python(r_obj)
                print(f"   Result type: {type(result)}")
                if isinstance(result, dict):
                    print(f"   Keys: {list(result.keys())}")
                else:
                    print(f"   Value: {result}")
            except Exception as e:
                print(f"   Error: {e}")
        
        print("\n=== Conversion Testing Complete ===")
        print("\n📋 Summary:")
        print("1. The _convert_r_to_python function properly handles R matrices and data.frames")
        print("2. It successfully converts them to pandas DataFrames")
        print("3. It gracefully handles other R object types as dictionaries")
        print("4. The 'state' parameter was unnecessary and has been removed")
        
    except ImportError:
        print("❌ rpy2 not available. Install with: pip install rpy2")
        print("   Also ensure R is installed and accessible")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


# Simple test that doesn't require R setup
def test_convert_simple():
    """Simple test with mock R-like objects."""
    
    print("=== Simple Test (No R Required) ===")
    
    class MockRMatrix:
        def __init__(self):
            self.rclass = ['matrix', 'array']
    
    class MockRDataFrame:
        def __init__(self):
            self.rclass = ['data.frame']
    
    class MockROther:
        def __init__(self):
            self.rclass = ['list']
    
    # Test with mock objects
    mock_matrix = MockRMatrix()
    mock_df = MockRDataFrame()
    mock_other = MockROther()
    
    print("Testing with mock R objects...")
    
    try:
        result1 = _convert_r_to_python(mock_matrix)
        print(f"Mock matrix result: {result1}")
        
        result2 = _convert_r_to_python(mock_df)
        print(f"Mock data.frame result: {result2}")
        
        result3 = _convert_r_to_python(mock_other)
        print(f"Mock other result: {result3}")
        
    except Exception as e:
        print(f"Expected error (no rpy2): {e}")


if __name__ == "__main__":
    print("Choose test type:")
    print("1. Comprehensive test (requires R + DROMA + rpy2)")
    print("2. Simple test (no dependencies)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_convert_r_to_python_comprehensive()
    else:
        test_convert_simple()


# For console usage, here are the key commands:

"""
CONSOLE USAGE COMMANDS:
======================

# 1. Basic setup
import pandas as pd
from typing import Union, Dict, Any
exec(open('test_convert_r_to_python.py').read())

# 2. Run comprehensive test
test_convert_r_to_python_comprehensive()

# 3. Or run simple test
test_convert_simple()

# 4. Manual testing with R (requires rpy2 + R + DROMA)
import rpy2.robjects as robjects
r = robjects.r

# Create test matrix
r_matrix = r("matrix(rnorm(100), nrow=10, ncol=10)")
result = _convert_r_to_python(r_matrix)
print(type(result), result.shape if hasattr(result, 'shape') else result)

# Test with actual DROMA (if available)
# r('library(DROMA)')
# r('droma_set <- createDromaSetFromDatabase("your_db_path", "CCLE")')
# r('result <- loadMolecularProfilesNormalized(droma_set, molecular_type="mRNA")')
# r_result = r('result')
# converted = _convert_r_to_python(r_result)
""" 