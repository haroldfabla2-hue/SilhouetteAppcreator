#!/bin/sh
# STDIO mode startup script for IRIS MCP Superior Server
set -e

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..." >&2
    python3 -m venv .venv
    echo "Installing dependencies..." >&2
    echo "Note: Dependency installation may take several minutes. Please wait..." >&2
    pip install fastmcp click requests pydantic python-dotenv uvicorn fastapi
fi

# Activate virtual environment
source .venv/bin/activate

# Start STDIO mode MCP server (demo version for testing)
python run_mcp_server_demo.py