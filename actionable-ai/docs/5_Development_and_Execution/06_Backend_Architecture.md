# 06 Backend Architecture

## Document Metadata

- **Product:** Actionable AI (A²I) Platform
- **Status:** Decided — Option B (2026-08-25)
- **Last Updated:** 2026-08-25
- **Companion:** [05 Frontend Architecture](./05_Frontend_Architecture.md), [01 System Architecture](./01_System_Architecture.md), [02 Database Schema](./02_Database_Schema.md), [07 Deployment Strategy](./07_Deployment_Strategy.md)

**Decision:** One FastAPI app (modular monolith). Models live in `app/models/` (package). Business logic lives in `app/services/`. Routes stay thin. Not microservices, not hexagonal, not a second chat process. Rules in §7 are in force.

---

## 1. Important correction

[01 System Architecture](./01_System_Architecture.md) describes a “decoupled microservices architecture.” **That is not what the repo is, and it should not be what we build for MVP.**

What we have: **one FastAPI process**, one Postgres, no Redis, no workers, all tables in one `models.py`.

What we should grow into for MVP and V1: a **modular monolith** — still one deployable, internally split by domain, with Redis and a background job runner when ingestion and HITL need them.

Split into real services (chat vs knowledge vs tools) only when a single process cannot scale or a team boundary appears. Doing it now would multiply auth, migrations, and local DX for no gain.

---



## 2. Current stack (as of this review)


| Layer         | Choice                                        | Notes                                                           |
| ------------- | --------------------------------------------- | --------------------------------------------------------------- |
| API           | FastAPI, Python ≥ 3.14                        | Sync route handlers (`def`, not `async def`) almost everywhere  |
| ORM           | SQLModel                                      | Tables + request/response schemas in `app/models.py`            |
| DB            | PostgreSQL 18 (Compose)                       | Alembic migrations. `create_all` is commented out               |
| Auth          | JWT (HS256), OAuth2 password form             | One token type: dashboard user id in `sub`                      |
| Password      | pwdlib Argon2 (+ bcrypt verify)               |                                                                 |
| Config        | `pydantic-settings` from root `.env`          |                                                                 |
| Email         | SMTP + Jinja HTML from `packages/react-email` |                                                                 |
| Observability | Sentry (non-dev)                              |                                                                 |
| Tests         | Pytest + `TestClient`                         | Real DB via Compose; session fixture deletes `Item` then `User` |
| Serve UI      | `app.frontend("/", directory=FRONTEND_DIR)`   | Built SPA copied into `backend/app/frontend`                    |


There is **no** pgvector, Redis, LangGraph, OpenAI client, object storage, or job queue in code yet. Compose services: Traefik, Postgres, Adminer, backend. Mailcatcher is in override.

---



## 3. Current folder structure

```text
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, mount frontend, include router
│   ├── models.py            # ALL tables + Pydantic/SQLModel schemas
│   ├── crud.py              # user helpers + create_item
│   ├── utils.py             # email send/templates
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py            # engine, init_db (first superuser)
│   │   └── security.py      # JWT + password hash
│   ├── api/
│   │   ├── main.py          # include route modules
│   │   ├── deps.py          # SessionDep, CurrentUser, superuser
│   │   └── routes/
│   │       ├── login.py
│   │       ├── users.py
│   │       ├── items.py     # SQL lives in the route, not crud
│   │       ├── utils.py     # health, test email
│   │       └── private.py   # dev-only
│   └── alembic/             # migrations; env.py imports SQLModel from app.models
├── tests/
│   ├── api/routes/
│   ├── crud/
│   └── utils/
└── pyproject.toml
```



### 3.1 How a request is handled today

```text
HTTP
  → app.main (CORS, /api/v1 prefix)
  → api/main.py router
  → api/routes/*.py
       Depends: SessionDep, CurrentUser
       SQLModel select / commit in the route (or crud.py for users)
  → Postgres
```

There is **no service layer**. Business rules (permissions, hashing, emails) sit in routes or `crud.py`. `items.py` inlines SQL; `users.py` mixes `crud` and inline SQL. That inconsistency will multiply.

### 3.2 Auth model today

- One JWT, signed with `SECRET_KEY`, `sub` = user UUID.
- `get_current_user` loads `User`. Inactive → 400. Superuser is a boolean on the user.
- There is **no workspace**, **no role**, **no second audience** for the embeddable widget’s end-user token.

The widget story requires a **different** token (minted by the *client’s* backend, verified with a per-workspace secret/JWKS). If we keep stuffing that into `get_current_user`, we will confuse “integrator logged into A²I” with “Alex using Acme’s app.”

---



## 4. What the product will add


| Domain               | Persistence                         | Runtime                             | Why a flat `models.py` / `routes/*.py` will hurt                                                 |
| -------------------- | ----------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Workspace / RBAC** | Workspace, User.role, membership    | Sync HTTP                           | Every later query must be tenant-scoped. Needs a `CurrentWorkspace` dep, not copy-paste filters. |
| **Knowledge**        | Document, DocumentChunk + vector    | Upload + **background** embed       | Long CPU/IO. Cannot sit in the request thread. Needs storage + OpenAI + status machine.          |
| **Tools**            | ToolRegistry JSON schema            | Outbound HTTP                       | SSRF, HITL flag, schema validation. Dangerous if mixed with chat routes.                         |
| **Chat / agent**     | Sessions, messages (or Redis state) | **Async** SSE + LangGraph interrupt | Sync `def` + `TestClient` patterns are the wrong default. HITL pause in Redis.                   |
| **Handoff**          | Settings on workspace               | Email + webhook POST                | Small, but needs transcript access from chat.                                                    |
| **GitHub (V1)**      | GithubRepository                    | Webhooks + workers                  | Must not be invented inside `items.py`-style files. Table can exist early; workers later.        |


If we keep the template shape, `models.py` and `api/routes/chat.py` become the bottleneck: unreviewable files, circular imports, and no place for “this is not an HTTP handler.”

---



## 5. Bottlenecks if we keep the template unchanged


| Bottleneck                      | What fails                                                                                                                                          |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Single** `models.py`          | Workspace, documents, chunks, tools, chat, github, HITL rows — one file, painful diffs, Alembic autogenerate noise.                                 |
| **Single** `crud.py`            | Either unused (logic in routes) or a thousand-line god module.                                                                                      |
| **Logic in route modules**      | Cannot reuse “ingest document” from a worker and from a retry endpoint. Cannot unit-test graph nodes without TestClient.                            |
| **Sync-only handlers**          | LangGraph, `httpx.AsyncClient`, SSE `yield` want async. Mixing blocking OpenAI calls inside `async def` will stall the event loop if we are sloppy. |
| **One JWT dependency**          | Widget impersonation / confused deputy: a dashboard token used as an end-user.                                                                      |
| **No tenant guard**             | First IDOR: `GET /documents/{id}` without `workspace_id`.                                                                                           |
| **Ingestion in-request**        | Upload waits on PDF parse + embeddings → timeouts, double-submit, no “Processing” badge.                                                            |
| **No Redis**                    | HITL resume and rate limits have nowhere cheap to live.                                                                                             |
| **No job runner**               | `BackgroundTasks` dies with the process; fine for first spike, not for reliable embed.                                                              |
| **Tests delete User/Item only** | New tables will leak between tests unless fixtures know the graph.                                                                                  |
| **Calling it microservices**    | Extra repos/networks before we have one working agent.                                                                                              |


---



## 6. Options



### Option A — Keep the template layout (flat files)

Keep adding `routes/knowledge.py`, more functions in `models.py` and `crud.py`.

**Fits:** Tutorials, CRUD apps, the next two weeks of *only* Workspace if we are ruthless.

**Fails:** Knowledge + chat in the same quarter. Review becomes “scroll 800 lines.”

**Verdict:** Acceptable **only** for the first Workspace table if we already know Option B is next. Not acceptable as the target.

### Option B — Modular monolith: shared models package + domain services + thin routes — **chosen**

One FastAPI app, one database, **folders by concern**:

```text
backend/app/
├── main.py
├── core/                      # config, db engine, redis, security, settings
│   ├── config.py
│   ├── db.py
│   ├── security.py
│   └── redis.py               # when we add it
├── models/                    # SQLModel tables + HTTP schemas (split by aggregate)
│   ├── __init__.py            # import all models so Alembic sees metadata
│   ├── workspace.py
│   ├── user.py
│   ├── document.py
│   ├── tool.py
│   └── chat.py
├── api/
│   ├── main.py
│   ├── deps.py                # SessionDep, CurrentUser, CurrentWorkspace, WidgetAuth
│   └── routes/
│       ├── login.py
│       ├── users.py
│       ├── workspaces.py
│       ├── knowledge.py       # HTTP only
│       ├── tools.py
│       └── chat.py            # SSE endpoints only
├── services/                  # reusable business logic (no FastAPI Request)
│   ├── workspaces.py
│   ├── knowledge/
│   │   ├── ingest.py
│   │   └── retrieve.py
│   ├── tools/
│   │   ├── registry.py
│   │   └── http_engine.py     # egress + SSRF denylist
│   └── chat/
│       ├── graph.py           # LangGraph
│       └── hitl.py
├── jobs/                      # enqueue / run embeddings (BackgroundTasks now, ARQ later)
└── alembic/
```

**Rules:**

- Routes parse auth, call a service, return a schema. No OpenAI or embedding loops in the route.
- Services take `Session` (or a unit of work), not `Request`.
- All product queries **require** `workspace_id` from `CurrentWorkspace`, never from an untrusted client field alone.
- Alembic still imports `from app.models import SQLModel` (package `__init__` imports every table module).

**Fits:** MVP through V1, small team, SQLModel relationships (FKs stay ordinary because models live in one package).

**Cost:** A one-time split of `models.py` / `crud.py` / `routes`. Must be done **before** the file is huge — i.e. as we add Workspace, not after chat.

**SQLModel note:** Official guidance is “keep related table models in one file when starting.” Splitting into a **package** with `__init__` imports is the usual next step; splitting into isolated domain packages that each define tables tends to create circular imports (`User` ↔ `Workspace`). That is why models stay together in `app/models/` even though *services* are split.

### Option C — Vertical slices (each domain owns its models)

```text
app/modules/knowledge/
  models.py
  router.py
  service.py
app/modules/chat/
  ...
```

**Fits:** Teams that want “change knowledge without opening users.”

**Cost:** SQLModel relationships across modules (`Document.workspace_id` → `Workspace`) force `TYPE_CHECKING` cycles and careful import side effects for Alembic. Easy to get wrong.

**Verdict:** Slightly cleaner story, worse ORM. Prefer B unless we leave SQLModel.

### Option D — Clean / hexagonal architecture

Ports, adapters, domain entities separate from SQLModel, repository interfaces.

**Fits:** Large orgs, swapping Postgres for something else.

**Cost:** We would wrap SQLModel twice. Slow delivery, little benefit while Postgres+pgvector is the product.

**Verdict:** No for MVP/V1.

### Option E — Microservices now

`knowledge-api`, `chat-api`, `widget-gateway`, separate DBs.

**Fits:** Independent scaling of SSE vs ingestion, multiple teams.

**Cost:** Distributed auth, distributed transactions, local compose explosion, HITL spanning services.

**Verdict:** Not before we have paying load and a real scaling problem. Redis + a worker inside Option B covers ingestion and HITL.

---



## 7. Working architecture (Option B)

These rules are **in force**. Adopt the layout **as we add the first product domain**, not as a big-bang rewrite of login/users routes.

### 7.1 Migration path (so Phase 1 stays reviewable)

Do **not** rewrite login/users/items **route logic** in the same slice as Workspace. Moving table classes into `app/models/` is a mechanical split and is allowed.

1. Introduce `app/models/` as a package: move existing `User` / `Item` / token schemas into files; `__init__.py` re-exports. Alembic import path stays `app.models.SQLModel`.
2. Add `Workspace` as `app/models/workspace.py` (Phase 1.1).
3. Add `app/services/` when signup must create a workspace (that is logic, not a route detail).
4. Add `app/api/routes/workspaces.py` when GET/PATCH exist.
5. Leave `items` routes where they are until we delete the feature.
6. When Knowledge starts: `services/knowledge/` + `jobs/` + a thin route. Do not put chunking in the route.
7. When Chat starts: **async** routes, LangGraph in `services/chat/`, Redis in `core/redis.py`.

### 7.2 Request architecture (target)

```text
Widget / Dashboard
  → FastAPI routes (auth + validation)
      → services (tenant rules, ingest, tools, graph)
          → Postgres (+ pgvector)
          → Redis (HITL, rate limit)
          → LLM provider
          → customer HTTPS APIs (tool engine, denylist)
      → jobs (embed)   // same services, different caller
```



### 7.3 Two auth dependencies (do not collapse)


| Dependency              | Token                                                     | Used by                                                                           |
| ----------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `CurrentUser`           | A²I dashboard JWT (`SECRET_KEY`, `sub` = our user)        | `/workspaces`, `/knowledge`, `/tools`, internal chat                              |
| `CurrentWorkspace`      | Derived from `CurrentUser` membership                     | All tenant queries                                                                |
| `WidgetUser` (name TBD) | JWT from **customer** signing key stored on the workspace | `/chat/stream` from the embed, tool execution identity forwarded to customer APIs |


Platform `is_superuser` stays for **our** ops (`/admin` users list). It is not client Admin.

### 7.4 Sync vs async

- CRUD and uploads that only touch Postgres: `def` is fine (FastAPI threadpool).
- Chat SSE, LangGraph, streaming LLM, async HTTP to customer APIs: `async def`.
- Never call blocking OpenAI/SDK sync clients inside `async def` without a thread offload.



### 7.5 Jobs


| Stage                 | Mechanism                                               |
| --------------------- | ------------------------------------------------------- |
| First Knowledge spike | FastAPI `BackgroundTasks` + status on `Document`        |
| Reliable MVP          | Redis queue (ARQ or TaskIQ) + worker process in Compose |
| Avoid until needed    | Celery (heavier)                                        |


HITL state: Redis, not a Postgres row, for MVP (fast interrupt). Persist chat transcript in Postgres if escalation needs it.

### 7.6 Testing

- Keep API tests with `TestClient` for HTTP contracts.
- Add **service tests** with a Session fixture for ingest, HITL lock, tenant isolation — these should not require SSE.
- Chat stream: pytest with `httpx.AsyncClient` or ASGI transport when we get there.
- Fixtures must truncate new tables in FK-safe order (chunks → documents → tools → users → workspaces).

---



## 8. Decision log

Widget JWT (B4) is **designed now**, implemented when the widget exists (Phase 6).

| # | Decision | Status | Choice |
| --- | --- | --- | --- |
| B1 | Overall shape | **Decided** | Option B — modular monolith, one FastAPI app |
| B2 | When to split `models.py` | **Decided** | **With Workspace** — introduce `app/models/` package; move User/Item/token into it; add `workspace.py` there. Do not grow the old single file |
| B3 | Tenant access | **Decided** | `CurrentWorkspace` from the session user. Do not trust a client-supplied workspace id alone |
| B4 | Widget auth | **Decided** | Separate `WidgetUser`. Dashboard JWT never authorizes customer tool calls |
| B5 | Ingestion runner | **Decided** | FastAPI `BackgroundTasks` first; ARQ (or TaskIQ) when Redis exists |
| B6 | HITL store | **Decided** | Redis (not a Postgres row) for pause/resume |
| B7 | LLM / graph | **Decided** | In-process LangGraph in `services/chat/` |
| B8 | File bytes | **Decided** | Local volume in Compose for MVP; hide behind `services/knowledge/storage.py` so S3 can swap later |


---



## 9. What not to do next

- Do not add a second FastAPI app or a “chat microservice.”
- Do not put LangGraph in `api/routes/chat.py`.
- Do not verify widget tokens with `get_current_user`.
- Do not run embeddings inside the upload request.
- Do not start pgvector/Redis until Workspace membership exists (tenant key for every row).

---

## 10. First implementation slices (after this decision)

Still **one task at a time**:

1. Create `app/models/` package and move existing User/Item/token schemas (mechanical; Alembic still imports `app.models.SQLModel`).
2. Add `Workspace` in `app/models/workspace.py` (Phase 1.1).
3. Alembic migration for `workspace`.
4. Attach user + role; `CurrentWorkspace`.
5. `GET`/`PATCH /workspaces/me`.
6. Signup creates workspace via `app/services/`.

Frontend stays [Option A](./05_Frontend_Architecture.md): no folder rewrite required for this backend work.

