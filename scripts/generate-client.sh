#! /usr/bin/env bash

set -e
set -x

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

cd "$ROOT/backend"
FASTAPI_ENV=development uv run python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../openapi.json
cd "$ROOT"
mv openapi.json frontend/
bun run --filter frontend generate-client
bun run lint
