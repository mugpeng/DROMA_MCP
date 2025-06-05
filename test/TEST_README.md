# Testing DROMA MCP Functions

This guide shows you how to test the DROMA MCP functions, specifically `list_droma_projects` and other database query functions.

## Prerequisites

1. Make sure you have a DROMA database file (SQLite)
2. Set the `DROMA_DB_PATH` environment variable:
   ```bash
   export DROMA_DB_PATH=/path/to/your/droma_database.db
   ```

## Test Files Created

### 1. `test_simple.py` - Direct Function Testing (Recommended for debugging)
This directly calls the function without running a full MCP server.

**Usage:**
```bash
python test_simple.py
```

**What it does:**
- Tests `list_droma_projects` with different parameters
- Shows direct function call results
- Good for debugging and understanding function behavior

### 2. `test_server.py` - MCP Server for Testing
This creates a standalone MCP server with your database query functions.

**Usage:**
```bash
# Run in background
python test_server.py &
```

**What it does:**
- Creates an MCP server with database query tools
- Lists available tools on startup
- Runs in background for client connections

### 3. `test_client.py` - MCP Client Testing
This connects to the MCP server and calls tools like a real client.

**Usage:**
```bash
# Make sure test_server.py is running first
python test_client.py
```

**What it does:**
- Connects to the MCP server
- Calls `list_droma_projects` with different parameters
- Shows how to use the MCP client-server architecture

## Test Examples

### Testing `list_droma_projects`

The function accepts these parameters via `ListProjectsModel`:

```python
# List all projects (full information)
request = ListProjectsModel(
    show_names_only=False,
    project_data_types=None
)

# List only project names
request = ListProjectsModel(
    show_names_only=True,
    project_data_types=None
)

# Get data types for a specific project
request = ListProjectsModel(
    show_names_only=False,
    project_data_types="gCSI"  # Replace with your project name
)
```

### Expected Results

1. **Full project list**: Returns detailed project information
2. **Names only**: Returns just project names array
3. **Project data types**: Returns available data types for specified project

## Troubleshooting

### Common Issues:

1. **"No database path configured"**
   - Make sure `DROMA_DB_PATH` is set
   - Check that the database file exists

2. **Import errors**
   - The test files automatically add `src/` to Python path
   - Make sure you're running from the project root directory

3. **"Database file not found"**
   - Verify the path in `DROMA_DB_PATH`
   - Check file permissions

### Quick Test Without Database

If you don't have a database yet, you can still test the function structure:

```python
# In test_simple.py, comment out the database path requirement
# The function will return an error, but you can see the structure
```

## Adding More Tests

To test other functions, you can extend the test files:

```python
# Test get_droma_annotation
from src.droma_mcp.server.database_query import get_droma_annotation
from src.droma_mcp.schema.database_query import GetAnnotationModel

# Test list_droma_samples  
from src.droma_mcp.server.database_query import list_droma_samples
from src.droma_mcp.schema.database_query import ListSamplesModel
```

## Example Output

When working correctly, you should see output like:

```
=== Direct Function Test ===

1. Testing: List all projects
INFO: Found 3 projects in database
Result: {
    'status': 'success', 
    'projects': [
        {'project_name': 'gCSI', 'source': 'inferred_from_tables'},
        {'project_name': 'CCLE', 'source': 'inferred_from_tables'}
    ],
    'total_projects': 2,
    'message': 'Found 2 projects (inferred from table names)'
} 