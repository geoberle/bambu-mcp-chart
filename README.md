# Bambu MCP

Helm chart for deploying [synman/bambu-mcp](https://github.com/synman/bambu-mcp) on
Kubernetes.

Exposes a Bambu Lab 3D printer MCP server over SSE that AI agents (e.g. Hermes) can use
to monitor and control a printer: state/telemetry, print control, climate, AMS/filament,
camera snapshots, file management, and raw MQTT commands (101 tools total).

The pod uses normal cluster networking (`ClusterIP` Service, no `hostNetwork`) — reach it
from another workload at `http://bambu-mcp-chart.<namespace>.svc.cluster.local:3003/sse`.

## How printer credentials work

Upstream `bambu-mcp` stores printer credentials in an encrypted on-disk vault
(`~/.bambu-mcp/secrets.enc`), normally populated by calling its `add_printer(...)` MCP
tool interactively. This chart has no `PersistentVolume` and does not use that flow —
instead the container entrypoint re-seeds the vault from the `PRINTER_*` env vars
(sourced from the `bambu-mcp-credentials` Secret) on every start via
`auth.save_printer_credentials()`, before the server boots. This is idempotent and
requires no manual setup step, but it means only **one printer** is configurable through
this chart, and the vault itself does not survive a pod restart — only the re-seed does.

## Write protection

All state-changing tools upstream require an explicit `user_permission=True` argument
from the calling agent — this chart does not change or bypass that.

## Install

```bash
helm install bambu-mcp oci://ghcr.io/geoberle/bambu-mcp-chart \
  -n bambu-mcp --create-namespace \
  -f values.local.yaml
```

## Configuration

Create a `values.local.yaml` with your printer's LAN details (LAN Only Mode + Developer
Mode must be enabled on the printer; get the access code from the touchscreen under
Settings → Network):

```yaml
printer:
  name: "myprinter"
  ip: "192.168.1.50"
  serial: "01P00A000000000"
  accessCode: "12345678"
```

All available values:

| Key | Default | Description |
|---|---|---|
| `image.repository` | `ghcr.io/geoberle/bambu-mcp` | bambu-mcp installed at build time from the upstream repo |
| `image.tag` | `latest` | Image tag |
| `service.port` | `3003` | SSE server port |
| `printer.name` | `""` | Printer name registered with the MCP server |
| `printer.ip` | `""` | Printer LAN IP address |
| `printer.serial` | `""` | Printer serial number |
| `printer.accessCode` | `""` | LAN Only Mode access code (touchscreen → Settings → Network) |
| `resources.requests.cpu` | `100m` | CPU request |
| `resources.requests.memory` | `128Mi` | Memory request |
| `resources.limits.memory` | `256Mi` | Memory limit |
