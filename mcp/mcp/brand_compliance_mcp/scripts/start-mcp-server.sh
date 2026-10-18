#!/usr/bin/env bash
# Start the brand compliance MCP server (HTTP + SSE on 127.0.0.1:8010) for Claude Code.
# The bearer token lives in .env (gitignored) so the server and Claude Code share the same one.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  umask 077
  echo "BRAND_MCP_AUTH_TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env
  echo "Created .env with a new token. Re-register Claude Code if it used an older token."
fi
set -a
# shellcheck disable=SC1091
source .env
set +a
exec env PYTHONPATH=src myenv/bin/python -m brand_compliance.server
