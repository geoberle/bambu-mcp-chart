#!/bin/sh
set -e

# Seed the encrypted printer vault from env-provided credentials on every boot.
# The vault itself is not persisted across restarts (no PVC) — this makes each
# start idempotent instead of requiring a one-time add_printer() tool call.
if [ -n "$PRINTER_NAME" ]; then
  python3 -c "
import os
import auth

auth.save_printer_credentials(
    os.environ['PRINTER_NAME'],
    os.environ['PRINTER_IP'],
    os.environ['PRINTER_ACCESS_CODE'],
    os.environ['PRINTER_SERIAL'],
)
"
fi

exec python3 run_sse.py
