#!/bin/sh
# Start both the Vibe-Trading API server (port 8899) and the MCP SSE server (port 8900).
# The MCP server is exposed to the epsilon api container via Docker Swarm overlay network.
# If the MCP server fails, the API server still serves the web UI — fail-soft.

set -e

# Start MCP server in background (SSE transport on port 8900)
echo "[entrypoint] starting MCP server on port 8900 (SSE)..."
python3 /app/agent/mcp_server.py --transport sse --port 8900 &
MCP_PID=$!

# Graceful shutdown — propagate SIGTERM to MCP child
trap "kill -TERM $MCP_PID 2>/dev/null || true; exit 0" TERM INT

# Start API server in foreground (port 8899)
echo "[entrypoint] starting Vibe-Trading API server on port 8899..."
exec vibe-trading serve --host 0.0.0.0 --port 8899
