"""Command-line interface for DROMA MCP server."""

import os
import sys
import asyncio
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

# Create Typer app
app = typer.Typer(
    name="droma-mcp",
    help="DROMA MCP Server - Model Context Protocol server for drug-omics association analysis",
    add_completion=False
)


class Module(str, Enum):
    """Available server modules."""
    ALL = "all"
    DATA_LOADING = "data_loading"
    DATABASE_QUERY = "database_query"


class Transport(str, Enum):
    """Available transport protocols."""
    STDIO = "stdio"
    SHTTP = "streamable-http"
    SSE = "sse"


@app.command(name="run")
def run(
    module: Annotated[Module, typer.Option(
        "-m", "--module",
        help="Server module to load"
    )] = Module.ALL,
    transport: Annotated[Transport, typer.Option(
        "-t", "--transport",
        help="Transport protocol to use"
    )] = Transport.STDIO,
    host: Annotated[str, typer.Option(
        "--host",
        help="Host to bind to (for HTTP transports)"
    )] = "127.0.0.1",
    port: Annotated[int, typer.Option(
        "-p", "--port",
        help="Port to bind to (for HTTP transports)"
    )] = 8000,
    path: Annotated[str, typer.Option(
        "--path",
        help="Path for streamable HTTP (default: /mcp)"
    )] = "/mcp",
    db_path: Annotated[Optional[str], typer.Option(
        "--db-path",
        help="Path to DROMA SQLite database"
    )] = None,
    r_libs: Annotated[Optional[str], typer.Option(
        "--r-libs",
        help="Path to R libraries (for DROMA.Set and DROMA.R packages)"
    )] = None,
    verbose: Annotated[bool, typer.Option(
        "-v", "--verbose",
        help="Enable verbose logging"
    )] = False,
) -> None:
    """Start DROMA MCP Server with specified configuration."""
    
    # Set environment variables for module selection
    os.environ['DROMA_MCP_MODULE'] = module.value
    
    if db_path:
        os.environ['DROMA_DB_PATH'] = db_path
    
    if r_libs:
        os.environ['R_LIBS'] = r_libs
    
    if verbose:
        os.environ['DROMA_MCP_VERBOSE'] = "1"
        typer.echo(f"Starting DROMA MCP Server with:")
        typer.echo(f"  Module: {module.value}")
        typer.echo(f"  Transport: {transport.value}")
        if transport != Transport.STDIO:
            typer.echo(f"  Host: {host}")
            typer.echo(f"  Port: {port}")
        if db_path:
            typer.echo(f"  Database: {db_path}")
        if r_libs:
            typer.echo(f"  R Libraries: {r_libs}")
    
    try:
        # Import and setup server
        from .server import droma_mcp, setup_server
        
        # Run setup
        asyncio.run(setup_server())
        
        # Start server with appropriate transport
        if transport == Transport.STDIO:
            typer.echo("Starting server with STDIO transport...")
            droma_mcp.run()
            
        elif transport == Transport.SHTTP:
            from .util import get_figure, get_data_export
            from starlette.routing import Route
            
            typer.echo(f"Starting server with Streamable HTTP transport on {host}:{port}{path}")
            
            # Add HTTP routes for data export and figures
            droma_mcp._additional_http_routes = [
                Route("/figures/{figure_name}", endpoint=get_figure),
                Route("/export/{data_id}", endpoint=get_data_export)
            ]
            
            droma_mcp.run(
                transport="streamable-http",
                host=host,
                port=port,
                path=path
            )
            
        elif transport == Transport.SSE:
            typer.echo(f"Starting server with SSE transport on {host}:{port}")
            droma_mcp.run(
                transport="sse",
                host=host,
                port=port
            )
            
    except ImportError as e:
        typer.echo(f"Error importing server modules: {e}", err=True)
        typer.echo("Make sure all dependencies are installed:", err=True)
        typer.echo("  pip install -e .", err=True)
        raise typer.Exit(1)
        
    except Exception as e:
        typer.echo(f"Error starting server: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="test")
def test_connection(
    db_path: Annotated[Optional[str], typer.Option(
        "--db-path",
        help="Path to DROMA SQLite database"
    )] = None,
    r_libs: Annotated[Optional[str], typer.Option(
        "--r-libs",
        help="Path to R libraries"
    )] = None,
) -> None:
    """Test DROMA MCP server configuration and dependencies."""
    
    typer.echo("Testing DROMA MCP Server configuration...")
    
    # Test Python dependencies
    typer.echo("\n1. Testing Python dependencies...")
    try:
        import pandas as pd
        import numpy as np
        import fastmcp
        typer.echo("  ✓ Core Python packages available")
    except ImportError as e:
        typer.echo(f"  ✗ Missing Python dependency: {e}")
        return
    
    # Test R integration
    typer.echo("\n2. Testing R integration...")
    if r_libs:
        os.environ['R_LIBS'] = r_libs
    
    try:
        import rpy2.robjects as robjects
        from rpy2.robjects import pandas2ri
        
        # Test R connection
        r = robjects.r
        r_version = r('R.version.string')[0]
        typer.echo(f"  ✓ R available: {r_version}")
        
        # Test pandas2ri conversion
        pandas2ri.activate()
        typer.echo("  ✓ pandas2ri conversion available")
        
        # Test DROMA packages
        try:
            r('library(DROMA.Set)')
            typer.echo("  ✓ DROMA.Set package loaded")
        except Exception as e:
            typer.echo(f"  ✗ DROMA.Set package not available: {e}")
            
        try:
            r('library(DROMA.R)')
            typer.echo("  ✓ DROMA.R package loaded")
        except Exception as e:
            typer.echo(f"  ✗ DROMA.R package not available: {e}")
            
    except ImportError as e:
        typer.echo(f"  ✗ R integration not available: {e}")
        typer.echo("    Install rpy2: pip install rpy2")
    
    # Test database connection
    if db_path:
        typer.echo(f"\n3. Testing database connection: {db_path}")
        if Path(db_path).exists():
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check for required tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['sample_anno', 'drug_anno']
                for table in required_tables:
                    if table in tables:
                        typer.echo(f"  ✓ Table '{table}' found")
                    else:
                        typer.echo(f"  ! Table '{table}' not found")
                
                conn.close()
                typer.echo("  ✓ Database connection successful")
                
            except Exception as e:
                typer.echo(f"  ✗ Database connection failed: {e}")
        else:
            typer.echo(f"  ✗ Database file not found: {db_path}")
    else:
        typer.echo("\n3. No database path provided (use --db-path to test)")
    
    # Test server import
    typer.echo("\n4. Testing server import...")
    try:
        from .server import droma_mcp
        typer.echo("  ✓ DROMA MCP server can be imported")
    except ImportError as e:
        typer.echo(f"  ✗ Server import failed: {e}")
    
    typer.echo("\nConfiguration test completed!")


@app.command(name="info")
def info() -> None:
    """Display information about DROMA MCP server."""
    
    from . import __version__, __author__
    
    typer.echo(f"""
DROMA MCP Server v{__version__}
{__author__}

A Model Context Protocol server for drug-omics association analysis using DROMA.

Available modules:
  • data_loading    - Data loading, caching, and normalization operations
  • all            - All modules (default)

Available transports:
  • stdio          - Standard input/output (default, for AI assistants)
  • streamable-http - HTTP with streaming support
  • sse            - Server-Sent Events

Usage:
  droma-mcp run                           # Start with default settings
  droma-mcp run -m data_loading           # Start with only data loading module
  droma-mcp run -t streamable-http -p 8080 # Start HTTP server on port 8080
  droma-mcp test --db-path path/to/db.sqlite # Test configuration

Environment variables:
  DROMA_DB_PATH         - Default database path
  R_LIBS                - R library path
  DROMA_MCP_VERBOSE     - Enable verbose logging

Documentation: https://github.com/mugpeng/DROMA
""")


@app.command(name="export-config")
def export_config(
    output: Annotated[str, typer.Option(
        "-o", "--output",
        help="Output file path"
    )] = "droma-mcp-config.json",
    transport: Annotated[Transport, typer.Option(
        "-t", "--transport",
        help="Transport protocol"
    )] = Transport.STDIO,
    host: Annotated[str, typer.Option(
        "--host",
        help="Host for HTTP transports"
    )] = "127.0.0.1",
    port: Annotated[int, typer.Option(
        "-p", "--port",
        help="Port for HTTP transports"
    )] = 8000,
) -> None:
    """Export MCP client configuration file."""
    
    import json
    
    if transport == Transport.STDIO:
        config = {
            "mcpServers": {
                "droma-mcp": {
                    "command": "droma-mcp",
                    "args": ["run", "--module", "all", "--transport", "stdio"]
                }
            }
        }
    elif transport == Transport.SHTTP:
        config = {
            "mcpServers": {
                "droma-mcp": {
                    "transport": {
                        "type": "http",
                        "url": f"http://{host}:{port}/mcp"
                    }
                }
            }
        }
    elif transport == Transport.SSE:
        config = {
            "mcpServers": {
                "droma-mcp": {
                    "transport": {
                        "type": "sse",
                        "url": f"http://{host}:{port}/sse"
                    }
                }
            }
        }
    
    with open(output, 'w') as f:
        json.dump(config, f, indent=2)
    
    typer.echo(f"MCP client configuration exported to: {output}")


if __name__ == "__main__":
    app() 