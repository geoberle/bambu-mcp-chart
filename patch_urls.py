"""
Rewrite bambu-mcp's hardcoded "http://localhost:{port}" URLs to a reachable host.

Both of bambu-mcp's local HTTP servers already bind 0.0.0.0 (api_server.py's Flask
app, camera/mjpeg_server.py's MJPEG streams) — they ARE reachable from other pods.
The only bug is that every URL they hand back to the MCP caller hardcodes the
literal string "localhost", which resolves to the CALLER's own loopback, not this
container's. That's fatal in Kubernetes: get_snapshot/get_stream_url/start_stream
return a URL the calling agent (e.g. Hermes, in a different pod) can never reach.

Wraps the original functions/methods and does a plain string substitution on
their return value, instead of patching source text — this is independent of
each function's internal implementation, so it survives upstream changes to
those bodies as long as the "http://localhost:" prefix convention holds.

BAMBU_PUBLIC_HOST should be set to this Service's in-cluster DNS name. Combine
with BAMBU_API_PORT (fixes api_server's port) and BAMBU_PORT_POOL_START/_END
(fixes the MJPEG stream port range) so the resulting URLs land on ports the
Service actually exposes — see chart/templates/deployment.yaml and service.yaml.
"""

from __future__ import annotations

import functools
import os

PUBLIC_HOST = os.environ.get("BAMBU_PUBLIC_HOST", "localhost")


def _rehost(url):
    if isinstance(url, str) and PUBLIC_HOST != "localhost":
        return url.replace("http://localhost:", f"http://{PUBLIC_HOST}:")
    return url


def _wrap(fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        return _rehost(fn(*args, **kwargs))
    return wrapped


def apply() -> None:
    if PUBLIC_HOST == "localhost":
        return  # no override configured — leave upstream behavior untouched

    import api_server
    api_server.get_url = _wrap(api_server.get_url)

    import tools.url_factory as url_factory
    url_factory._api_base = _wrap(url_factory._api_base)

    from camera.mjpeg_server import MJPEGServer
    MJPEGServer.start = _wrap(MJPEGServer.start)
    MJPEGServer.get_url = _wrap(MJPEGServer.get_url)

    _orig_get_active_streams = MJPEGServer.get_active_streams

    def get_active_streams(self):
        return {
            name: {**info, "url": _rehost(info["url"])}
            for name, info in _orig_get_active_streams(self).items()
        }

    MJPEGServer.get_active_streams = get_active_streams
