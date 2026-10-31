# 07 Deployment Strategy — Staging and Production

## Document Metadata

- **Product:** Actionable AI (A²I) Platform
- **Status:** Decided — Compose + Traefik, two environments (2026-08-25)
- **Last Updated:** 2026-08-25
- **Companion:** [06 Backend Architecture](./06_Backend_Architecture.md), [05 Frontend Architecture](./05_Frontend_Architecture.md), [01 System Architecture](./01_System_Architecture.md), [task.md](../task.md)
- **Operator how-to (not this doc):** [deployment-docker-compose.md](../../../deployment-docker-compose.md)

**Decision:** Staging and production are two isolated Docker Compose stacks behind Traefik with Let's Encrypt. Staging deploys automatically from the default branch. Production deploys only after a human approval. FastAPI Cloud is not the primary path. Kubernetes is not in scope for MVP or V1.

---

## 1. Why this exists

The MVP is **not** done when tickets close. It is done when [Phase 10.3](../task.md) passes on a **shared staging environment** that a beta client can actually hit. Production is the same stack, with stricter access, separate secrets, and backups, used only after staging has proven the release.

This document is the **policy**. It says which environments we run, how code gets there, what is allowed to differ, and what we add as Redis / pgvector / workers land. It does not replace the Compose operator guide.

---

## 2. What we are deploying

One **modular monolith** (backend Option B): a single FastAPI process that serves:

| Surface | How it is served |
| --- | --- |
| Marketing + dashboard SPA | Built in the backend image, mounted at `/` |
| REST + SSE API | Same origin under `/api/v1` |
| Embeddable widget (`packages/widget`, Phase 6) | Same origin first (`/widget.js`). CDN is V1 |

That is **one container image**, one public hostname per environment. Do not split dashboard, API, and widget into three hosts for MVP.

**Runtime today**

- Traefik (HTTP → HTTPS, Let's Encrypt)
- PostgreSQL 18 with pgvector (`pgvector/pgvector:pg18`)
- Redis 8 (ephemeral, Compose network only)
- FastAPI (`fastapi run --workers 4`)
- Adminer (local / staging only)

**Runtime we will add (same Compose project, not new products)**

| When | Add |
| --- | --- |
| Phase 3 | Docker named volume for uploads on the VM boot disk (~80 GB). No object storage |
| Reliable ingestion (after first Knowledge spike) | Worker process (ARQ / TaskIQ) sharing the backend image |
| Phase 6 | Widget static file in the backend image (or Traefik file server) |

This matches [06 Backend Architecture](./06_Backend_Architecture.md) §7.5 and §8 (B5, B8). Do not invent a second deployable to host Redis or the worker.

---

## 3. Environments

Three environments. Local is not staging.

| Environment | Purpose | Data | Who uses it |
| --- | --- | --- | --- |
| **Local** | Develop. `compose.yml` + `compose.override.yml` | Disposable | Engineers |
| **Staging** | Shared QA, MVP acceptance, beta widget on a client *staging* site | Fake / client-provided test data. Wiping is allowed with notice | Us + invited beta clients |
| **Production** | Live integrators and their end-users | Real. Backed up. Never wiped for convenience | Paying / live clients |

### 3.1 Proposed hostnames

Replace with the real DNS once domains are purchased. Keep the shape.

| Role | Staging | Production |
| --- | --- | --- |
| App (SPA + API + widget script) | `https://staging.dactionlabs.com` | `https://app.dactionlabs.com` |
| Adminer | `https://adminer.staging.dactionlabs.com` (VPN or IP allowlist) | **Not exposed** |
| Traefik dashboard | Off | Off |

`FRONTEND_HOST` in each environment is that environment’s app URL. CORS and password-reset links depend on it.

### 3.2 Isolation (locked)

**Two VPS, two Compose projects, two GitHub Environments.** Staging and production do not share a Docker daemon, a Postgres volume, a Traefik certificate store, or a `SECRET_KEY`.

**Oracle Cloud Always Free (current):** two Ampere VMs, **1 OCPU / 6 GB** each (Always Free Ampere is 2 OCPU / 12 GB total). Operator guide: [deployment-oracle-cloud.md](../../../deployment-oracle-cloud.md). 6 GB needs swap and `WEB_CONCURRENCY=1`.

| Why two VMs | Why not Kubernetes |
| --- | --- |
| Staging will churn (pgvector image, Redis, workers). A bad Compose change must not be able to stop production. | One FastAPI app and a handful of sidecars. K8s adds a cluster to operate before we have paying load. |

### 3.3 What may differ between staging and prod

Allowed:

- Domain, SMTP from-address, Sentry environment tag, log verbosity
- Superuser email/password
- LLM budget caps (staging can be tighter)
- Adminer on staging only
- OpenAPI `/docs` on staging; **off or auth-gated in production**

Not allowed:

- Different app architecture (one env on FastAPI Cloud, the other on Compose)
- Staging tokens or `SECRET_KEY` reused in production
- Production database restored onto staging without sanitizing PII
- Feature flags that make HITL, tenant isolation, or rate limits weaker in production than in staging

Staging must be a **faithful copy of the prod topology** (same services in Compose), even if it is smaller (1 vCPU vs 4). “It worked on my laptop” is not a staging check.

---

## 4. Hosting choice

### Option A — Docker Compose + Traefik on VPS — **chosen**

What we already have: `compose.yml` + `compose.deploy.yml`, backend Dockerfile that builds the frontend, GitHub workflow `.github/workflows/deploy-docker-compose.yml`.

**Fits:** Modular monolith, Postgres + (soon) Redis + worker + disk volumes, small team, predictable cost.

**Cost:** We operate the boxes (updates, backups, disk). Acceptable through V1.

### Option B — FastAPI Cloud + hosted Postgres

Already sketched in `deployment.md` and `.github/workflows/deploy.yml`.

**Fails for this product:** no first-class Redis, worker, pgvector extension we control, or upload volume. Widget + SSE + HITL will need those. Using Cloud for “API only” and Compose for the rest is two platforms for one app.

**Verdict:** Do not use as the primary path. Leave the workflow unused (or delete later). Do not push `master` to FastAPI Cloud.

### Option C — PaaS (Fly, Render, Railway) or managed K8s

**Fits:** If we later want managed TLS and scale-to-zero.

**Cost now:** Re-platform before the agent exists. Defer until Compose is the bottleneck.

---

## 5. Promotion model (how code reaches an environment)

```text
feature branch
    → PR into develop
        → CI: backend pytest, Playwright, Compose smoke
            → merge to develop
                → automatic deploy to STAGING (staging.dactionlabs.com)
                    → soak + smoke
                        → Actions → Prepare Release
                            → labeled release PR into master
                                → merge → deploy PRODUCTION (app.dactionlabs.com)
```

Rules:

1. **Nothing reaches production that has not run on staging** at that SHA (hotfix exception: §8).
2. **Production is not an automatic push of every commit to `master`.** It is a **release PR** (label `release`) that freezes `release-notes.md` and bumps the package version. The human gate is reviewing that PR.
3. **Staging deploys on every merge to `develop`** so it does not rot. A red staging deploy blocks a release, not feature work on a branch.
4. **Migrations run as part of deploy** (`scripts/prestart.sh`: wait for DB → `alembic upgrade head` → seed superuser). Forward-only. No auto-downgrade. A migration that cannot run in seconds on a copy of prod data does not ship.

### 5.1 CI vs CD

| Gate | When | Blocks |
| --- | --- | --- |
| Pytest + coverage | PR and `develop` / `master` | Merge |
| Playwright | PR and `develop` / `master` (when frontend/backend/compose change) | Merge |
| Compose smoke (`test-docker-compose.yml`) | PR and `develop` / `master` | Merge |
| Staging deploy | After merge to `develop` | Release (do not cut a release whose staging deploy failed) |
| Production deploy | Merge of a `release` PR into `master` | Live traffic |

CD does not replace CI. A deploy workflow must not skip tests “to go faster.”

### 5.2 GitHub Actions shape (target)

| Workflow | Trigger | Runner | GitHub Environment |
| --- | --- | --- | --- |
| Deploy staging | Push to `develop` + `workflow_dispatch` | GitHub-hosted `ubuntu-latest`, SSH to the **staging** VM | `staging` |
| Deploy production | Merged PR labeled `release` into `master` + `workflow_dispatch` | GitHub-hosted `ubuntu-latest`, SSH to the **prod** VM | `production` |

`concurrency` per environment so two deploys cannot interleave `compose up` on the same VM. Do not `cancel-in-progress` (let the in-flight deploy finish).

The repo is public: **no self-hosted runner on either VM**. Self-hosted runners are for private repos only.

---

## 6. Configuration and secrets

### 6.1 Per-environment GitHub Environment variables

| Name | Secret? | Notes |
| --- | --- | --- |
| `DOMAIN` | no | Hostname only, e.g. `staging.dactionlabs.com` |
| `PROJECT_NAME` | no | `Actionable AI` |
| `FIRST_SUPERUSER` | no | Ops inbox, not a personal Gmail if we can avoid it |
| `SMTP_HOST` / `SMTP_USER` / `EMAILS_FROM_EMAIL` | no | Real provider in both envs (not Mailcatcher) |
| `SENTRY_DSN` | no | Same project, different `environment` tag |
| `POSTGRES_PASSWORD` | **yes** | Unique per env |
| `SECRET_KEY` | **yes** | Unique per env. Rotating it logs everyone out |
| `FIRST_SUPERUSER_PASSWORD` | **yes** | Unique per env |
| `SMTP_PASSWORD` | **yes** | If the provider requires it |
| `GEMINI_API_KEY` | **yes** | Embeddings and chat. Staging can use a separate key with a spend cap |
| `CHAT_MODEL` | no | Default `gemini-3.5-flash-lite` when unset |

Add when those phases land (still unique per env):

| Name | Phase | Notes |
| --- | --- | --- |
| `REDIS_URL` | 2 | Internal Compose DNS, e.g. `redis://redis:6379/0` — not public |

Workspace widget JWT secrets live **in the database per workspace**, not in env (backend B4). Env only holds *our* signing key for dashboard users.

### 6.2 App environment flag

Today `FASTAPI_ENV=development` is the only special case: it allows `changethis` secrets and disables Sentry.

- Local: `FASTAPI_ENV=development`
- Staging and production: **unset**. Default secrets must fail boot. Sentry must be on.

Do not invent a second `ENVIRONMENT=staging` until something actually branches on it (Sentry tag, `/docs` off). When we do, it is `staging` | `production` | unset-for-local — not a fourth “preview” env.

### 6.3 Image and frontend origin

The backend image builds the SPA with `VITE_API_URL` empty so the browser talks to the **same origin**. That is correct for staging and prod. Do not bake `https://localhost:8000` into a deployed image.

---

## 7. Compose topology (target)

Same files for both remote envs: `compose.yml` + `compose.deploy.yml`. Each VM’s Traefik binds 80/443. Never apply `compose.override.yml` on a server (dev ports, Mailcatcher, insecure Traefik API, bind-mounted source).

```text
Internet
  → Traefik :80/:443  (HTTP redirect, TLS)
      → backend :8000   (SPA + API + later /widget.js)
      → adminer         (staging labels only)

backend → Postgres (volume app-db-data)
backend → Redis     (ephemeral, no volume)
worker  → Postgres + Redis   (when ingestion leaves BackgroundTasks)
backend → upload volume on the boot disk (Phase 2.3)
```

**Project name** must include the environment (`COMPOSE_PROJECT_NAME=a2i-staging` / `a2i-prod`).

**Adminer in production:** omit the service or do not set `traefik.enable=true`. Inspect Postgres with an SSH tunnel (`kubectl` is not a substitute we have).

**Health:** `/api/v1/utils/health-check/` pings Redis and returns 503 when Redis is down. Traefik should not route to an unhealthy backend.

**Restarts:** `restart: always` on remote services (already in `compose.deploy.yml`). Unattended-upgrades / Docker restart on reboot.

---

## 8. Releases, rollback, hotfixes

**Normal release:** git SHA that is green on CI, deployed to staging (`develop`), smoked, then a **Prepare Release** PR into `master`.

**Rollback:** redeploy the previous known-good image/SHA. If a migration already ran, rollback requires a **forward** fix or a written downgrade revision — do not `alembic downgrade` on production as the default move.

**Hotfix:** branch from the production SHA, PR with CI into `develop` (staging), then Prepare Release into `master`, then keep `develop` in sync. Do not SSH in and edit containers.

**Downtime:** `docker compose up -d` restarts the backend. MVP accepts a few seconds of dropped SSE. Do not build a blue/green platform until a client SLA requires it. Warn beta clients of a deploy window if we know HITL sessions will drop.

---

## 9. Data, backups, and files

| | Staging | Production |
| --- | --- | --- |
| Postgres volume | Persistent, but wipeable | Persistent |
| Backups | Optional | **Required before first real client:** nightly `pg_dump` (or volume snapshot) off-box, tested restore quarterly. Also copy the upload directory; a database dump does not contain the files |
| Uploaded files | Docker volume on the ~80 GB boot disk. Wipeable with the VM | Same disk. Shared with the OS, images, and Postgres |
| Redis | Ephemeral OK (HITL state is short-lived) | Ephemeral OK for MVP; losing Redis aborts in-flight HITL, not the document corpus |

Uploads do not use object storage. Each VM’s boot volume is the store (about 80 GB). At a 10 MB cap that holds a small beta after leaving room for the OS, images, and Postgres. Prune unused images so the disk does not fill. Revisit only when free space on either VM gets tight.

Never point a local laptop at the production `DATABASE_URL`. Never copy production dumps into Slack.

---

## 10. Observability and access

- **Sentry:** enabled on staging and production (`FASTAPI_ENV` not development). Tag `environment`.
- **Logs:** Traefik access log + backend stdout. Ship to a host file or a cheap log drain when beta starts; do not grep production by SSH as the long-term plan.
- **SSH:** key-based, no password, `github` user cannot be the only root path — keep a separate ops user.
- **Firewall:** 22 (allowlisted), 80, 443. Postgres, Redis, and 8000 bound to the Docker network only.
- **Platform superuser** (`is_superuser`): our ops account, not a client Admin. Different password per env.

---

## 11. Widget and client sites

Beta clients will paste the snippet on **their** staging or production origin. Our environments stay ours:

- Their staging site → our **staging** workspace + staging script URL
- Their production site → our **production** workspace + production script URL

Do not give a beta client a production snippet that still points at staging (mixed HITL, mixed JWT secrets, mixed RAG). The dashboard snippet (Phase 6.5 / 9) must be environment-aware.

CORS: widget API will need customer origins (Phase 9). Staging CORS list is not a substitute for production’s list.

---

## 12. LLM cost and launch safety on deployed envs

Staging is a public URL once beta exists. Treat it like production for **abuse**, with tighter caps:

- Redis rate limits (Phase 8.2) on in both envs
- Separate OpenAI project + spend cap for staging
- Production spend cap documented and alerted (Sentry or provider email)

A staging key leaked in a client’s public JS is expected (workspace public id). Dashboard `SECRET_KEY` and OpenAI keys are not.

---

## 13. What we have today vs the target

| Piece | Today | Target |
| --- | --- | --- |
| Compose deploy files | Yes (`STACK_NAME`) | Keep; add Redis / worker / vector image when product needs them |
| Manual server deploy | Documented | Keep as break-glass |
| GitHub deploy workflow | SSH from `ubuntu-latest`; staging on `develop`; prod on `release` PR | Keep |
| FastAPI Cloud workflow | Disabled | Stay disabled |
| `STACK_NAME` / project name | `a2i-staging` / `a2i-prod` | Keep |
| Staging + prod VM + DNS | Operator guide; not provisioned until OCI console work | First infra slice |
| Backups | None | Prod before real data |
| Widget URL | N/A | Same origin on each env |

---

## 14. Decision log

| # | Decision | Status | Choice |
| --- | --- | --- | --- |
| D1 | Primary hosting | **Decided** | Docker Compose + Traefik on VPS |
| D2 | FastAPI Cloud | **Decided** | Not primary; do not auto-deploy `master` there |
| D3 | Staging vs prod isolation | **Decided** | Two VPS (Always Free: 1 OCPU / 6 GB each), two secret sets, two GitHub Environments |
| D4 | Promotion | **Decided** | Auto staging from `develop`; prod only via labeled release PR into `master` |
| D5 | App packaging | **Decided** | Single backend image (SPA + API + later widget file) |
| D6 | Adminer | **Decided** | Staging only, not public on prod |
| D7 | Widget delivery (MVP) | **Decided** | Same origin as the API; CDN is V1 |
| D8 | Orchestration | **Decided** | Compose, not Kubernetes, through V1 |
| D9 | Zero-downtime | **Decided** | Not required for MVP; brief restart is OK |
| D10 | Config flag | **Decided** | Staging/prod do not set `FASTAPI_ENV=development` |

---

## 15. What not to do

- Do not deploy production from a laptop `rsync` as the happy path (break-glass only, then match git SHA).
- Do not run `compose.override.yml` on a server.
- Do not expose Postgres, Redis, or the Traefik API to the internet.
- Do not use one `SECRET_KEY` for both environments.
- Do not add a “preview app per PR” platform until staging is boring.
- Do not split the monolith into separately deployed microservices as a hosting trick (backend Option B).

---

## 16. Implementation slices (after this decision)

1. **Inventory:** FastAPI Cloud workflow disabled.
2. **Compose:** `STACK_NAME`, unique Traefik names, Adminer staging-only.
3. **GitHub Environments** `staging` and `production` with the secret table in §6.1 plus **per-VM** SSH keys.
4. **Staging VM + DNS** (`staging.dactionlabs.com`): 1 OCPU / 6 GB, Docker Engine, `deploy` user, first Compose deploy. See [deployment-oracle-cloud.md](../../../deployment-oracle-cloud.md).
5. **CD:** merge to `develop` → staging VM; labeled release PR into `master` → production VM.
6. **Smoke** health check + login on staging; then first release PR for the production VM.
7. **Backups** before real client data.
8. **Extend Compose** with Redis / pgvector / upload volume / worker in the same slices as the product phases — not as a separate “platform rewrite.”

**Done when:** a merge to `develop` updates staging without a laptop SSH as the happy path, a release PR can ship production, and Phase 10.3 can be executed against `https://staging.dactionlabs.com` rather than localhost.
