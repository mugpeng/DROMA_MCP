# DROMA MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for **DROMA** (Drug Response Omics association MAp) - enabling natural language interactions with drug-omics association analysis.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.3+-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

DROMA MCP Server bridges the gap between AI assistants and cancer pharmacogenomics analysis by providing a natural language interface to the [DROMA.R](https://github.com/mugpeng/DROMA_R) and [DROMA.Set](https://github.com/mugpeng/DROMA_Set) packages.

### Key Features

- **🔗 Natural Language Interface**: Ask questions about drug-omics associations in plain English
- **📊 Data Loading & Normalization**: Load molecular profiles and treatment response data with automatic z-score normalization
- **🗂️ Multi-Project Support**: Seamlessly work with data across multiple research projects
- **💾 Smart Caching**: Efficient data caching with metadata tracking for faster access
- **📤 Data Export**: Export analysis results to various formats (CSV, Excel, JSON)
- **⚡ Multi-Modal Support**: Works with various transport protocols (STDIO, HTTP, SSE)
- **🔄 R Integration**: Seamless integration with existing DROMA R packages via rpy2

## 📦 Installation

### Prerequisites

- Python 3.10+
- R 4.0+ with DROMA.Set and DROMA.R packages
- DROMA SQLite database

### Install via pip

```bash
pip install droma-mcp
```

### Development Installation

```bash
git clone https://github.com/mugpeng/DROMA_MCP
cd DROMA_MCP
pip install -e .
```

### R Dependencies

Ensure you have the DROMA R packages installed:

```r
# Install DROMA.Set and DROMA.R packages
# devtools::install_github("mugpeng/DROMA_Set")
# devtools::install_github("mugpeng/DROMA_R")
```

## 🚀 Quick Start

### 1. Test Configuration

```bash
droma-mcp test --db-path path/to/droma.sqlite --r-libs path/to/R/libs
```

### 2. Start the Server

```bash
# STDIO mode (for AI assistants)
droma-mcp run --db-path path/to/droma.sqlite

# HTTP mode (for web applications)
droma-mcp run --transport streamable-http --port 8000
```

### 3. MCP Client Configuration

Export a configuration file for your MCP client:

```bash
droma-mcp export-config -o droma-config.json
```

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "droma-mcp": {
      "command": "droma-mcp",
      "args": ["run", "--db-path", "path/to/droma.sqlite"]
    }
  }
}
```

## 🛠️ Available Tools

### Data Loading & Management

- **`load_molecular_profiles_normalized`**: Load molecular profiles (mRNA, CNV, methylation, etc.) with z-score normalization
- **`load_treatment_response_normalized`**: Load drug response data with normalization
- **`load_multi_project_molecular_profiles_normalized`**: Load data across multiple projects
- **`load_multi_project_treatment_response_normalized`**: Load treatment response across projects
- **`check_zscore_normalization`**: Verify normalization status of cached data
- **`get_cached_data_info`**: Get information about cached datasets
- **`export_cached_data`**: Export data to CSV/Excel/JSON formats

### Database Query & Exploration

- **`get_droma_annotation`**: Retrieve sample or drug annotation data from the database
- **`list_droma_samples`**: List all available samples for a project with filtering options
- **`list_droma_features`**: List all available features (genes, drugs) for a project and data type
- **`list_droma_projects`**: List all projects available in the DROMA database

## 💬 Example Usage with AI Assistants

Here are some natural language queries you can use:

### Data Loading

> "Load mRNA expression data for ABCB1 gene from the gCSI dataset with z-score normalization"

> "Get Paclitaxel drug response data across multiple projects, including only overlapping samples"

### Database Exploration

> "List all projects available in the DROMA database"

> "Show me all available samples for the gCSI project that have mRNA data"

> "Get the first 100 genes available in the CCLE mRNA dataset"

> "Retrieve sample annotations for breast cancer cell lines in the gCSI project"

### Data Management & Analysis

> "Check if my cached molecular data has been z-score normalized and show me the statistics"

> "Show me information about all cached datasets and export the mRNA data to CSV format"

> "Load multi-project treatment response data for Doxorubicin and verify the normalization status"

## 🏗️ Architecture

The DROMA MCP server follows a streamlined modular architecture:

```
src/droma_mcp/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── cli.py               # Command-line interface
├── util.py              # Utility functions
├── schema/              # Pydantic data models
│   ├── __init__.py
│   └── data_loading.py  # All data schemas
└── server/              # MCP server modules
    ├── __init__.py      # Server setup & state
    ├── data_loading.py  # Data loading operations
    └── database_query.py # Database exploration operations
```

### Key Components

- **Modular Design**: Separate modules for data loading and database exploration
- **State Management**: Centralized data and R environment management  
- **Type Safety**: Comprehensive Pydantic validation for all inputs
- **R Integration**: Seamless R-Python data exchange via rpy2
- **Database Access**: Direct SQLite database querying for exploration
- **Caching System**: Efficient data caching with metadata tracking

## 🔧 Configuration

### Environment Variables

- `DROMA_DB_PATH`: Default path to DROMA SQLite database
- `R_LIBS`: Path to R libraries
- `DROMA_MCP_MODULE`: Server module to load (`all`, `data_loading`, `normalization`)
- `DROMA_MCP_VERBOSE`: Enable verbose logging

### Command Line Options

```bash
droma-mcp run --help
```

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
black src/
isort src/
mypy src/
```

### Adding New Tools

1. Define Pydantic schemas in `schema/`
2. Implement server functions in `server/`
3. Register tools with FastMCP decorators
4. Update CLI module loading logic

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [DROMA](https://github.com/mugpeng/DROMA) - Main DROMA project
- [DROMA.Set](https://github.com/mugpeng/DROMA_Set) - R package for data management
- [DROMA.R](https://github.com/mugpeng/DROMA_R) - R package for analysis functions
- [FastMCP](https://github.com/jlowin/fastmcp) - Python framework for MCP servers
- [Model Context Protocol](https://modelcontextprotocol.io/) - Open standard for AI tool integration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/mugpeng/DROMA_MCP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mugpeng/DROMA_MCP/discussions)
- **Email**: [Contact DROMA Team](mailto:yc47680@um.edu.mo)

## 📊 Citation

If you use DROMA MCP in your research, please cite:

```bibtex
@software{droma_mcp2024,
  title={DROMA MCP: Model Context Protocol Server for Drug-Omics Association Analysis},
  author={DROMA Development Team},
  year={2024},
  url={https://github.com/mugpeng/DROMA_MCP}
}
```

---

**DROMA MCP** - Bridging AI and Cancer Pharmacogenomics 🧬💊🤖 