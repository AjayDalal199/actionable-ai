# Actionable AI (A²I)

An in-product agent that answers from your knowledge **and** takes action — with a confirmation gate on writes.

A developer can sign up, upload docs, register a tool, paste one script tag, and have a live agent on their site. Time-to-value under 5 minutes.

## What this repository is

| Path | Role |
| --- | --- |
| [`frontend/`](./frontend/) | Public marketing site (`/`) and integrator dashboard (`/dashboard`). React, Vite, TanStack Router, shadcn/ui. |
| [`backend/`](./backend/) | One FastAPI app: API under `/api/v1`, built SPA served from the same origin. Modular monolith. |
| [`packages/`](./packages/) | React Email templates today. Embeddable widget later (`packages/widget`). |
| [`actionable-ai/docs/`](./actionable-ai/docs/) | Product, architecture, and the MVP task list. |
| [`compose.yml`](./compose.yml) | Local and remote stack: Traefik, PostgreSQL, backend. |

**Status:** Auth and the marketing site work. Architecture is locked. Workspaces, knowledge (RAG), tools, chat, and the widget are not built yet. Track progress in [task.md](./actionable-ai/docs/task.md).

This repo started from the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template). The template leftovers (demo Items CRUD, FastAPI Cloud as a primary host) are being replaced, not shipped as product.

## Stack

- **API:** FastAPI, SQLModel, Alembic, PostgreSQL, JWT auth
- **Dashboard:** Vite, React, TypeScript, TanStack Query / Router, Tailwind, shadcn/ui
- **Emails:** React Email → Jinja HTML
- **Local / deploy:** Docker Compose, Traefik (HTTPS in deploy), Playwright, Pytest
- **Coming for MVP:** pgvector, Redis, LangGraph, embeddable Shadow DOM widget

Architecture (locked): frontend [Option A](./actionable-ai/docs/5_Development_and_Execution/05_Frontend_Architecture.md) — keep `frontend/` as-is; widget in `packages/widget`. Backend [Option B](./actionable-ai/docs/5_Development_and_Execution/06_Backend_Architecture.md) — models package, services, thin routes. One deployable, not microservices.

## Documentation

| Doc | What it is |
| --- | --- |
| [MVP task list](./actionable-ai/docs/task.md) | What to build, in order |
| [PRD](./actionable-ai/docs/3_Product_Definition_and_Scoping/PRD.md) | Product requirements |
| [System architecture](./actionable-ai/docs/5_Development_and_Execution/01_System_Architecture.md) | High-level shape |
| [Deployment strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md) | Staging vs production policy |
| [Development](./development.md) | Run the stack locally |
| [Deploy with Docker Compose](./deployment-docker-compose.md) | Operator steps for a VPS |
| [Contributing](./CONTRIBUTING.md) | How we take changes |

## Local development

Requirements: [Docker](https://www.docker.com/), [uv](https://docs.astral.sh/uv/), [Bun](https://bun.sh/).

```bash
cp .env.example .env   # if you do not already have a local .env
docker compose up -d db mailcatcher
cd backend && uv sync && uv run bash scripts/prestart.sh && uv run fastapi dev
```

In another terminal, from the repo root:

```bash
bun install
bun run dev
```

| URL | What |
| --- | --- |
| <http://localhost:5173> | Vite dashboard / marketing site |
| <http://localhost:8000> | API (and the built SPA after `bun run build` in `frontend/`) |
| <http://localhost:8000/docs> | OpenAPI |
| <http://localhost:1080> | Mailcatcher |

Default superuser comes from `.env` (`FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`). Do not use `changethis` outside local development.

Full workflow, Compose watch mode, linting, and tests: [development.md](./development.md).

## Deployment

**Staging and production** are Docker Compose + Traefik on separate VPS instances. Staging deploys from the default branch; production requires approval. Policy: [07 Deployment Strategy](./actionable-ai/docs/5_Development_and_Execution/07_Deployment_Strategy.md). Commands: [deployment-docker-compose.md](./deployment-docker-compose.md).

FastAPI Cloud is **not** the primary host (we need Postgres with pgvector, Redis, file volumes, and a worker). Do not treat a push to `master` as a Cloud deploy.

## License

MIT. See [LICENSE](./LICENSE). Template portions retain the original FastAPI Template copyright.
