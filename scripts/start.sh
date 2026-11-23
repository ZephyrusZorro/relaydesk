#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
node scripts/configure.mjs
node scripts/build-workflows.mjs
docker compose stop n8n
docker compose build desk
docker compose run --rm --no-deps --entrypoint node n8n /opt/relaydesk/scripts/n8n-init.mjs
docker compose up -d --wait desk n8n
node scripts/print-urls.mjs
