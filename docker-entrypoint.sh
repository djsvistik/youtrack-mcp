#!/bin/sh
# Docker entrypoint script for YouTrack MCP Server
# Supports both stdio and http transport modes via MCP_TRANSPORT environment variable

set -e

# Default values
TRANSPORT=${MCP_TRANSPORT:-stdio}
HOST=${MCP_HOST:-0.0.0.0}

echo "Starting YouTrack MCP Server..."
echo "Transport mode: $TRANSPORT"

# Build the command based on transport mode
if [ "$TRANSPORT" = "http" ]; then
    echo "Starting HTTP server on $HOST:8000"
    exec python main.py --transport http --host "$HOST" "$@"
else
    echo "Starting stdio transport (for Claude Desktop)"
    exec python main.py --transport stdio "$@"
fi