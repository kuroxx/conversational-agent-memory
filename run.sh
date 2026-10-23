#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}src"
exec python -m conversation_agent.main
