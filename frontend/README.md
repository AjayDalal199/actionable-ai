# Actionable AI — Frontend

Marketing site and integrator dashboard. React, Vite, TypeScript, TanStack Query, TanStack Router, Tailwind CSS, shadcn/ui.

The embeddable customer widget is **not** this app. It will live in `packages/widget` ([frontend architecture Option A](../actionable-ai/docs/5_Development_and_Execution/05_Frontend_Architecture.md)).

## Requirements

- [Bun](https://bun.sh/)

## Quick start

From the repo root:

```bash
bun install
bun run dev
```

Open <http://localhost:5173/>.

The API must be running. From `backend/`, with Postgres in Compose: `uv run bash scripts/prestart.sh` then `uv run fastapi dev`. Full setup: [../development.md](../development.md).

To serve the built SPA from FastAPI, run `bun run build` in `frontend/` and open `http://localhost:8000`.

Other scripts: `frontend/package.json`.

## Generate the API client

Do not hand-edit `src/api`. After backend OpenAPI changes, from the repo root:

```bash
bash ./scripts/generate-client.sh
```

Commit the result.

Manual path: with the backend up, save `http://localhost:8000/api/v1/openapi.json` as `frontend/openapi.json`, then `bun run generate-client`.

SSE chat (when it exists) will not use this client; that helper lives under `features/chat/`, not a global `services/` folder.

## Using a remote API

Vite defaults to `VITE_API_URL` in `frontend/.env`. The production image builds with an empty URL so the browser uses the same origin as FastAPI.

```env
VITE_API_URL=https://staging.actionable.ai
```

## Code structure

Route files stay thin. Product UI lives in `features/`. See architecture §3 and §7.

* `src/api` — generated OpenAPI client
* `src/app` — QueryClient and providers
* `src/features` — auth, dashboard shell, admin, settings, marketing; later workspace, knowledge, tools, chat
* `src/shared` — shadcn primitives, composites, hooks, helpers
* `src/routes` — TanStack Router URLs
* `src/styles` — tokens

`features/items` is template leftover. Hide or delete it when Knowledge exists; do not copy it as the model for workspace-scoped screens.

## Playwright

Needs the Compose backend:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose up -d --wait backend
bunx playwright test
```

UI mode: `bunx playwright test --ui`. Tear down: `docker compose down -v`.

Tests live in `frontend/tests/`. Docs: [Playwright](https://playwright.dev/docs/intro).
