# Actionable AI — Backend

FastAPI modular monolith: JWT auth today; workspaces, knowledge, tools, and chat next. Product layout: [06 Backend Architecture](../actionable-ai/docs/5_Development_and_Execution/06_Backend_Architecture.md). What to build: [task.md](../actionable-ai/docs/task.md).

## Requirements

* [Docker](https://www.docker.com/)
* [uv](https://docs.astral.sh/uv/)

## Local development

From the repo root, start PostgreSQL and Mailcatcher:

```console
$ docker compose up -d db mailcatcher
```

From `./backend/`:

```console
$ uv sync
$ uv run bash scripts/prestart.sh
$ uv run fastapi dev
```

API: `http://localhost:8000`. OpenAPI: `http://localhost:8000/docs`.

Point your editor at the workspace venv: `.venv/bin/python` at the repo root (uv workspace). Run backend commands from `./backend/` with `uv run`.

## Layout

| Path | Role |
| --- | --- |
| `app/models/` | SQLModel tables and HTTP schemas (package; Alembic imports `from app.models import SQLModel`) |
| `app/api/routes/` | Thin HTTP handlers |
| `app/services/` | Business logic (added as Workspace / Knowledge / Chat land) |
| `app/core/` | Settings, DB engine, security |
| `app/alembic/` | Migrations |
| `app/crud.py` | User helpers (template; do not grow this into a god module) |

Do not add product tables to a single `models.py`. Demo **Items** routes stay until Knowledge replaces them.

## VS Code / Cursor

Launch configs exist for the debugger and for the Python test runner.

## Full stack with Docker Compose

```console
$ docker compose run --rm backend bash scripts/prestart.sh
$ docker compose watch
```

App: `http://localhost:8000`. `compose.override.yml` is applied automatically locally (ports, watch, Mailcatcher). Shell in the container:

```console
$ docker compose exec backend bash
```

## Tests

From `backend/`. Pytest uses a dedicated database (`app_test` by default) so it does not wipe local data in `app`.

```console
$ uv run bash scripts/test.sh
```

Against a running Compose stack:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

Extra pytest flags are forwarded, for example `-x`. Coverage HTML is `htmlcov/index.html`.

## Migrations

After changing models, from `backend/`:

```console
$ uv run alembic revision --autogenerate -m "Add workspace table"
$ uv run alembic upgrade head
```

Commit the new files under `app/alembic/versions/`.

Do not uncomment `SQLModel.metadata.create_all` for anything we deploy. Staging and production run `alembic upgrade head` via `scripts/prestart.sh`.

## Email templates

Source: [React Email](https://react.email) in `./packages/react-email/`. Rendered HTML in `./backend/app/email-templates/` is generated — do not edit it by hand.

Preview from the repo root:

```console
$ bun run email:dev
```

Jinja placeholders in component props (for example `username = "{{ username }}"`) must match `generate_*_email()` in `app/utils.py`.

Export:

```console
$ bun run email:export
```
