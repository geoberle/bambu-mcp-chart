"""
Container launcher for bambu-mcp's SSE transport.

server.py's own `sse` branch hardcodes FastMCP's host/port to 127.0.0.1:8000 —
FastMCP.__init__ always passes explicit host/port to its Settings object, so the
documented FASTMCP_HOST/FASTMCP_PORT env vars never take effect for that branch.
Only the streamable-http branch works around this by mutating `mcp.settings`
directly before calling `mcp.run()`. This does the same for `sse`, reading the
bind address from HOST/PORT instead.

FastMCP.__init__ also auto-enables DNS-rebinding Host-header protection
whenever host defaults to 127.0.0.1 (which it always does here, since
server.py never passes host= explicitly), locking allowed_hosts to
127.0.0.1/localhost. That rejects every request that arrives via the
in-cluster Service DNS name with 421 Misdirected Request. This is a
ClusterIP-only internal service with no public exposure, so disable it —
the same tradeoff unifi-network-mcp's chart already makes explicitly via
UNIFI_MCP_ENABLE_DNS_REBINDING_PROTECTION=false.
"""

import os
import threading

import server
from mcp.server.transport_security import TransportSecuritySettings

import patch_urls
patch_urls.apply()

server.mcp.settings.host = os.environ.get("HOST", "0.0.0.0")
server.mcp.settings.port = int(os.environ.get("PORT", "3003"))
server.mcp.settings.transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

# Run startup (MQTT session connect) in the background so the SSE listener is
# up immediately instead of blocking on a printer handshake — same rationale
# server.py already applies to its stdio and streamable-http branches.
threading.Thread(target=server._startup, daemon=True, name="bambu-mcp-startup").start()
server.mcp.run(transport="sse")
