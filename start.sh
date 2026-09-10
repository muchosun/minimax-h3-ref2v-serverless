#!/usr/bin/env bash
set -euo pipefail
/opt/venv/bin/python /opt/h3/verify_models.py
exec /start.sh
