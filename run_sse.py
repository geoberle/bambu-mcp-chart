"""
Container launcher for bambu-mcp's SSE transport.

server.py's own `sse` branch hardcodes FastMCP's host/port to 127.0.0.1:8000 —
FastMCP.__init__ always passes explicit host/port to its Settings object, so the
documented FASTMCP_HOST/FASTMCP_PORT env vars never take effect for that branch.
Only the streamable-http branch works around this by mutating `mcp.settings`
directly before calling `mcp.run()`. This does the same for `sse`, reading the
bind address from HOST/PORT instead.
"""

import os
import threading

import server

server.mcp.settings.host = os.environ.get("HOST", "0.0.0.0")
server.mcp.settings.port = int(os.environ.get("PORT", "3003"))

# Run startup (MQTT session connect) in the background so the SSE listener is
# up immediately instead of blocking on a printer handshake — same rationale
# server.py already applies to its stdio and streamable-http branches.
threading.Thread(target=server._startup, daemon=True, name="bambu-mcp-startup").start()
server.mcp.run(transport="sse")
