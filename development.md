# Actionable AI — Development

## Local development

Run PostgreSQL and Mailcatcher with Docker Compose, and run the FastAPI and Vite servers on your machine.

Copy env defaults if you do not already have a local file (`.env` is gitignored):

```bash
cp .env.example .env
```

Start supporting services:

```bash
docker compose up -d db mailcatcher
```

From `backend/`, install dependencies and prepare the database:

```bash
uv sync
uv run bash scripts/prestart.sh
```

Start the FastAPI development server:

```bash
uv run fastapi dev
```

In another terminal, from the repo root:

```bash
bun install
bun run dev
```

| URL | What |
| --- | --- |
| <http://localhost:5173> | Vite: marketing site and dashboard |
| <http://localhost:8000> | FastAPI |
| <http://localhost:8000/docs> | OpenAPI (Swagger UI) |
| <http://localhost:1080> | Mailcatcher |

Vite talks to the API at `http://localhost:8000`, from `frontend/.env` (`VITE_API_URL`).

First superuser credentials are `FIRST_SUPERUSER` and `FIRST_SUPERUSER_PASSWORD` in `.env`. Local `.env` may use `changethis` because `FASTAPI_ENV=development`. Staging and production must not.

### Frontend served by FastAPI

From `frontend/`:

```bash
bun run build
```

The build is written to `backend/app/frontend` and served at <http://localhost:8000>. Rebuild after frontend changes.

## Full stack with Docker Compose

To run the backend and the built frontend in Compose (no local Vite):

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose watch
```

| URL | What |
| --- | --- |
| <http://localhost:8000> | App (SPA + API) |
| <http://localhost:8000/docs> | OpenAPI |
| <http://localhost:8080> | Adminer |
| <http://localhost:8090> | Traefik dashboard (local only) |
| <http://localhost:1080> | Mailcatcher |

Stop a locally running `fastapi dev` first; both use port `8000`.

The first start can take a minute. Watch with `docker compose logs` or `docker compose logs backend`.

## Mailcatcher

Mailcatcher captures mail in local development instead of sending it. The local backend uses `localhost:1025`; the Compose backend uses the `mailcatcher` service. UI: <http://localhost:1080>.

## Docker Compose files and environment variables

| File | When it loads |
| --- | --- |
| `compose.yml` | Always (shared stack) |
| `compose.override.yml` | Automatically locally (ports, Mailcatcher, watch, `FASTAPI_ENV=development`) |
| `compose.deploy.yml` | Only when you pass `-f compose.yml -f compose.deploy.yml` on a server (HTTPS, Let's Encrypt) |

Never apply `compose.override.yml` on staging or production.

The app reads local settings from `.env`. Compose interpolates the same file and passes each container what it needs. After changing variables, restart:

```bash
docker compose watch
```

Do not put staging or production secrets in `.env`. See [deployment strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md) and the [Compose operator guide](./deployment-docker-compose.md).

## Tests

Backend (from `backend/`, with Postgres up):

```bash
uv run bash scripts/test.sh
```

Playwright needs the Compose backend. See [frontend/README.md](./frontend/README.md).

## Pre-commit hooks and linting

The project uses [prek](https://prek.j178.dev/) (via `.pre-commit-config.yaml`) for linting and formatting.

From the repo root, install the Git hook:

```bash
uv run prek install -f
```

Run on all files:

```bash
uv run prek run --all-files
```

## Where to read next

- [MVP task list](./actionable-ai/docs/task.md) — what to build
- [Frontend architecture](./actionable-ai/docs/5_Development_and_Execution/05_Frontend_Architecture.md)
- [Backend architecture](./actionable-ai/docs/5_Development_and_Execution/06_Backend_Architecture.md)
- [backend/README.md](./backend/README.md) — models, Alembic, emails
- [frontend/README.md](./frontend/README.md) — OpenAPI client, Playwright
